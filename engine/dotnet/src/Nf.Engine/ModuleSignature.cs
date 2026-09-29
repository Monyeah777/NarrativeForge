using System.Security.Cryptography;
using System.Text;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/module_signature.py</c>：模块**边界签名**基线（边界写一次、实现可替）。
///
/// 基线 = <c>protocol/module_signatures.json</c>（模块 id → 边界摘要）；**边界漂移 = FAIL**，
/// 直到显式 <c>nf module signature --write</c> 重新冻结；新增模块 / 基线里的模块消失 = WARN。
/// 纪律：只取**边界字段**（inputs/outputs/events/interfaces/layer/category/io_types），
/// 不含 description/note 等易变文本。
/// </summary>
public static class ModuleSignature
{
    public const string Schema = "nf-module-signatures/1";
    public const string BaselineRel = "protocol/module_signatures.json";
    public const string ContractDescription = "模块边界冻结";

    private static readonly string[] BoundaryKeys =
        { "inputs", "outputs", "events", "interfaces", "layer", "category", "io_types" };

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _, _) = Verify(root);
        return issues.Count == 0
            ? (true, "模块边界零漂移")
            : (false, string.Join("; ", issues.Take(2)));
    }

    /// <summary>全仓模块边界签名：id → (摘要, 边界, 路径)。</summary>
    public static Dictionary<string, (string Digest, Dictionary<string, object?> Boundary, string Path)>
        Signatures(string root)
    {
        var result = new Dictionary<string, (string, Dictionary<string, object?>, string)>(StringComparer.Ordinal);
        foreach (var (rel, contract, id) in ModuleDocs.Contracts(root))
        {
            var boundary = new Dictionary<string, object?>(StringComparer.Ordinal);
            foreach (var key in BoundaryKeys)
                boundary[key] = contract.TryGetValue(key, out var value) ? value : null;
            // 等价 Python：json.dumps(boundary, sort_keys=True, ensure_ascii=False, separators=(",",":"))
            var blob = Encoding.UTF8.GetBytes(PythonJson.Compact(boundary));
            result[id] = (Convert.ToHexString(SHA256.HashData(blob)).ToLowerInvariant(), boundary, rel);
        }
        return result;
    }

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Verify(
        string root, string rel = BaselineRel)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path))
        {
            return (new List<string> { $"缺模块边界基线 {rel}（修复指引：nf module signature --write）" },
                warns, new Dictionary<string, object?>(StringComparer.Ordinal));
        }
        using var doc = JsonIo.ReadFile(path);
        var baseline = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        var baselineModules = baseline.GetValueOrDefault("modules") as Dictionary<string, object?>
                              ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var signatures = Signatures(root);
        foreach (var (id, signature) in signatures.OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            if (!baselineModules.TryGetValue(id, out var record) || record is not Dictionary<string, object?> recordMap)
            {
                warns.Add($"新模块未签边界：{id}（修复指引：nf module signature --write）");
                continue;
            }
            var want = recordMap.GetValueOrDefault("digest")?.ToString() ?? "";
            if (want != signature.Digest)
            {
                issues.Add($"边界漂移：{id}（inputs/outputs/events/interfaces 变了）" +
                           "（修复指引：评审后 nf module signature --write 重新冻结）");
            }
        }
        foreach (var id in baselineModules.Keys.Except(signatures.Keys).OrderBy(x => x, StringComparer.Ordinal))
            warns.Add($"基线中的模块已不在仓库：{id}（修复指引：重签以撤下）");

        var drifted = issues.Select(i => i.Split('：').ElementAtOrDefault(1)?.Split('（').FirstOrDefault() ?? "")
            .ToList();
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["modules"] = signatures.Count,
            ["signed"] = baselineModules.Count,
            ["drifted"] = drifted.Cast<object?>().ToList(),
        };
        return (issues, warns, stats);
    }
}
