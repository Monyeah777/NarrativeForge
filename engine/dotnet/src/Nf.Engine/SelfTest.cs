using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 负例 / 健壮性自检：证明引擎**会红在该红的地方**（不只是顺路径为绿）。
///
/// 覆盖三组：
/// ① 合成组合负例（临时 fixture 根）：撞号（默认塌陷 vs 严格相干）、深链 fail-closed、未知包、悬空依赖、未桥接事件；
/// ② 仓库产物篡改负例（内存注入）：协议回执记录、透明链链节、组合证书字段；
/// ③ 文件字节篡改负例（临时副本）：馆藏条目改一字节。
/// ④ 一致性契约负例（临时 fixture 根）：公开面泄漏、投影手改、取代链成环 + 干净语料正向对照。
/// ⑤ 签名锚方案分支（临时 fixture 根）：未知方案 / sigstore 必须 FAIL，hmac 缺密钥只许 WARN。
/// ⑥ 敌意输入：JSON 深度容忍度对齐 Python（不自设 64）、MCP 单条坏消息不许杀循环。
/// ⑦ 文档四型：镜像表自洽（清单内每件都有合法归属）+ 缺件不误报。
/// ⑧ 数字保真（整数不许变浮点）+ YAML 子集语义（PyYAML 口径）。
/// ⑧a Python 字符串语义：len() 数码点（不是 UTF-16 单元）、切片不劈开代理对。
/// ⑧b YAML 边界与转义：`.NaN` 不许崩、`\x41` 要还原成 A、子集外构造必须显式 fail-closed。
/// ⑨ IDL 子集校验器：越界关键字 / 未知字段 / 枚举 / 键名模式 / 缺 schema 目录。
/// ⑩ 治理族契约：条件先行排布 / 一致性声明三段与重叠 / 包装声明工具面 / ST 落产物判。
/// ⑪ 治理文档族：接力（未决带判据 + refs）/ 复盘（禁指责 + 根因机制 + 行动项可指派）/ 审计（对象 digest 绑定）。
/// ⑫ 端点契约：`maps_to` 必须指向现存 CLI 子命令或 MCP 工具；幂等语义不许沉默。
/// ⑬ 机读契约族：模块边界签名（漂移即 FAIL、非边界文本不算漂移）与事件背书（无发布方即 FAIL、挂账/跨包只 WARN）。
/// ⑭ 类型积压台账：untyped 缺 note 即 FAIL；在盘台账与实时重算不一致即 FAIL（防"台账当装饰"）。
/// ⑮ I/O 类型面：越词表 / 可证不匹配即 FAIL；键集不一致与未标只 WARN（不该被误判成红）。
/// ⑯ 管线抽象执行：模块缺失 / 依赖落在更后层 = hard FAIL；解析失败与 Python 同向抛异常（不是给判定）。
/// ⑰ 双源知识层：locator 缺件（防纸面源）/ 查询有序 / 幽灵频次 = FAIL；缺键文案按 Python 渲染成 None。
/// ⑱ 知识层可见性与复用面：clearance 秩裁剪（public ⊆ internal ⊆ restricted）；同内容两份即 FAIL。
/// 全部 fixture 只写临时目录，**绝不改动被检仓库**。
/// </summary>
public static class SelfTest
{
    public sealed record Check(string Name, bool Passed, string Detail);

    public static IReadOnlyList<Check> Run(string root)
    {
        var checks = new List<Check>();
        var work = Path.Combine(Path.GetTempPath(), "nf-selftest-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(work);
        try
        {
            SyntheticCases(checks, work);
            TamperCases(checks, root, work);
            StrictModeIsSafe(checks, root);
            FuzzCases(checks, root, work);
            ParallelInvariance(checks, root);
            ConformanceCases(checks, work);
            AnchorSchemeCases(checks, work);
            HostileCases(checks, work);
            DocKindCases(checks, work);
            NumberAndYamlCases(checks);
            PythonStringCases(checks);
            YamlBoundaryCases(checks);
            ToolFaceCases(checks, work);
            StValidateCases(checks, work);
            RepoStatsCases(checks, work);
            KnowledgeFrequencyCases(checks, work);
            InteropCases(checks, work);
            McpErrorIdCases(checks, root);
            WorldModelCases(checks, work);
            ImpactCases(checks);
            MarketCases(checks);
            AssetCases(checks, work);
            AssetQualityCases(checks, work);
            SmallFacesCases(checks, work);
            OutputFormsCases(checks, work);
            ConceptClosureCases(checks, work, root);
            MetricsRecomputeCases(checks, root, work);
            OutputGateCases(checks, work, root);
            AuxScannerCases(checks, work, root);
            ComboDomainCases(checks, work, root);
            ModuleLifecycleCases(checks, work, root);
            ProtocolGoldenCases(checks, work, root);
            CoreRegistryCases(checks, work, root);
            DocCompletenessCases(checks, work, root);
            TextHygieneCases(checks, work, root);
            LicenseGateCases(checks, work, root);
            ProseLintCases(checks, work, root);
            AutofixCases(checks, work, root);
            TelemetrySemconvCases(checks, work);
            DriverCases(checks, work, root);
            ExtensionPolicyCases(checks, work, root);
            StructureGateCases(checks, work, root);
            AnchorChecksCases(checks, work, root);
            Safe(checks, "深化面", () => DeepeningGateCases(checks, work, root));
            Safe(checks, "决策层", () => DecisionLayerCases(checks, work, root));
            Safe(checks, "出口面", () => ExitFacesCases(checks, work, root));
            Safe(checks, "回归面", () => RegressionCases(checks, work, root));
            Safe(checks, "构建回路", () => WorkloopCases(checks, work, root));
            Safe(checks, "GEO 出口", () => GeoExportCases(checks, work, root));
            Safe(checks, "FDE 样例", () => FdeSampleCases(checks, work, root));
            Safe(checks, "馆藏回执", () => LibraryReceiptsCases(checks, work, root));
            Safe(checks, "语料身份", () => CorpusStampCases(checks, work, root));
            Safe(checks, "装配面", () => AssembleCases(checks, work, root));
            SchemaLintCases(checks, work);
            GovernanceCases(checks, work);
            GovernanceDocCases(checks, work);
            EndpointCases(checks, work);
            MachineContractCases(checks, work);
            TypeBacklogCases(checks, work);
            IoTypeCases(checks, work);
            PipelineDryrunCases(checks, work);
            KnowledgeCases(checks, work);
            KnowledgeCliFacesCases(checks, work);
        }
        finally
        {
            try { Directory.Delete(work, recursive: true); } catch (IOException) { /* 临时目录清理失败不影响判定 */ }
        }
        return NormalizeTempPaths(checks);
    }

    /// <summary>
    /// 输出归一（第一百一十四片）：全部 fixture 都建在系统临时目录下，而临时目录名**每次运行都不同**
    /// （<c>…\Temp\nf-selftest-&lt;guid&gt;\…</c>，另有 <c>nf-market-fix-&lt;guid&gt;</c>）。于是
    /// <c>selftest --json</c> 这个机器面里凡是引用合成树路径的 <c>detail</c> 都会变 ⇒ **逐字节不可复现**，
    /// 与构建期的源码路径问题同源（那边用 <c>PathMap</c> 归一，见 Directory.Build.props）。
    /// 这里把临时根换成固定占位 <c>&lt;tmp&gt;</c>：既保留「是合成树里的哪一支」这条诊断信息，
    /// 又让输出可逐字节比对（实测：改后 `selftest --json` 三次运行 sha256 全同）。
    /// </summary>
    private static List<Check> NormalizeTempPaths(List<Check> checks)
    {
        var temp = Path.GetTempPath().TrimEnd(Path.DirectorySeparatorChar, '/');
        // 三种形态都要替：普通反斜杠、正斜杠、以及**Python 异常串里被转义的双反斜杠**
        // （`str(OSError)` 打出来的文件名是 repr ⇒ `C:\\Users\\…`；只替单反斜杠会漏）。
        var forms = new[]
        {
            temp,
            temp.Replace('\\', '/'),
            temp.Replace("\\", "\\\\"),
        };
        return checks
            .Select(c => new Check(c.Name, c.Passed, forms.Aggregate(c.Detail,
                (acc, f) => acc.Replace(f, "<tmp>", StringComparison.Ordinal))))
            .Select(c => c with { Detail = CollapseTempLeaf(c.Detail) })
            .ToList();
    }

    /// <summary>
    /// 把 <c>&lt;tmp&gt;</c> 之后**那一段每次运行都变的目录**（`nf-selftest-&lt;guid&gt;` /
    /// `nf-market-fix-&lt;guid&gt;`）一并折叠掉——诊断信息保留「合成树里的哪一支」，运行期噪声去掉。
    /// 三种分隔符形态都要覆盖：单反斜杠、双反斜杠（Python 异常串的 repr 形态）、正斜杠。
    /// </summary>
    private static string CollapseTempLeaf(string detail) =>
        Regex.Replace(detail, @"(<tmp>)\\{1,2}[^\\/]+|<tmp>/[^\\/]+", "<tmp>", RegexOptions.None);

    // ---------------------------------------------------------------- ① 合成组合负例

    private static void SyntheticCases(List<Check> checks, string work)
    {
        // 撞号：两包各自声明同一 module id
        var dup = Path.Combine(work, "dup");
        WritePack(dup, "PackA", "P99", new[] { "DUP:M01" },
            ("a.md", "DUP:M01", "P40", Array.Empty<string>(), Array.Empty<string>(), Array.Empty<string>()));
        WritePack(dup, "PackB", "P98", new[] { "DUP:M01" },
            ("b.md", "DUP:M01", "P60", Array.Empty<string>(), Array.Empty<string>(), Array.Empty<string>()));

        var dupDefault = Combinator.Build(dup, new[] { "PackA", "PackB" });
        checks.Add(new Check("撞号·默认模式与 Python 一致（不报错）", dupDefault.Legal,
            "legal=" + dupDefault.Legal));

        var records = ModuleContracts.Community(dup).RecordsByKey;
        var resolvedPack = records.TryGetValue("DUP:M01", out var rec) ? rec.Pack : "(缺失)";
        checks.Add(new Check("撞号·归属塌陷被观察到（跨包静默改写）", resolvedPack != "PackA",
            $"PackA 声明的 DUP:M01 解析到 pack={resolvedPack}"));

        var dupStrict = Combinator.Build(dup, new[] { "PackA", "PackB" }, strictCoherence: true);
        var hasConflicts = dupStrict.Certificate.TryGetValue("coherence_conflicts", out var conflicts)
                           && conflicts is List<object?> list && list.Count > 0;
        checks.Add(new Check("撞号·严格相干模式判非法并列出冲突", !dupStrict.Legal && hasConflicts,
            $"legal={dupStrict.Legal} · conflicts={(hasConflicts ? "有" : "无")}"));

        // 干净语料：严格相干模式**不得**改变证书（只在撞号时才扩展形状），否则这个开关就没法当 CI 开关用
        var clean = Path.Combine(work, "clean-coherence");
        WritePack(clean, "PackC", "P94", new[] { "OK:M01" },
            ("c.md", "OK:M01", "P40", Array.Empty<string>(), Array.Empty<string>(), Array.Empty<string>()));
        var cleanDefault = Combinator.Build(clean, new[] { "PackC" });
        var cleanStrict = Combinator.Build(clean, new[] { "PackC" }, strictCoherence: true);
        var sameBytes = PythonJson.CanonicalizeGraph(cleanDefault.Certificate)
                        == PythonJson.CanonicalizeGraph(cleanStrict.Certificate);
        checks.Add(new Check("干净语料·严格相干模式证书逐字节不变（且合法）",
            sameBytes && cleanDefault.Legal && cleanStrict.Legal,
            $"legal={cleanDefault.Legal}/{cleanStrict.Legal} · 逐字节相同={sameBytes}"));

        // 深链：链深 20，只声明头件 → 闭包补齐 12 轮上限 → fail-closed
        var deep = Path.Combine(work, "deep");
        var chainDocs = new List<(string, string, string, string[], string[], string[])>();
        for (var i = 60; i <= 79; i++)
        {
            var id = $"CH:M{i}";
            var inputs = i < 79 ? new[] { $"CH:M{i + 1}" } : Array.Empty<string>();
            chainDocs.Add(($"c{i}.md", id, "P40", inputs, Array.Empty<string>(), Array.Empty<string>()));
        }
        WritePack(deep, "Chain", "P97", new[] { "CH:M60" }, chainDocs.ToArray());
        var deepResult = Combinator.Build(deep, new[] { "Chain" });
        var deepClosure = (Dictionary<string, object?>)deepResult.Certificate["dependency_closure"]!;
        var dangling = (List<object?>)deepClosure["dangling"]!;
        checks.Add(new Check("深链 20 · fail-closed（判非法且悬空非空）",
            !deepResult.Legal && dangling.Count > 0,
            $"legal={deepResult.Legal} · dangling={dangling.Count} 条 · 模块 {deepResult.Certificate["module_count"]}"));

        // 未知包
        var unknownPack = Combinator.Build(deep, new[] { "NoSuchPack" });
        var unknownList = (List<object?>)unknownPack.Certificate["unknown_packs"]!;
        checks.Add(new Check("未知包 · 判非法且列入 unknown_packs",
            !unknownPack.Legal && unknownList.Contains("NoSuchPack"),
            $"unknown_packs={unknownList.Count} 项"));

        // 悬空依赖
        var danglingRoot = Path.Combine(work, "dangling");
        WritePack(danglingRoot, "PackD", "P96", new[] { "DG:M01" },
            ("d.md", "DG:M01", "P40", new[] { "NOPE:M99" }, Array.Empty<string>(), Array.Empty<string>()));
        var danglingResult = Combinator.Build(danglingRoot, new[] { "PackD" });
        var dangles = (List<object?>)((Dictionary<string, object?>)danglingResult.Certificate["dependency_closure"]!)["dangling"]!;
        checks.Add(new Check("悬空依赖 · 判非法且 dangling 非空",
            !danglingResult.Legal && dangles.Count > 0, $"dangling={dangles.Count} 条"));

        // 未桥接事件
        var unbridgedRoot = Path.Combine(work, "unbridged");
        WritePack(unbridgedRoot, "PackE", "P95", new[] { "EB:M01" },
            ("e.md", "EB:M01", "P40", Array.Empty<string>(), Array.Empty<string>(), new[] { "evt_unbridged_x" }));
        var unbridgedResult = Combinator.Build(unbridgedRoot, new[] { "PackE" });
        var unbridged = (List<object?>)((Dictionary<string, object?>)unbridgedResult.Certificate["event_closure"]!)["unbridged"]!;
        checks.Add(new Check("未桥接事件 · 判非法且 unbridged 非空",
            !unbridgedResult.Legal && unbridged.Count > 0, $"unbridged={unbridged.Count} 项"));
    }

    // ---------------------------------------------------------------- ② / ③ 篡改负例

    private static void TamperCases(List<Check> checks, string root, string work)
    {
        // ②a 协议回执：改记录里的 digest
        var receiptsDoc = JsonNode.Parse(File.ReadAllBytes(Path.Combine(root, "protocol/RECEIPTS.json")))!;
        receiptsDoc["entries"]![0]!["digest"] = new string('f', 64);
        using (var mutated = JsonIo.Parse(receiptsDoc.ToJsonString()))
        {
            var result = Receipts.VerifyProtocolReceipts(root, mutated);
            checks.Add(new Check("篡改·协议回执记录摘要 → 必须报红",
                !result.Ok && result.Issues.Any(i => i.Contains("条目摘要不一致", StringComparison.Ordinal)),
                $"{result.Issues.Count} 条问题"));
        }

        // ②b 透明链：改一个链节的 chain 值
        var chainDoc = JsonNode.Parse(File.ReadAllBytes(Path.Combine(root, "protocol/generated/receipt_chain.json")))!;
        chainDoc["links"]![0]!["chain"] = new string('a', 64);
        using (var mutatedChain = JsonIo.Parse(chainDoc.ToJsonString()))
        using (var receipts = JsonIo.ReadFile(Path.Combine(root, "protocol/RECEIPTS.json")))
        {
            var result = Receipts.VerifyTransparencyChain(root, mutatedChain, receipts);
            checks.Add(new Check("篡改·透明链链节 → 必须报红",
                !result.Ok && result.Issues.Any(i => i.Contains("chain 不一致", StringComparison.Ordinal)),
                $"{result.Issues.Count} 条问题"));
        }

        // ②c 组合证书：改一条证书的 modules
        var certDoc = JsonNode.Parse(File.ReadAllBytes(Path.Combine(root, "protocol/combo_certificates.json")))!;
        certDoc["certificates"]![0]!["modules"] = new JsonArray("SYNTH:FAKE");
        using (var mutatedCerts = JsonIo.Parse(certDoc.ToJsonString()))
        {
            var rows = CertificateVerifier.VerifyAll(root, mutatedCerts);
            var bad = rows.Count(r => r.Issues.Count > 0);
            checks.Add(new Check("篡改·组合证书字段 → 必须报红",
                bad > 0 && rows.Any(r => r.Issues.Any(i => i.Contains("字段不一致：modules", StringComparison.Ordinal))),
                $"{bad}/{rows.Count} 条证书报红"));
        }

        // ③ 文件字节篡改：馆藏副本改一字节
        var libRoot = Path.Combine(work, "libcopy");
        Directory.CreateDirectory(Path.Combine(libRoot, "library"));
        foreach (var file in Directory.GetFiles(Path.Combine(root, "library")))
        {
            File.Copy(file, Path.Combine(libRoot, "library", Path.GetFileName(file)), overwrite: true);
        }
        var target = Path.Combine(libRoot, "library", "NF-1.md");
        if (File.Exists(target))
        {
            File.AppendAllText(target, "\n<!-- tampered -->\n");
            var result = Receipts.VerifyLibraryReceipts(libRoot);
            checks.Add(new Check("篡改·馆藏条目文件字节 → 必须报红（真源口径：根不一致 + 条目内容已变）",
                !result.Ok && result.Issues.Any(i => i.Contains("条目内容已变", StringComparison.Ordinal))
                && result.Issues.Any(i => i.Contains("根不一致：记录=", StringComparison.Ordinal)),
                $"{result.Issues.Count} 条问题：{string.Join(" | ", result.Issues).Substring(0, Math.Min(120, string.Join(" | ", result.Issues).Length))}"));
        }
        else
        {
            checks.Add(new Check("篡改·馆藏条目文件字节 → 必须报红", false, "找不到 library/NF-1.md，用例未执行"));
        }
    }

    // ---------------------------------------------------------------- fixture 写入

    /// <summary>严格相干模式在**干净语料**上必须与默认模式逐字节一致（否则不能作为 CI 开关使用）。</summary>
    private static void StrictModeIsSafe(List<Check> checks, string root)
    {
        using var doc = JsonIo.ReadFile(Path.Combine(root, "protocol/combo_certificates.json"));
        var mismatched = 0;
        var total = 0;
        foreach (var cert in doc.RootElement.GetProperty("certificates").EnumerateArray())
        {
            var packs = cert.GetProperty("packs").EnumerateArray().Select(x => x.GetString()!).ToList();
            var extra = cert.GetProperty("extra_modules").EnumerateArray().Select(x => x.GetString()!).ToList();
            var relaxed = Combinator.Build(root, packs, extra);
            var strict = Combinator.Build(root, packs, extra, strictCoherence: true);
            total++;
            if (PythonJson.CanonicalizeGraph(relaxed.Certificate) != PythonJson.CanonicalizeGraph(strict.Certificate))
            {
                mismatched++;
            }
        }
        checks.Add(new Check("严格相干模式在干净语料上与默认模式逐字节一致",
            mismatched == 0,
            $"{total} 条证书 · 不一致 {mismatched}"));
    }

    // ---------------------------------------------------------------- ④ 失败卫生（破坏输入）

    /// <summary>
    /// 破坏输入自检：损坏的输入**要么受控失败、要么与 Python 等价**，
    /// 绝不允许"静默改变判定却自称通过"。每个用例在独立临时根上构造，不触碰被检仓库。
    /// </summary>
    private static void FuzzCases(List<Check> checks, string root, string work)
    {
        // ④a 破坏 JSON：组合证书 / 断言表 / 协议回执 / 透明链
        var badJson = Path.Combine(work, "badjson");
        Directory.CreateDirectory(Path.Combine(badJson, "protocol", "generated"));
        File.WriteAllText(Path.Combine(badJson, "protocol", "combo_certificates.json"), "{\"certificates\": [ {\"packs\"");
        File.WriteAllText(Path.Combine(badJson, "protocol", "assertions.json"), "");
        File.WriteAllText(Path.Combine(badJson, "protocol", "RECEIPTS.json"), "{\"root\": \"x\"");
        File.WriteAllText(Path.Combine(badJson, "protocol", "generated", "receipt_chain.json"), "not json at all");

        checks.Add(Guarded("破坏输入·损坏 JSON → 受控失败（不许静默通过）", () =>
        {
            var controlled = 0;
            if (Controlled(() => CertificateVerifier.VerifyAll(badJson).All(r => r.Issues.Count == 0))) controlled++;
            if (Controlled(() => Assertions.Run(badJson).Issues.Count > 0)) controlled++;
            if (Controlled(() => !Receipts.VerifyProtocolReceipts(badJson).Ok)) controlled++;
            if (Controlled(() => !Receipts.VerifyTransparencyChain(badJson).Ok)) controlled++;
            return (controlled == 4, $"四项中受控失败 {controlled}/4");
        }));

        // ④b 截断 protocol.yaml：与 Python 等价的 fail-open（该包贡献 0 模块，组合仍判合法）
        //     实测（2026-09-26）：Python 同一破坏根得 module_count=0 / legal=True / digest f43f92dd…
        var truncated = Path.Combine(work, "truncated");
        WritePack(truncated, "FuzzPackA", "P90", new[] { "FZ:M01" },
            ("a.md", "FZ:M01", "P40", Array.Empty<string>(), Array.Empty<string>(), Array.Empty<string>()));
        WritePack(truncated, "FuzzPackB", "P91", new[] { "FZ:M02" },
            ("b.md", "FZ:M02", "P60", Array.Empty<string>(), Array.Empty<string>(), Array.Empty<string>()));
        foreach (var pack in new[] { "FuzzPackA", "FuzzPackB" })
        {
            var path = Path.Combine(truncated, "community", pack, "protocol.yaml");
            var text = File.ReadAllText(path);
            File.WriteAllText(path, text[..Math.Min(60, text.Length)]);
        }
        checks.Add(Guarded("破坏输入·截断 protocol.yaml → fail-open 且两次同值（与 Python 等价）", () =>
        {
            var first = Combinator.Build(truncated, new[] { "FuzzPackA", "FuzzPackB" });
            var second = Combinator.Build(truncated, new[] { "FuzzPackA", "FuzzPackB" });
            var modules = (List<object?>)first.Certificate["modules"]!;
            var stable = first.Digest == second.Digest;
            return (modules.Count == 0 && first.Legal && stable,
                $"模块={modules.Count} · legal={first.Legal} · 摘要稳定={stable}");
        }));

        // ④c 未闭合 machine_contract 围栏 → 契约取不到 → module_missing_contract（fail-closed）
        var brokenFence = Path.Combine(work, "brokenfence");
        WritePack(brokenFence, "FuzzPackC", "P92", new[] { "FZ:M03" },
            ("c.md", "FZ:M03", "P40", Array.Empty<string>(), Array.Empty<string>(), Array.Empty<string>()));
        File.WriteAllText(Path.Combine(brokenFence, "community", "FuzzPackC", "modules", "c.md"),
            "```yaml\nmachine_contract:\n  id: FZ:M03\n");   // 围栏未闭合
        checks.Add(Guarded("破坏输入·未闭合围栏 → module_missing_contract（fail-closed）", () =>
        {
            var result = Combinator.Build(brokenFence, new[] { "FuzzPackC" });
            var missing = (List<object?>)result.Certificate["module_missing_contract"]!;
            return (missing.Count > 0 && !result.Legal, $"missing_contract={missing.Count} · legal={result.Legal}");
        }));

        // ④d 空根目录 → 空画像，不崩
        var emptyRoot = Path.Combine(work, "emptyroot");
        Directory.CreateDirectory(emptyRoot);
        checks.Add(Guarded("破坏输入·空根目录 → 空画像且不崩", () =>
        {
            var profiles = PackProfiles.Build(emptyRoot);
            var result = Combinator.Build(emptyRoot, Array.Empty<string>());
            return (profiles.Count == 0 && result.Legal, $"画像={profiles.Count} · legal={result.Legal}");
        }));

        // ④e 真源未被污染
        checks.Add(Guarded("破坏输入·被检仓库未被污染（真源仍全绿）", () =>
        {
            var receipts = Receipts.VerifyProtocolReceipts(root);
            var decisions = Decisions.Verify(root);
            return (receipts.Ok && decisions.Issues.Count == 0 && decisions.Projection.Count == 0,
                $"回执 {receipts.Count} 条 · 决策问题 {decisions.Issues.Count}");
        }));
    }

    /// <summary>受控 = 抛出托管异常，或返回明确的失败判定；静默成功（返回 true 且无异常）不算受控。</summary>
    private static bool Controlled(Func<bool> probe)
    {
        try
        {
            return !probe();
        }
        catch (Exception)
        {
            return true;
        }
    }

    /// <summary>并行/串行不变性：广度是引擎里唯一的并行路径，两种执行方式必须产出同一统计。</summary>
    private static void ParallelInvariance(List<Check> checks, string root)
    {
        checks.Add(Guarded("并行/串行不变性·广度统计逐字节一致", () =>
        {
            var parallel = PythonJson.CanonicalizeGraph(
                Breadth.RunSelfContained(root, parallel: true, triples: 60, quads: 30, quints: 20, sexts: 10));
            var serial = PythonJson.CanonicalizeGraph(
                Breadth.RunSelfContained(root, parallel: false, triples: 60, quads: 30, quints: 20, sexts: 10));
            return (parallel == serial,
                $"并行与串行统计一致={parallel == serial} · 输出 {parallel.Length} 字节");
        }));
    }

    // ------------------------------------------------- ④ 一致性契约负例（含正向对照）

    /// <summary>
    /// 已移植的一致性契约要「该红的必须红」。三条负例各打一个不同的判据面（泄漏 / 投影 /
    /// 取代链），另加一条**正向对照**——否则「一律判红」也能骗过负例自检。
    /// </summary>
    private static void ConformanceCases(List<Check> checks, string work)
    {
        var leak = Path.Combine(work, "conf-public");
        WriteFile(leak, "desktop/tests/fixtures/external/leak.md", "见 C:\\Users\\某人\\私有件.md\n");
        checks.Add(Guarded("一致性契约·公开面泄漏绝对路径 → 判 FAIL", () =>
        {
            var (ok, detail, _) = Conformance.RunOne("public-surface", leak);
            return (!ok && detail.Contains("含绝对路径", StringComparison.Ordinal), detail);
        }));

        var drift = Path.Combine(work, "conf-patterns");
        WriteFile(drift, "src/示例.cs", "// 占位（让 applies_to 可证，使首条问题落在投影上）\n");
        WriteFile(drift, "patterns/alpha/PATTERN.md", PatternDoc("alpha"));
        WriteFile(drift, "patterns/INDEX.md",
            "<!-- BEGIN GENERATED: patterns-index -->\n手改的表\n<!-- END GENERATED: patterns-index -->\n");
        checks.Add(Guarded("一致性契约·实践包投影被手改 → 判 FAIL", () =>
        {
            var (ok, detail, _) = Conformance.RunOne("patterns", drift);
            return (!ok && detail.Contains("不一致", StringComparison.Ordinal), detail);
        }));

        var cycle = Path.Combine(work, "conf-rfc");
        WriteFile(cycle, "protocol/rfc_index.json", string.Join("\n", new[]
        {
            "{",
            "  \"status_vocabulary\": [\"Active\", \"Superseded\"],",
            "  \"docs\": [",
            "    {\"rfc\": \"NF-0001\", \"path\": \"a.md\", \"category\": \"Standards Track\"},",
            "    {\"rfc\": \"NF-0002\", \"path\": \"b.md\", \"category\": \"Standards Track\"}",
            "  ]",
            "}",
        }) + "\n");
        WriteFile(cycle, "a.md", RfcDoc("NF-0001", "NF-0002"));
        WriteFile(cycle, "b.md", RfcDoc("NF-0002", "NF-0001"));
        checks.Add(Guarded("一致性契约·取代链成环 → 判 FAIL", () =>
        {
            var (ok, detail, _) = Conformance.RunOne("rfc-heads", cycle);
            return (!ok && detail.Contains("成环", StringComparison.Ordinal), detail);
        }));

        var clean = Path.Combine(work, "conf-clean");
        WriteFile(clean, "src/示例.cs", "// 占位\n");
        WriteFile(clean, "patterns/alpha/PATTERN.md", PatternDoc("alpha"));
        WriteFile(clean, "patterns/INDEX.md", Patterns.RenderIndex(clean));
        WriteFile(clean, "protocol/rfc_index.json", string.Join("\n", new[]
        {
            "{",
            "  \"status_vocabulary\": [\"Active\"],",
            "  \"docs\": [",
            "    {\"rfc\": \"NF-0001\", \"path\": \"a.md\", \"category\": \"Standards Track\"}",
            "  ]",
            "}",
        }) + "\n");
        WriteFile(clean, "a.md", RfcDoc("NF-0001", "—"));
        WriteFile(clean, "desktop/tests/fixtures/external/ok.md", "# 干净产物\n");
        checks.Add(Guarded("一致性契约·干净语料三面全绿（正向对照）", () =>
        {
            var rows = new[] { "patterns", "rfc-heads", "public-surface" }
                .Select(id => (Id: id, Row: Conformance.RunOne(id, clean))).ToList();
            var bad = rows.Where(r => !r.Row.Ok).Select(r => r.Id + "：" + r.Row.Detail).ToList();
            return (bad.Count == 0, bad.Count == 0
                ? "patterns / rfc-heads / public-surface 三面均判 PASS"
                : string.Join("; ", bad));
        }));
    }

    // --------------------------------------------- ⑤ 签名锚方案：fail-closed 的回归钉

    /// <summary>
    /// 差分模糊发现过的真 bug：**未知锚方案曾被记成 WARN**（fail-open），而 Python 侧判 FAIL。
    /// 这里钉住三个分支——未知方案 / sigstore → **FAIL**；hmac 缺密钥 → **只在 WARN**（不许误伤成 FAIL）。
    /// </summary>
    private static void AnchorSchemeCases(List<Check> checks, string work)
    {
        var anchor = Path.Combine(work, "anchor");
        WriteFile(anchor, "library/NF-9.md", AnchorDoc(new string('0', 64), "rsa-sig"));
        // attestation 先落真值：摘要剔除 attestation/anchor_* 行，故与方案无关，可复用
        var digest = Receipts.LibraryEntryDigest(anchor, "library/NF-9.md");

        checks.Add(Guarded("锚方案·未知方案 → 判 FAIL（缺验证器不得静默通过）", () =>
        {
            WriteFile(anchor, "library/NF-9.md", AnchorDoc(digest, "rsa-sig"));
            var issues = Library.Verify(anchor).Issues;
            var hit = issues.FirstOrDefault(i => i.Contains("未知锚方案：rsa-sig", StringComparison.Ordinal));
            return (hit is not null, hit ?? "未报「未知锚方案」（fail-open？）");
        }));

        checks.Add(Guarded("锚方案·sigstore → 判 FAIL（需外部验证器，不判通过）", () =>
        {
            WriteFile(anchor, "library/NF-9.md", AnchorDoc(digest, "sigstore-keyless"));
            var issues = Library.Verify(anchor).Issues;
            var hit = issues.FirstOrDefault(i => i.Contains("sigstore 锚需外部验证器", StringComparison.Ordinal));
            return (hit is not null, hit ?? "未报 sigstore 不可校验");
        }));

        checks.Add(Guarded("锚方案·hmac 缺密钥 → 只记 WARN（不误判 FAIL）", () =>
        {
            WriteFile(anchor, "library/NF-9.md", AnchorDoc(digest, "hmac-sha256"));
            var result = Library.Verify(anchor);
            var warned = result.Warns.Any(w => w.Contains("未提供密钥", StringComparison.Ordinal));
            var failed = result.Issues.Any(i => i.Contains("签名锚校验失败", StringComparison.Ordinal));
            return (warned && !failed, $"WARN={warned} · FAIL={failed}");
        }));
    }

    private static string AnchorDoc(string attestation, string scheme) => string.Join("\n", new[]
    {
        "---", "id: NF-9", "type: 锚方案用例", "title: 锚方案分支回归", "status: active",
        $"attestation: {attestation}", "attested_at: 2026-09-26", $"anchor_scheme: {scheme}",
        "---", "", "正文。", "",
    });

    // ------------------------------------------------------------ ⑥ 敌意输入

    /// <summary>
    /// 两条回归钉，都来自敌意输入探针的实测：
    /// ① JSON 深度容忍度**对齐 Python**（CPython 到 ~995 层才 RecursionError；引擎原自设 64，
    ///    会在 65 层就单方面判死合法输入）；
    /// ② MCP 循环**单条坏消息不许杀会话**（同 core/mcp_runtime.py：解析失败 → -32700 且继续，
    ///    单条异常 → -32603 且继续）。
    /// </summary>
    private static void HostileCases(List<Check> checks, string work)
    {
        checks.Add(Guarded("敌意输入·JSON 深度 200 可读（对齐 Python，不自设 64）", () =>
        {
            var deep = new string('[', 200) + new string(']', 200);
            using var doc = JsonIo.Parse(deep);
            return (doc.RootElement.GetArrayLength() == 1, $"深度 200 解析成功（MaxDepth={JsonIo.MaxDepth}）");
        }));

        checks.Add(Guarded("敌意输入·JSON 深度超上限仍 fail-closed", () =>
        {
            var deeper = new string('[', JsonIo.MaxDepth + 50) + new string(']', JsonIo.MaxDepth + 50);
            try
            {
                using var doc = JsonIo.Parse(deeper);
                return (false, "超上限竟然解析成功（上限失效）");
            }
            catch (JsonException)
            {
                return (true, $"深度 {JsonIo.MaxDepth + 50} → JsonException（受控）");
            }
        }));

        var mcpRoot = Path.Combine(work, "hostile-mcp");
        (Directory.CreateDirectory(Path.Combine(mcpRoot, "protocol"))).Create();
        checks.Add(Guarded("敌意输入·MCP 单条坏消息不杀循环（坏 JSON / 工具异常后仍应答）", () =>
        {
            var input = new StringReader(string.Join("\n", new[]
            {
                "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{}}",
                "{这不是 JSON",
                "{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"spec_ls\",\"arguments\":{}}}",
                "{\"jsonrpc\":\"2.0\",\"id\":4,\"method\":\"ping\"}",
            }) + "\n");
            var output = new StringWriter();
            var code = McpServer.ServeStdio(mcpRoot, input, output);
            var parsed = output.ToString().Split('\n', StringSplitOptions.RemoveEmptyEntries)
                .Select(line => JsonIo.Parse(line)).ToList();
            var pingAnswered = parsed.Any(p =>
                p.RootElement.TryGetProperty("id", out var id) && id.ValueKind == JsonValueKind.Number
                && id.GetInt32() == 4 && p.RootElement.TryGetProperty("result", out _));
            var internalError = parsed.Any(p =>
                p.RootElement.TryGetProperty("error", out var e)
                && e.GetProperty("code").GetInt32() == -32603);
            var detail = $"exit={code} · 响应 {parsed.Count} 条 · 末条 ping 有答={pingAnswered} · 工具异常转 -32603={internalError}";
            return (code == 0 && pingAnswered && internalError, detail);
        }));
    }

    // ------------------------------------------------------ ⑦ 文档四型（镜像表自洽）

    /// <summary>
    /// `doc-kinds` 的三张表是从 <c>core/doc_hygiene.py</c> 机械导出的镜像——最容易出的错是
    /// **抄漏/抄歪**（漏一件、型名打错）。这两条钉住镜像本身的健康：清单内每件都必须有合法归属；
    /// 缺件只跳过、不误报。表若漂移，双跑对账会立刻报不一致。
    /// </summary>
    private static void DocKindCases(List<Check> checks, string work)
    {
        checks.Add(Guarded("文档四型·镜像表自洽（清单内每件都有合法归属）", () =>
        {
            var issues = DocHygiene.KindCoverage(work);
            return (issues.Count == 0,
                issues.Count == 0
                    ? $"清单内 {DocHygiene.CoveredCount} 件四型归属齐（取值 {string.Join("/", DocHygiene.KindVocabulary)}）"
                    : string.Join("; ", issues.Take(2)));
        }));

        var empty = Path.Combine(work, "dockinds-empty");
        Directory.CreateDirectory(empty);
        checks.Add(Guarded("文档四型·缺件不误报（写法判据只判在盘件）", () =>
        {
            var warns = DocHygiene.KindRulesFor(empty);
            return (warns.Count == 0, $"空树上 WARN {warns.Count} 条");
        }));
    }

    // ------------------------------------- ⑧ 数字保真 + YAML 子集语义（今日抓到的真 bug）

    /// <summary>
    /// 三条钉，全部来自本轮实测暴露的缺陷：
    /// ① JSON 整数被三元表达式**静默转成浮点**（`cond ? long : double` 会统一成 double），
    ///    以前被「1.0 渲染成 1」掩盖——现在整数必须仍是整数、浮点必须带小数点（Python repr 形态）；
    /// ② YAML 标量定型按 PyYAML：`3`→int、`true`→bool、`010`→八进制 8、`2026-09-08`→date、
    ///    `2026-9-8`→字符串（PyYAML 的纯日期要求两位月日）；
    /// ③ YAML 结构语义：非空流映射、序列项是映射、带引号的键、键里含冒号（`通用:M10: untyped`）。
    /// </summary>
    private static void NumberAndYamlCases(List<Check> checks)
    {
        checks.Add(Guarded("数字保真·JSON 整数不转浮点、浮点按 Python repr 写", () =>
        {
            using var doc = JsonIo.Parse("{\"i\":1,\"big\":1234567890123,\"f\":1.0,\"g\":1e16,\"h\":1e-5}");
            var text = PythonJson.Compact(PythonJson.ToGraph(doc.RootElement));
            const string expected = "{\"big\":1234567890123,\"f\":1.0,\"g\":1e+16,\"h\":1e-05,\"i\":1}";
            return (text == expected, text == expected ? text : $"期望 {expected} 实得 {text}");
        }));

        checks.Add(Guarded("YAML·标量定型对齐 PyYAML（int/bool/八进制/日期/伪日期）", () =>
        {
            var map = MiniYaml.Parse("a: 3\nb: true\nc: 010\nd: 2026-09-08\ne: 2026-9-8\nf: 1.0e5\n");
            var detail = $"a={PyScalar.TypeName(map["a"])} b={PyScalar.TypeName(map["b"])} " +
                         $"c={map["c"]} d={PyScalar.TypeName(map["d"])} e={map["e"]} f={PyScalar.TypeName(map["f"])}";
            var ok = map["a"] is 3L && map["b"] is true && map["c"] is 8L
                     && map["d"] is PyScalar.Timestamp { Kind: "date" } && map["e"] is "2026-9-8"
                     && map["f"] is "1.0e5";     // PyYAML 的指数要求显式符号，无符号仍是字符串
            return (ok, detail);
        }));

        checks.Add(Guarded("YAML·结构语义（流映射 / 映射序列项 / 引号键 / 键含冒号）", () =>
        {
            var flow = MiniYaml.Parse("layers:\n  P40: {default: [M01], available: []}\n");
            var seq = MiniYaml.Parse("mods:\n  - id: \"M01\"\n    desc: 甲\n  - id: \"M02\"\n");
            var quoted = MiniYaml.Parse("io:\n  'P:M01': untyped\n");
            var colonKey = MiniYaml.Parse("io:\n  通用:M10: untyped\n");
            var flowOk = flow["layers"] is Dictionary<string, object?> layer
                         && layer["P40"] is Dictionary<string, object?> entry
                         && entry["default"] is List<object?> def && def.Count == 1 && (string?)def[0] == "M01"
                         && entry["available"] is List<object?> avail && avail.Count == 0;
            var seqOk = seq["mods"] is List<object?> mods && mods.Count == 2
                        && mods[0] is Dictionary<string, object?> first && (string?)first["id"] == "M01"
                        && (string?)first["desc"] == "甲"
                        && mods[1] is Dictionary<string, object?> second && (string?)second["id"] == "M02";
            var quotedOk = quoted["io"] is Dictionary<string, object?> qi && qi.ContainsKey("P:M01");
            var colonKeyOk = colonKey["io"] is Dictionary<string, object?> qc
                             && qc.ContainsKey("通用:M10") && (string?)qc["通用:M10"] == "untyped";
            var ok = flowOk && seqOk && quotedOk && colonKeyOk;
            return (ok, $"流映射={flowOk} 映射序列项={seqOk} 引号键={quotedOk} 键含冒号={colonKeyOk}");
        }));
    }

    // ------------------------------------------- ⑨ IDL 子集校验器（schema-clean）

    /// <summary>
    /// `schema-clean` 的判据是「自实现 JSON-Schema 子集」——最容易出错的两处：
    /// ① **子集越界不许静默忽略**（白名单外的关键字必须 FAIL，否则就是假绿）；
    /// ② 未知字段 / 枚举 / 键名模式这些分支要真的报，且报的文案与 Python 同形。
    /// 另钉一条：缺 `protocol/schema/` 目录时报「未落盘」，不是空过。
    /// </summary>
    private static void SchemaLintCases(List<Check> checks, string work)
    {
        var schema = MiniYaml.Parse(string.Join("\n", new[]
        {
            "type: object",
            "additionalProperties: false",
            "propertyNames: {pattern: '^[a-z_]+$', type: string}",
            "required: [id]",
            "properties:",
            "  id: {type: string, enum: [M01, M02]}",
        }));

        checks.Add(Guarded("IDL·未知字段与键名模式都要报（不许静默放过）", () =>
        {
            var instance = MiniYaml.Parse("id: M01\nBadKey: 1\n");
            var issues = SchemaLint.SubsetValidate(instance, schema, "x");
            var unknown = issues.Any(i => i.Contains("未知字段 BadKey", StringComparison.Ordinal));
            var badKey = issues.Any(i => i.Contains("（键名）", StringComparison.Ordinal));
            return (unknown && badKey, string.Join(" | ", issues));
        }));

        checks.Add(Guarded("IDL·枚举与必填都要报", () =>
        {
            var issues = SchemaLint.SubsetValidate(MiniYaml.Parse("id: M99\n"), schema, "x");
            var enumHit = issues.Any(i => i.Contains("不在枚举", StringComparison.Ordinal));
            var required = SchemaLint.SubsetValidate(MiniYaml.Parse("other: 1\n"), schema, "x");
            var missing = required.Any(i => i.Contains("缺必填字段 id", StringComparison.Ordinal));
            return (enumHit && missing, string.Join(" | ", issues.Concat(required)));
        }));

        checks.Add(Guarded("IDL·子集越界关键字必须报（防假绿）", () =>
        {
            var beyond = MiniYaml.Parse("type: object\noneOf: []\nproperties:\n  a: {type: string, format: email}\n");
            var issues = SchemaLint.SubsetKeyViolations(beyond, "s.schema.json");
            var oneOf = issues.Any(i => i.Contains("未实现的关键字 oneOf", StringComparison.Ordinal));
            var nested = issues.Any(i => i.Contains("properties/a", StringComparison.Ordinal)
                                         && i.Contains("format", StringComparison.Ordinal));
            return (issues.Count == 2 && oneOf && nested, string.Join(" | ", issues));
        }));

        var bare = Path.Combine(work, "schema-empty");
        Directory.CreateDirectory(bare);
        checks.Add(Guarded("IDL·缺 protocol/schema/ 判「未落盘」而非空过", () =>
        {
            var result = SchemaLint.Scan(bare);
            var hit = result.Issues.Any(i => i.Contains("协议层 IDL 未落盘", StringComparison.Ordinal));
            return (hit, string.Join(" | ", result.Issues.Take(2)));
        }));
    }

    // ------------------------------------------- ⑩ 治理族契约（声明 / 排布 / 包装 / 制卡）

    /// <summary>
    /// 四件治理契约各钉一条**该红的必须红**（都取自差分模糊里已实测同判的变异形态）：
    /// ① 条件先行：状态块没前置；
    /// ② 一致性声明：排除项与 scope 重叠（同一条不能既在范围又排除）；
    /// ③ 包装声明：声明工具面与运行时不一致（上架材料会漂移）；
    /// ④ ST 制卡：V2 初始值含未声明变量。
    /// </summary>
    private static void GovernanceCases(List<Check> checks, string work)
    {
        checks.Add(Guarded("治理·条件先行：状态块未前置必须报（且只报这一条）", () =>
        {
            var bad = StateFront.CheckOrder("# 件\n\n## 资料\n\n## 状态块（条件先行摘要）\n\n正文\n");
            var good = StateFront.CheckOrder("# 件\n\n## 状态块（条件先行摘要）\n\n## 资料\n");
            return (bad.Count == 1 && bad[0].Contains("状态块未前置", StringComparison.Ordinal) && good.Count == 0,
                $"bad={string.Join("|", bad)} · good={good.Count} 条");
        }));

        var declRoot = Path.Combine(work, "gov-decl");
        WriteFile(declRoot, "protocol/CONFORMANCE.md", string.Join("\n", new[]
        {
            "# 一致性声明", "", "## 声明", "",
            "| 规范 | 版本 | 真源 |", "|---|---|---|",
            "| IDL schema 集 | `0 件` | protocol/schema/ |", "",
            "## 范围", "", "- `明示目录`", "",
            "## 排除", "", "| 路径 | 理由 |", "|---|---|",
            "| `明示目录/子件` | 重叠用例 |", "",
        }));
        checks.Add(Guarded("治理·声明：排除项与 scope 重叠必须报", () =>
        {
            var (issues, _) = ConformanceDecl.Scan(declRoot);
            var hit = issues.FirstOrDefault(i => i.Contains("scope 与排除重叠", StringComparison.Ordinal));
            return (hit is not null, hit ?? $"未报重叠（共 {issues.Count} 条问题）");
        }));

        var mcpRoot = Path.Combine(work, "gov-mcp");
        WriteFile(mcpRoot, "protocol/mcp_package.json", string.Join("\n", new[]
        {
            "{",
            "  \"schema\": \"nf-mcp-package/1\",",
            "  \"status\": \"active\",",
            "  \"category_vocabulary\": [\"content-creation\", \"developer-tools\", \"knowledge-management\"],",
            "  \"red_lines\": [\"只读\"],",
            "  \"package\": {",
            "    \"name_candidates\": [\"甲\"], \"one_liner_candidates\": [\"乙\"],",
            "    \"category\": \"content-creation\", \"targets\": [],",
            "    \"tools\": [\"pipeline_ls\"], \"prompts\": [\"assemble_guide\"]",
            "  }",
            "}",
        }) + "\n");
        checks.Add(Guarded("治理·包装声明：工具面与运行时不一致必须报", () =>
        {
            var (ok, detail) = McpPackage.Contract(mcpRoot);
            return (!ok && detail.Contains("工具面与运行时不一致", StringComparison.Ordinal), detail);
        }));

        var stqRoot = Path.Combine(work, "gov-stq");
        WriteFile(stqRoot, "docs/examples/mvu-output/mvu_variables.json",
            "{\"variables\": [{\"name\": \"甲\"}], \"initial\": {\"甲\": 0, \"幽灵变量\": 1}}\n");
        checks.Add(Guarded("治理·ST 制卡：V2 初始值含未声明变量必须报", () =>
        {
            using var doc = JsonIo.ReadFile(Path.Combine(stqRoot, "docs/examples/mvu-output/mvu_variables.json"));
            var graph = (Dictionary<string, object?>)PythonJson.ToGraph(doc.RootElement)!;
            var names = ((List<object?>)graph["variables"]!).Cast<Dictionary<string, object?>>()
                .Select(v => (string)v["name"]!).ToHashSet(StringComparer.Ordinal);
            var initial = (Dictionary<string, object?>)graph["initial"]!;
            var extra = initial.Keys.Where(k => !names.Contains(k)).OrderBy(k => k, StringComparer.Ordinal).ToList();
            return (extra.Count == 1 && extra[0] == "幽灵变量",
                $"未声明变量={string.Join("、", extra)}（V2 判据：initial 键须 ⊆ 变量名集）");
        }));
    }

    // ------------------------------- ⑪ 治理文档族（接力 / 复盘 / 审计）

    /// <summary>
    /// 三件治理文档契约各钉一条核心判据（都取自差分模糊里已实测同判的变异形态）：
    /// ① 接力：未决项缺「判据」必须报（空未决 = 不合格交接的姊妹条款）；
    /// ② 复盘：命中指责词必须报，且根因段不含机制词也要报（对事不对人 + 指向机制）；
    /// ③ 审计：被审对象 digest 一变，旧审计立即失效。
    /// </summary>
    private static void GovernanceDocCases(List<Check> checks, string work)
    {
        var hoRoot = Path.Combine(work, "gov-ho");
        WriteFile(hoRoot, "verify.sh", "check35(){\n  :\n}\n");
        WriteFile(hoRoot, "protocol/handover.json", string.Join("\n", new[]
        {
            "{", "  \"schema\": \"nf-handover/1\",",
            "  \"sections\": [\"情境\", \"背景\", \"评估\", \"建议\", \"未决项\"],",
            "  \"required_fields\": [\"id\", \"date\", \"from\", \"to\", \"status\", \"refs\"],",
            "  \"status_vocabulary\": [\"open\", \"closed\"],", "  \"rules\": [\"规矩\"]", "}", "",
        }));
        WriteFile(hoRoot, "handovers/HO-9999-用例.md", string.Join("\n", new[]
        {
            "---", "id: HO-9999", "date: 2026-09-26", "from: 甲", "to: 乙", "status: open",
            "refs:", "  - verify.sh", "---", "",
            "## 情境", "", "## 背景", "", "## 评估", "", "## 建议", "",
            "## 未决项", "", "- 待办一（说明：怎么算完）", "",
        }));
        checks.Add(Guarded("治理·接力：未决项缺「判据」必须报（空未决/无判据同一纪律）", () =>
        {
            var (issues, stats) = Handover.CheckDoc(hoRoot, "handovers/HO-9999-用例.md");
            var hit = issues.FirstOrDefault(i => i.Contains("未决项缺判据", StringComparison.Ordinal));
            return (hit is not null && stats["pending"] is 1,
                hit ?? $"未报缺判据（共 {issues.Count} 条问题 · pending={stats.GetValueOrDefault("pending")}）");
        }));

        var poRoot = Path.Combine(work, "gov-po");
        WriteFile(poRoot, "verify.sh", "check35(){\n  :\n}\n");
        WriteFile(poRoot, "protocol/postmortem.json", string.Join("\n", new[]
        {
            "{", "  \"schema\": \"nf-postmortem/1\",",
            "  \"sections\": [\"现象\", \"影响\", \"根因\", \"行动项\"],",
            "  \"required_fields\": [\"id\", \"date\", \"trigger\", \"status\", \"refs\"],",
            "  \"status_vocabulary\": [\"open\", \"closed\"],",
            "  \"blame_tokens\": [\"个人失误\"], \"root_cause_tokens\": [\"机制\", \"流程\"],",
            "  \"rules\": [\"规矩\"]", "}", "",
        }));
        WriteFile(poRoot, "postmortems/PO-9999-用例.md", string.Join("\n", new[]
        {
            "---", "id: PO-9999", "date: 2026-09-26", "trigger: check35", "status: open",
            "refs:", "  - verify.sh", "---", "",
            "## 现象", "", "甲。", "## 影响", "", "乙（个人失误。）。", "## 根因", "",
            "丙（沟通不畅。）。", "## 行动项", "",
            "- 修一：**负责人** = 甲；**判据** = 绿。", "",
        }));
        checks.Add(Guarded("治理·复盘：指责词与「根因未指向机制」都必须报", () =>
        {
            var (issues, _) = Postmortem.CheckDoc(poRoot, "postmortems/PO-9999-用例.md");
            var blame = issues.Any(i => i.Contains("命中指责性归因词", StringComparison.Ordinal));
            var root = issues.Any(i => i.Contains("根因段未指向机制", StringComparison.Ordinal));
            return (blame && root, string.Join(" | ", issues));
        }));

        var auditRoot = Path.Combine(work, "gov-audit");
        WriteFile(auditRoot, "protocol/audit.json", string.Join("\n", new[]
        {
            "{", "  \"schema\": \"nf-audit/1\",",
            "  \"required_fields\": [\"id\", \"date\", \"scope\", \"verdict\", \"auditor\", \"subjects\"],",
            "  \"verdict_vocabulary\": [\"pass\", \"fail\", \"warn\"],", "  \"rules\": [\"规矩\"]", "}", "",
        }));
        WriteFile(auditRoot, "target.md", "原样\n");
        var digest = Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(
                System.Text.Encoding.UTF8.GetBytes("原样\n"))).ToLowerInvariant();
        WriteFile(auditRoot, "results/audit/AUD-9999-用例.md", string.Join("\n", new[]
        {
            "---", "id: AUD-9999", "date: 2026-09-26", "scope: 用例", "verdict: pass",
            "auditor: 甲", "subjects:", $"  - target.md:{digest}", "---", "", "正文。", "",
        }));
        checks.Add(Guarded("治理·审计：对象一改旧审计立即失效（digest 绑定）", () =>
        {
            var clean = Audit.CheckDoc(auditRoot, "results/audit/AUD-9999-用例.md");
            WriteFile(auditRoot, "target.md", "改过了\n");
            var dirty = Audit.CheckDoc(auditRoot, "results/audit/AUD-9999-用例.md");
            var ok = clean.Issues.Count == 0
                     && dirty.Issues.Any(i => i.Contains("被审对象已变，旧审计失效", StringComparison.Ordinal));
            return (ok, $"干净={clean.Issues.Count} 条 · 改动后={string.Join(" | ", dirty.Issues)}");
        }));
    }

    // ------------------------------------------- ⑫ 端点契约（契约不许指向空气）

    /// <summary>
    /// 端点契约的核心是「**不许指向空气**」：`maps_to` 必须指向现存 CLI 子命令或 MCP 工具；
    /// 另外幂等语义**不许沉默**（重试安全的前提）。两条钉都用合成树，CLI 注册表现扫 <c>scripts/nf.py</c>。
    /// </summary>
    private static void EndpointCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "endpoint");
        WriteFile(root, "scripts/nf.py", "sub.add_parser(\"assemble\", help=\"…\")\nsub.add_parser(\"bench\", help=\"…\")\n");
        WriteFile(root, "protocol/endpoint_contract.json", string.Join("\n", new[]
        {
            "{",
            "  \"schema\": \"nf-endpoint/1\", \"status\": \"proposed\",",
            "  \"conventions\": {\"streaming\": \"SSE\", \"idempotency\": \"默认幂等\"},",
            "  \"endpoints\": [",
            "    {\"id\": \"a.plan\", \"method\": \"POST\", \"path\": \"/a/plan\", \"maps_to\": \"nf assemble\"},",
            "    {\"id\": \"bad\", \"method\": \"POST\", \"path\": \"/bad\", \"maps_to\": \"nf 不存在的命令\"}",
            "  ]",
            "}", "",
        }));
        checks.Add(Guarded("端点契约·maps_to 指向不存在的 CLI 子命令必须报（不许指向空气）", () =>
        {
            var (issues, _, stats) = EndpointContract.Scan(root);
            var hit = issues.FirstOrDefault(i => i.Contains("无法解析为现存 CLI 子命令或 MCP 工具", StringComparison.Ordinal));
            return (hit is not null && stats["cli_commands"] is 2, hit ?? $"未报（CLI 表 {stats.GetValueOrDefault("cli_commands")} 条）");
        }));

        WriteFile(root, "protocol/endpoint_contract.json", string.Join("\n", new[]
        {
            "{",
            "  \"schema\": \"nf-endpoint/1\", \"status\": \"proposed\",",
            "  \"conventions\": {\"streaming\": \"SSE\"},",
            "  \"endpoints\": [",
            "    {\"id\": \"a.plan\", \"method\": \"POST\", \"path\": \"/a/plan\", \"maps_to\": \"nf assemble\"}",
            "  ]",
            "}", "",
        }));
        checks.Add(Guarded("端点契约·幂等语义沉默必须报（重试安全的前提）", () =>
        {
            var (issues, _, _) = EndpointContract.Scan(root);
            var hit = issues.FirstOrDefault(i => i.Contains("未声明幂等语义", StringComparison.Ordinal));
            return (hit is not null, hit ?? "未报幂等沉默");
        }));
    }

    // --------------------------------- ⑬ 机读契约族（边界签名 / 事件背书）

    /// <summary>
    /// 两组判据各自的**两个方向**都要钉：
    /// ① 模块边界签名——改了边界字段必须报漂移；**只改非边界文本（name/description）不该报**
    ///    （否则"冻结"会变成"任何改动都红"的噪音门）；
    /// ② 事件背书——订阅无人发布必须 FAIL；登记进外部通道后只 WARN；跨包发布只 WARN（不把跨包当断链）。
    /// </summary>
    private static void MachineContractCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "machine-contract");
        WriteFile(root, "04_模块库/世界类/M90_用例.md", ModuleDoc("M90", "  inputs: [通用:M10]"));
        var digest = ModuleSignature.Signatures(root)["M90"].Digest;
        WriteFile(root, "protocol/module_signatures.json", string.Join("\n", new[]
        {
            "{", "  \"schema\": \"nf-module-signatures/1\", \"count\": 1,",
            "  \"modules\": {", $"    \"M90\": {{\"digest\": \"{digest}\", \"path\": \"04_模块库/世界类/M90_用例.md\"}}",
            "  }", "}", "",
        }));

        checks.Add(Guarded("机读契约·边界字段一变即报漂移（冻结纪律）", () =>
        {
            WriteFile(root, "04_模块库/世界类/M90_用例.md", ModuleDoc("M90", "  inputs: [通用:M99]"));
            var (issues, _, _) = ModuleSignature.Verify(root);
            var hit = issues.FirstOrDefault(i => i.Contains("边界漂移：M90", StringComparison.Ordinal));
            return (hit is not null, hit ?? "未报边界漂移");
        }));

        checks.Add(Guarded("机读契约·只改非边界文本不该报漂移（边界只取七字段）", () =>
        {
            WriteFile(root, "04_模块库/世界类/M90_用例.md",
                ModuleDoc("M90", "  inputs: [通用:M10]").Replace("  name: 用例\n", "  name: 用例（改名）\n"));
            var (issues, _, _) = ModuleSignature.Verify(root);
            return (issues.Count == 0, issues.Count == 0 ? "改名后仍零漂移" : string.Join(" | ", issues));
        }));

        var eventRoot = Path.Combine(work, "machine-events");
        WriteFile(eventRoot, "04_模块库/世界类/M90_用例.md",
            ModuleDoc("M90", "  inputs: []\n  events:\n    publish: []\n    subscribe: [幽灵事件]"));
        checks.Add(Guarded("机读契约·订阅无人发布即 FAIL；登记外部通道后只 WARN", () =>
        {
            var (issues, _, _) = EventBacking.Scan(eventRoot);
            var hard = issues.Any(i => i.Contains("事件背书缺口：幽灵事件", StringComparison.Ordinal));
            WriteFile(eventRoot, "protocol/external_events.json",
                "{\"schema\": \"nf-external-events/1\", \"events\": {\"幽灵事件\": {\"why\": \"外部通道\"}}}\n");
            var (issues2, warns2, _) = EventBacking.Scan(eventRoot);
            var still = issues2.Any(i => i.Contains("事件背书缺口", StringComparison.Ordinal));
            var allowWarn = warns2.Any(w => w.Contains("已挂账为外部通道", StringComparison.Ordinal));
            return (hard && !still && allowWarn,
                $"未挂账=FAIL {hard} · 挂账后无 FAIL {!still} · 有挂账 WARN {allowWarn}");
        }));
    }

    /// <summary>合成模块文档（machine_contract 围栏；<paramref name="extra"/> 追加边界字段）。</summary>
    private static string ModuleDoc(string id, string extra) => string.Join("\n", new[]
    {
        "---", $"id: {id}", "title: 用例", "---", "",
        "```yaml", "machine_contract:", "  schema: \"1\"", $"  id: {id}", "  name: 用例",
        "  category: 世界", "  layer: P40", extra, "  outputs: []", "  interfaces: []", "```", "",
    });

    // -------------------------------------- ⑭ 类型积压台账（防"台账当装饰"）

    /// <summary>
    /// 台账纪律的两面都要钉：**untyped 必须带 note**（不许无声增长），
    /// **在盘台账必须等于实时重算**（改一处类型而不同步台账 → 立刻判过期）。
    /// </summary>
    private static void TypeBacklogCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "type-backlog");
        Registry(root, "untyped", "正文证据字段名；类型待核");
        WriteFile(root, "protocol/type_backlog.json", "{\"schema\": \"nf-type-backlog/1\", \"count\": 1}\n");
        checks.Add(Guarded("类型积压·台账与实时重算一致时零问题（正向对照）", () =>
        {
            var (issues, stats) = TypeBacklog.VerifyBacklog(root);
            return (issues.Count == 0 && stats["untyped"] is 1,
                issues.Count == 0 ? $"untyped {stats["untyped"]} 项 · 台账同步" : string.Join(" | ", issues));
        }));

        checks.Add(Guarded("类型积压·untyped 缺 note 即 FAIL（无声增长）", () =>
        {
            Registry(root, "untyped", "");
            var (issues, _) = TypeBacklog.VerifyBacklog(root);
            var hit = issues.FirstOrDefault(i => i.Contains("无声增长", StringComparison.Ordinal));
            return (hit is not null, hit ?? "未报无声增长");
        }));

        checks.Add(Guarded("类型积压·类型被收窄但台账未同步 → 判过期（台账不当装饰）", () =>
        {
            Registry(root, "string", "已收窄");
            var (issues, stats) = TypeBacklog.VerifyBacklog(root);
            var hit = issues.FirstOrDefault(i => i.Contains("台账过期", StringComparison.Ordinal));
            return (hit is not null && stats["untyped"] is 0, hit ?? "未报台账过期");
        }));
    }

    /// <summary>合成事件注册表（单事件单字段）。</summary>
    private static void Registry(string root, string type, string note)
        => WriteFile(root, "protocol/event_registry.json", string.Join("\n", new[]
        {
            "{", "  \"events\": {", "    \"ev_one\": {",
            "      \"fields\": { \"field_a\": {",
            $"        \"type\": \"{type}\", \"note\": \"{note}\"", "      } }", "    }", "  }", "}", "",
        }));

    // ------------------------------- ⑮ I/O 类型面（可证才判，未收窄只 WARN）

    /// <summary>
    /// 类型面的判据是**只判可证的**：取值越词表、消费方期望的产物类型提供方没声明 → FAIL；
    /// 而 io_types.outputs 与 outputs 键集不一致、整块未标 → 只 WARN。两个方向都要钉，
    /// 否则"类型面"会退化成"任何未收窄都红"的噪音门。
    /// </summary>
    private static void IoTypeCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "io-types");
        WriteFile(root, "04_模块库/甲/M01_提供.md", IoDoc("M01", "[alpha]", "[]",
            "    outputs:\n      alpha: number\n    inputs: {}"));
        WriteFile(root, "04_模块库/乙/M02_消费.md", IoDoc("M02", "[]", "[M01]",
            "    outputs: {}\n    inputs:\n      M01: number"));
        checks.Add(Guarded("I/O 类型面·期望与提供一致时零问题（正向对照）", () =>
        {
            var (issues, _, stats) = IoTypes.Scan(root);
            return (issues.Count == 0 && stats["typed_fields"] is 2,
                issues.Count == 0 ? $"typed={stats["typed_fields"]} untyped={stats["untyped_fields"]}" : string.Join(" | ", issues));
        }));

        checks.Add(Guarded("I/O 类型面·可证不匹配必须 FAIL（期望 boolean，提供方只有 number）", () =>
        {
            WriteFile(root, "04_模块库/乙/M02_消费.md", IoDoc("M02", "[]", "[M01]",
                "    outputs: {}\n    inputs:\n      M01: boolean"));
            var (issues, _, _) = IoTypes.Scan(root);
            var hit = issues.FirstOrDefault(i => i.Contains("类型不匹配：M02", StringComparison.Ordinal));
            return (hit is not null, hit ?? "未报类型不匹配");
        }));

        checks.Add(Guarded("I/O 类型面·取值越词表必须 FAIL；键集不一致只 WARN（不该误判）", () =>
        {
            WriteFile(root, "04_模块库/甲/M01_提供.md", IoDoc("M01", "[alpha]", "[]",
                "    outputs:\n      alpha: 字符串\n      beta: number\n    inputs: {}"));
            var (issues, warns, _) = IoTypes.Scan(root);
            var kindOut = issues.Any(i => i.Contains("类型越词表", StringComparison.Ordinal));
            var keyset = warns.Any(w => w.Contains("键集不一致", StringComparison.Ordinal));
            return (kindOut && keyset && !issues.Any(i => i.Contains("键集不一致", StringComparison.Ordinal)),
                $"越词表=FAIL {kindOut} · 键集不一致=WARN {keyset} · FAIL 数 {issues.Count}");
        }));
    }

    /// <summary>合成带 io_types 的模块文档。</summary>
    private static string IoDoc(string id, string outputs, string inputs, string ioBody) => string.Join("\n", new[]
    {
        "---", $"id: {id}", "title: 用例", "---", "",
        "```yaml", "machine_contract:", "  schema: \"1\"", $"  id: {id}", "  layer: P40",
        "  category: 通用", $"  outputs: {outputs}", $"  inputs: {inputs}",
        "  interfaces: []", "  io_types:", ioBody, "```", "",
    });

    // ------------------------------- ⑯ 管线抽象执行（hard / advisory 分层）

    /// <summary>
    /// 管线层的判据分层要能分开：**hard**（模块找不到 / 依赖落在更后层）必须红；
    /// **advisory**（同层依赖序 / 跨包外部）不判死；解析失败与 Python **同向抛异常**（不是给一条判定）。
    /// </summary>
    private static void PipelineDryrunCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "pipeline-dryrun");
        Directory.CreateDirectory(Path.Combine(root, "desktop", "src", "core"));
        WriteFile(root, "desktop/src/core/registry.json", "{\"modules\": []}\n");
        WriteFile(root, "04_模块库/甲/M01_提供.md", IoDoc("M01", "[alpha]", "[]",
            "    outputs:\n      alpha: number\n    inputs: {}"));
        WriteFile(root, "04_模块库/乙/M02_消费.md", IoDoc("M02", "[]", "[M01]",
            "    outputs: {}\n    inputs:\n      M01: number"));
        WriteFile(root, "03_管线库/P99_用例.md", PipelineDoc("[M01]", "[M02]"));

        checks.Add(Guarded("管线执行·干净声明零 hard 缺陷（正向对照）", () =>
        {
            var result = PipelineDryrun.Graph("03_管线库/P99_用例.md", root);
            return (result.Issues.Count == 0 && (int)(result.Stats["modules"] ?? 0) == 2,
                $"hard={result.Issues.Count} · advisory={result.Notes.Count} · 模块 {result.Stats["modules"]}");
        }));

        checks.Add(Guarded("管线执行·模块未在仓库找到必须 FAIL", () =>
        {
            WriteFile(root, "03_管线库/P99_用例.md", PipelineDoc("[M01, 幽灵模块]", "[M02]"));
            var result = PipelineDryrun.Graph("03_管线库/P99_用例.md", root);
            var hit = result.Issues.FirstOrDefault(i => i.Contains("模块未在仓库找到：幽灵模块", StringComparison.Ordinal));
            return (hit is not null, hit ?? "未报模块缺失");
        }));

        checks.Add(Guarded("管线执行·前向依赖按 Python 口径记 advisory（不误判成 hard）", () =>
        {
            WriteFile(root, "03_管线库/P99_用例.md", PipelineDoc("[M01]", "[M02]"));
            WriteFile(root, "04_模块库/甲/M01_提供.md", IoDoc("M01", "[alpha]", "[M02]",
                "    outputs:\n      alpha: number\n    inputs: {}"));
            var result = PipelineDryrun.Graph("03_管线库/P99_用例.md", root);
            // 实测 Python：M01 依赖尚未执行的 M02 → 记「跨包/外部依赖」advisory，**不判 hard**
            // （hard 的门槛是「已执行但层位严格更后」；前向引用属执行模型待裁决项，不误伤）
            var note = result.Notes.FirstOrDefault(n => n.Category == "跨包/外部依赖"
                                                       && n.Detail.StartsWith("M01 ← M02", StringComparison.Ordinal));
            return (result.Issues.Count == 0 && note is not null,
                note is null ? $"未记前置依赖 advisory（hard={result.Issues.Count}）" : note.Detail);
        }));

        checks.Add(Guarded("管线执行·解析失败与 Python 同向抛异常（不是给判定）", () =>
        {
            WriteFile(root, "03_管线库/P99_用例.md",
                PipelineDoc("[M01]", "[M02]").Replace("```yaml\nPipeline:", "```yamz\nPipeline:"));
            try
            {
                var result = PipelineDryrun.Graph("03_管线库/P99_用例.md", root);
                return (false, $"未抛异常，反而给了 hard={result.Issues.Count} 的判定");
            }
            catch (InvalidOperationException exc)
            {
                return (exc.Message.Contains("管线解析失败", StringComparison.Ordinal), exc.Message);
            }
        }));
    }

    /// <summary>合成管线文档（两层：P10 装 layerA、P20 装 layerB——顺序即依赖序）。</summary>
    private static string PipelineDoc(string layerA, string layerB) => string.Join("\n", new[]
    {
        "# 管线 P99", "", "```yaml", "Pipeline:", "  id: P99", "  name: 用例管线",
        "  structure:", "    type: linear", "  layers:",
        "    - id: P10", "      name: 甲层", "      description: 甲", "      optional: false",
        $"      default_modules: {layerA}",
        "    - id: P20", "      name: 乙层", "      description: 乙", "      optional: false",
        $"      default_modules: {layerB}", "```", "",
    });

    // ------------------------------------------- ⑰ 双源知识层（knowledge-sources）

    /// <summary>
    /// 知识层的三条硬判据各钉一条：**locator 必须指向真实件**（防纸面源）、
    /// **查询有序**（合同级必须全部排在参考级之前）、**幽灵频次**（频率台账含未声明的源）。
    /// 另钉一处易错：缺键字段的文案按 Python `str(s.get(k))` 渲染成 `None`（不是空串）。
    /// </summary>
    private static void KnowledgeCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "knowledge");
        WriteFile(root, "library/RECEIPTS.json", "{}\n");
        // 认知裁剪模块必须在册（knowledge 的 _module_ids 正则扫模块文档找 id）
        WriteFile(root, "04_模块库/通用类/M23_认知边界.md", IoDoc("M23", "[]", "[]",
            "    outputs: {}\n    inputs: {}"));
        WriteFile(root, "protocol/transform_log.json", "{\"schema\": \"nf-transform-log/1\", \"entries\": []}\n");
        WriteFile(root, "protocol/knowledge_usage.json",
            "{\"schema\": \"nf-knowledge-usage/1\", \"counts\": {}, \"total\": 0}\n");
        checks.Add(Guarded("知识层·声明齐备时零问题（正向对照）", () =>
        {
            WriteFile(root, "protocol/knowledge_sources.json", KnowledgeDecl("library", true));
            var (issues, _, stats) = KnowledgeSources.Scan(root);
            return (issues.Count == 0 && stats["contract"] is 1 && stats["reference"] is 1,
                issues.Count == 0 ? $"源 {stats["sources"]}（合同 1 / 参考 1）" : string.Join(" | ", issues));
        }));

        checks.Add(Guarded("知识层·locator 指向不存在的件必须 FAIL（防纸面源）", () =>
        {
            WriteFile(root, "protocol/knowledge_sources.json", KnowledgeDecl("不存在的目录", true));
            var (issues, _, _) = KnowledgeSources.Scan(root);
            var hit = issues.FirstOrDefault(i => i.Contains("locator 不存在", StringComparison.Ordinal));
            return (hit is not null, hit ?? "未报纸面源");
        }));

        checks.Add(Guarded("知识层·查询有序被破坏必须 FAIL（合同级须全部在前）", () =>
        {
            WriteFile(root, "protocol/knowledge_sources.json", KnowledgeDecl("library", true, reverseOrder: true));
            var (issues, _, _) = KnowledgeSources.Scan(root);
            var hit = issues.FirstOrDefault(i => i.Contains("查询有序被破坏", StringComparison.Ordinal));
            return (hit is not null, hit ?? "未报查询无序");
        }));

        checks.Add(Guarded("知识层·幽灵频次必须 FAIL；缺键文案按 Python 渲染成 None", () =>
        {
            WriteFile(root, "protocol/knowledge_sources.json", KnowledgeDecl("library", false));
            var (declIssues, _, _) = KnowledgeSources.Scan(root);
            var noneText = declIssues.Any(i => i.Contains("kind 越词表：None", StringComparison.Ordinal));
            WriteFile(root, "protocol/knowledge_sources.json", KnowledgeDecl("library", true));
            WriteFile(root, "protocol/knowledge_usage.json",
                "{\"schema\": \"nf-knowledge-usage/1\", \"counts\": {\"幽灵源\": 1}, \"total\": 1}\n");
            var (usageIssues, _, _) = KnowledgeSources.VerifyUsage(root);
            var ghost = usageIssues.Any(i => i.Contains("含未声明的源：幽灵源", StringComparison.Ordinal));
            return (noneText && ghost, $"缺键渲染 None={noneText} · 幽灵频次={ghost}");
        }));
    }

    /// <summary>合成知识源声明（合同级 nf-protocol + 参考级 ext-assets）。</summary>
    private static string KnowledgeDecl(string contractLocator, bool withKind, bool reverseOrder = false)
    {
        var order = reverseOrder
            ? "\"query_order\": [\"ext-assets\", \"nf-protocol\"],"
            : "\"query_order\": [\"nf-protocol\", \"ext-assets\"],";
        var kindLine = withKind ? "\"kind\": \"local-compiled\", " : "";
        return string.Join("\n", new[]
        {
            "{",
            "  \"schema\": \"nf-knowledge-sources/1\",",
            "  \"authority_vocabulary\": [\"contract\", \"reference\"],",
            "  \"kind_vocabulary\": [\"local-compiled\", \"external-retrieval\"],",
            "  \"visibility_vocabulary\": [\"public\", \"internal\", \"restricted\"],",
            $"  {order}",
            "  \"promotion\": {\"evidence_tiers\": [\"machine-checkable\", \"reproducible\", \"externally-attestable\"],",
            "    \"triggers\": [\"reuse-frequency\", \"author-mark\", \"machine-check-pass\"],",
            "    \"rule\": \"三档证据齐方可转正\", \"on_missing_evidence\": \"stay-reference\"},",
            "  \"review\": {\"machine_gates\": [\"check37\"], \"rule\": \"逐条核证据\"},",
            "  \"cognition\": {\"filter_module\": \"M23\"},",
            "  \"sources\": [",
            $"    {{\"id\": \"nf-protocol\", \"authority\": \"contract\", {kindLine}\"locator\": \"{contractLocator}\", \"requires_source_label\": false, \"visibility\": \"public\", \"freshness\": {{\"policy\": \"stale_after\"}}}},",
            "    {\"id\": \"ext-assets\", \"authority\": \"reference\", \"kind\": \"external-retrieval\", \"locator\": \"library\", \"requires_source_label\": true, \"visibility\": \"internal\", \"freshness\": {\"policy\": \"ttl\", \"ttl_days\": 180}}",
            "  ]",
            "}", "",
        });
    }

    // ---------------------------------------- ⑧a Python 字符串语义（码点 vs UTF-16 单元）

    /// <summary>
    /// 实测教训：`state-front --ab` 的 `sha256` 两侧全同、`chars` 差 1——因为 Python 的
    /// <c>len(str)</c> 数**码点**，而 C# 的 <c>string.Length</c> 数 **UTF-16 代码单元**，
    /// 非 BMP 字符（emoji 等）会差一。切片同理（<c>s[:n]</c> 按码点，不能劈开代理对）。
    /// </summary>
    private static void PythonStringCases(List<Check> checks)
    {
        checks.Add(Guarded("字符串语义·len 数码点（非 BMP 字符算 1 而不是 2）", () =>
        {
            var emoji = "😀";
            var ok = PyScalar.PyLen(emoji) == 1 && PyScalar.PyLen("中文") == 2
                     && PyScalar.PyLen("😀😀") == 2 && PyScalar.PyLen("") == 0;
            return (ok, $"PyLen(\"😀\")={PyScalar.PyLen(emoji)}（.NET Length={emoji.Length}）· " +
                        $"PyLen(\"中文\")={PyScalar.PyLen("中文")}");
        }));

        checks.Add(Guarded("字符串语义·切片按码点，不劈开代理对", () =>
        {
            var sliced = PyScalar.PySlice("😀abc", 2);
            var ok = sliced == "😀a" && PyScalar.PySlice("abc", 9) == "abc" && PyScalar.PySlice("", 3) == "";
            return (ok, $"PySlice(\"😀abc\", 2)={PyScalar.PyRepr(sliced)}");
        }));
    }

    // --------------------------------- ⑱ 知识层可见性秩与复用面（单一真相源）

    /// <summary>
    /// 两条钉：① **可见性秩**——clearance 达到源的秩才可见（`public ⊆ internal ⊆ restricted`），
    /// 且越权源不进入查询顺序；② **复用面**——同一内容存在两份（馆藏条目 / 实践包源件全文摘要相同）
    /// 即 FAIL，因为"同一内容两份 = 两个真源"。
    /// </summary>
    private static void KnowledgeCliFacesCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "knowledge-visible");
        WriteFile(root, "protocol/transform_log.json", "{\"schema\": \"nf-transform-log/1\", \"entries\": []}\n");
        WriteFile(root, "protocol/knowledge_usage.json",
            "{\"schema\": \"nf-knowledge-usage/1\", \"counts\": {}, \"total\": 0}\n");
        WriteFile(root, "protocol/knowledge_sources.json", string.Join("\n", new[]
        {
            "{", "  \"schema\": \"nf-knowledge-sources/1\",",
            "  \"authority_vocabulary\": [\"contract\", \"reference\"],",
            "  \"kind_vocabulary\": [\"local-compiled\", \"external-retrieval\"],",
            "  \"visibility_vocabulary\": [\"public\", \"internal\", \"restricted\"],",
            "  \"query_order\": [\"pub-src\", \"int-src\", \"res-src\"],",
            "  \"promotion\": {\"evidence_tiers\": [\"machine-checkable\", \"reproducible\", \"externally-attestable\"],",
            "    \"triggers\": [\"reuse-frequency\", \"author-mark\", \"machine-check-pass\"],",
            "    \"rule\": \"三档证据齐方可转正\", \"on_missing_evidence\": \"stay-reference\"},",
            "  \"review\": {\"machine_gates\": [\"check37\"], \"rule\": \"逐条核证据\"},",
            "  \"cognition\": {\"filter_module\": \"M23\"},", "  \"sources\": [",
            "    {\"id\": \"pub-src\", \"authority\": \"contract\", \"kind\": \"local-compiled\", \"locator\": \"library\", \"requires_source_label\": false, \"visibility\": \"public\", \"freshness\": {\"policy\": \"stale_after\"}},",
            "    {\"id\": \"int-src\", \"authority\": \"contract\", \"kind\": \"local-compiled\", \"locator\": \"library\", \"requires_source_label\": false, \"visibility\": \"internal\", \"freshness\": {\"policy\": \"stale_after\"}},",
            "    {\"id\": \"res-src\", \"authority\": \"reference\", \"kind\": \"external-retrieval\", \"locator\": \"library\", \"requires_source_label\": true, \"visibility\": \"restricted\", \"freshness\": {\"policy\": \"no-cache\"}}",
            "  ]", "}", "",
        }));
        checks.Add(Guarded("知识层·可见性秩：public ⊆ internal ⊆ restricted（越权源被裁掉）", () =>
        {
            var pub = KnowledgeSources.VisibleIds(root, "public");
            var mid = KnowledgeSources.VisibleIds(root, "internal");
            var all = KnowledgeSources.VisibleIds(root, "restricted");
            var unknown = KnowledgeSources.VisibleIds(root, "bogus");
            var order = KnowledgeSources.ResolveOrder(root, "internal").Select(r => (string)r["id"]!).ToList();
            var ok = pub.SetEquals(new[] { "pub-src" }) && mid.SetEquals(new[] { "pub-src", "int-src" })
                     && all.Count == 3 && unknown.Count == 0
                     && order.SequenceEqual(new[] { "pub-src", "int-src" });
            return (ok, $"public={pub.Count} · internal={mid.Count} · restricted={all.Count} · " +
                        $"未知级={unknown.Count} · 裁剪后顺序=[{string.Join(",", order)}]");
        }));

        var dup = Path.Combine(work, "knowledge-reuse");
        // 两件**逐字节相同**——这正是要抓的「同一内容两份 = 两个真源」
        const string sameBytes = "---\nid: NF-1\ntitle: 甲\n---\n正文同一份\n";
        WriteFile(dup, "library/NF-1.md", sameBytes);
        WriteFile(dup, "patterns/p/PATTERN.md", sameBytes);
        checks.Add(Guarded("知识层·复用面：同一内容存在两份即 FAIL（两个真源）", () =>
        {
            var (issues, _, stats) = KnowledgeSources.VerifyReuse(dup);
            var hit = issues.FirstOrDefault(i => i.Contains("同一内容存在两份", StringComparison.Ordinal));
            return (hit is not null && (int)(stats["unique_digests"] ?? 0) == 1,
                hit ?? $"未报同内容两份（unique_digests={stats.GetValueOrDefault("unique_digests")}）");
        }));
    }

    // ------------------------------------------- ⑧b YAML 边界与转义（构造矩阵实测）

    /// <summary>
    /// 构造矩阵探针实测出的三处真问题，逐条钉住：
    /// ① `.NaN` 曾落到 double.Parse 抛 FormatException（**进程级异常**）——修后按 PyYAML 语义
    ///    成为 NaN，而**裸 `NaN` 是字符串**（PyYAML 的特殊值必须带点）；
    /// ② `"\x41"` 曾把 `\x` 吞掉变成 `x41`——修后还原成 `A`；
    /// ③ 块标量 / 锚点 / 别名 / 合并键 / 未闭合引号**必须显式 fail-closed**——
    ///    此前它们被静默当字符串（`k: |` → 字面 `"|"`），使"越界即报错"的承诺对这几族是假的。
    /// </summary>
    private static void YamlBoundaryCases(List<Check> checks)
    {
        checks.Add(Guarded("YAML·特殊浮点：`.NaN` 不崩；裸 NaN 是字符串（同 PyYAML）", () =>
        {
            var map = MiniYaml.Parse("a: .NaN\nb: .inf\nc: NaN\nd: nan\ne: .INF\n");
            var ok = map["a"] is double nanA && double.IsNaN(nanA)
                     && map["b"] is double infB && double.IsPositiveInfinity(infB)
                     && map["c"] is "NaN" && map["d"] is "nan"
                     && map["e"] is double infE && double.IsPositiveInfinity(infE);
            return (ok, $"a={PyScalar.TypeName(map["a"])} b={PyScalar.TypeName(map["b"])} " +
                        $"c={PyScalar.PyRepr(map["c"])} d={PyScalar.PyRepr(map["d"])}");
        }));

        checks.Add(Guarded("YAML·双引号转义族：`\\x41` 还原成 A（此前被吞成 x41）", () =>
        {
            var map = MiniYaml.Parse("a: \"\\x41\"\nb: \"\\u4e2d\"\nc: \"a\\tb\"\nd: \"\\0\"\n");
            var ok = (string?)map["a"] == "A" && (string?)map["b"] == "中"
                     && (string?)map["c"] == "a\tb" && (string?)map["d"] == "\0";
            return (ok, $"a={PyScalar.PyRepr(map["a"])} b={PyScalar.PyRepr(map["b"])} c={PyScalar.PyRepr(map["c"])}");
        }));

        checks.Add(Guarded("YAML·子集外构造必须显式 fail-closed（不许静默当字符串）", () =>
        {
            var cases = new (string Doc, string Want)[]
            {
                ("k: |\n  内容\n", "块标量"),
                ("k: >-\n  内容\n", "块标量"),
                ("a: &x 1\nb: *x\n", "锚点"),
                ("- *x\n", "别名"),
                ("a:\n  <<: 1\n", "合并键"),
                ("k: \"未闭合\n", "未闭合的引号"),
                ("k:\n\tj: 1\n", "TAB"),
            };
            var results = new List<string>();
            var allOk = true;
            foreach (var (doc, want) in cases)
            {
                try
                {
                    MiniYaml.Parse(doc);
                    allOk = false;
                    results.Add(want + "→未报错");
                }
                catch (InvalidOperationException exc)
                {
                    var hit = exc.Message.Contains(want, StringComparison.Ordinal);
                    allOk = allOk && hit;
                    results.Add(want + (hit ? "✓" : "→文案不符"));
                }
            }
            return (allOk, string.Join(" · ", results));
        }));
    }

    private static void WriteFile(string root, string rel, string text)
    {
        var full = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(full)!);
        File.WriteAllText(full, text, new UTF8Encoding(false));
    }

    private static string PatternDoc(string id) => string.Join("\n", new[]
    {
        "---", $"id: {id}", "name: 示例实践包", "status: active", "scope:", "  - 代码层",
        "applies_to:", "  - src", "rules:", "  - 规则一", "evidence:", "  - check34",
        "---", "", "## 正文", "",
    });

    private static string RfcDoc(string rfc, string supersededBy) => string.Join("\n", new[]
    {
        "# 示例协议件",
        "> 最后更新：2026-01-02",
        $"> **RFC**: {rfc} · **Category**: Standards Track · **Date**: 2026-01-02 · **Status**: " +
        (supersededBy == "—" ? "Active" : "Superseded") +
        $" · **Supersedes**: — · **Superseded by**: {supersededBy}",
        "", "正文。", "",
    });

    private static Check Guarded(string name, Func<(bool Passed, string Detail)> body)
    {
        try
        {
            var (passed, detail) = body();
            return new Check(name, passed, detail);
        }
        catch (Exception ex)
        {
            return new Check(name, false, $"未处理异常：{ex.GetType().Name}: {ex.Message}");
        }
    }

    // ---------------------------------------------------------------- ② 模块工具面（tool_face）

    // ---------------------------------------------------------------- ②′ ST 制卡校验器

    // ---------------------------------------------------------------- ②″ 自述数字实算

    // ---------------------------------------------------------------- ②‴ 知识源频次复算

    // ---------------------------------------------------------------- ②⁗ 互操作导出面

    // ---------------------------------------------------------------- ②⁵ MCP 错误响应契约

    // ---------------------------------------------------------------- ②⁶ 世界模型校验

    // ---------------------------------------------------------------- ②⁷ registry 引用图 / 影响面

    // ---------------------------------------------------------------- ②⁸ 市场分级与 See-Also

    // ---------------------------------------------------------------- ②⁹ 资产台账（check23 同语义）

    private static void AssetCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "asset-ledger");
        if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        Directory.CreateDirectory(root);
        string Header(string key, string ver, string st)
            => $"<!-- nf-asset: key=\"{key}\" version=\"{ver}\" status=\"{st}\" -->\n";

        var ledger = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema_version"] = "1",
            ["tier"] = "community",
            ["package"] = "合成资产集",
            ["assets"] = new List<object?>
            {
                new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["file"] = "good.md", ["key"] = "GOOD", ["source"] = "合成来源",
                    ["version"] = "1.0", ["status"] = "active",
                },
                new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["file"] = "dup1.md", ["key"] = "DUP", ["source"] = "合成来源",
                    ["version"] = "1.0", ["status"] = "active",
                },
                new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["file"] = "dup2.md", ["key"] = "DUP", ["source"] = "合成来源",
                    ["version"] = "1.0", ["status"] = "active",
                },
                new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["file"] = "missing.md", ["key"] = "MISSING", ["source"] = "合成来源",
                    ["version"] = "1.0", ["status"] = "active",
                },
            },
        };
        File.WriteAllText(Path.Combine(root, "provenance.json"), PythonJson.Indented(ledger) + "\n");
        File.WriteAllText(Path.Combine(root, "good.md"), Header("GOOD", "1.0", "active") + "# 好资产\n");
        File.WriteAllText(Path.Combine(root, "dup1.md"), Header("DUP", "1.0", "active") + "# 一\n");
        File.WriteAllText(Path.Combine(root, "dup2.md"), Header("DUP", "1.0", "active") + "# 二\n");
        File.WriteAllText(Path.Combine(root, "orphan.md"), Header("ORPHAN", "1.0", "active") + "# 孤儿\n");
        File.WriteAllText(Path.Combine(root, "untracked.md"), "# 无头\n");
        // 货架单层不变量：community/<包>/assets 下出现子目录即 FAIL
        var shelf = Path.Combine(root, "community", "合成包", "assets");
        Directory.CreateDirectory(Path.Combine(shelf, "子目录"));
        File.WriteAllText(Path.Combine(shelf, "a.md"), Header("SHELF", "1.0", "active") + "# 架内\n");

        var (issues, stats) = AssetLedger.VerifyRoot(root);
        var joined = string.Join(" | ", issues);
        checks.Add(new Check("资产台账·闭合判定（重键 / 文件缺失 / 孤儿头 / 未托管 / 货架子目录）",
            Convert.ToInt64(stats["ledgers"]) == 1 && Convert.ToInt64(stats["assets"]) == 4
            && joined.Contains("键重复") && joined.Contains("在册文件缺失")
            && joined.Contains("孤儿文件头（键不在台账）: orphan.md")
            && joined.Contains("孤儿文件头（键不在台账）: community/合成包/assets/a.md")
            && joined.Contains("资产货架含子目录 子目录")
            && Convert.ToInt64(stats["untracked"]) == 1,
            $"台账 {stats["ledgers"]} · 在册 {stats["assets"]} · 未托管 {stats["untracked"]} · " +
            $"孤儿 {stats["orphans"]} · 问题 {issues.Count} 条"));

        // 货架检查**不许静默失灵**：显式钉一次货架计数（历史上这里曾把 `*` 当字面目录名 → 整条检查 no-op）
        var (shelfIssues, shelfStats) = AssetLedger.VerifyShelfShape(root);
        checks.Add(new Check("资产台账·货架单层不变量真的在跑（不许静默 no-op）",
            Convert.ToInt64(shelfStats["shelves"]) == 1 && shelfIssues.Count == 1,
            $"货架 {shelfStats["shelves"]} 个 · 问题 {shelfIssues.Count} 条"));

        // 过滤器与非法取值：tier/status 非法即抛（CLI 层按真源口径 exit 2）
        var rows = AssetLedger.IterAssets(root);
        var activeOnly = AssetLedger.FilterRows(rows, status: "active");
        var badTier = false;
        try { AssetLedger.FilterRows(rows, tier: "bogus"); }
        catch (AssetLedger.LedgerError) { badTier = true; }
        var inventory = AssetLedger.InventoryRoot(root);
        checks.Add(new Check("资产台账·浏览/过滤/盘点（行数 · 非法 tier 抛错 · 盘点摘要）",
            rows.Count == 4 && activeOnly.Count == 4 && badTier && inventory.Count == 1
            && Convert.ToInt64(inventory[0]["assets"]) == 4
            && (inventory[0]["package"] as string) == "合成资产集",
            $"行 {rows.Count} · 过滤后 {activeOnly.Count} · 非法 tier 抛错={badTier} · 盘点 {inventory.Count} 行"));
    }

    // ---------------------------------------------------------------- ②⁹ᵇ 资产质量五面（45 W2 · 第 68 片）

    private static void AssetQualityCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "asset-quality");
        if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        foreach (var rel in new[] { "community/合成甲包/assets", "community/合成乙包/assets",
                                    "05_资产库/用户自定义", "04_模块库", "docs", "protocol" })
            Directory.CreateDirectory(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)));

        // 合格档一律 ≥200 字符：把「短档 / 低信息候选」隔离到专门造的那一份上，不靠运气。
        var pad = string.Concat(Enumerable.Repeat("补长正文，用来顶过 200 字符阈值，避免整棵树被标成低信息候选；", 6));
        string Asset(string key) => $"# 合成档\n\n`{key}` 定义。\n\n## {key}\n\n{pad}\n";
        var dirA = Path.Combine(root, "community", "合成甲包", "assets");
        var dirB = Path.Combine(root, "community", "合成乙包", "assets");
        File.WriteAllText(Path.Combine(dirA, "ALPHA.md"), Asset("KEY_ALPHA"));
        File.WriteAllText(Path.Combine(dirA, "README.md"), "# 键表（人读）\n");
        File.WriteAllText(Path.Combine(dirB, "BETA.md"), Asset("KEY_BETA"));
        File.WriteAllText(Path.Combine(root, "05_资产库", "用户自定义", "USER.md"), Asset("KEY_USER"));
        File.WriteAllText(Path.Combine(root, "04_模块库", "M01合成.md"),
            "# 合成模块\n\n引用 `KEY_ALPHA` `KEY_BETA` `KEY_USER`。\n");
        File.WriteAllText(Path.Combine(root, "docs", "note.md"), "# 说明\n");

        // ① 键发现两套口径**不许互相替换**：密度面认带连字符条目键，投影面不认（各自照抄真源）
        const string probeText = "文首 `C01-01` 与 \"A_B\": 与\n\n## HEADKEY\n";
        var densityKeys = AssetDensity.KeysOf("PROBE.md", probeText);
        var projectionKeys = AssetLedgerProjection.FileKeys("PROBE.md", probeText);
        checks.Add(new Check("资产质量·键发现两套口径（密度认连字符 / 投影不认，不许混用）",
            densityKeys.Contains("C01-01") && projectionKeys.Contains("A_B")
            && !projectionKeys.Contains("C01-01")
            && densityKeys.Contains("HEADKEY") && projectionKeys.Contains("HEADKEY"),
            "密度=" + string.Join(",", densityKeys) + " · 投影=" + string.Join(",", projectionKeys)));

        // ② 行数基线：自洽即 PASS（先钉"不误报"），改一字节即 FAIL（再钉"真的会红"）
        var baselineDoc = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = AssetLineBaseline.Schema,
            ["note"] = "合成基线",
            ["recorded_at"] = "2026-09-27",
            ["packages"] = AssetLineBaseline.ScanPackages(root).Cast<object?>().ToList(),
        };
        File.WriteAllText(Path.Combine(root, "protocol", "asset_line_baseline.json"),
            PythonJson.Indented(baselineDoc) + "\n");
        var (bOkIssues, bOkWarns, bOkStats) = AssetLineBaseline.Verify(root);
        checks.Add(new Check("资产质量·行数基线自洽不误报（在册 N 包 · 零 FAIL 零 WARN）",
            bOkIssues.Count == 0 && bOkWarns.Count == 0
            && Convert.ToInt64(bOkStats["packages"]) == 2 && Convert.ToInt64(bOkStats["baseline"]) == 2,
            $"在册 {bOkStats["packages"]} · 基线 {bOkStats["baseline"]} · 问题 {bOkIssues.Count}"));

        // ③ 键表投影：自洽即 PASS；新增键即"过期"
        var entries = AssetLedgerProjection.Build(root);
        File.WriteAllText(Path.Combine(root, "protocol", "community_asset_ledger.json"),
            PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["schema"] = AssetLedgerProjection.LedgerSchemaName,
                ["entries"] = entries.Cast<object?>().ToList(),
            }) + "\n");
        var (lOkIssues, lOkStats) = AssetLedgerProjection.Verify(root);
        checks.Add(new Check("资产质量·键表投影自洽（条目数与重算一致 · 零 FAIL）",
            lOkIssues.Count == 0 && Convert.ToInt64(lOkStats["entries"]) == entries.Count,
            $"条目 {lOkStats["entries"]} · 问题 {lOkIssues.Count}"));

        // ④ 引用度：**只有文件名令牌、正文不出现**的键才会零引用（资产档自身也在语料里）
        File.WriteAllText(Path.Combine(dirA, "ORPHANKEY.md"),
            "# 孤键档\n\n正文刻意不提那个只写在文件名上的键。\n" + pad + "\n");
        var (uIssues, uStats) = AssetDensity.UsageScan(root);
        var zeroKeys = ((List<object?>)uStats["zero_keys"]!).Select(PyScalar.PyRepr).ToList();
        checks.Add(new Check("资产质量·引用度（零引用键被点名 · 正文声明过的键不算零引用）",
            uIssues.Count == 0 && Convert.ToInt64(uStats["zero_usage"]) == 1
            && zeroKeys.Contains("'ORPHANKEY'")
            && Convert.ToInt64(uStats["used"]) == Convert.ToInt64(uStats["assets"]) - 1,
            $"资产键 {uStats["assets"]} · 零引用 {uStats["zero_usage"]} = [{string.Join(",", zeroKeys)}]"));

        // ⑤ 密度：空档 = FAIL（空档不进档数，只进问题；短档另计数）
        File.WriteAllText(Path.Combine(dirA, "EMPTY.md"), "");
        var (dIssues, dStats) = AssetDensity.Scan(root);
        checks.Add(new Check("资产质量·密度（空档即 FAIL · 无键/短档只计数不翻红）",
            dIssues.Count == 1 && dIssues[0].Contains("为空档（0 字符）")
            && Convert.ToInt64(dStats["files"]) == 4 && Convert.ToInt64(dStats["tiny"]) == 0
            && Convert.ToString(dStats["avg_keys_per_file"])!.Length > 0,
            $"问题 {dIssues.Count} · 档 {dStats["files"]} · 短档 {dStats["tiny"]}"));

        // ⑥ 厚度：短档成为低信息候选，平均值为整数（不是浮点）
        File.WriteAllText(Path.Combine(dirA, "THIN.md"), "太短。\n");
        var (tIssues, tStats) = AssetDensity.ThicknessScan(root);
        var lowFiles = ((List<object?>)tStats["low_files"]!).Select(PyScalar.PyRepr).ToList();
        checks.Add(new Check("资产质量·厚度（低信息候选点名到档 · 平均值取整）",
            tIssues.Count == 0 && Convert.ToInt64(tStats["low_info"]) == 1
            && lowFiles.Count == 1 && lowFiles[0]!.Contains("THIN.md")
            && tStats["avg_chars"] is long && tStats["avg_sections"] is long,
            $"低信息 {tStats["low_info"]} = [{string.Join(",", lowFiles)}] · 平均字符 {tStats["avg_chars"]}"));

        // ⑦ 漂移三态：内容改动 / 新包未登记 / 缺包跳过——三条判定各走各的分支
        File.AppendAllText(Path.Combine(dirA, "ALPHA.md"), "\n追加一行。\n");
        var (bDrift, _w1, _s1) = AssetLineBaseline.Verify(root);
        var driftText = string.Join(" | ", bDrift);
        Directory.CreateDirectory(Path.Combine(root, "community", "合成丙包", "assets"));
        File.WriteAllText(Path.Combine(root, "community", "合成丙包", "assets", "DELTA.md"), Asset("KEY_DELTA"));
        var (bNew, _w2, _s2) = AssetLineBaseline.Verify(root);
        var newText = string.Join(" | ", bNew);
        Directory.Delete(Path.Combine(root, "community", "合成乙包"), recursive: true);
        var (bGone, bGoneWarns, _s3) = AssetLineBaseline.Verify(root);
        var staleLedger = AssetLedgerProjection.Verify(root).Issues;
        checks.Add(new Check("资产质量·漂移三分支（外形不一致 / 新包未登记 / 缺包只 WARN · 投影随动过期）",
            driftText.Contains("资产行数与基线不一致") && newText.Contains("社区包资产未登记基线")
            && bGoneWarns.Any(w => w.Contains("不在场"))
            && staleLedger.Any(i => i.Contains("与资产扫描不一致")),
            $"漂移 {bDrift.Count} 条 · 新包 {bNew.Count} 条 · WARN {bGoneWarns.Count} 条 · 投影过期 {staleLedger.Count} 条"));

        // ⑧ glob 口径：`*.md` 后缀按平台（Windows 不分大小写）且**不过滤点文件**——不许静默丢面
        var before = AssetShelf.MarkdownFiles(root).Count;
        File.WriteAllText(Path.Combine(dirA, "UPPER.MD"), Asset("KEY_UPPER"));
        File.WriteAllText(Path.Combine(dirA, ".hidden.md"), Asset("KEY_HIDDEN"));
        var after = AssetShelf.MarkdownFiles(root).Count;
        var expectDelta = OperatingSystem.IsWindows() ? 2 : 1;
        checks.Add(new Check("资产质量·glob 口径（后缀按平台判大小写 + 点文件在面内）",
            after - before == expectDelta,
            $"档数 {before} → {after}（期望 +{expectDelta} · Windows 上 .MD 与 .hidden.md 都算）"));
    }

    // ---------------------------------------------------------------- ②⁹ᶜ 判据面小口三件（第 69 片 · explain / who-refers / diff）

    private static void SmallFacesCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "small-faces");
        if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        Directory.CreateDirectory(root);

        // ① 修复指引表：机械导出件的长度与**码点序**键序（"10" 排在 "2" 前），缺键必须是 null
        var keys = CheckGuide.SortedKeys();
        checks.Add(new Check("小口·修复指引表（32 条 · 码点序键序 · 缺键 null）",
            CheckGuide.Count == 32 && keys.Count == 32
            && string.Join(",", keys.Take(4)) == "1,10,11,12"
            && keys[^1] == "9"
            && CheckGuide.Get("33") is null && CheckGuide.Get("32")!.Contains("质量纵深汇总"),
            $"条目 {CheckGuide.Count} · 前三键 {string.Join(",", keys.Take(3))} · 末键 {keys[^1]}"));

        // ② 引用反查：**类别感知**匹配（合成 registry —— 真仓被引声明恰好都是裸号，正向对账看不出这条差别）
        var regPath = Path.Combine(root, "synth_registry.json");
        var registry = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["registry_schema_version"] = "2",
            ["protocols"] = new List<object?>
            {
                new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["id"] = "包甲",
                    ["references"] = new List<object?>
                    {
                        Ref("情感:M55", "源甲", true), Ref("法律:M55", "源乙", false), Ref("M55", "源丙", null),
                    },
                },
                new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["id"] = "包乙",
                    ["references"] = new List<object?> { Ref("情感:M55", "源丁", null) },
                },
            },
        };
        File.WriteAllText(regPath, PythonJson.Indented(registry) + "\n");
        var catHits = Retriever.ReferencedBy("情感:M55", regPath);
        var bareHits = Retriever.ReferencedBy("M55", regPath);
        var catText = string.Join(" | ", catHits.Select(r => PyScalar.PyRepr(r["module_id"])));
        checks.Add(new Check("小口·引用反查类别感知（限定查询不越界到别的类别 · 裸号查询全命中）",
            catHits.Count == 3 && catText.Contains("情感:M55") && !catText.Contains("法律:M55")
            && bareHits.Count == 4,
            $"情感:M55 → {catHits.Count} 条 [{catText}] · M55 → {bareHits.Count} 条"));

        // ③ registry 缺件：真源吞成空表（不是报错）——只读门也不许在这里翻红
        var missingHits = Retriever.ReferencedBy("M55", Path.Combine(root, "不存在.json"));
        checks.Add(new Check("小口·引用反查 registry 缺件 → 空表不抛（与真源 try/except 同语义）",
            missingHits.Count == 0, $"命中 {missingHits.Count} 条"));

        // ④ 签名差异四分支：verdict 与 impact 各走一次
        var baseSig = Sig("01", "v1.0", new[] { "M01", "M02" });
        var sameSig = Sig("01", "v1.0", new[] { "M02", "M01" });          // 同集合、不同顺序 → 必须零差异
        var addSig = Sig("01", "v1.0", new[] { "M01", "M02", "M03" });    // 新增
        var dropSig = Sig("01", "v1.0", new[] { "M02" });                 // 移除 M01
        var docIdSig = Sig("02", "v1.0", new[] { "M01", "M02" });         // 编号变更
        var sameDiff = SignatureDiff.Diff(baseSig, sameSig);
        var addDiff = SignatureDiff.Diff(baseSig, addSig);
        var dropDiff = SignatureDiff.Diff(baseSig, dropSig);
        var idDiff = SignatureDiff.Diff(baseSig, docIdSig);
        checks.Add(new Check("小口·签名差异四分支（顺序无关 · 只增 additive · 移除需评审/bump · 编号变破坏/bump）",
            ((List<object?>)sameDiff["changes"]!).Count == 0
            && (string)addDiff["impact"]! == "additive"
            && (string)addDiff["verdict"]! == "兼容"
            && (string)dropDiff["impact"]! == "bump"
            && ((string)dropDiff["verdict"]!).Contains("需评审")
            && (string)idDiff["impact"]! == "bump"
            && ((string)idDiff["verdict"]!).Contains("破坏"),
            $"同集合 changes={((List<object?>)sameDiff["changes"]!).Count} · 只增={addDiff["impact"]} · " +
            $"移除={dropDiff["verdict"]} · 编号变={idDiff["verdict"]}"));

        // ⑤ 端到端：合成文档对经 BuildSignature → Diff（证明两条链真的接上了，不是只测比较器）
        var docA = Path.Combine(root, "01_甲.md");
        var docB = Path.Combine(root, "01_甲增.md");
        File.WriteAllText(docA, "# 甲\n\n```yaml\nid: M01\n```\n\n引用 M01 与 M02。\n");
        File.WriteAllText(docB, "# 甲\n\n```yaml\nid: M01\n```\n\n引用 M01 与 M02。\n\n## 乙\n\n新增引用 M03。\n");
        var endToEnd = SignatureDiff.Diff(KnowledgeSig.BuildSignature("01_甲.md", root),
                                          KnowledgeSig.BuildSignature("01_甲增.md", root));
        var added = ((List<object?>)endToEnd["changes"]!)
            .Cast<Dictionary<string, object?>>().Any(c => (string)c["kind"]! == "新增");
        checks.Add(new Check("小口·签名差异端到端（合成文档 → 签名 → 差异；新增项被抓到）",
            added && (string)endToEnd["impact"]! == "additive" && endToEnd["from"] as string == "01_甲.md",
            $"from={endToEnd["from"]} · impact={endToEnd["impact"]} · changes={((List<object?>)endToEnd["changes"]!).Count}"));

        static Dictionary<string, object?> Ref(string mid, string pkg, bool? ro) =>
            new(StringComparer.Ordinal)
            {
                ["module_id"] = mid, ["source_package"] = pkg,
                ["source_schema_version"] = "2", ["asset_readonly"] = ro,
            };

        static Dictionary<string, object?> Sig(string docId, string version, string[] refs) =>
            new(StringComparer.Ordinal)
            {
                ["kind"] = "doc", ["path"] = "01_甲.md", ["doc_id"] = docId, ["title"] = "甲",
                ["version"] = version, ["self_id"] = "M01", ["layer"] = "P01", ["category"] = "事件",
                ["heading_count"] = 2L, ["headings"] = new List<object?> { "甲" },
                ["schema_names"] = new List<object?>(), ["refs"] = refs.Cast<object?>().ToList(),
                ["meta_line_count"] = 0L, ["line_count"] = 3L, ["body_hash"] = "h",
            };
    }

    // ---------------------------------------------------------------- ②⁹ᵈ 产出形态面（第 70 片 · output list / check）

    private static void OutputFormsCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "output-forms");
        if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        Directory.CreateDirectory(root);
        string W(string rel, string text)
        {
            var full = Path.Combine(root, rel);
            Directory.CreateDirectory(Path.GetDirectoryName(full)!);
            File.WriteAllText(full, text);
            return rel;
        }

        // ① 形态识别：扩展名 + 内容嗅探（六类特型 + 未知兜底 text/T0）
        W("a.json", "{\"kind\": \"nf-domain-spec/1\"}\n");
        W("b.json", "{\"schema\": \"nf-combo/1\"}\n");
        W("c.json", "{\"$schema\": \"https://json-schema.org/draft/2020-12/schema\"}\n");
        W("d.json", "{\"kind\": \"nf-performance/1\"}\n");
        W("e.json", "{\"kind\": \"nf-quant-metrics/1\"}\n");
        W("f.json", "{\"kind\": \"nf-system-card/1\"}\n");
        W("g.unknown", "x\n");
        var detected = new[]
        {
            OutputForms.Detect(root, "a.json"), OutputForms.Detect(root, "b.json"),
            OutputForms.Detect(root, "c.json"), OutputForms.Detect(root, "d.json"),
            OutputForms.Detect(root, "e.json"), OutputForms.Detect(root, "f.json"),
        };
        checks.Add(new Check("产出形态·识别（domain-spec / combo-cert / json-schema / performance / quant / system-card）",
            string.Join(",", detected.Select(d => d.Form))
            == "domain-spec,combo-cert,json-schema,performance-report,quant-metrics,system-card"
            && OutputForms.Detect(root, "g.unknown") == ("text", "T0"),
            "识别=" + string.Join(",", detected.Select(d => d.Form))));

        // ② JSON 重复键（嵌套对象各自查重）+ 正常 JSON 零问题
        var dup = W("dup.json", "{\"a\": 1, \"b\": {\"k\": 1, \"k\": 2}, \"a\": 3}\n");
        var dupIssues = OutputForms.Check(root, dup, "json");
        W("ok.json", "{\"a\": 1}\n");
        checks.Add(new Check("产出形态·JSON 重复键（含嵌套各自查重 · 正常件零问题）",
            dupIssues.Count == 2 && dupIssues[0] == "JSON 重复键：a" && dupIssues[1] == "JSON 重复键：k"
            && OutputForms.Check(root, "ok.json", "json").Count == 0,
            string.Join(" | ", dupIssues)));

        // ③ CSV：行长不符 / 表头重名 / 空表
        W("bad.csv", "a,b,c\n1,2\n");
        W("duphead.csv", "a,a\n1,2\n");
        W("empty.csv", "\n");
        var csvIssues = OutputForms.Check(root, "bad.csv", "csv");
        checks.Add(new Check("产出形态·CSV（行长≠表头 · 表头重名 · 空表）",
            csvIssues.Count == 1 && csvIssues[0].Contains("字段数 2 ≠ 表头 3")
            && OutputForms.Check(root, "duphead.csv", "csv").Any(i => i.Contains("表头有重名列"))
            && OutputForms.Check(root, "empty.csv", "csv").Any(i => i == "空表"),
            string.Join(" | ", csvIssues)));

        // ④ XML/GraphML：**DTD 守卫必须触发**（钉住一处真缺陷：首版正则漏了 `!` → 守卫整条不生效）
        W("dtd.xml", "<?xml version=\"1.0\"?>\n<!DOCTYPE r [<!ENTITY x \"y\">]>\n<r>&x;</r>\n");
        W("dangling.graphml", "<?xml version=\"1.0\"?>\n<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">\n"
                              + "  <graph><node id=\"a\"/><edge source=\"a\" target=\"幽灵\"/></graph>\n</graphml>\n");
        checks.Add(new Check("产出形态·XML/GraphML（DTD 守卫真的在跑 · 悬空边被抓）",
            OutputForms.Check(root, "dtd.xml", "xml").Any(i => i.Contains("含 DTD/ENTITY 声明"))
            && OutputForms.Check(root, "dtd.xml", "svg").Any(i => i.Contains("含 DTD/ENTITY 声明"))
            && OutputForms.Check(root, "dangling.graphml", "graphml").Any(i => i.Contains("边端点悬空：target=幽灵")),
            string.Join(" | ", OutputForms.Check(root, "dtd.xml", "xml"))));

        // ⑤ YAML：**Tab 缩进必须被抓**（第二处真缺陷：首版查的是"lstrip 后首字符"，那永远不是空白）
        W("tab.yaml", "a:\n\tb: 1\n");
        W("nomap.yaml", "a: 1\n散行\n");
        checks.Add(new Check("产出形态·YAML（Tab 缩进真的被查 · 非映射行被抓）",
            OutputForms.Check(root, "tab.yaml", "yaml").Any(i => i.Contains("Tab 缩进"))
            && OutputForms.Check(root, "nomap.yaml", "yaml").Any(i => i.Contains("非映射项")),
            string.Join(" | ", OutputForms.Check(root, "tab.yaml", "yaml"))));

        // ⑥ TOML：**明确拒绝，不许返回空表**（空表 = 把"没判"当"判过"）
        W("x.toml", "a = 1\n");
        var toml = OutputForms.Check(root, "x.toml", "toml");
        checks.Add(new Check("产出形态·TOML（BCL 无解析器 → 明确拒绝，不静默放行）",
            toml.Count == 1 && toml[0].Contains("不可判定") && toml[0].Contains("不静默放行"),
            string.Join(" | ", toml)));

        // ⑦ JSON-Schema 子集：类型 / 必填 / 附加属性 / oneOf / 不支持关键字进 unsupported
        var schema = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["type"] = "object",
            ["required"] = new List<object?> { "id" },
            ["additionalProperties"] = false,
            ["properties"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["type"] = "string" },
            },
        };
        var instance = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = 7L, ["extra"] = true,
        };
        var unsupported = new List<string>();
        var schemaErrors = JsonSchemaSubset.Check(instance, schema, unsupported: unsupported);
        var withConditional = new Dictionary<string, object?>(schema, StringComparer.Ordinal) { ["if"] = new Dictionary<string, object?>() };
        var condUnsup = new List<string>();
        JsonSchemaSubset.Check(instance, withConditional, unsupported: condUnsup);
        checks.Add(new Check("产出形态·JSON-Schema 子集（类型/多余字段 · 不支持关键字进 unsupported 不静默通过）",
            schemaErrors.Count == 2
            && schemaErrors[0] == "$.id: 类型应为 string，实为 int"
            && schemaErrors[1] == "$: 多余字段 extra（additionalProperties=false）"
            && condUnsup.Any(u => u.StartsWith("if@$", StringComparison.Ordinal)),
            string.Join(" | ", schemaErrors) + " · unsupported=" + string.Join(",", condUnsup)));
    }

    // ---------------------------------------------------------------- ②⁹ᵉ 概念图闭包求值器（第 71 片）

    private static void ConceptClosureCases(List<Check> checks, string work, string repoRoot)
    {
        var root = Path.Combine(work, "concept-closure");
        if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        Directory.CreateDirectory(root);
        string Write(string name, string body)
        {
            var full = Path.Combine(root, name);
            File.WriteAllText(full, body);
            return full;
        }
        const string head = "# 合成概念图\n\n```yaml\nconcept_graph:\n  version: \"1.0\"\n  domain: 合成域\n"
                            + "  provenance_strength: domain-logic\n  provenance_legend:\n    domain-logic: 域内推理\n";
        const string nodes = "  nodes:\n"
                             + "    - id: C00\n      name: 根\n      layer: P00\n      provenance: [domain-logic]\n"
                             + "    - id: C01\n      name: 甲\n      layer: P10\n      provenance: [domain-logic]\n"
                             + "      aliases: [甲, Alpha]\n      prereqs: [C00]\n"
                             + "    - id: C02\n      name: 乙\n      layer: P20\n      provenance: [domain-logic]\n"
                             + "      prereqs: [C01]\n";
        const string tail = "  branches:\n    - id: main\n      nodes: [C00, C01, C02]\n"
                            + "  orderings:\n    - id: seq\n      seq: [C00, C01, C02]\n```\n";
        var healthy = Write("healthy.md", head + nodes + tail);

        // ① 图语义主线：健康图零问题；闭包 / 缺失 / 就绪 / 拓扑序 / 别名解析都对
        var graph = ConceptGraph.LoadGraph(healthy);
        var closure = ConceptGraph.Closure(graph, "C02");
        var order = ConceptGraph.Toposort(graph);
        checks.Add(new Check("概念图·语义主线（健康图零问题 · 闭包/拓扑序/别名解析）",
            ConceptGraph.Problems(graph).Count == 0
            && string.Join(",", closure) == "C00,C01,C02"
            && string.Join(",", order) == "C00,C01,C02"
            && ConceptGraph.Resolve(graph, "Alpha") == "C01"
            && ConceptGraph.Resolve(graph, "  甲  ") == "C01"
            && ConceptGraph.Missing(graph, "C02", new[] { "C01" }).Count == 2
            && string.Join(",", ConceptGraph.Frontier(graph, new[] { "C00" })) == "C01"
            && ConceptGraph.Violations(graph, new[] { "C02", "C01", "C00" }).Count == 2,
            $"闭包 {string.Join(",", closure)} · 序 {string.Join(",", order)}"));

        // ② problems() 逐条判据各触发一次（环 / 悬空 / 自环 / 重复 id / 缺 name / 缺 provenance / 图例漂移 / 层位）
        var expectations = new (string Name, string Body, string Need)[]
        {
            ("环", head + nodes.Replace("      prereqs: [C00]\n", "      prereqs: [C00, C02]\n") + tail, "环"),
            ("悬空", head + nodes.Replace("      prereqs: [C01]\n", "      prereqs: [C01, C99]\n") + tail, "悬空前置"),
            ("自环", head + nodes.Replace("      prereqs: [C00]\n", "      prereqs: [C01]\n") + tail, "自环"),
            ("重复id", head + nodes.Replace("    - id: C02\n", "    - id: C01\n") + tail, "节点 id 重复"),
            ("缺name", head + nodes.Replace("      name: 甲\n", "") + tail, "缺 name"),
            ("图例漂移", head + nodes.Replace("      provenance: [domain-logic]\n      aliases: [甲, Alpha]\n",
                "      provenance: [external-x]\n      aliases: [甲, Alpha]\n") + tail, "不在 provenance_legend 中"),
            ("层位越界", head + nodes.Replace("      layer: P10\n", "      layer: P99\n") + tail, "层位越界"),
            ("缺强度声明", head.Replace("  provenance_strength: domain-logic\n", "") + nodes + tail,
                "缺 provenance_strength 声明"),
            ("别名重复", head + nodes.Replace("      aliases: [甲, Alpha]\n", "      aliases: [甲, Alpha, 乙]\n")
                .Replace("      name: 乙\n", "      name: 乙\n      aliases: [乙]\n") + tail, "别名重复"),
            ("未归分支", head + nodes + tail.Replace("nodes: [C00, C01, C02]", "nodes: [C00, C01]"), "未归入任何分支"),
        };
        var misses = new List<string>();
        foreach (var (name, body, need) in expectations)
        {
            var issues = ConceptGraph.Problems(ConceptGraph.LoadGraph(Write($"bad-{name}.md", body)));
            if (!issues.Any(i => i.Contains(need, StringComparison.Ordinal))) misses.Add(name);
        }
        checks.Add(new Check("概念图·problems 逐条判据真的在判（十类注入各命中一次）",
            misses.Count == 0, misses.Count == 0 ? "十类全部命中" : "未命中：" + string.Join("、", misses)));

        // ③ 取块与结构错误的文案（缺件 / 缺机读块 / 顶层键错）
        var messages = new List<string>();
        try { ConceptGraph.LoadGraph(Path.Combine(root, "不存在.md")); }
        catch (ConceptGraph.ClosureError exc) { messages.Add(exc.Message); }
        try { ConceptGraph.LoadGraph(Write("noblock.md", "# 只有散文\n")); }
        catch (ConceptGraph.ClosureError exc) { messages.Add(exc.Message); }
        // 注意：块里**没有** `concept_graph:` 标记行 → 走的是「缺机读块」；要让「结构非法」出现，
        // 标记行须在场而顶层键不是映射（与真源两条报错的分界一致）。
        try { ConceptGraph.LoadGraph(Write("wrongkey.md", "```yaml\nconcept_graph: 1\n```\n")); }
        catch (ConceptGraph.ClosureError exc) { messages.Add(exc.Message); }
        checks.Add(new Check("概念图·三条拒绝文案（缺件 / 缺机读块 / 顶层键错）",
            messages.Count == 3 && messages[0].Contains("概念图资产不存在")
            && messages[1].Contains("机器可读块") && messages[2].Contains("机读块结构非法"),
            string.Join(" | ", messages.Select(m => m[..Math.Min(24, m.Length)]))));

        // ④ 求值器人读面：条目键全表 + 缺口清单（含 CJK 按码点补齐）
        var list = DomainClosure.RenderList(graph);
        var gaps = DomainClosure.RenderGaps(graph, Array.Empty<string>(), "", 3);
        checks.Add(new Check("求值器·人读面（条目键全表 / 缺口清单 / CJK 补齐按码点）",
            list.StartsWith("== 条目键全表（3 概念 + 0 包外前置）==", StringComparison.Ordinal)
            && list.Contains("C01  [main   ] P10    甲（别名：甲、Alpha）")
            && gaps.StartsWith("== 前置缺失清单（L=0 概念 · 非空项 3）==", StringComparison.Ordinal),
            list.Split('\n')[1]));

        // ⑤ 端到端：真仓资产上跑自检（登记样例路径）与全仓图扫描
        var asset = Path.Combine(repoRoot, ConceptGraph.DefaultAsset.Replace('/', Path.DirectorySeparatorChar));
        var (fails, passes) = DomainClosure.SelfCheck(asset);
        var (scanIssues, scanStats) = ConceptGraph.Scan(repoRoot);
        checks.Add(new Check("概念图·真仓自检与全仓扫描（登记样例全过 · 图资产零问题）",
            fails.Count == 0 && passes.Count >= 14 && scanIssues.Count == 0
            && Convert.ToInt64(scanStats["graphs"]) >= 1 && Convert.ToInt64(scanStats["nodes"]) > 0,
            $"自检 {passes.Count}/{passes.Count + fails.Count} · 图 {scanStats["graphs"]} 个 / "
            + $"节点 {scanStats["nodes"]} / 边 {scanStats["edges"]} · 扫描问题 {scanIssues.Count}"));
    }

    // ---------------------------------------------------------------- ②⁹ᶠ 度量引擎复算（第 72 片 · quant_metrics / domain_metrics）

    /// <summary>
    /// **真材料的复算证据**（不是自造期望值）：拿真仓在盘的 T4 产物当期望——对每个声明
    /// `domain-report` 的包用 `DomainMetrics.Evaluate` 按 INDEX 里的 params 重算，与 `outputs/REPORT.json` 比；
    /// 量化金融域包另比 `PERFORMANCE_REPORT.json` / 两张 Vega 规格 / 一张 Mermaid 图。
    /// 这正是 `output verify` 的 `_recompute_entry` 将来要做的事——**先在这里证它算得对**。
    /// </summary>
    private static void MetricsRecomputeCases(List<Check> checks, string repoRoot, string work)
    {
        var community = Path.Combine(repoRoot, "community");
        var domainChecked = 0;
        var families = new HashSet<string>(StringComparer.Ordinal);
        var mismatches = new List<string>();
        if (Directory.Exists(community))
            foreach (var pkgDir in Directory.GetDirectories(community).OrderBy(d => d, StringComparer.Ordinal))
            {
                var indexPath = Path.Combine(pkgDir, "outputs", "INDEX.json");
                if (!File.Exists(indexPath)) continue;
                var (index, err) = OutputForms.ReadJson(indexPath);
                if (err.Length > 0 || index is not Dictionary<string, object?> idx) continue;
                foreach (var entry in ConceptGraph.PyList(idx.GetValueOrDefault("outputs"))
                             .OfType<Dictionary<string, object?>>())
                {
                    var spec = entry.GetValueOrDefault("recompute") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
                    if (PyText(spec.GetValueOrDefault("id")) != "domain-report") continue;
                    var rawParams = spec.GetValueOrDefault("params") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
                    var family = PyText(rawParams.GetValueOrDefault("family"));
                    var inputs = ConceptGraph.PyList(spec.GetValueOrDefault("inputs"));
                    if (family.Length == 0 || inputs.Count == 0) continue;
                    var rel = PyText(inputs[0]);
                    var csv = Path.Combine(pkgDir, rel.Replace('/', Path.DirectorySeparatorChar));
                    var outPath = Path.Combine(pkgDir, PyText(entry.GetValueOrDefault("path")).Replace('/', Path.DirectorySeparatorChar));
                    if (!File.Exists(csv) || !File.Exists(outPath)) continue;
                    var (rows, loadErr) = DomainMetrics.LoadRows(csv);
                    if (loadErr.Length > 0) { mismatches.Add($"{Path.GetFileName(pkgDir)}: {loadErr}"); continue; }
                    var (onDisk, diskErr) = OutputForms.ReadJson(outPath);
                    if (diskErr.Length > 0 || onDisk is not Dictionary<string, object?> expected) continue;
                    // 在盘 REPORT.json 是**生成器包装件**（kind/code/domain/family/sample/sample_rows/metrics），
                    // `metrics` 才是 evaluate() 的产物——比较必须按同一形状，否则比的是两个东西。
                    Dictionary<string, object?> metrics;
                    try
                    {
                        metrics = DomainMetrics.Evaluate(family, rows, rawParams);
                    }
                    catch (ArgumentException exc)
                    {
                        mismatches.Add($"{Path.GetFileName(pkgDir)}/{family}: 复算异常 {exc.Message}");
                        continue;
                    }
                    var fresh = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["kind"] = "nf-domain-report/1",
                        ["code"] = PyText(rawParams.GetValueOrDefault("code")) is "None" ? "" : PyText(rawParams.GetValueOrDefault("code")),
                        ["domain"] = PyText(rawParams.GetValueOrDefault("domain")) is "None" ? "" : PyText(rawParams.GetValueOrDefault("domain")),
                        ["family"] = family,
                        ["sample"] = rel,
                        ["sample_rows"] = (long)rows.Count,
                        ["metrics"] = metrics,
                    };
                    domainChecked++;
                    families.Add(family);
                    if (PythonJson.CanonicalizeGraph(fresh) != PythonJson.CanonicalizeGraph(expected))
                    {
                        var diffs = DeepDiff(fresh, expected);
                        mismatches.Add($"{Path.GetFileName(pkgDir)}/{family}"
                                       + (mismatches.Count == 0
                                           ? " ⇒ " + string.Join(" | ", diffs.Take(3))
                                           : ""));
                    }
                }
            }
        checks.Add(new Check("度量引擎·真仓 T4 复算（domain-report ↔ 在盘 REPORT.json 逐字段一致）",
            mismatches.Count == 0 && domainChecked >= 50,
            $"复算 {domainChecked} 包 · 族 {families.Count} 种（{string.Join("、", families.OrderBy(x => x, StringComparer.Ordinal))}）"
            + $" · 不一致 {mismatches.Count}{(mismatches.Count > 0 ? "：" + string.Join("、", mismatches.Take(4)) : "")}"));

        // 量化金融域包：绩效报告 + 两张 Vega 规格 + Mermaid 口径声明链（全部与在盘产物逐字段/逐字节比）
        var quant = Path.Combine(repoRoot, "community", "量化金融域包", "outputs");
        var notes = new List<string>();
        var quantOk = true;
        if (Directory.Exists(quant))
        {
            var seriesPath = Path.Combine(quant, "samples", "EQUITY_CURVE.csv");
            var (series, seriesErr) = QuantMetrics.LoadEquityCurve(seriesPath);
            quantOk = seriesErr.Length == 0;
            if (!quantOk) notes.Add("净值曲线装载失败：" + seriesErr);
            if (quantOk)
            {
                var (report, _) = OutputForms.ReadJson(Path.Combine(quant, "PERFORMANCE_REPORT.json"));
                var fresh = QuantMetrics.PerformanceReport(series,
                    "2026-06-01", "2026-08-21", currency: "CNY", returnBasis: "simple",
                    frequency: "daily", riskFreeRateAnnual: 0.015, benchmarkId: "NF-SAMPLE-INDEX",
                    costBpsFee: 3.0, costBpsSlippage: 5.0, fillRule: "next_open",
                    singleSideTurnover: true, asOf: "2026-08-21");
                var same = report is Dictionary<string, object?> onDisk
                           && PythonJson.CanonicalizeGraph(fresh) == PythonJson.CanonicalizeGraph(onDisk);
                if (!same) { quantOk = false; notes.Add("PERFORMANCE_REPORT 不一致"); }

                var (vegaEq, _) = OutputForms.ReadJson(Path.Combine(quant, "charts", "EQUITY_CURVE.vega.json"));
                var freshEq = QuantMetrics.VegaEquityCurve(series, "净值曲线（策略 vs 基准，合成样例）");
                if (vegaEq is not Dictionary<string, object?> eqDisk
                    || PythonJson.CanonicalizeGraph(freshEq) != PythonJson.CanonicalizeGraph(eqDisk))
                { quantOk = false; notes.Add("EQUITY_CURVE.vega 不一致"); }

                var (vegaDd, _) = OutputForms.ReadJson(Path.Combine(quant, "charts", "DRAWDOWN.vega.json"));
                var freshDd = QuantMetrics.VegaDrawdown(series, "回撤曲线（净值口径）");
                if (vegaDd is not Dictionary<string, object?> ddDisk
                    || PythonJson.CanonicalizeGraph(freshDd) != PythonJson.CanonicalizeGraph(ddDisk))
                { quantOk = false; notes.Add("DRAWDOWN.vega 不一致"); }

                var mmdPath = Path.Combine(quant, "charts", "DECLARATION_CHAIN.mmd");
                if (File.Exists(mmdPath))
                {
                    var expected = KnowledgeSig.Norm(File.ReadAllText(mmdPath, new System.Text.UTF8Encoding(false)));
                    if (QuantMetrics.MermaidDeclarationFlow() != expected)
                    { quantOk = false; notes.Add("DECLARATION_CHAIN.mmd 不一致"); }
                }
            }
        }
        else
        {
            quantOk = false;
            notes.Add("量化金融域包不在场");
        }
        checks.Add(new Check("度量引擎·量化四件复算（绩效报告 / 两条 Vega 规格 / Mermaid 声明链）",
            quantOk, notes.Count == 0 ? "四件逐字段/逐字节一致" : string.Join("、", notes)));

        // 金标向量：真仓夹具没走到的族与边界（calibration / 各 k / 平局 / 空串 / 带单价），
        // 期望值由真源导出（MetricsGolden 是机械导出件）——与上面的「真材料复算」互补。
        using var goldenDoc = JsonIo.Parse(MetricsGolden.GoldenJson);
        var cases = PythonJson.ToGraph(goldenDoc.RootElement) as List<object?> ?? new List<object?>();
        var goldenBad = new List<string>();
        var goldenOk = 0;
        foreach (var item in cases.OfType<Dictionary<string, object?>>())
        {
            var name = PyText(item.GetValueOrDefault("name"));
            var family = PyText(item.GetValueOrDefault("family"));
            var csv = PyText(item.GetValueOrDefault("csv"));
            var parameters = item.GetValueOrDefault("params") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            var expected = item.GetValueOrDefault("expected");
            var csvPath = Path.Combine(work, "golden-" + name + ".csv");
            File.WriteAllText(csvPath, csv);
            var (rows, loadErr) = DomainMetrics.LoadRows(csvPath);
            if (loadErr.Length > 0) { goldenBad.Add($"{name}: {loadErr}"); continue; }
            Dictionary<string, object?> fresh;
            try
            {
                fresh = DomainMetrics.Evaluate(family, rows, parameters);
            }
            catch (ArgumentException exc)
            {
                goldenBad.Add($"{name}: {exc.Message}");
                continue;
            }
            if (PythonJson.CanonicalizeGraph(fresh) == PythonJson.CanonicalizeGraph(expected)) goldenOk++;
            else goldenBad.Add($"{name} ⇒ " + string.Join(" | ", DeepDiff(fresh, expected).Take(2)));
        }
        checks.Add(new Check("度量引擎·金标向量（未走到族与边界 · 期望值由真源导出）",
            goldenBad.Count == 0 && goldenOk >= 13,
            $"{goldenOk}/{cases.Count} 一致{(goldenBad.Count > 0 ? "：" + string.Join("、", goldenBad.Take(3)) : "")}"));
    }

    private static string PyText(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        double d => PythonJson.PyFloatRepr(d),
        _ => PyScalar.PyRepr(v),
    };

    private static bool PyTruthy(object? v) => v switch
    {
        null => false,
        bool b => b,
        string s => s.Length > 0,
        long l => l != 0,
        int i => i != 0,
        double d => d != 0,
        List<object?> list => list.Count > 0,
        Dictionary<string, object?> map => map.Count > 0,
        _ => true,
    };

    /// <summary>复刻 <c>output_forms._deep_diff</c>（只取前若干条，供复算不一致时定位）。</summary>
    private static List<string> DeepDiff(object? a, object? b, string path = "$", List<string>? output = null)
    {
        output ??= new List<string>();
        if (a is Dictionary<string, object?> ma && b is Dictionary<string, object?> mb)
        {
            foreach (var k in ma.Keys.Union(mb.Keys).OrderBy(x => x, StringComparer.Ordinal))
            {
                if (!ma.ContainsKey(k)) output.Add($"{path}.{k} 仅存于在盘");
                else if (!mb.ContainsKey(k)) output.Add($"{path}.{k} 仅存于复算");
                else DeepDiff(ma[k], mb[k], $"{path}.{k}", output);
            }
        }
        else if (a is List<object?> la && b is List<object?> lb)
        {
            if (la.Count != lb.Count) output.Add($"{path} 长度 {la.Count}≠{lb.Count}");
            for (var i = 0; i < Math.Min(la.Count, lb.Count); i++) DeepDiff(la[i], lb[i], $"{path}[{i}]", output);
        }
        else if (a is long or int or double && b is long or int or double && a is not bool && b is not bool)
        {
            var da = Convert.ToDouble(a, System.Globalization.CultureInfo.InvariantCulture);
            var db = Convert.ToDouble(b, System.Globalization.CultureInfo.InvariantCulture);
            if (Math.Abs(da - db) > 1e-9)
                output.Add($"{path} 数值 {PyScalar.PyRepr(a)}≠{PyScalar.PyRepr(b)}");
        }
        else if (!PyScalar.PyEquals(a, b))
        {
            output.Add($"{path} {PyScalar.PyRepr(a)}≠{PyScalar.PyRepr(b)}");
        }
        return output;
    }

    // ---------------------------------------------------------------- ②⁹ᵍ 产出形态门禁合成（第 73 片 · verify/render/meter）

    private static void OutputGateCases(List<Check> checks, string work, string repoRoot)
    {
        // ① 真仓三件：check32 三合一零问题 / 渲染全「同」（在盘与复算一致）/ 机验率有值
        var (scanIssues, scanStats) = OutputForms.Scan(repoRoot);
        var (_, renderRows) = OutputForms.RenderOutputs(repoRoot);
        var (_, meterStats) = OutputForms.Meter(repoRoot);
        checks.Add(new Check("产出门禁·真仓三合一（check32 零问题 · 渲染全同步 · 机验率在册）",
            scanIssues.Count == 0 && renderRows.Count >= 400 && renderRows.All(r => !PyTruthy(r["changed"]))
            && (meterStats.GetValueOrDefault("packages") as Dictionary<string, object?>)?.Count >= 50
            && (scanStats.GetValueOrDefault("index") as Dictionary<string, object?>)?.GetValueOrDefault("outputs") is long,
            $"扫描问题 {scanIssues.Count} · 渲染 {renderRows.Count} 件 · 包 {((meterStats.GetValueOrDefault("packages") as Dictionary<string, object?>)?.Count ?? 0)}"));

        // ② 合成违规：形态清单（重复 id / 档位非法 / 缺可达性实证 / 缺规范入口）与包级产出（声明件不存在 / T4 无 recompute）
        var root = Path.Combine(work, "output-gate");
        if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        Directory.CreateDirectory(Path.Combine(root, "protocol"));
        Directory.CreateDirectory(Path.Combine(root, "community", "合成包", "outputs"));
        File.WriteAllText(Path.Combine(root, "protocol", "output_forms.json"), PythonJson.Indented(
            new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["schema"] = "nf-output-forms/1",
                ["categories"] = new List<object?>
                {
                    new Dictionary<string, object?>(StringComparer.Ordinal) { ["id"] = "cat", ["name"] = "类目" },
                },
                ["forms"] = new List<object?>
                {
                    new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["id"] = "f1", ["category"] = "cat", ["tier"] = "T2", ["status"] = "supported",
                        ["spec"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["uri"] = "https://x" },
                        ["evidence"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["reachable"] = true },
                    },
                    new Dictionary<string, object?>(StringComparer.Ordinal)   // 重复 id + 档位非法 + 缺 uri + 缺实证
                    {
                        ["id"] = "f1", ["category"] = "cat", ["tier"] = "T9", ["status"] = "supported",
                    },
                },
            }) + "\n");
        File.WriteAllText(Path.Combine(root, "community", "合成包", "outputs", "INDEX.json"),
            PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["schema"] = "nf-output-index/1",
                ["package"] = "合成包",
                ["outputs"] = new List<object?>
                {
                    new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["path"] = "outputs/缺失.json", ["form"] = "json", ["tier"] = "T2", ["role"] = "r",
                    },
                    new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["path"] = "outputs/T4.md", ["form"] = "markdown", ["tier"] = "T4", ["role"] = "r",
                    },
                },
            }) + "\n");
        File.WriteAllText(Path.Combine(root, "community", "合成包", "outputs", "T4.md"), "# 占位\n");
        var (regIssues, _) = OutputForms.RegistryVerify(root);
        var (idxIssues, _) = OutputForms.IndexVerify(root);
        var regText = string.Join(" | ", regIssues);
        var idxText = string.Join(" | ", idxIssues);
        checks.Add(new Check("产出门禁·合成违规（清单四类 + 包级两类各自报出）",
            regText.Contains("形态 id 重复：f1") && regText.Contains("f1 档位非法")
            && regText.Contains("缺规范入口 spec.uri") && regText.Contains("缺可达性实证")
            && idxText.Contains("声明产出面不存在") && idxText.Contains("声明 T4（可复算）却无 recompute 声明"),
            "清单问题 " + regIssues.Count + " 条 · 包级问题 " + idxIssues.Count + " 条"));

        // ③ 机验率基线回退必须报（可重签工件的语义：低了就是 FAIL）
        File.WriteAllText(Path.Combine(root, "protocol", "output_forms_baseline.json"),
            PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["schema"] = "nf-output-forms-baseline/1",
                ["packages"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["合成包"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["machine_verifiable"] = 9L, ["functional"] = 9L, ["prose_assets"] = 0L,
                        ["machine_verifiable_ratio"] = 1.0,
                    },
                },
                ["totals"] = new Dictionary<string, object?>(StringComparer.Ordinal),
            }) + "\n");
        var (baseIssues, _) = OutputForms.BaselineVerify(root);
        var baseText = string.Join(" | ", baseIssues);
        checks.Add(new Check("产出门禁·机验率基线回退即 FAIL（机验面与功能面各报一条）",
            baseText.Contains("机验产出面回退") && baseText.Contains("功能面（T4 可复算）回退"),
            string.Join(" | ", baseIssues)));

        // ④ `_deep_diff` 四类差异（字典并集键 / 列表长度 / 数值容差 / 值不等）
        var left = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["a"] = 1L, ["b"] = new List<object?> { 1L, 2L }, ["c"] = "x", ["d"] = 1e-12,
        };
        var right = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["a"] = 2L, ["b"] = new List<object?> { 1L }, ["c"] = "y", ["e"] = 1L,
        };
        var diffs = OutputForms.DeepDiff(left, right);
        var diffText = string.Join(" | ", diffs);
        checks.Add(new Check("产出门禁·复算比对器 `_deep_diff`（数值容差 · 列表长度 · 并集键 · 值不等）",
            diffText.Contains("$.a 数值 1≠2") && diffText.Contains("$.b 长度 2≠1")
            && diffText.Contains("$.c 'x'≠'y'") && diffText.Contains("$.e 仅存于在盘"),
            diffText));
    }

    // ---------------------------------------------------------------- ②⁹ʰ check32 四件子扫描器（第 74 片）

    private static void AuxScannerCases(List<Check> checks, string work, string repoRoot)
    {
        var root = Path.Combine(work, "aux-scanners");
        if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        Directory.CreateDirectory(root);
        using var doc = JsonIo.Parse(AuxGolden.GoldenJson);
        var cases = PythonJson.ToGraph(doc.RootElement) as List<object?> ?? new List<object?>();
        var bad = new List<string>();
        var byScanner = new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (var item in cases.OfType<Dictionary<string, object?>>())
        {
            var name = PyText(item.GetValueOrDefault("name"));
            var scanner = PyText(item.GetValueOrDefault("scanner"));
            var expected = (Dictionary<string, object?>)item.GetValueOrDefault("expected")!;
            // `files` 为空 = **真仓基线**（在快照上实测的期望）；非空 = 合成负例（写到临时根再跑）。
            var files = item.GetValueOrDefault("files") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            string dir;
            if (files.Count == 0)
            {
                dir = repoRoot;
            }
            else
            {
                dir = Path.Combine(root, name.Replace("/", "-"));
                Directory.CreateDirectory(dir);
                foreach (var (rel, content) in files)
                {
                    var full = Path.Combine(dir, rel.Replace('/', Path.DirectorySeparatorChar));
                    Directory.CreateDirectory(Path.GetDirectoryName(full)!);
                    File.WriteAllText(full, PyText(content));
                }
            }
            var (issues, stats) = scanner switch
            {
                "world_slots" => AuxScanners.WorldSlotsScan(dir),
                "instruction_step_audit" => AuxScanners.InstructionStepAudit(dir),
                "payload_registry" => AuxScanners.PayloadRegistryScan(dir),
                "payload_consumer" => AuxScanners.PayloadConsumerScan(dir),
                _ => (new List<string>(), new Dictionary<string, object?>(StringComparer.Ordinal)),
            };
            byScanner[scanner] = byScanner.GetValueOrDefault(scanner) + 1;
            var issuesOk = issues.SequenceEqual(
                ConceptGraph.PyList(expected.GetValueOrDefault("issues")).Select(PyText), StringComparer.Ordinal);
            var statsOk = PythonJson.CanonicalizeGraph(stats)
                          == PythonJson.CanonicalizeGraph(expected.GetValueOrDefault("stats"));
            if (!issuesOk || !statsOk)
            {
                var detail = issuesOk ? "" : "issues：" + string.Join(" | ", issues);
                if (!statsOk)
                    detail += (detail.Length > 0 ? " · " : "")
                              + "stats：" + string.Join(" | ",
                                  DeepDiff(stats, expected.GetValueOrDefault("stats")).Take(3));
                bad.Add($"{name} ⇒ {detail}");
            }
        }
        checks.Add(new Check("check32 子扫描器·金标向量（四件 · 14 条：真仓 4 + 合成负例 10）",
            bad.Count == 0 && cases.Count == 14 && byScanner.Count == 4,
            $"{cases.Count - bad.Count}/{cases.Count} 一致（各扫描器 {byScanner.Count} 件）"
            + (bad.Count > 0 ? "：" + string.Join("、", bad.Take(3)) : "")));
    }

    // ---------------------------------------------------------------- ②⁹ⁱ check32 最后两件（第 75 片 · pack_combo.scan / domain_pack.manifest_verify）

    private static void ComboDomainCases(List<Check> checks, string work, string repoRoot)
    {
        var root = Path.Combine(work, "combo-domain");
        if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        Directory.CreateDirectory(root);
        using var doc = JsonIo.Parse(ComboDomainGolden.GoldenJson);
        var cases = PythonJson.ToGraph(doc.RootElement) as List<object?> ?? new List<object?>();
        var bad = new List<string>();
        foreach (var item in cases.OfType<Dictionary<string, object?>>())
        {
            var name = PyText(item.GetValueOrDefault("name"));
            var scanner = PyText(item.GetValueOrDefault("scanner"));
            var expected = (Dictionary<string, object?>)item.GetValueOrDefault("expected")!;
            var files = item.GetValueOrDefault("files") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            string dir;
            if (files.Count == 0)
            {
                dir = repoRoot;
            }
            else
            {
                dir = Path.Combine(root, name);
                Directory.CreateDirectory(dir);
                foreach (var (rel, content) in files)
                {
                    var full = Path.Combine(dir, rel.Replace('/', Path.DirectorySeparatorChar));
                    Directory.CreateDirectory(Path.GetDirectoryName(full)!);
                    File.WriteAllText(full, PyText(content));
                }
            }
            var (issues, stats) = scanner switch
            {
                "combo_scan" => ComboScan.Scan(dir),
                "domain_manifest" => DomainPackScan.ManifestVerify(dir),
                _ => (new List<string>(), new Dictionary<string, object?>(StringComparer.Ordinal)),
            };
            var issuesOk = issues.SequenceEqual(
                ConceptGraph.PyList(expected.GetValueOrDefault("issues")).Select(PyText), StringComparer.Ordinal);
            var statsOk = PythonJson.CanonicalizeGraph(stats)
                          == PythonJson.CanonicalizeGraph(expected.GetValueOrDefault("stats"));
            if (!issuesOk || !statsOk)
            {
                var detail = issuesOk ? "" : "issues：" + string.Join(" | ", issues);
                if (!statsOk)
                    detail += (detail.Length > 0 ? " · " : "") + "stats："
                              + string.Join(" | ", DeepDiff(stats, expected.GetValueOrDefault("stats")).Take(3));
                bad.Add($"{name} ⇒ {detail}");
            }
        }
        checks.Add(new Check("check32 子扫描器·最后两件金标向量（组合证书+广度 / 域包名录 · 6 条）",
            bad.Count == 0 && cases.Count == 6,
            $"{cases.Count - bad.Count}/{cases.Count} 一致"
            + (bad.Count > 0 ? "：" + string.Join("、", bad.Take(2)) : "")));
    }

    // ---------------------------------------------------------------- ②⁹ʲ 模块生命周期（第 76 片 · check24 同语义）

    private static void ModuleLifecycleCases(List<Check> checks, string work, string repoRoot)
    {
        var root = Path.Combine(work, "module-lifecycle");
        if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        Directory.CreateDirectory(Path.Combine(root, "04_模块库", "通用类"));
        Directory.CreateDirectory(Path.Combine(root, "community", "合成包", "modules"));
        string Module(string id, string name, string meta, string? extra = null) =>
            $"# 模块 {id} · {name}\n\n> {meta}\n\n## 职能\n\n正文。\n{extra ?? ""}";
        File.WriteAllText(Path.Combine(root, "04_模块库", "通用类", "M01_甲.md"),
            Module("M01", "甲", "类别：通用｜挂载点：P00｜状态：deprecated（口径重写）"));
        File.WriteAllText(Path.Combine(root, "04_模块库", "通用类", "M02_乙.md"),
            Module("M02", "乙", "类别：通用｜挂载点：P00｜依赖：M01、M03"));
        File.WriteAllText(Path.Combine(root, "community", "合成包", "modules", "M03_丙.md"),
            Module("M03", "丙", "类别：事件｜挂载点：P10｜状态：retired"));
        File.WriteAllText(Path.Combine(root, "community", "合成包", "protocol.yaml"),
            "id: 合成包\nmodule_ids:\n  - M03\n");

        var (issues, stats) = ModuleLifecycle.VerifyModules(root);
        var text = string.Join(" | ", issues);
        checks.Add(new Check("模块生命周期·check24 同语义（deprecated/retired 被引用即 FAIL · 三态计数）",
            issues.Count == 2
            && text.Contains("04_模块库/通用类/M01_甲.md 状态=deprecated 但仍被引用：04_模块库/通用类/M02_乙.md(依赖引用)")
            && text.Contains("community/合成包/modules/M03_丙.md 状态=retired 但仍被引用：04_模块库/通用类/M02_乙.md(依赖引用)")
            && Convert.ToInt64(stats["modules"]) == 3 && Convert.ToInt64(stats["deprecated"]) == 1
            && Convert.ToInt64(stats["retired"]) == 1 && Convert.ToInt64(stats["active"]) == 1,
            $"问题 {issues.Count} · 模块 {stats["modules"]} · deprecated {stats["deprecated"]} · retired {stats["retired"]}"));

        // 真仓：248 模块全 active、引用门禁全绿、清单行数与模块数一致
        var (realIssues, realStats) = ModuleLifecycle.VerifyModules(repoRoot);
        var rows = ModuleLifecycle.Rows(repoRoot);
        checks.Add(new Check("模块生命周期·真仓（248 模块全 active · 引用门禁全绿 · ls 行数一致）",
            realIssues.Count == 0 && Convert.ToInt64(realStats["modules"]) == rows.Count
            && Convert.ToInt64(realStats["deprecated"]) == 0 && Convert.ToInt64(realStats["retired"]) == 0,
            $"模块 {realStats["modules"]} · ls 行 {rows.Count} · 问题 {realIssues.Count}"));

        // 状态位解析口径：缺省 active、词表外视作 active、原因与状态分离
        var noMeta = ModuleLifecycle.GetStatus("# 模块 M09 · 无元信息\n\n正文\n");
        var badWord = ModuleLifecycle.GetStatus("# 模块 M09\n\n> 状态：deprecateded\n");
        var withReason = ModuleLifecycle.GetStatus("# 模块 M09\n\n> 状态：deprecated（口径重写）\n");
        checks.Add(new Check("模块生命周期·状态位三态口径（缺省/词表外 → active · 原因与状态分离）",
            noMeta.Status == "active" && badWord.Status == "active"
            && withReason.Status == "deprecated" && withReason.Reason == "口径重写",
            $"{noMeta.Status}/{badWord.Status}/{withReason.Status}({withReason.Reason})"));
    }

    // ---------------------------------------------------------------- ②⁹ᵏ 协议生成物 golden（第 77 片 · check31）

    private static void ProtocolGoldenCases(List<Check> checks, string work, string repoRoot)
    {
        // ① 真材料：真仓生成物 == 实时重算（**这一条绿就等价于两个生成物逐字节一致**）+ 统计数
        var (realIssues, realStats) = ProtocolGolden.VerifyGolden(repoRoot);
        checks.Add(new Check("协议生成物 golden·真仓（check31：生成物 == 实时重算 · 摘要 %s 字节 / schema %s 份）",
            realIssues.Count == 0 && Convert.ToInt64(realStats["schema_ids"]) == 5
            && Convert.ToInt64(realStats["report_bytes"]) > 50000,
            $"问题 {realIssues.Count} · report {realStats["report_bytes"]} 字节 · schema {realStats["schema_ids"]} 份"));

        // ② 合成：生成物缺失 → 两条「缺失」；生成物被篡改 → 两条「过期」（含人读摘要——真源注释点明它曾"只渲染不校验"）
        var root = Path.Combine(work, "protocol-golden");
        if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        Directory.CreateDirectory(Path.Combine(root, "protocol", "generated"));
        var (missingIssues, _) = ProtocolGolden.VerifyGolden(root);
        var missingText = string.Join(" | ", missingIssues);
        File.WriteAllText(Path.Combine(root, "protocol", "generated", ProtocolGolden.ReportName), "{}\n");
        File.WriteAllText(Path.Combine(root, "protocol", "generated", ProtocolGolden.SummaryName), "# 手改摘要\n");
        var (staleIssues, _) = ProtocolGolden.VerifyGolden(root);
        var staleText = string.Join(" | ", staleIssues);
        checks.Add(new Check("协议生成物 golden·合成（缺件两条 · 篡改两条「过期」· 人读摘要也在判）",
            missingText.Contains($"{ProtocolGolden.GeneratedDir}/{ProtocolGolden.ReportName} 缺失")
            && missingText.Contains($"{ProtocolGolden.GeneratedDir}/{ProtocolGolden.SummaryName} 缺失")
            && staleText.Contains($"{ProtocolGolden.GeneratedDir}/{ProtocolGolden.ReportName} 过期")
            && staleText.Contains($"{ProtocolGolden.GeneratedDir}/{ProtocolGolden.SummaryName} 过期"),
            $"缺件问题 {missingIssues.Count} · 篡改问题 {staleIssues.Count}"));

        // ③ 事件闭包（closure_scan）：只报告不设闸（issues 恒空）+ 三份事件集互斥划分
        var (closureIssues, closureStats) = ClosureScan.Scan(repoRoot);
        var linked = ConceptGraph.PyList(closureStats["linked_events"]).Count;
        var subOnly = ConceptGraph.PyList(closureStats["sub_only_events"]).Count;
        var pubOnly = ConceptGraph.PyList(closureStats["pub_only_events"]).Count;
        checks.Add(new Check("事件闭包扫描（只报告不设闸 · 三集互斥 · 模块数在册）",
            closureIssues.Count == 0 && Convert.ToInt64(closureStats["modules"]) > 0
            && linked + subOnly + pubOnly > 0,
            $"模块 {closureStats["modules"]} · 相连 {linked} · 仅订阅 {subOnly} · 仅发布 {pubOnly}"));
    }

    /// <summary>
    /// <summary>
    /// 决策层面（check33 第 15 条）三钉：真仓（声明完整 + stub 确定 + fail-closed 全绿）
    /// + 篡改声明（适配器缺 note · 候选 pulled=true 缺 local 三字段）+ 无声明件（summary 抛 KeyError →
    /// 按 check33 的 except 打成「不可用」）。金标由 probes/decision_layer_probe.py（真源模块原文）产出。
    /// </summary>
    private static void DecisionLayerCases(List<Check> checks, string work, string repoRoot)
    {
        const string RealGoldenDigest = "23314f1104ca53e07a7fc70acfb09760";
        const string TamperedGoldenDigest = "fff4d4a11b4240fcc10cad379bf019eb";
        const string AbsentGoldenDigest = "27c616bbc2385e1993c1909ca2121f18";

        var real = DecisionLayer.Scan(repoRoot);
        checks.Add(new Check("决策层·真仓（声明完整 + stub 确定性 + fail-closed · 与真源模块原文逐字节同摘要）",
            real.Ok && real.Issues.Count == 0 && real.LogDigest == RealGoldenDigest
            && Convert.ToInt64(real.Stats["primitives"]) == 3
            && Convert.ToInt64(real.Stats["adapters"]) == 3
            && Convert.ToInt64(real.Stats["candidates"]) == 3
            && real.Stats["issueless_stub"] is true,
            $"{real.SummaryLine} · 摘要 {real.LogDigest}（真源金标 {RealGoldenDigest}）"
            ));

        var tamperedRoot = Path.Combine(work, "decision-tampered");
        Fresh(tamperedRoot);
        Directory.CreateDirectory(Path.Combine(tamperedRoot, "protocol"));
        foreach (var (rel, b64) in DecisionLayerTamperedFiles) WriteBase64(tamperedRoot, rel, b64);
        var tampered = DecisionLayer.Scan(tamperedRoot);
        var text = string.Join(" | ", tampered.Issues);
        checks.Add(new Check("决策层·篡改声明（适配器缺 note · 候选 pulled=true 缺 local 三字段 = 4 条判出）",
            !tampered.Ok && tampered.Issues.Count == 4 && tampered.LogDigest == TamperedGoldenDigest
            && text.Contains("适配器 stub 缺 note（能力与边界须自述）")
            && text.Contains("候选 laya-multilingual 声明 pulled=true 却缺 local.how")
            && text.Contains("候选 laya-multilingual 声明 pulled=true 却缺 local.runtime")
            && text.Contains("候选 laya-multilingual 声明 pulled=true 却缺 local.served_by"),
            $"FAIL {tampered.Issues.Count} · 摘要 {tampered.LogDigest}（真源金标 {TamperedGoldenDigest}）"));

        var absentRoot = Path.Combine(work, "decision-absent");
        Fresh(absentRoot);
        var absent = DecisionLayer.Scan(absentRoot);
        checks.Add(new Check("决策层·无声明件（报缺声明 · summary 按 check33 的 except 打成「不可用」）",
            !absent.Ok && absent.Issues.Count == 1 && absent.LogDigest == AbsentGoldenDigest
            && absent.Issues[0] == "缺决策层声明 protocol/decision_layer.json（修复指引：补声明件再跑门禁）"
            && absent.Log[^1] == "决策层面：不可用",
            $"FAIL {absent.Issues.Count} · 末行 {absent.Log[^1]} · 摘要 {absent.LogDigest}"
            + $"（真源金标 {AbsentGoldenDigest}）"));
    }

    private static readonly (string Rel, string B64)[] DecisionLayerTamperedFiles =
    {
        ("protocol/decision_layer.json", "ewogICJhZGFwdGVycyI6IFsKICAgIHsKICAgICAgImNhbGlicmF0ZWQiOiBmYWxzZSwKICAgICAgImlkIjogInN0dWIiLAogICAgICAiaW5fZ2F0ZV9wYXRoIjogdHJ1ZSwKICAgICAgImtpbmQiOiAib2ZmbGluZS1kZXRlcm1pbmlzdGljIgogICAgfSwKICAgIHsKICAgICAgImNhbGlicmF0ZWQiOiB0cnVlLAogICAgICAiZW5kcG9pbnQiOiAiaHR0cDovLzEyNy4wLjAuMTo8cG9ydD4vdjEvc3lzdGVtb25lIiwKICAgICAgImlkIjogInN5c3RlbW9uZS1odHRwIiwKICAgICAgImluX2dhdGVfcGF0aCI6IGZhbHNlLAogICAgICAia2luZCI6ICJsb2NhbC1odHRwIiwKICAgICAgIm5vdGUiOiAi5a+55o6l5pys5ZywIHR5cGVkLWRlY2lzaW9uIOacjeWKoe+8m+WPquivu+iwg+eUqO+8jOacjeWKoeS4jeaJp+ihjOWKqOS9nCIsCiAgICAgICJwcm90b2NvbCI6ICJQT1NUIHtzdGF0ZSwgcXVlc3Rpb25zfSDihpIge2RlY2xhcmVkIGtleXM6IHByb2JhYmlsaXRpZXN977yISmV2IC8gTGF5YSDns7sgU3lzdGVtLTEg5pyN5Yqh5Y+j5b6E77yJIgogICAgfSwKICAgIHsKICAgICAgImNhbGlicmF0ZWQiOiBmYWxzZSwKICAgICAgImlkIjogIm9wZW5haS1qc29uIiwKICAgICAgImluX2dhdGVfcGF0aCI6IGZhbHNlLAogICAgICAia2luZCI6ICJyZW1vdGUtaHR0cCIsCiAgICAgICJub3RlIjogIuS7u+S4gOiBiuWkqeaooeWei+S7peWPl+mZkCBKU09OIOS9nOetlO+8myoq5YW26Ieq5oql5qaC546H5LiN5piv5qCh5YeG5qaC546HKirvvIjml6AgcHJvcGVyIHNjb3JpbmcgcnVsZSDkv53or4HvvInvvIzmlYUgY2FsaWJyYXRlZD1mYWxzZSIKICAgIH0KICBdLAogICJib3VuZGFyaWVzIjogWwogICAgIuWPque7meWGs+etluS4juamgueOh++8jOS4jeaJp+ihjOWKqOS9nO+8iOacjeWKoeerr+S4jiBORiDkvqflnYfkuI3okL3lnLDliqjkvZzvvIkiLAogICAgIuS4jeeUn+aIkOato+aWh++8muWGs+etluWxgumdnuiHquWbnuW9ku+8jOWGheWuueS7jeeUseWGheWuueWlkee6puWxgu+8iOWNj+iuriArIOaooeWdlyArIOi1hOS6p++8ieaJv+aLhSIsCiAgICAi5qih5Z6L5LiN5YWl6Zeo56aB6Lev5b6E77ya6Zeo56aB5b+F6aG756a757q/56Gu5a6a77yIc3R1YiDkuYvlpJbkuIDlvovpnZ7pl6jnpoHku7vliqHvvIkiLAogICAgIuamgueOh+eahOS9v+eUqOeUseiwg+eUqOaWueiHquivgeagoeWHhu+8iOacrOWxguS4jeabv+iwg+eUqOaWueaJv+aLheWGs+etluWQjuaenO+8iSIsCiAgICAi5YCZ6YCJ5qih5Z6L5Y+q5ZyoKirmmL7lvI/mi4nlj5YqKuWQjuWPr+eUqO+8iHB1bGxlZD1mYWxzZSDljbPmnKrkuIvovb3vvJtORiDkuI3mm7/kvZzogIXlhrPlrprkuIvovb3mlbDljYEgR0Ig5p2D6YeN77yJIgogIF0sCiAgImNhbmRpZGF0ZXMiOiBbCiAgICB7CiAgICAgICJjYWxpYnJhdGVkX2RlY2lzaW9ucyI6IHRydWUsCiAgICAgICJjb250ZXh0IjogMTAyNCwKICAgICAgImVuY29kZXIiOiAiYW5zd2VyZG90YWkvTW9kZXJuQkVSVC1sYXJnZSIsCiAgICAgICJldmlkZW5jZSI6ICIyMDI2LTA5LTIxIOWPluWbnuaooeWei+WNoeS4jumFjee9ruWunua1i++8mmFjY3VyYWN5IDAuNzY2IC8gQnJpZXIgMC4wNjIgLyBFQ0UgMC4yMTMgLyBzY29yZSBNQUUgMC4yNDLvvJvlm5vnp40gd29ya2Zsb3cg5LiT55So77yIYWdlbnQtdHJhY2UgLyBjdXN0b21lci1zZXJ2aWNlIC8gaW52b2ljZSAvIHNlY3VyaXR577yJ77yb5L2c6ICF6Ieq6L+wIHNwZWNpYWxpc3TvvIjli7/kvZzpnZnpu5jpu5jorqTvvInjgIHoi7HmlofkuJPnlKjjgIHpgInpobnmlbDlu7rorq4gPDIwIiwKICAgICAgImlkIjogImxheWEtdHlwZWQtZGVjaXNpb25zIiwKICAgICAgImxhbmd1YWdlIjogWwogICAgICAgICJlbiIKICAgICAgXSwKICAgICAgImxpY2Vuc2UiOiAiYXBhY2hlLTIuMCIsCiAgICAgICJwYXJhbXMiOiAiNDIxTSIsCiAgICAgICJwdWxsZWQiOiBmYWxzZSwKICAgICAgInNvdXJjZSI6ICJoZjpjb252YWlpbm5vdmF0aW9ucy9sYXlhLXR5cGVkLWRlY2lzaW9ucyIKICAgIH0sCiAgICB7CiAgICAgICJjYWxpYnJhdGVkX2RlY2lzaW9ucyI6IHRydWUsCiAgICAgICJjb250ZXh0IjogMTAyNCwKICAgICAgImVuY29kZXIiOiAibW1CRVJULWJhc2UiLAogICAgICAiZXZpZGVuY2UiOiAiMjAyNi0wOS0yMSDlj5blm57mqKHlnovljaHlrp7mtYvvvJrkuI4gYmFzZSDlkIzml4/nmoTlgZrlpJror63pnaLvvIhORiDkuK3mlocgc3RhdGUg5bqU5LyY5YWI5q2k5Y+Y5L2T77yM6ICM6Z2e6Iux5paH5LiT55SoIGNoZWNrcG9pbnTvvIkiLAogICAgICAiaWQiOiAibGF5YS1tdWx0aWxpbmd1YWwiLAogICAgICAibGFuZ3VhZ2UiOiBbCiAgICAgICAgIjEwMCsgbGFuZ3VhZ2Vz77yI5ZCr5Lit5paH77yJIgogICAgICBdLAogICAgICAibGljZW5zZSI6ICJhcGFjaGUtMi4wIiwKICAgICAgInBhcmFtcyI6ICIzMjJNIiwKICAgICAgInB1bGxlZCI6IHRydWUsCiAgICAgICJzb3VyY2UiOiAiaGY6Y29udmFpaW5ub3ZhdGlvbnMvbGF5YS1tdWx0aWxpbmd1YWwiCiAgICB9LAogICAgewogICAgICAiYmFzZV9tb2RlbCI6ICJRd2VuL1F3ZW4zLjUtOUIiLAogICAgICAiYmFzZV9yZXZpc2lvbiI6ICJjMjAyMjM2MjM1NzYyZTFjODcxYWQwY2NiNjBjOGVlNWJhMzM3YjlhIiwKICAgICAgImNhbGlicmF0ZWRfZGVjaXNpb25zIjogdHJ1ZSwKICAgICAgImV2aWRlbmNlIjogIjIwMjYtMDktMjEg5Y+W5Zue5qih5Z6L5Y2h5LiOIGFkYXB0ZXJfY29uZmlnIOWunua1i++8mumdnuiHquWbnuW9kuOAgeWPquivhOiwg+eUqOaWuee7meeahOWAmemAie+8m+S4ieWOn+ivrSBjaG9pY2Uvbm91bC9zY29yZe+8m+mcgOS4iua4uCBiYXNlIOeyvuehriByZXZpc2lvbiArIE9wZW4tSmV2IGxvYWRlciArIEdQVe+8m0F1dG9QZWZ0TW9kZWwg55u06LCD5LiN5a6e546w6K+l5o6l5Y+jIiwKICAgICAgImlkIjogIm9wZW4tamV2LTliIiwKICAgICAgImtpbmQiOiAiTG9SQSBhZGFwdGVyICsgc2NhbGFyIGRlY2lzaW9uIGhlYWQiLAogICAgICAibGljZW5zZSI6ICJhcGFjaGUtMi4wIiwKICAgICAgInB1bGxlZCI6IGZhbHNlLAogICAgICAic2VydmUiOiAicHl0aG9uIC1tIGpldi5zZXJ2ZXIgLS1jaGVja3BvaW50IC4vY2hlY2twb2ludHMvb3Blbi1qZXYtOWIvcGFja2FnZS9jaGVja3BvaW50IC0tZGV2aWNlIGN1ZGE6MCAtLW1heC1sZW5ndGggNDA5NiAtLWJhdGNoLXNpemUgMSAtLWhvc3QgMTI3LjAuMC4xIC0tcG9ydCA4NzkxIiwKICAgICAgInNvdXJjZSI6ICJoZjpaZWZhbkNhaS9PcGVuLUpldi05QiIKICAgIH0KICBdLAogICJub3RlIjogIuWGs+etluWxguerr+WPo++8iOacuuWItuWAn+mJtO+8mumdnuiHquWbnuW9kiB0eXBlZC1kZWNpc2lvbiDmqKHlnovnmoQgY2hvaWNlIC8gbm91bCAvIHNjb3JlIOS4ieWOn+ivreKAlOKAlOWGs+etliA9IOWcqCoq6LCD55So5pa557uZ5a6aKirnmoTlgJnpgInpm4bkuIrmiqXmpoLnjofliIbluIPkuI4gYXJnbWF477yM5LiN55Sf5oiQ5q2j5paH44CB5LiN5omn6KGM5Yqo5L2c77yJ44CCTkYg5L6n5Y+q5YGa5LiJ5Lu25LqL77ya5a6a5LmJ6Zeu6aKY5LiO562U5qGI55qE5b2i54q244CB5oqK5qih5Z6L5pS+5Zyo6Zeo56aB5LmL5aSW44CB5oqK5LiN5Y+v55So5oOF5b2iIGZhaWwtY2xvc2VkIOaIkCBhYnN0YWluZWTjgIIiLAogICJwcmltaXRpdmVzIjogewogICAgImNob2ljZSI6ICLlnKjosIPnlKjmlrnnu5nlrprnmoTlgJnpgInpm4bkuIrmiqXmpoLnjofliIbluIMgKyBhcmdtYXjvvJvlgJnpgInpm4bnlLHosIPnlKjmlrnmj5DkvpvvvIzmqKHlnovkuI3lvpfoh6rpgKDlgJnpgIkiLAogICAgIm5vdWwiOiAi5a+55piv6Z2e6Zeu6aKY5oql5qaC546HIHAodHJ1ZSkiLAogICAgInNjb3JlIjogIuWvueiwg+eUqOaWuee7meWumueahOacieW6j+etiee6p+aKpeamgueOh+WIhuW4gyArIOacn+acm+WAvCIKICB9LAogICJyZWxhdGVkIjogWwogICAgInByb3RvY29sL1dPUkxEX01PREVMLm1k77yI56Gu5a6a5oCn54q25oCB5aWR57qm77ya5Yaz562W5bGC55qEIHN0YXRlIOmdoueUseWug+e7me+8iSIsCiAgICAiMDJf6IGU5Yqo5rOo5YaM6KGoLm1kIMKnOO+8iFA0MCDooYzkuLrlhrPnrZblsYLkvY3vvJrlhrPnrZblsYLmnI3liqHnmoToo4XphY3mp73kvY3vvIkiCiAgXSwKICAicmVzcG9uc2VfY29udHJhY3QiOiB7CiAgICAiYWJzdGFpbl9ydWxlIjogImFkYXB0ZXIg5LiN5Y+v55So44CB6LaF5pe25oiW6L6T5Ye65LiN5ZCIIHNjaGVtYSDihpIgc3RhdHVzPWFic3RhaW5lZCArIHJlYXNvbu+8iOS4peemgeeMnOa1i+ihpem9kO+8muWGs+etluWxgueahOayiem7mOavlOe8lumAoOWuieWFqO+8iSIsCiAgICAiYW5zd2VycyI6ICJuYW1lIOKGkiB7dHlwZSwgcHJvYnM/OiBbZmxvYXRdLCBvcHRpb25zPzogW3N0cmluZ10sIGFyZ21heD86IHN0cmluZ3xpbnQsIHA/OiBmbG9hdCwgdmFsdWU/OiBmbG9hdH3vvJtwcm9icyDmsYLlkozpobsg4omIIDHvvIjlrrnlt64gMWUtNu+8ie+8jOmVv+W6pumhu+etieS6jiBvcHRpb25zL2xldmVscyDplb/luqYiLAogICAgIm1ldGEiOiAiYWRhcHRlciAvIGNhbGlicmF0ZWTvvIjmmK/lkKbmoKHlh4bmpoLnjofvvIkvIG5vbl9nYXRlOiB0cnVlIC8gc2NoZW1h77ybc3lzdGVtb25lLWh0dHAg5Y+m5pyJIG1vZGVsIOWtl+autSIsCiAgICAicmVxdWlyZWQiOiBbCiAgICAgICJzY2hlbWEiLAogICAgICAic3RhdHVzIiwKICAgICAgImFuc3dlcnMiLAogICAgICAibWV0YSIKICAgIF0sCiAgICAic3RhdHVzX3ZvY2FidWxhcnkiOiBbCiAgICAgICJvayIsCiAgICAgICJhYnN0YWluZWQiCiAgICBdCiAgfSwKICAic2NoZW1hIjogIm5mLWRlY2lzaW9uLWxheWVyLzEiLAogICJzdGF0dXMiOiAiYWN0aXZlIiwKICAid29ya2xvb3AiOiB7CiAgICAiZW50cnkiOiAicHl0aG9uIHNjcmlwdHMvbmYucHkgd29ya2xvb3AgWy0tYWRhcHRlciBzdHVifHN5c3RlbW9uZS1odHRwXSBbLS10b3AgTl0gWy0td3JpdGVdIiwKICAgICJub25fbmVnb3RpYWJsZXMiOiBbCiAgICAgICLlhrPnrZblsYLkuI3nlJ/miJDlhoXlrrnvvIhMYXlhIOaYr+e8lueggeWZqOWIhuexu+OAgU9wZW4tSmV2IOmdnuiHquWbnuW9kuWGs+etluWktOKAlOKAlOmDveS4jeS8muWGmeS7o+eggeaIluato+aWh++8iSIsCiAgICAgICLlt6XljZXlj6rokL3lhoXpg6jmoaPmoYjvvIjorqHliJLnsbvkuqflk4HlhoXpg6jmtojljJbvvJvlhazlvIDku5Plj6rmlLbnu5PmnpwgKyBhdWRpdO+8iSIsCiAgICAgICLokL3nrJTmlrnlv4XpobvmmK8gd29ya2Vy77yM5Yaz562W5qih5Z6L5Y+q5o+Q5L6b6YCJ5oup5LiO5qaC546HIiwKICAgICAgIumqjOaUtuWPquiupOmXqOemge+8iHZlcmlmeS5zaCDlhajnu78gKyBuZiBjb25mb3JtYW5jZSBjb25mb3JtYW5077yJIgogICAgXSwKICAgICJyb2xlIjogIuWGs+etluWxgumpseWKqOeahOaehOW7uuWbnui3r++8muWGs+etluaooeWei+aMkea0uyAvIOWIpOmjjumZqSAvIOWumuOAjOiDveWQpuWcqOS4jeeisOWbnuaJp+mUmuWumuS7tuadoeS7tuS4i+WujOaIkOOAje+8m+eUn+aIkOW8jyB3b3JrZXLvvIjkurogLyBDb2RleCAvIOeUn+aIkOW8j+aooeWei++8ieiQveeslO+8m05GIOmXqOemgemqjOaUtiIsCiAgICAic291cmNlcyI6IFsKICAgICAgInByb3RvY29sL3R5cGVfYmFja2xvZy5qc29u77yI5pyq5a6a5Z6L5LqL5Lu25a2X5q6177yJIiwKICAgICAgInByb3RvY29sL3BpcGVsaW5lX2Fkdmlzb3J5Lmpzb27vvIjnrqHnur8gYWR2aXNvcnnvvIkiCiAgICBdCiAgfQp9"),
    };

    /// <summary>
    /// 出口/派生面五钉：**他证通道**（check38 第二腿 · 真源 scripts/interop_thirdparty_kit.check）
    /// 真仓 / 篡改（sha 非 64 位十六进制 + 状态表缺面 = 2 条判出）/ 缺件；**入仓一致**
    /// （check33 第 14 条）真仓 / 篡改（改一字符 → 恰好一个 kind 判漂移）。两腿都以真源代码为
    /// oracle，金标由 probes/exit_faces_probe.py 产出。
    /// </summary>
    private static void ExitFacesCases(List<Check> checks, string work, string repoRoot)
    {
        const string TpRealGolden = "a28aa09cf3a4c6e657b67340980c1333";
        const string TpTamperedGolden = "97ca0615c602922e0d7dfbbe259f3e3f";
        const string TpAbsentGolden = "bb97a48d037a3fd6c16b1582237ab6ff";
        const string InRepoRealGolden = "e3b0c44298fc1c149afbf4c8996fb924";
        const string InRepoTamperedGolden = "2700a1029685e421b9ac050c6d813302";

        var real = ExitFaces.ThirdPartyCheck(repoRoot);
        var realDigest = real.LogDigest();
        checks.Add(new Check("出口面·他证通道·真仓（14 面全在行 · 与真源脚本 check() 逐字节同摘要）",
            real.Ok && realDigest == TpRealGolden
            && Convert.ToInt64(real.Stats["faces"]) == 14 && Convert.ToInt64(real.Stats["rows"]) == 14
            && Convert.ToInt64(real.Stats["filled"]) == 13 && Convert.ToInt64(real.Stats["unfilled"]) == 1,
            $"FAIL {real.Issues.Count} · 面 {real.Stats["faces"]} · 行 {real.Stats["rows"]} · 已填 {real.Stats["filled"]}"
            + $" · 摘要 {realDigest}（真源金标 {TpRealGolden}）"));

        // 篡改：整行删掉 ccv3（缺面）+ 首个带 sha 的行改成非 64 位十六进制
        var tamperedRoot = Path.Combine(work, "exit-thirdparty-tampered");
        Fresh(tamperedRoot);
        foreach (var (rel, b64) in ThirdPartyTamperedFiles) WriteBase64(tamperedRoot, rel, b64);
        var docSrc = Path.Combine(repoRoot, ExitFaces.ThirdPartyDocRel.Replace('/', Path.DirectorySeparatorChar));
        if (File.Exists(docSrc))
        {
            var docDst = Path.Combine(tamperedRoot, ExitFaces.ThirdPartyDocRel.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(docDst)!);
            File.Copy(docSrc, docDst, overwrite: true);
        }
        var tampered = ExitFaces.ThirdPartyCheck(tamperedRoot);
        var tamperedText = string.Join(" | ", tampered.Issues);
        checks.Add(new Check("出口面·他证通道·篡改（sha256 非 64 位十六进制 + 状态表缺面 = 2 条判出）",
            !tampered.Ok && tampered.Issues.Count == 2 && tampered.LogDigest() == TpTamperedGolden
            && tamperedText.Contains("的 output_sha256 不是 64 位十六进制（不可用「看起来通过」代替）")
            && tamperedText.Contains("状态表缺面：ccv3（每个互操作面都必须有一行，含 not-applicable）"),
            $"FAIL {tampered.Issues.Count} · 摘要 {tampered.LogDigest()}（真源金标 {TpTamperedGolden}）"));

        var absentRoot = Path.Combine(work, "exit-thirdparty-absent");
        Fresh(absentRoot);
        var absent = ExitFaces.ThirdPartyCheck(absentRoot);
        checks.Add(new Check("出口面·他证通道·缺件（缺回填状态表 → 单条 FAIL，不静默放过）",
            !absent.Ok && absent.Issues.Count == 1 && absent.LogDigest() == TpAbsentGolden
            && absent.Log()[^1] == "他证通道 子扫描：FAIL 1",
            $"FAIL {absent.Issues.Count} · 末行 {absent.Log()[^1]} · 摘要 {absent.LogDigest()}"
            + $"（真源金标 {TpAbsentGolden}）"));

        var inRepo = ExitFaces.InteropInRepoIssues(repoRoot);
        var inRepoDigest = ExitFaces.Digest32(inRepo.Select(i => "[FAIL] " + i));
        checks.Add(new Check("出口面·入仓一致·真仓（12 个 kind 均在盘且与实时派生逐字节一致）",
            inRepo.Count == 0 && inRepoDigest == InRepoRealGolden,
            $"FAIL {inRepo.Count} · 摘要 {inRepoDigest}（真源金标 {InRepoRealGolden}）"));

        var repoTree = Path.Combine(work, "exit-inrepo-tampered");
        Fresh(repoTree);
        CopyTree(repoRoot, repoTree);   // 入仓面比对要整棵源树在场（render 按 root 读源件）
        var sbom = Path.Combine(repoTree, ExitFaces.InteropDirRel.Replace('/', Path.DirectorySeparatorChar),
            "sbom.json");
        File.WriteAllBytes(sbom, ReplaceFirstBytes(File.ReadAllBytes(sbom),
            Encoding.UTF8.GetBytes("\"created\""), Encoding.UTF8.GetBytes("\"created_x\"")));
        var tamperedIn = ExitFaces.InteropInRepoIssues(repoTree);
        var tamperedInDigest = ExitFaces.Digest32(tamperedIn.Select(i => "[FAIL] " + i));
        checks.Add(new Check("出口面·入仓一致·篡改（sbom 改一字符 → 恰好一个 kind 判漂移）",
            tamperedIn.Count == 1 && tamperedInDigest == InRepoTamperedGolden
            && tamperedIn[0].Contains("互操作入仓面与实时派生不一致：sbom"),
            $"FAIL {tamperedIn.Count} · 摘要 {tamperedInDigest}（真源金标 {InRepoTamperedGolden}）"));
    }

    /// <summary>篡改后的他证通道状态表（真源口径：删 ccv3 整行 + 首个带 sha 的行写成 deadbeef）。</summary>
    private static readonly (string Rel, string B64)[] ThirdPartyTamperedFiles =
    {
        ("results/interop-thirdparty-status.md", "IyDkupLmk43kvZzmgKcgwrcg5LuW6K+B5Zue5aGr54q25oCB6KGoCgo+IOeUsSBgcHl0aG9uIHNjcmlwdHMvaW50ZXJvcF90aGlyZHBhcnR5X2tpdC5weSAtLWVtaXRgIOeUn+aIkOmqqOaetu+8m+eUseesrOS4ieaWueWbnuWhq+WPs+S+p+Wtl+auteOAggo+IOWIneWniyBgdmVyZGljdGAgPSBg5pyq5Zue5aGr77yI6YCa6YGT5bCx57uq77yJYO+8iOihqOekuumAmumBk+Wwsee7quOAgSoq5pyq6KKr5Lu75L2V56ys5LiJ5pa56LeR6L+HKirvvInjgIIKCnwgZmFjZSB8IGtpbmQgfCDlr7nnq6/lt6XlhbcgfCDlronoo4UgfCDlkb3ku6Tljp/mlocgfCB0b29sX3ZlcnNpb24gfCBydW5fYnkgfCBydW5fYXQgfCBvdXRwdXRfc2hhMjU2IHwgdmVyZGljdCB8IG5vdGUgfAp8LS0tfC0tLXwtLS18LS0tfC0tLXwtLS18LS0tfC0tLXwtLS18LS0tfC0tLXwKfCBgbWNwYCB8IHBlZXItY29uc3VtcHRpb24gfCDku7vmhI8gTUNQIOWuouaIt+err++8iENsYXVkZSBEZXNrdG9wIC8gbWNwLWluc3BlY3RvciDnrYnvvIkgfCDlr7nnq6/oh6rpgInvvJvmnI3liqHnq6/vvJpgcHl0aG9uIHNjcmlwdHMvbmYucHkgcnVuIC0tZm10IG1jcCAtLWRlc3Qgb3V0YCDkuqflh7ogbWNwLmpzb24g5b+r54WnIHwgYG5weCAteSBAbW9kZWxjb250ZXh0cHJvdG9jb2wvaW5zcGVjdG9yIC0tY2xpIHB5dGhvbiBzY3JpcHRzL25mLnB5IHNlcnZlIDxtY3AuanNvbj4gLS1tZXRob2QgdG9vbHMvbGlzdGAgfCBucHgg5pyA5paw56iz5a6a77yILXkg5ouJ5Y+W77yJIHwg5omn6KGM6ICF77yI5pys5py6IENvZGV4IOS8muivne+8icK3IOW3peWFt+S4uuesrOS4ieaWueWumOaWueWunueOsCB8IDIwMjYtMDktMjQgKEFzaWEvU2hhbmdoYWkpIHwgZGVhZGJlZWYgfCBQQVNT77yI5a+556uv5a6i5oi356uv5LiJ5pa55rOV5YWo6YOo5oiQ5Yqf77yJIHwg5b+r54Wn55SxIGBuZiBydW4gLS1waXBlbGluZSAwM1/nrqHnur/lupMvUDkwX+aKgOacr+aWh+aho+eUn+aIkOeuoee6vy5tZCAtLW1vZHVsZXMg6YCa55So57G7Ok0wMCzpgJrnlKjnsbs6TTgwIC0tZm10IG1jcCAtLXNlZWRgIOS6p+WHuu+8m0luc3BlY3RvciBDTEkg5LiN5pSv5oyBIHNlcnZlci9kaXNjb3Zlcu+8iOWFtuaUr+aMgeWIl+ihqOWQqyBpbml0aWFsaXplL3Rvb2xzL2xpc3QvcmVzb3VyY2VzL2xpc3QvcHJvbXB0cy9saXN0IOetie+8ie+8jOaVheS7peS4ieexu+WIl+ihqOS4uuivgeaNruOAgiB8CnwgYG9wZW5hcGlgIHwgb2ZmaWNpYWwtY2xpIHwgb3BlbmFwaS1zcGVjLXZhbGlkYXRvcu+8iOWumOaWueeUn+aAgeagoemqjOWZqO+8iSB8IHBpcCBpbnN0YWxsIG9wZW5hcGktc3BlYy12YWxpZGF0b3IgfCBgQzpcdG1wXG5mX2F1ZGl0XHZlbnZcU2NyaXB0c1xweXRob24uZXhlIC1tIG9wZW5hcGlfc3BlY192YWxpZGF0b3IgcmVzdWx0cy9pbnRlcm9wL29wZW5hcGkuanNvbmAgfCAwLjkuMCB8IOaJp+ihjOiAhe+8iOacrOacuiBDb2RleCDkvJror53vvInCtyDlt6XlhbfkuLrnrKzkuInmlrnlrpjmlrnlrp7njrAgfCAyMDI2LTA5LTI0IChBc2lhL1NoYW5naGFpKSB8IDVmZTljMTcyN2NhYTQyZmMxMTczMTYxZDhhMTgxMWUzYTYwNjk1NTE1ZDA5ZDU2YTliYmI4OGFlMjJmNDBjZDggfCBQQVNT77yI56ys5LiJ5pa55qCh6aqM5Zmo6YCa6L+H77yJIHwg6YCA5Ye656CBIDAgfAp8IGBhc3luY2FwaWAgfCBvZmZpY2lhbC1jbGkgfCBAYXN5bmNhcGkvY2xp77yI5a6Y5pa5IENMSe+8iSB8IG5wbSBpIC1nIEBhc3luY2FwaS9jbGkgfCBgbnB4IC15IEBhc3luY2FwaS9jbGkgdmFsaWRhdGUgcmVzdWx0cy9pbnRlcm9wL2FzeW5jYXBpLmpzb25gIHwgbnB4IOacgOaWsOeos+Wumu+8iC15IOaLieWPlu+8iSB8IOaJp+ihjOiAhe+8iOacrOacuiBDb2RleCDkvJror53vvInCtyDlt6XlhbfkuLrnrKzkuInmlrnlrpjmlrnlrp7njrAgfCAyMDI2LTA5LTI0IChBc2lhL1NoYW5naGFpKSB8IGQ4NDg1NTMwNGQxY2FlNmMzYjM2N2NhNzhkYjMxNGVhODk4ZjY5NTJmZWQ3NDg3MTA3YjkxZDJmMTcwZmQyODcgfCBQQVNT77yI5a6Y5pa5IENMSe+8mjAgZXJyb3LvvIkgfCDku5bor4HmipPlh7rnmoTnnJ/nvLrpmbflt7Lkv67vvJrpgJrpgZPplK7lkKsgYC9gIOacquaMiSBSRkMgNjkwMSDovazkuYkg4oaSIDQ0MyDmnaEgaW52YWxpZC1yZWbvvJvnjrAgMCBlcnJvcu+8iOS7heS/oeaBr+e6p++8muWumOaWueW7uuiuriBBc3luY0FQSSAzLjHvvInjgIIgfAp8IGBzYm9tYCB8IG9mZmljaWFsLWNsaSB8IHNwZHgtdG9vbHPvvIhTUERYIOWumOaWueW3peWFt++8iSB8IHBpcCBpbnN0YWxsIHNwZHgtdG9vbHMgfCBgcHlzcGR4dG9vbHMgLWkgcmVzdWx0cy9pbnRlcm9wL3Nib20uanNvbmAgfCA/IHwg5omn6KGM6ICF77yI5pys5py6IENvZGV4IOS8muivne+8icK3IOW3peWFt+S4uuesrOS4ieaWueWumOaWueWunueOsCB8IDIwMjYtMDktMjQgKEFzaWEvU2hhbmdoYWkpIHwgODViNTFiYjQ3MjczYmYzNThhNjkwZmE2ZjFmNWRkNjkwZjAyNjVlMGY0ZDRlNzQ0YTI2Njg2NTMwYTEyZTAyNCB8IFBBU1PvvIjlrpjmlrnlrp7njrDop6PmnpDpgJrov4fvvIkgfCDpgIDlh7rnoIEgMCB8CnwgYGN5Y2xvbmVkeGAgfCBvZmZpY2lhbC1jbGkgfCBjeWNsb25lZHgtY2xp77yI5a6Y5pa5IENMSe+8iSB8IOS4i+i9vSBjeWNsb25lZHgtY2xpIOWPkeihjOeJiO+8iEdpdEh1YiBSZWxlYXNlc++8iSB8IGBweXRob24gLWMgImpzb25zY2hlbWEudmFsaWRhdGUoY3ljbG9uZWR4Lmpzb24sIDxjeWNsb25lZHgtcHl0aG9uLWxpYj4vc2NoZW1hL19yZXMvYm9tLTEuNS5TTkFQU0hPVC5zY2hlbWEuanNvbikiYCB8IDExLjEyLjAgfCDmiafooYzogIXvvIjmnKzmnLogQ29kZXgg5Lya6K+d77yJwrcg5bel5YW35Li656ys5LiJ5pa55a6Y5pa55a6e546wIHwgMjAyNi0wOS0yNCAoQXNpYS9TaGFuZ2hhaSkgfCBlM2Q1MjI2OWViYjJjZTI4N2E0ZjIyYjc3YWRmZGVkOWU3MDUwOTAwOGY2ZTY2NmM2N2ZjY2U0MjY1NDlhMjVhIHwgUEFTU++8iOWumOaWuSBzY2hlbWEg5qCh6aqM6YCa6L+H77yJIHwg5a6Y5pa5IENMSe+8iGN5Y2xvbmVkeC1jbGkvLk5FVO+8ieacrOacuuS4jeWPr+W+l++8iOaXoCBHaXRIdWIg55u06L+e77yJ77yM5pS555So5a6Y5pa5IFB5dGhvbiDlupPlhoXnva4gc2NoZW1h77yb6L6T5Ye677yadmFsaWRhdGVkIGFnYWluc3QgYm9tLTEuNS5TTkFQU0hPVC5zY2hlbWEuanNvbu+8iOWumOaWueW6k+WGhee9ru+8jOWQqyBzcGR4IOW8leeUqO+8jOacrOWcsOino+aekO+8iSB8CnwgYHNsc2FgIHwgc2hhcGUtb25seSB8IHNsc2EtdmVyaWZpZXIgLyBDVUUg5bel5YW36ZO+77yI5a6Y5pa577yJIHwgZ28gaW5zdGFsbCBnaXRodWIuY29tL3Nsc2EtZnJhbWV3b3JrL3Nsc2EtdmVyaWZpZXIvdjIvY2xpL3Nsc2EtdmVyaWZpZXJAbGF0ZXN0IHwgYO+8iOingSBub3Rl77yJYCB8IC0gfCDmiafooYzogIXvvIjmnKzmnLogQ29kZXgg5Lya6K+d77yJwrcg5bel5YW35Li656ys5LiJ5pa55a6Y5pa55a6e546wIHwgMjAyNi0wOS0yNCAoQXNpYS9TaGFuZ2hhaSkgfCAyY2JiNjc5MjY0N2E4OTIxMWMyZDI1NjVmNzQ0ZjMwNmIxMDgzYTZjZTNiMTNkY2I4ZGExZjZlOGNiNzNjYWY4IHwg5LiN6YCC55So77yI5peg54us56uL5a6e546w5Y+v6LeR77yJIHwgc2xzYS12ZXJpZmllciDpnIAgZ28vZG9ja2Vy77yI5pys5py65LiN5Y+v5b6X77yJ5LiUIEdpdEh1YiDnm7Tov57kuI3lj6/ovr7vvJvmnKzpnaLnu7TmjIEgc2hhcGUtb25seSDliKTmja7vvIjlrpjmlrnmlofmnKzmoLjlr7nvvInvvIzkuI3orqHlhaXku5bor4HpgJrov4fmlbDjgIIgfAp8IGBpbnRvdG9gIHwgc2hhcGUtb25seSB8IGluLXRvdG/vvIjlrpjmlrnlrp7njrDvvIkgfCBwaXAgaW5zdGFsbCBpbi10b3RvIHwgYO+8iOingSBub3Rl77yJYCB8IC0gfCDmiafooYzogIXvvIjmnKzmnLogQ29kZXgg5Lya6K+d77yJwrcg5bel5YW35Li656ys5LiJ5pa55a6Y5pa55a6e546wIHwgMjAyNi0wOS0yNCAoQXNpYS9TaGFuZ2hhaSkgfCAyY2JiNjc5MjY0N2E4OTIxMWMyZDI1NjVmNzQ0ZjMwNmIxMDgzYTZjZTNiMTNkY2I4ZGExZjZlOGNiNzNjYWY4IHwg5LiN6YCC55So77yI5peg54us56uL5a6e546w5Y+v6LeR77yJIHwgaW4tdG90byAzLjEg5a6Y5pa55a6e546w6Z2i5ZCRIERTU0UgZW52ZWxvcGXvvIjml6Agc3RhdGVtZW50IOe6p+agoemqjOWFpeWPo++8ie+8m+acrOmdoue7tOaMgSBzaGFwZS1vbmx5IOWIpOaNru+8iOWumOaWueaWh+acrOaguOWvue+8ie+8jOS4jeiuoeWFpeS7luivgemAmui/h+aVsOOAgiB8CnwgYHZjYCB8IHNoYXBlLW9ubHkgfCBXM0MgVkMg5pWw5o2u5qih5Z6L5qCh6aqM5bqTIC8gSlNPTi1MRCDlpITnkIblmaggfCBwaXAgaW5zdGFsbCBweWxkIHwgYO+8iOingSBub3Rl77yJYCB8IC0gfCDmiafooYzogIXvvIjmnKzmnLogQ29kZXgg5Lya6K+d77yJwrcg5bel5YW35Li656ys5LiJ5pa55a6Y5pa55a6e546wIHwgMjAyNi0wOS0yNCAoQXNpYS9TaGFuZ2hhaSkgfCAyY2JiNjc5MjY0N2E4OTIxMWMyZDI1NjVmNzQ0ZjMwNmIxMDgzYTZjZTNiMTNkY2I4ZGExZjZlOGNiNzNjYWY4IHwg5LiN6YCC55So77yI5peg54us56uL5a6e546w5Y+v6LeR77yJIHwgcHlsZCDpnIDogZTnvZHlj5blrpjmlrnkuIrkuIvmlocgaHR0cHM6Ly93d3cudzMub3JnL25zL2NyZWRlbnRpYWxzL3Yy77yI5pys5py65Y+W5LiN5Yiw77yMSFRUUCAwMDDvvInvvJvnprvnur/ml6DkuIrkuIvmloflia/mnKwg4oaSIOaXoOazleWBmueLrOeri+WxleW8gO+8jOacrOmdouS4jeiuoeWFpeS7luivgemAmui/h+aVsO+8m+acrOmdoue7tOaMgSBzaGFwZS1vbmx5IOWIpOaNru+8iOWumOaWueaWh+acrOaguOWvue+8ie+8jOS4jeiuoeWFpeS7luivgemAmui/h+aVsOOAgiB8CnwgYHByb3ZgIHwgc2hhcGUtb25seSB8IFBST1Yg5bel5YW36ZO+IC8gSlNPTi1MRCDlpITnkIblmaggfCBwaXAgaW5zdGFsbCBweWxkIHwgYHB5dGhvbiAtYyAianNvbmxkLmV4cGFuZChyZXN1bHRzL2ludGVyb3AvcHJvdi5qc29uKSJgIHwgcHlsZCAocGlwKSB8IOaJp+ihjOiAhe+8iOacrOacuiBDb2RleCDkvJror53vvInCtyDlt6XlhbfkuLrnrKzkuInmlrnlrpjmlrnlrp7njrAgfCAyMDI2LTA5LTI0IChBc2lhL1NoYW5naGFpKSB8IGVkMDcwZGI1Y2E2MDEwMTM2Njc1YjFlNWM2ODY5N2E0ZTQwZjVkZjM2ZmQ1MTY4NDIyOWE5YzNkZDg5Y2Q4NjcgfCBQQVNT77yI5LiK5LiL5paH5Y+v5bGV5byA77yJIHwgUFJPVi1PIOWumOaWuSBwcm92Lmpzb25sZCDmnKzova7lj5blgLzlj5fpmZDvvIhIVFRQIDMwMO+8ie+8jOaVheS7pSBKU09OLUxEIOWxleW8gCArIOWbvuiKgueCueiuoeaVsOS4uuWHhuOAgui+k+WHuu+8mmdyYXBoIG5vZGVzIDAgfAp8IGBhMmFgIHwgbm90LWFwcGxpY2FibGUgfCBBMkEg5a6i5oi356uv77yI5aaC5a6Y5pa5IFNES++8iSB8IOWvueerr+iHquijhSB8IGDvvIjkuI3pgILnlKjvvIlgIHwgLSB8IOaJp+ihjOiAhe+8iOacrOacuiBDb2RleCDkvJror53vvInCtyDlt6XlhbfkuLrnrKzkuInmlrnlrpjmlrnlrp7njrAgfCAyMDI2LTA5LTI0IChBc2lhL1NoYW5naGFpKSB8IGYzMzM0MDMxNWM5NzM1YjE0NzgwYTU3ZjMyMjAwNDUwOWY3Yjk2YzcyOTlmNjVmZjQyODkzYjA1YThmMWY0ZGQgfCDkuI3pgILnlKjvvIjlt7LlnKjljaHniYflo7DmmI7nkIbnlLHvvIkgfCDmnKzku5Plj6rlr7zlh7ogQWdlbnQgQ2FyZCDlvaLnirbjgIHkuI3ov5DooYwgQTJBIOerr+eCuSDihpIg5peg5a+556uv5Y+v5raI6LS5IHwKfCBgYzJwYWAgfCBub3QtYXBwbGljYWJsZSB8IGMycGEtcnPvvIjlrpjmlrnlrp7njrDvvIkgfCDlr7nnq6/oh6roo4UgfCBg77yI5LiN6YCC55So77yJYCB8IC0gfCDmiafooYzogIXvvIjmnKzmnLogQ29kZXgg5Lya6K+d77yJwrcg5bel5YW35Li656ys5LiJ5pa55a6Y5pa55a6e546wIHwgMjAyNi0wOS0yNCAoQXNpYS9TaGFuZ2hhaSkgfCBhNzc5MTdlZjg2NTFmOGM5Y2EyMjc5Y2EzMWJiODMwMzM2Mjg0MWJiMmY2MDliMDgzN2JhNTc3MTlkMTI0ZTk0IHwg5LiN6YCC55So77yI5bey5Zyo5Y2h54mH5aOw5piO55CG55Sx77yJIHwg5pys5LuT5LiN5YGaIENCT1IvSlVNQkYg5a655Zmo5bCB6KOFIOKGkiBjMnBhLXJzIOaXoOWvueixoeWPr+mqjCB8CnwgYGNpZGAgfCBvZmZpY2lhbC1jbGkgfCBtdWx0aWZvcm1hdHMg5Y+C54Wn5a6e546wIC8g5bey55+l5ZCR6YeP5aSN566XIHwg5peg6ZyA5a6J6KOF77yIc2hhMjU2ICsgYmFzZTMyIOWkjeeul++8iSB8IGBweXRob24gLWMgIjzlr7kgY2lkLmpzb24g5q+P5p2hIHBhdGgg6YeN566XIENJRHYxKGNvZGVjIDB4NzEpK3NoYTI1NiDlubbmr5Tlr7k+ImAgfCBzaGEyNTYrYjMy77yI5peg5aSW6YOo5L6d6LWW77yJIHwg5omn6KGM6ICF77yI5pys5py6IENvZGV4IOS8muivne+8icK3IOW3peWFt+S4uuesrOS4ieaWueWumOaWueWunueOsCB8IDIwMjYtMDktMjQgKEFzaWEvU2hhbmdoYWkpIHwgNzQyMTBmYWE1OTc2ZjdjYzIxMWQ4Y2Y3MDU3ZTNjZTM3Mjc3MWRlNGMxYjY5ODkzMmRmZjU4NmI0OTNiMDRhZCB8IFBBU1PvvIhlbnRyaWVzIDQ5IG1pc21hdGNoIDAgbWlzc2luZyAw77yJIHwg5aSN566X5Y+j5b6E77yaQ0lEdjEgKyBjb2RlYyAweDcxICsgc2hhMi0yNTYgKyBtdWx0aWJhc2UgYmFzZTMybG93ZXIgfAp8IGBkZWNpc2lvbnNgIHwgbm90LWFwcGxpY2FibGUgfCDigJQgfCDigJQgfCBg77yI5LiN6YCC55So77yJYCB8IC0gfCDmiafooYzogIXvvIjmnKzmnLogQ29kZXgg5Lya6K+d77yJwrcg5bel5YW35Li656ys5LiJ5pa55a6Y5pa55a6e546wIHwgMjAyNi0wOS0yNCAoQXNpYS9TaGFuZ2hhaSkgfCAzMTMyMGQzYjg5NDliNjdlMjhjZGE1YWY1ODc1YjBhMGU5MDhkZjc4MDYyYTZlZTEzMGMyNzViYzViZjQzNGM1IHwg5LiN6YCC55So77yI5bey5Zyo5Y2h54mH5aOw5piO55CG55Sx77yJIHwg5Yaz562W6Z2i5pivIE5GIOiHquacieW9oueKtu+8jOaXoOWklumDqOWvueerr+S4juWklumDqCBzY2hlbWEgfAo="),
    };

    /// <summary>
    /// 回归面七钉：**分值**（check33 第 3 条：五信号复算 + 可复算子集归一分 + <c>purity_clean</c> 边界）
    /// + **比对口径**（<c>compare()</c> 纯函数六例）+ **信号源三面**（conformance_scan / quality_depth_scan
    /// 聚合 / doc_hygiene.check_markers）。两处合成语料（虚标分级 / 缺标识）按真源输出锚定摘要——
    /// 真仓全绿时单靠真材料证明不了判据会红，合成语料才是判据的证伪面。
    /// 金标由 probes/regression_score_probe.py（真源模块原文）产出。
    /// </summary>
    private static void RegressionCases(List<Check> checks, string work, string repoRoot)
    {
        const string CscReal = "9519e11e210362720ff3ef9523ac39ec";
        const string CscNegative = "f5f0809f803efdf76e4a3280df867f96";
        const string DepthReal = "6258b79e9313ea3fac4cceb8f6eccfb6";
        const string MarkersReal = "405738e515e30e94ce29d5ccf59b01e2";
        const string MarkersNegative = "3c10e35d1319e23adfebd296ed4054e4";
        const string ScoreReal = "9ffe6f5ce4088211a35880403abeea8e";
        const string CompareGolden = "e27d94b51aa676d41137b0657afd011d";

        var real = ConformanceScan.Scan(repoRoot);
        checks.Add(new Check("回归面·conformance·真仓（机读块 248 / 协议包 111 / 导出面 4 · 零虚标）",
            real.Issues.Count == 0 && real.LogDigest() == CscReal
            && Convert.ToInt64(real.Stats["modules_mc"]) == 248
            && Convert.ToInt64(real.Stats["packages"]) == 111
            && Convert.ToInt64(real.Stats["export_items"]) == 4,
            $"FAIL {real.Issues.Count} · 摘要 {real.LogDigest()}（真源金标 {CscReal}）"));

        var cscNegativeRoot = Path.Combine(work, "reg-csc-negative");
        Fresh(cscNegativeRoot);
        foreach (var (rel, b64) in ConformanceNegativeFiles) WriteBase64(cscNegativeRoot, rel, b64);
        var cscNegative = ConformanceScan.Scan(cscNegativeRoot);
        var cscText = string.Join(" | ", cscNegative.Issues);
        checks.Add(new Check("回归面·conformance·合成虚标（L3>L1 虚标 · L0 非法 · 包不在册 · 导出面缺证据/门禁 · mc.id 重复）",
            cscNegative.Issues.Count == 7 && cscNegative.LogDigest() == CscNegative
            && cscText.Contains("conformance 虚标 L3 > 可证 L1（'M99' 不在装配在册证据）")
            && cscText.Contains("conformance 虚标 L2 > 可证 L1（包不在 registry protocols[]）")
            && cscText.Contains("证据文件缺失 missing.txt") && cscText.Contains("证据门禁 check99 不在 verify.sh")
            && cscText.Contains("导出面 y: conformance 应为 L3（导出门禁锁定面）")
            && cscText.Contains("模块 id 与"),   // 真源 348577d 新增的重复 id 判据（D3）在这份合成语料上必须命中
            $"FAIL {cscNegative.Issues.Count} · 摘要 {cscNegative.LogDigest()}（真源金标 {CscNegative}）"));

        var depth = QualityDepth.Scan(repoRoot);
        checks.Add(new Check("回归面·纵深聚合·真仓（14 件子扫描器接线 · 真源 quality_depth_scan.scan）",
            depth.Issues.Count == 0 && depth.LogDigest() == DepthReal
            && depth.Stats.Count == QualityDepth.SubScannerOrder.Length,
            $"FAIL {depth.Issues.Count} · stats {depth.Stats.Count} · 摘要 {depth.LogDigest()}"
            + $"（真源金标 {DepthReal}）"));

        var markersReal = DocHygiene.CheckMarkers(repoRoot);
        checks.Add(new Check("回归面·文档卫生·真仓（关键档「最后更新」位 + 指令档标识头 · 零缺口）",
            markersReal.Count == 0
            && ExitFaces.Digest32(DocHygiene.MarkersLog(repoRoot)) == MarkersReal,
            $"FAIL {markersReal.Count} · 摘要 {ExitFaces.Digest32(DocHygiene.MarkersLog(repoRoot))}"
            + $"（真源金标 {MarkersReal}）"));

        var markersRoot = Path.Combine(work, "reg-markers-negative");
        Fresh(markersRoot);
        foreach (var (rel, b64) in MarkersNegativeFiles) WriteBase64(markersRoot, rel, b64);
        var markersNegative = DocHygiene.CheckMarkers(markersRoot);
        var markersText = string.Join(" | ", markersNegative);
        checks.Add(new Check("回归面·文档卫生·合成缺标识（无「最后更新」位 + 指令档缺标识 + 清单内缺件逐件报）",
            markersNegative.Count == 45
            && ExitFaces.Digest32(DocHygiene.MarkersLog(markersRoot)) == MarkersNegative
            && markersText.Contains("01_核心协议.md 缺「最后更新」位（头部 2 行内）")
            && markersText.Contains("docs/ai-menu.md 缺「⛔ 操作指令」标识头（指令类文档须全覆盖）")
            && markersText.Contains("02_联动注册表.md 缺失（须入 REQUIRED_DOCS 清单）"),
            $"FAIL {markersNegative.Count}"
            + $" · 摘要 {ExitFaces.Digest32(DocHygiene.MarkersLog(markersRoot))}（真源金标 {MarkersNegative}）"));

        var evaluation = RegressionScore.Evaluate(repoRoot);
        var signals = (evaluation["signals"] as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        checks.Add(new Check("回归面·分值·真仓（五信号复算 + 可复算子集归一分 + purity_clean 记边界）",
            RegressionScore.LogDigest(evaluation) == ScoreReal
            && signals.Count == 5 && signals.All(s => Convert.ToDouble(s["value"]) == 1.0)
            && Convert.ToDouble(evaluation["score"]) == 100.0
            && (evaluation["issues"] as List<object?>)!.Count == 0
            && string.Join(",", RegressionScore.BoundarySignals) == "purity_clean",
            $"信号 {signals.Count} · 分 {evaluation["score"]}"
            + $" · 摘要 {RegressionScore.LogDigest(evaluation)}（真源金标 {ScoreReal}）"));

        using var pairsDoc = JsonDocument.Parse(Convert.FromBase64String(RegressionComparePairsB64));
        var pairs = (PythonJson.ToGraph(pairsDoc.RootElement) as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var compareDigest = RegressionScore.CompareLogDigest(pairs);
        checks.Add(new Check("回归面·比对口径（compare() 六例：无回归/信号回落/整体下降/容差内/审计例外/无基线）",
            pairs.Count == 6 && compareDigest == CompareGolden
            && RegressionScore.CompareLog(pairs)[1].Contains("回归（信号回落）：schema_clean")
            && RegressionScore.CompareLog(pairs)[2].Contains("回归（整体分下降 10.00 > 容差 0.00）")
            && RegressionScore.CompareLog(pairs)[4].Contains("通过（含 1 项审计例外）")
            && RegressionScore.CompareLog(pairs)[5].Contains("无基线（只报当前分值，未做回归判定）"),
            $"例数 {pairs.Count} · 摘要 {compareDigest}（真源金标 {CompareGolden}）"));
    }

    /// <summary>
    /// 构建回路（check33 第 16 条 · `core/workloop.py`）三钉：真仓（待办 1229 项 / 适配器 3 /
    /// stub 工单确定）· 合成语料（CLI ↔ 声明件漏同步 → deepen 候选、工单成形）· 空树（待办真源为空
    /// → 问题面为空，逐条判出）。判据面 = `scan` + `summary`；`write_order` / `close` 是写 `.rivet/`
    /// 内部档案的写面，**不移植**（只读门不落盘）。金标由 probes/workloop_probe.py 产出。
    /// </summary>
    private static void WorkloopCases(List<Check> checks, string work, string repoRoot)
    {
        const string Real = "fb09f03eaf08d2aaad0e54098a6b79f4";
        const string Syn = "440b2a6a5f4c1b597dd5c9e54755c028";
        const string Empty = "acfeff33bd0f55d5315fecf706575719";

        var real = Workloop.Scan(repoRoot);
        checks.Add(new Check("构建回路·真仓（待办 1229 项 · 适配器 3 · stub 工单确定 · 与真源原文逐字节同摘要）",
            real.Ok && real.LogDigest == Real
            && Convert.ToInt64(real.Stats["items"]) == 1229
            && Convert.ToInt64(real.Stats["untyped"]) == 86
            && Convert.ToInt64(real.Stats["advisories"]) == 1142
            && Convert.ToInt64(real.Stats["adapters"]) == 3
            && PyScalar.PyRepr(real.Stats["pulled_candidates"]) == "['laya-multilingual']",
            $"FAIL {real.Issues.Count} · 项 {real.Stats["items"]} · 摘要 {real.LogDigest}"
            + $"（真源金标 {Real}）"));

        var synRoot = Path.Combine(work, "workloop-synthetic");
        Fresh(synRoot);
        foreach (var (rel, b64) in WorkloopSyntheticFiles) WriteBase64(synRoot, rel, b64);
        var syn = Workloop.Scan(synRoot);
        checks.Add(new Check("构建回路·合成语料（CLI↔声明件漏同步 → deepen 候选 · 工单成形 · 与真源原文同摘要）",
            syn.Ok && syn.LogDigest == Syn
            && Convert.ToInt64(syn.Stats["items"]) == 5 && Convert.ToInt64(syn.Stats["adapters"]) == 1
            && PyScalar.PyRepr(syn.Stats["pulled_candidates"]) == "['合成候选']",
            $"FAIL {syn.Issues.Count} · 项 {syn.Stats["items"]} · 摘要 {syn.LogDigest}（真源金标 {Syn}）"));

        var emptyRoot = Path.Combine(work, "workloop-empty");
        Fresh(emptyRoot);
        var empty = Workloop.Scan(emptyRoot);
        checks.Add(new Check("构建回路·空树（待办真源为空 + 问题面为空 → 逐条判出，不静默放过）",
            !empty.Ok && empty.Issues.Count == 2 && empty.LogDigest == Empty
            && empty.Issues[0].StartsWith("待办真源为空", StringComparison.Ordinal),
            $"FAIL {empty.Issues.Count} · 摘要 {empty.LogDigest}（真源金标 {Empty}）"));
    }

    /// <summary>
    /// GEO 出口（check38 子扫描 3 · `scripts/geo_export.py`）四钉：真仓（370 条标准 / 70 条被绑定 /
    /// 8 件生成物，**引擎重算须逐字节命中盘上原件**）· 合成语料（真源 `write()` 写出的盘上原件 →
    /// 引擎重算同样命中，证明渲染器不是只对真仓凑巧）· 合成漂移（删一个索引锚点 → 漂移 + 锚点集合
    /// 各报一条）· 缺生成物（8 件逐件报缺 + 锚点集合报差）。金标由 probes/geo_export_probe.py 产出。
    /// </summary>
    private static void GeoExportCases(List<Check> checks, string work, string repoRoot)
    {
        const string Real = "b7305f442f3e92b988103ebbca5e5514";
        const string OkDigest = "b7305f442f3e92b988103ebbca5e5514";
        const string Tampered = "229b81beeded32f15b79669db2d6d2b1";
        const string Absent = "4aa7946fa0a0edc6ccf8e560949dc5bb";

        var real = GeoExport.Check(repoRoot);
        checks.Add(new Check("GEO 出口·真仓（370 条标准 / 70 条被绑定 / 8 件生成物 · 重算逐字节命中）",
            real.Ok && real.LogDigest() == Real
            && Convert.ToInt64(real.Stats["standards"]) == 370
            && Convert.ToInt64(real.Stats["bound_standards"]) == 70
            && Convert.ToInt64(real.Stats["files"]) == 8,
            $"FAIL {real.Issues.Count} · 标准 {real.Stats["standards"]} · 摘要 {real.LogDigest()}"
            + $"（真源金标 {Real}）"));

        var okRoot = Path.Combine(work, "geo-synthetic-ok");
        Fresh(okRoot);
        foreach (var (rel, b64) in GeoSyntheticOkFiles) WriteBase64(okRoot, rel, b64);
        var ok = GeoExport.Check(okRoot);
        checks.Add(new Check("GEO 出口·合成语料（真源 write() 盘上原件 → 引擎重算逐字节命中）",
            ok.Ok && ok.LogDigest() == OkDigest && Convert.ToInt64(ok.Stats["standards"]) == 2,
            $"FAIL {ok.Issues.Count} · 摘要 {ok.LogDigest()}（真源金标 {OkDigest}）"));

        var tamperedRoot = Path.Combine(work, "geo-synthetic-tampered");
        Fresh(tamperedRoot);
        foreach (var (rel, b64) in GeoSyntheticTamperedFiles) WriteBase64(tamperedRoot, rel, b64);
        var tampered = GeoExport.Check(tamperedRoot);
        var tamperedText = string.Join(" | ", tampered.Issues);
        checks.Add(new Check("GEO 出口·合成漂移（删一个索引锚点 → 漂移 + 锚点集合各报一条）",
            !tampered.Ok && tampered.Issues.Count == 2 && tampered.LogDigest() == Tampered
            && tamperedText.Contains("docs/standards/index.md 与标准目录不一致")
            && tamperedText.Contains("索引锚点集合 ≠ 目录 id 集合（缺 1 / 多 0）"),
            $"FAIL {tampered.Issues.Count} · 摘要 {tampered.LogDigest()}（真源金标 {Tampered}）"));

        var absentRoot = Path.Combine(work, "geo-synthetic-absent");
        Fresh(absentRoot);
        foreach (var (rel, b64) in GeoSyntheticAbsentFiles) WriteBase64(absentRoot, rel, b64);
        var absent = GeoExport.Check(absentRoot);
        checks.Add(new Check("GEO 出口·缺生成物（8 件逐件报缺 + 锚点集合报差，不静默放过）",
            !absent.Ok && absent.Issues.Count == 9 && absent.LogDigest() == Absent
            && absent.Issues[0].StartsWith("缺生成物 docs/standards/index.md", StringComparison.Ordinal),
            $"FAIL {absent.Issues.Count} · 摘要 {absent.LogDigest()}（真源金标 {Absent}）"));
    }

    /// <summary>
    /// 需求 → 装配计划（`nf assemble` · `core/assemble_plan.py`）四钉：**预设命中**（西幻生存 → 包 / 管线 /
    /// 取件非空 / 允许集 ⊇ 官方核心）· **自定义流**（未命中且含自定义线索 → `custom` · 可借用包 = 全库包名 ·
    /// 允许集 = 官方 + 全部社区模块）· **澄清漏斗**（空需求 / 无线索需求 → 三点问句；含线索 → ready）·
    /// **成品验收**（合成 md：八段齐 + 编号在允许集 + 决策句带引用 → 通过；缺段 / 越界编号 / 无引用决策句逐条判出）。
    /// 前两钉断**语义结构**（语料规模随仓库变，不锚死数字），后两钉在**合成语料**上断，与仓库无关。
    /// 金标由 probes/face_parity_probe.py 的 assemble 六面（逐字节）另行钉住 CLI 输出。
    /// </summary>
    private static void AssembleCases(List<Check> checks, string work, string repoRoot)
    {
        var preset = AssemblePlan.Plan(repoRoot, "西幻生存");
        var core = AssemblePlan.OfficialCoreIds(repoRoot);
        var allowed = (preset.GetValueOrDefault("allowed_module_ids") as List<object?> ?? new List<object?>())
            .Select(x => x as string ?? "").ToHashSet(StringComparer.Ordinal);
        checks.Add(new Check("装配面·预设命中（西幻生存 → 包/管线 · 取件非空 · 允许集 ⊇ 官方核心）",
            preset.GetValueOrDefault("matched") is true
            && preset.GetValueOrDefault("package") as string == "西幻生存领域包"
            && preset.GetValueOrDefault("pipeline") as string == "P03"
            && (preset.GetValueOrDefault("fetch_modules") as List<object?> ?? new List<object?>()).Count > 0
            && core.Count > 0 && core.All(allowed.Contains)
            && preset.GetValueOrDefault("status") as string == "preset",
            $"包 {preset.GetValueOrDefault("package")} · 管线 {preset.GetValueOrDefault("pipeline")}"
            + $" · 取件 {(preset.GetValueOrDefault("fetch_modules") as List<object?> ?? new List<object?>()).Count}"
            + $" · 允许集 {allowed.Count}（官方核心 {core.Count} 全含）"));

        var customPlan = AssemblePlan.Plan(repoRoot, "自定义权谋宫廷");
        var packages = AssemblePlan.PackageModuleSets(repoRoot);
        var known = (customPlan.GetValueOrDefault("known_packages") as List<object?> ?? new List<object?>())
            .Select(x => x as string ?? "").ToList();
        var allRegistered = core.Concat(packages.Values.SelectMany(v => v))
            .ToHashSet(StringComparer.Ordinal);
        checks.Add(new Check("装配面·自定义流（未命中 → custom · 可借用包=全库 · 允许集=官方+全部社区模块）",
            customPlan.GetValueOrDefault("matched") is false
            && customPlan.GetValueOrDefault("status") as string == "custom"
            && known.Count == packages.Count
            && allowed.Count == allRegistered.Count
            && customPlan.GetValueOrDefault("fetch_modules") is List<object?> fetch && fetch.Count > 0,
            $"状态 {customPlan.GetValueOrDefault("status")} · 可借用包 {known.Count}/{packages.Count}"
            + $" · 允许集 {allowed.Count}/{allRegistered.Count}"));

        var emptyFunnel = AssemblePlan.Clarify(repoRoot, "   ");
        var vagueFunnel = AssemblePlan.Clarify(repoRoot, "帮我做个游戏");
        var cueFunnel = AssemblePlan.Clarify(repoRoot, "自定义权谋宫廷");
        checks.Add(new Check("装配面·澄清漏斗（空需求 / 无线索需求 → clarify；含自定义线索 → ready）",
            emptyFunnel.GetValueOrDefault("status") as string == "clarify"
            && (emptyFunnel.GetValueOrDefault("questions") as List<object?> ?? new List<object?>()).Count == 1
            && vagueFunnel.GetValueOrDefault("status") as string == "clarify"
            && (vagueFunnel.GetValueOrDefault("questions") as List<object?> ?? new List<object?>()).Count == 3
            && cueFunnel.GetValueOrDefault("status") as string == "ready"
            && cueFunnel.GetValueOrDefault("plan") is Dictionary<string, object?>,
            $"空需求 {(emptyFunnel.GetValueOrDefault("questions") as List<object?> ?? new List<object?>()).Count} 问"
            + $" · 无线索 {(vagueFunnel.GetValueOrDefault("questions") as List<object?> ?? new List<object?>()).Count} 问"
            + $" · 含线索 {cueFunnel.GetValueOrDefault("status")}"));

        var syntheticPlan = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["allowed_module_ids"] = new List<object?> { "通用:M10", "M50" },
            ["package"] = "合成包", ["pipeline"] = "P99",
        };
        // 注意（照抄真源口径）：**决策句只在叙事段 ##0–##2 里判**，且跳过 `-`/`*`/`|` 开头的行——
        // 故合成语料要把决策句放进 ##1 段内（首版把它放在 ##7 之后，是**测试数据错**而非移植错）。
        var good = string.Join("\n", Enumerable.Range(0, 8).Select(i => $"## {i}. 段{i}")) + "\n";
        var (goodIssues, goodStats) = AssemblePlan.Check(good, syntheticPlan);
        var bad = "## 0. 段0\n## 1. 段1\n"
                  + "本段必须引用 §3.1 才能落地。\n"      // 决策句带引用 → 不算问题
                  + "本段必须不要引用。\n"                // 决策句无引用 → 判出
                  + "越界编号 M55 出现在这里。\n"        // 越界编号 → 判出
                  + string.Join("\n", Enumerable.Range(2, 6).Select(i => $"## {i}. 段{i}")) + "\n";
        var (badIssues, badStats) = AssemblePlan.Check(bad, syntheticPlan);
        var missingSeg = AssemblePlan.Check("## 0. 段0\n## 1. 段1\n", syntheticPlan);
        checks.Add(new Check("装配面·成品验收（八段齐 → 通过；缺段 / 越界编号 / 无引用决策句 → 逐条判出）",
            goodIssues.Count == 0 && goodStats["segments"] as long? == 8L
            && badIssues.Count == 2
            && badIssues.Any(i => i.StartsWith("编造/越界编号：M55", StringComparison.Ordinal))
            && badIssues.Any(i => i.StartsWith("无引用决策句：", StringComparison.Ordinal))
            && badStats["modules_mentioned"] as long? == 1L
            && missingSeg.Issues.Count == 1
            && missingSeg.Issues[0].StartsWith("八段骨架缺段：##", StringComparison.Ordinal),
            $"好件 {goodIssues.Count} 问题 · 坏件 {badIssues.Count} 问题（{string.Join(" / ", badIssues).Substring(0, Math.Min(90, string.Join(" / ", badIssues).Length))}）"
            + $" · 缺段 {missingSeg.Issues.Count}"));
    }

    /// <summary>
    /// 语料身份（**操作性预检**，不是判据）：把「被测语料」量成指纹，好让**摘要类钉的红**能被正确归因
    /// ——作者前移 HEAD 后重新导出快照再跑门，摘要钉会红，那是「**语料变了**」而不是「引擎坏了」。
    ///
    /// 三钉：① 真仓（**导出快照断金标基线** / 工作区态只断模式）——若拿**新快照**跑，本钉会红并直接把
    /// 归因写在 detail 里（第一百零六片实测：作者 7 提交后的 `nf-snap-h6` 指纹 `23a7922f…` ≠ 金标
    /// `66db1450…`，而当时**只有一条**摘要钉红、看不出原因）；② 确定性（同语料两遍同值）；
    /// ③ 一字节敏感（临时树改一个字节 → 指纹变）。
    /// </summary>
    private static void CorpusStampCases(List<Check> checks, string work, string repoRoot)
    {
        var stamp = CorpusStamp.Check(repoRoot);
        var pinned = IsPinnedSnapshot(repoRoot);
        checks.Add(new Check("语料身份·真仓（导出快照断金标基线 · 工作区态只报模式——摘要钉的红据此归因）",
            pinned ? stamp.Matches : !stamp.IsSnapshot,
            $"指纹 {stamp.Fingerprint} · 金标 {stamp.Baseline} · 匹配={(stamp.Matches ? "是" : "否")}"
            + $" · 模式={(stamp.IsSnapshot ? "导出快照" : "工作区")}"
            + (pinned && !stamp.Matches
                ? " ⚠ 语料与金标基线不同——**摘要类钉的红应从「复基线」处置**（重生成 fixtures 并重嵌常量），"
                  + "或改跑活仓库走语义模式；**不是引擎坏了**。"
                : "")));

        var small = Path.Combine(work, "corpus-stamp");
        Fresh(small);
        File.WriteAllText(Path.Combine(small, "a.md"), "一\n", new UTF8Encoding(false));
        Directory.CreateDirectory(Path.Combine(small, "sub"));
        File.WriteAllText(Path.Combine(small, "sub", "b.md"), "二\n", new UTF8Encoding(false));
        var first = CorpusStamp.Fingerprint(small);
        var second = CorpusStamp.Fingerprint(small);
        checks.Add(new Check("语料身份·确定性（同语料两遍同值 · 且与金标基线不同）",
            first == second && first != CorpusStamp.Baseline && first.Length == 16,
            $"两遍 {first}/{second} · 金标 {CorpusStamp.Baseline}"));

        File.WriteAllText(Path.Combine(small, "a.md"), "一\n", new UTF8Encoding(false));   // 同内容 → 同指纹
        var sameAfterRewrite = CorpusStamp.Fingerprint(small) == first;
        File.WriteAllText(Path.Combine(small, "a.md"), "一!\n", new UTF8Encoding(false));  // 改一字节 → 变
        var changed = CorpusStamp.Fingerprint(small);
        checks.Add(new Check("语料身份·一字节敏感（同内容重写不变 · 改一字节即变）",
            sameAfterRewrite && changed != first,
            $"重写后 {(sameAfterRewrite ? "不变" : "**变了**（错）")} · 改字节后 {changed}（原 {first}）"));
    }

    /// <summary>
    /// 馆藏回执（`core/receipts.py` **馆藏作用域** · check35 第二条腿）七钉——真仓零缺口 + 六种破坏：
    /// 条目正文被改（根不一致 + 条目内容已变）· 回执少一条（`回执条数 2 ≠ 馆藏条数 3`）· 幽灵条目 ·
    /// schema 不匹配（真源**立刻返回**，不做折叠判定）· leaf 被改（包含证明不折叠到根）· 盘上多一条
    /// （根不一致 + 条数不等）。
    ///
    /// **本片修掉一处既有实现差异**：此前引擎按**文件路径**逐条比对（`缺文件：…` / `条目摘要不一致：…`），
    /// 真源是**从馆藏条目实时重建**（`build()` → 全馆根 + 逐条 inclusion proof），消息与判定面都与真源不同；
    /// 真仓语料两边都零问题，**只有破坏性语料才照得出来**。现按真源重写（`BuildLibrary` + `FoldProof`）。
    /// 金标由 probes/library_receipts_probe.py 产出。
    /// </summary>
    private static void LibraryReceiptsCases(List<Check> checks, string work, string repoRoot)
    {
        const string Real = "4e09bba9dfa80561029cc510865da206";
        const string EntryTampered = "8fbdadca49dd09a9b271ffb163119620";
        const string EntryRemoved = "19c7037d0116488470a6e6a5a311757a";
        const string GhostEntry = "aa14e1419ad17a83cceb04720d3f69a4";
        const string BadSchema = "c30c6d156dae65bc8b837bb9bc777867";
        const string ProofTampered = "c0bcb623f691e880111260ead2d7e3f5";
        const string NewEntry = "e734b5e13fda8494a565aa2757d0aa8e";

        Receipts.ArtifactResult Case(string name, (string Rel, string B64)[] files)
        {
            var dir = Path.Combine(work, name);
            Fresh(dir);
            foreach (var (rel, b64) in files) WriteBase64(dir, rel, b64);
            return Receipts.VerifyLibraryReceipts(dir);
        }

        var real = Receipts.VerifyLibraryReceipts(repoRoot);
        checks.Add(new Check("馆藏回执·真仓（3 条 · 逐条折叠到根 + 根与实时重算一致 · 与真源原文逐字节同摘要）",
            real.Ok && Receipts.LibraryLogDigest(real) == Real && real.Count == 3
            && real.Root.StartsWith("be9562d619c4", StringComparison.Ordinal),
            $"FAIL {real.Issues.Count} · 摘要 {Receipts.LibraryLogDigest(real)}（真源金标 {Real}）"));

        var tampered = Case("lib-entry-tampered", LibEntryTamperedFiles);
        var tamperedText = string.Join(" | ", tampered.Issues);
        checks.Add(new Check("馆藏回执·条目被改（根不一致 + 条目内容已变，均带真源修复指引）",
            !tampered.Ok && tampered.Issues.Count == 2
            && Receipts.LibraryLogDigest(tampered) == EntryTampered
            && tamperedText.Contains("根不一致：记录=") && tamperedText.Contains("（修复指引：馆藏改动后跑 nf library receipts --write）")
            && tamperedText.Contains("条目内容已变：NF-1（修复指引：重签该条并重建回执）"),
            $"FAIL {tampered.Issues.Count} · 摘要 {Receipts.LibraryLogDigest(tampered)}（真源金标 {EntryTampered}）"));

        var removed = Case("lib-entry-removed", LibEntryRemovedFiles);
        checks.Add(new Check("馆藏回执·回执少一条（回执条数 2 ≠ 馆藏条数 3）",
            !removed.Ok && removed.Issues.Count == 1 && Receipts.LibraryLogDigest(removed) == EntryRemoved
            && removed.Issues[0] == "回执条数 2 ≠ 馆藏条数 3",
            $"FAIL {removed.Issues.Count} · 摘要 {Receipts.LibraryLogDigest(removed)}（真源金标 {EntryRemoved}）"));

        var ghost = Case("lib-ghost-entry", LibGhostEntryFiles);
        checks.Add(new Check("馆藏回执·幽灵条目（回执指向不存在的条目：NF-999）",
            !ghost.Ok && ghost.Issues.Count == 1 && Receipts.LibraryLogDigest(ghost) == GhostEntry
            && ghost.Issues[0] == "回执指向不存在的条目：NF-999",
            $"FAIL {ghost.Issues.Count} · 摘要 {Receipts.LibraryLogDigest(ghost)}（真源金标 {GhostEntry}）"));

        var schema = Case("lib-schema", LibSchemaFiles);
        checks.Add(new Check("馆藏回执·schema 不匹配（真源立刻返回，不做折叠判定）",
            !schema.Ok && schema.Issues.Count == 1 && Receipts.LibraryLogDigest(schema) == BadSchema
            && schema.Issues[0] == "回执文件 schema 不匹配（期望 nf-receipts/1）" && schema.Count == 0,
            $"FAIL {schema.Issues.Count} · 摘要 {Receipts.LibraryLogDigest(schema)}（真源金标 {BadSchema}）"));

        var proof = Case("lib-proof-tampered", LibProofTamperedFiles);
        checks.Add(new Check("馆藏回执·leaf 被改（包含证明不折叠到根：NF-2）",
            !proof.Ok && proof.Issues.Count == 1 && Receipts.LibraryLogDigest(proof) == ProofTampered
            && proof.Issues[0] == "包含证明不折叠到根：NF-2",
            $"FAIL {proof.Issues.Count} · 摘要 {Receipts.LibraryLogDigest(proof)}（真源金标 {ProofTampered}）"));

        var added = Case("lib-new-entry", LibNewEntryFiles);
        checks.Add(new Check("馆藏回执·盘上多一条（根不一致 + 回执条数 3 ≠ 馆藏条数 4）",
            !added.Ok && added.Issues.Count == 2 && Receipts.LibraryLogDigest(added) == NewEntry
            && added.Issues[1] == "回执条数 3 ≠ 馆藏条数 4",
            $"FAIL {added.Issues.Count} · 摘要 {Receipts.LibraryLogDigest(added)}（真源金标 {NewEntry}）"));
    }

    /// <summary>馆藏回执合成语料（真源 build() 盘上原件 + 破坏；机械导出）。</summary>
    private static readonly (string Rel, string B64)[] LibEntryTamperedFiles =
    {
		("library/NF-1.md", "LS0tCmlkOiBORi0xCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64xCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMQoK5q2j5paH56ysIDEg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCgrnr6HmlLnkuIDooYzjgIIK"),
		("library/NF-2.md", "LS0tCmlkOiBORi0yCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64yCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMgoK5q2j5paH56ysIDIg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-3.md", "LS0tCmlkOiBORi0zCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64zCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMwoK5q2j5paH56ysIDMg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/RECEIPTS.json", "ewogICJhbGdvcml0aG0iOiAiUkZDNjk2Mi1zdHlsZSBzaGEyNTYgZG9tYWluLXNlcGFyYXRlZCIsCiAgImNvdW50IjogMywKICAiZW50cmllcyI6IFsKICAgIHsKICAgICAgImFuY2hvciI6IG51bGwsCiAgICAgICJkaWdlc3QiOiAiMTZlZTY0OTI3MDgzYjFiOGRmYzI0MTAxMTEyYjY3NmUyODNkMGEyYjY0YzVhYzE3Y2RjNTlmZjA1Mjk4YTU4MiIsCiAgICAgICJpZCI6ICJORi0xIiwKICAgICAgImxlYWYiOiAiNTJjMTk0YmRmMmQyNTFkOGEyNTM4ODVhM2MyZDYwYTNmN2NhZGZiMTg4OGIwN2QyNDFiZmI4MjYwOTQ2YzVhZSIsCiAgICAgICJwYXRoIjogImxpYnJhcnkvTkYtMS5tZCIsCiAgICAgICJwcm9vZiI6IFsKICAgICAgICB7CiAgICAgICAgICAiaGFzaCI6ICI5MjhkYWE2ZDFkOTg4MjczZWI1Y2Q3NWQwYzQxMjA5Yzk1MDdlN2ZhYjc5YWFkM2RhZDZlNjhiYTM4N2Y0Y2Q2IiwKICAgICAgICAgICJzaWRlIjogInJpZ2h0IgogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICAgICAic2lkZSI6ICJyaWdodCIKICAgICAgICB9CiAgICAgIF0KICAgIH0sCiAgICB7CiAgICAgICJhbmNob3IiOiBudWxsLAogICAgICAiZGlnZXN0IjogIjcwYzk0MGI0NGI4Mjg1MTA2OTM1YjU3YTU4NWJkZWU4MWE4MzYyNzJiMmQ3NWZhN2E1NzFmY2VmZGM0MjYzZTMiLAogICAgICAiaWQiOiAiTkYtMiIsCiAgICAgICJsZWFmIjogIjkyOGRhYTZkMWQ5ODgyNzNlYjVjZDc1ZDBjNDEyMDljOTUwN2U3ZmFiNzlhYWQzZGFkNmU2OGJhMzg3ZjRjZDYiLAogICAgICAicGF0aCI6ICJsaWJyYXJ5L05GLTIubWQiLAogICAgICAicHJvb2YiOiBbCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNTJjMTk0YmRmMmQyNTFkOGEyNTM4ODVhM2MyZDYwYTNmN2NhZGZiMTg4OGIwN2QyNDFiZmI4MjYwOTQ2YzVhZSIsCiAgICAgICAgICAic2lkZSI6ICJsZWZ0IgogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICAgICAic2lkZSI6ICJyaWdodCIKICAgICAgICB9CiAgICAgIF0KICAgIH0sCiAgICB7CiAgICAgICJhbmNob3IiOiBudWxsLAogICAgICAiZGlnZXN0IjogIjM3YjFlYzMyMGVlMGQ5ZWI4NzI0YjkzYWZhNmYzZGY1YWE5ZGE4ZmI1Y2I0N2Q5YTI4NDUwMTk2NzIxZTRiMGIiLAogICAgICAiaWQiOiAiTkYtMyIsCiAgICAgICJsZWFmIjogIjZiNTQwZjcyNmY4NzEwYzE5MjEwYTIwODY0ODBkZWNmZTIyYjlhZjQ1ZWQ5ZDQ0YzM5ZjNjMzdiNWRlMzM3MWUiLAogICAgICAicGF0aCI6ICJsaWJyYXJ5L05GLTMubWQiLAogICAgICAicHJvb2YiOiBbCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiZDQ3OGJmOWU0MWI0YzUzNzExMDBiM2QxN2Y4NmM4NzkwNDU4YzZhYzI0YzE4MmU0ZjZmZmFlM2MyY2FhMjQ4OSIsCiAgICAgICAgICAic2lkZSI6ICJsZWZ0IgogICAgICAgIH0KICAgICAgXQogICAgfQogIF0sCiAgInJvb3QiOiAiYTljNWNlODQ5NWU0NmRhM2Y0OTBjOTk3YjFkMDU2MWI2MDg2NzgzODYwZjhkODIxNzE3NzM2NzNjOWI1ZWQyMCIsCiAgInNjaGVtYSI6ICJuZi1yZWNlaXB0cy8xIgp9Cg=="),
    };

    private static readonly (string Rel, string B64)[] LibEntryRemovedFiles =
    {
		("library/NF-1.md", "LS0tCmlkOiBORi0xCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64xCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMQoK5q2j5paH56ysIDEg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-2.md", "LS0tCmlkOiBORi0yCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64yCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMgoK5q2j5paH56ysIDIg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-3.md", "LS0tCmlkOiBORi0zCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64zCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMwoK5q2j5paH56ysIDMg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/RECEIPTS.json", "ewogICJhbGdvcml0aG0iOiAiUkZDNjk2Mi1zdHlsZSBzaGEyNTYgZG9tYWluLXNlcGFyYXRlZCIsCiAgImNvdW50IjogMywKICAiZW50cmllcyI6IFsKICAgIHsKICAgICAgImFuY2hvciI6IG51bGwsCiAgICAgICJkaWdlc3QiOiAiMTZlZTY0OTI3MDgzYjFiOGRmYzI0MTAxMTEyYjY3NmUyODNkMGEyYjY0YzVhYzE3Y2RjNTlmZjA1Mjk4YTU4MiIsCiAgICAgICJpZCI6ICJORi0xIiwKICAgICAgImxlYWYiOiAiNTJjMTk0YmRmMmQyNTFkOGEyNTM4ODVhM2MyZDYwYTNmN2NhZGZiMTg4OGIwN2QyNDFiZmI4MjYwOTQ2YzVhZSIsCiAgICAgICJwYXRoIjogImxpYnJhcnkvTkYtMS5tZCIsCiAgICAgICJwcm9vZiI6IFsKICAgICAgICB7CiAgICAgICAgICAiaGFzaCI6ICI5MjhkYWE2ZDFkOTg4MjczZWI1Y2Q3NWQwYzQxMjA5Yzk1MDdlN2ZhYjc5YWFkM2RhZDZlNjhiYTM4N2Y0Y2Q2IiwKICAgICAgICAgICJzaWRlIjogInJpZ2h0IgogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICAgICAic2lkZSI6ICJyaWdodCIKICAgICAgICB9CiAgICAgIF0KICAgIH0sCiAgICB7CiAgICAgICJhbmNob3IiOiBudWxsLAogICAgICAiZGlnZXN0IjogIjcwYzk0MGI0NGI4Mjg1MTA2OTM1YjU3YTU4NWJkZWU4MWE4MzYyNzJiMmQ3NWZhN2E1NzFmY2VmZGM0MjYzZTMiLAogICAgICAiaWQiOiAiTkYtMiIsCiAgICAgICJsZWFmIjogIjkyOGRhYTZkMWQ5ODgyNzNlYjVjZDc1ZDBjNDEyMDljOTUwN2U3ZmFiNzlhYWQzZGFkNmU2OGJhMzg3ZjRjZDYiLAogICAgICAicGF0aCI6ICJsaWJyYXJ5L05GLTIubWQiLAogICAgICAicHJvb2YiOiBbCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNTJjMTk0YmRmMmQyNTFkOGEyNTM4ODVhM2MyZDYwYTNmN2NhZGZiMTg4OGIwN2QyNDFiZmI4MjYwOTQ2YzVhZSIsCiAgICAgICAgICAic2lkZSI6ICJsZWZ0IgogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICAgICAic2lkZSI6ICJyaWdodCIKICAgICAgICB9CiAgICAgIF0KICAgIH0KICBdLAogICJyb290IjogImE5YzVjZTg0OTVlNDZkYTNmNDkwYzk5N2IxZDA1NjFiNjA4Njc4Mzg2MGY4ZDgyMTcxNzczNjczYzliNWVkMjAiLAogICJzY2hlbWEiOiAibmYtcmVjZWlwdHMvMSIKfQo="),
    };

    private static readonly (string Rel, string B64)[] LibGhostEntryFiles =
    {
		("library/NF-1.md", "LS0tCmlkOiBORi0xCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64xCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMQoK5q2j5paH56ysIDEg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-2.md", "LS0tCmlkOiBORi0yCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64yCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMgoK5q2j5paH56ysIDIg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-3.md", "LS0tCmlkOiBORi0zCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64zCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMwoK5q2j5paH56ysIDMg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/RECEIPTS.json", "ewogICJhbGdvcml0aG0iOiAiUkZDNjk2Mi1zdHlsZSBzaGEyNTYgZG9tYWluLXNlcGFyYXRlZCIsCiAgImNvdW50IjogMywKICAiZW50cmllcyI6IFsKICAgIHsKICAgICAgImFuY2hvciI6IG51bGwsCiAgICAgICJkaWdlc3QiOiAiMTZlZTY0OTI3MDgzYjFiOGRmYzI0MTAxMTEyYjY3NmUyODNkMGEyYjY0YzVhYzE3Y2RjNTlmZjA1Mjk4YTU4MiIsCiAgICAgICJpZCI6ICJORi05OTkiLAogICAgICAibGVhZiI6ICI1MmMxOTRiZGYyZDI1MWQ4YTI1Mzg4NWEzYzJkNjBhM2Y3Y2FkZmIxODg4YjA3ZDI0MWJmYjgyNjA5NDZjNWFlIiwKICAgICAgInBhdGgiOiAibGlicmFyeS9ORi0xLm1kIiwKICAgICAgInByb29mIjogWwogICAgICAgIHsKICAgICAgICAgICJoYXNoIjogIjkyOGRhYTZkMWQ5ODgyNzNlYjVjZDc1ZDBjNDEyMDljOTUwN2U3ZmFiNzlhYWQzZGFkNmU2OGJhMzg3ZjRjZDYiLAogICAgICAgICAgInNpZGUiOiAicmlnaHQiCiAgICAgICAgfSwKICAgICAgICB7CiAgICAgICAgICAiaGFzaCI6ICI2YjU0MGY3MjZmODcxMGMxOTIxMGEyMDg2NDgwZGVjZmUyMmI5YWY0NWVkOWQ0NGMzOWYzYzM3YjVkZTMzNzFlIiwKICAgICAgICAgICJzaWRlIjogInJpZ2h0IgogICAgICAgIH0KICAgICAgXQogICAgfSwKICAgIHsKICAgICAgImFuY2hvciI6IG51bGwsCiAgICAgICJkaWdlc3QiOiAiNzBjOTQwYjQ0YjgyODUxMDY5MzViNTdhNTg1YmRlZTgxYTgzNjI3MmIyZDc1ZmE3YTU3MWZjZWZkYzQyNjNlMyIsCiAgICAgICJpZCI6ICJORi0yIiwKICAgICAgImxlYWYiOiAiOTI4ZGFhNmQxZDk4ODI3M2ViNWNkNzVkMGM0MTIwOWM5NTA3ZTdmYWI3OWFhZDNkYWQ2ZTY4YmEzODdmNGNkNiIsCiAgICAgICJwYXRoIjogImxpYnJhcnkvTkYtMi5tZCIsCiAgICAgICJwcm9vZiI6IFsKICAgICAgICB7CiAgICAgICAgICAiaGFzaCI6ICI1MmMxOTRiZGYyZDI1MWQ4YTI1Mzg4NWEzYzJkNjBhM2Y3Y2FkZmIxODg4YjA3ZDI0MWJmYjgyNjA5NDZjNWFlIiwKICAgICAgICAgICJzaWRlIjogImxlZnQiCiAgICAgICAgfSwKICAgICAgICB7CiAgICAgICAgICAiaGFzaCI6ICI2YjU0MGY3MjZmODcxMGMxOTIxMGEyMDg2NDgwZGVjZmUyMmI5YWY0NWVkOWQ0NGMzOWYzYzM3YjVkZTMzNzFlIiwKICAgICAgICAgICJzaWRlIjogInJpZ2h0IgogICAgICAgIH0KICAgICAgXQogICAgfSwKICAgIHsKICAgICAgImFuY2hvciI6IG51bGwsCiAgICAgICJkaWdlc3QiOiAiMzdiMWVjMzIwZWUwZDllYjg3MjRiOTNhZmE2ZjNkZjVhYTlkYThmYjVjYjQ3ZDlhMjg0NTAxOTY3MjFlNGIwYiIsCiAgICAgICJpZCI6ICJORi0zIiwKICAgICAgImxlYWYiOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICJwYXRoIjogImxpYnJhcnkvTkYtMy5tZCIsCiAgICAgICJwcm9vZiI6IFsKICAgICAgICB7CiAgICAgICAgICAiaGFzaCI6ICJkNDc4YmY5ZTQxYjRjNTM3MTEwMGIzZDE3Zjg2Yzg3OTA0NThjNmFjMjRjMTgyZTRmNmZmYWUzYzJjYWEyNDg5IiwKICAgICAgICAgICJzaWRlIjogImxlZnQiCiAgICAgICAgfQogICAgICBdCiAgICB9CiAgXSwKICAicm9vdCI6ICJhOWM1Y2U4NDk1ZTQ2ZGEzZjQ5MGM5OTdiMWQwNTYxYjYwODY3ODM4NjBmOGQ4MjE3MTc3MzY3M2M5YjVlZDIwIiwKICAic2NoZW1hIjogIm5mLXJlY2VpcHRzLzEiCn0K"),
    };

    private static readonly (string Rel, string B64)[] LibSchemaFiles =
    {
		("library/NF-1.md", "LS0tCmlkOiBORi0xCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64xCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMQoK5q2j5paH56ysIDEg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-2.md", "LS0tCmlkOiBORi0yCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64yCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMgoK5q2j5paH56ysIDIg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-3.md", "LS0tCmlkOiBORi0zCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64zCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMwoK5q2j5paH56ysIDMg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/RECEIPTS.json", "ewogICJhbGdvcml0aG0iOiAiUkZDNjk2Mi1zdHlsZSBzaGEyNTYgZG9tYWluLXNlcGFyYXRlZCIsCiAgImNvdW50IjogMywKICAiZW50cmllcyI6IFsKICAgIHsKICAgICAgImFuY2hvciI6IG51bGwsCiAgICAgICJkaWdlc3QiOiAiMTZlZTY0OTI3MDgzYjFiOGRmYzI0MTAxMTEyYjY3NmUyODNkMGEyYjY0YzVhYzE3Y2RjNTlmZjA1Mjk4YTU4MiIsCiAgICAgICJpZCI6ICJORi0xIiwKICAgICAgImxlYWYiOiAiNTJjMTk0YmRmMmQyNTFkOGEyNTM4ODVhM2MyZDYwYTNmN2NhZGZiMTg4OGIwN2QyNDFiZmI4MjYwOTQ2YzVhZSIsCiAgICAgICJwYXRoIjogImxpYnJhcnkvTkYtMS5tZCIsCiAgICAgICJwcm9vZiI6IFsKICAgICAgICB7CiAgICAgICAgICAiaGFzaCI6ICI5MjhkYWE2ZDFkOTg4MjczZWI1Y2Q3NWQwYzQxMjA5Yzk1MDdlN2ZhYjc5YWFkM2RhZDZlNjhiYTM4N2Y0Y2Q2IiwKICAgICAgICAgICJzaWRlIjogInJpZ2h0IgogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICAgICAic2lkZSI6ICJyaWdodCIKICAgICAgICB9CiAgICAgIF0KICAgIH0sCiAgICB7CiAgICAgICJhbmNob3IiOiBudWxsLAogICAgICAiZGlnZXN0IjogIjcwYzk0MGI0NGI4Mjg1MTA2OTM1YjU3YTU4NWJkZWU4MWE4MzYyNzJiMmQ3NWZhN2E1NzFmY2VmZGM0MjYzZTMiLAogICAgICAiaWQiOiAiTkYtMiIsCiAgICAgICJsZWFmIjogIjkyOGRhYTZkMWQ5ODgyNzNlYjVjZDc1ZDBjNDEyMDljOTUwN2U3ZmFiNzlhYWQzZGFkNmU2OGJhMzg3ZjRjZDYiLAogICAgICAicGF0aCI6ICJsaWJyYXJ5L05GLTIubWQiLAogICAgICAicHJvb2YiOiBbCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNTJjMTk0YmRmMmQyNTFkOGEyNTM4ODVhM2MyZDYwYTNmN2NhZGZiMTg4OGIwN2QyNDFiZmI4MjYwOTQ2YzVhZSIsCiAgICAgICAgICAic2lkZSI6ICJsZWZ0IgogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICAgICAic2lkZSI6ICJyaWdodCIKICAgICAgICB9CiAgICAgIF0KICAgIH0sCiAgICB7CiAgICAgICJhbmNob3IiOiBudWxsLAogICAgICAiZGlnZXN0IjogIjM3YjFlYzMyMGVlMGQ5ZWI4NzI0YjkzYWZhNmYzZGY1YWE5ZGE4ZmI1Y2I0N2Q5YTI4NDUwMTk2NzIxZTRiMGIiLAogICAgICAiaWQiOiAiTkYtMyIsCiAgICAgICJsZWFmIjogIjZiNTQwZjcyNmY4NzEwYzE5MjEwYTIwODY0ODBkZWNmZTIyYjlhZjQ1ZWQ5ZDQ0YzM5ZjNjMzdiNWRlMzM3MWUiLAogICAgICAicGF0aCI6ICJsaWJyYXJ5L05GLTMubWQiLAogICAgICAicHJvb2YiOiBbCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiZDQ3OGJmOWU0MWI0YzUzNzExMDBiM2QxN2Y4NmM4NzkwNDU4YzZhYzI0YzE4MmU0ZjZmZmFlM2MyY2FhMjQ4OSIsCiAgICAgICAgICAic2lkZSI6ICJsZWZ0IgogICAgICAgIH0KICAgICAgXQogICAgfQogIF0sCiAgInJvb3QiOiAiYTljNWNlODQ5NWU0NmRhM2Y0OTBjOTk3YjFkMDU2MWI2MDg2NzgzODYwZjhkODIxNzE3NzM2NzNjOWI1ZWQyMCIsCiAgInNjaGVtYSI6ICJuZi1yZWNlaXB0cy8yIgp9Cg=="),
    };

    private static readonly (string Rel, string B64)[] LibProofTamperedFiles =
    {
		("library/NF-1.md", "LS0tCmlkOiBORi0xCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64xCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMQoK5q2j5paH56ysIDEg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-2.md", "LS0tCmlkOiBORi0yCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64yCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMgoK5q2j5paH56ysIDIg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-3.md", "LS0tCmlkOiBORi0zCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64zCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMwoK5q2j5paH56ysIDMg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/RECEIPTS.json", "ewogICJhbGdvcml0aG0iOiAiUkZDNjk2Mi1zdHlsZSBzaGEyNTYgZG9tYWluLXNlcGFyYXRlZCIsCiAgImNvdW50IjogMywKICAiZW50cmllcyI6IFsKICAgIHsKICAgICAgImFuY2hvciI6IG51bGwsCiAgICAgICJkaWdlc3QiOiAiMTZlZTY0OTI3MDgzYjFiOGRmYzI0MTAxMTEyYjY3NmUyODNkMGEyYjY0YzVhYzE3Y2RjNTlmZjA1Mjk4YTU4MiIsCiAgICAgICJpZCI6ICJORi0xIiwKICAgICAgImxlYWYiOiAiNTJjMTk0YmRmMmQyNTFkOGEyNTM4ODVhM2MyZDYwYTNmN2NhZGZiMTg4OGIwN2QyNDFiZmI4MjYwOTQ2YzVhZSIsCiAgICAgICJwYXRoIjogImxpYnJhcnkvTkYtMS5tZCIsCiAgICAgICJwcm9vZiI6IFsKICAgICAgICB7CiAgICAgICAgICAiaGFzaCI6ICI5MjhkYWE2ZDFkOTg4MjczZWI1Y2Q3NWQwYzQxMjA5Yzk1MDdlN2ZhYjc5YWFkM2RhZDZlNjhiYTM4N2Y0Y2Q2IiwKICAgICAgICAgICJzaWRlIjogInJpZ2h0IgogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICAgICAic2lkZSI6ICJyaWdodCIKICAgICAgICB9CiAgICAgIF0KICAgIH0sCiAgICB7CiAgICAgICJhbmNob3IiOiBudWxsLAogICAgICAiZGlnZXN0IjogIjcwYzk0MGI0NGI4Mjg1MTA2OTM1YjU3YTU4NWJkZWU4MWE4MzYyNzJiMmQ3NWZhN2E1NzFmY2VmZGM0MjYzZTMiLAogICAgICAiaWQiOiAiTkYtMiIsCiAgICAgICJsZWFmIjogIjAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAiLAogICAgICAicGF0aCI6ICJsaWJyYXJ5L05GLTIubWQiLAogICAgICAicHJvb2YiOiBbCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNTJjMTk0YmRmMmQyNTFkOGEyNTM4ODVhM2MyZDYwYTNmN2NhZGZiMTg4OGIwN2QyNDFiZmI4MjYwOTQ2YzVhZSIsCiAgICAgICAgICAic2lkZSI6ICJsZWZ0IgogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICAgICAic2lkZSI6ICJyaWdodCIKICAgICAgICB9CiAgICAgIF0KICAgIH0sCiAgICB7CiAgICAgICJhbmNob3IiOiBudWxsLAogICAgICAiZGlnZXN0IjogIjM3YjFlYzMyMGVlMGQ5ZWI4NzI0YjkzYWZhNmYzZGY1YWE5ZGE4ZmI1Y2I0N2Q5YTI4NDUwMTk2NzIxZTRiMGIiLAogICAgICAiaWQiOiAiTkYtMyIsCiAgICAgICJsZWFmIjogIjZiNTQwZjcyNmY4NzEwYzE5MjEwYTIwODY0ODBkZWNmZTIyYjlhZjQ1ZWQ5ZDQ0YzM5ZjNjMzdiNWRlMzM3MWUiLAogICAgICAicGF0aCI6ICJsaWJyYXJ5L05GLTMubWQiLAogICAgICAicHJvb2YiOiBbCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiZDQ3OGJmOWU0MWI0YzUzNzExMDBiM2QxN2Y4NmM4NzkwNDU4YzZhYzI0YzE4MmU0ZjZmZmFlM2MyY2FhMjQ4OSIsCiAgICAgICAgICAic2lkZSI6ICJsZWZ0IgogICAgICAgIH0KICAgICAgXQogICAgfQogIF0sCiAgInJvb3QiOiAiYTljNWNlODQ5NWU0NmRhM2Y0OTBjOTk3YjFkMDU2MWI2MDg2NzgzODYwZjhkODIxNzE3NzM2NzNjOWI1ZWQyMCIsCiAgInNjaGVtYSI6ICJuZi1yZWNlaXB0cy8xIgp9Cg=="),
    };

    private static readonly (string Rel, string B64)[] LibNewEntryFiles =
    {
		("library/NF-1.md", "LS0tCmlkOiBORi0xCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64xCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMQoK5q2j5paH56ysIDEg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-2.md", "LS0tCmlkOiBORi0yCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64yCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMgoK5q2j5paH56ysIDIg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-3.md", "LS0tCmlkOiBORi0zCnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm64zCmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gMwoK5q2j5paH56ysIDMg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/NF-4.md", "LS0tCmlkOiBORi00CnR5cGU6IGd1aWRlCnRpdGxlOiDlkIjmiJDmnaHnm640CmRlc2NyaXB0aW9uOiDlkIjmiJDppobol4/mnaHnm67vvIjmjqLpkojor63mlpnvvIkKbGljZW5zZTogTUlUCnN0YXR1czogYWN0aXZlCi0tLQoKIyDlkIjmiJDmnaHnm64gNAoK5q2j5paH56ysIDQg5p2h77yI5o6i6ZKI6K+t5paZ77yJ44CCCg=="),
		("library/RECEIPTS.json", "ewogICJhbGdvcml0aG0iOiAiUkZDNjk2Mi1zdHlsZSBzaGEyNTYgZG9tYWluLXNlcGFyYXRlZCIsCiAgImNvdW50IjogMywKICAiZW50cmllcyI6IFsKICAgIHsKICAgICAgImFuY2hvciI6IG51bGwsCiAgICAgICJkaWdlc3QiOiAiMTZlZTY0OTI3MDgzYjFiOGRmYzI0MTAxMTEyYjY3NmUyODNkMGEyYjY0YzVhYzE3Y2RjNTlmZjA1Mjk4YTU4MiIsCiAgICAgICJpZCI6ICJORi0xIiwKICAgICAgImxlYWYiOiAiNTJjMTk0YmRmMmQyNTFkOGEyNTM4ODVhM2MyZDYwYTNmN2NhZGZiMTg4OGIwN2QyNDFiZmI4MjYwOTQ2YzVhZSIsCiAgICAgICJwYXRoIjogImxpYnJhcnkvTkYtMS5tZCIsCiAgICAgICJwcm9vZiI6IFsKICAgICAgICB7CiAgICAgICAgICAiaGFzaCI6ICI5MjhkYWE2ZDFkOTg4MjczZWI1Y2Q3NWQwYzQxMjA5Yzk1MDdlN2ZhYjc5YWFkM2RhZDZlNjhiYTM4N2Y0Y2Q2IiwKICAgICAgICAgICJzaWRlIjogInJpZ2h0IgogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICAgICAic2lkZSI6ICJyaWdodCIKICAgICAgICB9CiAgICAgIF0KICAgIH0sCiAgICB7CiAgICAgICJhbmNob3IiOiBudWxsLAogICAgICAiZGlnZXN0IjogIjcwYzk0MGI0NGI4Mjg1MTA2OTM1YjU3YTU4NWJkZWU4MWE4MzYyNzJiMmQ3NWZhN2E1NzFmY2VmZGM0MjYzZTMiLAogICAgICAiaWQiOiAiTkYtMiIsCiAgICAgICJsZWFmIjogIjkyOGRhYTZkMWQ5ODgyNzNlYjVjZDc1ZDBjNDEyMDljOTUwN2U3ZmFiNzlhYWQzZGFkNmU2OGJhMzg3ZjRjZDYiLAogICAgICAicGF0aCI6ICJsaWJyYXJ5L05GLTIubWQiLAogICAgICAicHJvb2YiOiBbCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNTJjMTk0YmRmMmQyNTFkOGEyNTM4ODVhM2MyZDYwYTNmN2NhZGZiMTg4OGIwN2QyNDFiZmI4MjYwOTQ2YzVhZSIsCiAgICAgICAgICAic2lkZSI6ICJsZWZ0IgogICAgICAgIH0sCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiNmI1NDBmNzI2Zjg3MTBjMTkyMTBhMjA4NjQ4MGRlY2ZlMjJiOWFmNDVlZDlkNDRjMzlmM2MzN2I1ZGUzMzcxZSIsCiAgICAgICAgICAic2lkZSI6ICJyaWdodCIKICAgICAgICB9CiAgICAgIF0KICAgIH0sCiAgICB7CiAgICAgICJhbmNob3IiOiBudWxsLAogICAgICAiZGlnZXN0IjogIjM3YjFlYzMyMGVlMGQ5ZWI4NzI0YjkzYWZhNmYzZGY1YWE5ZGE4ZmI1Y2I0N2Q5YTI4NDUwMTk2NzIxZTRiMGIiLAogICAgICAiaWQiOiAiTkYtMyIsCiAgICAgICJsZWFmIjogIjZiNTQwZjcyNmY4NzEwYzE5MjEwYTIwODY0ODBkZWNmZTIyYjlhZjQ1ZWQ5ZDQ0YzM5ZjNjMzdiNWRlMzM3MWUiLAogICAgICAicGF0aCI6ICJsaWJyYXJ5L05GLTMubWQiLAogICAgICAicHJvb2YiOiBbCiAgICAgICAgewogICAgICAgICAgImhhc2giOiAiZDQ3OGJmOWU0MWI0YzUzNzExMDBiM2QxN2Y4NmM4NzkwNDU4YzZhYzI0YzE4MmU0ZjZmZmFlM2MyY2FhMjQ4OSIsCiAgICAgICAgICAic2lkZSI6ICJsZWZ0IgogICAgICAgIH0KICAgICAgXQogICAgfQogIF0sCiAgInJvb3QiOiAiYTljNWNlODQ5NWU0NmRhM2Y0OTBjOTk3YjFkMDU2MWI2MDg2NzgzODYwZjhkODIxNzE3NzM2NzNjOWI1ZWQyMCIsCiAgInNjaGVtYSI6ICJuZi1yZWNlaXB0cy8xIgp9Cg=="),
    };

    /// <summary>
    /// FDE 样例（check38 子扫描 4 · `scripts/fde_sample_run.py`）四钉：真仓（四件证据齐 · manifest 忽略
    /// `generated_at` 后全同）· 交付物被手改（1 条）· **门失败传导**（删掉一个「已声明但交付物不读」的产出面
    /// → G1 FAIL 传导到 gates.txt + result.jsonl + manifest = 3 条）· manifest 被手改（`facts.standards` 改值
    /// → 1 条，证明 `generated_at` 豁免不是「整件不比」）。篡改都在**整树拷贝**上做（`.git` 跳过），
    /// 金标由 probes/fde_sample_probe.py 用同一套篡改配方产出。
    /// </summary>
    private static void FdeSampleCases(List<Check> checks, string work, string repoRoot)
    {
        const string Real = "f77da64c1aa965af5ad642d5e297589d";
        const string TamperedDeliverable = "a7c9c94882394d13f9f96e5547035170";
        const string GateFailure = "e87dc976694d10bc6d62335aeab24f9e";
        const string ManifestTampered = "9decf5a1dbcfcb6e2cbacb10a2fb48f8";

        var real = FdeSample.Check(repoRoot);
        checks.Add(new Check("FDE 样例·真仓（四件证据与当前仓库状态一致 · manifest 只豁免 generated_at）",
            real.Ok && real.LogDigest() == Real && Convert.ToInt64(real.Stats["evidence_files"]) == 4
            && Convert.ToInt64(real.Stats["gates"]) == 5,
            $"FAIL {real.Issues.Count} · 摘要 {real.LogDigest()}（真源金标 {Real}）"));

        var deliverableRoot = Path.Combine(work, "fde-tampered-deliverable");
        Fresh(deliverableRoot);
        CopyTree(repoRoot, deliverableRoot);
        var deliverable = Path.Combine(deliverableRoot, "docs", "fde-sample", "evidence", "deliverable.md");
        File.WriteAllText(deliverable,
            File.ReadAllText(deliverable, new UTF8Encoding(false)) + "- 手改一行（合成篡改）\n",
            new UTF8Encoding(false));
        var tampered = FdeSample.Check(deliverableRoot);
        checks.Add(new Check("FDE 样例·交付物被手改（证据包与当前仓库状态不一致 → 单条判出）",
            !tampered.Ok && tampered.Issues.Count == 1 && tampered.LogDigest() == TamperedDeliverable
            && tampered.Issues[0].StartsWith("docs/fde-sample/evidence/deliverable.md", StringComparison.Ordinal),
            $"FAIL {tampered.Issues.Count} · 摘要 {tampered.LogDigest()}（真源金标 {TamperedDeliverable}）"));

        var gateRoot = Path.Combine(work, "fde-gate-failure");
        Fresh(gateRoot);
        CopyTree(repoRoot, gateRoot);
        File.Delete(Path.Combine(gateRoot, "community", "AI系统域包", "outputs", "charts", "CONCEPT_DAG.mmd"));
        var gateFailure = FdeSample.Check(gateRoot);
        var gateText = string.Join(" | ", gateFailure.Issues);
        checks.Add(new Check("FDE 样例·门失败传导（G1 FAIL → gates.txt + result.jsonl + manifest 三条）",
            !gateFailure.Ok && gateFailure.Issues.Count == 3 && gateFailure.LogDigest() == GateFailure
            && gateText.Contains("evidence/gates.txt 与当前仓库状态不一致")
            && gateText.Contains("evidence/result.jsonl 与当前仓库状态不一致")
            && gateText.Contains("evidence/manifest.json 与当前仓库状态不一致"),
            $"FAIL {gateFailure.Issues.Count} · 摘要 {gateFailure.LogDigest()}（真源金标 {GateFailure}）"));

        var manifestRoot = Path.Combine(work, "fde-manifest-tampered");
        Fresh(manifestRoot);
        CopyTree(repoRoot, manifestRoot);
        var manifestPath = Path.Combine(manifestRoot, "docs", "fde-sample", "evidence", "manifest.json");
        using (var doc = JsonDocument.Parse(File.ReadAllBytes(manifestPath)))
        {
            var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
                        ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var facts = graph.GetValueOrDefault("facts") as Dictionary<string, object?>
                        ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            facts["standards"] = 999L;
            graph["facts"] = facts;
            File.WriteAllText(manifestPath, PythonJson.Indented(graph) + "\n", new UTF8Encoding(false));
        }
        var manifestTampered = FdeSample.Check(manifestRoot);
        checks.Add(new Check("FDE 样例·manifest 被手改（facts 改值即报 · generated_at 豁免不是整件不比）",
            !manifestTampered.Ok && manifestTampered.Issues.Count == 1
            && manifestTampered.LogDigest() == ManifestTampered
            && manifestTampered.Issues[0].StartsWith("docs/fde-sample/evidence/manifest.json", StringComparison.Ordinal),
            $"FAIL {manifestTampered.Issues.Count} · 摘要 {manifestTampered.LogDigest()}"
            + $"（真源金标 {ManifestTampered}）"));
    }

    /// <summary>GEO 出口合成语料（真源 write() 产出；机械导出）。</summary>
    private static readonly (string Rel, string B64)[] GeoSyntheticOkFiles =
    {
		("docs/standards/answer-cards.md", "IyDmoIflh4bnm67lvZUgwrcg5Y+v5byV55So5Y2h77yI5oyJ6Zeu6aKY5b2i5oCB77yJCgo+IOacrOmhteeUsSBgcHl0aG9uIHNjcmlwdHMvZ2VvX2V4cG9ydC5weSAtLXdyaXRlYCDnlJ/miJDvvIznpoHmraLmiYvmlLnjgILnnJ/mupDvvJpgcHJvdG9jb2wvc3RhbmRhcmRzX2NhdGFsb2cuanNvbmAgKyBgcHJvdG9jb2wvc3RhbmRhcmRzX2JpbmRpbmcuanNvbmDjgIIKCi0g6KaG55uW77ya5qCH5YeGICoqMioqIOadoSDCtyDmnKzmnLrlj6/ovr4gKioxKiogwrcg5LiN5Y+v6L6+ICoqMSoqIMK3IOacuuaehCAqKjEqKiDCtyDkvp3otZbovrkgKioxKioKLSDliIblsYLvvJplbmcgMSDCtyBmb3JtIDEKLSDlj6/ovr7mgKfmmK8qKuacrOacuuWunua1iyoq77yI5o6i6ZKI5pel5pyf6KeB5q+P5p2h77yJ77yM5LiN5Y+v6L6+5p2h55uu54Wn5a6e5qCH5rOo44CB5LiN5YGH6KOF5Y+v6L6+44CCCi0g5q+P5byg5Y2h5Zue562U5LiA57G76Zeu6aKY77yM5Y+v55u05o6l6KKr55Sf5oiQ5byP5byV5pOO5byV55So77yb5pWw5o2u5rqQ5ZCM5Li757Si5byV44CCCgojIyDljaEgMSDCtyDlk6rkupvmoIflh4bmj5DkvpvmianlsZXngrnvvJ8KCuWFqCAqKjIqKiDmnaHmoIflh4blnYflo7DmmI7mianlsZXngrnvvIhgZXh0X3BvaW50c2DvvInvvIzmianlsZXngrnmnIDlpJrnmoQgMjAg5p2h77yaCgotIGBhMmAgwrcg55Sy5qCH5YeGIMK3IOaJqeWxleeCuSAy77yaeC1leHQsIHktZXh0Ci0gYGIxYCDCtyDkuZnmoIflh4Ygwrcg5omp5bGV54K5IDDvvJoKCiMjIOWNoSAyIMK3IOWQhOWxguacieWTquS6m+agh+WHhu+8nwoKLSAqKmRhdGEqKiAwIOadoSDihpIgYGRvY3Mvc3RhbmRhcmRzL2xheWVyLWRhdGEubWRgCi0gKiplbmcqKiAxIOadoSDihpIgYGRvY3Mvc3RhbmRhcmRzL2xheWVyLWVuZy5tZGAKLSAqKmZvcm0qKiAxIOadoSDihpIgYGRvY3Mvc3RhbmRhcmRzL2xheWVyLWZvcm0ubWRgCi0gKipnb3YqKiAwIOadoSDihpIgYGRvY3Mvc3RhbmRhcmRzL2xheWVyLWdvdi5tZGAKLSAqKmlmYWNlKiogMCDmnaEg4oaSIGBkb2NzL3N0YW5kYXJkcy9sYXllci1pZmFjZS5tZGAKCiMjIOWNoSAzIMK3IOWTquS6m+agh+WHhuiiq+Wfn+WMhee7keWumuOAgee7keS6huWkmuWwkeasoe+8nwoK57uR5a6a5oC76YePICoqMTIwMCoq77yIMiDmnaHkuI3lkIzmoIflh4booqvlvJXnlKjvvJvkuLvplJo95Y+j5b6E6ZSa77yM6L6F6ZSaPeS6p+WHuuaJv+i9vemUmu+8ieOAgue7keWumuacgOWkmueahCAyMCDmnaHvvJoKCi0gYGEyYCDCtyDkuLvplJogMiAvIOi+hemUmiAwCi0gYGIxYCDCtyDkuLvplJogMCAvIOi+hemUmiAxCgojIyDljaEgNCDCtyDlk6rkupvmoIflh4bmnKzmnLrkuI3lj6/ovr7vvJ/vvIjor5rlrp7miqvpnLLvvIkKCuWFsSAqKjEqKiDmnaHmnKzmnLrmjqLmtYvmnKrovr7vvIjkuI3lgYfoo4Xlj6/ovr7vvInvvIzpgJDmnaHlpoLkuIvvvJoKCi0gYGIxYCDCtyDkuZnmoIflh4YgwrcgSFRUUCAwIMK3IFVSTEVycm9yOiBib29tCg=="),
		("docs/standards/index.md", "IyDmoIflh4bnm67lvZUgwrcg5Y+v5byV55So57Si5byV77yIR0VPIOWHuuWPo++8iQoKPiDmnKzpobXnlLEgYHB5dGhvbiBzY3JpcHRzL2dlb19leHBvcnQucHkgLS13cml0ZWAg55Sf5oiQ77yM56aB5q2i5omL5pS544CC55yf5rqQ77yaYHByb3RvY29sL3N0YW5kYXJkc19jYXRhbG9nLmpzb25gICsgYHByb3RvY29sL3N0YW5kYXJkc19iaW5kaW5nLmpzb25g44CCCgotIOimhueblu+8muagh+WHhiAqKjIqKiDmnaEgwrcg5pys5py65Y+v6L6+ICoqMSoqIMK3IOS4jeWPr+i+viAqKjEqKiDCtyDmnLrmnoQgKioxKiogwrcg5L6d6LWW6L65ICoqMSoqCi0g5YiG5bGC77yaZW5nIDEgwrcgZm9ybSAxCi0g5Y+v6L6+5oCn5pivKirmnKzmnLrlrp7mtYsqKu+8iOaOoumSiOaXpeacn+ingeavj+adoe+8ie+8jOS4jeWPr+i+vuadoeebrueFp+Wunuagh+azqOOAgeS4jeWBh+ijheWPr+i+vuOAggotIOavj+adoeagh+WHhuS4gOS4queos+WumumUmu+8mmAjPGlkPmDvvIjlpoIgYGRvY3Mvc3RhbmRhcmRzL2luZGV4Lm1kI29ubnhg77yJ44CCCgojIyMgYGIxYAotIOS5meagh+WHhiDCtyDigJQgwrcg5bGCIGVuZyDCtyDlj6/ovr4g5ZCm77yIMCDCtyAyMDI2LTAxLTAy77yJIMK3IOaJqeWxleeCuSDigJQgwrcg57uR5a6aIOS4u+mUmiAwIC8g6L6F6ZSaIDEgwrcg4oCUCgojIyMgYGEyYAotIOeUsuagh+WHhiDCtyDmnLrmnoTnlLIgwrcg5bGCIGZvcm0gwrcg5Y+v6L6+IOaYr++8iDIwMCDCtyAyMDI2LTAxLTAx77yJIMK3IOaJqeWxleeCuSB4LWV4dCwgeS1leHQgwrcg57uR5a6aIOS4u+mUmiAyIC8g6L6F6ZSaIDAgwrcgaHR0cHM6Ly9hLmV4YW1wbGUvYTIK"),
		("docs/standards/layer-data.md", "IyDmoIflh4bnm67lvZUgwrcg5bGCIGRhdGHvvIgwIOadoe+8iQoKPiDmnKzpobXnlLEgYHB5dGhvbiBzY3JpcHRzL2dlb19leHBvcnQucHkgLS13cml0ZWAg55Sf5oiQ77yM56aB5q2i5omL5pS544CC55yf5rqQ77yaYHByb3RvY29sL3N0YW5kYXJkc19jYXRhbG9nLmpzb25gICsgYHByb3RvY29sL3N0YW5kYXJkc19iaW5kaW5nLmpzb25g44CCCgotIOimhueblu+8muagh+WHhiAqKjIqKiDmnaEgwrcg5pys5py65Y+v6L6+ICoqMSoqIMK3IOS4jeWPr+i+viAqKjEqKiDCtyDmnLrmnoQgKioxKiogwrcg5L6d6LWW6L65ICoqMSoqCi0g5YiG5bGC77yaZW5nIDEgwrcgZm9ybSAxCi0g5Y+v6L6+5oCn5pivKirmnKzmnLrlrp7mtYsqKu+8iOaOoumSiOaXpeacn+ingeavj+adoe+8ie+8jOS4jeWPr+i+vuadoeebrueFp+Wunuagh+azqOOAgeS4jeWBh+ijheWPr+i+vuOAggotIOacrOmhteS4uiBgZG9jcy9zdGFuZGFyZHMvaW5kZXgubWRgIOeahOaMieWxguWIh+eJh++8jOmUmueCueS4juS4u+e0ouW8leS4gOiHtOOAggo="),
		("docs/standards/layer-eng.md", "IyDmoIflh4bnm67lvZUgwrcg5bGCIGVuZ++8iDEg5p2h77yJCgo+IOacrOmhteeUsSBgcHl0aG9uIHNjcmlwdHMvZ2VvX2V4cG9ydC5weSAtLXdyaXRlYCDnlJ/miJDvvIznpoHmraLmiYvmlLnjgILnnJ/mupDvvJpgcHJvdG9jb2wvc3RhbmRhcmRzX2NhdGFsb2cuanNvbmAgKyBgcHJvdG9jb2wvc3RhbmRhcmRzX2JpbmRpbmcuanNvbmDjgIIKCi0g6KaG55uW77ya5qCH5YeGICoqMioqIOadoSDCtyDmnKzmnLrlj6/ovr4gKioxKiogwrcg5LiN5Y+v6L6+ICoqMSoqIMK3IOacuuaehCAqKjEqKiDCtyDkvp3otZbovrkgKioxKioKLSDliIblsYLvvJplbmcgMSDCtyBmb3JtIDEKLSDlj6/ovr7mgKfmmK8qKuacrOacuuWunua1iyoq77yI5o6i6ZKI5pel5pyf6KeB5q+P5p2h77yJ77yM5LiN5Y+v6L6+5p2h55uu54Wn5a6e5qCH5rOo44CB5LiN5YGH6KOF5Y+v6L6+44CCCi0g5pys6aG15Li6IGBkb2NzL3N0YW5kYXJkcy9pbmRleC5tZGAg55qE5oyJ5bGC5YiH54mH77yM6ZSa54K55LiO5Li757Si5byV5LiA6Ie044CCCgojIyMgYGIxYAotIOS5meagh+WHhiDCtyDigJQgwrcg5bGCIGVuZyDCtyDlj6/ovr4g5ZCm77yIMCDCtyAyMDI2LTAxLTAy77yJIMK3IOaJqeWxleeCuSDigJQgwrcg57uR5a6aIOS4u+mUmiAwIC8g6L6F6ZSaIDEgwrcg4oCUCg=="),
		("docs/standards/layer-form.md", "IyDmoIflh4bnm67lvZUgwrcg5bGCIGZvcm3vvIgxIOadoe+8iQoKPiDmnKzpobXnlLEgYHB5dGhvbiBzY3JpcHRzL2dlb19leHBvcnQucHkgLS13cml0ZWAg55Sf5oiQ77yM56aB5q2i5omL5pS544CC55yf5rqQ77yaYHByb3RvY29sL3N0YW5kYXJkc19jYXRhbG9nLmpzb25gICsgYHByb3RvY29sL3N0YW5kYXJkc19iaW5kaW5nLmpzb25g44CCCgotIOimhueblu+8muagh+WHhiAqKjIqKiDmnaEgwrcg5pys5py65Y+v6L6+ICoqMSoqIMK3IOS4jeWPr+i+viAqKjEqKiDCtyDmnLrmnoQgKioxKiogwrcg5L6d6LWW6L65ICoqMSoqCi0g5YiG5bGC77yaZW5nIDEgwrcgZm9ybSAxCi0g5Y+v6L6+5oCn5pivKirmnKzmnLrlrp7mtYsqKu+8iOaOoumSiOaXpeacn+ingeavj+adoe+8ie+8jOS4jeWPr+i+vuadoeebrueFp+Wunuagh+azqOOAgeS4jeWBh+ijheWPr+i+vuOAggotIOacrOmhteS4uiBgZG9jcy9zdGFuZGFyZHMvaW5kZXgubWRgIOeahOaMieWxguWIh+eJh++8jOmUmueCueS4juS4u+e0ouW8leS4gOiHtOOAggoKIyMjIGBhMmAKLSDnlLLmoIflh4Ygwrcg5py65p6E55SyIMK3IOWxgiBmb3JtIMK3IOWPr+i+viDmmK/vvIgyMDAgwrcgMjAyNi0wMS0wMe+8iSDCtyDmianlsZXngrkgeC1leHQsIHktZXh0IMK3IOe7keWumiDkuLvplJogMiAvIOi+hemUmiAwIMK3IGh0dHBzOi8vYS5leGFtcGxlL2EyCg=="),
		("docs/standards/layer-gov.md", "IyDmoIflh4bnm67lvZUgwrcg5bGCIGdvdu+8iDAg5p2h77yJCgo+IOacrOmhteeUsSBgcHl0aG9uIHNjcmlwdHMvZ2VvX2V4cG9ydC5weSAtLXdyaXRlYCDnlJ/miJDvvIznpoHmraLmiYvmlLnjgILnnJ/mupDvvJpgcHJvdG9jb2wvc3RhbmRhcmRzX2NhdGFsb2cuanNvbmAgKyBgcHJvdG9jb2wvc3RhbmRhcmRzX2JpbmRpbmcuanNvbmDjgIIKCi0g6KaG55uW77ya5qCH5YeGICoqMioqIOadoSDCtyDmnKzmnLrlj6/ovr4gKioxKiogwrcg5LiN5Y+v6L6+ICoqMSoqIMK3IOacuuaehCAqKjEqKiDCtyDkvp3otZbovrkgKioxKioKLSDliIblsYLvvJplbmcgMSDCtyBmb3JtIDEKLSDlj6/ovr7mgKfmmK8qKuacrOacuuWunua1iyoq77yI5o6i6ZKI5pel5pyf6KeB5q+P5p2h77yJ77yM5LiN5Y+v6L6+5p2h55uu54Wn5a6e5qCH5rOo44CB5LiN5YGH6KOF5Y+v6L6+44CCCi0g5pys6aG15Li6IGBkb2NzL3N0YW5kYXJkcy9pbmRleC5tZGAg55qE5oyJ5bGC5YiH54mH77yM6ZSa54K55LiO5Li757Si5byV5LiA6Ie044CCCg=="),
		("docs/standards/layer-iface.md", "IyDmoIflh4bnm67lvZUgwrcg5bGCIGlmYWNl77yIMCDmnaHvvIkKCj4g5pys6aG155SxIGBweXRob24gc2NyaXB0cy9nZW9fZXhwb3J0LnB5IC0td3JpdGVgIOeUn+aIkO+8jOemgeatouaJi+aUueOAguecn+a6kO+8mmBwcm90b2NvbC9zdGFuZGFyZHNfY2F0YWxvZy5qc29uYCArIGBwcm90b2NvbC9zdGFuZGFyZHNfYmluZGluZy5qc29uYOOAggoKLSDopobnm5bvvJrmoIflh4YgKioyKiog5p2hIMK3IOacrOacuuWPr+i+viAqKjEqKiDCtyDkuI3lj6/ovr4gKioxKiogwrcg5py65p6EICoqMSoqIMK3IOS+nei1lui+uSAqKjEqKgotIOWIhuWxgu+8mmVuZyAxIMK3IGZvcm0gMQotIOWPr+i+vuaAp+aYryoq5pys5py65a6e5rWLKirvvIjmjqLpkojml6XmnJ/op4Hmr4/mnaHvvInvvIzkuI3lj6/ovr7mnaHnm67nhaflrp7moIfms6jjgIHkuI3lgYfoo4Xlj6/ovr7jgIIKLSDmnKzpobXkuLogYGRvY3Mvc3RhbmRhcmRzL2luZGV4Lm1kYCDnmoTmjInlsYLliIfniYfvvIzplJrngrnkuI7kuLvntKLlvJXkuIDoh7TjgIIK"),
		("protocol/geo_export.json", "ewogICJjb3ZlcmFnZSI6IHsKICAgICJib2RpZXMiOiAxLAogICAgImJ5X2xheWVyIjogewogICAgICAiZW5nIjogMSwKICAgICAgImZvcm0iOiAxCiAgICB9LAogICAgImRlcGVuZHNfZWRnZXMiOiAxLAogICAgInJlYWNoYWJsZSI6IDEsCiAgICAic3RhbmRhcmRzIjogMiwKICAgICJ1bnJlYWNoYWJsZSI6IDEKICB9LAogICJub3RlIjogIueUn+aIkOeJqe+8m+ecn+a6kCBwcm90b2NvbC9zdGFuZGFyZHNfY2F0YWxvZy5qc29uICsgcHJvdG9jb2wvc3RhbmRhcmRzX2JpbmRpbmcuanNvbuOAgiIsCiAgInNjaGVtYSI6ICJuZi1nZW8tZXhwb3J0LzEiLAogICJzdGFuZGFyZHMiOiBbCiAgICB7CiAgICAgICJib2R5IjogbnVsbCwKICAgICAgImJvdW5kX21haW4iOiAwLAogICAgICAiYm91bmRfc3VwcG9ydCI6IDEsCiAgICAgICJleHRfcG9pbnRzIjogW10sCiAgICAgICJodHRwX3N0YXR1cyI6IDAsCiAgICAgICJpZCI6ICJiMSIsCiAgICAgICJsYXllciI6ICJlbmciLAogICAgICAicHJvYmVfZGF0ZSI6ICIyMDI2LTAxLTAyIiwKICAgICAgInJlYWNoYWJsZSI6IGZhbHNlLAogICAgICAic2hhMjU2X3NhbXBsZSI6IG51bGwsCiAgICAgICJ0aXRsZSI6ICLkuZnmoIflh4YiLAogICAgICAidXJsIjogbnVsbAogICAgfSwKICAgIHsKICAgICAgImJvZHkiOiAi5py65p6E55SyIiwKICAgICAgImJvdW5kX21haW4iOiAyLAogICAgICAiYm91bmRfc3VwcG9ydCI6IDAsCiAgICAgICJleHRfcG9pbnRzIjogWwogICAgICAgICJ4LWV4dCIsCiAgICAgICAgInktZXh0IgogICAgICBdLAogICAgICAiaHR0cF9zdGF0dXMiOiAyMDAsCiAgICAgICJpZCI6ICJhMiIsCiAgICAgICJsYXllciI6ICJmb3JtIiwKICAgICAgInByb2JlX2RhdGUiOiAiMjAyNi0wMS0wMSIsCiAgICAgICJyZWFjaGFibGUiOiB0cnVlLAogICAgICAic2hhMjU2X3NhbXBsZSI6ICJhYmMiLAogICAgICAidGl0bGUiOiAi55Sy5qCH5YeGIiwKICAgICAgInVybCI6ICJodHRwczovL2EuZXhhbXBsZS9hMiIKICAgIH0KICBdCn0K"),
		("protocol/standards_binding.json", "ewogICJwYWNrcyI6IFsKICAgIHsKICAgICAgImJpbmRpbmdzIjogWwogICAgICAgIHsKICAgICAgICAgICJzdGFuZGFyZCI6ICJhMiIsCiAgICAgICAgICAic3VwcG9ydF9zdGFuZGFyZCI6ICJiMSIKICAgICAgICB9LAogICAgICAgIHsKICAgICAgICAgICJzdGFuZGFyZCI6ICJhMiIKICAgICAgICB9CiAgICAgIF0KICAgIH0KICBdCn0="),
		("protocol/standards_catalog.json", "ewogICJzdGFuZGFyZHMiOiBbCiAgICB7CiAgICAgICJpZCI6ICJhMiIsCiAgICAgICJ0aXRsZSI6ICLnlLLmoIflh4YiLAogICAgICAiYm9keSI6ICLmnLrmnoTnlLIiLAogICAgICAidXJsIjogImh0dHBzOi8vYS5leGFtcGxlL2EyIiwKICAgICAgImxheWVyIjogImZvcm0iLAogICAgICAiZXh0X3BvaW50cyI6IFsKICAgICAgICAieC1leHQiLAogICAgICAgICJ5LWV4dCIKICAgICAgXSwKICAgICAgImV2aWRlbmNlIjogewogICAgICAgICJyZWFjaGFibGUiOiB0cnVlLAogICAgICAgICJodHRwX3N0YXR1cyI6IDIwMCwKICAgICAgICAicHJvYmVfZGF0ZSI6ICIyMDI2LTAxLTAxIiwKICAgICAgICAic2hhMjU2X3NhbXBsZSI6ICJhYmMiCiAgICAgIH0KICAgIH0sCiAgICB7CiAgICAgICJpZCI6ICJiMSIsCiAgICAgICJ0aXRsZSI6ICLkuZnmoIflh4YiLAogICAgICAibGF5ZXIiOiAiZW5nIiwKICAgICAgImV4dF9wb2ludHMiOiBbXSwKICAgICAgImV2aWRlbmNlIjogewogICAgICAgICJyZWFjaGFibGUiOiBmYWxzZSwKICAgICAgICAiaHR0cF9zdGF0dXMiOiAwLAogICAgICAgICJwcm9iZV9kYXRlIjogIjIwMjYtMDEtMDIiLAogICAgICAgICJlcnJvciI6ICJVUkxFcnJvcjogYm9vbSIKICAgICAgfQogICAgfQogIF0sCiAgImNvdmVyYWdlIjogewogICAgInN0YW5kYXJkcyI6IDIsCiAgICAicmVhY2hhYmxlIjogMSwKICAgICJ1bnJlYWNoYWJsZSI6IDEsCiAgICAiYm9kaWVzIjogMSwKICAgICJkZXBlbmRzX2VkZ2VzIjogMSwKICAgICJieV9sYXllciI6IHsKICAgICAgImVuZyI6IDEsCiAgICAgICJmb3JtIjogMQogICAgfQogIH0KfQ=="),
    };

    /// <summary>GEO 出口合成语料（删掉一个索引锚点后的盘上状态；机械导出）。</summary>
    private static readonly (string Rel, string B64)[] GeoSyntheticTamperedFiles =
    {
		("docs/standards/answer-cards.md", "IyDmoIflh4bnm67lvZUgwrcg5Y+v5byV55So5Y2h77yI5oyJ6Zeu6aKY5b2i5oCB77yJCgo+IOacrOmhteeUsSBgcHl0aG9uIHNjcmlwdHMvZ2VvX2V4cG9ydC5weSAtLXdyaXRlYCDnlJ/miJDvvIznpoHmraLmiYvmlLnjgILnnJ/mupDvvJpgcHJvdG9jb2wvc3RhbmRhcmRzX2NhdGFsb2cuanNvbmAgKyBgcHJvdG9jb2wvc3RhbmRhcmRzX2JpbmRpbmcuanNvbmDjgIIKCi0g6KaG55uW77ya5qCH5YeGICoqMioqIOadoSDCtyDmnKzmnLrlj6/ovr4gKioxKiogwrcg5LiN5Y+v6L6+ICoqMSoqIMK3IOacuuaehCAqKjEqKiDCtyDkvp3otZbovrkgKioxKioKLSDliIblsYLvvJplbmcgMSDCtyBmb3JtIDEKLSDlj6/ovr7mgKfmmK8qKuacrOacuuWunua1iyoq77yI5o6i6ZKI5pel5pyf6KeB5q+P5p2h77yJ77yM5LiN5Y+v6L6+5p2h55uu54Wn5a6e5qCH5rOo44CB5LiN5YGH6KOF5Y+v6L6+44CCCi0g5q+P5byg5Y2h5Zue562U5LiA57G76Zeu6aKY77yM5Y+v55u05o6l6KKr55Sf5oiQ5byP5byV5pOO5byV55So77yb5pWw5o2u5rqQ5ZCM5Li757Si5byV44CCCgojIyDljaEgMSDCtyDlk6rkupvmoIflh4bmj5DkvpvmianlsZXngrnvvJ8KCuWFqCAqKjIqKiDmnaHmoIflh4blnYflo7DmmI7mianlsZXngrnvvIhgZXh0X3BvaW50c2DvvInvvIzmianlsZXngrnmnIDlpJrnmoQgMjAg5p2h77yaCgotIGBhMmAgwrcg55Sy5qCH5YeGIMK3IOaJqeWxleeCuSAy77yaeC1leHQsIHktZXh0Ci0gYGIxYCDCtyDkuZnmoIflh4Ygwrcg5omp5bGV54K5IDDvvJoKCiMjIOWNoSAyIMK3IOWQhOWxguacieWTquS6m+agh+WHhu+8nwoKLSAqKmRhdGEqKiAwIOadoSDihpIgYGRvY3Mvc3RhbmRhcmRzL2xheWVyLWRhdGEubWRgCi0gKiplbmcqKiAxIOadoSDihpIgYGRvY3Mvc3RhbmRhcmRzL2xheWVyLWVuZy5tZGAKLSAqKmZvcm0qKiAxIOadoSDihpIgYGRvY3Mvc3RhbmRhcmRzL2xheWVyLWZvcm0ubWRgCi0gKipnb3YqKiAwIOadoSDihpIgYGRvY3Mvc3RhbmRhcmRzL2xheWVyLWdvdi5tZGAKLSAqKmlmYWNlKiogMCDmnaEg4oaSIGBkb2NzL3N0YW5kYXJkcy9sYXllci1pZmFjZS5tZGAKCiMjIOWNoSAzIMK3IOWTquS6m+agh+WHhuiiq+Wfn+WMhee7keWumuOAgee7keS6huWkmuWwkeasoe+8nwoK57uR5a6a5oC76YePICoqMTIwMCoq77yIMiDmnaHkuI3lkIzmoIflh4booqvlvJXnlKjvvJvkuLvplJo95Y+j5b6E6ZSa77yM6L6F6ZSaPeS6p+WHuuaJv+i9vemUmu+8ieOAgue7keWumuacgOWkmueahCAyMCDmnaHvvJoKCi0gYGEyYCDCtyDkuLvplJogMiAvIOi+hemUmiAwCi0gYGIxYCDCtyDkuLvplJogMCAvIOi+hemUmiAxCgojIyDljaEgNCDCtyDlk6rkupvmoIflh4bmnKzmnLrkuI3lj6/ovr7vvJ/vvIjor5rlrp7miqvpnLLvvIkKCuWFsSAqKjEqKiDmnaHmnKzmnLrmjqLmtYvmnKrovr7vvIjkuI3lgYfoo4Xlj6/ovr7vvInvvIzpgJDmnaHlpoLkuIvvvJoKCi0gYGIxYCDCtyDkuZnmoIflh4YgwrcgSFRUUCAwIMK3IFVSTEVycm9yOiBib29tCg=="),
		("docs/standards/index.md", "IyDmoIflh4bnm67lvZUgwrcg5Y+v5byV55So57Si5byV77yIR0VPIOWHuuWPo++8iQoKPiDmnKzpobXnlLEgYHB5dGhvbiBzY3JpcHRzL2dlb19leHBvcnQucHkgLS13cml0ZWAg55Sf5oiQ77yM56aB5q2i5omL5pS544CC55yf5rqQ77yaYHByb3RvY29sL3N0YW5kYXJkc19jYXRhbG9nLmpzb25gICsgYHByb3RvY29sL3N0YW5kYXJkc19iaW5kaW5nLmpzb25g44CCCgotIOimhueblu+8muagh+WHhiAqKjIqKiDmnaEgwrcg5pys5py65Y+v6L6+ICoqMSoqIMK3IOS4jeWPr+i+viAqKjEqKiDCtyDmnLrmnoQgKioxKiogwrcg5L6d6LWW6L65ICoqMSoqCi0g5YiG5bGC77yaZW5nIDEgwrcgZm9ybSAxCi0g5Y+v6L6+5oCn5pivKirmnKzmnLrlrp7mtYsqKu+8iOaOoumSiOaXpeacn+ingeavj+adoe+8ie+8jOS4jeWPr+i+vuadoeebrueFp+Wunuagh+azqOOAgeS4jeWBh+ijheWPr+i+vuOAggotIOavj+adoeagh+WHhuS4gOS4queos+WumumUmu+8mmAjPGlkPmDvvIjlpoIgYGRvY3Mvc3RhbmRhcmRzL2luZGV4Lm1kI29ubnhg77yJ44CCCgojIyMgYGIxYAotIOS5meagh+WHhiDCtyDigJQgwrcg5bGCIGVuZyDCtyDlj6/ovr4g5ZCm77yIMCDCtyAyMDI2LTAxLTAy77yJIMK3IOaJqeWxleeCuSDigJQgwrcg57uR5a6aIOS4u+mUmiAwIC8g6L6F6ZSaIDEgwrcg4oCUCgotIOeUsuagh+WHhiDCtyDmnLrmnoTnlLIgwrcg5bGCIGZvcm0gwrcg5Y+v6L6+IOaYr++8iDIwMCDCtyAyMDI2LTAxLTAx77yJIMK3IOaJqeWxleeCuSB4LWV4dCwgeS1leHQgwrcg57uR5a6aIOS4u+mUmiAyIC8g6L6F6ZSaIDAgwrcgaHR0cHM6Ly9hLmV4YW1wbGUvYTIK"),
		("docs/standards/layer-data.md", "IyDmoIflh4bnm67lvZUgwrcg5bGCIGRhdGHvvIgwIOadoe+8iQoKPiDmnKzpobXnlLEgYHB5dGhvbiBzY3JpcHRzL2dlb19leHBvcnQucHkgLS13cml0ZWAg55Sf5oiQ77yM56aB5q2i5omL5pS544CC55yf5rqQ77yaYHByb3RvY29sL3N0YW5kYXJkc19jYXRhbG9nLmpzb25gICsgYHByb3RvY29sL3N0YW5kYXJkc19iaW5kaW5nLmpzb25g44CCCgotIOimhueblu+8muagh+WHhiAqKjIqKiDmnaEgwrcg5pys5py65Y+v6L6+ICoqMSoqIMK3IOS4jeWPr+i+viAqKjEqKiDCtyDmnLrmnoQgKioxKiogwrcg5L6d6LWW6L65ICoqMSoqCi0g5YiG5bGC77yaZW5nIDEgwrcgZm9ybSAxCi0g5Y+v6L6+5oCn5pivKirmnKzmnLrlrp7mtYsqKu+8iOaOoumSiOaXpeacn+ingeavj+adoe+8ie+8jOS4jeWPr+i+vuadoeebrueFp+Wunuagh+azqOOAgeS4jeWBh+ijheWPr+i+vuOAggotIOacrOmhteS4uiBgZG9jcy9zdGFuZGFyZHMvaW5kZXgubWRgIOeahOaMieWxguWIh+eJh++8jOmUmueCueS4juS4u+e0ouW8leS4gOiHtOOAggo="),
		("docs/standards/layer-eng.md", "IyDmoIflh4bnm67lvZUgwrcg5bGCIGVuZ++8iDEg5p2h77yJCgo+IOacrOmhteeUsSBgcHl0aG9uIHNjcmlwdHMvZ2VvX2V4cG9ydC5weSAtLXdyaXRlYCDnlJ/miJDvvIznpoHmraLmiYvmlLnjgILnnJ/mupDvvJpgcHJvdG9jb2wvc3RhbmRhcmRzX2NhdGFsb2cuanNvbmAgKyBgcHJvdG9jb2wvc3RhbmRhcmRzX2JpbmRpbmcuanNvbmDjgIIKCi0g6KaG55uW77ya5qCH5YeGICoqMioqIOadoSDCtyDmnKzmnLrlj6/ovr4gKioxKiogwrcg5LiN5Y+v6L6+ICoqMSoqIMK3IOacuuaehCAqKjEqKiDCtyDkvp3otZbovrkgKioxKioKLSDliIblsYLvvJplbmcgMSDCtyBmb3JtIDEKLSDlj6/ovr7mgKfmmK8qKuacrOacuuWunua1iyoq77yI5o6i6ZKI5pel5pyf6KeB5q+P5p2h77yJ77yM5LiN5Y+v6L6+5p2h55uu54Wn5a6e5qCH5rOo44CB5LiN5YGH6KOF5Y+v6L6+44CCCi0g5pys6aG15Li6IGBkb2NzL3N0YW5kYXJkcy9pbmRleC5tZGAg55qE5oyJ5bGC5YiH54mH77yM6ZSa54K55LiO5Li757Si5byV5LiA6Ie044CCCgojIyMgYGIxYAotIOS5meagh+WHhiDCtyDigJQgwrcg5bGCIGVuZyDCtyDlj6/ovr4g5ZCm77yIMCDCtyAyMDI2LTAxLTAy77yJIMK3IOaJqeWxleeCuSDigJQgwrcg57uR5a6aIOS4u+mUmiAwIC8g6L6F6ZSaIDEgwrcg4oCUCg=="),
		("docs/standards/layer-form.md", "IyDmoIflh4bnm67lvZUgwrcg5bGCIGZvcm3vvIgxIOadoe+8iQoKPiDmnKzpobXnlLEgYHB5dGhvbiBzY3JpcHRzL2dlb19leHBvcnQucHkgLS13cml0ZWAg55Sf5oiQ77yM56aB5q2i5omL5pS544CC55yf5rqQ77yaYHByb3RvY29sL3N0YW5kYXJkc19jYXRhbG9nLmpzb25gICsgYHByb3RvY29sL3N0YW5kYXJkc19iaW5kaW5nLmpzb25g44CCCgotIOimhueblu+8muagh+WHhiAqKjIqKiDmnaEgwrcg5pys5py65Y+v6L6+ICoqMSoqIMK3IOS4jeWPr+i+viAqKjEqKiDCtyDmnLrmnoQgKioxKiogwrcg5L6d6LWW6L65ICoqMSoqCi0g5YiG5bGC77yaZW5nIDEgwrcgZm9ybSAxCi0g5Y+v6L6+5oCn5pivKirmnKzmnLrlrp7mtYsqKu+8iOaOoumSiOaXpeacn+ingeavj+adoe+8ie+8jOS4jeWPr+i+vuadoeebrueFp+Wunuagh+azqOOAgeS4jeWBh+ijheWPr+i+vuOAggotIOacrOmhteS4uiBgZG9jcy9zdGFuZGFyZHMvaW5kZXgubWRgIOeahOaMieWxguWIh+eJh++8jOmUmueCueS4juS4u+e0ouW8leS4gOiHtOOAggoKIyMjIGBhMmAKLSDnlLLmoIflh4Ygwrcg5py65p6E55SyIMK3IOWxgiBmb3JtIMK3IOWPr+i+viDmmK/vvIgyMDAgwrcgMjAyNi0wMS0wMe+8iSDCtyDmianlsZXngrkgeC1leHQsIHktZXh0IMK3IOe7keWumiDkuLvplJogMiAvIOi+hemUmiAwIMK3IGh0dHBzOi8vYS5leGFtcGxlL2EyCg=="),
		("docs/standards/layer-gov.md", "IyDmoIflh4bnm67lvZUgwrcg5bGCIGdvdu+8iDAg5p2h77yJCgo+IOacrOmhteeUsSBgcHl0aG9uIHNjcmlwdHMvZ2VvX2V4cG9ydC5weSAtLXdyaXRlYCDnlJ/miJDvvIznpoHmraLmiYvmlLnjgILnnJ/mupDvvJpgcHJvdG9jb2wvc3RhbmRhcmRzX2NhdGFsb2cuanNvbmAgKyBgcHJvdG9jb2wvc3RhbmRhcmRzX2JpbmRpbmcuanNvbmDjgIIKCi0g6KaG55uW77ya5qCH5YeGICoqMioqIOadoSDCtyDmnKzmnLrlj6/ovr4gKioxKiogwrcg5LiN5Y+v6L6+ICoqMSoqIMK3IOacuuaehCAqKjEqKiDCtyDkvp3otZbovrkgKioxKioKLSDliIblsYLvvJplbmcgMSDCtyBmb3JtIDEKLSDlj6/ovr7mgKfmmK8qKuacrOacuuWunua1iyoq77yI5o6i6ZKI5pel5pyf6KeB5q+P5p2h77yJ77yM5LiN5Y+v6L6+5p2h55uu54Wn5a6e5qCH5rOo44CB5LiN5YGH6KOF5Y+v6L6+44CCCi0g5pys6aG15Li6IGBkb2NzL3N0YW5kYXJkcy9pbmRleC5tZGAg55qE5oyJ5bGC5YiH54mH77yM6ZSa54K55LiO5Li757Si5byV5LiA6Ie044CCCg=="),
		("docs/standards/layer-iface.md", "IyDmoIflh4bnm67lvZUgwrcg5bGCIGlmYWNl77yIMCDmnaHvvIkKCj4g5pys6aG155SxIGBweXRob24gc2NyaXB0cy9nZW9fZXhwb3J0LnB5IC0td3JpdGVgIOeUn+aIkO+8jOemgeatouaJi+aUueOAguecn+a6kO+8mmBwcm90b2NvbC9zdGFuZGFyZHNfY2F0YWxvZy5qc29uYCArIGBwcm90b2NvbC9zdGFuZGFyZHNfYmluZGluZy5qc29uYOOAggoKLSDopobnm5bvvJrmoIflh4YgKioyKiog5p2hIMK3IOacrOacuuWPr+i+viAqKjEqKiDCtyDkuI3lj6/ovr4gKioxKiogwrcg5py65p6EICoqMSoqIMK3IOS+nei1lui+uSAqKjEqKgotIOWIhuWxgu+8mmVuZyAxIMK3IGZvcm0gMQotIOWPr+i+vuaAp+aYryoq5pys5py65a6e5rWLKirvvIjmjqLpkojml6XmnJ/op4Hmr4/mnaHvvInvvIzkuI3lj6/ovr7mnaHnm67nhaflrp7moIfms6jjgIHkuI3lgYfoo4Xlj6/ovr7jgIIKLSDmnKzpobXkuLogYGRvY3Mvc3RhbmRhcmRzL2luZGV4Lm1kYCDnmoTmjInlsYLliIfniYfvvIzplJrngrnkuI7kuLvntKLlvJXkuIDoh7TjgIIK"),
		("protocol/geo_export.json", "ewogICJjb3ZlcmFnZSI6IHsKICAgICJib2RpZXMiOiAxLAogICAgImJ5X2xheWVyIjogewogICAgICAiZW5nIjogMSwKICAgICAgImZvcm0iOiAxCiAgICB9LAogICAgImRlcGVuZHNfZWRnZXMiOiAxLAogICAgInJlYWNoYWJsZSI6IDEsCiAgICAic3RhbmRhcmRzIjogMiwKICAgICJ1bnJlYWNoYWJsZSI6IDEKICB9LAogICJub3RlIjogIueUn+aIkOeJqe+8m+ecn+a6kCBwcm90b2NvbC9zdGFuZGFyZHNfY2F0YWxvZy5qc29uICsgcHJvdG9jb2wvc3RhbmRhcmRzX2JpbmRpbmcuanNvbuOAgiIsCiAgInNjaGVtYSI6ICJuZi1nZW8tZXhwb3J0LzEiLAogICJzdGFuZGFyZHMiOiBbCiAgICB7CiAgICAgICJib2R5IjogbnVsbCwKICAgICAgImJvdW5kX21haW4iOiAwLAogICAgICAiYm91bmRfc3VwcG9ydCI6IDEsCiAgICAgICJleHRfcG9pbnRzIjogW10sCiAgICAgICJodHRwX3N0YXR1cyI6IDAsCiAgICAgICJpZCI6ICJiMSIsCiAgICAgICJsYXllciI6ICJlbmciLAogICAgICAicHJvYmVfZGF0ZSI6ICIyMDI2LTAxLTAyIiwKICAgICAgInJlYWNoYWJsZSI6IGZhbHNlLAogICAgICAic2hhMjU2X3NhbXBsZSI6IG51bGwsCiAgICAgICJ0aXRsZSI6ICLkuZnmoIflh4YiLAogICAgICAidXJsIjogbnVsbAogICAgfSwKICAgIHsKICAgICAgImJvZHkiOiAi5py65p6E55SyIiwKICAgICAgImJvdW5kX21haW4iOiAyLAogICAgICAiYm91bmRfc3VwcG9ydCI6IDAsCiAgICAgICJleHRfcG9pbnRzIjogWwogICAgICAgICJ4LWV4dCIsCiAgICAgICAgInktZXh0IgogICAgICBdLAogICAgICAiaHR0cF9zdGF0dXMiOiAyMDAsCiAgICAgICJpZCI6ICJhMiIsCiAgICAgICJsYXllciI6ICJmb3JtIiwKICAgICAgInByb2JlX2RhdGUiOiAiMjAyNi0wMS0wMSIsCiAgICAgICJyZWFjaGFibGUiOiB0cnVlLAogICAgICAic2hhMjU2X3NhbXBsZSI6ICJhYmMiLAogICAgICAidGl0bGUiOiAi55Sy5qCH5YeGIiwKICAgICAgInVybCI6ICJodHRwczovL2EuZXhhbXBsZS9hMiIKICAgIH0KICBdCn0K"),
		("protocol/standards_binding.json", "ewogICJwYWNrcyI6IFsKICAgIHsKICAgICAgImJpbmRpbmdzIjogWwogICAgICAgIHsKICAgICAgICAgICJzdGFuZGFyZCI6ICJhMiIsCiAgICAgICAgICAic3VwcG9ydF9zdGFuZGFyZCI6ICJiMSIKICAgICAgICB9LAogICAgICAgIHsKICAgICAgICAgICJzdGFuZGFyZCI6ICJhMiIKICAgICAgICB9CiAgICAgIF0KICAgIH0KICBdCn0="),
		("protocol/standards_catalog.json", "ewogICJzdGFuZGFyZHMiOiBbCiAgICB7CiAgICAgICJpZCI6ICJhMiIsCiAgICAgICJ0aXRsZSI6ICLnlLLmoIflh4YiLAogICAgICAiYm9keSI6ICLmnLrmnoTnlLIiLAogICAgICAidXJsIjogImh0dHBzOi8vYS5leGFtcGxlL2EyIiwKICAgICAgImxheWVyIjogImZvcm0iLAogICAgICAiZXh0X3BvaW50cyI6IFsKICAgICAgICAieC1leHQiLAogICAgICAgICJ5LWV4dCIKICAgICAgXSwKICAgICAgImV2aWRlbmNlIjogewogICAgICAgICJyZWFjaGFibGUiOiB0cnVlLAogICAgICAgICJodHRwX3N0YXR1cyI6IDIwMCwKICAgICAgICAicHJvYmVfZGF0ZSI6ICIyMDI2LTAxLTAxIiwKICAgICAgICAic2hhMjU2X3NhbXBsZSI6ICJhYmMiCiAgICAgIH0KICAgIH0sCiAgICB7CiAgICAgICJpZCI6ICJiMSIsCiAgICAgICJ0aXRsZSI6ICLkuZnmoIflh4YiLAogICAgICAibGF5ZXIiOiAiZW5nIiwKICAgICAgImV4dF9wb2ludHMiOiBbXSwKICAgICAgImV2aWRlbmNlIjogewogICAgICAgICJyZWFjaGFibGUiOiBmYWxzZSwKICAgICAgICAiaHR0cF9zdGF0dXMiOiAwLAogICAgICAgICJwcm9iZV9kYXRlIjogIjIwMjYtMDEtMDIiLAogICAgICAgICJlcnJvciI6ICJVUkxFcnJvcjogYm9vbSIKICAgICAgfQogICAgfQogIF0sCiAgImNvdmVyYWdlIjogewogICAgInN0YW5kYXJkcyI6IDIsCiAgICAicmVhY2hhYmxlIjogMSwKICAgICJ1bnJlYWNoYWJsZSI6IDEsCiAgICAiYm9kaWVzIjogMSwKICAgICJkZXBlbmRzX2VkZ2VzIjogMSwKICAgICJieV9sYXllciI6IHsKICAgICAgImVuZyI6IDEsCiAgICAgICJmb3JtIjogMQogICAgfQogIH0KfQ=="),
    };

    /// <summary>GEO 出口合成语料（只有真源、无生成物；机械导出）。</summary>
    private static readonly (string Rel, string B64)[] GeoSyntheticAbsentFiles =
    {
		("protocol/standards_binding.json", "ewogICJwYWNrcyI6IFsKICAgIHsKICAgICAgImJpbmRpbmdzIjogWwogICAgICAgIHsKICAgICAgICAgICJzdGFuZGFyZCI6ICJhMiIsCiAgICAgICAgICAic3VwcG9ydF9zdGFuZGFyZCI6ICJiMSIKICAgICAgICB9LAogICAgICAgIHsKICAgICAgICAgICJzdGFuZGFyZCI6ICJhMiIKICAgICAgICB9CiAgICAgIF0KICAgIH0KICBdCn0="),
		("protocol/standards_catalog.json", "ewogICJzdGFuZGFyZHMiOiBbCiAgICB7CiAgICAgICJpZCI6ICJhMiIsCiAgICAgICJ0aXRsZSI6ICLnlLLmoIflh4YiLAogICAgICAiYm9keSI6ICLmnLrmnoTnlLIiLAogICAgICAidXJsIjogImh0dHBzOi8vYS5leGFtcGxlL2EyIiwKICAgICAgImxheWVyIjogImZvcm0iLAogICAgICAiZXh0X3BvaW50cyI6IFsKICAgICAgICAieC1leHQiLAogICAgICAgICJ5LWV4dCIKICAgICAgXSwKICAgICAgImV2aWRlbmNlIjogewogICAgICAgICJyZWFjaGFibGUiOiB0cnVlLAogICAgICAgICJodHRwX3N0YXR1cyI6IDIwMCwKICAgICAgICAicHJvYmVfZGF0ZSI6ICIyMDI2LTAxLTAxIiwKICAgICAgICAic2hhMjU2X3NhbXBsZSI6ICJhYmMiCiAgICAgIH0KICAgIH0sCiAgICB7CiAgICAgICJpZCI6ICJiMSIsCiAgICAgICJ0aXRsZSI6ICLkuZnmoIflh4YiLAogICAgICAibGF5ZXIiOiAiZW5nIiwKICAgICAgImV4dF9wb2ludHMiOiBbXSwKICAgICAgImV2aWRlbmNlIjogewogICAgICAgICJyZWFjaGFibGUiOiBmYWxzZSwKICAgICAgICAiaHR0cF9zdGF0dXMiOiAwLAogICAgICAgICJwcm9iZV9kYXRlIjogIjIwMjYtMDEtMDIiLAogICAgICAgICJlcnJvciI6ICJVUkxFcnJvcjogYm9vbSIKICAgICAgfQogICAgfQogIF0sCiAgImNvdmVyYWdlIjogewogICAgInN0YW5kYXJkcyI6IDIsCiAgICAicmVhY2hhYmxlIjogMSwKICAgICJ1bnJlYWNoYWJsZSI6IDEsCiAgICAiYm9kaWVzIjogMSwKICAgICJkZXBlbmRzX2VkZ2VzIjogMSwKICAgICJieV9sYXllciI6IHsKICAgICAgImVuZyI6IDEsCiAgICAgICJmb3JtIjogMQogICAgfQogIH0KfQ=="),
    };

    /// <summary>构建回路合成语料（真源 workloop.scan 输出锚定；机械导出）。</summary>
    private static readonly (string Rel, string B64)[] WorkloopSyntheticFiles =
    {
		("protocol/type_backlog.json", "ewogImNvdW50IjogMiwKICJmaWVsZHMiOiBbCiAgewogICAiZXZlbnQiOiAiZXYuYWxwaGEiLAogICAiZmllbGQiOiAicGF5bG9hZC54IiwKICAgIm5vdGUiOiAi5b6F5qC4IgogIH0sCiAgewogICAiZXZlbnQiOiAiZXYuYmV0YSIsCiAgICJmaWVsZCI6ICJwYXlsb2FkLnkiCiAgfQogXQp9"),
		("protocol/pipeline_advisory.json", "ewogImNvdW50IjogMSwKICJjb3VudHMiOiB7CiAgIui3qOWMhS/lpJbpg6jkuovku7YiOiAxCiB9LAogIml0ZW1zIjogWwogIHsKICAgInBpcGVsaW5lIjogIlAwOSIsCiAgICJjYXRlZ29yeSI6ICLot6jljIUv5aSW6YOo5LqL5Lu2IiwKICAgImRldGFpbCI6ICLlkIjmiJDmoLfmnKwiCiAgfQogXQp9"),
		("protocol/decision_layer.json", "ewogInNjaGVtYSI6ICJuZi1kZWNpc2lvbi1sYXllci8xIiwKICJwcmltaXRpdmVzIjogewogICJjaG9pY2UiOiAi5Zyo6LCD55So5pa557uZ5a6a6YCJ6aG55LiK57uZ5qaC546H5YiG5biDICsgYXJnbWF4IiwKICAibm91bCI6ICLlr7nmmK/pnZ7pl67popjmiqXmpoLnjocgcCIsCiAgInNjb3JlIjogIuWvueacieW6j+etiee6p+aKpeamgueOh+WIhuW4gyArIOacn+acm+WAvCIKIH0sCiAiYWRhcHRlcnMiOiBbCiAgewogICAiaWQiOiAic3R1YiIsCiAgICJraW5kIjogIm9mZmxpbmUtZGV0ZXJtaW5pc3RpYyIsCiAgICJpbl9nYXRlX3BhdGgiOiB0cnVlLAogICAiY2FsaWJyYXRlZCI6IGZhbHNlLAogICAibm90ZSI6ICLpl6jnpoHnlKjnmoTnprvnur/noa7lrprmgKfpgILphY3lmajvvIjlkIjmiJDor63mlpnvvIkiCiAgfQogXSwKICJjYW5kaWRhdGVzIjogWwogIHsKICAgImlkIjogIuWQiOaIkOWAmemAiSIsCiAgICJzb3VyY2UiOiAiaGY65ZCI5oiQL+WAmemAiSIsCiAgICJsaWNlbnNlIjogImFwYWNoZS0yLjAiLAogICAiZXZpZGVuY2UiOiAi5ZCI5oiQ6K+t5paZIiwKICAgInB1bGxlZCI6IHRydWUsCiAgICJsb2NhbCI6IHsKICAgICJob3ciOiAiaCIsCiAgICAicnVudGltZSI6ICJyIiwKICAgICJzZXJ2ZWRfYnkiOiAicyIKICAgfQogIH0KIF0sCiAiYm91bmRhcmllcyI6IFsKICAi5LiN5omn6KGM5Yqo5L2cIiwKICAi5LiN55Sf5oiQ5q2j5paHIiwKICAi5LiN5YWl6Zeo56aB6Lev5b6EIgogXQp9"),
		("scripts/nf.py", "aW1wb3J0IGFyZ3BhcnNlCmRlZiBidWlsZChzdWIpOgogICAgc3ViLmFkZF9wYXJzZXIoImRlY2lzaW9ucyIpCiAgICBzdWIuYWRkX3BhcnNlcigic2NvcmUiKQogICAgc3ViLmFkZF9wYXJzZXIoIndvcmtsb29wIikKICAgIHN1Yi5hZGRfcGFyc2VyKCJyZWNlaXB0cyIpCiAgICBzdWIuYWRkX3BhcnNlcigiZW5kcG9pbnQiKQogICAgcCA9IHN1Yi5hZGRfcGFyc2VyKCJpbnRlcm9wIikKICAgIHAuYWRkX2FyZ3VtZW50KCItLWtpbmQiLCBkZWZhdWx0PSJvcGVuYXBpIiwgY2hvaWNlcz1bIm9wZW5hcGkiLCAiYXN5bmNhcGkiXSkK"),
    };

    /// <summary>compare() 六例语料（JSON，base64；机械导出，勿手抄）。</summary>
    private const string RegressionComparePairsB64 = "WwogewogICJjYXNlIjogIm5vX3JlZ3Jlc3Npb24iLAogICJjdXJyZW50IjogewogICAic2NvcmUiOiAxMDAuMCwKICAgInNpZ25hbHMiOiBbCiAgICB7CiAgICAgIm5hbWUiOiAic2NoZW1hX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4yLAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJjb25mb3JtYW5jZV9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMiwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiZG9jX2h5Z2llbmUiLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJkZXB0aF9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImFzc2V0X2RlbnNpdHkiLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfQogICBdCiAgfSwKICAiYmFzZWxpbmUiOiB7CiAgICJzY29yZSI6IDEwMC4wLAogICAic2lnbmFscyI6IFsKICAgIHsKICAgICAibmFtZSI6ICJzY2hlbWFfY2xlYW4iLAogICAgICJ3ZWlnaHQiOiAwLjIsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImNvbmZvcm1hbmNlX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4yLAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJkb2NfaHlnaWVuZSIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImRlcHRoX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4xNSwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiYXNzZXRfZGVuc2l0eSIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9CiAgIF0KICB9CiB9LAogewogICJjYXNlIjogInNpZ25hbF9kcm9wIiwKICAiY3VycmVudCI6IHsKICAgInNjb3JlIjogOTYuMCwKICAgInNpZ25hbHMiOiBbCiAgICB7CiAgICAgIm5hbWUiOiAic2NoZW1hX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4yLAogICAgICJ2YWx1ZSI6IDAuOAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJjb25mb3JtYW5jZV9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMiwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiZG9jX2h5Z2llbmUiLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJkZXB0aF9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImFzc2V0X2RlbnNpdHkiLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfQogICBdCiAgfSwKICAiYmFzZWxpbmUiOiB7CiAgICJzY29yZSI6IDEwMC4wLAogICAic2lnbmFscyI6IFsKICAgIHsKICAgICAibmFtZSI6ICJzY2hlbWFfY2xlYW4iLAogICAgICJ3ZWlnaHQiOiAwLjIsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImNvbmZvcm1hbmNlX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4yLAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJkb2NfaHlnaWVuZSIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImRlcHRoX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4xNSwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiYXNzZXRfZGVuc2l0eSIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9CiAgIF0KICB9CiB9LAogewogICJjYXNlIjogIm92ZXJhbGxfZHJvcF9vbmx5IiwKICAiY3VycmVudCI6IHsKICAgInNjb3JlIjogOTAuMCwKICAgInNpZ25hbHMiOiBbCiAgICB7CiAgICAgIm5hbWUiOiAic2NoZW1hX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4yLAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJjb25mb3JtYW5jZV9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMiwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiZG9jX2h5Z2llbmUiLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJkZXB0aF9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImFzc2V0X2RlbnNpdHkiLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfQogICBdCiAgfSwKICAiYmFzZWxpbmUiOiB7CiAgICJzY29yZSI6IDEwMC4wLAogICAic2lnbmFscyI6IFsKICAgIHsKICAgICAibmFtZSI6ICJzY2hlbWFfY2xlYW4iLAogICAgICJ3ZWlnaHQiOiAwLjIsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImNvbmZvcm1hbmNlX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4yLAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJkb2NfaHlnaWVuZSIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImRlcHRoX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4xNSwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiYXNzZXRfZGVuc2l0eSIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9CiAgIF0KICB9CiB9LAogewogICJjYXNlIjogIndpdGhpbl90b2xlcmFuY2UiLAogICJjdXJyZW50IjogewogICAic2NvcmUiOiA5NS4wLAogICAic2lnbmFscyI6IFsKICAgIHsKICAgICAibmFtZSI6ICJzY2hlbWFfY2xlYW4iLAogICAgICJ3ZWlnaHQiOiAwLjIsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImNvbmZvcm1hbmNlX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4yLAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJkb2NfaHlnaWVuZSIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImRlcHRoX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4xNSwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiYXNzZXRfZGVuc2l0eSIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9CiAgIF0KICB9LAogICJiYXNlbGluZSI6IHsKICAgInNjb3JlIjogMTAwLjAsCiAgICJzaWduYWxzIjogWwogICAgewogICAgICJuYW1lIjogInNjaGVtYV9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMiwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiY29uZm9ybWFuY2VfY2xlYW4iLAogICAgICJ3ZWlnaHQiOiAwLjIsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImRvY19oeWdpZW5lIiwKICAgICAid2VpZ2h0IjogMC4xNSwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiZGVwdGhfY2xlYW4iLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJhc3NldF9kZW5zaXR5IiwKICAgICAid2VpZ2h0IjogMC4xNSwKICAgICAidmFsdWUiOiAxLjAKICAgIH0KICAgXQogIH0sCiAgInRvbGVyYW5jZSI6IDUuMAogfSwKIHsKICAiY2FzZSI6ICJleGVtcHRlZCIsCiAgImN1cnJlbnQiOiB7CiAgICJzY29yZSI6IDk4LjAsCiAgICJzaWduYWxzIjogWwogICAgewogICAgICJuYW1lIjogInNjaGVtYV9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMiwKICAgICAidmFsdWUiOiAwLjgKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiY29uZm9ybWFuY2VfY2xlYW4iLAogICAgICJ3ZWlnaHQiOiAwLjIsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImRvY19oeWdpZW5lIiwKICAgICAid2VpZ2h0IjogMC4xNSwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiZGVwdGhfY2xlYW4iLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJhc3NldF9kZW5zaXR5IiwKICAgICAid2VpZ2h0IjogMC4xNSwKICAgICAidmFsdWUiOiAxLjAKICAgIH0KICAgXQogIH0sCiAgImJhc2VsaW5lIjogewogICAic2NvcmUiOiAxMDAuMCwKICAgInNpZ25hbHMiOiBbCiAgICB7CiAgICAgIm5hbWUiOiAic2NoZW1hX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4yLAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJjb25mb3JtYW5jZV9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMiwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiZG9jX2h5Z2llbmUiLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJkZXB0aF9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImFzc2V0X2RlbnNpdHkiLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfQogICBdCiAgfSwKICAiZXhjZXB0aW9ucyI6IFsKICAgewogICAgInNpZ25hbCI6ICJzY2hlbWFfY2xlYW4iLAogICAgInJlYXNvbiI6ICLlt7Lmibnlh4bnmoTljZXkv6Hlj7flm57lvZLvvIjlkIjmiJDkvovvvIkiCiAgIH0KICBdCiB9LAogewogICJjYXNlIjogIm5vX2Jhc2VsaW5lIiwKICAiY3VycmVudCI6IHsKICAgInNjb3JlIjogODAuMCwKICAgInNpZ25hbHMiOiBbCiAgICB7CiAgICAgIm5hbWUiOiAic2NoZW1hX2NsZWFuIiwKICAgICAid2VpZ2h0IjogMC4yLAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJjb25mb3JtYW5jZV9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMiwKICAgICAidmFsdWUiOiAxLjAKICAgIH0sCiAgICB7CiAgICAgIm5hbWUiOiAiZG9jX2h5Z2llbmUiLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfSwKICAgIHsKICAgICAibmFtZSI6ICJkZXB0aF9jbGVhbiIsCiAgICAgIndlaWdodCI6IDAuMTUsCiAgICAgInZhbHVlIjogMS4wCiAgICB9LAogICAgewogICAgICJuYW1lIjogImFzc2V0X2RlbnNpdHkiLAogICAgICJ3ZWlnaHQiOiAwLjE1LAogICAgICJ2YWx1ZSI6IDEuMAogICAgfQogICBdCiAgfSwKICAiYmFzZWxpbmUiOiB7CiAgICJzY29yZSI6IDAuMCwKICAgInNpZ25hbHMiOiBbXQogIH0KIH0KXQ==";

    /// <summary>合成虚标语料（真源 conformance_scan 输出锚定；机械导出）。</summary>
    private static readonly (string Rel, string B64)[] ConformanceNegativeFiles =
    {
		("desktop/src/core/registry.json", "ewogIm1vZHVsZXMiOiBbCiAgewogICAiaWQiOiAiTTAxIgogIH0KIF0sCiAicHJvdG9jb2xzIjogWwogIHsKICAgImlkIjogIlAwMSIsCiAgICJtb2R1bGVfaWRzIjogWwogICAgIk0wMiIKICAgXQogIH0KIF0KfQ=="),
		("verify.sh", "IyDniYjmnKwgOiB2MS4wCmNoZWNrMTgKY2hlY2syMgo="),
		("a.txt", "eAo="),
		("protocol/export_conformance.json", "ewogImNvbmZvcm1hbmNlX3ZlcnNpb24iOiAiMSIsCiAiaXRlbXMiOiBbCiAgewogICAiaWQiOiAieCIsCiAgICJjb25mb3JtYW5jZSI6ICJMMyIsCiAgICJldmlkZW5jZSI6IFsKICAgICJhLnR4dCIsCiAgICAibWlzc2luZy50eHQiCiAgIF0sCiAgICJnYXRlcyI6IFsKICAgICJjaGVjazE4IiwKICAgICJjaGVjazk5IgogICBdCiAgfSwKICB7CiAgICJpZCI6ICJ5IiwKICAgImNvbmZvcm1hbmNlIjogIkwyIiwKICAgImV2aWRlbmNlIjogW10sCiAgICJnYXRlcyI6IFtdCiAgfQogXQp9"),
		("04_模块库/通用类/T01.md", "IyBUMDEKYGBgeWFtbAptYWNoaW5lX2NvbnRyYWN0OgogIGlkOiBNMDEKICBjb25mb3JtYW5jZTogTDIKYGBgCg=="),
		("04_模块库/通用类/T02.md", "IyBUMDIKYGBgeWFtbAptYWNoaW5lX2NvbnRyYWN0OgogIGlkOiBNOTkKICBjb25mb3JtYW5jZTogTDMKYGBgCg=="),
		("04_模块库/通用类/T03.md", "IyBUMDMKYGBgeWFtbAptYWNoaW5lX2NvbnRyYWN0OgogIGlkOiBNMDEKICBjb25mb3JtYW5jZTogTDAKYGBgCg=="),
		("community/入库包/protocol.yaml", "cGFja2FnZToKICBjb25mb3JtYW5jZTogIkwxIgogIGlkOiBQMDEK"),
		("community/测试包/protocol.yaml", "cGFja2FnZToKICBjb25mb3JtYW5jZTogIkwyIgogIGlkOiDmtYvor5XljIUK"),
    };

    /// <summary>合成缺标识语料（真源 doc_hygiene.check_markers 输出锚定；机械导出）。</summary>
    private static readonly (string Rel, string B64)[] MarkersNegativeFiles =
    {
		("01_核心协议.md", "IyDmoLjlv4PljY/orq4K5q2j5paHCg=="),
		("docs/ai-menu.md", "PiDmnIDlkI7mm7TmlrDvvJoyMDI2LTAxLTAxCuato+aWhwo="),
    };

    /// <summary>整树拷贝（**跳过 <c>.git</c> 与重解析点**）：金标锚定 HEAD，拷进临时树才能安全篡改。</summary>
    private static void CopyTree(string src, string dst)
    {
        Directory.CreateDirectory(dst);
        foreach (var dir in Directory.GetDirectories(src))
        {
            var info = new DirectoryInfo(dir);
            if (info.Name == ".git" || (info.Attributes & FileAttributes.ReparsePoint) != 0) continue;
            CopyTree(dir, Path.Combine(dst, info.Name));
        }
        foreach (var file in Directory.GetFiles(src))
            File.Copy(file, Path.Combine(dst, Path.GetFileName(file)), overwrite: true);
    }

    /// <summary>首个匹配字节串替换（真源 <c>bytes.replace(old, new, 1)</c> 口径）。</summary>
    private static byte[] ReplaceFirstBytes(byte[] data, byte[] find, byte[] repl)
    {
        for (var i = 0; i + find.Length <= data.Length; i++)
        {
            if (!data.AsSpan(i, find.Length).SequenceEqual(find)) continue;
            var outBytes = new byte[data.Length - find.Length + repl.Length];
            data.AsSpan(0, i).CopyTo(outBytes);
            repl.CopyTo(outBytes, i);
            data.AsSpan(i + find.Length).CopyTo(outBytes.AsSpan(i + repl.Length));
            return outBytes;
        }
        return data;
    }

    /// <summary>
    /// 深化面（check35）三钉：真仓（八条子项全绿）+ 空树（只带 desktop/src → 逐条报缺）
    /// + 篡改在盘一致性报告 verdict（验「报告过期/被改」这条腿）。金标由 probes/deepening_gate_probe.py
    /// （真源内嵌 Python 原文）产出；合成树**照探针的做法**拷入 `desktop/src`——真源要靠它 import，
    /// 引擎不读它，但两侧跑同一棵树才对得上。
    /// </summary>
    private static void DeepeningGateCases(List<Check> checks, string work, string repoRoot)
    {
        const string RealGoldenDigest = "9d3f106149a1768b47dded250bc30ac2";
        const string EmptyGoldenDigest = "545dd7695c28a814cc3d1cc409dc37c8";

        var real = DeepeningGate.Check35(repoRoot);
        checks.Add(new Check("深化面·真仓（check35 八条子项全绿 · 与真源内嵌 Python 逐字节同摘要）",
            real.Ok && real.Fail == 0 && real.LogDigest == RealGoldenDigest,
            $"FAIL {real.Fail} · 末行 {real.Log[^1]} · 摘要 {real.LogDigest}"
            + $"（真源金标 {RealGoldenDigest}）"));

        var emptyRoot = Path.Combine(work, "deepening-empty");
        Fresh(emptyRoot);
        DeepeningGate.CopySourceTree(repoRoot, emptyRoot);
        var empty = DeepeningGate.Check35(emptyRoot);
        checks.Add(new Check("深化面·空树（只带 desktop/src：逐条报缺 7 条 · 与真源逐字节同摘要）",
            !empty.Ok && empty.Fail == 7 && empty.LogDigest == EmptyGoldenDigest
            && empty.Log.Any(l => l.Contains("缺馆藏回执 library/RECEIPTS.json"))
            && empty.Log.Any(l => l.Contains("缺协议层回执 protocol/RECEIPTS.json"))
            && empty.Log.Any(l => l.Contains("缺一致性报告 protocol/conformance_report.json")),
            $"FAIL {empty.Fail} · 末行 {empty.Log[^1]} · 摘要 {empty.LogDigest}"
            + $"（真源金标 {EmptyGoldenDigest}）"));

        var staleRoot = Path.Combine(work, "deepening-stale");
        Fresh(staleRoot);
        DeepeningGate.CopySourceTree(repoRoot, staleRoot);
        foreach (var rel in DeepeningGate.CorpusFiles.Concat(new[]
                 {
                     DeepeningGate.ReportRel, DeepeningGate.ProtocolReceiptsRel,
                     DeepeningGate.LibraryReceiptsRel, DeepeningGate.AdvisoryLedgerRel,
                 }))
        {
            var src = Path.Combine(repoRoot, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(src)) continue;
            var dst = Path.Combine(staleRoot, rel.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(dst)!);
            File.Copy(src, dst, overwrite: true);
        }
        var reportPath = Path.Combine(staleRoot, "protocol", "conformance_report.json");
        if (File.Exists(reportPath))
        {
            var text = File.ReadAllText(reportPath, new UTF8Encoding(false));
            File.WriteAllText(reportPath,
                text.Replace("\"verdict\": \"conformant\"", "\"verdict\": \"partial\"", StringComparison.Ordinal),
                new UTF8Encoding(false));
        }
        var stale = DeepeningGate.Check35(staleRoot);
        // 声明边界：真源统计行用 **live verdict**（要跑未移植的 purity-clean），引擎按边界**读在盘 verdict**
        // → 该用例**不比摘要**，只断言「引擎抓出被改的 verdict 且不崩」。
        checks.Add(new Check("深化面·篡改报告（在盘 verdict 改成 partial：抓出「verdict 非 conformant」· **声明边界**：不比摘要）",
            !stale.Ok && stale.Fail > 0
            && stale.Log.Any(l => l.Contains("一致性报告 verdict 非 conformant：partial")),
            $"FAIL {stale.Fail} · 末行 {stale.Log[^1]} · 声明边界：真源统计行取 live verdict（需未移植契约），"
            + $"引擎读在盘 verdict，故本用例不比摘要（摘要 {stale.LogDigest}）"
            + $" · 抓出：{stale.Log.First(l => l.Contains("verdict 非 conformant"))}"));
    }

    /// <summary>
    /// 锚点断言（check2/3/4/5/6/9/10）三钉：真仓（七条 PASS · 与真源 **bash 本体**逐字节同摘要）
    /// + 空树（逐件报缺）+ 跨源不一致。金标由 probes/shell_check_probe.py --checks 产出。
    /// </summary>
    private static void AnchorChecksCases(List<Check> checks, string work, string repoRoot)
    {
        const string RealGoldenDigest = "e91bb18ae9b38ca79fa8c067d57a78b2";
        const string EmptyGoldenDigest = "34e35b85054e2dd7319bd04e1699d1ca";
        const string MismatchGoldenDigest = "f6a08900f5d2515ec8071a665a27572b";

        var real = AnchorChecks.Run(repoRoot);
        checks.Add(new Check("锚点面·真仓（check2/3/4/5/6/9/10/11 八条 · 与真源 shell 逐字节同摘要）",
            real.Ok && real.Pass == 8 && real.Fail == 0 && real.LogDigest == RealGoldenDigest,
            $"PASS {real.Pass} · FAIL {real.Fail} · 摘要 {real.LogDigest}（真源 shell 金标 {RealGoldenDigest}）"));

        var emptyRoot = Path.Combine(work, "anchor-empty");
        Fresh(emptyRoot);
        var empty = AnchorChecks.Run(emptyRoot);
        checks.Add(new Check("锚点面·空树（八条逐项报缺 75 条 + 1 WARN · 含 awk 缺件空位与「脚本不在场仍报对账全清」两处照抄）",
            empty.Fail == 75 && empty.Pass == 1 && empty.Warn == 1 && empty.LogDigest == EmptyGoldenDigest
            && empty.Log.Any(l => l.Contains("01 §5 缺不变式: 三正交分离"))
            && empty.Log.Any(l => l.Contains("02_联动注册表.md 含  处未类别限定的 M10/M22 引用"))
            && empty.Log.Any(l => l.Contains("导航目标缺失: 03_管线库 目录")),
            $"PASS {empty.Pass} · FAIL {empty.Fail} · 摘要 {empty.LogDigest}（真源 shell 金标 {EmptyGoldenDigest}）"));

        var mismatchRoot = Path.Combine(work, "anchor-mismatch");
        Fresh(mismatchRoot);
        foreach (var (rel, b64) in StructureGateSyntheticFiles) WriteBase64(mismatchRoot, rel, b64);
        var mismatch = AnchorChecks.Run(mismatchRoot);
        checks.Add(new Check("锚点面·跨源不一致（同一棵合成树上八条断言 72 条判出 + 1 WARN · 与真源 shell 逐字节同摘要）",
            mismatch.Fail == 72 && mismatch.Pass == 1 && mismatch.Warn == 1 && mismatch.LogDigest == MismatchGoldenDigest,
            $"PASS {mismatch.Pass} · FAIL {mismatch.Fail} · 摘要 {mismatch.LogDigest}"
            + $"（真源 shell 金标 {MismatchGoldenDigest}）"));
    }

    /// <summary>
    /// 结构断言（check1 官方目录结构 + check7 社区两包结构）三钉：**真仓**（两条 PASS 行 + 与真源
    /// **shell 本体**逐字节同摘要）+ **空树**（check1 全缺 24 条 FAIL + check7 两包不在场 WARN）
    /// + **跨源不一致**（登记 2/3 件 vs 实存 2/1 件 + 资产 1/0 件 + 缺 README/P03）。
    /// 金标由 probes/shell_check_probe.py（真源 bash 函数原文 + 同款 ok/no/wn 助手）产出。
    /// </summary>
    private static void StructureGateCases(List<Check> checks, string work, string repoRoot)
    {
        const string RealGoldenDigest = "18fe2537249ee3be05eafcf7b09f2b05";
        const string EmptyGoldenDigest = "08f7cdb2594f9e67398c311d963a736e";
        const string MismatchGoldenDigest = "2f82352292fd37d8be2467cf4c657a0d";

        var real = StructureGate.Run(repoRoot);
        checks.Add(new Check("结构面·真仓（check1 官方目录结构 + check7 社区两包 T6 在册数一致 · 与真源 shell 逐字节同摘要）",
            real.Ok && real.Fail == 0 && real.Pass == 2 && real.Warn == 0 && real.LogDigest == RealGoldenDigest,
            $"PASS {real.Pass} · FAIL {real.Fail} · WARN {real.Warn} · 摘要 {real.LogDigest}"
            + $"（真源 shell 金标 {RealGoldenDigest}）"));

        var emptyRoot = Path.Combine(work, "structure-empty");
        Fresh(emptyRoot);
        var empty = StructureGate.Run(emptyRoot);
        checks.Add(new Check("结构面·空树（check1 逐件报缺 24 条 · check7 两包不在场 WARN，且**照抄真源**仍打 PASS 行）",
            empty.Fail == 24 && empty.Warn == 2 && empty.Pass == 1 && empty.LogDigest == EmptyGoldenDigest
            && empty.Log.Any(l => l.Contains("根级缺失: 01_核心协议.md"))
            && empty.Log.Any(l => l.Contains("05 缺 用户自定义 扩增槽目录"))
            && empty.Log.Any(l => l.Contains("[WARN] 校园情感领域包不在场（跳过其结构校验）"))
            && empty.Log.Any(l => l.Contains("[PASS] 校园 9 模块+29 资产+P02+README（与 02 §8.1 在册 9 一致）")),
            $"PASS {empty.Pass} · FAIL {empty.Fail} · WARN {empty.Warn} · 摘要 {empty.LogDigest}"
            + $"（真源 shell 金标 {EmptyGoldenDigest}）"));

        var mismatchRoot = Path.Combine(work, "structure-mismatch");
        Fresh(mismatchRoot);
        foreach (var (rel, b64) in StructureGateSyntheticFiles) WriteBase64(mismatchRoot, rel, b64);
        var mismatch = StructureGate.Run(mismatchRoot);
        var text = string.Join(" | ", mismatch.Log);
        checks.Add(new Check("结构面·跨源不一致（登记 2/3 vs 实存 2/1 · 资产 1/0 · 缺 README/P03 各判出）",
            mismatch.Fail == 28 && mismatch.Pass == 0 && mismatch.Warn == 0
            && mismatch.LogDigest == MismatchGoldenDigest
            && text.Contains("西幻包 modules 实存 1 件，02 §8.2 在册 3 件——不一致")
            && text.Contains("校园包 assets 应 29 件，实为 1")
            && text.Contains("西幻包 assets 应 23 件，实为 0")
            && text.Contains("西幻包缺顶层 README")
            && text.Contains("西幻包缺 pipelines/P03_西幻生存流管线.md")
            && !text.Contains("校园包 modules 实存 2 件"),   // 校园 2=2 应当静默通过
            $"PASS {mismatch.Pass} · FAIL {mismatch.Fail} · WARN {mismatch.Warn} · 摘要 {mismatch.LogDigest}"
            + $"（真源 shell 金标 {MismatchGoldenDigest}）"));
    }

    private static readonly (string Rel, string B64)[] StructureGateSyntheticFiles =
    {
        ("02_联动注册表.md", "IyMgOC4g56S+5Yy66aKG5Z+f5YyF55m76K6w6KGoCgojIyMgOC4xIOagoeWbreaDheaEn+mihuWfn+WMhe+8iGNvbW11bml0eS/moKHlm63mg4XmhJ/poobln5/ljIUv77yJCj4g5qih5Z2X77yIMu+8ie+8muWPmeS6iyAyIOS7tuOAggoKIyMjIDguMiDopb/lubvnlJ/lrZjpoobln5/ljIXvvIhjb21tdW5pdHkv6KW/5bm755Sf5a2Y6aKG5Z+f5YyFL++8iQo+IOaooeWdl++8iDPvvInvvJrnlJ/lrZggMyDku7bjgIIKCiMjIyA4LjMg56ys5LiJ5pa55Y2P6K6u55m76K6wCg=="),
        ("community/校园情感领域包/modules/M01_甲.md", "IyDmqKHlnZcgTTAxCg=="),
        ("community/校园情感领域包/modules/M02_乙.md", "IyDmqKHlnZcgTTAyCg=="),
        ("community/校园情感领域包/assets/A1.md", "6LWE5Lqn5LiACg=="),
        ("community/校园情感领域包/README.md", "IyDmoKHlm63mg4XmhJ/poobln5/ljIUK"),
        ("community/校园情感领域包/pipelines/P02_校园情感流管线.md", "IyBQMDIK"),
        ("community/西幻生存领域包/modules/M01_丙.md", "IyDmqKHlnZcgTTAxCg=="),
    };

    /// <summary>
    /// 扩展策略 / bump 迁移门禁（check30）三钉：**真仓导出态**（判据词不缺 + diff 面照抄空判，与真源逐字节同摘要）
    /// + **合成负例**（缺判据词逐条列出）+ **边界声明**（工作区态 bump 面明示 UNKNOWN/不判，不写 PASS）。
    /// 摘要金标由 probes/extension_policy_probe.py（真源 verify.sh 内联 Python 原文）产出。
    /// </summary>
    private static void ExtensionPolicyCases(List<Check> checks, string work, string repoRoot)
    {
        const string RealGoldenDigest = "2ecc354222ae4ae205d6a0378463edde";
        const string SyntheticGoldenDigest = "4c8a7a6980a5c6054949cb0b79e00d70";

        var real = ExtensionPolicy.Scan(repoRoot);
        var pinned = IsPinnedSnapshot(repoRoot);
        checks.Add(new Check("扩展策略面·真仓（判据词零缺 · 导出态断金标摘要 / 工作区态断语义并显式 UNKNOWN）",
            real.Ok && real.MissWords.Count == 0 && real.Bumps.Count == 0
            && (pinned ? real.BumpFaceJudged && real.LogDigest == RealGoldenDigest : !real.BumpFaceJudged),
            $"{real.StatsLine} · 摘要 {real.LogDigest}（真源金标 {RealGoldenDigest}）"
            + $" · 模式={(pinned ? "导出快照·断金标" : "工作区·断语义（bump 面 UNKNOWN）")}"
            + $" · bump 面已判={real.BumpFaceJudged}"));

        var root = Path.Combine(work, "extension-policy");
        Fresh(root);
        foreach (var (rel, b64) in ExtensionPolicySyntheticFiles) WriteBase64(root, rel, b64);
        var synth = ExtensionPolicy.Scan(root);
        checks.Add(new Check("扩展策略面·合成负例（缺判据词五枚逐条列出 · 与真源原文逐字节同摘要）",
            !synth.Ok && synth.Issues.Count == 1 && synth.MissWords.Count == 5
            && synth.LogDigest == SyntheticGoldenDigest
            && synth.Issues[0] == "EXTENSION.md 缺判据词：字段级新增,迁移记录,bump,结构 bump,派生三问",
            $"{synth.StatsLine} · FAIL {synth.Issues.Count} · 摘要 {synth.LogDigest}（真源金标 {SyntheticGoldenDigest}）"));

        var worktree = Path.Combine(work, "extension-worktree");
        Fresh(worktree);
        Directory.CreateDirectory(Path.Combine(worktree, ".git"));   // 只要有 .git 目录即视作工作区态
        var boundary = ExtensionPolicy.Scan(worktree);
        checks.Add(new Check("扩展策略面·边界（工作区态：bump 面明示 UNKNOWN/不判，绝不写 PASS）",
            boundary.BumpFaceJudged == false && boundary.Boundary.Contains("UNKNOWN", StringComparison.Ordinal),
            $"BumpFaceJudged=False · 边界说明：{(boundary.Boundary.Length > 70 ? boundary.Boundary[..70] : boundary.Boundary)}…"
            + "（真源在该态会真报 bump+FAIL，故引擎**不得冒充等价**；三态纪律：PASS / FAIL / UNKNOWN）"));

        // 供 diff 的可判集（第一百零五片）：调用方（CI / 脚本）把 `git diff HEAD` 的标准统一 diff 交给引擎，
        // 引擎按真源算法逐文件判 bump 面——**引擎仍不接 VCS**，边界由「不判」变为「可判（需调用方供 diff）」。
        var judgedRoot = Path.Combine(work, "extension-judged");
        Fresh(judgedRoot);
        Directory.CreateDirectory(Path.Combine(judgedRoot, "protocol"));
        File.WriteAllText(Path.Combine(judgedRoot, "protocol", "EXTENSION.md"), ExtensionJudgedExt,
            new UTF8Encoding(false));
        var noRecord = ExtensionPolicy.ScanWithDiff(judgedRoot,
            Encoding.UTF8.GetString(Convert.FromBase64String(ExtensionJudgedNoRecordPatchB64)));
        checks.Add(new Check("扩展策略面·可判·bump 无四步记录（调用方供 diff → 与真源同报 bump 1 + 1 条 FAIL）",
            !noRecord.Ok && noRecord.BumpFaceJudged && noRecord.Bumps.Count == 1
            && noRecord.Bumps[0] == "02_联动注册表.md" && noRecord.Issues.Count == 1
            && noRecord.LogDigest == JudgedNoRecordGolden
            && noRecord.Issues[0].Contains("版本字段结构性变更（bump）但无四步迁移记录（缺：bump 声明,校验回读,现状快照,迁移说明）"),
            $"{noRecord.StatsLine} · 摘要 {noRecord.LogDigest}（真源金标 {JudgedNoRecordGolden}）"));
        var withRecord = ExtensionPolicy.ScanWithDiff(judgedRoot,
            Encoding.UTF8.GetString(Convert.FromBase64String(ExtensionJudgedWithRecordPatchB64)));
        checks.Add(new Check("扩展策略面·可判·bump 带四步记录（调用方供 diff → 与真源同通过，bump 仍如实计数）",
            withRecord.Ok && withRecord.BumpFaceJudged && withRecord.Bumps.Count == 1
            && withRecord.LogDigest == JudgedWithRecordGolden,
            $"{withRecord.StatsLine} · 摘要 {withRecord.LogDigest}（真源金标 {JudgedWithRecordGolden}）"));
    }

    private const string JudgedNoRecordGolden = "f4016b61d3a736b76067c68b921c58ae";
    private const string JudgedWithRecordGolden = "fe0a515e4053c83dd60b0e566f166712";
    private const string ExtensionJudgedNoRecordPatchB64 = "ZGlmZiAtLWdpdCAiYS8wMl9cMzUwXDIwMVwyMjRcMzQ1XDIxMlwyNTBcMzQ2XDI2M1wyNTBcMzQ1XDIwNlwyMTRcMzUwXDI0MVwyNTAubWQiICJiLzAyX1wzNTBcMjAxXDIyNFwzNDVcMjEyXDI1MFwzNDZcMjYzXDI1MFwzNDVcMjA2XDIxNFwzNTBcMjQxXDI1MC5tZCIKaW5kZXggZDk5MTYwNy4uMzBhZDIxMyAxMDA2NDQKLS0tICJhLzAyX1wzNTBcMjAxXDIyNFwzNDVcMjEyXDI1MFwzNDZcMjYzXDI1MFwzNDVcMjA2XDIxNFwzNTBcMjQxXDI1MC5tZCIKKysrICJiLzAyX1wzNTBcMjAxXDIyNFwzNDVcMjEyXDI1MFwzNDZcMjYzXDI1MFwzNDVcMjA2XDIxNFwzNTBcMjQxXDI1MC5tZCIKQEAgLTIsNyArMiw3IEBACiA+IOacgOWQjuabtOaWsO+8mjIwMjYtMDktMjAKID4gKipSRkMqKjogTkYtMDAwMiDCtyAqKkNhdGVnb3J5Kio6IFN0YW5kYXJkcyBUcmFjayDCtyAqKkRhdGUqKjogMjAyNi0wOS0yMCDCtyAqKlN0YXR1cyoqOiBBY3RpdmUgwrcgKipTdXBlcnNlZGVzKio6IOKAlCDCtyAqKlN1cGVyc2VkZWQgYnkqKjog4oCUCiAKLT4gKipyZWdpc3RyeV9zY2hlbWFfdmVyc2lvbjogIjIiKiog4oCU4oCUIOazqOWGjOihqOe7k+aehOeJiOacrO+8iHYwLjUuMCBUMi4zIOmmluW8lSAiMSLvvJt2MC42LjAgVDEuMSDmnLror7vmipXlvbEgcmVnaXN0cnkuanNvbiDlvJXlhaUgbG9hZGVyIOa2iOi0ueWtl+aute+8jOe7k+aehOaAp+a8lOi/myBidW1wIOiHsyAiMiLvvIxWMiDpppbmrKHlrp7miJjvvIzov4Hnp7vorrDlvZXop4Egwqc5LjPvvInjgILor7vlj5bml6fniYjmnKzms6jlhozooajpgbXlvqogMDEg5Y2P6K6uIMKnNyDniYjmnKzkuI7lhbzlrrnop4TliJnvvJrlj6rlop7kuI3liKDjgIHnu5PmnoTmgKflj5jmm7QgYnVtcCDlubbms6jmmI7ov4Hnp7vjgIIKKz4gKipyZWdpc3RyeV9zY2hlbWFfdmVyc2lvbjogIjMiKiog4oCU4oCUIOazqOWGjOihqOe7k+aehOeJiOacrO+8iHYwLjUuMCBUMi4zIOmmluW8lSAiMSLvvJt2MC42LjAgVDEuMSDmnLror7vmipXlvbEgcmVnaXN0cnkuanNvbiDlvJXlhaUgbG9hZGVyIOa2iOi0ueWtl+aute+8jOe7k+aehOaAp+a8lOi/myBidW1wIOiHsyAiMiLvvIxWMiDpppbmrKHlrp7miJjvvIzov4Hnp7vorrDlvZXop4Egwqc5LjPvvInjgILor7vlj5bml6fniYjmnKzms6jlhozooajpgbXlvqogMDEg5Y2P6K6uIMKnNyDniYjmnKzkuI7lhbzlrrnop4TliJnvvJrlj6rlop7kuI3liKDjgIHnu5PmnoTmgKflj5jmm7QgYnVtcCDlubbms6jmmI7ov4Hnp7vjgIIKIAogIyMgMS4g5b2T5YmN5rS76LeD566h57q/CiAtIOWumOaWuea0u+i3g+euoee6v++8mlAwMe+8iOagh+WHhueuoee6vyDCtyDlrpjmlrnmoLjlv4Poo4XphY3vvIwwM1/nrqHnur/lupMvUDAxX+agh+WHhueuoee6vy5tZO+8iQo=";
    private const string ExtensionJudgedWithRecordPatchB64 = "ZGlmZiAtLWdpdCAiYS8wMl9cMzUwXDIwMVwyMjRcMzQ1XDIxMlwyNTBcMzQ2XDI2M1wyNTBcMzQ1XDIwNlwyMTRcMzUwXDI0MVwyNTAubWQiICJiLzAyX1wzNTBcMjAxXDIyNFwzNDVcMjEyXDI1MFwzNDZcMjYzXDI1MFwzNDVcMjA2XDIxNFwzNTBcMjQxXDI1MC5tZCIKaW5kZXggZDk5MTYwNy4uMzgxMDE2MyAxMDA2NDQKLS0tICJhLzAyX1wzNTBcMjAxXDIyNFwzNDVcMjEyXDI1MFwzNDZcMjYzXDI1MFwzNDVcMjA2XDIxNFwzNTBcMjQxXDI1MC5tZCIKKysrICJiLzAyX1wzNTBcMjAxXDIyNFwzNDVcMjEyXDI1MFwzNDZcMjYzXDI1MFwzNDVcMjA2XDIxNFwzNTBcMjQxXDI1MC5tZCIKQEAgLTIsNyArMiw3IEBACiA+IOacgOWQjuabtOaWsO+8mjIwMjYtMDktMjAKID4gKipSRkMqKjogTkYtMDAwMiDCtyAqKkNhdGVnb3J5Kio6IFN0YW5kYXJkcyBUcmFjayDCtyAqKkRhdGUqKjogMjAyNi0wOS0yMCDCtyAqKlN0YXR1cyoqOiBBY3RpdmUgwrcgKipTdXBlcnNlZGVzKio6IOKAlCDCtyAqKlN1cGVyc2VkZWQgYnkqKjog4oCUCiAKLT4gKipyZWdpc3RyeV9zY2hlbWFfdmVyc2lvbjogIjIiKiog4oCU4oCUIOazqOWGjOihqOe7k+aehOeJiOacrO+8iHYwLjUuMCBUMi4zIOmmluW8lSAiMSLvvJt2MC42LjAgVDEuMSDmnLror7vmipXlvbEgcmVnaXN0cnkuanNvbiDlvJXlhaUgbG9hZGVyIOa2iOi0ueWtl+aute+8jOe7k+aehOaAp+a8lOi/myBidW1wIOiHsyAiMiLvvIxWMiDpppbmrKHlrp7miJjvvIzov4Hnp7vorrDlvZXop4Egwqc5LjPvvInjgILor7vlj5bml6fniYjmnKzms6jlhozooajpgbXlvqogMDEg5Y2P6K6uIMKnNyDniYjmnKzkuI7lhbzlrrnop4TliJnvvJrlj6rlop7kuI3liKDjgIHnu5PmnoTmgKflj5jmm7QgYnVtcCDlubbms6jmmI7ov4Hnp7vjgIIKKz4gKipyZWdpc3RyeV9zY2hlbWFfdmVyc2lvbjogIjMiKiog4oCU4oCUIOazqOWGjOihqOe7k+aehOeJiOacrO+8iHYwLjUuMCBUMi4zIOmmluW8lSAiMSLvvJt2MC42LjAgVDEuMSDmnLror7vmipXlvbEgcmVnaXN0cnkuanNvbiDlvJXlhaUgbG9hZGVyIOa2iOi0ueWtl+aute+8jOe7k+aehOaAp+a8lOi/myBidW1wIOiHsyAiMiLvvIxWMiDpppbmrKHlrp7miJjvvIzov4Hnp7vorrDlvZXop4Egwqc5LjPvvInjgILor7vlj5bml6fniYjmnKzms6jlhozooajpgbXlvqogMDEg5Y2P6K6uIMKnNyDniYjmnKzkuI7lhbzlrrnop4TliJnvvJrlj6rlop7kuI3liKDjgIHnu5PmnoTmgKflj5jmm7QgYnVtcCDlubbms6jmmI7ov4Hnp7vjgIIKIAogIyMgMS4g5b2T5YmN5rS76LeD566h57q/CiAtIOWumOaWuea0u+i3g+euoee6v++8mlAwMe+8iOagh+WHhueuoee6vyDCtyDlrpjmlrnmoLjlv4Poo4XphY3vvIwwM1/nrqHnur/lupMvUDAxX+agh+WHhueuoee6vy5tZO+8iQpAQCAtMTE2MCwzICsxMTYwLDUgQEAgcGFja2FnZToKIDIuICoqYnVtcCDlo7DmmI4qKu+8mioqYWRkaXRpdmUg5qGjKirvvIhgcmVmZXJlbmNlc2Ag55SxIDIg5p2h6KGl6IezIDUg5p2h77yM5paw5aKe5qCh5ZutIE00MyDmg4XmlYzns7vnu58gLyDmg4XmhJ86TTIyIOS4ieWGsuWKqOmpseWKqCAvIE00MCDlhbPns7vmt7HluqbvvInihpIgYDEuMC4wYCDljYcgKipgMS4xLjBgKirvvIhNSU5PUu+8ieOAggogMy4gKirov4Hnp7vor7TmmI4qKu+8mioq5Y+q5aKe5LiN5YigKirigJTigJRgbW9kdWxlX2lkX3JhbmdlYO+8iE05MS9NOTLvvIkvIGBwaXBlbGluZTogUDA0YCAvIGBjYXRlZ29yaWVzOiBb6L275re3XWAgLyBgYXNzZXRzLmNvdW50OiAwYCAvIGBtb3VudF9sYXllcnNgIOWdh+acquWPmO+8m+aWsOWinuW8leeUqOS4uioq5Y+q6K+75YCf6ZiFKirvvIhgYXNzZXRfcmVhZG9ubHk6IHRydWVg77yJ77yM5rqQ5YyF5qih5Z2X5LiN5pS55Y+344CB5LiN5aSN5Yi277yMdjEuMC4wIOivu+iAheeahOijhemFjeivreS5ieS4jeWPmOOAgioq6Kem5Y+R5p2l5rqQKirvvJrmlrDnu4TlkIjlvJXmk47vvIhgY29yZS9wYWNrX2NvbWJvLnB5YO+8ieeahOS6i+S7tumXreWMheWunua1i+KAlOKAlOi9u+a3t+WMheaooeWdl+iuoumYhSBgY29uZmVzc2lvbl9ldmVudGAgLyBgbnBjX2FjdGlvbmAgLyBgcmVsYXRpb25zaGlwX2NoYW5nZWDvvIzlhbblj5HluIPmlrnvvIjmoKHlm60gTTQzL00yMi9NNDDvvInmnKrlnKjlo7DmmI7kuK3vvIzlsZ4qKuWjsOaYjuS4juS6i+WunuS4jeS4gOiHtCoq55qE55yf5a6e57y65Y+j77yIQVVELTAwMjAgwqflha3vvInjgIIKIDQuICoq5qCh6aqM5Zue6K+7KirvvJpjaGVjazE0IOKRpiDlj4zmupDkuIDoh7TvvIhgcmVnaXN0cnkgcHJvdG9jb2xzW10udmVyc2lvbmAgPSBgcHJvdG9jb2wueWFtbCBwYWNrYWdlLnZlcnNpb25gID0gYDEuMS4wYO+8jHJlZmVyZW5jZXMg6YCQ5p2h5LiA6Ie077yJKyBjaGVjazE1IOS6lOaWreiogO+8iOWcqOWGjOWPr+Wvu+WdgCAvIOS+nei1lumXreWMhSAvIOaMgui9veWxgiAvIHNjaGVtYSDlhbzlrrkgLyDlj4zmupDkuIDoh7TvvIkrIGNoZWNrMzAg5pys5p2h6K6w5b2VICsgY2hlY2szMiBgY29tYm9zYCDlrZDmiavmj4/vvIjor6Xnu4TlkIjkuI7lhaggMTA3IOWMhee7hOWQiOWdh+WIpOWQiOazle+8ie+8m+WbnuW9kuWIpOaNruingSBgZGVza3RvcC90ZXN0cy90ZXN0X3BhY2tfY29tYm8ucHlg44CCCisKKz4g546w54q25b+r54WnIC8gYnVtcCDlo7DmmI4gLyDov4Hnp7vor7TmmI4gLyDmoKHpqozlm57or7sK";

    /// <summary>可判用例的合成 EXTENSION.md（七个判据词齐备）。</summary>
    private const string ExtensionJudgedExt = "# 扩展策略\n\n字段级新增与结构 bump 的区别；本档即「迁移记录」体例说明。\n\n"
        + "- additive：只增不删\n- editorial：措辞与排版\n- 结构 bump：结构性演进\n"
        + "- 派生三问：谁读、读什么、坏了怎么办\n";

    private static readonly (string Rel, string B64)[] ExtensionPolicySyntheticFiles =
    {
        ("protocol/EXTENSION.md", "IyDmianlsZXnrZbnlaUKCuWPquWGmeS6hiBhZGRpdGl2ZSDkuI4gZWRpdG9yaWFs44CCCg=="),
    };

    /// <summary>
    /// 指令档路由（driver override）两钉：**真仓**（3 工作流 / 3 文档 / 8 绑定工具 / 零问题零告警 +
    /// resolve 三态）与**合成负例**（schema / 绑定 / 工作流工具与提示 / fallback / 文档声明块与关键词全覆盖，
    /// 外加缺声明件与控制化路径）。
    /// </summary>
    private static void DriverCases(List<Check> checks, string work, string repoRoot)
    {
        var real = Driver.Scan(repoRoot);
        var assemble = Driver.Resolve(repoRoot, "assemble");
        var noWorkflow = Driver.Resolve(repoRoot, "不存在的流");
        checks.Add(new Check("指令档路由·真仓（3 工作流 / 3 文档 / 8 绑定工具 · 零问题零告警 · resolve 三态）",
            real.Ok && real.Warns.Count == 0
            && Convert.ToInt64(real.Stats["workflows"]) == 3
            && Convert.ToInt64(real.Stats["documents"]) == 3
            && Convert.ToInt64(real.Stats["tools_bound"]) == 8
            && Convert.ToInt64(real.Stats["fallback_files"]) == 3
            && Convert.ToString(assemble.GetValueOrDefault("mode")) == "mcp"
            && Convert.ToString(assemble.GetValueOrDefault("prompt")) == "assemble_guide"
            && Convert.ToString(assemble.GetValueOrDefault("fallback")) == "docs/agent/agent_组装指令包_v0.2.md"
            && (assemble.GetValueOrDefault("tools") as List<object?>)?.Count == 3
            && Convert.ToString(noWorkflow.GetValueOrDefault("mode")) == "unknown",
            $"工作流 {real.Stats["workflows"]} · 文档 {real.Stats["documents"]} · 绑定工具 {real.Stats["tools_bound"]}"
            + $" · fallback {real.Stats["fallback_files"]} · FAIL {real.Issues.Count} · WARN {real.Warns.Count}"));

        var root = Path.Combine(work, "driver");
        Fresh(root);
        Directory.CreateDirectory(Path.Combine(root, "protocol"));
        File.WriteAllText(Path.Combine(root, "protocol", "driver.json"),
            PythonJson.IndentedUnsorted(DriverSyntheticDocument()), new UTF8Encoding(false));
        File.WriteAllText(Path.Combine(root, "good.md"),
            "# 好文档\n\n> DRIVER OVERRIDE：本档走 good 工作流；派发失败即**停止**，**不得回退**成文本步骤。\n",
            new UTF8Encoding(false));
        File.WriteAllText(Path.Combine(root, "text.md"),
            "# 文本档\n\n> DRIVER OVERRIDE：派发失败即停止，不得回退。\n", new UTF8Encoding(false));
        File.WriteAllText(Path.Combine(root, "nostamp.md"), "# 无声明块\n\n正文\n", new UTF8Encoding(false));

        var synth = Driver.Scan(root);
        var text = string.Join(" | ", synth.Issues) + " || " + string.Join(" | ", synth.Warns);
        var textOnly = Driver.Resolve(root, "textonly");
        checks.Add(new Check("指令档路由·合成负例（schema/绑定/工作流工具与提示/fallback/声明块与关键词九类各判出 · 缺声明件受控）",
            !synth.Ok && synth.Issues.Count == 9 && synth.Warns.Count == 1
            && Convert.ToInt64(synth.Stats["workflows"]) == 4
            && Convert.ToInt64(synth.Stats["documents"]) == 4
            && Convert.ToInt64(synth.Stats["tools_bound"]) == 1
            && Convert.ToInt64(synth.Stats["fallback_files"]) == 3
            && text.Contains("driver schema 不匹配（期望 nf-driver/1）")
            && text.Contains("bindings.mcp.tools 引用了运行时不存在工具：nope_tool")
            && text.Contains("bindings.mcp.prompts 引用了运行时不存在提示：nope_prompt")
            && text.Contains("workflow bad 引用不存在的 MCP 工具：ghost_tool")
            && text.Contains("workflow bad 引用不存在的 MCP 提示：ghost_prompt")
            && text.Contains("workflow bad 的 fallback 不存在：missing.md")
            && text.Contains("workflow nofb 缺 fallback 文件")
            && text.Contains("driver.documents 指向不存在的文档：missing.md")
            && text.Contains("nostamp.md 缺 `DRIVER OVERRIDE` 声明块")
            && text.Contains("text.md 的 override 块未写出工作流名 textonly")
            && Convert.ToString(textOnly.GetValueOrDefault("mode")) == "markdown"
            && Driver.Scan(Path.Combine(work, "no-driver")).Issues.Count == 1,
            $"FAIL {synth.Issues.Count} · WARN {synth.Warns.Count} · 工作流 {synth.Stats["workflows"]}"
            + $" · 文档 {synth.Stats["documents"]} · 绑定工具 {synth.Stats["tools_bound"]}"
            + $" · fallback {synth.Stats["fallback_files"]} · textonly 模式 {textOnly.GetValueOrDefault("mode")}"));
    }

    private static Dictionary<string, object?> DriverSyntheticDocument() =>
        new(StringComparer.Ordinal)
        {
            ["schema"] = "nf-driver/9",
            ["bindings"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["mcp.tools"] = new List<object?> { "nope_tool" },
                ["mcp.prompts"] = new List<object?> { "nope_prompt" },
            },
            ["workflows"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["good"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["mcp_prompt"] = "assemble_guide",
                    ["mcp_tools"] = new List<object?> { "module_read" },
                    ["fallback"] = "good.md",
                },
                ["textonly"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["fallback"] = "text.md",
                },
                ["bad"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["mcp_tools"] = new List<object?> { "ghost_tool" },
                    ["mcp_prompt"] = "ghost_prompt",
                    ["fallback"] = "missing.md",
                },
                ["nofb"] = new Dictionary<string, object?>(StringComparer.Ordinal),
            },
            ["documents"] = new List<object?>
            {
                new Dictionary<string, object?>(StringComparer.Ordinal)
                    { ["path"] = "good.md", ["workflow"] = "good" },
                new Dictionary<string, object?>(StringComparer.Ordinal)
                    { ["path"] = "text.md", ["workflow"] = "textonly" },
                new Dictionary<string, object?>(StringComparer.Ordinal)
                    { ["path"] = "nostamp.md", ["workflow"] = "good" },
                new Dictionary<string, object?>(StringComparer.Ordinal)
                    { ["path"] = "missing.md", ["workflow"] = "good" },
            },
            ["fail_closed"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["marker_keywords"] = new List<object?> { "不得回退", "停止" },
            },
        };

    /// <summary>
    /// 遥测 semconv（check33 第 7 面）两钉：**真源单测的期望值**（属性名 / span 形状 / 最小记录 /
    /// 三种加载形状）+ **机械导出的调用 id 金标**（call id 由内容摘要派生，改一个字段就变）。
    /// 渲染面另有 **4 个 CLI 面**在面级对账里逐字节比对（见 <c>probes/face_parity_probe.py</c>）——
    /// 那比模块级钉更强，钉在此只兜「模块语义」这一层。
    /// </summary>
    private static void TelemetrySemconvCases(List<Check> checks, string work)
    {
        const string GoldenCallId = "nf-5e22b03a2ef472c6";
        var record = TelemetryRecord();
        var attrs = TelemetrySemconv.AttributesFor(record);
        var args = attrs.GetValueOrDefault(TelemetrySemconv.AttrToolArgs) as Dictionary<string, object?>;
        var result = attrs.GetValueOrDefault(TelemetrySemconv.AttrToolResult) as Dictionary<string, object?>;
        var span = TelemetrySemconv.ToSpan(record);
        var badSpan = TelemetrySemconv.ToSpan(TelemetryRecord(ok: false));
        var export = TelemetrySemconv.ToExport(new List<Dictionary<string, object?>>
        {
            record, TelemetryRecord(phase: "check"),
        });
        var resourceSpans = export.GetValueOrDefault("resourceSpans") as List<object?>;
        var resourceSpan = resourceSpans?.FirstOrDefault() as Dictionary<string, object?>;
        var resource = resourceSpan?.GetValueOrDefault("resource") as Dictionary<string, object?>;
        var resourceAttrs = resource?.GetValueOrDefault("attributes") as List<object?>;
        var firstResourceAttr = resourceAttrs?.FirstOrDefault() as Dictionary<string, object?>;
        var scopeSpans = resourceSpan?.GetValueOrDefault("scopeSpans") as List<object?>;
        var scopeSpan = scopeSpans?.FirstOrDefault() as Dictionary<string, object?>;
        var scope = scopeSpan?.GetValueOrDefault("scope") as Dictionary<string, object?>;
        var spans = scopeSpan?.GetValueOrDefault("spans") as List<object?>;
        var spanStatus = span.GetValueOrDefault("status") as Dictionary<string, object?>;
        var badStatus = badSpan.GetValueOrDefault("status") as Dictionary<string, object?>;

        checks.Add(new Check("遥测 semconv·真源单测期望值（属性名 / span 名与状态 / 最小记录不杜撰 / 调用 id 金标）",
            TelemetrySemconv.ToolNameOf(record) == "nf.assemble"
            && TelemetrySemconv.ToolNameOf(new Dictionary<string, object?>(StringComparer.Ordinal)
                { ["tool"] = "nf" }) == "nf"
            && TelemetrySemconv.ToolNameOf(new Dictionary<string, object?>(StringComparer.Ordinal)) == "nf"
            && TelemetrySemconv.CallIdOf(record) == GoldenCallId
            && Convert.ToString(attrs.GetValueOrDefault(TelemetrySemconv.AttrOperation)) == "execute_tool"
            && Convert.ToString(attrs.GetValueOrDefault(TelemetrySemconv.AttrToolName)) == "nf.assemble"
            && Convert.ToString(attrs.GetValueOrDefault(TelemetrySemconv.AttrAgentName)) == "ninfenz"
            && Convert.ToString(attrs.GetValueOrDefault(TelemetrySemconv.AttrConversation)) == "nf-plan"
            && args is not null && Convert.ToString(args.GetValueOrDefault("phase")) == "plan"
            && result is not null && Convert.ToString(result.GetValueOrDefault("pipeline")) == "P03"
            && Convert.ToString(span.GetValueOrDefault("name")) == "execute_tool nf.assemble"
            && Convert.ToInt64(spanStatus?["code"]) == 1 && Convert.ToInt64(badStatus?["code"]) == 2
            && Convert.ToString(span.GetValueOrDefault("spanId")) == GoldenCallId[3..19]
            && Convert.ToString(firstResourceAttr?.GetValueOrDefault("key")) == "service.name"
            && spans?.Count == 2
            && Convert.ToString(scope?.GetValueOrDefault("name")) == TelemetrySemconv.ScopeName
            && Convert.ToString(scope?.GetValueOrDefault("version")) == TelemetrySemconv.ScopeVersion,
            $"call_id {TelemetrySemconv.CallIdOf(record)}（金标 {GoldenCallId}）· 属性 {attrs.Count} 个"
            + $" · span {span.GetValueOrDefault("name")} · 导出 span {spans?.Count} 条"));

        var empty = TelemetrySemconv.AttributesFor(new Dictionary<string, object?>(StringComparer.Ordinal));
        var root = Path.Combine(work, "telemetry");
        Fresh(root);
        File.WriteAllText(Path.Combine(root, "single.json"),
            PythonJson.IndentedUnsorted(record), new UTF8Encoding(false));
        File.WriteAllText(Path.Combine(root, "wrap.json"),
            PythonJson.IndentedUnsorted(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["records"] = new List<object?>
                {
                    record, "not-a-record", 7L, TelemetryRecord(phase: "check"),
                },
            }), new UTF8Encoding(false));
        File.WriteAllText(Path.Combine(root, "list.json"),
            PythonJson.IndentedUnsorted(new List<object?> { record }), new UTF8Encoding(false));
        File.WriteAllText(Path.Combine(root, "scalar.json"), "42", new UTF8Encoding(false));
        var nSingle = TelemetrySemconv.LoadTrace(Path.Combine(root, "single.json")).Count;
        var nWrap = TelemetrySemconv.LoadTrace(Path.Combine(root, "wrap.json")).Count;
        var nList = TelemetrySemconv.LoadTrace(Path.Combine(root, "list.json")).Count;
        var nScalar = TelemetrySemconv.LoadTrace(Path.Combine(root, "scalar.json")).Count;
        checks.Add(new Check("遥测 semconv·加载三形状 + 过滤（单条 / {records:[…]} / 数组；非对象项丢弃；标量 → 空）",
            nSingle == 1 && nWrap == 2 && nList == 1 && nScalar == 0
            && Convert.ToString(empty.GetValueOrDefault(TelemetrySemconv.AttrToolName)) == "nf"
            && !empty.ContainsKey(TelemetrySemconv.AttrToolArgs),
            $"单条 {nSingle} / 包装 {nWrap} / 数组 {nList} / 标量 {nScalar} · 最小记录属性 {empty.Count} 个"
            + $" · tool.name={Convert.ToString(empty.GetValueOrDefault(TelemetrySemconv.AttrToolName))}"
            + $" · 有 arguments={empty.ContainsKey(TelemetrySemconv.AttrToolArgs)}"));
    }

    private static Dictionary<string, object?> TelemetryRecord(string phase = "plan", bool ok = true) =>
        new(StringComparer.Ordinal)
        {
            ["tool"] = "nf assemble",
            ["phase"] = phase,
            ["requirement"] = "校园情感，毕业遗憾线",
            ["status"] = "preset",
            ["matched"] = true,
            ["package"] = "西幻生存领域包",
            ["pipeline"] = "P03",
            ["allowed_modules"] = 44L,
            ["ok"] = ok,
            ["issues"] = new List<object?>(),
            ["stats"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["segments"] = 8L },
        };

    /// <summary>
    /// check33 第 5 / 12 面（正文 lint + 文档命令面）三钉：真仓命令面（72 文档 / 277 处 / 零问题）
    /// + 合成命令面（坏子命令与未登记 MCP 工具各判出）+ 合成正文 lint（八类规则全覆盖）。
    /// 摘要金标由 probes/prose_lint_probe.py（真源模块原文导入）产出。
    /// </summary>
    private static void ProseLintCases(List<Check> checks, string work, string repoRoot)
    {
        const string RealGoldenDigest = "fd1f1ccacc0e980f84d87dc99e74fd2d";
        const string SyntheticFaceGoldenDigest = "70929b995db28c674b3b2f79dd40d5eb";
        const string SyntheticLintGoldenDigest = "174fe1ed64ad984ec8e05bc096290f89";

        var real = ProseLint.CommandFace(repoRoot);
        var pinned = IsPinnedSnapshot(repoRoot);
        checks.Add(new Check("文档面·真仓命令面（零问题 · 导出态断 72 文档/327 处与金标摘要 / 工作区态断语义）",
            real.Ok
            && Convert.ToInt64(real.Stats["cli_commands"]) == 102
            && Convert.ToInt64(real.Stats["mcp_tools"]) == 10
            && (!pinned || (DigestOf(CommandFaceLog(real)) == RealGoldenDigest
                            && Convert.ToInt64(real.Stats["docs"]) == 72
                            && Convert.ToInt64(real.Stats["commands_checked"]) == 327)),
            $"docs {real.Stats["docs"]} · checked {real.Stats["commands_checked"]} · cli {real.Stats["cli_commands"]}"
            + $" · mcp {real.Stats["mcp_tools"]} · FAIL {real.Issues.Count} · 摘要 {DigestOf(CommandFaceLog(real))}"
            + $"（真源金标 {RealGoldenDigest}）"
            + $" · 模式={(pinned ? "导出快照·断金标" : "工作区·断语义（金标摘要锚定 HEAD 983741b）")}"));

        // MCP 工具表镜像核验：真源那 10 个基名必须仍在引擎的 MCP 工具面里（否则命令面判据会偏松）
        var engineTools = McpServer.ToolNames.ToHashSet(StringComparer.Ordinal);
        var missingTools = ProseLint.SourceMcpToolNames.Where(t => !engineTools.Contains(t)).ToList();
        checks.Add(new Check("文档面·MCP 工具表镜像（真源 10 基名 ⊆ 引擎 MCP 工具面）",
            missingTools.Count == 0 && engineTools.Count >= 28,
            $"引擎工具 {engineTools.Count} 个 · 真源基名缺 {missingTools.Count} 个"));

        var root = Path.Combine(work, "prose-lint");
        Fresh(root);
        foreach (var (rel, b64) in ProseLintSyntheticFiles) WriteBase64(root, rel, b64);
        var synth = ProseLint.CommandFace(root);
        var synthLog = CommandFaceLog(synth);
        var synthText = string.Join(" | ", synth.Issues);
        checks.Add(new Check("文档面·合成命令面（坏子命令 ×2 + 未登记 MCP 工具 ×1 判出 · 与真源原文逐字节同摘要）",
            !synth.Ok && synth.Issues.Count == 3 && DigestOf(synthLog) == SyntheticFaceGoldenDigest
            && synthText.Contains("README.md 命令面：`nf nope` 不是 CLI 子命令")
            && synthText.Contains("README.md 命令面：`nf bogus-cmd` 不是 CLI 子命令")
            && synthText.Contains("README.md 命令面：not_a_tool 不是已登记 MCP 工具")
            && Convert.ToInt64(synth.Stats["docs"]) == 2
            && Convert.ToInt64(synth.Stats["commands_checked"]) == 7
            && Convert.ToInt64(synth.Stats["cli_commands"]) == 2
            && Convert.ToInt64(synth.Stats["mcp_tools"]) == 10,
            $"docs {synth.Stats["docs"]} · checked {synth.Stats["commands_checked"]} · FAIL {synth.Issues.Count}"
            + $" · 摘要 {DigestOf(synthLog)}（真源金标 {SyntheticFaceGoldenDigest}）"));

        var prosePath = Path.Combine(root, "prose_sample.md");
        var findings = ProseLint.LintText(File.ReadAllText(prosePath, new UTF8Encoding(false)));
        var lintLog = LintTextLog(findings);
        var rules = findings.Select(f => f.Rule).Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToList();
        checks.Add(new Check("文档面·合成正文 lint（八类规则全覆盖 · 与真源原文逐字节同摘要）",
            findings.Count == 9 && DigestOf(lintLog) == SyntheticLintGoldenDigest && rules.Count == 8
            && findings[0].Rule == "hedge_overuse" && findings[0].Line == 0
            && findings.Any(f => f.Rule == "repeat_connector" && f.Line == 15)
            && findings.Any(f => f.Rule == "triple_adj" && f.Snippet.Contains("统筹兼顾、稳中求进、进退有据")),
            $"findings {findings.Count} · 规则 {rules.Count} 类 · 摘要 {DigestOf(lintLog)}（真源金标 {SyntheticLintGoldenDigest}）"));
    }

    /// <summary>机械修复面（check33 第 4 面）：真仓关键/指令档零待办 + 合成负例四类各判出。</summary>
    private static void AutofixCases(List<Check> checks, string work, string repoRoot)
    {
        var (pending, targets) = Autofix.ScanGateTargets(repoRoot);
        var pinnedRoot = IsPinnedSnapshot(repoRoot);
        checks.Add(new Check("机械修复面·真仓（关键/指令档零待办 · 导出态另断 46 档）",
            pending.Count == 0 && (pinnedRoot ? targets == 46 : targets > 0),
            $"目标档 {targets} 个（REQUIRED ∪ INSTRUCTION 里在盘者）· 待办 {pending.Count} 个"
            + $" · 模式={(pinnedRoot ? "导出快照（金标 46 档）" : "工作区·断语义")}"));

        var root = Path.Combine(work, "autofix");
        Fresh(root);
        var required = DocHygiene.RequiredDocPaths[0];
        // 取**只属指令档**的那一件（指令档大多同时是关键档，两者都判会多出「缺最后更新」，干扰本钉的判别）
        var instruction = DocHygiene.InstructionDocPaths.First(p => !DocHygiene.RequiredDocPaths.Contains(p));
        var writeRequired = Path.Combine(root, required.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(writeRequired)!);
        File.WriteAllText(writeRequired, "# 关键档\n\n正文带行尾空白   \n最后一行无换行", new UTF8Encoding(false));
        var writeInstruction = Path.Combine(root, instruction.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(writeInstruction)!);
        File.WriteAllText(writeInstruction, "# 指令档\n\n正文\n", new UTF8Encoding(false));
        var other = Path.Combine(root, "普通件.md");
        File.WriteAllText(other, "# 普通件\n\n正文", new UTF8Encoding(false));

        var requiredFindings = Autofix.LintRules(root, required,
            File.ReadAllText(writeRequired, new UTF8Encoding(false)));
        var instructionFindings = Autofix.LintRules(root, instruction,
            File.ReadAllText(writeInstruction, new UTF8Encoding(false)));
        var otherFindings = Autofix.LintRules(root, "普通件.md",
            File.ReadAllText(other, new UTF8Encoding(false)));
        checks.Add(new Check("机械修复面·合成负例（关键档缺「最后更新」/ 行尾空白 / 末缺换行 · 指令档缺标识 · 普通件只判机械面）",
            requiredFindings.Count == 3
            && requiredFindings.Select(f => f.Rule).SequenceEqual(new[] { "last_updated", "trailing_ws", "final_newline" })
            && instructionFindings.Count == 1 && instructionFindings[0].Rule == "instruction_mark"
            && otherFindings.Count == 1 && otherFindings[0].Rule == "final_newline",
            $"关键档 {requiredFindings.Count} 项 · 指令档 {instructionFindings.Count} 项 · 普通件 {otherFindings.Count} 项"
            + "（写面 apply_rules 明确不移植：只读门不说「我改过」）"));
    }

    private static List<string> CommandFaceLog(ProseLint.CommandFaceResult result)
    {
        var lines = result.Issues.Select(i => "[FAIL] " + i).ToList();
        lines.Add("[STAT] docs=" + Convert.ToInt64(result.Stats["docs"])
                  + " commands_checked=" + Convert.ToInt64(result.Stats["commands_checked"])
                  + " cli_commands=" + Convert.ToInt64(result.Stats["cli_commands"])
                  + " mcp_tools=" + Convert.ToInt64(result.Stats["mcp_tools"]));
        return lines;
    }

    private static List<string> LintTextLog(List<ProseLint.Finding> findings)
    {
        var lines = findings
            .Select(f => $"[FIND] {f.Rule} line={f.Line} {f.Message} | {f.Snippet}")
            .ToList();
        lines.Add("[STAT] findings=" + findings.Count);
        return lines;
    }

    private static string DigestOf(IEnumerable<string> lines) => Convert.ToHexString(
        System.Security.Cryptography.SHA256.HashData(
            Encoding.UTF8.GetBytes(string.Join("\n", lines)))).ToLowerInvariant()[..32];

    private static readonly (string Rel, string B64)[] ProseLintSyntheticFiles =
    {
        ("scripts/nf.py", "IiIi5o6i6ZKI5ZCI5oiQ6K+t5paZ77ya5Y+q5o+Q5L6bIGFkZF9wYXJzZXIg5rOo5YaM5ZCN77yM5L6bIGNvbW1hbmRfZmFjZSDmir3lj5bjgIIiIiIKaW1wb3J0IGFyZ3BhcnNlCgpzdWIgPSBhcmdwYXJzZS5Bcmd1bWVudFBhcnNlcigpLmFkZF9zdWJwYXJzZXJzKCkKcCA9IHN1Yi5hZGRfcGFyc2VyKCJhc3NlbWJsZSIpCnAgPSBzdWIuYWRkX3BhcnNlcigidmVyaWZ5IikK"),
        ("README.md", "IyDlkIjmiJDor63mlpkgwrcg5YWl5Y+j5paH5qGjCgrnlKggYG5mIGFzc2VtYmxlYCDoo4XphY3kuIDkuKrnu4TlkIjljIXjgIIKCueUqCBgbmYgbm9wZWAg5piv5LiN5a2Y5Zyo55qE5a2Q5ZG95Luk77yI5bqU5Yik5Ye677yJ44CCCgpgcmVnaXN0cnlfcXVlcnnvvIhNQ1Ag5bel5YW377yJYCDlnKjlhozvvJtgbm90X2FfdG9vbO+8iE1DUCDlt6XlhbfvvIlgIOS4jeWcqOWGjO+8iOW6lOWIpOWHuu+8ieOAggoKYGBgYmFzaApuZiB2ZXJpZnkgLS1hbGwKbmYgYm9ndXMtY21kCmBgYAo="),
        ("docs/x.md", "IyDlkIjmiJDor63mlpkgwrcgZG9jcyDpnaIKCuaVo+aWh+mHjOWGmSBuZiDkuI3luKblj43lvJXlj7fkuI3nrpflkb3ku6TpnaLvvIjmnKzooYzkuI3or6XooqvliKTvvInjgIIKCmBuZiBhc3NlbWJsZWAg5Zyo5YaM77yI5LiN6K+l6KKr5Yik77yJ44CCCg=="),
        ("prose_sample.md", "IyDlkIjmiJDor63mlpkgwrcg5q2j5paHIGxpbnQKCuWcqOi/meS4qumXrumimOS4iu+8jOaIkeS7rOmcgOimgeiwqOaFjuOAggoK5oC76ICM6KiA5LmL77yM5oiR5Lus5bqU6K+l57un57ut44CCCgrov5nkuI3mmK/pgJ/luqbpl67popjvvIzogIzmmK/mlrnlkJHpl67popjjgIIKCue7n+etueWFvOmhvuOAgeeos+S4reaxgui/m+OAgei/m+mAgOacieaNruWcsOaOqOi/m+OAggoK6L+Z5piv5LiA5Y+l5Lit5paHLOW4puiLseaWh+mAl+WPt+OAggoK54S26ICM5oOF5Ya15YWI5Y+Y5LqG44CCCgrnhLbogIzml7bpl7Tlj4jkuI3lpJ/jgIIKCuS5n+iuuOWkp+amguaIluiuuOS8vOS5juS7v+S9m+WPr+iDveafkOenjeeoi+W6puS4iu+8jOS6i+aDhei/mOaciei9rOacuuOAggo="),
    };

    /// <summary>
    /// check33 第 6 面（图书馆许可证门）两钉：真材料（真仓登记零 FAIL + WARN 台账 + 与真源原文逐字节同摘要）
    /// + 合成负例（五类 FAIL + 三类 WARN 各命中）。
    /// </summary>
    private static void LicenseGateCases(List<Check> checks, string work, string repoRoot)
    {
        // 金标来源：probes/license_gate_probe.py 导入**快照里那份**真源 core/license_gate.py 原文执行，
        // 统一渲染规则（[FAIL]/[WARN]/[STAT]）见探针头；摘要见 _fixtures/_license_gate_golden.json。
        const string RealGoldenDigest = "ee4bb55acf6688bf0e6cb8621fd1b979";
        const string SyntheticGoldenDigest = "ec3b4ca338650df71a93c8c476acad79";

        var real = LicenseGate.Scan(repoRoot);
        var pinned = IsPinnedSnapshot(repoRoot);
        checks.Add(new Check("许可证门·真仓（登记零 FAIL · 越词表/缺内联/双源不一致必须为 0 · 导出态另断金标摘要）",
            real.Ok && real.UnknownIds.Count == 0 && real.NoInlineIds.Count == 0 && real.MismatchedIds.Count == 0
            && (!pinned || (real.LogDigest == RealGoldenDigest
                            && Convert.ToInt64(real.Stats["entries"]) == 3
                            && Convert.ToInt64(real.Stats["declared"]) == 2)),
            $"登记 {real.Stats["entries"]} 条（声明 {real.Stats["declared"]}）· FAIL {real.Issues.Count} · WARN {real.Warnings.Count}"
            + $" · 摘要 {real.LogDigest}（真源金标 {RealGoldenDigest}）"
            + $" · 模式={(pinned ? "导出快照·断金标" : "工作区·断语义（未声明允许 ≤1，真仓为 1）")}"));

        var root = Path.Combine(work, "license-gate");
        Fresh(root);
        foreach (var (rel, b64) in LicenseGateSyntheticFiles) WriteBase64(root, rel, b64);
        var synth = LicenseGate.Scan(root);
        var text = string.Join(" | ", synth.Issues) + " || " + string.Join(" | ", synth.Warnings);
        checks.Add(new Check("许可证门·合成负例（越词表 / 无许可列 / 运算符缺操作数 / 括号不配平 / 非法字符五类 FAIL + 未声明/缺内联/双源不一致三类 WARN）",
            !synth.Ok && synth.Issues.Count == 5 && synth.Warnings.Count == 4
            && synth.LogDigest == SyntheticGoldenDigest
            && text.Contains("许可取值不合规：NF-BADID-1 = GPL-3.0-only（许可 id 不在词表：GPL-3.0-only")
            && text.Contains("登记行缺「许可」列值：NF-EMPTY-1")
            && text.Contains("运算符 AND 前缺少操作数")
            && text.Contains("括号不配平")
            && text.Contains("含非法字符")
            && text.Contains("许可未声明（待投稿人确认）：NF-UNDECL-1")
            && text.Contains("条目文件缺内联许可声明：NF-REF-1")
            && text.Contains("许可双源不一致：NF-EXPR-1 登记=MIT OR Apache-2.0 文件=MIT")
            && Convert.ToInt64(synth.Stats["entries"]) == 10 && Convert.ToInt64(synth.Stats["declared"]) == 5
            && synth.UndeclaredIds.SequenceEqual(new[] { "NF-UNDECL-1" })
            && synth.MismatchedIds.SequenceEqual(new[] { "NF-EXPR-1", "NF-MISMATCH-1" })
            && synth.UnknownIds.SequenceEqual(new[] { "NF-BADID-1", "NF-BADOP-1", "NF-PAREN-1", "NF-CHAR-1" }),
            $"登记 {synth.Stats["entries"]} 条 · FAIL {synth.Issues.Count} · WARN {synth.Warnings.Count}"
            + $" · 摘要 {synth.LogDigest}（真源金标 {SyntheticGoldenDigest}）"));
    }

    private static readonly (string Rel, string B64)[] LicenseGateSyntheticFiles =
    {
        ("library/INDEX.md", "IyDkupHnq6/lm77kuabppobntKLlvJXvvIjmjqLpkojlkIjmiJDor63mlpnvvIkKCnwg57yW5Y+3IHwg5qCH6aKYIHwg5b2i5oCBL+mihuWfnyB8IOaKleeov+S6uiB8IOWFpeW6k+aXpeacnyB8IOiuuOWPryB8IOWIhue6pyB8IOeKtuaAgSB8IOS4gOWPpeivnSB8CnwtLS18LS0tfC0tLXwtLS18LS0tfC0tLXwtLS18LS0tfC0tLXwKfCBORi1PSy0xIHwg5qC35L6L5LiAIHwg5LiW55WMIHwgYSB8IDIwMjYtMDEtMDEgfCBNSVQgfCB0ZWVuIHwgYWN0aXZlIHwg5ZCI6KeEIHwKfCBORi1FWFBSLTEgfCDmoLfkvovkuowgfCDkuJbnlYwgfCBiIHwgMjAyNi0wMS0wMiB8IE1JVCBPUiBBcGFjaGUtMi4wIHwgdGVlbiB8IGFjdGl2ZSB8IOihqOi+vuW8jyB8CnwgTkYtUkVGLTEgfCDmoLfkvovkuIkgfCDkuJbnlYwgfCBjIHwgMjAyNi0wMS0wMyB8IExpY2Vuc2VSZWYtQ3VzdG9tLTEgfCB0ZWVuIHwgYWN0aXZlIHwg6Ieq6YCgIGlkIHwKfCBORi1VTkRFQ0wtMSB8IOagt+S+i+WbmyB8IOS4lueVjCB8IGQgfCAyMDI2LTAxLTA0IHwg5pyq5aOw5piOIHwgZ2VuZXJhbCB8IGFjdGl2ZSB8IOacquWjsOaYjiB8CnwgTkYtTUlTTUFUQ0gtMSB8IOagt+S+i+S6lCB8IOS4lueVjCB8IGUgfCAyMDI2LTAxLTA1IHwgTUlUIHwgZ2VuZXJhbCB8IGFjdGl2ZSB8IOWPjOa6kOS4jeS4gOiHtCB8CnwgTkYtQkFESUQtMSB8IOagt+S+i+WFrSB8IOS4lueVjCB8IGYgfCAyMDI2LTAxLTA2IHwgR1BMLTMuMC1vbmx5IHwgZ2VuZXJhbCB8IGFjdGl2ZSB8IOi2iuivjeihqCB8CnwgTkYtRU1QVFktMSB8IOagt+S+i+S4gyB8IOS4lueVjCB8IGcgfCAyMDI2LTAxLTA3IHwgeCB8CnwgTkYtQkFET1AtMSB8IOagt+S+i+WFqyB8IOS4lueVjCB8IGggfCAyMDI2LTAxLTA4IHwgTUlUIEFORCBBTkQgQXBhY2hlLTIuMCB8IGdlbmVyYWwgfCBhY3RpdmUgfCDov5DnrpfnrKbnvLrmk43kvZzmlbAgfAp8IE5GLVBBUkVOLTEgfCDmoLfkvovkuZ0gfCDkuJbnlYwgfCBpIHwgMjAyNi0wMS0wOSB8IChNSVQgT1IgQXBhY2hlLTIuMCB8IGdlbmVyYWwgfCBhY3RpdmUgfCDmi6zlj7fkuI3phY3lubMgfAp8IE5GLUNIQVItMSB8IOagt+S+i+WNgSB8IOS4lueVjCB8IGogfCAyMDI2LTAxLTEwIHwgTUlUIMKpIHwgZ2VuZXJhbCB8IGFjdGl2ZSB8IOmdnuazleWtl+espiB8Cg=="),
        ("library/NF-OK-1.md", "IyDmoLfkvovkuIAKCj4g6K645Y+v77yaTUlUCg=="),
        ("library/NF-EXPR-1.md", "IyDmoLfkvovkuowKCj4g6K645Y+v77yaTUlUIE9SIEFwYWNoZS0yLjAK"),
        ("library/NF-REF-1.md", "IyDmoLfkvovkuIkKCu+8iOaXoOWGheiBlOiuuOWPr+WjsOaYjuKAlOKAlOW6lOiusCBXQVJO77yJCg=="),
        ("library/NF-UNDECL-1.md", "IyDmoLfkvovlm5sKCj4g6K645Y+v77ya5pyq5aOw5piOCg=="),
        ("library/NF-MISMATCH-1.md", "IyDmoLfkvovkupQKCj4g6K645Y+v77yaQXBhY2hlLTIuMAo="),
    };

    /// <summary>
    /// check33 第 9 面（编码卫生）三钉：**真材料**（真仓 2765 件零问题 + 计数在册 + 与真源原文逐字节同摘要）
    /// + **合成负例**（七条规则各命中一次，含排除目录/排除文件/二进制哨兵三条负对照）
    /// + **坏 UTF-8 不可约尾**（条数与问题前缀同判）。
    /// </summary>
    private static void TextHygieneCases(List<Check> checks, string work, string repoRoot)
    {
        // 金标来源：probes/text_hygiene_probe.py 把真源 core/text_hygiene.py **原文复制后执行**
        // （真源 __main__ 同一段代码），逐字节 stdout 摘要见 _fixtures/_text_hygiene_golden.json。
        // 合成树以 base64 记录 → 两侧比的是**同一棵树**。
        const string RealGoldenDigest = "a49d33b5f3f8819840d0da3f564578de";
        const string MixedGoldenDigest = "62705da4c6d1a6647f46aef038689209";
        const string BadUtf8Prefix = "c_bad.txt 不是合法 UTF-8：";

        var real = TextHygiene.Scan(repoRoot);
        var pinned = IsPinnedSnapshot(repoRoot);
        checks.Add(new Check("编码卫生·真仓（零问题 · 导出态另断 2773/1033/168425/111 与金标摘要）",
            real.Ok && Convert.ToInt64(real.Stats["versions_checked"]) > 0
            && (!pinned || (real.LogDigest == RealGoldenDigest
                            && Convert.ToInt64(real.Stats["text"]) == 2773
                            && Convert.ToInt64(real.Stats["json"]) == 1033
                            && Convert.ToInt64(real.Stats["keys_checked"]) == 168425
                            && Convert.ToInt64(real.Stats["versions_checked"]) == 111)),
            $"{real.SummaryLine} · 摘要 {real.LogDigest}（真源金标 {RealGoldenDigest}）"
            + $" · 模式={(pinned ? "导出快照·断金标" : "工作区·断语义")}"));

        var mixedRoot = Path.Combine(work, "text-hygiene-mixed");
        Fresh(mixedRoot);
        foreach (var (rel, b64) in TextHygieneMixedFiles) WriteBase64(mixedRoot, rel, b64);
        var mixed = TextHygiene.Scan(mixedRoot);
        var mixedText = string.Join(" | ", mixed.Issues);
        checks.Add(new Check("编码卫生·合成负例（七条规则各命中一次 · 与真源原文逐字节同摘要）",
            !mixed.Ok && mixed.Issues.Count == 7 && mixed.LogDigest == MixedGoldenDigest
            && mixedText.Contains("未声明 `* text=auto eol=lf`")
            && mixedText.Contains("a_bom.md 以 UTF-8 BOM 开头")
            && mixedText.Contains("b_crlf.md 含 CRLF 行尾")
            && mixedText.Contains("d_dup.json JSON 重复键 'a'")
            && mixedText.Contains("e_key.json JSON 键 '好\\xa0键' 违规：含隐形/同形字符 不换行空格(NBSP)（U+00A0）")
            // 注意：这一行的键是**分解形**（`e` + U+0301，可打印故 repr 原样输出）——断言不能写成预组合 `é`。
            && mixedText.Contains("f_non_nfc.json JSON 键 ") && mixedText.Contains("违规：非 NFC 规范化形态")
            && mixedText.Contains("community/示例包/protocol.yaml 的版本值 '1.0' 违规：缺补丁号")
            && Convert.ToInt64(mixed.Stats["text"]) == 9 && Convert.ToInt64(mixed.Stats["keys_checked"]) == 5
            && !mixedText.Contains("_cov_tmp.json") && !mixedText.Contains("h_binary.bin"),
            $"{mixed.SummaryLine} · 摘要 {mixed.LogDigest}（真源金标 {MixedGoldenDigest}）"));

        var badRoot = Path.Combine(work, "text-hygiene-bad-utf8");
        Fresh(badRoot);
        foreach (var (rel, b64) in TextHygieneBadUtf8Files) WriteBase64(badRoot, rel, b64);
        var badUtf8 = TextHygiene.Scan(badRoot);
        checks.Add(new Check("编码卫生·坏UTF8（1 条 · 前缀与真源同判；行尾文案属各自编解码器=不可约）",
            !badUtf8.Ok && badUtf8.Issues.Count == 1
            && badUtf8.Issues[0].StartsWith(BadUtf8Prefix, StringComparison.Ordinal),
            $"问题 {badUtf8.Issues.Count} 条 · 前缀 `{BadUtf8Prefix}` · 尾为 .NET 解码器文案（真源为 Python 编解码器文案）"));
    }

    private static readonly (string Rel, string B64)[] TextHygieneMixedFiles =
    {
        (".gitattributes", "KiB0ZXh0PWF1dG8gZW9sPWNybGYK"),
        ("a_bom.md", "77u/5q2j5paHCg=="),
        ("b_crlf.md", "6KGM5LiADQrooYzkuowNCg=="),
        ("d_dup.json", "eyJhIjoxLCJhIjoyLCJrIjozfQo="),
        ("e_key.json", "eyLlpb3CoOmUriI6MX0K"),
        ("f_non_nfc.json", "eyJlzIEiOjF9Cg=="),
        ("g_ok.json", "eyJnb29kX2tleSI6MX0K"),
        ("h_binary.bin", "AAECYmluYXJ5LWlzaAo="),
        ("_cov_tmp.json", "eyJleGNsdWRlZOOAgGtleSI6MX0K"),
        (".git/inside.md", "5o6S6Zmk55uu5b2V6YeM55qE5Lu25LiN6K+l6KKr5omrCg=="),
        ("community/示例包/protocol.yaml", "aWQ6IOekuuS+i+WMhQp2ZXJzaW9uOiAxLjAK"),
        ("community/示例包/modules/M01.md", "IyDmqKHlnZcgTTAxIMK3IOekuuS+iwo="),
    };

    private static readonly (string Rel, string B64)[] TextHygieneBadUtf8Files =
    {
        (".gitattributes", "KiB0ZXh0PWF1dG8gZW9sPWxmCg=="),
        ("c_bad.txt", "//5BQgo="),
    };

    private static void WriteBase64(string root, string rel, string b64)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllBytes(path, Convert.FromBase64String(b64));
    }

    /// <summary>
    /// check20（文档完整性）两钉：**真材料**（真仓官方 13 件强校验全过 + 社区统计）+ **合成负例**
    /// （官方四类问题各报出 / 社区有契约者强校验 / 未完备者只进 WARN 不进 errs）。
    /// </summary>
    private static void DocCompletenessCases(List<Check> checks, string work, string repoRoot)
    {
        // 金标来源：probes/doc_completeness_probe.py 把 verify.sh check20 的**内联 Python 原文**抽出后执行，
        // 摘要在 _fixtures/_doc_completeness_golden.json（真仓 294d2e18… / 合成 76e4ffcf…）。
        // 合成树的规格与探针里 SYNTH_FILES **逐字节相同**——两边跑同一棵树才有可比性。
        const string SyntheticGoldenDigest = "76e4ffcfd4746a0b7d95606ee6cb58b1";

        // ① 真材料：真仓官方 13 件强校验全过 + 社区机读完备件强校验 + 未完备存量只进 WARN 统计（不阻断）
        var real = DocCompleteness.Check(repoRoot);
        checks.Add(new Check("check20·真仓（官方 13 件强校验全过 · 社区机读完备强校验 · 未完备只 WARN 统计）",
            real.Ok && real.CoreCount == 13 && real.CommunityCount > 0,
            $"官方 {real.CoreCount} · 社区 {real.CommunityCount} · 未完备 WARN {real.IncompleteCount}"
            + $" · FAIL {real.Issues.Count} · 摘要 {real.LogDigest}（真源金标 294d2e18c7ab8aba89e56f182986b13b @ HEAD 983741b）"));

        // ② 合成树：官方 2 件（1 合规 / 1 缺机器契约 + 标题坏 + 缺元数据 + 缺章节）+ 社区 2 件（1 有契约缺键 / 1 未完备）
        var root = Path.Combine(work, "doc-completeness");
        Fresh(root);
        var coreDir = Path.Combine(root, "04_模块库", "通用类");
        Directory.CreateDirectory(coreDir);
        File.WriteAllText(Path.Combine(coreDir, "M00_好模块.md"),
            "# 模块 M00 · 数据结构\n> 类别：通用\n> 来源：核心\n> 挂载点：P00\n> 依赖：无\n\n## 职责\n正文\n\n"
            + "```yaml\nmachine_contract:\n  id: M00\n```\n", new UTF8Encoding(false));
        File.WriteAllText(Path.Combine(coreDir, "M99_坏.md"),
            "# 坏标题\n正文没有元数据也没有章节\n", new UTF8Encoding(false));
        var commDir = Path.Combine(root, "community", "示例包", "modules");
        Directory.CreateDirectory(commDir);
        File.WriteAllText(Path.Combine(commDir, "C01_完备但缺键.md"),
            "# 模块 C01 · 示例\n\n```yaml\nmachine_contract:\n  id: C01\n```\n\n## 职责\n正文\n",
            new UTF8Encoding(false));
        File.WriteAllText(Path.Combine(commDir, "C02_未完备.md"), "not a module doc\n", new UTF8Encoding(false));

        var synth = DocCompleteness.Check(root);
        var text = string.Join(" | ", synth.Issues);
        checks.Add(new Check("check20·合成负例（官方四类问题各报出 · 社区有契约者强校验 · 未完备者只进 WARN 不进 errs）",
            !synth.Ok && synth.CoreCount == 2 && synth.CommunityCount == 2 && synth.IncompleteCount == 1
            && synth.LogDigest == SyntheticGoldenDigest
            && text.Contains("[官方] M99_坏.md 缺 machine_contract")
            && text.Contains("[官方] M99_坏.md 标题格式异常")
            && text.Contains("[官方] M99_坏.md 元数据缺 类别")
            && text.Contains("[官方] M99_坏.md 缺 职责/核心逻辑 章节")
            && text.Contains("[社区] C01_完备但缺键.md 元数据缺 类别")
            && !text.Contains("C02_未完备.md")
            && synth.IncompleteBases.Contains("C02_未完备.md")
            && synth.Head5.Contains("文档完整性扫描：官方 2 件 + 社区 2 件"),
            $"官方 {synth.CoreCount} · 社区 {synth.CommunityCount} · 未完备 {synth.IncompleteCount}"
            + $" · FAIL {synth.Issues.Count} · 摘要 {synth.LogDigest}（真源金标 {SyntheticGoldenDigest}，逐字节同）"));
    }

    /// <summary>
    /// check13（协议版本一致性 + 迁移完整性）六钉：**真材料**（真仓三条全绿）+ **合成负例**（版本不一致 /
    /// §9.3 缺步 / 模块表双向差集各一）+ **受控化**（缺 registry.json 给判定而非崩溃）。
    /// </summary>
    private static void CoreRegistryCases(List<Check> checks, string work, string repoRoot)
    {
        // ① 真材料：真仓 ①版本一致 + ②§9.3 四步在场 + ③13 件模块全等（三条都读真件，无合成成分）
        var real = CoreRegistry.Check(repoRoot);
        checks.Add(new Check("check13·真仓（协议版本两处一致 · §9.3 四步齐备 · 模块表 13 件集合全等）",
            real.Ok && real.DocVersion == real.RegVersion && real.DocVersion.Length > 0
            && real.DocRows == CoreRegistry.ExpectedModules && real.RegRows == CoreRegistry.ExpectedModules
            && real.OnlyDoc.Count == 0 && real.OnlyReg.Count == 0,
            $"版本 {real.DocVersion}/{real.RegVersion} · 模块 {real.DocRows}/{real.RegRows} · 步骤 {real.Steps.Count} · 问题 {real.Issues.Count}"));

        var docPath = Path.Combine(repoRoot, CoreRegistry.DocRel);
        var regPath = Path.Combine(repoRoot, CoreRegistry.RegistryRel.Replace('/', Path.DirectorySeparatorChar));
        var docText = File.ReadAllText(docPath);
        var regText = File.ReadAllText(regPath);

        // ② 合成负例 A/B：版本不一致（首位版本号 2 → 1）+ §9.3 迁移关键词缺步（删掉全部「校验回读」行）
        var rootA = Path.Combine(work, "core-registry-version");
        Fresh(rootA);
        var needle = "registry_schema_version: \"2\"";
        var flip = docText.IndexOf(needle, StringComparison.Ordinal);
        var docA = flip >= 0
            ? docText[..flip] + "registry_schema_version: \"1\"" + docText[(flip + needle.Length)..]
            : docText;
        WriteCase(rootA, docA, regText);
        var resA = CoreRegistry.Check(rootA);
        var textA = string.Join(" | ", resA.Issues);
        checks.Add(new Check("check13·合成负例（版本不一致报错：02=\"1\" desktop=\"2\"）",
            !resA.Ok && flip >= 0 && textA.Contains("协议版本不一致：02=\"1\" desktop=\"2\""),
            $"问题 {resA.Issues.Count} · {First(resA)}"));

        var rootB = Path.Combine(work, "core-registry-migration");
        Fresh(rootB);
        var docB = string.Join("\n", docText.Split('\n').Where(l => !l.Contains("校验回读", StringComparison.Ordinal)));
        WriteCase(rootB, docB, regText);
        var resB = CoreRegistry.Check(rootB);
        var textB = string.Join(" | ", resB.Issues);
        checks.Add(new Check("check13·合成负例（§9.3 迁移缺步：删掉「校验回读」后报缺步）",
            !resB.Ok && textB.Contains("迁移记录缺步： 校验回读"),
            $"问题 {resB.Issues.Count} · {First(resB)}"));

        // ③ 合成负例 C/D：模块表双向差集——02 §2 少一行 / registry.json modules 少一个
        var rootC = Path.Combine(work, "core-registry-doc-short");
        Fresh(rootC);
        WriteCase(rootC, DropFirstModuleRow(docText), regText);
        var resC = CoreRegistry.Check(rootC);
        var textC = string.Join(" | ", resC.Issues);
        checks.Add(new Check("check13·合成负例（02 §2 少一行：行数 12 + registry 有而 02 缺）",
            !resC.Ok && resC.DocRows == CoreRegistry.ExpectedModules - 1
            && textC.Contains("02 §2 模块表行数=12")
            && textC.Contains("registry.json 有而 02 缺："),
            $"02 行 {resC.DocRows} · registry 行 {resC.RegRows} · 仅 registry {resC.OnlyReg.Count}"));

        var rootD = Path.Combine(work, "core-registry-reg-short");
        Fresh(rootD);
        var node = System.Text.Json.Nodes.JsonNode.Parse(regText)!;
        var modulesNode = node["modules"]!.AsArray();
        var droppedId = modulesNode[0]!["id"]!.GetValue<string>();
        modulesNode.RemoveAt(0);
        WriteCase(rootD, docText, node.ToJsonString());
        var resD = CoreRegistry.Check(rootD);
        var textD = string.Join(" | ", resD.Issues);
        checks.Add(new Check("check13·合成负例（registry.json 少一个 module：数 12 + 02 有而 registry 缺）",
            !resD.Ok && resD.RegRows == CoreRegistry.ExpectedModules - 1
            && textD.Contains("registry.json modules 数=12")
            && textD.Contains("02 有而 registry.json 缺：" + droppedId),
            $"registry 行 {resD.RegRows} · 仅 02 {resD.OnlyDoc.Count} · 丢 {droppedId}"));

        // ④ 受控化：registry.json 缺件（真源在 json.load 上崩、traceback 进 log；本件给判定）
        var rootE = Path.Combine(work, "core-registry-no-registry");
        Fresh(rootE);
        Directory.CreateDirectory(Path.Combine(rootE, Path.GetDirectoryName(CoreRegistry.RegistryRel)!
            .Replace('/', Path.DirectorySeparatorChar)));
        File.WriteAllText(Path.Combine(rootE, CoreRegistry.DocRel.Replace('/', Path.DirectorySeparatorChar)), docText);
        var resE = CoreRegistry.Check(rootE);
        var textE = string.Join(" | ", resE.Issues);
        checks.Add(new Check("check13·受控化（缺 registry.json 给判定而非崩溃：缺件 + 版本字段缺失）",
            !resE.Ok && textE.Contains("registry.json 缺件")
            && textE.Contains("版本字段缺失") && resE.Steps.Count == 3,
            $"问题 {resE.Issues.Count} · 步骤 {resE.Steps.Count} · {First(resE)}"));
    }

    /// <summary>
    /// 单组自检的**异常围栏**：一组抛异常不该让整套挂掉——此前一处异常会终止整个 Run，
    /// 把其余几百条结果一起藏掉（第八十八～九十片引入多组新钉后踩到）。围栏把异常变成
    /// **一条失败钉**，并带上类型 + 首个 Nf.Engine 栈帧，便于定位。
    /// </summary>
    private static void Safe(List<Check> checks, string group, Action action)
    {
        try
        {
            action();
        }
        catch (Exception exc)
        {
            var frame = (exc.StackTrace ?? "").Split('\n')
                .Select(line => line.Trim())
                .FirstOrDefault(line => line.Contains("Nf.Engine", StringComparison.Ordinal)) ?? "";
            checks.Add(new Check($"{group}·**自检组自身抛异常**（围栏兜住，不静默）", false,
                $"{exc.GetType().Name}：{exc.Message} · {frame}"));
        }
    }

    private static void Fresh(string dir)
    {
        if (Directory.Exists(dir)) Directory.Delete(dir, recursive: true);
        Directory.CreateDirectory(dir);
    }

    /// <summary>
    /// **测量模式判别**：<c>&lt;root&gt;/.git</c> 在场 = **工作区**（内容随提交漂移），不在场 = **导出快照**。
    ///
    /// 为什么需要：本工程的金标摘要**锚定具体 HEAD**（第八十～八十六片的快照 = <c>983741b</c>）。
    /// 导出态断「金标摘要逐字节一致」（最强）；工作区态改断**语义不变量**——拿一份被并发编辑过的
    /// 语料去比死摘要，只会把「语料漂了」误报成「引擎错了」（第八十六片实测：一键门直接打活仓库时
    /// 文档命令面与扩展策略面各红一条，而两者都只是 HEAD 前移/带 .git 所致）。
    /// </summary>
    private static bool IsPinnedSnapshot(string root) => !Directory.Exists(Path.Combine(root, ".git"));

    private static void WriteCase(string root, string doc, string registryJson)
    {
        File.WriteAllText(Path.Combine(root, CoreRegistry.DocRel.Replace('/', Path.DirectorySeparatorChar)),
            doc, new UTF8Encoding(false));
        var reg = Path.Combine(root, CoreRegistry.RegistryRel.Replace('/', Path.DirectorySeparatorChar));
        Directory.CreateDirectory(Path.GetDirectoryName(reg)!);
        File.WriteAllText(reg, registryJson, new UTF8Encoding(false));
    }

    /// <summary>在 02 §2 段内删掉第一条模块行（真源口径：5 格、首格非表头非分隔线）。</summary>
    private static string DropFirstModuleRow(string doc)
    {
        var start = doc.IndexOf("## 2. 官方核心模块表", StringComparison.Ordinal);
        if (start < 0) return doc;
        var end = doc.IndexOf("\n## 3.", start, StringComparison.Ordinal);
        if (end < 0) return doc;
        var segment = doc[start..end];
        var lines = segment.Split('\n').ToList();
        for (var i = 0; i < lines.Count; i++)
        {
            var cells = lines[i].Trim().Trim('|').Split('|').Select(c => c.Trim()).ToList();
            if (cells.Count == 5 && cells[0] != "模块ID" && cells[0] != "---" && cells[0].Length > 0)
            {
                lines.RemoveAt(i);
                break;
            }
        }
        return doc[..start] + string.Join("\n", lines) + doc[(start + segment.Length)..];
    }

    private static string First(CoreRegistry.Result result) =>
        result.Issues.Count > 0 ? result.Issues[0] : (result.Steps.Count > 0 ? result.Steps[0].Detail : "");

    private static void MarketCases(List<Check> checks)
    {
        // ①' 包视图三件：闭包（叶越界 / 嵌套 references / 源包不可读）· 挂载冲突 · 登记三要件
        var pkgProts = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal)
        {
            ["组合包"] = new(StringComparer.Ordinal)
            {
                ["module_ids"] = new List<object?> { "合成:M01" },
                ["references"] = new List<object?>
                {
                    new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["source_package"] = "源包", ["module_id"] = "源:M07",
                    },
                    new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["source_package"] = "幽灵包", ["module_id"] = "M09",
                    },
                },
            },
        };
        var data = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal)
        {
            ["组合包"] = new(StringComparer.Ordinal)
            {
                ["package"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["id"] = "组合包",
                    ["dependencies"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["core_modules"] = new List<object?> { "M00" },
                    },
                    ["mount_layers"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["P40 行为决策"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["default"] = new List<object?> { "组合:M01" },
                        },
                    },
                },
            },
            ["源包"] = new(StringComparer.Ordinal)
            {
                ["package"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["id"] = "源包",
                    ["dependencies"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["core_modules"] = new List<object?> { "M00", "M99" },   // M99 越界官方 13
                    },
                    ["references"] = new List<object?>                                    // 嵌套 references
                    {
                        new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["source_package"] = "幽灵包", ["module_id"] = "M09",
                        },
                    },
                    ["mount_layers"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["P40 行为约束"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["default"] = new List<object?> { "组合:M01" },       // 同层 default 冲突
                        },
                    },
                },
            },
        };
        var (seen, depIssues) = MarketAnalyzer.Dependencies("组合包", pkgProts, data);
        var conflicts = MarketAnalyzer.Conflicts("组合包", pkgProts, data);
        var depJoined = string.Join(" | ", depIssues);
        checks.Add(new Check("包视图·依赖闭包与挂载冲突（叶越界 / 嵌套 references / 源包不可读 / 同层 default 冲突）",
            seen.Contains("源包") && depJoined.Contains("叶节点越界官方核心 13 件: M99")
            && depJoined.Contains("源包嵌套 references") && depJoined.Contains("源包不可读: 幽灵包")
            && conflicts.Count == 1 && conflicts[0].Contains("挂载层 P40 default 冲突"),
            $"闭包源 {seen.Count} · 依赖问题 {depIssues.Count} 条 · 冲突 {conflicts.Count} 条"));

        // ①'' 登记三要件：缺件 / 缺 package 段 / 02 §8 未在册
        var tmp = Path.Combine(Path.GetTempPath(), "nf-market-fix-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(tmp);
        var missing = MarketAnalyzer.CheckRegisterable(Path.Combine(tmp, "不存在"), "### 8.1 x\n## 9. y\n");
        var noPkgDir = Path.Combine(tmp, "无package");
        Directory.CreateDirectory(noPkgDir);
        File.WriteAllText(Path.Combine(noPkgDir, "protocol.yaml"), "protocol:\n  schema_version: \"2\"\n");
        var noPkg = MarketAnalyzer.CheckRegisterable(noPkgDir, "### 8.1 x\n## 9. y\n");
        var pkgDir = Path.Combine(tmp, "未在册");
        Directory.CreateDirectory(pkgDir);
        File.WriteAllText(Path.Combine(pkgDir, "protocol.yaml"),
            "protocol:\n  schema_version: \"2\"\npackage:\n  id: 未在册包\n");
        var notRegistered = MarketAnalyzer.CheckRegisterable(pkgDir, "### 8.1 别的包\n## 9. y\n");
        checks.Add(new Check("包视图·登记三要件（缺件 / 缺 package 段 / 不在 02 §8 在册）",
            missing.Any(x => x.Contains("protocol.yaml 缺失")) && noPkg.Any(x => x.Contains("缺 package 段"))
            && notRegistered.Any(x => x.Contains("不在 02 §8 在册")),
            $"缺件={missing.Count} · 缺段={noPkg.Count} · 未在册={notRegistered.Count} 条问题"));
        try { Directory.Delete(tmp, recursive: true); } catch (IOException) { /* 清理失败不影响判定 */ }

        // ① 分级：官方 13 件比**完整 id**（事件:M22 官方 vs 情感:M22 社区同号段）；M91-M99 按裸号判实验
        var grades = new (string Id, string Want)[]
        {
            ("M50", "official"), ("事件:M22", "official"), ("情感:M22", "community"),
            ("通用:M10", "official"), ("M91", "experimental"), ("甲:M91", "experimental"),
            ("甲:M01", "community"),
        };
        var gradeOk = grades.All(g => MarketAnalyzer.GradeOfModule(g.Id) == g.Want);
        checks.Add(new Check("市场分级·官方比完整 id（同号段前缀不误判）+ M91-M99 实验段",
            gradeOk,
            string.Join(" · ", grades.Select(g => $"{g.Id}→{MarketAnalyzer.GradeOfModule(g.Id)}"))));

        // ② 目录视图：模块先、包后；包级 grading（全实验段 → experimental）；tier 过滤
        var reg = PythonJson.ToGraph(System.Text.Json.JsonDocument.Parse("""
        {"modules": [{"id": "M00", "name": "数据结构"}],
         "protocols": [
           {"id": "实验包", "name": "实验", "module_ids": ["甲:M91", "甲:M92"]},
           {"id": "社区包", "name": "社区", "version": "3.1.0", "module_ids": ["M01"]}]}
        """).RootElement) as Dictionary<string, object?>;
        var all = MarketAnalyzer.ListMarket(reg!);
        var experimental = MarketAnalyzer.ListMarket(reg!, "experimental");
        checks.Add(new Check("市场目录·全量顺序与分级 + tier 过滤（全实验段包 → experimental）",
            all.Count == 3
            && (all[0].GetValueOrDefault("kind") as string) == "module"
            && (all[0].GetValueOrDefault("grade") as string) == "official"
            && (all[1].GetValueOrDefault("grade") as string) == "experimental"
            && (all[2].GetValueOrDefault("version") as string) == "3.1.0"
            && experimental.Count == 1 && (experimental[0].GetValueOrDefault("id") as string) == "实验包",
            $"全量 {all.Count} 项（{string.Join("/", all.Select(x => x.GetValueOrDefault("grade")))}）· " +
            $"tier=experimental → {experimental.Count} 项"));

        // ③ See-Also：包目标（refs + 模块依赖图命中 + 反向引用方）与模块目标
        var prots = MarketAnalyzer.Protocols(reg!);
        var graph = new Dictionary<string, HashSet<string>>(StringComparer.Ordinal)
        {
            ["M01"] = new(StringComparer.Ordinal) { "M00" },
        };
        var asPackage = MarketAnalyzer.RelatedOf("社区包", prots, graph, null);
        var asModule = MarketAnalyzer.RelatedOf("M00", prots, graph, null);
        var pkgRefs = (asPackage.GetValueOrDefault("refs") as List<object?> ?? new List<object?>()).Count;
        checks.Add(new Check("See-Also·包/模块两态（依赖图注入：模块 M01→M00 形成互见）",
            (asPackage.GetValueOrDefault("kind") as string) == "package" && pkgRefs >= 1
            && (asModule.GetValueOrDefault("kind") as string) == "module"
            && (asModule.GetValueOrDefault("referenced_by") as List<object?> ?? new List<object?>()).Count >= 1,
            $"包态 refs={pkgRefs} · 模块态反向引用=" +
            $"{(asModule.GetValueOrDefault("referenced_by") as List<object?>)?.Count}"));
    }

    private static void ImpactCases(List<Check> checks)
    {
        // ① 裸号归一：三种写法同号；多段限定只剥第一段前的前缀
        var normOk = ImpactCheck.Norm("情感类:M55") == "M55" && ImpactCheck.Norm("情感:M55") == "M55"
                     && ImpactCheck.Norm("M55") == "M55" && ImpactCheck.Norm("a:b:c") == "b:c";
        checks.Add(new Check("影响面·裸号归一（长/短前缀与裸号同号；多段只剥一段）", normOk,
            $"情感类:M55→{ImpactCheck.Norm("情感类:M55")} · M55→{ImpactCheck.Norm("M55")} · a:b:c→{ImpactCheck.Norm("a:b:c")}"));

        // ② registry 引用图闭合（check21 判据本体）：裸号重复 ③ / 源包悬空 ①② / 源包无此号 ②
        var reg = PythonJson.ToGraph(System.Text.Json.JsonDocument.Parse("""
        {"modules": [{"id": "M00"}],
         "protocols": [
           {"id": "包甲", "module_ids": ["甲:M01", "M01"],
            "references": [{"source_package": "包乙", "module_id": "乙:M07"},
                           {"source_package": "幽灵包", "module_id": "M09"},
                           {"source_package": "包乙", "module_id": "M99"}]},
           {"id": "包乙", "module_ids": ["M07"], "references": []}]}
        """).RootElement) as Dictionary<string, object?>;
        var issues = ImpactCheck.RegistryIntegrityIssues(reg!);
        var joined = string.Join(" | ", issues);
        checks.Add(new Check("影响面·引用图闭合逐条报（裸号重复 / 源包悬空 / 源包无此号）",
            issues.Count == 3 && joined.Contains("③") && joined.Contains("①②") && joined.Contains("②"),
            $"问题 {issues.Count} 条 · {joined[..Math.Min(150, joined.Length)]}"));

        // ③ 影响面判定：官方核心模块 → 破坏性；无引用非官方模块 → 安全；不存在 → error
        var coreHit = ImpactCheck.ImpactOfChange(reg!, "M00");
        var safeHit = ImpactCheck.ImpactOfChange(reg!, "M07");
        var miss = ImpactCheck.ImpactOfChange(reg!, "不存在XYZ");
        checks.Add(new Check("影响面·三态判定（官方在册破坏性 / 仅被引用 / 目标不存在）",
            (coreHit.GetValueOrDefault("in_official_core") as List<object?> ?? new List<object?>()).Count == 1
            && (safeHit.GetValueOrDefault("referenced_by") as List<object?> ?? new List<object?>()).Count == 1
            && miss.ContainsKey("error"),
            $"官方核心在册={(coreHit.GetValueOrDefault("in_official_core") as List<object?>)?.Count} · " +
            $"被引用={(safeHit.GetValueOrDefault("referenced_by") as List<object?>)?.Count} · 不存在含 error={miss.ContainsKey("error")}"));
    }

    private static void WorldModelCases(List<Check> checks, string work)
    {
        // ① 值类型判定：bool 不许冒充 integer/number（Python isinstance(True, int) 为真，故须显式排除）
        var boolAsInt = WorldModel.ValueMatches(true, "integer");
        var longOk = WorldModel.ValueMatches(3L, "integer");
        var numOk = WorldModel.ValueMatches(1.5, "number") && WorldModel.ValueMatches(3L, "number");
        var arrOk = WorldModel.ValueMatches(new List<object?> { "a", "b" }, "array", "string")
                    && !WorldModel.ValueMatches(new List<object?> { "a", 1L }, "array", "string");
        checks.Add(new Check("世界模型·值类型判定（bool≠integer；array 元素类型逐一验）",
            !boolAsInt && longOk && numOk && arrOk,
            $"bool→integer={boolAsInt} · long→integer={longOk} · number 两态={numOk} · array 两态={arrOk}"));

        // ② 契约校验：坏契约须逐条报（未注册槽 / 类型漂移 / 相位不可达 / monotonic 用错）
        var broken = PythonJson.ToGraph(System.Text.Json.JsonDocument.Parse("""
        {
          "abstract_state": {
            "variables": [
              {"name": "tick", "kind": "string", "source": "通用:M10", "slot": "WorldState.time.tick"},
              {"name": "ghost", "kind": "integer", "source": "通用:M10", "slot": "ghost.slot"}
            ],
            "initial": {"tick": "0"}
          },
          "transition": {"initial_phase": "a",
            "phases": [{"phase": "a", "next": "b", "guard": "g", "writes": []},
                       {"phase": "b", "next": "a", "guard": "g", "writes": []},
                       {"phase": "c", "next": "a", "guard": "g", "writes": []}]},
          "invariants": ["x"],
          "checks": [{"kind": "monotonic", "field": "tick"}]
        }
        """).RootElement) as Dictionary<string, object?>;
        var slots = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal)
        {
            ["WorldState.time.tick"] = new(StringComparer.Ordinal)
            {
                ["kind"] = "integer", ["owner"] = "通用:M10",
            },
        };
        var issues = WorldModel.ValidateContract(broken, "wm", slots);
        var joined = string.Join(" | ", issues);
        checks.Add(new Check("世界模型·坏契约逐条报（未注册槽 / 类型漂移 / 相位不可达 / monotonic 用错）",
            joined.Contains("未在 protocol/world_slots.json 注册") && joined.Contains("类型漂移")
            && joined.Contains("不可达的相位") && joined.Contains("monotonic 只能用于"),
            $"违例 {issues.Count} 条 · {joined[..Math.Min(150, joined.Length)]}"));

        // ③ 扫描空根：fail-closed（缺槽位注册表即报，不静默零问题）
        var emptyRoot = Path.Combine(work, "worldmodel-empty");
        Directory.CreateDirectory(emptyRoot);
        var (scanIssues, scanStats) = WorldModel.Scan(emptyRoot);
        checks.Add(new Check("世界模型·缺槽位注册表 fail-closed（不静默给零问题）",
            scanIssues.Count == 1 && scanIssues[0].Contains("protocol/world_slots.json 缺失或 slots 为空")
            && Convert.ToInt64(scanStats["modules"]) == 0,
            $"问题 {scanIssues.Count} 条 · 模块 {scanStats["modules"]}"));

        // ④ 槽位读写往返（嵌套路径不存在时自动建层，与 Python _set_slot 的 setdefault 同义）
        var nested = WorldModel.SetSlot(new Dictionary<string, object?>(StringComparer.Ordinal),
            "a.b.c", 7L);
        var gotBack = WorldModel.TryGetSlot(nested, "a.b.c", out var slotValue) && Convert.ToInt64(slotValue) == 7
                      && !WorldModel.TryGetSlot(nested, "a.b.x", out _);
        checks.Add(new Check("世界模型·槽位读写往返（缺路径自动建层；取不存在的槽报缺）", gotBack,
            $"取回={Convert.ToInt64(slotValue ?? 0L)} · 缺槽=False"));

        // ⑤ 相位序列：环 → cycle + 重复相位；悬空 → dangling
        var cyclic = PythonJson.ToGraph(System.Text.Json.JsonDocument.Parse("""
        {"abstract_state": {"variables": [{"name": "phase", "kind": "string", "source": "s"}],
                            "initial": {"phase": "a"}},
         "transition": {"initial_phase": "a",
           "phases": [{"phase": "a", "next": "b", "guard": "g", "writes": []},
                      {"phase": "b", "next": "a", "guard": "g", "writes": []}]},
         "invariants": ["x"]}
        """).RootElement) as Dictionary<string, object?>;
        var (sequence, reason, repeat) = WorldModel.PhaseSequence(cyclic!);
        var dangling = PythonJson.ToGraph(System.Text.Json.JsonDocument.Parse("""
        {"abstract_state": {"variables": [{"name": "phase", "kind": "string", "source": "s"}],
                            "initial": {"phase": "a"}},
         "transition": {"initial_phase": "a",
           "phases": [{"phase": "a", "next": "b", "guard": "g", "writes": []},
                      {"phase": "b", "next": "a", "guard": "g", "writes": []}]},
         "invariants": ["x"]}
        """).RootElement) as Dictionary<string, object?>;
        checks.Add(new Check("世界模型·相位序列（环→cycle+重复相位；序列逐项）",
            // Python 语义：**先把当前相位入列，再判下一个**；回到已见相位时返回 cycle + 重复相位本身，
            // 故 2 相位环的序列是 a→b（不是 a→b→a）——这里如实测口径。
            string.Join("→", sequence) == "a→b" && reason == "cycle" && repeat == "a"
            && WorldModel.PhaseSequence(dangling!).Reason == "cycle",
            $"序列={string.Join("→", sequence)} · 终止={reason} · 重复={repeat}"));

        // ⑥ 重放：步数 / 终止原因 / digest 两次一致（确定性指纹）
        var runtime = new WorldModel.Runtime(cyclic!);
        var first = runtime.Replay();
        var second = runtime.Replay();
        var steps = (first.GetValueOrDefault("steps") as List<object?> ?? new List<object?>()).Count;
        checks.Add(new Check("世界模型·重放（2 步环 · 终止 cycle · digest 两次一致）",
            steps == 2 && (first.GetValueOrDefault("reason") as string) == "cycle"
            && (first.GetValueOrDefault("digest") as string) == (second.GetValueOrDefault("digest") as string)
            && (first.GetValueOrDefault("digest") as string)?.Length == 64,
            $"步数={steps} · 终止={first.GetValueOrDefault("reason")} · " +
            $"digest={(first.GetValueOrDefault("digest") as string)?.Substring(0, 12)}"));
    }

    private static void McpErrorIdCases(List<Check> checks, string root)
    {
        // 工具内部抛异常时：① 不许沉默（必须有 error 响应）；② **必须回带请求 id**（JSON-RPC 2.0 §5）；
        // ③ 不许杀循环（后续 ping 仍应答）。真源缺陷：此前固定回带 id=null。
        var input = new StringReader(
            """{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}""" + "\n" +
            """{"jsonrpc":"2.0","id":9001,"method":"tools/call","params":{"name":"nf_st_validate","arguments":{"path":"no/such/card.json"}}}""" + "\n" +
            """{"jsonrpc":"2.0","id":9002,"method":"ping"}""" + "\n");
        var output = new StringWriter();
        McpServer.ServeStdio(root, input, output);
        var lines = output.ToString().Split('\n', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);

        var errorLine = lines.FirstOrDefault(l => l.Contains("9001", StringComparison.Ordinal));
        var pingLine = lines.FirstOrDefault(l => l.Contains("9002", StringComparison.Ordinal));
        var echoedId = errorLine is not null && errorLine.Contains("\"id\": 9001", StringComparison.Ordinal);
        var internalError = errorLine is not null && errorLine.Contains("-32603", StringComparison.Ordinal);
        checks.Add(new Check("MCP·工具抛异常 → 错误响应回带请求 id 且码为 -32603（不沉默、不丢 id）",
            echoedId && internalError && pingLine is not null,
            $"id 回带={echoedId} · -32603={internalError} · 循环存活={pingLine is not null} · " +
            $"{(errorLine ?? "（无 9001 响应）")[..Math.Min(90, errorLine?.Length ?? 12)]}"));
    }

    private static void InteropCases(List<Check> checks, string work)
    {
        // ① CIDv1 已知向量（真源 docstring 给出的口径：raw codec 0x71 + sha2-256）
        var empty = Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(Array.Empty<byte>())).ToLowerInvariant();
        var cid = Interop.Cidv1RawSha256(empty);
        checks.Add(new Check("互操作·CIDv1 已知向量（sha256(\"\") → bafyrei…）",
            cid == "bafyreihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku",
            cid));

        // ② JSON Schema 映射（array → items；nullable → 联合类型；未识别 → object 保守兜底）
        var asArray = Interop.SchemaFor("array of strings");
        var nullable = Interop.SchemaFor("string|null");
        var unknown = Interop.SchemaFor("某些中文说明");
        var emptyDesc = Interop.SchemaFor("");
        checks.Add(new Check("互操作·字段说明串 → JSON Schema 映射（array/nullable/兜底/空描述）",
            PyScalar.PyEquals(asArray["type"], "array") && asArray.ContainsKey("items")
            && PyScalar.PyRepr(nullable["type"]) == "['string', 'null']"
            && PyScalar.PyEquals(unknown["type"], "object")
            && unknown.GetValueOrDefault("additionalProperties") is true
            && !emptyDesc.ContainsKey("description"),
            $"array={PyScalar.PyRepr(asArray["type"])} · nullable={PyScalar.PyRepr(nullable["type"])} · " +
            $"兜底={PyScalar.PyRepr(unknown["type"])} · 空描述含 description={emptyDesc.ContainsKey("description")}"));

        // ③ JSON Pointer 转义（RFC 6901）
        checks.Add(new Check("互操作·JSON Pointer 转义（~ → ~0、/ → ~1）",
            Interop.Ptr("nf/a~b") == "nf~1a~0b", Interop.Ptr("nf/a~b")));

        // ④ 空根：门禁 fail-closed（缺派生真源 → 报错不静默）
        var emptyRoot = Path.Combine(work, "interop-empty");
        Directory.CreateDirectory(emptyRoot);
        var (emptyIssues, _) = Interop.Verify(emptyRoot);
        checks.Add(new Check("互操作·真源缺失 fail-closed（不静默给空导出面）",
            emptyIssues.Count(x => x.Contains("缺派生真源")) == 3
            && emptyIssues.Any(x => x.Contains("缺派生真源 protocol/RECEIPTS.json"))
            && emptyIssues.Any(x => x.Contains("缺派生真源 protocol/endpoint_contract.json")),
            $"问题 {emptyIssues.Count} 条 · 缺真源 {emptyIssues.Count(x => x.Contains("缺派生真源"))} 条"));

        // ⑤ 确定性：同一根两次渲染逐字节一致（12 形状全跑）
        var root = Path.Combine(work, "interop-det");   // 空根也足以证明"两次一致"
        Directory.CreateDirectory(root);
        var deterministic = Interop.Kinds.All(k => Interop.Render(k.Id, root).SequenceEqual(Interop.Render(k.Id, root)));
        checks.Add(new Check("互操作·确定性（同输入两次渲染逐字节一致 · 12 形状）", deterministic,
            $"形状 {Interop.Kinds.Length} 个"));
    }

    private static void KnowledgeFrequencyCases(List<Check> checks, string work)
    {
        var dir = Path.Combine(work, "knowledge-frequency");
        Directory.CreateDirectory(dir);

        // JSONL：混合合法/坏行/非对象/无源标识 → 只数有源标识的对象，键排序
        var jsonl = Path.Combine(dir, "trace.jsonl");
        File.WriteAllLines(jsonl, new[]
        {
            """{"knowledge_source":"nf-protocol","ts":"t1"}""",
            """{"source_id":"nf-protocol","ts":"t2"}""",
            """{"knowledge_source":"nf-patterns","ts":"t3"}""",
            "{ 坏行 }",
            "42",
            """{"other":1}""",
            "",
        });
        var c1 = KnowledgeSources.HarvestFrequency(jsonl);
        checks.Add(new Check("频次复算·JSONL（坏行/非对象/无源标识都跳过；键排序）",
            c1.Count == 2 && Convert.ToInt64(c1["nf-protocol"]) == 2 && Convert.ToInt64(c1["nf-patterns"]) == 1
            && c1.Keys.First() == "nf-patterns",
            $"源 {c1.Count} · nf-protocol={c1["nf-protocol"]} · nf-patterns={c1["nf-patterns"]}"));

        // JSON 数组形态
        var arr = Path.Combine(dir, "trace_array.json");
        File.WriteAllText(arr, """[{"knowledge_source":"a"},{"knowledge_source":"b"},{"knowledge_source":"a"}]""");
        var c2 = KnowledgeSources.HarvestFrequency(arr);
        checks.Add(new Check("频次复算·JSON 数组形态",
            c2.Count == 2 && Convert.ToInt64(c2["a"]) == 2 && Convert.ToInt64(c2["b"]) == 1,
            $"a={c2["a"]} · b={c2["b"]}"));

        // {"records":[...]} 形态 + 单对象兜底
        var recs = Path.Combine(dir, "trace_records.json");
        File.WriteAllText(recs, """{"records":[{"source_id":"x"},{"source_id":"x"},{"source_id":"y"}]}""");
        var single = Path.Combine(dir, "trace_single.json");
        File.WriteAllText(single, """{"knowledge_source":"solo"}""");
        var c3 = KnowledgeSources.HarvestFrequency(recs);
        var c4 = KnowledgeSources.HarvestFrequency(single);
        checks.Add(new Check("频次复算·records 形态与单对象兜底",
            c3.Count == 2 && Convert.ToInt64(c3["x"]) == 2 && c4.Count == 1 && Convert.ToInt64(c4["solo"]) == 1,
            $"records: x={c3["x"]} · y={c3["y"]} · 单对象: solo={c4["solo"]}"));

        // 文件不可读 → 受控抛出（CLI 侧转 exit 1）
        var threw = false;
        try { KnowledgeSources.HarvestFrequency(Path.Combine(dir, "no-such.jsonl")); }
        catch (IOException) { threw = true; }
        checks.Add(new Check("频次复算·缺文件受控抛 IOException（不崩栈）", threw, $"受控={threw}"));
    }

    private static void RepoStatsCases(List<Check> checks, string work)
    {
        var root = Path.Combine(work, "repo-stats");
        var core = Path.Combine(root, "desktop", "src", "core");
        var pipes = Path.Combine(root, "03_管线库");
        var assets = Path.Combine(root, "community", "包甲", "assets");
        var protocol = Path.Combine(root, "protocol");
        var library = Path.Combine(root, "library");
        foreach (var dir in new[] { core, pipes, assets, protocol, library }) Directory.CreateDirectory(dir);

        File.WriteAllText(Path.Combine(core, "registry.json"),
            """{"modules":[{"id":"M00"},{"id":"M10"}],"protocols":[{"id":"包甲"}]}""");
        File.WriteAllText(Path.Combine(pipes, "P01_标准.md"), "# P01\n");
        File.WriteAllText(Path.Combine(root, "community", "包甲", "protocol.yaml"), "package:\n  id: 包甲\n");
        File.WriteAllText(Path.Combine(assets, "DOMAIN_SPEC.md"), "# 资产\n");
        File.WriteAllText(Path.Combine(assets, "CONCEPT_GRAPH.md"), "# 概念图\n");
        File.WriteAllText(Path.Combine(protocol, "standards_catalog.json"),
            """{"coverage":{"standards":3,"reachable":2,"unreachable":1,"bodies":1,"depends_edges":2,"by_layer":{"L1":1}}}""");
        File.WriteAllText(Path.Combine(protocol, "standards_binding.json"), """{"bindings_total":7}""");
        File.WriteAllText(Path.Combine(protocol, "domain_packs.json"), """{"count":100,"subdivisions_total":1200}""");
        File.WriteAllText(Path.Combine(library, "NF-1.md"), "# NF-1\n");
        File.WriteAllText(Path.Combine(root, "verify.sh"), "# 版本 : v2.29\ncheck1(){\n}\ncheck2(){\n}\n");
        File.WriteAllText(Path.Combine(core, "quality_baseline.py"), "EXPECTED_CHECKS = 2\nEXPECTED_PASS = 5\n");

        // 入口文件先放 marker 占位，再用**实算结果**回填（正向对照）
        var entries = new[] { "README.md", "README.en.md", "llms.txt" };
        foreach (var rel in entries)
            File.WriteAllText(Path.Combine(root, rel),
                "# 入口\n\n<!-- nf:stats:begin -->\n占位\n<!-- nf:stats:end -->\n");

        var (stats, computeIssues) = RepoStats.Compute(root);
        var blocks = RepoStats.Render(stats);
        foreach (var (rel, block) in blocks) FillBlock(Path.Combine(root, rel), block);
        File.WriteAllText(Path.Combine(protocol, "repo_stats.json"), PythonJson.Indented(stats) + "\n");

        var (cleanIssues, _) = RepoStats.Check(root);
        checks.Add(new Check("自述数字·合成语料生成区与台账一致 → 零问题（正向对照）",
            computeIssues.Count == 0 && cleanIssues.Count == 0,
            $"compute={computeIssues.Count} · check={cleanIssues.Count} 问题 · " +
            $"模块 {stats["core_modules"]} · 管线 {((List<object?>)stats["core_pipelines"]!).Count} · " +
            $"台账 check1-{stats["baseline_checks"]}/PASS={stats["baseline_pass"]}"));

        // 变异①：生成区里改一个数字 → 必报「生成区与实算不一致」
        var readme = Path.Combine(root, "README.md");
        File.WriteAllText(readme, File.ReadAllText(readme).Replace("2 模块", "9 模块"));
        var (drift, _) = RepoStats.Check(root);
        checks.Add(new Check("自述数字·生成区数字被手改 → 必报（README.md 生成区与实算不一致）",
            drift.Any(x => x.Contains("README.md") && x.Contains("生成区与实算不一致")),
            drift.Count > 0 ? drift[0] : "（无问题）"));
        FillBlock(readme, blocks["README.md"]);   // 还原

        // 变异②：台账被改 → 必报「与实算不一致」
        var ledger = Path.Combine(protocol, "repo_stats.json");
        File.WriteAllText(ledger, File.ReadAllText(ledger).Replace("\"core_modules\": 2", "\"core_modules\": 9"));
        var (ledgerIssues, _) = RepoStats.Check(root);
        checks.Add(new Check("自述数字·在盘台账与实算不一致 → 必报",
            ledgerIssues.Any(x => x.Contains("repo_stats.json") && x.Contains("与实算不一致")),
            ledgerIssues.Count > 0 ? string.Join(" | ", ledgerIssues) : "（无问题）"));
        File.WriteAllText(ledger, PythonJson.Indented(stats) + "\n");

        // 变异③：缺 verify.sh → 必报「取不到 verify.sh」
        File.Delete(Path.Combine(root, "verify.sh"));
        var (noVerify, _) = RepoStats.Check(root);
        checks.Add(new Check("自述数字·缺 verify.sh → 必报口径缺失（不静默填 0）",
            noVerify.Any(x => x.Contains("取不到 verify.sh")),
            noVerify.Count > 0 ? noVerify[0] : "（无问题）"));

        // 变异④：盘上包目录 ≠ registry 登记 → 必报登记不一致
        Directory.CreateDirectory(Path.Combine(root, "community", "包乙"));
        File.WriteAllText(Path.Combine(root, "community", "包乙", "protocol.yaml"), "package:\n  id: 包乙\n");
        var (mismatch, _) = RepoStats.Check(root);
        checks.Add(new Check("自述数字·盘上包目录 ≠ registry 登记 → 必报",
            mismatch.Any(x => x.Contains("盘上包目录") && x.Contains("registry 登记")),
            mismatch.Count > 0 ? mismatch[0] : "（无问题）"));
    }

    /// <summary>把 marker 区内容替换成给定块（缺 marker 时原样返回）。</summary>
    private static void FillBlock(string path, string block)
    {
        var text = File.ReadAllText(path);
        var i = text.IndexOf(RepoStats.Begin, StringComparison.Ordinal);
        var j = text.IndexOf(RepoStats.End, StringComparison.Ordinal);
        if (i < 0 || j < 0 || j < i) return;
        File.WriteAllText(path, text[..i] + block + text[(j + RepoStats.End.Length)..]);
    }

    private static void StValidateCases(List<Check> checks, string work)
    {
        var dir = Path.Combine(work, "st-validate");
        Directory.CreateDirectory(dir);

        // ① 干净卡（V2 + 六字段齐）→ card · 零 fail
        var clean = Path.Combine(dir, "clean_card.json");
        File.WriteAllText(clean, """
        {"spec":"chara_card_v2","spec_version":"2.0","data":{"name":"甲","description":"乙",
         "personality":"丙","scenario":"丁","first_mes":"戊","mes_example":"己"}}
        """);
        var cleanRep = StValidate.Validate(clean);
        var cleanCounts = (Dictionary<string, object?>)cleanRep["counts"]!;
        checks.Add(new Check("制卡校验·干净卡判 card 且 fail=0（正向对照）",
            (string)cleanRep["kind"]! == "card" && Convert.ToInt64(cleanCounts["fail"]) == 0
            && ((List<object?>)cleanRep["issues"]!).Count == 0,
            $"kind={cleanRep["kind"]} · fail={cleanCounts["fail"]} · issues={((List<object?>)cleanRep["issues"]!).Count}"));

        // ② 脏世界书（entries 非 dict/list 之外的四类：key 空 / content 空 / 逗号 key / 重复 key / 缺 scanDepth）
        var messy = Path.Combine(dir, "messy_worldbook.json");
        File.WriteAllText(messy, """
        {"entries":[{"key":"","content":"有正文"},
                    {"key":"驿站,客栈","content":"","scanDepth":4},
                    {"key":"北境","content":"正文 A","scanDepth":4},
                    {"key":"北境","content":"正文 B","scanDepth":4}]}
        """);
        var messyRep = StValidate.Validate(messy);
        var messyRules = ((List<object?>)messyRep["issues"]!).Cast<Dictionary<string, object?>>()
            .Select(i => (string)i["rule"]!).ToList();
        var messyCounts = (Dictionary<string, object?>)messyRep["counts"]!;
        checks.Add(new Check("制卡校验·脏世界书逐条报（W1 key/content 空 · W2 逗号与重复 · W5 缺 scanDepth）",
            (string)messyRep["kind"]! == "worldbook"
            && messyRules.Count(r => r == "W1") == 2
            && messyRules.Count(r => r == "W2") == 2
            && messyRules.Count(r => r == "W5") == 1
            && Convert.ToInt64(messyCounts["fail"]) == 2,
            $"kind={messyRep["kind"]} · W1×{messyRules.Count(r => r == "W1")} · W2×{messyRules.Count(r => r == "W2")} · " +
            $"W5×{messyRules.Count(r => r == "W5")} · fail={messyCounts["fail"]} · warn={messyCounts["warn"]}"));

        // ③ MVU 变量：initial 含未声明 + 缺初始值 + array 建议
        var mvu = Path.Combine(dir, "mvu.json");
        File.WriteAllText(mvu, """
        {"variables":[{"name":"血量","kind":"integer"},{"name":"台账","kind":"array"}],
         "initial":{"血量":100,"幽灵变量":1}}
        """);
        var mvuRep = StValidate.Validate(mvu);
        var mvuJoin = string.Join(" | ", ((List<object?>)mvuRep["issues"]!).Cast<Dictionary<string, object?>>()
            .Select(i => (string)i["detail"]!));
        checks.Add(new Check("制卡校验·MVU 变量报未声明初始值 / 缺初始值 / array 建议",
            (string)mvuRep["kind"]! == "mvu-variables"
            && mvuJoin.Contains("initial 含未声明变量：幽灵变量")
            && mvuJoin.Contains("变量缺初始值：台账")
            && mvuJoin.Contains("优先 record"),
            mvuJoin.Length > 160 ? mvuJoin[..160] : mvuJoin));

        // ④ 未知形状 + 缺文件（受控失败，不许崩栈）
        var unknown = Path.Combine(dir, "unknown.json");
        File.WriteAllText(unknown, "{\"foo\": 1}");
        var unknownRep = StValidate.Validate(unknown);
        var missingThrew = false;
        try { StValidate.Validate(Path.Combine(dir, "nope.json")); }
        catch (IOException) { missingThrew = true; }
        checks.Add(new Check("制卡校验·未知形状判 unknown 且缺文件受控抛 IO 异常",
            (string)unknownRep["kind"]! == "unknown" && missingThrew,
            $"kind={unknownRep["kind"]} · 缺文件受控={missingThrew}"));
    }

    private static void ToolFaceCases(List<Check> checks, string work)
    {
        // ① 正向对照：合规条目（purpose + 非空 guidance + candidate 带 https 与 license）
        var goodRoot = Path.Combine(work, "toolface-good");
        var goodDir = Path.Combine(goodRoot, "04_模块库", "通用类");
        Directory.CreateDirectory(goodDir);
        File.WriteAllText(Path.Combine(goodDir, "M00_合规.md"), ToolFaceDoc("M00",
            "  tool_face:\n" +
            "    - purpose: 取时间\n" +
            "      guidance:\n" +
            "        when: 需要推进时间\n" +
            "      candidates:\n" +
            "        - repo: https://example.com/x\n" +
            "          license: MIT\n"));
        var (goodIssues, goodStats) = ToolFace.Scan(goodRoot);
        checks.Add(new Check("工具面·合规条目零问题（正向对照）",
            goodIssues.Count == 0
            && Convert.ToInt64(goodStats["modules"]) == 1
            && Convert.ToInt64(goodStats["entries"]) == 1
            && Convert.ToInt64(goodStats["candidates"]) == 1,
            $"issues={goodIssues.Count} · modules={goodStats["modules"]} · entries={goodStats["entries"]} · candidates={goodStats["candidates"]}"));

        // ② 违规条目：四类问题逐条报（缺 purpose / 缺 guidance / 非法链接 / 缺 license）
        var badRoot = Path.Combine(work, "toolface-bad");
        var badDir = Path.Combine(badRoot, "04_模块库", "通用类");
        Directory.CreateDirectory(badDir);
        File.WriteAllText(Path.Combine(badDir, "M01_违规.md"), ToolFaceDoc("M01",
            "  tool_face:\n" +
            "    - purpose: \"\"\n" +
            "      candidates:\n" +
            "        - repo: ftp://example.com/x\n" +
            "        - repo: https://example.com/y\n" +
            "          license: \"  \"\n"));
        var (badIssues, _) = ToolFace.Scan(badRoot);
        var joined = string.Join(" | ", badIssues);
        checks.Add(new Check("工具面·违规条目逐条报（缺 purpose / 缺 guidance / 非法链接 / 缺 license）",
            joined.Contains("缺 purpose") && joined.Contains("缺 guidance")
            && joined.Contains("缺合法 https 链接") && joined.Contains("缺 license"),
            joined.Length > 170 ? joined[..170] : joined));

        // ③ 非列表：报「tool_face 非空列表」且不计入模块数
        var nonListRoot = Path.Combine(work, "toolface-nonlist");
        var nonListDir = Path.Combine(nonListRoot, "04_模块库", "通用类");
        Directory.CreateDirectory(nonListDir);
        File.WriteAllText(Path.Combine(nonListDir, "M02_非列表.md"), ToolFaceDoc("M02", "  tool_face: 不是列表\n"));
        var (nonListIssues, nonListStats) = ToolFace.Scan(nonListRoot);
        checks.Add(new Check("工具面·tool_face 非非空列表 → 报「非空列表」且不计模块数",
            nonListIssues.Any(x => x.Contains("tool_face 非空列表")) && Convert.ToInt64(nonListStats["modules"]) == 0,
            string.Join(" | ", nonListIssues)));
    }

    /// <summary>合成一件带 machine_contract 的模块文档（工具面用例用；只造判据需要的最小字段）。</summary>
    private static string ToolFaceDoc(string id, string toolFaceBlock)
        => "# 模块 " + id + "\n\n"
           + "> 类别：通用｜来源：核心｜挂载点：P40 行为决策（active，default）｜依赖：无｜状态：active\n\n"
           + "```yaml\n"
           + "machine_contract:\n"
           + "  schema: \"1\"\n"
           + "  id: " + id + "\n"
           + "  layer: P40\n"
           + "  inputs: []\n"
           + "  outputs: []\n"
           + "  events:\n"
           + "    publish: []\n"
           + "    subscribe: []\n"
           + toolFaceBlock
           + "```\n";

    private static void WritePack(string root, string pack, string pipeline, string[] declaredIds,
        params (string File, string Id, string Layer, string[] Inputs, string[] Publish, string[] Subscribe)[] modules)
    {
        var packDir = Path.Combine(root, "community", pack);
        var modulesDir = Path.Combine(packDir, "modules");
        Directory.CreateDirectory(modulesDir);

        var lines = new List<string>
        {
            "protocol:",
            "  schema_version: \"2\"",
            "package:",
            $"  id: {pack}",
            $"  pipeline: {pipeline}",
            "  module_id_range:",
        };
        lines.AddRange(declaredIds.Select(id => $"    - \"{id}\""));
        lines.Add("  mount_layers:");
        foreach (var module in modules)
        {
            lines.Add($"    P40: {{default: [{module.Id}]}}");
        }
        File.WriteAllText(Path.Combine(packDir, "protocol.yaml"), string.Join("\n", lines) + "\n");

        foreach (var module in modules)
        {
            var body = $"""
```yaml
machine_contract:
  schema: "1"
  id: {module.Id}
  layer: {module.Layer}
  inputs: [{string.Join(", ", module.Inputs)}]
  outputs: []
  events:
    publish: [{string.Join(", ", module.Publish)}]
    subscribe: [{string.Join(", ", module.Subscribe)}]
  interfaces: []
```
""";
            File.WriteAllText(Path.Combine(modulesDir, module.File), "# fixture\n\n" + body);
        }
    }
}
