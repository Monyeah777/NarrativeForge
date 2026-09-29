using System.Text.RegularExpressions;

namespace Nf.Engine;

/// <summary>
/// 复刻 <c>core/endpoint.py</c>：服务端点契约门禁（NF 不产服务，本件只固定"若暴露成服务长什么样"）。
///
/// 核心判据：每个端点的 <c>maps_to</c> 必须指向**当下真实存在**的 CLI 子命令或 MCP 工具——契约不许指向空气。
/// 另有：method/status/id 词表与唯一性、streaming 须有 SSE 约定、**幂等语义不许沉默**（RFC 9110 §9.2.2），
/// 以及弃用语义（OpenAPI deprecated + RFC 8594 Sunset）：有标志就必须有出口（sunset / replacement / 约定）。
///
/// **镜像说明**：CLI 子命令表从 <c>scripts/nf.py</c> 的 <c>sub.add_parser("…")</c> 现扫（不是镜像）；
/// MCP 工具表复用 <see cref="McpPackage.RuntimeTools"/>（与 B 线包装同一份镜像，漂移由双跑对账兜住）。
/// </summary>
public static class EndpointContract
{
    public const string ContractRel = "protocol/endpoint_contract.json";
    public const string Schema = "nf-endpoint/1";
    public const string ContractDescription = "服务端点契约指向真实性";

    private static readonly string[] Statuses = { "proposed", "implemented" };
    private static readonly string[] Methods = { "GET", "POST", "PUT", "PATCH", "DELETE" };
    private static readonly string[] IdempotencyModes = { "idempotent", "non-idempotent" };
    private static readonly string[] IdempotencyKeys = { "required", "none" };
    private static readonly Regex McpRef = new(@"^([a-z_]+)（MCP 工具）$");
    private static readonly Regex CliRef = new(@"^nf\s+([a-z-]+)");
    private static readonly Regex Dated = new(@"^\d{4}-\d{2}-\d{2}$");
    private static readonly Regex CliParser = new(@"sub\.add_parser\(\s*""([a-z-]+)""");
    private static readonly System.Text.UTF8Encoding StrictUtf8 = new(false, throwOnInvalidBytes: true);

    public static (bool Ok, string Detail) Contract(string root)
    {
        var (issues, _, stats) = Scan(root);
        if (issues.Count > 0) return (false, string.Join("; ", issues.Take(2)));
        return (true, $"端点 {stats.GetValueOrDefault("endpoints")}（status={stats.GetValueOrDefault("status")}）");
    }

    /// <summary>
    /// 原始契约对象（等价 Python <c>endpoint.load()</c> = <c>json.loads(protocol/endpoint_contract.json)</c>）——
    /// 供 <c>nf endpoint --json</c> 与 Python 逐字节对齐（含 conventions / idempotency_exceptions 全字段）。
    /// </summary>
    public static Dictionary<string, object?> Load(string root)
    {
        var path = Path.Combine(root, ContractRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path)) return new Dictionary<string, object?>(StringComparer.Ordinal);
        using var doc = JsonIo.ReadFile(path);
        return PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
    }

    public static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) Scan(string root)
    {
        var issues = new List<string>();
        var warns = new List<string>();
        var empty = new Dictionary<string, object?>(StringComparer.Ordinal);
        var path = Path.Combine(root, ContractRel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(path))
            return (new List<string> { $"缺端点契约 {ContractRel}（修复指引：见 protocol/endpoint_contract.json）" },
                warns, empty);

        using var doc = JsonIo.ReadFile(path);
        var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        if (Str(graph, "schema") != Schema)
            issues.Add($"端点契约 schema 不匹配（期望 {Schema}）");
        var status = Str(graph, "status");
        if (Array.IndexOf(Statuses, status) < 0)
            issues.Add($"status 越词表：{status}（{string.Join("/", Statuses)}）");
        if (status == "proposed")
            warns.Add("端点契约状态 = proposed（服务本体未实现，本契约只固定形状）");

        var conventions = graph.GetValueOrDefault("conventions") as Dictionary<string, object?>
                          ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var tools = McpPackage.RuntimeTools.ToHashSet(StringComparer.Ordinal);
        var commands = CliCommands(root);
        var endpoints = Rows(graph, "endpoints");
        var allIds = endpoints.Select(e => Str(e, "id")).ToList();
        var ids = new HashSet<string>(StringComparer.Ordinal);
        var paths = new HashSet<string>(StringComparer.Ordinal);
        foreach (var endpoint in endpoints)
        {
            var id = Str(endpoint, "id");
            if (!ids.Add(id)) issues.Add($"端点 id 重复：{id}");
            var method = Str(endpoint, "method");
            var endpointPath = Str(endpoint, "path");
            if (Array.IndexOf(Methods, method) < 0)
                issues.Add($"{id} 的 method 越词表：{method}");
            var key = $"{method} {endpointPath}";
            if (!paths.Add(key)) issues.Add($"端点 method+path 重复：{key}");
            if (Truthy(endpoint.GetValueOrDefault("streaming"))
                && !Truthy(conventions.GetValueOrDefault("streaming")))
            {
                issues.Add($"{id} 声明 streaming 但 conventions 未定义 SSE 约定");
            }
            var maps = Str(endpoint, "maps_to");
            var mcp = McpRef.Match(maps);
            if (mcp.Success)
            {
                if (!tools.Contains(mcp.Groups[1].Value))
                    issues.Add($"{id} 的 maps_to 指向不存在的 MCP 工具：{mcp.Groups[1].Value}");
            }
            else
            {
                var cli = CliRef.Match(maps);
                if (!cli.Success || !commands.Contains(cli.Groups[1].Value))
                {
                    issues.Add($"{id} 的 maps_to 无法解析为现存 CLI 子命令或 MCP 工具：{maps}" +
                               "（修复指引：改正，或先实现该能力）");
                }
            }

            // 弃用/日落语义：有标志就必须有出口
            var deprecated = endpoint.TryGetValue("deprecated", out var dep) ? dep : null;
            if (deprecated is not null and not bool)
                issues.Add($"{id} 的 deprecated 应为布尔：{PyScalar.PyRepr(deprecated)}");
            if (Truthy(deprecated))
            {
                if (status != "implemented")
                    issues.Add($"{id} 声明 deprecated 但契约 status={status}——未实装的能力没有可弃用的东西" +
                               "（修复指引：先落 implemented 再谈弃用）");
                if (!Truthy(conventions.GetValueOrDefault("deprecation")))
                    issues.Add($"{id} 声明 deprecated 但 conventions 未定义弃用约定");
                if (!Dated.IsMatch(Str(endpoint, "sunset")))
                    issues.Add($"{id} 声明 deprecated 但缺合规 sunset（YYYY-MM-DD）：" +
                               $"{PyScalar.PyRepr(endpoint.GetValueOrDefault("sunset"))}" +
                               "（修复指引：按 RFC 8594 给出日落日期）");
                if (!endpoint.ContainsKey("replacement"))
                {
                    issues.Add($"{id} 声明 deprecated 但缺 replacement（无替代写 null，不许省略）");
                }
                else
                {
                    var replacement = endpoint.GetValueOrDefault("replacement");
                    if (replacement is not null && !allIds.Contains(replacement.ToString() ?? ""))
                    {
                        issues.Add($"{id} 的 replacement 指向契约内不存在的端点：{PyScalar.PyRepr(replacement)}" +
                                   "（修复指引：改为契约内端点 id，或写 null 表示无替代）");
                    }
                }
            }
            else if (endpoint.ContainsKey("sunset") || endpoint.ContainsKey("replacement"))
            {
                issues.Add($"{id} 未声明 deprecated 却带 sunset/replacement（悬空弃用字段）");
            }
        }

        // 幂等声明面：默认幂等，例外须登记且非幂等端点须给幂等键策略
        if (!Truthy(conventions.GetValueOrDefault("idempotency")))
        {
            issues.Add("conventions 未声明幂等语义（修复指引：按 RFC 9110 §9.2.2 写明默认幂等 + " +
                       "例外登记规则——幂等性是重试安全的前提，不许沉默）");
        }
        var exceptions = Rows(graph, "idempotency_exceptions");
        var seenExceptions = new HashSet<string>(StringComparer.Ordinal);
        foreach (var exception in exceptions)
        {
            var id = Str(exception, "id");
            if (!ids.Contains(id))
            {
                issues.Add("幂等例外指向契约内不存在的端点：" + PyScalar.PyRepr(id) +
                           "（修复指引：改为契约内端点 id，或删除该例外）");
                continue;
            }
            if (!seenExceptions.Add(id)) issues.Add($"幂等例外重复登记端点：{id}");
            var mode = Str(exception, "mode");
            if (Array.IndexOf(IdempotencyModes, mode) < 0)
            {
                issues.Add($"幂等例外 mode 越词表：{id} = {PyScalar.PyRepr(mode)}（允许 {string.Join("/", IdempotencyModes)}）");
            }
            else if (mode == "non-idempotent")
            {
                var keyPolicy = Str(exception, "key");
                if (Array.IndexOf(IdempotencyKeys, keyPolicy) < 0)
                {
                    issues.Add($"非幂等端点 {id} 缺幂等键策略（修复指引：key ∈ {string.Join("/", IdempotencyKeys)}——" +
                               "required = 须幂等键去重；none = 明示不可重放并写 why）");
                }
                else if (keyPolicy == "required" && !Truthy(conventions.GetValueOrDefault("idempotency")))
                {
                    issues.Add($"幂等例外要求幂等键但 conventions 未定义幂等语义：{id}");
                }
            }
            if (Str(exception, "why").Trim().Length == 0)
                issues.Add("幂等例外缺 why（修复指引：写明为何非幂等、重放会发生什么）");
        }

        var stats = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["status"] = status,
            ["endpoints"] = endpoints.Count,
            ["streaming"] = endpoints.Count(e => Truthy(e.GetValueOrDefault("streaming"))),
            ["cli_commands"] = commands.Count,
            ["mcp_tools"] = tools.Count,
            ["idempotency_exceptions"] = exceptions.Count,
        };
        return (issues, warns, stats);
    }

    /// <summary>CLI 子命令注册表：现扫 <c>scripts/nf.py</c> 的 <c>sub.add_parser("…")</c>（同 Python）。</summary>
    public static HashSet<string> CliCommands(string root)
    {
        var path = Path.Combine(root, "scripts", "nf.py");
        if (!File.Exists(path)) return new HashSet<string>(StringComparer.Ordinal);
        var text = StrictUtf8.GetString(File.ReadAllBytes(path));
        return CliParser.Matches(text).Select(m => m.Groups[1].Value).ToHashSet(StringComparer.Ordinal);
    }

    private static List<Dictionary<string, object?>> Rows(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is List<object?> list
            ? list.OfType<Dictionary<string, object?>>().ToList()
            : new List<Dictionary<string, object?>>();

    private static string Str(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is not null ? value.ToString() ?? "" : "";

    /// <summary>Python 真值判定：非空字符串 / 非空表 / true 都算真。</summary>
    private static bool Truthy(object? value) => value switch
    {
        null => false,
        bool flag => flag,
        string text => text.Length > 0,
        List<object?> list => list.Count > 0,
        _ => true,
    };
}
