using System.Globalization;
using System.Text;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/domain_metrics.py</c>：AI 域包的**度量族引擎**（把「指标只写在散文里」变成可复算的口径值）。
///
/// 十二个族：classification / retrieval / extraction / generation / regression / calibration /
/// agreement / preference / exact_judgement / latency_cost / drift / contract_compliance。
/// 口径纪律：所有输出四舍五入到**固定 6 位**、`_safe_div` 除零记 0、确定性纯函数——
/// 同一夹具两次求值逐字节一致（check32 的 T4 复算前提）。
///
/// **范围声明（不冒充）**：真源的**夹具生成**三件（`_Rng` / `synthesize` / `rows_to_csv`）属
/// **域包工厂写面**（`nf domain build --write` 造样例），本件不移植——只读门不提供写命令。
/// </summary>
public static class DomainMetrics
{
    public const int Digits = 6;

    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>真源 <c>_r</c>：四舍五入到 6 位（Python <c>round</c> 的正确舍入语义）。</summary>
    public static double R(double x) => PyScalar.PyRound(x, Digits);

    private static double SafeDiv(double a, double b) => b == 0 ? 0.0 : a / b;

    // ------------------------------------------------------------------ 输入装载

    /// <summary>`csv.DictReader(text.splitlines())`：短行缺的字段补 **None**（与 Python 同），不是空串。</summary>
    public static (List<Dictionary<string, string?>> Rows, string Error) LoadRows(string path)
    {
        string text;
        try
        {
            text = KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(path)));
        }
        catch (Exception exc) when (exc is IOException or UnauthorizedAccessException)
        {
            return (new List<Dictionary<string, string?>>(), $"不可读：{exc.Message}");
        }
        var lines = KnowledgeSig.SplitLines(text);
        var table = lines.Select(SplitCsvLine).ToList();
        var rows = new List<Dictionary<string, string?>>();
        if (table.Count > 0)
        {
            var header = table[0];
            for (var i = 1; i < table.Count; i++)
            {
                var row = new Dictionary<string, string?>(StringComparer.Ordinal);
                for (var c = 0; c < header.Count; c++)
                    row[header[c]] = c < table[i].Count ? table[i][c] : null;
                rows.Add(row);
            }
        }
        if (rows.Count == 0) return (rows, $"空表（{Path.GetFileName(path)}）");
        return (rows, "");
    }

    private static List<string> SplitCsvLine(string line)
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
        return fields;
    }

    private static double Num(Dictionary<string, string?> row, string key)
    {
        var raw = row.GetValueOrDefault(key);
        if (raw is not null && QuantMetrics.TryPyFloat(raw, out var value)) return value;
        throw new ArgumentException($"列 {key} 非数值：{PyScalar.PyRepr(raw)}");
    }

    private static int Flag(Dictionary<string, string?> row, string key)
    {
        var v = PyStr(row.GetValueOrDefault(key)).Trim().ToLowerInvariant();
        if (v is "1" or "true" or "yes" or "y" or "正" or "是") return 1;
        if (v is "0" or "false" or "no" or "n" or "负" or "否") return 0;
        throw new ArgumentException($"列 {key} 非 0/1：{PyScalar.PyRepr(row.GetValueOrDefault(key))}");
    }

    private static string Cell(Dictionary<string, string?> row, string key) =>
        row.TryGetValue(key, out var v) ? PyStr(v) : "";

    // ------------------------------------------------------------------ 度量族

    public static Dictionary<string, object?> Classification(List<Dictionary<string, string?>> rows)
    {
        var labels = rows.Select(r => Cell(r, "gold")).Concat(rows.Select(r => Cell(r, "pred")))
            .Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToList();
        var cm = labels.ToDictionary(g => g,
            _ => labels.ToDictionary(p => p, _ => 0L, StringComparer.Ordinal), StringComparer.Ordinal);
        foreach (var r in rows) cm[Cell(r, "gold")][Cell(r, "pred")]++;
        var n = rows.Count;
        var correct = labels.Sum(l => cm[l][l]);
        var per = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var l in labels)
        {
            var tp = cm[l][l];
            var fp = labels.Where(g => g != l).Sum(g => cm[g][l]);
            var fn = labels.Where(p => p != l).Sum(p => cm[l][p]);
            var precision = SafeDiv(tp, tp + fp);
            var recall = SafeDiv(tp, tp + fn);
            var f1 = SafeDiv(2 * precision * recall, precision + recall);
            per[l] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["precision"] = R(precision), ["recall"] = R(recall), ["f1"] = R(f1),
                ["support"] = tp + fn,
            };
        }
        var macro = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var k in new[] { "precision", "recall", "f1" })
            macro[k] = R(labels.Sum(l => (double)((Dictionary<string, object?>)per[l]!)[k]!) / labels.Count);
        var output = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "classification",
            ["n"] = (long)n,
            ["accuracy"] = R((double)correct / n),
            ["macro"] = macro,
            ["confusion"] = labels.ToDictionary(g => g,
                g => (object?)cm[g].ToDictionary(kv => kv.Key, kv => (object?)kv.Value, StringComparer.Ordinal),
                StringComparer.Ordinal),
            ["per_label"] = per,
        };
        if (rows.All(r => Cell(r, "gold") is "0" or "1") && rows.All(r => r.ContainsKey("score")))
            output["roc_auc"] = R(Auc(rows.Select(r => (Num(r, "score"), Flag(r, "gold"))).ToList()));
        return output;
    }

    /// <summary>ROC-AUC（Mann-Whitney 口径，并列取 0.5 计）。</summary>
    private static double Auc(List<(double Score, int Label)> pairs)
    {
        var pos = pairs.Where(p => p.Label == 1).Select(p => p.Score).ToList();
        var neg = pairs.Where(p => p.Label == 0).Select(p => p.Score).ToList();
        if (pos.Count == 0 || neg.Count == 0) return 0.0;
        var wins = 0.0;
        foreach (var s in pos)
            foreach (var t in neg)
                wins += s > t ? 1.0 : (s == t ? 0.5 : 0.0);
        return wins / (pos.Count * neg.Count);
    }

    public static Dictionary<string, object?> Retrieval(List<Dictionary<string, string?>> rows, int k = 5)
    {
        var groups = new Dictionary<string, List<(int Rank, int Relevant)>>(StringComparer.Ordinal);
        foreach (var r in rows)
        {
            var key = Cell(r, "query_id");
            if (!groups.TryGetValue(key, out var list)) groups[key] = list = new List<(int, int)>();
            list.Add(((int)Math.Truncate(Num(r, "rank")), Flag(r, "relevant")));
        }
        var recalls = new List<double>();
        var precisions = new List<double>();
        var rrs = new List<double>();
        var ndcgs = new List<double>();
        var aps = new List<double>();
        foreach (var key in groups.Keys.OrderBy(x => x, StringComparer.Ordinal))
        {
            var items = groups[key].OrderBy(t => t.Rank).ToList();
            var rel = items.Select(t => t.Relevant).ToList();
            var topk = rel.Take(k).ToList();
            var totalRel = rel.Sum();
            recalls.Add(SafeDiv(topk.Sum(), totalRel));
            precisions.Add(SafeDiv(topk.Sum(), k));
            var rr = 0.0;
            for (var i = 0; i < rel.Count; i++)
                if (rel[i] != 0) { rr = 1.0 / (i + 1); break; }
            rrs.Add(rr);
            var dcg = 0.0;
            for (var i = 0; i < Math.Min(k, rel.Count); i++) dcg += rel[i] / Math.Log2(i + 2);
            var ideal = 0.0;
            for (var i = 1; i <= Math.Min(totalRel, k); i++) ideal += 1.0 / Math.Log2(i + 1);
            ndcgs.Add(SafeDiv(dcg, ideal));
            var hits = 0;
            var ap = 0.0;
            for (var i = 0; i < rel.Count; i++)
            {
                if (rel[i] == 0) continue;
                hits++;
                ap += (double)hits / (i + 1);
            }
            aps.Add(SafeDiv(ap, totalRel));
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "retrieval", ["k"] = (long)k, ["queries"] = (long)groups.Count,
            ["n"] = (long)rows.Count,
            ["recall_at_k"] = R(recalls.Count > 0 ? recalls.Sum() / recalls.Count : 0.0),
            ["precision_at_k"] = R(precisions.Count > 0 ? precisions.Sum() / precisions.Count : 0.0),
            ["mrr"] = R(rrs.Count > 0 ? rrs.Sum() / rrs.Count : 0.0),
            ["ndcg_at_k"] = R(ndcgs.Count > 0 ? ndcgs.Sum() / ndcgs.Count : 0.0),
            ["map"] = R(aps.Count > 0 ? aps.Sum() / aps.Count : 0.0),
        };
    }

    public static Dictionary<string, object?> Extraction(List<Dictionary<string, string?>> rows)
    {
        long em = 0, tp = 0, fp = 0, fn = 0;
        foreach (var r in rows)
        {
            var g = JsonSet(Cell(r, "gold_fields"));
            var p = JsonSet(Cell(r, "pred_fields"));
            if (g.SetEquals(p)) em++;
            tp += g.Intersect(p).Count();
            fp += p.Except(g).Count();
            fn += g.Except(p).Count();
        }
        var pr = SafeDiv(tp, tp + fp);
        var rc = SafeDiv(tp, tp + fn);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "extraction", ["n"] = (long)rows.Count,
            ["exact_match"] = R((double)em / rows.Count),
            ["field_precision"] = R(pr), ["field_recall"] = R(rc),
            ["field_f1"] = R(SafeDiv(2 * pr * rc, pr + rc)),
            ["tp"] = tp, ["fp"] = fp, ["fn"] = fn,
        };
    }

    private static HashSet<string> JsonSet(string raw)
    {
        var output = new HashSet<string>(StringComparer.Ordinal);
        using var doc = JsonIo.Parse(raw);
        if (doc.RootElement.ValueKind != JsonValueKind.Array) return output;
        foreach (var item in doc.RootElement.EnumerateArray()) output.Add(item.GetString() ?? "");
        return output;
    }

    public static Dictionary<string, object?> Generation(List<Dictionary<string, string?>> rows)
    {
        var em = 0;
        var charF1 = new List<double>();
        var setF1 = new List<double>();
        foreach (var r in rows)
        {
            var g = Cell(r, "reference");
            var p = Cell(r, "output");
            if (g == p) em++;
            var gs = g.ToHashSet();
            var ps = p.ToHashSet();
            var prec = SafeDiv(gs.Intersect(ps).Count(), ps.Count);
            var rec = SafeDiv(gs.Intersect(ps).Count(), gs.Count);
            charF1.Add(SafeDiv(2 * prec * rec, prec + rec));
            // Python `str.split()`（无参）按**任意空白**切且丢空段——不是只按空格切。
            var gt = g.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries)
                .ToHashSet(StringComparer.Ordinal);
            var pt = p.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries)
                .ToHashSet(StringComparer.Ordinal);
            var p2 = SafeDiv(gt.Intersect(pt).Count(), pt.Count);
            var r2 = SafeDiv(gt.Intersect(pt).Count(), gt.Count);
            setF1.Add(SafeDiv(2 * p2 * r2, p2 + r2));
        }
        var n = rows.Count;
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "generation", ["n"] = (long)n, ["exact_match"] = R((double)em / n),
            ["char_f1"] = R(charF1.Sum() / n), ["token_set_f1"] = R(setF1.Sum() / n),
        };
    }

    public static Dictionary<string, object?> Regression(List<Dictionary<string, string?>> rows)
    {
        var g = rows.Select(r => Num(r, "gold")).ToList();
        var p = rows.Select(r => Num(r, "pred")).ToList();
        var n = rows.Count;
        var mae = g.Zip(p, (a, b) => Math.Abs(a - b)).Sum() / n;
        var rmse = Math.Sqrt(g.Zip(p, (a, b) => (a - b) * (a - b)).Sum() / n);
        var mg = g.Sum() / n;
        var ssTot = g.Sum(a => (a - mg) * (a - mg));
        var ssRes = g.Zip(p, (a, b) => (a - b) * (a - b)).Sum();
        var nz = g.Zip(p, (a, b) => (a, b)).Where(t => t.a != 0).ToList();
        var mape = nz.Count > 0 ? nz.Sum(t => Math.Abs((t.a - t.b) / t.a)) / nz.Count : 0.0;
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "regression", ["n"] = (long)n, ["mae"] = R(mae), ["rmse"] = R(rmse),
            ["r2"] = R(1 - SafeDiv(ssRes, ssTot)), ["mape"] = R(mape),
            ["mape_samples"] = (long)nz.Count,
        };
    }

    public static Dictionary<string, object?> Calibration(List<Dictionary<string, string?>> rows, int bins = 10)
    {
        var pairs = rows.Select(r => (Prob: Num(r, "prob"), Label: Flag(r, "gold"))).ToList();
        if (pairs.Any(t => !(t.Prob >= 0.0 && t.Prob <= 1.0))) throw new ArgumentException("prob 必须在 [0,1]");
        var n = pairs.Count;
        var brier = pairs.Sum(t => (t.Prob - t.Label) * (t.Prob - t.Label)) / n;
        var buckets = new List<object?>();
        var ece = 0.0;
        for (var b = 0; b < bins; b++)
        {
            var lo = (double)b / bins;
            var hi = (double)(b + 1) / bins;
            var sel = pairs.Where(t => (t.Prob >= lo && t.Prob < hi) || (b == bins - 1 && t.Prob == 1.0)).ToList();
            if (sel.Count == 0) continue;
            var conf = sel.Sum(t => t.Prob) / sel.Count;
            var acc = (double)sel.Sum(t => t.Label) / sel.Count;
            ece += ((double)sel.Count / n) * Math.Abs(conf - acc);
            buckets.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["range"] = string.Format(CultureInfo.InvariantCulture, "[{0:F1},{1:F1}]", lo, hi),
                ["n"] = (long)sel.Count,
                ["confidence"] = R(conf), ["accuracy"] = R(acc), ["gap"] = R(Math.Abs(conf - acc)),
            });
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "calibration", ["n"] = (long)n, ["bins"] = (long)bins,
            ["nonempty_bins"] = (long)buckets.Count, ["ece"] = R(ece), ["brier"] = R(brier),
            ["buckets"] = buckets,
        };
    }

    public static Dictionary<string, object?> Agreement(List<Dictionary<string, string?>> rows)
    {
        var labels = rows.Select(r => Cell(r, "a")).Concat(rows.Select(r => Cell(r, "b")))
            .Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToList();
        var n = rows.Count;
        var cm = labels.ToDictionary(x => x,
            _ => labels.ToDictionary(y => y, _ => 0L, StringComparer.Ordinal), StringComparer.Ordinal);
        foreach (var r in rows) cm[Cell(r, "a")][Cell(r, "b")]++;
        var po = (double)labels.Sum(l => cm[l][l]) / n;
        var pe = labels.Sum(l =>
            ((double)cm[l].Values.Sum() / n) * ((double)labels.Sum(g => cm[g][l]) / n));
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "agreement", ["n"] = (long)n, ["labels"] = (long)labels.Count,
            ["observed_agreement"] = R(po), ["expected_agreement"] = R(pe),
            ["cohen_kappa"] = R(SafeDiv(po - pe, 1 - pe)),
            ["confusion"] = labels.ToDictionary(x => x,
                x => (object?)cm[x].ToDictionary(kv => kv.Key, kv => (object?)kv.Value, StringComparer.Ordinal),
                StringComparer.Ordinal),
        };
    }

    public static Dictionary<string, object?> Preference(List<Dictionary<string, string?>> rows)
    {
        var n = rows.Count;
        var agree = rows.Count(r => Cell(r, "judge").Trim() == Cell(r, "human").Trim());
        var win = rows.Count(r => Cell(r, "judge").Trim() == "a");
        var loss = rows.Count(r => Cell(r, "judge").Trim() == "b");
        var tie = n - win - loss;
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "preference", ["n"] = (long)n, ["agreement"] = R((double)agree / n),
            ["win"] = (long)win, ["loss"] = (long)loss, ["tie"] = (long)tie,
            ["win_rate_excl_tie"] = R(SafeDiv(win, win + loss)),
        };
    }

    public static Dictionary<string, object?> ExactJudgement(List<Dictionary<string, string?>> rows, int k = 4)
    {
        var groups = new Dictionary<string, List<int>>(StringComparer.Ordinal);
        foreach (var r in rows)
        {
            var key = Cell(r, "task_id");
            if (!groups.TryGetValue(key, out var list)) groups[key] = list = new List<int>();
            list.Add(Flag(r, "passed"));
        }
        var pass1 = new List<double>();
        var passk = new List<double>();
        var skipped = 0;
        var used = 0;
        foreach (var key in groups.Keys.OrderBy(x => x, StringComparer.Ordinal))
        {
            var ys = groups[key];
            var n = ys.Count;
            var c = ys.Sum();
            pass1.Add((double)c / n);
            if (n < k) { skipped++; continue; }
            used++;
            if (c == 0) { passk.Add(0.0); continue; }
            if (n - c < k) { passk.Add(1.0); continue; }
            var num = 1.0;
            for (var i = 0; i < k; i++) num *= (double)(n - c - i) / (n - i);
            passk.Add(1 - num);
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "exact_judgement", ["k"] = (long)k, ["tasks"] = (long)groups.Count,
            ["n"] = (long)rows.Count,
            ["pass_at_1"] = R(pass1.Count > 0 ? pass1.Sum() / pass1.Count : 0.0),
            ["pass_at_k"] = R(passk.Count > 0 ? passk.Sum() / passk.Count : 0.0),
            ["tasks_used_for_passk"] = (long)used,
            ["tasks_skipped_insufficient_samples"] = (long)skipped,
        };
    }

    public static Dictionary<string, object?> LatencyCost(List<Dictionary<string, string?>> rows,
        double pricePer1kIn = 0.0, double pricePer1kOut = 0.0)
    {
        var lat = rows.Select(r => Num(r, "latency_ms")).OrderBy(x => x).ToList();
        double Pct(double q)
        {
            var idx = Math.Max(0, Math.Min(lat.Count - 1, (int)Math.Ceiling(q * lat.Count) - 1));
            return R(lat[idx]);
        }
        var tin = rows.Sum(r => Num(r, "tokens_in"));
        var tout = rows.Sum(r => Num(r, "tokens_out"));
        var n = rows.Count;
        var cost = tin / 1000.0 * pricePer1kIn + tout / 1000.0 * pricePer1kOut;
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "latency_cost", ["n"] = (long)n,
            ["p50_ms"] = Pct(0.50), ["p95_ms"] = Pct(0.95), ["p99_ms"] = Pct(0.99),
            ["mean_ms"] = R(lat.Sum() / n), ["max_ms"] = R(lat[^1]),
            ["tokens_in"] = (long)Math.Truncate(tin), ["tokens_out"] = (long)Math.Truncate(tout),
            ["price_per_1k_in"] = R(pricePer1kIn), ["price_per_1k_out"] = R(pricePer1kOut),
            ["cost_total"] = R(cost), ["cost_per_1k_calls"] = R(cost / n * 1000),
        };
    }

    public static Dictionary<string, object?> Drift(List<Dictionary<string, string?>> rows)
    {
        const double eps = 1e-6;
        var psi = 0.0;
        var detail = new List<object?>();
        foreach (var r in rows)
        {
            var p = Num(r, "expected") + eps;
            var q = Num(r, "actual") + eps;
            var term = (p - q) * Math.Log(p / q);
            psi += term;
            detail.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["bucket"] = Cell(r, "bucket"), ["expected"] = R(p), ["actual"] = R(q),
                ["term"] = R(term),
            });
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "drift", ["buckets"] = (long)rows.Count, ["psi"] = R(psi),
            ["smoothing_epsilon"] = eps, ["detail"] = detail,
        };
    }

    public static Dictionary<string, object?> ContractCompliance(List<Dictionary<string, string?>> rows)
    {
        var n = rows.Count;
        var ok = rows.Count(r => Flag(r, "valid") == 1);
        var missing = new Dictionary<string, long>(StringComparer.Ordinal);
        foreach (var r in rows)
            foreach (var raw in Cell(r, "missing_fields").Replace("|", ",").Replace(";", ",").Split(','))
            {
                var f = raw.Trim();
                if (f.Length > 0) missing[f] = missing.GetValueOrDefault(f) + 1;
            }
        var top = missing.OrderBy(kv => -kv.Value).ThenBy(kv => kv.Key, StringComparer.Ordinal).Take(5);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["family"] = "contract_compliance", ["n"] = (long)n,
            ["compliance_rate"] = R((double)ok / n), ["violations"] = (long)(n - ok),
            ["missing_top"] = top.Select(kv => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
                { ["field"] = kv.Key, ["count"] = kv.Value }).ToList(),
        };
    }

    // ------------------------------------------------------------------ 求值入口

    public static readonly string[] Families =
    {
        "agreement", "calibration", "classification", "contract_compliance", "drift",
        "exact_judgement", "extraction", "generation", "latency_cost", "preference",
        "regression", "retrieval",
    };

    /// <summary><c>evaluate(family, rows, **params)</c>：追加 <c>digits</c> 与 <c>note</c> 两个元字段。</summary>
    public static Dictionary<string, object?> Evaluate(string family,
        List<Dictionary<string, string?>> rows, Dictionary<string, object?>? parameters = null)
    {
        var p = parameters ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        Dictionary<string, object?> body = family switch
        {
            "classification" => Classification(rows),
            "retrieval" => Retrieval(rows, PyInt(p.GetValueOrDefault("k"), 5)),
            "extraction" => Extraction(rows),
            "generation" => Generation(rows),
            "regression" => Regression(rows),
            "calibration" => Calibration(rows, PyInt(p.GetValueOrDefault("bins"), 10)),
            "agreement" => Agreement(rows),
            "preference" => Preference(rows),
            "exact_judgement" => ExactJudgement(rows, PyInt(p.GetValueOrDefault("k"), 4)),
            "latency_cost" => LatencyCost(rows, PyDouble(p.GetValueOrDefault("price_per_1k_in")),
                PyDouble(p.GetValueOrDefault("price_per_1k_out"))),
            "drift" => Drift(rows),
            "contract_compliance" => ContractCompliance(rows),
            _ => throw new ArgumentException(
                $"未登记度量族：{PyScalar.PyRepr(family)}（可选：{ReprList(Families)}）"),
        };
        body["digits"] = (long)Digits;
        body["note"] = "样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；"
                       + "本报告由 core/domain_metrics.py 确定性复算（T4）";
        return body;
    }

    private static int PyInt(object? v, int fallback) => v switch
    {
        long l => (int)l,
        int i => i,
        double d => (int)Math.Truncate(d),
        string s when double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out var parsed)
            => (int)Math.Truncate(parsed),
        _ => fallback,
    };

    private static double PyDouble(object? v) => v switch
    {
        long l => l,
        int i => i,
        double d => d,
        string s when double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out var parsed) => parsed,
        _ => 0.0,
    };

    private static string ReprList(IEnumerable<string> items) =>
        "[" + string.Join(", ", items.Select(PyScalar.PyRepr)) + "]";

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
