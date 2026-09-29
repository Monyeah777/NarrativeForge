namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/knowledge_sig.py::diff_signatures</c>（41 波C C2）：两份签名 → 字段级差异 + 兼容判定 + 影响度三档。
///
/// 判据自含（真源注释即规则）：
/// <list type="bullet">
/// <item><b>verdict</b>：文档编号变更 → 破坏；存在移除项（refs / headings）→ 需评审；版本演进 → 兼容（版本演进）；否则兼容；</item>
/// <item><b>impact</b>（43 A3，<c>protocol/EXTENSION.md</c> 判据表）：编号变 / 有移除 / 版本 bump → <c>bump</c>；有新增 → <c>additive</c>；否则 <c>editorial</c>。</item>
/// </list>
/// 标量字段按 <b>Python 相等</b>比较（<c>None != ""</c>、<c>1 == True</c>）；列表字段按**集合差**比较后再排序，
/// 故同一份内容里条目的先后不影响判定。
/// </summary>
public static class SignatureDiff
{
    private static readonly string[] ScalarFields =
    {
        "kind", "doc_id", "title", "version", "self_id",
        "layer", "category", "heading_count",
        "meta_line_count", "line_count", "body_hash",
    };

    private static readonly string[] ListFields = { "headings", "schema_names", "refs" };

    public static Dictionary<string, object?> Diff(
        Dictionary<string, object?> a, Dictionary<string, object?> b)
    {
        var changes = new List<Dictionary<string, object?>>();
        foreach (var f in ScalarFields)
        {
            var va = a.GetValueOrDefault(f);
            var vb = b.GetValueOrDefault(f);
            if (PyScalar.PyEquals(va, vb)) continue;
            changes.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["field"] = f, ["from"] = va, ["to"] = vb, ["kind"] = "字段变更",
            });
        }
        foreach (var f in ListFields)
        {
            var sa = new HashSet<string>(AsStrings(a.GetValueOrDefault(f)), StringComparer.Ordinal);
            var sb = new HashSet<string>(AsStrings(b.GetValueOrDefault(f)), StringComparer.Ordinal);
            foreach (var x in sa.Except(sb).OrderBy(v => v, StringComparer.Ordinal))
                changes.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = f, ["from"] = x, ["to"] = null, ["kind"] = "移除",
                });
            foreach (var x in sb.Except(sa).OrderBy(v => v, StringComparer.Ordinal))
                changes.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["field"] = f, ["from"] = null, ["to"] = x, ["kind"] = "新增",
                });
        }

        var removed = changes.Where(c => (string)c["kind"]! == "移除"
                                         && c["field"] is "refs" or "headings").ToList();
        var removedAny = changes.Any(c => (string)c["kind"]! == "移除");
        var addedAny = changes.Any(c => (string)c["kind"]! == "新增");

        var docA = a.GetValueOrDefault("doc_id");
        var docB = b.GetValueOrDefault("doc_id");
        var docIdChanged = IsTruthy(docA) && IsTruthy(docB) && !PyScalar.PyEquals(docA, docB);
        var versionBump = !PyScalar.PyEquals(a.GetValueOrDefault("version"), b.GetValueOrDefault("version"));

        string verdict;
        if (docIdChanged) verdict = "破坏（文档编号变更）";
        else if (removed.Count > 0) verdict = "需评审（存在移除项：引用/章节收缩）";
        else if (versionBump) verdict = "兼容（版本演进）";
        else verdict = "兼容";

        string impact;
        if (docIdChanged || removedAny || versionBump) impact = "bump";
        else if (addedAny) impact = "additive";
        else impact = "editorial";

        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["from"] = a.GetValueOrDefault("path"),
            ["to"] = b.GetValueOrDefault("path"),
            ["verdict"] = verdict,
            ["impact"] = impact,
            ["changes"] = changes.Cast<object?>().ToList(),
        };
    }

    private static IEnumerable<string> AsStrings(object? v) =>
        (v as List<object?> ?? new List<object?>()).Select(PyText);

    private static string PyText(object? v) => v switch
    {
        null => "None",
        string s => s,
        bool b => b ? "True" : "False",
        long l => l.ToString(System.Globalization.CultureInfo.InvariantCulture),
        int i => i.ToString(System.Globalization.CultureInfo.InvariantCulture),
        _ => PyScalar.PyRepr(v),
    };

    private static bool IsTruthy(object? v) => v switch
    {
        null => false,
        bool b => b,
        string s => s.Length > 0,
        long l => l != 0,
        int i => i != 0,
        _ => true,
    };
}
