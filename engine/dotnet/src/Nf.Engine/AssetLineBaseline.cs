using System.Text;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/asset_line_baseline.py</c> 的**只读校验面**：社区资产行数/外形基线
/// （<c>protocol/asset_line_baseline.json</c>，机制对齐 <c>module_signature</c> 的"外形冻结"）。
///
/// 判据四条：① 基线件在场且 <c>schema</c> 匹配；② 在盘的每个 <c>community/*/assets</c> 包必须在基线在册；
/// ③ 在册包的 <c>files</c> / <c>lines</c> / <c>digest</c>（逐文件行数映射的 SHA-256）须与实时扫描一致；
/// ④ 目录不在场的包按 <b>WARN 跳过</b>（对齐 verify 段 B 的部署语义）。
///
/// <c>--write</c>（重签基线）是写面，不属只读门；本件**不提供**。
/// 真源在"基线是 JSON 但根不是对象"时会在 <c>.get</c> 上崩（AttributeError）——本件收敛为受控错误，登记为非判据分岐。
/// </summary>
public static class AssetLineBaseline
{
    public const string Schema = "nf-asset-line-baseline/1";
    public const string BaselineRel = "protocol/asset_line_baseline.json";

    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);
    private const string ReadmeName = "README.md";

    /// <summary>实时扫描：<c>community/*/assets</c> 各包的文件数 / 行数 / 外形摘要（逐文件行数映射）。</summary>
    public static List<Dictionary<string, object?>> ScanPackages(string root)
    {
        var packages = new List<Dictionary<string, object?>>();
        var community = Path.Combine(root, "community");
        if (!Directory.Exists(community)) return packages;
        foreach (var pkgDir in Directory.GetDirectories(community).OrderBy(d => d, StringComparer.Ordinal))
        {
            var assetsDir = Path.Combine(pkgDir, "assets");
            if (!Directory.Exists(assetsDir)) continue;
            var perFile = new List<object?>();
            foreach (var full in Directory.GetFiles(assetsDir).OrderBy(f => f, StringComparer.Ordinal))
            {
                var name = Path.GetFileName(full);
                if (!name.EndsWith(".md", AssetShelf.NameComparison)) continue;
                if (name == ReadmeName) continue;
                var lines = AssetShelf.TryReadText(full, out var text)
                    ? KnowledgeSig.SplitLines(text).Count
                    : 0;
                perFile.Add(new List<object?> { name, (long)lines });
            }
            var payload = PythonJson.Compact(perFile);
            var digest = Convert.ToHexString(
                System.Security.Cryptography.SHA256.HashData(Encoding.UTF8.GetBytes(payload))).ToLowerInvariant();
            var relDir = Path.GetRelativePath(root, assetsDir).Replace('\\', '/');
            packages.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["package"] = Path.GetFileName(pkgDir),
                ["dir"] = relDir,
                ["files"] = (long)perFile.Count,
                ["lines"] = perFile.Sum(e => ((List<object?>)e!)[1] is long l ? l : 0),
                ["digest"] = digest,
            });
        }
        return packages;
    }

    /// <summary>校验（与 <c>nf asset baseline</c> / verify check8 同源）。</summary>
    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Verify(string root)
    {
        var doc = Load(root);
        var empty = new Dictionary<string, object?>(StringComparer.Ordinal);
        if (doc.Count == 0)
            return (new List<string> { $"缺资产行数基线 {BaselineRel}（修复指引：nf asset baseline --write）" },
                new List<string>(), empty);

        var rawSchema = doc.GetValueOrDefault("schema");
        if (PyStrOrEmpty(rawSchema) != Schema)
            return (new List<string>
                {
                    $"资产行数基线 schema 不匹配（期望 {Schema}）：{PyScalar.PyRepr(rawSchema)}",
                }, new List<string>(), empty);

        var baseMap = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        if (doc.GetValueOrDefault("packages") is List<object?> baseList)
        {
            foreach (var e in baseList.OfType<Dictionary<string, object?>>())
                baseMap[PyStrOrEmpty(e.GetValueOrDefault("dir"))] = e;
        }

        var liveMap = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var e in ScanPackages(root))
            liveMap[PyStrOrEmpty(e.GetValueOrDefault("dir"))] = e;

        var issues = new List<string>();
        var warns = new List<string>();
        foreach (var (d, cur) in liveMap.OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            if (baseMap.ContainsKey(d)) continue;
            issues.Add($"社区包资产未登记基线：{d}（{PyStr(cur.GetValueOrDefault("files"))} 文件 / " +
                       $"{PyStr(cur.GetValueOrDefault("lines"))} 行）——新增包须重签基线（nf asset baseline --write）");
        }
        foreach (var (d, want) in baseMap.OrderBy(kv => kv.Key, StringComparer.Ordinal))
        {
            if (!liveMap.TryGetValue(d, out var cur))
            {
                warns.Add($"{PyStrOrEmpty(want.GetValueOrDefault("package"), d)} 不在场" +
                          "（跳过资产行数基线核对——对齐段 B 缺包只记 WARN）");
                continue;
            }
            foreach (var (key, label) in new[] { ("files", "文件数"), ("lines", "行数"), ("digest", "外形摘要") })
            {
                var now = cur.GetValueOrDefault(key);
                var was = want.GetValueOrDefault(key);
                if (PyEqualsLoose(now, was)) continue;
                issues.Add($"{PyStrOrEmpty(want.GetValueOrDefault("package"), d)} 资产{label}与基线不一致：" +
                           $"实时={PyStr(now)} 基线={PyStr(was)}" +
                           "（修复指引：核对内容后显式重签 nf asset baseline --write）");
            }
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["packages"] = (long)liveMap.Count,
            ["baseline"] = (long)baseMap.Count,
            ["lines"] = liveMap.Values.ToDictionary(
                e => PyStrOrEmpty(e.GetValueOrDefault("package")),
                e => e.GetValueOrDefault("lines") ?? 0L, StringComparer.Ordinal),
            ["files"] = liveMap.Values.ToDictionary(
                e => PyStrOrEmpty(e.GetValueOrDefault("package")),
                e => e.GetValueOrDefault("files") ?? 0L, StringComparer.Ordinal),
        };
        return (issues, warns, stats);
    }

    private static Dictionary<string, object?> Load(string root)
    {
        var path = Path.Combine(root, BaselineRel.Replace('/', Path.DirectorySeparatorChar));
        var empty = new Dictionary<string, object?>(StringComparer.Ordinal);
        if (!File.Exists(path)) return empty;
        try
        {
            using var doc = JsonDocument.Parse(StrictUtf8.GetString(File.ReadAllBytes(path)));
            return PythonJson.ToGraph(doc.RootElement) is Dictionary<string, object?> map ? map : empty;
        }
        catch (JsonException)
        {
            return empty;
        }
    }

    /// <summary>Python <c>str(x)</c>（不含引号），<c>%s</c> 占位用。</summary>
    private static string PyStr(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        double d => PythonJson.PyFloatRepr(d),
        _ => PyScalar.PyRepr(v),
    };

    /// <summary>Python <c>x or fallback</c> 的 <c>%s</c> 口径（None / "" 等假值走回退）。</summary>
    private static string PyStrOrEmpty(object? v, string fallback = "") =>
        IsPyTruthy(v) ? PyStr(v) : fallback;

    private static bool IsPyTruthy(object? v) => v switch
    {
        null => false,
        bool b => b,
        string s => s.Length > 0,
        long l => l != 0,
        int i => i != 0,
        double d => d != 0,
        List<object?> list => list.Count > 0,
        Dictionary<string, object?> map => map.Count > 0,
        _ => true,
    };

    /// <summary>JSON 值比较：整数与整数、整数与等值浮点都算相等（Python <c>1 == 1.0</c>）。</summary>
    internal static bool PyEqualsLoose(object? a, object? b)
    {
        if (a is null || b is null) return a is null && b is null;
        if (a is string sa && b is string sb) return sa == sb;
        if (a is bool ba && b is bool bb) return ba == bb;
        var an = a as IConvertible;
        var bn = b as IConvertible;
        if (a is long or int or double && b is long or int or double)
            return Math.Abs(Convert.ToDouble(a, System.Globalization.CultureInfo.InvariantCulture)
                            - Convert.ToDouble(b, System.Globalization.CultureInfo.InvariantCulture)) == 0;
        return Equals(a, b);
    }
}
