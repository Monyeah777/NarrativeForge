using System.Text.RegularExpressions;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/modeling.py</c>：内容建模三件——词表登记册 / 规范与说明件名单 / 数据契约登记。
///
/// `probe.kind = python_attr` 是 Python 侧特有机制（引用 Python 模块常量）。本引擎用**固定表**
/// 镜像这四个常量（`doc_hygiene.KINDS` / `assertions.KINDS` / `rfc.CATEGORIES` / `patterns.STATUSES`），
/// 一旦 Python 侧改动，双跑对账会立刻报红——漂移不会被静默吞掉。
/// </summary>
public static class Modeling
{
    public const string VocabRel = "protocol/vocabularies.json";
    public const string NormRel = "protocol/normative.json";
    public const string ContractsRel = "protocol/data_contracts.json";
    public const string ReceiptsRel = "protocol/RECEIPTS.json";

    private static readonly Regex CheckRe = new(@"^check(\d+)\(\)\{", RegexOptions.Multiline);
    private static readonly Regex CheckNameRe = new(@"^check(\d+)$");

    /// <summary>镜像 Python 模块常量（见类注释）。</summary>
    private static readonly Dictionary<string, string[]> PythonAttrMirror = new(StringComparer.Ordinal)
    {
        ["core.doc_hygiene.KINDS"] = new[] { "tutorial", "how-to", "reference", "explanation" },
        ["core.assertions.KINDS"] = new[] { "regex_absent", "regex_present", "count_at_least", "json_value" },
        ["core.rfc.CATEGORIES"] = new[] { "Standards Track", "Informational", "Experimental", "Process" },
        ["core.patterns.STATUSES"] = new[] { "active", "deprecated" },
    };

    public sealed record PartResult(List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats);
    public sealed record Result(List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats);

    /// <summary>等价 <c>nf model [vocab|normative|contracts]</c>（part 为空 = 三件全跑）。</summary>
    public static Result Run(string root, string part = "")
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var (name, fn) in new (string, Func<string, PartResult>)[]
                 {
                     ("vocab", VerifyVocabularies),
                     ("normative", VerifyNormative),
                     ("contracts", VerifyContracts),
                 })
        {
            if (part.Length > 0 && part != name) continue;
            var result = fn(root);
            issues.AddRange(result.Issues);
            warns.AddRange(result.Warns);
            stats[name] = result.Stats;
        }
        return new Result(issues, warns, stats);
    }

    public static PartResult VerifyVocabularies(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var doc = ReadJson(root, VocabRel);
        if (doc is null)
            return new PartResult(new List<string> { $"缺词表登记册 {VocabRel}" }, warns,
                new Dictionary<string, object?>());

        using (doc)
        {
            var rootElement = doc.RootElement;
            if (Str(rootElement, "schema") != "nf-vocabularies/1")
                issues.Add("词表登记册 schema 不匹配（期望 nf-vocabularies/1）");
            var statuses = StringArray(rootElement, "status_vocabulary");
            if (!statuses.OrderBy(x => x, StringComparer.Ordinal)
                    .SequenceEqual(new[] { "active", "deprecated" }, StringComparer.Ordinal))
                issues.Add("status 词表与判据不一致（期望 active/deprecated）");
            var kinds = StringArray(rootElement, "probe_kinds");

            var seen = new HashSet<string>(StringComparer.Ordinal);
            var literalCount = 0;
            foreach (var scheme in rootElement.GetProperty("schemes").EnumerateArray())
            {
                var id = Str(scheme, "id");
                if (!seen.Add(id)) issues.Add("词表 id 重复：" + id);
                if (!statuses.Contains(Str(scheme, "status")))
                    issues.Add($"词表 {id} status 越词表：{Str(scheme, "status")}");

                var values = StringArray(scheme, "values");
                if (values.Count < 2) issues.Add($"词表 {id} 少于两个值（不成词表）");
                if (values.Distinct(StringComparer.Ordinal).Count() != values.Count)
                    issues.Add($"词表 {id} 值重复");
                foreach (var alias in StringArray(scheme, "aliases"))
                {
                    if (values.Contains(alias)) issues.Add($"词表 {id} 的 alias 与值撞车：{alias}");
                }

                var probe = scheme.TryGetProperty("probe", out var p) && p.ValueKind == JsonValueKind.Object ? p : default;
                var kind = probe.ValueKind == JsonValueKind.Object ? Str(probe, "kind") : "";
                if (!kinds.Contains(kind))
                {
                    issues.Add($"词表 {id} 的 probe.kind 不在册：{kind}");
                    continue;
                }
                var (live, note) = Probe(root, probe);
                if (kind == "literal") { literalCount++; continue; }
                if (live.Count == 0)
                {
                    issues.Add($"词表 {id} 的真源取不到（{note}）");
                    continue;
                }
                if (!live.OrderBy(x => x, StringComparer.Ordinal)
                        .SequenceEqual(values.OrderBy(x => x, StringComparer.Ordinal), StringComparer.Ordinal))
                {
                    issues.Add($"词表 {id} 与真源漂移：册={string.Join("/", values.OrderBy(x => x, StringComparer.Ordinal))} " +
                               $"真源={string.Join("/", live.OrderBy(x => x, StringComparer.Ordinal))}");
                }
            }
            return new PartResult(issues, warns, new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["schemes"] = seen.Count,
                ["literal"] = literalCount,
            });
        }
    }

    private static (List<string> Values, string Note) Probe(string root, JsonElement probe)
    {
        var kind = Str(probe, "kind");
        switch (kind)
        {
            case "literal":
                return (new List<string>(), "literal（以本册为准）");
            case "python_attr":
                var key = Str(probe, "module") + "." + Str(probe, "attr");
                return PythonAttrMirror.TryGetValue(key, out var mirrored)
                    ? (mirrored.ToList(), "python_attr")
                    : (new List<string>(), "python_attr 未在镜像表内：" + key);
            case "json_path":
                var doc = ReadJson(root, Str(probe, "file"));
                if (doc is null) return (new List<string>(), "json_path 断链：" + Str(probe, "path"));
                using (doc)
                {
                    var current = doc.RootElement;
                    var path = Str(probe, "path");
                    foreach (var part in path.Split('.'))
                    {
                        if (current.ValueKind != JsonValueKind.Object || !current.TryGetProperty(part, out var next))
                            return (new List<string>(), "json_path 断链：" + path);
                        current = next;
                    }
                    return (AsValues(current), "json_path");
                }
            default:
                return (new List<string>(), "未知 probe.kind：" + kind);
        }
    }

    private static List<string> AsValues(JsonElement element) => element.ValueKind switch
    {
        JsonValueKind.Object => element.EnumerateObject().Select(p => p.Name).ToList(),
        JsonValueKind.Array => element.EnumerateArray().Select(x => x.ValueKind == JsonValueKind.String
            ? x.GetString()! : x.GetRawText()).ToList(),
        _ => new List<string>(),
    };

    public static PartResult VerifyNormative(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var doc = ReadJson(root, NormRel);
        if (doc is null)
            return new PartResult(new List<string> { $"缺规范/说明件名单 {NormRel}" }, warns,
                new Dictionary<string, object?>());

        using (doc)
        {
            var rootElement = doc.RootElement;
            if (Str(rootElement, "schema") != "nf-normative/1")
                issues.Add("规范件名单 schema 不匹配（期望 nf-normative/1）");

            var verifyPath = Path.Combine(root, "verify.sh");
            var verifyText = File.Exists(verifyPath) ? File.ReadAllText(verifyPath) : "";
            var checks = CheckRe.Matches(verifyText).Select(m => m.Groups[1].Value)
                .ToHashSet(StringComparer.Ordinal);
            var receipts = ReceiptIds(root);

            var normativePaths = new List<string>();
            foreach (var item in rootElement.GetProperty("normative").EnumerateArray())
            {
                if (item.ValueKind != JsonValueKind.Object)
                {
                    var plain = item.ValueKind == JsonValueKind.String ? item.GetString()! : item.GetRawText();
                    normativePaths.Add(plain);
                    if (plain.Length == 0) issues.Add("规范件条目缺 path");
                    else if (!File.Exists(Path.Combine(root, plain))) issues.Add("规范件不存在：" + plain);
                    continue;
                }
                var entry = item;
                var rel = Str(entry, "path");
                normativePaths.Add(rel);
                if (rel.Length == 0) { issues.Add("规范件条目缺 path"); continue; }
                if (!File.Exists(Path.Combine(root, rel))) { issues.Add("规范件不存在：" + rel); continue; }
                if (receipts.Contains(rel)) continue;
                var covered = StringArray(entry, "covered_by");
                if (covered.Count == 0)
                {
                    issues.Add($"规范件既未被回执锚定也无 covered_by：{rel}（修复指引：跑 nf receipts --write，或显式声明 covered_by）");
                    continue;
                }
                foreach (var c in covered)
                {
                    var m = CheckNameRe.Match(c);
                    if (m.Success && !checks.Contains(m.Groups[1].Value))
                        issues.Add($"规范件 {rel} 的 covered_by 指向不存在的 check：{c}");
                }
            }

            var informativeFiles = new HashSet<string>(StringComparer.Ordinal);
            foreach (var glob in StringArray(rootElement, "informative"))
            {
                var pattern = glob.EndsWith("/**", StringComparison.Ordinal) ? glob + "/*" : glob;
                var hits = Assertions.Glob(root, pattern);
                if (hits.Count == 0) warns.Add("说明件名单的条目无匹配（可能写错）：" + glob);
                foreach (var hit in hits) informativeFiles.Add(Path.GetRelativePath(root, hit).Replace('\\', '/'));
            }
            foreach (var rel in informativeFiles.OrderBy(x => x, StringComparer.Ordinal))
            {
                if (receipts.Contains(rel)) issues.Add("说明件被回执锚定（等于把解释当规范）：" + rel);
            }
            foreach (var rel in normativePaths.Intersect(informativeFiles).OrderBy(x => x, StringComparer.Ordinal))
            {
                issues.Add("同一件既列规范又列说明：" + rel);
            }

            return new PartResult(issues, warns, new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["normative"] = normativePaths.Count,
                ["informative_files"] = informativeFiles.Count,
                ["receipts"] = receipts.Count,
            });
        }
    }

    public static PartResult VerifyContracts(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var doc = ReadJson(root, ContractsRel);
        if (doc is null)
            return new PartResult(new List<string> { $"缺数据契约登记 {ContractsRel}" }, warns,
                new Dictionary<string, object?>());

        using (doc)
        {
            var rootElement = doc.RootElement;
            if (Str(rootElement, "schema") != "nf-data-contracts/1")
                issues.Add("数据契约登记 schema 不匹配（期望 nf-data-contracts/1）");
            var statuses = StringArray(rootElement, "status_vocabulary");
            var prefixes = StringArray(rootElement, "rule_prefixes");
            if (!prefixes.SequenceEqual(new[] { "check", "assertion:" }, StringComparer.Ordinal))
                issues.Add("rule_prefixes 与判据不一致（期望 check / assertion:）");

            var verifyPath = Path.Combine(root, "verify.sh");
            var verifyText = File.Exists(verifyPath) ? File.ReadAllText(verifyPath) : "";
            var checks = CheckRe.Matches(verifyText).Select(m => m.Groups[1].Value)
                .ToHashSet(StringComparer.Ordinal);
            var assertionIds = AssertionIds(root);

            var seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (var contract in rootElement.GetProperty("contracts").EnumerateArray())
            {
                var id = Str(contract, "id");
                if (!seen.Add(id)) issues.Add("契约 id 重复：" + id);
                var artifact = Str(contract, "artifact");
                if (artifact.Length == 0 || !File.Exists(Path.Combine(root, artifact)))
                    issues.Add($"契约 {id} 的 artifact 不存在：{(artifact.Length > 0 ? artifact : "(缺)")}");
                if (!statuses.Contains(Str(contract, "status")))
                    issues.Add($"契约 {id} status 越词表：{Str(contract, "status")}");
                if (Str(contract, "owner").Trim().Length == 0)
                    issues.Add($"契约 {id} 缺 owner（无人认领的契约不许登记）");
                if (Str(contract, "freshness").Trim().Length == 0)
                    issues.Add($"契约 {id} 缺 freshness（重建动作必须写明）");

                var rule = Str(contract, "quality_rule");
                if (rule.StartsWith("check", StringComparison.Ordinal))
                {
                    var n = rule[5..];
                    if (!checks.Contains(n)) issues.Add($"契约 {id} 的 quality_rule 指向不存在的 check：{rule}");
                }
                else if (rule.StartsWith("assertion:", StringComparison.Ordinal))
                {
                    var aid = rule.Split(':', 2)[1];
                    if (!assertionIds.Contains(aid)) issues.Add($"契约 {id} 的 quality_rule 指向不存在的断言：{rule}");
                }
                else
                {
                    issues.Add($"契约 {id} 的 quality_rule 无法解析（须 checkN 或 assertion:<id>）：{(rule.Length > 0 ? rule : "(缺)")}");
                }
            }

            return new PartResult(issues, warns, new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["contracts"] = seen.Count,
                ["checks_seen"] = checks.Count,
                ["assertions_seen"] = assertionIds.Count,
            });
        }
    }

    private static HashSet<string> AssertionIds(string root)
    {
        var doc = ReadJson(root, "protocol/assertions.json");
        if (doc is null) return new HashSet<string>(StringComparer.Ordinal);
        using (doc)
        {
            return doc.RootElement.GetProperty("assertions").EnumerateArray()
                .Select(a => Str(a, "id")).ToHashSet(StringComparer.Ordinal);
        }
    }

    private static HashSet<string> ReceiptIds(string root)
    {
        var doc = ReadJson(root, ReceiptsRel);
        if (doc is null) return new HashSet<string>(StringComparer.Ordinal);
        using (doc)
        {
            if (!doc.RootElement.TryGetProperty("entries", out var entries))
                return new HashSet<string>(StringComparer.Ordinal);
            return entries.EnumerateArray().Select(e => Str(e, "id")).ToHashSet(StringComparer.Ordinal);
        }
    }

    private static JsonDocument? ReadJson(string root, string rel)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        return File.Exists(path) ? JsonIo.ReadFile(path) : null;
    }

    private static string Str(JsonElement element, string name)
        => element.ValueKind == JsonValueKind.Object && element.TryGetProperty(name, out var v) &&
           v.ValueKind == JsonValueKind.String
            ? v.GetString()!
            : "";

    private static List<string> StringArray(JsonElement element, string name)
    {
        if (element.ValueKind != JsonValueKind.Object || !element.TryGetProperty(name, out var v) ||
            v.ValueKind != JsonValueKind.Array)
        {
            return new List<string>();
        }
        return v.EnumerateArray().Select(x => x.ValueKind == JsonValueKind.String ? x.GetString()! : x.GetRawText())
            .ToList();
    }
}
