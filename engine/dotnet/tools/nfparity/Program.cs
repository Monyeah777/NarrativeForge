using System.Text;
using System.Text.Json;
using Nf.Engine;

// nfparity <repo-root>
// 等价判据：对 protocol/combo_certificates.json 的每条证书，用盘上 digest 字段做判据，
// 重算摘要必须与盘上一致（字节级）。退出码 0=全一致，1=有不一致，2=找不到向量文件。
// 诊断模式：nfparity --canonical-diff <python 期望规范串.json> <repo-root>

if (args.Length >= 3 && args[0] == "--canonical-diff")
{
    return CanonicalDiff(args[1], args[2]);
}

if (args.Length >= 3 && args[0] == "--protocol-parity")
{
    return ProtocolParity(args[1], args[2]);
}

if (args.Length >= 4 && args[0] == "--contracts-parity")
{
    return ContractsParity(args[1], args[2], args[3]);
}

if (args.Length >= 3 && args[0] == "--profiles-parity")
{
    return ProfilesParity(args[1], args[2]);
}

if (args.Length >= 3 && args[0] == "--combine-parity")
{
    return CombineParity(args[1], args[2]);
}

if (args.Length >= 2 && args[0] == "--receipts-verify")
{
    return ReceiptsVerify(args[1]);
}

if (args.Length >= 2 && args[0] == "--bench")
{
    return Bench(args[1]);
}

if (args.Length >= 3 && args[0] == "--breadth")
{
    return BreadthRun(args[1], args[2], serial: args.Contains("--serial"));
}

if (args.Length >= 3 && args[0] == "--sampler-parity")
{
    return SamplerParity(args[1], args[2]);
}

if (args.Length >= 2 && args[0] == "--assertions")
{
    var result = Assertions.Run(args[1]);
    Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
    {
        ["issues"] = result.Issues.Cast<object?>().ToList(),
        ["results"] = result.Results,
    }));
    return result.Issues.Count == 0 ? 0 : 1;
}

if (args.Length >= 2 && args[0] == "--decisions")
{
    var result = Decisions.Verify(args[1]);
    Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
    {
        ["issues"] = result.Issues.Cast<object?>().ToList(),
        ["projection"] = result.Projection.Cast<object?>().ToList(),
        ["stats"] = result.Stats,
        ["warns"] = result.Warns.Cast<object?>().ToList(),
    }));
    return result.Issues.Count == 0 && result.Projection.Count == 0 ? 0 : 1;
}

if (args.Length >= 2 && args[0] == "--cognition")
{
    var result = Cognition.Run(args[1]);
    Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
    {
        ["issues"] = result.Issues.Cast<object?>().ToList(),
        ["stats"] = result.Stats,
        ["warns"] = result.Warns.Cast<object?>().ToList(),
    }));
    return result.Issues.Count == 0 ? 0 : 1;
}

if (args.Length >= 2 && args[0] == "--library")
{
    var result = Library.Verify(args[1]);
    Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
    {
        ["issues"] = result.Issues.Cast<object?>().ToList(),
        ["projection"] = result.Projection.Cast<object?>().ToList(),
        ["stats"] = result.Stats,
        ["warns"] = result.Warns.Cast<object?>().ToList(),
    }));
    return result.Issues.Count == 0 && result.Projection.Count == 0 ? 0 : 1;
}

if (args.Length >= 2 && args[0] == "--model")
{
    var part = args.Length >= 3 ? args[2] : "";
    var result = Modeling.Run(args[1], part);
    Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
    {
        ["issues"] = result.Issues.Cast<object?>().ToList(),
        ["stats"] = result.Stats,
        ["warns"] = result.Warns.Cast<object?>().ToList(),
    }));
    return result.Issues.Count == 0 ? 0 : 1;
}

if (args.Length >= 2 && args[0] == "--sig")
{
    var scan = KnowledgeSig.Scan(args[1]);
    Console.WriteLine(PythonJson.Indented(scan.Records));
    return 0;
}

if (args.Length >= 2 && args[0] == "--conformance")
{
    var report = Conformance.Run(args[1]);
    Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
    {
        ["ported"] = report.Contracts.Select(c => (object?)new Dictionary<string, object?>
        {
            ["id"] = c.Id, ["ok"] = c.Ok, ["detail"] = c.Detail, ["digest"] = c.Digest,
            ["description"] = c.Description,
        }).ToList(),
        ["unported"] = report.Unported.Cast<object?>().ToList(),
        ["passed"] = report.Passed,
        ["root_of_ported"] = report.RootOfPorted,
    }));
    return 0;
}

if (args.Length >= 2 && args[0] == "--conformance-root")
{
    // 封印机制等价校验：喂 Python 侧的 (id, digest) 行，复算 root 应与其报告 root 逐字节一致
    using var rowsDoc = JsonIo.ReadFile(args[1]);
    var rows = new List<(string Id, string Digest)>();
    if (rowsDoc.RootElement.TryGetProperty("report", out var rep)
        && rep.TryGetProperty("contracts", out var contracts0))
    {
        foreach (var c in contracts0.EnumerateArray())
        {
            rows.Add((c.GetProperty("id").GetString()!, c.GetProperty("digest").GetString()!));
        }
    }
    Console.WriteLine(Conformance.RootOf(rows));
    return 0;
}

if (args.Length >= 3 && args[0] == "--conformance-one")
{
    // 单契约诊断（负例探针用）：打印 (ok, detail) 的紧凑 JSON，可直接与 Python 侧同契约比对
    var (oneOk, oneDetail, oneDigest) = Conformance.RunOne(args[1], args[2]);
    Console.WriteLine(PythonJson.CanonicalizeGraph(new Dictionary<string, object?>(StringComparer.Ordinal)
    {
        ["id"] = args[1], ["ok"] = oneOk, ["detail"] = oneDetail, ["digest"] = oneDigest,
    }));
    return 0;
}

if (args.Length >= 2 && args[0] == "--canonical-compact")
{
    // 紧凑规范化（attest.canonical 口径）跨实现校验：喂 JSON 文件，打印紧凑规范串
    using var canonDoc = JsonIo.ReadFile(args[1]);
    Console.WriteLine(PythonJson.Compact(PythonJson.ToGraph(canonDoc.RootElement)));
    return 0;
}

if (args.Length >= 2 && args[0] == "--yaml-dump")
{
    // 整份 YAML 解析后按 Python 规范串打印（日期/时间只比类型标记，见 probe 说明）
    try
    {
        var body = File.ReadAllText(args[1], new UTF8Encoding(false));
        Console.WriteLine(PythonJson.Compact(NormalizeYaml(MiniYaml.ParseAny(body))));
        return 0;
    }
    catch (Exception exc)
    {
        // 受控失败：子集外/坏输入都只许给可读错误 + exit 2（此前未捕获 → 打印栈，属工具级缺陷）
        Console.Error.WriteLine("错误（受控失败）：" + exc.Message);
        return 2;
    }
}

if (args.Length >= 3 && args[0] == "--yaml-fence")
{
    try
    {
        var text = File.ReadAllText(args[1], new UTF8Encoding(false));
        var parsed = MiniYaml.ParseFence(text, args[2]);
        Console.WriteLine(PythonJson.Compact(parsed is null ? null : NormalizeYaml(parsed)));
        return 0;
    }
    catch (Exception exc)
    {
        Console.Error.WriteLine("错误（受控失败）：" + exc.Message);
        return 2;
    }
}

var root = args.Length > 0 ? args[0] : ".";
var certPath = Path.Combine(root, "protocol", "combo_certificates.json");
if (!File.Exists(certPath))
{
    Console.Error.WriteLine("找不到向量文件：" + certPath);
    return 2;
}

using var doc = JsonIo.ReadFile(certPath);
if (!doc.RootElement.TryGetProperty("certificates", out var certs) || certs.ValueKind != JsonValueKind.Array)
{
    Console.Error.WriteLine("向量文件结构不符：缺少 certificates 数组");
    return 2;
}

var ok = 0;
var bad = 0;
var index = 0;

Console.WriteLine("== NF .NET 引擎 · 证书摘要等价校验 ==");
Console.WriteLine("向量：" + certPath);

foreach (var cert in certs.EnumerateArray())
{
    index++;
    var label = cert.TryGetProperty("label", out var l) && l.ValueKind == JsonValueKind.String
        ? l.GetString()!
        : ("#" + index);
    var stored = cert.TryGetProperty(CertDigest.DigestKey, out var d) && d.ValueKind == JsonValueKind.String
        ? d.GetString()
        : null;
    // 判据（主）：台账口径 —— 在盘 digest 覆盖的是未附加 label/note 的证书体
    var ledgerDigest = CertDigest.LedgerDigest(cert);
    // 参照（副）：引擎口径 —— Python _digest 语义（只剔除 digest，会把 label/note 计入）
    var engineDigest = CertDigest.EngineDigest(cert);

    if (stored == ledgerDigest)
    {
        ok++;
        var extra = stored == engineDigest ? "" : "（引擎口径不同：label/note 不参与在盘摘要）";
        Console.WriteLine($"  OK   {label,-28} digest={ledgerDigest}{extra}");
    }
    else
    {
        bad++;
        Console.WriteLine($"  FAIL {label,-28} 盘上={stored ?? "(缺失)"} 台账口径={ledgerDigest} 引擎口径={engineDigest}");
    }
}

Console.WriteLine($"—— 证书 {index} 条 · 摘要一致 {ok} · 不一致 {bad}（判据=台账口径）");
return bad == 0 ? 0 : 1;

static int CanonicalDiff(string expectedPath, string repoRoot)
{
    using var expectedDoc = JsonIo.ReadFile(expectedPath);
    if (expectedDoc.RootElement.ValueKind != JsonValueKind.Array)
    {
        Console.Error.WriteLine("期望文件必须是字符串数组");
        return 2;
    }

    var certPath = Path.Combine(repoRoot, "protocol", "combo_certificates.json");
    using var certDoc = JsonIo.ReadFile(certPath);
    var certs = certDoc.RootElement.GetProperty("certificates");

    var i = 0;
    foreach (var cert in certs.EnumerateArray())
    {
        var expected = expectedDoc.RootElement[i].GetString()!;
        var actual = PythonJson.Canonicalize(cert, CertDigest.DigestKey);
        i++;

        if (expected == actual)
        {
            Console.WriteLine($"  OK   #{i} 规范串逐字节一致（长度 {actual.Length}）");
            continue;
        }

        var n = Math.Min(expected.Length, actual.Length);
        var k = 0;
        while (k < n && expected[k] == actual[k]) k++;
        Console.WriteLine($"  DIFF #{i} 期望长度={expected.Length} 实测长度={actual.Length} 首个差异偏移={k}");
        var start = Math.Max(0, k - 40);
        Console.WriteLine("    期望: " + Slice(expected, start).Replace("\n", "\\n"));
        Console.WriteLine("    实测: " + Slice(actual, start).Replace("\n", "\\n"));
        return 1;
    }
    return 0;

    static string Slice(string s, int start) => s.Substring(start, Math.Min(90, s.Length - start));
}

static int ProtocolParity(string expectedPath, string repoRoot)
{
    using var expectedDoc = JsonIo.ReadFile(expectedPath);
    var expected = expectedDoc.RootElement;

    var communityDir = Path.Combine(repoRoot, "community");
    if (!Directory.Exists(communityDir))
    {
        Console.Error.WriteLine("找不到 community 目录：" + communityDir);
        return 2;
    }

    var packDirs = Directory.GetDirectories(communityDir)
        .Where(d => File.Exists(Path.Combine(d, "protocol.yaml")))
        .OrderBy(d => Path.GetFileName(d), StringComparer.Ordinal)
        .ToList();

    var ok = 0;
    var bad = 0;
    Console.WriteLine("== NF .NET 引擎 · protocol.yaml 解析等价校验 ==");
    Console.WriteLine($"包数（.NET 侧发现）={packDirs.Count}｜期望表={expected.EnumerateObject().Count()}");

    foreach (var dir in packDirs)
    {
        var name = Path.GetFileName(dir);
        var text = File.ReadAllText(Path.Combine(dir, "protocol.yaml"), new UTF8Encoding(false));
        var parsed = ProtocolYaml.Parse(text, name);

        if (!expected.TryGetProperty(name, out var exp))
        {
            bad++;
            Console.WriteLine($"  FAIL {name} 期望表缺失");
            continue;
        }

        var diffs = new List<string>();

        if (parsed.Id != exp.GetProperty("id").GetString()) diffs.Add("id");
        if (parsed.Pipeline != exp.GetProperty("pipeline").GetString()) diffs.Add("pipeline");

        var expIds = exp.GetProperty("module_ids").EnumerateArray().Select(x => x.GetString()!).ToList();
        if (!parsed.ModuleIds.SequenceEqual(expIds)) diffs.Add("module_ids");

        var expLayers = exp.GetProperty("mount_layers");
        var expLayerNames = expLayers.EnumerateObject().Select(p => p.Name)
            .OrderBy(x => x, StringComparer.Ordinal).ToList();
        if (!expLayerNames.SequenceEqual(parsed.MountLayers.Keys))
        {
            diffs.Add("mount_layers.keys");
        }
        else
        {
            foreach (var kv in expLayers.EnumerateObject())
            {
                var expMods = kv.Value.EnumerateArray().Select(x => x.GetString()!).ToList();
                if (!parsed.MountLayers[kv.Name].SequenceEqual(expMods))
                {
                    diffs.Add("mount_layers." + kv.Name);
                    break;
                }
            }
        }

        var expRefs = exp.GetProperty("references").EnumerateArray()
            .Select(r => (Src: r.GetProperty("source_package").GetString()!,
                          Mod: r.GetProperty("module_id").GetString()!)).ToList();
        if (expRefs.Count != parsed.References.Count)
        {
            diffs.Add("references.count");
        }
        else
        {
            for (var i = 0; i < expRefs.Count; i++)
            {
                if (expRefs[i].Src != parsed.References[i].SourcePackage ||
                    expRefs[i].Mod != parsed.References[i].ModuleId)
                {
                    diffs.Add("references[" + i + "]");
                    break;
                }
            }
        }

        if (diffs.Count == 0) ok++;
        else
        {
            bad++;
            Console.WriteLine($"  FAIL {name} 差异字段：{string.Join("、", diffs)}");
        }
    }

    Console.WriteLine($"—— 包 {packDirs.Count} 个 · 解析等价 {ok} · 不一致 {bad}");
    return bad == 0 ? 0 : 1;
}

// --contracts-parity <community期望.json> <core期望.json> <repo-root>
static int ContractsParity(string expectedPath, string coreExpectedPath, string repoRoot)
{
    var problems = new List<string>();

    using (var expDoc = JsonIo.ReadFile(expectedPath))
    {
        var expRecords = expDoc.RootElement.GetProperty("records");
        var expKeys = expDoc.RootElement.GetProperty("keys");
        var extraction = ModuleContracts.Community(repoRoot);

        Console.WriteLine("== NF .NET 引擎 · machine_contract 抽取等价校验 ==");
        Console.WriteLine($"期望契约 {expRecords.EnumerateObject().Count()} 条 · 期望键 {expKeys.EnumerateObject().Count()} 个");
        Console.WriteLine($"实测契约 {extraction.KeyToId.Values.Distinct(StringComparer.Ordinal).Count()} 条 · 实测键 {extraction.KeyToId.Count} 个");

        foreach (var prop in expRecords.EnumerateObject())
        {
            var id = prop.Name;
            var exp = prop.Value;
            var match = extraction.RecordsByKey.Values.FirstOrDefault(r => r.Id == id);
            if (match is null) { problems.Add("契约缺失：" + id); continue; }

            if (match.Stem != exp.GetProperty("stem").GetString()) problems.Add(id + " 字段 stem 不一致");
            if (match.Pack != exp.GetProperty("pack").GetString()) problems.Add(id + " 字段 pack 不一致");
            if (match.Layer != exp.GetProperty("layer").GetString()) problems.Add(id + " 字段 layer 不一致");
            if (match.Path != exp.GetProperty("path").GetString()) problems.Add(id + " 字段 path 不一致");

            var expStrings = exp.GetProperty("inputs").EnumerateArray().Select(x => x.GetString()!).ToList();
            if (!match.Inputs.SequenceEqual(expStrings)) problems.Add(id + " 字段 inputs 不一致");
            expStrings = exp.GetProperty("outputs").EnumerateArray().Select(x => x.GetString()!).ToList();
            if (!match.Outputs.SequenceEqual(expStrings)) problems.Add(id + " 字段 outputs 不一致");
            expStrings = exp.GetProperty("publish").EnumerateArray().Select(x => x.GetString()!).ToList();
            if (!match.Publish.SequenceEqual(expStrings)) problems.Add(id + " 字段 publish 不一致");
            expStrings = exp.GetProperty("subscribe").EnumerateArray().Select(x => x.GetString()!).ToList();
            if (!match.Subscribe.SequenceEqual(expStrings)) problems.Add(id + " 字段 subscribe 不一致");
        }

        if (expKeys.EnumerateObject().Count() != extraction.KeyToId.Count)
            problems.Add($"键总数不一致：实测={extraction.KeyToId.Count} 期望={expKeys.EnumerateObject().Count()}");
        foreach (var prop in expKeys.EnumerateObject())
        {
            if (!extraction.KeyToId.TryGetValue(prop.Name, out var actualId))
                problems.Add("键缺失：" + prop.Name);
            else if (actualId != prop.Value.GetString())
                problems.Add($"键 {prop.Name} 指向不一致：实测={actualId} 期望={prop.Value.GetString()}");
        }
    }

    using (var coreDoc = JsonIo.ReadFile(coreExpectedPath))
    {
        var expCore = coreDoc.RootElement.GetProperty("records");
        var actualCore = ModuleContracts.Core(repoRoot);
        Console.WriteLine($"核心：期望 {expCore.EnumerateObject().Count()} 键 · 实测 {actualCore.Count} 键");

        foreach (var prop in expCore.EnumerateObject())
        {
            if (!actualCore.TryGetValue(prop.Name, out var rec)) { problems.Add("核心键缺失：" + prop.Name); continue; }
            var exp = prop.Value;
            if (rec.Id != exp.GetProperty("id").GetString()) problems.Add(prop.Name + " 核心 id 不一致");
            if (rec.Stem != exp.GetProperty("stem").GetString()) problems.Add(prop.Name + " 核心 stem 不一致");
            if (rec.Path != exp.GetProperty("path").GetString()) problems.Add(prop.Name + " 核心 path 不一致");
            var expPub = exp.GetProperty("publish").EnumerateArray().Select(x => x.GetString()!).ToList();
            if (!rec.Publish.SequenceEqual(expPub)) problems.Add(prop.Name + " 核心 publish 不一致");
            var expSub = exp.GetProperty("subscribe").EnumerateArray().Select(x => x.GetString()!).ToList();
            if (!rec.Subscribe.SequenceEqual(expSub)) problems.Add(prop.Name + " 核心 subscribe 不一致");
        }
    }

    if (problems.Count == 0)
    {
        Console.WriteLine("—— 契约抽取等价：全部一致");
        return 0;
    }
    Console.WriteLine($"—— 不一致 {problems.Count} 项，前 10 项：");
    foreach (var p in problems.Take(10)) Console.WriteLine("   " + p);
    return 1;
}

// --profiles-parity <expected.json> <repo-root>
static int ProfilesParity(string expectedPath, string repoRoot)
{
    using var expDoc = JsonIo.ReadFile(expectedPath);
    var expected = expDoc.RootElement;
    var actual = PackProfiles.Build(repoRoot);
    var problems = new List<string>();

    Console.WriteLine("== NF .NET 引擎 · 组合画像等价校验 ==");
    Console.WriteLine($"期望画像 {expected.EnumerateObject().Count()} 个 · 实测 {actual.Count} 个");

    foreach (var prop in expected.EnumerateObject())
    {
        var pkg = prop.Name;
        var exp = prop.Value;
        if (!actual.TryGetValue(pkg, out var prof)) { problems.Add("画像缺失：" + pkg); continue; }

        if (prof.Pipeline != exp.GetProperty("pipeline").GetString()) problems.Add(pkg + " pipeline 不一致");

        var expModules = exp.GetProperty("modules").EnumerateArray().Select(x => x.GetString()!).ToList();
        if (!prof.Modules.SequenceEqual(expModules)) problems.Add(pkg + " modules 不一致");

        var expRefs = exp.GetProperty("references").EnumerateArray()
            .Select(r => (Src: r[0].GetString()!, Mod: r[1].GetString()!)).ToList();
        if (expRefs.Count != prof.References.Count) problems.Add(pkg + " references 数量不一致");
        else
        {
            for (var i = 0; i < expRefs.Count; i++)
            {
                if (expRefs[i].Src != prof.References[i].SourcePackage ||
                    expRefs[i].Mod != prof.References[i].ModuleId)
                { problems.Add(pkg + " references 不一致"); break; }
            }
        }

        var expLayers = exp.GetProperty("layers");
        var expLayerNames = expLayers.EnumerateObject().Select(p => p.Name).ToList();
        if (!expLayerNames.SequenceEqual(prof.Layers.Keys)) problems.Add(pkg + " layers 键不一致");
        else
        {
            foreach (var kv in expLayers.EnumerateObject())
            {
                var expVals = kv.Value.EnumerateArray().Select(x => x.GetString()!).ToList();
                if (!prof.Layers[kv.Name].SequenceEqual(expVals)) { problems.Add(pkg + " layers[" + kv.Name + "] 不一致"); break; }
            }
        }

        var expAssets = exp.GetProperty("assets").EnumerateArray()
            .Select(a => (K: a[0].GetString()!, F: a[1].GetString()!, M: a[2].GetString()!, S: a[3].GetString()!)).ToList();
        if (expAssets.Count != prof.Assets.Count) problems.Add(pkg + " assets 数量不一致");
        else
        {
            for (var i = 0; i < expAssets.Count; i++)
            {
                var a = prof.Assets[i];
                var e = expAssets[i];
                if (a.Key != e.K || a.File != e.F || a.Module != e.M || a.SourcePackage != e.S)
                { problems.Add(pkg + " assets 不一致"); break; }
            }
        }

        var expPub = exp.GetProperty("publishes").EnumerateArray().Select(x => x.GetString()!).ToList();
        if (!prof.Publishes.SequenceEqual(expPub)) problems.Add(pkg + " publishes 不一致");
        var expSub = exp.GetProperty("subscribes").EnumerateArray().Select(x => x.GetString()!).ToList();
        if (!prof.Subscribes.SequenceEqual(expSub)) problems.Add(pkg + " subscribes 不一致");
    }

    if (problems.Count == 0) { Console.WriteLine("—— 画像等价：全部一致"); return 0; }
    Console.WriteLine($"—— 不一致 {problems.Count} 项，前 12 项：");
    foreach (var p in problems.Take(12)) Console.WriteLine("   " + p);
    return 1;
}

// --combine-parity <expected.json> <repo-root>
static int CombineParity(string expectedPath, string repoRoot)
{
    using var expDoc = JsonIo.ReadFile(expectedPath);
    var expected = expDoc.RootElement;
    var ok = 0;
    var bad = 0;

    Console.WriteLine("== NF .NET 引擎 · 组合证书全字段等价校验 ==");
    foreach (var prop in expected.EnumerateObject())
    {
        var exp = prop.Value;
        var label = exp.GetProperty("label").GetString() ?? ("#" + prop.Name);
        var packs = exp.GetProperty("packs").EnumerateArray().Select(x => x.GetString()!).ToList();
        var extraModules = exp.GetProperty("extra_modules").EnumerateArray().Select(x => x.GetString()!).ToList();

        var result = Combinator.Build(repoRoot, packs, extraModules);
        var actualCanonical = PythonJson.CanonicalizeGraph(result.Certificate);
        var expectedCanonical = PythonJson.Canonicalize(exp.GetProperty("cert"));

        if (expectedCanonical == actualCanonical)
        {
            ok++;
            Console.WriteLine($"  OK   {label,-28} digest={result.Digest} 模块={result.Certificate["module_count"]}");
            continue;
        }

        bad++;
        var n = Math.Min(expectedCanonical.Length, actualCanonical.Length);
        var k = 0;
        while (k < n && expectedCanonical[k] == actualCanonical[k]) k++;
        Console.WriteLine($"  DIFF {label,-28} 期望长度={expectedCanonical.Length} 实测={actualCanonical.Length} 偏移={k}");
        var start = Math.Max(0, k - 60);
        Console.WriteLine("    期望: " + Slice2(expectedCanonical, start));
        Console.WriteLine("    实测: " + Slice2(actualCanonical, start));
    }

    Console.WriteLine($"—— 证书 {ok + bad} 条 · 全字段等价 {ok} · 不一致 {bad}");
    return bad == 0 ? 0 : 1;

    static string Slice2(string s, int start) => s.Substring(start, Math.Min(120, s.Length - start));
}

// --receipts-verify <repo-root>：三件仓库产物的独立复算（协议回执 / 馆藏回执 / 透明链）
static int ReceiptsVerify(string repoRoot)
{
    Console.WriteLine("== NF .NET 引擎 · 回执与透明链独立复算 ==");
    var results = new[]
    {
        Receipts.VerifyProtocolReceipts(repoRoot),
        Receipts.VerifyLibraryReceipts(repoRoot),
        Receipts.VerifyTransparencyChain(repoRoot),
    };

    var bad = 0;
    foreach (var r in results)
    {
        Console.WriteLine($"  {(r.Ok ? "OK  " : "FAIL")} {r.Name,-42} {r.Detail}");
        foreach (var issue in r.Issues.Take(5)) Console.WriteLine("         · " + issue);
        if (!r.Ok) bad++;
    }
    Console.WriteLine($"—— 产物 {results.Length} 件 · 通过 {results.Length - bad} · 失败 {bad}");
    return bad == 0 ? 0 : 1;
}

// --sampler-parity <python_samples.json> <repo-root>
// 判据：C# 自足抽样（MT19937 复刻）生成的样本集与 Python 导出样本**逐项相等**。
static int SamplerParity(string samplesPath, string repoRoot)
{
    using var doc = JsonIo.ReadFile(samplesPath);
    var expected = doc.RootElement;
    var actual = Breadth.GenerateSamples(repoRoot, Breadth.DefaultSeed);
    var ok = 0;
    var bad = 0;

    Console.WriteLine("== NF .NET 引擎 · 抽样器逐位等价校验 ==");
    foreach (var key in new[] { "triples", "quads", "quints", "sexts" })
    {
        var exp = expected.TryGetProperty(key, out var e) && e.ValueKind == JsonValueKind.Array
            ? e.EnumerateArray().Select(c => string.Join("\u0000", c.EnumerateArray().Select(x => x.GetString()!))).ToList()
            : new List<string>();
        var act = actual[key].Select(c => string.Join("\u0000", c)).ToList();

        if (exp.SequenceEqual(act))
        {
            ok++;
            Console.WriteLine($"  OK   {key,-8} {act.Count} 组逐项一致");
        }
        else
        {
            bad++;
            var idx = 0;
            while (idx < Math.Min(exp.Count, act.Count) && exp[idx] == act[idx]) idx++;
            Console.WriteLine($"  DIFF {key,-8} 期望 {exp.Count} 组 / 实测 {act.Count} 组 · 首个差异 #{idx}");
            if (idx < exp.Count) Console.WriteLine("    期望: " + exp[idx]);
            if (idx < act.Count) Console.WriteLine("    实测: " + act[idx]);
        }
    }
    Console.WriteLine($"—— 抽样档 {ok + bad} · 逐位一致 {ok} · 不一致 {bad}");
    return bad == 0 ? 0 : 1;
}

// --breadth <samples.json> <repo-root> [--serial]
// stdout 输出与 Python `nf combine breadth --json` 同形的统计；计时写到 stderr（不污染 stdout 的逐字节比对）
static int BreadthRun(string samplesPath, string repoRoot, bool serial)
{
    using var samples = JsonIo.ReadFile(samplesPath);
    var sw = System.Diagnostics.Stopwatch.StartNew();
    var stats = Breadth.Run(repoRoot, samples.RootElement, parallel: !serial);
    Console.Error.WriteLine($"breadth 用时 {(serial ? "串行" : "并行")} = {sw.ElapsedMilliseconds} ms");
    Console.WriteLine(PythonJson.Indented(stats));
    return stats["all_legal"] is true ? 0 : 1;
}

// --bench <repo-root>：分段计时（进程启动由外部测量）
// YAML 图 → 可比较的规范形态：日期/时间只留类型标记（两侧同形；值比较见 probe 说明）
static object? NormalizeYaml(object? node) => node switch
{
    PyScalar.Timestamp ts => new Dictionary<string, object?>(StringComparer.Ordinal)
    {
        ["__pytype__"] = ts.Kind,
    },
    Dictionary<string, object?> map => map.ToDictionary(
        kv => kv.Key, kv => NormalizeYaml(kv.Value), StringComparer.Ordinal),
    List<object?> list => list.Select(NormalizeYaml).ToList(),
    _ => node,
};

static int Bench(string repoRoot)
{
    var sw = System.Diagnostics.Stopwatch.StartNew();
    var cache = RepoCache.For(repoRoot);
    var parseMs = sw.ElapsedMilliseconds;

    sw.Restart();
    var extreme = Combinator.Build(repoRoot, cache.Profiles.Keys.ToList());
    var extremeMs = sw.ElapsedMilliseconds;

    using var doc = JsonIo.ReadFile(Path.Combine(repoRoot, "protocol", "combo_certificates.json"));
    var certs = doc.RootElement.GetProperty("certificates").EnumerateArray().ToList();
    sw.Restart();
    foreach (var c in certs)
    {
        var packs = c.GetProperty("packs").EnumerateArray().Select(x => x.GetString()!).ToList();
        var extra = c.GetProperty("extra_modules").EnumerateArray().Select(x => x.GetString()!).ToList();
        _ = Combinator.Build(repoRoot, packs, extra);
    }
    var allMs = sw.ElapsedMilliseconds;

    Console.WriteLine($"解析全仓（111 包 / 235 模块契约）: {parseMs} ms");
    Console.WriteLine($"极限工况解算（全部 {cache.Profiles.Count} 包 · {extreme.Certificate["module_count"]} 模块）: {extremeMs} ms");
    Console.WriteLine($"17 条证书解算（缓存后）: {allMs} ms");
    return 0;
}
