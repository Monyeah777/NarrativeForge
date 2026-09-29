using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 互操作导出面（复刻 <c>core/interop_export.py</c>）：把既有声明件**纯派生**为外部标准工具可读的文档。
///
/// 定位纪律：**不新增真源**——所有字段从既有声明件实时算出；门禁断言的是「覆盖完整 + 形状合法 + 确定性」。
/// 本件按片推进：已移植的形状在 <see cref="PortedKinds"/> 里列明；未移植的 <see cref="Render"/> 会**明确抛出**
/// （不静默给半个面、不冒充等价）——与 `purity-clean` 的范围裁定同一条纪律。
/// </summary>
public static class Interop
{
    public const string ContractRel = "protocol/endpoint_contract.json";
    public const string EventsRel = "protocol/event_registry.json";
    public const string ExternalEventsRel = "protocol/external_events.json";
    public const string ReceiptsRel = "protocol/RECEIPTS.json";
    public const string LicenseName = "MIT";

    /// <summary>12 种导出形状（键序 = 真源 <c>KINDS</c> 的声明序，<c>--list</c> 逐行按此序）。</summary>
    public static readonly (string Id, string Label)[] Kinds =
    {
        ("openapi", "OpenAPI 3.1 服务端点文档"),
        ("asyncapi", "AsyncAPI 3.0 事件通道文档（含 CloudEvents 属性）"),
        ("intoto", "in-toto Statement v1（协议层回执）"),
        ("sbom", "SPDX 2.3 SBOM（依赖登记面）"),
        ("slsa", "SLSA Provenance v1（本地门禁构建声明）"),
        ("a2a", "A2A Agent Card（能力面投影）"),
        ("prov", "PROV-O 溯源图（资产 / 馆藏 / 消化 / 回执）"),
        ("cyclonedx", "CycloneDX 1.5 SBOM（与 SPDX 面同源）"),
        ("vc", "W3C VC 2.0 形状（未签名，含状态注记）"),
        ("c2pa", "C2PA JSON 清单形状（未封装/未签名）"),
        ("cid", "CIDv1 内容寻址索引（multiformats）"),
        ("decisions", "决策面（决策能力 + 公开裁决索引；工单不入公开面）"),
    };

    /// <summary>已移植的导出形状（未列的 kind 在 <see cref="Render"/> 里明确拒绝）。</summary>
    public static readonly string[] PortedKinds =
    {
        "openapi", "asyncapi", "intoto", "sbom", "slsa", "a2a", "prov",
        "cyclonedx", "vc", "c2pa", "cid", "decisions",
    };

    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);
    private static readonly Regex DateRe = new(@"20\d\d-\d\d-\d\d", RegexOptions.CultureInvariant);
    private static readonly Regex VerifyVersionRe = new(@"# 版本\s*:\s*(v[0-9.]+)", RegexOptions.CultureInvariant);
    private static readonly Regex Sha256Re = new(@"^[0-9a-f]{64}$", RegexOptions.CultureInvariant);
    private static readonly Regex ExpectedChecksRe = new(@"^\s*EXPECTED_CHECKS\s*=\s*([0-9]+)", RegexOptions.Multiline);
    private static readonly Regex ExpectedPassRe = new(@"^\s*EXPECTED_PASS\s*=\s*([0-9]+)", RegexOptions.Multiline);

    /// <summary>确定性渲染（键排序 + UTF-8 + LF 尾）——同输入两次调用逐字节一致。</summary>
    public static byte[] Render(string kind, string root)
        => Encoding.UTF8.GetBytes(PythonJson.Indented(Document(kind, root)) + "\n");

    /// <summary>导出形状的对象图（供渲染与机读面共用；未移植形状明确抛出）。</summary>
    public static Dictionary<string, object?> Document(string kind, string root)
    {
        return kind switch
        {
            "openapi" => Openapi(root),
            "asyncapi" => Asyncapi(root),
            "intoto" => Intoto(root),
            "sbom" => Sbom(root),
            "slsa" => Slsa(root),
            "a2a" => A2a(root),
            "prov" => Prov(root),
            "cyclonedx" => Cyclonedx(root),
            "vc" => Vc(root),
            "c2pa" => C2pa(root),
            "cid" => Cid(root),
            "decisions" => Decisions(root),
            _ => throw new InvalidOperationException(
                $"interop 形状 {kind} 未移植（已移植：{string.Join(" / ", PortedKinds)}）——" +
                "本引擎不提供半个面，也不冒充等价；未移植形状见覆盖率矩阵"),
        };
    }

    // ------------------------------------------------------------------ 形状（逐字节对齐 Python）

    /// <summary>
    /// 门禁：**覆盖完整 + 形状合法 + 确定性**（复刻 <c>interop_export.verify</c>）。
    /// fail-closed：真源缺失 = 无从校验（不是"空导出面"，是"没有可导出的东西"）。
    /// </summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Verify(string root)
    {
        var issues = new List<string>();
        var contract = ReadJson(root, ContractRel);
        var reg = ReadJson(root, EventsRel);
        var ext = ReadJson(root, ExternalEventsRel);
        var rec = ReadJson(root, ReceiptsRel);
        foreach (var rel in new[] { ContractRel, EventsRel, ReceiptsRel })
        {
            if (!File.Exists(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))))
                issues.Add($"缺派生真源 {rel}（修复指引：先落声明件——导出面只做纯派生，不自造真源）");
        }

        // OpenAPI ↔ 端点契约
        var oa = Openapi(root);
        var wantPaths = Endpoints(contract).Select(e => PyText(e.GetValueOrDefault("path"))).ToHashSet(StringComparer.Ordinal);
        var oaPaths = oa.GetValueOrDefault("paths") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var gotPaths = oaPaths.Keys.ToHashSet(StringComparer.Ordinal);
        if (!wantPaths.SetEquals(gotPaths))
        {
            issues.Add("OpenAPI 派生面与服务端点契约不一致：缺 " +
                       $"{PyList(wantPaths.Except(gotPaths))} / 多 {PyList(gotPaths.Except(wantPaths))}");
        }
        foreach (var (path, opsNode) in oaPaths)
        {
            if (opsNode is not Dictionary<string, object?> ops) continue;
            foreach (var (method, opNode) in ops)
            {
                if (opNode is not Dictionary<string, object?> op) continue;
                if (!PyTruthy(op.GetValueOrDefault("operationId")))
                    issues.Add($"OpenAPI {method.ToUpperInvariant()} {path} 缺 operationId（修复指引：端点 id 必填）");
                var responses = op.GetValueOrDefault("responses") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
                if (!responses.ContainsKey("200"))
                    issues.Add($"OpenAPI {method.ToUpperInvariant()} {path} 缺 200 响应（修复指引：每端点须声明成功形状）");
            }
        }
        var schemas = ((oa.GetValueOrDefault("components") as Dictionary<string, object?>)
                       ?.GetValueOrDefault("schemas") as Dictionary<string, object?>) ?? new(StringComparer.Ordinal);
        if (!schemas.ContainsKey("NfError"))
            issues.Add("OpenAPI 缺 NfError 错误形状（修复指引：错误面须可机读）");
        var errMap = oa.GetValueOrDefault("x-nf-error-mapping") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        if (!PyTruthy(errMap.GetValueOrDefault("title")))
            issues.Add("OpenAPI 缺 RFC 9457 字段映射（修复指引：声明 error.message ↔ title/detail）");

        // AsyncAPI ↔ 事件登记
        var aa = Asyncapi(root);
        var wantEvents = new HashSet<string>(StringComparer.Ordinal);
        foreach (var src in new[] { reg, ext })
        {
            if (src.GetValueOrDefault("events") is Dictionary<string, object?> map)
                foreach (var key in map.Keys) wantEvents.Add(key);
        }
        var aaChannels = aa.GetValueOrDefault("channels") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var gotEvents = aaChannels.Keys.Select(k => k.Contains('/') ? k[(k.IndexOf('/') + 1)..] : k)
            .ToHashSet(StringComparer.Ordinal);
        if (!wantEvents.SetEquals(gotEvents))
            issues.Add("AsyncAPI 派生面与事件登记不一致：缺 " +
                       $"{PyList(wantEvents.Except(gotEvents))} / 多 {PyList(gotEvents.Except(wantEvents))}");
        var ceTypes = aaChannels.Values.OfType<Dictionary<string, object?>>()
            .Select(c => (c.GetValueOrDefault("x-nf-cloudevents") as Dictionary<string, object?>)
                         ?.GetValueOrDefault("type")).ToList();
        if (ceTypes.Count != ceTypes.Distinct().Count())
            issues.Add("CloudEvents type 派生重复（修复指引：事件名须全库唯一，见 01 §1.1 事件名唯一 + 词法纪律）");

        // in-toto ↔ 协议层回执
        var st = Intoto(root);
        var wantSubjects = Entries(rec).Select(e => Str(e, "path")).ToHashSet(StringComparer.Ordinal);
        var stSubjects = (st.GetValueOrDefault("subject") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var gotSubjects = stSubjects.Select(s => PyText(s.GetValueOrDefault("name"))).ToHashSet(StringComparer.Ordinal);
        if (!wantSubjects.SetEquals(gotSubjects))
            issues.Add($"in-toto subject 与协议层回执不一致：缺 {wantSubjects.Except(gotSubjects).Count()} / " +
                       $"多 {gotSubjects.Except(wantSubjects).Count()}");
        foreach (var s in stSubjects)
        {
            var digest = (s.GetValueOrDefault("digest") as Dictionary<string, object?>)?.GetValueOrDefault("sha256");
            if (!Sha256Re.IsMatch(PyText(digest)))
                issues.Add($"in-toto subject 缺合规 sha256：{PyText(s.GetValueOrDefault("name"))}" +
                           "（修复指引：回执 digest 须 64 位小写十六进制）");
        }
        if (st.GetValueOrDefault("_type") as string != "https://in-toto.io/Statement/v1")
            issues.Add("in-toto Statement 类型头不合法（修复指引：_type 须为 Statement/v1）");

        // SPDX SBOM
        var sb = Sbom(root);
        var sbPackages = (sb.GetValueOrDefault("packages") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var spdxIds = sbPackages.Select(p => p.GetValueOrDefault("SPDXID")).ToList();
        if (spdxIds.Count != spdxIds.Distinct().Count())
            issues.Add("SBOM 包 SPDXID 重复（修复指引：每依赖一个唯一 SPDXID）");
        if (!sbPackages.Any(p => PyText(p.GetValueOrDefault("name")) == "NarrativeForge"))
            issues.Add("SBOM 缺本项目包（修复指引：SBOM 须自述本仓）");
        var relationships = (sb.GetValueOrDefault("relationships") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        if (!relationships.Any(r => PyText(r.GetValueOrDefault("relationshipType")) == "DESCRIBES"))
            issues.Add("SBOM 缺 DESCRIBES 关系（修复指引：文档须描述本仓包）");
        var created = ((sb.GetValueOrDefault("creationInfo") as Dictionary<string, object?>)
                       ?.GetValueOrDefault("created"));
        if (!Regex.IsMatch(PyText(created), @"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"))
            issues.Add($"SBOM 的 creationInfo.created 缺失或非 ISO 8601 UTC：{PyScalar.PyRepr(created)}" +
                       "（修复指引：SPDX 2.3 要求必填；本仓取「仓内声明日期最大值」保确定性）");

        // 确定性：同输入两次渲染必须逐字节一致
        foreach (var (kind, _) in Kinds)
        {
            if (!Render(kind, root).SequenceEqual(Render(kind, root)))
                issues.Add($"导出面不确定性：{kind} 两次渲染不一致（修复指引：禁止引入时间戳/随机源）");
        }

        // SLSA：subject 同源 + 不虚标等级 + 基线句与 quality_baseline 同源
        var sl = Slsa(root);
        if (sl.GetValueOrDefault("predicateType") as string != "https://slsa.dev/provenance/v1")
            issues.Add("SLSA 派生面 predicateType 不合法（修复指引：须为 slsa.dev/provenance/v1）");
        var slSubjects = (sl.GetValueOrDefault("subject") as List<object?> ?? new List<object?>()).Count;
        if (slSubjects != Entries(rec).Count)
            issues.Add($"SLSA 派生面 subject 数与回执不一致：{slSubjects} vs {Entries(rec).Count}");
        var predicate = sl.GetValueOrDefault("predicate") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var runDetails = predicate.GetValueOrDefault("runDetails") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var slNote = ((runDetails.GetValueOrDefault("metadata") as Dictionary<string, object?>)
                      ?.GetValueOrDefault("note")) as string ?? "";
        if (!slNote.Contains("不构成 SLSA 等级声明"))
            issues.Add("SLSA 派生面缺「不作等级声明」注记（修复指引：本地门禁不得虚标 SLSA 等级）");
        var buildDef = predicate.GetValueOrDefault("buildDefinition") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var extParams = buildDef.GetValueOrDefault("externalParameters") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var declared = PyText(extParams.GetValueOrDefault("declaredBaseline"));
        var mBase = Regex.Match(declared, @"^check1-(\d+) PASS=(\d+)$");
        if (!mBase.Success || mBase.Groups[1].Value == "0" || mBase.Groups[2].Value == "0")
        {
            issues.Add($"SLSA 派生面基线句非法或为 0：{PyScalar.PyRepr(declared)}（修复指引：基线取自 " +
                       "core.quality_baseline 期望值——写 0 等于虚报门禁口径）");
        }
        else
        {
            var (wantChecks, wantPass) = Baseline(root);
            if (wantChecks != 0 || wantPass != 0)
            {
                if (long.Parse(mBase.Groups[1].Value) != wantChecks || long.Parse(mBase.Groups[2].Value) != wantPass)
                    issues.Add($"SLSA 派生面基线句与 quality_baseline 期望值不一致：{declared}（修复指引：两处须同源）");
            }
        }

        // A2A 卡片 ↔ 端点契约
        var card = A2a(root);
        var cardSkills = (card.GetValueOrDefault("skills") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        if (cardSkills.Count != Endpoints(contract).Count)
            issues.Add("A2A 卡片 skills 数与端点契约不一致（修复指引：卡片能力面须与契约同源）");
        if (PyText(contract.GetValueOrDefault("status")) != "implemented"
            && !PyText(card.GetValueOrDefault("x-nf-note")).Contains("未实装"))
        {
            issues.Add("A2A 卡片未声明「服务未实装」（修复指引：不得据此宣称在线能力）");
        }
        foreach (var sk in cardSkills)
        {
            if (!PyTruthy(sk.GetValueOrDefault("id")) || !PyTruthy(sk.GetValueOrDefault("description")))
                issues.Add("A2A 卡片 skill 缺 id/description（修复指引：能力面须自述）");
        }

        // PROV-O 溯源图
        var pv = Prov(root);
        var pvGraph = (pv.GetValueOrDefault("@graph") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var pvIds = pvGraph.Select(n => n.GetValueOrDefault("@id")).ToList();
        if (pvIds.Count != pvIds.Distinct().Count())
            issues.Add("PROV 图存在重复节点 id（修复指引：实体/活动/代理同一 id 只出现一次）");
        var known = pvIds.Select(PyText).ToHashSet(StringComparer.Ordinal);
        foreach (var n in pvGraph)
        {
            foreach (var rel in new[] { "prov:used", "prov:generated", "prov:wasAssociatedWith" })
            {
                var target = n.GetValueOrDefault(rel);
                if (PyTruthy(target) && !known.Contains(PyText(target)))
                    issues.Add($"PROV 图关系 {rel} 指向不在册节点：{PyText(target)}（修复指引：被引用节点须在图内）");
            }
        }
        var provSrc = ReadJson(root, "05_资产库/provenance.json");
        var wantAssets = (provSrc.GetValueOrDefault("assets") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().Select(a => $"nf:asset/{PyText(a.GetValueOrDefault("key"))}")
            .ToHashSet(StringComparer.Ordinal);
        if (!wantAssets.IsSubsetOf(known))
            issues.Add($"PROV 图缺资产实体：{PyList(wantAssets.Except(known))}（修复指引：资产台账每条须有实体节点）");
        if (!pvGraph.Any(n => PyText(n.GetValueOrDefault("@type")) == "prov:Entity"))
            issues.Add("PROV 图无实体节点（修复指引：溯源图至少一个被证对象）");

        // CycloneDX
        var cdx = Cyclonedx(root);
        if (PyText(cdx.GetValueOrDefault("bomFormat")) != "CycloneDX" || PyText(cdx.GetValueOrDefault("specVersion")) != "1.5")
            issues.Add($"CycloneDX 头非法：{PyScalar.PyRepr(cdx.GetValueOrDefault("bomFormat"))}/" +
                       $"{PyScalar.PyRepr(cdx.GetValueOrDefault("specVersion"))}（修复指引：bomFormat=CycloneDX、specVersion=1.5）");
        var cdxComponents = (cdx.GetValueOrDefault("components") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var bomRefs = cdxComponents.Select(c => c.GetValueOrDefault("bom-ref")).ToList();
        if (bomRefs.Count != bomRefs.Distinct().Count())
            issues.Add("CycloneDX 组件 bom-ref 重复（修复指引：每依赖一个唯一 bom-ref）");
        if (!Regex.IsMatch(PyText(cdx.GetValueOrDefault("serialNumber")), @"^urn:uuid:[0-9a-f-]{36}$"))
            issues.Add($"CycloneDX serialNumber 非 urn:uuid 形态：{PyScalar.PyRepr(cdx.GetValueOrDefault("serialNumber"))}" +
                       "（修复指引：由声明摘要派生，勿用随机 UUID）");
        var hardSet = cdxComponents.Where(c => PyText(c.GetValueOrDefault("scope")) == "required")
            .Select(c => PyText(c.GetValueOrDefault("name"))).ToHashSet(StringComparer.Ordinal);
        var wantHard = PurityTables.Entries.Hard.Keys.ToHashSet(StringComparer.Ordinal);
        if (wantHard.Count > 0 && !hardSet.SetEquals(wantHard))
            issues.Add($"CycloneDX 硬依赖集与登记面不一致：{PyList(hardSet)}（期望 {PyList(wantHard)}）" +
                       "（修复指引：两形同源——都读 purity_scan 登记面）");

        // VC
        var vc = Vc(root);
        var vcContext = (vc.GetValueOrDefault("@context") as List<object?> ?? new List<object?>()).Select(PyText).ToList();
        if (!vcContext.Contains("https://www.w3.org/ns/credentials/v2"))
            issues.Add("VC 缺 v2 上下文（修复指引：@context 须含 https://www.w3.org/ns/credentials/v2）");
        var vcTypes = (vc.GetValueOrDefault("type") as List<object?> ?? new List<object?>()).Select(PyText).ToList();
        if (!vcTypes.Contains("VerifiableCredential")) issues.Add("VC type 缺 VerifiableCredential");
        if (!PyTruthy(vc.GetValueOrDefault("issuer"))
            || !Regex.IsMatch(PyText(vc.GetValueOrDefault("validFrom")), @"^\d{4}-\d{2}-\d{2}$"))
        {
            issues.Add("VC 缺 issuer 或 validFrom（修复指引：自 protocol/approvals/* 取批准人与批准日）");
        }
        var subj = vc.GetValueOrDefault("credentialSubject") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        if (!Sha256Re.IsMatch(PyText(subj.GetValueOrDefault("receiptRoot"))))
            issues.Add($"VC credentialSubject.receiptRoot 非 sha256：{PyScalar.PyRepr(subj.GetValueOrDefault("receiptRoot"))}" +
                       "（修复指引：凭证须绑定内容摘要）");
        if (!vc.ContainsKey("proof") && !PyText(vc.GetValueOrDefault("x-nf-proof-status")).Contains("unsigned"))
            issues.Add("VC 无 proof 却未声明未签名状态（修复指引：x-nf-proof-status 须写明——形状可读 ≠ 可验证）");

        // C2PA
        var c2 = C2pa(root);
        if (!PyText(c2.GetValueOrDefault("claim_generator")).StartsWith("NarrativeForge", StringComparison.Ordinal))
            issues.Add("C2PA 缺 claim_generator（修复指引：须自述生成器）");
        var c2Assertions = (c2.GetValueOrDefault("assertions") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var labels = c2Assertions.Select(a => PyText(a.GetValueOrDefault("label"))).ToHashSet(StringComparer.Ordinal);
        if (!labels.Contains("c2pa.hash.data") || !labels.Contains("c2pa.actions"))
            issues.Add($"C2PA 断言面不全（修复指引：须含 c2pa.hash.data 与 c2pa.actions）：{PyList(labels)}");
        var hd = c2Assertions.FirstOrDefault(a => PyText(a.GetValueOrDefault("label")) == "c2pa.hash.data")
                 ?.GetValueOrDefault("data") as Dictionary<string, object?>;
        if (!Sha256Re.IsMatch(PyText(hd?.GetValueOrDefault("hash"))))
            issues.Add("C2PA hash.data 非 sha256（修复指引：硬绑定摘要须 64 位小写十六进制）");
        if (!PyText(c2.GetValueOrDefault("x-nf-package-status")).Contains("未封装"))
            issues.Add("C2PA 未声明封装/签名状态（修复指引：JSON 清单 ≠ 生产级 C2PA 包）");

        // CID
        var ci = Cid(root);
        var ciEntries = (ci.GetValueOrDefault("entries") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        if (ciEntries.Count != Entries(rec).Count)
            issues.Add($"CID 索引条目数与回执不一致：{ciEntries.Count} vs {Entries(rec).Count}");
        foreach (var e in ciEntries)
        {
            if (!Regex.IsMatch(PyText(e.GetValueOrDefault("cid")), @"^b[a-z2-7]{50,}$"))
            {
                issues.Add($"CID 形态非法：{PyText(e.GetValueOrDefault("path"))}（修复指引：CIDv1 multibase base32 小写，" +
                           "前缀 b + raw codec 0x71 + sha2-256 multihash）");
                break;
            }
        }

        // 决策面
        var ds = Decisions(root);
        var declDl = ReadJson(root, "protocol/decision_layer.json");
        var dsAdapters = (ds.GetValueOrDefault("adapters") as List<object?> ?? new List<object?>()).Count;
        var declAdapters = (declDl.GetValueOrDefault("adapters") as List<object?> ?? new List<object?>()).Count;
        if (dsAdapters != declAdapters)
            issues.Add($"决策面适配器数与声明不一致：{dsAdapters} vs {declAdapters}");
        var dsCandidates = (ds.GetValueOrDefault("candidates") as List<object?> ?? new List<object?>()).Count;
        var declCandidates = (declDl.GetValueOrDefault("candidates") as List<object?> ?? new List<object?>()).Count;
        if (dsCandidates != declCandidates)
            issues.Add($"决策面候选数与声明不一致：{dsCandidates} vs {declCandidates}");
        if (!PyText(ds.GetValueOrDefault("x-nf-internal")).Contains("不随本面发布"))
            issues.Add("决策面缺「工单不入公开面」声明（修复指引：写明内部档案边界，不得让外部以为逐次决策已公开）");
        if ((ds.GetValueOrDefault("publicDecisionIndex") as List<object?> ?? new List<object?>()).Count == 0)
            issues.Add("决策面缺公开裁决索引（修复指引：results/audit/*.md 的 frontmatter 可派生）");

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["openapi_paths"] = (long)oaPaths.Count,
            ["asyncapi_channels"] = (long)aaChannels.Count,
            ["intoto_subjects"] = (long)stSubjects.Count,
            ["sbom_packages"] = (long)sbPackages.Count,
            ["slsa_subjects"] = (long)slSubjects,
            ["a2a_skills"] = (long)cardSkills.Count,
            ["prov_nodes"] = (long)pvGraph.Count,
            ["prov_counts"] = pv.GetValueOrDefault("x-nf-counts") ?? new Dictionary<string, object?>(StringComparer.Ordinal),
            ["cyclonedx_components"] = (long)cdxComponents.Count,
            ["vc_type"] = vcTypes.Count > 0 ? vcTypes[0] : "",
            ["c2pa_assertions"] = (long)c2Assertions.Count,
            ["cid_entries"] = (long)ciEntries.Count,
            ["decision_adapters"] = (long)dsAdapters,
            ["decision_candidates"] = (long)dsCandidates,
            ["decision_audits"] = (long)((ds.GetValueOrDefault("publicDecisionIndex") as List<object?>)
                                          ?? new List<object?>()).Count,
            ["issues"] = (long)issues.Count,
        };
        return (issues, stats);
    }

    /// <summary>门禁摘要句（等价 <c>interop_export.summary</c>）。</summary>
    public static string Summary(Dictionary<string, object?> stats)
        => $"OpenAPI 路径 {stats.GetValueOrDefault("openapi_paths")} / AsyncAPI 通道 {stats.GetValueOrDefault("asyncapi_channels")} / " +
           $"in-toto subject {stats.GetValueOrDefault("intoto_subjects")} / SBOM 包 {stats.GetValueOrDefault("sbom_packages")} / " +
           $"SLSA subject {stats.GetValueOrDefault("slsa_subjects")} / A2A skills {stats.GetValueOrDefault("a2a_skills")} / " +
           $"PROV 节点 {stats.GetValueOrDefault("prov_nodes")} / 决策面 适配器 {stats.GetValueOrDefault("decision_adapters")}" +
           $"（裁决索引 {stats.GetValueOrDefault("decision_audits")}）";

    private static List<Dictionary<string, object?>> Endpoints(Dictionary<string, object?> contract)
        => (contract.GetValueOrDefault("endpoints") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();

    /// <summary>Python <c>sorted(...)</c> 的 repr 形态（消息里用）。</summary>
    private static string PyList(IEnumerable<string> items)
        => PyScalar.PyRepr(items.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList());

    /// <summary>服务端点契约 → OpenAPI 3.1 文档。</summary>
    public static Dictionary<string, object?> Openapi(string root)
    {
        var contract = ReadJson(root, ContractRel);
        var conv = contract.GetValueOrDefault("conventions") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var nonIdem = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var e in (contract.GetValueOrDefault("idempotency_exceptions") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            nonIdem[PyText(e.GetValueOrDefault("id"))] = e.GetValueOrDefault("key") is string k ? k : "";
        }

        var paths = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var ep in (contract.GetValueOrDefault("endpoints") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            var path = PyText(ep.GetValueOrDefault("path"));
            var method = PyText(ep.GetValueOrDefault("method")).ToLowerInvariant();
            if (path.Length == 0 || method.Length == 0) continue;
            var req = ep.GetValueOrDefault("request") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            var resp = ep.GetValueOrDefault("response") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            var epId = PyText(ep.GetValueOrDefault("id"));

            var ok200 = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["description"] = "成功",
                ["content"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["application/json"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["schema"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["type"] = "object",
                            ["properties"] = resp.ToDictionary(kv => kv.Key, kv => (object?)SchemaFor(kv.Value), StringComparer.Ordinal),
                        },
                    },
                },
            };
            var op = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["operationId"] = epId,
                ["summary"] = $"maps_to {PyText(ep.GetValueOrDefault("maps_to"))}",
                ["x-nf-idempotency"] = nonIdem.ContainsKey(epId)
                    ? $"non-idempotent（幂等键 {nonIdem[epId]}）"
                    : "idempotent",
                ["responses"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["200"] = ok200,
                    ["default"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["description"] = "错误（RFC 9457 Problem Details 映射见 x-nf-error-mapping）",
                        ["content"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["application/json"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                            {
                                ["schema"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                                {
                                    ["$ref"] = "#/components/schemas/NfError",
                                },
                            },
                        },
                    },
                },
            };
            if (req.Count > 0 || method == "post")
            {
                op["requestBody"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["required"] = true,
                    ["content"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["application/json"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["schema"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                            {
                                ["type"] = "object",
                                ["properties"] = req.ToDictionary(kv => kv.Key, kv => (object?)SchemaFor(kv.Value), StringComparer.Ordinal),
                            },
                        },
                    },
                };
            }
            if (PyTruthy(ep.GetValueOrDefault("streaming")))
            {
                var content = (Dictionary<string, object?>)ok200["content"]!;
                content["text/event-stream"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["schema"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["type"] = "string" },
                    ["x-nf-streaming"] = conv.GetValueOrDefault("streaming") ?? "",
                };
            }
            var tmplVars = Regex.Matches(path, @"\{([^}]+)\}").Select(m => m.Groups[1].Value).ToList();
            if (tmplVars.Count > 0)
            {
                op["parameters"] = tmplVars.Select(name => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["name"] = name,
                    ["in"] = "path",
                    ["required"] = true,
                    ["schema"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["type"] = "string" },
                    ["x-nf-derived"] = "由 protocol/endpoint_contract.json 的路径模板派生",
                }).ToList();
            }
            if (PyTruthy(ep.GetValueOrDefault("deprecated")))
            {
                op["deprecated"] = true;
                op["x-nf-sunset"] = ep.GetValueOrDefault("sunset");            // 可能是 null（Python 同）
                op["x-nf-replacement"] = ep.GetValueOrDefault("replacement");  // 可能是 null
            }
            if (!paths.TryGetValue(path, out var bucket) || bucket is not Dictionary<string, object?> ops)
            {
                ops = new Dictionary<string, object?>(StringComparer.Ordinal);
                paths[path] = ops;
            }
            ops[method] = op;
        }

        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["openapi"] = "3.1.0",
            ["info"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["title"] = "NarrativeForge 服务端点契约（派生）",
                ["version"] = "1.0.0",
                ["description"] = $"由 protocol/endpoint_contract.json 实时派生（status={PyText(contract.GetValueOrDefault("status"))}）；本文件非真源。",
            },
            ["servers"] = new List<object?>(),
            ["paths"] = paths,
            ["components"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["schemas"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["NfError"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["type"] = "object",
                        ["required"] = new List<object?> { "error" },
                        ["properties"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["error"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                            {
                                ["type"] = "object",
                                ["required"] = new List<object?> { "code", "message" },
                                ["properties"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                                {
                                    ["code"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                                    {
                                        ["type"] = "integer", ["description"] = "机器可判定错误码",
                                    },
                                    ["message"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                                    {
                                        ["type"] = "string", ["description"] = "人读说明，必须带修复指引",
                                    },
                                    ["data"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                                    {
                                        ["type"] = new List<object?> { "object", "null" },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            ["x-nf-error-mapping"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["type"] = "about:blank",
                ["title"] = "error.message",
                ["detail"] = "error.message + 修复指引（patterns/error-message-guidance）",
                ["instance"] = "请求路径",
                ["status"] = "HTTP 状态码（与 message 同源）",
                ["source"] = conv.GetValueOrDefault("errors") ?? "",
            },
            ["x-nf-endpoints"] = (long)((contract.GetValueOrDefault("endpoints") as List<object?>)?.Count ?? 0),
        };
    }

    /// <summary>事件登记 → AsyncAPI 3.0 文档 + CloudEvents 属性。</summary>
    public static Dictionary<string, object?> Asyncapi(string root)
    {
        var reg = ReadJson(root, EventsRel);
        var ext = ReadJson(root, ExternalEventsRel);
        var events = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var src in new[] { reg, ext })
        {
            if (src.GetValueOrDefault("events") is not Dictionary<string, object?> map) continue;
            foreach (var (name, meta) in map)
            {
                if (!events.ContainsKey(name))
                    events[name] = meta as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            }
        }

        var channels = new Dictionary<string, object?>(StringComparer.Ordinal);
        var messages = new Dictionary<string, object?>(StringComparer.Ordinal);
        var ordered = events.Keys.OrderBy(k => k, StringComparer.Ordinal).ToList();
        foreach (var name in ordered)
        {
            var meta = events[name];
            var fields = meta.GetValueOrDefault("fields") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            channels[$"nf/{name}"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["address"] = $"nf/{name}",
                ["title"] = name,
                ["messages"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    [$"nf.{name}"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["$ref"] = $"#/components/messages/{Ptr(name)}",
                    },
                },
                ["x-nf-cloudevents"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = $"nf.{name}", ["source"] = "urn:nf:repo",
                    ["specversion"] = "1.0", ["datacontenttype"] = "application/json",
                },
            };
            messages[name] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["name"] = name,
                ["contentType"] = "application/json",
                ["payload"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "object",
                    ["properties"] = fields.ToDictionary(kv => kv.Key,
                        kv => (object?)SchemaFor((kv.Value as Dictionary<string, object?>)?.GetValueOrDefault("type") ?? ""),
                        StringComparer.Ordinal),
                },
                ["x-nf-note"] = PyScalar.PySlice(PyText(meta.GetValueOrDefault("note")), 200),
            };
        }

        var operations = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var name in ordered)
        {
            operations[$"publish/{name}"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["action"] = "send",
                ["channel"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["$ref"] = $"#/channels/{Ptr($"nf/{name}")}",
                },
            };
        }

        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["asyncapi"] = "3.0.0",
            ["info"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["title"] = "NarrativeForge 事件登记（派生）",
                ["version"] = "1.0.0",
                ["description"] = "由 protocol/event_registry.json + external_events.json 实时派生；本文件非真源。",
            },
            ["channels"] = channels,
            ["operations"] = operations,
            ["components"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["messages"] = messages },
            ["x-nf-events"] = (long)events.Count,
        };
    }

    /// <summary>PROV-O 溯源图（资产 / 馆藏 / 消化 / 回执 → 实体·活动·代理三元组）。</summary>
    public static Dictionary<string, object?> Prov(string root)
    {
        var prov = ReadJson(root, "05_资产库/provenance.json");
        var transform = ReadJson(root, "protocol/transform_log.json");
        var rec = ReadJson(root, ReceiptsRel);
        var nodes = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        void Add(Dictionary<string, object?> node)
        {
            var id = PyText(node.GetValueOrDefault("@id"));
            if (!nodes.ContainsKey(id)) nodes[id] = node;
        }

        foreach (var a in (prov.GetValueOrDefault("assets") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["@id"] = $"nf:asset/{PyText(a.GetValueOrDefault("key"))}",
                ["@type"] = "prov:Entity",
                ["prov:label"] = PyText(a.GetValueOrDefault("key")),
                ["nf:file"] = PyText(a.GetValueOrDefault("file")),
                ["nf:module"] = PyText(a.GetValueOrDefault("module")),
                ["nf:status"] = PyText(a.GetValueOrDefault("status")),
                ["nf:version"] = PyText(a.GetValueOrDefault("version")),
            });
        }

        var idx = Path.Combine(root, "library", "INDEX.md");
        if (File.Exists(idx))
        {
            var text = StrictUtf8.GetString(File.ReadAllBytes(idx)).Replace("\r\n", "\n").Replace('\r', '\n');
            foreach (var line in text.Split('\n'))
            {
                if (!Regex.IsMatch(line, @"^\|\s*NF-[A-Za-z0-9\-]+\s*\|")) continue;
                var cells = line.Trim().Trim('|').Split('|').Select(c => c.Trim()).ToList();
                if (cells.Count < 6) continue;
                var eid = cells[0];
                var author = cells[3];
                var date = cells[4];
                var lic = cells[5];
                Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["@id"] = $"nf:library/{eid}", ["@type"] = "prov:Entity",
                    ["prov:label"] = cells[1], ["nf:license"] = lic,
                });
                Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["@id"] = $"nf:activity/library-ingest/{eid}",
                    ["@type"] = "prov:Activity",
                    ["prov:endedAtTime"] = date,
                    ["prov:wasAssociatedWith"] = $"nf:agent/{author}",
                    ["prov:generated"] = $"nf:library/{eid}",
                });
                Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["@id"] = $"nf:agent/{author}", ["@type"] = "prov:Person", ["prov:label"] = author,
                });
            }
        }

        foreach (var e in (rec.GetValueOrDefault("entries") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["@id"] = $"nf:file/{PyText(e.GetValueOrDefault("path"))}",
                ["@type"] = "prov:Entity",
                ["nf:sha256"] = PyText(e.GetValueOrDefault("digest")),
            });
        }

        var i = 0;
        foreach (var t in (transform.GetValueOrDefault("entries") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            i++;
            var used = t.GetValueOrDefault("source") ?? t.GetValueOrDefault("from");
            var generated = t.GetValueOrDefault("product") ?? t.GetValueOrDefault("to");
            Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["@id"] = $"nf:transform/{i}",
                ["@type"] = "prov:Activity",
                ["prov:used"] = $"nf:file/{PyText(used)}",
                ["prov:generated"] = $"nf:file/{PyText(generated)}",
                ["nf:digest"] = PyText(t.GetValueOrDefault("digest")),
            });
        }

        Add(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["@id"] = "nf:agent/verify-sh",
            ["@type"] = "prov:SoftwareAgent",
            ["prov:label"] = "NarrativeForge verify.sh 门禁",
            ["nf:present"] = File.Exists(Path.Combine(root, "verify.sh")),
        });

        var graph = nodes.Keys.OrderBy(k => k, StringComparer.Ordinal).Select(k => (object?)nodes[k]).ToList();
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["@context"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["prov"] = "http://www.w3.org/ns/prov#",
                ["nf"] = "https://narrativeforge.dev/ns#",
            },
            ["schema"] = "nf-prov/1",
            ["note"] = "由仓内声明件派生（资产 / 馆藏 / 消化记录 / 回执）；本文件非真源，空面即如实为空。",
            ["@graph"] = graph,
            ["x-nf-counts"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["entities"] = (long)graph.Count(n => ((Dictionary<string, object?>)n!)["@type"] as string == "prov:Entity"),
                ["activities"] = (long)graph.Count(n => ((Dictionary<string, object?>)n!)["@type"] as string == "prov:Activity"),
                ["agents"] = (long)graph.Count(n => ((Dictionary<string, object?>)n!)["@type"] as string is "prov:Person" or "prov:SoftwareAgent"),
            },
        };
    }

    /// <summary>决策面（能力 + 公开裁决索引；**不导出逐次工单**，并显式声明这一点）。</summary>
    public static Dictionary<string, object?> Decisions(string root)
    {
        var decl = ReadJson(root, "protocol/decision_layer.json");
        var audits = new List<object?>();
        var auditDir = Path.Combine(root, "results", "audit");
        if (Directory.Exists(auditDir))
        {
            foreach (var path in Directory.GetFiles(auditDir, "*.md").OrderBy(p => p, StringComparer.Ordinal))
            {
                string head;
                try
                {
                    var text = StrictUtf8.GetString(File.ReadAllBytes(path));
                    head = PyScalar.PySlice(text, 1200);
                }
                catch (IOException)
                {
                    continue;   // 尽力而为：读不到就跳过（缺件由回执门报出）
                }
                if (!head.StartsWith("---", StringComparison.Ordinal)) continue;
                var parts = head.Split("---", 3);
                if (parts.Length < 2) continue;
                var rec = new Dictionary<string, string>(StringComparer.Ordinal);
                foreach (var line in parts[1].Split('\n'))
                {
                    var at = line.IndexOf(':');
                    if (at < 0) continue;
                    rec[line[..at].Trim()] = line[(at + 1)..].Trim();
                }
                if (rec.TryGetValue("id", out var id) && id.Length > 0)
                {
                    audits.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["id"] = id,
                        ["title"] = rec.GetValueOrDefault("title", ""),
                        ["date"] = rec.GetValueOrDefault("date", ""),
                        ["verdict"] = rec.GetValueOrDefault("verdict", ""),
                    });
                }
            }
        }

        var adapters = new List<object?>();
        foreach (var a in (decl.GetValueOrDefault("adapters") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            adapters.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = a.GetValueOrDefault("id"),
                ["kind"] = a.GetValueOrDefault("kind"),
                ["inGatePath"] = a.GetValueOrDefault("in_gate_path"),
                ["calibrated"] = a.GetValueOrDefault("calibrated"),
            });
        }
        var candidates = new List<object?>();
        foreach (var c in (decl.GetValueOrDefault("candidates") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            var local = c.GetValueOrDefault("local") as Dictionary<string, object?>;
            candidates.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = c.GetValueOrDefault("id"),
                ["source"] = c.GetValueOrDefault("source"),
                ["license"] = c.GetValueOrDefault("license"),
                ["pulled"] = c.GetValueOrDefault("pulled"),
                ["evidence"] = PyScalar.PySlice(PyText(c.GetValueOrDefault("evidence")), 200),
                ["local"] = local is null
                    ? null
                    : new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["runtime"] = local.GetValueOrDefault("runtime"),
                        ["servedBy"] = local.GetValueOrDefault("served_by"),
                    },
            });
        }

        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = "nf-decision-surface/1",
            ["primitives"] = decl.GetValueOrDefault("primitives") as Dictionary<string, object?> ?? new(StringComparer.Ordinal),
            ["responseContract"] = decl.GetValueOrDefault("response_contract") as Dictionary<string, object?> ?? new(StringComparer.Ordinal),
            ["adapters"] = adapters,
            ["candidates"] = candidates,
            ["boundaries"] = decl.GetValueOrDefault("boundaries") as List<object?> ?? new List<object?>(),
            ["workloop"] = decl.GetValueOrDefault("workloop") as Dictionary<string, object?> ?? new(StringComparer.Ordinal),
            ["publicDecisionIndex"] = audits,
            ["x-nf-internal"] = "逐次工单（挑活/风险/收口）留在内部档案 .rivet/private_archive/work_orders/，" +
                                "不随本面发布（STRATEGY §四 计划内部消化）；本面只投影**能力与公开裁决索引**。",
        };
    }

    /// <summary>A2A Agent Card（能力面 = 端点契约投影 + MCP 包版本）。</summary>
    public static Dictionary<string, object?> A2a(string root)
    {
        var contract = ReadJson(root, ContractRel);
        var pkg = ReadJson(root, "protocol/mcp_package.json");
        var endpoints = (contract.GetValueOrDefault("endpoints") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var skills = endpoints.Select(ep => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = PyText(ep.GetValueOrDefault("id")),
            ["name"] = PyText(ep.GetValueOrDefault("id")),
            ["description"] = $"maps_to {PyText(ep.GetValueOrDefault("maps_to"))}（" +
                              $"{PyText(ep.GetValueOrDefault("method"))} {PyText(ep.GetValueOrDefault("path"))}）",
            ["tags"] = new List<object?> { "narrativeforge", "content-contract" },
        }).ToList();
        var version = pkg.GetValueOrDefault("version") as string;
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["protocolVersion"] = "0.2.5",
            ["name"] = "NarrativeForge",
            ["description"] = "内容契约层：装配 / 质检 / 图书馆 / 一致性报告（只读面）",
            ["url"] = "urn:nf:repo",
            ["preferredTransport"] = "stdio",
            ["version"] = version is { Length: > 0 } ? version : "1.0.0",
            ["capabilities"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["streaming"] = endpoints.Any(e => PyTruthy(e.GetValueOrDefault("streaming"))),
                ["pushNotifications"] = false,
            },
            ["defaultInputModes"] = new List<object?> { "text/plain", "application/json" },
            ["defaultOutputModes"] = new List<object?> { "text/plain", "application/json" },
            ["skills"] = skills,
            ["x-nf-note"] = $"能力面 = protocol/endpoint_contract.json 的投影；服务本体 " +
                            $"status={PyText(contract.GetValueOrDefault("status"))}（未实装，本卡不据此宣称在线）",
        };
    }

    /// <summary>字段说明串 → JSON Schema 片段（只做可判定映射，未识别一律 object 兜底）。</summary>
    public static Dictionary<string, object?> SchemaFor(object? descNode)
    {
        var desc = PyText(descNode);
        var m = Regex.Match(desc, @"^\s*([a-z]+)");
        var token = m.Success ? m.Groups[1].Value : "";
        var jtype = TypeMap.Contains(token) ? token : "object";
        var nullable = desc.Contains("null");
        var output = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["type"] = nullable ? new List<object?> { jtype, "null" } : jtype,
        };
        if (jtype == "array") output["items"] = new Dictionary<string, object?>(StringComparer.Ordinal);
        if (jtype == "object") output["additionalProperties"] = true;
        if (desc.Trim().Length > 0) output["description"] = desc;
        return output;
    }

    /// <summary>JSON Pointer 转义（RFC 6901：<c>~</c> → <c>~0</c>、<c>/</c> → <c>~1</c>）。</summary>
    public static string Ptr(string token) => token.Replace("~", "~0").Replace("/", "~1");

    private static readonly HashSet<string> TypeMap = new(StringComparer.Ordinal)
    {
        "string", "integer", "number", "boolean", "object", "array",
    };

    private static string PyText(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(CultureInfo.InvariantCulture),
        int i => i.ToString(CultureInfo.InvariantCulture),
        _ => PyScalar.PyRepr(v),
    };

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

    /// <summary>协议层回执 → in-toto Statement v1。</summary>
    public static Dictionary<string, object?> Intoto(string root)
    {
        var rec = ReadJson(root, ReceiptsRel);
        var entries = Entries(rec);
        var subject = entries.Select(e => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["name"] = Str(e, "path"),
            ["digest"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["sha256"] = Str(e, "digest"),
            },
        }).ToList();
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["_type"] = "https://in-toto.io/Statement/v1",
            ["subject"] = subject,
            ["predicateType"] = "https://narrativeforge.dev/attestation/protocol-receipts/v1",
            ["predicate"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["algorithm"] = rec.GetValueOrDefault("algorithm") ?? "",
                ["root"] = rec.GetValueOrDefault("root") ?? "",
                ["count"] = rec.GetValueOrDefault("count") ?? (long)subject.Count,
                ["scope"] = rec.GetValueOrDefault("scope") ?? "",
                ["note"] = "派生自 protocol/RECEIPTS.json；inclusion proof 留在原回执单根内。",
            },
        };
    }

    /// <summary>依赖登记面 → SPDX 2.3 风格 SBOM。</summary>
    public static Dictionary<string, object?> Sbom(string root)
    {
        var nfVersion = "0.0.0";
        var verifyPath = Path.Combine(root, "verify.sh");
        if (File.Exists(verifyPath))
        {
            var m = VerifyVersionRe.Match(StrictUtf8.GetString(File.ReadAllBytes(verifyPath)));
            if (m.Success) nfVersion = m.Groups[1].Value;
        }
        var (hard, soft) = PurityTables.Entries;

        var packages = new List<object?>
        {
            new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["SPDXID"] = "SPDXRef-Package-narrativeforge",
                ["name"] = "NarrativeForge",
                ["versionInfo"] = nfVersion,
                ["downloadLocation"] = "NOASSERTION",
                ["licenseConcluded"] = LicenseName,
                ["licenseDeclared"] = LicenseName,
                ["copyrightText"] = "NOASSERTION",
            },
        };
        var deps = new List<(string Pkg, string Rel)>();
        foreach (var (name, why) in hard.OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            var pkg = $"SPDXRef-Dependency-{name}";
            packages.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["SPDXID"] = pkg,
                ["name"] = name,
                ["downloadLocation"] = "NOASSERTION",
                ["licenseConcluded"] = "NOASSERTION",
                ["comment"] = $"硬依赖（登记）：{why}",
            });
            deps.Add((pkg, "DEPENDENCY_OF"));
        }
        foreach (var (name, why) in soft.OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            var pkg = $"SPDXRef-Optional-{name}";
            packages.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["SPDXID"] = pkg,
                ["name"] = name,
                ["downloadLocation"] = "NOASSERTION",
                ["licenseConcluded"] = "NOASSERTION",
                ["comment"] = $"软依赖（可选，须 try/except 守卫）：{why}",
            });
            deps.Add((pkg, "OPTIONAL_DEPENDENCY_OF"));
        }

        var maxDate = DeclaredMaxDate(root);
        var relationships = new List<object?>
        {
            new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["spdxElementId"] = "SPDXRef-DOCUMENT",
                ["relatedSpdxElement"] = "SPDXRef-Package-narrativeforge",
                ["relationshipType"] = "DESCRIBES",
            },
        };
        relationships.AddRange(deps.Select(d => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["spdxElementId"] = d.Pkg,
            ["relatedSpdxElement"] = "SPDXRef-Package-narrativeforge",
            ["relationshipType"] = d.Rel,
        }));

        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["spdxVersion"] = "SPDX-2.3",
            ["dataLicense"] = "CC0-1.0",
            ["SPDXID"] = "SPDXRef-DOCUMENT",
            ["name"] = "narrativeforge-sbom",
            ["documentNamespace"] = $"https://narrativeforge.dev/spdx/{nfVersion}",
            ["creationInfo"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["creators"] = new List<object?> { "Tool: nf interop --kind sbom" },
                ["created"] = maxDate.Length > 0 ? $"{maxDate}T00:00:00Z" : "",
                ["comment"] = "由纯度扫描登记面（HARD_ALLOW / SOFT_IMPORTS）实时派生；" +
                              "created = 仓内声明日期最大值（非墙钟，保确定性）",
            },
            ["comment"] = "派生面非真源；created = max(仓内声明日期: " +
                          "score_baseline / provenance / approvals)（保确定性，非墙钟）。",
            ["packages"] = packages,
            ["relationships"] = relationships,
        };
    }

    /// <summary>SLSA Provenance v1（从本地门禁事实派生，不宣称外部构建）。</summary>
    public static Dictionary<string, object?> Slsa(string root)
    {
        var rec = ReadJson(root, ReceiptsRel);
        var (wantChecks, wantPass) = Baseline(root);
        var version = "";
        var verifyPath = Path.Combine(root, "verify.sh");
        if (File.Exists(verifyPath))
        {
            var m = VerifyVersionRe.Match(StrictUtf8.GetString(File.ReadAllBytes(verifyPath)));
            version = m.Success ? m.Groups[1].Value : "";
        }
        var subjects = Entries(rec).Select(e => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["name"] = Str(e, "path"),
            ["digest"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["sha256"] = Str(e, "digest"),
            },
        }).ToList();
        var names = Entries(rec).Select(e => Str(e, "path")).ToList();
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["_type"] = "https://in-toto.io/Statement/v1",
            ["subject"] = subjects,
            ["predicateType"] = "https://slsa.dev/provenance/v1",
            ["predicate"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["buildDefinition"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["buildType"] = "https://narrativeforge.dev/buildtypes/local-gate/v1",
                    ["externalParameters"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["gate"] = "verify.sh",
                        ["gateVersion"] = version,
                        ["declaredBaseline"] = $"check1-{wantChecks} PASS={wantPass}",
                        ["note"] = "参数取自仓内声明件（不引入新真源）",
                    },
                    ["internalParameters"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["repoRoot"] = "relative",
                    },
                    ["resolvedDependencies"] = names.Select(n => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["uri"] = $"nf://repo/{n}",
                    }).ToList(),
                },
                ["runDetails"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["builder"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["id"] = "https://narrativeforge.dev/builder/verify-sh",
                    },
                    ["metadata"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["invocationId"] = Short(Str(rec, "root"), 16),
                        ["note"] = "本地门禁执行事实；**不构成 SLSA 等级声明**（无远程 builder）",
                    },
                },
            },
        };
    }

    /// <summary>CycloneDX 1.5（与 SPDX 面同源不同形；serialNumber 由内容寻址派生）。</summary>
    public static Dictionary<string, object?> Cyclonedx(string root)
    {
        var sbom = Sbom(root);
        var (hard, soft) = PurityTables.Entries;
        var ns = sbom.GetValueOrDefault("documentNamespace") as string ?? "";
        var seed = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(ns))).ToLowerInvariant();
        var serial = $"urn:uuid:{seed[..8]}-{seed[8..12]}-{seed[12..16]}-{seed[16..20]}-{seed[20..32]}";

        var components = new List<object?>();
        foreach (var (name, why) in hard.OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            components.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["type"] = "library", ["bom-ref"] = $"dep:{name}", ["name"] = name,
                ["scope"] = "required", ["description"] = $"硬依赖（登记）：{why}",
            });
        }
        foreach (var (name, why) in soft.OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            components.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["type"] = "library", ["bom-ref"] = $"opt:{name}", ["name"] = name,
                ["scope"] = "optional", ["description"] = $"软依赖（可选，须守卫）：{why}",
            });
        }

        var packages = (sbom.GetValueOrDefault("packages") as List<object?>) ?? new List<object?>();
        var firstPkg = packages.Count > 0 ? packages[0] as Dictionary<string, object?> : null;
        var versionInfo = firstPkg is null ? "0.0.0" : (firstPkg.GetValueOrDefault("versionInfo") as string ?? "0.0.0");
        var creationInfo = (sbom.GetValueOrDefault("creationInfo") as Dictionary<string, object?>) ?? new(StringComparer.Ordinal);

        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["bomFormat"] = "CycloneDX",
            ["specVersion"] = "1.5",
            ["serialNumber"] = serial,
            ["version"] = 1L,
            ["metadata"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["timestamp"] = creationInfo.GetValueOrDefault("created") ?? "",
                ["component"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "application",
                    ["bom-ref"] = $"pkg:nf/narrativeforge@{versionInfo}",
                    ["name"] = "NarrativeForge",
                    ["licenses"] = new List<object?>
                    {
                        new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["license"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["id"] = LicenseName },
                        },
                    },
                },
                ["tools"] = new List<object?>
                {
                    new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["vendor"] = "NarrativeForge", ["name"] = "nf interop --kind cyclonedx", ["version"] = "1.0.0",
                    },
                },
                ["properties"] = new List<object?>
                {
                    new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["name"] = "nf:source", ["value"] = "purity_scan 依赖登记面（纯派生）",
                    },
                    new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["name"] = "nf:note", ["value"] = "与 SPDX 面同源；timestamp 取仓内声明日期最大值（非墙钟）。",
                    },
                },
            },
            ["components"] = components,
        };
    }

    /// <summary>W3C VC 2.0 形状（未签名——状态写进注记，不宣称可验证）。</summary>
    public static Dictionary<string, object?> Vc(string root)
    {
        var rec = ReadJson(root, ReceiptsRel);
        var rep = ReadJson(root, "protocol/conformance_report.json");
        var approvals = new List<Dictionary<string, object?>>();
        var adir = Path.Combine(root, "protocol", "approvals");
        if (Directory.Exists(adir))
        {
            foreach (var name in Directory.GetFiles(adir, "*.json").Select(f => Path.GetFileName(f) ?? "")
                         .OrderBy(n => n, StringComparer.Ordinal))
            {
                var a = ReadJson(root, $"protocol/approvals/{name}");
                if (a.Count > 0) approvals.Add(a);
            }
        }
        var first = approvals.Count > 0 ? approvals[0] : null;
        var issuer = first is null ? "" : (first.GetValueOrDefault("approved_by") as string ?? "");
        if (issuer.Length == 0) issuer = "NarrativeForge";
        var validFrom = first is null ? "" : (first.GetValueOrDefault("approved_at") as string ?? "");

        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["@context"] = new List<object?>
            {
                "https://www.w3.org/ns/credentials/v2",
                "https://narrativeforge.dev/ns/credentials/v1",
            },
            ["type"] = new List<object?> { "VerifiableCredential", "NfConformanceCredential" },
            ["issuer"] = issuer,
            ["validFrom"] = validFrom,
            ["credentialSubject"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = "nf:conformance_report",
                ["verdict"] = rep.GetValueOrDefault("verdict") as string ?? "",
                ["contracts"] = (long)((rep.GetValueOrDefault("contracts") as List<object?>)?.Count ?? 0),
                ["receiptRoot"] = rec.GetValueOrDefault("root") as string ?? "",
                ["receiptCount"] = ToLong(rec.GetValueOrDefault("count")),
            },
            ["x-nf-proof-status"] = "unsigned（本仓签名走 ssh 外挂锚 nf attest；未接 JWS/Data Integrity " +
                                    "签名套件——形状可读，不可验证，勿当凭证使用）",
            ["x-nf-note"] = "派生自 protocol/conformance_report.json + protocol/RECEIPTS.json + " +
                            "protocol/approvals/*（纯派生，不新增真源）",
        };
    }

    /// <summary>C2PA JSON 清单形状（未封装/未签名；哈希硬绑定用回执摘要口径）。</summary>
    public static Dictionary<string, object?> C2pa(string root)
    {
        var rec = ReadJson(root, ReceiptsRel);
        var sample = Entries(rec).FirstOrDefault(e => Str(e, "path").Length > 0);
        var assertions = new List<object?>
        {
            new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["label"] = "c2pa.actions",
                ["data"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["actions"] = new List<object?>
                    {
                        new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["action"] = "c2pa.created",
                            ["digitalSourceType"] = "http://cv.iptc.org/newscodes/digitalsourcetype/digitalCapture",
                        },
                    },
                },
            },
        };
        if (sample is not null)
        {
            assertions.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["label"] = "c2pa.hash.data",
                ["data"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["alg"] = "sha256",
                    ["hash"] = Str(sample, "digest"),
                    ["name"] = Str(sample, "path"),
                },
            });
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["claim_generator"] = "NarrativeForge/1.0 (nf interop --kind c2pa)",
            ["claim_generator_info"] = new List<object?>
            {
                new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["name"] = "NarrativeForge", ["version"] = "1.0.0",
                },
            },
            ["title"] = "NarrativeForge 协议层内容清单",
            ["format"] = "application/json",
            ["assertions"] = assertions,
            ["x-nf-package-status"] = "未封装（无 JUMBF/CBOR 容器）、未签名（无 X.509 证书链）——" +
                                      "只出 JSON 清单形状，不得当作可验证内容凭证",
            ["x-nf-source"] = "protocol/RECEIPTS.json（回执摘要）",
        };
    }

    /// <summary>回执 → CIDv1（multibase base32 / raw codec / sha2-256）。</summary>
    public static Dictionary<string, object?> Cid(string root)
    {
        var rec = ReadJson(root, ReceiptsRel);
        var entries = new List<object?>();
        foreach (var e in Entries(rec))
        {
            var d = Str(e, "digest");
            entries.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["path"] = Str(e, "path"),
                ["sha256"] = d,
                ["cid"] = Sha256Re.IsMatch(d) ? Cidv1RawSha256(d) : "",
            });
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = "nf-cid-index/1",
            ["multibase"] = "base32 (lowercase, no padding, prefix 'b')",
            ["codec"] = "raw (0x71)",
            ["multihash"] = "sha2-256 (0x12)",
            ["entries"] = entries,
            ["x-nf-note"] = "派生自 protocol/RECEIPTS.json；CID 可被 multiformats 生态直接校验。",
        };
    }

    /// <summary>CIDv1 raw codec + sha2-256（base32 小写去填充，前缀 'b'）。</summary>
    public static string Cidv1RawSha256(string digestHex)
    {
        var raw = Convert.FromHexString(digestHex);
        var payload = new byte[4 + raw.Length];
        payload[0] = 0x01;   // CID 版本 1
        payload[1] = 0x71;   // raw codec
        payload[2] = 0x12;   // sha2-256
        payload[3] = 0x20;   // 32 字节
        raw.CopyTo(payload, 4);
        return "b" + Base32Lower(payload);
    }

    /// <summary>RFC 4648 base32（无填充、小写）——Python <c>base64.b32encode(...).lower().rstrip("=")</c> 等价。</summary>
    private static string Base32Lower(byte[] data)
    {
        const string alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
        var sb = new StringBuilder();
        int bits = 0, value = 0;
        foreach (var b in data)
        {
            value = (value << 8) | b;
            bits += 8;
            while (bits >= 5)
            {
                sb.Append(alphabet[(value >> (bits - 5)) & 31]);
                bits -= 5;
            }
        }
        if (bits > 0) sb.Append(alphabet[(value << (5 - bits)) & 31]);
        return sb.ToString().ToLowerInvariant();
    }

    // ------------------------------------------------------------------ 工具

    /// <summary>仓内声明日期的最大值（YYYY-MM-DD）；取不到返回空串。</summary>
    public static string DeclaredMaxDate(string root)
    {
        var dates = new List<string>();
        foreach (var rel in new[] { "protocol/score_baseline.json", "05_资产库/provenance.json" })
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path)) continue;
            dates.AddRange(DateRe.Matches(StrictUtf8.GetString(File.ReadAllBytes(path))).Select(m => m.Value));
        }
        var adir = Path.Combine(root, "protocol", "approvals");
        if (Directory.Exists(adir))
        {
            foreach (var name in Directory.GetFiles(adir, "*.json").Select(f => Path.GetFileName(f) ?? "")
                         .OrderBy(n => n, StringComparer.Ordinal))
            {
                var path = Path.Combine(adir, name);
                dates.AddRange(DateRe.Matches(StrictUtf8.GetString(File.ReadAllBytes(path))).Select(m => m.Value));
            }
        }
        return dates.Count > 0 ? dates.Max(StringComparer.Ordinal)! : "";
    }

    /// <summary>基线真源 = <c>quality_baseline.EXPECTED_CHECKS / EXPECTED_PASS</c>（按同源常量解析）。</summary>
    public static (long Checks, long Pass) Baseline(string root)
    {
        var path = Path.Combine(root, "desktop", "src", "core", "quality_baseline.py");
        if (!File.Exists(path)) return (0, 0);
        var text = StrictUtf8.GetString(File.ReadAllBytes(path));
        var c = ExpectedChecksRe.Match(text);
        var p = ExpectedPassRe.Match(text);
        return (c.Success ? long.Parse(c.Groups[1].Value, CultureInfo.InvariantCulture) : 0,
                p.Success ? long.Parse(p.Groups[1].Value, CultureInfo.InvariantCulture) : 0);
    }

    private static List<Dictionary<string, object?>> Entries(Dictionary<string, object?> rec)
        => (rec.GetValueOrDefault("entries") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();

    private static string Str(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var v) && v is string s ? s : "";

    private static long ToLong(object? v) => v is null ? 0L : Convert.ToInt64(v, CultureInfo.InvariantCulture);

    private static string Short(string s, int n) => s.Length <= n ? s : s[..n];

    /// <summary>读 JSON（缺件 / 解析失败 → 空表；等价 Python <c>_read_json</c>）。</summary>
    public static Dictionary<string, object?> ReadJson(string root, string rel)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return new Dictionary<string, object?>(StringComparer.Ordinal);
        try
        {
            using var doc = JsonIo.ReadFile(path);
            return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        }
        catch (Exception exc) when (exc is System.Text.Json.JsonException or IOException)
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal);
        }
    }
}

/// <summary>
/// R5 依赖登记表的 C# 镜像（真源 = <c>core/purity_scan.py</c> 的 <c>HARD_ALLOW</c> / <c>SOFT_IMPORTS</c>）。
///
/// 纪律：这是**静态数据表**，不是代码分析——`purity-clean` 契约（AST 面）仍在范围外；
/// 本表按既有「镜像表机械导出」先例处理（导出件留 `_purity_tables.json.txt` 可复核）。
/// </summary>
public static class PurityTables
{
    public static (Dictionary<string, string> Hard, Dictionary<string, string> Soft) Entries { get; } =
        (new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["yaml"] = "PyYAML（仓库既有依赖；check16/28 同源解析，见 CONTRIBUTING §4.2 例外）",
        },
        new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["jsonschema"] = "IDL 标准实现交叉验证（可选对照；缺依赖则跳过该面）",
            ["PySide6"] = "CCV3 卡面占位图写入（缺依赖须给明确修复指引，不得裸 ImportError）",
            ["laya"] = "决策层本地服务（scripts/serve_decision_model.py）的模型运行时；软导入 + 缺依赖给修复指引",
        });
}
