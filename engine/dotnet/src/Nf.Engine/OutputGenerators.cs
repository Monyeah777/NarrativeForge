using System.Globalization;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/output_forms.py</c> 的**生成器族**（13 个 id）：渲染与复算**共用同一函数**
/// （真源注释：不复算的渲染 = 手写，禁）。返回 <c>(value, errors)</c>；<c>value == null</c> 表示不可生成。
/// </summary>
public static class OutputGenerators
{
    /// <summary>生成器登记（唯一入口）。</summary>
    public static readonly string[] Ids =
    {
        "performance-report", "concept-closure", "vega-equity-curve", "vega-drawdown",
        "mermaid-declaration-flow", "mermaid-concept-dag", "graphml-concept-dag",
        "domain-report", "vega-metrics", "combo-cert", "vega-layer-stack",
        "mermaid-layer-load", "graphml-module-deps",
    };

    public static bool Registered(string id) => Ids.Contains(id);

    /// <summary>条目声明的生成器 id（<c>recompute</c> 优先，其次 <c>render</c>）。</summary>
    public static string GenId(Dictionary<string, object?> entry)
    {
        foreach (var key in new[] { "recompute", "render" })
            if (entry.GetValueOrDefault(key) is Dictionary<string, object?> spec
                && PyTruthy(spec.GetValueOrDefault("id")))
                return PyStr(spec.GetValueOrDefault("id"));
        return "";
    }

    /// <summary>包内声明的相对路径 → 仓库相对路径（以本包目录为根）。</summary>
    public static string PkgRel(Dictionary<string, object?> entry, string rel)
    {
        var pkg = PyStr(entry.GetValueOrDefault("_pkg"));
        if (pkg.Length == 0 || rel.StartsWith("community/", StringComparison.Ordinal)) return rel;
        return $"community/{pkg}/{rel.TrimStart('/')}";
    }

    /// <summary><c>_dump</c>：字符串原样补尾换行；对象走 <c>json.dumps(indent=2, sort_keys=True)</c>。</summary>
    public static string Dump(object? value) => value is string s
        ? (s.EndsWith("\n", StringComparison.Ordinal) ? s : s + "\n")
        : PythonJson.Indented(value) + "\n";

    public static (object? Value, List<string> Errors) Generate(string root, Dictionary<string, object?> entry)
    {
        var id = GenId(entry);
        if (!Registered(id)) return (null, new List<string> { $"未登记生成器 {PyScalar.PyRepr(id)}" });
        return id switch
        {
            "performance-report" => GenPerformanceReport(root, entry),
            "concept-closure" => GenConceptClosure(root, entry),
            "vega-equity-curve" or "vega-drawdown" => GenVega(root, entry),
            "mermaid-declaration-flow" => GenMermaidDeclarationFlow(entry),
            "mermaid-concept-dag" => GenMermaidConceptDag(root, entry),
            "graphml-concept-dag" => GenGraphmlConceptDag(root, entry),
            "domain-report" => GenDomainReport(root, entry),
            "vega-metrics" => GenVegaMetrics(root, entry),
            "combo-cert" => GenComboCert(root, entry),
            "vega-layer-stack" => GenVegaLayerStack(root, entry),
            "mermaid-layer-load" => GenMermaidLayerLoad(root, entry),
            "graphml-module-deps" => GenGraphmlModuleDeps(root, entry),
            _ => (null, new List<string> { $"未登记生成器 {PyScalar.PyRepr(id)}" }),
        };
    }

    private static Dictionary<string, object?> Spec(Dictionary<string, object?> entry)
    {
        var spec = entry.GetValueOrDefault("recompute") as Dictionary<string, object?>
                   ?? entry.GetValueOrDefault("render") as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        return spec;
    }

    // ------------------------------------------------------------------ 量化两面

    /// <summary>由净值数据用本仓引擎装配绩效报告（GIPS 对齐披露面）。</summary>
    private static (object?, List<string>) GenPerformanceReport(string root, Dictionary<string, object?> entry)
    {
        var spec = Spec(entry);
        var inputs = ConceptGraph.PyList(spec.GetValueOrDefault("inputs"));
        if (inputs.Count == 0) return (null, new List<string> { "声明可复算/可渲染但缺 inputs（无源即无功能）" });
        var src = PkgRel(entry, PyStr(inputs[0]));
        var (series, err) = QuantMetrics.LoadEquityCurve(Full(root, src));
        if (err.Length > 0) return (null, new List<string> { $"输入 {src} {err}" });
        var p = spec.GetValueOrDefault("params") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        try
        {
            var doc = QuantMetrics.PerformanceReport(series,
                PyStrOrEmpty(p.GetValueOrDefault("period_start")),
                PyStrOrEmpty(p.GetValueOrDefault("period_end")),
                currency: PyStrOr(p.GetValueOrDefault("currency"), "CNY"),
                returnBasis: PyStrOr(p.GetValueOrDefault("return_basis"), "simple"),
                frequency: PyStrOr(p.GetValueOrDefault("frequency"), "daily"),
                riskFreeRateAnnual: PyDouble(p.GetValueOrDefault("risk_free_rate_annual")),
                benchmarkId: PyStrOrEmpty(p.GetValueOrDefault("benchmark_id")),
                costBpsFee: PyDouble(p.GetValueOrDefault("cost_bps_fee")),
                costBpsSlippage: PyDouble(p.GetValueOrDefault("cost_bps_slippage")),
                fillRule: PyStrOr(p.GetValueOrDefault("fill_rule"), "next_open"),
                singleSideTurnover: !p.ContainsKey("single_side_turnover") || PyTruthy(p.GetValueOrDefault("single_side_turnover")),
                asOf: PyStrOrEmpty(p.GetValueOrDefault("as_of")));
            return (doc, new List<string>());
        }
        catch (ArgumentException exc)
        {
            return (null, new List<string> { $"复算异常 {exc.GetType().Name}: {exc.Message}" });
        }
    }

    private static (object?, List<string>) GenVega(string root, Dictionary<string, object?> entry)
    {
        var spec = Spec(entry);
        var inputs = ConceptGraph.PyList(spec.GetValueOrDefault("inputs"));
        if (inputs.Count == 0) return (null, new List<string> { "图表面缺 inputs" });
        var src = PkgRel(entry, PyStr(inputs[0]));
        var (series, err) = QuantMetrics.LoadEquityCurve(Full(root, src));
        if (err.Length > 0) return (null, new List<string> { $"输入 {src} {err}" });
        var p = spec.GetValueOrDefault("params") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var which = PyStrOrEmpty(spec.GetValueOrDefault("id"));
        var title = PyStrOr(p.GetValueOrDefault("title"), which == "vega-drawdown" ? "回撤曲线" : "净值曲线");
        return which == "vega-drawdown"
            ? (QuantMetrics.VegaDrawdown(series, title), new List<string>())
            : (QuantMetrics.VegaEquityCurve(series, title), new List<string>());
    }

    private static (object?, List<string>) GenMermaidDeclarationFlow(Dictionary<string, object?> entry)
    {
        var spec = Spec(entry);
        if (PyStrOrEmpty(spec.GetValueOrDefault("id")) == "mermaid-declaration-flow")
            return (QuantMetrics.MermaidDeclarationFlow(), new List<string>());
        return (null, new List<string> { $"未登记 Mermaid 生成器：{PyScalar.PyRepr(spec.GetValueOrDefault("id"))}" });
    }

    // ------------------------------------------------------------------ 概念图三面

    private static (Dictionary<string, object?> Graph, string Path, List<string> Errors) LoadGraphSpec(
        string root, Dictionary<string, object?> entry)
    {
        var spec = Spec(entry);
        var graphRel = spec.GetValueOrDefault("graph") is { } g && PyTruthy(g)
            ? PyStr(g) : ConceptGraph.DefaultAsset;
        var graphPath = PkgRel(entry, graphRel);
        try
        {
            return (ConceptGraph.LoadGraph(Full(root, graphPath)), graphPath, new List<string>());
        }
        catch (ConceptGraph.ClosureError)
        {
            return (new Dictionary<string, object?>(StringComparer.Ordinal), graphPath,
                new List<string> { $"概念图 {graphPath} 不可解析（无源）" });
        }
    }

    private static (object?, List<string>) GenConceptClosure(string root, Dictionary<string, object?> entry)
    {
        var spec = Spec(entry);
        var target = PyStrOrEmpty(spec.GetValueOrDefault("target"));
        if (target.Length == 0) return (null, new List<string> { "声明可复算但缺 target" });
        var (graph, graphPath, errors) = LoadGraphSpec(root, entry);
        if (errors.Count > 0 || graph.Count == 0) return (null, errors);
        var closure = ConceptGraph.Closure(graph, target).Select(x => (object?)ConceptGraph.Resolve(graph, x)).ToList();
        var aliases = ConceptGraph.AliasMap(graph).OrderBy(kv => kv.Key, StringComparer.Ordinal)
            .Select(kv => (object?)new List<object?> { kv.Key, kv.Value }).ToList();
        return (new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["kind"] = "nf-concept-closure/1",
            ["graph"] = graphPath,
            ["target"] = target,
            ["closure"] = closure,
            ["load_order"] = ConceptGraph.Toposort(graph).Cast<object?>().ToList(),
            ["alias"] = aliases,
        }, new List<string>());
    }

    private static (object?, List<string>) GenMermaidConceptDag(string root, Dictionary<string, object?> entry)
    {
        var (graph, graphPath, errors) = LoadGraphSpec(root, entry);
        if (errors.Count > 0 || graph.Count == 0) return (null, errors);
        var prereq = ConceptGraph.PrereqsOf(graph);
        var layer = ConceptGraph.NodeMeta(graph)
            .ToDictionary(kv => kv.Key,
                kv => PyStrOrEmpty(kv.Value.GetValueOrDefault("layer")) is { Length: > 0 } l ? l : "P00",
                StringComparer.Ordinal);
        var ids = ConceptGraph.InPackageIds(graph);
        var lines = new List<string>
        {
            $"%% 概念前置图（由 {graphPath} 确定性派生；唯一机读真相在资产 §4 围栏块）",
            "flowchart TD",
        };
        var seen = new List<string>();
        foreach (var node in ids)
        {
            var lay = layer.GetValueOrDefault(node, "P00");
            if (!seen.Contains(lay)) seen.Add(lay);
        }
        foreach (var lay in seen.OrderBy(x => x, StringComparer.Ordinal))
        {
            var inLayer = ids.Where(n => layer.GetValueOrDefault(n) == lay).ToList();
            if (inLayer.Count == 0) continue;
            lines.Add($"  subgraph {lay}[{lay}]");
            foreach (var n in inLayer) lines.Add($"    {n}");
            lines.Add("  end");
        }
        foreach (var node in ids)
            foreach (var pre in prereq.GetValueOrDefault(node) ?? new List<string>())
            {
                if (pre.StartsWith("C0", StringComparison.Ordinal) && pre == "C00") continue;
                lines.Add($"  {pre} --> {node}");
            }
        return (string.Join("\n", lines) + "\n", new List<string>());
    }

    private static (object?, List<string>) GenGraphmlConceptDag(string root, Dictionary<string, object?> entry)
    {
        var (graph, _, errors) = LoadGraphSpec(root, entry);
        if (errors.Count > 0 || graph.Count == 0) return (null, errors);
        var prereq = ConceptGraph.PrereqsOf(graph);
        var meta = ConceptGraph.NodeMeta(graph);
        var outLines = new List<string>
        {
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">",
            "  <key id=\"layer\" for=\"node\" attr.name=\"layer\" attr.type=\"string\"/>",
            "  <key id=\"branch\" for=\"node\" attr.name=\"branch\" attr.type=\"string\"/>",
            "  <key id=\"provenance\" for=\"edge\" attr.name=\"provenance\" attr.type=\"string\"/>",
            "  <graph id=\"concept-graph\" edgedefault=\"directed\">",
        };
        var nodes = ConceptGraph.InPackageIds(graph);
        foreach (var node in nodes.ToList())
            foreach (var pre in prereq.GetValueOrDefault(node) ?? new List<string>())
                if (!nodes.Contains(pre)) nodes.Add(pre);
        foreach (var node in nodes)
        {
            var m = meta.GetValueOrDefault(node) ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            outLines.Add($"    <node id=\"{node}\">");
            outLines.Add($"      <data key=\"layer\">{PyStrOrEmpty(m.GetValueOrDefault("layer"))}</data>");
            outLines.Add($"      <data key=\"branch\">{PyStrOrEmpty(m.GetValueOrDefault("branch"))}</data>");
            outLines.Add("    </node>");
        }
        foreach (var node in nodes)
            foreach (var pre in prereq.GetValueOrDefault(node) ?? new List<string>())
            {
                outLines.Add($"    <edge source=\"{pre}\" target=\"{node}\">");
                outLines.Add($"      <data key=\"provenance\">{EdgeProvenance(meta, node)}</data>");
                outLines.Add("    </edge>");
            }
        outLines.Add("  </graph>");
        outLines.Add("</graphml>");
        return (string.Join("\n", outLines) + "\n", new List<string>());
    }

    /// <summary>边溯源：取**目标节点** provenance（缺则 <c>unknown</c>）；列表形态按 Python <c>str(list)</c> 渲染。</summary>
    private static string EdgeProvenance(Dictionary<string, Dictionary<string, object?>> meta, string node)
    {
        var prov = meta.GetValueOrDefault(node)?.GetValueOrDefault("provenance");
        return PyTruthy(prov) ? PyStr(prov) : "unknown";
    }

    // ------------------------------------------------------------------ 域报告 / 指标图

    private static (object?, List<string>) GenDomainReport(string root, Dictionary<string, object?> entry)
    {
        var spec = Spec(entry);
        var inputs = ConceptGraph.PyList(spec.GetValueOrDefault("inputs"));
        var p = new Dictionary<string, object?>(spec.GetValueOrDefault("params") as Dictionary<string, object?>
            ?? new(StringComparer.Ordinal), StringComparer.Ordinal);
        var family = p.TryGetValue("family", out var f) ? PyStr(f) : "";
        p.Remove("family");
        if (inputs.Count == 0 || family.Length == 0)
            return (null, new List<string> { "域报告缺 inputs 或 family（无源/无族即无功能）" });
        var src = PkgRel(entry, PyStr(inputs[0]));
        var (rows, err) = DomainMetrics.LoadRows(Full(root, src));
        if (err.Length > 0) return (null, new List<string> { $"输入 {src} {err}" });
        Dictionary<string, object?> metrics;
        try
        {
            metrics = DomainMetrics.Evaluate(family, rows, p);
        }
        catch (ArgumentException exc)
        {
            return (null, new List<string> { $"复算异常 {exc.GetType().Name}: {exc.Message}" });
        }
        return (new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["kind"] = "nf-domain-report/1",
            // 真源是 `str(params.get("code") or "")` / `str(params.get("domain") or "")`——
            // 取自 **params**（family 已被 pop，code/domain 留在 kwargs 里传给族函数）。
            ["code"] = PyStrOrEmpty(p.GetValueOrDefault("code")),
            ["domain"] = PyStrOrEmpty(p.GetValueOrDefault("domain")),
            ["family"] = family,
            ["sample"] = PyStr(inputs[0]),
            ["sample_rows"] = (long)rows.Count,
            ["metrics"] = metrics,
        }, new List<string>());
    }

    private static (object?, List<string>) GenVegaMetrics(string root, Dictionary<string, object?> entry)
    {
        var spec = entry.GetValueOrDefault("render") as Dictionary<string, object?>
                   ?? entry.GetValueOrDefault("recompute") as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var inputs = ConceptGraph.PyList(spec.GetValueOrDefault("inputs"));
        if (inputs.Count == 0) return (null, new List<string> { "图表面缺 inputs" });
        var (data, err) = OutputForms.ReadJson(Full(root, PkgRel(entry, PyStr(inputs[0]))));
        if (err.Length > 0) return (null, new List<string> { $"输入 {PyStr(inputs[0])} {err}" });
        if (data is not Dictionary<string, object?> doc) return (null, new List<string>());
        var vals = new List<object?>();
        foreach (var (k, v) in (doc.GetValueOrDefault("metrics") as Dictionary<string, object?>
                                 ?? new(StringComparer.Ordinal)).OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            if (v is long or int or double && v is not bool)
                vals.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["metric"] = k,
                    ["value"] = Convert.ToDouble(v, CultureInfo.InvariantCulture),
                });
        }
        if (vals.Count == 0) return (null, new List<string> { "报告里没有可画的标量指标" });
        var paramsSpec = spec.GetValueOrDefault("params") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        return (new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["$schema"] = "https://vega.github.io/schema/vega-lite/v5.json",
            ["description"] = PyStrOr(paramsSpec.GetValueOrDefault("title"), "域指标"),
            ["data"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["values"] = vals },
            ["mark"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["type"] = "bar" },
            ["encoding"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["x"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = "value", ["type"] = "quantitative", ["title"] = "口径值",
                },
                ["y"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = "metric", ["type"] = "nominal", ["title"] = "指标",
                    ["sort"] = "-x",
                },
            },
        }, new List<string>());
    }

    // ------------------------------------------------------------------ 组合四面（读证书）

    private static (Dictionary<string, object?>? Data, List<string> Errors) ComboDoc(
        string root, Dictionary<string, object?> entry)
    {
        var spec = entry.GetValueOrDefault("render") as Dictionary<string, object?>
                   ?? entry.GetValueOrDefault("recompute") as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var inputs = ConceptGraph.PyList(spec.GetValueOrDefault("inputs"));
        var rel = inputs.Count > 0 ? PyStr(inputs[0]) : "outputs/COMBO_CERT.json";
        var (data, err) = OutputForms.ReadJson(Full(root, PkgRel(entry, rel)));
        if (err.Length > 0) return (null, new List<string> { $"输入 {rel} {err}" });
        return (data as Dictionary<string, object?>, new List<string>());
    }

    private static (object?, List<string>) GenComboCert(string root, Dictionary<string, object?> entry)
    {
        var spec = entry.GetValueOrDefault("recompute") as Dictionary<string, object?>
                   ?? entry.GetValueOrDefault("render") as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var p = spec.GetValueOrDefault("params") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var packs = ConceptGraph.PyList(p.GetValueOrDefault("packs")).Select(PyStr).ToList();
        var mods = ConceptGraph.PyList(p.GetValueOrDefault("extra_modules")).Select(PyStr).ToList();
        if (packs.Count == 0 && mods.Count == 0)
            return (null, new List<string> { "组合证书缺 packs/extra_modules（无输入即无复算）" });
        var result = Combinator.Build(root, packs, mods);
        var cert = new Dictionary<string, object?>(result.Certificate, StringComparer.Ordinal);
        if (PyTruthy(p.GetValueOrDefault("label"))) cert["label"] = p.GetValueOrDefault("label");
        if (PyTruthy(p.GetValueOrDefault("note"))) cert["note"] = p.GetValueOrDefault("note");
        return (cert, new List<string>());
    }

    /// <summary>层栈两种历史形态兼容：列表（当前）<c>[{layer, modules}]</c> 与字典 <c>{P40: [...]}</c>。</summary>
    public static List<(string Layer, List<string> Modules)> StackPairs(object? stacks)
    {
        var output = new List<(string, List<string>)>();
        if (stacks is List<object?> list)
        {
            foreach (var row in list.OfType<Dictionary<string, object?>>())
                output.Add((PyStrOrEmpty(row.GetValueOrDefault("layer")),
                    ConceptGraph.PyList(row.GetValueOrDefault("modules")).Select(PyStr).ToList()));
            return output;
        }
        if (stacks is Dictionary<string, object?> map)
        {
            foreach (var key in map.Keys.OrderBy(x => x, StringComparer.Ordinal))
                output.Add((key, ConceptGraph.PyList(map[key]).Select(PyStr).ToList()));
        }
        return output;
    }

    private static (object?, List<string>) GenVegaLayerStack(string root, Dictionary<string, object?> entry)
    {
        var (data, errors) = ComboDoc(root, entry);
        if (errors.Count > 0) return (null, errors);
        var rows = StackPairs(data!.GetValueOrDefault("layer_stacks"))
            .Select(t => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["layer"] = t.Layer, ["modules"] = (long)t.Modules.Count,
            }).ToList();
        if (rows.Count == 0) return (null, new List<string> { "证书无 layer_stacks（无可画数据）" });
        var renderSpec = entry.GetValueOrDefault("render") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var title = PyStrOr((renderSpec.GetValueOrDefault("params") as Dictionary<string, object?>)
            ?.GetValueOrDefault("title"), "层位堆叠");
        return (new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["$schema"] = "https://vega.github.io/schema/vega-lite/v5.json",
            ["description"] = title,
            ["data"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["values"] = rows },
            ["mark"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["type"] = "bar" },
            ["encoding"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["x"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = "layer", ["type"] = "nominal", ["title"] = "层位", ["sort"] = null,
                },
                ["y"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = "modules", ["type"] = "quantitative", ["title"] = "模块数",
                },
            },
        }, new List<string>());
    }

    private static (object?, List<string>) GenMermaidLayerLoad(string root, Dictionary<string, object?> entry)
    {
        var (data, errors) = ComboDoc(root, entry);
        if (errors.Count > 0) return (null, errors);
        var lines = new List<string>
        {
            "%% 组合包装载序（由 COMBO_CERT.json 确定性派生）", "flowchart LR",
        };
        foreach (var (lay, mods) in StackPairs(data!.GetValueOrDefault("layer_stacks")))
        {
            var tag = lay.Replace("-", "");
            lines.Add($"  {tag}[\"{lay}\"]");
            for (var i = 0; i < mods.Count; i++)
            {
                var node = $"{tag}_{i}";
                lines.Add($"  {node}[\"{mods[i]}\"]");
                lines.Add($"  {tag} --> {node}");
            }
        }
        return (string.Join("\n", lines) + "\n", new List<string>());
    }

    private static (object?, List<string>) GenGraphmlModuleDeps(string root, Dictionary<string, object?> entry)
    {
        var (data, errors) = ComboDoc(root, entry);
        if (errors.Count > 0) return (null, errors);
        var mods = ConceptGraph.PyList(data!.GetValueOrDefault("modules")).Select(PyStr).ToList();
        var explicitSet = new HashSet<string>(StringComparer.Ordinal);
        if (data!.GetValueOrDefault("dependency_closure") is Dictionary<string, object?> closure
            && closure.GetValueOrDefault("explicit") is List<object?> explicitList)
            foreach (var item in explicitList) explicitSet.Add(PyStr(item));
        var stacks = StackPairs(data!.GetValueOrDefault("layer_stacks"));
        var lines = new List<string>
        {
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">",
            "  <key id=\"layer\" for=\"node\" attr.name=\"layer\" attr.type=\"string\"/>",
            "  <graph id=\"combo\" edgedefault=\"directed\">",
        };
        foreach (var m in mods)
        {
            var lay = "";
            foreach (var (layer, members) in stacks)
            {
                if (!members.Contains(m)) continue;
                lay = layer;
                break;
            }
            lines.Add($"    <node id=\"{m}\"><data key=\"layer\">{lay}</data></node>");
        }
        foreach (var m in mods)
            foreach (var dep in ComboModuleInputs(root, m))
            {
                if (!explicitSet.Contains(dep) || dep == m) continue;
                lines.Add($"    <edge source=\"{m}\" target=\"{dep}\"/>");
            }
        lines.Add("  </graph>");
        lines.Add("</graphml>");
        return (string.Join("\n", lines) + "\n", new List<string>());
    }

    /// <summary>复刻 <c>pack_combo.prof_get_module</c>：community 契约按 id（缺则裸号）取，<c>inputs</c> 列表。</summary>
    private static List<string> ComboModuleInputs(string root, string moduleId)
    {
        var extraction = ModuleContracts.Community(root);
        var byId = new Dictionary<string, ModuleContracts.Contract>(StringComparer.Ordinal);
        foreach (var rec in extraction.RecordsByKey.Values)
            if (rec.Path.Length > 0) byId.TryAdd(rec.Id, rec);
        var bare = moduleId.Contains(':') ? moduleId[(moduleId.IndexOf(':') + 1)..] : moduleId;
        var hit = byId.GetValueOrDefault(moduleId) ?? byId.GetValueOrDefault(bare);
        return hit is null ? new List<string>() : hit.Inputs.ToList();
    }

    private static string Full(string root, string rel) =>
        Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));

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

    private static double PyDouble(object? v) => v switch
    {
        long l => l,
        int i => i,
        double d => d,
        string s when double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out var parsed) => parsed,
        _ => 0.0,
    };

    private static string PyStrOr(object? v, string fallback) => PyTruthy(v) ? PyStr(v) : fallback;
    private static string PyStrOrEmpty(object? v) => PyTruthy(v) ? PyStr(v) : "";

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
