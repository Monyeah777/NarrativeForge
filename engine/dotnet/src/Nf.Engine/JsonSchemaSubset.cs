using System.Globalization;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/output_forms.py::json_schema_check</c>：JSON Schema 2020-12 的**子集**校验器
/// （另见 <c>schema_lint</c> 那套 check28 用的子集——**两套关键字集合不同，不可互相替代**，各自照抄真源）。
///
/// 子集边界是**公开声明**：不在 <see cref="Supported"/> 里的关键字，凡属"条件/内容编码/dynamic"族或 <c>$</c> 开头，
/// 一律进 <c>unsupported</c> 清单——「不支持」绝不等价「通过」（真源注释原文）。
/// 类型错误文案里的 Python 类型名（<c>dict/list/str/bool/int/float/NoneType</c>）逐字对齐，
/// 因为它是**被比对的输出**（`output check` 的 issues 会打到 stdout）。
/// </summary>
public static class JsonSchemaSubset
{
    private static readonly HashSet<string> Supported = new(StringComparer.Ordinal)
    {
        "$schema", "$id", "$ref", "$defs", "definitions", "title", "description",
        "type", "enum", "const", "properties", "patternProperties", "required",
        "additionalProperties", "items", "prefixItems", "minItems", "maxItems",
        "uniqueItems", "minLength", "maxLength", "pattern", "format", "minimum",
        "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
        "allOf", "anyOf", "oneOf", "not", "propertyNames", "dependentRequired",
    };

    private static readonly HashSet<string> UnsupportedWords = new(StringComparer.Ordinal)
    {
        "if", "then", "else", "contains", "minContains", "maxContains",
        "unevaluatedProperties", "unevaluatedItems", "dependentSchemas",
        "$dynamicRef", "$dynamicAnchor", "contentEncoding", "contentMediaType",
    };

    public static List<string> Check(object? instance, Dictionary<string, object?> schema,
        string path = "$", Dictionary<string, object?>? rootSchema = null, List<string>? unsupported = null)
    {
        rootSchema ??= schema;
        unsupported ??= new List<string>();
        var errors = new List<string>();

        // `set(schema) - _SUPPORTED` 排序后逐个：属"不支持词"或 `$` / 开头 → 记 unsupported（去重）
        foreach (var kw in schema.Keys.Where(k => !Supported.Contains(k))
                     .OrderBy(k => k, StringComparer.Ordinal))
        {
            if (!UnsupportedWords.Contains(kw) && !kw.StartsWith("$", StringComparison.Ordinal)) continue;
            var tag = $"{kw}@{path}";
            if (!unsupported.Contains(tag)) unsupported.Add(tag);
        }

        if (schema.TryGetValue("$ref", out var refValue))
        {
            var target = ResolveRef(PyStr(refValue), rootSchema);
            if (target is null) unsupported.Add($"远程/悬空 $ref {PyStr(refValue)}@{path}");
            else errors.AddRange(Check(instance, target, path, rootSchema, unsupported));
        }

        if (schema.TryGetValue("type", out var types) && types is not null)
        {
            var cand = types is List<object?> list ? list : new List<object?> { types };
            if (!cand.Any(t => TypeOk(instance, PyStr(t))))
                errors.Add($"{path}: 类型应为 {string.Join("/", cand.Select(PyStr))}，实为 {PyTypeName(instance)}");
        }

        if (schema.TryGetValue("const", out var konst) && !PyScalar.PyEquals(instance, konst))
            errors.Add($"{path}: 应为常量 {PyScalar.PyRepr(konst)}");

        if (schema.TryGetValue("enum", out var enumValue) && enumValue is List<object?> choices
            && !choices.Any(c => PyScalar.PyEquals(instance, c)))
            errors.Add($"{path}: 取值 {PyScalar.PyRepr(instance)} 不在枚举内");

        if (instance is string text)
        {
            if (Num(schema.GetValueOrDefault("minLength")) is { } minLen && PyScalar.PyLen(text) < minLen)
                errors.Add($"{path}: 长度 < {PyStr(schema.GetValueOrDefault("minLength"))}");
            if (Num(schema.GetValueOrDefault("maxLength")) is { } maxLen && PyScalar.PyLen(text) > maxLen)
                errors.Add($"{path}: 长度 > {PyStr(schema.GetValueOrDefault("maxLength"))}");
            if (schema.TryGetValue("pattern", out var pattern)
                && !Regex.IsMatch(text, PyStr(pattern), RegexOptions.CultureInvariant))
                errors.Add($"{path}: 不匹配 pattern {PyStr(pattern)}");
            var fmt = PyStr(schema.GetValueOrDefault("format"));
            if (fmt.Length > 0) errors.AddRange(FormatErrors(text, fmt, path));
        }

        if (IsNumber(instance))
        {
            foreach (var (kw, op, cmp) in Comparisons)
            {
                if (schema.GetValueOrDefault(kw) is null) continue;
                var bound = Convert.ToDouble(schema.GetValueOrDefault(kw), CultureInfo.InvariantCulture);
                var value = Convert.ToDouble(instance, CultureInfo.InvariantCulture);
                if (!cmp(value, bound)) errors.Add($"{path}: {PyStr(instance)} {op} {PyStr(schema.GetValueOrDefault(kw))} 不成立");
            }
            if (Num(schema.GetValueOrDefault("multipleOf")) is { } step && step != 0)
            {
                var q = Convert.ToDouble(instance, CultureInfo.InvariantCulture) / step;
                if (Math.Abs(q - Math.Round(q, MidpointRounding.ToEven)) > 1e-9)
                    errors.Add($"{path}: 非 {PyStr(schema.GetValueOrDefault("multipleOf"))} 的整数倍");
            }
        }

        if (instance is List<object?> items)
        {
            if (Num(schema.GetValueOrDefault("minItems")) is { } minItems && items.Count < minItems)
                errors.Add($"{path}: 元素数 < {PyStr(schema.GetValueOrDefault("minItems"))}");
            if (Num(schema.GetValueOrDefault("maxItems")) is { } maxItems && items.Count > maxItems)
                errors.Add($"{path}: 元素数 > {PyStr(schema.GetValueOrDefault("maxItems"))}");
            if (PyTruthy(schema.GetValueOrDefault("uniqueItems")))
            {
                var seen = items.Select(x => PythonJson.CanonicalizeGraph(x)).ToList();
                if (seen.Distinct(StringComparer.Ordinal).Count() != seen.Count)
                    errors.Add($"{path}: uniqueItems 被违反");
            }
            var prefix = schema.GetValueOrDefault("prefixItems") as List<object?>;
            if (prefix is not null)
            {
                for (var i = 0; i < prefix.Count && i < items.Count; i++)
                    if (prefix[i] is Dictionary<string, object?> sub)
                        errors.AddRange(Check(items[i], sub, $"{path}[{i}]", rootSchema, unsupported));
            }
            if (schema.GetValueOrDefault("items") is Dictionary<string, object?> itemSchema)
            {
                var start = prefix?.Count ?? 0;
                for (var i = start; i < items.Count; i++)
                    errors.AddRange(Check(items[i], itemSchema, $"{path}[{i}]", rootSchema, unsupported));
            }
        }

        if (instance is Dictionary<string, object?> map)
        {
            var props = schema.GetValueOrDefault("properties") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            var pats = schema.GetValueOrDefault("patternProperties") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            if (schema.GetValueOrDefault("required") is List<object?> required)
                foreach (var key in required)
                    if (!map.ContainsKey(PyStr(key)))
                        errors.Add($"{path}: 缺必填字段 {PyStr(key)}");
            if (schema.GetValueOrDefault("dependentRequired") is Dictionary<string, object?> deps)
                foreach (var (dep, need) in deps)
                {
                    if (!map.ContainsKey(dep)) continue;
                    foreach (var n in need as List<object?> ?? new List<object?>())
                        if (!map.ContainsKey(PyStr(n)))
                            errors.Add($"{path}: 出现 {dep} 时必填 {PyStr(n)}");
                }
            foreach (var (key, value) in map)
            {
                var matched = false;
                if (props.TryGetValue(key, out var sub))
                {
                    matched = true;
                    if (sub is Dictionary<string, object?> subMap)
                        errors.AddRange(Check(value, subMap, $"{path}.{key}", rootSchema, unsupported));
                }
                foreach (var (pat, patSchema) in pats)
                {
                    if (!Regex.IsMatch(key, pat, RegexOptions.CultureInvariant)) continue;
                    matched = true;
                    if (patSchema is Dictionary<string, object?> patMap)
                        errors.AddRange(Check(value, patMap, $"{path}.{key}", rootSchema, unsupported));
                }
                if (matched) continue;
                var ap = schema.TryGetValue("additionalProperties", out var apv) ? apv : true;
                if (ap is bool apBool)
                {
                    if (!apBool) errors.Add($"{path}: 多余字段 {key}（additionalProperties=false）");
                }
                else if (ap is Dictionary<string, object?> apSchema)
                {
                    errors.AddRange(Check(value, apSchema, $"{path}.{key}", rootSchema, unsupported));
                }
            }
            if (schema.GetValueOrDefault("propertyNames") is Dictionary<string, object?> nameSchema)
                foreach (var key in map.Keys)
                    errors.AddRange(Check(key, nameSchema, $"{path}<键:{key}>", rootSchema, unsupported));
        }

        foreach (var (kw, mode) in new[] { ("allOf", "all"), ("anyOf", "any"), ("oneOf", "one") })
        {
            if (schema.GetValueOrDefault(kw) is not List<object?> subs) continue;
            var results = subs.OfType<Dictionary<string, object?>>()
                .Select(s => Check(instance, s, path, rootSchema, unsupported)).ToList();
            var ok = results.Count(r => r.Count == 0);
            if (mode == "all" && ok != subs.Count)
                errors.Add($"{path}: allOf 有 {subs.Count - ok}/{subs.Count} 子式不成立");
            if (mode == "any" && ok == 0) errors.Add($"{path}: anyOf 全不成立");
            if (mode == "one" && ok != 1) errors.Add($"{path}: oneOf 命中 {ok} 个（须恰 1）");
        }

        if (schema.GetValueOrDefault("not") is Dictionary<string, object?> notSchema
            && Check(instance, notSchema, path, rootSchema, unsupported).Count == 0)
            errors.Add($"{path}: not 子式被满足");

        return errors;
    }

    private static readonly (string Kw, string Op, Func<double, double, bool> Cmp)[] Comparisons =
    {
        ("minimum", ">=", (a, b) => a >= b),
        ("maximum", "<=", (a, b) => a <= b),
        ("exclusiveMinimum", ">", (a, b) => a > b),
        ("exclusiveMaximum", "<", (a, b) => a < b),
    };

    private static List<string> FormatErrors(string value, string fmt, string path) => fmt switch
    {
        "date" => Regex.IsMatch(value, @"^\d{4}-\d{2}-\d{2}$") ? new List<string>() : new List<string> { $"{path}: 非 ISO 8601 日期" },
        "date-time" => Regex.IsMatch(value, @"^\d{4}-\d{2}-\d{2}[Tt ].+$")
            ? new List<string>() : new List<string> { $"{path}: 非 ISO 8601 日期时间" },
        "uri" => Regex.IsMatch(value, @"^[a-zA-Z][a-zA-Z0-9+.-]*:")
            ? new List<string>() : new List<string> { $"{path}: 非绝对 URI" },
        _ => new List<string>(),
    };

    /// <summary>只支持本地引用（<c>#/$defs/x</c>、<c>#/definitions/x</c>）；远程由调用方记 unsupported。</summary>
    private static Dictionary<string, object?>? ResolveRef(string reference, Dictionary<string, object?> rootSchema)
    {
        if (!reference.StartsWith("#/", StringComparison.Ordinal)) return null;
        object? node = rootSchema;
        foreach (var raw in reference[2..].Split('/'))
        {
            var part = raw.Replace("~1", "/").Replace("~0", "~");
            if (node is Dictionary<string, object?> map && map.TryGetValue(part, out var next)) node = next;
            else return null;
        }
        return node as Dictionary<string, object?>;
    }

    private static bool TypeOk(object? value, string want)
    {
        if (want is "number" or "integer" && value is bool) return false;
        return want switch
        {
            "object" => value is Dictionary<string, object?>,
            "array" => value is List<object?>,
            "string" => value is string,
            "boolean" => value is bool,
            "number" => IsNumber(value),
            "integer" => value is long or int,
            "null" => value is null,
            _ => true,
        };
    }

    private static bool IsNumber(object? v) => v is long or int or double;

    private static double? Num(object? v) => v switch
    {
        long l => l,
        int i => i,
        double d => d,
        bool b => b ? 1 : 0,
        _ => null,
    };

    private static bool PyTruthy(object? v) => v switch
    {
        null => false,
        bool b => b,
        string s => s.Length > 0,
        long l => l != 0,
        double d => d != 0,
        List<object?> list => list.Count > 0,
        Dictionary<string, object?> map => map.Count > 0,
        _ => true,
    };

    /// <summary>Python <c>type(x).__name__</c>（错误文案里会打出来，须逐字对齐）。</summary>
    private static string PyTypeName(object? v) => v switch
    {
        null => "NoneType",
        bool => "bool",
        string => "str",
        long or int => "int",
        double => "float",
        List<object?> => "list",
        Dictionary<string, object?> => "dict",
        _ => "object",
    };

    private static string PyStr(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(CultureInfo.InvariantCulture),
        int i => i.ToString(CultureInfo.InvariantCulture),
        double d => PythonJson.PyFloatRepr(d),
        _ => PyScalar.PyRepr(v),
    };
}
