namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/retriever.py::referenced_by</c>（v2.2.0 A2）：registry <c>protocols[].references</c> 的引用反查。
///
/// <b>与 <see cref="ImpactCheck.ReferencedByPackages"/> 不是同一口径，故必须分开实现</b>：
/// 本件是**类别感知**匹配——查询带类别（<c>情感:M55</c>）→ 命中同类别声明与**裸号**声明，**不命**其它类别同号（<c>法律:M55</c>）；
/// 查询裸号（<c>M55</c>）→ 命中所有同裸号声明。而 <c>impact</c> 面走的是"裸号归一"（每号平等），
/// 若在此复用会把 <c>法律:M55</c> 也算成命中——**静默多报**，自检为此加了专钉。
///
/// 加载失败（文件缺失 / JSON 损坏）真源一律吞成空表 → 输出"无引用"，退出码 0（不是报错）。
/// </summary>
public static class Retriever
{
    public static List<Dictionary<string, object?>> ReferencedBy(string moduleId, string registryPath)
    {
        Dictionary<string, object?> registry;
        try
        {
            registry = ImpactCheck.LoadRegistry(registryPath);
        }
        catch
        {
            return new List<Dictionary<string, object?>>();
        }

        var q = moduleId;
        var (qCat, qBare) = Split(q);
        var output = new List<Dictionary<string, object?>>();
        foreach (var p in (registry.GetValueOrDefault("protocols") as List<object?> ?? new List<object?>())
                     .OfType<Dictionary<string, object?>>())
        {
            foreach (var r in (p.GetValueOrDefault("references") as List<object?> ?? new List<object?>())
                         .OfType<Dictionary<string, object?>>())
            {
                var mid = PyText(r.GetValueOrDefault("module_id"));
                var (mCat, mBare) = Split(mid);
                var hit = false;
                if (mid.Length > 0 && q.Length > 0)
                {
                    hit = qCat.Length == 0
                        ? mBare == qBare
                        : (mCat == qCat && mBare == qBare) || (mCat.Length == 0 && mBare == qBare);
                }
                if (!hit) continue;
                output.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["referrer"] = p.GetValueOrDefault("id"),
                    ["source_package"] = r.GetValueOrDefault("source_package"),
                    ["module_id"] = r.GetValueOrDefault("module_id"),
                    ["source_schema_version"] = r.GetValueOrDefault("source_schema_version"),
                    ["asset_readonly"] = r.GetValueOrDefault("asset_readonly"),
                });
            }
        }
        return output;
    }

    /// <summary>Python <c>q.split(":", 1)</c> 的两段（无冒号 → 类别空 + 全串为裸号）。</summary>
    private static (string Cat, string Bare) Split(string s)
    {
        var at = s.IndexOf(':');
        return at < 0 ? ("", s) : (s[..at], s[(at + 1)..]);
    }

    private static string PyText(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        _ => PyScalar.PyRepr(v),
    };
}
