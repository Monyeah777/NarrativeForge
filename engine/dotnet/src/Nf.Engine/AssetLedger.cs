using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/asset_ledger.py</c> 的**只读面**：台账闭合校验（与 verify.sh check23 同语义）·
/// 货架单层不变量 · 库存盘点 · 货架浏览。
///
/// 台账 = 资产根目录下的 <c>provenance.json</c>（溯源键表，机读唯一真相）；每个托管资产文件头
/// 写一行 <c>nf-asset</c> 机器可读头，与台账**双源一致**。写面（add / rm / deprecate / restore / baseline
/// 重签）不属只读门，本件不提供。
/// </summary>
public static class AssetLedger
{
    public const string LedgerFile = "provenance.json";
    public const string HeaderMark = "nf-asset";
    public const string LedgerSchemaVersion = "1";

    public static readonly string[] ValidStatus = { "active", "deprecated", "retired" };
    public static readonly string[] ValidTier = { "official", "community", "experimental" };

    /// <summary>资产货架目录（**单层不变量**：三面扫描不递归，子目录会静默丢口径）。</summary>
    private static readonly string[][] ShelfGlobs =
    {
        new[] { "community", "*", "assets" },
        new[] { "05_资产库", "用户自定义" },
    };

    private static readonly Regex HeaderRe = new(
        "<!--\\s*nf-asset:\\s*key=\"([^\"]+)\"\\s+version=\"([^\"]+)\"\\s+status=\"([^\"]+)\"\\s*-->",
        RegexOptions.CultureInvariant);

    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>台账操作拒绝原因（CLI 层据此友好提示，退出码 1──与真源 <c>AssetLedgerError</c> 同源）。</summary>
    public sealed class LedgerError : Exception
    {
        public LedgerError(string message) : base(message) { }
    }

    /// <summary>解析 nf-asset 头：无头返回 null，有头但不可解析**抛错**（防半截头混过）。</summary>
    public static Dictionary<string, string>? ParseHeader(string text)
    {
        if (!text.Contains(HeaderMark, StringComparison.Ordinal)) return null;
        var m = HeaderRe.Match(text);
        if (!m.Success) throw new LedgerError($"发现 {HeaderMark} 头但格式不可解析（应 key/version/status 齐备）");
        return new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["key"] = m.Groups[1].Value,
            ["version"] = m.Groups[2].Value,
            ["status"] = m.Groups[3].Value,
        };
    }

    /// <summary>读取台账；缺失或结构非法抛错（防静默覆盖/误写）。</summary>
    public static Dictionary<string, object?> LoadLedger(string ledgerPath)
    {
        if (!File.Exists(ledgerPath))
            throw new LedgerError($"台账不存在：{ledgerPath}（先 nf asset add 建档）");
        Dictionary<string, object?> data;
        try
        {
            using var doc = JsonIo.ReadFile(ledgerPath);
            data = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        }
        catch (System.Text.Json.JsonException exc)
        {
            throw new LedgerError($"台账结构非法：{ledgerPath}（缺 assets[]）：{exc.Message}");
        }
        if (data.GetValueOrDefault("assets") is not List<object?>)
            throw new LedgerError($"台账结构非法：{ledgerPath}（缺 assets[]）");
        if (data.GetValueOrDefault("schema_version") is not string schemaVersion
            || schemaVersion != LedgerSchemaVersion)
        {
            throw new LedgerError($"台账 schema_version=" +
                                  $"{PyScalar.PyRepr(data.GetValueOrDefault("schema_version"))} 不识别（当前 " +
                                  $"{LedgerSchemaVersion}）：{ledgerPath}");
        }
        return data;
    }

    /// <summary>台账目录下候选资产 md（排除 README*——包索引手册非内容资产，对齐 check7 口径）。</summary>
    private static List<string> IterMdCandidates(string ledgerDir)
    {
        var output = new List<string>();
        foreach (var (dir, _) in Walk(ledgerDir))
        {
            foreach (var fn in Directory.GetFiles(dir).Select(Path.GetFileName).Where(f => f is not null)
                         .Select(f => f!).OrderBy(f => f, StringComparer.Ordinal))
            {
                if (fn.ToLowerInvariant().StartsWith("readme", StringComparison.Ordinal)) continue;
                if (fn.EndsWith(".md", StringComparison.Ordinal)) output.Add(Path.Combine(dir, fn));
            }
        }
        return output;
    }

    /// <summary>复刻 <c>os.walk</c>：自顶向下、过滤 .git/.gitee/__pycache__（目录序保持文件系统序）。</summary>
    private static IEnumerable<(string Dir, List<string> Files)> Walk(string root)
    {
        var stack = new Queue<string>();
        stack.Enqueue(root);
        while (stack.Count > 0)
        {
            var dir = stack.Dequeue();
            List<string> files;
            string[] subdirs;
            try
            {
                files = Directory.GetFiles(dir).ToList();
                subdirs = Directory.GetDirectories(dir);
            }
            catch (Exception exc) when (exc is IOException or UnauthorizedAccessException)
            {
                continue;
            }
            foreach (var sub in subdirs)
            {
                var name = Path.GetFileName(sub);
                if (name is ".git" or ".gitee" or "__pycache__") continue;
                stack.Enqueue(sub);
            }
            yield return (dir, files);
        }
    }

    /// <summary>单台账闭合校验。stats：assets（在册条目数）/ untracked（目录下无头 md）/ orphans（孤儿文件头）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) VerifyLedgerDir(
        string ledgerDir, string? ledgerPath = null)
    {
        var lp = ledgerPath ?? Path.Combine(ledgerDir, LedgerFile);
        var issues = new List<string>();
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["assets"] = 0L, ["untracked"] = 0L, ["orphans"] = 0L,
        };
        if (!File.Exists(lp)) return (issues, stats);
        Dictionary<string, object?> ledger;
        try
        {
            ledger = LoadLedger(lp);
        }
        catch (LedgerError exc)
        {
            return (new List<string> { exc.Message }, stats);
        }
        var entries = (ledger.GetValueOrDefault("assets") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        stats["assets"] = (long)entries.Count;
        var seenKeys = new HashSet<string>(StringComparer.Ordinal);
        var seenFiles = new HashSet<string>(StringComparer.Ordinal);
        foreach (var e in entries)
        {
            var key = PyText(e.GetValueOrDefault("key"));
            var frel = PyText(e.GetValueOrDefault("file")).Replace('\\', '/');
            if (key.Length == 0) issues.Add($"[{lp}] 条目缺 key");
            if (!seenKeys.Add(key)) issues.Add($"[{lp}] 键重复（键无孤儿前提：键唯一）: {key}");
            if (frel.Length == 0 || !seenFiles.Add(frel))
            {
                issues.Add($"[{lp}] 文件重复/为空: {PyScalar.PyRepr(e.GetValueOrDefault("file") ?? "")}");
                continue;
            }
            var full = Path.Combine(ledgerDir, frel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(full))
            {
                issues.Add($"[{lp}] 在册文件缺失（可发现性断裂）: {frel}");
                continue;
            }
            var text = StrictUtf8.GetString(File.ReadAllBytes(full));
            Dictionary<string, string>? header;
            try
            {
                header = ParseHeader(text);
            }
            catch (LedgerError exc)
            {
                issues.Add($"[{lp}] {exc.Message}");
                continue;
            }
            if (header is null)
            {
                issues.Add($"[{lp}] 台账条目缺文件头（双源不一致）: {frel}");
            }
            else if (header["key"] != key || header["status"] != PyText(e.GetValueOrDefault("status")))
            {
                issues.Add($"[{lp}] 文件头与台账不一致（台账 key={key} status=" +
                           $"{PyStrRaw(e.GetValueOrDefault("status"))} / 头=" +
                           $"{PyScalar.PyRepr(header.ToDictionary(kv => kv.Key, kv => (object?)kv.Value, StringComparer.Ordinal))}）" +
                           $": {frel}");
            }
            if (PyText(e.GetValueOrDefault("source")).Trim().Length == 0)
                issues.Add($"[{lp}] 条目缺 source（不可溯源）: {key}");
            if (PyText(e.GetValueOrDefault("version")).Trim().Length == 0)
                issues.Add($"[{lp}] 条目缺 version（版本位必填）: {key}");
            var status = e.GetValueOrDefault("status") as string;
            if (status is null || !ValidStatus.Contains(status))
                issues.Add($"[{lp}] status 非法: {PyStrRaw(e.GetValueOrDefault("status"))}");
        }
        // 反向闭合：目录内带头 md 的键必须 ∈ 台账（键无孤儿）
        foreach (var cand in IterMdCandidates(ledgerDir))
        {
            var rel = Path.GetRelativePath(ledgerDir, cand).Replace('\\', '/');
            if (seenFiles.Contains(rel)) continue;
            var text = StrictUtf8.GetString(File.ReadAllBytes(cand));
            if (!text.Contains(HeaderMark, StringComparison.Ordinal))
            {
                stats["untracked"] = Convert.ToInt64(stats["untracked"]) + 1;
                continue;
            }
            Dictionary<string, string>? header;
            try
            {
                header = ParseHeader(text);
            }
            catch (LedgerError exc)
            {
                issues.Add($"[{lp}] {exc.Message}");
                continue;
            }
            stats["orphans"] = Convert.ToInt64(stats["orphans"]) + 1;
            issues.Add($"[{lp}] 孤儿文件头（键不在台账）: {rel}（key={header!["key"]}）——" +
                       "nf asset rm 后需手动清理旧头");
        }
        return (issues, stats);
    }

    /// <summary>资产货架**单层不变量**：货架目录下不得含子目录。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) VerifyShelfShape(string root)
    {
        var issues = new List<string>();
        long shelvesSeen = 0;
        foreach (var glob in ShelfGlobs)
        {
            // 逐段展开（含一个 `*` 层）：`community/*/assets` → 遍历 community 下每个子目录的 assets；
            // `05_资产库/用户自定义` → 单一路径。**不许**把 `*` 当字面目录名（那会让整条检查静默失灵）。
            var starAt = Array.IndexOf(glob, "*");
            var shelves = new List<string>();
            if (starAt >= 0)
            {
                var prefix = Path.Combine(root, Path.Combine(glob.Take(starAt).ToArray()));
                if (Directory.Exists(prefix))
                {
                    foreach (var mid in Directory.GetDirectories(prefix).OrderBy(d => d, StringComparer.Ordinal))
                    {
                        var tail = glob.Skip(starAt + 1).ToArray();
                        shelves.Add(tail.Length == 0
                            ? mid
                            : Path.Combine(new[] { mid }.Concat(tail).ToArray()));
                    }
                }
            }
            else
            {
                shelves.Add(Path.Combine(new[] { root }.Concat(glob).ToArray()));
            }
            foreach (var shelf in shelves)
            {
                if (!Directory.Exists(shelf)) continue;
                shelvesSeen++;
                var rel = Path.GetRelativePath(root, shelf).Replace('\\', '/');
                var subs = Directory.GetDirectories(shelf).Select(Path.GetFileName).Where(n => n is not null)
                    .Select(n => n!).OrderBy(n => n, StringComparer.Ordinal).ToList();
                if (subs.Count > 0)
                {
                    issues.Add($"{rel} 资产货架含子目录 {string.Join("、", subs)}（货架为单层：密度 / 键表投影 / " +
                               "行数基线三面不递归，子目录会静默丢口径；修复指引：资产平铺为 .md，分组用键表表达）");
                }
            }
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal) { ["shelves"] = shelvesSeen });
    }

    /// <summary>仓库级扫描：找出全部 provenance.json 台账目录并逐册校验；聚合统计。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) VerifyRoot(string root)
    {
        var issues = new List<string>();
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["ledgers"] = 0L, ["assets"] = 0L, ["untracked"] = 0L, ["orphans"] = 0L, ["shelves"] = 0L,
        };
        var (shapeIssues, shapeStats) = VerifyShelfShape(root);
        issues.AddRange(shapeIssues);
        stats["shelves"] = shapeStats["shelves"];
        foreach (var (dir, files) in Walk(root))
        {
            if (!files.Any(f => Path.GetFileName(f) == LedgerFile)) continue;
            var (dirIssues, dirStats) = VerifyLedgerDir(dir, Path.Combine(dir, LedgerFile));
            issues.AddRange(dirIssues);
            stats["ledgers"] = Convert.ToInt64(stats["ledgers"]) + 1;
            foreach (var key in new[] { "assets", "untracked", "orphans" })
                stats[key] = Convert.ToInt64(stats[key]) + Convert.ToInt64(dirStats.GetValueOrDefault(key) ?? 0L);
        }
        return (issues, stats);
    }

    /// <summary>浏览：逐台账展开为行（台账级 package/tier 与条目字段合并），按目录+文件+键排序。</summary>
    public static List<Dictionary<string, object?>> IterAssets(string root)
    {
        var rows = new List<Dictionary<string, object?>>();
        foreach (var (dir, files) in Walk(root))
        {
            if (!files.Any(f => Path.GetFileName(f) == LedgerFile)) continue;
            Dictionary<string, object?> ledger;
            try
            {
                ledger = LoadLedger(Path.Combine(dir, LedgerFile));
            }
            catch (LedgerError)
            {
                continue;
            }
            var relDir = Path.GetRelativePath(root, dir).Replace('\\', '/');
            foreach (var e in (ledger.GetValueOrDefault("assets") as List<object?> ?? new List<object?>())
                         .OfType<Dictionary<string, object?>>())
            {
                var row = e.ToDictionary(kv => kv.Key, kv => kv.Value, StringComparer.Ordinal);
                row["dir"] = relDir == "." ? "(root)" : relDir;
                row["package"] = ledger.GetValueOrDefault("package") ?? "";
                row["tier"] = ledger.GetValueOrDefault("tier") ?? "";
                rows.Add(row);
            }
        }
        return rows.OrderBy(r => PyText(r.GetValueOrDefault("dir")), StringComparer.Ordinal)
            .ThenBy(r => PyText(r.GetValueOrDefault("file")), StringComparer.Ordinal)
            .ThenBy(r => PyText(r.GetValueOrDefault("key")), StringComparer.Ordinal)
            .ToList();
    }

    /// <summary>ls 过滤器（pkg = 台账 package 字段；tier/status = 台账级/条目级匹配）。</summary>
    public static List<Dictionary<string, object?>> FilterRows(List<Dictionary<string, object?>> rows,
        string pkg = "", string tier = "", string status = "")
    {
        if (tier.Length > 0 && !ValidTier.Contains(tier)) throw new LedgerError($"tier 过滤器非法：{tier}");
        if (status.Length > 0 && !ValidStatus.Contains(status)) throw new LedgerError($"status 过滤器非法：{status}");
        return rows.Where(r =>
                (pkg.Length == 0 || PyText(r.GetValueOrDefault("package")) == pkg)
                && (tier.Length == 0 || PyText(r.GetValueOrDefault("tier")) == tier)
                && (status.Length == 0 || PyText(r.GetValueOrDefault("status")) == status))
            .ToList();
    }

    /// <summary>库存盘点：台账摘要行（目录/package/tier/在册数/未托管数/问题数），按目录排序。</summary>
    public static List<Dictionary<string, object?>> InventoryRoot(string root)
    {
        var rows = new List<Dictionary<string, object?>>();
        foreach (var (dir, files) in Walk(root))
        {
            if (!files.Any(f => Path.GetFileName(f) == LedgerFile)) continue;
            var lp = Path.Combine(dir, LedgerFile);
            var rel = Path.GetRelativePath(root, dir).Replace('\\', '/');
            try
            {
                var ledger = LoadLedger(lp);
                var (_, dirStats) = VerifyLedgerDir(dir, lp);
                rows.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["dir"] = rel == "." ? "(root)" : rel,
                    ["package"] = ledger.GetValueOrDefault("package") ?? "",
                    ["tier"] = ledger.GetValueOrDefault("tier") ?? "",
                    ["assets"] = (long)((ledger.GetValueOrDefault("assets") as List<object?>)?.Count ?? 0),
                    ["untracked"] = dirStats.GetValueOrDefault("untracked") ?? 0L,
                    ["orphans"] = dirStats.GetValueOrDefault("orphans") ?? 0L,
                });
            }
            catch (LedgerError exc)
            {
                rows.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["dir"] = rel, ["package"] = "", ["tier"] = "", ["assets"] = -1L,
                    ["untracked"] = 0L, ["orphans"] = 0L, ["error"] = exc.Message,
                });
            }
        }
        return rows.OrderBy(r => PyText(r.GetValueOrDefault("dir")), StringComparer.Ordinal).ToList();
    }

    private static string PyText(object? v) => v switch
    {
        null => "",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        _ => PyScalar.PyRepr(v),
    };

    /// <summary>Python <c>"%s"</c> 语义：None → <c>None</c>、字符串原样、容器走 repr（用于**文案**，不是比较）。</summary>
    private static string PyStrRaw(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        _ => PyScalar.PyRepr(v),
    };
}
