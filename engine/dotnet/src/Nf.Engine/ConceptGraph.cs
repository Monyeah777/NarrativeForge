using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/concept_graph.py</c>：概念前置偏序图的**图语义库 + 门禁体检**。
///
/// 判据（真源注释即口径）：结构（id 唯一 / 层位 ∈ P00–P80 / 必备 name / 边带 provenance）·
/// 图论（无环 / 前置无悬空 / 无自环）· 检索面（别名唯一）· 分支面（分支 id 唯一 / 每概念恰属一支 / 成员须真实存在）·
/// **证据面**（每个 provenance 键须在图例在册；`provenance_strength` ∈ 四级且与**节点外部覆盖**自洽）。
/// 门禁只判「声明在场 + 与图例一致」，**不判证据是否真的充分**（那不可判定，硬判会造假判据）。
///
/// YAML 取块与解析沿用本引擎既有件：围栏正则与真源逐字一致（`^```yaml` 锚定 + 标记行须是块内首键），
/// 正文交给 <see cref="MiniYaml"/>（子集越界即 fail-closed）。
/// </summary>
public static class ConceptGraph
{
    public const string BlockMarker = "concept_graph";
    public const string DefaultAsset = "community/AI系统域包/assets/CONCEPT_GRAPH.md";

    public static readonly string[] Layers = { "P00", "P10", "P20", "P30", "P40", "P50", "P60", "P70", "P80" };
    public static readonly string[] ProvenanceStrengths = { "external", "mixed", "domain-logic", "inferred" };

    /// <summary>非外部来源键（推断类）——覆盖度判定的分母之外。</summary>
    private static readonly string[] NonSourceKeys = { "inferred", "domain-logic" };

    //: 真源 `_FENCE = (?ms)^```yaml\s*\n(.*?)^``` ` —— 锚定与 DOTALL/MULTILINE 逐字照抄
    private static readonly Regex FenceRe = new(@"(?ms)^```yaml\s*\n(.*?)^```", RegexOptions.CultureInvariant);
    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public sealed class ClosureError : Exception
    {
        public ClosureError(string message) : base(message) { }
    }

    // ---------------------------------------------------------------- 读取机读块

    /// <summary>取含标记的 ```yaml 围栏正文（无则空串）——标记行须匹配 <c>^marker\s*:</c>。</summary>
    public static string FencedBlock(string text, string marker = BlockMarker)
    {
        foreach (Match m in FenceRe.Matches(text))
        {
            var body = m.Groups[1].Value;
            if (Regex.IsMatch(body, @"(?m)^" + Regex.Escape(marker) + @"\s*:", RegexOptions.CultureInvariant))
                return body;
        }
        return "";
    }

    public static Dictionary<string, object?> LoadGraph(string assetPath)
    {
        if (!File.Exists(assetPath))
            throw new ClosureError($"概念图资产不存在：{AssetShelf.PyPath(assetPath)}"
                                   + "（修复指引：给出域包内 assets/CONCEPT_GRAPH.md 路径）");
        var body = FencedBlock(ReadText(assetPath));
        if (body.Length == 0)
            throw new ClosureError($"资产缺 `{BlockMarker}:` 机器可读块：{AssetShelf.PyPath(assetPath)}"
                                   + $"（修复指引：补 ```yaml 围栏块，块内首键为 {BlockMarker}）");
        var data = MiniYaml.Parse(body);
        if (data.GetValueOrDefault(BlockMarker) is not Dictionary<string, object?> graph)
            throw new ClosureError($"机读块结构非法：{AssetShelf.PyPath(assetPath)}"
                                   + $"（修复指引：顶层键须为 {BlockMarker}）");
        return graph;
    }

    /// <summary>仓库内带概念图机读块的资产（相对 posix 路径，排序）。</summary>
    public static List<string> GraphAssets(string root)
    {
        var output = new List<string>();
        foreach (var (rel, full) in AssetShelf.MarkdownFiles(root))
        {
            string text;
            try
            {
                text = ReadText(full);
            }
            catch (Exception exc) when (exc is IOException or UnauthorizedAccessException)
            {
                continue;
            }
            if (FencedBlock(text).Length > 0) output.Add(rel);
        }
        return output;
    }

    // ---------------------------------------------------------------- 图语义

    /// <summary>{概念 id: 直接前置 id 列表}（保持资产声明序，去重）。</summary>
    public static Dictionary<string, List<string>> PrereqsOf(Dictionary<string, object?> graph)
    {
        var output = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var node in PyList(graph.GetValueOrDefault("nodes")).OfType<Dictionary<string, object?>>())
        {
            var id = PyStrOrEmpty(node.GetValueOrDefault("id"));
            if (id.Length == 0) continue;
            var seen = new List<string>();
            foreach (var raw in PyList(node.GetValueOrDefault("prereqs")))
            {
                var p = PyStr(raw);
                if (!seen.Contains(p)) seen.Add(p);
            }
            output[id] = seen;
        }
        return output;
    }

    /// <summary>{概念 id: 节点元信息}（含包外前置，标 external=true）。</summary>
    public static Dictionary<string, Dictionary<string, object?>> NodeMeta(Dictionary<string, object?> graph)
    {
        var output = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var node in PyList(graph.GetValueOrDefault("nodes")).OfType<Dictionary<string, object?>>())
        {
            var id = PyStrOrEmpty(node.GetValueOrDefault("id"));
            if (id.Length == 0) continue;
            var rec = new Dictionary<string, object?>(node, StringComparer.Ordinal) { ["external"] = false };
            output[id] = rec;
        }
        foreach (var node in PyList(graph.GetValueOrDefault("external_prereqs")).OfType<Dictionary<string, object?>>())
        {
            var id = PyStrOrEmpty(node.GetValueOrDefault("id"));
            if (id.Length == 0) continue;
            var rec = new Dictionary<string, object?>(node, StringComparer.Ordinal) { ["external"] = true };
            output.TryAdd(id, rec);
        }
        return output;
    }

    /// <summary>包内概念 id（外部前置族不计入装载序）。</summary>
    public static List<string> InPackageIds(Dictionary<string, object?> graph) =>
        PrereqsOf(graph).Keys.OrderBy(k => k, StringComparer.Ordinal).ToList();

    /// <summary>{分支 id: [概念 id]}（保持资产声明序）。</summary>
    public static Dictionary<string, List<string>> BranchMap(Dictionary<string, object?> graph)
    {
        var output = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var br in PyList(graph.GetValueOrDefault("branches")).OfType<Dictionary<string, object?>>())
        {
            var id = PyStrOrEmpty(br.GetValueOrDefault("id"));
            if (id.Length == 0) continue;
            output[id] = PyList(br.GetValueOrDefault("nodes")).Select(PyStr).ToList();
        }
        return output;
    }

    /// <summary>{概念 id: 分支 id}（未归入任何分支者不进映射）。</summary>
    public static Dictionary<string, string> NodeBranch(Dictionary<string, object?> graph)
    {
        var output = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var (bid, nodes) in BranchMap(graph))
            foreach (var nid in nodes)
                output.TryAdd(nid, bid);
        return output;
    }

    /// <summary>{别名（小写折叠）: 概念 id}；别名重复即抛错（防歧义）。</summary>
    public static Dictionary<string, string> AliasMap(Dictionary<string, object?> graph)
    {
        var output = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var node in PyList(graph.GetValueOrDefault("nodes")).OfType<Dictionary<string, object?>>())
        {
            var nid = PyStrOrEmpty(node.GetValueOrDefault("id"));
            if (nid.Length == 0) continue;
            foreach (var raw in PyList(node.GetValueOrDefault("aliases")))
            {
                var key = PyStr(raw).Trim().ToLowerInvariant();
                if (key.Length == 0) continue;
                if (output.TryGetValue(key, out var prior) && prior != nid)
                    throw new ClosureError($"别名重复：{PyScalar.PyRepr(raw)} 同时指向 {prior} 与 {nid}"
                                           + "（修复指引：别名在图内须唯一——与 01 §1.1 词法纪律同源）");
                output[key] = nid;
            }
        }
        return output;
    }

    /// <summary>(有外部来源锚的节点数, 包内节点总数)——覆盖度是强度声明的判定依据。</summary>
    public static (int Covered, int Total) ExternalCoverage(Dictionary<string, object?> graph)
    {
        var total = 0;
        var covered = 0;
        foreach (var node in PyList(graph.GetValueOrDefault("nodes")).OfType<Dictionary<string, object?>>())
        {
            if (PyStrOrEmpty(node.GetValueOrDefault("id")).Length == 0) continue;
            total++;
            var prov = PyList(node.GetValueOrDefault("provenance")).Select(PyStr).ToList();
            if (prov.Any(p => !NonSourceKeys.Contains(p))) covered++;
        }
        return (covered, total);
    }

    /// <summary>图上声明的证据强度（缺省空串——由 <see cref="Problems"/> 要求显式声明）。</summary>
    public static string ProvenanceStrength(Dictionary<string, object?> graph) =>
        PyStrOrEmpty(graph.GetValueOrDefault("provenance_strength")).Trim();

    /// <summary>检索词 → 概念 id（顺序：条目键 → 别名 → 概念名）。</summary>
    public static string Resolve(Dictionary<string, object?> graph, string token)
    {
        var t = token.Trim();
        var meta = NodeMeta(graph);
        if (meta.ContainsKey(t)) return t;
        var am = AliasMap(graph);
        var folded = t.ToLowerInvariant();
        if (am.TryGetValue(folded, out var hit)) return hit;
        foreach (var (nid, rec) in meta)
        {
            if (PyStrOrEmpty(rec.GetValueOrDefault("name")).Trim().ToLowerInvariant() == folded) return nid;
        }
        throw new ClosureError($"检索词不在图中：{token}（修复指引：用条目键 Cxx、别名或概念名——"
                               + "`--list` 可枚举全表）");
    }

    /// <summary>传递闭包 closure(target) = {target} ∪ ⋃ closure(p)；返回排序列表。</summary>
    public static List<string> Closure(Dictionary<string, object?> graph, string target)
    {
        var tid = Resolve(graph, target);
        var prereqs = PrereqsOf(graph);
        var seen = new HashSet<string>(StringComparer.Ordinal);
        var stack = new Stack<string>();
        stack.Push(tid);
        while (stack.Count > 0)
        {
            var cur = stack.Pop();
            if (!seen.Add(cur)) continue;
            foreach (var p in prereqs.GetValueOrDefault(cur) ?? new List<string>()) stack.Push(p);
        }
        return seen.OrderBy(x => x, StringComparer.Ordinal).ToList();
    }

    /// <summary>缺失清单 missing(target, L) = closure(target) − L。</summary>
    public static List<string> Missing(Dictionary<string, object?> graph, string target, IReadOnlyList<string> loaded)
    {
        var have = loaded.Select(x => x).ToHashSet(StringComparer.Ordinal);
        return Closure(graph, target).Where(c => !have.Contains(c)).ToList();
    }

    /// <summary>就绪清单 frontier(L) = {c ∉ L : prereqs(c) ⊆ L}（可限定分支）。</summary>
    public static List<string> Frontier(Dictionary<string, object?> graph, IReadOnlyList<string> loaded, string branch = "")
    {
        var have = loaded.ToHashSet(StringComparer.Ordinal);
        var prereqs = PrereqsOf(graph);
        var bids = branch.Length > 0 ? NodeBranch(graph) : new Dictionary<string, string>(StringComparer.Ordinal);
        var output = new List<string>();
        foreach (var c in InPackageIds(graph))
        {
            if (have.Contains(c)) continue;
            if (branch.Length > 0 && bids.GetValueOrDefault(c, "") != branch) continue;
            if ((prereqs.GetValueOrDefault(c) ?? new List<string>()).All(p => have.Contains(p))) output.Add(c);
        }
        return output.OrderBy(x => x, StringComparer.Ordinal).ToList();
    }

    /// <summary>确定性拓扑序（Kahn；并列按 id 升序）。图有环 → 抛错。</summary>
    public static List<string> Toposort(Dictionary<string, object?> graph)
    {
        var prereqs = PrereqsOf(graph);
        var ids = prereqs.Keys.OrderBy(x => x, StringComparer.Ordinal).ToList();
        var indeg = ids.ToDictionary(i => i, _ => 0, StringComparer.Ordinal);
        var children = ids.ToDictionary(i => i, _ => new List<string>(), StringComparer.Ordinal);
        foreach (var i in ids)
        {
            foreach (var p in prereqs[i])
            {
                if (!indeg.ContainsKey(p)) continue;
                indeg[i]++;
                children[p].Add(i);
            }
        }
        var ready = ids.Where(i => indeg[i] == 0).OrderBy(x => x, StringComparer.Ordinal).ToList();
        var output = new List<string>();
        while (ready.Count > 0)
        {
            var cur = ready[0];
            ready.RemoveAt(0);
            output.Add(cur);
            foreach (var nxt in children[cur].OrderBy(x => x, StringComparer.Ordinal))
            {
                indeg[nxt]--;
                if (indeg[nxt] == 0) ready.Add(nxt);
            }
            ready.Sort(StringComparer.Ordinal);
        }
        if (output.Count != ids.Count)
            throw new ClosureError("概念图存在环，无法给出装载序（修复指引：按资产 §4 conflict_rules 归并并列节点）");
        return output;
    }

    /// <summary>给定序列对图的违反边：[(前置, 后继)]。</summary>
    public static List<(string Prereq, string User)> Violations(
        Dictionary<string, object?> graph, IReadOnlyList<string> seq)
    {
        var pos = new Dictionary<string, int>(StringComparer.Ordinal);
        for (var i = 0; i < seq.Count; i++) pos[seq[i]] = i;
        var prereqs = PrereqsOf(graph);
        var bad = new List<(string, string)>();
        foreach (var user in prereqs.Keys.OrderBy(x => x, StringComparer.Ordinal))
        {
            if (!pos.ContainsKey(user)) continue;
            foreach (var p in prereqs[user])
                if (pos.TryGetValue(p, out var pp) && pp > pos[user]) bad.Add((p, user));
        }
        return bad;
    }

    /// <summary>图健康度：无环 / 无悬空 / 边有溯源 / 层位合法 / id 唯一 / 别名唯一 / 分支完备 / 证据面。</summary>
    public static List<string> Problems(Dictionary<string, object?> graph)
    {
        var issues = new List<string>();
        var prereqs = PrereqsOf(graph);
        var ext = PyList(graph.GetValueOrDefault("external_prereqs"))
            .OfType<Dictionary<string, object?>>().Select(x => PyStr(x.GetValueOrDefault("id")))
            .ToHashSet(StringComparer.Ordinal);
        var declared = prereqs.Keys.ToHashSet(StringComparer.Ordinal);
        declared.UnionWith(ext);
        var legend = (graph.GetValueOrDefault("provenance_legend") as Dictionary<string, object?>)
            ?.Keys.ToHashSet(StringComparer.Ordinal) ?? new HashSet<string>(StringComparer.Ordinal);
        var strength = ProvenanceStrength(graph);
        if (strength.Length == 0)
            issues.Add("图缺 provenance_strength 声明（修复指引：在机读块声明取值 "
                       + string.Join(" / ", ProvenanceStrengths) + "——证据强度须显式，不得默认按强证据理解）");
        else if (!ProvenanceStrengths.Contains(strength))
            issues.Add($"provenance_strength 越词表：{strength}（取值 {string.Join(" / ", ProvenanceStrengths)}）");
        else
        {
            var (covered, total) = ExternalCoverage(graph);
            var ratio = total > 0 ? (double)covered / total : 0.0;
            if (strength == "external" && ratio < 1.0)
                issues.Add($"provenance_strength=external 但外部覆盖仅 {covered}/{total}"
                           + "（修复指引：补齐每节点的外部来源锚，或按实况降为 mixed / domain-logic）");
            else if (strength == "mixed" && !(ratio > 0.0 && ratio < 1.0))
                issues.Add($"provenance_strength=mixed 但外部覆盖 = {covered}/{total}"
                           + "（修复指引：全覆盖用 external；无外部锚用 domain-logic / inferred）");
            else if ((strength == "domain-logic" || strength == "inferred") && ratio > 0.0)
                issues.Add($"provenance_strength={strength} 但已有 {covered}/{total} 节点挂外部来源键"
                           + "（修复指引：按实况升为 mixed / external）");
        }
        var seenNodes = new HashSet<string>(StringComparer.Ordinal);
        foreach (var node in PyList(graph.GetValueOrDefault("nodes")).OfType<Dictionary<string, object?>>())
        {
            var nid = PyStrOrEmpty(node.GetValueOrDefault("id"));
            if (nid.Length == 0)
            {
                issues.Add("节点缺 id（修复指引：每个节点须有 Cxx 编号）");
                continue;
            }
            if (!seenNodes.Add(nid)) issues.Add($"节点 id 重复：{nid}（编号须唯一）");
            if (PyStrOrEmpty(node.GetValueOrDefault("name")).Trim().Length == 0)
                issues.Add($"节点 {nid} 缺 name（修复指引：每个概念须有可读名）");
            var prov = PyList(node.GetValueOrDefault("provenance"));
            if (prov.Count == 0)
                issues.Add($"节点 {nid} 缺 provenance（边无溯源即不可复核）");
            else
                foreach (var key in prov)
                    if (!legend.Contains(PyStr(key)))
                        issues.Add($"节点 {nid} 的 provenance 键 {PyScalar.PyRepr(key)} 不在 provenance_legend 中"
                                   + "（修复指引：补图例键，防图例漂移静默）");
            var layer = PyStrOrEmpty(node.GetValueOrDefault("layer"));
            if (layer.Length > 0 && !Layers.Contains(layer))
                issues.Add($"节点 {nid} 层位越界：{layer}（取值 {string.Join("/", Layers)}）");
        }
        foreach (var (nid, ps) in prereqs.OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            foreach (var p in ps)
            {
                if (!declared.Contains(p))
                    issues.Add($"悬空前置：{nid} ← {p}（前置不在节点表 / 外部前置族中）");
                if (p == nid) issues.Add($"自环：{nid} ← {p}");
            }
        }
        var bids = NodeBranch(graph);
        foreach (var nid in prereqs.Keys.Except(bids.Keys).OrderBy(x => x, StringComparer.Ordinal))
            issues.Add($"概念 {nid} 未归入任何分支（修复指引：在图 branches 段登记）");
        foreach (var nid in bids.Keys.Except(prereqs.Keys).OrderBy(x => x, StringComparer.Ordinal))
            issues.Add($"分支声明了不存在的概念：{nid}（修复指引：核对 branches.nodes）");
        var flat = BranchMap(graph).Values.SelectMany(v => v).ToList();
        if (flat.Count != flat.Distinct(StringComparer.Ordinal).Count())
            issues.Add("概念被多个分支重复声明（修复指引：一概念只入一个分支）");
        try
        {
            AliasMap(graph);
        }
        catch (ClosureError exc)
        {
            issues.Add(exc.Message);
        }
        try
        {
            Toposort(graph);
        }
        catch (ClosureError exc)
        {
            issues.Add(exc.Message);
        }
        return issues;
    }

    /// <summary>全仓工程度扫描 → (issues, stats)（供 check32 子扫描；无图资产即中性通过）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        long nodes = 0, edges = 0;
        var assets = GraphAssets(root);
        foreach (var rel in assets)
        {
            Dictionary<string, object?> graph;
            try
            {
                graph = LoadGraph(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)));
            }
            catch (ClosureError exc)
            {
                issues.Add($"{rel}: {exc.Message}");
                continue;
            }
            var prereqs = PrereqsOf(graph);
            nodes += prereqs.Count;
            edges += prereqs.Values.Sum(v => v.Count);
            foreach (var msg in Problems(graph)) issues.Add($"{rel}: {msg}");
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["graphs"] = (long)assets.Count, ["nodes"] = nodes, ["edges"] = edges,
        });
    }

    // ---------------------------------------------------------------- 小工具

    private static string ReadText(string path) =>
        KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(path)));

    public static List<object?> PyList(object? v) => v as List<object?> ?? new List<object?>();

    private static string PyStr(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        double d => PythonJson.PyFloatRepr(d),
        _ => PyScalar.PyRepr(v),
    };

    private static string PyStrOrEmpty(object? v) =>
        v is null || (v is string s && s.Length == 0) || (v is bool b && !b) ? "" : PyStr(v);
}
