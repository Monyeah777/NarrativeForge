using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 Python <c>desktop/src/core/pack_combo.py::_parse_protocol</c> 的解析语义。
///
/// 关键事实（读源码得）：该函数**不使用 YAML 解析器**，而是四条正则做"极小读取"，
/// 只取组合需要的键（id / pipeline / module_id_range / mount_layers / references）。
/// 因此 .NET 侧不需要 YAML 依赖，但必须**逐条复刻正则与后处理语义**，否则画像不等价。
/// </summary>
public static class ProtocolYaml
{
    private static readonly Regex IdRe =
        new(@"(?m)^\s*id:\s*(\S+)\s*$", RegexOptions.Multiline);

    private static readonly Regex PipelineRe =
        new(@"(?m)^\s*pipeline:\s*(P\d{2,3})\s*$", RegexOptions.Multiline);

    private static readonly Regex QuotedQualifiedIdRe =
        new("(?m)^\\s*-\\s*\"([^\"]+:M\\d{2,3})\"\\s*(?:#.*)?$", RegexOptions.Multiline);

    private static readonly Regex BareIdRe =
        new("(?m)^\\s*-\\s*\"?(M\\d{2,3})\"?\\s*(?:#.*)?$", RegexOptions.Multiline);

    private static readonly Regex FlowRangeRe =
        new(@"(?m)^\s*module_id_range\s*:\s*\[([^\]]*)\]", RegexOptions.Multiline);

    private static readonly Regex LayerRe =
        new(@"(?m)^\s*(P\d{2})\s*[^:]*:\s*\{default:\s*\[([^\]]*)\]", RegexOptions.Multiline);

    private static readonly Regex ReferenceRe =
        new("(?ms)^\\s*-\\s*source_package:\\s*(\\S+)\\s*\\n\\s*module_id:\\s*(\\S+)",
            RegexOptions.Multiline | RegexOptions.Singleline);

    public sealed record Reference(string SourcePackage, string ModuleId);

    public sealed record ProtocolParse(
        string Dir,
        string Id,
        string Pipeline,
        IReadOnlyList<string> ModuleIds,
        IReadOnlyDictionary<string, IReadOnlyList<string>> MountLayers,
        IReadOnlyList<Reference> References);

    /// <param name="text">protocol.yaml 全文（UTF-8 已解码）。</param>
    /// <param name="dirName">包目录名（id 缺省回退值）。</param>
    public static ProtocolParse Parse(string text, string dirName)
    {
        var idMatch = IdRe.Match(text);
        var id = idMatch.Success ? idMatch.Groups[1].Value : dirName;

        var pipelineMatch = PipelineRe.Match(text);
        var pipeline = pipelineMatch.Success ? pipelineMatch.Groups[1].Value : "";

        // 两种写法并集（旧包混用行式裸号与全限定），并按出现序去重（Python dict.fromkeys 语义）
        var ids = new List<string>();
        var seen = new HashSet<string>(StringComparer.Ordinal);
        foreach (var m in QuotedQualifiedIdRe.Matches(text).Cast<Match>())
        {
            if (seen.Add(m.Groups[1].Value)) ids.Add(m.Groups[1].Value);
        }
        foreach (var m in BareIdRe.Matches(text).Cast<Match>())
        {
            if (seen.Add(m.Groups[1].Value)) ids.Add(m.Groups[1].Value);
        }

        if (ids.Count == 0)
        {
            // flow 写法：module_id_range: [M40, 情感:M22]
            var flow = FlowRangeRe.Match(text);
            if (flow.Success)
            {
                foreach (var segment in flow.Groups[1].Value.Split(','))
                {
                    var trimmed = segment.Trim();
                    if (trimmed.Length == 0) continue;
                    ids.Add(trimmed.Trim('\'', '"'));
                }
            }
        }

        var layers = new SortedDictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal);
        foreach (var m in LayerRe.Matches(text).Cast<Match>())
        {
            var mods = new List<string>();
            foreach (var segment in m.Groups[2].Value.Split(','))
            {
                var trimmed = segment.Trim();
                if (trimmed.Length == 0) continue;
                mods.Add(trimmed.Trim('\'', '"'));
            }
            if (mods.Count > 0) layers[m.Groups[1].Value] = mods;
        }

        var refs = new List<Reference>();
        foreach (var m in ReferenceRe.Matches(text).Cast<Match>())
        {
            refs.Add(new Reference(
                m.Groups[1].Value.Trim('\'', '"'),
                m.Groups[2].Value.Trim('\'', '"')));
        }

        return new ProtocolParse(dirName, id, pipeline, ids, layers, refs);
    }
}
