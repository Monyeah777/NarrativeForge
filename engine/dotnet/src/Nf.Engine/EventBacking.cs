namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/registry_cross.py</c>：全仓事件背书核对（社区域包的订阅是否真有人发布）。
///
/// 两档判定（诚实分层，不把"跨包"当"断链"）：
/// **hard（FAIL）**：订阅的事件在全仓无任何发布方，且未登记进 <c>protocol/external_events.json</c>；
/// **warn**：发布方在别的包（跨包依赖）——不是错，但要显式可见（references 应能解释）。
/// </summary>
public static class EventBacking
{
    public const string AllowlistRel = "protocol/external_events.json";
    public const string ContractDescription = "全仓事件背书";

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, warns, stats) = Scan(root);
        if (issues.Count > 0) return (false, string.Join("; ", issues.Take(2)));
        var events = stats.GetValueOrDefault("events");
        var cross = (stats.GetValueOrDefault("cross_pkg") as List<object?> ?? new List<object?>()).Count;
        return (true, $"事件 {events} · 跨包 {cross} · 挂账 {warns.Count - cross}");
    }

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var (publishers, subscribers) = Build(root);
        var allowlist = Allowlist(root);
        var issues = new List<string>();
        var warns = new List<string>();
        var uncovered = new List<string>();
        var crossPackage = new List<string>();

        foreach (var ev in subscribers.Keys.OrderBy(x => x, StringComparer.Ordinal))
        {
            var subs = subscribers[ev];
            var pubs = publishers.TryGetValue(ev, out var list) ? list : new List<(string Module, string Pkg)>();
            if (pubs.Count == 0)
            {
                if (allowlist.Contains(ev))
                {
                    warns.Add($"事件 {ev} 无仓内发布方（已挂账为外部通道：{AllowlistRel}）");
                }
                else
                {
                    uncovered.Add(ev);
                    var modules = string.Join("、", subs.Select(s => s.Module)
                        .Distinct(StringComparer.Ordinal)
                        .OrderBy(x => x, StringComparer.Ordinal)
                        .Take(3));
                    issues.Add($"事件背书缺口：{ev} 被 {modules} 订阅，但全仓无发布方" +
                               $"（修复指引：补发布模块，或登记进 {AllowlistRel} 作为外部通道）");
                }
                continue;
            }
            var subPkgs = subs.Select(s => s.Pkg).ToHashSet(StringComparer.Ordinal);
            var pubPkgs = pubs.Select(p => p.Pkg).ToHashSet(StringComparer.Ordinal);
            if (subPkgs.Count > 0 && pubPkgs.Count > 0 && !subPkgs.Overlaps(pubPkgs))
            {
                crossPackage.Add(ev);
                warns.Add($"跨包事件：{ev} 由 {string.Join("、", pubPkgs.OrderBy(x => x, StringComparer.Ordinal))} 发布、" +
                          $"被 {string.Join("、", subPkgs.OrderBy(x => x, StringComparer.Ordinal))} 订阅（references 应能解释）");
            }
        }

        var allEvents = publishers.Keys.Union(subscribers.Keys, StringComparer.Ordinal).Count();
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["events"] = allEvents,
            ["uncovered"] = uncovered.Cast<object?>().ToList(),
            ["cross_pkg"] = crossPackage.Cast<object?>().ToList(),
        };
        return (issues, warns, stats);
    }

    /// <summary>事件 → 发布方/订阅方（含所属包；官方核心标注为「官方核心」）。</summary>
    public static (Dictionary<string, List<(string Module, string Pkg)>> Publishers,
                   Dictionary<string, List<(string Module, string Pkg)>> Subscribers) Build(string root)
    {
        var publishers = new Dictionary<string, List<(string, string)>>(StringComparer.Ordinal);
        var subscribers = new Dictionary<string, List<(string, string)>>(StringComparer.Ordinal);
        foreach (var (rel, contract, id) in ModuleDocs.Contracts(root))
        {
            var parts = rel.Split('/');
            var pkg = rel.StartsWith("community/", StringComparison.Ordinal) && parts.Length > 1
                ? parts[1]
                : "官方核心";
            var events = contract.GetValueOrDefault("events") as Dictionary<string, object?>
                         ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            foreach (var name in Names(events, "publish"))
                publishers.TryAdd2(name, (id, pkg));
            foreach (var name in Names(events, "subscribe"))
                subscribers.TryAdd2(name, (id, pkg));
        }
        return (publishers, subscribers);
    }

    /// <summary>挂账的外部通道事件名（<c>protocol/external_events.json</c> 的 events 键）。</summary>
    public static HashSet<string> Allowlist(string root)
    {
        var path = Path.Combine(root, AllowlistRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return new HashSet<string>(StringComparer.Ordinal);
        try
        {
            using var doc = JsonIo.ReadFile(path);
            var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>;
            return (graph?.GetValueOrDefault("events") as Dictionary<string, object?>)?.Keys
                       .ToHashSet(StringComparer.Ordinal)
                   ?? new HashSet<string>(StringComparer.Ordinal);
        }
        catch (Exception)
        {
            return new HashSet<string>(StringComparer.Ordinal);   // 解析失败视为空表（同 Python）
        }
    }

    private static IEnumerable<string> Names(Dictionary<string, object?> events, string key)
        => events.TryGetValue(key, out var value) && value is List<object?> list
            ? list.Select(x => x?.ToString() ?? "")
            : Enumerable.Empty<string>();
}

/// <summary>字典追加助手（保持 Python <c>setdefault(...).append(...)</c> 的语义）。</summary>
internal static class DictionaryAppend
{
    public static void TryAdd2<TKey, TValue>(this Dictionary<TKey, List<TValue>> map, TKey key, TValue value)
        where TKey : notnull
    {
        if (!map.TryGetValue(key, out var list))
        {
            list = new List<TValue>();
            map[key] = list;
        }
        list.Add(value);
    }
}
