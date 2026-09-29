using System.Globalization;
using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/workloop.py</c>（**check33 第 16 条 · 构建回路**）：决策模型挑活 → 工单只落内部档案
/// → worker 落笔 → 门禁验收。本件移植的是 check33 真正消费的**离线判据面**：<c>state</c> /
/// <c>items</c> / <c>capability_gaps</c> / <c>questions</c> / <c>plan</c>（stub 适配器）与 <c>scan</c>。
///
/// **本件不移植的写面**（真源同类：`workloop.write_order` / `close` 写 `.rivet/` 内部档案）——
/// 只读门不落盘；`scan` 里对「工单只落内部档案」的判据（目录前缀断言的**常量**）仍照抄。
/// **端口边界**：`plan` 的端点类适配器（systemone-http / openai-json）只保留 fail-closed 分支——
/// 与 <see cref="DecisionLayer"/> 同一条边界（引擎不发起外呼）。
/// </summary>
public static class Workloop
{
    public const string BacklogRel = "protocol/type_backlog.json";
    public const string AdvisoryRel = "protocol/pipeline_advisory.json";
    public static readonly (string Name, string Rel)[] Sources =
    {
        ("type-backlog", BacklogRel), ("pipeline-advisory", AdvisoryRel),
    };
    public static readonly string[] Families = { "extend", "deepen", "innovate" };
    public const string OrderDir = ".rivet/private_archive/work_orders";
    public const string ArchivePrefix = ".rivet/";

    /// <summary>真源里「只读治理面」白名单（顺序 = 真源元组序，用于 ∩ cmds 的过滤）。</summary>
    public static readonly string[] ReadonlyGovernance =
    {
        "decisions", "handover", "postmortem", "audit", "transparency", "score",
        "conformance", "assertions", "model", "cognition", "events", "rfc",
        "endpoint", "interop", "workloop", "decide", "explain", "related",
        "who-refers", "impact",
    };

    /// <summary>真源已接 MCP 的只读面（`covered` 集合）。</summary>
    public static readonly string[] Covered = { "receipts", "endpoint", "driver", "patterns", "knowledge" };

    private static readonly Regex SubParserRe =
        new(@"sub\.add_parser\(\s*""([a-z0-9-]+)""", RegexOptions.Compiled);
    private static readonly Regex KindChoicesRe =
        new(@"add_argument\(\s*""--kind"",\s*default=""[a-z]+"",\s*choices=\[([^\]]+)\]", RegexOptions.Compiled);
    private static readonly Regex KindItemRe = new(@"""([a-z]+)""", RegexOptions.Compiled);

    public sealed record Result(List<string> Issues, Dictionary<string, object?> Stats)
    {
        public bool Ok => Issues.Count == 0;

        /// <summary>check33 第 16 条的框法：issues 逐条 <c>[FAIL] 构建回路：…</c>，末行 <c>构建回路：&lt;summary&gt;</c>。</summary>
        public List<string> Log
        {
            get
            {
                var lines = Issues.Select(issue => "[FAIL] 构建回路：" + issue).ToList();
                lines.Add("构建回路：" + Workloop.Summary(Stats));
                return lines;
            }
        }

        public string LogDigest => ExitFaces.Digest32(Log);
    }

    public static Dictionary<string, object?> Read(string root, string rel)
    {
        var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return new Dictionary<string, object?>(StringComparer.Ordinal);
        try
        {
            using var doc = JsonIo.ReadFile(path);
            return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        }
        catch (Exception)
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal);
        }
    }

    /// <summary>回路状态快照（只读公开声明，确定性）。</summary>
    public static Dictionary<string, object?> State(string root)
    {
        var backlog = Read(root, BacklogRel);
        var advisory = Read(root, AdvisoryRel);
        var decl = DecisionLayer.LoadDecl(root);
        var pulled = new List<object?>();
        foreach (var candidate in PyListOfMaps(decl.GetValueOrDefault("candidates")))
        {
            if (candidate.GetValueOrDefault("pulled") is true) pulled.Add(candidate.GetValueOrDefault("id"));
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["untyped_fields"] = (long)PyIntOr(backlog.GetValueOrDefault("count"),
                ObjList(backlog.GetValueOrDefault("fields")).Count),
            ["advisories"] = (long)PyIntOr(advisory.GetValueOrDefault("count"),
                ObjList(advisory.GetValueOrDefault("items")).Count),
            ["advisory_by_category"] = advisory.GetValueOrDefault("counts") as Dictionary<string, object?>
                                      ?? new Dictionary<string, object?>(StringComparer.Ordinal),
            ["candidates_pulled"] = pulled,
            ["adapters"] = DecisionLayer.AdapterIds(root),
        };
    }

    /// <summary>工作项清单（公开声明件 + 能力缺口候选）。</summary>
    public static List<Dictionary<string, object?>> Items(string root, long limit = 0, string source = "")
    {
        var out0 = new List<Dictionary<string, object?>>();
        var backlog = Read(root, BacklogRel);
        var index = 0;
        foreach (var f in PyListOfMaps(backlog.GetValueOrDefault("fields")))
        {
            index++;
            var ev = PyStr(f.GetValueOrDefault("event"));
            var fld = PyStr(f.GetValueOrDefault("field"));
            out0.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = $"TB-{index.ToString("D3", CultureInfo.InvariantCulture)}:{ev}.{fld}",
                ["source"] = "type-backlog", ["kind"] = "type-evidence",
                ["title"] = $"补类型证据：{ev}.{fld}",
                ["detail"] = PyTruthy(f.GetValueOrDefault("note"))
                    ? PyStr(f.GetValueOrDefault("note")) : "事件载荷字段类型待核",
                ["where_hint"] = $"事件发布方模块正文（{(ev.Length > 0 ? ev : "?")} 的载荷表）",
                ["done_when"] = new List<object?> { "模块正文补出该字段的类型证据", "nf lint / verify 全绿" },
            });
        }
        var advisory = Read(root, AdvisoryRel);
        index = 0;
        foreach (var a in PyListOfMaps(advisory.GetValueOrDefault("items")))
        {
            index++;
            var pipeline = PyStr(a.GetValueOrDefault("pipeline"));
            var category = PyStr(a.GetValueOrDefault("category"));
            out0.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = $"PA-{index.ToString("D3", CultureInfo.InvariantCulture)}:{(pipeline.Length > 0 ? pipeline : "?")}",
                ["source"] = "pipeline-advisory", ["kind"] = "advisory-shrink",
                ["title"] = $"收敛 advisory：{(category.Length > 0 ? category : "?")}"
                            + $"（{(pipeline.Length > 0 ? pipeline : "?")}）",
                ["detail"] = PyStr(a.GetValueOrDefault("detail")),
                ["where_hint"] = "对应管线声明与所涉模块的 references/事件声明",
                ["done_when"] = new List<object?>
                {
                    "该类别计数下降或转为在册机制", "nf pipeline dryrun --all 零 hard",
                },
            });
        }
        out0.AddRange(CapabilityGaps(root));
        var filtered = source.Length > 0
            ? out0.Where(it => PyStr(it.GetValueOrDefault("source")) == source).ToList()
            : out0;
        return limit > 0 ? filtered.Take((int)limit).ToList() : filtered;
    }

    /// <summary>现有功能的延伸 / 深化 / 创新候选（**全部机械派生**，每条附缺口事实）。</summary>
    public static List<Dictionary<string, object?>> CapabilityGaps(string root)
    {
        var out0 = new List<Dictionary<string, object?>>();
        var cmds = new List<string>();
        var nfPath = Path.Combine(root, "scripts", "nf.py");
        var nfText = "";
        if (File.Exists(nfPath))
        {
            nfText = File.ReadAllText(nfPath, new System.Text.UTF8Encoding(false, throwOnInvalidBytes: true));
            cmds = SubParserRe.Matches(nfText).Select(m => m.Groups[1].Value)
                .Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToList();
        }
        var tools = McpServer.ToolNames.Count;
        var readonlyGovernance = cmds.Where(c => Array.IndexOf(ReadonlyGovernance, c) >= 0).ToList();
        var missing = readonlyGovernance.Where(c => Array.IndexOf(Covered, c) < 0).ToList();
        if (missing.Count > 0)
        {
            out0.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = "CAP-EXTEND-MCP-READONLY", ["source"] = "capability-gaps",
                ["family"] = "extend", ["kind"] = "capability-extension",
                ["title"] = $"把只读治理面接入 MCP（当前 {missing.Count} 个只读面未暴露，工具仅 {tools} 个）",
                ["detail"] = "未接 MCP 的只读面：" + string.Join("、", missing.Take(8)),
                ["where_hint"] = "core/mcp_runtime.py（TOOL_DEFS + 只读白名单）+ protocol/mcp_package.json 登记",
                ["done_when"] = new List<object?>
                {
                    "新增工具逐名与实现一致", "check33 新面扫描含逐名一致断言", "MCP 工具仍全只读（无写路径）",
                },
            });
        }

        var interopDecl = Interop.Kinds.Select(k => k.Id).OrderBy(x => x, StringComparer.Ordinal).ToList();
        var cliKinds = new List<string>();
        if (cmds.Count > 0)
        {
            var match = KindChoicesRe.Match(nfText);
            if (match.Success)
            {
                cliKinds = KindItemRe.Matches(match.Groups[1].Value).Select(m => m.Groups[1].Value)
                    .Distinct(StringComparer.Ordinal).OrderBy(x => x, StringComparer.Ordinal).ToList();
            }
        }
        if (interopDecl.Count > 0 && cliKinds.Count > 0
            && !cliKinds.SequenceEqual(interopDecl, StringComparer.Ordinal))
        {
            var gap = interopDecl.Except(cliKinds, StringComparer.Ordinal)
                .OrderBy(x => x, StringComparer.Ordinal).ToList();
            out0.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = "CAP-DEEPEN-DECL-CONSISTENCY", ["source"] = "capability-gaps",
                ["family"] = "deepen", ["kind"] = "judgement-deepening",
                ["title"] = $"加「CLI 可选值 ↔ 声明件」一致性判据（已抓到实例：缺 {string.Join("、", gap)}）",
                ["detail"] = $"interop CLI kinds={PyScalar.PyRepr(cliKinds.Cast<object?>().ToList())}"
                             + $" / 导出面声明={PyScalar.PyRepr(interopDecl.Cast<object?>().ToList())}"
                             + " —— 同类漏同步此前已发生一次（slsa/a2a），属可机检的判据缺口",
                ["where_hint"] = "scripts/nf.py 的 choices + core/interop_export.KINDS（判据落 check33）",
                ["done_when"] = new List<object?>
                {
                    "修掉实例差异", "新增通用判据：CLI choices ⊆ 声明件（或相等）", "负例单测：故意漏一个 kind 应被抓",
                },
            });
        }

        if (!interopDecl.Contains("decisions", StringComparer.Ordinal))
        {
            out0.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = "CAP-INNOVATE-DECISION-INTEROP", ["source"] = "capability-gaps",
                ["family"] = "innovate", ["kind"] = "capability-innovation",
                ["title"] = "把决策层/工单面接进互操作导出（决策可被外部工具链读）",
                ["detail"] = "现状：decision_layer.json 与 workloop 工单都在仓内，互操作导出面"
                             + $"（{interopDecl.Count} 面）尚无「决策面」投影；外部工具链读不到「谁按什么概率决定了什么」",
                ["where_hint"] = "core/interop_export.py 新增 kind（纯派生自 decision_layer.json + 公开裁决索引）",
                ["done_when"] = new List<object?>
                {
                    "新导出面纯派生（不改真源）", "外部 schema 校验口径成立或如实记 no-schema",
                    "check33 入仓面逐字节一致",
                },
            });
        }
        return out0;
    }

    /// <summary>组类型化问题：挑活（choice）+ 每项风险（score）+ 每项「能否安全做」（noul）。</summary>
    public static Dictionary<string, object?> Questions(string root, long top = 5, string source = "")
    {
        var q = new Dictionary<string, object?>(StringComparer.Ordinal);
        var picked = Items(root, Math.Max(1, top), source);
        if (picked.Count == 0) return q;
        q["family"] = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["type"] = "choice",
            ["instructions"] = "这一轮要哪一类工作（extend 加面 / deepen 深化判据 / innovate 新组合）",
            ["options"] = Families.Cast<object?>().ToList(),
        };
        q["next_item"] = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["type"] = "choice",
            ["instructions"] = "选下一个要推进的工作项（优先小改动面、可门禁验收）",
            ["options"] = picked.Select(it => it["id"]).ToList(),
        };
        foreach (var it in picked)
        {
            var title = PyStr(it.GetValueOrDefault("title"));
            q[$"risk:{it["id"]}"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["type"] = "score", ["levels"] = new List<object?> { "低", "中", "高" },
                ["instructions"] = $"预估改动面风险：{title}",
            };
            q[$"gate_safe:{it["id"]}"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["type"] = "noul",
                ["true_hints"] = new List<object?> { "正文", "注释", "文档", "提示" },
                ["instructions"] = $"是否可在不触碰回执锚定件的条件下完成：{title}",
            };
        }
        return q;
    }

    /// <summary>工单号：<c>WO-</c> + <c>sha256(json({chosen, state}, sort_keys, 紧凑))[:12]</c>。</summary>
    public static string OrderId(string chosen, Dictionary<string, object?> st)
    {
        var payload = PythonJson.Compact(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["chosen"] = chosen, ["state"] = st,
        });
        var hash = System.Security.Cryptography.SHA256.HashData(
            System.Text.Encoding.UTF8.GetBytes(payload));
        return "WO-" + Convert.ToHexString(hash).ToLowerInvariant()[..12];
    }

    /// <summary>回路第一步：问决策层 → 产出工单（**只读声明，不落笔内容**）。</summary>
    public static Dictionary<string, object?> Plan(string root, string adapter = "stub", long top = 5,
                                                   string source = "")
    {
        var st = State(root);
        var picked = Items(root, Math.Max(1, top), source);
        var qs = Questions(root, top, source);
        if (qs.Count == 0)
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["schema"] = "nf-workorder/1", ["status"] = "empty",
                ["reason"] = "公开声明里没有待办项（type_backlog / pipeline_advisory 均为空）",
                ["state"] = st,
            };
        }
        var candidates = picked.Select(it => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = it["id"], ["title"] = it["title"], ["detail"] = it["detail"], ["where"] = it["where_hint"],
        }).ToList();
        var stateText = PythonJson.SortedWithSpaces(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["facts"] = st, ["candidates"] = candidates,
        });
        var request = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["state"] = stateText, ["questions"] = qs,
        };
        var output = DecisionLayer.Decide(request, adapter, root: root);
        if (PyStr(output.GetValueOrDefault("status")) != "ok")
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["schema"] = "nf-workorder/1", ["status"] = "abstained",
                ["reason"] = output.GetValueOrDefault("reason"), ["state"] = st,
                ["decision_meta"] = output.GetValueOrDefault("meta"),
            };
        }
        var answers = output.GetValueOrDefault("answers") as Dictionary<string, object?>
                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var nextItem = answers.GetValueOrDefault("next_item") as Dictionary<string, object?>
                       ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var chosenId = PyStr(nextItem.GetValueOrDefault("argmax"));
        var all = Items(root, source: source);
        var chosen = all.FirstOrDefault(it => PyStr(it.GetValueOrDefault("id")) == chosenId)
                     ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var risk = answers.GetValueOrDefault("risk:" + chosenId) as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var safe = answers.GetValueOrDefault("gate_safe:" + chosenId) as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var options = ObjList(nextItem.GetValueOrDefault("options"));
        var probs = ObjList(nextItem.GetValueOrDefault("probs"));
        var optionIndex = options.FindIndex(o => PyScalar.PyEquals(o, chosenId));
        var meta = output.GetValueOrDefault("meta") as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = "nf-workorder/1", ["status"] = "ok",
            ["order_id"] = OrderId(chosenId, st),
            ["state"] = st,
            ["decision"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["adapter"] = meta.GetValueOrDefault("adapter"),
                ["calibrated"] = meta.GetValueOrDefault("calibrated"),
                ["non_gate"] = meta.GetValueOrDefault("non_gate"),
                ["next_item_prob"] = optionIndex >= 0 && optionIndex < probs.Count ? probs[optionIndex] : null,
                ["risk_level"] = risk.GetValueOrDefault("value"),
                ["risk_probs"] = risk.GetValueOrDefault("probs"),
                ["gate_safe_p"] = safe.GetValueOrDefault("p"),
                ["note"] = "决策层只给选择与概率；**它不写内容**",
            },
            ["chosen"] = chosen,
            ["worker_brief"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["goal"] = chosen.GetValueOrDefault("title"),
                ["item"] = chosen.GetValueOrDefault("id"),
                ["evidence"] = chosen.GetValueOrDefault("detail"),
                ["where"] = chosen.GetValueOrDefault("where_hint"),
                ["done_when"] = chosen.GetValueOrDefault("done_when"),
                ["accept"] = "bash verify.sh（全绿）+ nf conformance（conformant）",
                ["worker_role"] = "生成式 worker（人 / Codex / 生成式模型）——决策模型不落笔",
            },
        };
    }

    /// <summary>回路体检（离线）：待办真源可读 + 问题形状合法 + 工单只落内部档案 + stub 确定性。</summary>
    public static Result Scan(string root)
    {
        var issues = new List<string>();
        var st = State(root);
        var allItems = Items(root);
        if (allItems.Count == 0)
            issues.Add($"待办真源为空（{string.Join("、", Sources.Select(s => s.Rel))} 均无条目）——回路无活可挑");
        var ids = allItems.Select(it => PyStr(it.GetValueOrDefault("id"))).ToList();
        if (ids.Distinct(StringComparer.Ordinal).Count() != ids.Count)
            issues.Add($"工作项 id 重复（{ids.Count} 项 / {ids.Distinct(StringComparer.Ordinal).Count()} 唯一）"
                       + "——选项重复会让决策无意义");
        foreach (var it in allItems.Take(5))
        {
            foreach (var key in new[] { "id", "kind", "title", "detail", "where_hint", "done_when" })
            {
                if (!PyTruthy(it.GetValueOrDefault(key)))
                    issues.Add($"工作项 {PyStr(it.GetValueOrDefault("id"))} 缺字段 {key}"
                               + "（工单须能自述怎么干、怎么验收）");
            }
        }
        var qs = Questions(root, 3);
        if (qs.Count == 0)
        {
            issues.Add("问题面为空（无法向决策层提问）");
        }
        else
        {
            var bad = DecisionLayer.RequestIssue(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["state"] = "x", ["questions"] = qs,
            });
            if (bad.Length > 0) issues.Add("回路产出的问题不合规：" + bad);
        }
        var p1 = Plan(root, "stub", 3);
        var p2 = Plan(root, "stub", 3);
        if (PythonJson.Compact(p1) != PythonJson.Compact(p2))
            issues.Add("stub 工单非确定性（同输入两次结果不一致）");
        var p1Ok = PyStr(p1.GetValueOrDefault("status")) == "ok";
        if (!p1Ok && allItems.Count > 0)
            issues.Add($"stub 工单未成形：{PyStr(p1.GetValueOrDefault("reason"))}");
        if (p1Ok)
        {
            var chosen = p1.GetValueOrDefault("chosen") as Dictionary<string, object?>
                         ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var chosenId = PyStr(chosen.GetValueOrDefault("id"));
            if (!allItems.Take(3).Any(it => PyStr(it.GetValueOrDefault("id")) == chosenId))
                issues.Add($"工单所选工作项不在候选集内（{chosenId}）");
            var brief = p1.GetValueOrDefault("worker_brief") as Dictionary<string, object?>
                        ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            foreach (var key in new[] { "goal", "done_when", "accept", "worker_role" })
            {
                if (!PyTruthy(brief.GetValueOrDefault(key)))
                    issues.Add($"工单缺 {key}（缺判据的工单等于没有验收）");
            }
        }
        if (!OrderDir.StartsWith(ArchivePrefix, StringComparison.Ordinal))
            issues.Add($"工单目录不在内部档案前缀 {ArchivePrefix} 下（计划类产品不得入公开仓）");
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["items"] = (long)allItems.Count,
            ["untyped"] = Convert.ToInt64(st["untyped_fields"]),
            ["advisories"] = Convert.ToInt64(st["advisories"]),
            ["adapters"] = (long)ObjList(st["adapters"]).Count,
            ["pulled_candidates"] = st["candidates_pulled"],
            ["stub_order"] = p1Ok ? PyStr(p1.GetValueOrDefault("order_id")) : "",
            ["issues"] = (long)issues.Count,
        };
        return new Result(issues, stats);
    }

    /// <summary>真源 <c>summary(stats)</c> 原文（<c>%(pulled_candidates)s</c> → Python repr）。</summary>
    public static string Summary(Dictionary<string, object?> stats) =>
        $"待办 {Convert.ToInt64(stats.GetValueOrDefault("items") ?? 0L)} 项"
        + $"（未定型字段 {Convert.ToInt64(stats.GetValueOrDefault("untyped") ?? 0L)}"
        + $" · advisory {Convert.ToInt64(stats.GetValueOrDefault("advisories") ?? 0L)}）"
        + $"· 适配器 {Convert.ToInt64(stats.GetValueOrDefault("adapters") ?? 0L)}"
        + $" · 已拉取候选 {PyScalar.PyRepr(stats.GetValueOrDefault("pulled_candidates"))}"
        + $" · stub 工单 {PyStr(stats.GetValueOrDefault("stub_order"))}";

    /// <summary>
    /// 真源 <c>render_brief(doc, closed=None)</c>：人读工单（给 worker 执行用）。
    /// 决策层那一行按 <c>%.2f</c> 渲染风险期望与 <c>gate_safe</c>（假值回落 0.0）。
    /// </summary>
    public static string RenderBrief(Dictionary<string, object?> doc)
    {
        if (PyStr(doc.GetValueOrDefault("status")) != "ok")
            return $"工单未成形：{PyStr(doc.GetValueOrDefault("reason"))}";
        var b = doc.GetValueOrDefault("worker_brief") as Dictionary<string, object?>
                ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var chosen = doc.GetValueOrDefault("chosen") as Dictionary<string, object?>
                     ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var decision = doc.GetValueOrDefault("decision") as Dictionary<string, object?>
                       ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var doneWhen = string.Join("；", ObjList(b.GetValueOrDefault("done_when")).Select(PyStr));
        var lines = new List<string>
        {
            $"# 工单 {PyStr(doc.GetValueOrDefault("order_id"))}",
            "",
            $"- 目标：{PyStr(b.GetValueOrDefault("goal"))}",
            $"- 条目：`{PyStr(b.GetValueOrDefault("item"))}`（{PyStr(chosen.GetValueOrDefault("source"))}）",
            $"- 证据/背景：{PyStr(b.GetValueOrDefault("evidence"))}",
            $"- 落点提示：{PyStr(b.GetValueOrDefault("where"))}",
            $"- 完成判据：{doneWhen}",
            $"- 验收：{PyStr(b.GetValueOrDefault("accept"))}",
            $"- 决策层（只选择、不写内容）：{PyStr(decision.GetValueOrDefault("adapter"))}"
            + $" · 风险期望 {PyFloat(PyOrZero(decision.GetValueOrDefault("risk_level")))}"
            + $" · gate_safe={PyFloat(PyOrZero(decision.GetValueOrDefault("gate_safe_p")))}",
            "",
        };
        return string.Join("\n", lines);
    }

    /// <summary>Python <c>x or 0.0</c>：假值 → 0.0。</summary>
    private static double PyOrZero(object? value) => value switch
    {
        double d when d != 0 => d,
        long l when l != 0 => l,
        int i when i != 0 => i,
        _ => 0.0,
    };

    /// <summary>Python <c>"%.2f"</c>（固定两位小数 · invariant）。</summary>
    private static string PyFloat(double value) =>
        value.ToString("F2", CultureInfo.InvariantCulture);

    /// <summary>Python <c>int(x or len(y))</c>：假值（None / 0 / ""）时取长度。</summary>
    private static long PyIntOr(object? count, int fallback)
    {
        if (count is long l && l != 0) return l;
        if (count is int i && i != 0) return i;
        if (count is double d && d != 0) return (long)d;
        return fallback;
    }

    private static string PyStr(object? value) => value switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        _ => Convert.ToString(value, CultureInfo.InvariantCulture) ?? "None",
    };

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

    private static List<object?> ObjList(object? value) => value as List<object?> ?? new List<object?>();

    private static List<Dictionary<string, object?>> PyListOfMaps(object? value) =>
        (value as List<object?>)?.OfType<Dictionary<string, object?>>().ToList()
        ?? new List<Dictionary<string, object?>>();
}
