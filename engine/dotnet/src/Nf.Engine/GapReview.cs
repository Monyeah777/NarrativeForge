using System.Globalization;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/gap_review.py</c>（**`nf review`**）：缺口逐行审查 = **决策模型逐行判 + 确定性规则复核**
/// 双轨（缺一不进修复清单）。三类行级候选：① `unharvestable-payload`（正文有类型证据但收割器不认）·
/// ② `silent-skip`（`except → pass/continue` 且无说明）· ③ `missing-quality-rule`（规范件未登记数据契约）；
/// 另有 ④ `payload-no-evidence`（只有字段名、无类型证据 → **只挂账**，不可靠改代码修）。
///
/// 双轨纪律照抄真源：模型判定（`noul` 缺口概率 / `score` 严重度）**只用于排序与提示**，
/// 进 `fixable` 必须另有确定性证据；stub 适配器**无判定能力**，本轮一律以证据为准
/// （`model_gap_p`/`model_severity` 置 `None` 并写 `model_note`）。
/// </summary>
public static class GapReview
{
    public const string Schema = "nf-gap-review/1";
    public const double ModelThreshold = 0.5;
    private static readonly Regex PayloadLineRe = new(@"payload\s*:\s*\{([^}]*)\}");
    private static readonly Regex ExceptRe = new(@"^\s*except\b");
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public static List<Dictionary<string, object?>> PayloadCandidates(string root)
    {
        var outList = new List<Dictionary<string, object?>>();
        foreach (var rel in ModuleDocs.Files(root))
        {
            var text = StrictUtf8.GetString(
                File.ReadAllBytes(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))));
            var found = PayloadHarvest.HarvestDoc(text);
            var known = new HashSet<string>(StringComparer.Ordinal);
            foreach (var fmap in found.Values)
            {
                foreach (var (key, value) in fmap)
                {
                    if (value != "untyped") known.Add(key);
                }
            }
            var lines = KnowledgeSig.SplitLines(text);
            for (var index = 0; index < lines.Count; index++)
            {
                var line = lines[index];
                var match = PayloadLineRe.Match(line);
                if (!match.Success) continue;
                var kind = "";
                var missing = new List<string>();
                foreach (var tok in PayloadHarvest.SplitTopLevel(match.Groups[1].Value))
                {
                    var (name, type) = PayloadHarvest.FieldType(tok);
                    if (name.Length == 0 || known.Contains(name)) continue;
                    missing.Add(name);
                    if (type.Length > 0 && type != "untyped") kind = "unharvestable-payload";
                }
                if (missing.Count == 0) continue;
                if (kind.Length == 0) kind = "payload-no-evidence";
                outList.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["class"] = kind, ["file"] = rel, ["line"] = (long)(index + 1),
                    ["detail"] = "未定型字段：" + string.Join("、", missing.Take(6)),
                    ["snippet"] = PySlice(line.Trim(), 160),
                });
            }
        }
        return outList;
    }

    public static List<Dictionary<string, object?>> SilentSkipCandidates(string root)
    {
        var outList = new List<Dictionary<string, object?>>();
        var files = new List<string>();
        foreach (var pattern in new[] { "desktop/src/core/*.py", "scripts/*.py" })
        {
            var full = Path.Combine(root, pattern.Replace('/', Path.DirectorySeparatorChar));
            var parent = Path.GetDirectoryName(full)!;
            if (!Directory.Exists(parent)) continue;
            files.AddRange(Directory.GetFiles(parent, Path.GetFileName(full))
                .OrderBy(f => f, StringComparer.Ordinal));
        }
        foreach (var file in files)
        {
            var lines = KnowledgeSig.SplitLines(StrictUtf8.GetString(File.ReadAllBytes(file)));
            for (var i = 0; i < lines.Count; i++)
            {
                var line = lines[i];
                if (!ExceptRe.IsMatch(line)) continue;
                var next = lines.Skip(i + 1).Take(2).Select(l => l.Trim()).ToList();
                if (next.Count == 0 || (next[0] != "pass" && next[0] != "continue")) continue;
                var prev = i > 0 ? lines[i - 1].Trim() : "";
                // 说明可以写在上一行，也可以内联在 except 行（仓库既有写法）
                if (prev.StartsWith('#')) continue;
                var afterColon = line.Contains(':') ? line.Split(':', 2)[1] : line;
                if (afterColon.Contains('#')) continue;
                outList.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["class"] = "silent-skip",
                    ["file"] = Posix(root, file),
                    ["line"] = (long)(i + 2),
                    ["detail"] = $"except → {next[0]} 且无说明",
                    ["snippet"] = $"{PySlice(line.Trim(), 80)} / {next[0]}",
                });
            }
        }
        return outList;
    }

    public static List<Dictionary<string, object?>> QualityRuleCandidates(string root)
    {
        var outList = new List<Dictionary<string, object?>>();
        var contracts = ReadMap(root, "protocol/data_contracts.json");
        var normative = ReadMap(root, "protocol/normative.json");
        var registered = new HashSet<string>(StringComparer.Ordinal);
        foreach (var contract in ObjList(contracts.GetValueOrDefault("contracts")))
        {
            if (contract is Dictionary<string, object?> row && row.GetValueOrDefault("artifact") is string artifact)
                registered.Add(artifact);
        }
        foreach (var item in ObjList(normative.GetValueOrDefault("normative")))
        {
            var row = item as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var path = PyStr(row.GetValueOrDefault("path"));
            if (path.EndsWith(".json", StringComparison.Ordinal) && !registered.Contains(path)
                && !PyTruthy(row.GetValueOrDefault("covered_by")))
            {
                outList.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["class"] = "missing-quality-rule", ["file"] = "protocol/normative.json",
                    ["line"] = 0L, ["detail"] = $"规范件未登记数据契约：{path}", ["snippet"] = path,
                });
            }
        }
        return outList;
    }

    /// <summary>行级候选（机械预筛，确定性排序：class → file → line）。</summary>
    public static List<Dictionary<string, object?>> Candidates(string root, IReadOnlyList<string>? classes = null)
    {
        var rows = new List<Dictionary<string, object?>>();
        rows.AddRange(PayloadCandidates(root));
        rows.AddRange(SilentSkipCandidates(root));
        rows.AddRange(QualityRuleCandidates(root));
        if (classes is { Count: > 0 })
        {
            var scope = new HashSet<string>(classes, StringComparer.Ordinal);
            rows = rows.Where(r => scope.Contains(PyStr(r.GetValueOrDefault("class")))).ToList();
        }
        return rows
            .OrderBy(r => PyStr(r.GetValueOrDefault("class")), StringComparer.Ordinal)
            .ThenBy(r => PyStr(r.GetValueOrDefault("file")), StringComparer.Ordinal)
            .ThenBy(r => Convert.ToInt64(r.GetValueOrDefault("line") ?? 0L))
            .ToList();
    }

    /// <summary>确定性复核：该类缺口能否由规则证实（空串 = 无证据 → 不进修复清单）。</summary>
    public static string Evidence(string root, Dictionary<string, object?> row)
    {
        var cls = PyStr(row.GetValueOrDefault("class"));
        var rel = PyStr(row.GetValueOrDefault("file"));
        var line = (int)Convert.ToInt64(row.GetValueOrDefault("line") ?? 0L);
        if (cls == "unharvestable-payload")
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path)) return "";
            var lines = KnowledgeSig.SplitLines(StrictUtf8.GetString(File.ReadAllBytes(path)));
            if (line - 1 < 0 || line - 1 >= lines.Count) return "";
            var text = lines[line - 1];
            return text.Contains("payload", StringComparison.Ordinal)
                ? "可证：该 payload 行含字段/类型信息，但收割器 `harvest_doc` 只认 "
                  + "`event:`/`name:`/`publish:` 标记，此行未提供 → 类型证据不可收割"
                : "";
        }
        if (cls == "silent-skip")
        {
            var lines = KnowledgeSig.SplitLines(StrictUtf8.GetString(
                File.ReadAllBytes(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)))));
            var idx = line - 2;
            if (idx >= 0 && idx < lines.Count && ExceptRe.IsMatch(lines[idx]))
            {
                var prev = idx > 0 ? lines[idx - 1].Trim() : "";
                var afterColon = lines[idx].Contains(':') ? lines[idx].Split(':', 2)[1] : lines[idx];
                if (!prev.StartsWith('#') && !afterColon.Contains('#'))
                    return "可证：except 后直接 pass/continue，且前一行无说明（静默吞错面）";
            }
            return "";
        }
        if (cls == "missing-quality-rule")
        {
            var contracts = ReadMap(root, "protocol/data_contracts.json");
            var registered = new HashSet<string>(StringComparer.Ordinal);
            foreach (var contract in ObjList(contracts.GetValueOrDefault("contracts")))
            {
                if (contract is Dictionary<string, object?> entry && entry.GetValueOrDefault("artifact") is string artifact)
                    registered.Add(artifact);
            }
            return registered.Contains(PyStr(row.GetValueOrDefault("snippet")))
                ? ""
                : "可证：该规范件在 normative 名单却不在数据契约登记表（无 quality_rule/owner/freshness）";
        }
        // payload-no-evidence：「缺证据」类不能靠改代码修（类型要模块作者给）→ 只挂账，不进修复清单
        return "";
    }

    /// <summary>模型逐行判定 + 证据复核 → fixable / suspected 两张清单。</summary>
    public static Dictionary<string, object?> Review(string root, string adapter = "stub", string endpoint = "",
                                                     int limit = 0, int batch = 8)
    {
        var rows = Candidates(root);
        if (limit > 0) rows = rows.Take(limit).ToList();
        var verdicts = new List<Dictionary<string, object?>>();
        var step = Math.Max(1, batch);
        for (var start = 0; start < rows.Count; start += step)
        {
            var chunk = rows.Skip(start).Take(step).ToList();
            var stateItems = new List<object?>();
            for (var i = 0; i < chunk.Count; i++)
            {
                stateItems.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["i"] = (long)i, ["class"] = chunk[i]["class"], ["file"] = chunk[i]["file"],
                    ["line"] = chunk[i]["line"], ["snippet"] = chunk[i]["snippet"],
                    ["detail"] = chunk[i]["detail"],
                });
            }
            var questions = new Dictionary<string, object?>(StringComparer.Ordinal);
            for (var i = 0; i < chunk.Count; i++)
            {
                questions[$"gap:{i}"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "noul",
                    ["instructions"] = $"第 {i} 条（{PyStr(chunk[i]["class"])} @ {PyStr(chunk[i]["file"])}"
                                       + $":{PyStr(chunk[i]["line"])}）是否构成**可证缺口**：{PyStr(chunk[i]["detail"])}",
                };
                questions[$"sev:{i}"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "score", ["levels"] = new List<object?> { "低", "中", "高" },
                    ["instructions"] = $"第 {i} 条若成立，严重度如何",
                };
            }
            var output = DecisionLayer.Decide(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["state"] = PythonJson.UnsortedWithSpaces(stateItems),
                ["questions"] = questions,
            }, adapter, endpoint, "", root);
            var answers = output.GetValueOrDefault("answers") as Dictionary<string, object?>
                          ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            for (var i = 0; i < chunk.Count; i++)
            {
                var row = new Dictionary<string, object?>(chunk[i], StringComparer.Ordinal);
                if (PyStr(output.GetValueOrDefault("status")) == "ok")
                {
                    row["model_gap_p"] = (answers.GetValueOrDefault($"gap:{i}") as Dictionary<string, object?>)
                        ?.GetValueOrDefault("p");
                    row["model_severity"] = (answers.GetValueOrDefault($"sev:{i}") as Dictionary<string, object?>)
                        ?.GetValueOrDefault("value");
                }
                else
                {
                    row["model_gap_p"] = null;
                    row["model_severity"] = null;
                    row["model_error"] = output.GetValueOrDefault("reason");
                }
                if (adapter == "stub")
                {
                    // stub 无判定能力（规则式）：不得当否决票——本轮以证据为准
                    row["model_gap_p"] = null;
                    row["model_severity"] = null;
                    row["model_note"] = "stub 无判定能力：本轮以确定性证据为准";
                }
                var evidence = Evidence(root, row);
                row["evidence"] = evidence;
                var gapP = row.GetValueOrDefault("model_gap_p");
                if (evidence.Length > 0 && (gapP is null
                                            || Convert.ToDouble(gapP, CultureInfo.InvariantCulture) >= ModelThreshold))
                    row["verdict"] = "fixable";
                else if (gapP is not null && evidence.Length == 0)
                    row["verdict"] = "suspected";
                else
                    row["verdict"] = "not-a-gap";
                verdicts.Add(row);
            }
        }
        var byClass = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var row in verdicts)
        {
            var cls = PyStr(row.GetValueOrDefault("class"));
            byClass[cls] = (long)(byClass.TryGetValue(cls, out var n) ? Convert.ToInt64(n) : 0L) + 1;
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = Schema, ["adapter"] = adapter, ["scanned"] = (long)verdicts.Count,
            ["by_class"] = byClass,
            ["fixable"] = verdicts.Where(r => PyStr(r.GetValueOrDefault("verdict")) == "fixable")
                .Select(r => (object?)r).ToList(),
            ["suspected"] = verdicts.Where(r => PyStr(r.GetValueOrDefault("verdict")) == "suspected")
                .Select(r => (object?)r).ToList(),
            ["model_meta"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["calibrated"] = adapter != "stub", ["threshold"] = ModelThreshold,
                ["note"] = "模型判定只用于排序；进修复清单必须另有确定性证据",
            },
        };
    }

    /// <summary>真源 <c>summary(doc)</c> 原文（<c>by_class</c> 走 Python repr）。</summary>
    public static string Summary(Dictionary<string, object?> doc) =>
        $"扫描 {PyStr(doc.GetValueOrDefault("scanned"))} 行"
        + $" · 可修 {ObjList(doc.GetValueOrDefault("fixable")).Count}（有证据）"
        + $"· 模型怀疑无证据 {ObjList(doc.GetValueOrDefault("suspected")).Count}"
        + $" · 分类 {PyScalar.PyRepr(doc.GetValueOrDefault("by_class"))}";

    private static Dictionary<string, object?> ReadMap(string root, string rel)
    {
        using var doc = JsonIo.ReadFile(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)));
        return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
               ?? new Dictionary<string, object?>(StringComparer.Ordinal);
    }

    private static string Posix(string root, string full) =>
        Path.GetRelativePath(root, full).Replace('\\', '/');

    private static string PySlice(string text, int max) => PyScalar.PySlice(text, max);

    private static List<object?> ObjList(object? value) => value as List<object?> ?? new List<object?>();

    private static string PyStr(object? value) => value switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        _ => Convert.ToString(value, CultureInfo.InvariantCulture) ?? "None",
    };

    private static bool PyTruthy(object? value) => value switch
    {
        null => false,
        bool b => b,
        long l => l != 0,
        int i => i != 0,
        double d => d != 0,
        string s => s.Length > 0,
        List<object?> list => list.Count > 0,
        Dictionary<string, object?> map => map.Count > 0,
        _ => true,
    };
}
