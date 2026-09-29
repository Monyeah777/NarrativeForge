namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/payload_harvest.py::verify_backlog</c>（一致性契约 <c>type-backlog</c>）：
/// 类型积压台账——把**不可从证据推断**的 untyped 字段显式化（可数、不隐身）。
///
/// 纪律：每个 untyped 字段必须带 note（说明为何没有类型证据），门禁据此判「无声增长」；
/// 另判「在盘台账 == 实时重算」（count 一致）。
/// </summary>
public static class TypeBacklog
{
    public const string RegistryRel = "protocol/event_registry.json";
    public const string BacklogRel = "protocol/type_backlog.json";
    public const string BacklogSchema = "nf-type-backlog/1";
    public const string ContractDescription = "类型积压显式化";

    public sealed record Row(string Event, string Field, string Note);

    /// <summary>实时重算台账：全部 untyped 字段（事件/字段均排序）+ 缺 note 的清单。</summary>
    public static (List<Row> Rows, List<string> MissingNote) Backlog(string root)
    {
        var rows = new List<Row>();
        var missing = new List<string>();
        using var doc = JsonIo.ReadFile(Path.Combine(root, RegistryRel.Replace('/', Path.DirectorySeparatorChar)));
        var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var events = graph.GetValueOrDefault("events") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        foreach (var ev in events.Keys.OrderBy(k => k, StringComparer.Ordinal))
        {
            var body = events[ev] as Dictionary<string, object?>;
            var fields = body?.GetValueOrDefault("fields") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            foreach (var field in fields.Keys.OrderBy(k => k, StringComparer.Ordinal))
            {
                var spec = fields[field] as Dictionary<string, object?>;
                if ((spec?.GetValueOrDefault("type")?.ToString() ?? "") != "untyped") continue;
                var note = (spec?.GetValueOrDefault("note")?.ToString() ?? "").Trim();
                rows.Add(new Row(ev, field, note));
                if (note.Length == 0) missing.Add($"{ev}.{field}");
            }
        }
        return (rows, missing);
    }

    /// <summary>台账一致性：实时重算无「无 note 的 untyped」，且与在盘台账 count 一致。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) VerifyBacklog(string root)
    {
        var (rows, missing) = Backlog(root);
        var issues = new List<string>();
        if (missing.Count > 0)
            issues.Add($"存在无 note 的 untyped 字段（无声增长）：{string.Join("、", missing.Take(3))}");
        var path = Path.Combine(root, BacklogRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path))
        {
            issues.Add($"缺类型积压台账 {BacklogRel}（修复指引：nf module types --backlog --write）");
        }
        else
        {
            try
            {
                using var doc = JsonIo.ReadFile(path);
                var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>;
                var recorded = graph?.GetValueOrDefault("count");
                if (recorded?.ToString() != rows.Count.ToString())
                {
                    issues.Add($"台账过期：记录 {recorded?.ToString() ?? "None"} ≠ 实测 {rows.Count}（修复指引：重写台账）");
                }
            }
            catch (Exception)
            {
                issues.Add("台账 JSON 不可解析");
            }
        }
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal) { ["untyped"] = rows.Count };
        return (issues, stats);
    }

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, stats) = VerifyBacklog(root);
        return issues.Count == 0
            ? (true, $"不可推断 untyped {stats["untyped"]} 项（台账同步）")
            : (false, string.Join("; ", issues.Take(2)));
    }
}
