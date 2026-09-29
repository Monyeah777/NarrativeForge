using System.Security.Cryptography;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/knowledge.py</c> 的三面（一致性契约 <c>knowledge-sources</c>）：
/// **声明机检**（词表 / 必填 / 防纸面源 / 权威分层 / 时效策略 / 查询有序 / 晋升与审核成文 / 认知裁剪模块在册）
/// + **消化记录**（from 须是已声明参考级源、to 须真实且 digest 一致、转正须三档证据与复核人）
/// + **频次台账**（含未声明源即 FAIL、与记录 reuse_count 交叉复算——频次不可手写）。
///
/// 纪律：只读声明与文件，不自造知识、不联网、零第三方依赖。
/// </summary>
public static class KnowledgeSources
{
    public const string DeclRel = "protocol/knowledge_sources.json";
    public const string LogRel = "protocol/transform_log.json";
    public const string UsageRel = "protocol/knowledge_usage.json";
    public const string Schema = "nf-knowledge-sources/1";
    public const string LogSchema = "nf-transform-log/1";
    public const string UsageSchema = "nf-knowledge-usage/1";
    public const string ContractDescription = "双源知识层（权威分层/查询有序/时效/溯源）";

    private static readonly string[] Authorities = { "contract", "reference" };
    private static readonly string[] Kinds = { "local-compiled", "external-retrieval" };
    private static readonly string[] Visibilities = { "public", "internal", "restricted" };
    private static readonly string[] Tiers = { "machine-checkable", "reproducible", "externally-attestable" };
    private static readonly string[] Triggers = { "reuse-frequency", "author-mark", "machine-check-pass" };
    private static readonly string[] FreshContract = { "stale_after" };
    private static readonly string[] FreshReference = { "ttl", "no-cache" };
    private static readonly string[] RequiredSource =
        { "id", "authority", "kind", "locator", "requires_source_label", "visibility", "freshness" };
    private static readonly string[] RequiredEntry =
        { "from", "to", "digest", "reviewed_by", "reviewed_at", "evidence" };

    private static readonly Regex ModuleIdRe = new(@"^\s*id:\s*(M\d+|事件:M\d+|通用:M\d+)\s*$", RegexOptions.Multiline);
    private static readonly Regex Dated = new(@"^\d{4}-\d{2}-\d{2}$");
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    private static Dictionary<string, object?> ReadJson(string path)
    {
        if (!File.Exists(path)) return new Dictionary<string, object?>(StringComparer.Ordinal);
        using var doc = JsonIo.ReadFile(path);
        return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
    }

    private static Dictionary<string, object?> Decl(string root)
        => ReadJson(Path.Combine(root, DeclRel.Replace('/', Path.DirectorySeparatorChar)));

    private static Dictionary<string, object?> Log(string root)
        => ReadJson(Path.Combine(root, LogRel.Replace('/', Path.DirectorySeparatorChar)));

    private static Dictionary<string, object?> Usage(string root)
        => ReadJson(Path.Combine(root, UsageRel.Replace('/', Path.DirectorySeparatorChar)));

    public static List<Dictionary<string, object?>> Sources(string root)
        => Decl(root).GetValueOrDefault("sources") is List<object?> list
            ? list.OfType<Dictionary<string, object?>>().ToList()
            : new List<Dictionary<string, object?>>();

    private static HashSet<string> ReferenceIds(string root)
        => Sources(root).Where(s => Str(s, "authority") == "reference").Select(s => Str(s, "id"))
            .ToHashSet(StringComparer.Ordinal);

    /// <summary>模块在册 id 集（正则扫模块文档全文，同 Python <c>_module_ids</c>）。</summary>
    private static HashSet<string> ModuleIds(string root)
    {
        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (var rel in PathGlob.Files(root, "04_模块库/*/*.md")
                     .Concat(PathGlob.Files(root, "community/*/modules/*.md")))
        {
            var text = StrictUtf8.GetString(File.ReadAllBytes(
                Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))));
            foreach (Match m in ModuleIdRe.Matches(text)) ids.Add(m.Groups[1].Value);
        }
        return ids;
    }

    private static string Sha256File(string path)
        => Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path))).ToLowerInvariant();

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var decl = Decl(root);
        if (decl.Count == 0)
            return (new List<string> { $"缺知识源声明 {DeclRel}（修复指引：见 docs/knowledge.md）" }, warns,
                new Dictionary<string, object?>(StringComparer.Ordinal));
        if (Str(decl, "schema") != Schema)
            issues.Add($"知识源声明 schema 不匹配（期望 {Schema}）");
        foreach (var (key, vocabulary) in new (string, string[])[]
                 {
                     ("authority_vocabulary", Authorities),
                     ("kind_vocabulary", Kinds),
                     ("visibility_vocabulary", Visibilities),
                 })
        {
            var got = Strings(decl, key);
            if (!got.SequenceEqual(vocabulary, StringComparer.Ordinal))
                issues.Add($"{key} 词表与判据不一致（期望 {string.Join("/", vocabulary)}）");
        }

        var rows = Sources(root);
        if (rows.Count == 0) issues.Add($"未声明任何知识源（{DeclRel}.sources 为空）");
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var source in rows)
        {
            var id = Str(source, "id");
            foreach (var key in RequiredSource)
            {
                if (!source.ContainsKey(key))
                    issues.Add($"源 {(id.Length == 0 ? "(无名)" : id)} 缺必填字段：{key}");
            }
            if (!seen.Add(id)) issues.Add($"源 id 重复：{id}");
            // 注意：Python 这里是 `str(s.get(k))`——**缺键渲染成 "None"**（不是空串），照抄
            var authority = StrOrNone(source, "authority");
            var kind = StrOrNone(source, "kind");
            if (Array.IndexOf(Authorities, authority) < 0)
                issues.Add($"源 {id} authority 越词表：{authority}");
            if (Array.IndexOf(Kinds, kind) < 0)
                issues.Add($"源 {id} kind 越词表：{kind}");
            var visibility = StrOrNone(source, "visibility");
            if (Array.IndexOf(Visibilities, visibility) < 0)
                issues.Add($"源 {id} visibility 越词表：{visibility}");
            var locator = Str(source, "locator");
            if (locator.Length > 0 && !File.Exists(Path.Combine(root, locator.Replace('/', Path.DirectorySeparatorChar)))
                                   && !Directory.Exists(Path.Combine(root, locator.Replace('/', Path.DirectorySeparatorChar))))
            {
                issues.Add($"源 {id} 的 locator 不存在：{locator}（防纸面源）");
            }
            var freshness = source.GetValueOrDefault("freshness") as Dictionary<string, object?>
                            ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var policy = Str(freshness, "policy");
            var labelled = Truthy(source.GetValueOrDefault("requires_source_label"));
            if (authority == "reference")
            {
                if (kind != "external-retrieval")
                    issues.Add($"源 {id} 为 reference 级但 kind 非 external-retrieval");
                if (!labelled)
                    issues.Add($"源 {id} 为 reference 级但未要求标注来源" +
                               "（外部数据不得写死；修复指引：requires_source_label: true）");
                if (Array.IndexOf(FreshReference, policy) < 0)
                    issues.Add($"源 {id} 为 reference 级但时效策略非法：{(policy.Length == 0 ? "(缺)" : policy)}" +
                               $"（需 {string.Join(" / ", FreshReference)}）");
                else if (policy == "ttl"
                         && !(freshness.GetValueOrDefault("ttl_days") is long ttl && ttl > 0))
                    issues.Add($"源 {id} 声明 ttl 但 ttl_days 非正整数");
            }
            else if (authority == "contract")
            {
                if (kind != "local-compiled")
                    issues.Add($"源 {id} 为 contract 级但 kind 非 local-compiled");
                if (labelled)
                    issues.Add($"源 {id} 为 contract 级却要求外部来源标注（合同级即本地真源）");
                if (Array.IndexOf(FreshContract, policy) < 0)
                    issues.Add($"源 {id} 为 contract 级但时效策略非法：{(policy.Length == 0 ? "(缺)" : policy)}（需 stale_after）");
            }
        }

        var order = Strings(decl, "query_order");
        var ids = rows.Select(s => Str(s, "id")).ToList();
        if (!order.OrderBy(x => x, StringComparer.Ordinal).SequenceEqual(
                ids.OrderBy(x => x, StringComparer.Ordinal), StringComparer.Ordinal))
        {
            issues.Add("query_order 与 sources 不是同一集合（缺 " +
                       $"{PyList(ids.Except(order))} / 多 {PyList(order.Except(ids))}）");
        }
        else
        {
            var position = new Dictionary<string, int>(StringComparer.Ordinal);
            for (var i = 0; i < order.Count; i++) position[order[i]] = i;
            var refIndex = ids.Where(i => Authority(rows, i) == "reference").Select(i => position[i]).ToList();
            var conIndex = ids.Where(i => Authority(rows, i) == "contract").Select(i => position[i]).ToList();
            if (refIndex.Count > 0 && conIndex.Count > 0 && conIndex.Max() > refIndex.Min())
                issues.Add("query_order 未把全部合同级排在参考级之前（查询有序被破坏）");
        }

        var promotion = decl.GetValueOrDefault("promotion") as Dictionary<string, object?>
                        ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        if (!Strings(promotion, "evidence_tiers").SequenceEqual(Tiers, StringComparer.Ordinal))
            issues.Add($"promotion.evidence_tiers 与判据不一致（期望 {string.Join("/", Tiers)}）");
        if (!Strings(promotion, "triggers").SequenceEqual(Triggers, StringComparer.Ordinal))
            issues.Add($"promotion.triggers 与判据不一致（期望 {string.Join("/", Triggers)}）");
        if (Str(promotion, "rule").Trim().Length == 0)
            issues.Add("promotion 缺 rule（晋升标准必须成文）");
        if (Str(promotion, "on_missing_evidence") != "stay-reference")
            issues.Add("promotion.on_missing_evidence 必须为 stay-reference（缺证据不得转正）");
        var review = decl.GetValueOrDefault("review") as Dictionary<string, object?>
                     ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        if (Strings(review, "machine_gates").Count == 0)
            issues.Add("review 缺 machine_gates（消化审核必须列机检项）");
        if (Str(review, "rule").Trim().Length == 0)
            issues.Add("review 缺 rule（消化审核规则必须成文）");
        var cognition = decl.GetValueOrDefault("cognition") as Dictionary<string, object?>
                        ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var filterModule = Str(cognition, "filter_module");
        if (filterModule.Length == 0)
            issues.Add("cognition 缺 filter_module（认知裁剪须指定执行模块）");
        else if (!ModuleIds(root).Contains(filterModule))
            issues.Add($"cognition.filter_module 指向不在册模块：{filterModule}");

        var log = Log(root);
        if (log.Count == 0)
            issues.Add($"缺消化记录 {LogRel}（修复指引：见 docs/knowledge.md）");
        else if (Str(log, "schema") != LogSchema)
            issues.Add($"消化记录 schema 不匹配（期望 {LogSchema}）");

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["sources"] = rows.Count,
            ["contract"] = rows.Count(s => Str(s, "authority") == "contract"),
            ["reference"] = rows.Count(s => Str(s, "authority") == "reference"),
            ["order"] = order.Cast<object?>().ToList(),
            ["transforms"] = (log.GetValueOrDefault("entries") as List<object?> ?? new List<object?>()).Count,
        };
        return (issues, warns, stats);
    }

    /// <summary>消化记录校验：from 须是已声明参考级源、to 须真实且 digest 一致、转正须三档证据与复核人。</summary>
    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) VerifyTransform(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var log = Log(root);
        var entries = (log.GetValueOrDefault("entries") as List<object?> ?? new List<object?>());
        var refs = ReferenceIds(root);
        for (var i = 0; i < entries.Count; i++)
        {
            var tag = $"记录 #{i + 1}";
            if (entries[i] is not Dictionary<string, object?> entry)
            {
                issues.Add($"{tag} 非对象");
                continue;
            }
            foreach (var key in RequiredEntry)
            {
                if (!entry.ContainsKey(key)) issues.Add($"{tag} 缺必填字段：{key}");
            }
            var from = Str(entry, "from");
            if (from.Length > 0 && !refs.Contains(from))
                issues.Add($"{tag} 的 from 不是已声明的参考级源：{from}");
            var to = Str(entry, "to");
            if (to.Length > 0)
            {
                var path = Path.Combine(root, to.Replace('/', Path.DirectorySeparatorChar));
                if (!File.Exists(path))
                {
                    issues.Add($"{tag} 的产物不存在：{to}");
                }
                else if (Str(entry, "digest") != Sha256File(path))
                {
                    issues.Add($"{tag} 的产物摘要与记录不一致：{to}" +
                               "（产物已改，记录失效；修复指引：重新消化并更新 digest）");
                }
            }
            var evidence = Strings(entry, "evidence");
            if (Truthy(entry.GetValueOrDefault("promoted")))
            {
                var missing = Tiers.Where(t => !evidence.Contains(t, StringComparer.Ordinal)).ToList();
                if (missing.Count > 0)
                    issues.Add($"{tag} 声明转正但缺证据档：{string.Join("/", missing)}");
                if (Str(entry, "reviewed_by").Trim().Length == 0)
                    issues.Add($"{tag} 声明转正但无复核人（消化审核未双签）");
            }
            if (entry.ContainsKey("reuse_count")
                && !(entry.GetValueOrDefault("reuse_count") is long count && count >= 0))
            {
                issues.Add($"{tag} 的 reuse_count 非非负整数（频次判据不可复算）");
            }
            var reviewedAt = Str(entry, "reviewed_at");
            if (reviewedAt.Length > 0 && !Dated.IsMatch(reviewedAt))
                issues.Add($"{tag} 的 reviewed_at 非 YYYY-MM-DD");
        }
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["entries"] = entries.Count,
            ["promoted"] = entries.OfType<Dictionary<string, object?>>()
                .Count(e => Truthy(e.GetValueOrDefault("promoted"))),
        };
        return (issues, warns, stats);
    }

    /// <summary>频率台账校验：含未声明源即 FAIL + 与消化记录 reuse_count 交叉复算（频次不可手写）。</summary>
    /// <summary>
    /// 复刻 <c>knowledge.py::harvest_frequency</c>：从 trace 记录数知识源使用频次（确定性、不联网）。
    /// 记录形态支持三种：JSON 数组 / <c>{"records": [...]}</c> / JSONL（逐行对象）；
    /// 源标识取 <c>knowledge_source</c> 或 <c>source_id</c>（与遥测 semconv 对齐）。
    /// 文件不可读 → 抛 <see cref="IOException"/>（CLI 侧按 <c>except OSError</c> 语义转受控失败）。
    /// </summary>
    public static Dictionary<string, object?> HarvestFrequency(string tracePath)
    {
        var text = StrictUtf8.GetString(File.ReadAllBytes(tracePath));
        var records = new List<object?>();
        var parsedWhole = true;
        try
        {
            using var doc = System.Text.Json.JsonDocument.Parse(text);
            var graph = PythonJson.ToGraph(doc.RootElement);
            if (graph is List<object?> list)
            {
                records = list;
            }
            else if (graph is Dictionary<string, object?> map)
            {
                records = map.GetValueOrDefault("records") is List<object?> rs
                    ? rs
                    : new List<object?> { map };
            }
        }
        catch (System.Text.Json.JsonException)
        {
            parsedWhole = false;
        }
        if (!parsedWhole)
        {
            foreach (var raw in text.Split('\n'))
            {
                var line = raw.Trim();
                if (line.Length == 0) continue;
                try
                {
                    using var doc = System.Text.Json.JsonDocument.Parse(line);
                    records.Add(PythonJson.ToGraph(doc.RootElement));
                }
                catch (System.Text.Json.JsonException)
                {
                    // Python：单行解析失败即 continue（不整体失败）
                }
            }
        }

        var counts = new SortedDictionary<string, long>(StringComparer.Ordinal);
        foreach (var node in records)
        {
            if (node is not Dictionary<string, object?> rec) continue;
            var rawId = rec.GetValueOrDefault("knowledge_source");
            if (!PyTruthy(rawId)) rawId = rec.GetValueOrDefault("source_id");
            var sid = PyTruthy(rawId) ? PyScalarText(rawId) : "";
            if (sid.Length == 0) continue;
            counts[sid] = counts.GetValueOrDefault(sid) + 1;
        }
        return counts.ToDictionary(kv => kv.Key, kv => (object?)kv.Value, StringComparer.Ordinal);
    }

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

    private static string PyScalarText(object? v) => v switch
    {
        null => "None",
        string s => s,
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        _ => PyScalar.PyRepr(v),
    };

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) VerifyUsage(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var doc = Usage(root);
        if (doc.Count == 0)
            return (new List<string> { $"缺频率台账 {UsageRel}（修复指引：nf knowledge frequency --trace <file> --write）" },
                warns, new Dictionary<string, object?>(StringComparer.Ordinal));
        if (Str(doc, "schema") != UsageSchema)
            issues.Add($"频率台账 schema 不匹配（期望 {UsageSchema}）");
        var counts = doc.GetValueOrDefault("counts") as Dictionary<string, object?>
                     ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        if (doc.GetValueOrDefault("counts") is not Dictionary<string, object?>)
            issues.Add("频率台账 counts 非对象");
        var ids = Sources(root).Select(s => Str(s, "id")).ToHashSet(StringComparer.Ordinal);
        foreach (var (key, value) in counts)
        {
            if (!ids.Contains(key)) issues.Add($"频率台账含未声明的源：{key}（防幽灵频次）");
            if (!(value is long n && n >= 0)) issues.Add($"频率计数非非负整数：{key}");
        }
        if (doc.GetValueOrDefault("total") is long total
            && total != counts.Values.OfType<long>().Sum())
        {
            issues.Add("频率台账 total 与 counts 求和不一致（手改痕迹）");
        }
        foreach (var entry in (Log(root).GetValueOrDefault("entries") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            if (!entry.ContainsKey("reuse_count")) continue;
            var from = Str(entry, "from");
            var got = counts.TryGetValue(from, out var value) ? value : null;
            var wanted = entry.GetValueOrDefault("reuse_count");
            if (!PyScalar.PyEquals(wanted, got))
            {
                issues.Add($"频次不可复算：{from} 的记录 reuse_count={PyReprPlain(wanted)}，" +
                           $"频率台账={PyReprPlain(got)}（修复指引：按 trace 重算，不要手写频次）");
            }
        }
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["sources_with_usage"] = counts.Count,
            ["events"] = counts.Values.OfType<long>().Sum(),
        };
        return (issues, warns, stats);
    }

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _, stats) = Scan(root);
        var all = new List<string>(issues);
        all.AddRange(VerifyTransform(root).Issues);
        var (usageIssues, _, usageStats) = VerifyUsage(root);
        all.AddRange(usageIssues);
        if (all.Count > 0) return (false, string.Join("; ", all.Take(2)));
        var detail = $"源 {stats.GetValueOrDefault("sources")}（合同 {stats.GetValueOrDefault("contract")} / " +
                     $"参考 {stats.GetValueOrDefault("reference")}）· 消化记录 {stats.GetValueOrDefault("transforms")} · " +
                     $"频次事件 {usageStats.GetValueOrDefault("events")}";
        return (true, detail);
    }

    /// <summary>可见性秩：clearance 达到源的秩即可见（public ⊆ internal ⊆ restricted）。</summary>
    private static readonly Dictionary<string, int> VisibilityRank = new(StringComparer.Ordinal)
    {
        ["public"] = 0, ["internal"] = 1, ["restricted"] = 2,
    };

    /// <summary>逐源可见性裁剪（认知边界协同的**执行面**：越权源不进入查询顺序）。</summary>
    public static HashSet<string> VisibleIds(string root, string clearance = "restricted")
    {
        var result = new HashSet<string>(StringComparer.Ordinal);
        if (!VisibilityRank.TryGetValue(clearance, out var cap)) return result;
        foreach (var source in Sources(root))
        {
            var rank = VisibilityRank.TryGetValue(Str(source, "visibility"), out var r) ? r : 99;
            if (rank <= cap) result.Add(Str(source, "id"));
        }
        return result;
    }

    /// <summary>按声明的 <c>query_order</c> 解析查询顺序（先合同级、再参考级）；clearance 非空时先裁剪。</summary>
    public static List<Dictionary<string, object?>> ResolveOrder(string root, string clearance = "")
    {
        var decl = Decl(root);
        var rows = Sources(root);
        var byId = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var source in rows) byId[Str(source, "id")] = source;
        var allowed = clearance.Length > 0 ? VisibleIds(root, clearance) : null;
        var result = new List<Dictionary<string, object?>>();
        foreach (var id in Strings(decl, "query_order"))
        {
            if (!byId.TryGetValue(id, out var source)) continue;
            if (allowed is not null && !allowed.Contains(id)) continue;
            result.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = id,
                ["authority"] = Str(source, "authority"),
                ["kind"] = Str(source, "kind"),
                ["locator"] = Str(source, "locator"),
                ["requires_source_label"] = Truthy(source.GetValueOrDefault("requires_source_label")) ? "true" : "false",
                ["visibility"] = Str(source, "visibility"),
            });
        }
        return result;
    }

    /// <summary>
    /// 唯一来源复用（conref/keyref 的可验证版）：ID 唯一且等于文件名 · ALIAS 小写键唯一且指向在册 ·
    /// **任意两件（馆藏条目 + 实践包源件）全文摘要不得相同**（同一内容两份 = 两个真源）。
    /// </summary>
    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) VerifyReuse(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var lib = PathGlob.Files(root, "library/NF-*.md");
        var ids = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var rel in lib)
        {
            var (fm, _) = DocContractIo.ReadFrontmatter(root, rel);
            var fileName = Path.GetFileName(rel);
            var eid = fm is null ? "" : DocContracts.Str(fm, "id");
            if (eid.Length == 0)
            {
                issues.Add($"{fileName} 缺 frontmatter id（复用面无法寻址）");
                continue;
            }
            if (ids.TryGetValue(eid, out var prior))
                issues.Add($"条目 id 重复：{eid}（{prior} 与 {fileName}）——同一编号两处真源");
            ids[eid] = fileName;
            if (eid != Path.GetFileNameWithoutExtension(fileName))
                issues.Add($"{fileName} 的 id 与文件名不一致：{eid}");
        }
        var digests = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        foreach (var rel in lib.Concat(PathGlob.Files(root, "patterns/*/PATTERN.md")))
        {
            var digest = Sha256File(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)));
            if (!digests.TryGetValue(digest, out var list)) digests[digest] = list = new List<string>();
            list.Add(rel);
        }
        foreach (var (_, files) in digests)
        {
            if (files.Count > 1)
                issues.Add($"同一内容存在两份（禁止复制正文）：{string.Join(" 、 ", files)}");
        }
        var aliasPath = Path.Combine(root, "library", "ALIAS.md");
        var aliasKeys = 0;
        if (File.Exists(aliasPath))
        {
            var seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (var line in StrictUtf8.GetString(File.ReadAllBytes(aliasPath))
                         .Split('\n').Select(l => l.TrimEnd('\r')))
            {
                if (!line.StartsWith('|')) continue;
                var cells = line.Trim('|').Split('|').Select(c => c.Trim()).ToList();
                if (cells.Count < 2 || cells[0] is "小写键" or "---"
                    || cells[0].All(c => c is '-' or ':' or ' ')) continue;
                var key = cells[0];
                var real = cells[1];
                if (!seen.Add(key)) issues.Add($"ALIAS 小写键重复：{key}（转译将歧义）");
                aliasKeys++;
                if (real.Length > 0 && !ids.ContainsKey(real))
                    issues.Add($"ALIAS 指向不在册条目：{key} → {real}");
            }
        }
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["entries"] = lib.Count,
            ["alias_keys"] = File.Exists(aliasPath) ? aliasKeys : 0,
            ["unique_digests"] = digests.Count,
        };
        return (issues, warns, stats);
    }

    /// <summary>知识层巡检（悬空引用 / 孤儿 / 时效 / 溯源 / 声明）——聚合前面几面 + 馆藏引用面。</summary>
    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Lint(string root)
    {
        var (issues, warns, stats) = Scan(root);
        issues.AddRange(VerifyTransform(root).Issues);
        issues.AddRange(VerifyUsage(root).Issues);
        issues.AddRange(VerifyReuse(root).Issues);
        var entryIds = PathGlob.Files(root, "library/NF-*.md")
            .Select(Path.GetFileName)
            .Select(n => n is null ? "" : n[..^3])
            .ToList();
        var indexPath = Path.Combine(root, "library", "INDEX.md");
        var index = File.Exists(indexPath) ? StrictUtf8.GetString(File.ReadAllBytes(indexPath)) : "";
        var dangling = new List<string>();
        foreach (var rel in new[] { "library/INDEX.md", "library/ALIAS.md", "llms.txt" })
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path)) continue;
            var text = StrictUtf8.GetString(File.ReadAllBytes(path));
            foreach (Match m in LibraryRefRe.Matches(text))
            {
                var target = Path.Combine(root, "library", m.Groups[1].Value + ".md");
                if (!File.Exists(target))
                    dangling.Add($"{rel} → {m.Groups[1].Value}.md");
            }
        }
        foreach (var item in dangling.Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal))
            issues.Add($"悬空引用（提及但无件）：{item}");
        var orphan = entryIds.Where(e => index.Length > 0 && !index.Contains(e, StringComparison.Ordinal)).ToList();
        foreach (var item in orphan) issues.Add($"孤儿条目（未出现在 INDEX 生成区）：{item}");
        var noStale = new List<string>();
        foreach (var rel in PathGlob.Files(root, "library/NF-*.md"))
        {
            var text = StrictUtf8.GetString(File.ReadAllBytes(
                Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))));
            if (!text.Contains("stale_after:", StringComparison.Ordinal))
                noStale.Add(Path.GetFileName(rel));
        }
        foreach (var item in noStale) warns.Add($"条目未声明 stale_after（时效无法判定）：{item}");
        stats["entries"] = entryIds.Count;
        stats["orphan"] = orphan.Count;
        stats["dangling"] = dangling.Distinct(StringComparer.Ordinal).Count();
        stats["no_stale_after"] = noStale.Count;
        return (issues, warns, stats);
    }

    private static readonly Regex LibraryRefRe = new(@"library/([A-Za-z0-9\-]+)\.md");

    /// <summary>源清单的只读别名（CLI 面用）。</summary>
    public static List<Dictionary<string, object?>> SourcesOf(string root) => Sources(root);

    /// <summary>消化记录条目（CLI 面用）。</summary>
    public static List<Dictionary<string, object?>> LogEntries(string root)
        => (Log(root).GetValueOrDefault("entries") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();

    private static string Authority(List<Dictionary<string, object?>> rows, string id)
    {
        foreach (var source in rows)
        {
            if (Str(source, "id") == id) return Str(source, "authority");
        }
        return "";
    }

    private static string Str(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is not null ? value.ToString() ?? "" : "";

    /// <summary>等价 Python <c>str(s.get(k))</c>：缺键与 null 都渲染成 <c>None</c>。</summary>
    private static string StrOrNone(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is not null ? value.ToString() ?? "None" : "None";

    private static List<string> Strings(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is List<object?> list
            ? list.Select(x => x?.ToString() ?? "").ToList()
            : new List<string>();

    private static bool Truthy(object? value) => value switch
    {
        null => false,
        bool flag => flag,
        string text => text.Length > 0,
        List<object?> list => list.Count > 0,
        _ => true,
    };

    private static string PyList(IEnumerable<string> items)
        => PyScalar.PyRepr(items.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList());

    /// <summary>Python <c>%s</c> 形态（整数不带引号，None → None）。</summary>
    private static string PyReprPlain(object? value) => value switch
    {
        null => "None",
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        string s => s,
        _ => value.ToString() ?? "",
    };
}
