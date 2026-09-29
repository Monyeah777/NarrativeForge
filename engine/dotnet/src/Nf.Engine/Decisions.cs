using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/decisions.py</c>：决策记录门禁（ADR：一条决策一编号，采纳后不改不删，只可被取代）。
/// 判据 = 编号/文件名一致 · 状态词表 · YYYY-MM-DD · 三段齐 · 取代链与环 · evidence 可解析（真实件 / checkN / ADR-N）
/// · accepted 必须被协议回执锚定 · INDEX 投影 == 实时重算。
/// </summary>
public static class Decisions
{
    public const string GlobPattern = "decisions/ADR-*.md";
    public const string IndexRel = "decisions/INDEX.md";
    public const string ReceiptsRel = "protocol/RECEIPTS.json";
    public const string Begin = "<!-- BEGIN GENERATED: decisions-index -->";
    public const string End = "<!-- END GENERATED: decisions-index -->";

    private static readonly string[] Statuses = { "proposed", "accepted", "superseded", "deprecated" };
    private static readonly string[] Sections = { "## 背景", "## 决策", "## 后果" };
    private static readonly string[] Dashes = { "—", "-", "" };
    private static readonly Regex IdRe = new(@"^ADR-(\d{4})$");
    private static readonly Regex FileIdRe = new(@"^ADR-(\d{4})-");
    private static readonly Regex CheckRe = new(@"^check(\d+)$");
    private static readonly Regex AdrRe = new(@"^ADR-\d{4}$");
    private static readonly Regex DatedRe = new(@"^\d{4}-\d{2}-\d{2}$");

    public sealed record Entry(string Path, string File, Dictionary<string, object?> Fm, string Body);

    /// <summary>极简 YAML frontmatter 解析（等价 <c>library.parse_frontmatter</c>）。</summary>
    public static (Dictionary<string, object?> Fm, string Body) ParseFrontmatter(string text)
    {
        var fm = new Dictionary<string, object?>(StringComparer.Ordinal);
        if (!text.StartsWith("---", StringComparison.Ordinal)) return (fm, text);
        var lines = KnowledgeSig.SplitLines(text).ToArray();
        int? end = null;
        for (var i = 1; i < lines.Length; i++)
        {
            if (lines[i].Trim() == "---") { end = i; break; }
        }
        if (end is null) return (fm, text);

        string? key = null;
        for (var i = 1; i < end.Value; i++)
        {
            var line = lines[i];
            if (line.Trim().Length == 0 || line.TrimStart().StartsWith('#')) continue;
            if ((line.StartsWith("  ", StringComparison.Ordinal) || line.StartsWith('\t')) && key is not null)
            {
                var item = line.Trim();
                if (item.StartsWith("- ", StringComparison.Ordinal)) item = item[2..].Trim();
                if (fm.TryGetValue(key, out var existing) && existing is List<string> list)
                {
                    list.Add(item.Trim('\'', '"'));
                }
                else
                {
                    fm[key] = new List<string> { item.Trim('\'', '"') };
                }
                continue;
            }
            var colon = line.IndexOf(':');
            if (colon < 0) continue;
            key = line[..colon].Trim();
            var value = line[(colon + 1)..].Trim();
            if (value.Length == 0)
            {
                fm[key] = new List<string>();
            }
            else if (value.StartsWith('[') && value.EndsWith(']'))
            {
                fm[key] = value[1..^1].Split(',')
                    .Select(x => x.Trim())
                    .Where(x => x.Length > 0)
                    .Select(x => x.Trim('\'', '"'))
                    .ToList();
            }
            else
            {
                fm[key] = value.Trim('\'', '"');
            }
        }
        return (fm, string.Join("\n", lines[(end.Value + 1)..]));
    }

    public static List<Entry> Entries(string root)
    {
        var dir = Path.Combine(root, "decisions");
        if (!Directory.Exists(dir)) return new List<Entry>();
        var list = Directory.GetFiles(dir, "ADR-*.md")
            .OrderBy(f => Relative(root, f), StringComparer.Ordinal)
            .Select(f =>
            {
                var (fm, body) = ParseFrontmatter(ReadText(f));
                return new Entry(Relative(root, f), Path.GetFileName(f), fm, body);
            })
            .ToList();
        return list.OrderBy(e => Str(e.Fm, "id") is { Length: > 0 } id ? id : e.File, StringComparer.Ordinal).ToList();
    }

    public sealed record Result(List<string> Issues, List<string> Warns, List<string> Projection,
        Dictionary<string, object?> Stats);

    public static Result Verify(string root)
    {
        var (issues, warns, stats) = Scan(root);
        var projection = CheckProjection(root, out var projectionIssues);
        issues.AddRange(projectionIssues);
        return new Result(issues, warns, projection, stats);
    }

    private static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var rows = Entries(root);
        if (rows.Count == 0)
        {
            return (new List<string> { $"未发现任何 ADR（{GlobPattern}）" }, warns,
                new Dictionary<string, object?>(StringComparer.Ordinal) { ["decisions"] = 0 });
        }

        var verifyPath = Path.Combine(root, "verify.sh");
        var verifyText = File.Exists(verifyPath) ? ReadText(verifyPath) : "";
        var checks = Regex.Matches(verifyText, @"(?m)^check(\d+)\(\)\{")
            .Select(m => m.Groups[1].Value).ToHashSet(StringComparer.Ordinal);
        var receipts = ReceiptIds(root);
        var hasReceipts = File.Exists(Path.Combine(root, ReceiptsRel));

        var ids = new Dictionary<string, string>(StringComparer.Ordinal);
        var supBy = new Dictionary<string, string>(StringComparer.Ordinal);

        foreach (var e in rows)
        {
            var did = Str(e.Fm, "id");
            var tag = did.Length > 0 ? did : e.File;
            if (did.Length == 0)
            {
                issues.Add($"{e.File} 缺 frontmatter id");
                continue;
            }
            if (!IdRe.IsMatch(did)) issues.Add($"{e.File} 的 id 不合法（须 ADR-四位数字）：{did}");

            var fileMatch = FileIdRe.Match(e.File);
            if (!fileMatch.Success || "ADR-" + fileMatch.Groups[1].Value != did)
                issues.Add($"{e.File} 的 id 与文件名不一致：{did}");

            if (ids.TryGetValue(did, out var previous))
                issues.Add($"ADR 编号重复：{did}（{previous} 与 {e.File}）");
            ids[did] = e.File;

            foreach (var field in new[] { "title", "status", "date", "evidence" })
            {
                if (IsFalsy(e.Fm.TryGetValue(field, out var v) ? v : null))
                    issues.Add($"{tag} 缺必填字段：{field}");
            }

            var status = Str(e.Fm, "status");
            if (status.Length > 0 && Array.IndexOf(Statuses, status) < 0)
                issues.Add($"{tag} 的 status 越词表：{status}（{string.Join("/", Statuses)}）");

            var date = Str(e.Fm, "date");
            if (date.Length > 0 && !DatedRe.IsMatch(date))
                issues.Add($"{tag} 的 date 非 YYYY-MM-DD：{date}");

            foreach (var section in Sections)
            {
                if (!e.Body.Contains(section, StringComparison.Ordinal))
                    issues.Add($"{tag} 正文缺段落：{section}");
            }

            foreach (var evidence in EvidenceItems(e.Fm))
            {
                var s = evidence.Trim();
                if (s.Length == 0) { issues.Add($"{tag} 的 evidence 有空项"); continue; }
                var checkMatch = CheckRe.Match(s);
                if (checkMatch.Success)
                {
                    if (!checks.Contains(checkMatch.Groups[1].Value))
                        issues.Add($"{tag} 的 evidence 指向不存在的 check：{s}");
                    continue;
                }
                if (AdrRe.IsMatch(s)) continue;   // 跨 ADR 引用在链检查里统一判
                var path = s.Replace('\\', '/');
                if (!File.Exists(Path.Combine(root, path)) && !Directory.Exists(Path.Combine(root, path)))
                {
                    issues.Add($"{tag} 的 evidence 无法解析：{s}（修复指引：改为真实件路径，或 checkN，或 ADR-N）");
                }
            }

            if (status == "accepted" && hasReceipts && !receipts.Contains(e.Path))
            {
                issues.Add($"{tag} 已 accepted 但未被协议回执锚定（修复指引：nf receipts --write）——未锚定的 accepted 等于可被偷改");
            }

            var supersededBy = Str(e.Fm, "superseded_by").Trim();
            if (status == "superseded" && Dashes.Contains(supersededBy))
                issues.Add($"{tag} 标 superseded 但缺 superseded_by");
            if (!Dashes.Contains(supersededBy)) supBy[did] = supersededBy;
        }

        foreach (var (did, target) in supBy)
        {
            if (!ids.ContainsKey(target))
            {
                issues.Add($"{did} 的 superseded_by 指向不在册编号：{target}");
                continue;
            }
            var current = target;
            var hops = 0;
            while (supBy.TryGetValue(current, out var next) && hops < supBy.Count + 1)
            {
                current = next;
                hops++;
                if (current == did)
                {
                    issues.Add($"取代链成环：{did} → … → {did}");
                    break;
                }
            }
        }

        foreach (var did in ids.Keys)
        {
            foreach (var other in rows)
            {
                if (Str(other.Fm, "id") != did) continue;
                var supersedes = Str(other.Fm, "supersedes").Trim();
                if (!Dashes.Contains(supersedes) && !ids.ContainsKey(supersedes))
                    issues.Add($"{did} 的 supersedes 指向不在册编号：{supersedes}");
            }
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["decisions"] = ids.Count,
            ["accepted"] = rows.Count(e => Str(e.Fm, "status") == "accepted"),
            ["chains"] = supBy.Count,
        };
        return (issues, warns, stats);
    }

    public static string RenderIndex(string root)
    {
        var output = new List<string>
        {
            Begin, "", "## 决策登记表（由各 ADR frontmatter 生成，勿手改）", "",
            "| 编号 | 标题 | 状态 | 日期 | 取代 |", "|---|---|---|---|---|",
        };
        foreach (var e in Entries(root))
        {
            var supersededBy = Str(e.Fm, "superseded_by");
            output.Add($"| {Value(e.Fm, "id", e.File)} | {Str(e.Fm, "title")} | {Str(e.Fm, "status")} | " +
                       $"{Str(e.Fm, "date")} | {(supersededBy.Length > 0 ? supersededBy : "—")} |");
        }
        output.Add("");
        output.Add("> 真源 = `decisions/ADR-*.md` 的 frontmatter；本表为投影（`nf decisions reindex` 重建）。");
        output.Add("");
        output.Add(End);
        return string.Join("\n", output);
    }

    private static List<string> CheckProjection(string root, out List<string> projectionIssues)
    {
        var path = Path.Combine(root, IndexRel);
        if (!File.Exists(path))
        {
            projectionIssues = new List<string> { $"缺 {IndexRel}（修复指引：nf decisions reindex）" };
            return new List<string>();
        }
        var text = ReadText(path);
        if (!text.Contains(Begin, StringComparison.Ordinal) || !text.Contains(End, StringComparison.Ordinal))
        {
            projectionIssues = new List<string> { $"{IndexRel} 缺生成区标记" };
            return new List<string>();
        }
        var start = text.IndexOf(Begin, StringComparison.Ordinal);
        var finish = text.IndexOf(End, StringComparison.Ordinal) + End.Length;
        var current = text[start..finish];
        if (current == RenderIndex(root))
        {
            projectionIssues = new List<string>();
            return new List<string>();
        }
        projectionIssues = new List<string> { "决策登记表与实时重算不一致（跑 nf decisions reindex）" };
        return new List<string>();
    }

    /// <summary>等价 Python：值非列表时按**字符串逐字符**迭代（历史语义，照搬以保证等价）。</summary>
    private static IEnumerable<string> EvidenceItems(Dictionary<string, object?> fm)
    {
        if (!fm.TryGetValue("evidence", out var value) || value is null) yield break;
        if (value is List<string> list)
        {
            foreach (var item in list) yield return item;
            yield break;
        }
        if (value is string text)
        {
            foreach (var ch in text) yield return ch.ToString();
        }
    }

    private static HashSet<string> ReceiptIds(string root)
    {
        var path = Path.Combine(root, ReceiptsRel);
        if (!File.Exists(path)) return new HashSet<string>(StringComparer.Ordinal);
        using var doc = JsonIo.ReadFile(path);
        var result = new HashSet<string>(StringComparer.Ordinal);
        if (doc.RootElement.TryGetProperty("entries", out var entries))
        {
            foreach (var entry in entries.EnumerateArray())
            {
                if (entry.TryGetProperty("id", out var id) && id.ValueKind == JsonValueKind.String)
                    result.Add(id.GetString()!);
            }
        }
        return result;
    }

    private static bool IsFalsy(object? value) => value switch
    {
        null => true,
        string s => s.Length == 0,
        List<string> l => l.Count == 0,
        _ => false,
    };

    private static string Str(Dictionary<string, object?> fm, string key)
        => fm.TryGetValue(key, out var v) && v is string s ? s : "";

    private static string Value(Dictionary<string, object?> fm, string key, string fallback)
        => fm.TryGetValue(key, out var v) && v is string s && s.Length > 0 ? s : fallback;

    private static string ReadText(string path)
        => new UTF8Encoding(false).GetString(File.ReadAllBytes(path));

    private static string Relative(string root, string full)
        => Path.GetRelativePath(root, full).Replace('\\', '/');
}
