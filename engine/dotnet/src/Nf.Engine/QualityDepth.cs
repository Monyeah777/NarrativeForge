namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/quality_depth_scan.py::scan</c>（**check32** 的聚合入口，也是 check33 第 3 条
/// <c>depth_clean</c> 信号的来源）：把 14 件既有子扫描器串成一个「质量纵深」面——子项 issue
/// 逐条前缀 <c>&lt;name&gt;: </c>，子项 stats 落 <c>stats[name]</c>。
///
/// 两处**照抄真源**的语义：
/// ① <c>asset_usage_strict</c>：子扫描器自己报的 issue 被**替换**成一条按 <c>stats["zero_usage"]</c>
///    合成的「资产零引用键 N 个」（真源同式）；
/// ② <c>payload_consumer</c>：**只取 stats、丢 issue**（真源 <c>_, consumer_stats = pc.scan(root)</c>）。
///
/// 子扫描器本体各自有独立金标钉（第八十～九十二片），本件钉的是**聚合接线与顺序**。
/// </summary>
public static class QualityDepth
{
    /// <summary>真源 <c>scan</c> 的子项顺序（issues 前缀序 + stats 键序）。</summary>
    public static readonly string[] SubScannerOrder =
    {
        "payload_registry", "asset_ledger", "instruction_audit", "concept_graph", "output_forms",
        "domain_packs", "combos", "asset_density", "asset_thickness", "asset_usage_strict",
        "tool_face", "world_model", "world_slots", "payload_consumer",
    };

    public sealed record Result(List<string> Issues, Dictionary<string, object?> Stats)
    {
        public List<string> Log(string label = "质量纵深")
        {
            var lines = Issues.Select(issue => "[FAIL] " + issue).ToList();
            var ok = SubScannerOrder.Count(name =>
                !Issues.Any(issue => issue.StartsWith(name + ": ", StringComparison.Ordinal)));
            lines.Add($"{label} 子扫描：{ok}/{SubScannerOrder.Length} 零缺口");
            return lines;
        }

        public string LogDigest(string label = "质量纵深") => ExitFaces.Digest32(Log(label));
    }

    public static Result Scan(string root)
    {
        var issues = new List<string>();
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var (name, scan) in Scanners())
        {
            var (subIssues, subStats) = scan(root);
            if (name == "asset_usage_strict" && Convert.ToInt64(subStats.GetValueOrDefault("zero_usage") ?? 0L) > 0)
                subIssues = new List<string> { $"资产零引用键 {subStats["zero_usage"]} 个（键消费证明未闭合）" };
            issues.AddRange(subIssues.Select(issue => $"{name}: {issue}"));
            stats[name] = subStats;
        }
        var (_, consumerStats) = AuxScanners.PayloadConsumerScan(root);   // 真源只取 stats，丢 issue
        stats["payload_consumer"] = consumerStats;
        return new Result(issues, stats);
    }

    /// <summary>与真源 <c>for name, fn in (...)</c> 元组**同序同源**的子扫描器表。</summary>
    private static IEnumerable<(string Name, Func<string, (List<string> Issues, Dictionary<string, object?> Stats)>)> Scanners()
    {
        yield return ("payload_registry", root => AuxScanners.PayloadRegistryScan(root));
        yield return ("asset_ledger", root => AssetLedgerProjection.Verify(root));
        yield return ("instruction_audit", root => AuxScanners.InstructionStepAudit(root));
        yield return ("concept_graph", root => ConceptGraph.Scan(root));
        yield return ("output_forms", root => OutputForms.Scan(root));
        yield return ("domain_packs", root => DomainPackScan.ManifestVerify(root));
        yield return ("combos", root => ComboScan.Scan(root));
        yield return ("asset_density", root => AssetDensity.Scan(root));
        yield return ("asset_thickness", root => AssetDensity.ThicknessScan(root));
        yield return ("asset_usage_strict", root => AssetDensity.UsageScan(root));
        yield return ("tool_face", root => ToolFace.Scan(root));
        yield return ("world_model", root => WorldModel.Scan(root));
        yield return ("world_slots", root => AuxScanners.WorldSlotsScan(root));
    }
}
