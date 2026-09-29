using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/rfc.py</c>：协议件的**版本史头**（RFC 编号 / Category / Date / Status /
/// Supersedes / Superseded by）——文档头部为真源，<c>protocol/rfc_index.json</c> 为机读投影并逐条比对。
///
/// 判据：头齐备 + 编号在册唯一 + Category/Status 在词表 + Date 与「最后更新」自洽 +
/// Superseded 须给取代者 + 取代链可解析且不成环。
/// </summary>
public static class Rfc
{
    public const string IndexRel = "protocol/rfc_index.json";
    public const string FallbackStatus = "Active";

    private static readonly string[] Categories =
        { "Standards Track", "Informational", "Experimental", "Process" };

    private static readonly Regex HeadRe = new(
        @"\*\*RFC\*\*:\s*(?<rfc>NF-\d{4})\s*·\s*\*\*Category\*\*:\s*(?<cat>[^·]+?)\s*·\s*" +
        @"\*\*Date\*\*:\s*(?<date>[\d-]+)\s*·\s*\*\*Status\*\*:\s*(?<status>[^·]+?)\s*·\s*" +
        @"\*\*Supersedes\*\*:\s*(?<sup>[^·]+?)\s*·\s*\*\*Superseded by\*\*:\s*(?<supby>[^·\n]+)",
        RegexOptions.CultureInvariant);

    private static readonly Regex LastUpdatedRe = new(@">\s*最后更新：\s*([\d-]+)", RegexOptions.CultureInvariant);
    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public sealed record DocItem(string Path, string Rfc, string Category);

    /// <summary>取文档头 8 行内的 RFC 头（缺则空字典）。</summary>
    public static Dictionary<string, string> ParseHead(string text)
    {
        var outMap = new Dictionary<string, string>(StringComparer.Ordinal);
        var lines = KnowledgeSig.SplitLines(text);
        var head = string.Join("\n", lines.Take(8));
        var m = HeadRe.Match(head);
        if (!m.Success) return outMap;
        foreach (var name in new[] { "rfc", "cat", "date", "status", "sup", "supby" })
            outMap[name] = m.Groups[name].Value.Trim();
        var updated = LastUpdatedRe.Match(head);
        outMap["last_updated"] = updated.Success ? updated.Groups[1].Value : "";
        return outMap;
    }

    /// <summary>读协议件 RFC 索引（缺件 → 空表，交由 scan 报「缺索引」）。</summary>
    public static (List<DocItem> Docs, List<string> StatusVocabulary) Index(string root)
        => IndexPairs(root);

    /// <summary>
    /// 原始索引对象（等价 Python <c>rfc.index()</c> = <c>json.loads(protocol/rfc_index.json)</c>）——
    /// 供 <c>nf rfc --json</c> 与 Python 逐字节对齐（含 note / schema / status_vocabulary 全字段）。
    /// </summary>
    public static Dictionary<string, object?> IndexDoc(string root)
    {
        var path = Path.Combine(root, IndexRel);
        if (!File.Exists(path)) return new Dictionary<string, object?>(StringComparer.Ordinal);
        using var doc = JsonIo.ReadFile(path);
        return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
    }

    private static (List<DocItem> Docs, List<string> StatusVocabulary) IndexPairs(string root)
    {
        var path = Path.Combine(root, IndexRel);
        var docs = new List<DocItem>();
        if (!File.Exists(path)) return (docs, new List<string>());
        using var doc = JsonIo.ReadFile(path);
        var rootEl = doc.RootElement;
        var vocabulary = new List<string>();
        if (rootEl.TryGetProperty("status_vocabulary", out var vocab) && vocab.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in vocab.EnumerateArray())
                if (item.ValueKind == JsonValueKind.String) vocabulary.Add(item.GetString()!);
        }
        if (rootEl.TryGetProperty("docs", out var rows) && rows.ValueKind == JsonValueKind.Array)
        {
            foreach (var row in rows.EnumerateArray())
            {
                string Text(string key) =>
                    row.TryGetProperty(key, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString()! : "";
                docs.Add(new DocItem(Text("path"), Text("rfc"), Text("category")));
            }
        }
        return (docs, vocabulary);
    }

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var (docs, vocabulary) = Index(root);
        if (docs.Count == 0)
        {
            issues.Add($"缺 RFC 索引 {IndexRel}（修复指引：见 protocol/rfc_index.json）");
            return (issues, warns, new Dictionary<string, object?>(StringComparer.Ordinal));
        }
        var vocab = vocabulary.Count > 0 ? vocabulary : new List<string> { FallbackStatus };

        var seen = new Dictionary<string, string>(StringComparer.Ordinal);
        var supby = new Dictionary<string, string>(StringComparer.Ordinal);
        var chainOrder = new List<string>();

        foreach (var item in docs)
        {
            var rel = item.Path;
            var rfc = item.Rfc;
            var full = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(full))
            {
                issues.Add($"RFC 索引指向不存在的文档：{rel}");
                continue;
            }
            if (seen.TryGetValue(rfc, out var prior))
                issues.Add($"RFC 编号重复：{rfc}（{prior} 与 {rel}）");
            seen[rfc] = rel;

            var head = ParseHead(StrictUtf8.GetString(File.ReadAllBytes(full)));
            if (head.Count == 0)
            {
                issues.Add($"{rel} 缺 RFC 头（修复指引：见 docs 或 core/rfc.py 头格式）");
                continue;
            }
            if (head["rfc"] != rfc)
                issues.Add($"{rel} 头部 RFC 与索引不一致：头={head["rfc"]} 索引={rfc}");
            if (Array.IndexOf(Categories, head["cat"]) < 0)
                issues.Add($"{rel} Category 越词表：{head["cat"]}（{string.Join("/", Categories)}）");
            if (!vocab.Contains(head["status"], StringComparer.Ordinal))
                issues.Add($"{rel} Status 越词表：{head["status"]}（{string.Join("/", vocab)}）");
            if (head["last_updated"].Length > 0 && head["date"] != head["last_updated"])
                issues.Add($"{rel} Date 与「最后更新」不一致：RFC={head["date"]} 最后更新={head["last_updated"]}");
            if (item.Category.Length > 0 && item.Category != head["cat"])
                issues.Add($"{rel} Category 索引与头部不一致：索引={item.Category} 头={head["cat"]}");
            if (head["status"] == "Superseded" && IsBlank(head["supby"]))
                issues.Add($"{rel} 标记 Superseded 但缺 Superseded by");
            if (!IsBlank(head["supby"]))
            {
                if (!supby.ContainsKey(rfc)) chainOrder.Add(rfc);
                supby[rfc] = head["supby"];
            }
        }

        foreach (var key in chainOrder)
        {
            var target = supby[key];
            if (!seen.ContainsKey(target))
            {
                issues.Add($"{key} 的 Superseded by 指向不在册的编号：{target}");
                continue;
            }
            var current = target;
            var hops = 0;
            while (supby.ContainsKey(current) && hops < supby.Count + 1)
            {
                current = supby[current];
                hops++;
                if (current == key)
                {
                    issues.Add($"supersede 链成环：{key} → … → {key}");
                    break;
                }
            }
        }

        // stats.statuses = 在册文档头部的 status 去重排序（等价 Python 的 sorted({...}) 集合推导）
        var statuses = new SortedSet<string>(StringComparer.Ordinal);
        foreach (var rel in seen.Values)
        {
            var full = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(full)) continue;
            var head = ParseHead(StrictUtf8.GetString(File.ReadAllBytes(full)));
            statuses.Add(head.TryGetValue("status", out var st) ? st : "");
        }
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["docs"] = seen.Count,
            ["chains"] = supby.Count,
            ["statuses"] = statuses.Cast<object?>().ToList(),
        };
        return (issues, warns, stats);
    }

    private static bool IsBlank(string value) => value is "—" or "-" or "";
}
