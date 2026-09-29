using System.Globalization;
using System.Text;
using System.Text.Json;

namespace Nf.Engine;

// 复刻 core/decision_layer.py（**决策层面** · typed-decision 端口 · check33 第 15 条）。
//
// 判据（全部离线）：声明完整（schema / 三原语 / stub 适配器 / 候选模型 / boundaries）·
// 适配器**诚实标注**（note 必填；`in_gate_path` 只许 stub）· 候选 `pulled=true` 必须自带
// `local.{how,runtime,served_by}` 证据 · **stub 确定性**（同输入两次一致）· **fail-closed**
// （未登记适配器 / 缺 endpoint / 不合规请求 → abstained + reason）。
//
// **声明边界（引擎不发起外呼）**：真源的 `systemone-http` / `openai-json` 会真的 POST 到给定端点；
// 引擎**只保留其 fail-closed 分支**（缺 endpoint / 缺 model 时的 ValueError 文案逐字一致），
// 端点齐备时返回 abstained 并注明「未移植：引擎不发起外呼」——只读门不做网络写面。
public static class DecisionLayer
{
    public const string DeclRel = "protocol/decision_layer.json";
    public const string Schema = "nf-decision-layer/1";
    public const string ResponseSchema = "nf-decision-response/1";
    public static readonly string[] Primitives = { "choice", "noul", "score" };
    public const double ProbTol = 1e-3;

    public sealed record Result(List<string> Issues, Dictionary<string, object?> Stats)
    {
        public bool Ok => Issues.Count == 0;

        /// <summary>真源 <c>summary(stats)</c> 原文。</summary>
        public string SummaryLine =>
            $"原语 {Stats["primitives"]} · 适配器 {Stats["adapters"]} · 候选模型 {Stats["candidates"]} · "
            + $"stub {PyBool(Stats["issueless_stub"])}";

        /// <summary>
        /// 按 **check33 第 15 条**的框法落日志：issues 逐条 <c>[FAIL] 决策层：…</c>，再一行 <c>决策层面：…</c>；
        /// 声明缺失时真源在 summary 上抛 KeyError → 被 check33 的 try 兜住打成「不可用」，本件照抄该措辞。
        /// </summary>
        public List<string> Log
        {
            get
            {
                var lines = Issues.Select(i => "[FAIL] 决策层：" + i).ToList();
                lines.Add(Stats.Count == 0 ? "决策层面：不可用" : "决策层面：" + SummaryLine);
                return lines;
            }
        }

        public string LogDigest => Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(
                Encoding.UTF8.GetBytes(string.Join("\n", Log)))).ToLowerInvariant()[..32];
    }

    public static Dictionary<string, object?> LoadDecl(string root)
    {
        var path = Path.Combine(root, DeclRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return new Dictionary<string, object?>(StringComparer.Ordinal);
        try
        {
            using var json = JsonIo.ReadFile(path);
            return PythonJson.ToGraph(json.RootElement) as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        }
        catch (Exception)
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal);
        }
    }

    public static Dictionary<string, object?> AdapterSpec(string root, string adapter)
    {
        foreach (var item in PyList(LoadDecl(root).GetValueOrDefault("adapters")))
        {
            if (PyStr(item.GetValueOrDefault("id")) == adapter) return item;
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal);
    }

    /// <summary>等价 Python <c>decision_layer.adapter_ids</c>：<c>[str(a.get("id")) for a in adapters]</c>（保序）。</summary>
    public static List<object?> AdapterIds(string root) =>
        PyList(LoadDecl(root).GetValueOrDefault("adapters"))
            .Select(item => (object?)(item.GetValueOrDefault("id") is null
                ? "None"
                : PyStr(item.GetValueOrDefault("id"))))
            .ToList();

    /// <summary>请求体检 → 违规说明（空串 = 合规）。</summary>
    public static string RequestIssue(object? req)
    {
        if (req is not Dictionary<string, object?> request) return "请求须为对象";
        if (!PyTruthy(request.GetValueOrDefault("state"))
            || request.GetValueOrDefault("state") is not string)
            return "缺 state（决策层只对给定的状态做判断）";
        var questions = request.GetValueOrDefault("questions") as Dictionary<string, object?>;
        if (questions is null || questions.Count == 0) return "缺 questions（须至少一个问题）";
        foreach (var (name, value) in questions)
        {
            if (value is not Dictionary<string, object?> question) return $"问题 {name} 须为对象";
            var ptype = question.GetValueOrDefault("type") as string;
            if (ptype is null || !Primitives.Contains(ptype))
                return $"问题 {name} 的 type 越词表：{PyScalar.PyRepr(ptype)}（允许 {string.Join("/", Primitives)}）";
            if (ptype == "choice")
            {
                var options = question.GetValueOrDefault("options") as List<object?>;
                if (options is null || options.Count < 2)
                    return $"choice 问题 {name} 须给 ≥2 个候选（候选集由调用方提供）";
                if (!options.All(o => o is string s && s.Length > 0))
                    return $"choice 问题 {name} 的候选须为非空字符串";
                if (options.Select(o => (string)o!).Distinct(StringComparer.Ordinal).Count() != options.Count)
                    return $"choice 问题 {name} 的候选取值重复";
            }
            if (ptype == "score")
            {
                var levels = question.GetValueOrDefault("levels") as List<object?>;
                if (levels is null || levels.Count < 2) return $"score 问题 {name} 须给 ≥2 个有序等级";
            }
        }
        return "";
    }

    /// <summary>应答体检 → 违规说明（空串 = 合规）。</summary>
    public static string ResponseIssue(object? output, Dictionary<string, object?>? req)
    {
        if (output is not Dictionary<string, object?> response) return "应答须为对象";
        foreach (var key in new[] { "schema", "status", "answers", "meta" })
        {
            if (!response.ContainsKey(key)) return $"缺字段 {key}";
        }
        if (response.GetValueOrDefault("schema") as string != ResponseSchema)
            return $"schema 不匹配（期望 {ResponseSchema}）";
        var status = response.GetValueOrDefault("status") as string;
        if (status == "abstained")
        {
            return PyTruthy(response.GetValueOrDefault("reason")) ? "" : "abstained 须给 reason";
        }
        if (status != "ok")
            return $"status 越词表：{PyScalar.PyRepr(status)}（允许 ok/abstained）";
        var answers = response.GetValueOrDefault("answers") as Dictionary<string, object?>;
        var questions = (req?.GetValueOrDefault("questions") as Dictionary<string, object?>)
                        ?? new Dictionary<string, object?>();
        if (answers is null) return "answers 须为对象";
        var missing = questions.Keys.Where(name => !answers.ContainsKey(name)).ToList();
        if (missing.Count > 0) return $"answers 缺问题：{string.Join("、", missing)}（不得静默漏答）";
        foreach (var (name, value) in answers)
        {
            if (value is not Dictionary<string, object?> answer) return $"答案 {name} 须为对象";
            var ptype = (questions.GetValueOrDefault(name) as Dictionary<string, object?>)
                ?.GetValueOrDefault("type") as string;
            if (answer.GetValueOrDefault("type") as string != ptype)
                return $"答案 {name} 的 type 与提问不一致：{PyScalar.PyRepr(answer.GetValueOrDefault("type"))}"
                       + $" ≠ {PyScalar.PyRepr(ptype)}";
            if (ptype is "choice" or "score")
            {
                var question = questions.GetValueOrDefault(name) as Dictionary<string, object?>;
                var options = (question?.GetValueOrDefault("options") ?? question?.GetValueOrDefault("levels"))
                              as List<object?> ?? new List<object?>();
                var probs = answer.GetValueOrDefault("probs") as List<object?>;
                if (probs is null || probs.Count != options.Count)
                    return $"答案 {name} 的 probs 长度须等于候选/等级数（{options.Count}）";
                if (probs.Any(p => p is not (int or long or double) || Convert.ToDouble(p, CultureInfo.InvariantCulture) < 0))
                    return $"答案 {name} 的概率须为非负数";
                var sum = probs.Sum(p => Convert.ToDouble(p, CultureInfo.InvariantCulture));
                if (Math.Abs(sum - 1.0) > ProbTol)
                    return $"答案 {name} 的概率和须 ≈1（实得 {sum.ToString("F6", CultureInfo.InvariantCulture)}）";
                if (ptype == "choice")
                {
                    var argmax = answer.GetValueOrDefault("argmax");
                    if (!options.Any(o => PyScalar.PyEquals(o, argmax)))
                        return $"答案 {name} 的 argmax 须落在候选集内：{PyScalar.PyRepr(argmax)}";
                }
                else if (answer.GetValueOrDefault("value") is not (int or long or double))
                {
                    return $"答案 {name} 须给期望值 value（score 原语）";
                }
            }
            else
            {
                var p = answer.GetValueOrDefault("p");
                if (p is not (int or long or double))
                    return $"答案 {name} 的 p 须为 [0,1] 内的数";
                var probability = Convert.ToDouble(p, CultureInfo.InvariantCulture);
                if (!(probability >= 0.0 && probability <= 1.0)) return $"答案 {name} 的 p 须为 [0,1] 内的数";
            }
        }
        var meta = response.GetValueOrDefault("meta") as Dictionary<string, object?> ?? new Dictionary<string, object?>();
        if (meta.GetValueOrDefault("non_gate") is not true)
            return "meta.non_gate 须为 true（决策层不出现在门禁路径）";
        if (!meta.ContainsKey("calibrated")) return "meta 缺 calibrated（是否校准概率必须自述）";
        return "";
    }

    /// <summary>把外部模型的（可能被舍入的）概率归一化到和为 1。</summary>
    public static List<object?> NormalizeProbs(IEnumerable<object?> probs) =>
        Normalize(probs.Select(p => Convert.ToDouble(p, CultureInfo.InvariantCulture)).ToList());

    private static List<object?> Normalize(List<double> scores)
    {
        var total = scores.Sum();
        if (total <= 0) return Enumerable.Repeat<object?>(1.0 / scores.Count, scores.Count).ToList();
        return scores.Select(s => (object?)(s / total)).ToList();
    }

    private static int Hits(string state, IEnumerable<object?> needles)
    {
        var low = state.ToLowerInvariant();
        return needles.Count(n => n is not null && PyStr(n).Length > 0
                                  && low.Contains(PyStr(n).ToLowerInvariant(), StringComparison.Ordinal));
    }

    /// <summary>离线确定性决策（门禁/CI/演练用）：规则式打分 + 声明序破平 + <c>calibrated=false</c>。</summary>
    public static Dictionary<string, object?> StubDecide(Dictionary<string, object?> req)
    {
        var state = PyStr(req.GetValueOrDefault("state"));
        var answers = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var (name, value) in (req.GetValueOrDefault("questions") as Dictionary<string, object?>)
                 ?? new Dictionary<string, object?>())
        {
            var question = value as Dictionary<string, object?> ?? new Dictionary<string, object?>();
            var ptype = question.GetValueOrDefault("type") as string;
            if (ptype == "choice")
            {
                var options = ObjList(question.GetValueOrDefault("options")).Select(PyStr).ToList();
                var probs = Normalize(options.Select(o => (double)Hits(state, new object?[] { o })).ToList());
                var max = probs.Max(p => Convert.ToDouble(p, CultureInfo.InvariantCulture));
                var argmax = options[probs.FindIndex(p => Convert.ToDouble(p, CultureInfo.InvariantCulture) == max)];
                answers[name] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "choice", ["options"] = options.Cast<object?>().ToList(),
                    ["probs"] = probs, ["argmax"] = argmax,
                };
            }
            else if (ptype == "score")
            {
                var levels = ObjList(question.GetValueOrDefault("levels")).Select(PyStr).ToList();
                var probs = Normalize(levels.Select(l => (double)Hits(state, new object?[] { l })).ToList());
                var value2 = probs.Select((p, i) => (i + 1) * Convert.ToDouble(p, CultureInfo.InvariantCulture)).Sum();
                answers[name] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "score", ["levels"] = levels.Cast<object?>().ToList(),
                    ["probs"] = probs, ["value"] = value2,
                };
            }
            else
            {
                var hits = Hits(state, ObjList(question.GetValueOrDefault("true_hints")));
                answers[name] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "noul", ["p"] = hits > 0 ? 1.0 : 0.0,
                };
            }
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = ResponseSchema, ["status"] = "ok", ["answers"] = answers,
            ["meta"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["adapter"] = "stub", ["calibrated"] = false, ["non_gate"] = true,
                ["note"] = "规则式确定性输出：排序信号，非校准概率",
            },
        };
    }

    /// <summary>
    /// 统一入口：形状校验 → 适配器 → 应答校验；任一环节失败 → **abstained**（fail-closed）。
    /// **端口边界**：http 类适配器只保留「缺 endpoint / 缺 model」的 fail-closed 分支（文案逐字一致）；
    /// 参数齐备时返回 abstained 并注明「引擎不发起外呼」——不做网络写面。
    /// </summary>
    public static Dictionary<string, object?> Decide(Dictionary<string, object?> req, string adapter = "stub",
                                                     string endpoint = "", string model = "", string root = ".")
    {
        Dictionary<string, object?> Abstain(string reason, bool calibrated) =>
            new(StringComparer.Ordinal)
            {
                ["schema"] = ResponseSchema, ["status"] = "abstained",
                ["answers"] = new Dictionary<string, object?>(StringComparer.Ordinal),
                ["reason"] = reason,
                ["meta"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["adapter"] = adapter, ["calibrated"] = calibrated, ["non_gate"] = true,
                },
            };

        var bad = RequestIssue(req);
        if (bad.Length > 0) return Abstain("请求不合规：" + bad, false);
        var spec = AdapterSpec(root, adapter);
        if (spec.Count == 0)
            return Abstain($"未登记的适配器：{adapter}（登记面 {DeclRel}）", false);

        Dictionary<string, object?> output;
        try
        {
            if (adapter == "stub")
            {
                output = StubDecide(req);
            }
            else if (adapter == "systemone-http")
            {
                if (endpoint.Length == 0) throw new InvalidOperationException("systemone-http 需 --endpoint（本地 typed-decision 服务地址）");
                return Abstain($"adapter {adapter} 不可用：InvalidOperationException: 引擎不发起外呼（端口边界：只有 fail-closed 分支已移植）", PyTruthy(spec.GetValueOrDefault("calibrated")));
            }
            else if (adapter == "openai-json")
            {
                if (endpoint.Length == 0 || model.Length == 0) throw new InvalidOperationException("openai-json 需 --endpoint 与 --model");
                return Abstain($"adapter {adapter} 不可用：InvalidOperationException: 引擎不发起外呼（端口边界：只有 fail-closed 分支已移植）", PyTruthy(spec.GetValueOrDefault("calibrated")));
            }
            else
            {
                throw new InvalidOperationException($"适配器 {adapter} 未实现（登记面已声明：{DeclRel}）");
            }
        }
        catch (Exception exc)
        {
            var text = exc.Message.Length > 140 ? exc.Message[..140] : exc.Message;
            return Abstain($"adapter {adapter} 不可用：{exc.GetType().Name}: {text}",
                PyTruthy(spec.GetValueOrDefault("calibrated")));
        }

        // 真源此处写 latency_ms（时钟值）；引擎写 0 → **自比对确定**（日志不含该字段）
        var meta = output.GetValueOrDefault("meta") as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        meta["latency_ms"] = 0L;
        output["meta"] = meta;
        var issue = ResponseIssue(output, req);
        if (issue.Length > 0)
            return Abstain($"adapter {adapter} 输出不合 schema：{issue}", PyTruthy(spec.GetValueOrDefault("calibrated")));
        return output;
    }

    /// <summary>请求指纹（可回放：同 state+questions 得同指纹）。</summary>
    public static string Fingerprint(Dictionary<string, object?> req) =>
        Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(
            Encoding.UTF8.GetBytes(PythonJson.SortedWithSpaces(req)))).ToLowerInvariant()[..16];

    /// <summary>决策层面体检（离线）：声明完整 + 适配器诚实标注 + stub 确定性 + fail-closed。</summary>
    public static Result Scan(string root)
    {
        var issues = new List<string>();
        var decl = LoadDecl(root);
        if (decl.Count == 0)
            return new Result(new List<string>
            {
                $"缺决策层声明 {DeclRel}（修复指引：补声明件再跑门禁）",
            }, new Dictionary<string, object?>(StringComparer.Ordinal));
        if (decl.GetValueOrDefault("schema") as string != Schema)
            issues.Add($"{DeclRel} schema 不匹配（期望 {Schema}）");
        var prims = decl.GetValueOrDefault("primitives") as Dictionary<string, object?>
                    ?? new Dictionary<string, object?>();
        foreach (var primitive in Primitives)
        {
            if (!prims.ContainsKey(primitive))
                issues.Add($"声明缺原语 {primitive}（三原语齐全才谈得上类型化决策）");
        }
        var adapters = PyList(decl.GetValueOrDefault("adapters"));
        if (!adapters.Any(a => PyStr(a.GetValueOrDefault("id")) == "stub"))
            issues.Add("缺 stub 适配器（门禁必须有一条离线确定性路径）");
        foreach (var adapter in adapters)
        {
            var id = PyStr(adapter.GetValueOrDefault("id"));
            foreach (var key in new[] { "id", "kind", "in_gate_path", "calibrated" })
            {
                if (!adapter.ContainsKey(key)) issues.Add($"适配器 {Or(id)} 缺字段 {key}");
            }
            if (PyStr(adapter.GetValueOrDefault("note")).Trim().Length == 0)
                issues.Add($"适配器 {id} 缺 note（能力与边界须自述）");
            if (PyTruthy(adapter.GetValueOrDefault("in_gate_path")) && id != "stub")
                issues.Add($"适配器 {id} 声明 in_gate_path 却非 stub（门禁只许离线确定性路径）");
        }
        var candidates = PyList(decl.GetValueOrDefault("candidates"));
        if (candidates.Count == 0) issues.Add("候选模型清单为空（决策层没有可拉取的模型就只是空壳）");
        foreach (var candidate in candidates)
        {
            var id = PyStr(candidate.GetValueOrDefault("id"));
            foreach (var key in new[] { "id", "source", "license", "evidence", "pulled" })
            {
                if (!candidate.ContainsKey(key)) issues.Add($"候选 {Or(id)} 缺字段 {key}（来源/许可/实证/是否已拉取都要写）");
            }
            var pulled = candidate.GetValueOrDefault("pulled");
            if (pulled is not bool) issues.Add($"候选 {id} 的 pulled 须为布尔（状态不许含糊）");
            else if ((bool)pulled)
            {
                var local = candidate.GetValueOrDefault("local") as Dictionary<string, object?>
                            ?? new Dictionary<string, object?>();
                foreach (var key in new[] { "how", "runtime", "served_by" })
                {
                    if (PyStr(local.GetValueOrDefault(key)).Trim().Length == 0)
                        issues.Add($"候选 {id} 声明 pulled=true 却缺 local.{key}（修复指引：写明怎么拉的、什么运行时、由谁服务）");
                }
            }
        }
        if (ObjList(decl.GetValueOrDefault("boundaries")).Count == 0)
            issues.Add("声明缺 boundaries（不执行动作/不生成正文/不入门禁 等边界须成文）");

        var req = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["state"] = "雨天走廊 与 校园情感 场景；候选：P02 校园情感流 / P03 西幻生存流",
            ["questions"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["pipeline"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "choice",
                    ["options"] = new List<object?> { "P02 校园情感流", "P03 西幻生存流" },
                },
                ["multilingual"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "noul", ["true_hints"] = new List<object?> { "中文", "多语" },
                },
                ["risk"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "score", ["levels"] = new List<object?> { "低", "中", "高" },
                },
            },
        };
        var requestIssue = RequestIssue(req);
        if (requestIssue.Length > 0) issues.Add("内部样例请求不合规：" + requestIssue);
        var a1 = Decide(req, "stub", root: root);
        var a2 = Decide(req, "stub", root: root);
        if (!DictEquals(a1, a2)) issues.Add("stub 非确定性（同输入两次结果不一致）");
        if (a1.GetValueOrDefault("status") as string != "ok")
            issues.Add($"stub 样例未产出 ok：{PyScalar.PyRepr(a1.GetValueOrDefault("reason"))}");
        var responseIssue = ResponseIssue(a1, req);
        if (responseIssue.Length > 0) issues.Add("stub 应答不合 schema：" + responseIssue);
        if ((a1.GetValueOrDefault("meta") as Dictionary<string, object?>)?.GetValueOrDefault("calibrated") is not false)
            issues.Add("stub 应答须自称 calibrated=false（排序信号不是概率）");
        foreach (var (label, adapter) in new[] { ("未登记适配器", "ghost"), ("缺 endpoint", "systemone-http") })
        {
            var output = Decide(req, adapter, root: root);
            if (output.GetValueOrDefault("status") as string != "abstained" || !PyTruthy(output.GetValueOrDefault("reason")))
                issues.Add($"{label} 未 fail-closed（应 abstained + reason）");
        }
        var bad = Decide(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["questions"] = new Dictionary<string, object?>(StringComparer.Ordinal),
        }, "stub", root: root);
        if (bad.GetValueOrDefault("status") as string != "abstained") issues.Add("不合规请求未 fail-closed");
        var malformed = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["schema"] = ResponseSchema, ["status"] = "ok",
            ["answers"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["risk"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "score", ["probs"] = new List<object?> { 0.2, 0.2 }, ["value"] = 1.5,
                },
            },
            ["meta"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["calibrated"] = true, ["non_gate"] = true,
            },
        };
        if (ResponseIssue(malformed, req).Length == 0)
            issues.Add("概率和不等于 1 的应答竟通过校验（判据失效）");
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["primitives"] = (long)prims.Count,
            ["adapters"] = (long)adapters.Count,
            ["candidates"] = (long)candidates.Count,
            ["issueless_stub"] = a1.GetValueOrDefault("status") as string == "ok",
            ["issues"] = (long)issues.Count,
        };
        return new Result(issues, stats);
    }

    private static bool DictEquals(Dictionary<string, object?> a, Dictionary<string, object?> b) =>
        PythonJson.SortedWithSpaces(a) == PythonJson.SortedWithSpaces(b);

    private static string Or(string value) => value.Length > 0 ? value : "?";

    private static string PyBool(object? value) => value is true ? "True" : "False";

    private static List<Dictionary<string, object?>> PyList(object? value) =>
        (value as List<object?>)?.OfType<Dictionary<string, object?>>().ToList()
        ?? new List<Dictionary<string, object?>>();

    /// <summary>原样取值列表（options / levels / true_hints / boundaries 都是**字符串**列表）。</summary>
    private static List<object?> ObjList(object? value) => value as List<object?> ?? new List<object?>();

    private static string PyStr(object? value) => value switch
    {
        null => "",
        string s => s,
        bool b => b ? "True" : "False",
        _ => Convert.ToString(value, CultureInfo.InvariantCulture) ?? "",
    };

    private static bool PyTruthy(object? value) => value switch
    {
        null => false,
        bool b => b,
        int i => i != 0,
        long l => l != 0,
        double d => d != 0,
        string s => s.Length > 0,
        List<object?> list => list.Count > 0,
        Dictionary<string, object?> map => map.Count > 0,
        _ => true,
    };
}
