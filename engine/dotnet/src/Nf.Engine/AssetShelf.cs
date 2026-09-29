using System.Text;

namespace Nf.Engine;

/// <summary>
/// 资产货架的**只读文件枚举与读取**（45 资产质量三面 + 行数基线共用）。
///
/// 复刻 <c>pathlib.Path.glob</c> 在本仓的两条资产模式：
/// <list type="bullet">
/// <item><c>community/*/assets/*.md</c>——社区包各资产货架；</item>
/// <item><c>05_资产库/用户自定义/*.md</c>——官方用户自定义货架。</item>
/// </list>
///
/// **两条平台口径都镜像 CPython 本机行为，不是自设**：
/// ① <c>*.md</c> 的后缀匹配在 Windows 上**不分大小写**（<c>pathlib</c> 走 <c>os.path.normcase</c>，
/// 实测 <c>d.glob('*.md')</c> 会命中 <c>A.MD</c>），Linux 上区分——故按平台选比较器；
/// ② <c>*</c> **不过滤点文件**（<c>pathlib</c> 与 shell glob 在此不同），实测 <c>.md</c> / <c>.hidden.md</c> 都在面内。
/// </summary>
public static class AssetShelf
{
    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary><c>*.md</c> 后缀匹配的大小写口径（镜像 CPython 的平台语义）。</summary>
    public static readonly StringComparison NameComparison =
        OperatingSystem.IsWindows() ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;

    private static readonly string[][] Globs =
    {
        new[] { "community", "*", "assets" },
        new[] { "05_资产库", "用户自定义" },
    };

    /// <summary>
    /// 资产货架上的 <c>.md</c> 文件：按「模式序 → 目录序（ordinal）→ 文件名序（ordinal）」确定性地返回
    /// <c>(相对 posix 路径, 绝对路径)</c>。
    ///
    /// 注：真源此处是 <c>sorted(r.glob(pat))</c>（按**整条路径串**排序），本件改按「目录、文件名」两段排——
    /// 三点已核对不影响判定：密度 / 厚度只出**聚合数**；引用度的键插入序不进输出（零引用清单另排序）；
    /// 键表投影末尾按 <c>(package, key, file)</c> **全序**重排。故顺序不属被比对面（差分探针证的是值）。
    /// </summary>
    public static List<(string Rel, string Full)> MarkdownFiles(string root)
    {
        var hits = new List<(string Rel, string Full)>();
        foreach (var glob in Globs)
        {
            var starAt = Array.IndexOf(glob, "*");
            var dirs = new List<string>();
            if (starAt >= 0)
            {
                var prefix = Path.Combine(new[] { root }.Concat(glob.Take(starAt)).ToArray());
                if (Directory.Exists(prefix))
                {
                    var tail = glob.Skip(starAt + 1).ToArray();
                    foreach (var mid in Directory.GetDirectories(prefix).OrderBy(d => d, StringComparer.Ordinal))
                        dirs.Add(tail.Length == 0 ? mid : Path.Combine(new[] { mid }.Concat(tail).ToArray()));
                }
            }
            else
            {
                dirs.Add(Path.Combine(new[] { root }.Concat(glob).ToArray()));
            }

            foreach (var dir in dirs)
            {
                if (!Directory.Exists(dir)) continue;
                foreach (var full in Directory.GetFiles(dir).OrderBy(f => f, StringComparer.Ordinal))
                {
                    if (!Path.GetFileName(full).EndsWith(".md", NameComparison)) continue;
                    hits.Add((Path.GetRelativePath(root, full).Replace('\\', '/'), full));
                }
            }
        }
        return hits;
    }

    /// <summary>
    /// Python 文本模式读取的等价：严格 UTF-8 解码（<c>encoding="utf-8"</c>，**不去 BOM**）＋ 通用换行归一。
    /// 只吞 <c>OSError</c>（<c>IOException</c> / <c>UnauthorizedAccessException</c>）→ 返回 false；
    /// 解码失败**照抛**（真源会抛 <c>UnicodeDecodeError</c>，属"不可约差异"类，不静默吞）。
    /// </summary>
    public static bool TryReadText(string full, out string text)
    {
        try
        {
            text = KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(full)));
            return true;
        }
        catch (Exception exc) when (exc is IOException or UnauthorizedAccessException)
        {
            text = "";
            return false;
        }
    }

    /// <summary>Python <c>Path.stem</c>：只去**最后一个**后缀，且前导点不算后缀（<c>.hidden</c> 的 stem 仍是 <c>.hidden</c>）。</summary>
    public static string Stem(string name)
    {
        var i = name.LastIndexOf('.');
        return i > 0 && i < name.Length - 1 ? name[..i] : name;
    }

    /// <summary>Python <c>str.strip()</c> 的空白集：比 .NET <c>char.IsWhiteSpace</c> 多 U+001C–U+001F。</summary>
    public static bool IsPySpace(char c) => char.IsWhiteSpace(c) || (c >= '\x1c' && c <= '\x1f');

    public static string PyStrip(string s)
    {
        var a = 0;
        var b = s.Length;
        while (a < b && IsPySpace(s[a])) a++;
        while (b > a && IsPySpace(s[b - 1])) b--;
        return s[a..b];
    }

    public static string PyLStrip(string s)
    {
        var a = 0;
        while (a < s.Length && IsPySpace(s[a])) a++;
        return s[a..];
    }

    /// <summary>Python <c>str.count</c> 的口径：**不可重叠**计数。</summary>
    public static long CountNonOverlapping(string blob, string needle)
    {
        if (needle.Length == 0) return blob.Length + 1L;
        long n = 0;
        var i = 0;
        while (true)
        {
            var j = blob.IndexOf(needle, i, StringComparison.Ordinal);
            if (j < 0) break;
            n++;
            i = j + needle.Length;
        }
        return n;
    }

    /// <summary>
    /// 报错文案里的路径渲染：<c>str(Path)</c> 在 Windows 上**一律反斜杠**（即便调用者给的是正斜杠）。
    /// 只在错误分支用到，顺路径输出不受影响。
    /// </summary>
    public static string PyPath(string p) =>
        OperatingSystem.IsWindows() ? p.Replace('/', '\\') : p;
}
