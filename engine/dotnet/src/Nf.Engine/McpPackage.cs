namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/mcp_package.py</c>：B 线包装声明门禁（内容质检 MCP 包）。
///
/// 核心判据是红线「**只读面不变**」：声明里的 tools/prompts 必须与运行时逐名一致
/// （多一个少一个即 FAIL）——这样"上架材料写的工具列表"永远不会与真实运行时漂移。
///
/// **镜像说明**：运行时的工具/提示面取自 <c>core/mcp_runtime.TOOL_DEFS/PROMPT_DEFS</c>
/// （引擎不导入 Python，故机械导出为下表）。仓库若增删工具而只改运行时，本表会滞后——
/// 该漂移由**双跑对账**兜住（契约 ok/detail 会立刻不一致），不自愈。
/// </summary>
public static class McpPackage
{
    public const string DeclRel = "protocol/mcp_package.json";
    public const string Schema = "nf-mcp-package/1";
    public const string ContractDescription = "B 线包装声明（工具面与运行时一致）";

    private static readonly string[] Categories =
        { "content-creation", "developer-tools", "knowledge-management" };

    /// <summary>镜像 <c>mcp_runtime.TOOL_DEFS</c> 的工具名（同一 HEAD 导出，顺序即运行时顺序）。</summary>
    public static readonly string[] RuntimeTools =
    {
        "pipeline_ls", "spec_ls", "registry_query", "library_search", "library_read",
        "pattern_read", "knowledge_order", "module_read", "pipeline_read", "asset_get",
    };

    /// <summary>镜像 <c>mcp_runtime.PROMPT_DEFS</c> 的提示名。</summary>
    public static readonly string[] RuntimePrompts = { "assemble_guide" };

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _, stats) = Scan(root);
        if (issues.Count > 0) return (false, string.Join("; ", issues.Take(2)));
        var detail = $"工具 {stats["tools"]} · 提示 {stats["prompts"]} · " +
                     $"类目 {stats["category"]} · 目标平台 {stats["targets"]}";
        return (true, detail);
    }

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var empty = new Dictionary<string, object?>(StringComparer.Ordinal);
        var path = Path.Combine(root, DeclRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return (new List<string> { $"缺 B 线包装声明 {DeclRel}" }, warns, empty);

        Dictionary<string, object?> decl;
        try
        {
            using var doc = JsonIo.ReadFile(path);
            decl = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        }
        catch (Exception exc)
        {
            return (new List<string> { $"缺 B 线包装声明 {DeclRel}（解析失败：{exc.Message}）" }, warns, empty);
        }

        if (Str(decl, "schema") != Schema)
            issues.Add($"包装声明 schema 不匹配（期望 {Schema}）");
        if (!List(decl, "category_vocabulary").SequenceEqual(Categories, StringComparer.Ordinal))
            issues.Add($"类目词表与判据不一致（期望 {string.Join("/", Categories)}）");
        if (List(decl, "red_lines").Count == 0)
            issues.Add("红线不得为空（上架包的纪律必须成文）");
        if (Str(decl, "status") == "draft" && List(decl, "pending").Count == 0)
            issues.Add("status=draft 但 pending 为空——草案必须写明还差什么");

        var pkg = decl.TryGetValue("package", out var packageValue)
                  && packageValue is Dictionary<string, object?> packageMap
            ? packageMap
            : new Dictionary<string, object?>(StringComparer.Ordinal);
        if (List(pkg, "name_candidates").Count == 0) issues.Add("缺命名候选（B-S1 须给候选）");
        if (List(pkg, "one_liner_candidates").Count == 0) issues.Add("缺一句话候选（B-S1 须给候选）");
        if (Array.IndexOf(Categories, Str(pkg, "category")) < 0)
            issues.Add($"类目越词表：{Str(pkg, "category")}");

        var gotTools = List(pkg, "tools");
        var gotPrompts = List(pkg, "prompts");
        var liveTools = RuntimeTools.ToList();
        var livePrompts = RuntimePrompts.ToList();
        if (!gotTools.OrderBy(x => x, StringComparer.Ordinal).SequenceEqual(
                liveTools.OrderBy(x => x, StringComparer.Ordinal), StringComparer.Ordinal))
        {
            var more = gotTools.Except(liveTools).OrderBy(x => x, StringComparer.Ordinal).ToList();
            var less = liveTools.Except(gotTools).OrderBy(x => x, StringComparer.Ordinal).ToList();
            issues.Add($"工具面与运行时不一致（上架材料会漂移）：声明 {gotTools.Count} 个 / 运行时 {liveTools.Count} 个" +
                       $"（多：{PyListOrNone(more)}；少：{PyListOrNone(less)}）");
        }
        if (!gotPrompts.OrderBy(x => x, StringComparer.Ordinal).SequenceEqual(
                livePrompts.OrderBy(x => x, StringComparer.Ordinal), StringComparer.Ordinal))
        {
            issues.Add($"提示面与运行时不一致：声明 {PyScalar.PyRepr(gotPrompts.Cast<object?>().ToList())} / " +
                       $"运行时 {PyScalar.PyRepr(livePrompts.Cast<object?>().ToList())}");
        }

        var pending = List(decl, "pending");
        if (pending.Count > 0)
            warns.Add($"包装声明为草案：{pending.Count} 项待补（{string.Join("；", pending.Take(2))}）");

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["tools"] = gotTools.Count,
            ["prompts"] = gotPrompts.Count,
            ["targets"] = List(pkg, "targets").Count,
            ["category"] = Str(pkg, "category"),
        };
        return (issues, warns, stats);
    }

    private static string PyListOrNone(List<string> items)
        => items.Count == 0 ? "无" : PyScalar.PyRepr(items.Cast<object?>().ToList());

    private static string Str(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var v) && v is not null ? v.ToString() ?? "" : "";

    private static List<string> List(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var v) && v is List<object?> items
            ? items.Select(x => x?.ToString() ?? "").ToList()
            : new List<string>();
}
