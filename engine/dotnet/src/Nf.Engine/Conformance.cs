using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 一致性报告（`nf conformance`）的**部分实现**：落本引擎已具备判据的 10 条契约，
/// 其余 17 条显式列出为「未移植」——**不伪造 root/verdict**（root 只覆盖已移植叶子）。
///
/// 逐契约字段（id / ok / detail / digest）与 Python 侧**逐字节对账**；digest 口径 =
/// <c>sha256(json.dumps({id, ok, detail}, sort_keys=True, ensure_ascii=False, separators=(",",":")))</c>。
///
/// 与 Python 侧的唯一已知差异：契约自身抛异常时，<c>detail</c> 前缀同为「契约执行异常：」，
/// 但尾随的异常文案来自本运行时（Python 侧来自 Python）——该分支只在执行失败时可见。
/// </summary>
public static class Conformance
{
    public const string Schema = "nf-conformance/1";

    public sealed record Contract(string Id, string Description, bool Ok, string Detail, string Digest);

    /// <summary>Python 侧 CONTRACTS 的完整 id 顺序（用于标明未移植项与保持相对次序）。</summary>
    public static readonly string[] AllContractIds =
    {
        "canonical-digest-determinism", "schema-clean", "purity-clean", "doc-kinds",
        "library-verify", "library-projection", "pipeline-dryrun", "module-signature",
        "io-types", "type-backlog", "event-backing", "declaration", "rfc-heads",
        "patterns", "endpoint-contract", "knowledge-sources", "assertions", "modeling",
        "decisions", "handover", "postmortem", "audit", "cognition", "st-quality",
        "mcp-package", "state-front", "public-surface",
    };

    private static string Sha256Hex(byte[] data) => Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();

    /// <summary>等价 Python：<c>sha256(json.dumps({id, ok, detail}, sort_keys=True, ensure_ascii=False, separators=(",",":")))</c>。</summary>
    private static string ContractDigest(string id, bool ok, string detail)
    {
        // sort_keys → digest < detail < id（按码位）；separators=(",", ":") → 无空格
        var payload = "{\"detail\":" + PythonJson.Quote(detail) +
                      ",\"id\":" + PythonJson.Quote(id) +
                      ",\"ok\":" + (ok ? "true" : "false") + "}";
        return Sha256Hex(Encoding.UTF8.GetBytes(payload));
    }

    private static byte[] Leaf(byte[] payload) => SHA256.HashData(Concat(new byte[] { 0x00 }, payload));
    private static byte[] Node(byte[] left, byte[] right) => SHA256.HashData(Concat(new byte[] { 0x01 }, left, right));

    private static byte[] Concat(params byte[][] parts)
    {
        var total = parts.Sum(p => p.Length);
        var buffer = new byte[total];
        var offset = 0;
        foreach (var part in parts)
        {
            Buffer.BlockCopy(part, 0, buffer, offset, part.Length);
            offset += part.Length;
        }
        return buffer;
    }

    private static byte[] MerkleRoot(IReadOnlyList<byte[]> leaves)
    {
        if (leaves.Count == 0) return Array.Empty<byte>();
        if (leaves.Count == 1) return leaves[0];
        var mid = 1;
        while (mid * 2 < leaves.Count) mid *= 2;
        return Node(MerkleRoot(leaves.Take(mid).ToList()), MerkleRoot(leaves.Skip(mid).ToList()));
    }

    public sealed record Report(List<Contract> Contracts, List<string> Unported, int Passed, string RootOfPorted);

    /// <summary>跑已移植契约（按 Python CONTRACTS 的相对次序）+ 列出未移植项。</summary>
    public static Report Run(string root)
    {
        var results = new Dictionary<string, (bool Ok, string Detail)>(StringComparer.Ordinal);
        foreach (var (id, runner) in Runners)
        {
            try
            {
                results[id] = runner(root);
            }
            catch (Exception exc)   // 契约自身异常 = 不通过（同 Python）
            {
                results[id] = (false, "契约执行异常：" + exc.Message);
            }
        }

        var contracts = new List<Contract>();
        var unported = new List<string>();
        foreach (var id in AllContractIds)
        {
            if (!results.TryGetValue(id, out var result))
            {
                unported.Add(id);
                continue;
            }
            var description = Descriptions.TryGetValue(id, out var d) ? d : id;
            contracts.Add(new Contract(id, description, result.Ok, result.Detail,
                ContractDigest(id, result.Ok, result.Detail)));
        }

        var leaves = contracts.Select(c =>
        {
            var payload = "{\"digest\":" + PythonJson.Quote(c.Digest) + ",\"id\":" + PythonJson.Quote(c.Id) + "}";
            return Leaf(Encoding.UTF8.GetBytes(payload));
        }).ToList();
        var rootHex = leaves.Count == 0 ? "" : Convert.ToHexString(MerkleRoot(leaves)).ToLowerInvariant();
        return new Report(contracts, unported, contracts.Count(c => c.Ok), rootHex);
    }

    /// <summary>
    /// 按同一条密码学规则（RFC 6962 式域分隔叶/节点）复算 root——用于**只把行喂进来**的
    /// 封印机制等价校验（即使部分契约未移植，也能证明 root 计算本身与 Python 逐字节一致）。
    /// </summary>
    public static string RootOf(IEnumerable<(string Id, string Digest)> rows)
    {
        var leaves = rows.Select(r => Leaf(Encoding.UTF8.GetBytes(
            "{\"digest\":" + PythonJson.Quote(r.Digest) + ",\"id\":" + PythonJson.Quote(r.Id) + "}"))).ToList();
        return leaves.Count == 0 ? "" : Convert.ToHexString(MerkleRoot(leaves)).ToLowerInvariant();
    }

    /// <summary>单契约求值（负例探针用）：返回 (ok, detail, digest)；未移植 id 抛 <see cref="ArgumentException"/>。</summary>
    public static (bool Ok, string Detail, string Digest) RunOne(string id, string root)
    {
        var runner = Runners.FirstOrDefault(r => r.Id == id);
        if (runner.Run is null) throw new ArgumentException("未移植的契约 id：" + id);
        bool ok;
        string detail;
        try
        {
            (ok, detail) = runner.Run(root);
        }
        catch (Exception exc)
        {
            (ok, detail) = (false, "契约执行异常：" + exc.Message);
        }
        return (ok, detail, ContractDigest(id, ok, detail));
    }

    /// <summary>契约 id → 求值函数（顺序同 Python <c>CONTRACTS</c>，此处只含已移植项）。</summary>
    private static readonly (string Id, Func<string, (bool Ok, string Detail)> Run)[] Runners =
    {
        ("canonical-digest-determinism", CanonicalDeterminism),
        ("doc-kinds", DocKindsContract),
        ("schema-clean", SchemaContract),
        ("library-verify", LibraryVerify),
        ("library-projection", LibraryProjection),
        ("pipeline-dryrun", PipelineDryrunContract),
        ("module-signature", ModuleSignatureContract),
        ("io-types", IoTypesContract),
        ("event-backing", EventBackingContract),
        ("type-backlog", TypeBacklogContract),
        ("declaration", DeclarationContract),
        ("rfc-heads", RfcHeads),
        ("patterns", PatternsContract),
        ("endpoint-contract", EndpointContractHandler),
        ("knowledge-sources", KnowledgeSourcesContract),
        ("assertions", AssertionsContract),
        ("modeling", ModelingContract),
        ("decisions", DecisionsContract),
        ("cognition", CognitionContract),
        ("handover", HandoverContract),
        ("postmortem", PostmortemContract),
        ("audit", AuditContract),
        ("st-quality", StQualityContract),
        ("mcp-package", McpPackageContract),
        ("state-front", StateFrontContract),
        ("public-surface", PublicSurface),
    };

    private static readonly Dictionary<string, string> Descriptions = new(StringComparer.Ordinal)
    {
        ["canonical-digest-determinism"] = "规范化摘要可复现",
        ["doc-kinds"] = DocHygiene.ContractDescription,
        ["schema-clean"] = SchemaLint.ContractDescription,
        ["library-verify"] = "馆藏 frontmatter 真源",
        ["library-projection"] = "INDEX/ALIAS 投影一致",
        ["rfc-heads"] = "协议件版本史头",
        ["patterns"] = "实践包品类",
        ["assertions"] = "数据化断言表（形状类断言数据化）",
        ["modeling"] = "内容建模三件（词表/规范说明件/数据契约）",
        ["decisions"] = "决策记录（ADR：不可改 + 取代链）",
        ["cognition"] = "认知族（术语表 + 执行分档）",
        ["declaration"] = ConformanceDecl.ContractDescription,
        ["st-quality"] = StQuality.ContractDescription,
        ["mcp-package"] = McpPackage.ContractDescription,
        ["state-front"] = StateFront.ContractDescription,
        ["handover"] = Handover.ContractDescription,
        ["postmortem"] = Postmortem.ContractDescription,
        ["audit"] = Audit.ContractDescription,
        ["endpoint-contract"] = EndpointContract.ContractDescription,
        ["module-signature"] = ModuleSignature.ContractDescription,
        ["event-backing"] = EventBacking.ContractDescription,
        ["type-backlog"] = TypeBacklog.ContractDescription,
        ["io-types"] = IoTypes.ContractDescription,
        ["pipeline-dryrun"] = PipelineDryrun.ContractDescription,
        ["knowledge-sources"] = KnowledgeSources.ContractDescription,
        ["public-surface"] = "公开导出面零泄漏",
    };

    private static readonly string[] TextSuffixes = { ".md", ".json", ".yaml", ".yml", ".txt" };
    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>公开导出面泄漏判据：绝对路径 / 内部件路径不得出现在对外产物里。</summary>
    private static readonly Regex AbsolutePathRe = new(
        @"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/Users/|/home/[a-z]|\\Users\\",
        RegexOptions.CultureInvariant);

    private static (bool, string) CanonicalDeterminism(string root)
    {
        // 与 Python 侧同形的「两个插入序 → 同一规范串」探针；另钉住跨实现字节（非 ASCII 不转义）：
        // attest.canonical({"b":2,"a":1}) == b'{"a":1,"b":2}'；键按 Unicode 码位升序（'a' < '名'）。
        var first = PythonJson.Compact(new Dictionary<string, object?>(StringComparer.Ordinal)
            { ["b"] = 2L, ["a"] = 1L });
        var second = PythonJson.Compact(new Dictionary<string, object?>(StringComparer.Ordinal)
            { ["a"] = 1L, ["b"] = 2L });
        var unicode = PythonJson.Compact(new Dictionary<string, object?>(StringComparer.Ordinal)
            { ["名"] = "值", ["a"] = 1L });
        var ok = first == second && first == "{\"a\":1,\"b\":2}" && unicode == "{\"a\":1,\"名\":\"值\"}";
        return (ok, ok ? "canonical digest 两遍一致" : "不一致");
    }

    private static (bool, string) DocKindsContract(string root) => DocHygiene.Contract(root);

    private static (bool, string) SchemaContract(string root) => SchemaLint.Contract(root);

    private static (bool, string) DeclarationContract(string root) => ConformanceDecl.Contract(root);

    private static (bool, string) StQualityContract(string root) => StQuality.Contract(root);

    private static (bool, string) McpPackageContract(string root) => McpPackage.Contract(root);

    private static (bool, string) StateFrontContract(string root) => StateFront.Contract(root);

    private static (bool, string) HandoverContract(string root) => Handover.Contract(root);

    private static (bool, string) PostmortemContract(string root) => Postmortem.Contract(root);

    private static (bool, string) AuditContract(string root) => Audit.Contract(root);

    private static (bool, string) EndpointContractHandler(string root) => EndpointContract.Contract(root);

    private static (bool, string) ModuleSignatureContract(string root) => ModuleSignature.Contract(root);

    private static (bool, string) EventBackingContract(string root) => EventBacking.Contract(root);

    private static (bool, string) TypeBacklogContract(string root) => TypeBacklog.Contract(root);

    private static (bool, string) IoTypesContract(string root) => IoTypes.Contract(root);

    private static (bool, string) PipelineDryrunContract(string root) => PipelineDryrun.Contract(root);

    private static (bool, string) KnowledgeSourcesContract(string root) => KnowledgeSources.Contract(root);

    private static (bool, string) RfcHeads(string root)
    {
        var (issues, _, stats) = Rfc.Scan(root);
        if (issues.Count > 0) return (false, string.Join("; ", issues.Take(2)));
        var docs = stats.TryGetValue("docs", out var d) ? d : 0;
        var chains = stats.TryGetValue("chains", out var c) ? c : 0;
        return (true, $"RFC 件 {docs} · 链 {chains}");
    }

    private static (bool, string) PatternsContract(string root)
    {
        var (issues, _, stats) = Patterns.Scan(root);
        issues.AddRange(Patterns.CheckProjection(root));
        if (issues.Count > 0) return (false, string.Join("; ", issues.Take(2)));
        var count = stats.TryGetValue("patterns", out var p) ? p : 0;
        return (true, $"实践包 {count} 条（格式/可证/投影）");
    }

    private static (bool, string) PublicSurface(string root)
    {
        var bad = new List<string>();
        // 与 Python EXPORT_GLOBS 同序（递归面在前、单层面在后）——只影响取前两条时的措辞
        var groups = new (string Dir, SearchOption Depth)[]
        {
            ("desktop/tests/fixtures/external", SearchOption.AllDirectories),
            ("docs/external-validation-assets", SearchOption.TopDirectoryOnly),
        };
        foreach (var (dirRel, depth) in groups)
        {
            var dir = Path.Combine(root, dirRel.Replace('/', Path.DirectorySeparatorChar));
            if (!Directory.Exists(dir)) continue;
            foreach (var file in Directory.EnumerateFiles(dir, "*", depth)
                         .OrderBy(f => f, StringComparer.Ordinal))
            {
                if (Array.IndexOf(TextSuffixes, Path.GetExtension(file)) < 0) continue;
                string text;
                try
                {
                    text = StrictUtf8.GetString(File.ReadAllBytes(file));
                }
                catch (IOException) { continue; }                    // 不可读 → 跳过（同 Python 的 OSError）
                catch (DecoderFallbackException) { continue; }        // 非 UTF-8 → 跳过（同 Python 的 UnicodeDecodeError）
                if (AbsolutePathRe.IsMatch(text)) bad.Add($"{Rel(root, file)} 含绝对路径");
            }
        }
        return bad.Count == 0 ? (true, "公开导出面零泄漏") : (false, string.Join("; ", bad.Take(2)));
    }

    private static string Rel(string root, string full)
        => Path.GetRelativePath(root, full).Replace('\\', '/');

    private static (bool, string) LibraryVerify(string root)
    {
        var result = Library.Verify(root);
        return (result.Issues.Count == 0,
            result.Issues.Count == 0 ? "馆藏 frontmatter 真源零 FAIL" : string.Join("; ", result.Issues.Take(2)));
    }

    private static (bool, string) LibraryProjection(string root)
    {
        var issues = Library.CheckProjection(root);
        return (issues.Count == 0, issues.Count == 0 ? "投影一致" : string.Join("; ", issues.Take(2)));
    }

    private static (bool, string) AssertionsContract(string root)
    {
        var result = Assertions.Run(root);
        var passed = result.Results.Cast<Dictionary<string, object?>>().Count(r => r["ok"] is true);
        var detail = $"断言 {result.Results.Count} 条（通过 {passed}）· kind 封闭集 4 种";
        return (result.Issues.Count == 0, result.Issues.Count == 0 ? detail : string.Join("; ", result.Issues.Take(2)));
    }

    private static (bool, string) ModelingContract(string root)
    {
        var result = Modeling.Run(root);
        // 缺件时 Stats 里可能没有该子表——Python 用 stats.get(k, {}) 兜底，
        // 引擎必须同样给「可读判定」而不是抛 KeyNotFoundException（敌意输入探针实测差异）
        var v = Sub(result.Stats, "vocab");
        var n = Sub(result.Stats, "normative");
        var d = Sub(result.Stats, "contracts");
        var detail = $"词表 {Num(v, "schemes")} · 规范件 {Num(n, "normative")} / 说明件 {Num(n, "informative_files")} · 数据契约 {Num(d, "contracts")}";
        return (result.Issues.Count == 0, result.Issues.Count == 0 ? detail : string.Join("; ", result.Issues.Take(2)));
    }

    private static (bool, string) DecisionsContract(string root)
    {
        var result = Decisions.Verify(root);
        var issues = result.Issues.Concat(result.Projection).ToList();
        var detail = $"决策 {Num(result.Stats, "decisions")} 条（accepted {Num(result.Stats, "accepted")} · 取代链 {Num(result.Stats, "chains")}）";
        return (issues.Count == 0, issues.Count == 0 ? detail : string.Join("; ", issues.Take(2)));
    }

    private static (bool, string) CognitionContract(string root)
    {
        var result = Cognition.Run(root);
        var g = Sub(result.Stats, "glossary");
        var m = Sub(result.Stats, "modes");
        var detail = $"术语 {Num(g, "terms")} 条（使用面 {Num(g, "uses")}）· 执行档 {Num(m, "modes")}（合格实例 {Num(m, "instances_ok")}）";
        return (result.Issues.Count == 0, result.Issues.Count == 0 ? detail : string.Join("; ", result.Issues.Take(2)));
    }

    /// <summary>等价 Python <c>stats.get(key, {})</c>：缺键或类型不符都退回空表，绝不抛。</summary>
    private static Dictionary<string, object?> Sub(Dictionary<string, object?> stats, string key)
        => stats.TryGetValue(key, out var v) && v is Dictionary<string, object?> map
            ? map
            : new Dictionary<string, object?>(StringComparer.Ordinal);

    /// <summary>等价 Python <c>stats.get(key, 0)</c>：缺键退 0（渲染成 <c>0</c>）。</summary>
    private static object? Num(Dictionary<string, object?> stats, string key)
        => stats.TryGetValue(key, out var v) ? v : 0;
}
