using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>verify.sh</c> <c>check13</c>（**协议版本一致性 + 迁移完整性** · 09 方案 T2.3）的三条只读断言：
///
/// ① **版本一致性**：02 文档头部 <c>registry_schema_version</c> == <c>desktop/src/core/registry.json</c>
///    的同名字段（两处同源，结构性变更须两处同步 bump）；
/// ② **迁移完整性**：02 §9.3 迁移记录节在场，且四步关键词齐备（现状快照 / bump 声明 / 迁移说明 / 校验回读）；
/// ③ **模块逐条一致**：02 §2 官方核心模块表 13 行 ID 集合 == <c>registry.json</c> 的 <c>modules[].id</c>
///    （条目数与集合全等，双向差集都报）。
///
/// 真源里 check13 **只被 <c>verify.sh</c> 消费**（没有 <c>nf</c> 子命令面），故本件**不新增 CLI 面**：
/// 证据通道 = 真材料（真仓三条全绿）+ 合成负例（自检钉），与 check31 / check32 同例。
///
/// **两处受控化差异（真源会崩、本件给判定，如实登记，不冒充等价）**：
/// 02 文档缺件 / registry.json 缺件或不可解析时，Python 侧是**未捕获异常**（traceback 进 check13 的 log，
/// verify.sh 只把前 3 行打出来）；本件收敛为**可读问题条目**。判定方向一致（都 FAIL），文案不同。
///
/// **一处口径如实照抄**：② 的关键词搜索范围是 **awk「从 §9.3 标题行到文件末尾」**——所以 §9.4～§9.6
/// 里同样出现的四步关键词**也算数**（真源行为）。本件照抄，**不"顺手修好"**成"只查 §9.3 那一段"。
/// </summary>
public static class CoreRegistry
{
    public const string DocRel = "02_联动注册表.md";
    public const string RegistryRel = "desktop/src/core/registry.json";
    public const int ExpectedModules = 13;

    private const string MigrationHeading = "### 9.3 迁移记录";
    private static readonly string[] MigrationSteps = { "现状快照", "bump 声明", "迁移说明", "校验回读" };

    /// <summary>真源 <c>grep -o 'registry_schema_version: *"[^"]*"'</c>——**空格**零或多（不含制表符/换行）。</summary>
    private static readonly Regex VersionRe =
        new("registry_schema_version: *\"([^\"]*)\"", RegexOptions.Compiled);

    /// <summary>真源 <c>re.search(r'## 2\. 官方核心模块表.*?(?=\n## 3\.)', re.S)</c>。</summary>
    private static readonly Regex ModuleTableRe =
        new("## 2\\. 官方核心模块表.*?(?=\\n## 3\\.)", RegexOptions.Compiled | RegexOptions.Singleline);

    public sealed record Step(string Label, bool Ok, string Detail);

    public sealed record Result(
        List<string> Issues,
        List<Step> Steps,
        string DocVersion,
        string RegVersion,
        int DocRows,
        int RegRows,
        List<string> OnlyDoc,
        List<string> OnlyReg)
    {
        public bool Ok => Issues.Count == 0;
    }

    public static Result Check(string root)
    {
        var issues = new List<string>();
        var steps = new List<Step>();

        var docPath = Path.Combine(root, DocRel.Replace('/', Path.DirectorySeparatorChar));
        var regPath = Path.Combine(root, RegistryRel.Replace('/', Path.DirectorySeparatorChar));

        var doc = ReadTextOrReport(docPath, DocRel, issues);

        // ① 版本一致性
        var match = VersionRe.Match(doc);
        var docVersion = match.Success ? match.Groups[1].Value : "";
        var regVersion = "";
        var regModuleIds = new List<string>();
        try
        {
            if (!File.Exists(regPath))
            {
                issues.Add($"{RegistryRel} 缺件（两处版本须同源、同步 bump）");
            }
            else
            {
                using var json = JsonIo.ReadFile(regPath);
                var regRoot = json.RootElement;
                regVersion = regRoot.TryGetProperty("registry_schema_version", out var ver) ? PyStr(ver) : "";
                if (regRoot.TryGetProperty("modules", out var mods) && mods.ValueKind == JsonValueKind.Array)
                {
                    foreach (var mod in mods.EnumerateArray())
                    {
                        if (mod.ValueKind != JsonValueKind.Object || !mod.TryGetProperty("id", out var id))
                        {
                            issues.Add($"{RegistryRel} 有 modules 条目缺 id（真源此处在 KeyError 上崩，本件给判定）");
                            continue;
                        }
                        regModuleIds.Add(PyStr(id));
                    }
                }
            }
        }
        catch (Exception ex)
        {
            issues.Add($"{RegistryRel} 不可解析（{ex.GetType().Name}：{ex.Message}）");
        }

        if (docVersion.Length > 0 && regVersion.Length > 0)
        {
            if (docVersion == regVersion)
            {
                steps.Add(new Step("version", true,
                    $"协议版本两处一致：02 头部 = desktop registry.json = \"{docVersion}\""));
            }
            else
            {
                var detail = $"协议版本不一致：02=\"{docVersion}\" desktop=\"{regVersion}\"（须两处同步 bump）";
                steps.Add(new Step("version", false, detail));
                issues.Add(detail);
            }
        }
        else
        {
            var detail = $"版本字段缺失：02=\"{Or(docVersion)}\" desktop=\"{Or(regVersion)}\"";
            steps.Add(new Step("version", false, detail));
            issues.Add(detail);
        }

        // ② 迁移完整性（awk：从 §9.3 标题行到文件末尾；行边界按 '\n'——与 awk 的按行记录一致）
        var migrationSegment = MigrationSegment(doc);
        if (migrationSegment.Length > 0)
        {
            var missing = "";
            foreach (var key in MigrationSteps)
                if (!migrationSegment.Contains(key, StringComparison.Ordinal)) missing += " " + key;
            if (missing.Length == 0)
            {
                steps.Add(new Step("migration", true,
                    "迁移记录在场：02 §9.3 四步齐备（现状快照/bump 声明/迁移说明/校验回读）"));
            }
            else
            {
                var detail = $"02 §9.3 迁移记录缺步：{missing}（bump 实体必有迁移记录，按 01 §7 迁移实操四步补全）";
                steps.Add(new Step("migration", false, detail));
                issues.Add(detail);
            }
        }
        else
        {
            const string detail = "02 缺 §9.3 迁移记录节（版本 bump 实体必有迁移记录）";
            steps.Add(new Step("migration", false, detail));
            issues.Add(detail);
        }

        // ③ 模块逐条一致（Python str.splitlines() 语义——真源用的是 m.group(0).splitlines()）
        var docIds = new List<string>();
        var table = ModuleTableRe.Match(doc);
        if (table.Success)
        {
            foreach (var raw in KnowledgeSig.SplitLines(table.Value))
            {
                var cells = raw.Trim().Trim('|').Split('|').Select(c => c.Trim()).ToList();
                if (cells.Count == 5 && cells[0] != "模块ID" && cells[0] != "---" && cells[0].Length > 0)
                    docIds.Add(cells[0]);
            }
        }

        var errs = new List<string>();
        if (docIds.Count != ExpectedModules)
            errs.Add($"02 §2 模块表行数={docIds.Count}（预期 {ExpectedModules}）");
        if (regModuleIds.Count != ExpectedModules)
            errs.Add($"registry.json modules 数={regModuleIds.Count}（预期 {ExpectedModules}）");
        var onlyDoc = docIds.Distinct().Except(regModuleIds.Distinct())
            .OrderBy(x => x, StringComparer.Ordinal).ToList();
        var onlyReg = regModuleIds.Distinct().Except(docIds.Distinct())
            .OrderBy(x => x, StringComparer.Ordinal).ToList();
        if (onlyDoc.Count > 0) errs.Add("02 有而 registry.json 缺：" + string.Join(",", onlyDoc));
        if (onlyReg.Count > 0) errs.Add("registry.json 有而 02 缺：" + string.Join(",", onlyReg));

        if (errs.Count == 0)
        {
            steps.Add(new Step("module-rows", true,
                $"模块逐条一致：02 §2 模块表 {ExpectedModules} 件 == registry.json modules（ID 集合全等）"));
        }
        else
        {
            // 真源把日志前 3 行用空格连起来（verify.sh: head -3 ... | tr '\n' ' '）
            var detail = "模块表与机读投影不一致——" + string.Join(" ", errs.Take(3));
            steps.Add(new Step("module-rows", false, detail));
            issues.Add(detail);
        }

        if (issues.Count == 0)
        {
            steps.Add(new Step("summary", true,
                "协议版本一致性 + 迁移完整性全绿（check13：两处版本一致 + §9.3 四步在场 + 13 件模块全等）"));
        }

        return new Result(issues, steps, docVersion, regVersion, docIds.Count, regModuleIds.Count, onlyDoc, onlyReg);
    }

    /// <summary>Python <c>str()</c> 口径（JSON 值的打印形态：字符串原样 / True / False / None / 数字原文本）。</summary>
    private static string PyStr(JsonElement value) => value.ValueKind switch
    {
        JsonValueKind.String => value.GetString() ?? "",
        JsonValueKind.True => "True",
        JsonValueKind.False => "False",
        JsonValueKind.Null => "None",
        _ => value.GetRawText(),
    };

    private static string Or(string value) => value.Length > 0 ? value : "空";

    /// <summary>awk <c>/^### 9\.3 迁移记录/{f=1} f</c>：从首个行首匹配的标题行起到文件末尾。</summary>
    private static string MigrationSegment(string doc)
    {
        var lines = doc.Split('\n');
        for (var i = 0; i < lines.Length; i++)
        {
            if (lines[i].StartsWith(MigrationHeading, StringComparison.Ordinal))
                return string.Join("\n", lines.Skip(i));
        }
        return "";
    }

    private static string ReadTextOrReport(string path, string rel, List<string> issues)
    {
        if (!File.Exists(path))
        {
            issues.Add($"{rel} 缺件（check13 ① 版本头部与 §2 模块表都取自此件）");
            return "";
        }
        try
        {
            return File.ReadAllText(path, new UTF8Encoding(false));
        }
        catch (Exception ex)
        {
            issues.Add($"{rel} 不可读（{ex.GetType().Name}：{ex.Message}）");
            return "";
        }
    }
}
