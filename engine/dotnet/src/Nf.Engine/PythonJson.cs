using System.Globalization;
using System.Text;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 Python <c>json.dumps(obj, ensure_ascii=False, sort_keys=True)</c> 的字节语义。
///
/// 为什么必须自写：.NET 默认序列化器会转义非 ASCII 与 HTML 敏感字符、且浮点格式与 Python 不同，
/// 直接用它会让摘要（digest）字节不一致——等价判据要求字节级一致，不接受"语义近似"。
/// </summary>
public static class PythonJson
{
    /// <summary>规范化序列化。<paramref name="skipTopLevelKeys"/> 中的顶层键在序列化前剔除（对应 Python 的字典推导过滤）。</summary>
    public static string Canonicalize(JsonElement element, params string[] skipTopLevelKeys)
    {
        var sb = new StringBuilder();
        var skip = skipTopLevelKeys.Length == 0 ? null : new HashSet<string>(skipTopLevelKeys, StringComparer.Ordinal);
        Write(element, sb, skip, isTop: true);
        return sb.ToString();
    }

    /// <summary>规范化序列化「对象图」形式（Dictionary / List / string / int / bool / null），语义同 <see cref="Canonicalize"/>。</summary>
    public static string CanonicalizeGraph(object? node)
    {
        var sb = new StringBuilder();
        WriteGraph(node, sb);
        return sb.ToString();
    }

    /// <summary>
    /// 紧凑规范化序列化（分隔符 <c>","</c> / <c>":"</c>，无空格）——等价 Python
    /// <c>json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))</c>，
    /// 即 <c>core/attest.py::canonical</c> 的口径（与证书摘要用的默认带空格分隔符是两套口径，勿混用）。
    /// </summary>
    public static string Compact(object? node)
    {
        var sb = new StringBuilder();
        WriteGraph(node, sb, ",", ":");
        return sb.ToString();
    }

    /// <summary>
    /// 等价 Python <c>json.dumps(obj, ensure_ascii=False, sort_keys=True)</c>——**默认带空格分隔符**
    /// （<c>", "</c> / <c>": "</c>）。与 <see cref="Compact"/> 的无空格口径是**两套**，勿混用：
    /// 证书摘要走无空格，遥测调用 id 走带空格。
    /// </summary>
    public static string SortedWithSpaces(object? node)
    {
        var sb = new StringBuilder();
        WriteGraph(node, sb);
        return sb.ToString();
    }

    /// <summary>
    /// 等价 Python <c>json.dumps(obj, ensure_ascii=False)</c>——默认带空格分隔符、**保持插入序**（不排序）。
    /// 用于把单个属性值渲染成人读日志（真源 <c>nf telemetry</c> 的文本面就是这么打的）。
    /// </summary>
    public static string UnsortedWithSpaces(object? node)
    {
        var sb = new StringBuilder();
        WriteGraph(node, sb, ", ", ": ", sortKeys: false);
        return sb.ToString();
    }

    /// <summary>
    /// <see cref="JsonElement"/> → 对象图（Dictionary / List / string / long / double / bool / null）。
    /// 供 <see cref="Compact"/> 等「另一套分隔符口径」复用；重复键取后值（同 Python <c>json.load</c>）。
    /// </summary>
    public static object? ToGraph(JsonElement element)
    {
        switch (element.ValueKind)
        {
            case JsonValueKind.Object:
                var map = new Dictionary<string, object?>(StringComparer.Ordinal);
                foreach (var property in element.EnumerateObject()) map[property.Name] = ToGraph(property.Value);
                return map;
            case JsonValueKind.Array:
                var list = new List<object?>();
                foreach (var item in element.EnumerateArray()) list.Add(ToGraph(item));
                return list;
            case JsonValueKind.String:
                return element.GetString();
            case JsonValueKind.Number:
                // 注意：`cond ? asLong : GetDouble()` 的三元类型会被推断成 double，
                // 会把整数**静默转成浮点**（1 → 1.0）。必须分开写，别图短。
                if (element.TryGetInt64(out var asLong)) return asLong;
                return element.GetDouble();
            case JsonValueKind.True:
                return true;
            case JsonValueKind.False:
                return false;
            default:
                return null;
        }
    }

    /// <summary>按 Python <c>json</c> 的转义规则返回带引号的字符串字面量（供拼装紧凑载荷用）。</summary>
    public static string Quote(string s)
    {
        var sb = new StringBuilder();
        WriteString(s, sb);
        return sb.ToString();
    }

    /// <summary>
    /// 等价 Python <c>json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)</c>——
    /// 用于 CLI 的 <c>--json</c> 面，使 .NET 侧输出与 <c>nf</c> 的输出可逐字节比对。
    /// </summary>
    public static string Indented(object? node, int indent = 2)
    {
        return IndentedOrdered(node, sortKeys: true, indent);
    }

    /// <summary>
    /// 等价 Python <c>json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False)</c>——
    /// **保持插入顺序**（如 <c>nf telemetry --otlp</c> 的 OTLP 形状：resourceSpans → scopeSpans → spans 的顺序本身是语义）。
    /// </summary>
    public static string IndentedUnsorted(object? node, int indent = 2)
    {
        return IndentedOrdered(node, sortKeys: false, indent);
    }

    private static string IndentedOrdered(object? node, bool sortKeys, int indent)
    {
        var sb = new StringBuilder();
        WriteIndentedGraph(node, sb, 0, indent, sortKeys);
        return sb.ToString();
    }

    private static void WriteIndentedGraph(object? node, StringBuilder sb, int level, int indent, bool sortKeys)
    {
        switch (node)
        {
            case Dictionary<string, object?> map when map.Count == 0:
                sb.Append("{}");
                return;
            case Dictionary<string, object?> map:
                sb.Append('{');
                var firstEntry = true;
                var entries = sortKeys
                    ? map.OrderBy(k => k.Key, StringComparer.Ordinal)
                    : map.AsEnumerable();
                foreach (var kv in entries)
                {
                    if (!firstEntry) sb.Append(',');
                    firstEntry = false;
                    sb.Append('\n').Append(' ', (level + 1) * indent);
                    WriteString(kv.Key, sb);
                    sb.Append(": ");
                    WriteIndentedGraph(kv.Value, sb, level + 1, indent, sortKeys);
                }
                sb.Append('\n').Append(' ', level * indent).Append('}');
                return;
            case IReadOnlyList<object?> list when list.Count == 0:
                sb.Append("[]");
                return;
            case IReadOnlyList<object?> list:
                sb.Append('[');
                var firstItem = true;
                foreach (var item in list)
                {
                    if (!firstItem) sb.Append(',');
                    firstItem = false;
                    sb.Append('\n').Append(' ', (level + 1) * indent);
                    WriteIndentedGraph(item, sb, level + 1, indent, sortKeys);
                }
                sb.Append('\n').Append(' ', level * indent).Append(']');
                return;
            default:
                WriteGraph(node, sb);   // 标量（字符串/整数/布尔/null）
                return;
        }
    }

    private static void WriteGraph(object? node, StringBuilder sb, string itemSep = ", ", string kvSep = ": ",
                                   bool sortKeys = true)
    {
        switch (node)
        {
            case null:
                sb.Append("null");
                break;
            case string s:
                WriteString(s, sb);
                break;
            case bool b:
                sb.Append(b ? "true" : "false");
                break;
            case int i:
                sb.Append(i.ToString(CultureInfo.InvariantCulture));
                break;
            case long l:
                sb.Append(l.ToString(CultureInfo.InvariantCulture));
                break;
            case double d:
                sb.Append(PyFloatRepr(d));
                break;
            case Dictionary<string, object?> map:
                sb.Append('{');
                var first = true;
                var entries = sortKeys
                    ? map.OrderBy(k => k.Key, StringComparer.Ordinal)
                    : map.AsEnumerable();
                foreach (var kv in entries)
                {
                    if (!first) sb.Append(itemSep);
                    first = false;
                    WriteString(kv.Key, sb);
                    sb.Append(kvSep);
                    WriteGraph(kv.Value, sb, itemSep, kvSep, sortKeys);
                }
                sb.Append('}');
                break;
            case IReadOnlyList<object?> list:
                sb.Append('[');
                var firstItem = true;
                foreach (var item in list)
                {
                    if (!firstItem) sb.Append(itemSep);
                    firstItem = false;
                    WriteGraph(item, sb, itemSep, kvSep, sortKeys);
                }
                sb.Append(']');
                break;
            default:
                throw new InvalidOperationException("不支持的对象图节点类型：" + node.GetType().Name);
        }
    }

    private static void Write(JsonElement e, StringBuilder sb, HashSet<string>? skipKeys, bool isTop)
    {
        switch (e.ValueKind)
        {
            case JsonValueKind.Object:
                sb.Append('{');
                var first = true;
                if (isTop && skipKeys is not null)
                {
                    foreach (var p in e.EnumerateObject()
                                      .Where(p => !skipKeys.Contains(p.Name))
                                      .OrderBy(p => p.Name, StringComparer.Ordinal))
                    {
                        if (!first) sb.Append(", ");
                        first = false;
                        WriteString(p.Name, sb);
                        sb.Append(": ");
                        Write(p.Value, sb, null, isTop: false);
                    }
                }
                else
                {
                    foreach (var p in e.EnumerateObject().OrderBy(p => p.Name, StringComparer.Ordinal))
                    {
                        if (!first) sb.Append(", ");
                        first = false;
                        WriteString(p.Name, sb);
                        sb.Append(": ");
                        Write(p.Value, sb, null, isTop: false);
                    }
                }
                sb.Append('}');
                break;

            case JsonValueKind.Array:
                sb.Append('[');
                var firstItem = true;
                foreach (var v in e.EnumerateArray())
                {
                    if (!firstItem) sb.Append(", ");
                    firstItem = false;
                    Write(v, sb, null, isTop: false);
                }
                sb.Append(']');
                break;

            case JsonValueKind.String:
                WriteString(e.GetString()!, sb);
                break;

            case JsonValueKind.Number:
                WriteNumber(e, sb);
                break;

            case JsonValueKind.True:
                sb.Append("true");
                break;

            case JsonValueKind.False:
                sb.Append("false");
                break;

            case JsonValueKind.Null:
                sb.Append("null");
                break;

            default:
                throw new InvalidOperationException("不支持的 JSON 值类型：" + e.ValueKind);
        }
    }

    private static void WriteNumber(JsonElement e, StringBuilder sb)
    {
        // 本仓证书面只含整数。出现小数/指数即 fail-closed：Python 的浮点 repr 语义不在本片实现范围。
        if (!e.TryGetInt64(out var value))
        {
            throw new InvalidOperationException(
                "证书面出现非整数数值：" + e.GetRawText() + "（Python 浮点 repr 未在本片实现，按 fail-closed 处理）");
        }
        sb.Append(value.ToString(CultureInfo.InvariantCulture));
    }

    /// <summary>
    /// 等价 Python <c>json.dumps</c> 对浮点的写法（即 <c>repr(float)</c> 的形态）：
    /// 非有限值写 <c>NaN</c> / <c>Infinity</c> / <c>-Infinity</c>（Python 的 <c>allow_nan=True</c>）；
    /// 有限值用最短往返表示，**确保带小数点或指数**——.NET 的 <c>"R"</c> 会把 <c>100000.0</c> 写成
    /// <c>100000</c>（少了小数点），指数大小写也不同，直接用就会与 Python 逐字节不一致。
    /// </summary>
    internal static string PyFloatRepr(double value)
    {
        if (double.IsNaN(value)) return "NaN";
        if (double.IsPositiveInfinity(value)) return "Infinity";
        if (double.IsNegativeInfinity(value)) return "-Infinity";
        var text = value.ToString("R", CultureInfo.InvariantCulture);
        var negative = text.StartsWith('-');
        if (negative) text = text[1..];
        if (text.Contains('E'))
        {
            text = text.Replace("E", "e");
            var index = text.IndexOf('e');
            if (index + 1 < text.Length && text[index + 1] != '+' && text[index + 1] != '-')
                text = text[..(index + 1)] + "+" + text[(index + 1)..];
            return negative ? "-" + text : text;
        }
        if (!text.Contains('.')) text += ".0";
        var parts = text.Split('.');
        if (parts[0].Length >= 17)
        {
            // Python 在整数部分 ≥17 位时切科学计数法（`1e+16`），.NET 的 "R" 仍写定点
            var digits = (parts[0] + parts[1]).TrimEnd('0');
            var mantissa = digits.Length <= 1 ? digits : digits[..1] + "." + digits[1..];
            var scientific = mantissa + "e+" + (parts[0].Length - 1).ToString(CultureInfo.InvariantCulture);
            return negative ? "-" + scientific : scientific;
        }
        return negative ? "-" + text : text;
    }

    private static void WriteString(string s, StringBuilder sb)
    {
        sb.Append('"');
        foreach (var ch in s)
        {
            switch (ch)
            {
                case '"': sb.Append("\\\""); break;
                case '\\': sb.Append("\\\\"); break;
                case '\n': sb.Append("\\n"); break;
                case '\r': sb.Append("\\r"); break;
                case '\t': sb.Append("\\t"); break;
                case '\b': sb.Append("\\b"); break;
                case '\f': sb.Append("\\f"); break;
                default:
                    if (ch < 0x20)
                    {
                        sb.Append("\\u").Append(((int)ch).ToString("x4", CultureInfo.InvariantCulture));
                    }
                    else
                    {
                        // ensure_ascii=False：非 ASCII（含 CJK）原样输出，不转 \uXXXX
                        sb.Append(ch);
                    }
                    break;
            }
        }
        sb.Append('"');
    }
}
