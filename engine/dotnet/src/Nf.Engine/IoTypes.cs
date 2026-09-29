using System.Globalization;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/io_types.py</c>：模块 I/O **类型面**（`machine_contract.io_types`）。
///
/// 判据分层（诚实分层，避免把"未收窄"当"错"）：**可证不匹配 / 越词表 = FAIL**；
/// 未标 io_types / outputs 键集不一致 / 无机读契约（L0）**只 WARN**；`untyped` 是合法值。
/// 类型面从**正文行**读（自带行解析器，与 Python 同口径，不走 YAML 图）。
/// </summary>
public static class IoTypes
{
    public const string RegistryRel = "protocol/event_registry.json";
    public const string ContractDescription = "I/O 类型面（可证不匹配）";

    private static readonly string[] Kinds =
        { "string", "integer", "number", "boolean", "array", "object", "event", "state", "untyped" };

    private static readonly Regex IoLine = new(@"^(\s*)io_types:\s*$");
    private static readonly Regex SubLine = new(@"^(\s*)(outputs|inputs):\s*(\{\})?\s*$");
    private static readonly Regex PairLine = new(@"^(\s*)([^:\s]+):\s*(\S+)\s*$");
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>从正文读 io_types 行块（无 <c>io_types:</c> 行 → null）。</summary>
    public static Dictionary<string, Dictionary<string, string>>? ParseIoTypes(string text)
    {
        var lines = KnowledgeSig.SplitLines(text);
        int? start = null;
        var baseIndent = 0;
        for (var i = 0; i < lines.Count; i++)
        {
            var m = IoLine.Match(lines[i]);
            if (!m.Success) continue;
            start = i;
            baseIndent = m.Groups[1].Value.Length;
            break;
        }
        if (start is null) return null;

        var result = new Dictionary<string, Dictionary<string, string>>(StringComparer.Ordinal)
        {
            ["outputs"] = new(StringComparer.Ordinal),
            ["inputs"] = new(StringComparer.Ordinal),
        };
        string? section = null;
        for (var i = start.Value + 1; i < lines.Count; i++)
        {
            var line = lines[i];
            if (line.Trim().Length == 0) continue;
            var indent = line.Length - line.TrimStart().Length;
            if (indent <= baseIndent) break;
            var sub = SubLine.Match(line);
            if (sub.Success)
            {
                section = sub.Groups[2].Value;
                if (sub.Groups[3].Success) result[section] = new Dictionary<string, string>(StringComparer.Ordinal);
                continue;
            }
            var pair = PairLine.Match(line);
            if (pair.Success && section is not null && result.ContainsKey(section))
                result[section][pair.Groups[2].Value] = pair.Groups[3].Value;
        }
        return result;
    }

    /// <summary>→ (issues, warns, stats)：可证不匹配/越词表 = FAIL；未收窄/L0/键集不一致 = WARN。</summary>
    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var rows = new List<(string Rel, string Text, Dictionary<string, object?> Contract)>();
        foreach (var rel in ModuleDocs.Files(root))
        {
            var text = StrictUtf8.GetString(File.ReadAllBytes(
                Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))));
            var parsed = MiniYaml.ParseFence(text, "machine_contract");
            var contract = parsed is not null && parsed.TryGetValue("machine_contract", out var block)
                           && block is Dictionary<string, object?> map
                ? map
                : new Dictionary<string, object?>(StringComparer.Ordinal);
            rows.Add((rel, text, contract));
        }

        var typed = 0;
        var untyped = 0;
        var provided = new Dictionary<string, Dictionary<string, string>>(StringComparer.Ordinal);
        var l0 = new List<string>();
        foreach (var (rel, text, contract) in rows)
        {
            var id = contract.GetValueOrDefault("id")?.ToString() ?? "";
            if (id.Length == 0)
            {
                l0.Add(rel);
                continue;
            }
            var io = ParseIoTypes(text);
            if (io is null)
            {
                warns.Add($"{id} 未标 io_types（修复指引：nf module types --write）");
                continue;
            }
            foreach (var section in new[] { "outputs", "inputs" })
            {
                foreach (var (key, kind) in io[section])
                {
                    if (Array.IndexOf(Kinds, kind) < 0)
                        issues.Add($"{id} io_types.{section}.{key} 类型越词表：{kind}（{string.Join("/", Kinds)}）");
                    if (kind == "untyped") untyped++;
                    else typed++;
                }
            }
            var declared = Strings(contract, "outputs").Select(x => x).ToHashSet(StringComparer.Ordinal);
            var marked = io["outputs"].Keys.ToHashSet(StringComparer.Ordinal);
            if (!declared.SetEquals(marked))
            {
                warns.Add($"{id} io_types.outputs 与 outputs 键集不一致（缺 {PyList(declared.Except(marked))} / " +
                          $"多 {PyList(marked.Except(declared))}）");
            }
            provided[id] = io["outputs"];
        }

        // 可证不匹配：消费方声明期望类型，提供方有类型声明但无一匹配
        foreach (var (_, text, contract) in rows)
        {
            var id = contract.GetValueOrDefault("id")?.ToString() ?? "";
            if (id.Length == 0) continue;
            var io = ParseIoTypes(text);
            if (io is null) continue;
            foreach (var (dep, want) in io["inputs"])
            {
                if (want is "untyped" or "state") continue;
                if (provided.TryGetValue(dep, out var got) && !got.Values.Contains(want))
                {
                    issues.Add($"类型不匹配：{id} 期望 {dep} 提供 {want}，但 {dep} 声明输出类型为 " +
                               $"{PyList(got.Values.ToHashSet(StringComparer.Ordinal))}（修复指引：对齐 io_types 或改依赖）");
                }
            }
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["modules_with_contract"] = rows.Count - l0.Count,
            ["l0_modules"] = l0.Count,
            ["typed_fields"] = typed,
            ["untyped_fields"] = untyped,
        };
        if (l0.Count > 0)
            warns.Add($"无机读契约（L0，无法承载 io_types）共 {l0.Count} 件：{string.Join("、", l0.Take(3))}");
        return (issues, warns, stats);
    }

    /// <summary>类型面覆盖率（供展示；不用来判死）。</summary>
    public static Dictionary<string, object?> Coverage(string root)
    {
        var (_, _, stats) = Scan(root);
        var total = (int)(stats["typed_fields"] ?? 0) + (int)(stats["untyped_fields"] ?? 0);
        stats["coverage"] = total == 0 ? 0.0 : Math.Round(100.0 * (int)(stats["typed_fields"] ?? 0) / total, 1);
        return stats;
    }

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _, stats) = Scan(root);
        var coverage = Coverage(root);
        var total = (int)(stats["typed_fields"] ?? 0) + (int)(stats["untyped_fields"] ?? 0);
        var detail = $"可证不匹配 {issues.Count} · 类型覆盖 " +
                     $"{(coverage["coverage"] as double? ?? 0.0).ToString("F1", CultureInfo.InvariantCulture)}%" +
                     $"（{stats["typed_fields"]}/{total} 字段）";
        return issues.Count == 0 ? (true, detail) : (false, string.Join("; ", issues.Take(2)));
    }

    private static List<string> Strings(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is List<object?> list
            ? list.Select(x => x?.ToString() ?? "").ToList()
            : new List<string>();

    private static string PyList(IEnumerable<string> items)
        => PyScalar.PyRepr(items.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList());
}
