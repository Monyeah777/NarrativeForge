using System.Globalization;
using System.Numerics;
using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// YAML/JSON 标量的**Python 语义**：把裸标量按 PyYAML <c>safe_load</c> 的解析器规则定型
/// （null / bool / int / float / timestamp），并提供 <c>type(x).__name__</c> 的等价名。
///
/// 为什么必须做：Python 侧一律用 PyYAML，`count: 3` 是 **int**、`core_only: true` 是 **bool**；
/// 引擎若把它当字符串，JSON-Schema 的 `type: integer` / `enum: [True]` 就会误判——
/// 这不是"更严"，是**判错**（`schema-clean` 契约会立刻显形）。
///
/// 规则取自 YAML 1.1 的隐式解析器（PyYAML 默认）：`yes/no/on/off` 也是布尔，
/// `010` 是**八进制** 8，`1:30` 是六十进制 90，`2026-09-08` 是**日期**。
/// 带引号的标量不参与定型（由调用方在引号分支提前返回）。
/// </summary>
public static class PyScalar
{
    /// <summary>PyYAML 解析出的日期/时间（<c>type().__name__</c> 为 <c>date</c> / <c>datetime</c>）。</summary>
    public sealed record Timestamp(string Kind, string Raw);

    private static readonly HashSet<string> TrueWords = new(StringComparer.Ordinal)
        { "yes", "Yes", "YES", "true", "True", "TRUE", "on", "On", "ON" };

    private static readonly HashSet<string> FalseWords = new(StringComparer.Ordinal)
        { "no", "No", "NO", "false", "False", "FALSE", "off", "Off", "OFF" };

    private static readonly HashSet<string> NullWords = new(StringComparer.Ordinal)
        { "", "~", "null", "Null", "NULL" };

    private static readonly Regex IntRe = new(
        @"^(?:[-+]?0b[0-1_]+|[-+]?0[0-7_]+|[-+]?(?:0|[1-9][0-9_]*)|[-+]?0x[0-9a-fA-F_]+|[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$",
        RegexOptions.CultureInvariant);

    private static readonly Regex FloatRe = new(
        // 注意：PyYAML 的指数**要求显式符号**（`1.0e5` 不是浮点、仍算字符串）——照抄这个怪癖
        @"^(?:[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?|\.[0-9_]+(?:[eE][-+][0-9]+)?|" +
        @"[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$",
        RegexOptions.CultureInvariant);

    private static readonly Regex DateRe = new(
        // PyYAML 的**纯日期**形态要求月/日都是两位（`2026-9-8` 会被当字符串，`2026-09-08` 才是 date）
        @"^[0-9]{4}-[0-9][0-9]-[0-9][0-9]$", RegexOptions.CultureInvariant);

    private static readonly Regex DateTimeRe = new(
        @"^[0-9]{4}-[0-9][0-9]?-[0-9][0-9]?(?:[Tt]|[ \t]+)[0-9][0-9]?:[0-9][0-9]:[0-9][0-9]" +
        @"(?:\.[0-9]*)?(?:[ \t]*(?:Z|[-+][0-9][0-9]?(?::[0-9][0-9])?))?$",
        RegexOptions.CultureInvariant);

    /// <summary>裸标量 → Python 值（null / bool / long / double / <see cref="Timestamp"/> / string）。</summary>
    /// <summary>
    /// YAML 标量取值（`key: 值` 的右侧）：带引号取引号内；否则截掉行尾注释（` #` 起）。
    /// 供 protocol.yaml 的**定向抽取**复用（真源走 PyYAML；引擎 YAML 子集不保证嵌套映射）。
    /// </summary>
    public static string YamlScalar(string raw)
    {
        var text = raw.Trim();
        if (text.Length == 0) return "";
        if (text[0] is '"' or '\'')
        {
            var quote = text[0];
            var end = text.IndexOf(quote, 1);
            return end < 0 ? text[1..] : text[1..end];
        }
        var hash = text.IndexOf(" #", StringComparison.Ordinal);
        if (hash >= 0) text = text[..hash];
        return text.TrimEnd();
    }

    public static object? Resolve(string raw)
    {
        if (NullWords.Contains(raw)) return null;
        if (TrueWords.Contains(raw)) return true;
        if (FalseWords.Contains(raw)) return false;
        if (IntRe.IsMatch(raw)) return ToInt(raw);
        if (FloatRe.IsMatch(raw)) return ToFloat(raw);
        if (DateRe.IsMatch(raw)) return new Timestamp("date", raw);
        if (DateTimeRe.IsMatch(raw)) return new Timestamp("datetime", raw);
        return raw;
    }

    private static long ToInt(string raw)
    {
        var s = raw.Replace("_", "");
        var negative = s.StartsWith('-');
        var body = s.TrimStart('+', '-');
        if (body.StartsWith("0b", StringComparison.OrdinalIgnoreCase))
            return Sign(Convert.ToInt64(body[2..], 2), negative);
        if (body.StartsWith("0x", StringComparison.OrdinalIgnoreCase))
            return Sign(Convert.ToInt64(body[2..], 16), negative);
        if (body.Length > 1 && body[0] == '0')               // YAML 1.1：前导 0 = 八进制
            return Sign(Convert.ToInt64(body[1..], 8), negative);
        if (body.Contains(':'))                              // 六十进制
        {
            long acc = 0;
            foreach (var part in body.Split(':')) acc = acc * 60 + long.Parse(part, CultureInfo.InvariantCulture);
            return Sign(acc, negative);
        }
        return Sign(long.Parse(body, CultureInfo.InvariantCulture), negative);
    }

    private static double ToFloat(string raw)
    {
        var s = raw.Replace("_", "");
        var negative = s.StartsWith('-');
        var body = s.TrimStart('+', '-');
        // PyYAML 的特殊值**必须带点**：`.inf/.Inf/.INF`、`.nan/.NaN/.NAN`（可带符号）。
        // 裸 `NaN`/`inf` 是**字符串**（此前把裸 NaN 当浮点、且 `.NaN` 落到 double.Parse 抛
        // FormatException → 进程级异常，属真 bug）。
        if (body is ".inf" or ".Inf" or ".INF") return negative ? double.NegativeInfinity : double.PositiveInfinity;
        if (body is ".nan" or ".NaN" or ".NAN") return double.NaN;
        if (body.Contains(':'))
        {
            double acc = 0;
            var parts = body.Split(':');
            for (var i = 0; i < parts.Length; i++)
                acc = acc * 60 + double.Parse(parts[i], CultureInfo.InvariantCulture);
            return negative ? -acc : acc;
        }
        var value = double.Parse(body, CultureInfo.InvariantCulture);
        return negative ? -value : value;
    }

    private static long Sign(long value, bool negative) => negative ? -value : value;

    /// <summary>等价 Python <c>len(str)</c>：数**码点**，不是 UTF-16 代码单元（非 BMP 字符会差一）。
    /// 为什么单列：`sha256` 可以相同而 `chars` 不同——只有按码点计数才对得上。</summary>
    public static int PyLen(string text)
    {
        var count = 0;
        for (var i = 0; i < text.Length; i++)
        {
            if (char.IsHighSurrogate(text[i]) && i + 1 < text.Length && char.IsLowSurrogate(text[i + 1])) i++;
            count++;
        }
        return count;
    }

    /// <summary>等价 Python 切片 <c>s[:n]</c>（按码点截断，不劈开代理对）。</summary>
    public static string PySlice(string text, int maxCodePoints)
    {
        var count = 0;
        for (var i = 0; i < text.Length; i++)
        {
            if (char.IsHighSurrogate(text[i]) && i + 1 < text.Length && char.IsLowSurrogate(text[i + 1])) i++;
            count++;
            if (count == maxCodePoints) return text[..(i + 1)];
        }
        return text;
    }

    /// <summary>等价 Python <c>type(x).__name__</c>（用于把判错文案对齐到 Python）。</summary>
    public static string TypeName(object? value) => value switch
    {
        null => "NoneType",
        bool => "bool",
        string => "str",
        int => "int",
        long => "int",
        double => "float",
        float => "float",
        Dictionary<string, object?> => "dict",
        IReadOnlyDictionary<string, object?> => "dict",
        List<object?> => "list",
        IReadOnlyList<object?> => "list",
        Timestamp ts => ts.Kind,
        _ => value.GetType().Name,
    };

    /// <summary>Python <c>==</c> 等价（含 <c>True == 1</c> 这类跨类型相等），用于 <c>enum</c> 判定。</summary>
    public static bool PyEquals(object? a, object? b)
    {
        if (a is null || b is null) return a is null && b is null;
        if (a is bool ab && b is bool bb) return ab == bb;
        if (a is bool || b is bool)
        {
            var other = a is bool ? b : a;
            var flag = a is bool ? (bool)a : (bool)b;
            return other switch
            {
                long l => flag ? l == 1 : l == 0,
                int i => flag ? i == 1 : i == 0,
                double d => flag ? d == 1.0 : d == 0.0,
                _ => false,
            };
        }
        if (a is string sa && b is string sb) return string.Equals(sa, sb, StringComparison.Ordinal);
        // 注意 **int 也算数**：引擎内部有的字段是 C# `int`（如 Combinator 的 module_count），
        // 而从 JSON 读回来的同一字段是 `long`——漏了 int 就会把"6 与 6 相等"判成不等
        // （首版正是这样让 17 条在盘证书全报"字段不一致：module_count（复算 6 ≠ 在盘 6）"）。
        if (a is (long or int or double) && b is (long or int or double))
            return Convert.ToDouble(a, CultureInfo.InvariantCulture)
                   == Convert.ToDouble(b, CultureInfo.InvariantCulture);
        if (a is Timestamp ta && b is Timestamp tb) return ta.Raw == tb.Raw;
        if (a is List<object?> la && b is List<object?> lb)
            return la.Count == lb.Count && la.Zip(lb).All(p => PyEquals(p.First, p.Second));
        if (a is Dictionary<string, object?> ma && b is Dictionary<string, object?> mb)
            return ma.Count == mb.Count && ma.All(kv => mb.TryGetValue(kv.Key, out var other) && PyEquals(kv.Value, other));
        return a.Equals(b);
    }

    /// <summary>
    /// Python <c>repr(x)</c> 等价（判错文案里要用它，如 <c>值 'x' 不在枚举 ['a', 'b']</c>）。
    /// 覆盖本引擎会遇到的类型；控制字符写 <c>\xNN</c>，非 ASCII 可打印字符原样保留（同 Python 3）。
    /// </summary>
    public static string PyRepr(object? value) => value switch
    {
        null => "None",
        bool b => b ? "True" : "False",
        string s => StrRepr(s),
        long l => l.ToString(CultureInfo.InvariantCulture),
        int i => i.ToString(CultureInfo.InvariantCulture),
        double d => PythonJson.PyFloatRepr(d),
        Dictionary<string, object?> map => "{" + string.Join(", ",
            map.Select(kv => StrRepr(kv.Key) + ": " + PyRepr(kv.Value))) + "}",
        List<object?> list => "[" + string.Join(", ", list.Select(PyRepr)) + "]",
        _ => value.ToString() ?? "None",
    };

    /// <summary>Python <c>repr(str)</c>：优先单引号；串内已有单引号且无双引号时改用双引号。</summary>
    private static string StrRepr(string s)
    {
        var quote = s.Contains('\'') && !s.Contains('"') ? '"' : '\'';
        var sb = new System.Text.StringBuilder();
        sb.Append(quote);
        for (var i = 0; i < s.Length; i++)
        {
            var c = s[i];
            // 码点口径：代理对按一个码点处理（Python repr 也按码点判定可打印性），
            // 落单代理按单字符处理（它的 Python 类别是 Cs → 非可打印 → 转义）。
            var isPair = char.IsHighSurrogate(c) && i + 1 < s.Length && char.IsLowSurrogate(s[i + 1]);
            var codePoint = isPair ? char.ConvertToUtf32(c, s[i + 1]) : c;
            if (isPair) i++;
            switch (c)
            {
                case '\\': sb.Append("\\\\"); break;
                case '\n': sb.Append("\\n"); break;
                case '\r': sb.Append("\\r"); break;
                case '\t': sb.Append("\\t"); break;
                default:
                    if (c == quote && !isPair) sb.Append('\\').Append(c);
                    else if (IsPyPrintable(codePoint, isPair))
                        sb.Append(isPair ? char.ConvertFromUtf32(codePoint) : c.ToString());
                    else sb.Append(EscapeCodePoint(codePoint));
                    break;
            }
        }
        sb.Append(quote);
        return sb.ToString();
    }

    /// <summary>
    /// Python <c>str.isprintable()</c> 的判定：非可打印 = Unicode 类别 <c>C*</c> 与 <c>Z*</c>，
    /// **唯 ASCII 空格 (0x20) 例外**。（Python 3 的 <c>repr</c> 正是按这条决定要不要转义。）
    /// </summary>
    private static bool IsPyPrintable(int codePoint, bool isPair)
    {
        if (codePoint == 0x20) return true;
        var category = isPair
            ? Rune.GetUnicodeCategory(new Rune(codePoint))
            : CharUnicodeInfo.GetUnicodeCategory((char)codePoint);
        return category switch
        {
            UnicodeCategory.Control or UnicodeCategory.Format or UnicodeCategory.Surrogate
                or UnicodeCategory.PrivateUse or UnicodeCategory.OtherNotAssigned
                or UnicodeCategory.LineSeparator or UnicodeCategory.ParagraphSeparator
                or UnicodeCategory.SpaceSeparator => false,
            _ => true,
        };
    }

    /// <summary>Python repr 的转义宽度：<c>\xNN</c>（≤0xFF）/ <c>\uNNNN</c>（≤0xFFFF）/ <c>\UNNNNNNNN</c>。</summary>
    private static string EscapeCodePoint(int codePoint) => codePoint switch
    {
        <= 0xFF => "\\x" + codePoint.ToString("x2", CultureInfo.InvariantCulture),
        <= 0xFFFF => "\\u" + codePoint.ToString("x4", CultureInfo.InvariantCulture),
        _ => "\\U" + codePoint.ToString("x8", CultureInfo.InvariantCulture),
    };

    /// <summary>
    /// Python <c>round(x, n)</c> 的**正确舍入**语义（tie→even），用于取代
    /// <c>Math.Round(double, int)</c>——后者内部是「×10ⁿ 再取整再 ÷10ⁿ」的**缩放法**，
    /// 在恰好压在中点的值上会与 CPython 分道扬镳（实测：<c>classification.macro.recall</c>
    /// 上 .NET 给 0.833334、Python 给 0.833333）。
    ///
    /// 做法：把 double 拆成 <c>m·2^e</c>（<c>m</c> 为整数），用 <see cref="BigInteger"/> 构造
    /// <c>x·10ⁿ = 分子/分母</c> 的**精确有理数**，按「余数×2 与分母比较 + 平局取偶」定舍入，
    /// 再把整数结果写成十进制串交给 <c>double.Parse</c>（.NET Core 的正确舍入解析）——
    /// **一次舍入到位**，不做二次双重舍入。
    /// </summary>
    public static double PyRound(double value, int digits)
    {
        if (double.IsNaN(value) || double.IsInfinity(value) || value == 0.0) return value;
        var bits = BitConverter.DoubleToInt64Bits(value);
        var negative = bits < 0;
        var exponentBits = (int)((bits >> 52) & 0x7FF);
        var mantissaBits = bits & 0xFFFFFFFFFFFFFL;
        long exponent;
        BigInteger mantissa;
        if (exponentBits == 0)
        {
            exponent = -1074;
            mantissa = mantissaBits;
        }
        else
        {
            exponent = exponentBits - 1075;
            mantissa = mantissaBits | (1L << 52);
        }
        if (mantissa.IsZero) return value;

        BigInteger numerator, denominator;
        if (digits >= 0)
        {
            numerator = mantissa * BigInteger.Pow(10, digits);
            denominator = BigInteger.One;
        }
        else
        {
            numerator = mantissa;
            denominator = BigInteger.Pow(10, -digits);
        }
        if (exponent >= 0) numerator <<= (int)exponent;
        else denominator <<= (int)(-exponent);

        var quotient = BigInteger.DivRem(numerator, denominator, out var remainder);
        var twice = remainder * 2;
        var cmp = twice.CompareTo(denominator);
        if (cmp > 0 || (cmp == 0 && !quotient.IsEven)) quotient += 1;

        var digitsText = quotient.ToString(System.Globalization.CultureInfo.InvariantCulture);
        string text;
        if (digits > 0)
        {
            if (digitsText.Length <= digits) digitsText = new string('0', digits - digitsText.Length + 1) + digitsText;
            var cut = digitsText.Length - digits;
            text = digitsText[..cut] + "." + digitsText[cut..];
        }
        else
        {
            text = digitsText + new string('0', -digits);
        }
        var parsed = double.Parse(text, System.Globalization.NumberStyles.Float,
            System.Globalization.CultureInfo.InvariantCulture);
        return negative ? -parsed : parsed;
    }
}
