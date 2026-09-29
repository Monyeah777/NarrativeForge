using System.Globalization;
using System.Text;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/quant_metrics.py</c>：量化金融域功能面（把「指标只写在散文里」变成**可复算的引擎**）。
///
/// 口径纪律（与 <c>QUANT_METRICS.md</c> 一一对应，不另立门派）：简单收益 <c>r_t = P_t/P_{t-1} − 1</c>；
/// 年化因子按频率取 252/52/12（**必须显式声明**）；夏普 <c>(mean(r) − rf_period)/std(r) × sqrt(af)</c>
/// （样本标准差 ddof=1）；最大回撤按**净值**序列历史峰值；卡尔玛 = 年化收益 / 最大回撤（同区间）；
/// 换手 `sum(|Δw|)/2`（单边缺省）；IC = 因子与随后期收益的**秩相关**（spearman）。
///
/// 确定性：所有输出四舍五入到**固定 6 位**，纯函数、无墙钟、无随机——同一输入两次调用逐字节一致
/// （check32 复算比对的前提）。本件的等价性由**金标向量**钉住（真源同输入导出的期望 JSON）。
/// </summary>
public static class QuantMetrics
{
    public static readonly Dictionary<string, int> AnnualFactors = new(StringComparer.Ordinal)
    {
        ["daily"] = 252, ["weekly"] = 52, ["monthly"] = 12,
    };

    public const int Digits = 6;

    /// <summary>本仓口径与 GIPS 的关系：只有「口径 + 披露面」对齐，**不构成 GIPS 合规声明**。</summary>
    public const string GipsAlignment =
        "口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）逐项显式；"
        + "**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据";

    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>真源 <c>_r</c>：四舍五入到 6 位（Python <c>round(float(x), 6)</c>，tie→even）。</summary>
    /// <summary>真源 <c>_r</c>：四舍五入到 6 位（Python <c>round</c> 的**正确舍入**语义，见 PyScalar.PyRound）。</summary>
    public static double R(double x) => PyScalar.PyRound(x, Digits);

    // ------------------------------------------------------------------ 数据装载

    /// <summary>读净值曲线 CSV（表头须含 date,equity[,benchmark]）；口径错误即返回错误串。</summary>
    public static (Dictionary<string, object?> Series, string Error) LoadEquityCurve(string path)
    {
        string text;
        try
        {
            text = KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(path)));
        }
        catch (Exception exc) when (exc is IOException or UnauthorizedAccessException)
        {
            return (new Dictionary<string, object?>(StringComparer.Ordinal), $"不可读：{exc.Message}");
        }
        var lines = KnowledgeSig.SplitLines(text);
        var rows = ParseCsvLines(lines);
        if (rows.Count == 0) return (Empty(), "空表");
        var header = rows[0];
        var cols = header.Where(c => c.Length > 0).Select(c => c.Trim().ToLowerInvariant())
            .ToHashSet(StringComparer.Ordinal);
        foreach (var need in new[] { "date", "equity" })
            if (!cols.Contains(need))
                return (Empty(), $"缺列 {need}（实际列：{PyReprList(cols.OrderBy(x => x, StringComparer.Ordinal))}）");
        var hasBench = cols.Contains("benchmark");
        var dates = new List<object?>();
        var equity = new List<double>();
        var bench = new List<double>();
        for (var i = 1; i < rows.Count; i++)
        {
            var row = RowMap(header, rows[i]);
            var dateRaw = FirstNonEmpty(row.GetValueOrDefault("date"), row.GetValueOrDefault("Date"));
            var eqRaw = FirstNonEmpty(row.GetValueOrDefault("equity"), row.GetValueOrDefault("Equity"));
            if (!TryPyFloat(eqRaw, out var eq))
                return (Empty(), $"第 {i + 1} 行数值不可解析");
            dates.Add(dateRaw.Trim());
            equity.Add(eq);
            if (!hasBench) continue;
            var bRaw = FirstNonEmpty(row.GetValueOrDefault("benchmark"), row.GetValueOrDefault("Benchmark"));
            if (!TryPyFloat(bRaw, out var bv))
                return (Empty(), $"第 {i + 1} 行数值不可解析");
            bench.Add(bv);
        }
        if (equity.Count < 3) return (Empty(), "样本过短（< 3 个净值点）");
        if (equity.Any(v => v <= 0)) return (Empty(), "净值须为正数（口径：净值序列，非累计收益）");
        return (new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["dates"] = dates,
            ["equity"] = equity.Cast<object?>().ToList(),
            ["benchmark"] = hasBench ? bench.Cast<object?>().ToList() : null,
        }, "");
    }

    private static Dictionary<string, object?> Empty() => new(StringComparer.Ordinal);

    // ------------------------------------------------------------------ 基础口径

    public static List<double> SimpleReturns(IReadOnlyList<double> prices)
    {
        var output = new List<double>();
        for (var i = 1; i < prices.Count; i++) output.Add(prices[i] / prices[i - 1] - 1.0);
        return output;
    }

    public static List<double> LogReturns(IReadOnlyList<double> prices)
    {
        var output = new List<double>();
        for (var i = 1; i < prices.Count; i++) output.Add(Math.Log(prices[i] / prices[i - 1]));
        return output;
    }

    public static List<double> Returns(IReadOnlyList<double> prices, string kind = "simple") => kind switch
    {
        "simple" => SimpleReturns(prices),
        "log" => LogReturns(prices),
        _ => throw new ArgumentException($"收益口径只支持 simple / log，实为 {PyScalar.PyRepr(kind)}"),
    };

    public static double CumulativeReturn(IReadOnlyList<double> prices) => prices[^1] / prices[0] - 1.0;

    public static double AnnualizedReturn(IReadOnlyList<double> prices, int annualFactor)
    {
        var n = prices.Count - 1;
        if (n <= 0) return 0.0;
        var growth = prices[^1] / prices[0];
        return Math.Pow(growth, (double)annualFactor / n) - 1.0;
    }

    private static double Mean(IReadOnlyList<double> xs) => xs.Count > 0 ? xs.Sum() / xs.Count : 0.0;

    /// <summary>样本标准差（ddof=1）——与 empyrical / pandas 默认口径一致。</summary>
    private static double Stdev(IReadOnlyList<double> xs)
    {
        var n = xs.Count;
        if (n < 2) return 0.0;
        var mu = Mean(xs);
        return Math.Sqrt(xs.Sum(x => (x - mu) * (x - mu)) / (n - 1));
    }

    public static double AnnualizedVolatility(IReadOnlyList<double> rets, int annualFactor) =>
        Stdev(rets) * Math.Sqrt(annualFactor);

    public static double MaxDrawdown(IReadOnlyList<double> prices)
    {
        var peak = prices[0];
        var mdd = 0.0;
        foreach (var p in prices)
        {
            peak = Math.Max(peak, p);
            mdd = Math.Max(mdd, (peak - p) / peak);
        }
        return mdd;
    }

    public static List<double> DrawdownSeries(IReadOnlyList<double> prices)
    {
        var peak = prices[0];
        var output = new List<double>();
        foreach (var p in prices)
        {
            peak = Math.Max(peak, p);
            output.Add((peak - p) / peak);
        }
        return output;
    }

    public static double Sharpe(IReadOnlyList<double> rets, double riskFreeAnnual, int annualFactor)
    {
        var sd = Stdev(rets);
        if (sd == 0) return 0.0;
        var rfPeriod = Math.Pow(1.0 + riskFreeAnnual, 1.0 / annualFactor) - 1.0;
        return (Mean(rets) - rfPeriod) / sd * Math.Sqrt(annualFactor);
    }

    public static double Calmar(double annualRet, double mdd) => mdd == 0 ? 0.0 : annualRet / mdd;

    public static double TrackingError(IReadOnlyList<double> rets, IReadOnlyList<double> bench, int annualFactor)
    {
        var n = Math.Min(rets.Count, bench.Count);
        if (n < 2) return 0.0;
        var active = new List<double>();
        for (var i = 0; i < n; i++) active.Add(rets[i] - bench[i]);
        return Stdev(active) * Math.Sqrt(annualFactor);
    }

    public static double InformationRatio(IReadOnlyList<double> rets, IReadOnlyList<double> bench, int annualFactor)
    {
        var n = Math.Min(rets.Count, bench.Count);
        if (n < 2) return 0.0;
        var active = new List<double>();
        for (var i = 0; i < n; i++) active.Add(rets[i] - bench[i]);
        var sd = Stdev(active);
        return sd == 0 ? 0.0 : Mean(active) / sd * Math.Sqrt(annualFactor);
    }

    /// <summary>平均秩（并列取平均）——spearman 的秩定义，避免并列值造成口径漂移。</summary>
    public static List<double> Rank(IReadOnlyList<double> xs)
    {
        var order = Enumerable.Range(0, xs.Count).OrderBy(i => xs[i]).ToList();
        var ranks = new double[xs.Count];
        var i = 0;
        while (i < order.Count)
        {
            var j = i;
            while (j + 1 < order.Count && xs[order[j + 1]] == xs[order[i]]) j++;
            var avg = (i + j) / 2.0 + 1.0;
            for (var k = i; k <= j; k++) ranks[order[k]] = avg;
            i = j + 1;
        }
        return ranks.ToList();
    }

    private static double Pearson(IReadOnlyList<double> a, IReadOnlyList<double> b)
    {
        var n = Math.Min(a.Count, b.Count);
        if (n < 2) return 0.0;
        var ma = Mean(a.Take(n).ToList());
        var mb = Mean(b.Take(n).ToList());
        var num = 0.0;
        var da = 0.0;
        var db = 0.0;
        for (var i = 0; i < n; i++)
        {
            num += (a[i] - ma) * (b[i] - mb);
            da += (a[i] - ma) * (a[i] - ma);
            db += (b[i] - mb) * (b[i] - mb);
        }
        return da == 0 || db == 0 ? 0.0 : num / (Math.Sqrt(da) * Math.Sqrt(db));
    }

    public static double InformationCoefficient(IReadOnlyList<double> factor,
        IReadOnlyList<double> forwardReturn, string method = "spearman") => method switch
    {
        "spearman" => Pearson(Rank(factor), Rank(forwardReturn)),
        "pearson" => Pearson(factor, forwardReturn),
        _ => throw new ArgumentException($"IC 口径只支持 spearman / pearson，实为 {PyScalar.PyRepr(method)}"),
    };

    /// <summary>换手率：<c>sum(|Δw|)/2</c>（单边，缺省）或 <c>sum(|Δw|)</c>（双边）。</summary>
    public static List<double> Turnover(IReadOnlyList<IReadOnlyList<double>> weights, bool singleSide = true)
    {
        var output = new List<double>();
        for (var i = 1; i < weights.Count; i++)
        {
            var n = Math.Min(weights[i].Count, weights[i - 1].Count);
            var gross = 0.0;
            for (var j = 0; j < n; j++) gross += Math.Abs(weights[i][j] - weights[i - 1][j]);
            output.Add(singleSide ? gross / 2.0 : gross);
        }
        return output;
    }

    // ------------------------------------------------------------------ 报告装配

    private static Dictionary<string, object?> Block(IReadOnlyList<double> prices, int annualFactor,
        double riskFreeAnnual, string retKind)
    {
        var rets = Returns(prices, retKind);
        var ann = AnnualizedReturn(prices, annualFactor);
        var mdd = MaxDrawdown(prices);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["cumulative"] = R(CumulativeReturn(prices)),
            ["annualized"] = R(ann),
            ["volatility_annualized"] = R(AnnualizedVolatility(rets, annualFactor)),
            ["sharpe"] = R(Sharpe(rets, riskFreeAnnual, annualFactor)),
            ["max_drawdown"] = R(mdd),
            ["calmar"] = R(Calmar(ann, mdd)),
        };
    }

    public static Dictionary<string, object?> PerformanceReport(Dictionary<string, object?> series,
        string periodStart, string periodEnd, string currency = "CNY", string returnBasis = "simple",
        string frequency = "daily", double riskFreeRateAnnual = 0.0, string benchmarkId = "",
        double costBpsFee = 0.0, double costBpsSlippage = 0.0, string fillRule = "next_open",
        bool singleSideTurnover = true, string asOf = "")
    {
        if (!AnnualFactors.ContainsKey(frequency))
            throw new ArgumentException($"频率须在 {PyReprList(AnnualFactors.Keys.OrderBy(x => x, StringComparer.Ordinal))} 中，"
                                        + $"实为 {PyScalar.PyRepr(frequency)}");
        var af = AnnualFactors[frequency];
        var equity = PyDoubles(series.GetValueOrDefault("equity"));
        var bench = series.GetValueOrDefault("benchmark") is List<object?> bl && bl.Count > 0
            ? PyDoubles(bl) : null;
        var gross = Block(equity, af, riskFreeRateAnnual, returnBasis);
        var doc = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["kind"] = "nf-performance/1",
            ["as_of"] = asOf.Length > 0 ? asOf : periodEnd,
            ["currency"] = currency,
            ["return_basis"] = returnBasis,
            ["frequency"] = frequency,
            ["annual_factor"] = (long)af,
            ["risk_free_rate_annual"] = R(riskFreeRateAnnual),
            ["period"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["start"] = periodStart, ["end"] = periodEnd, ["observations"] = (long)equity.Count,
            },
            ["gross"] = gross,
            ["benchmark"] = null,
            ["excess"] = null,
            ["costs"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["fee_bps"] = R(costBpsFee), ["slippage_bps"] = R(costBpsSlippage),
                ["fill_rule"] = fillRule,
                ["turnover_basis"] = singleSideTurnover ? "single_side" : "double_side",
            },
            ["disclosures"] = new List<object?>
            {
                $"收益口径 = {returnBasis}；年化因子 = {af}（{frequency}）；无风险利率年化 = {PyNum(R(riskFreeRateAnnual))}",
                $"绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee={PyNum(R(costBpsFee))} bps, "
                + $"slippage={PyNum(R(costBpsSlippage))} bps）",
                $"成交价假设 = {fillRule}（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）",
                "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间",
                GipsAlignment,
            },
        };
        if (bench is not null)
        {
            var benchBlock = Block(bench, af, riskFreeRateAnnual, returnBasis);
            benchBlock["id"] = benchmarkId.Length > 0 ? benchmarkId : "UNSPECIFIED";
            doc["benchmark"] = benchBlock;
            var rets = Returns(equity, returnBasis);
            var brets = Returns(bench, returnBasis);
            doc["excess"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["annualized"] = R(Convert.ToDouble(gross["annualized"], CultureInfo.InvariantCulture)
                                   - Convert.ToDouble(benchBlock["annualized"], CultureInfo.InvariantCulture)),
                ["tracking_error"] = R(TrackingError(rets, brets, af)),
                ["information_ratio"] = R(InformationRatio(rets, brets, af)),
            };
        }
        return doc;
    }

    // ------------------------------------------------------------------ 图表规格

    public static Dictionary<string, object?> VegaEquityCurve(Dictionary<string, object?> series,
        string title = "净值曲线")
    {
        var dates = PyStrings(series.GetValueOrDefault("dates"));
        var equity = PyDoubles(series.GetValueOrDefault("equity"));
        var data = new List<object?>();
        for (var i = 0; i < dates.Count && i < equity.Count; i++)
            data.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["date"] = dates[i], ["series"] = "策略", ["value"] = equity[i],
            });
        if (series.GetValueOrDefault("benchmark") is List<object?> bench && bench.Count > 0)
        {
            var bv = PyDoubles(bench);
            for (var i = 0; i < dates.Count && i < bv.Count; i++)
                data.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["date"] = dates[i], ["series"] = "基准", ["value"] = bv[i],
                });
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["$schema"] = "https://vega.github.io/schema/vega-lite/v5.json",
            ["description"] = title,
            ["data"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["values"] = data },
            ["mark"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["type"] = "line", ["point"] = false },
            ["encoding"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["x"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = "date", ["type"] = "temporal", ["title"] = "日期",
                },
                ["y"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = "value", ["type"] = "quantitative", ["title"] = "净值",
                    ["scale"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["zero"] = false },
                },
                ["color"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = "series", ["type"] = "nominal", ["title"] = "",
                },
            },
        };
    }

    public static Dictionary<string, object?> VegaDrawdown(Dictionary<string, object?> series,
        string title = "回撤曲线")
    {
        var dates = PyStrings(series.GetValueOrDefault("dates"));
        var dd = DrawdownSeries(PyDoubles(series.GetValueOrDefault("equity")));
        var values = new List<object?>();
        for (var i = 0; i < dates.Count && i < dd.Count; i++)
            values.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["date"] = dates[i], ["value"] = -Math.Abs(dd[i]),
            });
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["$schema"] = "https://vega.github.io/schema/vega-lite/v5.json",
            ["description"] = title,
            ["data"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["values"] = values },
            ["mark"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["type"] = "area", ["line"] = true },
            ["encoding"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["x"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = "date", ["type"] = "temporal", ["title"] = "日期",
                },
                ["y"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = "value", ["type"] = "quantitative", ["title"] = "回撤",
                    ["scale"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["zero"] = true },
                },
            },
        };
    }

    /// <summary>口径声明依赖（Mermaid 图即数据）：缺一环即口径未定义。</summary>
    public static string MermaidDeclarationFlow() => string.Join("\n", new[]
    {
        "%% 口径声明链（QUANT_METRICS 口径纪律的可视化，非新增真源）",
        "flowchart LR",
        "  A[收益口径 simple/log] --> D[绩效报告]",
        "  B[年化因子 252/52/12] --> D",
        "  C[无风险利率 rf] --> D",
        "  E[净值序列] --> D",
        "  D --> F[披露面 disclosures]",
        "  G[成本与滑点申报] --> F",
        "  H[基准与成交价假设] --> F",
    }) + "\n";

    // ------------------------------------------------------------------ 小工具

    /// <summary>张量行形态（<c>csv.DictReader(text.splitlines())</c>）：每行独立解析，字段可带引号与逗号。</summary>
    private static List<List<string>> ParseCsvLines(IReadOnlyList<string> lines)
    {
        var rows = new List<List<string>>();
        foreach (var line in lines)
        {
            var fields = new List<string>();
            var sb = new StringBuilder();
            var inQuotes = false;
            for (var i = 0; i < line.Length; i++)
            {
                var c = line[i];
                if (inQuotes)
                {
                    if (c == '"')
                    {
                        if (i + 1 < line.Length && line[i + 1] == '"') { sb.Append('"'); i++; }
                        else inQuotes = false;
                    }
                    else sb.Append(c);
                    continue;
                }
                if (c == '"') { inQuotes = true; continue; }
                if (c == ',') { fields.Add(sb.ToString()); sb.Clear(); continue; }
                sb.Append(c);
            }
            fields.Add(sb.ToString());
            rows.Add(fields);
        }
        return rows;
    }

    private static Dictionary<string, string> RowMap(IReadOnlyList<string> header, IReadOnlyList<string> row)
    {
        var map = new Dictionary<string, string>(StringComparer.Ordinal);
        for (var i = 0; i < header.Count; i++)
            map[header[i]] = i < row.Count ? row[i] : "";
        return map;
    }

    private static string FirstNonEmpty(string? a, string? b) => !string.IsNullOrEmpty(a) ? a! : (b ?? "");

    public static bool TryPyFloat(string raw, out double value)
    {
        var text = raw.Trim();
        if (text.Length == 0) { value = 0; return false; }
        switch (text.ToLowerInvariant())
        {
            case "inf": case "+inf": case "infinity": case "+infinity":
                value = double.PositiveInfinity; return true;
            case "-inf": case "-infinity":
                value = double.NegativeInfinity; return true;
            case "nan": case "+nan": case "-nan":
                value = double.NaN; return true;
        }
        return double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out value);
    }

    public static List<double> PyDoubles(object? v) =>
        (v as List<object?> ?? new List<object?>()).Select(x => x switch
        {
            long l => (double)l,
            int i => i,
            double d => d,
            _ => 0.0,
        }).ToList();

    public static List<string> PyStrings(object? v) =>
        (v as List<object?> ?? new List<object?>()).Select(PyStr).ToList();

    private static string PyReprList(IEnumerable<string> items) =>
        "[" + string.Join(", ", items.Select(PyScalar.PyRepr)) + "]";

    /// <summary>
    /// Python <c>%s</c> 的数值形态。真源 <c>_r</c> 恒返回 **float**（<c>round(float, 6)</c>），
    /// 故 <c>%s</c> 走的是 <c>repr(float)</c>——**<c>0.0</c> 打出来是 "0.0" 不是 "0"**。
    /// </summary>
    private static string PyNum(double d) => PythonJson.PyFloatRepr(d);

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
