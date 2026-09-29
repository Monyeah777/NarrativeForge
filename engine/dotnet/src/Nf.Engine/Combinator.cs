using System.Security.Cryptography;
using System.Text;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>pack_combo.py::combine</c>：并集 → 闭包补齐（≤12 轮）→ 层栈 → 借阅 → 证书。
/// 证书以「对象图」返回，可直接交给 <see cref="PythonJson.CanonicalizeGraph"/> 做字节级比对与摘要。
/// </summary>
public static class Combinator
{
    public static readonly string[] Core13 =
    {
        "M00", "通用:M10", "M08", "M23", "M24", "M50", "M80",
        "事件:M22", "M06", "M12", "M13", "M20", "M90",
    };

    public static HashSet<string> CoreIds()
    {
        var ids = new HashSet<string>(Core13, StringComparer.Ordinal);
        foreach (var x in Core13) ids.Add(x.Split(':')[^1]);
        return ids;
    }

    private sealed class OrderedModules
    {
        private readonly Dictionary<string, ModuleContracts.Contract> _map = new(StringComparer.Ordinal);
        private readonly List<string> _order = new();

        public int Count => _map.Count;
        public bool Contains(string id) => _map.ContainsKey(id);
        public bool TryGet(string id, out ModuleContracts.Contract? rec) => _map.TryGetValue(id, out rec);
        public ModuleContracts.Contract? Get(string id) => _map.TryGetValue(id, out var r) ? r : null;

        public bool AddIfAbsent(string id, ModuleContracts.Contract rec)
        {
            if (_map.ContainsKey(id)) return false;
            _map[id] = rec;
            _order.Add(id);
            return true;
        }

        public void Set(string id, ModuleContracts.Contract rec)
        {
            if (!_map.ContainsKey(id)) _order.Add(id);
            _map[id] = rec;
        }

        public IEnumerable<string> OrderedKeys => _order;
        public IEnumerable<string> SortedKeys => _order.OrderBy(k => k, StringComparer.Ordinal);
    }

    public sealed record Result(Dictionary<string, object?> Certificate, string Digest, bool Legal);

    public static Result Build(string root, IReadOnlyList<string> packs,
        IReadOnlyList<string>? extraModules = null, IReadOnlyList<string>? extraAssets = null,
        bool strictCoherence = false)
    {
        extraModules ??= Array.Empty<string>();
        extraAssets ??= Array.Empty<string>();

        var cache = RepoCache.For(root);
        var profiles = cache.Profiles;
        var contracts = cache.Contracts;
        var coreContracts = cache.CoreContracts;

        var unknown = packs.Where(p => !profiles.ContainsKey(p)).ToList();
        var chosen = packs.Where(profiles.ContainsKey).Select(p => profiles[p]).ToList();

        // ISA v1 C1′（撞号即 DENY）：严格相干模式下，若某包声明的模块 id 实际解析到**别的包**的契约，
        // 说明该 id 被跨包重复占用（默认行为与 Python 一致：静默塌陷到后到者）。
        var coherenceConflicts = new List<object?>();
        if (strictCoherence)
        {
            foreach (var pr in chosen)
            {
                foreach (var id in pr.Modules)
                {
                    if (!contracts.TryGetValue(id, out var rec)) continue;
                    if (rec.Pack != pr.Package)
                    {
                        coherenceConflicts.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["pack"] = pr.Package,
                            ["module"] = id,
                            ["resolved_pack"] = rec.Pack,
                        });
                    }
                }
            }
        }

        var mods = new OrderedModules();
        foreach (var pr in chosen)
        {
            // 与 Python 对齐：`mods` 由画像的 module_recs 建立——**缺契约的模块也要进来**
            // （以 path 为空的占位记录参与组合，从而被记为 module_missing_contract）。
            // 早期版本改为从 contracts 查表、查不到即丢弃，会让缺契约的模块静默消失（自检抓出）。
            foreach (var id in pr.Modules)
            {
                var rec = contracts.TryGetValue(id, out var found)
                    ? found
                    : contracts.TryGetValue(id.Split(':')[^1], out var byBare)
                        ? byBare
                        : ModuleContracts.FallbackContract(id, pr.Package);
                mods.Set(rec.Id, rec);
            }
        }
        foreach (var mid in extraModules)
        {
            if (!contracts.TryGetValue(mid, out var rec))
            {
                contracts.TryGetValue(mid.Split(':')[^1], out rec);
            }
            if (rec is not null) mods.Set(rec.Id, rec);
        }

        // indexes：by_id / pub_index（community 契约）/ core_pub（核心契约）
        var byId = new Dictionary<string, ModuleContracts.Contract>(StringComparer.Ordinal);
        var pubIndex = new Dictionary<string, List<ModuleContracts.Contract>>(StringComparer.Ordinal);
        foreach (var rec in contracts.Values)
        {
            if (rec.Path.Length == 0) continue;
            byId.TryAdd(rec.Id, rec);
            foreach (var e in rec.Publish)
            {
                if (!pubIndex.TryGetValue(e, out var list)) pubIndex[e] = list = new List<ModuleContracts.Contract>();
                list.Add(rec);
            }
        }
        var corePub = new HashSet<string>(coreContracts.Values.SelectMany(r => r.Publish), StringComparer.Ordinal);

        var borrowed = new List<Dictionary<string, object?>>();
        var unresolvedRefs = new List<Dictionary<string, object?>>();

        bool AddIfAbsent(ModuleContracts.Contract rec, string why, string by)
        {
            if (!mods.AddIfAbsent(rec.Id, rec)) return false;
            borrowed.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["module"] = rec.Id,
                ["from"] = rec.Pack,
                ["by"] = by.Length == 0 ? "<组件级>" : by,
                ["mode"] = "closure_pull",
                ["why"] = why,
            });
            return true;
        }

        foreach (var pr in chosen)
        {
            foreach (var reference in pr.References)
            {
                var src = reference.SourcePackage;
                var mid = reference.ModuleId;
                if (!contracts.TryGetValue(mid, out var rec))
                {
                    contracts.TryGetValue(mid.Split(':')[^1], out rec);
                }
                if (rec is not null && rec.Pack == src)
                {
                    if (!mods.Contains(rec.Id))
                    {
                        mods.Set(rec.Id, rec);
                        borrowed.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["module"] = rec.Id, ["from"] = src, ["by"] = pr.Package, ["mode"] = "module_borrow",
                        });
                    }
                }
                else if (rec is not null)
                {
                    if (!mods.Contains(rec.Id))
                    {
                        mods.Set(rec.Id, rec);
                        borrowed.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["module"] = rec.Id, ["from"] = rec.Pack, ["by"] = pr.Package, ["mode"] = "module_borrow",
                        });
                    }
                }
                else
                {
                    unresolvedRefs.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["by"] = pr.Package, ["source_package"] = src, ["module_id"] = mid,
                    });
                }
            }
        }

        var core = CoreIds();
        for (var round = 0; round < 12; round++)
        {
            var grew = false;
            foreach (var m in mods.OrderedKeys.ToList())
            {
                var r = mods.Get(m)!;
                foreach (var dep in r.Inputs)
                {
                    if (core.Contains(dep) || mods.Contains(dep) || core.Contains(dep.Split(':')[^1])) continue;
                    if (!byId.TryGetValue(dep, out var rec)) byId.TryGetValue(dep.Split(':')[^1], out rec);
                    if (rec is not null && AddIfAbsent(rec, $"依赖 {m} 的 inputs 需要 {dep}", m)) grew = true;
                }
            }

            var publishedNow = new HashSet<string>(StringComparer.Ordinal);
            foreach (var k in mods.OrderedKeys) foreach (var e in mods.Get(k)!.Publish) publishedNow.Add(e);
            publishedNow.UnionWith(corePub);

            foreach (var m in mods.OrderedKeys.ToList())
            {
                var r = mods.Get(m)!;
                foreach (var ev in r.Subscribe)
                {
                    if (publishedNow.Contains(ev)) continue;
                    if (!pubIndex.TryGetValue(ev, out var candidates)) continue;
                    foreach (var rec in candidates)
                    {
                        if (AddIfAbsent(rec, $"事件 {ev} 需要发布方（{m} 订阅）", m)) grew = true;
                    }
                }
            }
            if (!grew) break;
        }

        var missingContracts = mods.SortedKeys.Where(m => mods.Get(m)!.Path.Length == 0).ToList();

        var dangling = new List<object?>();
        foreach (var m in mods.SortedKeys)
        {
            var r = mods.Get(m)!;
            foreach (var dep in r.Inputs)
            {
                if (core.Contains(dep) || mods.Contains(dep) || core.Contains(dep.Split(':')[^1])) continue;
                dangling.Add(new Dictionary<string, object?>(StringComparer.Ordinal) { ["module"] = m, ["needs"] = dep });
            }
        }

        var published = new HashSet<string>(StringComparer.Ordinal);
        foreach (var k in mods.OrderedKeys) foreach (var e in mods.Get(k)!.Publish) published.Add(e);
        published.UnionWith(corePub);

        var unbridged = mods.OrderedKeys.SelectMany(k => mods.Get(k)!.Subscribe)
            .Where(e => !published.Contains(e)).Distinct(StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal).ToList();
        var unpublished = mods.OrderedKeys.SelectMany(k => mods.Get(k)!.Subscribe)
            .Where(e => !published.Contains(e) && !pubIndex.ContainsKey(e)).Distinct(StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal).ToList();
        var explicitDeps = mods.OrderedKeys.SelectMany(k => mods.Get(k)!.Inputs)
            .Where(d => mods.Contains(d)).Distinct(StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal).ToList();

        // 规范序：与层栈一致（Python: canon = sorted(set(packs))）
        var canon = packs.Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToList();
        var order = new Dictionary<string, int>(StringComparer.Ordinal);
        for (var i = 0; i < canon.Count; i++) order[canon[i]] = i;

        var stacks = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var pr in chosen)
        {
            foreach (var kv in pr.Layers)
            {
                if (!stacks.TryGetValue(kv.Key, out var bucket)) stacks[kv.Key] = bucket = new List<string>();
                foreach (var m in kv.Value) if (!bucket.Contains(m, StringComparer.Ordinal)) bucket.Add(m);
            }
        }
        foreach (var m in mods.SortedKeys)
        {
            var lay = mods.Get(m)!.Layer;
            if (lay.Length == 0) continue;
            if (!stacks.TryGetValue(lay, out var bucket)) stacks[lay] = bucket = new List<string>();
            if (!bucket.Contains(m, StringComparer.Ordinal)) bucket.Add(m);
        }
        var stackList = new List<object?>();
        foreach (var lay in stacks.Keys.OrderBy(x => x, StringComparer.Ordinal))
        {
            var modules = stacks[lay].Distinct(StringComparer.Ordinal)
                .OrderBy(m => order.TryGetValue(mods.Get(m)?.Pack ?? "", out var idx) ? idx : 99)
                .ThenBy(m => m, StringComparer.Ordinal).ToList();
            stackList.Add(new Dictionary<string, object?>(StringComparer.Ordinal) { ["layer"] = lay, ["modules"] = modules.Cast<object?>().ToList() });
        }

        var assetIndex = new Dictionary<string, PackProfiles.Asset>(StringComparer.Ordinal);
        foreach (var pr in profiles.Values)
            foreach (var a in pr.Assets) assetIndex[pr.Package + "\u0000" + a.Key] = a;

        var borrow = new List<Dictionary<string, object?>>();
        var unresolvedAssets = new List<string>();
        foreach (var pr in chosen)
        {
            foreach (var a in pr.Assets)
            {
                if (a.Module.Length > 0 && !mods.Contains(a.Module))
                {
                    borrow.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["key"] = a.Key, ["from"] = pr.Package, ["for_module"] = a.Module, ["mode"] = "asset_readonly",
                    });
                }
            }
        }
        foreach (var spec in extraAssets)
        {
            var idx = spec.IndexOf(':');
            var pkg = idx < 0 ? spec : spec[..idx];
            var key = idx < 0 ? "" : spec[(idx + 1)..];
            if (assetIndex.ContainsKey(pkg + "\u0000" + key))
            {
                borrow.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["key"] = key, ["from"] = pkg, ["for_module"] = "", ["mode"] = "asset_readonly",
                });
            }
            else unresolvedAssets.Add(spec);
        }

        var borrowSorted = borrow
            .OrderBy(b => (string)b["from"]!, StringComparer.Ordinal)
            .ThenBy(b => (string)b["key"]!, StringComparer.Ordinal)
            .Select(b => (object?)b).ToList();
        var borrowedSorted = borrowed
            .OrderBy(b => (string)b["by"]!, StringComparer.Ordinal)
            .ThenBy(b => (string)b["module"]!, StringComparer.Ordinal)
            .Select(b => (object?)b).ToList();
        var refsSorted = unresolvedRefs
            .OrderBy(r => (string)r["by"]!, StringComparer.Ordinal)
            .ThenBy(r => (string)r["module_id"]!, StringComparer.Ordinal)
            .Select(r => (object?)r).ToList();

        var cert = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = "nf-combo/1",
            ["packs"] = canon.Cast<object?>().ToList(),
            ["unknown_packs"] = unknown.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
            ["extra_modules"] = extraModules.Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
            ["modules"] = mods.SortedKeys.Cast<object?>().ToList(),
            ["module_count"] = mods.Count,
            ["layer_stacks"] = stackList,
            ["dependency_closure"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["core"] = CoreIds().OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
                ["explicit"] = explicitDeps.Cast<object?>().ToList(),
                ["dangling"] = dangling,
            },
            ["event_closure"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["published"] = published.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
                ["unbridged"] = unbridged.Cast<object?>().ToList(),
            },
            ["events_unpublished"] = unpublished.Cast<object?>().ToList(),
            ["assets_borrowed"] = borrowSorted,
            ["modules_borrowed"] = borrowedSorted,
            ["references_unresolved"] = refsSorted,
            ["assets_unresolved"] = unresolvedAssets.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
            ["module_missing_contract"] = missingContracts.Cast<object?>().ToList(),
        };

        var legal = unknown.Count == 0 && dangling.Count == 0 && unbridged.Count == 0 &&
                    missingContracts.Count == 0 && unresolvedAssets.Count == 0 && unresolvedRefs.Count == 0 &&
                    coherenceConflicts.Count == 0;
        // 只在**确实发现撞号**时才扩展证书形状：干净语料下严格模式与默认模式逐字节一致，
        // 便于把严格模式当作 CI 开关使用而不改变在盘摘要。
        if (strictCoherence && coherenceConflicts.Count > 0)
        {
            cert["coherence_conflicts"] = coherenceConflicts;
            cert["coherence_mode"] = "strict";
        }
        cert["legal"] = legal;

        var canonical = PythonJson.CanonicalizeGraph(cert);
        var digest = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(canonical))).ToLowerInvariant()[..32];
        cert["digest"] = digest;
        return new Result(cert, digest, legal);
    }
}
