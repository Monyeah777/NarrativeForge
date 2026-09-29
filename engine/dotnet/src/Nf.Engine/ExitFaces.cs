using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Nf.Engine;

// 复刻两处**出口/派生面**的只读判据：
//
// ① `scripts/interop_thirdparty_kit.py::check`（**他证通道** · check38 第二腿）：回填状态表
//    （每面一行 11 列）——已标 verdict 的行必须给全 tool_version / run_by / run_at / output_sha256，
//    且 sha256 必须是 **64 位十六进制**（「不可用『看起来通过』代替」）；`not-applicable` 的面必须写理由；
//    每个面都必须有行（含 not-applicable）。**只读面**，`--emit` / `record` 是写面不移植。
// ② check33 第 14 条（**互操作入仓一致性**）：`results/interop/<kind>.json` 与**实时派生**逐字节比对——
//    入仓面是**派生投影，不是真源**（改一个字符都该红）。
public static class ExitFaces
{
    public const string ThirdPartyDocRel = "docs/interop-thirdparty.md";
    public const string ThirdPartyStatusRel = "results/interop-thirdparty-status.md";
    public const string Unfilled = "未回填（通道就绪）";
    public const string InteropDirRel = "results/interop";

    /// <summary>真源 <c>FACES</c> 的 (id, kind) 镜像（14 面）。</summary>
    public static readonly (string Id, string Kind)[] Faces =
    {
        ("mcp", "peer-consumption"), ("ccv3", "peer-consumption"),
        ("openapi", "official-cli"), ("asyncapi", "official-cli"), ("sbom", "official-cli"),
        ("cyclonedx", "official-cli"), ("slsa", "shape-only"), ("intoto", "shape-only"),
        ("vc", "shape-only"), ("prov", "shape-only"),
        ("a2a", "not-applicable"), ("c2pa", "not-applicable"),
        ("cid", "official-cli"), ("decisions", "not-applicable"),
    };

    private static readonly Regex Sha256Re = new("^[0-9a-f]{64}$", RegexOptions.Compiled);

    public sealed record Result(List<string> Issues, Dictionary<string, object?> Stats)
    {
        public bool Ok => Issues.Count == 0;

        /// <summary>
        /// 按 **check38 第二腿**的框法落日志：issues 逐条 <c>[FAIL] …</c>，末行
        /// <c>&lt;label&gt; 子扫描：&lt;零缺口 | FAIL N&gt;</c>（真源 <c>interop_thirdparty_check</c> 同式）。
        /// 摘要只在**渲染行**上算——真源以行为单位比对，字段宽度/排序不影响结论。
        /// </summary>
        public List<string> Log(string label = "他证通道")
        {
            var lines = Issues.Select(issue => "[FAIL] " + issue).ToList();
            lines.Add($"{label} 子扫描：{(Issues.Count == 0 ? "零缺口" : "FAIL " + Issues.Count)}");
            return lines;
        }

        public string LogDigest(string label = "他证通道") => Digest32(Log(label));
    }

    /// <summary>真源口径：<c>sha256("\n".join(渲染行))[:32]</c>。</summary>
    public static string Digest32(IEnumerable<string> lines) =>
        Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(
            Encoding.UTF8.GetBytes(string.Join("\n", lines)))).ToLowerInvariant()[..32];

    /// <summary>他证通道：回填状态表体检（真源 <c>interop_thirdparty_kit.check</c>）。</summary>
    public static Result ThirdPartyCheck(string root)
    {
        var issues = new List<string>();
        var statusPath = Path.Combine(root, ThirdPartyStatusRel.Replace('/', Path.DirectorySeparatorChar));
        var docPath = Path.Combine(root, ThirdPartyDocRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(statusPath))
            return new Result(new List<string> { $"缺回填状态表 {ThirdPartyStatusRel}（跑 --emit）" },
                              new Dictionary<string, object?>(StringComparer.Ordinal));
        if (!File.Exists(docPath)) issues.Add($"缺说明页 {ThirdPartyDocRel}（跑 --emit）");

        var text = File.ReadAllText(statusPath, new UTF8Encoding(false));
        var seen = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        var filled = 0;
        foreach (var line in KnowledgeSig.SplitLines(text))
        {
            if (!line.StartsWith("| `", StringComparison.Ordinal)) continue;
            var cells = line.Trim().Trim('|').Split('|').Select(c => c.Trim()).ToList();
            if (cells.Count < 11)
            {
                issues.Add($"状态表行列数不足（{cells.Count}）：{PyScalar.PySlice(line, 60)}");
                continue;
            }
            var fid = cells[0].Trim('`');
            seen[fid] = cells;
            var verdict = cells[9];
            if (verdict.Length > 0 && verdict != Unfilled)
            {
                filled++;
                var need = new (string Key, string Value)[]
                {
                    ("tool_version", cells[5]), ("run_by", cells[6]),
                    ("run_at", cells[7]), ("output_sha256", cells[8]),
                };
                var miss = need.Where(n => n.Value.Length == 0).Select(n => n.Key).ToList();
                if (miss.Count > 0)
                    issues.Add($"{fid} 已标 verdict={verdict} 但缺字段：{PyScalar.PyRepr(miss.Cast<object?>().ToList())}");
                if (cells[8].Length > 0 && !Sha256Re.IsMatch(cells[8]))
                    issues.Add($"{fid} 的 output_sha256 不是 64 位十六进制（不可用「看起来通过」代替）");
            }
        }
        foreach (var (id, kind) in Faces)
        {
            if (!seen.TryGetValue(id, out var cells))
                issues.Add($"状态表缺面：{id}（每个互操作面都必须有一行，含 not-applicable）");
            else if (cells[10].Length == 0 && kind == "not-applicable")
                issues.Add($"{id} 标为 not-applicable 但 note 未写理由");
        }
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["faces"] = (long)Faces.Length,
            ["rows"] = (long)seen.Count,
            ["filled"] = (long)filled,
            ["unfilled"] = (long)(Faces.Length - filled),
        };
        return new Result(issues, stats);
    }

    /// <summary>
    /// check33 第 14 条：互操作**入仓面**（<c>results/interop/*.json</c>）与实时派生逐字节一致。
    /// 缺件与漂移各汇总成**一条** issue（真源同式：逗号连接 kind 名）。
    /// </summary>
    public static List<string> InteropInRepoIssues(string root)
    {
        var issues = new List<string>();
        var dir = Path.Combine(root, InteropDirRel.Replace('/', Path.DirectorySeparatorChar));
        if (!Directory.Exists(dir)) return issues;
        var missing = new List<string>();
        var drift = new List<string>();
        foreach (var (kind, _) in Interop.Kinds)
        {
            var path = Path.Combine(dir, kind + ".json");
            if (!File.Exists(path))
            {
                missing.Add(kind);
                continue;
            }
            if (!File.ReadAllBytes(path).SequenceEqual(Interop.Render(kind, root))) drift.Add(kind);
        }
        if (missing.Count > 0)
            issues.Add($"互操作入仓面缺件：{string.Join(",", missing)}（修复指引：nf interop --all --out results/interop）");
        if (drift.Count > 0)
            issues.Add($"互操作入仓面与实时派生不一致：{string.Join(",", drift)}"
                       + "（修复指引：重跑 nf interop --all ——入仓面是派生投影，不是真源）");
        return issues;
    }
}
