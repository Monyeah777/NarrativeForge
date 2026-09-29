using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>verify.sh</c> 的两条**纯 shell** 结构断言（第八十八片起，证据通道 = 真源 shell 本体当 oracle）：
///
/// ① <c>check1</c> 官方核心目录结构（07 §7 项1）：根级 6 件 · <c>03_管线库</c> 官方三管线（P00/P01/P90）·
///    <c>04_模块库</c> 核心 13 件逐件在场 · <c>05_资产库</c> = 总 README + <c>用户自定义</c> 扩增槽目录；
/// ② <c>check7</c> 社区两包结构完整（07 §7 项2，**T6 在册数一致性**）：<c>02 §8.1/§8.2</c> 登记行反解在册模块数，
///    与 <c>community/&lt;包&gt;/modules</c> 实存件数比对（**防注册表与文件失同步**）· 资产固定 29 / 23 件 ·
///    顶层 README 与 <c>P02/P03</c> 管线在场。
///
/// <b>逐字对齐的四处 shell 语义</b>（都不"顺手修好"）：
/// 1. 段号锚点必须带**尾随空格**（<c>^### 8\\.1 </c>）——真源注释点明「不带空格会连 <c>### 8.10</c> 一起命中」；
/// 2. <c>regxy</c> 用 <c>grep -oE</c> 收集**全部**命中：多于一个时它是**多行字符串**，数值比较报错 → 判"不一致"；
/// 3. ok 行的 <c>${cmod:-9}</c> / <c>${regxy:-9}</c> 是**默认值展开**：包不在场时用 9 / 14 兜底；
/// 4. <b>一处真源缺陷（照抄 + 登记）</b>：两个社区包**双双不在场**时，<c>err</c> 不会被置位（只有 <c>wn</c>），
///    于是 check7 仍打 <c>[PASS] …结构完整</c>，数字还是默认的 9/14/29/23 ——「包没了却报结构完整」。
/// </summary>
public static class StructureGate
{
    public static readonly string[] RootFiles =
    {
        "01_核心协议.md", "02_联动注册表.md", "06_Agent执行协议.md",
        "07_官方核心出厂与社区预设导航.md", "README.md", "LICENSE",
    };

    public static readonly string[] Pipelines =
    {
        "P00_通用文档生成管线.md", "P01_标准管线.md", "P90_技术文档生成管线.md",
    };

    public static readonly string[] CoreModules =
    {
        "04_模块库/世界类/M08_季节天气.md",
        "04_模块库/事件类/M06_任务剧情.md",
        "04_模块库/事件类/M12_NPC对话.md",
        "04_模块库/事件类/M13_NPC交互.md",
        "04_模块库/事件类/M20_世界知识库.md",
        "04_模块库/事件类/M22_事件叙事.md",
        "04_模块库/技术文档类/M90_技术文档结构.md",
        "04_模块库/通用类/M00_数据结构.md",
        "04_模块库/通用类/M10_时间推进.md",
        "04_模块库/通用类/M23_认知边界.md",
        "04_模块库/通用类/M24_组合规则.md",
        "04_模块库/通用类/M50_主循环.md",
        "04_模块库/通用类/M80_输出生成器.md",
    };

    private static readonly Regex ModulesInRegistry = new("模块（([0-9]+)）", RegexOptions.Compiled);

    public sealed record Result(List<string> Log, int Pass, int Fail, int Warn)
    {
        public bool Ok => Fail == 0;

        public string LogDigest => Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(
                Encoding.UTF8.GetBytes(string.Join("\n", Log)))).ToLowerInvariant()[..32];
    }

    /// <summary>两条结构断言串联（顺序同 verify.sh：check1 → check7）。</summary>
    public static Result Run(string root)
    {
        var first = Check1(root);
        var second = Check7(root);
        return new Result(
            first.Log.Concat(second.Log).ToList(),
            first.Pass + second.Pass,
            first.Fail + second.Fail,
            first.Warn + second.Warn);
    }

    public static Result Check1(string root)
    {
        var log = new List<string>();
        var pass = 0;
        var fail = 0;
        var err = false;
        foreach (var file in RootFiles)
        {
            if (!File.Exists(Path.Combine(root, file)))
            {
                fail++;
                log.Add($"  [FAIL] 根级缺失: {file}");
                err = true;
            }
        }
        foreach (var pipeline in Pipelines)
        {
            if (!File.Exists(Path.Combine(root, "03_管线库", pipeline)))
            {
                fail++;
                log.Add($"  [FAIL] 03 缺官方管线文件: {pipeline}");
                err = true;
            }
        }
        foreach (var module in CoreModules)
        {
            if (!File.Exists(Path.Combine(root, module.Replace('/', Path.DirectorySeparatorChar))))
            {
                fail++;
                log.Add($"  [FAIL] 04 缺核心模块: {module}");
                err = true;
            }
        }
        if (!File.Exists(Path.Combine(root, "05_资产库", "README.md")))
        {
            fail++;
            log.Add("  [FAIL] 05_资产库缺总 README");
            err = true;
        }
        if (!Directory.Exists(Path.Combine(root, "05_资产库", "用户自定义")))
        {
            fail++;
            log.Add("  [FAIL] 05 缺 用户自定义 扩增槽目录");
            err = true;
        }
        if (!err)
        {
            pass++;
            log.Add("  [PASS] 根级 6 件；03 官方三管线（P00/P01/P90）；04 核心 13 件逐件在场；"
                    + "05=README+用户自定义");
        }
        return new Result(log, pass, fail, 0);
    }

    public static Result Check7(string root)
    {
        var log = new List<string>();
        var pass = 0;
        var fail = 0;
        var warn = 0;
        var err = false;

        var regxy = "";
        var regxh = "";
        var registryPath = Path.Combine(root, "02_联动注册表.md");
        if (File.Exists(registryPath))
        {
            var registry = NormalizeNewlines(File.ReadAllText(registryPath, new UTF8Encoding(false)));
            regxy = ModulesRegistered(Section(registry, "^### 8\\.1 ", "^### 8\\.2 "));
            regxh = ModulesRegistered(Section(registry, "^### 8\\.2 ", "^### 8\\.3 "));
        }

        string campusSummary;
        var campusDir = Path.Combine(root, "community", "校园情感领域包");
        if (Directory.Exists(campusDir))
        {
            var cmod = CountMarkdown(Path.Combine(campusDir, "modules"), excludeReadme: false);
            var cass = CountMarkdown(Path.Combine(campusDir, "assets"), excludeReadme: true);
            if (regxy.Length == 0)
            {
                fail++;
                log.Add("  [FAIL] 02 §8.1 未取到校园包在册模块数（登记行缺失）");
                err = true;
            }
            if (!long.TryParse(regxy, out var campusRegistered) || cmod != campusRegistered)
            {
                fail++;
                log.Add($"  [FAIL] 校园包 modules 实存 {cmod} 件，02 §8.1 在册 {regxy} 件——不一致");
                err = true;
            }
            if (cass != 29)
            {
                fail++;
                log.Add($"  [FAIL] 校园包 assets 应 29 件，实为 {cass}");
                err = true;
            }
            if (!File.Exists(Path.Combine(campusDir, "README.md")))
            {
                fail++;
                log.Add("  [FAIL] 校园包缺顶层 README");
                err = true;
            }
            if (!File.Exists(Path.Combine(campusDir, "pipelines", "P02_校园情感流管线.md")))
            {
                fail++;
                log.Add("  [FAIL] 校园包缺 pipelines/P02_校园情感流管线.md");
                err = true;
            }
            campusSummary = $"校园 {cmod} 模块+29 资产+P02+README"
                            + $"（与 02 §8.1 在册 {(regxy.Length > 0 ? regxy : "9")} 一致）";
        }
        else
        {
            warn++;
            log.Add("  [WARN] 校园情感领域包不在场（跳过其结构校验）");
            campusSummary = "校园 9 模块+29 资产+P02+README（与 02 §8.1 在册 9 一致）";
        }

        string westSummary;
        var westDir = Path.Combine(root, "community", "西幻生存领域包");
        if (Directory.Exists(westDir))
        {
            var xmod = CountMarkdown(Path.Combine(westDir, "modules"), excludeReadme: false);
            var xass = CountMarkdown(Path.Combine(westDir, "assets"), excludeReadme: true);
            if (regxh.Length == 0)
            {
                fail++;
                log.Add("  [FAIL] 02 §8.2 未取到西幻包在册模块数（登记行缺失）");
                err = true;
            }
            if (!long.TryParse(regxh, out var westRegistered) || xmod != westRegistered)
            {
                fail++;
                log.Add($"  [FAIL] 西幻包 modules 实存 {xmod} 件，02 §8.2 在册 {regxh} 件——不一致");
                err = true;
            }
            if (xass != 23)
            {
                fail++;
                log.Add($"  [FAIL] 西幻包 assets 应 23 件，实为 {xass}");
                err = true;
            }
            if (!File.Exists(Path.Combine(westDir, "README.md")))
            {
                fail++;
                log.Add("  [FAIL] 西幻包缺顶层 README");
                err = true;
            }
            if (!File.Exists(Path.Combine(westDir, "pipelines", "P03_西幻生存流管线.md")))
            {
                fail++;
                log.Add("  [FAIL] 西幻包缺 pipelines/P03_西幻生存流管线.md");
                err = true;
            }
            westSummary = $"西幻 {xmod} 模块+23 资产+P03+README"
                          + $"（与 02 §8.2 在册 {(regxh.Length > 0 ? regxh : "14")} 一致）";
        }
        else
        {
            warn++;
            log.Add("  [WARN] 西幻生存领域包不在场（跳过其结构校验）");
            westSummary = "西幻 14 模块+23 资产+P03+README（与 02 §8.2 在册 14 一致）";
        }

        // 照抄真源：包不在场时 err 未置位 → 这行**照样**打 PASS（真源缺陷，已登记）
        if (!err)
        {
            pass++;
            log.Add($"  [PASS] {campusSummary}；{westSummary}结构完整");
        }
        return new Result(log, pass, fail, warn);
    }

    /// <summary>sed 范围：从首个命中 <paramref name="startPattern"/> 的行到首个命中 <paramref name="endPattern"/> 的行（含）。</summary>
    private static string Section(string text, string startPattern, string endPattern)
    {
        var collected = new List<string>();
        var inRange = false;
        foreach (var line in KnowledgeSig.SplitLines(text))
        {
            if (!inRange && Regex.IsMatch(line, startPattern)) inRange = true;
            if (!inRange) continue;
            collected.Add(line);
            if (Regex.IsMatch(line, endPattern)) break;
        }
        return string.Join("\n", collected);
    }

    /// <summary><c>grep -oE '模块（[0-9]+）' | grep -oE '[0-9]+'</c>：多命中时是**多行**字符串（照抄）。</summary>
    private static string ModulesRegistered(string section)
    {
        var numbers = ModulesInRegistry.Matches(section).Select(m => m.Groups[1].Value).ToList();
        return string.Join("\n", numbers);
    }

    /// <summary><c>find &lt;dir&gt; -name '*.md' | wc -l</c>（目录不在场 = 0）。</summary>
    private static int CountMarkdown(string dir, bool excludeReadme)
    {
        if (!Directory.Exists(dir)) return 0;
        return Directory.GetFiles(dir, "*", SearchOption.AllDirectories)
            .Count(f => f.EndsWith(".md", StringComparison.Ordinal)
                        && (!excludeReadme || Path.GetFileName(f) != "README.md"));
    }

    private static string NormalizeNewlines(string text) => text.Replace("\r\n", "\n").Replace('\r', '\n');
}
