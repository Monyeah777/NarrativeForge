namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/impact_check.py</c>：registry 引用图闭合断言（A4 / check21）+ 变更影响面预检。
///
/// 为什么值得移植：check15 ① 的数据源是 <c>community/*/protocol.yaml</c>（需 PyYAML 与目录在场，
/// 缺则降级为文本粗校验）；本件**直接以 registry.json 为起点**做纯 JSON 引用图闭合，
/// 无降级路径——正是引擎这种"只读产物复算"定位该做的那一面。
/// </summary>
public static class ImpactCheck
{
    /// <summary>模块 id 裸号归一：<c>情感类:M55</c> / <c>情感:M55</c> / <c>M55</c> → <c>M55</c>。</summary>
    public static string Norm(object? mid)
    {
        var text = PyText(mid);
        var at = text.IndexOf(':');
        return at < 0 ? text : text[(at + 1)..];
    }

    /// <summary>protocols[] → {id: entry}（缺 id 的条目跳过）。</summary>
    public static Dictionary<string, Dictionary<string, object?>> PkgMap(Dictionary<string, object?> registry)
    {
        var output = new Dictionary<string, Dictionary<string, object?>>(StringComparer.Ordinal);
        foreach (var p in Protocols(registry))
        {
            if (p.GetValueOrDefault("id") is string id && id.Length > 0) output[id] = p;
        }
        return output;
    }

    /// <summary>registry 引用图闭合断言（A4/check21）：空 = 自洽 PASS。只依赖 registry 自身。</summary>
    public static List<string> RegistryIntegrityIssues(Dictionary<string, object?> registry)
    {
        var issues = new List<string>();
        var pkgs = PkgMap(registry);
        foreach (var p in Protocols(registry))
        {
            var pid = p.GetValueOrDefault("id") as string;
            if (string.IsNullOrEmpty(pid)) pid = "<匿名>";
            var seen = new Dictionary<string, string>(StringComparer.Ordinal);
            foreach (var raw in p.GetValueOrDefault("module_ids") as List<object?> ?? new List<object?>())
            {
                var n = Norm(raw);
                if (seen.TryGetValue(n, out var prior))
                    issues.Add($"③{pid} module_ids 裸号重复（寻址歧义）: {prior} 与 {PyText(raw)} 同为 {n}");
                else
                    seen[n] = PyText(raw);
            }
            foreach (var r in (p.GetValueOrDefault("references") as List<object?> ?? new List<object?>())
                         .OfType<Dictionary<string, object?>>())
            {
                var sp = r.GetValueOrDefault("source_package") as string;
                if (sp is null || !pkgs.ContainsKey(sp))
                {
                    issues.Add($"①②{pid} references.source_package 不在 registry " +
                               $"protocols[] 在册: {PyScalar.PyRepr(r.GetValueOrDefault("source_package"))}");
                    continue;
                }
                var srcMids = (pkgs[sp].GetValueOrDefault("module_ids") as List<object?> ?? new List<object?>())
                    .Select(Norm).ToHashSet(StringComparer.Ordinal);
                var mid = Norm(r.GetValueOrDefault("module_id"));
                if (!srcMids.Contains(mid))
                    issues.Add($"②{pid} references.module_id 不在源包 {sp} module_ids 在列: " +
                               $"{PyScalar.PyRepr(r.GetValueOrDefault("module_id"))}");
            }
        }
        return issues;
    }

    /// <summary>引用反查：registry protocols[].references 中引用该 module_id 的包。</summary>
    public static List<Dictionary<string, object?>> ReferencedByPackages(Dictionary<string, object?> registry, string moduleId)
    {
        var n = Norm(moduleId);
        var output = new List<Dictionary<string, object?>>();
        foreach (var p in Protocols(registry))
        {
            foreach (var r in (p.GetValueOrDefault("references") as List<object?> ?? new List<object?>())
                         .OfType<Dictionary<string, object?>>())
            {
                if (Norm(r.GetValueOrDefault("module_id")) != n) continue;
                output.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["protocol"] = p.GetValueOrDefault("id"),
                    ["source_package"] = r.GetValueOrDefault("source_package"),
                    ["source_schema_version"] = r.GetValueOrDefault("source_schema_version"),
                    ["asset_readonly"] = r.GetValueOrDefault("asset_readonly"),
                });
            }
        }
        return output;
    }

    /// <summary>拟删除 module_id 的影响面：被谁引用 + 是否官方核心在册。</summary>
    public static Dictionary<string, object?> RemovalImpact(Dictionary<string, object?> registry, string moduleId)
    {
        var n = Norm(moduleId);
        var refs = ReferencedByPackages(registry, moduleId);
        var coreHits = Modules(registry).Where(m => Norm(m.GetValueOrDefault("id")) == n)
            .Select(m => m.GetValueOrDefault("id")).ToList();
        var pkgHits = Protocols(registry)
            .Where(p => (p.GetValueOrDefault("module_ids") as List<object?> ?? new List<object?>())
                .Select(Norm).Contains(n))
            .Select(p => p.GetValueOrDefault("id")).ToList();
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["module_id"] = moduleId,
            ["referenced_by"] = refs.Cast<object?>().ToList(),
            ["in_official_core"] = coreHits,
            ["in_packages"] = pkgHits,
        };
    }

    /// <summary>拟删除整包（protocol id）的影响面：包自身引用 + 谁引用该包的模块。</summary>
    public static Dictionary<string, object?> RemovalImpactProtocol(Dictionary<string, object?> registry, string protocolId)
    {
        var entry = Protocols(registry).FirstOrDefault(p => p.GetValueOrDefault("id") as string == protocolId);
        if (entry is null)
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["protocol_id"] = protocolId,
                ["error"] = $"protocol 不在 registry protocols[] 在册: {PyScalar.PyRepr(protocolId)}",
                ["module_ids"] = new List<object?>(),
                ["referenced_by_packages"] = new List<object?>(),
                ["referenced_modules"] = new List<object?>(),
            };
        }
        var mids = entry.GetValueOrDefault("module_ids") as List<object?> ?? new List<object?>();
        var refPkgs = new List<object?>();
        var refMods = new List<object?>();
        foreach (var mid in mids)
        {
            foreach (var r in ReferencedByPackages(registry, PyText(mid)))
            {
                if (r.GetValueOrDefault("protocol") as string == protocolId) continue;
                refPkgs.Add(r);
                refMods.Add(mid);
            }
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["protocol_id"] = protocolId,
            ["module_ids"] = mids,
            ["referenced_by_packages"] = refPkgs,
            ["referenced_modules"] = refMods,
        };
    }

    /// <summary>统一入口：自动判别 target 是 protocol id 还是 module id。</summary>
    public static Dictionary<string, object?> ImpactOfChange(Dictionary<string, object?> registry, string target)
    {
        if (Protocols(registry).Any(p => p.GetValueOrDefault("id") as string == target))
            return RemovalImpactProtocol(registry, target);
        var n = Norm(target);
        var exists = Modules(registry).Any(m => Norm(m.GetValueOrDefault("id")) == n)
                     || Protocols(registry).Any(p => (p.GetValueOrDefault("module_ids") as List<object?> ?? new List<object?>())
                         .Select(Norm).Contains(n));
        if (exists) return RemovalImpact(registry, target);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["target"] = target,
            ["error"] = $"registry 无该目标（protocol/module 均 miss）: {PyScalar.PyRepr(target)}",
        };
    }

    /// <summary>文件级便捷入口：读 registry.json → integrity issues（check21 接线）。</summary>
    public static List<string> CheckRegistry(string path)
        => RegistryIntegrityIssues(LoadRegistry(path));

    /// <summary>读 registry.json（缺件 / 解析失败 → 空表；调用方按"取不到"处理）。</summary>
    public static Dictionary<string, object?> LoadRegistry(string path)
    {
        if (!File.Exists(path)) return new Dictionary<string, object?>(StringComparer.Ordinal);
        try
        {
            using var doc = JsonIo.ReadFile(path);
            return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        }
        catch (Exception exc) when (exc is System.Text.Json.JsonException or IOException)
        {
            return new Dictionary<string, object?>(StringComparer.Ordinal);
        }
    }

    private static List<Dictionary<string, object?>> Protocols(Dictionary<string, object?> registry)
        => (registry.GetValueOrDefault("protocols") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();

    private static List<Dictionary<string, object?>> Modules(Dictionary<string, object?> registry)
        => (registry.GetValueOrDefault("modules") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();

    private static string PyText(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        _ => PyScalar.PyRepr(v),
    };
}
