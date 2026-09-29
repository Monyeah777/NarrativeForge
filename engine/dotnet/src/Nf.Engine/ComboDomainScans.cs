using System.Globalization;
using System.Text;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// check32 最后两件子扫描器（读面）：`pack_combo.scan`（在盘组合证书复算 + 广度证明）与
/// `domain_pack.scan`（= `manifest_verify`，域包名录 ↔ 盘上实况一致 + 可机验占比门槛）。
/// 两者在真源里**没有独立命令面**（只被 check32 消费），故按内层组件落地，等价性由金标向量钉住。
/// </summary>
public static class ComboScan
{
    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>在盘组合证书复算（T4）+ 广度证明。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var (doc, _) = OutputForms.ReadJson(Path.Combine(root, "protocol", "combo_certificates.json"));
        var certs = ConceptGraph.PyList((doc as Dictionary<string, object?>)?.GetValueOrDefault("certificates"));
        using var schemaDoc = JsonIo.Parse(OutputTables.ComboCertSchemaJson);
        var schema = (Dictionary<string, object?>)PythonJson.ToGraph(schemaDoc.RootElement)!;
        foreach (var cert in certs.OfType<Dictionary<string, object?>>())
        {
            var unsupported = new List<string>();
            var schemaErrs = JsonSchemaSubset.Check(cert, schema, unsupported: unsupported);
            var name = PyStrOrEmpty(cert.GetValueOrDefault("label"));
            if (name.Length == 0)
                name = string.Join("+", ConceptGraph.PyList(cert.GetValueOrDefault("packs")).Select(PyStr));
            if (name.Length == 0) name = "<空>";
            issues.AddRange(schemaErrs.Take(4).Select(e => $"组合 {name}: 证书不合 schema: {e}"));
            if (unsupported.Count > 0)
                issues.Add($"组合 {name}: 证书校验器遇到不支持关键字 "
                           + ReprList(unsupported.Distinct(StringComparer.Ordinal)
                               .OrderBy(x => x, StringComparer.Ordinal).Take(2)));
            issues.AddRange(VerifyCertificate(root, cert).Select(s => $"组合 {name}: {s}"));
        }
        var breadth = Breadth.RunSelfContained(root);
        if (!PyTruthy(breadth.GetValueOrDefault("all_legal")))
            issues.Add($"广度证明不成立：两两 {PyStr(breadth["pairs_legal"])}/{PyStr(breadth["pairs"])} · "
                       + $"三元 {PyStr(breadth["triples_legal"])}/{PyStr(breadth["triples"])} · "
                       + $"四元 {PyStr(breadth["quads_legal"])}/{PyStr(breadth["quads"])} · "
                       + $"五元 {PyStr(breadth["quints_legal"])}/{PyStr(breadth["quints"])} · "
                       + $"六元 {PyStr(breadth["sexts_legal"])}/{PyStr(breadth["sexts"])}"
                       + $"（样本 {ReprList(ConceptGraph.PyList(breadth.GetValueOrDefault("failures")).Take(2).Select(PyStr))}）");
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["declared_certificates"] = (long)certs.Count, ["breadth"] = breadth,
        });
    }

    /// <summary>T4 复算：按证书输入重算组合，与在盘证书逐字段比对（九字段）。</summary>
    public static List<string> VerifyCertificate(string root, Dictionary<string, object?> cert)
    {
        var issues = new List<string>();
        var packs = ConceptGraph.PyList(cert.GetValueOrDefault("packs")).Select(PyStr).ToList();
        var extra = ConceptGraph.PyList(cert.GetValueOrDefault("extra_modules")).Select(PyStr).ToList();
        var fresh = Combinator.Build(root, packs, extra).Certificate;
        foreach (var key in new[]
                 {
                     "modules", "module_count", "layer_stacks", "dependency_closure",
                     "event_closure", "assets_borrowed", "modules_borrowed", "legal", "digest",
                 })
        {
            var freshValue = fresh.GetValueOrDefault(key);
            var diskValue = cert.GetValueOrDefault(key);
            if (PyScalar.PyEquals(freshValue, diskValue)) continue;
            issues.Add($"字段不一致：{key}（复算 {PyScalar.PyRepr(freshValue)} ≠ 在盘 {PyScalar.PyRepr(diskValue)}）");
        }
        return issues;
    }

    private static string PyStrOrEmpty(object? v) => PyTruthy(v) ? PyStr(v) : "";

    private static bool PyTruthy(object? v) => v switch
    {
        null => false,
        bool b => b,
        string s => s.Length > 0,
        long l => l != 0,
        int i => i != 0,
        double d => d != 0,
        List<object?> list => list.Count > 0,
        Dictionary<string, object?> map => map.Count > 0,
        _ => true,
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

    private static string ReprList(IEnumerable<string> items) =>
        "[" + string.Join(", ", items.Select(PyScalar.PyRepr)) + "]";
}

/// <summary>复刻 <c>core/domain_pack.py::manifest_verify</c>（域包名录机检）。</summary>
public static class DomainPackScan
{
    public const string ManifestRel = "protocol/domain_packs.json";
    public const string StandardsRel = "protocol/standards_catalog.json";
    public const string BindingRel = "protocol/standards_binding.json";
    public const string RegistryRel = "desktop/src/core/registry.json";
    public const string SpecDir = ".rivet/private_archive/ai_packs/specs";
    public const double AuthenticityThreshold = 0.95;
    public const double ReachableRatioThreshold = 0.9;

    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    private static Dictionary<string, object?> ReadJsonOrEmpty(string path)
    {
        var (doc, _) = OutputForms.ReadJson(path);
        return doc as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
    }

    /// <summary>可扩展标准目录（<c>standards_catalog</c>：id → 标准条目）。</summary>
    public static Dictionary<string, object?> Catalog(string root)
    {
        var doc = ReadJsonOrEmpty(Path.Combine(root, StandardsRel.Replace('/', Path.DirectorySeparatorChar)));
        var output = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var s in ConceptGraph.PyList(doc.GetValueOrDefault("standards"))
                     .OfType<Dictionary<string, object?>>())
        {
            var id = PyStr(s.GetValueOrDefault("id"));
            output[id] = s;
        }
        return output;
    }

    public static (List<string> Issues, Dictionary<string, object?> Stats) ManifestVerify(string root)
    {
        var issues = new List<string>();
        var manifestPath = Path.Combine(root, ManifestRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(manifestPath))
            return (new List<string>(), new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["packs"] = 0L, ["note"] = "无域包名录（域包工程未启用）",
            });
        var doc = ReadJsonOrEmpty(manifestPath);
        var thr = PyDouble(doc.GetValueOrDefault("machine_verifiable_threshold")) is var t && t != 0 ? t : 0.95;
        var catalog = Catalog(root);
        var densMin = PyDouble(doc.GetValueOrDefault("concept_density_threshold")) is var dm && dm != 0 ? dm : 1.0;
        var authMin = PyDouble(doc.GetValueOrDefault("data_authenticity_threshold")) is var am && am != 0
            ? am : AuthenticityThreshold;
        var reachMin = PyDouble(doc.GetValueOrDefault("reachable_ratio_threshold")) is var rm && rm != 0
            ? rm : ReachableRatioThreshold;
        long packs = 0, facesTotal = 0, functionalTotal = 0;
        var registry = ReadJsonOrEmpty(Path.Combine(root, RegistryRel.Replace('/', Path.DirectorySeparatorChar)));
        var byId = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var p in ConceptGraph.PyList(registry.GetValueOrDefault("protocols"))
                     .OfType<Dictionary<string, object?>>())
            byId[PyStr(p.GetValueOrDefault("id"))] = p;
        var binding = ReadJsonOrEmpty(Path.Combine(root, BindingRel.Replace('/', Path.DirectorySeparatorChar)));
        var bindBy = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var b in ConceptGraph.PyList(binding.GetValueOrDefault("packs"))
                     .OfType<Dictionary<string, object?>>())
            bindBy[PyStr(b.GetValueOrDefault("code"))] = b;

        foreach (var p in ConceptGraph.PyList(doc.GetValueOrDefault("packs"))
                     .OfType<Dictionary<string, object?>>())
        {
            var pkg = PyStrOrEmpty(p.GetValueOrDefault("package"));
            var bp = bindBy.GetValueOrDefault(PyStr(p.GetValueOrDefault("code")))
                     ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            packs++;
            facesTotal += PyInt(p.GetValueOrDefault("output_faces"));
            functionalTotal += PyInt(p.GetValueOrDefault("functional_faces"));
            if (!byId.TryGetValue(pkg, out var regp))
            {
                issues.Add($"{pkg}：registry protocols[] 无该包（名录 ↔ 登记不一致）");
            }
            else
            {
                if (PyStr(regp.GetValueOrDefault("pipeline")) != PyStr(p.GetValueOrDefault("pipeline")))
                    // 真源用 `%s`（**原值**），不是 `%r`——首版照直写成 PyRepr，文案多了一对单引号。
                    issues.Add($"{pkg}：管线不一致（名录 {PyStr(p.GetValueOrDefault("pipeline"))} / "
                               + $"registry {PyStr(regp.GetValueOrDefault("pipeline"))}）");
                if (!ConceptGraph.PyList(regp.GetValueOrDefault("module_ids")).Select(PyStr)
                        .SequenceEqual(ConceptGraph.PyList(p.GetValueOrDefault("module_ids")).Select(PyStr),
                            StringComparer.Ordinal))
                    issues.Add($"{pkg}：模块 id 不一致（名录 ↔ registry）");
            }
            var proto = Path.Combine(root, "community", pkg, "protocol.yaml");
            if (!File.Exists(proto))
            {
                issues.Add($"{pkg}：包目录或 protocol.yaml 缺失");
                continue;
            }
            var text = KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(proto)));
            foreach (var token in new[] { PyStr(p.GetValueOrDefault("pipeline")), PyStr(p.GetValueOrDefault("category")) })
                if (!text.Contains(token, StringComparison.Ordinal))
                    issues.Add($"{pkg}：protocol.yaml 缺名录声明 {token}");
            var idxPath = Path.Combine(root, "community", pkg, "outputs", "INDEX.json");
            if (!File.Exists(idxPath))
            {
                issues.Add($"{pkg}：缺 outputs/INDEX.json");
                continue;
            }
            var index = ReadJsonOrEmpty(idxPath);
            var faces = ConceptGraph.PyList(index.GetValueOrDefault("outputs"));
            var mv = faces.OfType<Dictionary<string, object?>>()
                .Count(e => PyStrOrEmpty(e.GetValueOrDefault("tier")) is "T2" or "T3" or "T4");
            var ratio = PyScalar.PyRound((double)mv / Math.Max(1, faces.Count), 4);
            if (ratio < thr)
                issues.Add($"{pkg}：可机验产出占比 {Fmt(ratio)} < 门槛 {Fmt2(thr)}（产出面必须 ≥95% 可机验）");
            if (!faces.OfType<Dictionary<string, object?>>().Any(e => PyStrOrEmpty(e.GetValueOrDefault("tier")) == "T4"))
                issues.Add($"{pkg}：无 T4 可复算面（域包必须有一个可重算产出）");
            if (PyInt(p.GetValueOrDefault("output_faces")) != faces.Count)
                issues.Add($"{pkg}：名录产出面数 {PyStr(p.GetValueOrDefault("output_faces"))} ≠ INDEX 实况 {faces.Count}");

            var specPath = Path.Combine(root, SpecDir.Replace('/', Path.DirectorySeparatorChar),
                PyStr(p.GetValueOrDefault("code")) + ".json");
            if (!File.Exists(specPath)) continue;
            var payload = ReadJsonOrEmpty(Path.Combine(root, "community", pkg, "outputs", "DOMAIN_SPEC.json"));
            var subs = ConceptGraph.PyList(payload.GetValueOrDefault("subdivisions"));
            var badRef = subs.OfType<Dictionary<string, object?>>()
                .Select(s => (Id: PyStr(s.GetValueOrDefault("id")), Ref: PyStrOrEmpty(s.GetValueOrDefault("standard_ref"))))
                .Where(x => !catalog.ContainsKey(x.Ref)).Select(x => x.Id).ToList();
            if (badRef.Count > 0)
                issues.Add($"{pkg}：细分未绑可扩展标准或引用不在册：{ReprList(badRef.Take(4))}");
            var bindingCoverage = PyDouble(p.GetValueOrDefault("standards_binding_coverage"));
            if (bindingCoverage < 1.0)
                issues.Add($"{pkg}：标准绑定覆盖率 {Fmt2(bindingCoverage)} < 1.0（每条细分须绑一个目录内标准）");
            var density = PyDouble(p.GetValueOrDefault("concept_density"));
            if (density < densMin)
                issues.Add($"{pkg}：概念密度 {Fmt3(density)} < 门槛 {Fmt3(densMin)}（边/节点；含标准节点与绑定边）");
            if (PyInt(p.GetValueOrDefault("standards_bound")) < 3)
                issues.Add($"{pkg}：绑定标准数 {PyStr(p.GetValueOrDefault("standards_bound"))} < 3"
                           + "（单包至少要贴 3 条不同标准）");
            var supportCoverage = PyDouble(p.GetValueOrDefault("support_binding_coverage"));
            if (supportCoverage < 1.0)
                issues.Add($"{pkg}：辅锚覆盖率 {Fmt2(supportCoverage)} < 1.0（每条细分须另绑一条产出承载标准）");
            if (PyInt(p.GetValueOrDefault("standards_dep_edges")) < 1)
                issues.Add($"{pkg}：概念图无标准依赖边（绑定标准的 depends_on 未入图）");
            var auth = PyDouble(p.GetValueOrDefault("data_authenticity"));
            if (auth < authMin)
                issues.Add($"{pkg}：数据真实性分 {Fmt(auth)} < 门槛 {Fmt2(authMin)}（在册 × 实测可达 × 证据齐备）");
            var rr = PyDouble(p.GetValueOrDefault("standards_reachable_ratio"));
            if (rr < reachMin)
                issues.Add($"{pkg}：绑定标准本机实测可达率 {Fmt(rr)} < 门槛 {Fmt2(reachMin)}");
            var badBinding = ConceptGraph.PyList(bp.GetValueOrDefault("bindings"))
                .OfType<Dictionary<string, object?>>()
                .Where(r => !catalog.ContainsKey(PyStrOrEmpty(r.GetValueOrDefault("standard")))
                            || !catalog.ContainsKey(PyStrOrEmpty(r.GetValueOrDefault("support_standard")))
                            || PyStrOrEmpty(r.GetValueOrDefault("standard_probe_date")).Length == 0
                            || PyStrOrEmpty(r.GetValueOrDefault("support_standard_probe_date")).Length == 0)
                .Select(r => PyStrOrEmpty(r.GetValueOrDefault("subdivision"))).ToList();
            if (badBinding.Count > 0)
                issues.Add($"{pkg}：绑定表缺在册证明或实测记录：{ReprList(badBinding.Take(4))}");
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["packs"] = packs, ["faces"] = facesTotal, ["functional"] = functionalTotal,
        });
    }

    /// <summary>Python <c>%.4f</c>。</summary>
    private static string Fmt(double v) => v.ToString("F4", CultureInfo.InvariantCulture);
    /// <summary>Python <c>%.2f</c>。</summary>
    private static string Fmt2(double v) => v.ToString("F2", CultureInfo.InvariantCulture);
    /// <summary>Python <c>%.3f</c>。</summary>
    private static string Fmt3(double v) => v.ToString("F3", CultureInfo.InvariantCulture);

    private static long PyInt(object? v) => v switch
    {
        long l => l,
        int i => i,
        double d => (long)Math.Truncate(d),
        string s when double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out var parsed)
            => (long)Math.Truncate(parsed),
        _ => 0L,
    };

    private static double PyDouble(object? v) => v switch
    {
        long l => l,
        int i => i,
        double d => d,
        bool b => b ? 1 : 0,
        string s when double.TryParse(s, NumberStyles.Float, CultureInfo.InvariantCulture, out var parsed) => parsed,
        _ => 0.0,
    };

    private static string PyStrOrEmpty(object? v) => v is null || (v is string s0 && s0.Length == 0) ? "" : PyStr(v);

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

    private static string ReprList(IEnumerable<string> items) =>
        "[" + string.Join(", ", items.Select(PyScalar.PyRepr)) + "]";
}
