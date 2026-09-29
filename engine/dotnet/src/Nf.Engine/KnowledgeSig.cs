using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/knowledge_sig.py</c>：根目录 01–36 编号方案文档的**结构化签名**（知识指纹）。
/// check25 的语义 = 同一套签名两遍生成逐字节一致（可复现）。
/// </summary>
public static class KnowledgeSig
{
    private static readonly Regex DocRangeRe = new(@"^((?:0[1-9]|[12][0-9]|3[0-6]))_");
    private static readonly Regex VersionRe = new(@"v\d+(?:\.\d+){1,2}");
    private static readonly Regex RefPRe = new(@"(?<![A-Za-z0-9])P\d{2,4}");
    private static readonly Regex RefMRe = new(@"(?<![A-Za-z0-9])M\d{2,4}");
    private static readonly Regex HeadingRe = new(@"^#{1,6}\s+(.*?)\s*$", RegexOptions.Multiline);
    private static readonly Regex YamlFenceRe = new(@"^```[ \t]*[Yy][Aa][Mm][Ll]?[ \t]*$");
    private static readonly Regex BlockKeyRe = new(@"^([A-Za-z_]\w*):\s*$", RegexOptions.Multiline);

    /// <summary>通用换行归一（等价 Python 文本模式读取的 universal newlines）。</summary>
    public static string Norm(string text) => text.Replace("\r\n", "\n").Replace('\r', '\n');
    private static string Sha(string text) => Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(text))).ToLowerInvariant();

    /// <summary>
    /// Python <c>str.splitlines()</c> 的逐位语义：识别 <c>\r</c> / <c>\r\n</c> 与全部 Unicode 行边界
    /// （<c>\v \f \x1c \x1d \x1e \x85 \u2028 \u2029</c>），且**末尾边界不产生空元素**。
    ///
    /// 为什么值得单独抽出来：<c>"a\n".Split('\n')</c> 会多出一个空元素（行数 +1），
    /// 进而让 `line_count` / `body_hash` 这类字段整体偏移——sig 首版正是栽在这里。
    /// 决策族与馆藏族的 frontmatter 解析同样按此语义取值。
    /// </summary>
    private static readonly char[] LineBoundaries = { '\n', '\v', '\f', '\x1c', '\x1d', '\x1e', '\x85', '\u2028', '\u2029' };

    public static List<string> SplitLines(string text)
    {
        var result = new List<string>();
        var start = 0;
        for (var i = 0; i < text.Length; i++)
        {
            if (text[i] == '\r')
            {
                result.Add(text[start..i]);
                if (i + 1 < text.Length && text[i + 1] == '\n') i++;
                start = i + 1;
                continue;
            }
            if (Array.IndexOf(LineBoundaries, text[i]) < 0) continue;
            result.Add(text[start..i]);
            start = i + 1;
        }
        if (start < text.Length) result.Add(text[start..]);
        return result;
    }

    public static string ParseDocId(string path)
    {
        var m = DocRangeRe.Match(Path.GetFileName(path));
        return m.Success ? m.Groups[1].Value : "";
    }

    public static string KindOf(string path)
    {
        var p = path.Replace('\\', '/');
        if (p.Contains("/03_管线库/", StringComparison.Ordinal) || p.Contains("/pipelines/", StringComparison.Ordinal))
            return "pipeline";
        if (p.Contains("/04_模块库/", StringComparison.Ordinal) || p.Contains("/modules/", StringComparison.Ordinal))
            return "module";
        return "doc";
    }

    /// <summary>提取 ```yaml 代码块正文（纯文本切段，不做 YAML 解析）。</summary>
    public static List<string> ExtractFences(string text)
    {
        var fences = new List<string>();
        var inFence = false;
        var buffer = new List<string>();
        foreach (var line in SplitLines(Norm(text)))
        {
            if (!inFence)
            {
                if (YamlFenceRe.IsMatch(line)) { inFence = true; buffer = new List<string>(); }
            }
            else if (line.TrimStart().StartsWith("```", StringComparison.Ordinal))
            {
                inFence = false;
                fences.Add(string.Join("\n", buffer));
            }
            else
            {
                buffer.Add(line);
            }
        }
        return fences;
    }

    public static string FieldFromFence(string text, string field)
    {
        var pattern = new Regex(@"(?m)^\s*" + Regex.Escape(field) + @":\s*(.+?)\s*$");
        foreach (var fence in ExtractFences(text))
        {
            var m = pattern.Match(fence);
            if (m.Success) return m.Groups[1].Value.Trim().Trim('\'', '"');
        }
        return "";
    }

    public static Dictionary<string, object?> BuildSignature(string path, string root)
    {
        var raw = new UTF8Encoding(false).GetString(
            File.ReadAllBytes(Path.Combine(root, path.Replace('/', Path.DirectorySeparatorChar))));
        var text = Norm(raw);
        var lines = SplitLines(text);
        var headings = new List<string>();
        foreach (var line in lines)
        {
            var m = HeadingRe.Match(line);
            if (m.Success && !m.Groups[1].Value.StartsWith("#", StringComparison.Ordinal))
                headings.Add(m.Groups[1].Value.Trim());
        }
        var docId = ParseDocId(path);
        var title = headings.Count > 0 ? headings[0] : Path.GetFileName(path);
        var versionMatch = VersionRe.Match(title + "\n" + string.Join("\n", lines.Take(8)));

        var schemaNames = new List<string>();
        foreach (var fence in ExtractFences(text))
        {
            foreach (Match m in BlockKeyRe.Matches(fence))
            {
                var name = m.Groups[1].Value;
                if (name is not ("yaml" or "yml" or "text")) schemaNames.Add(name);
            }
        }

        var refs = RefMRe.Matches(text).Select(m => m.Value)
            .Concat(RefPRe.Matches(text).Select(m => m.Value))
            .Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToList();
        var metaLineCount = lines.Count(l => l.TrimStart().StartsWith(">", StringComparison.Ordinal));

        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["kind"] = KindOf(path),
            ["path"] = path.Replace('\\', '/'),
            ["doc_id"] = docId,
            ["title"] = title,
            ["version"] = versionMatch.Success ? versionMatch.Value : "",
            ["self_id"] = FieldFromFence(text, "id"),
            ["layer"] = FieldFromFence(text, "layer"),
            ["category"] = FieldFromFence(text, "category"),
            ["heading_count"] = headings.Count,
            ["headings"] = headings.Cast<object?>().ToList(),
            ["schema_names"] = schemaNames.Distinct(StringComparer.Ordinal)
                .OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
            ["refs"] = refs.Cast<object?>().ToList(),
            ["meta_line_count"] = metaLineCount,
            ["line_count"] = lines.Count,
            ["body_hash"] = Sha(text),
        };
    }

    public static string SignatureDigest(Dictionary<string, object?> signature)
        => Sha(PythonJson.CanonicalizeGraph(signature));

    /// <summary>根目录 01–36 编号方案文档（按文件名排序）。</summary>
    public static List<string> DiscoverDocs(string root)
    {
        if (!Directory.Exists(root)) return new List<string>();
        return Directory.GetFiles(root, "*.md")
            .Select(Path.GetFileName)
            .Where(name => name is not null && DocRangeRe.IsMatch(name))
            .Select(name => name!)
            .OrderBy(x => x, StringComparer.Ordinal)
            .ToList();
    }

    public sealed record ScanResult(int Count, List<object?> Records);

    public static ScanResult Scan(string root)
    {
        var records = new List<object?>();
        foreach (var rel in DiscoverDocs(root))
        {
            var sig = BuildSignature(rel, root);
            records.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["digest"] = SignatureDigest(sig),
                ["sig"] = sig,
            });
        }
        return new ScanResult(records.Count, records);
    }

    /// <summary>check25 语义：两遍扫描逐字节一致。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) VerifyReproducible(string root)
    {
        var issues = new List<string>();
        var first = Scan(root);
        var second = Scan(root);
        if (first.Count == 0) issues.Add("未发现任何 01-36 编号方案文档");
        if (first.Count != second.Count) issues.Add("两遍扫描文件数不一致");
        var firstCanonical = PythonJson.CanonicalizeGraph(first.Records);
        var secondCanonical = PythonJson.CanonicalizeGraph(second.Records);
        if (firstCanonical != secondCanonical) issues.Add("两遍签名不一致（知识指纹不稳定）");
        var reproducible = first.Count > 0 && firstCanonical == secondCanonical;
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["docs"] = first.Count,
            ["reproducible"] = first.Count,
        };
        return (issues, stats);
    }
}
