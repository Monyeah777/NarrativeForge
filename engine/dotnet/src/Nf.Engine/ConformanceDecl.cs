using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/conformance_decl.py</c>：一致性**声明**（符合什么 / 管到哪 / 什么不管）。
///
/// `protocol/CONFORMANCE.md` 三段：`## 声明`（规范 × 版本 × 真源，版本必须与真源逐条一致）、
/// `## 范围`（scope 白名单，路径必须存在）、`## 排除`（显式排除清单），硬约束 scope ∩ 排除 = ∅。
/// 纪律：版本事实一律**从真源读**（registry.json / schema / protocol.yaml / verify.sh 基线），
/// 声明里改数字改不动门禁。
///
/// **镜像说明**：基线两项（<c>EXPECTED_CHECKS</c> / <c>EXPECTED_PASS</c>）取自
/// <c>core/quality_baseline.py</c>。仓库改基线时本镜像会滞后 → 该契约会**立刻报不一致**
/// （fail-closed 且可由双跑对账定位），不静默通过。
/// </summary>
public static class ConformanceDecl
{
    public const string DeclRel = "protocol/CONFORMANCE.md";
    public const string ContractDescription = "一致性声明";
    public const int ExpectedChecks = 39;
    public const int ExpectedPass = 68;

    private static readonly Regex Row = new(@"^\|\s*`?([^`|]+?)`?\s*\|\s*`?([^`|]+?)`?\s*\|\s*([^|]+?)\s*\|\s*$");
    private static readonly Regex Row2 = new(@"^\|\s*`?([^`|]+?)`?\s*\|\s*([^|]+?)\s*\|\s*$");
    private static readonly Regex Bullet = new(@"^\s*[-*]\s+`([^`]+)`");
    private static readonly Regex DashOnly = new(@"^[-: ]+$");
    private static readonly Regex SchemaVersion = new(@"schema_version\s*:\s*""?([\w.]+)""?");
    private static readonly Regex VerifyVersion = new(@"# 版本 : (v[\d.]+)");
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public sealed record Declaration(
        Dictionary<string, (string Version, string Source)> Versions,
        List<string> Scope,
        List<(string Path, string Reason)> Excluded);

    /// <summary>取 `## &lt;title&gt;` 到下一个同级标题之间的行（同 Python <c>_section</c>）。</summary>
    private static List<string> Section(string text, string title)
    {
        var lines = KnowledgeSig.SplitLines(text);
        int? start = null;
        for (var i = 0; i < lines.Count; i++)
        {
            if (lines[i].Trim() == "## " + title)
            {
                start = i + 1;
                continue;
            }
            if (start is not null && lines[i].StartsWith("## ", StringComparison.Ordinal))
                return lines.GetRange(start.Value, i - start.Value);
        }
        return start is null ? new List<string>() : lines.GetRange(start.Value, lines.Count - start.Value);
    }

    public static Declaration Parse(string root)
    {
        var path = Path.Combine(root, DeclRel.Replace('/', Path.DirectorySeparatorChar));
        var text = File.Exists(path) ? StrictUtf8.GetString(File.ReadAllBytes(path)) : "";
        var versions = new Dictionary<string, (string, string)>(StringComparer.Ordinal);
        foreach (var raw in Section(text, "声明"))
        {
            var m = Row.Match(raw.Trim());
            if (!m.Success) continue;
            var name = m.Groups[1].Value.Trim();
            if (name == "规范" || DashOnly.IsMatch(name)) continue;
            versions[name] = (m.Groups[2].Value.Trim(), m.Groups[3].Value.Trim());
        }
        var scope = new List<string>();
        foreach (var raw in Section(text, "范围"))
        {
            var m = Bullet.Match(raw);
            if (m.Success) scope.Add(m.Groups[1].Value.Trim());
        }
        var excluded = new List<(string, string)>();
        foreach (var raw in Section(text, "排除"))
        {
            var m = Row2.Match(raw.Trim());
            var cell = m.Success ? m.Groups[1].Value.Trim() : "";
            if (m.Success && cell != "路径" && !DashOnly.IsMatch(cell))
                excluded.Add((m.Groups[1].Value.Trim(), m.Groups[2].Value.Trim()));
        }
        return new Declaration(versions, scope, excluded);
    }

    /// <summary>版本真源（声明必须与这里一致）。</summary>
    public static Dictionary<string, string> LiveVersions(string root)
    {
        var live = new Dictionary<string, string>(StringComparer.Ordinal);
        var registryPath = Path.Combine(root, "desktop", "src", "core", "registry.json");
        if (File.Exists(registryPath))
        {
            using var doc = JsonIo.ReadFile(registryPath);
            var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>;
            live["registry schema"] = graph is not null && graph.TryGetValue("registry_schema_version", out var v)
                ? v?.ToString() ?? ""
                : "";
        }
        var contractPath = Path.Combine(root, "protocol", "schema", "contract.schema.json");
        if (File.Exists(contractPath))
        {
            using var doc = JsonIo.ReadFile(contractPath);
            var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>;
            var enumValues = ((graph?.GetValueOrDefault("properties") as Dictionary<string, object?>)
                              ?.GetValueOrDefault("schema") as Dictionary<string, object?>)
                             ?.GetValueOrDefault("enum") as List<object?>;
            live["machine_contract schema"] = enumValues is null
                ? ""
                : string.Join(",", enumValues.Select(x => x?.ToString() ?? ""));
        }
        var community = Path.Combine(root, "community");
        var protocols = Directory.Exists(community)
            ? Directory.GetDirectories(community).Select(p => Path.Combine(p, "protocol.yaml"))
                .Where(File.Exists).OrderBy(p => p, StringComparer.Ordinal).ToList()
            : new List<string>();
        if (protocols.Count > 0)
        {
            var m = SchemaVersion.Match(StrictUtf8.GetString(File.ReadAllBytes(protocols[0])));
            live["protocol.yaml schema"] = m.Success ? m.Groups[1].Value : "";
        }
        var schemaDir = Path.Combine(root, "protocol", "schema");
        live["IDL schema 集"] = (Directory.Exists(schemaDir)
            ? Directory.GetFiles(schemaDir, "*.json").Length
            : 0) + " 件";
        var verifyPath = Path.Combine(root, "verify.sh");
        var verify = File.Exists(verifyPath) ? StrictUtf8.GetString(File.ReadAllBytes(verifyPath)) : "";
        var vm = VerifyVersion.Match(verify);
        live["基线"] = $"{(vm.Success ? vm.Groups[1].Value : "?")} · check1-{ExpectedChecks} · PASS={ExpectedPass}";
        return live;
    }

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _) = Scan(root);
        var detail = $"版本 {Parse(root).Versions.Count} · scope {Parse(root).Scope.Count} · 排除 {Parse(root).Excluded.Count}";
        return issues.Count == 0 ? (true, detail) : (false, string.Join("; ", issues.Take(2)));
    }

    /// <summary>声明机检 → (issues, stats)（同 Python <c>scan</c> 的形状）。</summary>
    public static (List<string> Issues, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var decl = Parse(root);
        var live = LiveVersions(root);
        if (decl.Versions.Count == 0)
            issues.Add($"声明文件缺 `## 声明` 版本表（修复指引：见 {DeclRel}）");
        foreach (var pair in live)
        {
            var got = decl.Versions.TryGetValue(pair.Key, out var row) ? row.Version : "";
            if (got != pair.Value)
                issues.Add($"声明与真源不一致：{pair.Key} 声明={(got.Length == 0 ? "(缺)" : got)} 真源={pair.Value}" +
                           "（修复指引：改声明对齐真源）");
        }
        foreach (var name in decl.Versions.Keys)
        {
            if (!live.ContainsKey(name))
                issues.Add($"声明了无法核验的规范项：{name}（真源缺失；修复指引：补真源或删该行）");
        }
        if (decl.Scope.Count == 0) issues.Add("声明文件缺 `## 范围` 白名单");
        foreach (var rel in decl.Scope)
        {
            var full = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(full) && !Directory.Exists(full))
                issues.Add($"范围里的路径不存在：{rel}（修复指引：删掉或改正）");
        }
        if (decl.Excluded.Count == 0) issues.Add("声明文件缺 `## 排除` 清单（显式排除是声明的核心价值）");
        foreach (var (rel, reason) in decl.Excluded)
        {
            if (rel.Length == 0) continue;
            var optional = reason.Contains("允许不存在", StringComparison.Ordinal);
            if (rel.Any(ch => ch is '*' or '?' or '['))
            {
                if (!optional && PathGlob.Files(root, rel).Count == 0)
                    issues.Add($"排除项 glob 无匹配：{rel}");
            }
            else
            {
                var full = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
                if (!optional && !File.Exists(full) && !Directory.Exists(full))
                    issues.Add($"排除项路径不存在：{rel}（修复指引：删除该条或修正路径）");
            }
        }
        var scopeSet = decl.Scope.Select(s => s.TrimEnd('/')).ToList();
        foreach (var (rawPath, _) in decl.Excluded)
        {
            var rel = rawPath.TrimEnd('/');
            foreach (var s in scopeSet)
            {
                if (rel == s || rel.StartsWith(s + "/", StringComparison.Ordinal)
                    || s.StartsWith(rel + "/", StringComparison.Ordinal))
                {
                    issues.Add($"scope 与排除重叠：{s} ↔ {rel}（同一条不能既在范围又排除）");
                }
            }
        }
        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["versions"] = decl.Versions.Count,
            ["scope"] = decl.Scope.Count,
            ["excluded"] = decl.Excluded.Count,
        };
        return (issues, stats);
    }
}
