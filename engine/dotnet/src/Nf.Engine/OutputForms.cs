using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Xml.Linq;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/output_forms.py</c>（45 产出形态面 · check32 子扫描）的**读面**：
/// <c>output list</c>（形态清单）与 <c>output check</c>（判件：按扩展名 + 内容嗅探判形态与上限档位，再跑该形态的校验器）。
///
/// 档位 = **本仓可做的判定强度**（T0 散文 → T4 可复算），不是"格式有多高级"。
/// 写面（<c>render --write</c> / <c>meter --write</c>）不属只读门。
///
/// <b>一处已声明边界（不静默放行）</b>：<c>toml</c> 形态的校验器依赖 Python 3.11 的 <c>tomllib</c>；
/// 本引擎 BCL-only 无 TOML 解析器，故对该形态**明确报"不可判定"**而不是返回空 issues
/// （返回空 = 把"没判"当"判过"，正是本工程要防的假绿）。
/// </summary>
public static class OutputForms
{
    public const string RegistryRel = "protocol/output_forms.json";
    public const string BaselineRel = "protocol/output_forms_baseline.json";
    public const string IndexRel = "outputs/INDEX.json";

    public static readonly string[] Tiers = { "T0", "T1", "T2", "T3", "T4" };

    private static readonly HashSet<string> Statuses = new(StringComparer.Ordinal)
    {
        "supported", "absorbed", "planned", "deferred", "unfit", "reference", "unreachable",
    };

    private static readonly Dictionary<string, string> ExtForm = new(StringComparer.Ordinal)
    {
        [".json"] = "json", [".jsonl"] = "jsonl", [".ndjson"] = "jsonl", [".yaml"] = "yaml",
        [".yml"] = "yaml", [".toml"] = "toml", [".csv"] = "csv", [".tsv"] = "csv", [".xml"] = "xml",
        [".md"] = "markdown", [".mmd"] = "mermaid", [".dot"] = "graphviz-dot", [".gv"] = "graphviz-dot",
        [".graphml"] = "graphml", [".svg"] = "svg", [".txt"] = "text", [".proto"] = "protobuf-proto3",
        [".graphql"] = "graphql-sdl", [".ttl"] = "turtle", [".sql"] = "sql-ddl",
    };

    private static readonly Dictionary<string, string> FormMaxTier = new(StringComparer.Ordinal)
    {
        ["json"] = "T2", ["jsonl"] = "T2", ["yaml"] = "T2", ["toml"] = "T2", ["csv"] = "T2",
        ["xml"] = "T1", ["svg"] = "T1", ["markdown"] = "T1", ["text"] = "T0",
        ["json-schema"] = "T2", ["vega-lite"] = "T3", ["mermaid"] = "T3", ["graphviz-dot"] = "T3",
        ["graphml"] = "T3", ["json-graph-format"] = "T3", ["quant-metrics"] = "T3",
        ["performance-report"] = "T4", ["concept-closure"] = "T4", ["system-card"] = "T3",
        ["domain-spec"] = "T3", ["domain-report"] = "T4", ["combo-cert"] = "T4",
    };

    private static readonly UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);
    // 真源是 `<!` + 可选空白 + DOCTYPE/ENTITY —— 首版漏了那个 `!`，DTD 守卫**整条不触发**
    // （合成语料 `<!DOCTYPE …` 当场照出来：py 判红、net 放行）。守卫失灵 = 安全面假绿，属最不该有的那类。
    private static readonly Regex DtdRe = new(@"<!\s*(?:DOCTYPE|ENTITY)", RegexOptions.IgnoreCase);
    private static readonly Regex DotHeadRe = new(@"^\s*(strict\s+)?(di)?graph\b", RegexOptions.Multiline);
    private static readonly string[] MermaidKinds =
    {
        "graph", "flowchart", "sequencediagram", "classdiagram", "erdiagram",
        "statediagram", "gantt", "pie", "journey", "mindmap",
    };

    /// <summary>形态清单真源（<c>protocol/output_forms.json</c>）；缺件/非对象 → 空表。</summary>
    public static Dictionary<string, object?> LoadRegistry(string root)
    {
        var (data, _) = ReadJson(Rel(root, RegistryRel));
        return data as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
    }

    /// <summary>按扩展名 + 内容嗅探判形态，返回 (form, 上限档位)。认不出即 <c>text</c>/<c>T0</c>。</summary>
    public static (string Form, string Tier) Detect(string root, string rel)
    {
        var suffix = Path.GetExtension(rel).ToLowerInvariant();
        var form = ExtForm.GetValueOrDefault(suffix, "text");
        if (suffix == ".json")
        {
            var (data, _) = ReadJson(Rel(root, rel));
            if (data is Dictionary<string, object?> map)
            {
                var sch = PyStrOrEmpty(map.GetValueOrDefault("$schema"));
                if (sch.Contains("json-schema.org", StringComparison.Ordinal)) form = "json-schema";
                var kind = PyStrOrEmpty(map.GetValueOrDefault("kind"));
                if (kind.StartsWith("nf-domain-spec", StringComparison.Ordinal)) form = "domain-spec";
                else if (PyStrOrEmpty(map.GetValueOrDefault("schema")).StartsWith("nf-combo/1", StringComparison.Ordinal)) form = "combo-cert";
                else if (kind.StartsWith("nf-domain-report", StringComparison.Ordinal)) form = "domain-report";
                else if (kind.StartsWith("nf-system-card", StringComparison.Ordinal)) form = "system-card";
                else if (sch.Contains("vega-lite", StringComparison.Ordinal)) form = "vega-lite";
                else if (sch.Contains("vega", StringComparison.Ordinal)) form = "vega";
                else if (kind.StartsWith("nf-performance", StringComparison.Ordinal)) form = "performance-report";
                else if (kind.StartsWith("nf-quant-metrics", StringComparison.Ordinal)) form = "quant-metrics";
                else if (kind.StartsWith("nf-concept-closure", StringComparison.Ordinal)) form = "concept-closure";
            }
        }
        return (form, FormMaxTier.GetValueOrDefault(form, "T1"));
    }

    /// <summary>该形态的结构校验器（真源 <c>_FORM_CHECK</c> 表；未登记的形态返回空表 = 只判形态与档位）。</summary>
    public static List<string> Check(string root, string rel, string form) => form switch
    {
        "json" or "json-schema" or "vega" or "json-graph-format" or "performance-report"
            or "concept-closure" or "system-card" => CheckJson(root, rel),
        "jsonl" => CheckJsonl(root, rel),
        "csv" => CheckCsv(root, rel),
        "xml" or "svg" => CheckXml(root, rel),
        "markdown" => CheckMarkdown(root, rel),
        "toml" => CheckToml(),
        "yaml" => CheckYaml(root, rel),
        "vega-lite" => CheckVegaLite(root, rel),
        "mermaid" => CheckMermaid(root, rel),
        "graphviz-dot" => CheckDot(root, rel),
        "graphml" => CheckGraphml(root, rel),
        "quant-metrics" => CheckQuantMetrics(root, rel),
        "domain-spec" => CheckDomainSpec(root, rel),
        "domain-report" => CheckDomainReport(root, rel),
        "combo-cert" => CheckComboCert(root, rel),
        _ => new List<string>(),
    };

    // ---------------------------------------------------------------- JSON 读取

    public static string Rel(string root, string rel) => Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
    private static string ReadText(string path) => KnowledgeSig.Norm(StrictUtf8.GetString(File.ReadAllBytes(path)));

    /// <summary>
    /// <c>_read_json</c> 等价：读不到 / 解析失败 → <c>(null, 原因文案)</c>。
    /// **解析失败的具体文案随各自 JSON 运行时**（CPython 与 System.Text.Json 不同）——属已登记的不可约类。
    /// </summary>
    public static (object? Data, string Error) ReadJson(string path)
    {
        string text;
        try
        {
            text = ReadText(path);
        }
        catch (Exception exc) when (exc is IOException or UnauthorizedAccessException)
        {
            return (null, $"不可读：{exc.Message}");
        }
        try
        {
            using var doc = JsonIo.Parse(text);
            return (PythonJson.ToGraph(doc.RootElement), "");
        }
        catch (JsonException exc)
        {
            return (null, $"JSON 解析失败：{exc.Message}");
        }
    }

    /// <summary>对象层重复键（Python <c>object_pairs_hook</c> 语义：每个对象各自查重，最后去重排序）。</summary>
    private static (List<string> Dups, string Error) ScanDuplicateKeys(byte[] utf8)
    {
        var reader = new Utf8JsonReader(utf8, new JsonReaderOptions
        {
            MaxDepth = JsonIo.MaxDepth,
            AllowTrailingCommas = false,
            CommentHandling = JsonCommentHandling.Disallow,
        });
        var stack = new Stack<HashSet<string>>();
        var dups = new List<string>();
        try
        {
            while (reader.Read())
            {
                switch (reader.TokenType)
                {
                    case JsonTokenType.StartObject:
                        stack.Push(new HashSet<string>(StringComparer.Ordinal));
                        break;
                    case JsonTokenType.EndObject:
                        if (stack.Count > 0) stack.Pop();
                        break;
                    case JsonTokenType.PropertyName:
                        var name = reader.GetString() ?? "";
                        if (stack.Count > 0 && !stack.Peek().Add(name)) dups.Add(name);
                        break;
                }
            }
        }
        catch (JsonException exc)
        {
            return (new List<string>(), $"JSON 不可解析：{exc.Message}");
        }
        dups.Sort(StringComparer.Ordinal);
        return (dups.Distinct(StringComparer.Ordinal).ToList(), "");
    }

    private static List<string> CheckJson(string root, string rel)
    {
        var (dups, err) = ScanDuplicateKeys(File.ReadAllBytes(Rel(root, rel)));
        if (err.Length > 0) return new List<string> { err };
        return dups.Select(d => $"JSON 重复键：{d}").ToList();
    }

    private static List<string> CheckJsonl(string root, string rel)
    {
        var issues = new List<string>();
        var lines = KnowledgeSig.SplitLines(ReadText(Rel(root, rel)));
        for (var i = 0; i < lines.Count; i++)
        {
            if (lines[i].Trim().Length == 0) continue;
            try
            {
                using var _ = JsonIo.Parse(lines[i]);
            }
            catch (JsonException exc)
            {
                issues.Add($"第 {i + 1} 行非 JSON：{exc.Message}");
            }
        }
        return issues;
    }

    private static List<string> CheckCsv(string root, string rel)
    {
        var text = ReadText(Rel(root, rel));
        if (text.Contains('\x00')) return new List<string> { "含 NUL 字节（非文本 CSV）" };
        var rows = ParseCsv(text).Where(r => r.Count > 0).ToList();
        if (rows.Count == 0) return new List<string> { "空表" };
        var width = rows[0].Count;
        var issues = width > 0 ? new List<string>() : new List<string> { "表头为空" };
        for (var i = 1; i < rows.Count; i++)
            if (rows[i].Count != width)
                issues.Add($"第 {i + 1} 行字段数 {rows[i].Count} ≠ 表头 {width}");
        if (rows[0].Distinct(StringComparer.Ordinal).Count() != width) issues.Add("表头有重名列");
        return issues;
    }

    /// <summary>Python <c>csv.reader</c> 默认方言（逗号 / 双引号 / 双写转义 / 可跨行）。</summary>
    private static List<List<string>> ParseCsv(string text)
    {
        var rows = new List<List<string>>();
        var row = new List<string>();
        var field = new StringBuilder();
        var inQuotes = false;
        var started = false;
        for (var i = 0; i < text.Length; i++)
        {
            var c = text[i];
            if (inQuotes)
            {
                if (c == '"')
                {
                    if (i + 1 < text.Length && text[i + 1] == '"') { field.Append('"'); i++; }
                    else inQuotes = false;
                    continue;
                }
                field.Append(c);
                continue;
            }
            if (c == '"' && field.Length == 0 && !started) { inQuotes = true; started = true; continue; }
            if (c == ',') { row.Add(field.ToString()); field.Clear(); started = false; continue; }
            if (c == '\n')
            {
                // **空行产出的是空记录 `[]`**（Python csv.reader 口径），不是"一个空字段"——
                // 两者在真源里分别走「空表」与「表头为空」两条判定，混了就判错。
                if (row.Count == 0 && field.Length == 0 && !started) rows.Add(new List<string>());
                else { row.Add(field.ToString()); rows.Add(row); }
                field.Clear();
                row = new List<string>();
                started = false;
                continue;
            }
            field.Append(c);
            started = true;
        }
        if (field.Length > 0 || row.Count > 0) { row.Add(field.ToString()); rows.Add(row); }
        return rows;
    }

    private static string XmlGuard(string text) =>
        DtdRe.IsMatch(text) ? "含 DTD/ENTITY 声明（本仓 XML 产出面禁 DTD：堵实体展开类攻击）" : "";

    private static List<string> CheckXml(string root, string rel)
    {
        var text = ReadText(Rel(root, rel));
        var guard = XmlGuard(text);
        if (guard.Length > 0) return new List<string> { guard };
        try
        {
            XDocument.Parse(text);
        }
        catch (System.Xml.XmlException exc)
        {
            return new List<string> { $"XML 良构性失败：{exc.Message}" };
        }
        return new List<string>();
    }

    private static List<string> CheckMarkdown(string root, string rel)
    {
        var text = ReadText(Rel(root, rel));
        var issues = new List<string>();
        if (AssetShelf.PyStrip(text).Length == 0) issues.Add("空档");
        if (AssetShelf.CountNonOverlapping(text, "```") % 2 != 0) issues.Add("代码围栏未闭合（``` 奇数个）");
        return issues;
    }

    /// <summary>
    /// <b>已声明边界</b>：真源用 Python 3.11 <c>tomllib</c> 判 TOML 良构；本引擎 BCL-only 无 TOML 解析器。
    /// 返回"不可判定"而不是空表——**"不支持"绝不等价"通过"**（真源自己的子集纪律，此处照同一标准执行）。
    /// </summary>
    private static List<string> CheckToml() => new()
    {
        "TOML 形态不可判定：本引擎未内建 TOML 解析器（BCL-only）——明确拒绝，不静默放行",
    };

    private static List<string> CheckYaml(string root, string rel)
    {
        var issues = new List<string>();
        var lines = KnowledgeSig.SplitLines(ReadText(Rel(root, rel)));
        for (var i = 0; i < lines.Count; i++)
        {
            var line = lines[i];
            // 真源是 `"\t" in line[: len(line) - len(line.lstrip())]` —— 查的是**行首空白段**里有没有 Tab。
            // 首版写成"lstrip 后第一个字符是不是 Tab"（那永远不是空白）→ Tab 缩进**整条漏判**。
            var lead = 0;
            while (lead < line.Length && AssetShelf.IsPySpace(line[lead])) lead++;
            if (line[..lead].Contains('\t'))
                issues.Add($"第 {i + 1} 行用 Tab 缩进（YAML 禁 Tab）");
            var body = line.Trim();
            if (body.StartsWith("- ", StringComparison.Ordinal) || body.Length == 0
                || body.StartsWith("#", StringComparison.Ordinal)) continue;
            if (!line.Contains(':'))
                issues.Add($"第 {i + 1} 行非映射项（收窄子集要求 key: value）：{PySlice(body, 40)}");
        }
        return issues;
    }

    private static List<string> CheckVegaLite(string root, string rel)
    {
        var (data, err) = ReadJson(Rel(root, rel));
        if (err.Length > 0) return new List<string> { err };
        if (data is not Dictionary<string, object?> map) return new List<string>();
        var issues = new List<string>();
        if (!PyStr(map.GetValueOrDefault("$schema")).Contains("vega-lite", StringComparison.Ordinal))
            issues.Add("缺 $schema（应为 vega-lite v5）");
        if (!new[] { "mark", "layer", "hconcat", "vconcat", "concat", "facet", "spec", "repeat" }
                .Any(k => map.ContainsKey(k)))
            issues.Add("缺 mark/layer 等绘图主体");
        if (!map.ContainsKey("data")) issues.Add("缺 data（图不能没有数据源）");
        var enc = map.GetValueOrDefault("encoding");
        if (enc is Dictionary<string, object?> encMap)
        {
            foreach (var (ch, spec) in encMap)
            {
                if (spec is not Dictionary<string, object?> specMap) { issues.Add($"encoding.{ch} 非对象"); continue; }
                if (!new[] { "field", "aggregate", "value", "datum", "timeUnit", "bin" }.Any(k => specMap.ContainsKey(k)))
                    issues.Add($"encoding.{ch} 无 field/aggregate/value（通道未绑定）");
            }
        }
        else if (enc is not null) issues.Add("encoding 非对象");
        return issues;
    }

    private static List<string> CheckMermaid(string root, string rel)
    {
        var body = KnowledgeSig.SplitLines(ReadText(Rel(root, rel)))
            .Select(x => x.TrimEnd())
            .Where(x => x.Trim().Length > 0 && !x.Trim().StartsWith("%%", StringComparison.Ordinal))
            .ToList();
        if (body.Count == 0) return new List<string> { "空图" };
        var head = body[0].Trim().ToLowerInvariant();
        if (!MermaidKinds.Any(head.StartsWith)) 
            return new List<string> { $"首行非已知图种：{PyScalar.PyRepr(PySlice(body[0].Trim(), 40))}" };
        return new List<string>();
    }

    private static List<string> CheckDot(string root, string rel)
    {
        var text = ReadText(Rel(root, rel));
        var issues = new List<string>();
        if (!DotHeadRe.IsMatch(text)) issues.Add("缺 digraph/graph 头");
        var open = text.Count(c => c == '{');
        var close = text.Count(c => c == '}');
        if (open != close) issues.Add($"花括号不配对（{{ {open} / }} {close}）");
        return issues;
    }

    private static List<string> CheckGraphml(string root, string rel)
    {
        var path = Rel(root, rel);
        var guard = XmlGuard(ReadText(path));
        if (guard.Length > 0) return new List<string> { $"GraphML {guard}" };
        XDocument tree;
        try
        {
            tree = XDocument.Parse(ReadText(path));
        }
        catch (System.Xml.XmlException exc)
        {
            return new List<string> { $"GraphML XML 解析失败：{exc.Message}" };
        }
        var rootEl = tree.Root!;
        var issues = new List<string>();
        if (rootEl.Name.LocalName != "graphml") issues.Add($"根元素应为 graphml，实为 {rootEl.Name.LocalName}");
        var graphs = rootEl.Descendants().Where(e => e.Name.LocalName == "graph").ToList();
        if (graphs.Count == 0) issues.Add("缺 <graph> 元素");
        var nodes = graphs.SelectMany(g => g.Elements().Where(e => e.Name.LocalName == "node"))
            .Select(n => n.Attribute("id")?.Value).Where(v => v is not null).ToHashSet(StringComparer.Ordinal);
        foreach (var g in graphs)
            foreach (var e in g.Elements().Where(x => x.Name.LocalName == "edge"))
                foreach (var end in new[] { "source", "target" })
                {
                    var v = e.Attribute(end)?.Value;
                    if (v is null || !nodes.Contains(v)) issues.Add($"边端点悬空：{end}={v ?? "None"}");
                }
        return issues;
    }

    private static List<string> CheckQuantMetrics(string root, string rel)
    {
        var issues = CheckJson(root, rel);
        var (data, err) = ReadJson(Rel(root, rel));
        if (err.Length > 0 || data is not Dictionary<string, object?> map)
        {
            if (err.Length > 0) issues.Add(err);
            return issues;
        }
        var entries = PyList(map.GetValueOrDefault("metrics")).Concat(PyList(map.GetValueOrDefault("declared_only")));
        foreach (var entry in entries)
        {
            if (entry is not Dictionary<string, object?> m) { issues.Add($"条目非对象：{PyReprTuple(entry)}"); continue; }
            // 真源是 `m.get("id") or "?"` / `str(m.get("engine") or "")` —— **None 走假值分支**，
            // 不是 Python 的 str(None)="None"（首版照直用 PyStr 就栽在这里：真仓 QUANT_METRICS 的 engine 为 null，
            // 引擎误报"宣称 engine=None"）。凡 `x or 默认` 一律经 PyTruthy 判后再取串。
            var mid = PyStrOrEmpty(m.GetValueOrDefault("id"), "?");
            var eng = PyStrOrEmpty(m.GetValueOrDefault("engine"));
            if (eng.Length > 0)
            {
                var at = eng.IndexOf(':');
                var mod = at < 0 ? eng : eng[..at];
                var fn = at < 0 ? "" : eng[(at + 1)..];
                if (mod != "quant_metrics" || !OutputTables.QuantMetricNames.Contains(fn))
                    issues.Add($"{mid}: 宣称 engine={eng}，但 core/quant_metrics 无该实现（宣称≠实现）");
            }
            if (PyStr(m.GetValueOrDefault("verifiable")) == "T4" && eng.Length == 0)
                issues.Add($"{mid}: 标 T4（可复算）却无 engine");
            var required = PyList(m.GetValueOrDefault("required_params")).Select(PyStr).ToList();
            if (PyTruthy(m.GetValueOrDefault("annual_factor_required")) && !required.Contains("annual_factor"))
                issues.Add($"{mid}: 需年化因子却未列入 required_params（口径四要素不全）");
        }
        var names = PyList(map.GetValueOrDefault("metrics")).Select(m => PyStr((m as Dictionary<string, object?>)?.GetValueOrDefault("id"))).ToHashSet(StringComparer.Ordinal);
        var expected = (map.GetValueOrDefault("annual_factors") as Dictionary<string, object?>)?.Keys.ToHashSet(StringComparer.Ordinal)
                       ?? new HashSet<string>(StringComparer.Ordinal);
        var want = new HashSet<string>(new[] { "daily", "weekly", "monthly" }, StringComparer.Ordinal);
        if (!expected.SetEquals(want))
            issues.Add($"annual_factors 键集应为 daily/weekly/monthly，实为 {PyReprList(expected.OrderBy(x => x, StringComparer.Ordinal))}");
        if (names.Count != PyList(map.GetValueOrDefault("metrics")).Count) issues.Add("metrics 存在重复 id");
        return issues;
    }

    private static List<string> CheckDomainSpec(string root, string rel)
    {
        var issues = CheckJson(root, rel);
        var (data, err) = ReadJson(Rel(root, rel));
        if (err.Length > 0 || data is not Dictionary<string, object?> map)
        {
            if (err.Length > 0) issues.Add(err);
            return issues;
        }
        var code = PyStrOrEmpty(map.GetValueOrDefault("code"));
        var subs = PyList(map.GetValueOrDefault("subdivisions"));
        if (subs.Count != 12) issues.Add($"细分条目应为 12 条，实为 {subs.Count}");
        for (var i = 0; i < subs.Count; i++)
        {
            if (subs[i] is not Dictionary<string, object?> s) continue;
            var want = $"{code}-{i + 1:D2}";
            if (PyStr(s.GetValueOrDefault("id")) != want)
                issues.Add($"第 {i + 1} 条 id 应为 {want}，实为 {PyScalar.PyRepr(s.GetValueOrDefault("id"))}");
            var anchor = PyStrOrEmpty(s.GetValueOrDefault("anchor"));
            if (!anchor.StartsWith("http://", StringComparison.Ordinal) && !anchor.StartsWith("https://", StringComparison.Ordinal))
                issues.Add($"{PyStr(s.GetValueOrDefault("id"))} 锚非绝对 URL");
            if (PyIntOf(s.GetValueOrDefault("anchor_status")) == 0)
                issues.Add($"{PyStr(s.GetValueOrDefault("id"))} 锚缺可达性实测值（不得假装可达：探不到记 0 并在锚表注明）");
        }
        return issues;
    }

    private static List<string> CheckDomainReport(string root, string rel)
    {
        var issues = CheckJson(root, rel);
        var (data, err) = ReadJson(Rel(root, rel));
        if (err.Length > 0 || data is not Dictionary<string, object?> map)
        {
            if (err.Length > 0) issues.Add(err);
            return issues;
        }
        var family = PyStrOrEmpty(map.GetValueOrDefault("family"));
        if (!OutputTables.DomainMetricFamilies.Contains(family))
            issues.Add($"度量族未在本仓引擎登记：{PyScalar.PyRepr(family)}（不得宣称可复算）");
        var metrics = map.GetValueOrDefault("metrics") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        if (PyStrOrEmpty(metrics.GetValueOrDefault("family")) != family) issues.Add("metrics.family 与报告 family 不一致");
        if (PyIntOf(map.GetValueOrDefault("sample_rows")) < 1) issues.Add("样例规模为 0（无样例即无口径值）");
        return issues;
    }

    private static List<string> CheckComboCert(string root, string rel)
    {
        var issues = CheckJson(root, rel);
        var (data, err) = ReadJson(Rel(root, rel));
        if (err.Length > 0 || data is not Dictionary<string, object?> map)
        {
            if (err.Length > 0) issues.Add(err);
            return issues;
        }
        using var schemaDoc = JsonIo.Parse(OutputTables.ComboCertSchemaJson);
        var schema = (Dictionary<string, object?>)PythonJson.ToGraph(schemaDoc.RootElement)!;
        var unsupported = new List<string>();
        var schemaErrors = JsonSchemaSubset.Check(map, schema, unsupported: unsupported);
        issues.AddRange(schemaErrors.Take(4).Select(e => $"证书不合 schema：{e}"));
        if (unsupported.Count > 0)
            issues.Add($"证书校验器遇不支持关键字：{PyReprList(unsupported.Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).Take(2))}");

        var packs = PyList(map.GetValueOrDefault("packs")).Select(PyStr).ToList();
        var extra = PyList(map.GetValueOrDefault("extra_modules")).Select(PyStr).ToList();
        if (packs.Count == 0 && extra.Count == 0)
        {
            issues.Add("复算失败：组合证书缺 packs/extra_modules（无输入即无复算）");
            return issues;
        }
        var result = Combinator.Build(root, packs, extra);
        if (!result.Legal) issues.Add("组合非法（五不变量未全成立）");
        if (!PyScalar.PyEquals(result.Certificate.GetValueOrDefault("digest"), map.GetValueOrDefault("digest")))
            issues.Add("证书摘要与实时复算不一致（组合输入已变）");
        return issues;
    }

    // ---------------------------------------------------------------- 小工具

    private static List<object?> PyList(object? v) => v as List<object?> ?? new List<object?>();

    private static bool PyTruthy(object? v) => v switch
    {
        null => false,
        bool b => b,
        string s => s.Length > 0,
        long l => l != 0,
        double d => d != 0,
        List<object?> list => list.Count > 0,
        Dictionary<string, object?> map => map.Count > 0,
        _ => true,
    };

    private static long PyIntOf(object? v) => v switch
    {
        long l => l,
        int i => i,
        double d => (long)d,
        bool b => b ? 1 : 0,
        string s => long.TryParse(s, NumberStyles.Integer, CultureInfo.InvariantCulture, out var parsed) ? parsed : 0,
        _ => 0,
    };

    private static string PyStr(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(CultureInfo.InvariantCulture),
        int i => i.ToString(CultureInfo.InvariantCulture),
        double d => PythonJson.PyFloatRepr(d),
        _ => PyScalar.PyRepr(v),
    };

    /// <summary>Python <c>x or fallback</c> 的 **str** 口径（假值走 fallback，不经过 <c>str(None)</c>）。</summary>
    private static string PyStrOrEmpty(object? v, string fallback = "") =>
        PyTruthy(v) ? PyStr(v) : fallback;

    private static string PySlice(string s, int maxCodePoints) => PyScalar.PySlice(s, maxCodePoints);

    private static string PyReprList(IEnumerable<string> items) =>
        "[" + string.Join(", ", items.Select(PyScalar.PyRepr)) + "]";

    private static string PyReprTuple(object? item) => "(" + PyScalar.PyRepr(item) + ",)";

    // ---------------------------------------------------------------- 包级产出清单 / 门禁合成

    /// <summary><c>_pack_dirs</c>：community 下**声明了 outputs/INDEX.json** 的包目录名（排序）。</summary>
    public static List<string> PackDirs(string root)
    {
        var baseDir = Path.Combine(root, "community");
        if (!Directory.Exists(baseDir)) return new List<string>();
        return Directory.GetDirectories(baseDir)
            .Where(d => File.Exists(Path.Combine(d, "outputs", "INDEX.json")))
            .Select(Path.GetFileName).Where(n => n is not null).Select(n => n!)
            .OrderBy(n => n, StringComparer.Ordinal).ToList();
    }

    /// <summary>形态清单自检：结构合法 + 类别/档位在册 + id 唯一 + 可达性实证齐备。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) RegistryVerify(string root)
    {
        var issues = new List<string>();
        var registry = LoadRegistry(root);
        if (registry.Count == 0)
            return (new List<string> { $"{RegistryRel} 缺失或不可解析（形态清单是真源）" },
                new Dictionary<string, object?>(StringComparer.Ordinal));
        if (PyStrOrEmpty(registry.GetValueOrDefault("schema")) != "nf-output-forms/1")
            issues.Add($"schema 应为 nf-output-forms/1，实为 {PyScalar.PyRepr(registry.GetValueOrDefault("schema"))}");
        var cats = PyList(registry.GetValueOrDefault("categories"));
        var catIds = cats.OfType<Dictionary<string, object?>>()
            .Select(c => PyStrOrEmpty(c.GetValueOrDefault("id"))).Where(x => x.Length > 0)
            .ToHashSet(StringComparer.Ordinal);
        if (catIds.Count == 0) issues.Add("categories 为空（形态必须有类别归属）");
        foreach (var c in cats)
        {
            if (c is not Dictionary<string, object?> cm) continue;
            if (PyStrOrEmpty(cm.GetValueOrDefault("id")).Length == 0
                || PyStrOrEmpty(cm.GetValueOrDefault("name")).Length == 0)
                issues.Add($"categories 条目缺 id/name：{PyScalar.PyRepr(c)}");
        }
        var forms = PyList(registry.GetValueOrDefault("forms"));
        var seen = new HashSet<string>(StringComparer.Ordinal);
        var perCat = new Dictionary<string, long>(StringComparer.Ordinal);
        var perTier = new Dictionary<string, long>(StringComparer.Ordinal);
        var perStatus = new Dictionary<string, long>(StringComparer.Ordinal);
        var unreachable = 0L;
        foreach (var f in forms)
        {
            if (f is not Dictionary<string, object?> fm)
            {
                issues.Add($"forms 条目非对象：{PyScalar.PyRepr(f)}");
                continue;
            }
            var fid = PyStrOrEmpty(fm.GetValueOrDefault("id"));
            if (fid.Length == 0)
            {
                issues.Add($"forms 条目缺 id：{PyScalar.PyRepr(f)}");
                continue;
            }
            if (!seen.Add(fid)) issues.Add($"形态 id 重复：{fid}");
            var category = PyStrOrEmpty(fm.GetValueOrDefault("category"));
            if (!catIds.Contains(category)) issues.Add($"{fid} 类别未在册：{PyScalar.PyRepr(fm.GetValueOrDefault("category"))}");
            var tier = PyStrOrEmpty(fm.GetValueOrDefault("tier"));
            if (!Tiers.Contains(tier)) issues.Add($"{fid} 档位非法：{PyScalar.PyRepr(fm.GetValueOrDefault("tier"))}（预期 {string.Join("/", Tiers)}）");
            var status = PyStrOrEmpty(fm.GetValueOrDefault("status"));
            if (!Statuses.Contains(status)) issues.Add($"{fid} 状态非法：{PyScalar.PyRepr(fm.GetValueOrDefault("status"))}");
            var spec = fm.GetValueOrDefault("spec") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            if (status != "unfit" && PyStrOrEmpty(spec.GetValueOrDefault("uri")).Length == 0)
                issues.Add($"{fid} 缺规范入口 spec.uri（不适面才可空）");
            var evidence = fm.GetValueOrDefault("evidence") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            if (!evidence.ContainsKey("reachable"))
                issues.Add($"{fid} 缺可达性实证 evidence.reachable（不伪造：查不到也要记 false）");
            else if (evidence.GetValueOrDefault("reachable") is bool rb && !rb)
                unreachable++;
            perCat[category] = perCat.GetValueOrDefault(category) + 1;
            perTier[tier] = perTier.GetValueOrDefault(tier) + 1;
            perStatus[status] = perStatus.GetValueOrDefault(status) + 1;
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["forms"] = (long)forms.Count, ["categories"] = (long)catIds.Count,
            ["by_category"] = perCat.ToDictionary(kv => kv.Key, kv => (object?)kv.Value, StringComparer.Ordinal),
            ["by_tier"] = perTier.ToDictionary(kv => kv.Key, kv => (object?)kv.Value, StringComparer.Ordinal),
            ["by_status"] = perStatus.ToDictionary(kv => kv.Key, kv => (object?)kv.Value, StringComparer.Ordinal),
            ["unreachable"] = unreachable,
        });
    }

    /// <summary>机验率与功能面计量（不改盘；基线比对见 <see cref="BaselineVerify"/>）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Meter(string root)
    {
        var packages = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var pkg in PackDirs(root))
        {
            var (idx, _) = ReadJson(Rel(root, $"community/{pkg}/{IndexRel}"));
            var entries = PyList((idx as Dictionary<string, object?>)?.GetValueOrDefault("outputs"));
            var mv = entries.OfType<Dictionary<string, object?>>()
                .Where(e => Tiers.Skip(2).Contains(PyStrOrEmpty(e.GetValueOrDefault("tier")))).ToList();
            var fnFaces = entries.OfType<Dictionary<string, object?>>()
                .Where(e => PyStrOrEmpty(e.GetValueOrDefault("tier")) == "T4").ToList();
            var assetsDir = Path.Combine(root, "community", pkg, "assets");
            var prose = Directory.Exists(assetsDir)
                ? Directory.GetFiles(assetsDir, "*.md").Select(Path.GetFileName)
                    .Where(n => n is not null && n != "README.md").ToList()
                : new List<string?>();
            var denom = mv.Count + prose.Count;
            packages[pkg] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["machine_verifiable"] = (long)mv.Count,
                ["functional"] = (long)fnFaces.Count,
                ["prose_assets"] = (long)prose.Count,
                ["machine_verifiable_ratio"] = denom > 0 ? PyScalar.PyRound((double)mv.Count / denom, 4) : 0.0,
                ["roles"] = Count(entries.OfType<Dictionary<string, object?>>()
                    .Select(e => new Dictionary<string, object?>(StringComparer.Ordinal)
                    { ["r"] = e.GetValueOrDefault("role") }), "r"),
                ["tiers"] = Count(entries.OfType<Dictionary<string, object?>>()
                    .Select(e => new Dictionary<string, object?>(StringComparer.Ordinal)
                    { ["t"] = e.GetValueOrDefault("tier") }), "t"),
            };
        }
        var totals = new Dictionary<string, object?>(StringComparer.Ordinal);
        if (packages.Count > 0)
        {
            long Mv(Dictionary<string, object?> p) => Convert.ToInt64(p["machine_verifiable"]);
            long Prose(Dictionary<string, object?> p) => Convert.ToInt64(p["prose_assets"]);
            var values = packages.Values.Cast<Dictionary<string, object?>>().ToList();
            totals = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["machine_verifiable"] = values.Sum(Mv),
                ["functional"] = values.Sum(p => Convert.ToInt64(p["functional"])),
                ["prose_assets"] = values.Sum(Prose),
                ["machine_verifiable_ratio"] = PyScalar.PyRound(
                    (double)values.Sum(Mv) / Math.Max(1, values.Sum(p => Mv(p) + Prose(p))), 4),
            };
        }
        return (new List<string>(), new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["packages"] = packages, ["totals"] = totals,
        });
    }

    /// <summary>机验率基线（可重签）：低于基线即 FAIL——防「新增产出又退回散文」。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) BaselineVerify(string root)
    {
        var issues = new List<string>();
        var (baseDoc, err) = ReadJson(Rel(root, BaselineRel));
        var (_, stats) = Meter(root);
        if (err.Length > 0)
            return (new List<string> { $"{BaselineRel} 缺失或不可解析（{err}；重签：nf output meter --write）" }, stats);
        var prev = (baseDoc as Dictionary<string, object?>)?.GetValueOrDefault("packages") as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var (pkg, cur) in (stats.GetValueOrDefault("packages") as Dictionary<string, object?>
                                    ?? new Dictionary<string, object?>(StringComparer.Ordinal)))
        {
            if (cur is not Dictionary<string, object?> c) continue;
            if (prev.GetValueOrDefault(pkg) is not Dictionary<string, object?> old) continue;
            var oldMv = PyLong(old.GetValueOrDefault("machine_verifiable"));
            var curMv = Convert.ToInt64(c["machine_verifiable"]);
            if (curMv < oldMv)
                issues.Add($"{pkg} 机验产出面回退：{oldMv} → {curMv}（基线 {BaselineRel}）");
            var oldFn = PyLong(old.GetValueOrDefault("functional"));
            var curFn = Convert.ToInt64(c["functional"]);
            if (curFn < oldFn) issues.Add($"{pkg} 功能面（T4 可复算）回退：{oldFn} → {curFn}");
        }
        stats["baseline"] = baseDoc is not null;
        return (issues, stats);
    }

    /// <summary>check32 子扫描入口：形态清单 + 包级产出清单 + 机验率基线三合一。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var (regIssues, regStats) = RegistryVerify(root);
        issues.AddRange(regIssues.Select(i => $"形态清单: {i}"));
        var (idxIssues, idxStats) = IndexVerify(root);
        issues.AddRange(idxIssues.Select(i => $"包级产出面: {i}"));
        var (baseIssues, baseStats) = BaselineVerify(root);
        issues.AddRange(baseIssues.Select(i => $"机验率基线: {i}"));
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["registry"] = regStats, ["index"] = idxStats,
            ["meter"] = (baseStats.GetValueOrDefault("packages") as Dictionary<string, object?>)
                       ?? new Dictionary<string, object?>(StringComparer.Ordinal),
        });
    }

    /// <summary>包级产出清单机检：声明存在 / 形态与档位属实 / schema 校验 / 双源一致 / T4 复算。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) IndexVerify(string root)
    {
        var issues = new List<string>();
        var rows = new List<Dictionary<string, object?>>();
        foreach (var pkg in PackDirs(root))
        {
            var rel = $"community/{pkg}/{IndexRel}";
            var (idx, err) = ReadJson(Rel(root, rel));
            if (err.Length > 0) { issues.Add($"{rel}: {err}"); continue; }
            if (idx is not Dictionary<string, object?> index) continue;
            if (PyStrOrEmpty(index.GetValueOrDefault("schema")) != "nf-output-index/1")
                issues.Add($"{rel}: schema 应为 nf-output-index/1");
            if (PyStrOrEmpty(index.GetValueOrDefault("package")) != pkg)
                issues.Add($"{rel}: package 字段 {PyScalar.PyRepr(index.GetValueOrDefault("package"))} ≠ 包目录名 {PyScalar.PyRepr(pkg)}");
            foreach (var entry in PyList(index.GetValueOrDefault("outputs")).OfType<Dictionary<string, object?>>())
            {
                var path = PyStrOrEmpty(entry.GetValueOrDefault("path"));
                var form = PyStrOrEmpty(entry.GetValueOrDefault("form"));
                var tier = PyStrOrEmpty(entry.GetValueOrDefault("tier"));
                if (path.Length == 0) { issues.Add($"{rel}: outputs 条目缺 path"); continue; }
                if (!Tiers.Contains(tier)) { issues.Add($"{rel}: {path} 档位非法 {PyScalar.PyRepr(entry.GetValueOrDefault("tier"))}"); continue; }
                var fullRel = $"community/{pkg}/{path}";
                if (!File.Exists(Rel(root, fullRel))) { issues.Add($"{rel}: 声明产出面不存在 {path}"); continue; }
                var (gotForm, gotTier) = Detect(root, fullRel);
                if (form.Length > 0 && form != gotForm) issues.Add($"{rel}: {path} 声明形态 {form}，实测 {gotForm}");
                if (Array.IndexOf(Tiers, tier) > Array.IndexOf(Tiers, gotTier))
                    issues.Add($"{rel}: {path} 声明档位 {tier} 超出本仓可判上限 {gotTier}");
                var useForm = form.Length > 0 ? form : gotForm;
                // `_FORM_CHECK.get(form or got_form)`：无校验器的形态返回空表（不是"没判"）
                issues.AddRange(Check(root, fullRel, useForm).Select(s => $"{rel}: {path} {s}"));
                var schRel = PyStrOrEmpty(entry.GetValueOrDefault("schema"));
                if (schRel.Length > 0)
                {
                    var (schemaDoc, serr) = ReadJson(Rel(root, $"community/{pkg}/{schRel}"));
                    if (serr.Length > 0) issues.Add($"{rel}: {path} schema {serr}");
                    else if (schemaDoc is Dictionary<string, object?> schemaMap)
                    {
                        var (inst, ierr) = ReadJson(Rel(root, fullRel));
                        if (ierr.Length > 0) issues.Add($"{rel}: {path} {ierr}");
                        else
                        {
                            var unsupported = new List<string>();
                            var errs = JsonSchemaSubset.Check(inst, schemaMap, unsupported: unsupported);
                            issues.AddRange(errs.Take(8).Select(e => $"{rel}: {path} schema 不符 {e}"));
                        }
                    }
                }
                if (entry.GetValueOrDefault("dual_source") is Dictionary<string, object?> ds)
                    issues.AddRange(DualSourceCheck(root, pkg, path, ds).Select(m => $"{rel}: {path} {m}"));
                if (entry.GetValueOrDefault("recompute") is Dictionary<string, object?>)
                {
                    var withPkg = new Dictionary<string, object?>(entry, StringComparer.Ordinal) { ["_pkg"] = pkg };
                    issues.AddRange(RecomputeEntry(root, withPkg).Issues.Select(s => $"{rel}: {s}"));
                }
                else if (tier == "T4")
                {
                    issues.Add($"{rel}: {path} 声明 T4（可复算）却无 recompute 声明");
                }
                rows.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["package"] = pkg, ["path"] = path, ["form"] = useForm,
                    ["tier"] = tier, ["role"] = PyStrOrEmpty(entry.GetValueOrDefault("role")),
                });
            }
        }
        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["packages"] = (long)PackDirs(root).Count, ["outputs"] = (long)rows.Count,
            ["by_role"] = Count(rows, "role"), ["by_tier"] = Count(rows, "tier"),
            ["by_form"] = Count(rows, "form"),
        });
    }

    /// <summary>T4 复算：生成器重算 → 与在盘产物比对（JSON 逐字段 / 文本逐字节）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) RecomputeEntry(
        string root, Dictionary<string, object?> entry)
    {
        var outRel = PyStrOrEmpty(entry.GetValueOrDefault("path"));
        var gid = OutputGenerators.GenId(entry);
        if (!OutputGenerators.Registered(gid))
            return (new List<string> { $"{outRel} 声明复算 {PyScalar.PyRepr(gid)} 无对应引擎（不得假装可复算）" },
                new Dictionary<string, object?>(StringComparer.Ordinal));
        var (fresh, errs) = OutputGenerators.Generate(root, entry);
        if (fresh is null)
            return (errs.Select(e => $"{outRel}: {e}").ToList(), new Dictionary<string, object?>(StringComparer.Ordinal));
        var diskPath = Rel(root, OutputGenerators.PkgRel(entry, outRel));
        var onDisk = File.ReadAllBytes(diskPath);
        var diffs = new List<string>();
        if (fresh is string text)
        {
            if (!onDisk.SequenceEqual(Encoding.UTF8.GetBytes(OutputGenerators.Dump(text))))
                diffs.Add("文本面与复算不一致（逐字节）");
        }
        else
        {
            string decoded;
            try
            {
                decoded = StrictUtf8.GetString(onDisk);
                using var doc = JsonIo.Parse(decoded);
                var declared = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
                               ?? new Dictionary<string, object?>(StringComparer.Ordinal);
                var subset = new Dictionary<string, object?>(StringComparer.Ordinal);
                if (fresh is Dictionary<string, object?> freshMap)
                    foreach (var key in freshMap.Keys) subset[key] = declared.GetValueOrDefault(key);
                diffs = DeepDiff(fresh, subset);
            }
            catch (Exception exc) when (exc is JsonException or System.Text.DecoderFallbackException)
            {
                return (new List<string> { $"{outRel}: 在盘产物不可解析 {exc.Message}" },
                    new Dictionary<string, object?>(StringComparer.Ordinal));
            }
            if (onDisk.AsSpan().IndexOf("\r\n"u8) >= 0)
                diffs.Add("在盘产物含 CRLF（仓库 EOL 契约 = LF）");
        }
        return (diffs.Select(d => $"{outRel}: 复算与在盘不一致 {d}").ToList(),
            new Dictionary<string, object?> { ["diff"] = (long)diffs.Count });
    }

    /// <summary>渲染包内声明的产出面（数据 / 图表）：<c>--write</c> 才落盘；缺生成器即报错不静默。</summary>
    public static (List<string> Issues, List<Dictionary<string, object?>> Rows) RenderOutputs(
        string root, string package = "", bool write = false)
    {
        var issues = new List<string>();
        var rows = new List<Dictionary<string, object?>>();
        foreach (var pkg in PackDirs(root))
        {
            if (package.Length > 0 && pkg != package) continue;
            var (idx, err) = ReadJson(Rel(root, $"community/{pkg}/{IndexRel}"));
            if (err.Length > 0) { issues.Add($"{pkg}: {err}"); continue; }
            foreach (var entry in PyList((idx as Dictionary<string, object?>)?.GetValueOrDefault("outputs"))
                         .OfType<Dictionary<string, object?>>())
            {
                var gid = OutputGenerators.GenId(entry);
                if (gid.Length == 0) continue;
                if (!OutputGenerators.Registered(gid))
                {
                    issues.Add($"{pkg}/{PyStrOrEmpty(entry.GetValueOrDefault("path"))}: 未登记生成器 {PyScalar.PyRepr(gid)}");
                    continue;
                }
                var withPkg = new Dictionary<string, object?>(entry, StringComparer.Ordinal) { ["_pkg"] = pkg };
                var (value, errs) = OutputGenerators.Generate(root, withPkg);
                if (value is null)
                {
                    issues.AddRange(errs.Select(e => $"{pkg}/{PyStrOrEmpty(entry.GetValueOrDefault("path"))}: {e}"));
                    continue;
                }
                var dest = Rel(root, $"community/{pkg}/{PyStrOrEmpty(entry.GetValueOrDefault("path"))}");
                var text = OutputGenerators.Dump(value);
                var bytes = Encoding.UTF8.GetBytes(text);
                var changed = !File.Exists(dest) || !File.ReadAllBytes(dest).SequenceEqual(bytes);
                if (write && changed)
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(dest)!);
                    File.WriteAllBytes(dest, bytes);
                }
                rows.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["package"] = pkg, ["path"] = PyStrOrEmpty(entry.GetValueOrDefault("path")),
                    ["generator"] = gid, ["changed"] = changed,
                    ["written"] = write && changed,
                });
            }
        }
        return (issues, rows);
    }

    /// <summary>双源一致：数据面 vs 散文面（键集必须互为子集）。</summary>
    private static List<string> DualSourceCheck(string root, string pkg, string path,
        Dictionary<string, object?> ds)
    {
        var mdRel = PyStrOrEmpty(ds.GetValueOrDefault("markdown"));
        var pattern = PyStrOrEmpty(ds.GetValueOrDefault("key_pattern"));
        if (pattern.Length == 0) pattern = "`([A-Z][A-Z0-9_]{2,})`";
        var mdPath = Rel(root, $"community/{pkg}/{mdRel}");
        if (!File.Exists(mdPath)) return new List<string> { $"双源对照件不存在：{mdRel}" };
        var regex = new System.Text.RegularExpressions.Regex(pattern, RegexOptions.CultureInvariant);
        var mdKeys = regex.Matches(ReadText(mdPath)).Select(m => m.Groups[1].Value)
            .ToHashSet(StringComparer.Ordinal);
        foreach (var drop in PyList(ds.GetValueOrDefault("exclude"))) mdKeys.Remove(PyStr(drop));
        var (data, err) = ReadJson(Rel(root, $"community/{pkg}/{path}"));
        if (err.Length > 0) return new List<string> { err };
        var field = PyStrOrEmpty(ds.GetValueOrDefault("field"));
        if (field.Length == 0) field = "id";
        var dataKeys = new HashSet<string>(StringComparer.Ordinal);
        if (data is Dictionary<string, object?> map)
            foreach (var value in map.Values)
                foreach (var item in PyList(value).OfType<Dictionary<string, object?>>())
                    if (PyTruthy(item.GetValueOrDefault(field)))
                        dataKeys.Add(PyStr(item.GetValueOrDefault(field)));
        var onlyMd = mdKeys.Except(dataKeys).OrderBy(x => x, StringComparer.Ordinal).ToList();
        var onlyData = dataKeys.Except(mdKeys).OrderBy(x => x, StringComparer.Ordinal).ToList();
        var output = new List<string>();
        if (onlyMd.Count > 0) output.Add($"双源不一致：散文面独有键 {ReprList(onlyMd.Take(6))}");
        if (onlyData.Count > 0) output.Add($"双源不一致：数据面独有键 {ReprList(onlyData.Take(6))}");
        return output;
    }

    private static Dictionary<string, object?> Count(IEnumerable<Dictionary<string, object?>> rows, string key)
    {
        var output = new Dictionary<string, long>(StringComparer.Ordinal);
        foreach (var row in rows)
        {
            var k = PyStr(row.GetValueOrDefault(key));
            output[k] = output.GetValueOrDefault(k) + 1;
        }
        return output.OrderBy(kv => kv.Key, StringComparer.Ordinal)
            .ToDictionary(kv => kv.Key, kv => (object?)kv.Value, StringComparer.Ordinal);
    }

    /// <summary>复刻 <c>_deep_diff</c>：字典按并集键序、列表按下标、数值按 1e-9 容差。</summary>
    public static List<string> DeepDiff(object? a, object? b, string path = "$", List<string>? output = null)
    {
        output ??= new List<string>();
        if (a is Dictionary<string, object?> ma && b is Dictionary<string, object?> mb)
        {
            foreach (var k in ma.Keys.Union(mb.Keys).OrderBy(x => x, StringComparer.Ordinal))
            {
                if (!ma.ContainsKey(k)) output.Add($"{path}.{k} 仅存于在盘");
                else if (!mb.ContainsKey(k)) output.Add($"{path}.{k} 仅存于复算");
                else DeepDiff(ma[k], mb[k], $"{path}.{k}", output);
            }
        }
        else if (a is List<object?> la && b is List<object?> lb)
        {
            if (la.Count != lb.Count) output.Add($"{path} 长度 {la.Count}≠{lb.Count}");
            for (var i = 0; i < Math.Min(la.Count, lb.Count); i++) DeepDiff(la[i], lb[i], $"{path}[{i}]", output);
        }
        else if (a is long or int or double && b is long or int or double && a is not bool && b is not bool)
        {
            var da = Convert.ToDouble(a, System.Globalization.CultureInfo.InvariantCulture);
            var db = Convert.ToDouble(b, System.Globalization.CultureInfo.InvariantCulture);
            if (Math.Abs(da - db) > 1e-9)
                output.Add($"{path} 数值 {PyScalar.PyRepr(a)}≠{PyScalar.PyRepr(b)}");
        }
        else if (!PyScalar.PyEquals(a, b))
        {
            output.Add($"{path} {PyScalar.PyRepr(a)}≠{PyScalar.PyRepr(b)}");
        }
        return output;
    }

    private static long PyLong(object? v) => v switch
    {
        long l => l,
        int i => i,
        double d => (long)Math.Truncate(d),
        _ => 0L,
    };

    private static string ReprList(IEnumerable<string> items) =>
        "[" + string.Join(", ", items.Select(PyScalar.PyRepr)) + "]";
}
