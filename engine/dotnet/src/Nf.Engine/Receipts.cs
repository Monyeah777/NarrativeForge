using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 回执与透明链复算（C# 侧独立实现）：
/// ① 协议层回执 <c>protocol/RECEIPTS.json</c>（51 件）：条目摘要 = 文件字节 sha256；
/// ② 馆藏回执 <c>library/RECEIPTS.json</c>（3 件）：条目摘要 = 剔除签名/锚行后的整文 sha256；
/// ③ 透明链 <c>protocol/generated/receipt_chain.json</c>：<c>chain[i]=H(0x01nf-node:|prev|leaf[i])</c>。
///
/// 全部按 RFC 6962 风格域分隔：叶 = <c>sha256(0x00 ‖ 载荷)</c>，节点 = <c>sha256(0x01 ‖ 左 ‖ 右)</c>。
/// </summary>
public static class Receipts
{
    private static readonly Regex AnchorLineRe =
        new(@"^(attestation|attested_at|anchor_[a-z_]+)\s*:", RegexOptions.Multiline);

    private static readonly byte[] LeafPrefix = { 0x00 };
    private static readonly byte[] NodePrefix = { 0x01 };
    private static readonly byte[] ChainLeafPrefix = Encoding.ASCII.GetBytes("\u0000nf-leaf:");
    private static readonly byte[] ChainNodePrefix = Encoding.ASCII.GetBytes("\u0001nf-node:");

    private static byte[] Sha256(params byte[][] parts)
    {
        using var sha = SHA256.Create();
        foreach (var p in parts)
        {
            sha.TransformBlock(p, 0, p.Length, null, 0);
        }
        sha.TransformFinalBlock(Array.Empty<byte>(), 0, 0);
        return sha.Hash!;
    }

    private static byte[] Leaf(byte[] payload) => Sha256(LeafPrefix, payload);
    private static byte[] Node(byte[] left, byte[] right) => Sha256(NodePrefix, left, right);

    private static byte[] MerkleRoot(IReadOnlyList<byte[]> leaves)
    {
        if (leaves.Count == 0) return Array.Empty<byte>();
        if (leaves.Count == 1) return leaves[0];
        var mid = 1;
        while (mid * 2 < leaves.Count) mid *= 2;
        return Node(MerkleRoot(leaves.Take(mid).ToList()), MerkleRoot(leaves.Skip(mid).ToList()));
    }

    private static byte[] Fold(byte[] leaf, IEnumerable<(string Side, byte[] Hash)> proof)
    {
        var current = leaf;
        foreach (var (side, sibling) in proof)
        {
            current = side == "left" ? Node(sibling, current) : Node(current, sibling);
        }
        return current;
    }

    private static string Hex(byte[] bytes) => Convert.ToHexString(bytes).ToLowerInvariant();

    /// <summary>协议层条目的「最简载荷」：Python 侧 <c>json.dumps({"id":…, "digest":…}, sort_keys=True, separators=(",",":"))</c>。</summary>
    private static byte[] CompactPayload(string id, string digest)
        => Encoding.UTF8.GetBytes("{\"digest\":" + PythonJson.Quote(digest) + ",\"id\":" + PythonJson.Quote(id) + "}");

    /// <summary>协议层条目摘要 = 文件字节 sha256。</summary>
    public static string ProtocolFileDigest(string root, string rel)
        => Hex(SHA256.HashData(File.ReadAllBytes(Path.Combine(root, rel))));

    /// <summary>馆藏条目摘要 = 剔除 <c>attestation</c> / <c>attested_at</c> / <c>anchor_*</c> 行后的整文 sha256（换行统一为 \n）。</summary>
    public static string LibraryEntryDigest(string root, string rel)
    {
        var bytes = File.ReadAllBytes(Path.Combine(root, rel));
        var text = new UTF8Encoding(false).GetString(bytes).Replace("\r\n", "\n").Replace('\r', '\n');
        var kept = text.Split('\n').Where(line => !AnchorLineRe.IsMatch(line));
        return Hex(SHA256.HashData(Encoding.UTF8.GetBytes(string.Join("\n", kept))));
    }

    public sealed record ArtifactResult(string Name, bool Ok, IReadOnlyList<string> Issues, string Detail,
        int Count, string Root);

    /// <summary>真源 <c>receipts.SCHEMA</c>。</summary>
    public const string Schema = "nf-receipts/1";

    /// <summary>馆藏侧实时复算结果（真源 <c>receipts.build(root)</c> 的可核验部分）。</summary>
    public sealed record LibraryLive(long Count, string Root, List<LibraryLiveEntry> Entries);
    public sealed record LibraryLiveEntry(string Id, string Path, string Digest, string Leaf,
        List<Dictionary<string, object?>> Proof);

    /// <summary>
    /// 真源 <c>receipts.build(root)</c>（**馆藏作用域**）：从馆藏条目实时算全馆根 + 逐条 inclusion proof。
    /// 叶子载荷 = <c>json.dumps({"id","digest"}, sort_keys, separators=(",",":"))</c>；
    /// 条目顺序 = <c>library.entries(root)</c>（按 id 排序）。
    /// </summary>
    public static LibraryLive BuildLibrary(string root)
    {
        var rows = Library.Entries(root);
        var digests = new List<string>();
        var leaves = new List<byte[]>();
        foreach (var entry in rows)
        {
            var digest = LibraryEntryDigest(root, entry.Path);
            digests.Add(digest);
            leaves.Add(Leaf(CompactPayload(entry.Id, digest)));
        }
        var rootHash = MerkleRoot(leaves);
        var entries = new List<LibraryLiveEntry>();
        for (var i = 0; i < rows.Count; i++)
        {
            entries.Add(new LibraryLiveEntry(rows[i].Id, rows[i].Path, digests[i], Hex(leaves[i]),
                InclusionProof(leaves, i)));
        }
        return new LibraryLive(rows.Count, rootHash.Length == 0 ? "" : Hex(rootHash), entries);
    }

    /// <summary>真源 <c>receipts.inclusion_proof</c>：**自底向上**（返回前整体反转）。</summary>
    public static List<Dictionary<string, object?>> InclusionProof(IReadOnlyList<byte[]> leaves, int index)
    {
        if (leaves.Count == 0 || index < 0 || index >= leaves.Count)
            throw new IndexOutOfRangeException($"叶子下标越界：{index}（共 {leaves.Count} 叶）");
        var proof = new List<(string Side, byte[] Hash)>();
        void Walk(IReadOnlyList<byte[]> sub, int i)
        {
            if (sub.Count <= 1) return;
            var mid = 1;
            while (mid * 2 < sub.Count) mid *= 2;
            if (i < mid)
            {
                proof.Add(("right", MerkleRoot(sub.Skip(mid).ToList())));
                Walk(sub.Take(mid).ToList(), i);
            }
            else
            {
                proof.Add(("left", MerkleRoot(sub.Take(mid).ToList())));
                Walk(sub.Skip(mid).ToList(), i - mid);
            }
        }
        Walk(leaves, index);
        proof.Reverse();
        return proof.Select(step => (Dictionary<string, object?>)new Dictionary<string, object?>(
            StringComparer.Ordinal)
        {
            ["side"] = step.Side, ["hash"] = Hex(step.Hash),
        }).ToList();
    }

    /// <summary>① 协议层回执：重算每条摘要与叶 → 折叠到根 → 全叶重算根 → 与记录比对。</summary>
    public static ArtifactResult VerifyProtocolReceipts(string root)
        => VerifyProtocolReceipts(root, JsonIo.ReadFile(Path.Combine(root, "protocol/RECEIPTS.json")));

    /// <summary>可注入文档版本：供负例自检在内存里篡改记录后仍能走同一校验路径。</summary>
    public static ArtifactResult VerifyProtocolReceipts(string root, JsonDocument doc)
    {
        var issues = new List<string>();
        var recordRoot = doc.RootElement.GetProperty("root").GetString() ?? "";
        var entries = doc.RootElement.GetProperty("entries").EnumerateArray().ToList();

        var leaves = new List<byte[]>();
        foreach (var entry in entries)
        {
            var id = entry.GetProperty("id").GetString()!;
            var recordedDigest = entry.GetProperty("digest").GetString()!;
            var recordedLeaf = entry.GetProperty("leaf").GetString()!;
            var path = Path.Combine(root, id);
            if (!File.Exists(path)) { issues.Add("缺文件：" + id); continue; }

            var digest = ProtocolFileDigest(root, id);
            if (digest != recordedDigest) issues.Add("条目摘要不一致：" + id);
            var leaf = Leaf(CompactPayload(id, digest));
            if (Hex(leaf) != recordedLeaf) issues.Add("叶不一致：" + id);
            leaves.Add(leaf);

            var proof = entry.GetProperty("proof").EnumerateArray()
                .Select(p => (Side: p.GetProperty("side").GetString()!, Hash: Convert.FromHexString(p.GetProperty("hash").GetString()!)))
                .ToList();
            if (Hex(Fold(leaf, proof)) != recordRoot) issues.Add("包含证明不折叠到根：" + id);
        }

        var liveRoot = Hex(MerkleRoot(leaves));
        if (liveRoot != recordRoot) issues.Add($"根不一致：记录={Short(recordRoot)} 实测={Short(liveRoot)}");
        return new ArtifactResult("protocol/RECEIPTS.json", issues.Count == 0, issues,
            $"{entries.Count} 条 · 根 {Short(liveRoot)}", entries.Count, liveRoot);
    }

    /// <summary>② 馆藏回执：同上，但条目摘要走「剔除锚行」规则。</summary>
    public static ArtifactResult VerifyLibraryReceipts(string root)
        => VerifyLibraryReceipts(root, JsonIo.ReadFile(Path.Combine(root, "library/RECEIPTS.json")));

    /// <summary>可注入文档版本（同上）。</summary>
    public static ArtifactResult VerifyLibraryReceipts(string root, JsonDocument doc)
    {
        var issues = new List<string>();
        var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
                    ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        // 真源：schema 不匹配 → 立刻返回（stats 空），不做任何折叠判定。
        if (PyStr(graph.GetValueOrDefault("schema")) != Schema)
            return new ArtifactResult("library/RECEIPTS.json", false,
                new List<string> { $"回执文件 schema 不匹配（期望 {Schema}）" }, "", 0, "");

        var live = BuildLibrary(root);
        var recordRoot = PyStr(graph.GetValueOrDefault("root"));
        if (recordRoot != live.Root)
        {
            issues.Add($"根不一致：记录={Short(recordRoot)} 实测={Short(live.Root)}"
                       + "（修复指引：馆藏改动后跑 nf library receipts --write）");
        }
        var liveById = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (var entry in live.Entries) liveById[entry.Id] = entry.Digest;
        var docEntries = ObjList(graph.GetValueOrDefault("entries"));
        foreach (var item in docEntries)
        {
            var row = item as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var eid = PyStr(row.GetValueOrDefault("id"));
            if (!liveById.TryGetValue(eid, out var liveDigest))
            {
                issues.Add("回执指向不存在的条目：" + eid);
                continue;
            }
            if (PyStr(row.GetValueOrDefault("digest")) != liveDigest)
                issues.Add($"条目内容已变：{eid}（修复指引：重签该条并重建回执）");
            if (FoldProof(PyStr(row.GetValueOrDefault("leaf")), row.GetValueOrDefault("proof")) != recordRoot)
                issues.Add("包含证明不折叠到根：" + eid);
        }
        if (docEntries.Count != live.Count)
            issues.Add($"回执条数 {docEntries.Count} ≠ 馆藏条数 {live.Count}");
        return new ArtifactResult("library/RECEIPTS.json", issues.Count == 0, issues,
            $"{live.Count} 条 · 根 {Short(live.Root)}", (int)live.Count, live.Root);
    }

    /// <summary>真源 <c>fold_proof(leaf_hex, proof)</c>：按证明逐层折叠出根（十六进制串在手）。</summary>
    public static string FoldProof(string leafHex, object? proof)
    {
        var steps = new List<(string Side, byte[] Hash)>();
        foreach (var item in ObjList(proof))
        {
            var row = item as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var hash = PyStr(row.GetValueOrDefault("hash"));
            steps.Add((PyStr(row.GetValueOrDefault("side")), Convert.FromHexString(hash)));
        }
        if (leafHex.Length == 0) return "";
        return Hex(Fold(Convert.FromHexString(leafHex), steps));
    }

    private static List<object?> ObjList(object? value) => value as List<object?> ?? new List<object?>();

    /// <summary>check35 第二条腿的框法：issues 逐条 <c>[FAIL] 馆藏回执：…</c>，末行 <c>馆藏回执 子扫描：…</c>。</summary>
    public static List<string> LibraryLog(ArtifactResult result, string label = "馆藏回执")
    {
        var lines = result.Issues.Select(issue => "[FAIL] " + label + "：" + issue).ToList();
        lines.Add($"{label} 子扫描：{(result.Issues.Count == 0 ? "零缺口" : "FAIL " + result.Issues.Count)}");
        return lines;
    }

    public static string LibraryLogDigest(ArtifactResult result, string label = "馆藏回执") =>
        ExitFaces.Digest32(LibraryLog(result, label));

    private static string PyStr(object? value) => value switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        _ => Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture) ?? "None",
    };

    /// <summary>③ 透明链：从协议回执重算 <c>chain[i] = H(0x01nf-node: | prev | leaf[i])</c>。</summary>
    public static ArtifactResult VerifyTransparencyChain(string root)
        => VerifyTransparencyChain(root,
            JsonIo.ReadFile(Path.Combine(root, "protocol/generated/receipt_chain.json")),
            JsonIo.ReadFile(Path.Combine(root, "protocol/RECEIPTS.json")));

    /// <summary>可注入文档版本（同上）。</summary>
    public static ArtifactResult VerifyTransparencyChain(string root, JsonDocument chainDoc, JsonDocument recDoc)
    {
        var issues = new List<string>();
        var entries = recDoc.RootElement.GetProperty("entries").EnumerateArray().ToList();
        var links = chainDoc.RootElement.GetProperty("links").EnumerateArray().ToList();

        if (entries.Count != links.Count) issues.Add($"链节数不一致：回执={entries.Count} 链={links.Count}");

        var prev = new string('0', 64);
        for (var i = 0; i < links.Count; i++)
        {
            var entry = entries[i];
            var path = entry.GetProperty("path").GetString() ?? "";
            var digest = entry.GetProperty("digest").GetString() ?? "";
            var leaf = Hex(Sha256(ChainLeafPrefix, Encoding.UTF8.GetBytes("|"), Encoding.UTF8.GetBytes(path),
                Encoding.UTF8.GetBytes("|"), Encoding.UTF8.GetBytes(digest)));

            var link = links[i];
            if (link.GetProperty("leaf").GetString() != leaf) issues.Add($"链节 {i + 1} 叶不一致");
            if (link.GetProperty("prev").GetString() != prev) issues.Add($"链节 {i + 1} prev 不一致");
            var node = Hex(Sha256(ChainNodePrefix, Encoding.UTF8.GetBytes("|"), Encoding.ASCII.GetBytes(prev),
                Encoding.UTF8.GetBytes("|"), Encoding.ASCII.GetBytes(leaf)));
            if (link.GetProperty("chain").GetString() != node) issues.Add($"链节 {i + 1} chain 不一致");
            prev = node;
        }

        var head = chainDoc.RootElement.GetProperty("head").GetString() ?? "";
        if (head != prev) issues.Add($"链头不一致：记录={Short(head)} 实测={Short(prev)}");
        if (chainDoc.RootElement.GetProperty("count").GetInt32() != links.Count) issues.Add("count 字段与链节数不一致");
        if (!chainDoc.RootElement.TryGetProperty("boundary", out var boundary) || boundary.GetString() is not { Length: > 0 })
            issues.Add("boundary 声明缺失（不可抵赖性边界必须显式在场）");

        return new ArtifactResult("protocol/generated/receipt_chain.json", issues.Count == 0, issues,
            $"{links.Count} 节 · 链头 {Short(prev)}", links.Count, prev);
    }

    /// <summary>
    /// Python 切片语义的「取前 16 位」：**短串不越界**（<c>"abc"[:16]</c> == <c>"abc"</c>）。
    ///
    /// 为什么需要：回执/链自洽检查在「条目全缺」时 liveRoot 是**空串**，直接 `[..16]` 会抛
    /// `ArgumentOutOfRangeException`（第九十片用空树/缺条目合成语料照出的既有缺陷）；真源遇到
    /// 短串不会崩，本件也不许崩——受控失败而不是崩栈。
    /// </summary>
    private static string Short(string hash) => hash.Length <= 16 ? hash : hash[..16];
}
