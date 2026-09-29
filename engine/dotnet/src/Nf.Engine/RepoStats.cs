using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/repo_stats.py</c>：出口自动化 · 自述数字实算真源（check38 子扫描 1）。
///
/// 口径纪律：README / README.en / llms.txt 里的每个数字都必须能回指唯一产物并实算；
/// 文档只承载 marker 包围的生成区，禁止手改。取不到数字 → 记 issue，**不静默填 0**。
/// </summary>
public static class RepoStats
{
    public const string StatsRel = "protocol/repo_stats.json";
    public const string Begin = "<!-- nf:stats:begin -->";
    public const string End = "<!-- nf:stats:end -->";

    private static readonly Regex CheckRe = new(@"^check[0-9]+\(\)", RegexOptions.Multiline);
    private static readonly Regex VersionRe = new(@"^# 版本\s*:\s*v([0-9][0-9.]*)", RegexOptions.Multiline);
    private static readonly Regex ExpectedChecksRe = new(@"^\s*EXPECTED_CHECKS\s*=\s*([0-9]+)", RegexOptions.Multiline);
    private static readonly Regex ExpectedPassRe = new(@"^\s*EXPECTED_PASS\s*=\s*([0-9]+)", RegexOptions.Multiline);
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>实算全部自述数字（缺源即记 issue）。</summary>
    public static (Dictionary<string, object?> Stats, List<string> Issues) Compute(string root)
    {
        var issues = new List<string>();
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal);
        var sep = Path.DirectorySeparatorChar;

        var reg = ReadJson(Path.Combine(root, "desktop", "src", "core", "registry.json"));
        if (reg is null)
        {
            issues.Add("取不到 registry.json（官方核心模块/登记包口径缺失）");
            reg = new Dictionary<string, object?>(StringComparer.Ordinal);
        }
        stats["core_modules"] = (long)ListLen(reg, "modules");
        stats["registered_packs"] = (long)ListLen(reg, "protocols");

        var pipeDir = Path.Combine(root, "03_管线库");
        var pipes = Directory.Exists(pipeDir)
            ? Directory.GetFiles(pipeDir, "P*.md").Select(f => Path.GetFileName(f)[..Math.Min(3, Path.GetFileName(f).Length)])
                .OrderBy(x => x, StringComparer.Ordinal).ToList()
            : new List<string>();
        stats["core_pipelines"] = pipes.Cast<object?>().ToList();

        var community = Path.Combine(root, "community");
        var packDirs = Directory.Exists(community)
            ? Directory.GetDirectories(community)
                .Where(d => File.Exists(Path.Combine(d, "protocol.yaml")))
                .Select(d => Path.GetFileName(d)).OrderBy(x => x, StringComparer.Ordinal).ToList()
            : new List<string>();
        stats["pack_dirs"] = (long)packDirs.Count;
        if (packDirs.Count > 0 && packDirs.Count != ListLen(reg, "protocols"))
            issues.Add($"盘上包目录 {packDirs.Count} ≠ registry 登记 {ListLen(reg, "protocols")}" +
                       "（登记三要件与盘上实况不一致）");

        stats["pack_assets"] = (long)GlobCount(Path.Combine(community, "*"), Path.Combine("assets", "*.md"));
        stats["concept_graphs"] = (long)GlobCount(Path.Combine(community, "*"), Path.Combine("assets", "CONCEPT_GRAPH.md"));

        var catalog = ReadJson(Path.Combine(root, "protocol", "standards_catalog.json"))
                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var coverage = Val(catalog, "coverage") as Dictionary<string, object?>
                       ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var key in new[] { "standards", "reachable", "unreachable", "bodies", "depends_edges", "by_layer" })
        {
            if (!coverage.ContainsKey(key)) issues.Add($"标准目录 coverage 缺 {key}（口径不完整）");
        }
        stats["standards_total"] = Num(coverage, "standards");
        stats["standards_reachable"] = Num(coverage, "reachable");
        stats["standards_unreachable"] = Num(coverage, "unreachable");
        stats["standards_bodies"] = Num(coverage, "bodies");
        stats["standards_edges"] = Num(coverage, "depends_edges");
        stats["standards_by_layer"] = Val(coverage, "by_layer") as Dictionary<string, object?>
                                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);

        var binding = ReadJson(Path.Combine(root, "protocol", "standards_binding.json"))
                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        stats["standard_bindings"] = Num(binding, "bindings_total");

        var manifest = ReadJson(Path.Combine(root, "protocol", "domain_packs.json"))
                       ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        stats["domain_packs"] = Num(manifest, "count");
        stats["subdivisions_total"] = Num(manifest, "subdivisions_total");

        var libraryDir = Path.Combine(root, "library");
        var libraryItems = Directory.Exists(libraryDir)
            ? Directory.GetFiles(libraryDir, "*.md").Select(Path.GetFileName)
                .Where(f => f is not ("INDEX.md" or "ALIAS.md")).Count()
            : 0;
        stats["library_items"] = (long)libraryItems;

        var verifyText = "";
        var verifyPath = Path.Combine(root, "verify.sh");
        if (File.Exists(verifyPath))
        {
            verifyText = StrictUtf8.GetString(File.ReadAllBytes(verifyPath));
        }
        else
        {
            issues.Add("取不到 verify.sh（质量凭证口径缺失）");
        }
        var checkCount = CheckRe.Matches(verifyText).Count;
        var versionMatch = VersionRe.Match(verifyText);
        var version = versionMatch.Success ? versionMatch.Groups[1].Value : "";
        stats["verify_checks"] = (long)checkCount;
        stats["verify_version"] = version;
        if (version.Length == 0) issues.Add("verify.sh 头部缺「# 版本 : vX」版本行");
        if (checkCount < 1) issues.Add("verify.sh 未扫到任何 checkN() 定义");

        // 质量基线真源：quality_baseline.EXPECTED_*（Python 侧 import；此处按同源常量解析）
        var baselinePath = Path.Combine(root, "desktop", "src", "core", "quality_baseline.py");
        if (File.Exists(baselinePath))
        {
            var baselineText = StrictUtf8.GetString(File.ReadAllBytes(baselinePath));
            var mChecks = ExpectedChecksRe.Match(baselineText);
            var mPass = ExpectedPassRe.Match(baselineText);
            stats["baseline_checks"] = mChecks.Success ? long.Parse(mChecks.Groups[1].Value, CultureInfo.InvariantCulture) : (long)checkCount;
            stats["baseline_pass"] = mPass.Success ? long.Parse(mPass.Groups[1].Value, CultureInfo.InvariantCulture) : 0L;
            if (!mChecks.Success)
                issues.Add("取不到 quality_baseline.EXPECTED_*（基线句无法生成）");
        }
        else
        {
            stats["baseline_checks"] = (long)checkCount;
            stats["baseline_pass"] = 0L;
            issues.Add("取不到 quality_baseline.EXPECTED_*（基线句无法生成）");
        }
        if (Convert.ToInt64(stats["baseline_checks"]) != checkCount)
            issues.Add($"基线 check 数 {stats["baseline_checks"]} ≠ verify.sh 实扫 {checkCount}" +
                       "（同步 quality_baseline.EXPECTED_CHECKS）");

        stats["schema"] = "nf-repo-stats/1";
        return (stats, issues);
    }

    /// <summary>三个入口文件的 marker 区文本（键 = 仓库相对路径）。</summary>
    public static Dictionary<string, string> Render(Dictionary<string, object?> stats)
        => new(StringComparer.Ordinal)
        {
            ["README.md"] = Zh(stats),
            ["README.en.md"] = En(stats),
            ["llms.txt"] = Llms(stats),
        };

    /// <summary>校验：生成区 == 实算 且在盘 repo_stats.json == 实算。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Check(string root)
    {
        var (stats, issues) = Compute(root);
        foreach (var (rel, block) in Render(stats))
        {
            var path = Path.Combine(root, rel);
            if (!File.Exists(path))
            {
                issues.Add($"缺入口文件 {rel}");
                continue;
            }
            var text = StrictUtf8.GetString(File.ReadAllBytes(path));
            var (replaced, ok) = ReplaceBlock(text, block);
            if (!ok) issues.Add($"{rel} 缺 marker 区");
            else if (replaced != text) issues.Add($"{rel} 的生成区与实算不一致（跑 `nf stats --write` 重写）");
        }
        var recorded = ReadJson(Path.Combine(root, StatsRel.Replace('/', Path.DirectorySeparatorChar)));
        if (!PyEquals(recorded, stats))
            issues.Add($"{StatsRel} 与实算不一致（跑 `nf stats --write` 重写）");
        return (issues, stats);
    }

    // ------------------------------------------------------------------ 三个生成块（逐字节）

    private static string Zh(Dictionary<string, object?> stats)
    {
        var pipes = string.Join(" / ", Pipelines(stats));
        if (pipes.Length == 0) pipes = "—";
        var layers = (Val(stats, "standards_by_layer") as Dictionary<string, object?>) ?? new(StringComparer.Ordinal);
        var layerTxt = string.Join(" · ", layers.Keys.OrderBy(k => k, StringComparer.Ordinal)
            .Select(k => $"{k} {PyScalarText(layers[k])}"));
        if (layerTxt.Length == 0) layerTxt = "—";
        return string.Join("\n", new[]
        {
            Begin,
            $"**官方核心**：{Num(stats, "core_modules")} 模块 · {Pipelines(stats).Count} 管线（{pipes}） · 核心协议件 01–07",
            $"**社区规模**：{Num(stats, "registered_packs")} 登记包 · {Num(stats, "pack_assets")} 资产档 · " +
            $"{Num(stats, "concept_graphs")} 概念图 · {Num(stats, "domain_packs")} 域包/{Num(stats, "subdivisions_total")} 细分 · " +
            $"标准目录 {Num(stats, "standards_total")} 条（可达 {Num(stats, "standards_reachable")} / 不可达 {Num(stats, "standards_unreachable")} · " +
            $"机构 {Num(stats, "standards_bodies")} · {Num(stats, "standards_edges")} 条依赖边） · 标准绑定 {Num(stats, "standard_bindings")} 条",
            $"**质量凭证**：verify v{PyScalarText(Val(stats, "verify_version"))} · check1-{Num(stats, "baseline_checks")} · " +
            $"PASS={Num(stats, "baseline_pass")}（`bash verify.sh` 单入口；期望基线取自 `quality_baseline.EXPECTED_*`） · 馆藏 {Num(stats, "library_items")} 件",
            "",
            $"分层：{layerTxt} （按标准目录 layer）",
            "",
            "> 本区由 `python scripts/nf.py stats --write` 生成，禁止手改；口径与实算真源见 `protocol/repo_stats.json`。",
            End,
        });
    }

    private static string En(Dictionary<string, object?> stats)
    {
        var pipes = Pipelines(stats);
        var pipeTxt = pipes.Count > 0 ? string.Join(" / ", pipes) : "—";
        return string.Join("\n", new[]
        {
            Begin,
            $"**Official core**: {Num(stats, "core_modules")} modules · {pipes.Count} pipelines ({pipeTxt}) · protocol files 01-07",
            $"**Community scale**: {Num(stats, "registered_packs")} registered packs · {Num(stats, "pack_assets")} asset files · " +
            $"{Num(stats, "concept_graphs")} concept graphs · {Num(stats, "domain_packs")} domain packs / {Num(stats, "subdivisions_total")} subdivisions · " +
            $"standards catalog {Num(stats, "standards_total")} (reachable {Num(stats, "standards_reachable")} / unreachable {Num(stats, "standards_unreachable")} · " +
            $"{Num(stats, "standards_bodies")} bodies · {Num(stats, "standards_edges")} dependency edges) · standard bindings {Num(stats, "standard_bindings")}",
            $"**Quality evidence**: verify v{PyScalarText(Val(stats, "verify_version"))} · check1-{Num(stats, "baseline_checks")} · " +
            $"PASS={Num(stats, "baseline_pass")} (`bash verify.sh`; expectations from `quality_baseline.EXPECTED_*`) · library {Num(stats, "library_items")} items",
            "",
            "> Generated by `python scripts/nf.py stats --write`. Do not edit by hand; sources in `protocol/repo_stats.json`.",
            End,
        });
    }

    private static string Llms(Dictionary<string, object?> stats)
        => string.Join("\n", new[]
        {
            Begin,
            $"- 质量凭证（可静态实算）：verify v{PyScalarText(Val(stats, "verify_version"))} · check1-{Num(stats, "baseline_checks")} · " +
            $"PASS={Num(stats, "baseline_pass")}（`bash verify.sh` 单入口；期望基线取自 `quality_baseline.EXPECTED_*`，本行由生成器写入）。",
            $"- 规模（实算真源 `protocol/repo_stats.json`）：{Num(stats, "registered_packs")} 登记包 · {Num(stats, "pack_assets")} 资产档 · " +
            $"{Num(stats, "concept_graphs")} 概念图 · 标准目录 {Num(stats, "standards_total")} 条（可达 {Num(stats, "standards_reachable")}） · " +
            $"标准绑定 {Num(stats, "standard_bindings")} 条 · 馆藏 {Num(stats, "library_items")} 件。",
            "- 标准目录 GEO 出口（可引用）：`docs/standards/index.md` · 机读 `protocol/geo_export.json`。",
            End,
        });

    // ------------------------------------------------------------------ 工具

    private static (string Text, bool Ok) ReplaceBlock(string text, string block)
    {
        var i = text.IndexOf(Begin, StringComparison.Ordinal);
        var j = text.IndexOf(End, StringComparison.Ordinal);
        if (i < 0 || j < 0 || j < i) return (text, false);
        return (text[..i] + block + text[(j + End.Length)..], true);
    }

    private static List<string> Pipelines(Dictionary<string, object?> stats)
        => (Val(stats, "core_pipelines") as List<object?>)?.Select(PyScalarText).ToList() ?? new List<string>();

    private static object? Val(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var v) ? v : null;

    private static int ListLen(Dictionary<string, object?> map, string key)
        => Val(map, key) is List<object?> list ? list.Count : 0;

    private static long Num(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var v) && v is not null
            ? Convert.ToInt64(v, CultureInfo.InvariantCulture) : 0L;

    private static string PyScalarText(object? v) => v switch
    {
        null => "None",
        string s => s,
        long l => l.ToString(CultureInfo.InvariantCulture),
        int i => i.ToString(CultureInfo.InvariantCulture),
        _ => PyScalar.PyRepr(v),
    };

    private static int GlobCount(string dirPattern, string subPattern)
    {
        var parent = Path.GetDirectoryName(dirPattern)!;
        if (!Directory.Exists(parent)) return 0;
        var count = 0;
        foreach (var dir in Directory.GetDirectories(parent))
        {
            var sub = Path.GetDirectoryName(subPattern);
            var file = Path.GetFileName(subPattern);
            var target = sub is { Length: > 0 } ? Path.Combine(dir, sub) : dir;
            if (Directory.Exists(target)) count += Directory.GetFiles(target, file).Length;
        }
        return count;
    }

    private static Dictionary<string, object?>? ReadJson(string path)
    {
        if (!File.Exists(path)) return null;
        try
        {
            using var doc = JsonIo.ReadFile(path);
            return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>;
        }
        catch (Exception exc) when (exc is System.Text.Json.JsonException or IOException)
        {
            return null;   // Python：_read_json 吞掉一切异常 → None
        }
    }

    /// <summary>Python <c>==</c> 的深比较（dict/list/数值等价；None 与缺键不等价）。</summary>
    private static bool PyEquals(object? a, object? b)
    {
        if (a is null || b is null) return a is null && b is null;
        if (a is long la && b is long lb) return la == lb;
        if (a is double da && b is double db) return da == db;
        if (a is long lc && b is double dc) return lc == dc;
        if (a is double dd && b is long ld) return dd == ld;
        if (a is string sa && b is string sb) return sa == sb;
        if (a is bool ba && b is bool bb) return ba == bb;
        if (a is Dictionary<string, object?> ma && b is Dictionary<string, object?> mb)
        {
            if (ma.Count != mb.Count) return false;
            foreach (var (k, v) in ma)
            {
                if (!mb.TryGetValue(k, out var other) || !PyEquals(v, other)) return false;
            }
            return true;
        }
        if (a is List<object?> listA && b is List<object?> listB)
        {
            if (listA.Count != listB.Count) return false;
            for (var i = 0; i < listA.Count; i++)
            {
                if (!PyEquals(listA[i], listB[i])) return false;
            }
            return true;
        }
        return a.Equals(b);
    }
}
