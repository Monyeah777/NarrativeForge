using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>pack_combo.py::profiles</c>（每包组合画像）与 <c>::_pack_assets</c>。
/// 画像是组合解算（<c>combine</c>）的唯一输入面。
/// </summary>
public static class PackProfiles
{
    public sealed record Asset(string Key, string File, string Module, string SourcePackage);

    public sealed record Profile(
        string Package,
        string Pipeline,
        IReadOnlyList<string> Modules,
        IReadOnlyList<ProtocolYaml.Reference> References,
        IReadOnlyDictionary<string, IReadOnlyList<string>> Layers,
        IReadOnlyList<Asset> Assets,
        IReadOnlyList<string> Publishes,
        IReadOnlyList<string> Subscribes);

    /// <summary>缺契约时的占位记录（等价 Python 的 fallback dict）。</summary>
    private static ModuleContracts.Contract Fallback(string id, string pack)
        => ModuleContracts.FallbackContract(id, pack);

    public static SortedDictionary<string, Profile> Build(string root)
        => RepoCache.For(root).Profiles;

    /// <summary>不做缓存解析的原始实现（由 <see cref="RepoCache"/> 调用一次）。</summary>
    public static SortedDictionary<string, Profile> BuildUncached(
        string root, IReadOnlyDictionary<string, ModuleContracts.Contract> contracts)
    {
        var output = new SortedDictionary<string, Profile>(StringComparer.Ordinal);

        var community = Path.Combine(root, "community");
        if (!Directory.Exists(community)) return output;

        foreach (var packDir in Directory.GetDirectories(community)
                     .Where(d => File.Exists(Path.Combine(d, "protocol.yaml")))
                     .OrderBy(d => Path.GetFileName(d), StringComparer.Ordinal))
        {
            var packName = Path.GetFileName(packDir);
            var text = File.ReadAllText(Path.Combine(packDir, "protocol.yaml"));
            var parsed = ProtocolYaml.Parse(text, packName);

            var own = new List<ModuleContracts.Contract>();
            foreach (var moduleId in parsed.ModuleIds)
            {
                var key = moduleId;
                if (!contracts.TryGetValue(key, out var rec))
                {
                    var bare = moduleId.Split(':')[^1];
                    contracts.TryGetValue(bare, out rec);
                }
                own.Add(rec ?? Fallback(moduleId, parsed.Id));
            }

            var layers = new Dictionary<string, List<string>>(StringComparer.Ordinal);
            foreach (var rec in own)
            {
                if (rec.Layer.Length == 0) continue;
                if (!layers.TryGetValue(rec.Layer, out var bucket)) layers[rec.Layer] = bucket = new List<string>();
                if (!bucket.Contains(rec.Id, StringComparer.Ordinal)) bucket.Add(rec.Id);
            }

            var layersSorted = new SortedDictionary<string, IReadOnlyList<string>>(StringComparer.Ordinal);
            foreach (var kv in layers)
            {
                layersSorted[kv.Key] = kv.Value.OrderBy(x => x, StringComparer.Ordinal).Distinct(StringComparer.Ordinal).ToList();
            }

            var publishes = own.SelectMany(r => r.Publish).Distinct(StringComparer.Ordinal)
                .OrderBy(x => x, StringComparer.Ordinal).ToList();
            var subscribes = own.SelectMany(r => r.Subscribe).Distinct(StringComparer.Ordinal)
                .OrderBy(x => x, StringComparer.Ordinal).ToList();

            output[parsed.Id] = new Profile(
                parsed.Id,
                parsed.Pipeline,
                own.Select(r => r.Id).ToList(),
                parsed.References,
                layersSorted,
                PackAssets(root, packName),
                publishes,
                subscribes);
        }
        return output;
    }

    /// <summary>community/&lt;pack&gt;/assets/provenance.json → 资产清单。</summary>
    public static IReadOnlyList<Asset> PackAssets(string root, string packDir)
    {
        var path = Path.Combine(root, "community", packDir, "assets", "provenance.json");
        if (!File.Exists(path)) return new List<Asset>();
        try
        {
            using var doc = JsonIo.ReadFile(path);
            if (!doc.RootElement.TryGetProperty("assets", out var assets) || assets.ValueKind != JsonValueKind.Array)
                return new List<Asset>();
            var list = new List<Asset>();
            foreach (var a in assets.EnumerateArray())
            {
                list.Add(new Asset(
                    Str(a, "key"), Str(a, "file"), Str(a, "module"), packDir));
            }
            return list;
        }
        catch (JsonException)
        {
            return new List<Asset>();
        }
    }

    private static string Str(JsonElement obj, string name)
        => obj.TryGetProperty(name, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString()! : "";
}
