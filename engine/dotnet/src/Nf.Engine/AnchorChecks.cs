using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

// 复刻 verify.sh 段 A/B 里七条「锚点断言」（check2/3/4/5/6/9/10）。
//
// 它们此前被记作「散文面」，但读代码后可见判据是 **grep 锚点 + 件在场 + 一段 awk 行扫描**，
// 属**可机检**，只是判定对象是文档。第八十九片起用**真源 bash 函数本体当 oracle**
// （probes/shell_check_probe.py）逐字节对账。
//
// 两处 bash 语义照抄：① grep -q 对**缺件**返回非零 → 判失败（Has 对缺件返回 false）；
// ② awk 行扫描若**文件不存在**，bad 是**空串**（不是 0）→ 数值比较报错 → 判失败**且文案数字位为空**。
public static class AnchorChecks
{
    private static readonly string[] CategoryWords = { "通用", "生存", "情感", "事件" };
    private static readonly Regex M10Re = new("(^|[^0-9])M10([^0-9]|$)", RegexOptions.Compiled);
    private static readonly Regex M22Re = new("(^|[^0-9])M22([^0-9]|$)", RegexOptions.Compiled);

    public sealed record Result(List<string> Log, int Pass, int Fail, int Warn)
    {
        public bool Ok => Fail == 0;

        public string LogDigest => Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(
                Encoding.UTF8.GetBytes(string.Join("\n", Log)))).ToLowerInvariant()[..32];
    }

    /// <summary>
    /// check11 委派的 <c>reconcile_assets.sh</c> 的 **stdout**（对账汇总行与结论行）。
    ///
    /// 为什么单独放：真源里这段是**子进程直接打到 verify.sh 的 stdout**，而本工程的探针口径是
    /// 「只比 <c>[PASS]/[FAIL]/[WARN]</c> **裁决行**」（脚本的进度/汇总输出不进摘要）——所以它
    /// 既不该混进 <see cref="Result.Log"/>（会比出假差异），也不该丢掉（复算得出的数字要可查）。
    /// </summary>
    public static List<string> ScriptOutput { get; private set; } = new();

    /// <summary>七条锚点断言串联（顺序同 verify.sh：2 → 3 → 4 → 5 → 6 → 9 → 10）。</summary>
    public static Result Run(string root)
    {
        var parts = new[]
        {
            Check2(root), Check3(root), Check4(root), Check5(root),
            Check6(root), Check9(root), Check10(root),
            Check11(root),
        };
        return new Result(
            parts.SelectMany(p => p.Log).ToList(),
            parts.Sum(p => p.Pass),
            parts.Sum(p => p.Fail),
            parts.Sum(p => p.Warn));
    }

    public static Result Check2(string root)
    {
        var log = new List<string>();
        var fail = 0;
        var err = false;
        void No(string message) { fail++; log.Add("  [FAIL] " + message); err = true; }

        if (!File.Exists(Path.Combine(root, "04_模块库", "通用类", "M10_时间推进.md")))
            No("缺 通用类/M10_时间推进.md");
        if (!File.Exists(Path.Combine(root, "04_模块库", "事件类", "M22_事件叙事.md")))
            No("缺 事件类/M22_事件叙事.md");
        var n10 = CountNamed(Path.Combine(root, "04_模块库"), "M10_*.md");
        var n22 = CountNamed(Path.Combine(root, "04_模块库"), "M22_*.md");
        if (n10 != 1) No($"04 内 M10 文件应 1 件（仅通用:M10），实为 {n10}");
        if (n22 != 1) No($"04 内 M22 文件应 1 件（仅事件:M22），实为 {n22}");
        if (!Has(root, "02_联动注册表.md", "通用:M10")) No("注册表缺限定 ID: 通用:M10");
        if (!Has(root, "02_联动注册表.md", "事件:M22")) No("注册表缺限定 ID: 事件:M22");
        foreach (var rel in new[]
                 {
                     "02_联动注册表.md", "06_Agent执行协议.md", "07_官方核心出厂与社区预设导航.md",
                 })
        {
            var bad = AwkBadText(root, rel);
            if (bad != "0") No($"{rel} 含 {bad} 处未类别限定的 M10/M22 引用");
        }
        if (!err)
        {
            log.Add("  [PASS] 04 核心两重号在场（M10/M22 各 1 件）；02 注册两限定 ID；02/06/07 全类别前缀限定");
            return new Result(log, 1, 0, 0);
        }
        return new Result(log, 0, fail, 0);
    }

    public static Result Check3(string root)
    {
        var log = new List<string>();
        var fail = 0;
        var err = false;
        void No(string message) { fail++; log.Add("  [FAIL] " + message); err = true; }
        foreach (var word in new[] { "三正交分离", "核心固定", "通信契约", "数据隔离", "真相唯一" })
        {
            if (!Has(root, "01_核心协议.md", word)) No($"01 §5 缺不变式: {word}");
        }
        foreach (var api in new[] { "asset_get", "asset_query", "asset_match", "asset_roll", "asset_register" })
        {
            if (!Has(root, "01_核心协议.md", api)) No($"I4 五接口缺: {api}");
        }
        var protocol = Read(root, "01_核心协议.md");
        if (!(protocol.Contains("M50", StringComparison.Ordinal) && protocol.Contains("M80", StringComparison.Ordinal)))
            No("I2 核心固定缺 M50/M80 字样");
        if (!err)
        {
            log.Add("  [PASS] I1-I5 五条不变式 + I4 五接口 + I2 核心锚点全部落于 01 §5");
            return new Result(log, 1, 0, 0);
        }
        return new Result(log, 0, fail, 0);
    }

    public static Result Check4(string root)
    {
        var log = new List<string>();
        var fail = 0;
        var err = false;
        void No(string message) { fail++; log.Add("  [FAIL] " + message); err = true; }
        foreach (var word in new[] { "事实管线", "事实快照", "认知裁剪", "裁剪渲染", "锚点回验" })
        {
            if (!Has(root, "06_Agent执行协议.md", word)) No($"06 §4 缺认知层名: {word}");
        }
        foreach (var word in new[] { "视角裁剪", "可见域", "推断域", "隐藏域", "fail", "白描" })
        {
            if (!Has(root, "04_模块库/通用类/M23_认知边界.md", word)) No($"M23 缺认知域措辞: {word}");
        }
        if (!err)
        {
            log.Add("  [PASS] 06 §4 认知五步与 M23 认知域措辞语义一致（快照/裁剪/隐藏域/fail/白描）");
            return new Result(log, 1, 0, 0);
        }
        return new Result(log, 0, fail, 0);
    }

    public static Result Check5(string root)
    {
        var log = new List<string>();
        var fail = 0;
        var err = false;
        void No(string message) { fail++; log.Add("  [FAIL] " + message); err = true; }
        foreach (var word in new[]
                 {
                     "pass:", "warn:", "fail:", "白描", "隐藏域直述", "gate_action", "gate_decision_record",
                 })
        {
            if (!Has(root, "04_模块库/通用类/M80_输出生成器.md", word)) No($"M80 gate 缺: {word}");
        }
        foreach (var word in new[] { "pass", "warn", "fail", "隐藏域直述", "白描" })
        {
            if (!Has(root, "06_Agent执行协议.md", word)) No($"06 §5 gate 缺呼应: {word}");
        }
        if (!err)
        {
            log.Add("  [PASS] M80 gate_action 声明式流水线（pass/warn/fail + 白描降级 + 决策记录）与 06 §5 呼应一致");
            return new Result(log, 1, 0, 0);
        }
        return new Result(log, 0, fail, 0);
    }

    public static Result Check6(string root)
    {
        var log = new List<string>();
        var fail = 0;
        var err = false;
        void No(string message) { fail++; log.Add("  [FAIL] " + message); err = true; }
        if (!Has(root, "README.md", "07_官方核心出厂与社区预设导航"))
            No("README 缺指向 07_官方核心出厂与社区预设导航");
        foreach (var word in new[]
                 {
                     "01_核心协议", "02_联动注册表", "03_管线库", "05_资产库", "06_Agent执行协议", "community",
                 })
        {
            if (!Has(root, "07_官方核心出厂与社区预设导航.md", word)) No($"07 缺引用: {word}");
        }
        foreach (var rel in new[]
                 {
                     "07_官方核心出厂与社区预设导航.md", "01_核心协议.md", "02_联动注册表.md",
                     "06_Agent执行协议.md", "05_资产库/README.md",
                 })
        {
            if (!File.Exists(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))))
                No($"导航目标缺失: {rel}");
        }
        if (!Directory.Exists(Path.Combine(root, "03_管线库"))) No("导航目标缺失: 03_管线库 目录");
        if (!err)
        {
            log.Add("  [PASS] README→07→01/02/06/03/05 官方入口导航闭环可访问");
            return new Result(log, 1, 0, 0);
        }
        return new Result(log, 0, fail, 0);
    }

    public static Result Check9(string root)
    {
        var log = new List<string>();
        var fail = 0;
        var err = false;
        void No(string message) { fail++; log.Add("  [FAIL] " + message); err = true; }
        var pairs = new (string Key, string File)[]
        {
            ("ATTR_TEMPLATES", "community/校园情感领域包/assets/ATTR_TEMPLATES.md"),
            ("LOCATIONS", "community/校园情感领域包/assets/LOCATIONS.md"),
            ("EMOTION_WHEEL", "community/校园情感领域包/assets/EMOTION_WHEEL.md"),
            ("JOB", "community/西幻生存领域包/assets/01_职业成长与基础属性_JOB.md"),
            ("WORLD_KNOWLEDGE", "community/西幻生存领域包/assets/20_世界知识_WORLD_KNOWLEDGE.md"),
        };
        foreach (var (key, file) in pairs)
        {
            if (!File.Exists(Path.Combine(root, file.Replace('/', Path.DirectorySeparatorChar))))
                No($"引用键 {key} 对应资产缺失（应经五接口可寻址）: {file}");
        }
        foreach (var rel in new[]
                 {
                     "community/校园情感领域包/README.md", "community/西幻生存领域包/README.md",
                 })
        {
            if (!File.Exists(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar)))) continue;
            var bad = AwkBadText(root, rel);
            if (bad != "0") No($"{rel} 含 {bad} 处未类别限定的 M10/M22 引用");
        }
        if (!err)
        {
            log.Add("  [PASS] 代表键 ATTR_TEMPLATES/LOCATIONS/EMOTION_WHEEL/JOB/WORLD_KNOWLEDGE 在两包 assets 可寻址；"
                    + "两包 README 的 M10/M22 全类别前缀限定");
            return new Result(log, 1, 0, 0);
        }
        return new Result(log, 0, fail, 0);
    }

    public static Result Check10(string root)
    {
        var log = new List<string>();
        var fail = 0;
        var err = false;
        void No(string message) { fail++; log.Add("  [FAIL] " + message); err = true; }
        const string f1 = "community/西幻生存领域包/assets/01_职业成长与基础属性_JOB.md";
        const string f2 = "community/西幻生存领域包/assets/20_世界知识_WORLD_KNOWLEDGE.md";
        var f1Full = Path.Combine(root, f1.Replace('/', Path.DirectorySeparatorChar));
        var f2Full = Path.Combine(root, f2.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(f1Full)) No($"缺西幻 01: {f1}");
        if (!File.Exists(f2Full)) No($"缺西幻 20: {f2}");
        if (File.Exists(f1Full))
        {
            if (!Has(root, f1, "36820")) No("西幻01 缺 EXT 起始行 36820");
            if (!Has(root, f1, "37280")) No("西幻01 缺 EXT 终止行 37280");
            if (!Has(root, f1, "外部完整实体源")) No("西幻01 缺 EXT 溯源注释");
        }
        if (File.Exists(f2Full))
        {
            if (!Has(root, f2, "28894")) No("西幻20 缺 EXT 起始行 28894");
            if (!Has(root, f2, "29064")) No("西幻20 缺 EXT 终止行 29064");
            if (!Has(root, f2, "外部完整实体源")) No("西幻20 缺 EXT 溯源注释");
            if (!Has(root, f2, "已填充")) No("西幻20 缺 状态已填充 标记");
        }
        const string m22 = "community/校园情感领域包/modules/M22_三冲动驱动.md";
        const string crd = "community/校园情感领域包/README.md";
        if (!File.Exists(Path.Combine(root, m22.Replace('/', Path.DirectorySeparatorChar)))) No($"缺校园 M22: {m22}");
        if (!File.Exists(Path.Combine(root, crd.Replace('/', Path.DirectorySeparatorChar)))) No($"缺校园包 README: {crd}");
        foreach (var word in new[] { "冲动驱动边界", "物理位移", "动作连带", "视线停留", "relationship_change" })
        {
            if (!Has(root, m22, word)) No($"M22 §7 缺冲动隔离措辞: {word}");
        }
        if (!Has(root, m22, "v0.7.12")) No("M22 §7 缺 v0.7.12 版本锚点");
        if (!Has(root, crd, "v0.7.12")) No("校园 README 缺 v0.7.12 版本锚点");
        if (!Has(root, crd, "冲动-社会关系隔离")) No("校园 README 缺 冲动-社会关系隔离 表述");
        if (!Has(root, "06_Agent执行协议.md", "v0.7.12")) No("06 §9 缺 v0.7.12 红线锚点");
        if (!Has(root, "06_Agent执行协议.md", "关系推进权归 M40/M41")) No("06 §9 缺 关系推进权归 M40/M41 表述");
        if (!err)
        {
            log.Add("  [PASS] 西幻01/20 EXT 闭合+溯源注释+已填充；冲动-社会关系隔离三落点一致"
                    + "（M22 §7/校园 README/06 §9 红线7）");
            return new Result(log, 1, 0, 0);
        }
        return new Result(log, 0, fail, 0);
    }

    /// <summary>
    /// check11 资产-模块三方对账：真源是 `bash scripts/reconcile_assets.sh --quiet` 的退出码 + 把脚本 stdout
    /// 直接打进本 check 的输出。本件用 <see cref="AssetReconcile"/> **照其判据复算**，并把脚本的 stdout 逐行并入
    /// （顺序同真源：脚本输出在前，ok/no 行在后）。脚本不在场 → WARN（08 方案 T5 A5 要求缺脚本 WARN）。
    /// </summary>
    public static Result Check11(string root)
    {
        var log = new List<string>();
        var script = Path.Combine(root, AssetReconcile.ScriptRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(script))
        {
            ScriptOutput = new List<string>();
            log.Add("  [WARN] scripts/reconcile_assets.sh 不在场（跳过资产对账；08 方案 T5 A5 要求缺脚本 WARN）");
            // 照抄真源：WARN 分支**不置 err** → 紧随其后的 ok 行照样打（第二处同类缺陷，已登记待裁决）
            log.Add("  [PASS] 资产三方对账全清：幽灵编号=0（源编号残留已豁免）/ 孤儿模块=0 / 未登记模块=0");
            return new Result(log, 1, 0, 1);
        }
        var result = AssetReconcile.Run(root);
        ScriptOutput = result.Lines;   // 脚本 stdout 归这里；**裁决行**才是本 check 的 Log（口径同探针）
        if (!result.Clean)
        {
            log.Add("  [FAIL] reconcile_assets.sh 报告资产对账告警（幽灵编号/孤儿模块/未登记模块任一非零）"
                    + "——核对 02 §8.1 在册、modules/ 实存、assets/README 引用与豁免清单");
            return new Result(log, 0, 1, 0);
        }
        log.Add("  [PASS] 资产三方对账全清：幽灵编号=0（源编号残留已豁免）/ 孤儿模块=0 / 未登记模块=0");
        return new Result(log, 1, 0, 0);
    }

    /// <summary>`grep -q`：缺件 → false（与 shell 同向：grep 对缺件返回非零）。</summary>
    private static bool Has(string root, string rel, string needle)
    {
        var text = Read(root, rel);
        return text.Contains(needle, StringComparison.Ordinal);
    }

    private static string Read(string root, string rel)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return "";
        return File.ReadAllText(path, new UTF8Encoding(false)).Replace("\r\n", "\n").Replace('\r', '\n');
    }

    /// <summary>真源那段 awk 行扫描的等价物；**文件不存在时返回空串**（照抄 bash 的 `bad=""` 空位）。</summary>
    private static string AwkBadText(string root, string rel)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return "";
        var bad = 0;
        foreach (var line in KnowledgeSig.SplitLines(File.ReadAllText(path, new UTF8Encoding(false))))
        {
            var hasCategory = CategoryWords.Any(w => line.Contains(w, StringComparison.Ordinal));
            var m10 = M10Re.IsMatch(line);
            var m22 = M22Re.IsMatch(line);
            if ((m10 || m22) && !hasCategory && !(m10 && m22) && !line.Contains('☐')) bad++;
        }
        return bad.ToString(System.Globalization.CultureInfo.InvariantCulture);
    }

    /// <summary>`find &lt;dir&gt; -name '&lt;pattern&gt;' | wc -l`（目录不在场 = 0）。</summary>
    private static int CountNamed(string dir, string pattern)
    {
        if (!Directory.Exists(dir)) return 0;
        return Directory.GetFiles(dir, pattern, SearchOption.AllDirectories).Length;
    }
}
