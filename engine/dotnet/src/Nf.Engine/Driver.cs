using System.Text;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>desktop/src/core/driver.py</c>（**指令档 → 机器面路由** · driver override，机制借鉴 ACP）：
/// NF 的指令档（组装指令包 / AI_ROUTING / ai-menu）此前只说「怎么读」，**不声明「有机器面时走哪条路」**
/// ——能否走 MCP 工具面全靠执行者自觉。本模块补这层：
///
/// <c>protocol/driver.json</c>（机读真源）声明 <c>bindings</c>（MCP 入口 / 工具集 / 提示集，名字须与
/// 运行时**逐名一致**）、<c>workflows</c>（工作流 → MCP 提示/工具 + **文本 fallback 文件**）、
/// <c>documents</c>（哪些指令档属于哪个工作流，文档头部**必须**带 override 声明块）、
/// <c>fail_closed</c>（派发失败即停、**禁止回退**，含必须出现在声明块里的关键词）。
///
/// 判据（全部可证）：schema 合法；工具/提示名在运行时存在；fallback 文件存在；文档存在且头部 14 行内带
/// <c>DRIVER OVERRIDE</c> 块且块内写明本工作流名与 fail-closed 关键词。
///
/// **两处镜像照抄**：工具名取 <see cref="McpPackage.RuntimeTools"/>（真源 <c>TOOL_DEFS</c> 那 10 个，
/// **不是**引擎自有的 28 个工具面——用后者会偏松）；提示名取 <see cref="McpPackage.RuntimePrompts"/>。
/// 真源在 <c>driver.json</c> 非法 JSON 时会抛到 CLI 层；本件收敛为「空声明 + 缺声明问题」（受控化差异，已登记）。
/// </summary>
public static class Driver
{
    public const string DriverRel = "protocol/driver.json";
    public const string OverrideMark = "DRIVER OVERRIDE";

    public sealed record Result(List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats)
    {
        public bool Ok => Issues.Count == 0;
    }

    /// <summary>读机读真源；缺件或不可解析 → 空字典（不崩）。</summary>
    public static Dictionary<string, object?> Load(string root)
    {
        var path = Path.Combine(root, DriverRel.Replace('/', Path.DirectorySeparatorChar));
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

    /// <summary>解析某工作流该走哪条路（只读；**不实际派发**）。</summary>
    public static Dictionary<string, object?> Resolve(string root, string workflow)
    {
        var doc = Load(root);
        var workflows = doc.GetValueOrDefault("workflows") as Dictionary<string, object?>;
        var wf = workflows?.GetValueOrDefault(workflow) as Dictionary<string, object?>;
        if (wf is null || wf.Count == 0)
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["workflow"] = workflow,
                ["mode"] = "unknown",
                ["reason"] = $"未在 {DriverRel} 中映射",
            };
        }
        var tools = (wf.GetValueOrDefault("mcp_tools") as List<object?> ?? new List<object?>())
            .Select(PyStr).ToList();
        var prompt = PyOr(wf.GetValueOrDefault("mcp_prompt"));
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["workflow"] = workflow,
            ["mode"] = tools.Count > 0 || prompt.Length > 0 ? "mcp" : "markdown",
            ["prompt"] = prompt,
            ["tools"] = tools.Cast<object?>().ToList(),
            ["fallback"] = PyOr(wf.GetValueOrDefault("fallback")),
            ["on_dispatch_failure"] = "stop（禁止回退到文本步骤）",
        };
    }

    /// <summary>机检 driver 声明 → (issues, warns, stats)。</summary>
    public static Result Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var doc = Load(root);
        if (doc.Count == 0)
        {
            return new Result(
                new List<string> { $"缺 driver 声明 {DriverRel}（修复指引：见 protocol/driver.json）" },
                warns,
                new Dictionary<string, object?>(StringComparer.Ordinal));
        }
        if (PyOr(doc.GetValueOrDefault("schema")) != "nf-driver/1")
            issues.Add("driver schema 不匹配（期望 nf-driver/1）");

        var liveTools = McpPackage.RuntimeTools.ToHashSet(StringComparer.Ordinal);
        var livePrompts = McpPackage.RuntimePrompts.ToHashSet(StringComparer.Ordinal);

        var bind = doc.GetValueOrDefault("bindings") as Dictionary<string, object?> ?? new Dictionary<string, object?>();
        foreach (var tool in PyList(bind.GetValueOrDefault("mcp.tools")))
        {
            if (!liveTools.Contains(tool))
                issues.Add($"bindings.mcp.tools 引用了运行时不存在工具：{tool}");
        }
        foreach (var prompt in PyList(bind.GetValueOrDefault("mcp.prompts")))
        {
            if (!livePrompts.Contains(prompt))
                issues.Add($"bindings.mcp.prompts 引用了运行时不存在提示：{prompt}");
        }

        var workflows = doc.GetValueOrDefault("workflows") as Dictionary<string, object?>
                        ?? new Dictionary<string, object?>();
        foreach (var name in workflows.Keys.OrderBy(x => x, StringComparer.Ordinal))
        {
            var wf = workflows[name] as Dictionary<string, object?> ?? new Dictionary<string, object?>();
            foreach (var tool in PyList(wf.GetValueOrDefault("mcp_tools")))
            {
                if (!liveTools.Contains(tool))
                    issues.Add($"workflow {name} 引用不存在的 MCP 工具：{tool}（修复指引：改正或实现该工具）");
            }
            var prompt = PyOr(wf.GetValueOrDefault("mcp_prompt"));
            if (prompt.Length > 0 && !livePrompts.Contains(prompt))
                issues.Add($"workflow {name} 引用不存在的 MCP 提示：{prompt}");
            var fallback = PyOr(wf.GetValueOrDefault("fallback"));
            if (fallback.Length == 0)
            {
                issues.Add($"workflow {name} 缺 fallback 文件（无机器面时的文本路径必须显式）");
            }
            else if (!File.Exists(Path.Combine(root, fallback.Replace('/', Path.DirectorySeparatorChar))))
            {
                issues.Add($"workflow {name} 的 fallback 不存在：{fallback}");
            }
        }

        var failClosed = doc.GetValueOrDefault("fail_closed") as Dictionary<string, object?>
                         ?? new Dictionary<string, object?>();
        var keywords = PyList(failClosed.GetValueOrDefault("marker_keywords"));
        var workflowNames = workflows.Keys.ToHashSet(StringComparer.Ordinal);
        foreach (var item in (doc.GetValueOrDefault("documents") as List<object?> ?? new List<object?>()))
        {
            var entry = item as Dictionary<string, object?> ?? new Dictionary<string, object?>();
            var rel = PyOr(entry.GetValueOrDefault("path"));
            var workflow = PyOr(entry.GetValueOrDefault("workflow"));
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path))
            {
                issues.Add($"driver.documents 指向不存在的文档：{rel}");
                continue;
            }
            if (!workflowNames.Contains(workflow))
                issues.Add($"{rel} 声明的工作流未在 workflows 中定义：{workflow}");
            var text = File.ReadAllText(path, new UTF8Encoding(false));
            var head = string.Join("\n", KnowledgeSig.SplitLines(text).Take(14));
            if (!head.Contains(OverrideMark, StringComparison.Ordinal))
            {
                issues.Add($"{rel} 缺 `{OverrideMark}` 声明块（修复指引：见 protocol/driver.json 的 fail_closed）");
                continue;
            }
            if (workflow.Length > 0 && !head.Contains(workflow, StringComparison.Ordinal))
                warns.Add($"{rel} 的 override 块未写出工作流名 {workflow}");
            foreach (var keyword in keywords)
            {
                if (!head.Contains(keyword, StringComparison.Ordinal))
                    issues.Add($"{rel} 的 override 块缺 fail-closed 关键词「{keyword}」");
            }
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["workflows"] = (long)workflowNames.Count,
            ["documents"] = (long)(doc.GetValueOrDefault("documents") as List<object?> ?? new List<object?>()).Count,
            ["tools_bound"] = (long)PyList(bind.GetValueOrDefault("mcp.tools")).Count,
            ["fallback_files"] = (long)workflows.Values
                .OfType<Dictionary<string, object?>>()
                .Count(w => PyOr(w.GetValueOrDefault("fallback")).Length > 0),
        };
        return new Result(issues, warns, stats);
    }

    private static List<string> PyList(object? value) =>
        (value as List<object?>)?.Select(PyStr).ToList() ?? new List<string>();

    private static string PyStr(object? value) => value switch
    {
        null => "",
        string s => s,
        _ => Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture) ?? "",
    };

    /// <summary>Python <c>str(x or "")</c>：**假值**（None / 空串 / 0 / 空表 / 空映射 / False）一律回落空串。</summary>
    private static string PyOr(object? value) => PyTruthy(value) ? PyStr(value) : "";

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
