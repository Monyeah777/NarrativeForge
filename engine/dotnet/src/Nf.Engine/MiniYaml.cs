using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// `machine_contract` 代码围栏的提取 + **最小 YAML 子集**解析（BCL-only，无第三方依赖）。
///
/// 子集范围由 235 个真实模块文档扫出（2026-09-26 实测）：嵌套映射（深度 ≤4）、块序列（6 篇）、
/// 行内序列 `[a, b]`（235 篇）、空流映射 `{}`（13 篇）、单/双引号标量、键行行尾注释。
/// 语料中**不存在**锚点/别名、块标量（`|` / `>`）、TAB、多文档分隔符、非空流映射——
/// 越出子集一律 **fail-closed 抛错**，不静默误解析。
/// </summary>
public static class MiniYaml
{
    private static readonly Regex FenceRe = new(@"(?ms)```yaml\s*(.*?)```");

    /// <summary>提取含指定标记的 YAML 围栏正文（等价 Python <c>conformance_scan._fence_yaml</c> 的取块部分）。</summary>
    public static string? ExtractFence(string text, string marker)
    {
        foreach (Match m in FenceRe.Matches(text))
        {
            var body = m.Groups[1].Value;
            if (body.Contains(marker, StringComparison.Ordinal)) return body;
        }
        return null;
    }

    /// <summary>解析 YAML 子集正文；返回顶层映射。</summary>
    public static Dictionary<string, object?> Parse(string body)
    {
        var node = ParseAny(body);
        if (node is Dictionary<string, object?> map) return map;
        throw new InvalidOperationException("顶部不是映射（超出子集）");
    }

    /// <summary>解析任意顶层节点（映射/序列/标量/空）——空文档返回 <c>null</c>（同 PyYAML <c>safe_load("")</c>）。</summary>
    public static object? ParseAny(string body)
    {
        var lines = Preprocess(body);
        if (lines.Count == 0) return null;
        var index = 0;
        return ParseBlock(lines, ref index, lines[0].Indent);
    }

    /// <summary>
    /// 等价 Python <c>schema_lint._fence_yaml(text, marker)</c>：逐个「含 marker」的围栏尝试解析，
    /// **解析抛错即返回 null（不再试后续围栏）**；解析成功但顶层不是映射时继续看下一个围栏。
    /// </summary>
    public static Dictionary<string, object?>? ParseFence(string text, string marker)
    {
        foreach (Match m in FenceRe.Matches(text))
        {
            var body = m.Groups[1].Value;
            if (!body.Contains(marker, StringComparison.Ordinal)) continue;
            object? node;
            try
            {
                node = ParseAny(body);
            }
            catch (Exception)
            {
                return null;
            }
            if (node is Dictionary<string, object?> map) return map;
        }
        return null;
    }

    private sealed record Line(int Indent, string Text);

    private static List<Line> Preprocess(string body)
    {
        var result = new List<Line>();
        foreach (var raw in body.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n'))
        {
            if (raw.Contains('\t'))
            {
                throw new InvalidOperationException("YAML 子集不含 TAB 缩进（fail-closed）：" + raw);
            }
            var noComment = StripComment(raw).TrimEnd();
            if (noComment.Trim().Length == 0) continue;
            var indent = 0;
            while (indent < noComment.Length && noComment[indent] == ' ') indent++;
            result.Add(new Line(indent, noComment[indent..]));
        }
        return result;
    }

    /// <summary>去掉行尾注释：`#` 且位于行首或前面是空白，且不在引号内。</summary>
    private static string StripComment(string line)
    {
        var inSingle = false;
        var inDouble = false;
        for (var i = 0; i < line.Length; i++)
        {
            var c = line[i];
            if (c == '\'' && !inDouble) inSingle = !inSingle;
            else if (c == '"' && !inSingle) inDouble = !inDouble;
            else if (c == '#' && !inSingle && !inDouble && (i == 0 || line[i - 1] == ' ' || line[i - 1] == '\t'))
            {
                return line[..i];
            }
        }
        return line;
    }

    private static object? ParseBlock(List<Line> lines, ref int index, int indent)
    {
        if (index >= lines.Count || lines[index].Indent < indent)
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal);
        }
        return lines[index].Text.StartsWith("-", StringComparison.Ordinal)
            ? ParseSequence(lines, ref index, indent)
            : ParseMap(lines, ref index, indent);
    }

    private static List<object?> ParseSequence(List<Line> lines, ref int index, int indent)
    {
        var list = new List<object?>();
        while (index < lines.Count && lines[index].Indent == indent &&
               lines[index].Text.StartsWith("-", StringComparison.Ordinal))
        {
            var afterDash = lines[index].Text.Length > 1 ? lines[index].Text[1..] : "";
            var lead = afterDash.Length - afterDash.TrimStart(' ').Length;
            var itemKeyIndent = indent + 1 + lead;      // 序列项内容的列（续行与首键同列）
            var rest = afterDash.Trim();
            index++;
            if (rest.Length == 0)
            {
                // `-` 独占一行：其块在更深缩进处（PyYAML 形态 `- \n  a: 1`）
                list.Add(index < lines.Count && lines[index].Indent > indent
                    ? ParseBlock(lines, ref index, lines[index].Indent)
                    : null);
                continue;
            }
            if (IsBlockMapStart(rest))
            {
                list.Add(ParseSequenceItemMap(lines, ref index, itemKeyIndent, rest));
                continue;
            }
            list.Add(ParseScalar(rest));
        }
        return list;
    }

    /// <summary>
    /// 序列项本身是映射（`- id: "X"` + 续行）：首个键值在 `- ` 同行，其余键与首键**同列**。
    /// 依据 YAML 语义：只有 `": "`（冒号+空格）或行尾冒号才算映射键——`- 通用:M10` 是**标量**。
    /// </summary>
    private static Dictionary<string, object?> ParseSequenceItemMap(
        List<Line> lines, ref int index, int keyIndent, string first)
    {
        var map = new Dictionary<string, object?>(StringComparer.Ordinal);
        var colon = first.IndexOf(':');
        var key = UnquoteKey(first[..colon].Trim());
        var rest = first[(colon + 1)..].Trim();
        if (rest.Length > 0)
        {
            map[key] = ParseScalar(rest);
        }
        else
        {
            map[key] = index < lines.Count && lines[index].Indent > keyIndent
                ? ParseBlock(lines, ref index, lines[index].Indent)
                : null;
        }
        if (index < lines.Count && lines[index].Indent == keyIndent &&
            !lines[index].Text.StartsWith("-", StringComparison.Ordinal))
        {
            foreach (var kv in ParseMap(lines, ref index, keyIndent)) map[kv.Key] = kv.Value;
        }
        return map;
    }

    /// <summary>「块映射键」判定：存在顶层键值分隔符（否则按标量，如 `通用:M10`）。</summary>
    private static bool IsBlockMapStart(string text)
    {
        if (text.StartsWith('[') || text.StartsWith('{')) return false;
        return FindTopLevelColon(text) > 0;
    }

    /// <summary>
    /// 找**键值分隔符**：顶层（不在引号/流括号内）且紧跟空格或行尾的冒号；无则 -1。
    /// 只认这种冒号是 YAML 的语义——`a:b` 是标量、`a: b` 才是映射项。
    /// </summary>
    private static int FindTopLevelColon(string text)
    {
        var inSingle = false;
        var inDouble = false;
        var depth = 0;
        for (var i = 0; i < text.Length; i++)
        {
            var c = text[i];
            if (c == '\'' && !inDouble) inSingle = !inSingle;
            else if (c == '"' && !inSingle) inDouble = !inDouble;
            else if (!inSingle && !inDouble && (c == '[' || c == '{')) depth++;
            else if (!inSingle && !inDouble && (c == ']' || c == '}')) depth--;
            else if (c == ':' && !inSingle && !inDouble && depth == 0
                     && (i + 1 == text.Length || text[i + 1] == ' ')) return i;
        }
        return -1;
    }

    private static string UnquoteKey(string key)
    {
        if (key.Length >= 2 && key[0] == '"' && key[^1] == '"') return UnescapeDouble(key[1..^1]);
        if (key.Length >= 2 && key[0] == '\'' && key[^1] == '\'') return key[1..^1].Replace("''", "'");
        return key;
    }

    private static Dictionary<string, object?> ParseMap(List<Line> lines, ref int index, int indent)
    {
        var map = new Dictionary<string, object?>(StringComparer.Ordinal);
        while (index < lines.Count && lines[index].Indent == indent)
        {
            var text = lines[index].Text;
            if (text.StartsWith("-", StringComparison.Ordinal)) break;

            // 键值分隔符 = **顶层**、且紧跟空格或行尾的冒号（YAML 语义）；
            // 故 `通用:M10: untyped` 的键是 `通用:M10` 而不是 `通用`。
            var colon = FindTopLevelColon(text);
            if (colon <= 0)
            {
                throw new InvalidOperationException("不是 `key: value` 形式，超出本子集（fail-closed）：" + text);
            }
            var key = UnquoteKey(text[..colon].Trim());   // 键也可能带引号（`'AI保险:M01': untyped`）
            if (key == "<<")
                throw new InvalidOperationException("YAML 合并键（<<）超出本子集（fail-closed）");
            var rest = text[(colon + 1)..].Trim();
            if (FindTopLevelColon(rest) > 0)
            {
                // 未引用的值里又出现 `: ` —— PyYAML 在此**报错**（mapping values are not allowed here），
                // 引擎同样 fail-closed，绝不静默拼成字符串。
                throw new InvalidOperationException("块映射值里出现未引用的 `: `（PyYAML 同错，fail-closed）：" + text);
            }
            index++;

            if (rest.Length == 0)
            {
                map[key] = index < lines.Count && lines[index].Indent > indent
                    ? ParseBlock(lines, ref index, lines[index].Indent)
                    : null;
            }
            else
            {
                map[key] = ParseScalar(rest);
            }
        }
        return map;
    }

    private static object? ParseScalar(string raw)
    {
        var s = raw.Trim();
        if (s == "{}") return new Dictionary<string, object?>(StringComparer.Ordinal);
        if (s == "[]") return new List<object?>();
        // 子集边界**显式化**：下列构造引擎未实现，必须 fail-closed 而不是当字符串吞掉
        // （此前 `k: |` 会被解析成字面 "|"、`a: &x 1` 成 "&x 1"、`b: *x` 成 "*x" ——
        //  即"越界即报错"的承诺对这几族是**假的**；构造矩阵探针实测发现）
        if (BlockScalarRe.IsMatch(s))
            throw new InvalidOperationException("块标量（" + s + "）超出本子集（fail-closed）："
                                              + "请改用行内写法或先扩展解析器");
        if (s.StartsWith('&'))
            throw new InvalidOperationException("YAML 锚点（" + s[..Math.Min(12, s.Length)] + "）超出本子集（fail-closed）");
        if (s.StartsWith('*'))
            throw new InvalidOperationException("YAML 别名（" + s[..Math.Min(12, s.Length)] + "）超出本子集（fail-closed）");
        // 跨行引号标量（YAML 会把换行折叠成空格）——未闭合时必须报错，不能当普通字符串吞掉
        if ((s.StartsWith('"') && !s.EndsWith('"')) || (s.StartsWith('\'') && !s.EndsWith('\'')))
            throw new InvalidOperationException("未闭合的引号标量（跨行引号超出本子集，fail-closed）："
                                              + s[..Math.Min(20, s.Length)]);
        if (s.StartsWith('['))
        {
            if (!s.EndsWith(']')) throw new InvalidOperationException("行内序列未闭合（fail-closed）：" + s);
            var inner = s[1..^1];
            var items = new List<object?>();
            foreach (var part in SplitTopLevel(inner))
            {
                var trimmed = part.Trim();
                if (trimmed.Length == 0) continue;
                items.Add(ParseScalar(trimmed));
            }
            return items;
        }
        if (s.StartsWith('{'))
        {
            if (!s.EndsWith('}')) throw new InvalidOperationException("流映射未闭合（fail-closed）：" + s);
            var inner = s[1..^1];
            var flow = new Dictionary<string, object?>(StringComparer.Ordinal);
            foreach (var part in SplitTopLevel(inner))
            {
                var trimmed = part.Trim();
                if (trimmed.Length == 0) continue;
                var colon = FindTopLevelColon(trimmed);
                if (colon > 0)
                {
                    flow[UnquoteKey(trimmed[..colon].Trim())] = ParseScalar(trimmed[(colon + 1)..].Trim());
                }
                else
                {
                    // `{a:1}` 是「无值的流映射项」：键即整段、值为 null（与 PyYAML 同判）
                    flow[UnquoteKey(trimmed)] = null;
                }
            }
            return flow;
        }
        if (s.Length >= 2 && s[0] == '"' && s[^1] == '"') return UnescapeDouble(s[1..^1]);
        if (s.Length >= 2 && s[0] == '\'' && s[^1] == '\'') return s[1..^1].Replace("''", "'");
        return PyScalar.Resolve(s);
    }

    /// <summary>块标量指示符：<c>|</c> / <c>&gt;</c> 加可选的缩进指示与 chomping（如 <c>|-</c> / <c>&gt;2+</c>）。</summary>
    private static readonly Regex BlockScalarRe = new(@"^[|>]([0-9][-+]?|[-+][0-9]?|[-+])?$");

    private static IEnumerable<string> SplitTopLevel(string inner)
    {
        var buffer = new StringBuilder();
        var inSingle = false;
        var inDouble = false;
        var depth = 0;
        foreach (var c in inner)
        {
            if (c == '\'' && !inDouble) inSingle = !inSingle;
            else if (c == '"' && !inSingle) inDouble = !inDouble;
            if (!inSingle && !inDouble)
            {
                if (c is '[' or '{') depth++;
                else if (c is ']' or '}') depth--;
            }
            if (c == ',' && !inSingle && !inDouble && depth == 0)
            {
                yield return buffer.ToString();
                buffer.Clear();
                continue;
            }
            buffer.Append(c);
        }
        yield return buffer.ToString();
    }

    private static string UnescapeDouble(string s)
    {
        var sb = new StringBuilder();
        for (var i = 0; i < s.Length; i++)
        {
            if (s[i] != '\\' || i + 1 >= s.Length) { sb.Append(s[i]); continue; }
            var next = s[++i];
            switch (next)
            {
                case 'n': sb.Append('\n'); break;
                case 't': sb.Append('\t'); break;
                case 'r': sb.Append('\r'); break;
                case '"': sb.Append('"'); break;
                case '\\': sb.Append('\\'); break;
                // YAML 双引号转义族（PyYAML 支持；此前只做了 n/t/r/"/\\/u，`\x41` 被吞成 `x41`）
                case '0': sb.Append('\0'); break;
                case 'a': sb.Append('\a'); break;
                case 'b': sb.Append('\b'); break;
                case 'f': sb.Append('\f'); break;
                case 'v': sb.Append('\v'); break;
                case 'e': sb.Append('\u001b'); break;
                case 'x':
                    if (i + 2 >= s.Length) throw new InvalidOperationException("\\x 转义不完整（fail-closed）");
                    sb.Append((char)int.Parse(s.Substring(i + 1, 2), NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                    i += 2;
                    break;
                case 'u':
                    if (i + 4 >= s.Length) throw new InvalidOperationException("\\u 转义不完整（fail-closed）");
                    var hex = s.Substring(i + 1, 4);
                    sb.Append((char)int.Parse(hex, NumberStyles.HexNumber, CultureInfo.InvariantCulture));
                    i += 4;
                    break;
                default: sb.Append(next); break;
            }
        }
        return sb.ToString();
    }
}
