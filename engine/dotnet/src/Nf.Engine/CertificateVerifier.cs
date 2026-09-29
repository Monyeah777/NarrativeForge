using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>pack_combo.py::verify_certificate</c>：按证书声明的输入（<c>packs</c> / <c>extra_modules</c>）
/// **重算**组合并与在盘证书逐字段比对（T4）。
/// </summary>
public static class CertificateVerifier
{
    private static readonly string[] ComparedKeys =
    {
        "modules", "module_count", "layer_stacks", "dependency_closure", "event_closure",
        "assets_borrowed", "modules_borrowed", "legal", "digest",
    };

    public sealed record Row(string Label, bool Legal, int Modules, IReadOnlyList<string> Issues);

    public static IReadOnlyList<Row> VerifyAll(string root)
    {
        var path = Path.Combine(root, "protocol", "combo_certificates.json");
        return VerifyAll(root, JsonIo.ReadFile(path));
    }

    /// <summary>可注入文档版本：供负例自检在内存里篡改证书后仍能走同一校验路径。</summary>
    public static IReadOnlyList<Row> VerifyAll(string root, JsonDocument doc)
    {
        var rows = new List<Row>();
        foreach (var cert in doc.RootElement.GetProperty("certificates").EnumerateArray())
        {
            var label = cert.TryGetProperty("label", out var l) && l.ValueKind == JsonValueKind.String
                ? l.GetString()!
                : "(无标签)";
            var packs = cert.GetProperty("packs").EnumerateArray().Select(x => x.GetString()!).ToList();
            var extraModules = cert.GetProperty("extra_modules").EnumerateArray().Select(x => x.GetString()!).ToList();

            var fresh = Combinator.Build(root, packs, extraModules);
            var issues = new List<string>();
            foreach (var key in ComparedKeys)
            {
                var freshCanonical = PythonJson.CanonicalizeGraph(fresh.Certificate[key]);
                var storedCanonical = cert.TryGetProperty(key, out var stored)
                    ? PythonJson.Canonicalize(stored)
                    : "(缺失)";
                if (freshCanonical != storedCanonical)
                {
                    issues.Add($"字段不一致：{key}（复算 {Truncate(freshCanonical)} ≠ 在盘 {Truncate(storedCanonical)}）");
                }
            }
            rows.Add(new Row(label, fresh.Legal, fresh.Certificate["module_count"] is int c ? c : 0, issues));
        }
        return rows;
    }

    private static string Truncate(string s) => s.Length <= 60 ? s : s[..57] + "…";
}
