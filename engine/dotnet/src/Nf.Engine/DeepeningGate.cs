using System.Text;
using System.Text.Json;

namespace Nf.Engine;

// 复刻 verify.sh check35（深化面门禁 · 八条子项）：管线抽象执行 / 馆藏回执 / 模块边界冻结 /
// 内容绑定批准 / 一致性报告工件 / 无效语料件在场 / 协议层回执 / advisory 台账一致。
//
// 证据通道：真源 check35 是**内嵌 Python**，探针把该段原文抽出执行当 oracle（同 check30 的做法）。
//
// 两处**声明的边界**（引擎不判的部分，写清楚不冒充）：
// ① 一致性报告的 **Merkle root** 覆盖全部 27 条契约（含未移植的 purity-clean）→ 引擎**不重算 root**；
// ② 同理引擎**不重算 live verdict**，而是读在盘报告的 `total`/`verdict`，并对**已移植的 26 行**逐行比对摘要
//    （比真源只比 root/verdict **更严**：行被改也抓得住；但 purity-clean 那一行与 root 仍属边界）。
public static class DeepeningGate
{
    public const string ReportRel = "protocol/conformance_report.json";
    public const string LibraryReceiptsRel = "library/RECEIPTS.json";
    public const string ProtocolReceiptsRel = "protocol/RECEIPTS.json";
    public const string AdvisoryLedgerRel = "protocol/pipeline_advisory.json";

    public static readonly string[] CorpusFiles =
    {
        "desktop/tests/fixtures/fixes/fix_cases.json",
        "desktop/tests/test_invalid_corpus.py",
    };

    public sealed record Result(List<string> Log, int Pass, int Fail, int Warn)
    {
        public bool Ok => Fail == 0;

        public string LogDigest => Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(
                Encoding.UTF8.GetBytes(string.Join("\n", Log)))).ToLowerInvariant()[..32];
    }

    /// <summary>八条子项 → 真源同式的 stdout（FAIL 行 + 统计行）。</summary>
    public static Result Check35(string root)
    {
        var problems = new List<string>();

        // 1 管线抽象执行：全仓零 hard 缺陷（advisory 不判死）
        var (sweepIssues, sweepStats) = PipelineDryrun.Sweep(root);
        foreach (var issue in sweepIssues) problems.Add("管线 dry-run：" + issue);

        // 2 馆藏回执：逐条折叠到根 + 根与实时重算一致
        if (!File.Exists(Path.Combine(root, LibraryReceiptsRel.Replace('/', Path.DirectorySeparatorChar))))
        {
            problems.Add($"缺馆藏回执 {LibraryReceiptsRel}（修复指引：nf library receipts --write）");
        }
        else
        {
            foreach (var issue in Receipts.VerifyLibraryReceipts(root).Issues)
                problems.Add("馆藏回执：" + issue);
        }

        // 3 模块边界冻结：零漂移
        foreach (var issue in ModuleSignature.Verify(root).Issues) problems.Add("模块边界：" + issue);

        // 4 内容绑定批准：零失效
        foreach (var issue in Approval.Verify(root).Issues) problems.Add("批准记录：" + issue);

        // 5 一致性报告工件（引擎口径见类注：逐行比对已移植契约 + 读在盘 verdict）
        var report = CommittedReportCheck(root);
        foreach (var issue in report.Issues) problems.Add("一致性报告：" + issue);
        if (report.Verdict is not null && report.Verdict != "conformant")
            problems.Add($"一致性报告 verdict 非 conformant：{report.Verdict}");

        // 6 无效语料 + golden 修复对在场
        foreach (var rel in CorpusFiles)
        {
            if (!File.Exists(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))))
                problems.Add("缺语料件：" + rel);
        }

        // 7 协议层回执（覆盖面从馆藏扩到 01-07 / schema / baseline）
        if (!File.Exists(Path.Combine(root, ProtocolReceiptsRel.Replace('/', Path.DirectorySeparatorChar))))
        {
            problems.Add($"缺协议层回执 {ProtocolReceiptsRel}（修复指引：nf receipts --write）");
        }
        else
        {
            foreach (var issue in Receipts.VerifyProtocolReceipts(root).Issues)
                problems.Add("协议回执：" + issue);
        }

        // 8 advisory 分类台账与实时重算一致
        foreach (var issue in PipelineDryrun.VerifyAdvisory(root).Issues)
            problems.Add("advisory 台账：" + issue);

        var log = problems.Select(p => "[FAIL] " + p).ToList();
        // 逐字照抄真源格式串：'深化面统计：管线 %d 条（advisory %d）· 回执 %d 条 · 报告 %s'
        log.Add($"深化面统计：管线 {sweepStats["pipelines"]} 条（advisory {sweepStats["notes"]}）"
                + $"· 回执 {(report.Contracts is { } c ? c : 0)} 条 · 报告 {report.Verdict ?? "-"}");
        return problems.Count == 0
            ? new Result(log, 1, 0, 0)
            : new Result(log, 0, problems.Count, 0);
    }

    public sealed record CommittedReport(List<string> Issues, long? Contracts, string? Verdict, string? RootHash);

    /// <summary>
    /// 把真仓的 `desktop/src` 拷进合成树（**不拷 `__pycache__`**）：真源 check35 要靠它 `from core import …`，
    /// 引擎虽不读它，但两侧必须跑同一棵树才谈得上对账。
    /// </summary>
    public static void CopySourceTree(string repoRoot, string targetRoot)
    {
        var src = Path.Combine(repoRoot, "desktop", "src");
        if (!Directory.Exists(src)) return;
        var dst = Path.Combine(targetRoot, "desktop", "src");
        foreach (var file in Directory.GetFiles(src, "*", SearchOption.AllDirectories))
        {
            if (file.Contains($"{Path.DirectorySeparatorChar}__pycache__{Path.DirectorySeparatorChar}")) continue;
            var rel = Path.GetRelativePath(src, file);
            var outPath = Path.Combine(dst, rel);
            Directory.CreateDirectory(Path.GetDirectoryName(outPath)!);
            File.Copy(file, outPath, overwrite: true);
        }
    }

    /// <summary>
    /// 在盘一致性报告 vs 实时重算的**引擎口径**：逐行比对**已移植**契约的 digest（真源只比 root/verdict，
    /// 故本件更严），并读在盘 `total`/`verdict`。**不重算 root**（含未移植契约）——见类注边界。
    /// </summary>
    public static CommittedReport CommittedReportCheck(string root)
    {
        var issues = new List<string>();
        var path = Path.Combine(root, ReportRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path))
            return new CommittedReport(new List<string>
            {
                $"缺一致性报告 {ReportRel}（修复指引：nf conformance --write）",
            }, null, null, null);
        JsonDocument json;
        try
        {
            json = JsonIo.ReadFile(path);
        }
        catch (JsonException exc)
        {
            return new CommittedReport(new List<string> { "报告 JSON 不可解析：" + exc.Message }, null, null, null);
        }
        using (json)
        {
            var doc = PythonJson.ToGraph(json.RootElement) as Dictionary<string, object?>
                      ?? new Dictionary<string, object?>();
            var rows = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
            foreach (var row in (doc.GetValueOrDefault("contracts") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
            {
                if (row.GetValueOrDefault("id") is string rowId) rows[rowId] = row;
            }
            foreach (var contract in Conformance.Run(root).Contracts)
            {
                if (!rows.TryGetValue(contract.Id, out var row))
                {
                    issues.Add($"报告缺契约行：{contract.Id}（修复指引：nf conformance --write）");
                    continue;
                }
                var digest = row.GetValueOrDefault("digest") as string ?? "";
                if (digest != contract.Digest)
                    issues.Add($"报告过期或被改：{contract.Id} 行摘要不符（修复指引：nf conformance --write）");
            }
            var total = doc.GetValueOrDefault("total") is { } t ? Convert.ToInt64(t) : (long?)null;
            var verdict = doc.GetValueOrDefault("verdict") as string;
            var rootHash = doc.GetValueOrDefault("root") as string;
            return new CommittedReport(issues, total, verdict, rootHash);
        }
    }
}
