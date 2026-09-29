using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/market_analyzer.py</c> 的**分级 + 目录视图 + See-Also 关联**三面
/// （依赖闭包 / 挂载冲突两面依赖完整 protocol.yaml 解析与登记三要件，另片再做）。
/// </summary>
public static class MarketAnalyzer
{
    /// <summary>官方核心 13 件（对齐 check14/check15 硬编码 + 01 §6）。</summary>
    public static readonly string[] Official13 =
    {
        "M00", "通用:M10", "M08", "M23", "M24", "M50", "M80",
        "事件:M22", "M06", "M12", "M13", "M20", "M90",
    };

    private static readonly HashSet<string> ExperimentalNums = new(StringComparer.Ordinal)
    {
        "M91", "M92", "M93", "M94", "M95", "M96", "M97", "M98", "M99",
    };

    private static readonly Regex FenceRe = new(@"```yaml(.*?)```", RegexOptions.Singleline);
    private static readonly Regex BareIdRe = new(@"(?m)^\s*id:\s*(M\d+)");
    private static readonly Regex InputsRe = new(@"(?ms)^\s*inputs:\s*\[(.*?)\]");

    /// <summary>模块 id 裸号（M55 / 情感:M55 → M55）。</summary>
    public static string NormNum(object? mid)
    {
        var text = PyText(mid);
        var at = text.LastIndexOf(':');
        return at < 0 ? text : text[(at + 1)..];
    }

    /// <summary>模块质量分级：官方核心 13 件（**比完整 id**，防 M22 重号段误判）→ official；M91-M99 → experimental；其余 → community。</summary>
    public static string GradeOfModule(string moduleId)
    {
        if (Official13.Contains(moduleId, StringComparer.Ordinal)) return "official";
        return ExperimentalNums.Contains(NormNum(moduleId)) ? "experimental" : "community";
    }

    /// <summary>包内各 module_id → grade。</summary>
    public static Dictionary<string, string> GradesOfPackage(
        Dictionary<string, Dictionary<string, object?>> prots, string pkgId)
    {
        var output = new Dictionary<string, string>(StringComparer.Ordinal);
        var entry = prots.TryGetValue(pkgId, out var found) ? found : new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var mid in entry.GetValueOrDefault("module_ids") as List<object?> ?? new List<object?>())
            output[PyText(mid)] = GradeOfModule(PyText(mid));
        return output;
    }

    /// <summary>包级分级：模块全 experimental → experimental；否则 community。</summary>
    public static string PackageGrade(Dictionary<string, Dictionary<string, object?>> prots, string pkgId)
    {
        var grades = GradesOfPackage(prots, pkgId);
        if (grades.Count == 0) return "community";
        return grades.Values.All(g => g == "experimental") ? "experimental" : "community";
    }

    /// <summary>市场目录：官方核心 13 件 + community 包（各带 grade）；<paramref name="tier"/> 过滤。</summary>
    public static List<Dictionary<string, object?>> ListMarket(Dictionary<string, object?> registry, string? tier = null)
    {
        var output = new List<Dictionary<string, object?>>();
        foreach (var m in (registry.GetValueOrDefault("modules") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            output.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["kind"] = "module",
                ["id"] = m.GetValueOrDefault("id"),
                ["name"] = m.GetValueOrDefault("name"),
                ["grade"] = "official",
            });
        }
        var protocols = (registry.GetValueOrDefault("protocols") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var prots = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var p in protocols)
        {
            if (p.GetValueOrDefault("id") is string id && id.Length > 0) prots[id] = p;
        }
        foreach (var p in protocols)
        {
            if (p.GetValueOrDefault("id") is not string pid || pid.Length == 0) continue;
            output.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["kind"] = "package",
                ["id"] = pid,
                ["name"] = p.GetValueOrDefault("name") is string name && name.Length > 0 ? name : pid,
                ["grade"] = PackageGrade(prots, pid),
                ["version"] = (p.GetValueOrDefault("version") as string) is { Length: > 0 } v ? v : "1.0.0",
                ["modules"] = (long)((p.GetValueOrDefault("module_ids") as List<object?>)?.Count ?? 0),
            });
        }
        if (!string.IsNullOrEmpty(tier))
            output = output.Where(x => x.GetValueOrDefault("grade") as string == tier).ToList();
        return output;
    }

    /// <summary>
    /// See-Also 关联（41 波C C4）：目标 = 包 id 或模块 id → 引用了谁 / 谁引用我 / 相关模块互见。
    /// <paramref name="moduleGraph"/> 与 <paramref name="ownerMap"/> 由调用方注入（模块级依赖图）。
    /// </summary>
    public static Dictionary<string, object?> RelatedOf(string target,
        Dictionary<string, Dictionary<string, object?>> prots,
        Dictionary<string, HashSet<string>>? moduleGraph = null,
        Dictionary<string, string>? ownerMap = null)
    {
        var pkgs = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var (pid, p) in prots)
        {
            if (p.GetValueOrDefault("module_ids") is not null) pkgs[pid] = p;
        }
        var mod2pkgs = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
        foreach (var (pid, p) in pkgs)
        {
            foreach (var m in p.GetValueOrDefault("module_ids") as List<object?> ?? new List<object?>())
            {
                var key = PyText(m);
                if (!mod2pkgs.TryGetValue(key, out var set)) mod2pkgs[key] = set = new HashSet<string>(StringComparer.Ordinal);
                set.Add(pid);
            }
        }

        HashSet<string> RefsOf(string pid)
            => (pkgs[pid].GetValueOrDefault("references") as List<object?> ?? new List<object?>())
                .OfType<Dictionary<string, object?>>()
                .Select(r => r.GetValueOrDefault("source_package") as string)
                .Where(sp => !string.IsNullOrEmpty(sp)).Select(sp => sp!).ToHashSet(StringComparer.Ordinal);

        var pkgModules = pkgs.ToDictionary(kv => kv.Key,
            kv => (kv.Value.GetValueOrDefault("module_ids") as List<object?> ?? new List<object?>())
                .Select(PyText).ToHashSet(StringComparer.Ordinal), StringComparer.Ordinal);
        var graph = moduleGraph ?? new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
        var owner = ownerMap ?? new Dictionary<string, string>(StringComparer.Ordinal);

        string OwnerLabel(string mid) => owner.TryGetValue(mid, out var label) ? label : "官方核心";

        var refs = new HashSet<string>(StringComparer.Ordinal);
        var referencedBy = new HashSet<string>(StringComparer.Ordinal);
        var relatedModules = new HashSet<string>(StringComparer.Ordinal);
        var kind = "package";
        if (pkgs.ContainsKey(target))
        {
            refs = RefsOf(target);
            var own = pkgModules[target];
            var deps = new HashSet<string>(StringComparer.Ordinal);
            foreach (var m in own)
            {
                if (graph.TryGetValue(m, out var mDeps)) deps.UnionWith(mDeps);
            }
            deps.ExceptWith(own);
            refs.UnionWith(deps.Select(OwnerLabel));
            relatedModules.UnionWith(deps);
            foreach (var pid in pkgs.Keys)
            {
                if (pid == target) continue;
                var shared = pkgModules[pid].Intersect(own).Any();
                var depHit = pkgModules[pid].Any(m => graph.TryGetValue(m, out var ms) && ms.Overlaps(own));
                if (RefsOf(pid).Contains(target) || depHit || shared)
                {
                    referencedBy.Add(pid);
                    relatedModules.UnionWith(pkgModules[pid]);
                }
            }
        }
        else
        {
            kind = "module";
            var owners = mod2pkgs.TryGetValue(target, out var o) ? o : new HashSet<string>(StringComparer.Ordinal);
            var deps = graph.TryGetValue(target, out var d) ? new HashSet<string>(d, StringComparer.Ordinal) : new HashSet<string>(StringComparer.Ordinal);
            refs.UnionWith(deps.Select(OwnerLabel));
            relatedModules.UnionWith(deps);
            foreach (var pid in owners) refs.UnionWith(RefsOf(pid));
            foreach (var pid in pkgs.Keys)
            {
                if (owners.Contains(pid)) continue;
                var depHit = pkgModules[pid].Any(m => graph.TryGetValue(m, out var ms) && ms.Contains(target));
                if (pkgModules[pid].Contains(target) || depHit)
                {
                    referencedBy.Add(pid);
                    relatedModules.UnionWith(pkgModules[pid]);
                }
            }
            if (relatedModules.Count == 0 && owners.Count > 0) relatedModules = new HashSet<string>(owners, StringComparer.Ordinal);
        }
        refs.Remove(target);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["kind"] = kind,
            ["target"] = target,
            ["refs"] = refs.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
            ["referenced_by"] = referencedBy.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
            ["related_modules"] = relatedModules.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
        };
    }

    /// <summary>
    /// 模块级依赖图（对齐 Python 侧的正则口径）：只收**裸号** `id: M\d+` 的模块，
    /// inputs 取 `inputs: [...]` 原文按 <c>[,\s]+</c> 切分——带前缀的 id 不进图（这是真源的行为，不是本实现的简化）。
    /// </summary>
    public static Dictionary<string, HashSet<string>> ModuleGraph(string root)
    {
        var graph = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal);
        foreach (var rel in ModuleDocs.Files(root))
        {
            var abs = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            string text;
            try
            {
                text = File.ReadAllText(abs, new System.Text.UTF8Encoding(false, true));
            }
            catch (Exception exc) when (exc is IOException or System.Text.DecoderFallbackException)
            {
                continue;
            }
            foreach (var fence in FenceRe.Matches(text).Select(m => m.Groups[1].Value))
            {
                if (!fence.Contains("machine_contract:", StringComparison.Ordinal)) continue;
                var im = BareIdRe.Match(fence);
                if (!im.Success) continue;
                var inputs = new HashSet<string>(StringComparer.Ordinal);
                var iv = InputsRe.Match(fence);
                if (iv.Success)
                {
                    foreach (var x in Regex.Split(iv.Groups[1].Value.Trim(), @"[,\s]+"))
                    {
                        if (x.Length > 0 && !x.StartsWith('#')) inputs.Add(x);
                    }
                }
                if (!graph.TryGetValue(im.Groups[1].Value, out var set))
                    graph[im.Groups[1].Value] = set = new HashSet<string>(StringComparer.Ordinal);
                set.UnionWith(inputs);
            }
        }
        return graph;
    }

    /// <summary>归属映射：community 包内模块 → 包 id；官方 modules[] → 「官方核心」。</summary>
    public static Dictionary<string, string> OwnerMap(Dictionary<string, object?> registry)
    {
        var owner = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var p in (registry.GetValueOrDefault("protocols") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            foreach (var m in p.GetValueOrDefault("module_ids") as List<object?> ?? new List<object?>())
            {
                var key = PyText(m);
                if (!owner.ContainsKey(key)) owner[key] = PyText(p.GetValueOrDefault("id"));
            }
        }
        foreach (var m in (registry.GetValueOrDefault("modules") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            var key = PyText(m.GetValueOrDefault("id"));
            if (!owner.ContainsKey(key)) owner[key] = "官方核心";
        }
        return owner;
    }

    /// <summary>protocols[] → {id: entry}。</summary>
    public static Dictionary<string, Dictionary<string, object?>> Protocols(Dictionary<string, object?> registry)
    {
        var prots = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var p in (registry.GetValueOrDefault("protocols") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            if (p.GetValueOrDefault("id") is string pid && pid.Length > 0) prots[pid] = p;
        }
        return prots;
    }

    // ------------------------------------------------------------------ 包视图：完整协议画像 + 闭包 + 冲突

    /// <summary>挂载层键归一：协议长键（'P40 行为决策'）→ Pxx 短键。</summary>
    public static string LayerKey(object? key)
    {
        var s = key as string ?? PyText(key);
        var parts = s.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        return parts.Length > 0 ? parts[0] : s;
    }

    /// <summary>
    /// 各社区包的**完整** protocol.yaml 画像（<c>package.dependencies</c> / <c>mount_layers</c> 等），
    /// 键 = <c>package.id</c>；不可读 / 不可解析的包按 Python 同规**跳过**。
    /// </summary>
    public static Dictionary<string, Dictionary<string, object?>> PackData(string root)
    {
        var output = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        var community = Path.Combine(root, "community");
        if (!Directory.Exists(community)) return output;
        foreach (var dir in Directory.GetDirectories(community).OrderBy(d => Path.GetFileName(d), StringComparer.Ordinal))
        {
            var path = Path.Combine(dir, "protocol.yaml");
            if (!File.Exists(path)) continue;
            try
            {
                var text = File.ReadAllText(path, new System.Text.UTF8Encoding(false, true));
                var raw = MiniYaml.Parse(text);
                if (raw.GetValueOrDefault("package") is Dictionary<string, object?> pkg
                    && pkg.GetValueOrDefault("id") is string id && id.Length > 0)
                {
                    output[id] = raw;
                }
            }
            catch (Exception exc) when (exc is IOException or ArgumentException or System.Text.DecoderFallbackException)
            {
                continue;   // 尽力而为：跳过不可读/不可解析项（对应门禁另报）
            }
        }
        return output;
    }

    /// <summary>登记三要件前置门槛（等价 <c>registry_sync.check_registerable</c>）：空 = 通过。</summary>
    public static List<string> CheckRegisterable(string pkgDir, string doc)
    {
        var issues = new List<string>();
        var path = Path.Combine(pkgDir, "protocol.yaml");
        if (!File.Exists(path))
            return new List<string> { $"① protocol.yaml 缺失：{path}" };
        Dictionary<string, object?> data;
        try
        {
            data = MiniYaml.Parse(File.ReadAllText(path, new System.Text.UTF8Encoding(false, true)));
        }
        catch (Exception exc) when (exc is IOException or ArgumentException or System.Text.DecoderFallbackException)
        {
            return new List<string> { $"① protocol.yaml 解析失败: {exc.Message}" };
        }
        if (data.GetValueOrDefault("package") is not Dictionary<string, object?> pkg)
            return new List<string> { "① protocol.yaml 缺 package 段（01 §6.1 Schema）" };

        var sv = (data.GetValueOrDefault("protocol") as Dictionary<string, object?>)?.GetValueOrDefault("schema_version");
        var svText = PyText(sv);
        if (svText is not ("1" or "2"))
            issues.Add($"① protocol.schema_version={PyScalar.PyRepr(sv)}（预期 v1 或 v2）");
        var pid = PyText(pkg.GetValueOrDefault("id"));
        if (pid.Length == 0 || pid == "None")
        {
            issues.Add("① package.id 缺失");
            return issues;
        }
        var from = doc.IndexOf("### 8.", StringComparison.Ordinal);
        var to = doc.IndexOf("## 9.", StringComparison.Ordinal);
        var zone = from >= 0 && to > from ? doc[from..to] : "";
        if (zone.Length == 0)
            issues.Add("② 02 §8 登记段未找到（文档结构异常）");
        else if (!zone.Contains(pid, StringComparison.Ordinal))
            issues.Add($"② 包不在 02 §8 在册（登记三要件②缺失）：{pid}——须先在 02 §8.x 登记");
        return issues;
    }

    private static Dictionary<string, object?> PkgDeps(Dictionary<string, Dictionary<string, object?>> data, string pkgId)
        => ((data.TryGetValue(pkgId, out var raw) ? raw.GetValueOrDefault("package") : null)
            as Dictionary<string, object?>)?.GetValueOrDefault("dependencies") as Dictionary<string, object?>
           ?? new Dictionary<string, object?>(StringComparer.Ordinal);

    private static Dictionary<string, object?> PkgMl(Dictionary<string, Dictionary<string, object?>> data, string pkgId)
        => ((data.TryGetValue(pkgId, out var raw) ? raw.GetValueOrDefault("package") : null)
            as Dictionary<string, object?>)?.GetValueOrDefault("mount_layers") as Dictionary<string, object?>
           ?? new Dictionary<string, object?>(StringComparer.Ordinal);

    private static Dictionary<string, object?> PkgRaw(Dictionary<string, Dictionary<string, object?>> data, string pkgId)
        => (data.TryGetValue(pkgId, out var raw) ? raw.GetValueOrDefault("package") : null)
           as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);

    /// <summary>
    /// 依赖闭包（verify check15 ② 同构）：以 references 为起点沿源包 <c>core_modules</c> 递归展开；
    /// 返回 (seen 源包集, issues)。注意真源的一处语义：源包嵌套检查取 **package 层 references**
    /// （verify.sh 误取 <c>dependencies.references</c> 恒空，属死检查）。
    /// </summary>
    public static (HashSet<string> Seen, List<string> Issues) Dependencies(string pkgId,
        Dictionary<string, Dictionary<string, object?>> prots,
        Dictionary<string, Dictionary<string, object?>> data)
    {
        var issues = new List<string>();
        var entry = prots.TryGetValue(pkgId, out var found) ? found : new Dictionary<string, object?>(StringComparer.Ordinal);
        var refs = (entry.GetValueOrDefault("references") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var stack = new List<(string Sp, List<string> Cms)>();
        var pushed = new HashSet<string>(StringComparer.Ordinal);
        foreach (var r in refs)
        {
            if (r.GetValueOrDefault("source_package") is not string sp || sp.Length == 0) continue;
            if (!data.ContainsKey(sp))
            {
                issues.Add($"依赖闭包源包不可读: {sp}");
                continue;
            }
            if (!pushed.Add(sp)) continue;
            var cms = (PkgDeps(data, sp).GetValueOrDefault("core_modules") as List<object?> ?? new List<object?>())
                .Select(PyText).ToList();
            stack.Add((sp, cms));
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        while (stack.Count > 0)
        {
            var (sp, cms) = stack[^1];
            stack.RemoveAt(stack.Count - 1);
            if (!seen.Add(sp))
            {
                issues.Add($"依赖闭包成环: {sp}");
                continue;
            }
            foreach (var x in cms)
            {
                if (!Official13.Contains(x, StringComparer.Ordinal))
                    issues.Add($"依赖闭包叶节点越界官方核心 13 件: {x}（源包 {sp} core_modules）");
            }
            if (PkgRaw(data, sp).GetValueOrDefault("references") is List<object?> nested && nested.Count > 0)
                issues.Add($"依赖闭包检测到源包嵌套 references: {sp}（当前不支持多层组合）");
        }
        return (seen, issues);
    }

    /// <summary>挂载冲突（verify check15 ③ 同构）：组合包各层 default 与源包同层 default 交集非空即冲突。</summary>
    public static List<string> Conflicts(string pkgId,
        Dictionary<string, Dictionary<string, object?>> prots,
        Dictionary<string, Dictionary<string, object?>> data)
    {
        var issues = new List<string>();
        var entry = prots.TryGetValue(pkgId, out var found) ? found : new Dictionary<string, object?>(StringComparer.Ordinal);
        var refs = (entry.GetValueOrDefault("references") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var pkgMl = PkgMl(data, pkgId);
        foreach (var r in refs)
        {
            if (r.GetValueOrDefault("source_package") is not string sp || sp.Length == 0) continue;
            if (!data.ContainsKey(sp)) continue;
            var spMl = PkgMl(data, sp);
            foreach (var (rawKey, specNode) in pkgMl)
            {
                if (specNode is not Dictionary<string, object?> spec) continue;
                var key = LayerKey(rawKey);
                Dictionary<string, object?>? spSpec = null;
                foreach (var (lk, ls) in spMl)
                {
                    if (LayerKey(lk) == key || PyText(lk) == key)
                    {
                        spSpec = ls as Dictionary<string, object?>;
                        break;
                    }
                }
                if (spSpec is null) continue;
                var mine = (spec.GetValueOrDefault("default") as List<object?> ?? new List<object?>()).Select(PyText)
                    .ToHashSet(StringComparer.Ordinal);
                var theirs = (spSpec.GetValueOrDefault("default") as List<object?> ?? new List<object?>()).Select(PyText)
                    .ToHashSet(StringComparer.Ordinal);
                mine.IntersectWith(theirs);
                if (mine.Count > 0)
                {
                    issues.Add($"挂载层 {key} default 冲突: {pkgId}∩{sp}=" +
                               PyScalar.PyRepr(mine.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList()));
                }
            }
        }
        return issues;
    }

    private static string PyText(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        _ => PyScalar.PyRepr(v),
    };
}
