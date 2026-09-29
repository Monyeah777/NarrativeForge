namespace Nf.Engine;

/// <summary>
/// 复刻 <c>pack_combo.py::_module_contracts</c> 与 <c>::_core_contracts</c> 的契约抽取与**别名语义**
/// （<c>out[id] = rec</c> 覆盖写；<c>setdefault(stem)</c> / <c>setdefault(裸号)</c> 先到先得）。
/// </summary>
public static class ModuleContracts
{
    public sealed record Contract(
        string Id,
        string Stem,
        string Pack,
        string Layer,
        IReadOnlyList<string> Inputs,
        IReadOnlyList<string> Outputs,
        IReadOnlyList<string> Publish,
        IReadOnlyList<string> Subscribe,
        string Path);

    public sealed record CoreContract(
        string Id,
        string Stem,
        IReadOnlyList<string> Publish,
        IReadOnlyList<string> Subscribe,
        string Path);

    public sealed record Extraction(
        IReadOnlyDictionary<string, Contract> RecordsByKey,
        IReadOnlyDictionary<string, string> KeyToId);

    /// <summary>缺契约时的占位记录（等价 Python <c>profiles</c> 里的 fallback dict：path 为空 → 记 module_missing_contract）。</summary>
    public static Contract FallbackContract(string id, string pack)
        => new(id, id, pack, "", new List<string>(), new List<string>(), new List<string>(), new List<string>(), "");

    /// <summary>community/&lt;pack&gt;/modules/*.md → 契约（含别名键）。</summary>
    public static Extraction Community(string root)
    {
        var byKey = new Dictionary<string, Contract>(StringComparer.Ordinal);
        var keyToId = new Dictionary<string, string>(StringComparer.Ordinal);
        var community = Path.Combine(root, "community");
        if (!Directory.Exists(community)) return new Extraction(byKey, keyToId);

        var docs = new List<string>();
        foreach (var packDir in Directory.GetDirectories(community).OrderBy(d => Path.GetFileName(d), StringComparer.Ordinal))
        {
            var modulesDir = Path.Combine(packDir, "modules");
            if (!Directory.Exists(modulesDir)) continue;
            docs.AddRange(Directory.GetFiles(modulesDir, "*.md")
                .OrderBy(f => RelativePosix(root, f), StringComparer.Ordinal));
        }

        foreach (var doc in docs)
        {
            var mc = MachineContractOf(doc);
            if (mc is null) continue;
            var stem = Path.GetFileNameWithoutExtension(doc).Split('_')[0];
            var id = Text(mc, "id") is { Length: > 0 } explicitId ? explicitId : stem;
            var pack = Path.GetFileName(Path.GetDirectoryName(Path.GetDirectoryName(doc)!)!)!;
            var rec = new Contract(
                id,
                stem,
                pack,
                Text(mc, "layer"),
                Sequence(mc, "inputs"),
                Sequence(mc, "outputs"),
                NestedSequence(mc, "events", "publish"),
                NestedSequence(mc, "events", "subscribe"),
                RelativePosix(root, doc));
            byKey[id] = rec;
            keyToId[id] = rec.Id;
            AddAlias(byKey, keyToId, stem, rec);
            AddAlias(byKey, keyToId, id.Split(':')[^1], rec);
        }
        return new Extraction(byKey, keyToId);
    }

    /// <summary>04_模块库/*/*.md → 核心契约（含别名键）。</summary>
    public static IReadOnlyDictionary<string, CoreContract> Core(string root)
    {
        var byKey = new Dictionary<string, CoreContract>(StringComparer.Ordinal);
        var baseDir = Path.Combine(root, "04_模块库");
        if (!Directory.Exists(baseDir)) return byKey;

        var docs = Directory.GetDirectories(baseDir)
            .OrderBy(d => Path.GetFileName(d), StringComparer.Ordinal)
            .SelectMany(d => Directory.GetFiles(d, "*.md").OrderBy(f => RelativePosix(root, f), StringComparer.Ordinal))
            .ToList();

        foreach (var doc in docs)
        {
            var mc = MachineContractOf(doc);
            if (mc is null) continue;
            var stem = Path.GetFileNameWithoutExtension(doc).Split('_')[0];
            var id = Text(mc, "id") is { Length: > 0 } explicitId ? explicitId : stem;
            var rec = new CoreContract(id, stem,
                NestedSequence(mc, "events", "publish"),
                NestedSequence(mc, "events", "subscribe"),
                RelativePosix(root, doc));
            byKey[id] = rec;
            byKey.TryAdd(stem, rec);
        }
        return byKey;
    }

    private static void AddAlias(Dictionary<string, Contract> byKey, Dictionary<string, string> keyToId, string alias, Contract rec)
    {
        if (byKey.ContainsKey(alias)) return;   // setdefault：先到先得
        byKey[alias] = rec;
        keyToId[alias] = rec.Id;
    }

    /// <summary>取模块文档的 <c>machine_contract</c> 围栏（缺件 / 非映射 / 空映射 → null）。</summary>
    public static Dictionary<string, object?>? MachineContractOf(string docPath)
    {
        string text;
        try { text = File.ReadAllText(docPath); }
        catch (IOException) { return null; }

        var body = MiniYaml.ExtractFence(text, "machine_contract");
        if (body is null) return null;
        var parsed = MiniYaml.Parse(body);
        if (!parsed.TryGetValue("machine_contract", out var node) ||
            node is not Dictionary<string, object?> mc || mc.Count == 0)
        {
            return null;
        }
        return mc;
    }

    private static string Text(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var v) && v is string s ? s : "";

    private static List<string> Sequence(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var v) && v is List<object?> list
            ? list.Select(x => x?.ToString() ?? "").ToList()
            : new List<string>();

    private static List<string> NestedSequence(Dictionary<string, object?> map, string outer, string inner)
        => map.TryGetValue(outer, out var v) && v is Dictionary<string, object?> nested
            ? Sequence(nested, inner)
            : new List<string>();

    public static string RelativePosix(string root, string fullPath)
        => Path.GetRelativePath(root, fullPath).Replace('\\', '/');
}
