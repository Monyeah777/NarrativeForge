using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/tool_face.py</c>：模块工具面（<c>machine_contract.tool_face</c> 可选建议层）。
///
/// 定位：轻量机检只验**可无歧义项**——purpose / guidance 在场、candidates 有链接必有出处（repo + license）；
/// 「装不装 / 装哪个 / 自造」不入门禁（AI 自由裁量）。
/// </summary>
public static class ToolFace
{
    private static readonly Regex HttpRe = new(@"^https?://", RegexOptions.CultureInvariant);

    public static (List<string> Issues, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var modules = 0;
        var entries = 0;
        var candidates = 0;
        var faces = new List<object?>();

        foreach (var rel in ModuleDocs.Files(root))
        {
            var abs = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            var mc = ModuleContracts.MachineContractOf(abs);
            if (mc is null || !mc.TryGetValue("tool_face", out var faceNode)) continue;

            // Python：`if not isinstance(face, list) or not face` → 报「tool_face 非空列表」并跳过该件
            if (faceNode is not List<object?> face || face.Count == 0)
            {
                issues.Add($"{abs}: tool_face 非空列表");
                continue;
            }

            modules++;
            var id = mc.TryGetValue("id", out var idNode) && idNode is string s && s.Length > 0 ? s : abs;
            faces.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["module"] = id,
                ["source"] = abs,
                ["entries"] = face.Count,
            });
            foreach (var entry in face)
            {
                entries++;
                var map = entry as Dictionary<string, object?>
                          ?? throw new ArgumentException(
                              $"tool_face 条目不是映射：{PyScalar.PyRepr(entry)}（与 Python 同向：validate_entry 会取属性失败）");
                issues.AddRange(ValidateEntry(map));
                candidates += map.TryGetValue("candidates", out var cs) && cs is List<object?> list ? list.Count : 0;
            }
        }

        return (issues, new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["modules"] = modules,
            ["entries"] = entries,
            ["candidates"] = candidates,
            ["faces"] = faces,
        });
    }

    /// <summary>等价 <c>tool_face.validate_entry</c>（逐条给无歧义结论，不做风格评判）。</summary>
    private static List<string> ValidateEntry(Dictionary<string, object?> entry)
    {
        var issues = new List<string>();
        if (entry.TryGetValue("purpose", out var purpose) is false || purpose is not string ps || ps.Trim().Length == 0)
            issues.Add("tool_face 条目缺 purpose");

        if (entry.TryGetValue("guidance", out var guidance) is false
            || guidance is not Dictionary<string, object?> gm || gm.Count == 0)
            issues.Add("tool_face 条目缺 guidance（指导段是验收硬核）");

        if (entry.TryGetValue("candidates", out var cands) && cands is List<object?> list)
        {
            foreach (var cand in list)
            {
                if (cand is not Dictionary<string, object?> cm)
                {
                    issues.Add("candidate 非对象");
                    continue;
                }
                var repo = cm.TryGetValue("repo", out var r) && r is string rs ? rs : "";
                if (!HttpRe.IsMatch(repo)) issues.Add("candidate 缺合法 https 链接");
                var license = cm.TryGetValue("license", out var l) && l is string ls ? ls : "";
                if (license.Trim().Length == 0) issues.Add("candidate 缺 license（有链接必须有出处）");
            }
        }
        return issues;
    }
}
