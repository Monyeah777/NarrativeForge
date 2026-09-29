using System.Globalization;
using System.Text;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/closure_scan.py</c>（machine 事件闭包**只报告不设闸**：issues 恒空）。
/// 被 <see cref="ProtocolGolden"/> 作为 <c>event_closure</c> 字段消费。
/// </summary>
public static class ClosureScan
{
    public static (List<string> Issues, Dictionary<string, object?> Stats) Scan(string root)
    {
        var publishers = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        var subscribers = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        var modules = 0;
        foreach (var (_, contract, id) in ModuleDocs.Contracts(root))
        {
            modules++;
            var events = contract.GetValueOrDefault("events") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            foreach (var e in ConceptGraph.PyList(events.GetValueOrDefault("publish")).Select(PyStr))
            {
                if (!publishers.TryGetValue(e, out var list)) publishers[e] = list = new List<string>();
                list.Add(id);
            }
            foreach (var e in ConceptGraph.PyList(events.GetValueOrDefault("subscribe")).Select(PyStr))
            {
                if (!subscribers.TryGetValue(e, out var list)) subscribers[e] = list = new List<string>();
                list.Add(id);
            }
        }
        var pubEvents = publishers.Keys.OrderBy(x => x, StringComparer.Ordinal).ToList();
        var subEvents = subscribers.Keys.OrderBy(x => x, StringComparer.Ordinal).ToList();
        var linked = pubEvents.Intersect(subEvents, StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal).ToList();
        var subOnly = subEvents.Except(pubEvents, StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal).ToList();
        var pubOnly = pubEvents.Except(subEvents, StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal).ToList();
        Dictionary<string, object?> SideMap(List<string> events, Dictionary<string, List<string>> table) =>
            events.ToDictionary(e => e, e => (object?)(table.GetValueOrDefault(e) ?? new List<string>())
                .Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal)
                .Cast<object?>().ToList(), StringComparer.Ordinal);
        return (new List<string>(), new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["modules"] = (long)modules,
            ["linked_events"] = linked.Cast<object?>().ToList(),
            ["sub_only_events"] = subOnly.Cast<object?>().ToList(),
            ["pub_only_events"] = pubOnly.Cast<object?>().ToList(),
            ["sub_only_by_module"] = SideMap(subOnly, subscribers),
            ["pub_only_by_module"] = SideMap(pubOnly, publishers),
        });
    }

    internal static string PyStr(object? v) => v switch
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

/// <summary>
/// 复刻 <c>core/protocol_golden.py</c>（43 A4）：**协议生成物同仓 golden**——schema 定义 → 可复现产物
/// （<c>protocol/generated/idl_report.json</c> 校验摘要 + <c>idl_summary.md</c> 人读摘要，同一 canonical 数据渲染，
/// **逐字节可复现**），并以 verify check31 的双源纪律断言「仓库内生成物 == 实时重算」。
///
/// 另含透明日志（哈希链）校验——它也是生成物：链自洽 + 与回执一致 + 在盘 == 实时重算。
/// 写面 <c>write_golden</c>（刷新入仓）不属只读门。
/// </summary>
public static class ProtocolGolden
{
    public const string GeneratedDir = "protocol/generated";
    public const string ReportName = "idl_report.json";
    public const string SummaryName = "idl_summary.md";

    private static string MdRow(IEnumerable<object?> cells) =>
        "| " + string.Join(" | ", cells.Select(c => c?.ToString() ?? "None")) + " |";

    /// <summary>收集生成物 canonical 数据（全部来自 schema/协议件实时扫描，确定性排序）。</summary>
    public static Dictionary<string, object?> Collect(string root)
    {
        var scan = SchemaLint.Scan(root);
        var (_, schemas) = SchemaLint.CheckSchemaFiles(root);
        var schemaIds = schemas.Select(s => ProtocolGolden.PyStrOf(s.GetValueOrDefault("$id")))
            .Where(s => s.Length > 0).OrderBy(s => s, StringComparer.Ordinal).Cast<object?>().ToList();

        var evidence = EvidenceIds(root).OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList();

        var contracts = new List<Dictionary<string, object?>>();
        foreach (var rel in ModuleDocs.Files(root))
        {
            string text;
            try
            {
                text = KnowledgeSig.Norm(new UTF8Encoding(false, true).GetString(
                    File.ReadAllBytes(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)))));
            }
            catch (Exception)
            {
                continue;   // 尽力而为：不可读项由对应门禁另行报出
            }
            var parsed = MiniYaml.ParseFence(text, "machine_contract");
            if (parsed is null) continue;
            var mc = parsed.TryGetValue("machine_contract", out var block) ? block : parsed;
            if (mc is not Dictionary<string, object?> mcMap) continue;
            contracts.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = mcMap.GetValueOrDefault("id"),
                ["name"] = mcMap.GetValueOrDefault("name"),
                ["layer"] = mcMap.GetValueOrDefault("layer"),
                ["conformance"] = mcMap.GetValueOrDefault("conformance"),
                ["source"] = rel,
            });
        }
        contracts = contracts
            .OrderBy(c => PyStrOf(c["id"]), StringComparer.Ordinal)
            .ThenBy(c => PyStrOf(c["source"]), StringComparer.Ordinal).ToList();

        var (_, pipelineDocs, protocolFiles) = SchemaLint.Discover(root);
        var pipelines = pipelineDocs.Select(Path.GetFileName).Where(n => n is not null)
            .Select(n => n!).OrderBy(n => n, StringComparer.Ordinal).Cast<object?>().ToList();
        var packages = protocolFiles.Select(p => RelPosix(root, p))
            .OrderBy(p => p, StringComparer.Ordinal).Cast<object?>().ToList();

        var (registry, _) = OutputForms.ReadJson(Path.Combine(root, "desktop", "src", "core", "registry.json"));
        var registryModules = new List<Dictionary<string, object?>>();
        foreach (var m in ConceptGraph.PyList((registry as Dictionary<string, object?>)?.GetValueOrDefault("modules"))
                     .OfType<Dictionary<string, object?>>())
        {
            registryModules.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = m.GetValueOrDefault("id"),
                ["category"] = m.GetValueOrDefault("category"),
                ["source"] = m.GetValueOrDefault("source"),
                ["layers"] = ConceptGraph.PyList(m.GetValueOrDefault("mounts"))
                    .OfType<Dictionary<string, object?>>()
                    .Select(mo => mo.GetValueOrDefault("layer")).ToList(),
            });
        }
        registryModules = registryModules.OrderBy(m => PyStrOf(m["id"]), StringComparer.Ordinal).ToList();

        var (prov, _) = OutputForms.ReadJson(Path.Combine(root, "05_资产库", "provenance.json"));
        var assetKeys = ConceptGraph.PyList((prov as Dictionary<string, object?>)?.GetValueOrDefault("assets"))
            .OfType<Dictionary<string, object?>>()
            .Select(a => a.GetValueOrDefault("key"))
            .OrderBy(k => PyStrOf(k), StringComparer.Ordinal).Cast<object?>().ToList();

        var (_, closureStats) = ClosureScan.Scan(root);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["generated_by"] = "43 A4 protocol_golden（schema 定义 → 校验摘要，确定性渲染）",
            ["schema_ids"] = schemaIds,
            ["coverage"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["module_docs"] = scan.Stats.GetValueOrDefault("module_docs"),
                ["contract_covered"] = scan.Stats.GetValueOrDefault("contract_covered"),
                ["pipelines"] = scan.Stats.GetValueOrDefault("pipelines"),
                ["protocols"] = scan.Stats.GetValueOrDefault("protocols"),
                ["asset_entries"] = scan.Stats.GetValueOrDefault("asset_entries"),
                ["schema_issues"] = (long)scan.Issues.Count,
            },
            ["evidence_ids"] = evidence,
            ["registry_modules"] = registryModules.Cast<object?>().ToList(),
            ["contracts"] = contracts.Cast<object?>().ToList(),
            ["pipeline_files"] = pipelines,
            ["protocol_files"] = packages,
            ["asset_keys"] = assetKeys,
            ["event_closure"] = closureStats,
        };
    }

    public static byte[] RenderJson(Dictionary<string, object?> data) =>
        Encoding.UTF8.GetBytes(PythonJson.Indented(data) + "\n");

    public static byte[] RenderMarkdown(Dictionary<string, object?> data)
    {
        var coverage = (Dictionary<string, object?>)data["coverage"]!;
        var lines = new List<string>
        {
            "# protocol/generated · 协议层 IDL 校验摘要（43 A4 golden 产物）",
            "",
            "> 本文件由 `desktop/src/core/protocol_golden.py` 确定性渲染；",
            "> 校验摘要与 schema/协议件双源一致由 verify check31 断言（过期即红，重跑刷新）。",
            "",
            "## 覆盖",
            MdRow(new object?[] { "schema", "模块文档", "机读契约", "管线", "协议包", "台账条目" }),
            MdRow(new object?[] { "-", "-", "-", "-", "-", "-" }),
            MdRow(new object?[]
            {
                ConceptGraph.PyList(data["schema_ids"]).Count,
                coverage["module_docs"], coverage["contract_covered"],
                coverage["pipelines"], coverage["protocols"], coverage["asset_entries"],
            }),
            "",
            "## schema 定义",
        };
        lines.AddRange(ConceptGraph.PyList(data["schema_ids"]).Select(sid => "- " + PyStrOf(sid)));
        lines.AddRange(new[]
        {
            "", "## 装配在册证据（id 集）",
            "- " + string.Join(", ", ConceptGraph.PyList(data["evidence_ids"]).Select(PyStrOf)),
            "", "## 机读契约模块", MdRow(new object?[] { "id", "conformance", "layer", "source" }),
            MdRow(new object?[] { "-", "-", "-", "-" }),
        });
        foreach (var c in ConceptGraph.PyList(data["contracts"]).OfType<Dictionary<string, object?>>())
            lines.Add(MdRow(new[] { c["id"], c["conformance"], c["layer"], c["source"] }));
        lines.AddRange(new[]
        {
            "", "## 管线", "- " + string.Join(", ", ConceptGraph.PyList(data["pipeline_files"]).Select(PyStrOf)),
            "", "## 协议包", "- " + string.Join(", ", ConceptGraph.PyList(data["protocol_files"]).Select(PyStrOf)),
            "", "## 资产台账键", "- " + string.Join(", ", ConceptGraph.PyList(data["asset_keys"]).Select(PyStrOf)), "",
        });
        return Encoding.UTF8.GetBytes(string.Join("\n", lines) + "\n");
    }

    /// <summary>check31：仓库内生成物 == 实时重算（schema↔生成物双源一致）+ 透明日志校验。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) VerifyGolden(string root)
    {
        var issues = new List<string>();
        var data = Collect(root);
        var expected = RenderJson(data);
        var reportPath = Path.Combine(root, GeneratedDir.Replace('/', Path.DirectorySeparatorChar), ReportName);
        if (!File.Exists(reportPath))
        {
            issues.Add($"{GeneratedDir}/{ReportName} 缺失（生成物未入仓）");
        }
        else if (!File.ReadAllBytes(reportPath).SequenceEqual(expected))
        {
            issues.Add($"{GeneratedDir}/{ReportName} 过期：与当前 schema/协议件不一致——"
                       + "请用 protocol_golden.write_golden 刷新并随变更一并提交");
        }
        var expectedMd = RenderMarkdown(data);
        var summaryPath = Path.Combine(root, GeneratedDir.Replace('/', Path.DirectorySeparatorChar), SummaryName);
        if (!File.Exists(summaryPath))
        {
            issues.Add($"{GeneratedDir}/{SummaryName} 缺失（生成物未入仓）");
        }
        else if (!File.ReadAllBytes(summaryPath).SequenceEqual(expectedMd))
        {
            issues.Add($"{GeneratedDir}/{SummaryName} 过期：与实时重算不一致（修复指引：刷新生成物并随变更提交）");
        }
        try
        {
            var chain = Receipts.VerifyTransparencyChain(root);
            issues.AddRange(chain.Issues.Select(i => $"透明日志：{i}"));
        }
        catch (Exception exc)
        {
            issues.Add($"透明日志校验不可用：{exc.Message}（修复指引：检查 core/transparency_log.py）");
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["report_bytes"] = (long)expected.Length,
            ["schema_ids"] = (long)ConceptGraph.PyList(data["schema_ids"]).Count,
        });
    }

    /// <summary>官方 registry <c>modules[]</c> + community <c>protocols[].module_ids</c>（装配在册证据）。</summary>
    private static List<string> EvidenceIds(string root)
    {
        var ids = new List<string>();
        var (registry, _) = OutputForms.ReadJson(Path.Combine(root, "desktop", "src", "core", "registry.json"));
        if (registry is not Dictionary<string, object?> reg) return ids;
        foreach (var m in ConceptGraph.PyList(reg.GetValueOrDefault("modules"))
                     .OfType<Dictionary<string, object?>>())
            if (m.GetValueOrDefault("id") is string id) ids.Add(id);
        foreach (var p in ConceptGraph.PyList(reg.GetValueOrDefault("protocols"))
                     .OfType<Dictionary<string, object?>>())
            foreach (var mid in ConceptGraph.PyList(p.GetValueOrDefault("module_ids")))
                if (mid is string s) ids.Add(s);
        return ids;
    }

    private static string RelPosix(string root, string full) =>
        Path.GetRelativePath(root, full).Replace('\\', '/');

    internal static string PyStrOf(object? v) => v switch
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
