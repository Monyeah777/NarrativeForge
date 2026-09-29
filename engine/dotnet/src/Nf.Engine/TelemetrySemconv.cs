using System.Text;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>desktop/src/core/telemetry_semconv.py</c>（**遥测对齐 OTel GenAI 语义约定** · check33 第 7 面）：
/// 把 NF 既有的自定 trace 记录**映射**为 OTel GenAI semconv 的属性面与 OTLP 形状，
/// **不改 trace 格式本身**、**不引入 OTel SDK**（core 零第三方依赖红线保持）。
///
/// 判据照抄：每条 trace 记录 = 一次工具调用的 span（<c>gen_ai.operation.name=execute_tool</c> +
/// <c>gen_ai.tool.name=nf.&lt;命令&gt;</c>）；入参 / 出参走结构化字段
/// （<c>gen_ai.tool.call.arguments</c> / <c>.result</c>）；NF 侧身份走 <c>gen_ai.agent.name</c>；
/// 需求原文进 arguments 内字段；输出 OTLP 形状 JSON（<c>resourceSpans → scopeSpans → spans</c>）供采集侧适配。
///
/// **不宣称 OTLP 传输兼容**（无 protobuf / 无导出端点，只有**形状与属性命名**对齐）；
/// <c>schema_url</c> 未填 = semconv 官方站点尚标 TODO，**不杜撰**。
/// <c>traceId</c> / <c>timeUnixNano</c> 留空由采集方外套（trace 无时间戳纪律：调用 id 由内容摘要派生，可复现）。
/// </summary>
public static class TelemetrySemconv
{
    public const string ScopeName = "nf.telemetry";
    public const string ScopeVersion = "1.0.0";

    public const string AttrOperation = "gen_ai.operation.name";
    public const string AttrToolName = "gen_ai.tool.name";
    public const string AttrToolCallId = "gen_ai.tool.call.id";
    public const string AttrToolArgs = "gen_ai.tool.call.arguments";
    public const string AttrToolResult = "gen_ai.tool.call.result";
    public const string AttrAgentName = "gen_ai.agent.name";
    public const string AttrConversation = "gen_ai.conversation.id";

    public const string OpExecuteTool = "execute_tool";

    /// <summary>trace 字段 → 调用参数面（入参）/ 结果面（出参）。</summary>
    private static readonly string[] ArgFields = { "requirement", "phase", "status" };
    private static readonly string[] ResultFields =
        { "matched", "package", "pipeline", "allowed_modules", "ok", "issues", "stats" };

    /// <summary><c>nf assemble</c> / <c>nf run</c> → <c>nf.assemble</c> / <c>nf.run</c>（点分工具名）。</summary>
    public static string ToolNameOf(Dictionary<string, object?> record)
    {
        // 真源 `str(record.get("tool") or "nf").strip()`：**假值**（缺省 / null / 空串 / 0）一律回落 "nf"。
        var value = record.TryGetValue("tool", out var v) ? v : null;
        var raw = (PyTruthy(value) ? PyStr(value!) : "nf").Trim();
        var parts = raw.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
        // 真源在「tool 全空白」时会 parts[0] 越界崩溃；本件收敛为空串（受控化差异，已登记）。
        return parts.Length > 1 ? parts[0] + "." + parts[1] : (parts.Length == 1 ? parts[0] : "");
    }

    /// <summary>确定性调用标识（trace 无时间戳纪律：id 由内容摘要派生，可复现）。</summary>
    public static string CallIdOf(Dictionary<string, object?> record)
    {
        var payload = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var key in new[] { "tool", "phase", "requirement", "package", "pipeline" })
            payload[key] = record.GetValueOrDefault(key);
        var json = PythonJson.SortedWithSpaces(payload);
        var digest = Convert.ToHexString(
            System.Security.Cryptography.SHA256.HashData(Encoding.UTF8.GetBytes(json))).ToLowerInvariant();
        return "nf-" + digest[..16];
    }

    /// <summary>单条 trace 记录 → semconv 属性 dict（未提供的字段**不杜撰**）。</summary>
    public static Dictionary<string, object?> AttributesFor(Dictionary<string, object?> record,
                                                            string agentName = "narrativeforge")
    {
        var attrs = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            [AttrOperation] = OpExecuteTool,
            [AttrToolName] = ToolNameOf(record),
            [AttrToolCallId] = CallIdOf(record),
            [AttrAgentName] = agentName,
        };
        var args = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var key in ArgFields)
        {
            if (record.TryGetValue(key, out var value)) args[key] = JsonValue(value);
        }
        if (args.Count > 0) attrs[AttrToolArgs] = args;

        var result = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var key in ResultFields)
        {
            if (record.TryGetValue(key, out var value)) result[key] = JsonValue(value);
        }
        if (result.Count > 0) attrs[AttrToolResult] = result;

        if (record.GetValueOrDefault("phase") is string phase && phase.Length > 0)
            attrs[AttrConversation] = "nf-" + phase;
        return attrs;
    }

    /// <summary>trace 记录 → OTLP 形状 span（无时间戳：<c>timeUnixNano</c> 留空由采集方外套）。</summary>
    public static Dictionary<string, object?> ToSpan(Dictionary<string, object?> record,
                                                     string spanId = "", string agentName = "narrativeforge")
    {
        var name = OpExecuteTool + " " + ToolNameOf(record);
        var attributes = AttributesFor(record, agentName)
            .OrderBy(kv => kv.Key, StringComparer.Ordinal)
            .Select(kv => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["key"] = kv.Key,
                ["value"] = OtlpValue(kv.Value),
            })
            .ToList();
        var callId = CallIdOf(record);
        var ok = record.TryGetValue("ok", out var okValue) ? PyTruthy(okValue) : true;
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["name"] = name,
            ["kind"] = 1L,   // SPAN_KIND_INTERNAL
            ["traceId"] = "",
            ["spanId"] = spanId.Length > 0 ? spanId : callId[3..19],
            ["attributes"] = attributes,
            ["status"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["code"] = ok ? 1L : 2L },
        };
    }

    /// <summary>trace 记录集 → OTLP 形状 JSON（<c>resourceSpans → scopeSpans → spans</c>）。</summary>
    public static Dictionary<string, object?> ToExport(List<Dictionary<string, object?>> records,
                                                       string agentName = "narrativeforge")
    {
        var spans = records.Select(r => (object?)ToSpan(r, agentName: agentName)).ToList();
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["resourceSpans"] = new List<object?>
            {
                new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["resource"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["attributes"] = new List<object?>
                        {
                            new Dictionary<string, object?>(StringComparer.Ordinal)
                            {
                                ["key"] = "service.name",
                                ["value"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                                    { ["stringValue"] = "narrativeforge" },
                            },
                        },
                    },
                    ["scopeSpans"] = new List<object?>
                    {
                        new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["scope"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                                { ["name"] = ScopeName, ["version"] = ScopeVersion },
                            ["spans"] = spans,
                        },
                    },
                },
            },
        };
    }

    /// <summary>读 trace JSON：单条记录 / <c>{"records":[…]}</c> / 数组三种形状；非对象项过滤掉。</summary>
    public static List<Dictionary<string, object?>> LoadTrace(string path)
    {
        using var json = JsonIo.ReadFile(path);
        var root = json.RootElement;
        if (root.ValueKind == JsonValueKind.Object)
        {
            if (root.TryGetProperty("records", out var records) && records.ValueKind == JsonValueKind.Array)
            {
                return records.EnumerateArray()
                    .Where(e => e.ValueKind == JsonValueKind.Object)
                    .Select(e => (Dictionary<string, object?>)PythonJson.ToGraph(e)!)
                    .ToList();
            }
            return new List<Dictionary<string, object?>> { (Dictionary<string, object?>)PythonJson.ToGraph(root)! };
        }
        if (root.ValueKind == JsonValueKind.Array)
        {
            return root.EnumerateArray()
                .Where(e => e.ValueKind == JsonValueKind.Object)
                .Select(e => (Dictionary<string, object?>)PythonJson.ToGraph(e)!)
                .ToList();
        }
        return new List<Dictionary<string, object?>>();
    }

    /// <summary>Python 值 → OTLP AnyValue 形状（dict/list 走 <c>stringValue</c> + 排序紧凑 JSON）。</summary>
    public static Dictionary<string, object?> OtlpValue(object? value) => value switch
    {
        null => new Dictionary<string, object?>(StringComparer.Ordinal) { ["stringValue"] = "" },
        bool b => new Dictionary<string, object?>(StringComparer.Ordinal) { ["boolValue"] = b },
        long l => new Dictionary<string, object?>(StringComparer.Ordinal)
            { ["intValue"] = l.ToString(System.Globalization.CultureInfo.InvariantCulture) },
        int i => new Dictionary<string, object?>(StringComparer.Ordinal)
            { ["intValue"] = i.ToString(System.Globalization.CultureInfo.InvariantCulture) },
        double d => new Dictionary<string, object?>(StringComparer.Ordinal) { ["doubleValue"] = d },
        // 真源 `_otlp_value` 对 dict/list 用 `json.dumps(..., ensure_ascii=False, sort_keys=True)`——
        // **默认带空格分隔符**（`, ` / `: `）且排序；不是 Compact 的无空格口径。
        Dictionary<string, object?> or List<object?> =>
            new Dictionary<string, object?>(StringComparer.Ordinal) { ["stringValue"] = PythonJson.SortedWithSpaces(value) },
        _ => new Dictionary<string, object?>(StringComparer.Ordinal) { ["stringValue"] = PyStr(value) },
    };

    /// <summary>semconv 的结构化字段：保持 JSON 可表示（不是 dict/list/str/int/float/bool/None 的转成字符串）。</summary>
    private static object? JsonValue(object? value) => value switch
    {
        null or Dictionary<string, object?> or List<object?> or string or int or long or double or bool => value,
        _ => PyStr(value),
    };

    /// <summary>Python <c>str()</c> 口径（trace 记录的值可能来自 JSON 之外）。</summary>
    private static string PyStr(object value) => value switch
    {
        string s => s,
        bool b => b ? "True" : "False",
        null => "None",
        _ => Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture) ?? "",
    };

    /// <summary>Python 真值语义（`1 if x else 2` 用的是真值，不是「非 null」）。</summary>
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
