using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

// 复刻 scripts/reconcile_assets.sh（资产-模块三方对账 · 08 方案 T5 A5）的 **--quiet 输出面 + 退出码**。
//
// 三方：02 §8.1/§8.2 在册登记行 ↔ community/<包>/modules/ 实存 ↔ <包>/assets/README.md 引用；
// 三类告警：幽灵编号（README 引用无文件且未豁免）· 孤儿模块（实存未登记）· 未登记模块（在册无文件）。
//
// 照抄的三处口径：
// ① 编号提取只认**恰好两位数字**（awk substr 后 length==2）——M001/M899 等三位伪编号与孤立 M 自动排除；
// ② 登记行用 `grep -E '^- 模块（9）：'` / `'^- 模块（14）：'` **硬编码条数**取第一行——条数变了就取不到，
//    此时 reg_ids 为空 → 所有实存模块都会被报成「孤儿模块」（脚本自身没有「登记行缺失」守卫，照抄）；
// ③ `--quiet` 只静音 `say`（进度与表头），**告警行、汇总行与结论行照打**——check11 靠退出码判，输出进 stdout。
public static class AssetReconcile
{
    public const string ScriptRel = "scripts/reconcile_assets.sh";

    private static readonly Regex MNumber = new("M[0-9]+", RegexOptions.Compiled);
    private static readonly Regex FileNumber = new("^M([0-9]+)_.*", RegexOptions.Compiled);

    private static readonly string[] RemnantXy = { "07", "10", "21", "26", "34", "42", "60", "62" };
    private static readonly string[] RemnantXh = { "21" };

    public sealed record Result(List<string> Lines, int Ghosts, int Orphans, int Unregistered)
    {
        public bool Clean => Ghosts + Orphans + Unregistered == 0;
        public int ExitCode => Clean ? 0 : 1;
    }

    /// <summary>等价 `bash scripts/reconcile_assets.sh --quiet` 的 stdout 与退出码。</summary>
    public static Result Run(string root)
    {
        var lines = new List<string>();
        var core = CoreNumbers(root);
        var registry = Read(root, "02_联动注册表.md");
        var regXy = FirstLineMatching(registry, "^- 模块（9）：");
        var regXh = FirstLineMatching(registry, "^- 模块（14）：");

        var ghosts = 0;
        var orphans = 0;
        var unregistered = 0;
        ReconcilePackage(root, regXy, "community/校园情感领域包", "校园", RemnantXy, core,
                         lines, ref ghosts, ref orphans, ref unregistered);
        ReconcilePackage(root, regXh, "community/西幻生存领域包", "西幻", RemnantXh, core,
                         lines, ref ghosts, ref orphans, ref unregistered);

        lines.Add($"对账汇总: 幽灵编号={ghosts}  孤儿模块={orphans}  未登记模块={unregistered}");
        lines.Add(ghosts + orphans + unregistered > 0
            ? ">>> 存在告警 = 资产-模块对账不一致：请核对 02 §8.1 / modules/ 实存 / assets/README 引用与豁免清单 <<<"
            : ">>> 对账全清：零幽灵（源编号残留已豁免）/ 零孤儿 / 零未登记，变更可提交 <<<");
        return new Result(lines, ghosts, orphans, unregistered);
    }

    private static void ReconcilePackage(string root, string regLine, string pkg, string name,
                                         string[] remnant, List<string> core, List<string> lines,
                                         ref int ghosts, ref int orphans, ref int unregistered)
    {
        var regIds = IdsOf(regLine);
        var modIds = FileNumbers(Path.Combine(root, pkg.Replace('/', Path.DirectorySeparatorChar), "modules"));
        foreach (var m in modIds)
        {
            if (!regIds.Contains(m))
            {
                orphans++;
                lines.Add($"  [孤儿模块] {name} modules/M{m} 实存但 02 §8.1 未登记");
            }
        }
        foreach (var m in regIds)
        {
            if (!modIds.Contains(m))
            {
                unregistered++;
                lines.Add($"  [未登记模块] 02 §8.1 在册 {name} M{m} 但 modules/ 无对应文件");
            }
        }
        var readmePath = Path.Combine(root, pkg.Replace('/', Path.DirectorySeparatorChar), "assets", "README.md");
        var refs = File.Exists(readmePath) ? IdsOf(File.ReadAllText(readmePath, new UTF8Encoding(false))) : new List<string>();
        foreach (var r in refs)
        {
            var exempt = core.Contains(r) || modIds.Contains(r) || remnant.Contains(r);
            if (exempt) continue;
            ghosts++;
            lines.Add($"  [幽灵编号] {name} assets/README.md 引用 M{r}：无对应文件"
                      + "（非官方核心 / 非本包 modules / 非源编号残留豁免）");
        }
    }

    /// <summary>`find 04_模块库 -type f -name 'M[0-9]*.md'` → `sed -E 's/^M([0-9]+)_.*/\1/'` → `sort -u`。</summary>
    private static List<string> CoreNumbers(string root) =>
        FileNumbers(Path.Combine(root, "04_模块库"));

    private static List<string> FileNumbers(string dir)
    {
        var outList = new List<string>();
        if (!Directory.Exists(dir)) return outList;
        foreach (var file in Directory.GetFiles(dir, "*", SearchOption.AllDirectories))
        {
            var name = Path.GetFileName(file);
            if (!name.EndsWith(".md", StringComparison.Ordinal)) continue;
            if (!Regex.IsMatch(name, "^M[0-9].*")) continue;
            var match = FileNumber.Match(name);
            outList.Add(match.Success ? match.Groups[1].Value : name);
        }
        outList = outList.Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToList();
        return outList;
    }

    /// <summary>`grep -oE 'M[0-9]+' | awk 取两位数字 | sort -u`。</summary>
    private static List<string> IdsOf(string text)
    {
        var ids = MNumber.Matches(text).Select(m => m.Value[1..])
            .Where(digits => digits.Length == 2)
            .Distinct(StringComparer.Ordinal)
            .OrderBy(x => x, StringComparer.Ordinal)
            .ToList();
        return ids;
    }

    /// <summary>`grep -E '&lt;pattern&gt;' file | head -1`。</summary>
    private static string FirstLineMatching(string text, string pattern)
    {
        foreach (var line in KnowledgeSig.SplitLines(text))
        {
            if (Regex.IsMatch(line, pattern)) return line;
        }
        return "";
    }

    private static string Read(string root, string rel)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        return File.Exists(path) ? File.ReadAllText(path, new UTF8Encoding(false)) : "";
    }
}
