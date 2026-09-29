using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/patterns.py</c>：**实践包（pattern）品类**——frontmatter 为真源、
/// <c>patterns/INDEX.md</c> 为投影；可证性要求 <c>applies_to</c> 指向仓库内真实件。
///
/// 与 Python 侧同口径的三条判据：必填字段 / 可证（applies_to 与 evidence 可解析）/ 投影一致。
/// 文本一律按 **严格 UTF-8** 解码（Python <c>read_text(encoding="utf-8")</c> 语义）——
/// 解码失败即抛，由调用方按「契约执行异常」处理，不静默替换字符。
/// </summary>
public static class Patterns
{
    public const string EntryGlob = "patterns/*/PATTERN.md";
    public const string IndexRel = "patterns/INDEX.md";
    public const string BeginMarker = "<!-- BEGIN GENERATED: patterns-index -->";
    public const string EndMarker = "<!-- END GENERATED: patterns-index -->";

    private static readonly string[] Required = { "id", "name", "status", "scope", "applies_to", "rules" };
    private static readonly string[] Statuses = { "active", "deprecated" };
    private static readonly Regex CheckRe = new(@"^check\d+$", RegexOptions.CultureInvariant);
    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public sealed record Entry(string Dir, string Path, Dictionary<string, object?> Fm);

    /// <summary>全量 pattern 包（先按仓库相对路径排、再按 id/目录名稳定排序——同 Python 的两次排序）。</summary>
    public static List<Entry> Entries(string root)
    {
        var rows = new List<Entry>();
        var dir = System.IO.Path.Combine(root, "patterns");
        if (!Directory.Exists(dir)) return rows;
        foreach (var file in Directory.GetDirectories(dir)
                     .Select(d => System.IO.Path.Combine(d, "PATTERN.md"))
                     .Where(File.Exists)
                     .OrderBy(f => Rel(root, f), StringComparer.Ordinal))
        {
            var (fm, _) = Decisions.ParseFrontmatter(StrictUtf8.GetString(File.ReadAllBytes(file)));
            rows.Add(new Entry(System.IO.Path.GetFileName(System.IO.Path.GetDirectoryName(file)!)!,
                Rel(root, file), fm));
        }
        return rows.OrderBy(e => IdOrDir(e), StringComparer.Ordinal).ToList();
    }

    private static string IdOrDir(Entry e) => Str(e.Fm, "id") is { Length: > 0 } id ? id : e.Dir;

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var rows = Entries(root);
        if (rows.Count == 0)
        {
            issues.Add($"未发现任何 pattern 包（{EntryGlob}）");
            return (issues, warns, new Dictionary<string, object?>(StringComparer.Ordinal) { ["patterns"] = 0 });
        }

        var seen = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var e in rows)
        {
            var fm = e.Fm;
            var d = e.Dir;
            if (fm.Count == 0)
            {
                issues.Add($"{d} 缺 frontmatter（修复指引：见 patterns/README.md）");
                continue;
            }
            foreach (var key in Required)
            {
                var raw = fm.TryGetValue(key, out var v) ? v : null;
                // Python：`not (fm.get(k) or fm.get(k) == [])` —— 缺失与空串算缺，空列表不算
                if (IsFalsy(raw) && raw is not List<string> { Count: 0 })
                    issues.Add($"{d} 缺必填字段：{key}");
            }

            var pid = Str(fm, "id");
            if (pid.Length > 0 && pid != d)
                issues.Add($"{d} 的 id 与目录名不一致：{pid} vs {d}");
            if (pid.Length > 0)
            {
                if (seen.TryGetValue(pid, out var prev))
                    issues.Add($"pattern id 重复：{pid}（{prev} / {d}）");
                seen[pid] = d;
            }

            var status = Str(fm, "status");
            if (status.Length > 0 && Array.IndexOf(Statuses, status) < 0)
                issues.Add($"{d} status 越词表：{status}（{string.Join("/", Statuses)}）");

            if (AsList(fm.TryGetValue("rules", out var rv) ? rv : null).Count == 0)
                issues.Add($"{d} 的 rules 为空（pattern 必须有可执行规则）");

            foreach (var raw in AsList(fm.TryGetValue("applies_to", out var av) ? av : null))
            {
                var pattern = raw.Trim();
                if (pattern.Any(ch => ch is '*' or '?' or '['))
                {
                    if (!GlobHasHit(root, pattern))
                        issues.Add($"{d} 的 applies_to 通配无匹配：{pattern}（修复指引：指向仓库内真实文件）");
                }
                else if (!Exists(root, pattern))
                {
                    issues.Add($"{d} 的 applies_to 路径不存在：{pattern}");
                }
            }

            var evidence = AsList(fm.TryGetValue("evidence", out var ev) ? ev : null);
            if (evidence.Count == 0)
                warns.Add($"{d} 缺 evidence（可证性弱：无法回溯规则来源）");
            foreach (var raw in evidence)
            {
                var s = raw.Trim();
                if (CheckRe.IsMatch(s) || s.StartsWith("docs/", StringComparison.Ordinal)
                    || s.StartsWith("desktop/", StringComparison.Ordinal)
                    || s.StartsWith("protocol/", StringComparison.Ordinal)
                    || s.StartsWith("library/", StringComparison.Ordinal))
                {
                    if (CheckRe.IsMatch(s)) continue;
                    if (!Exists(root, s)) warns.Add($"{d} 的 evidence 指向不存在的件：{s}");
                }
                else if (s.Length == 0)
                {
                    warns.Add($"{d} 的 evidence 有空项");
                }
            }
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["patterns"] = rows.Count,
            ["ids"] = seen.Keys.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
        };
        return (issues, warns, stats);
    }

    /// <summary>投影块实时重算（真源 = 各包 frontmatter）。</summary>
    public static string RenderIndex(string root)
    {
        var output = new List<string>
        {
            BeginMarker, "", "## Pattern 登记表（由各包 frontmatter 生成，勿手改）", "",
            "| id | 名称 | 状态 | 适用面 | 规则数 |", "|---|---|---|---|---|",
        };
        foreach (var e in Entries(root))
        {
            var fm = e.Fm;
            var scope = AsList(fm.TryGetValue("scope", out var sv) ? sv : null);
            var rules = AsList(fm.TryGetValue("rules", out var rv) ? rv : null);
            output.Add($"| {PyStr(Value(fm, "id") ?? e.Dir)} | {PyStr(Value(fm, "name") ?? "")} | " +
                       $"{PyStr(Value(fm, "status") ?? "")} | {string.Join("、", scope.Take(2))} | {rules.Count} |");
        }
        output.Add("");
        output.Add("> 真源 = 各包 `PATTERN.md` 的 frontmatter；本表为投影（`nf patterns reindex` 重建）。");
        output.Add("");
        output.Add(EndMarker);
        return string.Join("\n", output);
    }

    /// <summary>在盘 INDEX.md 的生成区 == 实时重算？</summary>
    public static List<string> CheckProjection(string root)
    {
        var path = System.IO.Path.Combine(root, IndexRel);
        if (!File.Exists(path)) return new List<string> { $"缺 {IndexRel}（修复指引：nf patterns reindex）" };
        var text = StrictUtf8.GetString(File.ReadAllBytes(path));
        var begin = text.IndexOf(BeginMarker, StringComparison.Ordinal);
        var end = text.IndexOf(EndMarker, StringComparison.Ordinal);
        if (begin < 0 || end < 0) return new List<string> { $"{IndexRel} 缺生成区标记" };
        var current = text[begin..(end + EndMarker.Length)];
        return current == RenderIndex(root)
            ? new List<string>()
            : new List<string> { "patterns 登记表与实时重算不一致（跑 nf patterns reindex）" };
    }

    /// <summary>
    /// 复刻 <c>core/patterns.py::for_path</c>——**可消费面的核心**：某文件适用哪些 pattern。
    /// 两条匹配语义严格分开：含通配符的走 <c>fnmatch</c>（<c>*</c> 跨目录、Windows 下大小写不敏感），
    /// 不含通配符的走「等值 or 目录前缀」。
    /// </summary>
    public static List<Dictionary<string, object?>> ForPath(string root, string target)
    {
        var hits = new List<Dictionary<string, object?>>();
        var t = target.Replace('\\', '/');
        foreach (var e in Entries(root))
        {
            foreach (var raw in AsList(Value(e.Fm, "applies_to")))
            {
                var p = raw.Trim().Replace('\\', '/');
                var wildcard = p.IndexOfAny(new[] { '*', '?', '[' }) >= 0;
                var matched = wildcard
                    ? Fnmatch(t, p)
                    : t == p || t.StartsWith(p.TrimEnd('/') + "/", StringComparison.Ordinal);
                if (!matched) continue;
                hits.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["id"] = IdOrDir(e),
                    ["name"] = Str(e.Fm, "name"),
                    ["matched"] = p,
                });
                break;
            }
        }
        return hits;
    }

    /// <summary>
    /// Python <c>fnmatch.fnmatch</c> 的等价实现：两侧先过 <c>os.path.normcase</c>
    /// （Windows 下把 <c>/</c> 换成 <c>\</c> 并转小写，故 Windows 上大小写不敏感——与真源同平台同口径）。
    /// </summary>
    private static bool Fnmatch(string name, string pattern)
        => Regex.IsMatch(NormCase(name), FnmatchTranslate(NormCase(pattern)), RegexOptions.Singleline);

    private static string NormCase(string s)
        => OperatingSystem.IsWindows() ? s.Replace('/', '\\').ToLowerInvariant() : s;

    /// <summary>Python <c>fnmatch.translate</c> 的子集：<c>*</c> 跨目录、<c>?</c> 单字符、<c>[!…]</c> 取反。</summary>
    private static string FnmatchTranslate(string pat)
    {
        var sb = new StringBuilder("(?s:");
        var i = 0;
        while (i < pat.Length)
        {
            var c = pat[i++];
            if (c == '*')
            {
                sb.Append(".*");
            }
            else if (c == '?')
            {
                sb.Append('.');
            }
            else if (c == '[')
            {
                var j = i;
                if (j < pat.Length && (pat[j] == '!' || pat[j] == '^')) j++;
                if (j < pat.Length && pat[j] == ']') j++;
                while (j < pat.Length && pat[j] != ']') j++;
                if (j >= pat.Length)
                {
                    sb.Append("\\[");
                }
                else
                {
                    var stuff = pat[i..j].Replace("\\", "\\\\");
                    i = j + 1;
                    if (stuff.StartsWith('!')) stuff = "^" + stuff[1..];
                    else if (stuff.StartsWith('^')) stuff = "\\" + stuff;
                    sb.Append('[').Append(stuff).Append(']');
                }
            }
            else
            {
                sb.Append(Regex.Escape(c.ToString()));
            }
        }
        sb.Append(")\\Z");
        return sb.ToString();
    }

    // ------------------------------------------------------------------ 工具

    private static object? Value(Dictionary<string, object?> fm, string key)
        => fm.TryGetValue(key, out var v) ? v : null;

    private static string Str(Dictionary<string, object?> fm, string key)
        => fm.TryGetValue(key, out var v) && v is string s ? s : "";

    private static bool IsFalsy(object? v) => v switch
    {
        null => true,
        string s => s.Length == 0,
        List<string> l => l.Count == 0,
        _ => false,
    };

    /// <summary>等价 Python <c>_as_list</c>：列表原样、非空标量包成单元素、空值 → 空表。</summary>
    private static List<string> AsList(object? v) => v switch
    {
        List<string> list => list.Select(x => x).ToList(),
        string s => s.Length > 0 ? new List<string> { s } : new List<string>(),
        null => new List<string>(),
        _ => new List<string> { PyStr(v) },
    };

    /// <summary>近似 Python <c>"%s"</c> 的渲染：字符串原样，列表用 Python repr 形态。</summary>
    private static string PyStr(object? v) => v switch
    {
        null => "None",
        string s => s,
        List<string> list => "[" + string.Join(", ", list.Select(x => "'" + x + "'")) + "]",
        _ => v.ToString() ?? "",
    };

    private static bool Exists(string root, string rel)
        => File.Exists(System.IO.Path.Combine(root, rel))
           || Directory.Exists(System.IO.Path.Combine(root, rel));

    /// <summary>等价 <c>glob.glob(os.path.join(root, pat), recursive=True)</c> 的「是否有匹配」判断题。</summary>
    private static bool GlobHasHit(string root, string pattern)
    {
        var regex = GlobToRegex(pattern.Replace('\\', '/'));
        foreach (var entry in Directory.EnumerateFileSystemEntries(root, "*", SearchOption.AllDirectories))
        {
            if (regex.IsMatch(Rel(root, entry))) return true;
        }
        return false;
    }

    /// <summary>glob → 正则（相对 posix 路径）：<c>**</c> 跨目录、<c>*</c> 不跨、<c>?</c> 单字符、字符类透传。</summary>
    private static Regex GlobToRegex(string pattern)
    {
        var sb = new StringBuilder("^");
        var i = 0;
        while (i < pattern.Length)
        {
            var ch = pattern[i];
            if (ch == '*')
            {
                if (i + 1 < pattern.Length && pattern[i + 1] == '*')
                {
                    var trailingSlash = i + 2 < pattern.Length && pattern[i + 2] == '/';
                    sb.Append(trailingSlash ? "(?:.*/)?" : ".*");
                    i += trailingSlash ? 3 : 2;
                    continue;
                }
                sb.Append("[^/]*");
                i++;
                continue;
            }
            if (ch == '?') { sb.Append("[^/]"); i++; continue; }
            if (ch == '[')
            {
                var close = pattern.IndexOf(']', i + 1);
                if (close > 0)
                {
                    var body = pattern[(i + 1)..close];
                    sb.Append('[').Append(body.StartsWith('!') ? "^" + body[1..] : body).Append(']');
                    i = close + 1;
                    continue;
                }
            }
            sb.Append(Regex.Escape(ch.ToString()));
            i++;
        }
        sb.Append('$');
        return new Regex(sb.ToString(), RegexOptions.CultureInvariant);
    }

    private static string Rel(string root, string full)
        => System.IO.Path.GetRelativePath(root, full).Replace('\\', '/');
}
