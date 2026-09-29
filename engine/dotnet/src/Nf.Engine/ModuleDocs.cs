namespace Nf.Engine;

/// <summary>
/// 模块契约文档的发现与解析（等价 <c>conformance_scan._module_docs</c> + <c>_fence_yaml</c>）：
/// `04_模块库/**/*.md` + `community/*/modules/*.md`，**全局按路径排序**；取含
/// <c>machine_contract</c> 且顶层是映射、<c>id</c> 非空的契约块。
/// </summary>
public static class ModuleDocs
{
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    /// <summary>全部模块文档（仓库相对 posix 路径，已全局排序）。</summary>
    public static List<string> Files(string root)
    {
        var found = new List<string>();
        var core = Path.Combine(root, "04_模块库");
        if (Directory.Exists(core))
        {
            foreach (var file in Directory.GetFiles(core, "*", SearchOption.AllDirectories)
                         .Where(f => f.EndsWith(".md", StringComparison.Ordinal)))
            {
                found.Add(Rel(root, file));
            }
        }
        var community = Path.Combine(root, "community");
        if (Directory.Exists(community))
        {
            foreach (var pack in Directory.GetDirectories(community)
                         .OrderBy(d => Path.GetFileName(d), StringComparer.Ordinal))
            {
                var modules = Path.Combine(pack, "modules");
                if (!Directory.Exists(modules)) continue;
                foreach (var file in Directory.GetFiles(modules)
                             .Where(f => f.EndsWith(".md", StringComparison.Ordinal))
                             .OrderBy(f => Path.GetFileName(f), StringComparer.Ordinal))
                {
                    found.Add(Rel(root, file));
                }
            }
        }
        found.Sort(StringComparer.Ordinal);
        return found;
    }

    /// <summary>→ (相对路径, machine_contract 映射, id 字符串)：只含「契约块是映射且 id 非空」的件。</summary>
    public static IEnumerable<(string Rel, Dictionary<string, object?> Contract, string Id)> Contracts(string root)
    {
        foreach (var rel in Files(root))
        {
            var path = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            var text = StrictUtf8.GetString(File.ReadAllBytes(path));
            var parsed = MiniYaml.ParseFence(text, "machine_contract");
            if (parsed is null) continue;
            if (!parsed.TryGetValue("machine_contract", out var block)) continue;
            if (block is not Dictionary<string, object?> contract) continue;
            var id = contract.TryGetValue("id", out var idValue) && idValue is not null
                ? idValue.ToString() ?? ""
                : "";
            if (id.Length == 0) continue;
            yield return (rel, contract, id);
        }
    }

    private static string Rel(string root, string full)
        => Path.GetRelativePath(root, full).Replace('\\', '/');
}
