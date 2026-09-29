using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>pack_combo.py::breadth</c>：全部两两组合 + 定种子抽样的三元/四元/五元/六元，
/// 跑同一套不变量，产出与 Python 侧**同形同值**的统计。
///
/// 抽样自足：<see cref="GenerateSamples"/> 用 <see cref="PyRandom"/>（MT19937 逐位复刻）
/// 生成与 CPython 同序样本集，故整条广度证明**不需外部样本文件**。
/// </summary>
public static class Breadth
{
    public const long DefaultSeed = 20260923;

    public static Dictionary<string, object?> Run(string root, JsonElement samples, bool parallel = true)
        => Core(root, FromJson(samples), parallel);

    /// <summary>自足模式：内部生成样本（两两全集 + 四档抽样），不需要外部样本文件。</summary>
    public static Dictionary<string, object?> RunSelfContained(string root, bool parallel = true,
        long seed = DefaultSeed, int triples = 400, int quads = 200, int quints = 120, int sexts = 60)
        => Core(root, GenerateSamples(root, seed, triples, quads, quints, sexts), parallel);

    /// <summary>只跑两两全集（不抽样）——最小自足面。</summary>
    public static Dictionary<string, object?> RunPairsOnly(string root, bool parallel = true)
    {
        var samples = GenerateSamples(root, DefaultSeed, 0, 0, 0, 0);
        var stats = Core(root, samples, parallel);
        stats["samples_source"] = "internal-pairs-only";
        return stats;
    }

    /// <summary>等价 Python：<c>names=sorted(profiles)</c> + <c>rnd=random.Random(seed)</c> + 逐档 while 抽样 + <c>sorted(...)</c>。</summary>
    public static Dictionary<string, List<List<string>>> GenerateSamples(string root, long seed,
        int triples = 400, int quads = 200, int quints = 120, int sexts = 60)
    {
        var names = RepoCache.For(root).Profiles.Keys.OrderBy(x => x, StringComparer.Ordinal).ToList();
        var rnd = new PyRandom(seed);

        List<List<string>> Draw(int size, int want)
        {
            var picks = new List<List<string>>();
            var seen = new HashSet<string>(StringComparer.Ordinal);
            if (names.Count >= size)
            {
                while (picks.Count < Math.Min(want, 5000))
                {
                    var sample = rnd.SampleSet(names, size);
                    sample.Sort(StringComparer.Ordinal);           // tuple(sorted(...))
                    var key = string.Join("\u0000", sample);
                    if (seen.Add(key)) picks.Add(sample);
                }
            }
            picks.Sort(CompareSequences);                              // sorted(tuples)
            return picks;
        }

        var pairs = new List<List<string>>();
        for (var i = 0; i < names.Count; i++)
        {
            for (var j = i + 1; j < names.Count; j++) pairs.Add(new List<string> { names[i], names[j] });
        }

        // 顺序必须与 Python 一致：triples → quads → quints → sexts（共享同一 RNG 状态）
        var result = new Dictionary<string, List<List<string>>>(StringComparer.Ordinal)
        {
            ["pairs"] = pairs,
            ["triples"] = Draw(3, triples),
            ["quads"] = Draw(4, quads),
            ["quints"] = Draw(5, quints),
            ["sexts"] = Draw(6, sexts),
        };
        return result;
    }

    private static int CompareSequences(List<string> a, List<string> b)
    {
        var n = Math.Min(a.Count, b.Count);
        for (var i = 0; i < n; i++)
        {
            var c = string.CompareOrdinal(a[i], b[i]);
            if (c != 0) return c;
        }
        return a.Count.CompareTo(b.Count);
    }

    private static Dictionary<string, List<List<string>>> FromJson(JsonElement samples)
    {
        var result = new Dictionary<string, List<List<string>>>(StringComparer.Ordinal);
        foreach (var key in new[] { "pairs", "triples", "quads", "quints", "sexts" })
        {
            var list = new List<List<string>>();
            if (samples.TryGetProperty(key, out var array) && array.ValueKind == JsonValueKind.Array)
            {
                foreach (var combo in array.EnumerateArray())
                {
                    list.Add(combo.EnumerateArray().Select(x => x.GetString()!).ToList());
                }
            }
            result[key] = list;
        }
        return result;
    }

    private static Dictionary<string, object?> Core(string root,
        Dictionary<string, List<List<string>>> samples, bool parallel)
    {
        RepoCache.For(root);   // 预填缓存，避免并行阶段争用

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["packs"] = RepoCache.For(root).Profiles.Count,
            ["pairs"] = samples["pairs"].Count, ["pairs_legal"] = 0,
            ["triples"] = samples["triples"].Count, ["triples_legal"] = 0,
            ["quads"] = samples["quads"].Count, ["quads_legal"] = 0,
            ["quints"] = samples["quints"].Count, ["quints_legal"] = 0,
            ["sexts"] = samples["sexts"].Count, ["sexts_legal"] = 0,
            ["failures"] = new List<object?>(),
        };
        var failures = (List<object?>)stats["failures"]!;

        Evaluate(root, samples["pairs"], "pairs", stats, failures, parallel);
        Evaluate(root, samples["triples"], "triples", stats, failures, parallel);
        Evaluate(root, samples["quads"], "quads", stats, failures, parallel);
        Evaluate(root, samples["quints"], "quints", stats, failures, parallel);
        Evaluate(root, samples["sexts"], "sexts", stats, failures, parallel);

        stats["all_legal"] = (int)stats["pairs"]! == (int)stats["pairs_legal"]! &&
                             (int)stats["triples"]! == (int)stats["triples_legal"]! &&
                             (int)stats["quads"]! == (int)stats["quads_legal"]! &&
                             (int)stats["quints"]! == (int)stats["quints_legal"]! &&
                             (int)stats["sexts"]! == (int)stats["sexts_legal"]!;
        return stats;
    }

    private static void Evaluate(string root, List<List<string>> combos, string tag,
        Dictionary<string, object?> stats, List<object?> failures, bool parallel)
    {
        var results = new (bool Legal, List<object?> Dangling, List<object?> Unbridged)[combos.Count];
        void Body(int index)
        {
            var cert = Combinator.Build(root, combos[index]).Certificate;
            var closure = (Dictionary<string, object?>)cert["dependency_closure"]!;
            var events = (Dictionary<string, object?>)cert["event_closure"]!;
            results[index] = (cert["legal"] is true,
                ((List<object?>)closure["dangling"]!).Take(2).ToList(),
                ((List<object?>)events["unbridged"]!).Take(2).ToList());
        }

        if (parallel)
        {
            Parallel.For(0, combos.Count, Body);
        }
        else
        {
            for (var i = 0; i < combos.Count; i++) Body(i);
        }

        for (var i = 0; i < results.Length; i++)
        {
            if (results[i].Legal) stats[tag + "_legal"] = (int)stats[tag + "_legal"]! + 1;
            else if (failures.Count < 10 && tag != "triples" && tag != "quads")
            {
                failures.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["combo"] = combos[i].Cast<object?>().ToList(),
                    ["dangling"] = results[i].Dangling,
                    ["unbridged"] = results[i].Unbridged,
                });
            }
        }
    }
}
