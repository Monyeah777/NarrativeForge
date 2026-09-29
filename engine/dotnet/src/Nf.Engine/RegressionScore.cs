using System.Globalization;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/regression_score.py</c>（**check33 第 3 条**：基线相对回归评分，no silent worsening）。
///
/// 信号 = 复用既有扫描器算 0..1 分值：<c>_penalty(n, step) = max(0, 1 - n·step)</c>；
/// **扫描器不可用 → 哨兵 → 0 分 + issues**（不可用 ≠ 零问题，fail-closed）。
/// 比对 = 与存盘基线逐信号 delta：**整体分跌破容差**或**任一非豁免信号回落**即判不可接受；
/// 审计例外释放额度 <c>Σ weight×drop×100</c>（只释放已批准的那一项，不外溢）。
///
/// **声明边界**：<c>purity_clean</c> 的信号源是 <c>purity_scan</c>——**源码 AST linter**，本引擎
/// 无 Python AST，已按「范围外」裁定（见覆盖率矩阵范围裁定）；因此该信号**不入复算**，
/// 显式落在 <c>boundary</c> 清单里（既不静默丢弃、也不伪造 1.0）。
/// 分值口径随之**只在可复算子集上归一**（Σw·v / Σw），基线侧同口径——不可比的分共同剔除，
/// 避免拿「少算一个信号」的分子去比「六个信号」的分母。分值只作**回归相对量**，不作质量宣称。
/// </summary>
public static class RegressionScore
{
    public const string Schema = "nf-score/1";
    public const string DefaultBaselineRel = "protocol/score_baseline.json";
    public const double DensityTarget = 3.0;

    /// <summary>真源 <c>SIGNAL_SPECS</c>：权重和 = 1.0（含边界项）。</summary>
    public static readonly (string Name, double Weight, string Note)[] SignalSpecs =
    {
        ("schema_clean", 0.20, "IDL schema 零漂移（schema_lint）"),
        ("conformance_clean", 0.20, "机读契约/一致性分级零虚标（conformance_scan）"),
        ("purity_clean", 0.15, "架构纯度零违规（purity_scan）"),
        ("doc_hygiene", 0.15, "文档卫生零缺口（doc_hygiene）"),
        ("depth_clean", 0.15, "质量纵深零缺口（quality_depth_scan）"),
        ("asset_density", 0.15, "资产键密度归一（asset_density）"),
    };

    /// <summary>**声明边界**：信号源不在本引擎判据内（源码 linter 面），不复算、不伪造。</summary>
    public static readonly string[] BoundarySignals = { "purity_clean" };

    public static double Penalty(long issueCount, double step = 0.1) => Math.Max(0.0, 1.0 - issueCount * step);

    /// <summary>算当前分值（纯读）：<c>{schema, score, signals[], metrics, issues[], boundary[]}</c>。</summary>
    public static Dictionary<string, object?> Evaluate(string root)
    {
        var issues = new List<string>();
        var values = new Dictionary<string, double>(StringComparer.Ordinal);

        double ScanSignal(string module, string fn, Func<long> count, double step = 0.1)
        {
            try
            {
                return Penalty(count(), step);
            }
            catch (Exception)
            {
                issues.Add($"扫描器不可用：core.{module}.{fn}（评分按 0 分计，修复后重跑——"
                           + "不可用不等于零问题）");
                return 0.0;
            }
        }

        values["schema_clean"] = ScanSignal("schema_lint", "scan", () => SchemaLint.Scan(root).Issues.Count);
        values["conformance_clean"] = ScanSignal("conformance_scan", "scan", () => ConformanceScan.Scan(root).Issues.Count);
        try
        {
            values["doc_hygiene"] = Penalty(DocHygiene.CheckMarkers(root).Count, step: 0.2);
        }
        catch (Exception)
        {
            issues.Add("扫描器不可用：core.doc_hygiene.check_markers（评分按 0 分计）");
            values["doc_hygiene"] = 0.0;
        }
        values["depth_clean"] = ScanSignal("quality_depth_scan", "scan", () => QualityDepth.Scan(root).Issues.Count);

        long keys = 0, files = 0;
        try
        {
            var (_, stats) = AssetDensity.Scan(root);
            keys = Convert.ToInt64(stats.GetValueOrDefault("keys") ?? 0L);
            files = Convert.ToInt64(stats.GetValueOrDefault("files") ?? 0L);
        }
        catch (Exception exc)
        {
            issues.Add($"资产档扫描不可用：{exc.Message}（评分按 0 分计）");
        }
        var density = files > 0 ? (double)keys / files : 0.0;
        values["asset_density"] = Math.Max(0.0, Math.Min(1.0, density / DensityTarget));
        if (files == 0) issues.Add("资产档扫描为空（asset_density 未取到文件数）");

        var signals = new List<object?>();
        double weighted = 0.0, weightSum = 0.0;
        foreach (var (name, weight, note) in SignalSpecs)
        {
            if (Array.IndexOf(BoundarySignals, name) >= 0) continue;
            var value = Math.Round(values.GetValueOrDefault(name), 4);
            weighted += weight * value;
            weightSum += weight;
            signals.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["name"] = name, ["weight"] = weight, ["value"] = value, ["note"] = note,
            });
        }
        var score = weightSum > 0 ? Math.Round(weighted / weightSum * 100.0, 2) : 0.0;
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = Schema,
            ["score"] = score,
            ["signals"] = signals,
            ["metrics"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["asset_keys"] = keys, ["asset_files"] = files,
            },
            ["issues"] = issues.Cast<object?>().ToList(),
            ["boundary"] = BoundarySignals.Cast<object?>().ToList(),
        };
    }

    /// <summary>
    /// 当前 vs 基线 → <c>{ok, delta, verdict, regressed[], exempted[]}</c>（**与真源逐字段同式**）。
    /// 纯函数、吃两个机读面——可拿合成对直接与真源 <c>compare()</c> 对账。
    /// </summary>
    public static Dictionary<string, object?> Compare(
        Dictionary<string, object?> current,
        Dictionary<string, object?> baseline,
        double tolerance = 0.0,
        List<Dictionary<string, object?>>? exceptions = null,
        double eps = 1e-9)
    {
        var exc = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var item in exceptions ?? new List<Dictionary<string, object?>>())
        {
            var signal = item.GetValueOrDefault("signal");
            if (signal is string text && text.Length > 0) exc[text] = item;
        }
        var baseSig = SignalValues(baseline);
        var curSig = SignalValues(current);
        var regressed = new List<object?>();
        var exempted = new List<object?>();
        foreach (var name in baseSig.Keys.Intersect(curSig.Keys).OrderBy(x => x, StringComparer.Ordinal))
        {
            var b = baseSig[name];
            var c = curSig[name];
            if (!(c < b - eps)) continue;
            var item = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["signal"] = name, ["from"] = Math.Round(b, 4), ["to"] = Math.Round(c, 4),
                ["drop"] = Math.Round(b - c, 4),
            };
            if (exc.TryGetValue(name, out var exception))
            {
                item["reason"] = exception.GetValueOrDefault("reason") as string ?? "";
                exempted.Add(item);
            }
            else
            {
                regressed.Add(item);
            }
        }
        var baseScore = ToDouble(baseline.GetValueOrDefault("score"));
        var curScore = ToDouble(current.GetValueOrDefault("score"));
        var delta = Math.Round(curScore - baseScore, 2);
        var weights = new Dictionary<string, double>(StringComparer.Ordinal);
        foreach (var signal in ObjList(current.GetValueOrDefault("signals")))
        {
            if (signal is Dictionary<string, object?> row && row.GetValueOrDefault("name") is string name)
                weights[name] = ToDouble(row.GetValueOrDefault("weight"));
        }
        var exemptBudget = exempted.Sum(item =>
            weights.GetValueOrDefault(((Dictionary<string, object?>)item!)["signal"] as string ?? "")
            * ToDouble(((Dictionary<string, object?>)item!)["drop"]) * 100.0);
        var ok = delta >= -(Math.Abs(tolerance) + exemptBudget) && regressed.Count == 0;
        string verdict;
        if (!SignalValuesPresent(baseline)) verdict = "无基线（只报当前分值，未做回归判定）";
        else if (!ok && regressed.Count > 0)
            verdict = "回归（信号回落）：" + string.Join("、",
                regressed.Select(r => ((Dictionary<string, object?>)r!)["signal"] as string ?? ""));
        else if (!ok)
            verdict = $"回归（整体分下降 {(-delta).ToString("F2", CultureInfo.InvariantCulture)}"
                      + $" > 容差 {Math.Abs(tolerance).ToString("F2", CultureInfo.InvariantCulture)}）";
        else if (exempted.Count > 0) verdict = $"通过（含 {exempted.Count} 项审计例外）";
        else verdict = "通过（无回归）";
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["ok"] = ok, ["delta"] = delta, ["baseline_score"] = baseScore,
            ["current_score"] = curScore, ["regressed"] = regressed, ["exempted"] = exempted,
            ["verdict"] = verdict,
        };
    }

    /// <summary>读基线件（机读面）。</summary>
    public static Dictionary<string, object?> LoadBaseline(string path)
    {
        using var doc = JsonIo.ReadFile(path);
        return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
               ?? new Dictionary<string, object?>(StringComparer.Ordinal);
    }

    /// <summary>
    /// 分值面的取行口径（真源 <c>evaluate()</c> 的机读字段逐行化）：
    /// 信号行（**不含边界项**）· <c>score=</c> · <c>boundary=</c> · <c>issues=</c>。
    /// 浮点按 Python <c>repr</c> 渲染（整数浮点补 <c>.0</c>），两侧同式才谈得上逐字节对账。
    /// </summary>
    public static List<string> Log(Dictionary<string, object?> evaluation)
    {
        var lines = new List<string>();
        foreach (var signal in ObjList(evaluation.GetValueOrDefault("signals")))
        {
            var row = (Dictionary<string, object?>)signal!;
            lines.Add($"{row["name"]}={PyFloat(ToDouble(row.GetValueOrDefault("value")))}");
        }
        lines.Add("score=" + PyFloat(ToDouble(evaluation.GetValueOrDefault("score"))));
        lines.Add("boundary=" + string.Join(",",
            ObjList(evaluation.GetValueOrDefault("boundary")).Select(item => item as string ?? "")));
        var issues = ObjList(evaluation.GetValueOrDefault("issues"));
        lines.Add($"issues={(issues.Count == 0 ? "零缺口" : "FAIL " + issues.Count)}");
        return lines;
    }

    public static string LogDigest(Dictionary<string, object?> evaluation) =>
        ExitFaces.Digest32(Log(evaluation));

    /// <summary>
    /// 比对口径的取行：每例一行 <c>{case}: ok=.. delta=.. verdict=..</c>（真源 <c>compare()</c> 纯函数）。
    /// <paramref name="pairs"/> 每项键：<c>case</c> / <c>current</c> / <c>baseline</c> /
    /// <c>tolerance</c>（可缺） / <c>exceptions</c>（可缺）。
    /// </summary>
    public static List<string> CompareLog(IEnumerable<Dictionary<string, object?>> pairs)
    {
        var lines = new List<string>();
        foreach (var pair in pairs)
        {
            var current = (Dictionary<string, object?>)pair["current"]!;
            var baseline = (Dictionary<string, object?>)pair["baseline"]!;
            var tolerance = pair.TryGetValue("tolerance", out var toleranceValue) ? ToDouble(toleranceValue) : 0.0;
            var exceptions = new List<Dictionary<string, object?>>();
            foreach (var item in ObjList(pair.GetValueOrDefault("exceptions")))
            {
                if (item is Dictionary<string, object?> row) exceptions.Add(row);
            }
            var result = Compare(current, baseline, tolerance, exceptions);
            lines.Add($"{pair.GetValueOrDefault("case")}: ok={PyBool(result["ok"])}"
                      + $" delta={PyFloat(ToDouble(result["delta"]))} verdict={result["verdict"]}");
        }
        return lines;
    }

    public static string CompareLogDigest(IEnumerable<Dictionary<string, object?>> pairs) =>
        ExitFaces.Digest32(CompareLog(pairs));

    private static string PyBool(object? value) => value is true ? "True" : "False";

    /// <summary>Python <c>repr(float)</c> 的口径：整数浮点补 <c>.0</c>。</summary>
    public static string PyFloat(double value)
    {
        if (double.IsNaN(value)) return "nan";
        if (double.IsPositiveInfinity(value)) return "inf";
        if (double.IsNegativeInfinity(value)) return "-inf";
        var text = value.ToString("R", CultureInfo.InvariantCulture);
        return text.Contains('.') || text.Contains('e') || text.Contains('E') ? text : text + ".0";
    }

    public static Dictionary<string, object?> LoadBaselineAt(string root) =>
        LoadBaseline(Path.Combine(root, DefaultBaselineRel.Replace('/', Path.DirectorySeparatorChar)));

    /// <summary>check33 第 3 条的框法：<c>problems</c>（空 = 过）。</summary>
    public static List<string> Problems(string root)
    {
        var problems = new List<string>();
        var basePath = Path.Combine(root, DefaultBaselineRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(basePath))
        {
            problems.Add($"缺回归评分基线 {DefaultBaselineRel}");
            return problems;
        }
        var comparison = Compare(Evaluate(root), LoadBaseline(basePath));
        if (comparison["ok"] is false) problems.Add($"回归评分未过：{comparison["verdict"]}");
        return problems;
    }

    private static bool SignalValuesPresent(Dictionary<string, object?> baseline) =>
        ObjList(baseline.GetValueOrDefault("signals")).Count > 0;

    private static Dictionary<string, double> SignalValues(Dictionary<string, object?> side)
    {
        var map = new Dictionary<string, double>(StringComparer.Ordinal);
        foreach (var signal in ObjList(side.GetValueOrDefault("signals")))
        {
            if (signal is Dictionary<string, object?> row && row.GetValueOrDefault("name") is string name)
            {
                var value = row.GetValueOrDefault("value");
                map[name] = ToDouble(value);
            }
        }
        return map;
    }

    /// <summary>Python <c>float(x or 0.0)</c>：None/缺键 → 0.0。</summary>
    private static double ToDouble(object? value) => value switch
    {
        null => 0.0,
        double d => d,
        long l => l,
        int i => i,
        _ => Convert.ToDouble(value, CultureInfo.InvariantCulture),
    };

    private static List<object?> ObjList(object? value) => value as List<object?> ?? new List<object?>();
}
