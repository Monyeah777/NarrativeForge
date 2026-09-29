using System.Globalization;
using System.Text;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/st_validator.py</c>：ST 制卡校验器原型 v0（卡 / 世界书 / MVU 变量 → 可复用报告）。
///
/// 只做**可自动化项**：R1 结构完备（C1/C2/C3）· R3 世界书健康（W1/W2/W5）· R4 变量系统（V2/V4/V5）。
/// 边界：**不解析 PNG 实卡**、不新增读写工具；级别映射沿用 <c>protocol/st_quality.json</c>：M→fail · S→warn · R→info。
/// </summary>
public static class StValidate
{
    private static readonly Dictionary<string, string> Sev = new(StringComparer.Ordinal)
    {
        ["M"] = "fail", ["S"] = "warn", ["R"] = "info",
    };

    private static readonly string[] RequiredSix =
    {
        "name", "description", "personality", "scenario", "first_mes", "mes_example",
    };

    private static readonly Dictionary<string, string> SpecExpect = new(StringComparer.Ordinal)
    {
        ["chara_card_v2"] = "2.0", ["chara_card_v3"] = "3.0",
    };

    private static Dictionary<string, object?> Issue(string rid, string level, string detail)
        => new(StringComparer.Ordinal)
        {
            ["rule"] = rid,
            ["level"] = level,
            ["severity"] = Sev.TryGetValue(level, out var sev) ? sev : "info",
            ["detail"] = detail,
        };

    /// <summary>R1：卡结构（V1/V2/V3）。</summary>
    public static List<Dictionary<string, object?>> CheckCard(Dictionary<string, object?> doc)
    {
        var output = new List<Dictionary<string, object?>>();
        var spec = PyStr(Val(doc, "spec") ?? "");
        var dataRaw = Val(doc, "data");
        var data = dataRaw as Dictionary<string, object?>;

        Dictionary<string, object?> body;
        if (spec.Length > 0)
        {
            if (!SpecExpect.ContainsKey(spec))
                output.Add(Issue("C1", "M", $"spec 非法：{spec}（应为 chara_card_v2/v3）"));
            var want = SpecExpect.TryGetValue(spec, out var w) ? w : null;
            var gotRaw = Val(doc, "spec_version") ?? (data is null ? null : Val(data, "spec_version")) ?? "";
            var got = PyStr(gotRaw);
            if (want is not null && got != want)
                output.Add(Issue("C2", "M", $"spec_version 应为 {want}，实为 {(got.Length > 0 ? got : "(缺)")}"));
            body = data is { Count: > 0 } ? data : new Dictionary<string, object?>(StringComparer.Ordinal);
        }
        else if (data is not null)
        {
            output.Add(Issue("C1", "M", "有 data 但缺 spec——无法判定 V2/V3"));
            body = data;
        }
        else
        {
            body = doc;   // V1 平铺
        }

        foreach (var key in RequiredSix)
        {
            var v = Val(body, key);
            if (v is null || (v is string s && s.Trim().Length == 0))
                output.Add(Issue("C3", "M", $"基础字段缺失或为空：{key}"));
        }
        return output;
    }

    /// <summary>R3：世界书健康。</summary>
    public static List<Dictionary<string, object?>> CheckWorldbook(Dictionary<string, object?> doc)
    {
        var output = new List<Dictionary<string, object?>>();
        var raw = Val(doc, "entries");
        if (raw is null && Val(doc, "character_book") is Dictionary<string, object?> cb)
            raw = Val(cb, "entries");

        var rows = new List<Dictionary<string, object?>>();
        if (raw is Dictionary<string, object?> map)
        {
            rows.AddRange(map.Values.OfType<Dictionary<string, object?>>());
        }
        else if (raw is List<object?> list)
        {
            rows.AddRange(list.OfType<Dictionary<string, object?>>());
        }
        else
        {
            return new List<Dictionary<string, object?>>
            {
                Issue("W1", "M", "entries 缺失或不是 dict/list（ST convertCharacterBook 要求数组）"),
            };
        }

        var seen = new Dictionary<string, int>(StringComparer.Ordinal);
        for (var i = 0; i < rows.Count; i++)
        {
            var e = rows[i];
            var keysNode = Val(e, "keys") ?? Val(e, "key");
            List<string> keys = keysNode switch
            {
                null => new List<string>(),
                string one => new List<string> { one },
                List<object?> many => many.Select(PyStr).ToList(),
                Dictionary<string, object?> dictKeys => dictKeys.Keys.ToList(),
                _ => throw new InvalidOperationException(
                    $"keys 不是可迭代对象：{PyScalar.PyRepr(keysNode)}（与 Python 同向：此处会 TypeError）"),
            };
            keys = keys.Where(k => k.Trim().Length > 0).ToList();
            if (keys.Count == 0) output.Add(Issue("W1", "M", $"第 {i} 条 key 为空"));
            if (PyStr(Val(e, "content") ?? "").Trim().Length == 0)
                output.Add(Issue("W1", "M", $"第 {i} 条 content 为空"));
            foreach (var k in keys)
            {
                if (k.Contains(',')) output.Add(Issue("W2", "S", $"key 含逗号（会被当分隔符）：{k}"));
                seen[k] = seen.GetValueOrDefault(k) + 1;
            }
            if (Val(e, "scanDepth") is null)
                output.Add(Issue("W5", "S", $"第 {i} 条未声明 scanDepth（触发可能在扫描范围外）"));
        }
        foreach (var (k, n) in seen)
        {
            if (n > 1) output.Add(Issue("W2", "S", $"同书内 key 重复 {n} 次：{k}"));
        }
        return output;
    }

    /// <summary>R4：MVU 变量系统。</summary>
    public static List<Dictionary<string, object?>> CheckMvuVariables(Dictionary<string, object?> doc)
    {
        var output = new List<Dictionary<string, object?>>();
        var variables = (Val(doc, "variables") as List<object?>) ?? new List<object?>();
        var names = new List<string>();
        foreach (var node in variables)
        {
            var v = node as Dictionary<string, object?>
                    ?? throw new InvalidOperationException(
                        $"variables 元素不是映射：{PyScalar.PyRepr(node)}（与 Python 同向：此处会 AttributeError）");
            var name = Val(v, "name");
            if (PyTruthy(name)) names.Add(PyStr(name));
        }
        if (names.Count == 0)
            return new List<Dictionary<string, object?>> { Issue("V2", "M", "变量表为空——无 schema 可校验") };

        var init = (Val(doc, "initial") as Dictionary<string, object?>) ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var nameSet = names.ToHashSet(StringComparer.Ordinal);
        var extra = init.Keys.Where(k => !nameSet.Contains(k)).OrderBy(k => k, StringComparer.Ordinal).ToList();
        if (extra.Count > 0) output.Add(Issue("V2", "M", $"initial 含未声明变量：{string.Join("、", extra)}"));
        var missing = names.Where(n => !init.ContainsKey(n)).Distinct(StringComparer.Ordinal)
            .OrderBy(n => n, StringComparer.Ordinal).ToList();
        if (missing.Count > 0) output.Add(Issue("V2", "M", $"变量缺初始值：{string.Join("、", missing)}"));

        foreach (var n in names)
        {
            if (n.Contains("{{") || n.Contains("}}")) output.Add(Issue("V5", "S", $"变量名含宏：{n}"));
            if (n.StartsWith('_') || n.StartsWith('$'))
                output.Add(Issue("V4", "S", $"变量名带可见性前缀（{n[0]}）——确认语义正确"));
        }
        foreach (var node in variables)
        {
            var v = (Dictionary<string, object?>)node!;
            if (PyStr(Val(v, "kind")) == "array")
                output.Add(Issue("V5", "S", $"变量 {PyStr(Val(v, "name"))} 为 array，规范建议优先 record"));
        }
        return output;
    }

    /// <summary>按形状分派（卡 / 世界书 / MVU 变量）→ 报告。</summary>
    public static Dictionary<string, object?> Validate(string path)
    {
        object? graph;
        try
        {
            using var doc = JsonIo.ReadFile(path);
            graph = PythonJson.ToGraph(doc.RootElement);
        }
        catch (FileNotFoundException exc)
        {
            throw new IOException(exc.Message, exc);
        }

        if (graph is not Dictionary<string, object?> map)
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["path"] = path,
                ["kind"] = "unknown",
                ["issues"] = new List<object?> { Issue("C1", "M", "顶层不是对象，无法判定资产类型") },
            };
        }

        string kind;
        List<Dictionary<string, object?>> issues;
        if (Val(map, "variables") is not null && Val(map, "initial") is not null)
        {
            kind = "mvu-variables";
            issues = CheckMvuVariables(map);
        }
        else if (Val(map, "entries") is not null || Val(map, "character_book") is not null)
        {
            kind = "worldbook";
            issues = CheckWorldbook(map);
        }
        else if (Val(map, "spec") is not null || Val(map, "name") is not null)
        {
            kind = "card";
            issues = CheckCard(map);
        }
        else
        {
            kind = "unknown";
            issues = new List<Dictionary<string, object?>>
            {
                Issue("C1", "M", "无法识别资产类型（无 spec/name/entries/variables 特征）"),
            };
        }

        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["path"] = path,
            ["kind"] = kind,
            ["issues"] = issues.Cast<object?>().ToList(),
            ["counts"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["fail"] = issues.Count(i => (string)i["severity"]! == "fail"),
                ["warn"] = issues.Count(i => (string)i["severity"]! == "warn"),
                ["info"] = issues.Count(i => (string)i["severity"]! == "info"),
            },
        };
    }

    /// <summary>等价 <c>st_validator.report_markdown</c>（逐字节）。</summary>
    public static string ReportMarkdown(Dictionary<string, object?> rep)
    {
        var counts = rep.GetValueOrDefault("counts") as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var outLines = new List<string>
        {
            "# ST 制卡校验报告", "",
            $"- 对象：`{PyStr(rep.GetValueOrDefault("path"))}`",
            $"- 判定形态：**{PyStr(rep.GetValueOrDefault("kind"))}**",
            $"- 结果：fail {Num(counts, "fail")} · warn {Num(counts, "warn")} · info {Num(counts, "info")}", "",
        };
        var issues = rep.GetValueOrDefault("issues") as List<object?> ?? new List<object?>();
        if (issues.Count == 0)
        {
            outLines.Add("**零问题**——该对象在可自动化项（R1/R3/R4）上全部通过。");
            outLines.Add("");
        }
        else
        {
            outLines.Add("| 规则 | 级别 | 严重度 | 说明 |");
            outLines.Add("|---|---|---|---|");
            foreach (var node in issues)
            {
                var issue = (Dictionary<string, object?>)node!;
                outLines.Add($"| {PyStr(issue["rule"])} | {PyStr(issue["level"])} | " +
                             $"{PyStr(issue["severity"])} | {PyStr(issue["detail"])} |");
            }
            outLines.Add("");
        }
        outLines.Add("> 本报告只覆盖**可自动化项**（R1 结构 / R3 世界书 / R4 变量）；");
        outLines.Add("> R2 引用一致、R5 可复现、R6 长会话友好等仍需人工清单（见 `docs/st-quality-checklist.md`）。");
        outLines.Add("> 校验器原型 v0 不解析 PNG 实卡；输入为已解出的 JSON。");
        outLines.Add("");
        return string.Join("\n", outLines);
    }

    // ------------------------------------------------------------------ 工具

    private static object? Val(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var v) ? v : null;

    private static long Num(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var v) && v is not null
            ? Convert.ToInt64(v, CultureInfo.InvariantCulture)
            : 0;

    /// <summary>Python <c>str()</c>：字符串原样、None 字面量、容器走 repr。</summary>
    private static string PyStr(object? v) => v switch
    {
        null => "None",
        bool b => b ? "True" : "False",
        string s => s,
        long l => l.ToString(CultureInfo.InvariantCulture),
        int i => i.ToString(CultureInfo.InvariantCulture),
        double d => PythonJson.PyFloatRepr(d),
        _ => PyScalar.PyRepr(v),
    };

    /// <summary>Python 真值判定（用于 <c>if v.get("name")</c>）。</summary>
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
}
