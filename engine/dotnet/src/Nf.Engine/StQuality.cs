namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/st_quality.py</c>：ST 制卡质量规范门禁（验收层规范的**数据化**：M/S/R → fail/warn/info）。
///
/// 两件确定性的事：① **声明完整性**（id 唯一且前缀 = scope、level/scope/check 词表、rule/basis/check 必填、
/// draft 须写 pending）；② **可落到产物的规则就判**（标 <c>check: artifact</c> 的规则在真实产物上核，
/// 当前只有 V2「初始值完备」）。边界：NF 不做 ST 运行时，不解析 PNG/实卡。
/// </summary>
public static class StQuality
{
    public const string DeclRel = "protocol/st_quality.json";
    public const string Schema = "nf-st-quality/1";
    public const string ArtifactRel = "docs/examples/mvu-output/mvu_variables.json";
    public const string ContractDescription = "ST 制卡质量规范（M/S/R 数据化 + 落产物判）";

    private static readonly string[] Levels = { "M", "S", "R" };
    private static readonly string[] Scopes = { "C", "W", "V", "X" };
    private static readonly string[] Checks = { "declaration", "artifact" };
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _, stats) = Scan(root);
        if (issues.Count > 0) return (false, string.Join("; ", issues.Take(2)));
        var byLevel = stats["by_level"] as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var detail = $"规则 {stats["rules"]} 条（M {byLevel.GetValueOrDefault("M")} / S {byLevel.GetValueOrDefault("S")} / " +
                     $"R {byLevel.GetValueOrDefault("R")}）· 落产物判 {stats["artifact_checked"]}";
        return (true, detail);
    }

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var empty = new Dictionary<string, object?>(StringComparer.Ordinal);
        var path = Path.Combine(root, DeclRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return (new List<string> { $"缺 ST 制卡质量规范 {DeclRel}" }, warns, empty);

        using var doc = JsonIo.ReadFile(path);
        var decl = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        if ((decl.GetValueOrDefault("schema")?.ToString() ?? "") != Schema)
            issues.Add($"规范 schema 不匹配（期望 {Schema}）");
        if (!Strings(decl, "level_vocabulary").SequenceEqual(Levels, StringComparer.Ordinal))
            issues.Add("level 词表必须为 M/S/R");
        if (!Strings(decl, "scope_vocabulary").SequenceEqual(Scopes, StringComparer.Ordinal))
            issues.Add("scope 词表必须为 C/W/V/X");
        if (!Strings(decl, "check_vocabulary").SequenceEqual(Checks, StringComparer.Ordinal))
            issues.Add("check 词表必须为 declaration/artifact");
        if ((decl.GetValueOrDefault("status")?.ToString() ?? "") == "draft" && Strings(decl, "pending").Count == 0)
            issues.Add("status=draft 但 pending 为空——草案必须写明还差什么");

        var seen = new HashSet<string>(StringComparer.Ordinal);
        var byLevel = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var level in Levels) byLevel[level] = 0;
        var artifacts = new List<string>();
        var rules = decl.GetValueOrDefault("rules") is List<object?> list
            ? list.OfType<Dictionary<string, object?>>().ToList()
            : new List<Dictionary<string, object?>>();
        foreach (var rule in rules)
        {
            var id = rule.GetValueOrDefault("id")?.ToString() ?? "";
            var tag = id.Length == 0 ? "(无名)" : id;
            if (!seen.Add(id)) issues.Add($"规则 id 重复：{id}");
            var scope = rule.GetValueOrDefault("scope")?.ToString() ?? "";
            if (Array.IndexOf(Scopes, scope) < 0)
            {
                issues.Add($"{tag} scope 越词表：{scope}");
            }
            else if (id.Length > 0 && !id.StartsWith(scope, StringComparison.Ordinal))
            {
                issues.Add($"{tag} 的 id 前缀与 scope 不一致（应 {scope} 开头）");
            }
            var level = rule.GetValueOrDefault("level")?.ToString() ?? "";
            if (Array.IndexOf(Levels, level) < 0)
            {
                issues.Add($"{tag} level 越词表：{level}");
            }
            else
            {
                byLevel[level] = (int)(byLevel[level] ?? 0) + 1;
            }
            foreach (var key in new[] { "rule", "basis", "check" })
            {
                if ((rule.GetValueOrDefault(key)?.ToString() ?? "").Trim().Length == 0)
                    issues.Add($"{tag} 缺必填字段：{key}");
            }
            if ((rule.GetValueOrDefault("check")?.ToString() ?? "") == "artifact") artifacts.Add(id);
        }
        foreach (var id in artifacts)
        {
            if (id == "V2") issues.AddRange(CheckV2(root));
        }
        issues.AddRange(CheckChecklist(root, decl, rules));

        var pending = Strings(decl, "pending");
        if (pending.Count > 0)
            warns.Add($"规范为草案：{pending.Count} 项待补（{string.Join("；", pending.Take(2))}）");

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["rules"] = seen.Count,
            ["by_level"] = byLevel,
            ["artifact_checked"] = artifacts.Count,
        };
        return (issues, warns, stats);
    }

    /// <summary>V2 初始值完备：`initial` 键集合 ⊆ 变量名集合。</summary>
    private static List<string> CheckV2(string root)
    {
        var path = Path.Combine(root, ArtifactRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return new List<string>();
        using var doc = JsonIo.ReadFile(path);
        var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var names = (graph.GetValueOrDefault("variables") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>()
            .Select(v => v.GetValueOrDefault("name")?.ToString() ?? "")
            .ToHashSet(StringComparer.Ordinal);
        var initial = graph.GetValueOrDefault("initial") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var extra = initial.Keys.Where(k => !names.Contains(k)).OrderBy(k => k, StringComparer.Ordinal).ToList();
        return extra.Count == 0
            ? new List<string>()
            : new List<string> { $"V2：初始值含未声明变量 {string.Join("、", extra)}（initial 与变量表不一一对应）" };
    }

    /// <summary>清单必须覆盖全部规则（`| &lt;id&gt; |` 形态出现），否则清单是装饰。</summary>
    private static List<string> CheckChecklist(
        string root, Dictionary<string, object?> decl, List<Dictionary<string, object?>> rules)
    {
        var rel = decl.GetValueOrDefault("checklist")?.ToString() ?? "";
        if (rel.Length == 0) return new List<string> { "缺 checklist 字段——人工自查清单必须登记（否则 S 级规则无处落地）" };
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return new List<string> { $"自查清单不存在：{rel}" };
        var text = StrictUtf8.GetString(File.ReadAllBytes(path));
        var missing = rules
            .Select(r => r.GetValueOrDefault("id")?.ToString() ?? "")
            .Where(id => id.Length > 0 && !text.Contains("| " + id + " |", StringComparison.Ordinal))
            .ToList();
        return missing.Count == 0
            ? new List<string>()
            : new List<string> { $"自查清单未覆盖规则：{string.Join("、", missing)}" };
    }

    private static List<string> Strings(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is List<object?> list
            ? list.Select(x => x?.ToString() ?? "").ToList()
            : new List<string>();
}
