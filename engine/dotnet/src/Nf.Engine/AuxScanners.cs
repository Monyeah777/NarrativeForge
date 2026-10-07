using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// check32（`quality_depth_scan`）里最后四件**只读子扫描器**的移植——它们各自没有独立 CLI 命令面
/// （真源只被 `nf doctor` / `nf release` / `quality_depth_scan` 消费，前两者含 bash 与 Python 运行时依赖），
/// 故按「内层组件」落地：等价性由**真仓实测 + 金标向量**钉住（同第七十二片度量引擎的口径）。
/// </summary>
public static class AuxScanners
{
    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    // ---------------------------------------------------------------- world_slots

    public static readonly HashSet<string> SlotKinds = new(StringComparer.Ordinal)
    {
        "string", "integer", "number", "boolean", "array", "object",
    };

    public static readonly HashSet<string> ItemKinds = new(StringComparer.Ordinal)
    {
        "string", "integer", "number", "boolean",
    };

    /// <summary>M00 数据槽注册表自身的结构与类型约束（world_model.slot 引用的不许是会漂移的自由 JSON）。</summary>
    public static List<string> ValidateRegistry(object? data, string label = "world_slots")
    {
        var issues = new List<string>();
        if (data is not Dictionary<string, object?> map) return new List<string> { $"{label}: 顶层非对象" };
        if (PyStr(map.GetValueOrDefault("schema_version")) != "1")
            issues.Add($"{label}.schema_version: 应为 \"1\"");
        if (map.GetValueOrDefault("slots") is not Dictionary<string, object?> slots || slots.Count == 0)
        {
            issues.Add($"{label}.slots: 非空对象");
            return issues;
        }
        foreach (var (path, spec) in slots)
        {
            var at = $"{label}.slots.{PyScalar.PyRepr(path)}";
            if (path.Trim().Length == 0) issues.Add($"{at}: 槽位路径非空字符串");
            if (spec is not Dictionary<string, object?> sm)
            {
                issues.Add($"{at}: 槽位定义非对象");
                continue;
            }
            var kind = sm.GetValueOrDefault("kind");
            var owner = sm.GetValueOrDefault("owner");
            var itemKind = sm.GetValueOrDefault("item_kind");
            if (!SlotKinds.Contains(PyStr(kind))) issues.Add($"{at}.kind: 非法类型 {PyScalar.PyRepr(kind)}");
            if (owner is not string os || os.Trim().Length == 0) issues.Add($"{at}.owner: 非空字符串");
            if (PyStr(kind) == "array")
            {
                if (itemKind is not null && !ItemKinds.Contains(PyStr(itemKind)))
                    issues.Add($"{at}.item_kind: 非法元素类型 {PyScalar.PyRepr(itemKind)}");
            }
            else if (itemKind is not null)
            {
                issues.Add($"{at}.item_kind: 仅 kind=array 可用");
            }
        }
        return issues;
    }

    public static (List<string> Issues, Dictionary<string, object?> Stats) WorldSlotsScan(string root)
    {
        var path = Path.Combine(root, "protocol", "world_slots.json");
        if (!File.Exists(path))
            return (new List<string> { "protocol/world_slots.json 缺失" },
                new Dictionary<string, object?>(StringComparer.Ordinal) { ["slots"] = 0L });
        object? data;
        try
        {
            using var doc = JsonIo.Parse(File.ReadAllBytes(path));
            data = PythonJson.ToGraph(doc.RootElement);
        }
        catch (Exception exc) when (exc is IOException or System.Text.Json.JsonException)
        {
            return (new List<string> { $"protocol/world_slots.json 解析失败：{exc.Message}" },
                new Dictionary<string, object?>(StringComparer.Ordinal) { ["slots"] = 0L });
        }
        var issues = ValidateRegistry(data);
        var m00 = Path.Combine(root, "04_模块库", "通用类", "M00_数据结构.md");
        var slots = (data as Dictionary<string, object?>)?.GetValueOrDefault("slots") as Dictionary<string, object?>
                    ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        if (File.Exists(m00))
        {
            var text = KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(m00)));
            foreach (var slot in slots.Keys)
                foreach (var part in slot.Split('.'))
                    if (part.Length > 0 && !text.Contains(part, StringComparison.Ordinal))
                        issues.Add($"world_slots slot 路径段未在 M00 文档锚定：{PyScalar.PyRepr(part)}（{slot}）");
        }
        else
        {
            issues.Add("04_模块库/通用类/M00_数据结构.md 缺失");
        }
        var arrays = slots.Values.OfType<Dictionary<string, object?>>()
            .Count(v => PyStr(v.GetValueOrDefault("kind")) == "array");
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["slots"] = (long)slots.Count, ["arrays"] = (long)arrays,
        });
    }

    // ---------------------------------------------------------------- instruction_step_audit

    public static readonly string[] AuditDocs =
    {
        "docs/agent/agent_组装指令包_v0.2.md",
        "docs/45_执行遥测规范.md",
        "docs/45_M2_回合级drill.md",
        "docs/45_M3_techdoc载荷提案.md",
        "docs/44_M2_AI通道内容规范.md",
    };

    private static readonly Regex InlineCode = new("`([^`\n]{1,160})`", RegexOptions.CultureInvariant);
    private static readonly Regex AddParser = new("add_parser\\(\\s*\"([^\"]+)\"", RegexOptions.CultureInvariant);

    /// <summary>指令档步进级可机检审计：内联 `nf &lt;sub&gt;` / `python scripts/…` / 仓库路径引用必须真实存在。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) InstructionStepAudit(string root)
    {
        var issues = new List<string>();
        var nfPy = Path.Combine(root, "scripts", "nf.py");
        var nfSubs = new HashSet<string>(StringComparer.Ordinal);
        if (File.Exists(nfPy))
        {
            var text = KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(nfPy)));
            foreach (Match m in AddParser.Matches(text)) nfSubs.Add(m.Groups[1].Value);
        }
        var steps = 0L;
        foreach (var rel in AuditDocs)
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path))
            {
                issues.Add($"{rel} 缺失（审计清单内档须在场）");
                continue;
            }
            var text = KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(path)));
            foreach (Match m in InlineCode.Matches(text))
            {
                var code = m.Groups[1].Value.Trim();
                if (code.StartsWith("nf ", StringComparison.Ordinal))
                {
                    steps++;
                    var parts = code.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                    if (parts.Length > 1 && !nfSubs.Contains(parts[1]))
                        issues.Add($"{rel}: 引用未知子命令 nf {parts[1]}");
                }
                else if (code.StartsWith("python scripts/", StringComparison.Ordinal))
                {
                    steps++;
                    var parts = code.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                    var fname = parts.Length > 1 ? parts[1].TrimStart('.', '/') : "";
                    if (fname.Length > 0
                        && !File.Exists(Path.Combine(root, fname.Replace('/', Path.DirectorySeparatorChar))))
                        issues.Add($"{rel}: 引用脚本不存在 {fname}");
                }
                else if (Regex.IsMatch(code, "(?:community|docs|protocol|03_管线库)/")
                         && (code.EndsWith(".md", StringComparison.Ordinal)
                             || code.EndsWith(".json", StringComparison.Ordinal)
                             || code.EndsWith(".yaml", StringComparison.Ordinal)))
                {
                    steps++;
                    if (!File.Exists(Path.Combine(root, code.Replace('/', Path.DirectorySeparatorChar))))
                        issues.Add($"{rel}: 引用路径不存在 {code}");
                }
            }
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["docs"] = (long)AuditDocs.Length, ["steps"] = steps,
        });
    }

    // ---------------------------------------------------------------- 载荷注册表 / 消费核对

    private static Dictionary<string, object?> EventRegistry(string root)
    {
        var path = Path.Combine(root, "protocol", "event_registry.json");
        if (!File.Exists(path)) return new Dictionary<string, object?>(StringComparer.Ordinal);
        using var doc = JsonIo.Parse(File.ReadAllBytes(path));
        return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
               ?? new Dictionary<string, object?>(StringComparer.Ordinal);
    }

    /// <summary>每个模块契约的 (id, publish, subscribe)——等价 <c>csc._module_docs</c> + <c>_fence_yaml</c> 的消费面。</summary>
    private static List<(string Id, List<string> Publish, List<string> Subscribe)> ModuleEvents(string root)
    {
        var output = new List<(string, List<string>, List<string>)>();
        foreach (var (rel, contract, id) in ModuleDocs.Contracts(root))
        {
            _ = rel;
            var events = contract.GetValueOrDefault("events") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            output.Add((id,
                ConceptGraph.PyList(events.GetValueOrDefault("publish")).Select(PyStr).ToList(),
                ConceptGraph.PyList(events.GetValueOrDefault("subscribe")).Select(PyStr).ToList()));
        }
        return output;
    }

    /// <summary>事件载荷字段注册表：schema 自校验 + 死注册 / 漏登交叉断言。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) PayloadRegistryScan(string root)
    {
        var issues = new List<string>();
        // 缺根/缺协议件时**如实报 issue**，不抛裸异常（真源 348577d 改动，极端渗透 D4：
        // 其余扫描器在空根下都返回 issue 列表，只有本入口会崩——同一纪律须一致）。
        var missingProtocol = new[] { "protocol/event_payload.schema.json", "protocol/event_registry.json" }
            .Where(rel => !File.Exists(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))))
            .ToList();
        if (missingProtocol.Count > 0)
        {
            return (new List<string> { $"缺 {string.Join("、", missingProtocol)}（修复指引：在 NF 仓库根运行本扫描，或先补齐该协议件）" },
                    new Dictionary<string, object?>(StringComparer.Ordinal));
        }
        var schemaPath = Path.Combine(root, "protocol", "event_payload.schema.json");
        object? schema = null;
        if (File.Exists(schemaPath))
        {
            using var schemaDoc = JsonIo.Parse(File.ReadAllBytes(schemaPath));
            schema = PythonJson.ToGraph(schemaDoc.RootElement);
        }
        var registry = EventRegistry(root);
        issues.AddRange(SchemaLint.SubsetValidate(registry, schema, "event_registry"));

        var used = new HashSet<string>(StringComparer.Ordinal);
        foreach (var (_, publish, subscribe) in ModuleEvents(root))
        {
            used.UnionWith(publish);
            used.UnionWith(subscribe);
        }
        var regPath = Path.Combine(root, "desktop", "src", "core", "registry.json");
        if (File.Exists(regPath))
        {
            using var regDoc = JsonIo.Parse(File.ReadAllBytes(regPath));
            var reg = PythonJson.ToGraph(regDoc.RootElement) as Dictionary<string, object?>
                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            if (reg.GetValueOrDefault("subscriptions") is Dictionary<string, object?> subs)
                used.UnionWith(subs.Keys);
        }
        var registered = (registry.GetValueOrDefault("events") as Dictionary<string, object?>)
                         ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var dead = registered.Keys.Except(used).OrderBy(x => x, StringComparer.Ordinal).ToList();
        if (dead.Count > 0)
            issues.Add($"已登记事件无 machine 引用（死注册）：{string.Join(", ", dead)}");
        var missing = used.Except(registered.Keys).OrderBy(x => x, StringComparer.Ordinal).ToList();
        if (missing.Count > 0)
            issues.Add($"机器事件未登记载荷（漏登）：{string.Join(", ", missing)}");
        var declared = registered.Values.OfType<Dictionary<string, object?>>()
            // 真源是 `if v.get("fields")` —— **Python 真值**：`fields` 在真仓是**映射**（字段名→规格）
            // 而不是列表，首版按 `PyList(...).Count > 0` 判 → 442 条全被判成"未声明"（declared=0）。
            .Count(v => PyTruthy(v.GetValueOrDefault("fields")));
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["registered"] = (long)registered.Count, ["used"] = (long)used.Count,
            ["declared"] = (long)declared, ["pending"] = (long)(registered.Count - declared),
        });
    }

    /// <summary>事件载荷 → 订阅方对应（只报告不设闸：缺订阅方不 FAIL，允许广播/出口事件）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) PayloadConsumerScan(string root)
    {
        var registry = EventRegistry(root);
        var subs = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var (id, _, subscribe) in ModuleEvents(root))
            foreach (var e in subscribe)
            {
                if (!subs.TryGetValue(e, out var list)) subs[e] = list = new List<string>();
                list.Add(id);
            }
        var consumers = new Dictionary<string, object?>(StringComparer.Ordinal);
        var declared = 0;
        foreach (var (ev, spec) in (registry.GetValueOrDefault("events") as Dictionary<string, object?>
                                    ?? new Dictionary<string, object?>(StringComparer.Ordinal)))
        {
            if (spec is not Dictionary<string, object?> sm) continue;
            if (!PyTruthy(sm.GetValueOrDefault("fields"))) continue;
            declared++;
            consumers[ev] = (subs.GetValueOrDefault(ev) ?? new List<string>())
                .Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal)
                .Cast<object?>().ToList();
        }
        return (new List<string>(), new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["events_declared"] = (long)declared,
            ["events_consumed"] = (long)consumers.Values
                .Count(v => v is List<object?> l && l.Count > 0),
            ["consumer_map"] = consumers,
        });
    }

    private static bool PyTruthy(object? v) => v switch
    {
        null => false,
        bool b => b,
        string s => s.Length > 0,
        long l => l != 0,
        int i => i != 0,
        double d => d != 0,
        List<object?> list => list.Count > 0,
        Dictionary<string, object?> map => map.Count > 0,
        _ => true,
    };

    private static string PyStr(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(CultureInfo.InvariantCulture),
        int i => i.ToString(CultureInfo.InvariantCulture),
        double d => PythonJson.PyFloatRepr(d),
        _ => PyScalar.PyRepr(v),
    };
}
