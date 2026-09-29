using System.Text;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/cognition.py</c>：认知族门禁——行话术语表（`protocol/glossary.json`）
/// + 执行面分档（`protocol/execution_modes.json`）。
///
/// 判据：术语唯一 / definition 非空 / **source 与 used_in 必须真实存在且逐字出现该术语**（防"登记没人用的行话"）；
/// 分档 id 唯一 / required_blocks 非空 / 实例 ≥1 且每件逐字含全部必备结构块（防自称 Runbook 却没有步骤）。
/// </summary>
public static class Cognition
{
    public const string GlossaryRel = "protocol/glossary.json";
    public const string ModesRel = "protocol/execution_modes.json";
    public const string GlossarySchema = "nf-glossary/1";
    public const string ModesSchema = "nf-execution-modes/1";

    public sealed record Result(List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats);

    public static Result Run(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        VerifyGlossary(root, issues, out var glossaryStats);
        VerifyModes(root, issues, out var modesStats);
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["glossary"] = glossaryStats,
            ["modes"] = modesStats,
        };
        return new Result(issues, warns, stats);
    }

    private static void VerifyGlossary(string root, List<string> issues, out Dictionary<string, object?> stats)
    {
        stats = new Dictionary<string, object?>(StringComparer.Ordinal);
        var path = Path.Combine(root, GlossaryRel);
        if (!File.Exists(path))
        {
            issues.Add("缺术语表 " + GlossaryRel);
            return;
        }
        using var doc = JsonIo.ReadFile(path);
        var rootElement = doc.RootElement;
        if (Str(rootElement, "schema") != GlossarySchema)
            issues.Add($"术语表 schema 不匹配（期望 {GlossarySchema}）");
        if (!rootElement.TryGetProperty("rules", out var rules) || rules.GetArrayLength() == 0)
            issues.Add("术语表 rules 不得为空（登记纪律必须成文）");

        var seen = new HashSet<string>(StringComparer.Ordinal);
        var uses = 0;
        foreach (var term in rootElement.GetProperty("terms").EnumerateArray())
        {
            var name = Str(term, "term");
            if (name.Length == 0) { issues.Add("存在无 term 的条目"); continue; }
            if (!seen.Add(name)) issues.Add("术语重复：" + name);
            if (Str(term, "definition").Trim().Length == 0) issues.Add($"术语 {name} 缺 definition");

            var source = Str(term, "source");
            if (!File.Exists(Path.Combine(root, source)))
            {
                issues.Add($"术语 {name} 的 source 不存在：{source}");
            }
            else if (!ReadText(Path.Combine(root, source)).Contains(name, StringComparison.Ordinal))
            {
                issues.Add($"术语 {name} 未在其 source 中逐字出现：{source}（定义必须落在真源里）");
            }

            foreach (var usedIn in StringList(term, "used_in"))
            {
                if (!File.Exists(Path.Combine(root, usedIn)))
                {
                    issues.Add($"术语 {name} 的 used_in 不存在：{usedIn}");
                }
                else if (!ReadText(Path.Combine(root, usedIn)).Contains(name, StringComparison.Ordinal))
                {
                    issues.Add($"术语 {name} 的 used_in 未逐字出现该术语：{usedIn}（防登记没人用的行话）");
                }
                else
                {
                    uses++;
                }
            }
        }
        stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["terms"] = seen.Count,
            ["uses"] = uses,
        };
    }

    private static void VerifyModes(string root, List<string> issues, out Dictionary<string, object?> stats)
    {
        stats = new Dictionary<string, object?>(StringComparer.Ordinal);
        var path = Path.Combine(root, ModesRel);
        if (!File.Exists(path))
        {
            issues.Add("缺执行分档声明 " + ModesRel);
            return;
        }
        using var doc = JsonIo.ReadFile(path);
        var rootElement = doc.RootElement;
        if (Str(rootElement, "schema") != ModesSchema)
            issues.Add($"执行分档 schema 不匹配（期望 {ModesSchema}）");

        var seen = new HashSet<string>(StringComparer.Ordinal);
        var instancesOk = 0;
        foreach (var mode in rootElement.GetProperty("modes").EnumerateArray())
        {
            var id = Str(mode, "id");
            if (!seen.Add(id)) issues.Add("mode id 重复：" + id);
            var blocks = StringList(mode, "required_blocks");
            if (blocks.Count == 0) issues.Add($"mode {id} 缺 required_blocks（该档必备结构必须成文）");
            var instances = StringList(mode, "instances");
            if (instances.Count == 0) issues.Add($"mode {id} 无实例（声明了档却没有件属于它）");

            foreach (var rel in instances)
            {
                if (!File.Exists(Path.Combine(root, rel)))
                {
                    issues.Add($"mode {id} 的实例不存在：{rel}");
                    continue;
                }
                var text = ReadText(Path.Combine(root, rel));
                var missing = blocks.Where(b => !text.Contains(b, StringComparison.Ordinal)).ToList();
                if (missing.Count > 0)
                    issues.Add($"实例 {rel} 不属于 {id} 档：缺结构块 {string.Join("/", missing)}");
                else
                    instancesOk++;
            }
        }
        stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["modes"] = seen.Count,
            ["instances_ok"] = instancesOk,
        };
    }

    private static string Str(JsonElement element, string name)
        => element.ValueKind == JsonValueKind.Object && element.TryGetProperty(name, out var v) &&
           v.ValueKind == JsonValueKind.String
            ? v.GetString()!
            : "";

    /// <summary>等价 Python：字符串视为单项，数组逐项；其余为空。</summary>
    private static List<string> StringList(JsonElement element, string name)
    {
        if (element.ValueKind != JsonValueKind.Object || !element.TryGetProperty(name, out var v)) return new List<string>();
        return v.ValueKind switch
        {
            JsonValueKind.String => new List<string> { v.GetString()! },
            JsonValueKind.Array => v.EnumerateArray()
                .Where(x => x.ValueKind == JsonValueKind.String)
                .Select(x => x.GetString()!).ToList(),
            _ => new List<string>(),
        };
    }

    private static string ReadText(string path)
        => new UTF8Encoding(false).GetString(File.ReadAllBytes(path));
}
