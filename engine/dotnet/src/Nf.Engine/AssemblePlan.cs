using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/assemble_plan.py</c>（**`nf assemble`**）：需求 → 澄清漏斗 → 装配计划；`--check` 对成品
/// 做机器验收（八段骨架 / 编号在装配允许集 / 决策句带引用 / 无编造编号）。
///
/// **读面 vs 写面**：本件只移植**读面**（`clarify` / `plan` / `dossier` / `check`）。真源 CLI 的
/// `--session-path`（会话档读写）· `--save-path`（需求档案落盘）· `--trace-path`（工具轨迹落盘）与
/// `--rounds`（需 `core/round_drill`，未移植）都属写面/未移植面——CLI 侧**明确拒绝**，不静默降级。
///
/// **YAML 取值口径（定向抽取）**：真源用 PyYAML 读 <c>community/*/protocol.yaml</c> 的
/// <c>package.id</c> 与 <c>package.module_id_range</c>；引擎的 YAML 子集**不保证嵌套映射**，
/// 故按「`package:` 块内、缩进等于首个子键缩进」的键行定向抽取（与 <see cref="ConformanceScan"/> 同法），
/// 列表项按 <c>- "值"</c> 收集。合法语料上两侧取值一致（面级对账钉住）。
/// </summary>
public static class AssemblePlan
{
    /// <summary>需求关键词 → 官方预设（包 id / 管线 id）。</summary>
    public static readonly (string[] Keys, string Pkg, string Pipeline)[] DomainMap =
    {
        (new[] { "西幻", "生存", "生存流" }, "西幻生存领域包", "P03"),
        (new[] { "校园", "情感", "恋爱", "毕业" }, "校园情感领域包", "P02"),
        (new[] { "轻混", "组合", "混搭" }, "校园西幻轻混组合包", "P04"),
        (new[] { "通用核心", "核心基础" }, "通用核心基础包", "P05"),
        (new[] { "技术文档", "techdoc", "文档工厂" }, "技术文档域包", "P06"),
    };

    /// <summary>未命中官方预设但足以判定「用户有具体自定义题材」的内容线索。</summary>
    public static readonly string[] CustomCues =
    {
        "自定义", "权谋", "宫廷", "科幻", "都市", "悬疑", "恐怖",
        "修仙", "机甲", "冒险", "武侠", "末日", "星际", "盗墓", "权斗",
    };

    private static readonly Regex SegRe = new(@"^##\s*([0-7])\s*\.", RegexOptions.Multiline);
    private static readonly Regex ModuleRe = new(@"(?:[\u4e00-\u9fff]+:)?M\d{2,3}");
    private static readonly Regex DecisionRe = new(@"(应|应该|必须|禁止|不得|下一步|输出|结论)");
    private static readonly Regex CitationRe = new(
        @"(§\s*\d+(?:[.-]\d+)*|第\s*\d+\s*(?:节|步|章)|L\d+|[0-9A-Za-z_]+:[MTP]\d{2,3}|\b\d{1,3}\b\s*行)");
    private static readonly string[] Explanations = { "残留", "不命中", "源编号", "未装配", "说明" };
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>真源 <c>_official_core_ids()</c>：registry 的 <c>modules[].id</c>。</summary>
    public static List<string> OfficialCoreIds(string root)
    {
        using var doc = JsonIo.ReadFile(Path.Combine(root, "desktop", "src", "core", "registry.json"));
        var reg = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
                  ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var ids = new List<string>();
        foreach (var item in ObjList(reg.GetValueOrDefault("modules")))
        {
            if (item is Dictionary<string, object?> row) ids.Add(PyStr(row.GetValueOrDefault("id")));
        }
        return ids;
    }

    /// <summary>真源 <c>_package_module_sets()</c>：各社区包 → 其 `module_id_range`。</summary>
    public static Dictionary<string, List<string>> PackageModuleSets(string root)
    {
        var sets = new Dictionary<string, List<string>>(StringComparer.Ordinal);
        var community = Path.Combine(root, "community");
        if (!Directory.Exists(community)) return sets;
        foreach (var dir in Directory.GetDirectories(community)
                     .OrderBy(d => d, StringComparer.Ordinal))
        {
            var proto = Path.Combine(dir, "protocol.yaml");
            if (!File.Exists(proto)) continue;
            try
            {
                var text = StrictUtf8.GetString(File.ReadAllBytes(proto));
                var (pkg, moduleIds) = PackageIdAndModuleIds(text);
                if (pkg.Length > 0) sets[pkg] = moduleIds;
            }
            catch (Exception)
            {
                // 真源：尽力而为——跳过不可读/不可解析项（该类缺口由对应门禁另行报出）
            }
        }
        return sets;
    }

    /// <summary>
    /// 从 <c>protocol.yaml</c> 定向抽取 <c>package.id</c> 与 <c>package.module_id_range</c>（见类注释）。
    /// 返回 <c>(id, 模块号列表)</c>；取不到给空。
    /// </summary>
    public static (string Package, List<string> ModuleIds) PackageIdAndModuleIds(string text)
    {
        var lines = KnowledgeSig.SplitLines(text);
        var start = -1;
        for (var i = 0; i < lines.Count; i++)
        {
            var trimmed = lines[i].Trim();
            if (trimmed.Length == 0 || trimmed.StartsWith('#')) continue;
            if (trimmed.Split(':', 2)[0].Trim() == "package") { start = i; break; }
        }
        if (start < 0) return ("", new List<string>());
        var baseIndent = IndentOf(lines[start]);
        var childIndent = -1;
        var package = "";
        var moduleIds = new List<string>();
        var inRange = false;
        var rangeIndent = -1;
        for (var j = start + 1; j < lines.Count; j++)
        {
            var trimmed = lines[j].Trim();
            if (trimmed.Length == 0) continue;
            var indent = IndentOf(lines[j]);
            if (trimmed.StartsWith('#')) continue;
            if (indent <= baseIndent) break;
            if (childIndent < 0) childIndent = indent;
            if (inRange && indent > rangeIndent && trimmed.StartsWith('-'))
            {
                moduleIds.Add(PyScalar.YamlScalar(trimmed[1..]));
                continue;
            }
            if (indent != childIndent) continue;
            var parts = trimmed.Split(':', 2);
            if (parts.Length != 2) continue;
            var key = parts[0].Trim();
            if (key == "id" && package.Length == 0) package = PyScalar.YamlScalar(parts[1]);
            inRange = key == "module_id_range";
            if (inRange) rangeIndent = indent;
        }
        return (package, moduleIds);
    }

    /// <summary>真源 <c>clarify(requirement)</c>：信息不足 → 澄清问句；足够 → 直接进 plan。</summary>
    public static Dictionary<string, object?> Clarify(string root, string requirement)
    {
        var req = requirement.Trim();
        if (req.Length == 0)
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["status"] = "clarify", ["requirement"] = req,
                ["questions"] = new List<object?> { "请描述你要的世界：题材方向（如 西幻生存/校园情感/自定义）？" },
            };
        }
        var plan = Plan(root, req);
        if (plan["matched"] is true || CustomCues.Any(cue => req.Contains(cue, StringComparison.Ordinal)))
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["status"] = "ready", ["requirement"] = req, ["plan"] = plan,
                ["questions"] = new List<object?>(),
            };
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["status"] = "clarify", ["requirement"] = req,
            ["questions"] = new List<object?>
            {
                "① 题材方向：官方预设（西幻生存/校园情感/技术文档/轻混/通用核心）还是你的自定义题材？",
                "② 玩法主轴：生存/关系/成长/任务/探索……哪个是推进核心？",
                "③ 世界尺度：单个完整版世界，还是要跨预设组合？",
            },
        };
    }

    /// <summary>真源 <c>plan(requirement)</c>：需求 → 装配计划（预设包 + 取件清单）。</summary>
    public static Dictionary<string, object?> Plan(string root, string requirement)
    {
        var req = requirement.Trim();
        string? pkg = null, pipeline = null;
        foreach (var (keys, hitPkg, hitPipeline) in DomainMap)
        {
            if (!keys.Any(key => req.Contains(key, StringComparison.Ordinal))) continue;
            pkg = hitPkg;
            pipeline = hitPipeline;
            break;
        }
        var modules = new List<string>();
        var matched = pkg is not null;
        if (pkg is not null)
        {
            var proto = Path.Combine(root, "community", pkg, "protocol.yaml");
            if (File.Exists(proto))
            {
                try
                {
                    var (_, moduleIds) = PackageIdAndModuleIds(StrictUtf8.GetString(File.ReadAllBytes(proto)));
                    modules = moduleIds;
                }
                catch (Exception)
                {
                    modules = new List<string>();
                }
            }
        }
        var packages = PackageModuleSets(root);
        List<string> known;
        if (!matched)
        {
            foreach (var mids in packages.Values) modules.AddRange(mids);
            modules = modules.Distinct(StringComparer.Ordinal).OrderBy(m => m, StringComparer.Ordinal).ToList();
            known = packages.Keys.OrderBy(k => k, StringComparer.Ordinal).ToList();
        }
        else
        {
            known = new List<string> { pkg! };
        }
        var allRegistered = OfficialCoreIds(root);
        foreach (var mids in packages.Values) allRegistered.AddRange(mids);
        var allowed = allRegistered.Distinct(StringComparer.Ordinal)
            .OrderBy(m => m, StringComparer.Ordinal).ToList();
        var pipeFiles = new List<string>();
        if (pipeline is not null && pkg is not null)
        {
            var dir = Path.Combine(root, "community", pkg, "pipelines");
            if (Directory.Exists(dir))
            {
                pipeFiles = Directory.GetFiles(dir, pipeline + "*.md")
                    .Select(f => Path.GetRelativePath(root, f).Replace('\\', '/'))
                    .OrderBy(p => p, StringComparer.Ordinal).ToList();
            }
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["requirement"] = req, ["matched"] = matched, ["package"] = pkg, ["pipeline"] = pipeline,
            ["pipeline_files"] = pipeFiles.Cast<object?>().ToList(),
            ["fetch_modules"] = modules.Count > 0
                ? modules.Cast<object?>().ToList()
                : OfficialCoreIds(root).Cast<object?>().ToList(),
            ["allowed_module_ids"] = allowed.Cast<object?>().ToList(),
            ["known_packages"] = known.Cast<object?>().ToList(),
            ["status"] = matched ? "preset" : "custom",
        };
    }

    /// <summary>真源 <c>dossier(...)</c>：漏斗产出 → 需求档案（八字段回填稿）。</summary>
    public static string Dossier(string requirement, Dictionary<string, object?> plan,
                                 IReadOnlyList<string> questions, IReadOnlyList<string> answers)
    {
        var req = requirement.Trim();
        var status = questions.Count > 0
            ? "澄清中（nf assemble 已抛问句，待回填）"
            : plan["matched"] is true ? "preset 预设匹配" : "custom 用户自定义流";
        var known = ObjList(plan.GetValueOrDefault("known_packages")).Select(PyStr).ToList();
        var pipeFiles = ObjList(plan.GetValueOrDefault("pipeline_files")).Select(PyStr).ToList();
        var fetchModules = ObjList(plan.GetValueOrDefault("fetch_modules")).Select(PyStr).ToList();
        var lines = new List<string>
        {
            "需求澄清稿",
            $"1. 一句话需求：{req}",
            "2. 背景与痛点：（待回填——为什么现在做 / 现有哪一环断了）",
            "3. 谁消费（决策人 / 外部方）：（待确认——作者 / agent 用户）",
            $"4. 范围边界（做 / 不做）：{status}",
            plan["matched"] is true
                ? $"   领域判定：{PyStr(plan.GetValueOrDefault("package"))}/{PyStr(plan.GetValueOrDefault("pipeline"))}"
                : "   领域判定：未命中官方预设 → 用户自定义（可借用包："
                  + $"{(known.Count > 0 ? string.Join("、", known) : "—")}）",
            "   取件模块：" + string.Join("、", fetchModules),
            $"5. 验收标准（可测断言）：nf assemble \"{req}\" --check <out.md> 期望 PASS"
            + "（八段骨架 / 编号在装配允许集 / 决策句带引用）",
            "6. 风险与未知：关键词识别有界（未命中 ≠ 不适配，需回填确认）；"
            + "用户自定义件须先落库登记（M91-M99 或 <独占类别>:Mxx 类内段 / 资产 900+ / 新 Pxx 避让层位 id）验收才认；"
            + "外部实证按 STRATEGY 封闭期冻结（NF-FIELD-001 素材缺位）",
            "7. 涉及协议 / 文件：agent_组装指令包_v0.2.md；"
            + $"{(pipeFiles.Count > 0 ? string.Join("、", pipeFiles) : "（待定）")} 管线件；"
            + $"装配计划允许集 {ObjList(plan.GetValueOrDefault("allowed_module_ids")).Count} 模块；"
            + "community/模板制作指令包.md（如需建自定义件）",
            "8. 素材引用：仓库内完整版样本 / 资产键表；外部素材无则如实声明",
        };
        if (questions.Count > 0)
        {
            lines.Add("待澄清（nf assemble 问句）：");
            lines.AddRange(questions.Select(q => "  · " + q));
        }
        if (answers.Count > 0)
        {
            lines.Add("澄清回填（--answer，已并入需求与档案）：");
            lines.AddRange(answers.Select(a => "  · " + a));
        }
        return string.Join("\n", lines) + "\n";
    }

    /// <summary>真源 <c>check(output_md, plan_)</c>：成品机器验收。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Check(
        string outputMd, Dictionary<string, object?> plan)
    {
        var issues = new List<string>();
        var segs = SegRe.Matches(outputMd).Select(m => int.Parse(m.Groups[1].Value)).ToHashSet();
        var missing = Enumerable.Range(0, 8).Where(i => !segs.Contains(i)).ToList();
        if (missing.Count > 0)
            issues.Add("八段骨架缺段：##" + string.Join(", ", missing));
        var allowed = new HashSet<string>(
            ObjList(plan.GetValueOrDefault("allowed_module_ids")).Select(PyStr), StringComparer.Ordinal);
        var bareIds = new HashSet<string>(
            allowed.Select(a => a.Split(':', 2)[^1]), StringComparer.Ordinal);
        var mentioned = new HashSet<string>(StringComparer.Ordinal);
        int? curSeg = null;
        var inCode = false;
        foreach (var line in KnowledgeSig.SplitLines(outputMd))
        {
            var s = line.Trim();
            if (s.StartsWith("```", StringComparison.Ordinal))
            {
                inCode = !inCode;
                continue;
            }
            if (inCode) continue;
            var seg = SegRe.Match(line);
            if (seg.Success)
            {
                curSeg = int.Parse(seg.Groups[1].Value);
                continue;
            }
            foreach (Match tok in ModuleRe.Matches(line))
            {
                var text = tok.Value;
                mentioned.Add(text);
                if (allowed.Contains(text) || bareIds.Contains(text.Split(':', 2)[^1])) continue;
                if (Explanations.Any(k => line.Contains(k, StringComparison.Ordinal))) continue;
                issues.Add($"编造/越界编号：{text}（全库允许集外，且非残留/不命中说明）");
            }
            if (curSeg is null || curSeg > 2 || s.StartsWith('-') || s.StartsWith('*') || s.StartsWith('|'))
                continue;
            foreach (var raw in Regex.Split(line, "[。！？；\\n]+"))
            {
                var clause = raw.Trim();
                if (clause.Length == 0) continue;
                if (DecisionRe.IsMatch(clause) && !CitationRe.IsMatch(clause) && !ModuleRe.IsMatch(clause))
                    issues.Add("无引用决策句：" + PyScalar.PySlice(clause, 60));
            }
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["segments"] = (long)segs.Count, ["modules_mentioned"] = (long)mentioned.Count,
            ["allowed"] = (long)allowed.Count,
        });
    }

    private static int IndentOf(string line)
    {
        var n = 0;
        foreach (var ch in line)
        {
            if (ch == ' ') n++;
            else if (ch == '\t') n += 8;
            else break;
        }
        return n;
    }

    private static List<object?> ObjList(object? value) => value as List<object?> ?? new List<object?>();

    private static string PyStr(object? value) => value switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        _ => Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture) ?? "None",
    };
}
