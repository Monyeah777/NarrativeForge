using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/payload_harvest.py</c> 的**确定性核心**（`_split_top_level` / `_field_type` / `harvest_doc`）：
/// 从模块正文逐字收割事件载荷的类型证据，**没有证据的字段保持 untyped（不猜）**。
///
/// 本件只移植 <c>nf review</c>（`gap_review`）所需的读面；`apply` / `backlog`（写面）不移植。
/// **照抄真源一处死代码**：`harvest_doc` 里 payload 出现且尚无事件名时那段 `for back in fence...`
/// 循环**不产生任何效果**（它只 `continue`，从不赋值），本件照抄为注释、不实现该空转。
/// </summary>
public static class PayloadHarvest
{
    public const string EventRegistryRel = "protocol/event_registry.json";

    private static readonly Regex FenceRe = new(@"```(?:yaml|yml)\n(.*?)```", RegexOptions.Singleline);
    private static readonly Regex EventRe = new(@"^\s*(?:event|name)\s*:\s*([a-z_][a-z0-9_]*)");
    private static readonly Regex PublishRe = new(@"^\s*(?:publish|produce)\s*:\s*\[?\s*([a-z_][a-z0-9_]*)");
    private static readonly Regex PayloadLineRe = new(@"^\s*payload\s*:\s*\{(.*)\}\s*$");
    private static readonly Regex NumberRe = new(@"^\d+(\.\d+)?$");
    private static readonly Regex UnitRe = new(@"回合|tick|日|分钟|数|量");

    private static readonly Dictionary<string, string> TypeWords = new(StringComparer.Ordinal)
    {
        ["bool"] = "boolean", ["boolean"] = "boolean", ["int"] = "integer",
        ["integer"] = "integer", ["str"] = "string", ["string"] = "string",
        ["float"] = "number", ["number"] = "number", ["list"] = "array",
        ["array"] = "array", ["object"] = "object", ["dict"] = "object",
    };

    /// <summary>按顶层逗号切分（跳过 <c>{}</c> / <c>[]</c> 内部）；顶层的逗号**本身被吃掉**。</summary>
    public static List<string> SplitTopLevel(string body)
    {
        var outList = new List<string>();
        var depth = 0;
        var current = "";
        foreach (var ch in body)
        {
            if (ch is '{' or '[') depth++;
            else if (ch is '}' or ']') depth--;
            if (ch == ',' && depth == 0)
            {
                outList.Add(current);
                current = "";
            }
            else
            {
                current += ch;
            }
        }
        if (current.Trim().Length > 0) outList.Add(current);
        return outList;
    }

    /// <summary>单个字段 token → (字段名, 类型)。规则全部来自文本字面形式。</summary>
    public static (string Name, string Kind) FieldType(string token)
    {
        token = token.Trim().TrimEnd('?');
        if (token.Length == 0) return ("", "");
        if (token.Contains('{'))
        {
            var head = token.Split('{', 2)[0].Trim();
            return (head, "object");
        }
        if (token.EndsWith("[]", StringComparison.Ordinal) || token.EndsWith("[ ]", StringComparison.Ordinal))
            return (token[..^2].Trim(), "array");
        if (token.Contains(':'))
        {
            var parts = token.Split(':', 2);
            var name = parts[0].Trim();
            var val = parts[1].Trim();
            if (val.StartsWith('{') || val.EndsWith('}')) return (name, "object");
            if (val.StartsWith('[')) return (name, "array");
            var low = val.ToLowerInvariant();
            if (TypeWords.TryGetValue(low, out var mapped)) return (name, mapped);
            if (low is "true" or "false") return (name, "boolean");
            if (NumberRe.IsMatch(val)) return (name, "number");
            if (val.StartsWith('<') || val.StartsWith('（'))
                return UnitRe.IsMatch(val) ? (name, "number") : (name, "untyped");
            if (val.Contains('|')) return (name, "string");
            if (val.Length > 0 && !val.StartsWith('[') && !val.StartsWith('{')) return (name, "string");
            return (name, "untyped");
        }
        return (token, "untyped");
    }

    /// <summary>单篇模块文档 → {事件名: {字段: 类型}}。</summary>
    public static Dictionary<string, Dictionary<string, string>> HarvestDoc(string text)
    {
        var outMap = new Dictionary<string, Dictionary<string, string>>(StringComparer.Ordinal);
        foreach (Match fence in FenceRe.Matches(text))
        {
            var body = fence.Groups[1].Value;
            var ev = "";
            var payloadRaw = "";
            foreach (var line in body.Split('\n'))
            {
                var m = EventRe.Match(line);
                if (m.Success) ev = m.Groups[1].Value;
                var m2 = PublishRe.Match(line);
                if (m2.Success && ev.Length == 0) ev = m2.Groups[1].Value;
                var m3 = PayloadLineRe.Match(line);
                if (!m3.Success) continue;
                payloadRaw = m3.Groups[1].Value;
                if (ev.Length == 0) continue;   // 真源此处有一段**空转**的 for 循环（无副作用），不实现
                var fields = new Dictionary<string, string>(StringComparer.Ordinal);
                foreach (var tok in SplitTopLevel(payloadRaw))
                {
                    var (name, kind) = FieldType(tok);
                    if (name.Length > 0) fields[name] = kind;
                }
                if (fields.Count == 0) continue;
                if (!outMap.TryGetValue(ev, out var slot))
                {
                    slot = new Dictionary<string, string>(StringComparer.Ordinal);
                    outMap[ev] = slot;
                }
                foreach (var (key, value) in fields) slot[key] = value;
            }
        }
        return outMap;
    }
}
