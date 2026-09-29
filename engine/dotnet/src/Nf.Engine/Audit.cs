using System.Security.Cryptography;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/audit.py</c>：审计 / 验收门禁（Audit Report + Acceptance/Sign-off）。
///
/// 判据：声明（schema / verdict 词表 / rules 非空）+ 带审计头的报告（必填齐、verdict 在词表、date 格式、
/// **`subjects` 每条 `路径:sha256` 必须与当前文件一致**——对象一改旧审计即失效、
/// `accepted_by` 出现则必须有合法 `accepted_at`）+ 无审计头的存量件按 **WARN** 挂账（不判死）。
/// </summary>
public static class Audit
{
    public const string DeclRel = "protocol/audit.json";
    public const string Glob = "results/audit/*.md";
    public const string Schema = "nf-audit/1";
    public const string ContractDescription = "审计/验收（结论绑定对象 digest + 签收双要素）";

    private static readonly string[] Verdicts = { "pass", "fail", "warn" };

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _, stats) = Scan(root);
        if (issues.Count > 0) return (false, string.Join("; ", issues.Take(2)));
        return (true, $"审计 {stats.GetValueOrDefault("audits")} 件（带审计头 {stats.GetValueOrDefault("with_header")} · " +
                      $"legacy {stats.GetValueOrDefault("legacy")}）· 绑定对象 {stats.GetValueOrDefault("subjects_ok")}");
    }

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var decl = DocContractIo.Decl(root, DeclRel);
        if (decl.Count == 0)
            return (new List<string> { $"缺审计协议声明 {DeclRel}" }, warns,
                new Dictionary<string, object?>(StringComparer.Ordinal));
        if (DocContracts.Str(decl, "schema") != Schema)
            issues.Add($"审计协议 schema 不匹配（期望 {Schema}）");
        var vocabulary = decl.TryGetValue("verdict_vocabulary", out var v) && v is List<object?> list
            ? list.Select(x => x?.ToString() ?? "").ToList()
            : new List<string>();
        if (!vocabulary.SequenceEqual(Verdicts, StringComparer.Ordinal))
            issues.Add("verdict 词表与判据不一致（期望 pass/fail/warn）");
        if (!(decl.TryGetValue("rules", out var rules) && rules is List<object?> r && r.Count > 0))
            issues.Add("rules 不得为空（审计纪律必须成文）");

        var rows = DocContracts.GlobFiles(root, Glob);
        var legacy = new List<string>();
        var subjectsOk = 0;
        foreach (var rel in rows)
        {
            var (docIssues, stats) = CheckDoc(root, rel, decl);
            if (stats.TryGetValue("legacy", out var isLegacy) && isLegacy is true)
            {
                legacy.Add(Path.GetFileName(rel));
                continue;
            }
            var fm = DocContractIo.ReadFrontmatter(root, rel).Fm;
            var label = fm is null ? "" : DocContracts.Str(fm, "id");
            if (label.Length == 0) label = Path.GetFileName(rel);
            foreach (var issue in docIssues) issues.Add($"{label}：{issue}");
            subjectsOk += stats.TryGetValue("subjects", out var s) && s is int n ? n : 0;
        }
        if (legacy.Count > 0)
            warns.Add($"存量审计件无审计头（legacy，按回合收）：{legacy.Count} 件 —— {string.Join("、", legacy.Take(3))}");
        if (rows.Count == 0) warns.Add($"暂无审计件（{Glob}）");
        var outStats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["audits"] = rows.Count,
            ["with_header"] = rows.Count - legacy.Count,
            ["legacy"] = legacy.Count,
            ["subjects_ok"] = subjectsOk,
        };
        return (issues, warns, outStats);
    }

    /// <summary>单件机检 → (issues, stats)。无审计头者返回空 issues + legacy 统计。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) CheckDoc(
        string root, string rel, Dictionary<string, object?>? decl = null)
    {
        decl ??= DocContractIo.Decl(root, DeclRel);
        var (fm, _) = DocContractIo.ReadFrontmatter(root, rel);
        if (fm is null) return (new List<string> { $"审计件不存在：{rel}" }, new Dictionary<string, object?>());
        if (!DocContractIo.Filled(fm, "id"))
            return (new List<string>(), new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["legacy"] = true, ["subjects"] = 0,
            });

        var issues = new List<string>();
        var required = DocContractIo.Strings(decl, "required_fields");
        if (required.Count == 0)
            required = new List<string> { "id", "date", "scope", "verdict", "auditor", "subjects" };
        foreach (var key in required)
        {
            if (!DocContractIo.Filled(fm, key)) issues.Add($"缺必填字段：{key}");
        }
        var vocabulary = DocContractIo.Strings(decl, "verdict_vocabulary");
        if (vocabulary.Count == 0) vocabulary = Verdicts.ToList();
        if (!vocabulary.Contains(DocContracts.Str(fm, "verdict"), StringComparer.Ordinal))
            issues.Add($"verdict 越词表：{DocContracts.Str(fm, "verdict")}");
        if (!DocContracts.IsDated(DocContracts.Str(fm, "date")))
            issues.Add($"date 非 YYYY-MM-DD：{DocContracts.Str(fm, "date")}");

        var subjectsOk = 0;
        foreach (var subject in DocContracts.RefsOf(fm.TryGetValue("subjects", out var subs) ? subs : null))
        {
            var text = subject.Trim();
            if (!text.Contains(':'))
            {
                issues.Add($"subjects 条目格式须为 路径:sha256：{text[..Math.Min(40, text.Length)]}");
                continue;
            }
            var split = text.LastIndexOf(':');
            var relPath = text[..split];
            var want = text[(split + 1)..];
            var full = Path.Combine(root, relPath.Replace('\\', '/').Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(full))
            {
                issues.Add($"被审对象不存在：{relPath}");
                continue;
            }
            if (!string.Equals(Sha256Hex(File.ReadAllBytes(full)), want.Trim(), StringComparison.Ordinal))
            {
                issues.Add($"被审对象已变，旧审计失效：{relPath}（修复指引：重审并更新 digest）");
                continue;
            }
            subjectsOk++;
        }
        if (DocContractIo.Filled(fm, "accepted_by") && !DocContracts.IsDated(DocContracts.Str(fm, "accepted_at")))
            issues.Add("有 accepted_by 但 accepted_at 缺失或格式非法（签收须双要素）");

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["legacy"] = false,
            ["subjects"] = subjectsOk,
        };
        return (issues, stats);
    }

    private static string Sha256Hex(byte[] data)
        => Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
}
