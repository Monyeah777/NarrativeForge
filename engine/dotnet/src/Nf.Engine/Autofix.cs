using System.Text;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>desktop/src/core/autofix.py</c> 的**只读判据面**（check33 第 4 面「机械修复面」）：
/// 关键文档 / 指令档**不该有待办**——列出该文件**可自动修**的机械问题（与 <c>doc_hygiene</c> 同源，不另造标准）：
///
/// 1. <c>last_updated</c>——关键文档（<c>REQUIRED_DOCS</c>）头部 8 行内缺 <c>&gt; 最后更新：</c> 位；
/// 2. <c>instruction_mark</c>——指令档（<c>INSTRUCTION_DOCS</c>）头部 8 行内缺 <c>⛔ 操作指令</c> 标识；
/// 3. <c>trailing_ws</c>——存在行尾空白；
/// 4. <c>final_newline</c>——文件末尾缺换行。
///
/// **写面明确拒绝**：真源的 <c>apply_rules</c>（机械改写）**不移植**——本引擎是只读门，
/// 修复动作留给 <c>nf</c> 真源与作者（auto-fix 不替人做决定）。判据面与写面分离，
/// 这样「引擎说没问题」永远不等于「引擎改过文件」。
///
/// 清单来源：**复用**引擎既有 <c>DocHygiene</c> 的 <c>REQUIRED_DOCS</c> / <c>INSTRUCTION_DOCS</c> 镜像表
/// （不另建第二份清单，避免两处漂移）。
/// </summary>
public static class Autofix
{
    public const string LastUpdatedPrefix = "> 最后更新：";
    public const string InstructionMark = "⛔ 操作指令";
    public const int HeadLines = 8;

    public sealed record Finding(string Rule, string Message);

    /// <summary>
    /// 该文件**可自动修**的问题。顺序照抄真源 <c>lint_rules</c> 的 append 顺序：
    /// <c>last_updated → instruction_mark → trailing_ws → final_newline</c>（与真源 <c>RULES</c> 元组的应用顺序不同，
    /// 这里要的是**报告顺序**）。
    /// </summary>
    public static List<Finding> LintRules(string root, string rel, string text)
    {
        var outList = new List<Finding>();
        var normalizedRel = rel.Replace('\\', '/');
        var required = DocHygiene.RequiredDocPaths.Contains(normalizedRel);
        var instruction = DocHygiene.InstructionDocPaths.Contains(normalizedRel);

        var head = KnowledgeSig.SplitLines(text).Take(HeadLines).ToList();
        if (required && !head.Any(ln => ln.StartsWith(LastUpdatedPrefix, StringComparison.Ordinal)))
            outList.Add(new Finding("last_updated", "缺「最后更新」位（头部 8 行内）"));
        if (instruction && !head.Any(ln => ln.Contains(InstructionMark, StringComparison.Ordinal)))
            outList.Add(new Finding("instruction_mark", "指令档缺「⛔ 操作指令」标识"));
        if (KnowledgeSig.SplitLines(text).Any(ln => ln != ln.TrimEnd()))
            outList.Add(new Finding("trailing_ws", "存在行尾空白"));
        if (text.Length > 0 && !text.EndsWith('\n'))
            outList.Add(new Finding("final_newline", "文件末尾缺换行"));
        return outList;
    }

    /// <summary>
    /// 真源 check33 第 4 面的**门禁口径**：对 <c>REQUIRED_DOCS ∪ INSTRUCTION_DOCS</c> 里**在盘**的每一个文件跑
    /// <see cref="LintRules"/>，返回「有待办的文件」清单（真源要求为空）。
    /// </summary>
    public static (List<string> Pending, int Targets) ScanGateTargets(string root)
    {
        var targets = DocHygiene.RequiredDocPaths
            .Concat(DocHygiene.InstructionDocPaths)
            .Distinct(StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal)
            .ToList();
        var pending = new List<string>();
        var existing = 0;
        foreach (var rel in targets)
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path)) continue;
            existing++;
            var text = File.ReadAllText(path, new UTF8Encoding(false));
            if (LintRules(root, rel, text).Count > 0) pending.Add(rel);
        }
        return (pending, existing);
    }
}
