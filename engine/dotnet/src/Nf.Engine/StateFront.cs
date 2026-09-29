using System.Text.RegularExpressions;
using System.Security.Cryptography;
using System.Text;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/state_front.py</c> 的**门禁面**：凡登记为 condition-first 的产物件/产物族，
/// 状态块必须位于所有其它二级小节之前。本件只判「排布」这一层，不声称任何效果。
///
/// 判据（<c>check_order</c>）：状态块存在；且它之前没有别的 `##` 小节。
/// </summary>
public static class StateFront
{
    public const string DeclRel = "protocol/state_front.json";
    public const string Schema = "nf-state-front/1";
    public const string StateHead = "## 状态块（条件先行摘要）";
    public const string ContractDescription = "条件先行（登记件须通过排布判据）";

    private static readonly Regex Sections = new(@"^##\s+", RegexOptions.Multiline);
    private static readonly Regex ModuleIds = new(@"\b(?:M\d{2,3}|P\d{2})\b");
    private static readonly Regex NfIds = new(@"NF-[A-Za-z0-9-]+");
    private static readonly Regex Bullets = new(@"^\s*[-*]\s+(.+)$", RegexOptions.Multiline);
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>
    /// 确定性提取状态块（等价 <c>build_state_block</c>）——**不调模型、不编内容**：
    /// 编号集合 / NF 编号 / 二级标题数 / 要点行数 / 原文 sha256 前 16 位，加最多 8 条原文摘录。
    /// </summary>
    public static string BuildStateBlock(string text, int maxPoints = 8)
    {
        var ids = ModuleIds.Matches(text).Select(m => m.Value).Distinct(StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal).ToList();
        var nfs = NfIds.Matches(text).Select(m => m.Value).Distinct(StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal).ToList();
        var sections = Sections.Matches(text).Count;
        var bullets = Bullets.Matches(text).Select(m => m.Groups[1].Value.Trim()).ToList();
        var sha = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(text)))[..16].ToLowerInvariant();
        var lines = new List<string>
        {
            StateHead, "",
            "> 本块由产物**确定性提取**（非模型生成）——它是该产物的「状态文本代理」，供重读时先对齐状态。",
            "", "| 项 | 值 |", "|---|---|",
            $"| 模块/挂载编号 | {(ids.Count > 0 ? string.Join("、", ids) : "（无）")} |",
            $"| NF 编号 | {(nfs.Count > 0 ? string.Join("、", nfs) : "（无）")} |",
            $"| 二级标题数 | {sections} |",
            $"| 要点行数 | {bullets.Count} |",
            $"| 原文 sha256 | `{sha}` |",
            "",
        };
        if (bullets.Count > 0)
        {
            lines.Add("**关键设置点（原文摘录，非改写）**：");
            lines.Add("");
            foreach (var bullet in bullets.Take(maxPoints))
                lines.Add($"- {PyScalar.PySlice(bullet, 120)}");   // Python 的 b[:120] 按码点截
            lines.Add("");
        }
        return string.Join("\n", lines);
    }

    /// <summary>去掉已存在的状态块（幂等：重复 reorder 不叠加），等价 <c>strip_state_block</c>。</summary>
    public static string StripStateBlock(string text)
    {
        var head = text.IndexOf(StateHead, StringComparison.Ordinal);
        if (head < 0) return text;
        var prefix = text[..head];
        var tail = text[(head + StateHead.Length)..];
        var separator = tail.IndexOf("\n---\n", StringComparison.Ordinal);
        if (separator >= 0) return (prefix + tail[(separator + "\n---\n".Length)..]).TrimStart('\n');
        var match = Sections.Match(tail);
        return match.Success ? (prefix + tail[match.Index..]).TrimStart('\n') : prefix;
    }

    /// <summary>front=条件先行 / back=条件后置 / none=省略。</summary>
    public static string Reorder(string text, string mode)
    {
        if (mode == "none") return text;
        var body = StripStateBlock(text);
        var block = BuildStateBlock(body);
        if (mode == "front") return block + "\n---\n\n" + body;
        if (mode == "back") return body.TrimEnd('\n') + "\n\n---\n\n" + block;
        throw new ArgumentException($"mode 只能是 front / back / none：{mode}");
    }

    /// <summary>T3 三刺激件清单（只备装置，不执行模型）：三种排布各自的 sha256 / 字符数 / 是否前置。</summary>
    public static Dictionary<string, object?> AbManifest(string text)
    {
        var result = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var mode in new[] { "front", "back", "none" })
        {
            var variant = Reorder(text, mode);
            result[mode] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["sha256"] = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(variant))).ToLowerInvariant(),
                ["chars"] = PyScalar.PyLen(variant),              // Python len(str) 数码点，不是 UTF-16 单元
                ["state_front"] = CheckOrder(variant).Count == 0,
            };
        }
        return result;
    }

    /// <summary>判据：状态块存在且前置（位于所有其它二级小节之前）。</summary>
    public static List<string> CheckOrder(string text)
    {
        var index = text.IndexOf(StateHead, StringComparison.Ordinal);
        if (index < 0) return new List<string> { "缺状态块——无状态文本代理可前置" };
        var before = Sections.Matches(text).Cast<Match>()
            .Count(m => m.Index < index
                        && !text.AsSpan(m.Index).StartsWith("## 状态块", StringComparison.Ordinal));
        return before > 0
            ? new List<string> { $"状态块未前置：它出现在 {before} 个二级小节之后（条件先行要求置于资料之前）" }
            : new List<string>();
    }

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _, stats) = Scan(root);
        if (issues.Count > 0) return (false, string.Join("; ", issues.Take(2)));
        var detail = $"单件 {stats["declared"]} · 族规则 {stats["family_rules"]} · 族成员 {stats["family_members"]}";
        return (true, detail);
    }

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal);
        var path = Path.Combine(root, DeclRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return (new List<string> { $"缺条件先行声明 {DeclRel}" }, warns, stats);

        using var doc = JsonIo.ReadFile(path);
        var decl = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        if ((decl.GetValueOrDefault("schema")?.ToString() ?? "") != Schema)
            issues.Add($"声明 schema 不匹配（期望 {Schema}）");

        var rows = Rows(decl, "declared");
        var rules = Rows(decl, "family_rules");
        if (rows.Count == 0 && rules.Count == 0)
            warns.Add("条件先行声明为空——门禁空转");

        var hits = new List<string>();
        foreach (var rule in rules)
        {
            var glob = rule.GetValueOrDefault("glob")?.ToString() ?? "";
            if (glob.Length == 0)
            {
                issues.Add("族规则缺 glob");
                continue;
            }
            var matched = PathGlob.Files(root, glob);
            var low = rule.TryGetValue("min_members", out var minValue) && minValue is long min ? (int)min : 1;
            if (matched.Count < low)
                issues.Add($"族 {glob} 成员不足：{matched.Count} < {low}（修复指引：按 sources 重新生成）");
            hits.AddRange(matched);
        }
        foreach (var rel in hits)
        {
            var bad = CheckOrder(StrictUtf8.GetString(File.ReadAllBytes(
                Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)))));
            if (bad.Count > 0)
                issues.Add($"族内件未通过 condition-first：{rel}（{bad[0]}）");
        }
        foreach (var row in rows)
        {
            var rel = row.GetValueOrDefault("path")?.ToString() ?? "";
            if (rel.Length == 0)
            {
                issues.Add("声明条目缺 path");
                continue;
            }
            var full = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(full))
            {
                issues.Add($"登记件不存在：{rel}");
                continue;
            }
            var bad = CheckOrder(StrictUtf8.GetString(File.ReadAllBytes(full)));
            if (bad.Count > 0)
                issues.Add($"登记为 condition-first 但未通过：{rel}（{bad[0]}）");
        }
        stats["declared"] = rows.Count;
        stats["family_rules"] = rules.Count;
        stats["family_members"] = hits.Count;
        return (issues, warns, stats);
    }

    private static List<Dictionary<string, object?>> Rows(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is List<object?> list
            ? list.OfType<Dictionary<string, object?>>().ToList()
            : new List<Dictionary<string, object?>>();
}
