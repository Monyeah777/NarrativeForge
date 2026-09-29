using System.Text;
using System.Text.RegularExpressions;
using System.Security.Cryptography;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>verify.sh</c> <c>check20</c>（**文档完整性门禁** · v2.2.0 A3：模块文档必填项）的**分层判据**：
///
/// - **官方核心 13 件**（<c>04_模块库/*/*.md</c>）→ **机读完备强校验**：必须含 <c>machine_contract</c>，
///   且标题格式、元数据行（类别 / 来源 / 挂载点 / 依赖）、章节（职责 / 核心逻辑 …）齐备，**缺即 FAIL**；
/// - **社区模块**（<c>community/*/modules/*.md</c>）→ 含 <c>machine_contract</c> 者**同结构强校验**；
///   **未完备存量只 WARN + 统计**（随 13 方案过渡策略演进，**不阻断**既有 PASS）。
///
/// 真源里 check20 **只被 <c>verify.sh</c> 消费**（没有 <c>nf</c> 子命令面），故本件**不新增 CLI 面**：
/// 证据通道 = 真材料（真仓）+ 合成负例（自检钉）+ 探针 <c>probes/doc_completeness_probe.py</c>
/// （把 verify.sh 里那段 Python **原文抽出**，与本件在同一棵树上双跑对账）。
///
/// **三处口径如实照抄**：
/// ① 标题正则 <c>^# (模块|M\d+|情感:|生存:|事件:|通用:)[^#]*</c> 只对**首行**求值（<c>re.match</c> 锚定串首）；
/// ② 元数据行取**前 6 行**合并查找（键可分布多行）；
/// ③ 社区未完备件**进 WARN 统计但不进 errs**——所以「有 WARN」不等于红。
///
/// **两处受控化差异（登记，不冒充等价）**：文件不可读（权限/编码）时，Python 侧抛未捕获异常（traceback 进 log），
/// 本件收敛为可读问题条目；另外 Python 文本模式做**universal newlines**（<c>\r\n</c> / <c>\r</c> → <c>\n</c>），
/// 本件读取时同法归一。
/// </summary>
public static class DocCompleteness
{
    private static readonly string[] ReqMeta = { "类别", "来源", "挂载点", "依赖" };

    /// <summary>真源 <c>re.match(r'^# (模块|M\d+|情感:|生存:|事件:|通用:)[^#]*', head)</c>。</summary>
    private static readonly Regex TitleRe =
        new("^# (模块|M\\d+|情感:|生存:|事件:|通用:)[^#]*", RegexOptions.Compiled);

    /// <summary>真源的五条「章节在场」任一即可（<c>## 2 输入输出</c> 无点号是有意为之——照抄）。</summary>
    private static readonly string[] ChapterMarkers =
        { "## 职责", "## 核心逻辑", "## 1. 职责", "## 1 职责", "## 2 输入输出" };

    public sealed record Result(
        List<string> Issues,
        List<string> IncompleteBases,
        int CoreCount,
        int CommunityCount,
        int IncompleteCount,
        List<string> Log)
    {
        public bool Ok => Issues.Count == 0;

        /// <summary>真源失败时的文案：<c>head -5 &lt;log&gt; | tr '\n' ' '</c>。</summary>
        public string Head5 => string.Join(" ", Log.Take(5));

        /// <summary>
        /// 日志**逐字节**摘要（<c>sha256("\n".join(日志行))[:32]</c>，与真源 stdout 同口径）——
        /// 用来把「引擎侧的 check20 输出」与「verify.sh 里那段 Python 的输出」做逐字节对账，
        /// 金标向量见 <c>probes/_fixtures/_doc_completeness_golden.json</c>。
        /// </summary>
        public string LogDigest => Convert.ToHexString(
            SHA256.HashData(Encoding.UTF8.GetBytes(string.Join("\n", Log)))).ToLowerInvariant()[..32];
    }

    public static Result Check(string root)
    {
        var issues = new List<string>();
        var incomplete = new List<(string Base, List<string> Issues)>();

        var coreFiles = GlobCoreModules(root);
        foreach (var rel in coreFiles)
        {
            var (fileIssues, _) = CheckFile(root, rel, strict: true);
            foreach (var issue in fileIssues) issues.Add("[官方] " + issue);
        }

        var communityFiles = GlobCommunityModules(root);
        foreach (var rel in communityFiles)
        {
            var (fileIssues, hasMachineContract) = CheckFile(root, rel, strict: false);
            if (hasMachineContract)
            {
                foreach (var issue in fileIssues) issues.Add("[社区] " + issue);
            }
            else if (fileIssues.Count > 0)
            {
                incomplete.Add((Path.GetFileName(rel), fileIssues));
            }
        }

        var log = new List<string>
        {
            $"文档完整性扫描：官方 {coreFiles.Count} 件 + 社区 {communityFiles.Count} 件"
            + $"（社区机读完备强校验；未完备存量 WARN 统计 {incomplete.Count} 件）",
        };
        foreach (var (baseName, fileIssues) in incomplete)
            log.Add($" [WARN] 社区未完备存量（过渡期不阻断，随 retro-fit）：{baseName} {string.Join("；", fileIssues.Take(2))}");
        foreach (var issue in issues)
            log.Add(" [FAIL] " + issue);
        if (incomplete.Count > 0)
            log.Add($" [STAT] 社区未完备 {incomplete.Count} 件（WARN 统计，随 13 方案过渡策略演进）");

        return new Result(
            issues,
            incomplete.Select(x => x.Base).ToList(),
            coreFiles.Count,
            communityFiles.Count,
            incomplete.Count,
            log);
    }

    private static (List<string> Issues, bool HasMachineContract) CheckFile(string root, string rel, bool strict)
    {
        var issues = new List<string>();
        var name = Path.GetFileName(rel);
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        var text = ReadNormalized(path, name, issues);

        var hasMachineContract = text.Contains("machine_contract", StringComparison.Ordinal);
        if (strict && !hasMachineContract)
            issues.Add($"{name} 缺 machine_contract（01 §1.1 机读契约，官方模块必含）");

        var head = text.Length > 0 ? text.Split('\n', 2)[0] : "";
        if (!TitleRe.IsMatch(head))
            issues.Add($"{name} 标题格式异常（应 # 模块 Mxx · 名称）");

        var metaBlock = string.Join("\n", text.Split('\n').Take(6));
        foreach (var key in ReqMeta)
        {
            if (!metaBlock.Contains(key, StringComparison.Ordinal))
                issues.Add($"{name} 元数据缺 {key}（标题下应含 > 类别/来源/挂载点/依赖 行）");
        }

        if (!ChapterMarkers.Any(marker => text.Contains(marker, StringComparison.Ordinal)))
            issues.Add($"{name} 缺 职责/核心逻辑 章节");

        return (issues, hasMachineContract);
    }

    /// <summary>Python 文本模式的 universal newlines：<c>\r\n</c> 与孤立 <c>\r</c> 都归一为 <c>\n</c>。</summary>
    private static string ReadNormalized(string path, string name, List<string> issues)
    {
        try
        {
            var raw = File.ReadAllText(path, new UTF8Encoding(false));
            return raw.Replace("\r\n", "\n").Replace('\r', '\n');
        }
        catch (Exception ex)
        {
            issues.Add($"{name} 不可读（{ex.GetType().Name}：{ex.Message}）");
            return "";
        }
    }

    /// <summary>Python <c>glob.glob('04_模块库/*/*.md')</c>：**单层**子目录；<c>*</c> 不匹配以 <c>.</c> 开头的名字。</summary>
    private static List<string> GlobCoreModules(string root)
    {
        var result = new List<string>();
        var baseDir = Path.Combine(root, "04_模块库");
        if (!Directory.Exists(baseDir)) return result;
        foreach (var sub in Directory.GetDirectories(baseDir))
        {
            var subName = Path.GetFileName(sub);
            if (subName.StartsWith('.')) continue;
            foreach (var file in Directory.GetFiles(sub, "*.md"))
            {
                var fileName = Path.GetFileName(file);
                if (fileName.StartsWith('.')) continue;
                result.Add($"04_模块库/{subName}/{fileName}");
            }
        }
        result.Sort(StringComparer.Ordinal);
        return result;
    }

    /// <summary>Python <c>glob.glob('community/*/modules/*.md')</c>。</summary>
    private static List<string> GlobCommunityModules(string root)
    {
        var result = new List<string>();
        var community = Path.Combine(root, "community");
        if (!Directory.Exists(community)) return result;
        foreach (var pack in Directory.GetDirectories(community))
        {
            var packName = Path.GetFileName(pack);
            if (packName.StartsWith('.')) continue;
            var modulesDir = Path.Combine(pack, "modules");
            if (!Directory.Exists(modulesDir)) continue;
            foreach (var file in Directory.GetFiles(modulesDir, "*.md"))
            {
                var fileName = Path.GetFileName(file);
                if (fileName.StartsWith('.')) continue;
                result.Add($"community/{packName}/modules/{fileName}");
            }
        }
        result.Sort(StringComparer.Ordinal);
        return result;
    }
}
