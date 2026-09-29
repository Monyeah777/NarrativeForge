using System.Globalization;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>scripts/geo_export.py</c>（**check38 子扫描 3 · GEO 出口**）：把标准目录
/// （<c>protocol/standards_catalog.json</c> 370 条）+ 绑定面（<c>protocol/standards_binding.json</c>）
/// 导出成**生成式引擎可引用**的稳定面，`check` 逐字节比对**在盘生成物 ↔ 实时派生**。
///
/// 八个生成物：<c>docs/standards/index.md</c> · <c>layer-{data,eng,form,gov,iface}.md</c> ·
/// <c>answer-cards.md</c> · <c>protocol/geo_export.json</c>。**全是生成物、禁止手写**——
/// 这正是本件作为「只读门」最有价值的一面：重算一遍即可判定盘上文件是否被手改。
/// 写面（<c>--write</c>）不移植。
/// </summary>
public static class GeoExport
{
    public const string CatalogRel = "protocol/standards_catalog.json";
    public const string BindingRel = "protocol/standards_binding.json";
    public const string IndexRel = "docs/standards/index.md";
    public const string CardsRel = "docs/standards/answer-cards.md";
    public const string MachineRel = "protocol/geo_export.json";
    public static readonly string[] Layers = { "data", "eng", "form", "gov", "iface" };
    private const string Head =
        "> 本页由 `python scripts/geo_export.py --write` 生成，禁止手改。"
        + "真源：`protocol/standards_catalog.json` + `protocol/standards_binding.json`。";

    private static readonly Regex AnchorRe = new(@"^### `([^`]+)`", RegexOptions.Multiline);
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public sealed record Result(List<string> Issues, Dictionary<string, object?> Stats)
    {
        public bool Ok => Issues.Count == 0;

        /// <summary>check38 的框法：issues 逐条 <c>[FAIL] …</c>，末行 <c>GEO 出口 子扫描：…</c>。</summary>
        public List<string> Log(string label = "GEO 出口")
        {
            var lines = Issues.Select(issue => "[FAIL] " + issue).ToList();
            lines.Add($"{label} 子扫描：{(Issues.Count == 0 ? "零缺口" : "FAIL " + Issues.Count)}");
            return lines;
        }

        public string LogDigest(string label = "GEO 出口") => ExitFaces.Digest32(Log(label));
    }

    private sealed record Loaded(List<Dictionary<string, object?>> Standards,
                                 Dictionary<string, object?> Coverage,
                                 Dictionary<string, Dictionary<string, object?>> Counts);

    private static Loaded Load(string root)
    {
        var catalog = ReadJson(root, CatalogRel) as Dictionary<string, object?>
                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var binding = ReadJson(root, BindingRel) as Dictionary<string, object?>
                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var counts = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var pack in Dicts(binding.GetValueOrDefault("packs")))
        {
            foreach (var b in Dicts(pack.GetValueOrDefault("bindings")))
            {
                // 真源 `str(b.get("standard") or "")`：**假值一律归空串**（缺键/None/0 → ""）。
                // 实测踩过：缺 `support_standard` 时若按 `str(None)` 处理会凭空多出一个 "None" 计数键，
                // 卡 3 的「N 条不同标准被引用」随之偏大（真仓语料两键齐全，只有合成语料照得出来）。
                var main = PyOr(b.GetValueOrDefault("standard"), "");
                var support = PyOr(b.GetValueOrDefault("support_standard"), "");
                if (main.Length > 0) Bump(counts, main, "main");
                if (support.Length > 0) Bump(counts, support, "support");
            }
        }
        var standards = Dicts(catalog.GetValueOrDefault("standards"));
        var coverage = catalog.GetValueOrDefault("coverage") as Dictionary<string, object?>
                       ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        return new Loaded(standards, coverage, counts);
    }

    private static void Bump(Dictionary<string, Dictionary<string, object?>> counts, string id, string key)
    {
        if (!counts.TryGetValue(id, out var row))
        {
            row = new Dictionary<string, object?>(StringComparer.Ordinal) { ["main"] = 0L, ["support"] = 0L };
            counts[id] = row;
        }
        row[key] = Convert.ToInt64(row[key]) + 1;
    }

    /// <summary>真源 <c>build()</c>：八个生成物的文本（纯派生，无副作用）。</summary>
    public static Dictionary<string, string> Build(string root)
    {
        var loaded = Load(root);
        var ordered = loaded.Standards
            .OrderBy(s => PyStr(s.GetValueOrDefault("layer")), StringComparer.Ordinal)
            .ThenBy(s => PyStr(s.GetValueOrDefault("id")), StringComparer.Ordinal)
            .ToList();
        var outs = new Dictionary<string, string>(StringComparer.Ordinal);

        var idx = HeadLines("标准目录 · 可引用索引（GEO 出口）", loaded.Coverage,
            $"每条标准一个稳定锚：`#<id>`（如 `{IndexRel}#onnx`）。");
        foreach (var s in ordered)
        {
            idx.Add($"### `{PyStr(s.GetValueOrDefault("id"))}`");
            idx.Add(Line(s, loaded.Counts));
            idx.Add("");
        }
        outs[IndexRel] = string.Join("\n", idx).TrimEnd() + "\n";

        foreach (var layer in Layers)
        {
            var rows = ordered.Where(s => PyStr(s.GetValueOrDefault("layer")) == layer).ToList();
            var body = HeadLines($"标准目录 · 层 {layer}（{rows.Count} 条）", loaded.Coverage,
                $"本页为 `{IndexRel}` 的按层切片，锚点与主索引一致。");
            foreach (var s in rows)
            {
                body.Add($"### `{PyStr(s.GetValueOrDefault("id"))}`");
                body.Add(Line(s, loaded.Counts));
                body.Add("");
            }
            outs[$"docs/standards/layer-{layer}.md"] = string.Join("\n", body).TrimEnd() + "\n";
        }

        var cards = HeadLines("标准目录 · 可引用卡（按问题形态）", loaded.Coverage,
            "每张卡回答一类问题，可直接被生成式引擎引用；数据源同主索引。");
        var topExt = loaded.Standards
            .OrderByDescending(s => ObjList(s.GetValueOrDefault("ext_points")).Count)
            .ThenBy(s => PyStr(s.GetValueOrDefault("id")), StringComparer.Ordinal)
            .Take(20).ToList();
        cards.Add("## 卡 1 · 哪些标准提供扩展点？");
        cards.Add("");
        cards.Add($"全 **{loaded.Standards.Count}** 条标准均声明扩展点（`ext_points`），扩展点最多的 20 条：");
        cards.Add("");
        foreach (var s in topExt)
        {
            var ext = string.Join(", ", ObjList(s.GetValueOrDefault("ext_points")).Select(PyStr));
            cards.Add($"- `{PyStr(s.GetValueOrDefault("id"))}` · {PyOr(s.GetValueOrDefault("title"), "—")}"
                      + $" · 扩展点 {ObjList(s.GetValueOrDefault("ext_points")).Count}：{PySlice(ext, 120)}");
        }
        cards.Add("");
        cards.Add("## 卡 2 · 各层有哪些标准？");
        cards.Add("");
        var byLayer = loaded.Coverage.GetValueOrDefault("by_layer") as Dictionary<string, object?>
                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var layer in Layers)
        {
            cards.Add($"- **{layer}** {PyInt(byLayer.GetValueOrDefault(layer), 0)} 条"
                      + $" → `docs/standards/layer-{layer}.md`");
        }
        var boundRows = loaded.Counts
            .Select(kv => (Id: kv.Key, Main: PyInt(kv.Value.GetValueOrDefault("main"), 0),
                           Support: PyInt(kv.Value.GetValueOrDefault("support"), 0)))
            .OrderByDescending(r => r.Main + r.Support)
            .ThenBy(r => r.Id, StringComparer.Ordinal)
            .ToList();
        cards.Add("");
        cards.Add("## 卡 3 · 哪些标准被域包绑定、绑了多少次？");
        cards.Add("");
        cards.Add($"绑定总量 **1200**（{loaded.Counts.Count} 条不同标准被引用；主锚=口径锚，辅锚=产出承载锚）。"
                  + "绑定最多的 20 条：");
        cards.Add("");
        foreach (var row in boundRows.Take(20))
            cards.Add($"- `{row.Id}` · 主锚 {row.Main} / 辅锚 {row.Support}");
        var unreach = loaded.Standards
            .Where(s => !PyTruthy((s.GetValueOrDefault("evidence") as Dictionary<string, object?>)
                                  ?.GetValueOrDefault("reachable")))
            .ToList();
        cards.Add("");
        cards.Add("## 卡 4 · 哪些标准本机不可达？（诚实披露）");
        cards.Add("");
        cards.Add($"共 **{unreach.Count}** 条本机探测未达（不假装可达），逐条如下：");
        cards.Add("");
        foreach (var s in unreach)
        {
            var ev = s.GetValueOrDefault("evidence") as Dictionary<string, object?>
                     ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            cards.Add($"- `{PyStr(s.GetValueOrDefault("id"))}` · {PyOr(s.GetValueOrDefault("title"), "—")}"
                      + $" · HTTP {PyGet(ev, "http_status", "-")}"
                      + $" · {PySlice(PyStr(ev.GetValueOrDefault("error")), 80)}");
        }
        outs[CardsRel] = string.Join("\n", cards).TrimEnd() + "\n";

        var machineStandards = ordered.Select(s =>
        {
            var ev = s.GetValueOrDefault("evidence") as Dictionary<string, object?>
                     ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var c = loaded.Counts.GetValueOrDefault(PyStr(s.GetValueOrDefault("id")))
                    ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            return (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = s.GetValueOrDefault("id"), ["title"] = s.GetValueOrDefault("title"),
                ["body"] = s.GetValueOrDefault("body"), ["url"] = s.GetValueOrDefault("url"),
                ["layer"] = s.GetValueOrDefault("layer"),
                ["ext_points"] = s.GetValueOrDefault("ext_points") ?? new List<object?>(),
                ["reachable"] = PyTruthy(ev.GetValueOrDefault("reachable")),
                ["http_status"] = ev.GetValueOrDefault("http_status"),
                ["probe_date"] = ev.GetValueOrDefault("probe_date"),
                ["sha256_sample"] = ev.GetValueOrDefault("sha256_sample"),
                ["bound_main"] = c.GetValueOrDefault("main") ?? 0L,
                ["bound_support"] = c.GetValueOrDefault("support") ?? 0L,
            };
        }).ToList();
        var machine = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = "nf-geo-export/1",
            ["note"] = "生成物；真源 protocol/standards_catalog.json + protocol/standards_binding.json。",
            ["coverage"] = loaded.Coverage,
            ["standards"] = machineStandards,
        };
        outs[MachineRel] = PythonJson.Indented(machine) + "\n";
        return outs;
    }

    /// <summary>真源 <c>check()</c>：生成物与标准目录一致 + 索引锚点集合 = 目录 id 集合。</summary>
    public static Result Check(string root)
    {
        var outs = Build(root);
        var issues = new List<string>();
        foreach (var (rel, text) in outs)
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path))
            {
                issues.Add($"缺生成物 {rel}（跑 `geo_export.py --write`）");
                continue;
            }
            if (StrictUtf8.GetString(File.ReadAllBytes(path)) != text)
                issues.Add($"{rel} 与标准目录不一致（跑 `geo_export.py --write` 重写）");
        }
        var loaded = Load(root);
        var ids = loaded.Standards.Select(s => PyStr(s.GetValueOrDefault("id")))
            .ToHashSet(StringComparer.Ordinal);
        var anchored = new HashSet<string>(StringComparer.Ordinal);
        var idxPath = Path.Combine(root, IndexRel.Replace('/', Path.DirectorySeparatorChar));
        if (File.Exists(idxPath))
        {
            foreach (Match m in AnchorRe.Matches(StrictUtf8.GetString(File.ReadAllBytes(idxPath))))
                anchored.Add(m.Groups[1].Value);
        }
        if (!anchored.SetEquals(ids))
        {
            issues.Add($"索引锚点集合 ≠ 目录 id 集合（缺 {ids.Except(anchored).Count()}"
                       + $" / 多 {anchored.Except(ids).Count()}）");
        }
        return new Result(issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["standards"] = (long)loaded.Standards.Count,
            ["bound_standards"] = (long)loaded.Counts.Count,
            ["files"] = (long)outs.Count,
            ["coverage"] = loaded.Coverage,
        });
    }

    private static List<string> HeadLines(string title, Dictionary<string, object?> coverage, string extra)
    {
        var lines = new List<string> { "# " + title, "", Head, "" };
        lines.Add($"- 覆盖：标准 **{PyInt(coverage.GetValueOrDefault("standards"), 0)}** 条"
                  + $" · 本机可达 **{PyInt(coverage.GetValueOrDefault("reachable"), 0)}**"
                  + $" · 不可达 **{PyInt(coverage.GetValueOrDefault("unreachable"), 0)}**"
                  + $" · 机构 **{PyInt(coverage.GetValueOrDefault("bodies"), 0)}**"
                  + $" · 依赖边 **{PyInt(coverage.GetValueOrDefault("depends_edges"), 0)}**");
        var byLayer = coverage.GetValueOrDefault("by_layer") as Dictionary<string, object?>
                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        lines.Add("- 分层：" + string.Join(" · ", byLayer.Keys.OrderBy(k => k, StringComparer.Ordinal)
            .Select(k => $"{k} {PyInt(byLayer[k], 0)}")));
        lines.Add("- 可达性是**本机实测**（探针日期见每条），不可达条目照实标注、不假装可达。");
        if (extra.Length > 0) lines.Add("- " + extra);
        lines.Add("");
        return lines;
    }

    private static string Line(Dictionary<string, object?> s, Dictionary<string, Dictionary<string, object?>> counts)
    {
        var ev = s.GetValueOrDefault("evidence") as Dictionary<string, object?>
                 ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var reach = PyTruthy(ev.GetValueOrDefault("reachable")) ? "是" : "否";
        // Python `ev.get("http_status", "-")`——**缺键才取默认值**（键在场时 None→"None"、0→"0"），
        // 不是 `or`（实测踩过：`http_status: 0` 被 `or` 误当缺值打成 "-"）。
        var http = PyGet(ev, "http_status", "-");
        var date = PyGet(ev, "probe_date", "-");
        var ext = string.Join(", ", ObjList(s.GetValueOrDefault("ext_points")).Select(PyStr));
        if (ext.Length == 0) ext = "—";
        var c = counts.GetValueOrDefault(PyStr(s.GetValueOrDefault("id")))
                ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        return $"- {PyOr(s.GetValueOrDefault("title"), PyStr(s.GetValueOrDefault("id")))}"
               + $" · {PyOr(s.GetValueOrDefault("body"), "—")}"
               + $" · 层 {PyOr(s.GetValueOrDefault("layer"), "—")}"
               + $" · 可达 {reach}（{http} · {date}） · 扩展点 {ext}"
               + $" · 绑定 主锚 {PyInt(c.GetValueOrDefault("main"), 0)} / 辅锚 {PyInt(c.GetValueOrDefault("support"), 0)}"
               + $" · {PyOr(s.GetValueOrDefault("url"), "—")}";
    }

    private static object? ReadJson(string root, string rel)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        using var doc = JsonIo.ReadFile(path);
        return PythonJson.ToGraph(doc.RootElement);
    }

    private static List<Dictionary<string, object?>> Dicts(object? value) =>
        (value as List<object?>)?.OfType<Dictionary<string, object?>>().ToList()
        ?? new List<Dictionary<string, object?>>();

    private static List<object?> ObjList(object? value) => value as List<object?> ?? new List<object?>();

    /// <summary>Python <c>str(x)</c>（None → <c>None</c>）。</summary>
    private static string PyStr(object? value) => value switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        _ => Convert.ToString(value, CultureInfo.InvariantCulture) ?? "None",
    };

    /// <summary>Python <c>x or fallback</c>（假值 → fallback；fallback 按 <c>%s</c> 语义渲染）。</summary>
    private static string PyOr(object? value, string fallback) =>
        PyTruthy(value) ? PyStr(value) : fallback;

    /// <summary>Python <c>d.get(k, default)</c>：**只有缺键**才取默认值，键在场一律按 <c>%s</c> 渲染。</summary>
    private static string PyGet(Dictionary<string, object?> map, string key, string fallback) =>
        map.ContainsKey(key) ? PyStr(map[key]) : fallback;

    private static long PyInt(object? value, long fallback) => value switch
    {
        long l => l,
        int i => i,
        double d => (long)d,
        _ => fallback,
    };

    /// <summary>Python 切片 <c>s[:n]</c>（按码点，不劈开代理对）。</summary>
    private static string PySlice(string text, int max) => PyScalar.PySlice(text, max);

    private static bool PyTruthy(object? value) => value switch
    {
        null => false,
        bool b => b,
        long l => l != 0,
        int i => i != 0,
        double d => d != 0,
        string s => s.Length > 0,
        List<object?> list => list.Count > 0,
        Dictionary<string, object?> map => map.Count > 0,
        _ => true,
    };
}
