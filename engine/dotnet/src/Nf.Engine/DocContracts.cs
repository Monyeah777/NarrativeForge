using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 治理族（接力 / 复盘 / 审计）共用的**文档级判据助手**——三件契约的判定结构同源：
/// frontmatter 必填 + 必备段齐 + 列表块逐条判 + 引用可解析。抽在这里，避免三份拷贝各自漂移。
/// </summary>
public static class DocContracts
{
    private static readonly Regex BulletStart = new(@"^\s*[-*]\s+", RegexOptions.Multiline);
    private static readonly Regex CheckDef = new(@"^check(\d+)\(\)\{", RegexOptions.Multiline);
    private static readonly Regex CheckRef = new(@"^check(\d+)$");
    private static readonly Regex AdrRef = new(@"^ADR-\d{4}$");
    private static readonly Regex Dated = new(@"^\d{4}-\d{2}-\d{2}$");
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>等价 <c>core.library.parse_frontmatter</c>（与 decisions 同一实现，已对账）。</summary>
    public static (Dictionary<string, object?> Fm, string Body) Frontmatter(string text)
        => Decisions.ParseFrontmatter(text);

    /// <summary>
    /// 列表按「bullet 块」切分：一条 bullet 含其后续缩进续行（换行续写算同一条）。
    /// 等价 Python <c>_bullet_blocks</c>。
    /// </summary>
    public static List<string> BulletBlocks(string text)
    {
        var blocks = new List<string>();
        var current = new List<string>();
        foreach (var line in KnowledgeSig.SplitLines(text))
        {
            if (BulletStart.IsMatch(line))
            {
                if (current.Count > 0) blocks.Add(string.Join("\n", current).Trim());
                current = new List<string> { line };
            }
            else if (current.Count > 0 && line.Trim().Length > 0)
            {
                current.Add(line);
            }
            else if (current.Count > 0)
            {
                blocks.Add(string.Join("\n", current).Trim());
                current = new List<string>();
            }
        }
        if (current.Count > 0) blocks.Add(string.Join("\n", current).Trim());
        return blocks;
    }

    /// <summary>verify.sh 里在册的 check 编号集合（<c>^checkN(){</c>）。</summary>
    public static HashSet<string> ChecksFromVerify(string root)
    {
        var path = Path.Combine(root, "verify.sh");
        var text = File.Exists(path) ? StrictUtf8.GetString(File.ReadAllBytes(path)) : "";
        return CheckDef.Matches(text).Select(m => m.Groups[1].Value).ToHashSet(StringComparer.Ordinal);
    }

    /// <summary>单条引用是否可解析：<c>checkN</c> 须在册；<c>ADR-nnnn</c> 放行；其余须是真实件。</summary>
    public static string? CheckRefIssue(string root, string reference, HashSet<string> checks, string label)
    {
        var text = reference.Trim();
        var match = CheckRef.Match(text);
        if (match.Success)
            return checks.Contains(match.Groups[1].Value) ? null : $"{label}指向不存在的 check：{text}";
        if (AdrRef.IsMatch(text)) return null;
        var full = Path.Combine(root, text.Replace('\\', '/').Replace('/', Path.DirectorySeparatorChar));
        return File.Exists(full) || Directory.Exists(full) ? null : $"{label}无法解析：{text}";
    }

    public static bool IsDated(string value) => Dated.IsMatch(value);

    /// <summary>取 glob 命中的件（排序，posix 相对路径）——<c>handovers/HO-*.md</c> 这类单层模式。</summary>
    public static List<string> GlobFiles(string root, string pattern) => PathGlob.Files(root, pattern);

    public static string Str(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is string text ? text : "";

    /// <summary>Python <c>fm.get(k) or []</c>：字符串包成单元素表，其余空。</summary>
    public static List<string> RefsOf(object? value) => value switch
    {
        List<string> list => list.Select(x => x).ToList(),
        List<object?> list => list.Select(x => x?.ToString() ?? "").ToList(),
        string text => new List<string> { text },
        null => new List<string>(),
        _ => new List<string> { value.ToString() ?? "" },
    };
}

/// <summary>治理族共用的**文件 IO**：声明读取 / frontmatter 读取 / 字段判空 / 字符串表。</summary>
public static class DocContractIo
{
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public static Dictionary<string, object?> Decl(string root, string rel)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return new Dictionary<string, object?>(StringComparer.Ordinal);
        using var doc = JsonIo.ReadFile(path);
        return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
    }

    /// <summary>读件并切 frontmatter；件不存在时返回 <c>(null, "")</c>。</summary>
    public static (Dictionary<string, object?>? Fm, string Body) ReadFrontmatter(string root, string rel)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return (null, "");
        var text = StrictUtf8.GetString(File.ReadAllBytes(path));
        return DocContracts.Frontmatter(text);
    }

    /// <summary>等价 Python <c>if not fm.get(k)</c>：缺键 / 空串 / 空表都算未填。</summary>
    public static bool Filled(Dictionary<string, object?> fm, string key)
        => fm.TryGetValue(key, out var value) && value switch
        {
            null => false,
            string text => text.Length > 0,
            List<object?> list => list.Count > 0,
            List<string> list => list.Count > 0,
            _ => true,
        };

    public static List<string> Strings(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is List<object?> list
            ? list.Select(x => x?.ToString() ?? "").ToList()
            : new List<string>();

    /// <summary>全量条目（相对 posix 路径 + 文件名 + frontmatter），按路径排序——等价各模块的 <c>entries()</c>。</summary>
    public static List<(string Rel, string File, Dictionary<string, object?> Fm)> Entries(string root, string glob)
    {
        var rows = new List<(string, string, Dictionary<string, object?>)>();
        foreach (var rel in DocContracts.GlobFiles(root, glob))
        {
            var (fm, _) = ReadFrontmatter(root, rel);
            rows.Add((rel, Path.GetFileName(rel), fm ?? new Dictionary<string, object?>(StringComparer.Ordinal)));
        }
        return rows;
    }

    /// <summary>等价 Python <c>"%s" % fm.get(k)</c>：缺键渲染成 <c>None</c>。</summary>
    public static string PyValue(Dictionary<string, object?> fm, string key)
        => fm.TryGetValue(key, out var value) && value is not null ? value.ToString() ?? "None" : "None";

    /// <summary>等价 Python <c>fm.get(k) or fallback</c>：空串/None/空表都退到 fallback。</summary>
    public static string PyOr(Dictionary<string, object?> fm, string key, string fallback)
    {
        var value = fm.TryGetValue(key, out var raw) ? raw : null;
        var text = value switch
        {
            null => "",
            string s => s,
            List<object?> list => list.Count == 0 ? "" : PyScalar.PyRepr(value),
            _ => value.ToString() ?? "",
        };
        return text.Length == 0 ? fallback : text;
    }
}
