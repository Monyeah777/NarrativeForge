using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/conformance_scan.py::scan</c>（**check29**：一致性分级——声明 ≤ 可证级别，防虚标）。
///
/// 三面：① 模块机读块 <c>machine_contract.conformance</c>（可证证据 = registry modules[] 在册）；
/// ② 社区协议包 <c>package.conformance</c>（可证 = registry protocols[] 在册）；
/// ③ 导出契约面 manifest（L3 = 导出门禁锁定面：证据文件在场 + 门禁号在 verify.sh）。
///
/// **声明边界（两处，均不改判定，只影响罕见错误路径的文案）**：
/// ① 「protocol.yaml 解析失败」分支以引擎的 YAML 子集（<see cref="MiniYaml"/>）为准，真源用 PyYAML 全量——
///    **取值另走定向抽取**（`package` 块直接子键），因此合法语料上两侧取值一致；
/// ② 「manifest 缺失/解析失败」的异常尾串来自各运行时（Python 的 errno 文案 vs .NET 的 message）。
/// ③ `machine_contract` 块不是映射时，真源会在 <c>mc.get</c> 处抛异常（整条 check29 变异常），
///    本件按「缺/非法声明」路径报出——**同一事实、不静默**，此差异登记在此。
/// </summary>
public static class ConformanceScan
{
    public const string ManifestRel = "protocol/export_conformance.json";
    public const string RegistryRel = "desktop/src/core/registry.json";
    public static readonly string[] Levels = { "L1", "L2", "L3" };

    public sealed record Result(List<string> Issues, Dictionary<string, object?> Stats)
    {
        public List<string> Log(string label = "Conformance")
        {
            var lines = Issues.Select(issue => "[FAIL] " + issue).ToList();
            lines.Add($"{label} 统计：机读块 {Stats["modules_mc"]} / 协议包 {Stats["packages"]}"
                      + $" / 导出面 {Stats["export_items"]}");
            return lines;
        }

        public string LogDigest(string label = "Conformance") => ExitFaces.Digest32(Log(label));
    }

    public static Result Scan(string root)
    {
        var issues = new List<string>();
        var evidence = EvidenceIds(root);
        var seenMcId = new Dictionary<string, string>(StringComparer.Ordinal);   // mc.id → 首个声明它的文件（重复即判 FAIL）

        var modulesMc = 0L;
        foreach (var rel in ModuleDocs.Files(root))
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            string text;
            try
            {
                text = File.ReadAllText(path, new System.Text.UTF8Encoding(false, throwOnInvalidBytes: true));
            }
            catch (Exception exc)
            {
                issues.Add($"{rel}: 读取失败 {exc.Message}");
                continue;
            }
            var parsed = MiniYaml.ParseFence(text, "machine_contract");
            if (parsed is null || !parsed.TryGetValue("machine_contract", out var block)) continue;
            modulesMc++;
            var mc = block as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            // 模块 id 全局唯一（真源 348577d 新增，极端渗透 D3）：**同一 mc.id 被两个模块文件声明**此前无判据，
            // 运行时索引 first-wins 静默择一（mcp_runtime._resolve_module / pipelinerun._module_files），
            // 会让"看起来唯一"的编号实际指向不确定的模块。此处补**文件级**唯一判据。
            var mcId = mc.GetValueOrDefault("id") is string midText ? midText : "";
            if (mcId.Length > 0)
            {
                if (seenMcId.TryGetValue(mcId, out var firstFile))
                {
                    issues.Add($"{rel}: 模块 id 与 {firstFile} 重复（mc.id={mcId}）——编号是全局寻址面，"
                               + "运行时索引会静默择一，须改号（修复指引：按 01 §1.6.11 换类内段号或 M91-M99 段号）");
                }
                else
                {
                    seenMcId[mcId] = rel;
                }
            }
            var declared = mc.TryGetValue("conformance", out var declaredValue) ? PyText(declaredValue) : null;
            if (declared is null || Array.IndexOf(Levels, declared) < 0)
            {
                issues.Add($"{rel}: machine_contract 缺/非法 conformance 声明 {PyScalar.PyRepr(declaredValue)}");
                continue;
            }
            var mid = mc.GetValueOrDefault("id") as string;
            var provable = mid is not null && evidence.Contains(mid) ? 2 : 1;
            if (Array.IndexOf(Levels, declared) + 1 > provable)
                issues.Add($"{rel}: conformance 虚标 {declared} > 可证 L{provable}"
                           + $"（{PyScalar.PyRepr(mc.GetValueOrDefault("id"))} 不在装配在册证据）");
        }

        var packages = 0L;
        var registry = ReadJson(root, RegistryRel);
        var regIds = new HashSet<string>(StringComparer.Ordinal);
        foreach (var item in PyListOfMaps((registry.Data as Dictionary<string, object?>)?.GetValueOrDefault("protocols")))
        {
            var pid = item.GetValueOrDefault("id");
            if (pid is string idText) regIds.Add(idText);
        }
        foreach (var pack in CommunityDirs(root))
        {
            var proto = Path.Combine(pack, "protocol.yaml");
            var rel = Rel(root, proto);
            string text;
            try
            {
                text = File.ReadAllText(proto, new System.Text.UTF8Encoding(false, throwOnInvalidBytes: true));
            }
            catch (Exception exc)
            {
                issues.Add($"{rel}: protocol.yaml 解析失败 {exc.Message}");
                continue;
            }
            try
            {
                MiniYaml.Parse(text);
            }
            catch (Exception exc)
            {
                issues.Add($"{rel}: protocol.yaml 解析失败 {exc.Message}");
                continue;
            }
            packages++;
            var (declared, pid2) = PackageFields(text);
            if (declared is null || Array.IndexOf(Levels, declared) < 0)
            {
                issues.Add($"{rel}: package 缺/非法 conformance 声明 {PyScalar.PyRepr(declared)}");
                continue;
            }
            var provable = pid2 is not null && regIds.Contains(pid2) ? 2 : 1;
            if (Array.IndexOf(Levels, declared) + 1 > provable)
                issues.Add($"{rel}: conformance 虚标 {declared} > 可证 L{provable}（包不在 registry protocols[]）");
        }

        var exportItems = 0L;
        var (manifest, err) = ReadJson(root, ManifestRel);
        if (manifest is not Dictionary<string, object?> manifestMap)
        {
            issues.Add($"{ManifestRel} 缺失/解析失败：{err}");
        }
        else
        {
            var verifyPath = Path.Combine(root, "verify.sh");
            var verifyText = File.Exists(verifyPath)
                ? File.ReadAllText(verifyPath, new System.Text.UTF8Encoding(false, throwOnInvalidBytes: true))
                : "";
            foreach (var item in ObjList(manifestMap.GetValueOrDefault("items")))
            {
                exportItems++;
                if (item is not Dictionary<string, object?> row)
                {
                    issues.Add("export manifest item 非对象");
                    continue;
                }
                if (PyText(row.GetValueOrDefault("conformance")) != "L3")
                    issues.Add($"导出面 {PyStr(row.GetValueOrDefault("id"))}: conformance 应为 L3（导出门禁锁定面）");
                foreach (var ev in ObjList(row.GetValueOrDefault("evidence")))
                {
                    var rel = PyStr(ev);
                    if (!File.Exists(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))))
                        issues.Add($"导出面 {PyStr(row.GetValueOrDefault("id"))}: 证据文件缺失 {rel}");
                }
                foreach (var gate in ObjList(row.GetValueOrDefault("gates")))
                {
                    var gateText = PyStr(gate);
                    if (!verifyText.Contains(gateText, StringComparison.Ordinal))
                        issues.Add($"导出面 {PyStr(row.GetValueOrDefault("id"))}: 证据门禁 {gateText} 不在 verify.sh");
                }
            }
        }

        return new Result(issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["modules_mc"] = modulesMc,
            ["packages"] = packages,
            ["export_items"] = exportItems,
        });
    }

    /// <summary>官方 registry <c>modules[].id</c> + <c>protocols[].module_ids[]</c>（装配在册证据）。</summary>
    public static HashSet<string> EvidenceIds(string root)
    {
        var ids = new HashSet<string>(StringComparer.Ordinal);
        var (data, _) = ReadJson(root, RegistryRel);
        if (data is not Dictionary<string, object?> reg) return ids;
        foreach (var module in PyListOfMaps(reg.GetValueOrDefault("modules")))
        {
            if (module.GetValueOrDefault("id") is string id) ids.Add(id);
        }
        foreach (var protocol in PyListOfMaps(reg.GetValueOrDefault("protocols")))
        {
            foreach (var mid in ObjList(protocol.GetValueOrDefault("module_ids")))
            {
                if (mid is string text) ids.Add(text);
            }
        }
        return ids;
    }

    /// <summary>Python <c>_read_json</c>：<c>(None, str(exc))</c>（只在解析失败时给出文案）。</summary>
    private static (object? Data, string Error) ReadJson(string root, string rel)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        try
        {
            using var doc = JsonIo.ReadFile(path);
            return (PythonJson.ToGraph(doc.RootElement), "");
        }
        catch (Exception exc)
        {
            return (null, exc.Message);
        }
    }

    private static List<string> CommunityDirs(string root)
    {
        var community = Path.Combine(root, "community");
        if (!Directory.Exists(community)) return new List<string>();
        return Directory.GetDirectories(community)
            .Where(dir => File.Exists(Path.Combine(dir, "protocol.yaml")))
            .OrderBy(dir => dir, StringComparer.Ordinal)
            .ToList();
    }

    /// <summary>
    /// 定向抽取 <c>package:</c> 块的直接子键 <c>conformance</c> / <c>id</c>（YAML 子集不含流映射时的取法）。
    /// 只读「紧跟 package 行、缩进等于首个子键缩进」的键行——<c>modules:</c> 下的 <c>- id:</c> 天然不在这一层。
    /// </summary>
    public static (string? Declared, string? Id) PackageFields(string text)
    {
        var lines = KnowledgeSig.SplitLines(text);
        var start = -1;
        for (var i = 0; i < lines.Count; i++)
        {
            var trimmed = lines[i].Trim();
            if (trimmed.Length == 0 || trimmed.StartsWith('#')) continue;
            var key = trimmed.Split(':', 2)[0].Trim();
            if (key == "package")
            {
                start = i;
                break;
            }
        }
        if (start < 0) return (null, null);
        var baseIndent = IndentOf(lines[start]);
        var childIndent = -1;
        string? declared = null, id = null;
        for (var j = start + 1; j < lines.Count; j++)
        {
            var trimmed = lines[j].Trim();
            if (trimmed.Length == 0 || trimmed.StartsWith('#')) continue;
            var indent = IndentOf(lines[j]);
            if (indent <= baseIndent) break;
            if (childIndent < 0) childIndent = indent;
            if (indent != childIndent) continue;
            var parts = trimmed.Split(':', 2);
            if (parts.Length != 2) continue;
            var key = parts[0].Trim();
            if (key == "conformance" && declared is null) declared = YamlScalar(parts[1]);
            else if (key == "id" && id is null) id = YamlScalar(parts[1]);
        }
        return (declared, id);
    }

    private static int IndentOf(string line)
    {
        var n = 0;
        foreach (var ch in line)
        {
            if (ch == ' ') n++;
            else if (ch == '\t') n += 8;
            else break;
        }
        return n;
    }

    /// <summary>取标量原文：带引号取引号内；否则截掉行尾注释（<c> #</c> 起）。空值 → <c>null</c>。</summary>
    private static string? YamlScalar(string raw)
    {
        var text = raw.Trim();
        if (text.Length == 0) return null;
        if (text[0] is '"' or '\'')
        {
            var quote = text[0];
            var end = text.IndexOf(quote, 1);
            return end < 0 ? text[1..] : text[1..end];
        }
        var hash = text.IndexOf(" #", StringComparison.Ordinal);
        if (hash >= 0) text = text[..hash];
        text = text.TrimEnd();
        return text.Length == 0 ? null : text;
    }

    private static string Rel(string root, string full) =>
        Path.GetRelativePath(root, full).Replace('\\', '/');

    private static string? PyText(object? value) => value switch
    {
        null => null,
        string s => s,
        bool b => b ? "True" : "False",
        _ => Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture),
    };

    /// <summary>Python f-string 里的取值：<c>None</c> 渲染成字面 <c>None</c>。</summary>
    private static string PyStr(object? value) => PyText(value) ?? "None";

    private static List<object?> ObjList(object? value) => value as List<object?> ?? new List<object?>();

    private static List<Dictionary<string, object?>> PyListOfMaps(object? value) =>
        (value as List<object?>)?.OfType<Dictionary<string, object?>>().ToList()
        ?? new List<Dictionary<string, object?>>();
}
