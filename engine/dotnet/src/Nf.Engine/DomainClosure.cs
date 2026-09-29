using System.Globalization;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>scripts/ai_domain_closure.py</c>：概念前置闭包**只读求值器**（四件产物 + 三件可证检查）。
///
/// 图语义**不自带一套**——一律走 <see cref="ConceptGraph"/>（与 check32 的概念图子扫描同一实现），
/// 避免「门禁算一套、求值器算另一套」的双源漂移。
/// 检索词解析：条目键 → 别名 → 概念名（大小写与首尾空白无关）；并列按 id 升序，集合输出一律排序。
/// </summary>
public static class DomainClosure
{
    public static Dictionary<string, object?>? SamplesFor(string asset)
    {
        var stem = Path.GetFileNameWithoutExtension(asset);
        using var doc = JsonIo.Parse(ClosureSamples.SamplesJson);
        var all = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>;
        return all?.GetValueOrDefault(stem) as Dictionary<string, object?>;
    }

    /// <summary>四件产物 + 判定，打包成结构化结果。</summary>
    public static Dictionary<string, object?> Report(
        Dictionary<string, object?> graph, string target, IReadOnlyList<string> loaded, string assetLabel)
    {
        var tid = ConceptGraph.Resolve(graph, target);
        var meta = ConceptGraph.NodeMeta(graph);
        var bids = ConceptGraph.NodeBranch(graph);
        var clo = ConceptGraph.Closure(graph, tid);
        var miss = ConceptGraph.Missing(graph, tid, loaded);
        var order = ConceptGraph.Toposort(graph);
        var front = ConceptGraph.Frontier(graph, loaded);
        var branches = ConceptGraph.BranchMap(graph)
            .OrderBy(kv => kv.Key, StringComparer.Ordinal)
            .ToDictionary(kv => kv.Key, kv => (object?)(long)kv.Value.Count, StringComparer.Ordinal);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["asset"] = assetLabel,
            ["graph_version"] = PyStrOrEmpty(graph.GetValueOrDefault("version")),
            ["domain"] = PyStrOrEmpty(graph.GetValueOrDefault("domain")),
            ["nodes"] = (long)ConceptGraph.InPackageIds(graph).Count,
            ["external_prereqs"] = (long)ConceptGraph.PyList(graph.GetValueOrDefault("external_prereqs")).Count,
            ["branches"] = branches,
            ["target"] = tid,
            ["target_query"] = target,
            ["target_name"] = PyStrOrEmpty(meta.GetValueOrDefault(tid)?.GetValueOrDefault("name")),
            ["target_branch"] = bids.GetValueOrDefault(tid, ""),
            ["loaded"] = loaded.Select(x => x).Distinct(StringComparer.Ordinal)
                .OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
            ["closure"] = clo.Cast<object?>().ToList(),
            ["closure_size"] = (long)clo.Count,
            ["missing"] = miss.Cast<object?>().ToList(),
            ["missing_size"] = (long)miss.Count,
            ["missing_external"] = miss
                .Where(c => PyTruthy(meta.GetValueOrDefault(c)?.GetValueOrDefault("external")))
                .Cast<object?>().ToList(),
            ["readiness"] = miss.Count == 0,
            ["load_order"] = order.Cast<object?>().ToList(),
            ["load_order_size"] = (long)order.Count,
            ["frontier"] = front.Cast<object?>().ToList(),
            ["frontier_size"] = (long)front.Count,
        };
    }

    public static string Render(Dictionary<string, object?> res)
    {
        var branches = (Dictionary<string, object?>)res["branches"]!;
        var lines = new List<string>
        {
            "== 概念前置闭包求值（只读）==",
            $"资产：{PyStr(res["asset"])}（v{PyStr(res["graph_version"])} · 域 {PyStr(res["domain"])} · "
            + $"节点 {PyStr(res["nodes"])} + 包外前置 {PyStr(res["external_prereqs"])} · 分支 "
            + string.Join(" / ", branches.OrderBy(kv => kv.Key, StringComparer.Ordinal)
                .Select(kv => $"{kv.Key}={PyStr(kv.Value)}")) + "）",
            $"目标：{PyStr(res["target"])}（{PyStr(res["target_name"])}）· 分支 "
            + (PyStr(res["target_branch"]).Length > 0 ? PyStr(res["target_branch"]) : "-"),
            $"[1] 前置闭包 closure({PyStr(res["target"])})：{PyStr(res["closure_size"])} 个概念",
            $"    {string.Join("、", ConceptGraph.PyList(res["closure"]).Select(PyStr))}",
            $"[2] 缺失清单 missing({PyStr(res["target"])}, L)：{PyStr(res["missing_size"])} 个概念",
            "    " + (ConceptGraph.PyList(res["missing"]).Count > 0
                ? string.Join("、", ConceptGraph.PyList(res["missing"]).Select(PyStr))
                : "（空 · 已就绪）"),
            $"[3] 合法装载序 load_order（toposort 确定性线性化）：{PyStr(res["load_order_size"])} 个概念",
            $"    {string.Join("、", ConceptGraph.PyList(res["load_order"]).Select(PyStr))}",
            $"[4] 下一步可装载集 frontier(L)：{PyStr(res["frontier_size"])} 个概念",
            "    " + (ConceptGraph.PyList(res["frontier"]).Count > 0
                ? string.Join("、", ConceptGraph.PyList(res["frontier"]).Select(PyStr))
                : "（空）"),
            $"已装载集 L：{ConceptGraph.PyList(res["loaded"]).Count} 个 · 就绪判定 readiness："
            + (PyTruthy(res["readiness"]) ? "就绪" : "未就绪"),
        };
        var ext = ConceptGraph.PyList(res["missing_external"]);
        if (ext.Count > 0)
            lines.Add($"    其中包外前置（读者侧应已具备，不建模块）：{string.Join("、", ext.Select(PyStr))}");
        return string.Join("\n", lines);
    }

    /// <summary>条目键全表 + 别名（人读；供 <c>--list</c>）。</summary>
    public static string RenderList(Dictionary<string, object?> graph)
    {
        var meta = ConceptGraph.NodeMeta(graph);
        var bids = ConceptGraph.NodeBranch(graph);
        var lines = new List<string>
        {
            $"== 条目键全表（{ConceptGraph.InPackageIds(graph).Count} 概念 + "
            + $"{ConceptGraph.PyList(graph.GetValueOrDefault("external_prereqs")).Count} 包外前置）==",
        };
        foreach (var nid in ConceptGraph.InPackageIds(graph))
        {
            var rec = meta[nid];
            var alias = string.Join("、", ConceptGraph.PyList(rec.GetValueOrDefault("aliases")).Select(PyStr));
            lines.Add("  " + PadCp(nid, 4) + " [" + PadCp(bids.GetValueOrDefault(nid, "-"), 7) + "] "
                      + PadCp(PyStrOrEmpty(rec.GetValueOrDefault("layer"), "-"), 6) + " "
                      + PyStrOrEmpty(rec.GetValueOrDefault("name"))
                      + (alias.Length > 0 ? $"（别名：{alias}）" : ""));
        }
        return string.Join("\n", lines);
    }

    /// <summary>前置缺失清单（只列非空，按缺失规模降序；供 <c>--gaps</c>）。</summary>
    public static string RenderGaps(Dictionary<string, object?> graph, IReadOnlyList<string> loaded,
        string branch, int limit)
    {
        var meta = ConceptGraph.NodeMeta(graph);
        var bids = ConceptGraph.NodeBranch(graph);
        var rows = new List<(string Nid, List<string> Miss)>();
        foreach (var nid in ConceptGraph.InPackageIds(graph))
        {
            if (branch.Length > 0 && bids.GetValueOrDefault(nid, "") != branch) continue;
            var miss = ConceptGraph.Missing(graph, nid, loaded);
            if (miss.Count > 0) rows.Add((nid, miss));
        }
        rows = rows.OrderBy(r => -r.Miss.Count).ThenBy(r => r.Nid, StringComparer.Ordinal).ToList();
        var lines = new List<string>
        {
            $"== 前置缺失清单（L={loaded.Distinct(StringComparer.Ordinal).Count()} 概念"
            + (branch.Length > 0 ? " · 分支 " + branch : "") + $" · 非空项 {rows.Count}）==",
        };
        foreach (var (nid, miss) in rows.Take(limit))
        {
            var ext = miss.Where(c => PyTruthy(meta.GetValueOrDefault(c)?.GetValueOrDefault("external"))).ToList();
            var head = string.Join("、", miss.Take(8)) + (miss.Count > 8 ? "…" : "");
            lines.Add("  " + PadCp(nid, 4) + " " + PadCp(PySlice(PyStrOrEmpty(meta.GetValueOrDefault(nid)?.GetValueOrDefault("name")), 30), 30)
                      + " 缺 " + miss.Count.ToString(CultureInfo.InvariantCulture).PadLeft(2) + "：" + head
                      + (ext.Count > 0 ? $"（含包外前置 {string.Join("、", ext)}）" : ""));
        }
        if (rows.Count > limit) lines.Add($"  …（另有 {rows.Count - limit} 项，--limit 调整）");
        return string.Join("\n", lines);
    }

    /// <summary>自检 → (failures, passes)。含负例注入：环 / 悬空 / 别名重复 / 分支缺口。</summary>
    public static (List<string> Fails, List<string> Passes) SelfCheck(string asset)
    {
        var fails = new List<string>();
        var passes = new List<string>();
        void Expect(bool cond, string label) => (cond ? passes : fails).Add(label);

        var graph = ConceptGraph.LoadGraph(asset);
        var pack = SamplesFor(asset);
        Expect(ConceptGraph.Problems(graph).Count == 0,
            "图健康度：无环 / 无悬空 / 有溯源 / 层位合法 / 别名唯一 / 分支完备");
        var order = ConceptGraph.Toposort(graph);
        Expect(order.Count == ConceptGraph.InPackageIds(graph).Count
               && ConceptGraph.Violations(graph, order).Count == 0,
            "load_order 覆盖全部包内概念且对图零违反边");
        if (pack is null)
        {
            Expect(ConceptGraph.Toposort(graph).SequenceEqual(order, StringComparer.Ordinal),
                "确定性：同输入两次求值逐字节一致");
            Expect(ConceptGraph.Violations(graph, order.AsEnumerable().Reverse().ToList()).Count > 0,
                "负例：逆序序列的违反边非零");
            return (fails, passes);
        }

        var t = PyStr(pack["closure_target"]);
        var clo = ConceptGraph.Closure(graph, t);
        Expect(clo.Count == PyInt(pack["closure_size"]) && clo.Contains(t) && clo.Contains(PyStr(pack["closure_root"])),
            $"closure({t}) = {PyStr(pack["closure_size"])} 个概念（含自身与包外前置 {PyStr(pack["closure_root"])}）");
        Expect(ConceptGraph.Toposort(graph).SequenceEqual(order, StringComparer.Ordinal)
               && ConceptGraph.Closure(graph, t).SequenceEqual(clo, StringComparer.Ordinal),
            "确定性：同输入两次求值逐字节一致");
        var loaded = ConceptGraph.PyList(pack["missing_loaded"]).Select(PyStr).ToList();
        var miss = ConceptGraph.Missing(graph, t, loaded);
        Expect(miss.Count == PyInt(pack["missing_size"])
               && ConceptGraph.PyList(pack["missing_has"]).Select(PyStr).All(c => miss.Contains(c)),
            $"missing({t}, {{{string.Join(",", loaded)}}}) = {PyStr(pack["missing_size"])} 个概念");
        var mt = PyStr(pack["min_target"]);
        Expect(ConceptGraph.Closure(graph, mt).SequenceEqual(
                ConceptGraph.PyList(pack["min_closure"]).Select(PyStr).OrderBy(x => x, StringComparer.Ordinal),
                StringComparer.Ordinal),
            $"closure({mt}) = {{{string.Join(", ", ConceptGraph.PyList(pack["min_closure"]).Select(PyStr))}}}");
        Expect(ConceptGraph.PyList(pack["resolve_cases"]).All(c =>
                ConceptGraph.Resolve(graph, PyStr(ConceptGraph.PyList(c)[0])) == PyStr(ConceptGraph.PyList(c)[1])),
            "检索词解析：别名（含大小写 / 空白）与条目键同解");
        var aliasPair = ConceptGraph.PyList(pack["alias_pair"]);
        Expect(ConceptGraph.Closure(graph, PyStr(aliasPair[0])).SequenceEqual(
                ConceptGraph.Closure(graph, PyStr(aliasPair[1])), StringComparer.Ordinal),
            "别名闭包与条目键闭包一致");
        var front = ConceptGraph.Frontier(graph, ConceptGraph.PyList(pack["frontier_loaded"]).Select(PyStr).ToList());
        Expect(front.Contains(PyStr(pack["frontier_has"])) && !front.Contains(PyStr(pack["frontier_not"])),
            $"frontier({{{string.Join(",", ConceptGraph.PyList(pack["frontier_loaded"]).Select(PyStr))}}}) 含 "
            + $"{PyStr(pack["frontier_has"])} 且不含前置未齐的 {PyStr(pack["frontier_not"])}");
        Expect(ConceptGraph.Frontier(graph, ConceptGraph.PyList(pack["frontier_loaded"]).Select(PyStr).ToList(),
                   PyStr(pack["branch_empty"])).Count == 0,
            $"frontier 分支过滤生效（{PyStr(pack["branch_empty"])} 支此时为空）");

        var cycle = Inject(graph, PyStr(ConceptGraph.PyList(pack["inject_cycle"])[0]), "prereqs",
            PyStr(ConceptGraph.PyList(pack["inject_cycle"])[1]));
        Expect(ConceptGraph.Problems(cycle).Any(i => i.Contains("环")), "负例：注入环被检出");
        var dang = Inject(graph, PyStr(ConceptGraph.PyList(pack["inject_dangling"])[0]), "prereqs",
            PyStr(ConceptGraph.PyList(pack["inject_dangling"])[1]));
        Expect(ConceptGraph.Problems(dang).Any(i => i.Contains("悬空")), "负例：悬空前置被检出");
        var dup = Inject(graph, PyStr(ConceptGraph.PyList(pack["inject_dup_alias"])[0]), "aliases",
            PyStr(ConceptGraph.PyList(pack["inject_dup_alias"])[1]));
        Expect(ConceptGraph.Problems(dup).Any(i => i.Contains("别名重复")), "负例：重复别名被检出");
        var dropped = PyStr(pack["branch_drop"]);
        var nbr = (Dictionary<string, object?>)DeepCopy(graph)!;
        foreach (var br in ConceptGraph.PyList(nbr.GetValueOrDefault("branches")).OfType<Dictionary<string, object?>>())
            br["nodes"] = ConceptGraph.PyList(br.GetValueOrDefault("nodes")).Select(PyStr)
                .Where(n => n != dropped).Cast<object?>().ToList();
        Expect(ConceptGraph.Problems(nbr).Any(i => i.Contains("未归入任何分支")), "负例：分支缺口被检出");
        Expect(ConceptGraph.Violations(graph, order.AsEnumerable().Reverse().ToList()).Count > 0,
            "负例：逆序序列的违反边非零");
        return (fails, passes);
    }

    public static Dictionary<string, List<string>> Orderings(Dictionary<string, object?> graph)
    {
        var output = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var item in ConceptGraph.PyList(graph.GetValueOrDefault("orderings"))
                     .OfType<Dictionary<string, object?>>())
        {
            var id = PyStrOrEmpty(item.GetValueOrDefault("id"));
            if (id.Length == 0) continue;
            output[id] = ConceptGraph.PyList(item.GetValueOrDefault("seq")).Select(PyStr).ToList();
        }
        return output;
    }

    public static List<string> LoadedArg(string raw) =>
        (raw ?? "").Split(',', StringSplitOptions.None).Select(x => x.Trim())
            .Where(x => x.Length > 0).ToList();

    private static Dictionary<string, object?> Inject(
        Dictionary<string, object?> graph, string nodeId, string field, string value)
    {
        var copy = (Dictionary<string, object?>)DeepCopy(graph)!;
        foreach (var node in ConceptGraph.PyList(copy.GetValueOrDefault("nodes"))
                     .OfType<Dictionary<string, object?>>())
        {
            if (PyStrOrEmpty(node.GetValueOrDefault("id")) != nodeId) continue;
            var list = ConceptGraph.PyList(node.GetValueOrDefault(field)).Select(PyStr).Cast<object?>().ToList();
            list.Add(value);
            node[field] = list;
        }
        return copy;
    }

    private static object? DeepCopy(object? node) => node switch
    {
        Dictionary<string, object?> map => map.ToDictionary(kv => kv.Key, kv => DeepCopy(kv.Value), StringComparer.Ordinal),
        List<object?> list => list.Select(DeepCopy).ToList(),
        _ => node,
    };

    private static string PadCp(string s, int width)
    {
        var len = PyScalar.PyLen(s);
        return len >= width ? s : s + new string(' ', width - len);
    }

    private static string PySlice(string s, int maxCodePoints) => PyScalar.PySlice(s, maxCodePoints);

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

    private static long PyInt(object? v) => v switch
    {
        long l => l,
        int i => i,
        double d => (long)d,
        _ => 0,
    };

    private static string PyStrOrEmpty(object? v, string fallback = "") =>
        PyTruthy(v) ? PyStr(v) : fallback;

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
