using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/module_lifecycle.py</c>（v2.8 波B S5）：模块生命周期只读面——
/// <c>ls</c>（状态清单）· <c>status</c>（单件状态位）· <c>verify</c>（**check24 同语义**：
/// deprecated / retired 模块不得被其它模块（依赖/被依赖/订阅）或 community <c>protocol.yaml</c> 引用）。
///
/// 状态存放 = 模块文件**元信息行**（<c>&gt; 类别：…｜…｜状态：deprecated（原因：…）</c>），缺省视作 active。
/// 写面（<c>deprecate</c> / <c>restore</c>）不属只读门。
/// </summary>
public static class ModuleLifecycle
{
    public static readonly string[] Statuses = { "active", "deprecated", "retired" };
    public const string DefaultStatus = "active";
    private const string Tag = "状态";

    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);
    private static readonly Regex TitleRe = new(@"#\s*模块\s*([\u4e00-\u9fffA-Za-z]+:)?(M?\d+)\s*[·.、\-]?\s*(.*)", RegexOptions.CultureInvariant);
    private static readonly Regex MetaSep = new("[｜|]", RegexOptions.CultureInvariant);
    private static readonly string[] RefKeys = { "依赖", "被依赖", "订阅" };
    private static readonly Regex IdNum = new(@"M(\d{2,3})$", RegexOptions.CultureInvariant);
    private static readonly Regex ProtocolNum = new(@"M(\d{2,3})", RegexOptions.CultureInvariant);

    /// <summary>相对 root 的模块 md 路径（<c>04_模块库/*/*.md</c> + <c>community/*/modules/*.md</c>）。</summary>
    public static List<string> IterModuleFiles(string root)
    {
        var output = new List<string>();
        foreach (var (pattern, full) in new (string, IEnumerable<string>)[]
                 {
                     ("04_模块库", Enumerate(root, "04_模块库", recurse: false)),
                     ("community", EnumerateCommunityModules(root)),
                 })
        {
            _ = pattern;
            foreach (var f in full.OrderBy(x => x, StringComparer.Ordinal))
            {
                var name = Path.GetFileName(f);
                if (name.StartsWith("README", StringComparison.Ordinal)
                    || name.StartsWith("readme", StringComparison.Ordinal)
                    || name.StartsWith("_", StringComparison.Ordinal)) continue;
                if (!name.EndsWith(".md", AssetShelf.NameComparison)) continue;
                output.Add(Path.GetRelativePath(root, f).Replace('\\', '/'));
            }
        }
        return output;
    }

    /// <summary>`04_模块库/&lt;类&gt;/*.md`（一层）。</summary>
    private static IEnumerable<string> Enumerate(string root, string sub, bool recurse)
    {
        var baseDir = Path.Combine(root, sub);
        if (!Directory.Exists(baseDir)) return Array.Empty<string>();
        return Directory.GetFiles(baseDir, "*", recurse ? SearchOption.AllDirectories : SearchOption.AllDirectories)
            .Where(f => Path.GetRelativePath(baseDir, f).Split(Path.DirectorySeparatorChar).Length == 2);
    }

    /// <summary>`community/&lt;包&gt;/modules/*.md`（一层）。</summary>
    private static IEnumerable<string> EnumerateCommunityModules(string root)
    {
        var community = Path.Combine(root, "community");
        if (!Directory.Exists(community)) return Array.Empty<string>();
        var output = new List<string>();
        foreach (var pkg in Directory.GetDirectories(community))
        {
            var modules = Path.Combine(pkg, "modules");
            if (Directory.Exists(modules)) output.AddRange(Directory.GetFiles(modules));
        }
        return output;
    }

    public static string ReadText(string root, string rel) =>
        KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(
            Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)))));

    /// <summary>一条 <c>&gt; …</c> 元信息内容 → key→value（以 <c>|</c> 或 <c>｜</c> 分隔）。</summary>
    private static Dictionary<string, string> MetaPairs(string lineBody)
    {
        var output = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var seg in MetaSep.Split(lineBody))
        {
            var kv = Regex.Split(seg, "[:：]", RegexOptions.CultureInvariant);
            if (kv.Length >= 2 && kv[0].Trim().Length > 0)
                output[kv[0].Trim()] = string.Join(":", kv.Skip(1)).Trim();
        }
        return output;
    }

    /// <summary>聚合全文 <c>&gt;</c> 元信息行（重复键后者覆盖）。</summary>
    public static Dictionary<string, string> ParseMeta(string text)
    {
        var output = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var line in KnowledgeSig.SplitLines(text))
        {
            var s = line.Trim();
            if (!s.StartsWith(">", StringComparison.Ordinal)) continue;
            foreach (var (k, v) in MetaPairs(s[1..].Trim())) output[k] = v;
        }
        return output;
    }

    public static string ModuleIdFromText(string text)
    {
        foreach (var line in KnowledgeSig.SplitLines(text))
        {
            var s = line.Trim();
            if (!s.StartsWith("# 模块", StringComparison.Ordinal)) continue;
            var m = TitleRe.Match(s);
            if (!m.Success) continue;
            var num = m.Groups[2].Value.TrimStart('M').PadLeft(2, '0');
            return m.Groups[1].Success
                ? $"{m.Groups[1].Value.TrimEnd(':')}:M{num}"
                : $"M{num}";
        }
        return "";
    }

    /// <summary>→ (status, reason)；状态不在词表即视作 active（真源口径）。</summary>
    public static (string Status, string Reason) GetStatus(string text)
    {
        var meta = ParseMeta(text);
        var raw = (meta.GetValueOrDefault(Tag) ?? DefaultStatus).Trim();
        var body = raw.Contains('（') ? raw.Split('（', 2)[0].Trim() : raw;
        body = body.ToLowerInvariant();
        if (!Statuses.Contains(body)) return (DefaultStatus, "");
        var m = Regex.Match(raw, "[（(](.*?)[)）]", RegexOptions.CultureInvariant);
        return (body, m.Success ? m.Groups[1].Value.Trim() : "");
    }

    /// <summary>模块头 依赖/被依赖/订阅 的 id 集合。</summary>
    public static HashSet<string> ParseRefs(Dictionary<string, string> meta)
    {
        var refs = new HashSet<string>(StringComparer.Ordinal);
        foreach (var key in RefKeys)
            foreach (var tok in Regex.Split(meta.GetValueOrDefault(key) ?? "", "[、,，;\\s]+"))
            {
                var t = tok.Trim();
                if (t.Length == 0 || Regex.IsMatch(t, "^[（(].*[)）]$")) continue;
                refs.Add(t);
            }
        return refs;
    }

    /// <summary>community <c>protocol.yaml</c> 里出现的模块 id 词频（同一号可多次出现）。</summary>
    private static Dictionary<string, List<string>> ProtocolIds(string root)
    {
        var hits = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        var community = Path.Combine(root, "community");
        if (!Directory.Exists(community)) return hits;
        foreach (var pkg in Directory.GetDirectories(community))
        {
            var path = Path.Combine(pkg, "protocol.yaml");
            if (!File.Exists(path)) continue;
            string text;
            try
            {
                text = KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(path)));
            }
            catch (Exception exc) when (exc is IOException or UnauthorizedAccessException)
            {
                continue;
            }
            var rel = Path.GetRelativePath(root, path).Replace('\\', '/');
            foreach (Match m in ProtocolNum.Matches(text))
            {
                var key = "M" + m.Groups[1].Value;
                if (!hits.TryGetValue(key, out var list)) hits[key] = list = new List<string>();
                list.Add(rel);
            }
        }
        return hits;
    }

    private sealed record Info(string Status, string File, HashSet<string> Refs, string Id);

    private static (Dictionary<string, Info> Infos, long Modules, Dictionary<string, long> Counts,
        Dictionary<string, List<string>> NumIds) CollectInfos(string root)
    {
        var infos = new Dictionary<string, Info>(StringComparer.Ordinal);
        var counts = new Dictionary<string, long>(StringComparer.Ordinal) { ["modules"] = 0 };
        var numIds = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var rel in IterModuleFiles(root))
        {
            var text = ReadText(root, rel);
            var mid = ModuleIdFromText(text);
            var (status, _) = GetStatus(text);
            var refs = ParseRefs(ParseMeta(text));
            counts["modules"]++;
            counts[status] = counts.GetValueOrDefault(status) + 1;
            var key = mid.Length > 0 ? mid : rel;
            infos[key] = new Info(status, rel, refs, mid);
            var n = NumOf(key);
            if (n.Length > 0)
            {
                if (!numIds.TryGetValue(n, out var list)) numIds[n] = list = new List<string>();
                list.Add(key);
            }
        }
        return (infos, counts["modules"], counts, numIds);
    }

    private static string NumOf(string moduleId)
    {
        var m = IdNum.Match(moduleId);
        return m.Success ? m.Groups[1].Value : "";
    }

    /// <summary>引用方清单（模块文件 + protocol 文本命中）。</summary>
    private static List<string> IsReferenced(string targetId, Dictionary<string, Info> infos,
        Dictionary<string, List<string>> numIds, Dictionary<string, List<string>> protocolHits)
    {
        var output = new List<string>();
        var tnum = NumOf(targetId);
        var numericUnique = tnum.Length == 0 || numIds.GetValueOrDefault(tnum)?.Count == 1;
        foreach (var (key, info) in infos)
        {
            if (key == targetId) continue;
            foreach (var r in info.Refs)
            {
                if (r == targetId) output.Add($"{info.File}(依赖引用)");
                else if (!r.Contains(':') && !targetId.Contains(':') && r == targetId)
                    output.Add($"{info.File}(依赖引用)");
                else if (!r.Contains(':') && !numericUnique && r == (tnum.Length > 0 ? "M" + tnum : r))
                {
                    // 裸号 + 目标编号与其它模块撞号：不能断定指向本模块，跳过
                }
            }
        }
        if (tnum.Length > 0)
            foreach (var p in protocolHits.GetValueOrDefault(tnum) ?? new List<string>())
                output.Add($"{p}(protocol 出现)");
        return output.Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToList();
    }

    /// <summary>check24 语义：扫描全部模块状态；deprecated/retired 被引用 → FAIL。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) VerifyModules(string root)
    {
        var issues = new List<string>();
        var (infos, modules, counts, numIds) = CollectInfos(root);
        var protocol = ProtocolIds(root);
        foreach (var (key, info) in infos)
        {
            if (info.Status is not ("deprecated" or "retired")) continue;
            var refs = IsReferenced(info.Id.Length > 0 ? info.Id : key, infos, numIds, protocol);
            if (refs.Count > 0)
                issues.Add($"{info.File} 状态={info.Status} 但仍被引用：{string.Join("；", refs)}");
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["modules"] = modules,
            ["active"] = counts.GetValueOrDefault("active"),
            ["deprecated"] = counts.GetValueOrDefault("deprecated"),
            ["retired"] = counts.GetValueOrDefault("retired"),
        });
    }

    /// <summary><c>module ls</c> 的行（**保持扫描序**；JSON 面另按 (status,file) 排序）。</summary>
    public static List<(string Status, string File)> Rows(string root, string statusFilter = "")
    {
        var rows = new List<(string, string)>();
        foreach (var rel in IterModuleFiles(root))
        {
            var (status, _) = GetStatus(ReadText(root, rel));
            if (statusFilter.Length > 0 && status != statusFilter) continue;
            rows.Add((status, rel));
        }
        return rows;
    }
}
