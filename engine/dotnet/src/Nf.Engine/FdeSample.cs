using System.Globalization;
using System.Security.Cryptography;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>scripts/fde_sample_run.py</c>（**check38 子扫描 4 · FDE 样例**）：把一次 FDE 交付跑成证据——
/// 客户 brief → 域包（AI系统域包）装配面 → 四道门 + 中游层核验 → 交付物 + 证据包。
///
/// 五道门（全部本地、确定性、无网络）：G1 产出面自洽 · G2 契约合规（T2 schema ↔ T3 data 逐对）·
/// G3 概念图健康 · G4 装配链在场 · G5 中游层成立（`nf stats --check` + `geo_export --check`）。
/// 产物（<c>docs/fde-sample/evidence/</c>）：<c>deliverable.md</c> · <c>gates.txt</c> ·
/// <c>result.jsonl</c> · <c>manifest.json</c>。
///
/// `check` 重建全部产物并与在盘逐字节比对（manifest 按 **JSON 相等、忽略 `generated_at`**）——
/// 与真源同式。**写面 `--run`（落盘）不移植**；`manifest` 里的 `generated_at` 时间戳属时钟值。
/// </summary>
public static class FdeSample
{
    public const string Pack = "community/AI系统域包";
    public const string Ev = "docs/fde-sample/evidence";
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public sealed record Result(List<string> Issues, Dictionary<string, object?> Stats)
    {
        public bool Ok => Issues.Count == 0;

        /// <summary>check38 的框法：issues 逐条 <c>[FAIL] …</c>，末行 <c>FDE 样例 子扫描：…</c>。</summary>
        public List<string> Log(string label = "FDE 样例")
        {
            var lines = Issues.Select(issue => "[FAIL] " + issue).ToList();
            lines.Add($"{label} 子扫描：{(Issues.Count == 0 ? "零缺口" : "FAIL " + Issues.Count)}");
            return lines;
        }

        public string LogDigest(string label = "FDE 样例") => ExitFaces.Digest32(Log(label));
    }

    /// <summary>真源 <c>_gates()</c>：五道门 → (rows, issues, facts)。</summary>
    private static (List<Dictionary<string, object?>> Rows, List<string> Issues,
                    Dictionary<string, object?> Facts) Gates(string root)
    {
        var rows = new List<Dictionary<string, object?>>();
        var issues = new List<string>();
        var facts = new Dictionary<string, object?>(StringComparer.Ordinal);

        // G1 产出面自洽
        var idx = ReadJson(root, $"{Pack}/outputs/INDEX.json") as Dictionary<string, object?>
                  ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var declared = ObjList(idx.GetValueOrDefault("outputs"));
        var missing = new List<object?>();
        var unparsable = new List<object?>();
        foreach (var entry in declared)
        {
            var row = entry as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var rel = PyStr(row.GetValueOrDefault("path"));
            var path = Path.Combine(root, $"{Pack}/{rel}".Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path))
            {
                missing.Add(row.GetValueOrDefault("path"));
            }
            else if (rel.EndsWith(".json", StringComparison.Ordinal))
            {
                try
                {
                    using var _ = JsonIo.ReadFile(path);
                }
                catch (Exception exc)
                {
                    unparsable.Add($"{rel} ({exc.Message})");
                }
            }
        }
        var g1 = missing.Count == 0 && unparsable.Count == 0;
        rows.Add(Row("G1_outputs_declared", g1,
            $"声明面 {declared.Count} · 缺失 {missing.Count} · 不可解析 {unparsable.Count}"));
        if (!g1) issues.Add($"G1：产出面缺失={PyScalar.PyRepr(missing)} 不可解析={PyScalar.PyRepr(unparsable)}");
        facts["declared_outputs"] = (long)declared.Count;

        // G2 契约合规（T2 schema ↔ T3 data 逐对）
        var pairs = 0L;
        var schemaFail = new List<string>();
        foreach (var entry in declared)
        {
            var row = entry as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var schemaRel = row.GetValueOrDefault("schema");
            if (!PyTruthy(schemaRel)) continue;
            var sp = Path.Combine(root, $"{Pack}/{PyStr(schemaRel)}".Replace('/', Path.DirectorySeparatorChar));
            var dp = Path.Combine(root, $"{Pack}/{PyStr(row.GetValueOrDefault("path"))}".Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(sp) || !File.Exists(dp))
            {
                schemaFail.Add($"{PyStr(row.GetValueOrDefault("path"))}：schema 或 data 缺失");
                continue;
            }
            pairs++;
            var data = ReadJsonFile(dp);
            var schema = ReadJsonFile(sp) as Dictionary<string, object?>
                         ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var errs = JsonSchemaSubset.Check(data, schema);
            if (errs.Count > 0)
                schemaFail.Add($"{PyStr(row.GetValueOrDefault("path"))}：{PyScalar.PyRepr(errs.Take(2).Cast<object?>().ToList())}");
        }
        var g2 = schemaFail.Count == 0 && pairs > 0;
        rows.Add(Row("G2_contracts", g2, $"schema↔data 对 {pairs} · 不合规 {schemaFail.Count}"));
        if (!g2) issues.Add($"G2：{PyScalar.PyRepr(schemaFail.Take(3).Cast<object?>().ToList())}");
        facts["schema_pairs"] = pairs;

        // G3 概念图健康
        var graphPath = Path.Combine(root, $"{Pack}/assets/CONCEPT_GRAPH.md".Replace('/', Path.DirectorySeparatorChar));
        var graph = ConceptGraph.LoadGraph(graphPath);
        var problems = ConceptGraph.Problems(graph);
        var nodes = ConceptGraph.NodeMeta(graph).Count;
        var order = ConceptGraph.Toposort(graph);
        var strength = ConceptGraph.ProvenanceStrength(graph);
        var g3 = problems.Count == 0;
        rows.Add(Row("G3_concept_graph", g3,
            $"节点 {nodes} · 拓扑序 {order.Count} · 问题 {problems.Count} · 证据强度 {strength}"));
        if (!g3) issues.Add($"G3：{PyScalar.PyRepr(problems.Take(3).Cast<object?>().ToList())}");
        facts["concept_nodes"] = (long)nodes;
        facts["topo_len"] = (long)order.Count;
        facts["provenance_strength"] = strength;

        // G4 装配链在场
        var need = new[]
        {
            $"{Pack}/protocol.yaml",
            $"{Pack}/pipelines/P07_AI系统域装配流管线.md",
            $"{Pack}/modules/M25_前置闭包求值.md",
            $"{Pack}/modules/M26_装载序就绪门.md",
        };
        var lack = need
            .Where(rel => !File.Exists(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))))
            .ToList();
        var g4 = lack.Count == 0;
        rows.Add(Row("G4_assembly_chain", g4, $"装配链 4 件，缺 {lack.Count}"));
        if (!g4) issues.Add($"G4：缺 {PyScalar.PyRepr(lack.Cast<object?>().ToList())}");

        // G5 中游层成立（出口自动化就位）
        var statsResult = RepoStats.Check(root);
        var geoResult = GeoExport.Check(root);
        var g5 = statsResult.Issues.Count == 0 && geoResult.Issues.Count == 0;
        rows.Add(Row("G5_midstream_exports", g5,
            $"stats.check 问题 {statsResult.Issues.Count} · geo.check 问题 {geoResult.Issues.Count}"));
        if (!g5)
        {
            issues.Add($"G5：{PyScalar.PyRepr(statsResult.Issues.Take(2).Cast<object?>().ToList())}"
                       + $" {PyScalar.PyRepr(geoResult.Issues.Take(2).Cast<object?>().ToList())}");
        }
        facts["standards"] = geoResult.Stats.GetValueOrDefault("standards") ?? 0L;
        return (rows, issues, facts);
    }

    private static Dictionary<string, object?> Row(string gate, bool ok, string detail) =>
        new(StringComparer.Ordinal)
        {
            ["gate"] = gate, ["verdict"] = ok ? "PASS" : "FAIL", ["detail"] = detail,
        };

    /// <summary>真源 <c>_deliverable()</c>：技术文档交付物原文。</summary>
    private static string Deliverable(string root, Dictionary<string, object?> facts)
    {
        var card = ReadJson(root, $"{Pack}/outputs/SYSTEM_CARD.json") as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var closure = ReadJson(root, $"{Pack}/outputs/CONCEPT_CLOSURE.json") as Dictionary<string, object?>
                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var idx = ReadJson(root, $"{Pack}/outputs/INDEX.json") as Dictionary<string, object?>
                  ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var sysmod = card.GetValueOrDefault("system") as Dictionary<string, object?>
                     ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var use = card.GetValueOrDefault("intended_use") as Dictionary<string, object?>
                  ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var upstream = string.Join(", ", ObjList(sysmod.GetValueOrDefault("upstream_models")).Select(PyStr));
        var limits = string.Join("；", ObjList(card.GetValueOrDefault("limitations"))
            .Select(x => PySlice(PyStr(x), 80)));
        var riskFramework = (card.GetValueOrDefault("risk_management") as Dictionary<string, object?>)
            ?.GetValueOrDefault("framework");
        var lines = new List<string>
        {
            "# FDE 交付样例 · AI 系统域包 → 技术文档交付物",
            "",
            "> 本文件由 `python scripts/fde_sample_run.py --run` 生成（生成物，禁止手改）。",
            "> 交付形态：技术文档（techdoc）。中游位置：NF 契约层夹在「模型/传输协议」与「客户交付物」之间。",
            "",
            "## 1. 交付对象（系统卡摘要）",
            "",
            $"- 系统：{PyStr(sysmod.GetValueOrDefault("name"))}（{PyStr(sysmod.GetValueOrDefault("id"))}"
            + $" · v{PyStr(sysmod.GetValueOrDefault("version"))}"
            + $" · {PyStr(sysmod.GetValueOrDefault("kind_of_system"))}）",
            $"- 用途：{PySlice(PyStr(use.GetValueOrDefault("purpose")), 300)}",
            $"- 模型无关：{PyStr(sysmod.GetValueOrDefault("model_agnostic"))}"
            + $" · 上游模型：{(upstream.Length > 0 ? upstream : "—")}",
            $"- 限制：{PySlice(limits, 300)}",
            $"- 风险框架：{PyOr(riskFramework, "—")}",
            "",
            "## 2. 概念闭包（装配前提）",
            "",
            $"- 目标：`{PyStr(closure.GetValueOrDefault("target"))}`"
            + $" · 闭包大小 {ObjList(closure.GetValueOrDefault("closure")).Count}"
            + $" · 装载序长度 {ObjList(closure.GetValueOrDefault("load_order")).Count}",
            $"- 概念节点 {PyStr(facts.GetValueOrDefault("concept_nodes"))}"
            + $" · 拓扑序 {PyStr(facts.GetValueOrDefault("topo_len"))}"
            + $" · 证据强度 `{PyStr(facts.GetValueOrDefault("provenance_strength"))}`",
            "",
            "## 3. 交付面清单（包自持声明）",
            "",
            "| 面 | 形态 | 档位 | 角色 |",
            "|---|---|---|---|",
        };
        foreach (var entry in ObjList(idx.GetValueOrDefault("outputs")))
        {
            var row = entry as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            lines.Add($"| `{PyStr(row.GetValueOrDefault("path"))}` | {PyStr(row.GetValueOrDefault("form"))}"
                      + $" | {PyStr(row.GetValueOrDefault("tier"))} | {PyStr(row.GetValueOrDefault("role"))} |");
        }
        lines.AddRange(new[]
        {
            "",
            "## 4. 装配步骤（FDE 侧照做）",
            "",
            $"1. 装载域包声明：`{Pack}/protocol.yaml`",
            "2. 求前置闭包：模块 `M25_前置闭包求值`（本样例结果见 §2）",
            "3. 过装载序就绪门：模块 `M26_装载序就绪门`",
            $"4. 走本包管线：`{Pack}/pipelines/P07_AI系统域装配流管线.md`",
            "5. 交付出面：按 §3 清单产出（T2 schema / T3 data）",
            "",
            "## 5. 验收判据（本样例实跑的四道门 + 中游层核验）",
            "",
            "| 门 | 判据 | 证据 |",
            "|---|---|---|",
            "| G1 | 声明产出面全部在场且可解析 | `evidence/gates.txt` |",
            "| G2 | T2 schema ↔ T3 data 逐对合规 | `evidence/gates.txt` |",
            "| G3 | 概念图健康（无环/无悬空/别名唯一/分支完备） | `evidence/gates.txt` |",
            "| G4 | 装配链四件在场可指认 | `evidence/gates.txt` |",
            "| G5 | 中游出口成立（`nf stats --check` + `geo_export --check`） | `evidence/result.jsonl` |",
            "",
            "> 复算：`python scripts/fde_sample_run.py --check`（逐字节比对本目录证据与当前仓库状态）。",
            "",
        });
        return string.Join("\n", lines);
    }

    /// <summary>真源 <c>_build()</c>：四件产物文本（<c>generated_at</c> 留空）。</summary>
    public static Dictionary<string, string> Build(string root)
    {
        var (rows, issues, facts) = Gates(root);
        var outs = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            [$"{Ev}/deliverable.md"] = Deliverable(root, facts),
        };
        var gates = new List<string>
        {
            "$ python scripts/fde_sample_run.py --run",
            $"exit={(issues.Count > 0 ? 1 : 0)}",
        };
        gates.AddRange(rows.Select(r => $"  [{r["verdict"]}] {r["gate"]} · {r["detail"]}"));
        outs[$"{Ev}/gates.txt"] = string.Join("\n", gates) + "\n";
        outs[$"{Ev}/result.jsonl"] = string.Join("\n", rows.Select(r => PythonJson.UnsortedWithSpaces(r))) + "\n";
        var inputs = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var rel in new[]
                 {
                     $"{Pack}/outputs/INDEX.json", $"{Pack}/outputs/SYSTEM_CARD.json",
                     $"{Pack}/outputs/CONCEPT_CLOSURE.json", $"{Pack}/assets/CONCEPT_GRAPH.md",
                     $"{Pack}/protocol.yaml",
                 })
        {
            inputs[rel] = Sha256Hex(File.ReadAllBytes(
                Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))));
        }
        var artifacts = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var (rel, text) in outs)
            artifacts[rel] = Sha256Hex(System.Text.Encoding.UTF8.GetBytes(text));
        var manifest = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = "nf-fde-sample/1", ["pack"] = Pack, ["facts"] = facts,
            ["inputs"] = inputs,
            ["issues"] = issues.Cast<object?>().ToList(),
            ["artifacts"] = artifacts,
            ["generated_at"] = "",
        };
        outs[$"{Ev}/manifest.json"] = PythonJson.Indented(manifest) + "\n";
        return outs;
    }

    /// <summary>真源 <c>check()</c>：产物与当前仓库状态一致（manifest 忽略 <c>generated_at</c>）。</summary>
    public static Result Check(string root)
    {
        var outs = Build(root);
        var issues = new List<string>();
        foreach (var (rel, text) in outs)
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path))
            {
                issues.Add($"缺样例证据 {rel}（跑 `fde_sample_run.py --run`）");
                continue;
            }
            if (rel.EndsWith("manifest.json", StringComparison.Ordinal))
            {
                try
                {
                    var onDisk = ReadJsonFile(path) as Dictionary<string, object?>
                                  ?? new Dictionary<string, object?>(StringComparer.Ordinal);
                    var fresh = PythonJson.ToGraph(
                        System.Text.Json.JsonDocument.Parse(text).RootElement) as Dictionary<string, object?>
                                ?? new Dictionary<string, object?>(StringComparer.Ordinal);
                    onDisk.Remove("generated_at");
                    fresh.Remove("generated_at");
                    if (PythonJson.Compact(onDisk) != PythonJson.Compact(fresh))
                        issues.Add($"{rel} 与当前仓库状态不一致（跑 `--run` 重跑）");
                }
                catch (Exception exc)
                {
                    issues.Add($"{rel} 不可解析：{exc.Message}");
                }
            }
            else if (StrictUtf8.GetString(File.ReadAllBytes(path)) != text)
            {
                issues.Add($"{rel} 与当前仓库状态不一致（跑 `--run` 重跑）");
            }
        }
        return new Result(issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["gates"] = 5L, ["evidence_files"] = (long)outs.Count,
        });
    }

    private static object? ReadJson(string root, string rel) =>
        ReadJsonFile(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)));

    private static object? ReadJsonFile(string path)
    {
        using var doc = JsonIo.ReadFile(path);
        return PythonJson.ToGraph(doc.RootElement);
    }

    private static string Sha256Hex(byte[] data) =>
        Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();

    private static string PyStr(object? value) => value switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        _ => Convert.ToString(value, CultureInfo.InvariantCulture) ?? "None",
    };

    private static string PyOr(object? value, string fallback) => PyTruthy(value) ? PyStr(value) : fallback;

    private static string PySlice(string text, int max) => PyScalar.PySlice(text, max);

    private static List<object?> ObjList(object? value) => value as List<object?> ?? new List<object?>();

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
