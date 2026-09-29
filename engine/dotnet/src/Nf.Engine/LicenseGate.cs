using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>desktop/src/core/license_gate.py</c>（**图书馆入库许可证门** · check33 第 6 面）：
///
/// 判据（与 <c>library/INDEX.md</c> 投稿须知同源，不另造标准）：
/// ① 每条登记行的「许可」列必须有值，且取值过 **SPDX 表达式词法**（id 在册 + 运算符合法 + 括号配平；
///    允许 <c>LicenseRef-&lt;自定义&gt;</c> 与 <c>专有</c> / <c>未声明</c> 两个 NF 占位）；
/// ② 取值 <c>未声明</c> 允许存在，但**计入 WARN 挂账**（入口不静默通过）；
/// ③ 条目文件应带内联许可声明（<c>&gt; 许可：…</c> 或 frontmatter <c>license: …</c>）；
///    缺失或与登记行**不一致**同样记 WARN（不回填不阻断，但不隐身）。
///
/// 纪律照抄：本门只判「许可声明是否在场 / 合规」，**不判内容质量、不替投稿人做授权判断**。
/// 真源里本面只被 <c>verify.sh check33</c> 消费（无 <c>nf</c> 子命令面），故**不新增 CLI 面**；
/// 证据通道 = 真材料 + 合成负例（自检钉）+ 探针 <c>probes/license_gate_probe.py</c>
/// （真源模块**原文**导入，同一棵树、同一套渲染规则下逐字节同摘要）。
///
/// **两处口径如实照抄**：① <c>parse_index</c> 里 <b>6 格行视作「无许可列」</b>（<c>cells[5] if len&gt;=7 else ""</c>）——
/// 即老格式登记行必然报「登记行缺许可列值」；② 「允许：…」两处渲染**不同**：表达式面**不含** <c>未声明</c>，
/// 扫描面**含**（照抄，不统一）。
/// </summary>
public static class LicenseGate
{
    public const string IndexRel = "library/INDEX.md";
    public const string Undeclared = "未声明";

    private static readonly string[] Allowed =
    {
        "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC",
        "CC-BY-4.0", "CC-BY-SA-4.0", "CC0-1.0", "专有", Undeclared,
    };

    private static readonly string[] Operators = { "AND", "OR", "WITH" };

    private static readonly Regex ExprToken = new("\\(|\\)|[A-Za-z0-9.+\\-]+", RegexOptions.Compiled);
    private static readonly Regex RowRe = new("^\\|\\s*(NF-[A-Za-z0-9\\-]+)\\s*\\|", RegexOptions.Compiled);
    private static readonly Regex InlineRe =
        new("^\\s*(?:>\\s*)?(?:许可|license)\\s*[:：]\\s*([^\\s（(]+)", RegexOptions.Multiline | RegexOptions.Compiled);

    public sealed record Row(string Id, string License, List<string> Cells);

    public sealed record Result(List<string> Issues, List<string> Warnings, Dictionary<string, object?> Stats)
    {
        public bool Ok => Issues.Count == 0;

        public List<string> UndeclaredIds => Ids("undeclared");
        public List<string> UnknownIds => Ids("unknown");
        public List<string> NoInlineIds => Ids("no_inline");
        public List<string> MismatchedIds => Ids("mismatched");

        private List<string> Ids(string key) =>
            Stats.TryGetValue(key, out var value) && value is List<string> list ? list : new List<string>();

        /// <summary>
        /// 双跑对账面：真源 stdout 里本面**只有** <c>[FAIL]</c>（warnings 只进 stats，不打印），
        /// 故本件按探针约定的统一渲染规则落日志——真材料下日志为空，合成语料下逐条列出。
        /// </summary>
        public List<string> Log
        {
            get
            {
                var lines = new List<string>();
                lines.AddRange(Issues.Select(i => "[FAIL] " + i));
                lines.AddRange(Warnings.Select(w => "[WARN] " + w));
                lines.Add("[STAT] entries=" + Convert.ToInt64(Stats["entries"])
                           + " declared=" + Convert.ToInt64(Stats["declared"])
                           + " undeclared=" + PyScalar.PyRepr(UndeclaredIds.Cast<object?>().ToList())
                           + " unknown=" + PyScalar.PyRepr(UnknownIds.Cast<object?>().ToList())
                           + " no_inline=" + PyScalar.PyRepr(NoInlineIds.Cast<object?>().ToList())
                           + " mismatched=" + PyScalar.PyRepr(MismatchedIds.Cast<object?>().ToList()));
                return lines;
            }
        }

        public string LogDigest => Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(
                Encoding.UTF8.GetBytes(string.Join("\n", Log)))).ToLowerInvariant()[..32];
    }

    /// <summary>SPDX 表达式词法体检 → 违规说明（空串 = 合规）。</summary>
    public static string ExpressionIssue(string? expr)
    {
        var text = (expr ?? "").Trim();
        if (text.Length == 0) return "许可为空";
        if (text == "专有" || text == Undeclared) return "";
        var tokens = ExprToken.Matches(text).Select(m => m.Value).ToList();
        if (string.Concat(tokens) != Regex.Replace(text, "\\s+", ""))
            return "含非法字符（修复指引：SPDX id / AND / OR / WITH / 括号 / `+` 之外不得出现）";
        if (Count(text, '(') != Count(text, ')')) return "括号不配平";
        var atoms = tokens.Where(t => t != "(" && t != ")").ToList();
        if (atoms.Count == 0) return "表达式无许可 id";
        foreach (var atom in atoms)
        {
            if (Operators.Contains(atom)) continue;
            var basis = atom.EndsWith('+') ? atom[..^1] : atom;
            if (Allowed.Contains(basis) || basis.StartsWith("LicenseRef-", StringComparison.Ordinal)) continue;
            var allowed = string.Join("、", Allowed.Where(x => x != Undeclared).OrderBy(x => x, StringComparer.Ordinal));
            return $"许可 id 不在词表：{atom}（允许：{allowed}；或用 `LicenseRef-<自定义>` 显式自造）";
        }
        for (var i = 0; i < tokens.Count; i++)
        {
            var token = tokens[i];
            if (!Operators.Contains(token)) continue;
            if (i == 0 || i == tokens.Count - 1)
                return $"运算符 {token} 出现在表达式首/尾（缺操作数）";
            if (Operators.Contains(tokens[i - 1]) || tokens[i - 1] == "(")
                return $"运算符 {token} 前缺少操作数";
            if (tokens[i + 1] == ")")
                return $"运算符 {token} 后缺少操作数";
        }
        return "";
    }

    /// <summary>解析登记表数据行（<c>NF-</c> 起始且 ≥6 格）。</summary>
    public static List<Row> ParseIndex(string root)
    {
        var rows = new List<Row>();
        var path = Path.Combine(root, "library", "INDEX.md");
        if (!File.Exists(path)) return rows;
        var text = NormalizeNewlines(File.ReadAllText(path, new UTF8Encoding(false)));
        foreach (var line in KnowledgeSig.SplitLines(text))
        {
            if (!RowRe.IsMatch(line)) continue;
            var cells = Cells(line);
            if (cells.Count < 6) continue;
            // 照抄真源：只有 ≥7 格才取第 6 格当许可列，否则视作「无许可列」。
            rows.Add(new Row(cells[0], cells.Count >= 7 ? cells[5] : "", cells));
        }
        return rows;
    }

    /// <summary>条目文件内联许可声明（缺 = 空串；只读前 4000 字符，同真源）。</summary>
    public static string InlineLicense(string root, string entryId)
    {
        var path = Path.Combine(root, "library", entryId + ".md");
        if (!File.Exists(path)) return "";
        var head = NormalizeNewlines(File.ReadAllText(path, new UTF8Encoding(false)));
        if (head.Length > 4000) head = head[..4000];
        var match = InlineRe.Match(head);
        return match.Success ? match.Groups[1].Value.Trim() : "";
    }

    public static Result Scan(string root)
    {
        var issues = new List<string>();
        var warnings = new List<string>();
        var rows = ParseIndex(root);
        var undeclared = new List<string>();
        var unknown = new List<string>();
        var noInline = new List<string>();
        var mismatched = new List<string>();

        foreach (var row in rows)
        {
            var license = row.License;
            if (license.Length == 0)
            {
                issues.Add($"登记行缺「许可」列值：{row.Id}（修复指引：按许可词表补值，"
                           + $"投稿人未回填写「{Undeclared}」）");
                continue;
            }
            var expressionBad = ExpressionIssue(license);
            if (expressionBad.Length > 0)
            {
                var allowed = string.Join("、", Allowed.OrderBy(x => x, StringComparer.Ordinal));
                issues.Add($"许可取值不合规：{row.Id} = {license}（{expressionBad}；允许：{allowed}）");
                unknown.Add(row.Id);
                continue;
            }
            if (license == Undeclared)
            {
                warnings.Add($"许可未声明（待投稿人确认）：{row.Id}");
                undeclared.Add(row.Id);
            }
            var inner = InlineLicense(root, row.Id);
            if (inner.Length == 0)
            {
                warnings.Add($"条目文件缺内联许可声明：{row.Id}（修复指引：文件头补 "
                             + "「> 许可：<SPDX>」）");
                noInline.Add(row.Id);
            }
            else if (inner != license)
            {
                warnings.Add($"许可双源不一致：{row.Id} 登记={license} 文件={inner}");
                mismatched.Add(row.Id);
            }
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["entries"] = (long)rows.Count,
            ["declared"] = (long)(rows.Count - undeclared.Count - unknown.Count),
            ["undeclared"] = undeclared,
            ["unknown"] = unknown,
            ["no_inline"] = noInline,
            ["mismatched"] = mismatched,
            ["warnings"] = warnings,
        };
        return new Result(issues, warnings, stats);
    }

    private static List<string> Cells(string row) =>
        row.Trim().Trim('|').Split('|').Select(c => c.Trim()).ToList();

    private static int Count(string text, char ch)
    {
        var total = 0;
        foreach (var c in text)
        {
            if (c == ch) total++;
        }
        return total;
    }

    private static string NormalizeNewlines(string text) => text.Replace("\r\n", "\n").Replace('\r', '\n');
}
