namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/handover.py</c>：接力协议门禁（SBAR：情境 → 背景 → 评估 → 建议 + 未决项）。
///
/// 判据：声明（schema / 五段 / rules 非空）+ 交接件（frontmatter 必填、status 词表、date 格式、
/// 五段齐、**未决项非空**、**每条未决必须带判据**、refs 每条可解析到真实件或 `checkN`）。
/// </summary>
public static class Handover
{
    public const string DeclRel = "protocol/handover.json";
    public const string Glob = "handovers/HO-*.md";
    public const string Schema = "nf-handover/1";
    public const string ContractDescription = "接力协议（SBAR 五段 + 未决带判据）";

    private static readonly string[] Sections =
        { "## 情境", "## 背景", "## 评估", "## 建议", "## 未决项" };
    private static readonly string[] SectionTitles = { "情境", "背景", "评估", "建议", "未决项" };

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _, stats) = Scan(root);
        if (issues.Count > 0) return (false, string.Join("; ", issues.Take(2)));
        return (true, $"交接件 {stats.GetValueOrDefault("handovers")} 件 · 未决 {stats.GetValueOrDefault("pending")} 条");
    }

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var decl = Decl(root);
        if (decl.Count == 0)
            return (new List<string> { $"缺交接协议声明 {DeclRel}" }, warns,
                new Dictionary<string, object?>(StringComparer.Ordinal));
        if (DocContracts.Str(decl, "schema") != Schema)
            issues.Add($"交接协议 schema 不匹配（期望 {Schema}）");
        var declaredSections = decl.TryGetValue("sections", out var s) && s is List<object?> list
            ? list.Select(x => x?.ToString() ?? "").ToList()
            : new List<string>();
        if (!declaredSections.SequenceEqual(SectionTitles, StringComparer.Ordinal))
            issues.Add("sections 必须是五段（情境/背景/评估/建议/未决项）");
        if (!(decl.TryGetValue("rules", out var rules) && rules is List<object?> r && r.Count > 0))
            issues.Add("rules 不得为空（交接纪律必须成文）");

        var rows = DocContracts.GlobFiles(root, Glob);
        var pendingTotal = 0;
        foreach (var rel in rows)
        {
            var (docIssues, stats) = CheckDoc(root, rel, decl);
            var fm = ReadFrontmatter(root, rel).Fm;
            var label = fm is null ? "" : DocContracts.Str(fm, "id");
            if (label.Length == 0) label = Path.GetFileName(rel);
            foreach (var issue in docIssues) issues.Add($"{label}：{issue}");
            pendingTotal += stats.TryGetValue("pending", out var p) && p is int n ? n : 0;
        }
        if (rows.Count == 0) warns.Add($"暂无交接件（{Glob}）——门禁空转");
        var outStats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["handovers"] = rows.Count,
            ["pending"] = pendingTotal,
        };
        return (issues, warns, outStats);
    }

    /// <summary>单件机检 → (issues, stats)。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) CheckDoc(
        string root, string rel, Dictionary<string, object?>? decl = null)
    {
        decl ??= Decl(root);
        var (fm, body) = ReadFrontmatter(root, rel);
        if (fm is null) return (new List<string> { $"交接件不存在：{rel}" }, new Dictionary<string, object?>());
        var issues = new List<string>();
        var required = Strings(decl, "required_fields");
        if (required.Count == 0) required = new List<string> { "id", "date", "from", "to", "status", "refs" };
        foreach (var key in required)
        {
            if (!Filled(fm, key)) issues.Add($"缺必填字段：{key}");
        }
        var vocabulary = Strings(decl, "status_vocabulary");
        if (vocabulary.Count == 0) vocabulary = new List<string> { "open", "closed" };
        if (!vocabulary.Contains(DocContracts.Str(fm, "status"), StringComparer.Ordinal))
            issues.Add($"status 越词表：{DocContracts.Str(fm, "status")}");
        if (!DocContracts.IsDated(DocContracts.Str(fm, "date")))
            issues.Add($"date 非 YYYY-MM-DD：{DocContracts.Str(fm, "date")}");
        foreach (var section in Sections)
        {
            if (!body.Contains(section, StringComparison.Ordinal)) issues.Add($"正文缺段落：{section}");
        }
        var pending = body.Contains("## 未决项", StringComparison.Ordinal)
            ? body[(body.IndexOf("## 未决项", StringComparison.Ordinal) + "## 未决项".Length)..]
            : "";
        var items = DocContracts.BulletBlocks(pending);
        if (items.Count == 0)
            issues.Add("未决项为空——空未决 = 不合格交接（没有未决就是没交接）");
        foreach (var item in items)
        {
            if (!item.Contains("判据", StringComparison.Ordinal))
                issues.Add($"未决项缺判据（怎样算完成）：{item[..Math.Min(40, item.Length)]}");
        }
        var checks = DocContracts.ChecksFromVerify(root);
        foreach (var reference in Refs(fm))
        {
            var text = reference.Trim();
            if (text.StartsWith('[') && text.EndsWith(']')) text = text[1..^1].Trim();
            // 注意：handover 侧的文案是 `refs 无法解析：…`（refs 后**带空格**），
            // 而 postmortem 侧是 `引用无法解析：…`——两模块本身间距不一致，照抄各自的字面。
            var issue = DocContracts.CheckRefIssue(root, text, checks, "refs ");
            if (issue is not null) issues.Add(issue);
        }
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["pending"] = items.Count,
            ["sections"] = Sections.Count(s => body.Contains(s, StringComparison.Ordinal)),
        };
        return (issues, stats);
    }

    public static Dictionary<string, object?> Decl(string root) => DocContractIo.Decl(root, DeclRel);

    private static (Dictionary<string, object?>? Fm, string Body) ReadFrontmatter(string root, string rel)
        => DocContractIo.ReadFrontmatter(root, rel);

    private static List<string> Refs(Dictionary<string, object?> fm)
        => DocContracts.RefsOf(fm.TryGetValue("refs", out var value) ? value : null);

    private static bool Filled(Dictionary<string, object?> fm, string key)
        => DocContractIo.Filled(fm, key);

    private static List<string> Strings(Dictionary<string, object?> map, string key)
        => DocContractIo.Strings(map, key);
}
