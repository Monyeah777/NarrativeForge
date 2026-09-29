using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>verify.sh check30</c> 的**可判面**（扩展策略 + bump 迁移门禁 · 43 A3）：
///
/// ① <b>判据词面</b>（纯只读，可独立复算）：<c>protocol/EXTENSION.md</c> 须在场且含七个判据词
///    （字段级新增 / 迁移记录 / bump / additive / editorial / 结构 bump / 派生三问），缺一个即 FAIL；
/// ② <b>bump 面</b>（**VCS diff 面**）：真源判据是「<c>git diff HEAD</c> 里版本字段行发生过结构性变更 →
///    必须带四步迁移记录（现状快照 / bump 声明 / 迁移说明 / 校验回读）」。
///
/// <b>边界声明（本模块的核心决定）</b>：本引擎 **BCL-only、只读、不接 VCS**，因此对 ② 采取**显式不判**
/// 的姿态，而不是「没判 = 判过」：
/// - <b>非仓库导出态</b>（root 下无 <c>.git</c>）：真源自己也会因 <c>git diff</c> 失败而把 diff 面当空，
///   故本件**照抄该空判**（<see cref="Result.BumpFaceJudged"/> = true 且 bump 列表为空）——两侧逐字节同判；
/// - <b>工作区态</b>（root 下有 <c>.git</c>）：diff 面**有意义且本件判不了**，故标
///   <see cref="Result.BumpFaceJudged"/> = false 并给出 <see cref="Result.Boundary"/> 说明——
///   按三态纪律（PASS / FAIL / UNKNOWN）**不得写成 PASS**。
///
/// 证据（probes/extension_policy_probe.py）：临时 git 仓库里把一个版本字段从 <c>"2"</c> 改成 <c>"3"</c>，
/// 真源立刻报 <c>bump 文件 1（02_联动注册表.md）</c> + 一条 FAIL；而引擎在该态**明示不判**——不冒充等价。
/// </summary>
public static class ExtensionPolicy
{
    public const string ExtensionRel = "protocol/EXTENSION.md";

    /// <summary>判据词（顺序照抄真源 <c>need</c> 列表）。</summary>
    public static readonly string[] NeedWords =
    {
        "字段级新增", "迁移记录", "bump", "additive", "editorial", "结构 bump", "派生三问",
    };

    public sealed record Result(
        List<string> Issues,
        List<string> MissWords,
        List<string> Bumps,
        bool BumpFaceJudged,
        string Boundary)
    {
        public bool Ok => Issues.Count == 0;

        /// <summary>判据词面是否干净（与 bump 面无关的独立断言）。</summary>
        public string StatsLine =>
            $"扩展策略统计：判据词缺 {MissWords.Count} / bump 文件 {Bumps.Count}"
            + $"（{(Bumps.Count > 0 ? string.Join("、", Bumps) : "无")}）";

        /// <summary>真源 <c>check30</c> 的 stdout：统计行 + 逐条 <c>[FAIL]</c>（本件在导出态与之逐字节同式）。</summary>
        public List<string> Log
        {
            get
            {
                var lines = new List<string> { StatsLine };
                lines.AddRange(Issues.Select(i => "[FAIL] " + i));
                return lines;
            }
        }

        public string LogDigest => Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(
                Encoding.UTF8.GetBytes(string.Join("\n", Log)))).ToLowerInvariant()[..32];
    }

    public static Result Scan(string root)
    {
        var issues = new List<string>();
        var ext = "";
        var extPath = Path.Combine(root, ExtensionRel.Replace('/', Path.DirectorySeparatorChar));
        if (File.Exists(extPath)) ext = NormalizeNewlines(File.ReadAllText(extPath, new UTF8Encoding(false)));

        var miss = NeedWords.Where(w => !ext.Contains(w, StringComparison.Ordinal)).ToList();
        if (miss.Count > 0) issues.Add("EXTENSION.md 缺判据词：" + string.Join(",", miss));

        // bump 面：只在**非仓库导出态**照抄真源的空判；工作区态显式不判（三态纪律）。
        var isWorkingTree = Directory.Exists(Path.Combine(root, ".git"));
        var bumps = new List<string>();
        var boundary = isWorkingTree
            ? "工作区态（root 下有 .git）：bump 面 = `git diff HEAD` 的版本字段结构性变更面，"
              + "引擎 BCL-only 不接 VCS → **UNKNOWN（不判，不写 PASS）**；须由真源 verify.sh 或带 VCS 的工具判定"
            : "非仓库导出态（root 下无 .git）：真源 `git diff` 亦失败 → diff 面恒空，本件照抄该空判（两侧同判）";

        return new Result(issues, miss, bumps, !isWorkingTree, boundary);
    }

    private static string NormalizeNewlines(string text) => text.Replace("\r\n", "\n").Replace('\r', '\n');

    /// <summary>
    /// **调用方供 diff** 的 bump 面判定（第一百零五片）：引擎仍**不接 VCS**——由调用方（CI / 脚本）
    /// 跑 <c>git diff HEAD</c> 并把标准统一 diff 文本交给引擎，本件按真源算法逐文件判。
    ///
    /// 真源算法（`verify.sh check30` 内联 Python）：对文件清单里每个文件取**该文件的 diff**，
    /// 只看版本字段行（`tok` 词表：`registry_schema_version` / `schema_version` / `version`），
    /// 若**改动前的版本串集合**与**改动后的版本串集合**都非空且**不相等** → 记一个 bump，
    /// 并要求四步迁移记录（现状快照 / bump 声明 / 迁移说明 / 校验回读）出现在
    /// 「该文件 diff ∪ 记录面（02_联动注册表.md 的 diff + protocol/EXTENSION.md 的 diff）」里。
    /// </summary>
    public static Result ScanWithDiff(string root, string diffText)
    {
        var issues = new List<string>();
        var extPath = Path.Combine(root, ExtensionRel.Replace('/', Path.DirectorySeparatorChar));
        var ext = File.Exists(extPath)
            ? NormalizeNewlines(File.ReadAllText(extPath, new UTF8Encoding(false)))
            : "";
        var miss = NeedWords.Where(w => !ext.Contains(w, StringComparison.Ordinal)).ToList();
        if (miss.Count > 0) issues.Add("EXTENSION.md 缺判据词：" + string.Join(",", miss));

        var sections = SplitDiffByFile(NormalizeNewlines(diffText));
        var recordFace = Section(sections, "02_联动注册表.md") + "\n"
                         + Section(sections, "protocol/EXTENSION.md");
        var bumps = new List<string>();
        foreach (var rel in FileList(root))
        {
            var diff = Section(sections, rel);
            if (diff.Length == 0) continue;
            var old = new HashSet<string>(StringComparer.Ordinal);
            var fresh = new HashSet<string>(StringComparer.Ordinal);
            foreach (var line in diff.Split('\n'))
            {
                if (line.StartsWith("---", StringComparison.Ordinal)
                    || line.StartsWith("+++", StringComparison.Ordinal)) continue;
                if (line.Length == 0 || (line[0] != '-' && line[0] != '+')) continue;
                var body = line[1..];
                if (!VersionTokenRe.IsMatch(body)) continue;   // 只认版本字段行
                var value = ParseVersion(body);
                if (value is null) continue;
                (line[0] == '-' ? old : fresh).Add(value);
            }
            if (old.Count == 0 || fresh.Count == 0 || old.SetEquals(fresh)) continue;
            bumps.Add(rel);
            var haystack = diff + "\n" + recordFace;
            var present = FourStepMarkers.Where(m => haystack.Contains(m, StringComparison.Ordinal)).ToList();
            if (present.Count < FourStepMarkers.Length)
            {
                var lacking = FourStepMarkers.Where(m => !present.Contains(m, StringComparer.Ordinal))
                    .OrderBy(m => m, StringComparer.Ordinal);
                issues.Add($"{rel}: 版本字段结构性变更（bump）但无四步迁移记录（缺：{string.Join(",", lacking)}）"
                           + "——记录可内嵌该文件 diff，或写入 02 §9 / protocol/EXTENSION.md 的同次提交 diff");
            }
        }
        return new Result(issues, miss, bumps, true,
            "调用方供 diff（`git diff HEAD` 的标准统一 diff）：bump 面按真源算法逐文件判定");
    }

    /// <summary>真源 <c>tok</c> / <c>parse_version</c> 两个正则（顺序与语义照抄）。</summary>
    private static readonly Regex VersionTokenRe = new(
        "\\b(?:registry_schema_version|schema_version|version)\"?\\s*[:=]\\s*\"?[0-9][0-9.]*\"?",
        RegexOptions.CultureInvariant);
    private static readonly Regex VersionValueRe = new("[:=]\\s*\"?([0-9][0-9.]*)\"?",
        RegexOptions.CultureInvariant);

    private static string? ParseVersion(string line)
    {
        var m = VersionValueRe.Match(line);
        return m.Success ? m.Groups[1].Value : null;
    }

    private static readonly string[] FourStepMarkers =
    {
        "现状快照", "bump 声明", "迁移说明", "校验回读",
    };

    /// <summary>真源 <c>files</c> 清单：三件固定 + `protocol/schema/*.json` + `community/*/protocol.yaml`（各自排序）。</summary>
    public static List<string> FileList(string root)
    {
        var files = new List<string> { "01_核心协议.md", "02_联动注册表.md", "desktop/src/core/registry.json" };
        var schemaDir = Path.Combine(root, "protocol", "schema");
        if (Directory.Exists(schemaDir))
        {
            files.AddRange(Directory.GetFiles(schemaDir, "*.json")
                .Select(f => "protocol/schema/" + Path.GetFileName(f))
                .OrderBy(p => p, StringComparer.Ordinal));
        }
        var community = Path.Combine(root, "community");
        if (Directory.Exists(community))
        {
            files.AddRange(Directory.GetDirectories(community)
                .OrderBy(d => Path.GetFileName(d), StringComparer.Ordinal)
                .Select(d => "community/" + Path.GetFileName(d) + "/protocol.yaml")
                .Where(rel => File.Exists(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)))));
        }
        return files;
    }

    /// <summary>把标准统一 diff 按 <c>diff --git a/X b/Y</c> 切成「每文件一段」（真源是逐文件 <c>git diff</c>，两式等价）。</summary>
    private static Dictionary<string, string> SplitDiffByFile(string diffText)
    {
        var sections = new Dictionary<string, string>(StringComparer.Ordinal);
        var current = "";
        var buffer = new List<string>();
        void Flush()
        {
            if (current.Length > 0) sections[current] = string.Join("\n", buffer);
            buffer.Clear();
        }
        foreach (var line in diffText.Split('\n'))
        {
            if (line.StartsWith("diff --git ", StringComparison.Ordinal))
            {
                Flush();
                current = PathFromDiffHeader(line);
            }
            if (current.Length > 0) buffer.Add(line);
        }
        Flush();
        return sections;
    }

    /// <summary>
    /// 从 <c>diff --git a/X b/Y</c> 取出新路径 Y。**非 ASCII 路径会被 git 按 <c>core.quotePath</c>
    /// 的 C 风格引号包起来（八进制转义）**——实测踩过：不解码就取不到 `02_联动注册表.md` 的段，
    /// bump 面于是恒报「bump 文件 0」（假绿）。此处按 git 的转义表解码（含 <c>\NNN</c> 八进制 → UTF-8）。
    /// </summary>
    private static string PathFromDiffHeader(string line)
    {
        var rest = line["diff --git ".Length..];
        if (rest.StartsWith('"'))
        {
            var parts = Regex.Matches(rest, "\"((?:[^\"\\\\]|\\\\.)*)\"");
            if (parts.Count >= 2)
            {
                var second = GitUnquote(parts[1].Groups[1].Value);
                return second.StartsWith("b/", StringComparison.Ordinal) ? second[2..] : second;
            }
            return "";
        }
        var marker = rest.IndexOf(" b/", StringComparison.Ordinal);
        return marker >= 0 ? rest[(marker + 3)..] : "";
    }

    /// <summary>按 git 的 C 风格引号规则还原路径：<c>\\ \&quot; \a \b \f \n \r \t \v</c> 与 <c>\NNN</c>（八进制字节）。</summary>
    private static string GitUnquote(string value)
    {
        var bytes = new List<byte>();
        for (var i = 0; i < value.Length; i++)
        {
            var ch = value[i];
            if (ch != '\\' || i + 1 >= value.Length)
            {
                bytes.AddRange(Encoding.UTF8.GetBytes(ch.ToString()));
                continue;
            }
            var next = value[++i];
            switch (next)
            {
                case 'a': bytes.Add(0x07); break;
                case 'b': bytes.Add(0x08); break;
                case 'f': bytes.Add(0x0C); break;
                case 'n': bytes.Add(0x0A); break;
                case 'r': bytes.Add(0x0D); break;
                case 't': bytes.Add(0x09); break;
                case 'v': bytes.Add(0x0B); break;
                case '\\': bytes.Add(0x5C); break;
                case '"': bytes.Add(0x22); break;
                default:
                    if (next is >= '0' and <= '7')
                    {
                        var octal = next.ToString();
                        for (var k = 0; k < 2 && i + 1 < value.Length && value[i + 1] is >= '0' and <= '7'; k++)
                            octal += value[++i];
                        bytes.Add(Convert.ToByte(octal, 8));
                    }
                    else
                    {
                        bytes.AddRange(Encoding.UTF8.GetBytes(next.ToString()));
                    }
                    break;
            }
        }
        return Encoding.UTF8.GetString(bytes.ToArray());
    }

    private static string Section(Dictionary<string, string> sections, string rel) =>
        sections.TryGetValue(rel, out var text) ? text : "";
}
