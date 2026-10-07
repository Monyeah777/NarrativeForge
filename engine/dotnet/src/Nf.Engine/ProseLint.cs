using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>desktop/src/core/prose_lint.py</c>（**正文级 lint + 文档命令面** · check33 第 5 / 12 面）：
///
/// ① <b>正文 lint</b>（<see cref="LintText"/>）：对正文段落跑确定性规则，输出**可寻址**发现项
///    （行号 + 规则 + 片段）。规则取向 = 「AI 味」的**可判定面**（不判文笔好坏）：陈词滥调开头 /
///    总结腔收尾 / 说教腔 / 对称句式 / 四字词堆砌 / 段首连接词复用 / 模糊限定词过密 / 中英标点混用。
///    纪律照抄：**只报告不阻断**；规则集可由资产键 <c>05_资产库/用户自定义/PROSE_LINT.md</c> 扩展。
/// ② <b>文档命令面</b>（<see cref="CommandFace"/>）：文档里**当作命令呈现**的片段（行内代码 + 围栏块）
///    里的 <c>nf 子命令</c> 与 <c>工具名（MCP 工具）</c> 必须能在 CLI 注册表 / MCP 工具表里查到——
///    写错一个子命令，读者按文档执行即失败，而旧门禁一条都不会红。
///
/// 真源里这两面只被 <c>verify.sh check33</c> 消费（没有独立的 <c>nf</c> 判定面），故**不新增 CLI 面**；
/// 证据通道 = 真材料 + 合成负例（自检钉）+ 探针 <c>probes/prose_lint_probe.py</c>（真源模块**原文**同树双跑）。
///
/// **两处口径如实照抄**：① <c>_MCP_TOOL_MENTION</c> 只在**工具表非空**时才判（表不可读即跳过工具面）；
/// ② 片段顺序是**先全部行内代码、再全部围栏块**（不是按出现位置交错）——发现项的先后由此决定。
/// **一处镜像声明**：MCP 工具表取真源 <c>core.mcp_runtime.TOOL_DEFS</c> 的 **10 个**基名；引擎自有 18 个
/// <c>nf_*</c> 工具**不在**该表内，用引擎自己的表会偏松，故按真源表镜像。
/// </summary>
public static class ProseLint
{
    private static readonly string[] Cliches =
    {
        "在这个", "随着时代", "众所周知", "不言而喻", "无论如何", "某种程度上",
        "在当今", "如今的社会", "无需多言",
    };

    private static readonly string[] SummaryTails = { "总而言之", "综上所述", "总之", "总的来说", "综上" };
    private static readonly string[] Lecture = { "我们应该", "让我们", "请记住", "要知道", "我们必须" };

    private static readonly string[] Connectors =
        { "然而", "与此同时", "值得一提的是", "不仅如此", "更重要的是", "毫无疑问" };

    private static readonly string[] Hedges = { "似乎", "仿佛", "或许", "也许", "可能", "大概", "某种程度上" };

    private const double HedgePer1000 = 12.0;
    private const int TripleAdjMin = 3;

    private static readonly Regex BinaryRe = new(
        "不是[^。；\\n]{1,20}而是|不仅[^。；\\n]{1,20}而且|既要[^。；\\n]{1,20}又要", RegexOptions.Compiled);
    private static readonly Regex QuadRe = new("(?:[\\u4e00-\\u9fa5]{4}、){2,}[\\u4e00-\\u9fa5]{4}", RegexOptions.Compiled);
    private static readonly Regex PunctRe = new("[\\u4e00-\\u9fa5][,;:!?]", RegexOptions.Compiled);
    private static readonly Regex FenceRe = new("^\\s*```", RegexOptions.Compiled);
    private static readonly Regex CodeSpanRe = new("`([^`\\n]+)`", RegexOptions.Compiled);
    private static readonly Regex FenceBlockRe = new("```[a-zA-Z0-9]*\\n(.*?)```", RegexOptions.Singleline | RegexOptions.Compiled);
    private static readonly Regex NfCallRe = new("\\b(?:nf|nf\\.py)\\s+([a-z][a-z0-9-]*)", RegexOptions.Compiled);
    private static readonly Regex McpToolMentionRe = new("([a-z][a-z0-9_]{2,})（MCP 工具）", RegexOptions.Compiled);
    private static readonly Regex NfAddParserRe = new("sub\\.add_parser\\(\\s*\"([a-z0-9-]+)\"", RegexOptions.Compiled);

    public const string CustomAsset = "05_资产库/用户自定义/PROSE_LINT.md";

    /// <summary>命令面一致性扫描范围（入口文档 + 协议件 + 使用面 docs）。</summary>
    public static readonly string[] FaceDocs =
    {
        "README.md", "README.en.md", "docs/agent/ROUTES.md", "docs/agent/AGENT_START.md",
        "docs/agent/AI_ROUTING.md", "docs/agent/agent_组装指令包_v0.2.md", "llms.txt",
        "01_核心协议.md", "02_联动注册表.md", "06_Agent执行协议.md",
        "07_官方核心出厂与社区预设导航.md",
    };

    /// <summary>
    /// 镜像真源 <c>core.mcp_runtime.TOOL_DEFS</c> 的 10 个基名（**不含**引擎自有的 18 个 <c>nf_*</c>）。
    /// 单一出处 = <see cref="McpPackage.RuntimeTools"/>（本属性只是转发，避免第二份清单漂移）。
    /// </summary>
    public static string[] SourceMcpToolNames => McpPackage.RuntimeTools;

    public sealed record Finding(string Rule, int Line, string Message, string Snippet);

    public sealed record CommandFaceResult(List<string> Issues, Dictionary<string, object?> Stats)
    {
        public bool Ok => Issues.Count == 0;
    }

    /// <summary>读资产槽里的自定义禁用词（每行一个；跳过空行与 <c>#</c> / <c>&gt;</c> / <c>-</c> / <c>|</c> 起首行）。</summary>
    public static List<string> LoadCustomTerms(string root)
    {
        var terms = new List<string>();
        var path = Path.Combine(root, CustomAsset.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return terms;
        var text = File.ReadAllText(path, new UTF8Encoding(false));
        foreach (var raw in KnowledgeSig.SplitLines(text))
        {
            var line = raw.Trim();
            if (line.Length == 0) continue;
            if (line[0] is '#' or '>' or '-' or '|') continue;
            terms.Add(line);
        }
        return terms;
    }

    /// <summary>
    /// 正文 → 发现项列表（1 基行号）。<paramref name="extraTerms"/> 为空则只用内置陈词表；
    /// 排序键为 <c>(line, rule)</c>（同真源）。
    /// </summary>
    public static List<Finding> LintText(string text, IReadOnlyList<string>? extraTerms = null,
                                         double hedgePer1000 = HedgePer1000)
    {
        var findings = new List<Finding>();
        var lines = ProseLines(text);
        var body = string.Concat(lines.Select(l => l.Text));
        var terms = Cliches.Concat(extraTerms ?? Array.Empty<string>()).ToList();

        foreach (var (no, s) in lines)
        {
            var hit = FirstContained(terms, s);
            if (hit is not null)
                findings.Add(new Finding("cliche_open", no, $"陈词滥调/套话：「{hit}」", PySlice(s, 40)));
            var tail = FirstContained(SummaryTails, s);
            if (tail is not null)
                findings.Add(new Finding("summary_tail", no, $"总结腔：「{tail}」", PySlice(s, 40)));
            var lec = FirstContained(Lecture, s);
            if (lec is not null)
                findings.Add(new Finding("lecture_tone", no, $"说教腔：「{lec}」", PySlice(s, 40)));
            var binary = BinaryRe.Match(s);
            if (binary.Success)
                findings.Add(new Finding("binary_parallel", no,
                    $"对称句式（AI 腔高发）：{PySlice(binary.Value, 20)}", PySlice(s, 40)));
            var quad = QuadRe.Match(s);
            if (quad.Success && Count(quad.Value, '、') + 1 >= TripleAdjMin)
                findings.Add(new Finding("triple_adj", no,
                    $"四字词堆砌（≥{TripleAdjMin} 连）：{PySlice(quad.Value, 24)}", PySlice(s, 40)));
            var punct = PunctRe.Match(s);
            if (punct.Success)
                findings.Add(new Finding("punct_mix", no, $"中英标点混用：{punct.Value}", PySlice(s, 40)));
        }

        var starts = lines.Select(l => PySlice(l.Text, 4)).ToList();
        foreach (var connector in Connectors)
        {
            var hits = new List<int>();
            for (var i = 0; i < starts.Count; i++)
            {
                if (starts[i].StartsWith(connector, StringComparison.Ordinal)) hits.Add(i);
            }
            if (hits.Count >= 2)
            {
                findings.Add(new Finding("repeat_connector", lines[hits[1]].No,
                    $"段首连接词复用 {hits.Count} 次：「{connector}」", connector));
            }
        }

        if (body.Length > 0)
        {
            var nHedge = Hedges.Sum(w => CountOccurrences(body, w));
            var per1K = nHedge * 1000.0 / Math.Max(1, PyScalar.PyLen(body));
            if (per1K > hedgePer1000)
                findings.Add(new Finding("hedge_overuse", 0,
                    $"模糊限定词过密：{per1K.ToString("F1", System.Globalization.CultureInfo.InvariantCulture)} 次/千字"
                    + $"（阈值 {hedgePer1000.ToString("F1", System.Globalization.CultureInfo.InvariantCulture)}）", ""));
        }

        return findings
            .OrderBy(f => f.Line)
            .ThenBy(f => f.Rule, StringComparer.Ordinal)
            .ToList();
    }

    /// <summary>文档命令面 ↔ CLI 注册表 / MCP 工具表一致性。</summary>
    public static CommandFaceResult CommandFace(string root)
    {
        var issues = new List<string>();
        var cmds = NfCliCommands(root);
        var tools = SourceMcpToolNames.ToHashSet(StringComparer.Ordinal);

        var docs = FaceDocs
            .Where(d => File.Exists(Path.Combine(root, d.Replace('/', Path.DirectorySeparatorChar))))
            .ToList();
        var docsDir = Path.Combine(root, "docs");
        if (Directory.Exists(docsDir))
        {
            docs.AddRange(Directory.GetFiles(docsDir, "*.md")
                .Select(f => Rel(root, f))
                .OrderBy(x => x, StringComparer.Ordinal));
        }

        var checkedCount = 0;
        foreach (var rel in docs)
        {
            var text = File.ReadAllText(
                Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)),
                new UTF8Encoding(false));
            foreach (var snippet in CommandSnippets(text))
            {
                foreach (Match m in NfCallRe.Matches(snippet))
                {
                    checkedCount++;
                    var name = m.Groups[1].Value;
                    if (!cmds.Contains(name))
                    {
                        issues.Add($"{rel} 命令面：`{("nf " + name).Trim()}` 不是 CLI 子命令"
                                   + "（修复指引：核对 scripts/nf.py 注册表改文档，或先实现该命令）");
                    }
                }
                foreach (Match m in McpToolMentionRe.Matches(snippet))
                {
                    checkedCount++;
                    if (tools.Count > 0 && !tools.Contains(m.Groups[1].Value))
                    {
                        issues.Add($"{rel} 命令面：{m.Groups[1].Value} 不是已登记 MCP 工具"
                                   + "（修复指引：核对 core/mcp_runtime.TOOL_DEFS，工具名与实现须逐名一致）");
                    }
                }
            }
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["docs"] = (long)docs.Count,
            ["commands_checked"] = (long)checkedCount,
            ["cli_commands"] = (long)cmds.Count,
            ["mcp_tools"] = (long)tools.Count,
        };
        return new CommandFaceResult(issues, stats);
    }

    /// <summary>从 <c>scripts/nf.py</c> 的 <c>sub.add_parser("…")</c> 文本抽取 CLI 子命令名（与真源同正则）。</summary>
    public static HashSet<string> NfCliCommands(string root)
    {
        var result = new HashSet<string>(StringComparer.Ordinal);
        var path = Path.Combine(root, "scripts", "nf.py");
        if (!File.Exists(path)) return result;
        var text = File.ReadAllText(path, new UTF8Encoding(false));
        foreach (Match m in NfAddParserRe.Matches(text)) result.Add(m.Groups[1].Value);
        return result;
    }

    /// <summary>只取**当作命令呈现**的片段：先全部行内代码，再全部围栏块（顺序照抄真源）。</summary>
    private static List<string> CommandSnippets(string text)
    {
        var outList = CodeSpanRe.Matches(text).Select(m => m.Groups[1].Value).ToList();
        outList.AddRange(FenceBlockRe.Matches(text).Select(m => m.Groups[1].Value));
        return outList;
    }

    /// <summary>正文行 = 非代码围栏内的非结构行（跳过标题 / 引用 / 表格 / 列表 / 分隔线 / 有序项）。</summary>
    private static List<(int No, string Text)> ProseLines(string text)
    {
        var outList = new List<(int No, string Text)>();
        var inFence = false;
        var all = KnowledgeSig.SplitLines(text);
        for (var i = 0; i < all.Count; i++)
        {
            var line = all[i];
            if (FenceRe.IsMatch(line))
            {
                inFence = !inFence;
                continue;
            }
            if (inFence) continue;
            var s = line.Trim();
            if (s.Length == 0) continue;
            if (s[0] is '#' or '>' or '|') continue;
            if (s.StartsWith("- ", StringComparison.Ordinal) || s.StartsWith("* ", StringComparison.Ordinal)) continue;
            if (Regex.IsMatch(s, "^\\d+[.、]")) continue;
            outList.Add((i + 1, s));
        }
        return outList;
    }

    private static string? FirstContained(IEnumerable<string> terms, string text)
    {
        foreach (var term in terms)
        {
            if (text.Contains(term, StringComparison.Ordinal)) return term;
        }
        return null;
    }

    private static int CountOccurrences(string haystack, string needle)
    {
        if (needle.Length == 0) return 0;
        var count = 0;
        var index = 0;
        while ((index = haystack.IndexOf(needle, index, StringComparison.Ordinal)) >= 0)
        {
            count++;
            index += needle.Length;
        }
        return count;
    }

    private static int Count(string text, char ch)
    {
        var total = 0;
        foreach (var c in text)
        {
            if (c == ch) total++;
        }
        return total;
    }

    private static string PySlice(string text, int maxCodePoints) => PyScalar.PySlice(text, maxCodePoints);

    private static string Rel(string root, string path) =>
        Path.GetRelativePath(root, path).Replace('\\', '/');
}
