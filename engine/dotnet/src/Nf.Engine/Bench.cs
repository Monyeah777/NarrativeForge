using System.Diagnostics;

namespace Nf.Engine;

/// <summary>
/// 性能基线测量：把引擎的关键操作各测一遍（每项取两次的最小值，压低噪声），
/// 供 CLI 与基线文件比对、做**回归门**。
///
/// 注意：这是 .NET 侧自有能力（Python 侧没有等价单命令），故不做逐字节对账；
/// 它的判据是"相对自己上一次不许显著变慢"。
/// </summary>
public static class Bench
{
    public sealed record Measurement(string Name, double Milliseconds, string Detail);

    public static List<Measurement> Run(string root)
    {
        var results = new List<Measurement>();

        results.Add(Measure("parse", () =>
        {
            RepoCache.Clear();
            var cache = RepoCache.For(root);
            return $"包 {cache.Profiles.Count} · 契约 {cache.Contracts.Count}";
        }));

        results.Add(Measure("certificates", () =>
        {
            var rows = CertificateVerifier.VerifyAll(root);
            return $"证书 {rows.Count} · 失败 {rows.Count(r => r.Issues.Count > 0)}";
        }));

        results.Add(Measure("breadth-pairs", () =>
        {
            var stats = Breadth.RunPairsOnly(root);
            return $"两两 {stats["pairs_legal"]}/{stats["pairs"]}";
        }));

        results.Add(Measure("receipts", () =>
        {
            var protocol = Receipts.VerifyProtocolReceipts(root);
            var library = Receipts.VerifyLibraryReceipts(root);
            var chain = Receipts.VerifyTransparencyChain(root);
            return $"{protocol.Count}+{library.Count} 条 · 链 {chain.Count} 节";
        }));

        results.Add(Measure("assertions", () =>
        {
            var result = Assertions.Run(root);
            return $"断言 {result.Results.Count}";
        }));

        results.Add(Measure("decisions", () =>
        {
            var result = Decisions.Verify(root);
            return $"ADR {result.Stats["decisions"]}";
        }));

        results.Add(Measure("library", () =>
        {
            var result = Library.Verify(root);
            return $"条目 {result.Stats["entries"]}";
        }));

        results.Add(Measure("cognition", () =>
        {
            var result = Cognition.Run(root);
            return $"术语 {((Dictionary<string, object?>)result.Stats["glossary"]!)["terms"]}";
        }));

        return results;
    }

    private static Measurement Measure(string name, Func<string> body)
    {
        var watch = Stopwatch.StartNew();
        var detail = body();
        var first = watch.Elapsed.TotalMilliseconds;
        watch.Restart();
        body();
        var second = watch.Elapsed.TotalMilliseconds;
        return new Measurement(name, Math.Round(Math.Min(first, second), 2), detail);
    }
}
