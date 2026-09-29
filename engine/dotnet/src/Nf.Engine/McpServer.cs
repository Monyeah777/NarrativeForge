using System.Text;
using System.Text.Json;

namespace Nf.Engine;

/// <summary>
/// NF .NET 引擎的 MCP stdio 服务器：**协议机制与仓库侧 <c>core/mcp_runtime.py</c> 对齐**
/// （JSON-RPC 2.0 · 换行分隔帧 · dual-era 版本处理 · 可缓存结果三键 · 同一套错误码与消息），
/// **工具目录不同**——这里暴露的是本引擎自己的只读判据面（不回填 Python 侧的快照工具集）。
///
/// 与 Python 侧的差别（刻意）：不需要 mcp 快照，直接对仓库根求解。
/// </summary>
public static class McpServer
{
    public const string ModernVersion = "2026-07-28";
    public const string LegacyVersion = "2025-11-25";
    public static readonly string[] SupportedVersions = { ModernVersion, LegacyVersion };
    public const string JsonRpcVersion = "2.0";

    private const string MetaProtocolVersion = "io.modelcontextprotocol/protocolVersion";
    private const string MetaClientInfo = "io.modelcontextprotocol/clientInfo";
    private const string MetaClientCapabilities = "io.modelcontextprotocol/clientCapabilities";
    private const string MetaServerInfo = "io.modelcontextprotocol/serverInfo";

    private const int ParseError = -32700;
    private const int InvalidRequest = -32600;
    private const int MethodNotFound = -32601;
    private const int InvalidParams = -32602;
    private const int InternalError = -32603;
    private const int UnsupportedProtocolVersion = -32022;

    public const string ServerName = "nf-dotnet-engine";
    public const string ServerVersion = "0.1.0";

    private static readonly (string Name, string Description, Dictionary<string, object?> Schema)[] Tools =
    {
        ("nf_verify", "只读总检：协议回执 / 馆藏回执 / 透明链 / 组合证书 / 断言表 / 决策门禁 / 馆藏条目与投影 / 建模三件", ObjectSchema()),
        ("nf_receipts", "回执复算（scope=protocol|library）", ObjectSchema(("scope", "string", "protocol 或 library，缺省 protocol"))),
        ("nf_transparency", "透明链复算（哈希链自洽 + 在盘生成物一致）", ObjectSchema()),
        ("nf_combine_verify", "组合证书 T4 复算（按 packs+extra_modules 重算并与在盘证书逐字段比对）", ObjectSchema()),
        ("nf_combine_plan", "组合求解（并集闭包补齐 → 层栈/闭包/借阅 → 证书）", ObjectSchema(("packs", "array", "包名数组"), ("extra_modules", "array", "额外模块 id 数组（可选）"), ("strict_coherence", "boolean", "ISA v1 C1′ 严格相干：撞号即 DENY（默认与 Python 同口径静默塌陷）"))),
        ("nf_assertions", "数据化断言表求值（封闭 kind 集）", ObjectSchema()),
        ("nf_decisions", "决策记录门禁（ADR 编号/状态/取代链/证据/回执锚定/INDEX 投影）", ObjectSchema()),
        ("nf_cognition", "认知族门禁（术语表真源逐字命中 + 执行分档结构块）", ObjectSchema()),
        ("nf_library", "馆藏门（frontmatter + 签名锚漂移 + INDEX/ALIAS 投影）", ObjectSchema()),
        ("nf_model", "内容建模三件（part=vocab|normative|contracts，缺省三件全跑）", ObjectSchema(("part", "string", "vocab / normative / contracts"))),
        ("nf_sig", "知识签名（verify=true 时跑两遍一致性证明）", ObjectSchema(("verify", "boolean", "true=只跑可复现性校验"))),
        ("nf_bench", "性能基线测量（八项关键操作）", ObjectSchema()),
        ("nf_patterns_list", "实践包清单（id / 名称 / 状态 / 适用面；真源 = 各包 frontmatter，投影 = patterns/INDEX.md）", ObjectSchema()),
        ("nf_patterns_for", "反向查询：某文件适用哪些实践包（含通配符走 fnmatch，Windows 下大小写不敏感）", ObjectSchema(("target", "string", "目标路径（仓库相对，如 protocol/RECEIPTS.json）"))),
        ("nf_patterns_verify", "实践包门禁（必填字段 / 可证性 / INDEX 投影一致 → issues/warns/projection/stats）", ObjectSchema()),
        ("nf_stats", "自述数字实算（README / README.en / llms.txt 生成区 == 实算；在盘 repo_stats.json == 实算）", ObjectSchema()),
        ("nf_interop", "互操作导出面：kind 缺省列 12 形状清单；给 kind 返回该形状派生文档；check=true 跑导出面门禁", ObjectSchema(("kind", "string", "导出形状（openapi/asyncapi/intoto/sbom/slsa/a2a/prov/cyclonedx/vc/c2pa/cid/decisions）"), ("check", "boolean", "true=跑门禁（覆盖完整 + 形状合法 + 确定性）"))),
        ("nf_st_validate", "ST 制卡校验器（卡 / 世界书 / MVU 变量 JSON → R1/R3/R4 可自动化项报告；只读，不落报告文件）", ObjectSchema(("path", "string", "被校验 JSON 的路径"))),
        // —— 以下三个与仓库侧 mcp_runtime 的**同名同形**：工具级逐字节对账已实测（见 README 第二十四片）
        ("pipeline_ls", "列出 NF 管线清单（03_管线库 + community 包 pipelines）", ObjectSchema(("query", "string", "可选过滤串（匹配 id/标题）"))),
        ("spec_ls", "列出 registry protocols 协议包清单（id/version/模块数/类别）", ObjectSchema()),
        ("registry_query", "查询 registry 模块/协议（按 id/name 子串匹配，只读）", ObjectSchema(("query", "string", "检索串（如 M90 或 域包 id）"))),
        ("library_read", "取云端图书馆馆藏条目正文（按 NF 编号，大小写不敏感；返回 frontmatter + 全文）", ObjectSchema(("entry_id", "string", "馆藏编号（如 NF-1）"))),
        ("pattern_read", "取实践包（patterns/）正文：按 id 返回 frontmatter + 可执行规则 + 正反例（只读）", ObjectSchema(("pattern_id", "string", "pattern id（如 fail-closed-verification）"))),
        ("module_read", "取模块文档正文（04_模块库 与 community 包 modules；支持全限定 id 与裸号）", ObjectSchema(("module_id", "string", "模块 id（如 M90 / 通用:M10）"))),
        ("pipeline_read", "取管线正文（按 Pxx 编号或仓库内相对路径；只读 03_管线库 与 community/*/pipelines）", ObjectSchema(("pipeline", "string", "Pxx 或相对路径（如 03_管线库/P90….md）"))),
        ("library_search", "仓库侧知识库检索：馆藏条目（正文级）+ docs + community README + 编号方案文档", ObjectSchema(("query", "string", "检索串"))),
        ("knowledge_order", "解析知识源查询顺序（先合同级后参考级；可按可见性 clearance 裁剪）", ObjectSchema(("clearance", "string", "可见性上限（public/internal/restricted）"))),
        ("asset_get", "取资产正文（按资产键；可限定包）", ObjectSchema(("key", "string", "资产键"), ("package", "string", "包名（可选）"))),
    };

    private static Dictionary<string, object?> ObjectSchema(params (string Name, string Type, string Description)[] properties)
    {
        var props = new Dictionary<string, object?>(StringComparer.Ordinal);
        foreach (var (name, type, description) in properties)
        {
            props[name] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["type"] = type, ["description"] = description,
            };
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["type"] = "object", ["properties"] = props,
        };
    }

    /// <summary>等价 Python <c>encode_message</c>：单行 JSON，U+2028/2029/0085 转义（帧边界陷阱）。</summary>
    /// <summary>
    /// 本引擎暴露的工具名。供自检做「真源 <c>core.mcp_runtime.TOOL_DEFS</c> ⊆ 引擎工具面」的**镜像交叉核验**：
    /// <c>ProseLint.CommandFace</c> 用的是真源那 10 个基名（引擎自有 18 个 <c>nf_*</c> 不在其内），
    /// 若引擎的 MCP 面把基名工具删了，这条钉会红。
    /// </summary>
    public static IReadOnlyList<string> ToolNames => Tools.Select(t => t.Name).ToList();

    public static string EncodeMessage(object? message)
        => PythonJson.CanonicalizeGraph(message)
            .Replace("\u2028", "\\u2028").Replace("\u2029", "\\u2029").Replace("\u0085", "\\u0085");

    /// <summary>等价 Python <c>McpRuntime.handle</c>。返回 null 表示"不应答"（通知或非法输入）。</summary>
    public static Dictionary<string, object?>? Handle(string root, JsonElement msg)
    {
        if (msg.ValueKind != JsonValueKind.Object)
            return Err(root, InvalidRequest, "消息必须是 JSON 对象", null, null);
        if (Str(msg, "jsonrpc") != JsonRpcVersion)
            return Err(root, InvalidRequest, $"jsonrpc 版本必须为 {JsonRpcVersion}", null, null);
        if (!msg.TryGetProperty("method", out var methodElement) || methodElement.ValueKind != JsonValueKind.String)
            return Err(root, InvalidRequest, "缺 method", null, null);
        var method = methodElement.GetString()!;

        var isRequest = msg.TryGetProperty("id", out var idElement);
        JsonElement? id = isRequest ? idElement : null;
        if (isRequest && !IsValidId(idElement))
            return Err(root, InvalidRequest, "id 必须是字符串、数字或 null（修复指引：按 JSON-RPC 2.0 §4 用请求序号，勿用结构体/布尔）", null, null);

        JsonElement paramsElement = default;
        var hasParams = msg.TryGetProperty("params", out var p) && p.ValueKind != JsonValueKind.Null;
        if (hasParams)
        {
            paramsElement = p;
            if (p.ValueKind is not (JsonValueKind.Object or JsonValueKind.Array))
                return Err(root, InvalidRequest, "params 必须是结构化值（对象或数组）（修复指引：JSON-RPC 2.0 §4.2——原始类型参数非法）", id, null);
            if (p.ValueKind == JsonValueKind.Array)
                return Err(root, InvalidParams, "params 只接受按名对象（修复指引：改用 {name: value} 形式，本运行时无位置参数面）", id, null);
        }

        // modern 版本协商：请求自带 _meta 版本时逐请求校验
        if (hasParams && paramsElement.TryGetProperty("_meta", out var meta) && meta.ValueKind == JsonValueKind.Object)
        {
            var requested = meta.TryGetProperty(MetaProtocolVersion, out var rv) && rv.ValueKind == JsonValueKind.String
                ? rv.GetString()
                : null;
            if (requested is not null && !SupportedVersions.Contains(requested, StringComparer.Ordinal))
            {
                if (!isRequest) return null;
                return Err(root, UnsupportedProtocolVersion, "Unsupported protocol version", null,
                    new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["supported"] = SupportedVersions.Cast<object?>().ToList(),
                        ["requested"] = requested,
                    });
            }
        }

        Dictionary<string, object?>? result;
        try
        {
            result = Dispatch(root, method, hasParams ? paramsElement : default);
        }
        catch (ArgumentException exc)
        {
            return isRequest ? ErrorAt(InvalidParams, exc.Message, idElement) : null;
        }

        if (result is null)
        {
            return isRequest
                ? ErrorAt(MethodNotFound, $"Method not found: {method}", idElement)
                : null;
        }
        if (!isRequest) return null;
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["jsonrpc"] = JsonRpcVersion, ["id"] = ToNode(idElement), ["result"] = result,
        };
    }

    private static Dictionary<string, object?>? Dispatch(string root, string method, JsonElement parameters)
    {
        switch (method)
        {
            case "server/discover":
                return new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["resultType"] = "complete",
                    ["supportedVersions"] = SupportedVersions.Cast<object?>().ToList(),
                    ["capabilities"] = Capabilities(),
                    ["_meta"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        [MetaServerInfo] = new Dictionary<string, object?>(StringComparer.Ordinal)
                        {
                            ["name"] = ServerName, ["version"] = ServerVersion,
                        },
                    },
                    ["instructions"] = "NF .NET 工业引擎只读判据面：回执/透明链/组合证书/断言表/决策门禁/馆藏门/建模三件/知识签名/性能基线。全部只读，不写仓库。",
                    ["ttlMs"] = 3600000,
                    ["cacheScope"] = "public",
                };
            case "initialize":
                var requested = parameters.ValueKind == JsonValueKind.Object &&
                                parameters.TryGetProperty("protocolVersion", out var pv) && pv.ValueKind == JsonValueKind.String
                    ? pv.GetString()
                    : null;
                var version = requested is not null && SupportedVersions.Contains(requested, StringComparer.Ordinal)
                    ? requested
                    : LegacyVersion;
                return new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["protocolVersion"] = version,
                    ["capabilities"] = Capabilities(),
                    ["serverInfo"] = new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["name"] = ServerName, ["version"] = ServerVersion,
                    },
                };
            case "tools/list":
                return Cacheable(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["tools"] = Tools.Select(t => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["name"] = t.Name, ["description"] = t.Description, ["inputSchema"] = t.Schema,
                    }).ToList(),
                });
            case "tools/call":
                return CallTool(root, parameters);
            case "ping":
                return new Dictionary<string, object?>(StringComparer.Ordinal);
            default:
                return null;
        }
    }

    private static Dictionary<string, object?> CallTool(string root, JsonElement parameters)
    {
        if (parameters.ValueKind != JsonValueKind.Object ||
            !parameters.TryGetProperty("name", out var nameElement) || nameElement.ValueKind != JsonValueKind.String)
            throw new ArgumentException("tools/call 需 params{name, arguments}");
        var name = nameElement.GetString()!;
        var args = parameters.TryGetProperty("arguments", out var a) && a.ValueKind == JsonValueKind.Object ? a : default;

        if (Tools.All(t => t.Name != name))
        {
            throw new ArgumentException($"未知工具：{name}（只读工具面 = {string.Join("、", Tools.Select(t => t.Name).OrderBy(x => x, StringComparer.Ordinal))}）");
        }

        object? payload = name switch
        {
            "nf_verify" => VerifyPayload(root),
            "nf_receipts" => ReceiptsPayload(root, Str(args, "scope") is { Length: > 0 } scope ? scope : "protocol"),
            "nf_transparency" => Receipts.VerifyTransparencyChain(root) is var chain
                ? new Dictionary<string, object?>
                {
                    ["issues"] = chain.Issues.Cast<object?>().ToList(),
                    ["stats"] = new Dictionary<string, object?>
                    {
                        ["head"] = chain.Root[..16], ["links"] = chain.Count, ["issues"] = chain.Issues.Count,
                    },
                } : null,
            "nf_combine_verify" => new Dictionary<string, object?>
            {
                ["rows"] = CertificateVerifier.VerifyAll(root).Select(r => (object?)new Dictionary<string, object?>
                {
                    ["label"] = r.Label, ["legal"] = r.Legal, ["modules"] = r.Modules,
                    ["issues"] = r.Issues.Cast<object?>().ToList(),
                }).ToList(),
            },
            "nf_combine_plan" => Combinator.Build(root, StringList(args, "packs"), StringList(args, "extra_modules"),
                strictCoherence: Bool(args, "strict_coherence")).Certificate,
            "nf_assertions" => AssertionsPayload(root),
            "nf_decisions" => DecisionsPayload(root),
            "nf_cognition" => CognitionPayload(root),
            "nf_library" => LibraryPayload(root),
            "nf_model" => ModelPayload(root, Str(args, "part")),
            "nf_sig" => SigPayload(root, Bool(args, "verify")),
            "nf_bench" => new Dictionary<string, object?>
            {
                ["ops"] = Bench.Run(root).Select(m => (object?)new Dictionary<string, object?>
                {
                    ["name"] = m.Name, ["ms"] = m.Milliseconds, ["detail"] = m.Detail,
                }).ToList(),
            },
            "nf_patterns_list" => Patterns.Entries(root).Select(e => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = e.Fm.TryGetValue("id", out var pid) ? pid : null,
                ["name"] = e.Fm.TryGetValue("name", out var pname) ? pname : null,
                ["status"] = e.Fm.TryGetValue("status", out var pst) ? pst : null,
                ["applies_to"] = e.Fm.TryGetValue("applies_to", out var pat) ? pat : null,
            }).ToList(),
            "nf_patterns_for" => Patterns.ForPath(root, Str(args, "target")).Cast<object?>().ToList(),
            "nf_patterns_verify" => PatternsPayload(root),
            "nf_stats" => RepoStatsPayload(root),
            "nf_interop" => InteropPayload(root, args),
            "nf_st_validate" => StValidate.Validate(ResolvePath(root, Str(args, "path"))),
            "pipeline_ls" => PipelineList(root, Str(args, "query")),
            "spec_ls" => SpecList(root),
            "registry_query" => RegistryQuery(root, Str(args, "query")),
            "library_read" => LibraryRead(root, Str(args, "entry_id")),
            "pattern_read" => PatternRead(root, Str(args, "pattern_id")),
            "module_read" => ModuleRead(root, Str(args, "module_id")),
            "pipeline_read" => PipelineRead(root, Str(args, "pipeline")),
            "library_search" => LibrarySearch(root, Str(args, "query")),
            "knowledge_order" => KnowledgeOrder(root, Str(args, "clearance")),
            "asset_get" => AssetGet(root, Str(args, "key"), Str(args, "package")),
            _ => null,
        };

        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["content"] = new List<object?>
            {
                new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["type"] = "text",
                    ["text"] = PythonJson.Indented(payload),
                },
            },
        };
    }

    private static Dictionary<string, object?> VerifyPayload(string root)
    {
        var protocol = Receipts.VerifyProtocolReceipts(root);
        var library = Receipts.VerifyLibraryReceipts(root);
        var chain = Receipts.VerifyTransparencyChain(root);
        var rows = CertificateVerifier.VerifyAll(root);
        var assertions = Assertions.Run(root);
        var decisions = Decisions.Verify(root);
        var cog = Cognition.Run(root);
        var lib = Library.Verify(root);
        var model = Modeling.Run(root);
        var components = new List<object?>
        {
            Component(protocol.Name, protocol.Ok, protocol.Issues, protocol.Detail),
            Component(library.Name, library.Ok, library.Issues, library.Detail),
            Component(chain.Name, chain.Ok, chain.Issues, chain.Detail),
            Component("protocol/combo_certificates.json", rows.All(r => r.Issues.Count == 0),
                rows.Where(r => r.Issues.Count > 0).SelectMany(r => r.Issues).ToList(),
                $"证书 {rows.Count} 条 · 失败 {rows.Count(r => r.Issues.Count > 0)}"),
            Component("protocol/assertions.json", assertions.Issues.Count == 0, assertions.Issues,
                $"断言 {assertions.Results.Count} 条 · 问题 {assertions.Issues.Count}"),
            Component("decisions/ADR-*.md", decisions.Issues.Count + decisions.Projection.Count == 0,
                decisions.Issues.Concat(decisions.Projection).ToList(),
                $"ADR {decisions.Stats["decisions"]} 条"),
            Component("library/NF-*.md", lib.Issues.Count + lib.Projection.Count == 0,
                lib.Issues.Concat(lib.Projection).ToList(), $"条目 {lib.Stats["entries"]}"),
            Component("model", model.Issues.Count == 0, model.Issues, $"问题 {model.Issues.Count}"),
        };
        var ok = components.Cast<Dictionary<string, object?>>().All(c => c["ok"] is true)
                 && cog.Issues.Count == 0;
        if (cog.Issues.Count > 0) components.Add(Component("cognition", false, cog.Issues, $"问题 {cog.Issues.Count}"));
        return new Dictionary<string, object?>(StringComparer.Ordinal) { ["ok"] = ok, ["components"] = components };
    }

    private static object? Component(string name, bool ok, IEnumerable<string> issues, string detail)
        => new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["name"] = name, ["ok"] = ok, ["issues"] = issues.Cast<object?>().ToList(), ["detail"] = detail,
        };

    private static Dictionary<string, object?> ReceiptsPayload(string root, string scope)
    {
        var result = scope == "library" ? Receipts.VerifyLibraryReceipts(root) : Receipts.VerifyProtocolReceipts(root);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["stats"] = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["entries"] = result.Count, ["root"] = result.Root,
            },
        };
    }

    private static Dictionary<string, object?> AssertionsPayload(string root)
    {
        var result = Assertions.Run(root);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(), ["results"] = result.Results,
        };
    }

    private static Dictionary<string, object?> DecisionsPayload(string root)
    {
        var result = Decisions.Verify(root);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["projection"] = result.Projection.Cast<object?>().ToList(),
            ["stats"] = result.Stats,
            ["warns"] = result.Warns.Cast<object?>().ToList(),
        };
    }

    private static Dictionary<string, object?> CognitionPayload(string root)
    {
        var result = Cognition.Run(root);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["stats"] = result.Stats,
            ["warns"] = result.Warns.Cast<object?>().ToList(),
        };
    }

    private static Dictionary<string, object?> LibraryPayload(string root)
    {
        var result = Library.Verify(root);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["projection"] = result.Projection.Cast<object?>().ToList(),
            ["stats"] = result.Stats,
            ["warns"] = result.Warns.Cast<object?>().ToList(),
        };
    }

    private static Dictionary<string, object?> ModelPayload(string root, string part)
    {
        var result = Modeling.Run(root, part);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["stats"] = result.Stats,
            ["warns"] = result.Warns.Cast<object?>().ToList(),
        };
    }

    private static Dictionary<string, object?> SigPayload(string root, bool verify)
    {
        if (!verify) return new Dictionary<string, object?>(StringComparer.Ordinal) { ["records"] = KnowledgeSig.Scan(root).Records };
        var (issues, stats) = KnowledgeSig.VerifyReproducible(root);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = issues.Cast<object?>().ToList(), ["stats"] = stats,
        };
    }

    /// <summary>等价 Python <c>library._tokens</c>：英文词 + 数字 + 中文整段与 2-gram。</summary>
    private static List<string> Tokens(string text)
    {
        var lowered = text.ToLowerInvariant();
        var tokens = System.Text.RegularExpressions.Regex.Matches(lowered, "[a-z0-9_]+")
            .Select(m => m.Value).ToList();
        foreach (System.Text.RegularExpressions.Match han in
                 System.Text.RegularExpressions.Regex.Matches(lowered, "[\u4e00-\u9fa5]+"))
        {
            var run = han.Value;
            tokens.Add(run);
            if (run.Length > 2)
            {
                for (var i = 0; i + 2 <= run.Length; i++) tokens.Add(run.Substring(i, 2));
            }
        }
        return tokens;
    }

    /// <summary>等价 Python <c>library.search</c>（倒排权重 + 裸子串兜底 + (-score, id) 排序）。</summary>
    private static List<Dictionary<string, object?>> LibrarySearchIndex(string root, string query, int limit = 10)
    {
        var entries = Library.Entries(root);
        var index = new Dictionary<string, Dictionary<string, int>>(StringComparer.Ordinal);
        foreach (var entry in entries)
        {
            var (text, _) = ReadRepoText(root, entry.Path);
            var body = System.Text.RegularExpressions.Regex.Replace(text, "(?m)^#{1,6}\\s*", "");
            if (body.Length > 8000) body = body[..8000];
            var fields = new (string Text, int Weight)[]
            {
                (DictStr(entry.Fm, "title"), 6),
                (DictStr(entry.Fm, "description"), 4),
                (string.Join(" ", DictList(entry.Fm, "tags")), 3),
                (string.Join(" ", DictList(entry.Fm, "sources")), 2),
                (entry.Id, 5),
                (body, 1),
            };
            foreach (var (fieldText, weight) in fields)
            {
                foreach (var token in Tokens(fieldText).Distinct(StringComparer.Ordinal))
                {
                    if (!index.TryGetValue(token, out var byId)) index[token] = byId = new Dictionary<string, int>(StringComparer.Ordinal);
                    byId[entry.Id] = (byId.TryGetValue(entry.Id, out var w) ? w : 0) + weight;
                }
            }
        }

        var scores = new Dictionary<string, int>(StringComparer.Ordinal);
        var queryLow = query.Trim().ToLowerInvariant();
        foreach (var token in Tokens(query).Distinct(StringComparer.Ordinal))
        {
            if (!index.TryGetValue(token, out var byId)) continue;
            foreach (var (id, weight) in byId) scores[id] = (scores.TryGetValue(id, out var s) ? s : 0) + weight;
        }
        foreach (var entry in entries)
        {
            var (text, _) = ReadRepoText(root, entry.Path);
            if (queryLow.Length > 0 && text.ToLowerInvariant().Contains(queryLow, StringComparison.Ordinal))
                scores[entry.Id] = (scores.TryGetValue(entry.Id, out var s) ? s : 0) + 2;
        }

        var output = new List<Dictionary<string, object?>>();
        foreach (var (id, score) in scores.OrderBy(kv => -kv.Value).ThenBy(kv => kv.Key, StringComparer.Ordinal))
        {
            var entry = entries.First(e => e.Id == id);
            output.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = id,
                ["score"] = score,
                ["title"] = DictStr(entry.Fm, "title") is { Length: > 0 } t ? t : id,
                ["type"] = DictStr(entry.Fm, "type"),
                ["status"] = DictStr(entry.Fm, "status") is { Length: > 0 } st ? st : "active",
                ["path"] = entry.Path,
                ["description"] = DictStr(entry.Fm, "description"),
            });
            if (output.Count >= limit) break;
        }
        return output;
    }

    private static List<object?> LibrarySearch(string root, string query)
    {
        var q = query.Trim();
        var hits = new List<object?>();
        foreach (var hit in LibrarySearchIndex(root, q))
        {
            hits.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["kind"] = "library", ["id"] = hit["id"], ["path"] = hit["path"],
                ["title"] = hit["title"], ["score"] = hit["score"], ["status"] = hit["status"],
                ["type"] = hit["type"], ["uri"] = "nf://repo/library/" + hit["id"],
            });
        }
        foreach (var file in Directory.Exists(root)
                     ? Directory.GetFiles(root, "*.md").Select(Path.GetFileName).Select(x => x!).OrderBy(x => x, StringComparer.Ordinal)
                     : Enumerable.Empty<string>())
        {
            var include = file.StartsWith("0", StringComparison.Ordinal) ||
                          file.StartsWith("4", StringComparison.Ordinal) ||
                          (file.Length >= 2 && char.IsAsciiDigit(file[0]) && char.IsAsciiDigit(file[1]));
            if (!include) continue;
            var (text, _) = ReadRepoText(root, file);
            var title = MdTitle(text);
            if (file.Contains(q, StringComparison.Ordinal) || title.Contains(q, StringComparison.Ordinal))
                hits.Add(new Dictionary<string, object?>(StringComparer.Ordinal) { ["kind"] = "doc", ["path"] = file, ["title"] = title });
        }
        foreach (var pattern in new[] { "docs/*.md", "community/*/README.md" })
        {
            foreach (var file in Assertions.Glob(root, pattern))
            {
                var rel = Path.GetRelativePath(root, file).Replace('\\', '/');
                var (text, _) = ReadRepoText(root, rel);
                var title = MdTitle(text);
                if (Path.GetFileName(rel).Contains(q, StringComparison.Ordinal) || title.Contains(q, StringComparison.Ordinal))
                    hits.Add(new Dictionary<string, object?>(StringComparer.Ordinal) { ["kind"] = "doc", ["path"] = rel, ["title"] = title });
            }
        }
        return hits.Take(10).ToList();
    }

    private static Dictionary<string, object?> KnowledgeOrder(string root, string clearance)
    {
        using var decl = JsonIo.ReadFile(Path.Combine(root, "protocol/knowledge_sources.json"));
        var order = decl.RootElement.TryGetProperty("query_order", out var qo) && qo.ValueKind == JsonValueKind.Array
            ? qo.EnumerateArray().Select(x => x.ValueKind == JsonValueKind.String ? x.GetString()! : x.GetRawText()).ToList()
            : new List<string>();
        var sources = new Dictionary<string, JsonElement>(StringComparer.Ordinal);
        if (decl.RootElement.TryGetProperty("sources", out var sourceArray))
        {
            foreach (var source in sourceArray.EnumerateArray())
            {
                if (source.TryGetProperty("id", out var id) && id.ValueKind == JsonValueKind.String)
                    sources[id.GetString()!] = source;
            }
        }
        var rank = new Dictionary<string, int>(StringComparer.Ordinal) { ["public"] = 0, ["internal"] = 1, ["restricted"] = 2 };
        HashSet<string>? allowed = null;
        if (clearance.Length > 0)
        {
            allowed = new HashSet<string>(StringComparer.Ordinal);
            if (rank.TryGetValue(clearance, out var cap))
            {
                foreach (var (id, source) in sources)
                {
                    var visibility = source.TryGetProperty("visibility", out var v) && v.ValueKind == JsonValueKind.String
                        ? v.GetString()! : "";
                    if (rank.TryGetValue(visibility, out var sourceRank) && sourceRank <= cap) allowed.Add(id);
                }
            }
        }
        var rows = new List<object?>();
        foreach (var id in order)
        {
            if (!sources.TryGetValue(id, out var source)) continue;
            if (allowed is not null && !allowed.Contains(id)) continue;
            var requiresLabel = source.TryGetProperty("requires_source_label", out var r) && r.ValueKind == JsonValueKind.True;
            rows.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = id,
                ["authority"] = source.TryGetProperty("authority", out var a) ? a.ToString() : "",
                ["kind"] = source.TryGetProperty("kind", out var k) ? k.ToString() : "",
                ["locator"] = source.TryGetProperty("locator", out var l) ? l.ToString() : "",
                ["requires_source_label"] = requiresLabel ? "true" : "false",
                ["visibility"] = source.TryGetProperty("visibility", out var vv) ? vv.ToString() : "",
            });
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["clearance"] = clearance.Length > 0 ? clearance : "不裁剪",
            ["contract_first"] = true,
            ["count"] = rows.Count,
            ["query_order"] = rows,
        };
    }

    private static (string Text, int Bytes) AssetText(string root, string rel) => ReadRepoText(root, rel);

    /// <summary>等价 Python <c>_asset_keys_of_file</c>：文件名令牌 ∪ 正文键声明（`KEY` / "KEY": / ## KEY）。</summary>
    private static List<string> AssetKeysOfFile(string file)
    {
        var stem = Path.GetFileNameWithoutExtension(file);
        var keys = new HashSet<string>(StringComparer.Ordinal);
        foreach (System.Text.RegularExpressions.Match m in
                 System.Text.RegularExpressions.Regex.Matches(stem, "[A-Z][A-Z0-9_]*"))
        {
            keys.Add(m.Value);
        }
        var text = new System.Text.UTF8Encoding(false).GetString(File.ReadAllBytes(file));
        var head = text.Length > 6000 ? text[..6000] : text;
        foreach (var pattern in new[] { "`([A-Z][A-Z0-9_]{2,})`", "\"([A-Z][A-Z0-9_]{2,})\"\\s*:", "##\\s*([A-Z][A-Z0-9_]{2,})" })
        {
            foreach (System.Text.RegularExpressions.Match m in System.Text.RegularExpressions.Regex.Matches(head, pattern))
            {
                keys.Add(m.Groups[1].Value);
            }
        }
        return keys.OrderBy(x => x, StringComparer.Ordinal).ToList();
    }

    private static Dictionary<string, object?> AssetGet(string root, string key, string package)
    {
        var req = key.Trim();
        var patterns = package.Length > 0
            ? new[] { $"community/{package}/assets/*.md" }
            : new[] { "community/*/assets/*.md", "05_资产库/用户自定义/*.md" };
        var hits = new List<(string Package, string File)>();
        foreach (var pattern in patterns)
        {
            foreach (var file in Assertions.Glob(root, pattern))
            {
                if (Path.GetFileName(file) == "README.md") continue;
                if (!AssetKeysOfFile(file).Contains(req, StringComparer.Ordinal)) continue;
                var rel = Path.GetRelativePath(root, file).Replace('\\', '/');
                hits.Add((rel.StartsWith("community/", StringComparison.Ordinal) ? rel.Split('/')[1] : "官方", rel));
            }
        }
        if (hits.Count == 0)
            throw new ArgumentException($"资产键未找到：{key}（asset ls / 包 assets/README.md 可枚举）（修复指引：用包内资产键表登记的键名重试）");
        var matches = new List<object?>();
        foreach (var (pkg, rel) in hits)
        {
            var (text, bytes) = AssetText(root, rel);
            matches.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["package"] = pkg, ["file"] = rel, ["bytes"] = bytes, ["text"] = text,
            });
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["found"] = true, ["key"] = req, ["matches"] = matches,
        };
    }

    private static List<string> DictList(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is List<string> list ? list : new List<string>();

    /// <summary>等价 Python <c>Path.read_text(encoding="utf-8")</c>：UTF-8 解码 + 通用换行归一；返回文本与归一后的字节数。</summary>
    private static (string Text, int Bytes) ReadRepoText(string root, string rel)
    {
        var raw = new System.Text.UTF8Encoding(false).GetString(
            File.ReadAllBytes(Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar))));
        var text = KnowledgeSig.Norm(raw);
        return (text, System.Text.Encoding.UTF8.GetByteCount(text));
    }

    private static Dictionary<string, object?> LibraryRead(string root, string entryId)
    {
        var want = entryId.Trim();
        foreach (var entry in Library.Entries(root))
        {
            if (!string.Equals(entry.Id, want, StringComparison.OrdinalIgnoreCase)) continue;
            var (text, bytes) = ReadRepoText(root, entry.Path);
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["found"] = true, ["id"] = entry.Id, ["path"] = entry.Path,
                ["status"] = DictStr(entry.Fm, "status") is { Length: > 0 } s ? s : "active",
                ["frontmatter"] = entry.Fm, ["bytes"] = bytes, ["text"] = text,
            };
        }
        throw new ArgumentException($"馆藏条目未找到：{entryId}（library_search 可枚举；编号大小写不敏感）（修复指引：用 nf library ls 列全量编号）");
    }

    /// <summary>实践包门禁的机读面（与 CLI <c>patterns verify --json</c> 同源，只扫一遍）。</summary>
    private static Dictionary<string, object?> PatternsPayload(string root)
    {
        var (issues, warns, stats) = Patterns.Scan(root);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = issues.Cast<object?>().ToList(),
            ["warns"] = warns.Cast<object?>().ToList(),
            ["projection"] = Patterns.CheckProjection(root).Cast<object?>().ToList(),
            ["stats"] = stats,
        };
    }

    /// <summary>
    /// MCP 面按**仓库相对路径**收参（与其它工具一致，如 <c>protocol/RECEIPTS.json</c>）；绝对路径原样使用。
    /// 注意：CLI 的 <c>st-validate</c> 与 Python 同口径按进程 CWD 解析——两者刻意不同，
    /// 因为 MCP 消费方（外部 agent）的世界观是"这一个仓库"。
    /// </summary>
    private static string ResolvePath(string root, string rel)
        => string.IsNullOrEmpty(rel) || Path.IsPathRooted(rel)
            ? rel
            : Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));

    /// <summary>自述数字实算的机读面（与 CLI <c>stats --json</c> 同源；只实算一遍）。</summary>
    private static Dictionary<string, object?> RepoStatsPayload(string root)
    {
        var (issues, stats) = RepoStats.Check(root);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = issues.Cast<object?>().ToList(),
            ["stats"] = stats,
        };
    }

    /// <summary>
    /// 互操作导出面的机读面：<c>check=true</c> → 门禁；给了 <c>kind</c> → 该形状派生文档；
    /// 都不给 → 12 形状清单（与 CLI <c>interop --list</c> 同源）。
    /// </summary>
    private static object? InteropPayload(string root, JsonElement args)
    {
        if (Bool(args, "check"))
        {
            var (issues, stats) = Interop.Verify(root);
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["issues"] = issues.Cast<object?>().ToList(),
                ["stats"] = stats,
            };
        }
        var kind = Str(args, "kind");
        if (kind.Length > 0)
        {
            if (!Interop.Kinds.Any(k => k.Id == kind))
            {
                throw new ArgumentException(
                    $"interop 未知形状：{kind}（可选：{string.Join(" / ", Interop.Kinds.Select(k => k.Id))}）");
            }
            return Interop.Document(kind, root);
        }
        return Interop.Kinds.Select(k => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = k.Id,
            ["label"] = k.Label,
        }).ToList();
    }

    private static Dictionary<string, object?> PatternRead(string root, string patternId)
    {
        var want = patternId.Trim();
        foreach (var file in Assertions.Glob(root, "patterns/*/PATTERN.md"))
        {
            if (Path.GetFileName(Path.GetDirectoryName(file)!) != want) continue;
            var rel = Path.GetRelativePath(root, file).Replace('\\', '/');
            var (text, bytes) = ReadRepoText(root, rel);
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["found"] = true, ["id"] = want, ["path"] = rel, ["bytes"] = bytes, ["text"] = text,
            };
        }
        throw new ArgumentException($"pattern 未找到：{patternId}（修复指引：patterns/ 下按目录名取，如 fail-closed-verification）");
    }

    private sealed record ModuleIndexRow(string? McId, string? TitleId, string Rel, bool HasContract);

    private static List<ModuleIndexRow> ModuleIndex(string root)
    {
        var docs = new List<string>();
        var core = Path.Combine(root, "04_模块库");
        if (Directory.Exists(core))
        {
            docs.AddRange(Directory.GetFiles(core, "*.md", SearchOption.AllDirectories));
        }
        var community = Path.Combine(root, "community");
        if (Directory.Exists(community))
        {
            foreach (var package in Directory.GetDirectories(community).OrderBy(d => Path.GetFileName(d), StringComparer.Ordinal))
            {
                var modules = Path.Combine(package, "modules");
                if (!Directory.Exists(modules)) continue;
                docs.AddRange(Directory.GetFiles(modules, "*.md").OrderBy(f => Path.GetFileName(f), StringComparer.Ordinal));
            }
        }
        var rows = new List<ModuleIndexRow>();
        foreach (var doc in docs.OrderBy(d => Path.GetRelativePath(root, d).Replace('\\', '/'), StringComparer.Ordinal))
        {
            var rel = Path.GetRelativePath(root, doc).Replace('\\', '/');
            var text = new System.Text.UTF8Encoding(false).GetString(File.ReadAllBytes(doc));
            var body = MiniYaml.ExtractFence(text, "machine_contract");
            string? mcId = null;
            if (body is not null)
            {
                var parsed = MiniYaml.Parse(body);
                if (parsed.TryGetValue("machine_contract", out var mc) && mc is Dictionary<string, object?> map &&
                    map.TryGetValue("id", out var id) && id is string idText && idText.Length > 0)
                {
                    mcId = idText;
                }
            }
            var titleMatch = System.Text.RegularExpressions.Regex.Match(text, @"#\s*模块\s+([^\s·]+)");
            rows.Add(new ModuleIndexRow(mcId, titleMatch.Success ? titleMatch.Groups[1].Value.Trim() : null, rel, mcId is not null));
        }
        return rows;
    }

    private static Dictionary<string, object?> ModuleRead(string root, string moduleId)
    {
        var req = moduleId.Trim();
        var exact = new List<ModuleIndexRow>();
        var suffix = new List<ModuleIndexRow>();
        foreach (var row in ModuleIndex(root))
        {
            var ids = new[] { row.McId, row.TitleId }.Where(x => !string.IsNullOrEmpty(x)).Select(x => x!).ToList();
            if (ids.Contains(req, StringComparer.Ordinal)) exact.Add(row);
            else if (req.All(char.IsAsciiDigit) && ids.Any(x => x.Split(':')[^1] == req)) suffix.Add(row);
        }
        ModuleIndexRow hit;
        if (exact.Count > 0) hit = exact[0];
        else if (suffix.Count == 1) hit = suffix[0];
        else if (suffix.Count > 1)
            throw new ArgumentException("module_id 存在多个同号限定（如 通用:M10 / 生存:M10）——请用限定 id（修复指引：先 registry_query 查全限定 id 再重试）");
        else
            throw new ArgumentException($"模块未找到：{moduleId}（module ls / registry_query 可枚举）（修复指引：用仓库内真实模块 id，如 M90、M40 或 通用:M10）");

        var (text, bytes) = ReadRepoText(root, hit.Rel);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["found"] = true,
            ["id"] = hit.McId ?? hit.TitleId ?? req,
            ["path"] = hit.Rel,
            ["has_machine_contract"] = hit.HasContract,
            ["bytes"] = bytes,
            ["text"] = text,
        };
    }

    private static Dictionary<string, object?> PipelineRead(string root, string pipeline)
    {
        var req = pipeline.Trim();
        var candidate = Path.Combine(root, req.Replace('/', Path.DirectorySeparatorChar));
        if (req.EndsWith(".md", StringComparison.Ordinal) && File.Exists(candidate))
        {
            var allowed = req.StartsWith("03_管线库/", StringComparison.Ordinal) ||
                          req.Contains("/pipelines/", StringComparison.Ordinal);
            if (!allowed)
                throw new ArgumentException("管线路径越界：只读 03_管线库 与 community/*/pipelines（修复指引：路径须指向仓库内管线件，如 03_管线库/P90….md）");
            var (text, bytes) = ReadRepoText(root, req);
            return new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["found"] = true, ["path"] = req, ["bytes"] = bytes, ["text"] = text,
            };
        }

        var hits = new List<string>();
        foreach (var pattern in new[] { "03_管线库/*.md", "community/*/pipelines/*.md" })
        {
            foreach (var file in Assertions.Glob(root, pattern))
            {
                if (Path.GetFileName(file).Split('_')[0] == req) hits.Add(file);
            }
        }
        if (hits.Count == 0)
            throw new ArgumentException($"管线未找到：{pipeline}（pipeline_ls 可枚举）（修复指引：用 Pxx 编号或仓库内相对路径）");
        var rel = Path.GetRelativePath(root, hits[0]).Replace('\\', '/');
        var (hitText, hitBytes) = ReadRepoText(root, rel);
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["found"] = true, ["path"] = rel, ["bytes"] = hitBytes, ["text"] = hitText,
        };
    }

    /// <summary>等价 Python <c>_md_title</c>：首个以 # 开头的行 → <c>lstrip("# ").strip()</c>。</summary>
    private static string MdTitle(string text)
    {
        foreach (var line in KnowledgeSig.SplitLines(text))
        {
            if (line.StartsWith("#", StringComparison.Ordinal)) return line.TrimStart('#', ' ').Trim();
        }
        return "";
    }

    private static List<object?> PipelineList(string root, string query)
    {
        var output = new List<object?>();
        foreach (var pattern in new[] { "03_管线库/*.md", "community/*/pipelines/*.md" })
        {
            foreach (var file in Assertions.Glob(root, pattern))
            {
                var text = new System.Text.UTF8Encoding(false).GetString(File.ReadAllBytes(file));
                var title = MdTitle(text);
                var rel = Path.GetRelativePath(root, file).Replace('\\', '/');
                if (query.Length > 0 && !rel.Contains(query, StringComparison.Ordinal) &&
                    !title.Contains(query, StringComparison.Ordinal)) continue;
                output.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["path"] = rel, ["title"] = title,
                });
            }
        }
        return output;
    }

    private static List<object?> SpecList(string root)
    {
        using var registry = JsonIo.ReadFile(Path.Combine(root, "desktop/src/core/registry.json"));
        var output = new List<object?>();
        foreach (var protocol in registry.RootElement.GetProperty("protocols").EnumerateArray())
        {
            var moduleIds = protocol.TryGetProperty("module_ids", out var ids) && ids.ValueKind == JsonValueKind.Array
                ? ids.GetArrayLength()
                : 0;
            output.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = Str(protocol, "id"),
                ["version"] = Str(protocol, "version"),
                ["modules"] = moduleIds,
                ["categories"] = StringList(protocol, "categories").Cast<object?>().ToList(),
            });
        }
        return output;
    }

    private static Dictionary<string, object?> RegistryQuery(string root, string query)
    {
        using var registry = JsonIo.ReadFile(Path.Combine(root, "desktop/src/core/registry.json"));
        var q = query.Trim();
        var modules = new List<object?>();
        foreach (var module in registry.RootElement.GetProperty("modules").EnumerateArray())
        {
            var id = module.TryGetProperty("id", out var idElement) ? idElement.ToString() : "";
            var name = module.TryGetProperty("name", out var nameElement) ? nameElement.ToString() : "";
            if (!id.Contains(q, StringComparison.Ordinal) && !name.Contains(q, StringComparison.Ordinal)) continue;
            modules.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = module.TryGetProperty("id", out var mi) && mi.ValueKind == JsonValueKind.String ? mi.GetString() : null,
                ["name"] = module.TryGetProperty("name", out var mn) && mn.ValueKind == JsonValueKind.String ? mn.GetString() : null,
            });
        }
        var protocols = new List<object?>();
        foreach (var protocol in registry.RootElement.GetProperty("protocols").EnumerateArray())
        {
            var id = protocol.TryGetProperty("id", out var pid) ? pid.ToString() : "";
            var name = protocol.TryGetProperty("name", out var pname) ? pname.ToString() : "";
            if (!id.Contains(q, StringComparison.Ordinal) && !name.Contains(q, StringComparison.Ordinal)) continue;
            protocols.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = protocol.TryGetProperty("id", out var x) && x.ValueKind == JsonValueKind.String ? x.GetString() : null,
                ["version"] = protocol.TryGetProperty("version", out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null,
                ["modules"] = protocol.TryGetProperty("module_ids", out var mids) && mids.ValueKind == JsonValueKind.Array
                    ? mids.GetArrayLength() : 0,
            });
        }
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["modules"] = modules, ["protocols"] = protocols,
        };
    }

    private static Dictionary<string, object?> Capabilities()
        => new(StringComparer.Ordinal) { ["resources"] = new Dictionary<string, object?>(), ["tools"] = new Dictionary<string, object?>(), ["prompts"] = new Dictionary<string, object?>() };

    private static Dictionary<string, object?> Cacheable(Dictionary<string, object?> payload, long ttlMs = 3600000, string cacheScope = "public")
    {
        var output = new Dictionary<string, object?>(StringComparer.Ordinal) { ["resultType"] = "complete" };
        foreach (var kv in payload) output[kv.Key] = kv.Value;
        if (!output.ContainsKey("ttlMs")) output["ttlMs"] = ttlMs;
        if (!output.ContainsKey("cacheScope")) output["cacheScope"] = cacheScope;
        return output;
    }

    private static bool IsValidId(JsonElement id) => id.ValueKind switch
    {
        JsonValueKind.Null or JsonValueKind.String or JsonValueKind.Number => true,
        _ => false,
    };

    private static object? ToNode(JsonElement element) => element.ValueKind switch
    {
        JsonValueKind.String => element.GetString(),
        // 同 PythonJson.ToGraph：三元会把 long/double 统一成 double，整数会被静默转成 1.0
        JsonValueKind.Number => element.TryGetInt64(out var l) ? (object)l : element.GetDouble(),
        JsonValueKind.Null => null,
        _ => null,
    };

    private static Dictionary<string, object?> Err(string root, int code, string message, JsonElement? id, Dictionary<string, object?>? data)
    {
        var error = new Dictionary<string, object?>(StringComparer.Ordinal) { ["code"] = code, ["message"] = message };
        if (data is not null) error["data"] = data;
        return new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["jsonrpc"] = JsonRpcVersion,
            ["id"] = id is null ? null : ToNode(id.Value),
            ["error"] = error,
        };
    }

    private static Dictionary<string, object?> ErrorAt(int code, string message, JsonElement id)
        => new(StringComparer.Ordinal)
        {
            ["jsonrpc"] = JsonRpcVersion,
            ["id"] = ToNode(id),
            ["error"] = new Dictionary<string, object?>(StringComparer.Ordinal) { ["code"] = code, ["message"] = message },
        };

    private static string Str(JsonElement element, string name)
        => element.ValueKind == JsonValueKind.Object && element.TryGetProperty(name, out var v) &&
           v.ValueKind == JsonValueKind.String ? v.GetString()! : "";

    private static string DictStr(Dictionary<string, object?> map, string key)
        => map.TryGetValue(key, out var value) && value is string text ? text : "";

    private static bool Bool(JsonElement element, string name)
        => element.ValueKind == JsonValueKind.Object && element.TryGetProperty(name, out var v) &&
           v.ValueKind == JsonValueKind.True;

    private static List<string> StringList(JsonElement element, string name)
    {
        if (element.ValueKind != JsonValueKind.Object || !element.TryGetProperty(name, out var v) ||
            v.ValueKind != JsonValueKind.Array) return new List<string>();
        return v.EnumerateArray().Where(x => x.ValueKind == JsonValueKind.String)
            .Select(x => x.GetString()!).ToList();
    }

    /// <summary>stdio 会话：逐行读 JSON-RPC、逐行写响应；stdout 只写 MCP 消息。</summary>
    public static int ServeStdio(string root, TextReader input, TextWriter output)
    {
        string? line;
        while ((line = input.ReadLine()) is not null)
        {
            if (line.Trim().Length == 0) continue;
            JsonDocument doc;
            try
            {
                doc = JsonIo.Parse(line);
            }
            catch (JsonException)
            {
                // 文案与 core/mcp_runtime.py 同字：就是 "Parse error"（不带运行时细节）
                output.WriteLine(EncodeMessage(Err(root, ParseError, "Parse error", null, null)));
                output.Flush();
                continue;
            }
            Dictionary<string, object?>? response;
            using (doc)
            {
                // JSON-RPC 2.0 §5：**错误响应必须回带请求 id**（除解析错误外）。
                // 此前这里固定传 null，导致调用方按 id 匹配时"看不到"这次失败——
                // 单条消息不杀循环是对的，但"静默丢响应"不是。
                var idElement = (JsonElement?)null;
                if (doc.RootElement.ValueKind == JsonValueKind.Object
                    && doc.RootElement.TryGetProperty("id", out var rawId)
                    && rawId.ValueKind is JsonValueKind.String or JsonValueKind.Number or JsonValueKind.Null)
                {
                    idElement = rawId;
                }
                try
                {
                    response = Handle(root, doc.RootElement);
                }
                catch (Exception exc)
                {
                    // 防御：**单条消息异常不许杀循环**（同 core/mcp_runtime.py 的 INTERNAL_ERROR 分支）
                    response = Err(root, InternalError, "Internal error: " + exc.Message, idElement, null);
                }
            }
            if (response is null) continue;
            output.WriteLine(EncodeMessage(response));
            output.Flush();
        }
        return 0;
    }
}
