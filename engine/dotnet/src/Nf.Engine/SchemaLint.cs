using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/schema_lint.py</c>：协议层 **IDL 校验器**（自实现 JSON-Schema 子集 + 全量件扫描）。
///
/// 扫描六类件：五份 schema 文件的元结构 + 模块契约 / registry 投影 / 管线声明 / 社区协议 / 资产台账。
/// **子集越界即 FAIL**（白名单之外的关键字一律报错），杜绝「声称子集却静默忽略语义」的假绿。
/// 判错文案与 Python 逐字对齐（含 <c>!r</c> 形态与路径写法）——两侧同参必须给同一句话。
/// </summary>
public static class SchemaLint
{
    public const string SchemaDir = "protocol/schema";
    public const string Dialect = "https://json-schema.org/draft/2020-12/schema";
    public const string ContractDescription = "IDL 单一真相零漂移";

    private static readonly HashSet<string> SubsetAllowedKeys = new(StringComparer.Ordinal)
    {
        "$schema", "$id", "title", "description", "type",
        "required", "properties", "propertyNames", "additionalProperties", "items",
        "enum", "pattern", "minLength", "minimum", "minItems", "maxItems",
    };

    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    // ------------------------------------------------------------ 子集越界检查

    /// <summary>递归扫描 schema 定义里校验器未实现的关键字（越界即 FAIL）。</summary>
    public static List<string> SubsetKeyViolations(object? schema, string path)
    {
        var issues = new List<string>();
        if (schema is not Dictionary<string, object?> map) return issues;
        foreach (var key in map.Keys)
        {
            if (!SubsetAllowedKeys.Contains(key))
                issues.Add($"{path}: 使用了校验器未实现的关键字 {key}（JSON-schema 子集越界——" +
                           "check28 无法兑现该语义；须扩展校验器或删除该关键字）");
        }
        if (map.TryGetValue("properties", out var props) && props is Dictionary<string, object?> propsMap)
        {
            foreach (var pair in propsMap)
                issues.AddRange(SubsetKeyViolations(pair.Value, $"{path}/properties/{pair.Key}"));
        }
        if (map.TryGetValue("items", out var items) && items is Dictionary<string, object?> itemsMap)
            issues.AddRange(SubsetKeyViolations(itemsMap, $"{path}/items"));
        if (map.TryGetValue("additionalProperties", out var extra) && extra is Dictionary<string, object?> extraMap)
            issues.AddRange(SubsetKeyViolations(extraMap, $"{path}/additionalProperties"));
        if (map.TryGetValue("propertyNames", out var pnames) && pnames is Dictionary<string, object?> pnamesMap)
            issues.AddRange(SubsetKeyViolations(pnamesMap, $"{path}/propertyNames"));
        return issues;
    }

    // ------------------------------------------------------------ 子集校验器

    /// <summary>JSON-Schema 子集校验；返回违例消息列表（空 = 通过）。</summary>
    public static List<string> SubsetValidate(object? instance, object? schema, string path)
    {
        var issues = new List<string>();
        if (schema is null) return issues;
        if (schema is not Dictionary<string, object?> map)
            return new List<string> { $"{path}: schema 段非对象" };

        var type = map.TryGetValue("type", out var t) ? t as string : null;

        if (type == "object")
        {
            if (instance is not Dictionary<string, object?> obj)
                return new List<string> { $"{path}: 应为 object，实为 {PyScalar.TypeName(instance)}" };

            var props = map.TryGetValue("properties", out var p) && p is Dictionary<string, object?> pm
                ? pm
                : new Dictionary<string, object?>(StringComparer.Ordinal);

            if (map.TryGetValue("required", out var req) && req is List<object?> required)
            {
                foreach (var item in required)
                {
                    var key = item as string ?? "";
                    if (!obj.ContainsKey(key)) issues.Add($"{path}: 缺必填字段 {key}");
                }
            }

            if (map.TryGetValue("propertyNames", out var pnames) && pnames is Dictionary<string, object?> pnamesMap)
            {
                foreach (var key in obj.Keys)
                    issues.AddRange(SubsetValidate(key, pnamesMap, $"{path}/{key}（键名）"));
            }

            foreach (var pair in props)
            {
                if (obj.TryGetValue(pair.Key, out var value))
                    issues.AddRange(SubsetValidate(value, pair.Value, $"{path}/{pair.Key}"));
            }

            var extra = map.TryGetValue("additionalProperties", out var e) ? e : null;
            foreach (var key in obj.Keys)
            {
                if (props.ContainsKey(key)) continue;
                if (extra is bool flag && !flag)
                {
                    issues.Add($"{path}: 未知字段 {key}（不在该 schema 词表内）");
                }
                else if (extra is Dictionary<string, object?> extraMap)
                {
                    issues.AddRange(SubsetValidate(obj[key], extraMap, $"{path}/{key}"));
                }
            }
            return issues;
        }

        if (type == "array")
        {
            if (instance is not List<object?> list)
                return new List<string> { $"{path}: 应为 array，实为 {PyScalar.TypeName(instance)}" };
            if (map.TryGetValue("minItems", out var min) && min is long minItems && list.Count < minItems)
                issues.Add($"{path}: 数组长度 {list.Count} < minItems {minItems}");
            if (map.TryGetValue("maxItems", out var max) && max is long maxItems && list.Count > maxItems)
                issues.Add($"{path}: 数组长度 {list.Count} > maxItems {maxItems}");
            var items = map.TryGetValue("items", out var it) ? it : null;
            for (var i = 0; i < list.Count; i++)
                issues.AddRange(SubsetValidate(list[i], items, $"{path}[{i}]"));
            return issues;
        }

        if (type == "string")
        {
            if (instance is not string text)
                return new List<string> { $"{path}: 应为 string，实为 {PyScalar.TypeName(instance)}" };
            if (map.TryGetValue("minLength", out var len) && len is long minLength && text.Length < minLength)
                issues.Add($"{path}: 字符串过短 {text.Length} < minLength {minLength}");
            if (map.TryGetValue("enum", out var values) && values is List<object?> allowed
                && !allowed.Any(v => PyScalar.PyEquals(v, text)))
            {
                issues.Add($"{path}: 值 {PyScalar.PyRepr(text)} 不在枚举 {PyScalar.PyRepr(allowed)}");
            }
            if (map.TryGetValue("pattern", out var pattern) && pattern is string patternText
                && !Regex.IsMatch(text, patternText))
            {
                issues.Add($"{path}: 值 {PyScalar.PyRepr(text)} 不匹配 pattern {patternText}");
            }
            return issues;
        }

        if (type == "integer")
        {
            if (instance is bool || instance is not long number)
                return new List<string> { $"{path}: 应为 integer，实为 {PyScalar.TypeName(instance)}" };
            if (map.TryGetValue("minimum", out var minValue) && minValue is not null
                && ToDouble(number) < ToDouble(minValue))
                issues.Add($"{path}: 值 {number} < minimum {PyReprPlain(minValue)}");
            return issues;
        }

        if (type == "number")
        {
            if (instance is bool || instance is not (long or double))
                return new List<string> { $"{path}: 应为 number，实为 {PyScalar.TypeName(instance)}" };
            if (map.TryGetValue("minimum", out var minValue) && minValue is not null
                && ToDouble(instance) < ToDouble(minValue))
                issues.Add($"{path}: 值 {PyReprPlain(instance)} < minimum {PyReprPlain(minValue)}");
            return issues;
        }

        if (type == "boolean")
        {
            return instance is bool
                ? issues
                : new List<string> { $"{path}: 应为 boolean，实为 {PyScalar.TypeName(instance)}" };
        }

        if (type is null) return issues;
        return new List<string> { $"{path}: 校验器不支持的 type {PyScalar.PyRepr(type)}" };
    }

    /// <summary>Python 的 <c>%s</c> 形态（整数不带引号、浮点按 repr）——用于 minimum 等直插。</summary>
    private static string PyReprPlain(object? value) => value switch
    {
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        double d => PythonJson.PyFloatRepr(d),
        string s => s,
        null => "None",
        _ => value.ToString() ?? "",
    };

    private static double ToDouble(object? value) => value switch
    {
        long l => l,
        int i => i,
        double d => d,
        _ => double.NaN,
    };

    // ------------------------------------------------------------ schema 元检

    public sealed record ScanResult(List<string> Issues, Dictionary<string, object?> Stats);

    /// <summary>校验 <c>protocol/schema/*.json</c> 在场且元结构合法；返回 (issues, schemas)。
    /// （第七十七片起<b>公开</b>：<c>protocol_golden</c> 的 golden 汇总也要同一份 schema 清单——保持单一实现。）</summary>
    public static (List<string> Issues, List<Dictionary<string, object?>> Schemas) CheckSchemaFiles(string root)
    {
        var issues = new List<string>();
        var schemas = new List<Dictionary<string, object?>>();
        var dir = Path.Combine(root, SchemaDir.Replace('/', Path.DirectorySeparatorChar));
        if (!Directory.Exists(dir))
            return (new List<string> { $"{SchemaDir}/ 缺失（协议层 IDL 未落盘）" }, schemas);
        foreach (var file in Directory.GetFiles(dir, "*.json").OrderBy(f => f, StringComparer.Ordinal))
        {
            var name = Path.GetFileName(file);
            Dictionary<string, object?>? data;
            try
            {
                using var doc = JsonIo.ReadFile(file);
                data = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>;
            }
            catch (Exception exc)
            {
                issues.Add($"{name}: JSON 解析失败 {exc.Message}");
                continue;
            }
            if (data is null)
            {
                issues.Add($"{name}: schema 顶层非对象");
                continue;
            }
            foreach (var key in new[] { "$id", "title", "type" })
            {
                if (!data.ContainsKey(key)) issues.Add($"{name}: schema 缺 {key}");
            }
            if (!(data.TryGetValue("$schema", out var dialect) && dialect is string dialectText
                  && dialectText == Dialect))
            {
                issues.Add($"{name}: $schema={PyScalar.PyRepr(data.TryGetValue("$schema", out var d) ? d : null)} " +
                           $"与校验器实现的方言不一致（预期 {Dialect}；修复指引：改声明或先扩展校验器再改声明）");
            }
            if (!(data.TryGetValue("type", out var schemaType) && schemaType is "object"))
                issues.Add($"{name}: schema.type 应为 object");
            if (!(data.TryGetValue("properties", out var properties) && properties is Dictionary<string, object?>))
                issues.Add($"{name}: schema.properties 缺失/非对象");
            if (data.TryGetValue("required", out var required) && required is not List<object?>)
                issues.Add($"{name}: schema.required 非数组");
            issues.AddRange(SubsetKeyViolations(data, name));
            schemas.Add(data);
        }
        return (issues, schemas);
    }

    // ------------------------------------------------------------ 件发现

    private static List<string> WalkMd(string root, string sub)
    {
        var found = new List<string>();
        var baseDir = Path.Combine(root, sub);
        if (!Directory.Exists(baseDir)) return found;
        void Recurse(string dir)
        {
            found.AddRange(Directory.GetFiles(dir)
                .Where(f => f.EndsWith(".md", StringComparison.Ordinal))
                .OrderBy(f => Path.GetFileName(f), StringComparer.Ordinal));
            foreach (var child in Directory.GetDirectories(dir))
            {
                if (Path.GetFileName(child) == "__pycache__") continue;
                Recurse(child);
            }
        }
        Recurse(baseDir);
        return found;
    }

    /// <summary>发现模块文档 / 管线声明 / 协议包三面（<b>公开</b>理由同 <see cref="CheckSchemaFiles"/>）。</summary>
    public static (List<string> ModuleDocs, List<string> PipelineDocs, List<string> ProtocolFiles) Discover(string root)
    {
        var moduleDocs = WalkMd(root, "04_模块库");
        var pipelineDocs = WalkMd(root, "03_管线库");
        var community = Path.Combine(root, "community");
        if (Directory.Exists(community))
        {
            foreach (var pack in Directory.GetDirectories(community)
                         .OrderBy(d => Path.GetFileName(d), StringComparer.Ordinal))
            {
                var modulesDir = Path.Combine(pack, "modules");
                if (Directory.Exists(modulesDir))
                {
                    moduleDocs.AddRange(Directory.GetFiles(modulesDir)
                        .Where(f => f.EndsWith(".md", StringComparison.Ordinal))
                        .OrderBy(f => Path.GetFileName(f), StringComparer.Ordinal));
                }
                var pipelinesDir = Path.Combine(pack, "pipelines");
                if (Directory.Exists(pipelinesDir))
                {
                    pipelineDocs.AddRange(Directory.GetFiles(pipelinesDir)
                        .Where(f => f.EndsWith(".md", StringComparison.Ordinal))
                        .OrderBy(f => Path.GetFileName(f), StringComparer.Ordinal));
                }
            }
        }
        var protocolFiles = Directory.Exists(community)
            ? Directory.GetDirectories(community)
                .Select(p => Path.Combine(p, "protocol.yaml"))
                .Where(File.Exists)
                .OrderBy(f => f, StringComparer.Ordinal)
                .ToList()
            : new List<string>();
        return (moduleDocs, pipelineDocs, protocolFiles);
    }

    // ------------------------------------------------------------ 扫描主入口

    public static ScanResult Scan(string root)
    {
        var issues = new List<string>();
        var (schemaIssues, schemas) = CheckSchemaFiles(root);
        issues.AddRange(schemaIssues);
        var byName = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var schema in schemas)
        {
            if (schema.TryGetValue("$id", out var id) && id is string idText)
                byName[Path.GetFileName(idText)] = schema;
        }

        var (moduleDocs, pipelineDocs, protocolFiles) = Discover(root);
        var contractSchema = byName.GetValueOrDefault("contract.schema.json");
        var moduleSchema = byName.GetValueOrDefault("module.schema.json");
        var pipelineSchema = byName.GetValueOrDefault("pipeline.schema.json");
        var protocolSchema = byName.GetValueOrDefault("protocol.schema.json");
        var assetSchema = byName.GetValueOrDefault("asset.schema.json");

        var contractCovered = 0;
        foreach (var doc in moduleDocs)
        {
            var rel = Rel(root, doc);
            string text;
            try
            {
                text = StrictUtf8.GetString(File.ReadAllBytes(doc));
            }
            catch (Exception exc)
            {
                issues.Add($"{rel}: 读取失败 {exc.Message}");
                continue;
            }
            var parsed = MiniYaml.ParseFence(text, "machine_contract");
            if (parsed is null) continue;          // 存量旧格式模块（缺块不阻断）
            contractCovered++;
            var mc = parsed.TryGetValue("machine_contract", out var block) ? block : parsed;
            if (contractSchema is not null)
                issues.AddRange(SubsetValidate(mc, contractSchema, $"{rel} machine_contract"));
        }

        // registry 投影（module.schema.json）
        var registryPath = Path.Combine(root, "desktop", "src", "core", "registry.json");
        var (registry, registryError) = ReadJson(registryPath);
        var registryModules = new List<object?>();
        if (registry is null)
        {
            issues.Add($"registry.json 读取/解析失败：{registryError}");
        }
        else if (registry.TryGetValue("modules", out var modules) && modules is List<object?> moduleList)
        {
            registryModules = moduleList;
        }
        if (moduleSchema is not null)
        {
            foreach (var entry in registryModules)
                issues.AddRange(SubsetValidate(entry, moduleSchema, "registry.modules"));
        }

        // 管线声明（pipeline.schema.json）
        foreach (var doc in pipelineDocs)
        {
            var rel = Rel(root, doc);
            string text;
            try
            {
                text = StrictUtf8.GetString(File.ReadAllBytes(doc));
            }
            catch (Exception exc)
            {
                issues.Add($"{rel}: 读取失败 {exc.Message}");
                continue;
            }
            var parsed = MiniYaml.ParseFence(text, "Pipeline:");
            if (parsed is null)
            {
                issues.Add($"{rel}: Pipeline yaml 缺失/解析失败");
                continue;
            }
            var obj = parsed.TryGetValue("Pipeline", out var pipeline) ? pipeline : parsed;
            if (pipelineSchema is not null)
                issues.AddRange(SubsetValidate(obj, pipelineSchema, $"{rel} Pipeline"));
        }

        // community 协议声明（protocol.schema.json）
        foreach (var proto in protocolFiles)
        {
            var rel = Rel(root, proto);
            object? data;
            try
            {
                data = MiniYaml.ParseAny(StrictUtf8.GetString(File.ReadAllBytes(proto)));
            }
            catch (Exception exc)
            {
                issues.Add($"{rel}: protocol.yaml 解析失败 {exc.Message}");
                continue;
            }
            if (protocolSchema is not null)
                issues.AddRange(SubsetValidate(data, protocolSchema, rel));
        }

        // 资产台账（asset.schema.json）
        var provenancePath = Path.Combine(root, "05_资产库", "provenance.json");
        var (provenance, provenanceError) = ReadJson(provenancePath);
        var assetEntries = new List<object?>();
        if (provenance is null)
        {
            issues.Add($"provenance.json 读取/解析失败：{provenanceError}");
        }
        else if (provenance.TryGetValue("assets", out var assets) && assets is List<object?> assetList)
        {
            assetEntries = assetList;
        }
        if (assetSchema is not null)
        {
            for (var i = 0; i < assetEntries.Count; i++)
                issues.AddRange(SubsetValidate(assetEntries[i], assetSchema, $"provenance.assets[{i}]"));
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema_files"] = schemas.Count,
            ["module_docs"] = moduleDocs.Count,
            ["contract_covered"] = contractCovered,
            ["pipelines"] = pipelineDocs.Count,
            ["protocols"] = protocolFiles.Count,
            ["asset_entries"] = assetEntries.Count,
        };
        return new ScanResult(issues, stats);
    }

    /// <summary>等价 Python <c>_read_json</c>：失败时把原因当**文案**返回（缺件按 CPython 形态写）。</summary>
    private static (Dictionary<string, object?>? Doc, string Error) ReadJson(string path)
    {
        if (!File.Exists(path))
            // 按 CPython 的 FileNotFoundError 文案镜像（路径走 repr 形态：反斜杠要转义）
            return (null, $"[Errno 2] No such file or directory: {PyScalar.PyRepr(path)}");
        try
        {
            using var doc = JsonIo.ReadFile(path);
            return (PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>,
                "JSON 内容不是对象");
        }
        catch (Exception exc)
        {
            return (null, exc.Message);
        }
    }

    private static string Rel(string root, string full)
        => Path.GetRelativePath(root, full).Replace('\\', '/');

    /// <summary>契约口径：<c>(ok, detail)</c>——detail 与 Python 的 f-string 同字。</summary>
    public static (bool Ok, string Detail) Contract(string root)
    {
        var result = Scan(root);
        var detail = $"schema 零漂移（{result.Stats.Count} 类件）";
        return result.Issues.Count == 0
            ? (true, detail)
            : (false, string.Join("; ", result.Issues.Take(2)));
    }
}
