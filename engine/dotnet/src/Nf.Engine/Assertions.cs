using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/assertions.py</c>：数据化断言表 runner（真源 <c>protocol/assertions.json</c>）。
/// kind 是**封闭集**（4 种），只做确定性形状判定；表自身也先过一遍合法性（scan）。
/// </summary>
public static class Assertions
{
    public const string DeclRel = "protocol/assertions.json";
    public const string Schema = "nf-assertions/1";

    private static readonly string[] Severities = { "fail", "warn" };
    private static readonly string[] KindOrder = { "regex_absent", "regex_present", "count_at_least", "json_value" };
    private static readonly string[] Required = { "id", "severity", "kind", "params", "message", "fix" };

    public sealed record RunResult(List<object?> Results, List<string> Issues);

    public static RunResult Run(string root)
    {
        var declaration = Load(root);
        var issues = new List<string>();
        var results = new List<object?>();
        if (declaration is null)
        {
            issues.Add("缺断言表 " + DeclRel);
            return new RunResult(results, issues);
        }
        using (declaration)
        {
        var doc = declaration.RootElement;

        Scan(doc, issues);

        foreach (var assertion in doc.GetProperty("assertions").EnumerateArray())
        {
            var id = Str(assertion, "id");
            var severity = Str(assertion, "severity");
            var kind = Str(assertion, "kind");
            var parameters = assertion.TryGetProperty("params", out var p) ? p : default;

            bool ok;
            string detail;
            if (Array.IndexOf(KindOrder, kind) < 0)
            {
                issues.Add($"断言 {id} 的 kind 不在封闭集：{kind}");
                continue;
            }
            try
            {
                (ok, detail) = Evaluate(root, kind, parameters);
            }
            catch (Exception exc)
            {
                ok = false;
                detail = "断言执行异常：" + exc.Message;
            }

            results.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = id,
                ["severity"] = severity,
                ["kind"] = kind,
                ["ok"] = ok,
                ["detail"] = detail,
                ["message"] = Str(assertion, "message"),
                ["fix"] = Str(assertion, "fix"),
                ["evidence"] = Str(assertion, "evidence"),
            });
            if (!ok && severity == "fail")
            {
                issues.Add($"{id} 不通过：{detail}（修复指引：{Str(assertion, "fix")}）");
            }
        }
        return new RunResult(results, issues);
        }
    }

    private static void Scan(JsonElement doc, List<string> issues)
    {
        if (Str(doc, "schema") != Schema) issues.Add($"断言表 schema 不匹配（期望 {Schema}）");
        if (!SequenceEquals(doc, "severity_vocabulary", Severities))
            issues.Add("severity 词表与判据不一致（期望 " + string.Join("/", Severities) + "）");
        if (!SequenceEquals(doc, "kind_vocabulary", KindOrder))
            issues.Add("kind 词表必须与 runner 封闭集逐项一致（" + string.Join("/", KindOrder) + "）");

        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var assertion in doc.GetProperty("assertions").EnumerateArray())
        {
            var id = Str(assertion, "id");
            foreach (var field in Required)
            {
                if (!assertion.TryGetProperty(field, out var value) || IsFalsy(value))
                    issues.Add($"断言 {(id.Length == 0 ? "(无名)" : id)} 缺必填字段：{field}");
            }
            if (!seen.Add(id)) issues.Add("断言 id 重复：" + id);
            var severity = Str(assertion, "severity");
            if (Array.IndexOf(Severities, severity) < 0)
                issues.Add($"断言 {id} severity 越词表：{severity}");
            var kind = Str(assertion, "kind");
            if (Array.IndexOf(KindOrder, kind) < 0)
                issues.Add($"断言 {id} kind 不在封闭集：{kind}");
            if (Str(assertion, "fix").Trim().Length == 0)
                issues.Add($"断言 {id} 缺 fix（无修复指引不许入表）");
        }
    }

    private static (bool Ok, string Detail) Evaluate(string root, string kind, JsonElement p) => kind switch
    {
        "regex_absent" => RegexAbsent(root, p),
        "regex_present" => RegexPresent(root, p),
        "count_at_least" => CountAtLeast(root, p),
        "json_value" => JsonValue(root, p),
        _ => (false, "未知 kind：" + kind),
    };

    private static (bool, string) RegexAbsent(string root, JsonElement p)
    {
        var pattern = new Regex(Str(p, "pattern"));
        var hits = new List<string>();
        if (p.ValueKind == JsonValueKind.Object && p.TryGetProperty("globs", out var globs))
        {
            foreach (var glob in globs.EnumerateArray())
            {
                foreach (var file in Glob(root, glob.GetString()!))
                {
                    // 命中路径按 Python 口径渲染：`str(Path(root) / 相对路径)`（原生分隔符，
                    // 且"."成分与尾随分隔符被正规化掉）——不是仓库相对 posix 路径
                    if (pattern.IsMatch(ReadText(file))) hits.Add(PyJoined(root, Relative(root, file)));
                }
            }
        }
        return hits.Count == 0
            ? (true, "零命中")
            : (false, "命中：" + string.Join(", ", hits.Take(2)));
    }

    private static (bool, string) RegexPresent(string root, JsonElement p)
    {
        var rel = Str(p, "path");
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return (false, "目标件不存在：" + rel);
        var text = ReadText(path);
        var patterns = p.TryGetProperty("patterns", out var list)
            ? list.EnumerateArray().Select(x => x.GetString()!).ToList()
            : new List<string>();
        var missing = patterns.Where(x => !text.Contains(x, StringComparison.Ordinal)).ToList();
        return missing.Count == 0
            ? (true, $"{patterns.Count} 锚点齐")
            : (false, "缺：" + string.Join(", ", missing.Take(3)));
    }

    private static (bool, string) CountAtLeast(string root, JsonElement p)
    {
        var count = Glob(root, Str(p, "glob")).Count;
        var want = p.TryGetProperty("min", out var m) && m.TryGetInt32(out var v) ? v : 0;
        return (count >= want, $"{count} ≥ {want}");
    }

    private static (bool, string) JsonValue(string root, JsonElement p)
    {
        var rel = Str(p, "path");
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return (false, "目标件不存在：" + rel);

        JsonDocument doc;
        try
        {
            doc = JsonIo.ReadFile(path);
        }
        catch (JsonException exc)
        {
            return (false, "JSON 不可解析：" + exc.Message);
        }

        using (doc)
        {
            var current = doc.RootElement;
            var keyPath = Str(p, "key");
            foreach (var part in keyPath.Split('.'))
            {
                if (current.ValueKind != JsonValueKind.Object || !current.TryGetProperty(part, out var next))
                    return (false, "缺键：" + keyPath);
                current = next;
            }

            var op = Str(p, "op");
            var value = p.TryGetProperty("value", out var v) ? v : default;
            switch (op)
            {
                case "exists":
                    return (true, "键在场");
                case "nonempty":
                    var nonEmpty = IsTruthy(current);
                    return (nonEmpty, nonEmpty ? "非空" : "空值");
                case "equals":
                    var equal = JsonEquals(current, value);
                    return (equal, "= " + JsonPreview(value));
                case "in_vocab":
                    var inVocab = value.ValueKind == JsonValueKind.Array &&
                                  value.EnumerateArray().Any(x => x.GetString() == current.GetString());
                    return (inVocab, inVocab ? $"{current.GetString()} ∈ 词表" : $"{current.GetString()} 越词表");
                case "contains_keys":
                    var required = value.ValueKind == JsonValueKind.Array
                        ? value.EnumerateArray().Select(x => x.GetString()!).ToList()
                        : new List<string>();
                    var missing = required.Where(k => current.ValueKind != JsonValueKind.Object ||
                                                      !current.TryGetProperty(k, out _)).ToList();
                    return missing.Count == 0
                        ? (true, "键齐")
                        : (false, "缺：" + string.Join(", ", missing));
                default:
                    return (false, $"未知 op：{op}（封闭集：exists/nonempty/equals/in_vocab/contains_keys）");
            }
        }
    }

    // ---------------------------------------------------------------- 工具

    private static JsonDocument? Load(string root)
    {
        var path = Path.Combine(root, DeclRel.Replace('/', Path.DirectorySeparatorChar));
        return File.Exists(path) ? JsonIo.ReadFile(path) : null;
    }

    private static string Str(JsonElement element, string name)
        => element.ValueKind == JsonValueKind.Object && element.TryGetProperty(name, out var v) &&
           v.ValueKind == JsonValueKind.String
            ? v.GetString()!
            : "";

    /// <summary>Python 真值语义（[] / {} / "" / 0 / false / null 为假）。</summary>
    private static bool IsFalsy(JsonElement value) => !IsTruthy(value);

    private static bool IsTruthy(JsonElement value) => value.ValueKind switch
    {
        JsonValueKind.Array => value.GetArrayLength() > 0,
        JsonValueKind.Object => value.EnumerateObject().Any(),
        JsonValueKind.String => value.GetString()!.Length > 0,
        JsonValueKind.Number => value.GetDouble() != 0,
        JsonValueKind.True => true,
        _ => false,
    };

    private static bool JsonEquals(JsonElement a, JsonElement b)
    {
        if (a.ValueKind != b.ValueKind)
        {
            return a.ValueKind == JsonValueKind.Number && b.ValueKind == JsonValueKind.Number;
        }
        return a.ValueKind switch
        {
            JsonValueKind.String => a.GetString() == b.GetString(),
            JsonValueKind.Number => Math.Abs(a.GetDouble() - b.GetDouble()) < double.Epsilon,
            JsonValueKind.True or JsonValueKind.False or JsonValueKind.Null => true,
            JsonValueKind.Array => a.EnumerateArray().Count() == b.EnumerateArray().Count() &&
                                   a.EnumerateArray().Zip(b.EnumerateArray()).All(pair => JsonEquals(pair.First, pair.Second)),
            JsonValueKind.Object => a.EnumerateObject().Count() == b.EnumerateObject().Count() &&
                                    a.EnumerateObject().All(p =>
                                        b.TryGetProperty(p.Name, out var other) && JsonEquals(p.Value, other)),
            _ => false,
        };
    }

    private static string JsonPreview(JsonElement value)
        => value.ValueKind == JsonValueKind.String ? value.GetString()!
            : value.ValueKind is JsonValueKind.True or JsonValueKind.False ? (value.GetBoolean() ? "True" : "False")
            : value.GetRawText();

    private static bool SequenceEquals(JsonElement doc, string name, string[] expected)
    {
        if (!doc.TryGetProperty(name, out var array) || array.ValueKind != JsonValueKind.Array) return false;
        var actual = array.EnumerateArray().Select(x => x.GetString()).ToList();
        return actual.Count == expected.Length && actual.Zip(expected).All(p => p.First == p.Second);
    }

    private static string ReadText(string path)
        => new UTF8Encoding(false).GetString(File.ReadAllBytes(path)).Replace("\r\n", "\n").Replace('\r', '\n');

    private static string Relative(string root, string full)
        => Path.GetRelativePath(root, full).Replace('\\', '/');

    /// <summary>
    /// 等价 Python <c>str(Path(root) / rel)</c>：用平台分隔符拼接，并去掉 <c>root</c> 里的
    /// 空段与 <c>"."</c> 段（<c>Path("./x")</c> 序列化为 <c>x</c>，<c>Path("x/")</c> 同理）。
    /// </summary>
    private static string PyJoined(string root, string relPosix)
    {
        var native = relPosix.Replace('/', Path.DirectorySeparatorChar);
        var parts = root.Replace('\\', '/')
            .Split('/', StringSplitOptions.RemoveEmptyEntries)
            .Where(part => part != ".")
            .ToList();
        return parts.Count == 0
            ? native
            : string.Join(Path.DirectorySeparatorChar, parts) + Path.DirectorySeparatorChar + native;
    }

    /// <summary>等价 Python <c>Path.glob</c> 的所需子集：支持 <c>**</c> 递归、段内 <c>*</c> 与 <c>?</c>、字面路径。</summary>
    public static List<string> Glob(string root, string pattern)
    {
        var normalized = pattern.Replace('\\', '/');
        if (normalized.IndexOfAny(new[] { '*', '?', '[' }) < 0)
        {
            var literal = Path.Combine(root, normalized.Replace('/', Path.DirectorySeparatorChar));
            return File.Exists(literal) ? new List<string> { literal } : new List<string>();
        }

        var segments = normalized.Split('/');
        var matches = new List<string>();
        Walk(Path.GetFullPath(root), segments, 0, matches);
        return matches.OrderBy(m => Relative(root, m), StringComparer.Ordinal).ToList();
    }

    private static void Walk(string current, string[] segments, int index, List<string> matches)
    {
        if (index >= segments.Length)
        {
            if (File.Exists(current)) matches.Add(current);
            return;
        }

        var segment = segments[index];
        if (segment == "**")
        {
            Walk(current, segments, index + 1, matches);   // ** 可匹配零层
            if (Directory.Exists(current))
            {
                foreach (var dir in Directory.GetDirectories(current))
                {
                    Walk(dir, segments, index, matches);
                }
            }
            return;
        }

        if (segment.IndexOfAny(new[] { '*', '?' }) < 0)
        {
            Walk(Path.Combine(current, segment), segments, index + 1, matches);
            return;
        }

        if (!Directory.Exists(current)) return;
        var regex = WildcardRegex(segment);
        foreach (var entry in Directory.GetFileSystemEntries(current))
        {
            if (regex.IsMatch(Path.GetFileName(entry))) Walk(entry, segments, index + 1, matches);
        }
    }

    private static Regex WildcardRegex(string segment)
    {
        var pattern = "^" + Regex.Escape(segment).Replace("\\*", "[^/]*").Replace("\\?", "[^/]") + "$";
        return new Regex(pattern);
    }
}
