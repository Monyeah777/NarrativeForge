using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/asset_ledger_projection.py</c> 的**只读校验面**：资产键表机读投影
/// （<c>protocol/community_asset_ledger.json</c>，"键 → 文件 → 行"的键条目级寻址）。
///
/// 键发现口径与 <c>asset_density</c> **故意不同**（各自照抄真源）：
/// 本件字符集 <c>[A-Z][A-Z0-9_]</c>（**无连字符**）· 取前 **8000 码点** · 标题键用 <c>^##…</c>（MULTILINE）。
/// 行号 = 该键在正文中**首次**以词边界出现的那一行（找不到 = 1）；行号搜索用 <c>\b&lt;key&gt;\b</c>。
///
/// <c>--refresh</c>（重生成 ledger）是写面，不属只读门；本件**不提供**。
/// </summary>
public static class AssetLedgerProjection
{
    public const string LedgerRel = "protocol/community_asset_ledger.json";
    public const string LedgerSchemaName = "community-asset-ledger/1";
    private const int KeyHeadCodePoints = 8000;

    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);
    private static readonly Regex StemKeyRe = new("[A-Z][A-Z0-9_]*", RegexOptions.CultureInvariant);
    private static readonly Regex BacktickKeyRe = new("`([A-Z][A-Z0-9_]{2,})`", RegexOptions.CultureInvariant);
    private static readonly Regex QuotedKeyRe = new("\"([A-Z][A-Z0-9_]{2,})\"\\s*:", RegexOptions.CultureInvariant);
    private static readonly Regex HeadingKeyRe =
        new("^##\\s*([A-Z][A-Z0-9_]{2,})", RegexOptions.Multiline | RegexOptions.CultureInvariant);

    /// <summary>键发现（投影口径）。<paramref name="text"/> 为 null = 读不到正文，只留文件名令牌。</summary>
    public static List<string> FileKeys(string name, string? text)
    {
        var keys = new HashSet<string>(StringComparer.Ordinal);
        foreach (Match m in StemKeyRe.Matches(AssetShelf.Stem(name))) keys.Add(m.Value);
        if (text is null) return keys.OrderBy(k => k, StringComparer.Ordinal).ToList();
        var head = PyScalar.PySlice(text, KeyHeadCodePoints);
        foreach (Match m in BacktickKeyRe.Matches(head)) keys.Add(m.Groups[1].Value);
        foreach (Match m in QuotedKeyRe.Matches(head)) keys.Add(m.Groups[1].Value);
        foreach (Match m in HeadingKeyRe.Matches(head)) keys.Add(m.Groups[1].Value);
        return keys.OrderBy(k => k, StringComparer.Ordinal).ToList();
    }

    /// <summary>重算投影行（<c>{key, package, file, line}</c>），按 <c>(package, key, file)</c> 全序。</summary>
    public static List<Dictionary<string, object?>> Build(string root)
    {
        var rows = new List<Dictionary<string, object?>>();
        foreach (var (rel, full) in AssetShelf.MarkdownFiles(root))
        {
            var name = Path.GetFileName(full);
            if (name == "README.md") continue;
            // 真源此处**不吞 OSError**（读不到即抛）；本件同向抛出，由 CLI 层收敛成受控失败。
            var text = StrictUtf8.GetString(File.ReadAllBytes(full));
            text = KnowledgeSig.Norm(text);
            var lines = KnowledgeSig.SplitLines(text);
            var pkg = rel.StartsWith("community", StringComparison.Ordinal) ? rel.Split('/')[1] : "官方";
            foreach (var key in FileKeys(name, text))
            {
                long line = 1;
                var re = new Regex("\\b" + Regex.Escape(key) + "\\b", RegexOptions.CultureInvariant);
                for (var idx = 0; idx < lines.Count; idx++)
                {
                    if (!re.IsMatch(lines[idx])) continue;
                    line = idx + 1;
                    break;
                }
                rows.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["key"] = key, ["package"] = pkg, ["file"] = rel, ["line"] = line,
                });
            }
        }
        return rows
            .OrderBy(r => (string)r["package"]!, StringComparer.Ordinal)
            .ThenBy(r => (string)r["key"]!, StringComparer.Ordinal)
            .ThenBy(r => (string)r["file"]!, StringComparer.Ordinal)
            .ToList();
    }

    /// <summary>校验投影与实时扫描一致（<c>nf asset ledger</c> 只读面）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Verify(string root)
    {
        var empty = new Dictionary<string, object?>(StringComparer.Ordinal);
        var path = Path.Combine(root, LedgerRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path))
            return (new List<string> { $"{LedgerRel} 缺失（refresh 生成）" }, empty);

        // 真源 json.loads 对坏 JSON 直接抛（未捕获）；本件同向抛出，由 CLI 层收敛成受控失败。
        using var doc = JsonDocument.Parse(StrictUtf8.GetString(File.ReadAllBytes(path)));
        var graph = PythonJson.ToGraph(doc.RootElement);
        var onDisk = graph is Dictionary<string, object?> map ? map.GetValueOrDefault("entries") : null;
        var current = Build(root).Cast<object?>().ToList();
        var issues = new List<string>();
        if (!PyDeepEqual(onDisk, current))
            issues.Add($"{LedgerRel} 过期：与资产扫描不一致（refresh）");
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["entries"] = (long)current.Count,
        });
    }

    /// <summary>Python 值相等（含 <c>1 == 1.0</c>、<c>True == 1</c>）；字典比键集与值，列表按序。</summary>
    internal static bool PyDeepEqual(object? a, object? b)
    {
        if (a is null || b is null) return a is null && b is null;
        if (a is bool || b is bool)
            return NumOf(a) is { } na && NumOf(b) is { } nb && na == nb;
        if (NumOf(a) is { } da && NumOf(b) is { } db) return da == db;
        if (a is string sa && b is string sb) return sa == sb;
        if (a is Dictionary<string, object?> ma && b is Dictionary<string, object?> mb)
        {
            if (ma.Count != mb.Count) return false;
            foreach (var kv in ma)
                if (!mb.TryGetValue(kv.Key, out var other) || !PyDeepEqual(kv.Value, other)) return false;
            return true;
        }
        if (a is List<object?> la && b is List<object?> lb)
        {
            if (la.Count != lb.Count) return false;
            for (var i = 0; i < la.Count; i++)
                if (!PyDeepEqual(la[i], lb[i])) return false;
            return true;
        }
        return false;
    }

    private static double? NumOf(object? v) => v switch
    {
        bool b => b ? 1 : 0,
        long l => l,
        int i => i,
        double d => d,
        _ => null,
    };
}
