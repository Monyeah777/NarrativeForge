using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/doc_hygiene.py</c> 的**四型覆盖面**（一致性契约 <c>doc-kinds</c>，并供
/// <c>nf-dotnet lint --kinds</c> 用）：关键文档与指令档每件都必须有合法的四型归属；
/// 四型**写法**判据只记 WARN（存量按可数收敛，不判死）。
///
/// **镜像纪律**：下列三张表（<c>DOC_KINDS</c> / <c>REQUIRED_DOCS</c> / <c>INSTRUCTION_DOCS</c>）
/// 是 Python 侧的逐字镜像（同一 HEAD 机械导出，非手抄）。仓库若新增文档而只改 Python 表，
/// 本镜像会滞后——该漂移由**双跑对账**兜住（契约的 ok/detail 会立刻不一致），故此处不自愈。
/// </summary>
public static class DocHygiene
{
    public const string InstructionMark = "⛔ 操作指令";
    public const string LastUpdatedPrefix = "> 最后更新：";
    public const int HeadLines = 8;

    /// <summary>与 Python <c>CONTRACTS</c> 表里的契约描述逐字一致。</summary>
    public const string ContractDescription = "文档四型覆盖";

    private static readonly string[] Kinds = { "tutorial", "how-to", "reference", "explanation" };

    private static readonly (string Rel, string Kind)[] DocKinds =
    {
        ("01_核心协议.md", "reference"),
        ("02_联动注册表.md", "reference"),
        ("06_Agent执行协议.md", "how-to"),
        ("07_官方核心出厂与社区预设导航.md", "reference"),
        ("DEEP_DIVE.md", "explanation"),
        ("AI_ROUTING.md", "how-to"),
        ("agent_组装指令包_v0.2.md", "how-to"),
        ("docs/mcp.md", "how-to"),
        ("docs/ai-menu.md", "how-to"),
        ("docs/ai-menu-fieldtest-v1.md", "how-to"),
        ("docs/迁移指南-基于nf-sig-diff.md", "how-to"),
        ("docs/attest.md", "how-to"),
        ("docs/verification-cards.md", "reference"),
        ("docs/需求收敛模板.md", "reference"),
        ("docs/42_M1_协议可执行性自测规范.md", "reference"),
        ("docs/42_M1_P03_演练集.md", "tutorial"),
        ("docs/42_M2_回合状态头_v1.md", "reference"),
        ("docs/42_M3_纯度体检.md", "reference"),
        ("docs/44_M1_执行演练扩展.md", "tutorial"),
        ("docs/44_M2_AI通道内容规范.md", "reference"),
        ("docs/45_执行遥测规范.md", "reference"),
        ("docs/45_M2_回合级drill.md", "tutorial"),
        ("docs/45_M3_techdoc载荷提案.md", "explanation"),
        ("docs/library.md", "how-to"),
        ("docs/receipts.md", "how-to"),
        ("docs/conformance.md", "how-to"),
        ("docs/io_types.md", "reference"),
        ("docs/pipelinerun.md", "how-to"),
        ("docs/machine_contract.md", "how-to"),
        ("docs/approval.md", "how-to"),
        ("docs/module_signature.md", "how-to"),
        ("docs/lsp.md", "how-to"),
        ("docs/driver.md", "how-to"),
        ("docs/patterns.md", "how-to"),
        ("docs/bench.md", "how-to"),
        ("docs/endpoint.md", "how-to"),
        ("docs/rfc.md", "reference"),
        ("docs/knowledge.md", "how-to"),
        ("docs/assertions.md", "how-to"),
        ("docs/modeling.md", "how-to"),
        ("docs/interop.md", "how-to"),
        ("docs/text-hygiene.md", "reference"),
        ("docs/decision-layer.md", "how-to"),
        ("docs/output-forms.md", "how-to"),
        ("docs/domain-packs.md", "how-to"),
        ("docs/combos.md", "how-to"),
        ("docs/terminal.md", "how-to"),
        ("docs/layers.md", "how-to"),
    };

    private static readonly string[] RequiredDocs =
    {
        "01_核心协议.md",
        "02_联动注册表.md",
        "06_Agent执行协议.md",
        "07_官方核心出厂与社区预设导航.md",
        "docs/mcp.md",
        "docs/ai-menu.md",
        "docs/ai-menu-fieldtest-v1.md",
        "docs/迁移指南-基于nf-sig-diff.md",
        "docs/需求收敛模板.md",
        "docs/42_M1_协议可执行性自测规范.md",
        "docs/42_M1_P03_演练集.md",
        "docs/42_M2_回合状态头_v1.md",
        "docs/42_M3_纯度体检.md",
        "agent_组装指令包_v0.2.md",
        "docs/44_M1_执行演练扩展.md",
        "docs/44_M2_AI通道内容规范.md",
        "docs/45_执行遥测规范.md",
        "docs/45_M2_回合级drill.md",
        "docs/45_M3_techdoc载荷提案.md",
        "DEEP_DIVE.md",
        "docs/library.md",
        "docs/receipts.md",
        "docs/conformance.md",
        "docs/io_types.md",
        "docs/pipelinerun.md",
        "docs/machine_contract.md",
        "docs/approval.md",
        "docs/module_signature.md",
        "docs/lsp.md",
        "docs/driver.md",
        "docs/patterns.md",
        "docs/bench.md",
        "docs/endpoint.md",
        "docs/rfc.md",
        "docs/knowledge.md",
        "docs/assertions.md",
        "docs/modeling.md",
        "docs/interop.md",
        "docs/output-forms.md",
        "docs/domain-packs.md",
        "docs/combos.md",
        "docs/text-hygiene.md",
        "docs/decision-layer.md",
        "docs/terminal.md",
        "docs/layers.md",
    };

    private static readonly string[] InstructionDocs =
    {
        "docs/ai-menu.md",
        "docs/ai-menu-fieldtest-v1.md",
        "docs/迁移指南-基于nf-sig-diff.md",
        "docs/42_M1_协议可执行性自测规范.md",
        "docs/42_M1_P03_演练集.md",
        "docs/42_M2_回合状态头_v1.md",
        "docs/42_M3_纯度体检.md",
        "agent_组装指令包_v0.2.md",
        "docs/44_M1_执行演练扩展.md",
        "docs/44_M2_AI通道内容规范.md",
        "docs/45_执行遥测规范.md",
        "docs/45_M2_回合级drill.md",
        "docs/45_M3_techdoc载荷提案.md",
        "AI_ROUTING.md",
        "docs/library.md",
        "docs/receipts.md",
        "docs/conformance.md",
        "docs/pipelinerun.md",
        "docs/machine_contract.md",
        "docs/approval.md",
        "docs/module_signature.md",
        "docs/lsp.md",
        "docs/driver.md",
        "docs/patterns.md",
        "docs/bench.md",
        "docs/endpoint.md",
        "docs/rfc.md",
        "docs/knowledge.md",
        "docs/assertions.md",
        "docs/modeling.md",
        "docs/interop.md",
        "docs/decision-layer.md",
        "docs/terminal.md",
        "docs/layers.md",
    };

    /// <summary>四型写法判据：命中 must_any 之一即算定型；未命中只记 WARN。</summary>
    /// <summary>关键文档清单（供 <see cref="Autofix"/> 复用，避免第二份清单漂移）。</summary>
    public static IReadOnlyList<string> RequiredDocPaths => RequiredDocs;

    /// <summary>指令档清单（供 <see cref="Autofix"/> 复用）。</summary>
    public static IReadOnlyList<string> InstructionDocPaths => InstructionDocs;

    private static readonly Dictionary<string, (string[] Patterns, string Label)> KindRules =
        new(StringComparer.Ordinal)
        {
            ["how-to"] = (new[] { "```", @"python scripts/nf\.py", @">\s*⛔" }, "可执行命令块"),
            ["reference"] = (new[] { @"^\|.+\|", "词表", "字段" }, "词表或字段表"),
            ["tutorial"] = (new[] { @"^\s*\d+[.、]\s", "步骤", "演练" }, "步骤序列"),
            ["explanation"] = (new[] { "为什么", "权衡", "机制", "原理" }, "为什么或权衡"),
        };

    private static readonly Dictionary<string, string> KindByPath =
        DocKinds.ToDictionary(x => x.Rel, x => x.Kind, StringComparer.Ordinal);

    /// <summary>四型词表（自检用；Python 侧同名常量 <c>KINDS</c>）。</summary>
    public static IReadOnlyList<string> KindVocabulary => Kinds;

    /// <summary>镜像表里已登记四型的件数（自检用：表自洽与否的可读证据）。</summary>
    public static int CoveredCount => KindByPath.Count;

    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>等价 Python <c>kind_coverage</c>：清单内每件都必须有四型归属且取值合法。</summary>
    public static List<string> KindCoverage(string root)
    {
        var issues = new List<string>();
        var vocabulary = string.Join("/", Kinds);
        foreach (var rel in RequiredDocs.Concat(InstructionDocs).Distinct(StringComparer.Ordinal)
                     .OrderBy(x => x, StringComparer.Ordinal))
        {
            if (!KindByPath.TryGetValue(rel, out var kind) || kind.Length == 0)
            {
                issues.Add($"{rel} 缺四型归属（DOC_KINDS；取值 {vocabulary}）");
            }
            else if (Array.IndexOf(Kinds, kind) < 0)
            {
                issues.Add($"{rel} 四型取值非法：{kind}（取值 {vocabulary}）");
            }
        }
        return issues;
    }

    /// <summary>等价 Python <c>kind_rules</c>：四型写法判据 → WARN 清单（在盘件才判）。</summary>
    public static List<string> KindRulesFor(string root)
    {
        var warns = new List<string>();
        foreach (var (rel, kind) in DocKinds.OrderBy(x => x.Rel, StringComparer.Ordinal))
        {
            if (!KindRules.TryGetValue(kind, out var rule)) continue;
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path)) continue;
            var text = StrictUtf8.GetString(File.ReadAllBytes(path));
            if (!rule.Patterns.Any(p => Regex.IsMatch(text, p, RegexOptions.Multiline | RegexOptions.CultureInvariant)))
                warns.Add($"{rel} 属 {kind} 型但缺「{rule.Label}」（写法未定型）");
        }
        return warns;
    }

    /// <summary>契约口径：<c>(issues, detail)</c>——detail 与 Python 的 f-string 同字。</summary>
    public static (bool Ok, string Detail) Contract(string root)
    {
        var issues = KindCoverage(root);
        var warns = KindRulesFor(root);
        var detail = $"四型全覆盖 · 写法 WARN {warns.Count}";
        return issues.Count == 0 ? (true, detail) : (false, string.Join("; ", issues.Take(2)));
    }

    /// <summary>
    /// 等价 Python <c>doc_hygiene.check_markers</c>：关键文档每件须有「最后更新」位（**头 8 行内**），
    /// 指令档每件须有「⛔ 操作指令」标识头；缺失关键文档本身也报（清单内 100%）。
    /// </summary>
    public static List<string> CheckMarkers(string root)
    {
        var issues = new List<string>();
        foreach (var rel in RequiredDocs)
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path))
            {
                issues.Add($"{rel} 缺失（须入 REQUIRED_DOCS 清单）");
                continue;
            }
            var head = Head(StrictUtf8.GetString(File.ReadAllBytes(path)));
            if (!head.Any(ln => ln.StartsWith(LastUpdatedPrefix, StringComparison.Ordinal)))
                issues.Add($"{rel} 缺「最后更新」位（头部 {head.Count} 行内）");
        }
        foreach (var rel in InstructionDocs)
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path)) continue;
            var head = Head(StrictUtf8.GetString(File.ReadAllBytes(path)));
            if (!head.Any(ln => ln.Contains(InstructionMark, StringComparison.Ordinal)))
                issues.Add($"{rel} 缺「⛔ 操作指令」标识头（指令类文档须全覆盖）");
        }
        return issues;
    }

    /// <summary>Python <c>_head_lines(text, n=8)</c>：<c>text.splitlines()[:8]</c>。</summary>
    private static List<string> Head(string text) =>
        KnowledgeSig.SplitLines(text).Take(8).ToList();

    /// <summary>doc_hygiene 信号面的取行口径（check33 第 3 条的 <c>doc_hygiene</c> 用同一份 issue）。</summary>
    public static List<string> MarkersLog(string root, string label = "文档卫生")
    {
        var issues = CheckMarkers(root);
        var lines = issues.Select(issue => "[FAIL] " + issue).ToList();
        lines.Add($"{label}：{(issues.Count == 0 ? "零缺口" : "FAIL " + issues.Count)}");
        return lines;
    }
}
