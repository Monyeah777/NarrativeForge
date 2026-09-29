using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/asset_density.py</c>（45 W2）的只读三面：
/// <list type="bullet">
/// <item><c>density</c>：资产键语义密度（键数 / 字符数 / 无键档 / 短档）——FAIL 面只留"空档 / 不可读"；</item>
/// <item><c>usage</c>：资产键在 04/community/docs 全语料的引用度（零引用清单**只报告不删**，<c>--strict</c> 才进门禁）；</item>
/// <item><c>thickness</c>：每档 字符 / 键 / 小节 / 表格行 与低信息档候选（只报告，issues 恒空）。</item>
/// </list>
///
/// 键发现口径（三面共用）= 文件名令牌 <c>[A-Z][A-Z0-9_]*</c> ∪ 正文键声明
/// （<c>`KEY`</c> / <c>"KEY":</c> / <c>## KEY</c>，字符集含**带连字符的条目键**）· 只取前 **6000 码点**。
/// 注意 <c>_keys_of</c> 的字符集与键表投影 <c>_file_keys</c> **故意不同**（后者无连字符、取 8000），两处各自照抄。
/// </summary>
public static class AssetDensity
{
    private const int KeyHeadCodePoints = 6000;

    private static readonly Regex StemKeyRe = new("[A-Z][A-Z0-9_]*", RegexOptions.CultureInvariant);
    private static readonly Regex BacktickKeyRe = new("`([A-Z][A-Z0-9_-]{2,})`", RegexOptions.CultureInvariant);
    private static readonly Regex QuotedKeyRe = new("\"([A-Z][A-Z0-9_-]{2,})\"\\s*:", RegexOptions.CultureInvariant);
    private static readonly Regex HeadingKeyRe = new("##\\s*([A-Z][A-Z0-9_-]{2,})", RegexOptions.CultureInvariant);
    private static readonly Regex SectionRe = new("^#{1,3}\\s", RegexOptions.CultureInvariant);

    /// <summary>键发现（density / usage / thickness 同口径）。<paramref name="text"/> 为 null = 读不到正文，只留文件名令牌。</summary>
    public static List<string> KeysOf(string name, string? text)
    {
        var keys = new HashSet<string>(StringComparer.Ordinal);
        foreach (Match m in StemKeyRe.Matches(AssetShelf.Stem(name))) keys.Add(m.Value);
        if (text is null) return Sorted(keys);
        var head = PyScalar.PySlice(text, KeyHeadCodePoints);
        AddGroup(keys, BacktickKeyRe, head);
        AddGroup(keys, QuotedKeyRe, head);
        AddGroup(keys, HeadingKeyRe, head);
        return Sorted(keys);
    }

    /// <summary>密度体检：键数 / 字符数 / 无键档 / 短档。issues = 空档与不可读（真异常）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var rows = new List<(string Package, int Keys, int Chars)>();
        foreach (var (rel, full) in AssetShelf.MarkdownFiles(root))
        {
            var name = Path.GetFileName(full);
            if (name == "README.md") continue;
            if (!AssetShelf.TryReadText(full, out var text))
            {
                // **跟随真源 5449824 的文案变更**：空档 / 不可读两处提示由**绝对路径**改为
                // **root 相对 posix 路径**（真源 asset_density.py 的 scan 段同步改动）。
                // 判据按逐字节比，故引擎必须同形；`rel` 即 `AssetShelf.MarkdownFiles` 给出的相对路径。
                issues.Add($"{rel} 不可读：文件不可读（只读门：无权限或路径异常）");
                continue;
            }
            if (AssetShelf.PyStrip(text).Length == 0)
            {
                issues.Add($"{rel} 为空档（0 字符）");
                continue;
            }
            rows.Add((PackageOf(rel), KeysOf(name, text).Count, PyScalar.PyLen(text)));
        }
        var nFiles = rows.Count;
        var nKeys = rows.Sum(r => r.Keys);
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["files"] = (long)nFiles,
            ["keys"] = (long)nKeys,
            ["unkeyed"] = (long)rows.Count(r => r.Keys == 0),
            ["tiny"] = (long)rows.Count(r => r.Chars < 200),
            ["avg_keys_per_file"] = Math.Round((double)nKeys / Math.Max(1, nFiles), 2),
        };
        return (issues, stats);
    }

    /// <summary>引用度体检：键在 04/community/docs 全语料的引用次数与零引用清单。issues 恒空（纯统计）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) UsageScan(string root)
    {
        var keys = new List<string>();
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var (_rel, full) in AssetShelf.MarkdownFiles(root))
        {
            var name = Path.GetFileName(full);
            if (name == "README.md") continue;
            // 真源此处**不吞异常**：读不到时 _keys_of 内部退化为"只文件名令牌"，故照样出键。
            var ok = AssetShelf.TryReadText(full, out var text);
            foreach (var k in KeysOf(name, ok ? text : null))
                if (seen.Add(k)) keys.Add(k);
        }

        var corpus = new List<string>();
        foreach (var baseDir in new[] { "04_模块库", "community", "docs" })
        {
            var dir = Path.Combine(root, baseDir);
            if (!Directory.Exists(dir)) continue;
            foreach (var full in Directory.EnumerateFiles(dir, "*", SearchOption.AllDirectories)
                         .OrderBy(f => f, StringComparer.Ordinal))
            {
                if (!Path.GetFileName(full).EndsWith(".md", AssetShelf.NameComparison)) continue;
                if (AssetShelf.TryReadText(full, out var text)) corpus.Add(text);
            }
        }
        var blob = string.Join("\n", corpus);

        long totalRefs = 0;
        var zero = new List<string>();
        foreach (var k in keys)
        {
            var n = AssetShelf.CountNonOverlapping(blob, k);
            totalRefs += n;
            if (n == 0) zero.Add(k);
        }
        zero.Sort(StringComparer.Ordinal);
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["assets"] = (long)keys.Count,
            ["zero_usage"] = (long)zero.Count,
            ["used"] = (long)(keys.Count - zero.Count),
            ["total_refs"] = totalRefs,
            ["zero_keys"] = zero.Cast<object?>().ToList(),
        };
        return (new List<string>(), stats);
    }

    /// <summary>语义厚度：字符 / 键 / 小节 / 表格行 与低信息档候选（只报告不删，issues 恒空）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) ThicknessScan(string root)
    {
        var rows = new List<(string File, int Chars, int Keys, int Sections, bool Low)>();
        foreach (var (rel, full) in AssetShelf.MarkdownFiles(root))
        {
            var name = Path.GetFileName(full);
            if (name == "README.md") continue;
            if (!AssetShelf.TryReadText(full, out var text)) continue;
            if (AssetShelf.PyStrip(text).Length == 0) continue;
            var keys = KeysOf(name, text).Count;
            var lines = KnowledgeSig.SplitLines(text);
            var sections = lines.Count(ln => SectionRe.IsMatch(ln));
            var chars = PyScalar.PyLen(text);
            var low = chars < 200 || (keys == 0 && sections == 0);
            rows.Add((rel, chars, keys, sections, low));
        }
        var lowFiles = rows.Where(r => r.Low).Select(r => r.File).OrderBy(f => f, StringComparer.Ordinal).ToList();
        var n = rows.Count;
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["files"] = (long)n,
            ["low_info"] = (long)lowFiles.Count,
            ["low_files"] = lowFiles.Cast<object?>().ToList(),
            ["avg_chars"] = (long)Math.Round((double)rows.Sum(r => r.Chars) / Math.Max(1, n)),
            ["avg_sections"] = (long)Math.Round((double)rows.Sum(r => r.Sections) / Math.Max(1, n)),
        };
        return (new List<string>(), stats);
    }

    private static string PackageOf(string relPosix) =>
        relPosix.StartsWith("community", StringComparison.Ordinal) ? relPosix.Split('/')[1] : "官方";

    private static void AddGroup(HashSet<string> keys, Regex re, string head)
    {
        foreach (Match m in re.Matches(head)) keys.Add(m.Groups[1].Value);
    }

    private static List<string> Sorted(HashSet<string> keys) =>
        keys.OrderBy(k => k, StringComparer.Ordinal).ToList();
}
