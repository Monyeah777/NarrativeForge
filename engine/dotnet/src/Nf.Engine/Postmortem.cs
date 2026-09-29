namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/postmortem.py</c>：复盘门禁（SRE：无指责 + 根因指向机制 + 行动项可指派可验）。
///
/// 判据：声明（schema / 四段 / blame_tokens 与 root_cause_tokens 非空）+ 复盘件（必填、status 词表、
/// date 格式、四段齐、`trigger`/`refs` 可解析、**禁指责词**、根因段须含机制词、每条行动项须含
/// 「负责人」与「判据」、**status=closed 必须已被协议回执锚定**）。
/// </summary>
public static class Postmortem
{
    public const string DeclRel = "protocol/postmortem.json";
    public const string ReceiptsRel = "protocol/RECEIPTS.json";
    public const string Glob = "postmortems/PO-*.md";
    public const string Schema = "nf-postmortem/1";
    public const string ContractDescription = "复盘（无指责 + 根因指向机制 + 行动项闭环）";

    private static readonly string[] Sections = { "## 现象", "## 影响", "## 根因", "## 行动项" };
    private static readonly string[] SectionTitles = { "现象", "影响", "根因", "行动项" };

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _, stats) = Scan(root);
        if (issues.Count > 0) return (false, string.Join("; ", issues.Take(2)));
        return (true, $"复盘 {stats.GetValueOrDefault("postmortems")} 件 · 行动项 {stats.GetValueOrDefault("actions")} 条");
    }

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var decl = Decl(root);
        if (decl.Count == 0)
            return (new List<string> { $"缺复盘协议声明 {DeclRel}" }, warns,
                new Dictionary<string, object?>(StringComparer.Ordinal));
        if (DocContracts.Str(decl, "schema") != Schema)
            issues.Add($"复盘协议 schema 不匹配（期望 {Schema}）");
        var declaredSections = decl.TryGetValue("sections", out var s) && s is List<object?> list
            ? list.Select(x => x?.ToString() ?? "").ToList()
            : new List<string>();
        if (!declaredSections.SequenceEqual(SectionTitles, StringComparer.Ordinal))
            issues.Add("sections 必须是四段（现象/影响/根因/行动项）");
        foreach (var key in new[] { "blame_tokens", "root_cause_tokens" })
        {
            if (!(decl.TryGetValue(key, out var v) && v is List<object?> l && l.Count > 0))
                issues.Add($"{key} 不得为空（无指责与根因判据必须成文）");
        }

        var rows = DocContracts.GlobFiles(root, Glob);
        var actions = 0;
        foreach (var rel in rows)
        {
            var (docIssues, stats) = CheckDoc(root, rel, decl);
            var fm = ReadFrontmatter(root, rel).Fm;
            var label = fm is null ? "" : DocContracts.Str(fm, "id");
            if (label.Length == 0) label = Path.GetFileName(rel);
            foreach (var issue in docIssues) issues.Add($"{label}：{issue}");
            actions += stats.TryGetValue("actions", out var a) && a is int n ? n : 0;
        }
        if (rows.Count == 0) warns.Add($"暂无复盘件（{Glob}）——门禁空转");
        var outStats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["postmortems"] = rows.Count,
            ["actions"] = actions,
        };
        return (issues, warns, outStats);
    }

    /// <summary>单件机检 → (issues, stats)。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) CheckDoc(
        string root, string rel, Dictionary<string, object?>? decl = null)
    {
        decl ??= Decl(root);
        var (fm, body) = ReadFrontmatter(root, rel);
        if (fm is null) return (new List<string> { $"复盘件不存在：{rel}" }, new Dictionary<string, object?>());
        var issues = new List<string>();
        var required = Strings(decl, "required_fields");
        if (required.Count == 0) required = new List<string> { "id", "date", "trigger", "status", "refs" };
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
        foreach (var token in Strings(decl, "blame_tokens"))
        {
            if (token.Length > 0 && body.Contains(token, StringComparison.Ordinal))
                issues.Add($"命中指责性归因词「{token}」——复盘对事不对人");
        }
        var rootSection = "";
        if (body.Contains("## 根因", StringComparison.Ordinal))
        {
            rootSection = body[(body.IndexOf("## 根因", StringComparison.Ordinal) + "## 根因".Length)..];
            var actIndex = rootSection.IndexOf("## 行动项", StringComparison.Ordinal);
            if (actIndex >= 0) rootSection = rootSection[..actIndex];
        }
        var rootTokens = Strings(decl, "root_cause_tokens");
        if (rootSection.Length > 0 && rootTokens.Count > 0
            && !rootTokens.Any(t => rootSection.Contains(t, StringComparison.Ordinal)))
        {
            issues.Add($"根因段未指向机制（须出现 {string.Join("/", rootTokens.Take(4))} 之一）");
        }
        var actions = body.Contains("## 行动项", StringComparison.Ordinal)
            ? DocContracts.BulletBlocks(body[(body.IndexOf("## 行动项", StringComparison.Ordinal) + "## 行动项".Length)..])
            : new List<string>();
        if (actions.Count == 0) issues.Add("行动项为空——没有行动项的复盘不闭环");
        foreach (var action in actions)
        {
            if (!action.Contains("负责人", StringComparison.Ordinal))
                issues.Add($"行动项缺负责人：{action[..Math.Min(40, action.Length)]}");
            if (!action.Contains("判据", StringComparison.Ordinal))
                issues.Add($"行动项缺判据：{action[..Math.Min(40, action.Length)]}");
        }
        var checks = DocContracts.ChecksFromVerify(root);
        foreach (var reference in DocContracts.RefsOf(fm.TryGetValue("trigger", out var trigger) ? trigger : null))
        {
            var issue = DocContracts.CheckRefIssue(root, reference.Trim(), checks, "引用");
            if (issue is not null) issues.Add(issue);
        }
        foreach (var reference in DocContracts.RefsOf(fm.TryGetValue("refs", out var refs) ? refs : null))
        {
            var issue = DocContracts.CheckRefIssue(root, reference.Trim(), checks, "引用");
            if (issue is not null) issues.Add(issue);
        }
        if (DocContracts.Str(fm, "status") == "closed")
        {
            var receiptsPath = Path.Combine(root, ReceiptsRel.Replace('/', Path.DirectorySeparatorChar));
            if (File.Exists(receiptsPath))
            {
                using var doc = JsonIo.ReadFile(receiptsPath);
                var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>;
                var ids = (graph?.GetValueOrDefault("entries") as List<object?> ?? new List<object?>())
                    .OfType<Dictionary<string, object?>>()
                    .Select(e => e.GetValueOrDefault("id")?.ToString() ?? "")
                    .ToHashSet(StringComparer.Ordinal);
                if (!ids.Contains(rel))
                    issues.Add("status=closed 但未被协议回执锚定（防事后美化；修复指引：nf receipts --write）");
            }
        }
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["actions"] = actions.Count,
            ["sections"] = Sections.Count(s => body.Contains(s, StringComparison.Ordinal)),
        };
        return (issues, stats);
    }

    public static Dictionary<string, object?> Decl(string root) => DocContractIo.Decl(root, DeclRel);

    private static (Dictionary<string, object?>? Fm, string Body) ReadFrontmatter(string root, string rel)
        => DocContractIo.ReadFrontmatter(root, rel);

    private static bool Filled(Dictionary<string, object?> fm, string key)
        => DocContractIo.Filled(fm, key);

    private static List<string> Strings(Dictionary<string, object?> map, string key)
        => DocContractIo.Strings(map, key);
}
