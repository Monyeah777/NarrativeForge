using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 仓库相对路径的 glob 匹配（等价 <c>pathlib.Path(root).glob(pattern)</c> 的所需子集）：
/// <c>**</c> 跨目录、<c>*</c> 不跨段、<c>?</c> 单字符、字符类透传；返回**文件**的相对 posix 路径（已排序）。
///
/// 说明：<c>Patterns.cs</c> 里有一份同源的私有实现（只做「有无命中」判定）。此处是返回命中集的版本，
/// 供 <c>state-front</c> 的族规则用；刻意不改动已验证的 Patterns，避免连带回归。
/// </summary>
public static class PathGlob
{
    public static List<string> Files(string root, string pattern)
    {
        var regex = Translate(pattern.Replace('\\', '/'));
        var hits = new List<string>();
        if (!Directory.Exists(root)) return hits;
        foreach (var entry in Directory.EnumerateFileSystemEntries(root, "*", SearchOption.AllDirectories))
        {
            var rel = Path.GetRelativePath(root, entry).Replace('\\', '/');
            if (regex.IsMatch(rel) && File.Exists(entry)) hits.Add(rel);
        }
        hits.Sort(StringComparer.Ordinal);
        return hits;
    }

    private static Regex Translate(string pattern)
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
}
