using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/pipelinerun.py</c>：管线**抽象执行**（dry-run）→ 全仓扫一遍。
///
/// 判决分层（关键：把「真错」与「NF 执行模型决定的待裁决项」分开，避免噪声门禁）：
/// **hard**（真缺陷）= 模块在仓库找不到 · 依赖落在严格更后的层 · 类型冲突/可证不匹配；
/// **advisory**（不判死）= 同层内依赖序 · 事件在本执行集内无发布方 · 跨包/外部依赖。
/// 执行集 = 官方核心基座（registry.json modules[]）∪ 管线各层模块。只读、不执行生成。
/// </summary>
public static class PipelineDryrun
{
    public const string ContractDescription = "管线抽象执行零 hard 缺陷";

    private static readonly string[] ModuleGlobs = { "04_模块库/*/*.md", "community/*/modules/*.md" };
    private static readonly Regex FenceRe = new(@"(?ms)```ya?ml\s*\n(.*?)\n```");
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public sealed record Layer(string Id, string Name, bool Optional, List<string> DefaultModules);
    public sealed record Pipeline(string Id, string Name, string StructureType, List<Layer> Layers);

    /// <summary>等价 <c>core.models.fid_key</c>：类别段去「类」字后比较。</summary>
    public static string FidKey(string fid)
    {
        var colon = fid.IndexOf(':');
        if (colon < 0) return fid;
        return fid[..colon].TrimEnd('类') + ":" + fid[(colon + 1)..];
    }

    /// <summary>等价 <c>pipeline_loader.parse_pipeline_md</c>（PyYAML 口径，用 MiniYaml 的等价子集）。</summary>
    public static Pipeline? ParsePipeline(string text)
    {
        var m = FenceRe.Match(text);
        if (!m.Success) return null;
        object? node;
        try
        {
            node = MiniYaml.ParseAny(m.Groups[1].Value);
        }
        catch (Exception)
        {
            return null;
        }
        if (node is not Dictionary<string, object?> root) return null;
        var pnode = root.TryGetValue("Pipeline", out var inner) && inner is Dictionary<string, object?> innerMap
            ? innerMap
            : root;

        var id = (pnode.GetValueOrDefault("id")?.ToString() ?? "").Trim();
        if (id.Length == 0) id = "P00";
        var name = (pnode.GetValueOrDefault("name")?.ToString() ?? id).Trim();
        var structureType = "linear";
        if (pnode.GetValueOrDefault("structure") is Dictionary<string, object?> structure)
            structureType = structure.GetValueOrDefault("type")?.ToString() ?? "linear";

        var layers = new List<Layer>();
        if (pnode.GetValueOrDefault("layers") is List<object?> layerList)
        {
            foreach (var item in layerList.OfType<Dictionary<string, object?>>())
            {
                layers.Add(new Layer(
                    (item.GetValueOrDefault("id")?.ToString() ?? "").Trim(),
                    (item.GetValueOrDefault("name")?.ToString() ?? "").Trim(),
                    item.GetValueOrDefault("optional") is bool flag && flag,
                    Strings(item, "default_modules")));
            }
        }
        return new Pipeline(id, name, structureType, layers);
    }

    public sealed record ModuleRec(string Id, string CatId, string Path, bool HasContract,
        List<string> Inputs, List<string> Outputs, List<string> Publish, List<string> Subscribe,
        Dictionary<string, Dictionary<string, string>> IoTypes);

    /// <summary>仓库模块索引：文件名即 id（全限定由类别限定补），机读契约在场则挂上。</summary>
    public static Dictionary<string, ModuleRec> ModuleFiles(string root)
    {
        var index = new Dictionary<string, ModuleRec>(StringComparer.Ordinal);
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var pattern in ModuleGlobs)
        {
            foreach (var rel in PathGlob.Files(root, pattern))
            {
                if (!seen.Add(rel) || Path.GetFileName(rel) == "README.md") continue;
                var fileName = Path.GetFileName(rel);
                var stem = fileName.Split('_')[0];
                var parent = Path.GetFileName(Path.GetDirectoryName(rel)?.Replace('\\', '/') ?? "");
                var category = parent.Replace("类", "");
                var catId = $"{category}:{stem}";
                var text = StrictUtf8.GetString(File.ReadAllBytes(
                    Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))));
                var parsed = MiniYaml.ParseFence(text, "machine_contract");
                var contract = parsed is not null && parsed.TryGetValue("machine_contract", out var block)
                               && block is Dictionary<string, object?> map
                    ? map
                    : null;
                var hasContract = contract is not null;
                var inputs = Strings(contract, "inputs");
                var outputs = Strings(contract, "outputs");
                var events = contract?.GetValueOrDefault("events") as Dictionary<string, object?>;
                var publish = Strings(events, "publish");
                var subscribe = Strings(events, "subscribe");
                if (contract?.GetValueOrDefault("id")?.ToString() is { Length: > 0 } declaredId)
                    catId = declaredId;
                var ioTypes = IoTypes.ParseIoTypes(text)
                              ?? new Dictionary<string, Dictionary<string, string>>(StringComparer.Ordinal)
                              {
                                  ["outputs"] = new(StringComparer.Ordinal),
                                  ["inputs"] = new(StringComparer.Ordinal),
                              };
                var rec = new ModuleRec(stem, catId, rel, hasContract, inputs, outputs, publish, subscribe, ioTypes);
                index.TryAdd(stem, rec);
                index.TryAdd(catId, rec);
                index.TryAdd(FidKey(catId), rec);
            }
        }
        return index;
    }

    /// <summary>官方核心基座 id（registry.json modules[]）。</summary>
    public static List<string> CoreIds(string root)
    {
        var path = Path.Combine(root, "desktop", "src", "core", "registry.json");
        if (!File.Exists(path)) return new List<string>();
        try
        {
            using var doc = JsonIo.ReadFile(path);
            var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>;
            return (graph?.GetValueOrDefault("modules") as List<object?> ?? new List<object?>())
                .OfType<Dictionary<string, object?>>()
                .Select(m => m.GetValueOrDefault("id")?.ToString() ?? "")
                .Where(id => id.Length > 0)
                .ToList();
        }
        catch (Exception)
        {
            return new List<string>();
        }
    }

    private static ModuleRec? Resolve(string reference, Dictionary<string, ModuleRec> index)
        => index.TryGetValue(reference, out var rec)
            ? rec
            : index.TryGetValue(FidKey(reference), out var byFid)
                ? byFid
                : index.TryGetValue(reference.Split(':')[^1], out var byBare) ? byBare : null;

    /// <summary>advisory 条目（结构化：类别 + 说明，供 CLI 面与台账聚合共用）。</summary>
    public sealed record Note(string Category, string Detail);

    /// <summary>步内模块记录（id / 路径 / 是否有契约）——单管线 --json 面要用。</summary>
    public sealed record StepModule(string Id, string Path, bool HasContract);

    /// <summary>一层执行步（供 CLI 面逐层打印）。</summary>
    public sealed record Step(int Index, string Layer, string LayerName, bool Optional,
        List<StepModule> Modules, List<string> Missing);

    /// <summary>执行图边（kind 恒为 input；同层依赖也记边，与 Python 一致）。</summary>
    public sealed record Edge(string From, string To, string Kind);

    public sealed record GraphResult(string PipelineId, string PipelineName, string StructureType,
        List<Step> Steps,
        List<Edge> Edges, List<string> Tokens, List<string> Published,
        List<string> Issues, List<Note> Notes, Dictionary<string, object?> Stats);

    /// <summary>跑一遍管线声明 → 执行图（hard issues 与 advisory notes 分列）。</summary>
    public static GraphResult Graph(string pipelinePath, string root,
        Dictionary<string, ModuleRec>? moduleIndex = null, List<string>? coreIds = null,
        string? displayPath = null)
    {
        var abs = Path.IsPathRooted(pipelinePath)
            ? pipelinePath
            : Path.Combine(root, pipelinePath.Replace('/', Path.DirectorySeparatorChar));
        var pipeline = File.Exists(abs)
            ? ParsePipeline(StrictUtf8.GetString(File.ReadAllBytes(abs)))
            : null;
        if (pipeline is null)
        {
            // 同 Python：解析失败**抛异常**（由契约层兜成「契约执行异常」），不是给一条判定
            throw new InvalidOperationException(
                $"管线解析失败：{displayPath ?? pipelinePath}（修复指引：检查 frontmatter 与代码围栏闭合）");
        }
        var index = moduleIndex ?? ModuleFiles(root);
        var core = coreIds ?? CoreIds(root);
        var issues = new List<string>();
        var notes = new List<Note>();
        var steps = new List<Step>();
        var edges = new List<Edge>();
        var tokens = new List<string>();
        var done = new HashSet<string>(StringComparer.Ordinal);
        foreach (var id in core)
        {
            done.Add(id);
            done.Add(FidKey(id));
            done.Add(id.Split(':')[^1]);
        }
        var published = new Dictionary<string, string>(StringComparer.Ordinal);
        var subscribed = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        var layerOf = new Dictionary<string, int>(StringComparer.Ordinal);
        var executed = new List<string>();
        var modulesInSteps = 0;
        var missingInSteps = 0;

        // 基座先跑：官方核心的产出/事件进入池
        foreach (var reference in core)
        {
            var rec = Resolve(reference, index);
            if (rec is null) continue;
            foreach (var token in rec.Outputs)
            {
                if (!tokens.Contains(token)) tokens.Add(token);
            }
            foreach (var ev in rec.Publish) published.TryAdd(ev, rec.CatId);
            foreach (var ev in rec.Subscribe)
            {
                if (!subscribed.TryGetValue(ev, out var list))
                {
                    list = new List<string>();
                    subscribed[ev] = list;
                }
                list.Add(rec.CatId);
            }
        }

        for (var idx = 1; idx <= pipeline.Layers.Count; idx++)
        {
            var layer = pipeline.Layers[idx - 1];
            var refs = layer.DefaultModules;
            var sameLayer = refs.Select(r => r).ToHashSet(StringComparer.Ordinal);
            var stepModules = new List<StepModule>();
            var stepMissing = new List<string>();
            foreach (var rawRef in refs)
            {
                var rec = Resolve(rawRef, index);
                if (rec is null)
                {
                    missingInSteps++;
                    stepMissing.Add(rawRef);
                    issues.Add($"模块未在仓库找到：{rawRef}（层 {layer.Id}）" +
                               "（修复指引：核对 04_模块库/community/*/modules 的文件名与类别限定）");
                    continue;
                }
                var mid = rec.CatId;
                executed.Add(mid);
                modulesInSteps++;
                stepModules.Add(new StepModule(mid, rec.Path, rec.HasContract));
                layerOf[mid] = idx;
                foreach (var dep in rec.Inputs)
                {
                    var depRec = Resolve(dep, index);
                    var depId = depRec?.CatId ?? dep;
                    var bare = depId.Split(':')[^1];
                    var depLayer = layerOf.TryGetValue(depId, out var l1) ? l1
                        : layerOf.TryGetValue(bare, out var l2) ? l2 : (int?)null;
                    if (done.Contains(depId) || done.Contains(dep) || done.Contains(bare))
                    {
                        edges.Add(new Edge(depId, mid, "input"));
                    }
                    else if (sameLayer.Contains(dep) || sameLayer.Contains(depId) || sameLayer.Contains(bare))
                    {
                        notes.Add(new Note("同层依赖序", $"{mid} ← {depId}（以注册表合并顺序为准）"));
                        edges.Add(new Edge(depId, mid, "input"));
                    }
                    else if (depLayer is not null && depLayer > idx)
                    {
                        issues.Add($"依赖序违约：{mid} 依赖 {depId}，但 {depId} 未在其之前执行" +
                                   "（修复指引：前移提供方层位，或把该模块移出本层 default）");
                    }
                    else
                    {
                        notes.Add(new Note("跨包/外部依赖", $"{mid} ← {depId}（可能由 references 闭包或外部域包提供）"));
                    }
                }
                done.Add(mid);
                done.Add(FidKey(mid));
                done.Add(mid.Split(':')[^1]);
                done.Add(rec.Id);
                foreach (var token in rec.Outputs)
                {
                    if (!tokens.Contains(token)) tokens.Add(token);
                }
                foreach (var ev in rec.Publish) published.TryAdd(ev, mid);
                foreach (var ev in rec.Subscribe)
                {
                    if (!subscribed.TryGetValue(ev, out var list))
                    {
                        list = new List<string>();
                        subscribed[ev] = list;
                    }
                    list.Add(mid);
                }
            }
            steps.Add(new Step(idx, layer.Id, layer.Name, layer.Optional, stepModules, stepMissing));
        }

        foreach (var ev in subscribed.Keys.OrderBy(x => x, StringComparer.Ordinal))
        {
            if (published.ContainsKey(ev)) continue;
            var subs = string.Join("、", subscribed[ev].Distinct(StringComparer.Ordinal)
                .OrderBy(x => x, StringComparer.Ordinal));
            notes.Add(new Note("跨包/外部事件", $"{subs} ← {ev}（可能由 references 跨包闭包或外部域包提供）"));
        }

        // 类型面：仅在本执行集内判**可证**事项（未收窄不判死）
        var kindOfToken = new Dictionary<string, string>(StringComparer.Ordinal);
        var typeIssuesBefore = issues.Count;
        foreach (var mid in executed)
        {
            var rec = Resolve(mid, index);
            if (rec is null) continue;
            foreach (var (token, kind) in rec.IoTypes["outputs"])
            {
                if (kind == "untyped") continue;
                if (kindOfToken.TryGetValue(token, out var previous) && previous != kind)
                {
                    issues.Add($"类型冲突：token {token} 同时被声明为 {previous} 与 {kind}" +
                               "（修复指引：对齐各模块 io_types.outputs）");
                }
                kindOfToken.TryAdd(token, kind);
            }
        }
        foreach (var mid in executed)
        {
            var rec = Resolve(mid, index);
            if (rec is null) continue;
            foreach (var (dep, want) in rec.IoTypes["inputs"])
            {
                if (want is "untyped" or "state") continue;
                var depRec = Resolve(dep, index);
                if (depRec is null) continue;
                var got = depRec.IoTypes["outputs"].Values.Where(v => v != "untyped")
                    .ToHashSet(StringComparer.Ordinal).OrderBy(v => v, StringComparer.Ordinal).ToList();
                if (got.Count > 0 && !got.Contains(want))
                {
                    issues.Add($"类型不匹配：{mid} 期望 {dep} 提供 {want}，而 {dep} 声明输出类型 " +
                               $"{PyScalar.PyRepr(got.Cast<object?>().ToList())}（修复指引：对齐 io_types 或调整依赖）");
                }
            }
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["layers"] = pipeline.Layers.Count,
            ["modules"] = modulesInSteps,
            ["missing"] = missingInSteps,
            ["core_base"] = core.Count,
            ["tokens"] = tokens.Count,
            ["events_published"] = published.Count,
            ["typed_tokens"] = kindOfToken.Count,
            ["issues"] = issues.Count,
            ["type_issues"] = issues.Count - typeIssuesBefore,
            ["notes"] = notes.Count,
        };
        return new GraphResult(pipeline.Id, pipeline.Name, pipeline.StructureType, steps, edges, tokens,
            published.Keys.OrderBy(x => x, StringComparer.Ordinal).ToList(), issues, notes, stats);
    }

    /// <summary>
    /// 仓库内全部管线文件（<c>03_管线库/*.md</c> + <c>community/*/pipelines/*.md</c>）。
    /// **路径形态同 Python**：<c>Path(root).glob(...)</c> 的结果——root 为绝对时即绝对路径（posix 斜杠），
    /// 报错文案依赖这一点，故不能改成纯相对路径。
    /// </summary>
    public static List<string> Discover(string root)
        => DiscoverPairs(root).Select(p => p.Display).ToList();

    private static List<(string Rel, string Display)> DiscoverPairs(string root)
    {
        var hits = new List<(string, string)>();
        foreach (var pattern in new[] { "03_管线库/*.md", "community/*/pipelines/*.md" })
        {
            foreach (var rel in PathGlob.Files(root, pattern))
                hits.Add((rel, JoinPosix(root, rel)));
        }
        return hits;
    }

    /// <summary>等价 <c>Path(root) / rel</c> 的 posix 字符串（去掉 "." 段与尾随分隔符，保持相对/绝对性）。</summary>
    private static string JoinPosix(string root, string rel)
    {
        var trimmed = root.Replace('\\', '/').TrimEnd('/');
        if (trimmed.Length == 0 || trimmed == ".") return rel;
        return trimmed + "/" + rel;
    }

    /// <summary>全仓管线扫一遍 → (hard issues, stats)（供门禁聚合）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Sweep(string root)
    {
        var issues = new List<string>();
        var pipelines = 0;
        var notes = 0;
        var modules = 0;
        var coreBase = 0;
        var buckets = new Dictionary<string, object?>(StringComparer.Ordinal);
        var index = ModuleFiles(root);           // 等价 Python；进程内缓存（结果相同，仅更快）
        var core = CoreIds(root);
        foreach (var (rel, display) in DiscoverPairs(root))
        {
            var result = Graph(rel, root, index, core, display);
            pipelines++;
            notes += (int)(result.Stats.GetValueOrDefault("notes") ?? 0);
            modules += (int)(result.Stats.GetValueOrDefault("modules") ?? 0);
            coreBase = Math.Max(coreBase, (int)(result.Stats.GetValueOrDefault("core_base") ?? 0));
            foreach (var issue in result.Issues) issues.Add($"{result.PipelineId}：{issue}");
            foreach (var note in result.Notes)
            {
                buckets[note.Category] = (int)(buckets.GetValueOrDefault(note.Category) ?? 0) + 1;
            }
        }
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["pipelines"] = pipelines,
            ["notes"] = notes,
            ["modules"] = modules,
            ["core_base"] = coreBase,
            ["advisory_buckets"] = buckets,
        };
        return (issues, stats);
    }

    /// <summary>
    /// 等价 `pipelinerun.verify_advisory`：**advisory 分类台账与实时重算一致**（类别计数不得悄悄变）。
    /// 台账缺失 / JSON 不可解析 / counts 不一致 都会报 FAIL。
    ///
    /// 计数比较走 `PyScalar.PyEquals`：在盘 JSON 的计数是 **long**、实时重算的是 **int**，直接比 object
    /// 会把 5 与 5 判成不等（第七十五片在 `PyEquals` 上踩过同一坑）。
    /// </summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) VerifyAdvisory(string root)
    {
        var (_, sweepStats) = Sweep(root);
        var live = sweepStats["advisory_buckets"] as Dictionary<string, object?> ?? new Dictionary<string, object?>();
        var notes = Convert.ToInt64(sweepStats["notes"]);
        var issues = new List<string>();
        var ledger = Path.Combine(root, "protocol", "pipeline_advisory.json");
        if (!File.Exists(ledger))
        {
            issues.Add("缺 advisory 台账 protocol/pipeline_advisory.json"
                       + "（修复指引：nf pipeline dryrun --all --write-advisory）");
            return (issues, new Dictionary<string, object?>(StringComparer.Ordinal) { ["total"] = notes });
        }
        try
        {
            using var json = JsonIo.ReadFile(ledger);
            var committed = PythonJson.ToGraph(json.RootElement) as Dictionary<string, object?>;
            var committedCounts = committed?.GetValueOrDefault("counts") as Dictionary<string, object?>;
            if (!PyDictEquals(committedCounts, live))
            {
                issues.Add($"advisory 台账过期：记录 {PyScalar.PyRepr(committedCounts)} ≠ 实测 {PyScalar.PyRepr(live)}"
                           + "（修复指引：重建台账）");
            }
        }
        catch (System.Text.Json.JsonException)
        {
            issues.Add("advisory 台账 JSON 不可解析");
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["total"] = notes,
            ["counts"] = live,
        });
    }

    /// <summary>Python dict 相等：键集相同且**逐值按 Python 语义**相等（int/long/float 混用不算差异）。</summary>
    private static bool PyDictEquals(Dictionary<string, object?>? a, Dictionary<string, object?>? b)
    {
        if (a is null || b is null) return a is null && b is null;
        if (a.Count != b.Count) return false;
        foreach (var (key, value) in a)
        {
            if (!b.TryGetValue(key, out var other)) return false;
            if (!PyScalar.PyEquals(value, other)) return false;
        }
        return true;
    }

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, stats) = Sweep(root);
        return issues.Count == 0
            ? (true, $"管线 {stats["pipelines"]} 条零 hard 缺陷（advisory {stats["notes"]}）")
            : (false, string.Join("; ", issues.Take(2)));
    }

    private static List<string> Strings(Dictionary<string, object?>? map, string key)
        => map is not null && map.TryGetValue(key, out var value) && value is List<object?> list
            ? list.Select(x => x?.ToString() ?? "").ToList()
            : new List<string>();
}
