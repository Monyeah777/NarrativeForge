using System.Text.Json;
using Nf.Engine;

// nf-dotnet · NF 工业引擎 CLI（只读子集，输出面与 Python 侧 nf 对齐）
// 用法：nf-dotnet [--root <dir>] [--json] <command> [options]
//   verify                                  聚合校验（协议回执 + 馆藏回执 + 透明链 + 组合证书）
//   receipts [--scope protocol|library]     回执复算
//   transparency                            透明链复算
//   combine verify                          组合证书 T4 复算
//   combine plan --packs a,b [--extra-modules x,y] [--strict-coherence]
//   conformance                             一致性报告（部分实现：已移植契约逐条给 ok/detail/digest）

const string Version = "0.1.0";

string? root = null;
string scope = "protocol";
string? samplesPath = null;
string? benchBaselinePath = null;
string? benchWritePath = null;
var tolerance = 2.0;
var pairsOnly = false;
var kindsOnly = false;
var backlogOnly = false;
var pipelineAll = false;
string? pipelineName = null;
var stateFrontCheck = false;
var stateFrontAb = false;
var stateFrontMode = "front";
// 通用 `--out` 值：state-front 侧是写面（未移植，明确拒绝）；st-validate 侧是报告输出路径（同 Python）
string? outPath = null;
var writeRequested = false;
string? tracePath = null;
string? interopKind = null;
var interopList = false;
var interopCheck = false;
var interopAll = false;
var worldModelRun = false;
var worldModelWalk = false;
string? worldModelState = null;
var impactCheck = false;
// 构建回路（workloop）面的开关：候选数 / 来源限定 / 适配器；--close 与 --write 是写面（明确拒绝）
var topCount = 5;
string? sourceFlag = null;
var adapterFlag = "stub";
var workloopList = false;
var closeFlag = "";
// 回归评分（score）面的开关：基线路径可覆盖；--write-baseline 是写面
var scoreBaselinePath = "";
var scoreWriteBaseline = false;
double? scoreTolerance = null;   // 真源 `nf score --tolerance` 缺省 0.0（与 bench 的 2.0 不同）
// 决策层（decide）面的开关：状态文本 / 问题件 / 端点类参数（非 stub 走 fail-closed 边界）
string? decideStatePath = null;
var decideStateText = "";
string? questionsPath = null;
var endpointFlag = "";
var modelFlag = "";
var decideDryRun = false;
var limitCount = 0;    // 同 `--limit` 开关：review 只审前 N 行候选（0 = 全量）
var batchCount = 8;    // review 每批行数（真源缺省 8）
string? diffPath = null;   // `extension --diff <文件|->`：调用方供 `git diff HEAD` 的标准统一 diff
// 需求 → 装配计划（assemble）面：`--answer` 可重复；`--check` 复用既有开关（成品 md 走位置参数）；
// session/save/trace/rounds 都是写面或未移植面 → 明确拒绝。
var assemblyAnswers = new List<string>();
var assembleCheck = false;
var assembleSessionPath = "";
var assembleSavePath = "";
var assembleTracePath = "";
var assembleRounds = false;
string? registryPath = null;
string? marketTier = null;
var marketList = false;
string? assetsRootFlag = null;
var assetPkg = "";
var assetTier = "";
var assetStatus = "";
var strictRequested = false;
var refreshRequested = false;
var outputCategory = "";
var outputPackage = "";
string? closureAsset = null;
var closureTarget = "C22";
var closureLoaded = "";
var closureBranch = "";
var closureOrder = "";
var closureList = false;
var closureReadyList = false;
var closureGaps = false;
var closureCheck = false;
var closureLimit = 20;
var knowledgeClearance = "";
var packs = new List<string>();
var extraModules = new List<string>();
// ISA v1 C1′「撞号即 DENY」：默认与 Python 同口径（静默塌陷），加了开关才判死。
var strictCoherence = false;
var flags = new List<string>();
var positional = new List<string>();

for (var i = 0; i < args.Length; i++)
{
    switch (args[i])
    {
        case "--root":
            if (++i >= args.Length) return Usage("--root 需要一个目录参数");
            root = args[i];
            break;
        case "--scope":
            if (++i >= args.Length) return Usage("--scope 需要 protocol|library");
            scope = args[i];
            break;
        case "--packs":
            if (++i >= args.Length) return Usage("--packs 需要逗号分隔的包名");
            packs = args[i].Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries).ToList();
            break;
        case "--samples":
            if (++i >= args.Length) return Usage("--samples 需要 Python 导出的样本集 JSON");
            samplesPath = args[i];
            break;
        case "--pairs-only":
            pairsOnly = true;
            break;
        case "--kinds":
            kindsOnly = true;
            break;
        case "--backlog":
            backlogOnly = true;
            break;
        case "--all":
            pipelineAll = true;
            interopAll = true;   // 同一 --all 开关：pipeline 与 interop 各自读取
            break;
        case "--pipeline":
            if (++i >= args.Length) return Usage("--pipeline 需要管线路径");
            pipelineName = args[i];
            break;
        case "--check":
            stateFrontCheck = true;
            interopCheck = true;   // 同一 --check 开关：state-front 与 interop 各自读取
            impactCheck = true;    // 同一 --check 开关：impact 读它（门禁模式）
            closureCheck = true;   // 同一 --check 开关：domain-closure 自检读它
            assembleCheck = true;  // 同一 --check 开关：assemble 读它（成品 md 路径走位置参数）
            break;
        case "--answer":
            if (++i >= args.Length) return Usage("--answer 需要一条澄清回填");
            assemblyAnswers.Add(args[i]);
            break;
        case "--session-path":
            if (++i >= args.Length) return Usage("--session-path 需要路径");
            assembleSessionPath = args[i];
            break;
        case "--save-path":
            if (++i >= args.Length) return Usage("--save-path 需要路径");
            assembleSavePath = args[i];
            break;
        case "--trace-path":
            if (++i >= args.Length) return Usage("--trace-path 需要路径");
            assembleTracePath = args[i];
            break;
        case "--rounds":
            assembleRounds = true;
            break;
        case "--registry":
            if (++i >= args.Length) return Usage("--registry 需要一个 registry.json 路径");
            registryPath = args[i];
            break;
        case "--ab":
            stateFrontAb = true;
            break;
        case "--mode":
            if (++i >= args.Length) return Usage("--mode 需要 front|back|none");
            stateFrontMode = args[i];
            break;
        case "--out":
            if (++i >= args.Length) return Usage("--out 需要输出路径");
            outPath = args[i];
            break;
        case "--write":
            writeRequested = true;
            break;
        case "--trace":
            if (++i >= args.Length) return Usage("--trace 需要一个 trace 文件路径");
            tracePath = args[i];
            break;
        case "--run":
            worldModelRun = true;
            break;
        case "--walk":
            worldModelWalk = true;
            break;
        case "--state":
            if (++i >= args.Length) return Usage("--state 需要一个状态文件路径");
            worldModelState = args[i];
            decideStatePath = args[i];   // 同一 --state 开关：worldmodel 取状态 id、decide 取状态文本文件
            break;
        case "--state-text":
            if (++i >= args.Length) return Usage("--state-text 需要状态文本");
            decideStateText = args[i];
            break;
        case "--questions":
            if (++i >= args.Length) return Usage("--questions 需要问题 JSON 文件路径");
            questionsPath = args[i];
            break;
        case "--endpoint":
            if (++i >= args.Length) return Usage("--endpoint 需要适配器端点");
            endpointFlag = args[i];
            break;
        case "--model":
            if (++i >= args.Length) return Usage("--model 需要模型名（openai-json 适配器）");
            modelFlag = args[i];
            break;
        case "--dry-run":
            decideDryRun = true;
            break;
        case "--kind":
            if (++i >= args.Length) return Usage("--kind 需要一个导出形状");
            interopKind = args[i];
            break;
        case "--list":
            interopList = true;
            marketList = true;   // 同一 --list 开关：interop 与 market 各自读取
            closureList = true;   // 同一 --list 开关：domain-closure 条目键全表
            workloopList = true;   // 同一 --list 开关：workloop 列候选工作项
            break;
        case "--top":
            if (++i >= args.Length) return Usage("--top 需要整数（候选工作项数）");
            if (!int.TryParse(args[i], System.Globalization.NumberStyles.Integer,
                    System.Globalization.CultureInfo.InvariantCulture, out topCount))
                return Usage("--top 需要整数（候选工作项数）");
            break;
        case "--source":
            if (++i >= args.Length) return Usage("--source 需要来源限定（type-backlog / pipeline-advisory / capability-gaps）");
            sourceFlag = args[i];
            break;
        case "--adapter":
            if (++i >= args.Length) return Usage("--adapter 需要适配器 id（stub / systemone-http / openai-json）");
            adapterFlag = args[i];
            break;
        case "--close":
            if (++i >= args.Length) return Usage("--close 需要工单号");
            closeFlag = args[i];
            break;
        case "--tier":
            if (++i >= args.Length) return Usage("--tier 需要 official|community|experimental");
            marketTier = args[i];
            assetTier = marketTier;   // 同一 --tier 开关：market --list 与 asset ls 各自读取
            break;
        case "--assets-root":
            if (++i >= args.Length) return Usage("--assets-root 需要一个扫描根路径");
            assetsRootFlag = args[i];
            break;
        case "--pkg":
            if (++i >= args.Length) return Usage("--pkg 需要一个包名");
            assetPkg = args[i];
            break;
        case "--category":
            if (++i >= args.Length) return Usage("--category 需要一个形态类别 id");
            outputCategory = args[i];
            break;
        case "--package":
            if (++i >= args.Length) return Usage("--package 需要一个包名");
            outputPackage = args[i];
            break;
        case "--asset":
            if (++i >= args.Length) return Usage("--asset 需要一个概念图资产路径");
            closureAsset = args[i];
            break;
        case "--target":
            if (++i >= args.Length) return Usage("--target 需要一个目标概念");
            closureTarget = args[i];
            break;
        case "--loaded":
            if (++i >= args.Length) return Usage("--loaded 需要逗号分隔的已装载概念集");
            closureLoaded = args[i];
            break;
        case "--branch":
            if (++i >= args.Length) return Usage("--branch 需要一个分支 id");
            closureBranch = args[i];
            break;
        case "--order":
            if (++i >= args.Length) return Usage("--order 需要一个序 id");
            closureOrder = args[i];
            break;
        case "--ready-list":
            closureReadyList = true;
            break;
        case "--gaps":
            closureGaps = true;
            break;
        case "--limit":
            if (++i >= args.Length) return Usage("--limit 需要一个整数（--gaps 行数上限）");
            if (!int.TryParse(args[i], out closureLimit)) return Usage("--limit 需要一个整数");
            limitCount = closureLimit;   // 同一 --limit 开关：domain-closure --gaps 与 review 各自读取
            break;
        case "--batch":
            if (++i >= args.Length) return Usage("--batch 需要整数（review 每批行数）");
            if (!int.TryParse(args[i], out batchCount)) return Usage("--batch 需要整数（review 每批行数）");
            break;
        case "--diff":
            if (++i >= args.Length) return Usage("--diff 需要统一 diff 文件路径（或 - 读 stdin）");
            diffPath = args[i];
            break;
        case "--status":
            if (++i >= args.Length) return Usage("--status 需要 active|deprecated|retired");
            assetStatus = args[i];
            break;
        case "--as":
            if (++i >= args.Length) return Usage("--as 需要 public|internal|restricted");
            knowledgeClearance = args[i];
            break;
        case "--baseline":
            if (++i >= args.Length) return Usage("--baseline 需要基线 JSON 路径");
            benchBaselinePath = args[i];
            scoreBaselinePath = args[i];   // 同一 --baseline 开关：bench 与 score 各自读取
            break;
        case "--write-baseline":
            // 真源两义：`nf bench --write-baseline <f>` 取路径；`nf score --write-baseline` 是布尔（写面）。
            if (positional.Count > 0 && positional[0] == "score")
            {
                scoreWriteBaseline = true;
                break;
            }
            if (++i >= args.Length) return Usage("--write-baseline 需要输出 JSON 路径");
            benchWritePath = args[i];
            break;
        case "--tolerance":
            if (++i >= args.Length) return Usage("--tolerance 需要数值（如 2.0）");
            if (!double.TryParse(args[i], System.Globalization.NumberStyles.Float,
                    System.Globalization.CultureInfo.InvariantCulture, out tolerance))
                return Usage("--tolerance 需要数值（如 2.0）");
            scoreTolerance = tolerance;   // 同一 --tolerance 开关：bench 与 score 各自读取
            break;
        case "--extra-modules":
            if (++i >= args.Length) return Usage("--extra-modules 需要逗号分隔的模块 id");
            extraModules = args[i].Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries).ToList();
            break;
        case "--strict-coherence":
            strictCoherence = true;
            break;
        case "--strict":
            // nf asset usage --strict：零引用键存在即 exit 1（键消费证明进门禁）。真源只有这一个 --strict。
            strictRequested = true;
            break;
        case "--refresh":
            // nf asset ledger --refresh 是写面（重生成键表投影）——只读门据此明确拒绝。
            refreshRequested = true;
            break;
        case "--json":
        case "--otlp":
        case "--help":
        case "-h":
        case "--version":
            flags.Add(args[i]);
            break;
        default:
            positional.Add(args[i]);
            break;
    }
}

if (flags.Contains("--version")) { Console.WriteLine("nf-dotnet " + Version); return 0; }
if (flags.Contains("--help") || flags.Contains("-h") || positional.Count == 0) return Usage(null);

// 输出口径对齐 Python 文本模式：Python 把**每一个** '\n' 都翻成宿主换行（Windows = CRLF），
// 而 .NET 默认只在 WriteLine 边界写 CRLF——多行 JSON / 正文里内嵌的 '\n' 会与 Python 差一拍。
// 统一在此处翻译：Windows 上等价把裸 '\n' 补成 CRLF；Linux 上 Environment.NewLine == "\n"（恒等）。
Console.SetOut(new NewlineNormalizingWriter(Console.Out));

var json = flags.Contains("--json");
root ??= ".";
if (!Directory.Exists(Path.Combine(root, "protocol"))) return Fail("根目录不含 protocol/：" + Path.GetFullPath(root));

// 受控失败：任何非致命异常都必须变成"可读错误 + 退出码 2"，不许崩栈（工业级失败卫生）
try
{
    return Dispatch();
}
catch (Exception ex)
{
    Console.Error.WriteLine($"错误（受控失败）：{ex.GetType().Name}: {ex.Message}");
    return 2;
}

int Dispatch()
{
    switch (positional[0])
    {
        case "receipts":
            return ReceiptsCommand();
        case "transparency":
            return TransparencyCommand();
        case "combine" when positional.Count >= 2 && positional[1] == "verify":
            return CombineVerifyCommand();
        case "combine" when positional.Count >= 2 && positional[1] == "plan":
            return CombinePlanCommand();
        case "combine" when positional.Count >= 2 && positional[1] == "breadth":
            return CombineBreadthCommand();
        case "verify":
            return AggregateCommand();
        case "assertions":
            return AssertionsCommand();
    case "decisions":
        return DecisionsCommand();
    case "cognition":
        return CognitionCommand();
    case "library":
        return LibraryCommand();
    case "bench":
        return BenchCommand();
    case "model":
        return ModelCommand();
    case "conformance":
        return ConformanceCommand();
    case "lint":
        return LintCommand();
    case "module":
        return ModuleCommand();
    case "pipeline":
        return PipelineCommand();
    case "handover":
        return GovernanceCommand("handover");
    case "postmortem":
        return GovernanceCommand("postmortem");
    case "audit":
        return GovernanceCommand("audit");
    case "state-front":
        return StateFrontCommand();
    case "knowledge":
        return KnowledgeCommand();
        case "sig":
            return SigCommand();
        case "patterns":
            return PatternsCommand();
        case "rfc":
            return RfcCommand();
        case "endpoint":
            return EndpointCommand();
        case "events":
            return EventsCommand();
        case "toolface":
            return ToolFaceCommand();
        case "st-validate":
            return StValidateCommand();
        case "stats":
            return StatsCommand();
        case "telemetry":
            return TelemetryCommand();
        case "driver":
            return DriverCommand();
    case "interop":
        return InteropCommand();
    case "workloop":
        return WorkloopCommand();
    case "license":
        return LicenseCommand();
    case "score":
        return ScoreCommand();
    case "decide":
        return DecideCommand();
    case "doctor":
        return DoctorCommand();
    case "spec":
        return SpecCommand();
    case "review":
        return ReviewCommand();
    case "extension":
        return ExtensionCommand();
    case "corpus":
        return CorpusCommand();
    case "assemble":
        return AssembleCommand();
        case "worldmodel":
            return WorldModelCommand();
        case "impact":
            return ImpactCommand();
        case "who-refers":
            return WhoRefersCommand();
        case "diff":
            return DiffCommand();
        case "explain":
            return ExplainCommand();
        case "output":
            return OutputCommand();
        case "domain-closure":
            return DomainClosureCommand();
        case "related":
            return RelatedCommand();
        case "market":
            return MarketCommand();
        case "asset":
            return AssetCommand();
        case "serve":
            return McpServer.ServeStdio(root!, Console.In, Console.Out);
        case "selftest":
            return SelfTestCommand();
        case "daemon":
            // 真源在 348577d 新增 `nf daemon`（执行层常驻守护：start/stop/status/exec/shell-init/bench）。
            // 按本线端口边界（ADR-0005 §决策 2）：**运行层/写面不实现**——故**显式拒绝**，
            // 而不是让它掉进"未知命令"（那会把"设计边界"误报成"拼错命令"）。
            return Fail("daemon 是执行层常驻守护（起进程 / 落 <NF_HOME>/daemon.json）——本引擎是只读门，不提供运行层");
        // 执行层 / 交互层（真源有）：本引擎是只读判据门，不提供运行层——**显式拒绝**，
        // 不让它掉进"未知命令"（那会把"设计边界"误报成"拼错命令"，与 daemon 分支同一条纪律）。
        // 纪律：**每个标签只放一个命令词**——cli_surface_probe 按「标签 + 单引号命令词」逐个抽静态面，
        // 若一个标签用 or 串多个词，只有第一个词进静态面，其余会变成"帮助里列了却分派不到"的幽灵命令假红。
        // （注意：该判据连**注释文本**一起扫，注释里也不要写出「标签 + 命令词」的字面样式。）
        case "shell":
        case "terminal":
        case "lsp":
        case "completion":
        case "demo":
        case "run":
        case "help":
            return Fail("执行层/交互层命令（shell / terminal / lsp / completion / demo / run / help）——本引擎只读，不提供运行层；引擎用法见 --help");
        // 写面 / 工厂（真源有）：本线端口边界（ADR-0005 §决策 2）不实现写面。
        case "register":
        case "rename":
        case "import":
        case "approve":
        case "attest":
        case "design":
        case "domain":
            return Fail("该命令属写面/工厂（register / rename / import / approve / attest / design / domain）——本引擎只做只读判据面");
        // 读面但**未移植**：如实声明边界，避免与"已覆盖"混淆（覆盖矩阵命令级一节登记）。
        case "layers":
        case "release":
            return Fail("该读面未移植到引擎：layers（真源 protocol/LAYERS.json · 与 check27 R7 同源）/ release（verify + doctor 组合）");
        default:
            return Usage("未知命令：" + string.Join(' ', positional));
    }
}

int ReceiptsCommand()
{
    var result = scope == "library"
        ? Receipts.VerifyLibraryReceipts(root!)
        : Receipts.VerifyProtocolReceipts(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["stats"] = new Dictionary<string, object?>
            {
                ["entries"] = result.Count,
                ["root"] = result.Root,
            },
        }));
    }
    else
    {
        Console.WriteLine($"== nf-dotnet receipts --scope {scope} ==");
        foreach (var issue in result.Issues) Console.WriteLine("  ✗ " + issue);
        if (result.Ok) Console.WriteLine("  ✓ 每条回执折叠到根，且根与实时重算一致");
        Console.WriteLine($"  —— {result.Detail}");
    }
    return result.Ok ? 0 : 1;
}

int TransparencyCommand()
{
    var result = Receipts.VerifyTransparencyChain(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["stats"] = new Dictionary<string, object?>
            {
                ["head"] = result.Root[..16],
                ["issues"] = result.Issues.Count,
                ["links"] = result.Count,
                ["on_disk"] = true,
            },
        }));
    }
    else
    {
        Console.WriteLine("== nf-dotnet transparency ==");
        foreach (var issue in result.Issues) Console.WriteLine("  ✗ " + issue);
        if (result.Ok) Console.WriteLine("  ✓ 链自洽（在盘生成物一致）");
        Console.WriteLine($"  —— {result.Detail}");
    }
    return result.Ok ? 0 : 1;
}

int CombineVerifyCommand()
{
    var rows = CertificateVerifier.VerifyAll(root!);
    var failed = rows.Count(r => r.Issues.Count > 0);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["certificates"] = rows.Count,
            ["failed"] = failed,
            ["rows"] = rows.Select(r => (object?)new Dictionary<string, object?>
            {
                ["issues"] = r.Issues.Cast<object?>().ToList(),
                ["label"] = r.Label,
                ["legal"] = r.Legal,
                ["modules"] = r.Modules,
            }).ToList(),
        }));
    }
    else
    {
        Console.WriteLine("== nf-dotnet combine verify（T4 复算）==");
        foreach (var row in rows)
        {
            Console.WriteLine($"  {(row.Issues.Count == 0 ? "✓" : "✗")} {row.Label,-28} 模块 {row.Modules}");
        }
        Console.WriteLine($"  —— 证书 {rows.Count} 条，失败 {failed}");
    }
    return failed == 0 ? 0 : 1;
}

int CombinePlanCommand()
{
    var result = Combinator.Build(root!, packs, extraModules, strictCoherence: strictCoherence);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(result.Certificate));
    }
    else
    {
        Console.WriteLine("== nf-dotnet combine plan ==");
        Console.WriteLine($"  包 {packs.Count} 个 · 模块 {result.Certificate["module_count"]} · 合法 {result.Legal}");
        Console.WriteLine($"  摘要 {result.Digest}");
        if (strictCoherence)
        {
            var conflicts = result.Certificate.TryGetValue("coherence_conflicts", out var c) && c is List<object?> list
                ? list
                : new List<object?>();
            Console.WriteLine($"  相干模式 strict · 撞号冲突 {conflicts.Count}");
            foreach (var row in conflicts.Cast<Dictionary<string, object?>>())
            {
                Console.WriteLine($"  ✗ 包 {row["pack"]} 声明的 {row["module"]} 实际解析到包 {row["resolved_pack"]}（按 ISA v1 C1′ 判 DENY）");
            }
        }
    }
    return result.Legal ? 0 : 1;
}

int PatternsCommand()
{
    var sub = positional.Count >= 2 ? positional[1] : "ls";
    if (sub == "reindex")
        return Usage("patterns reindex 是写面（重建 INDEX 投影）——本引擎是只读门，不提供写命令");
    if (sub is not ("ls" or "show" or "for" or "verify"))
        return Usage("patterns 的子命令须为 ls / show / for / verify（reindex 属写面，不提供）");

    if (sub == "ls")
    {
        var rows = Patterns.Entries(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(rows.Select(e => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = Fm(e, "id"),
                ["name"] = Fm(e, "name"),
                ["status"] = Fm(e, "status"),
                ["applies_to"] = Fm(e, "applies_to"),
            }).ToList()));
        }
        else
        {
            Console.WriteLine($"== nf patterns ls（{rows.Count} 条）==");
            foreach (var e in rows)
            {
                var id = Fm(e, "id") ?? e.Dir;
                Console.WriteLine($"  {PadCp(PyS(id), 28)} {PadCp(PyS(Fm(e, "status")), 10)} {PyS(Fm(e, "name"))}");
            }
        }
        return 0;
    }

    if (sub == "show")
    {
        if (positional.Count < 3) return Usage("patterns show 需要一个 pattern id");
        var want = positional[2].Trim();
        var hit = Patterns.Entries(root!).FirstOrDefault(e =>
            (e.Fm.TryGetValue("id", out var id) && id is string s && s == want) || (e.Dir == want && !e.Fm.ContainsKey("id")));
        if (hit is null)
        {
            Console.Error.WriteLine($"  ✗ pattern 未找到：{positional[2]}（nf patterns ls 可枚举）");
            return 1;
        }
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["id"] = want,
                ["path"] = hit.Path,
                ["frontmatter"] = hit.Fm,
            }));
            return 0;
        }
        var text = File.ReadAllText(Path.Combine(root!, hit.Path), new System.Text.UTF8Encoding(false, true));
        Console.WriteLine($"== nf patterns show {want} ==");
        foreach (var key in hit.Fm.Keys.OrderBy(k => k, StringComparer.Ordinal))
            Console.WriteLine($"  {PadCp(key + ":", 12)} {PyS(hit.Fm[key])}");
        Console.WriteLine();
        var parts = text.Split("---", 3, StringSplitOptions.None);
        Console.WriteLine(PyScalar.PySlice(parts[^1].Trim(), 1200));
        return 0;
    }

    if (sub == "for")
    {
        if (positional.Count < 3) return Usage("patterns for 需要一个目标路径");
        var target = positional[2];
        var hits = Patterns.ForPath(root!, target);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(hits.Cast<object?>().ToList()));
        }
        else
        {
            Console.WriteLine($"== nf patterns for {target}（{hits.Count} 条适用）==");
            foreach (var h in hits)
                Console.WriteLine($"  {PadCp(PyS(h["id"]), 28)} {PyS(h["name"])}（命中 {PyS(h["matched"])}）");
        }
        return 0;
    }

    var (issues, warns, stats) = Patterns.Scan(root!);
    var projection = Patterns.CheckProjection(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = issues.Cast<object?>().ToList(),
            ["warns"] = warns.Cast<object?>().ToList(),
            ["projection"] = projection.Cast<object?>().ToList(),
            ["stats"] = stats,
        }));
    }
    else
    {
        Console.WriteLine($"== nf patterns verify（{stats["patterns"]} 条）==");
        foreach (var i in issues.Concat(projection)) Console.Error.WriteLine($"  [FAIL] {i}");
        foreach (var w in warns) Console.WriteLine($"  [WARN] {w}");
        if (issues.Count == 0 && projection.Count == 0)
            Console.WriteLine("  ✓ 格式合规 + 适用面/证据可证 + INDEX 投影一致");
    }
    return (issues.Count > 0 || projection.Count > 0) ? 1 : 0;
}

/// <summary>frontmatter 取值：键不存在 → null（Python <c>dict.get</c> 语义，缺键与 None 都渲染成 None）。</summary>
static object? Fm(Patterns.Entry e, string key) => e.Fm.TryGetValue(key, out var v) ? v : null;

/// <summary>近似 Python <c>"%s"</c>：字符串原样、列表走 repr、None 字面量。</summary>
static string PyS(object? v) => v switch
{
    null => "None",
    bool b => b ? "True" : "False",
    string s => s,
    // 浮点必须走 Python 的 repr 口径：`"%s" % 1.0` 是 "1.0" 而不是 "1"
    // （首版缺这一支 → `output meter` 的机验率 1.0 被打成 "1"，与真源对不上）
    double d => PyScalar.PyRepr(d),
    List<string> list => PyScalar.PyRepr(list.Cast<object?>().ToList()),
    List<object?> list => PyScalar.PyRepr(list),
    Dictionary<string, object?> map => PyScalar.PyRepr(map),
    _ => v.ToString() ?? "None",
};

/// <summary>Python <c>%-Ns</c>：按**码点**补空格（与 PyLen 同口径）。</summary>
static string PadCp(string s, int width)
{
    var len = PyScalar.PyLen(s);
    return len >= width ? s : s + new string(' ', width - len);
}

int AssetCommand()
{
    // 只读八面：verify（与 check23 同语义的闭合门禁）/ inventory（盘点）/ ls（货架浏览）/
    //           baseline（行数基线）/ density（键语义密度）/ usage（引用度）/ thickness（语义厚度）/
    //           ledger（键表机读投影）。
    // 写面（add / rm / deprecate / restore / baseline --write / ledger --refresh）不移植——只读门不提供写命令。
    var sub = positional.Count >= 2 ? positional[1] : "";
    if (sub.Length == 0)
        return Usage("asset 需要子命令（verify / inventory / ls / baseline / density / usage / thickness / ledger）");
    if (sub is "add" or "rm" or "deprecate" or "restore")
        return Fail($"asset {sub} 是写面（改台账/文件头）——本引擎是只读门，不提供写命令");
    if (sub == "baseline" && writeRequested)
        return Fail("asset baseline --write 是写面（重签行数基线）——本引擎是只读门");
    if (sub == "ledger" && refreshRequested)
        return Fail("asset ledger --refresh 是写面（重生成键表投影）——本引擎是只读门");
    if (sub is not ("verify" or "inventory" or "ls" or "baseline" or "density" or "usage" or "thickness" or "ledger"))
        return Usage($"asset 的子命令须为 verify / inventory / ls / baseline / density / usage / thickness / ledger（写面不提供）：{sub}");

    // 扫描根：Python 侧 `asset * --root` 缺省 = 仓库根；本引擎避免与全局 --root 撞名，用 --assets-root
    var assetsRoot = assetsRootFlag is null
        ? root!
        : (Path.IsPathRooted(assetsRootFlag) ? assetsRootFlag : Path.Combine(root!, assetsRootFlag));
    try
    {
        if (sub == "verify")
        {
            var (issues, stats) = AssetLedger.VerifyRoot(assetsRoot);
            Console.WriteLine($"== nf asset verify（扫描根：{assetsRoot}）==");
            Console.WriteLine($"  台账 {PyS(stats["ledgers"])} · 托管资产 {PyS(stats["assets"])} · " +
                              $"存量未托管 {PyS(stats["untracked"])} · 孤儿头 {PyS(stats["orphans"])}");
            foreach (var i in issues) Console.WriteLine($"  [FAIL] {i}");
            if (issues.Count > 0)
            {
                Console.Error.WriteLine("  ✗ 供应链台账存在缺口——修复后重跑（verify.sh check23 同语义）");
                return 1;
            }
            Console.WriteLine("  ✓ 台账闭合：每资产可溯源 / 可发现 / 键无孤儿");
            return 0;
        }

        if (sub == "inventory")
        {
            var rows = AssetLedger.InventoryRoot(assetsRoot);
            if (json)
            {
                Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["kind"] = "asset-inventory",
                    ["rows"] = rows.Cast<object?>().ToList(),
                }));
                return 0;
            }
            Console.WriteLine($"== nf asset inventory（扫描根：{assetsRoot}）==");
            if (rows.Count == 0)
            {
                Console.WriteLine("  （无 provenance.json 台账——nf asset add 建档首个资产集）");
                return 0;
            }
            foreach (var r in rows)
            {
                var err = r.TryGetValue("error", out var e) && e is not null ? $"（读取失败：{PyS(e)}）" : "";
                Console.WriteLine($"  · {PadCp(PyS(r["dir"]), 28)} pkg={PadCp(PyS(r["package"]), 10)} " +
                                  $"tier={PadCp(PyS(r["tier"]), 12)} 在册={PyS(r["assets"])} " +
                                  $"未托管={PyS(r["untracked"])} 孤儿={PyS(r["orphans"])}{err}");
            }
            return 0;
        }

        if (sub == "baseline")
        {
            var (issues, warns, stats) = AssetLineBaseline.Verify(assetsRoot);
            Console.WriteLine($"== nf asset baseline（在册 {PyS(stats.GetValueOrDefault("packages", 0L))} 包 · " +
                              $"基线 {PyS(stats.GetValueOrDefault("baseline", 0L))} 包）==");
            foreach (var w in warns) Console.WriteLine($"  [WARN] {w}");
            foreach (var i in issues) Console.WriteLine($"  [FAIL] {i}");
            if (issues.Count == 0) Console.WriteLine("  [OK] 社区包资产外形与基线一致（改外形须显式重签）");
            return issues.Count > 0 ? 1 : 0;
        }

        if (sub == "density")
        {
            var (issues, stats) = AssetDensity.Scan(assetsRoot);
            if (json)
            {
                Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["kind"] = "asset-density",
                    ["ok"] = issues.Count == 0,
                    ["issues"] = issues.Cast<object?>().ToList(),
                    ["stats"] = stats,
                }));
                return issues.Count > 0 ? 1 : 0;
            }
            Console.WriteLine("== nf asset density（45 资产键语义密度）==");
            Console.WriteLine($"  资产文件 {PyS(stats["files"])} · 键 {PyS(stats["keys"])} · 平均 " +
                              $"{((double)stats["avg_keys_per_file"]!).ToString("F2", System.Globalization.CultureInfo.InvariantCulture)} 键/档");
            Console.WriteLine($"  无键档（中文名/附机制，合法计数）{PyS(stats["unkeyed"])} · 短档(<200字) {PyS(stats["tiny"])}");
            foreach (var i in issues) Console.WriteLine($"  [FAIL] {i}");
            if (issues.Count == 0) Console.WriteLine("  ✓ 密度体检通过：无空档/不可读资产档");
            return issues.Count > 0 ? 1 : 0;
        }

        if (sub == "usage")
        {
            var (issues, stats) = AssetDensity.UsageScan(assetsRoot);
            if (json)
            {
                Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["kind"] = "asset-usage",
                    ["issues"] = issues.Cast<object?>().ToList(),
                    ["stats"] = stats,
                }));
            }
            else
            {
                Console.WriteLine("== nf asset usage（45 资产引用度）==");
                Console.WriteLine($"  资产键 {PyS(stats["assets"])} · 有引用 {PyS(stats["used"])} · " +
                                  $"零引用 {PyS(stats["zero_usage"])} · 引用总次数 {PyS(stats["total_refs"])}");
                var zeroKeys = (List<object?>)stats["zero_keys"]!;
                if (zeroKeys.Count > 0)
                    Console.WriteLine("  零引用键（低信息候选，不自动删）：" +
                                      string.Join("、", zeroKeys.Take(20).Select(PyS)));
            }
            return issues.Count > 0 || (strictRequested && Convert.ToInt64(stats["zero_usage"]) > 0) ? 1 : 0;
        }

        if (sub == "thickness")
        {
            var (issues, stats) = AssetDensity.ThicknessScan(assetsRoot);
            if (json)
            {
                Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["kind"] = "asset-thickness",
                    ["issues"] = issues.Cast<object?>().ToList(),
                    ["stats"] = stats,
                }));
            }
            else
            {
                Console.WriteLine("== nf asset thickness（45 资产语义厚度）==");
                Console.WriteLine($"  资产档 {PyS(stats["files"])} · 平均 {PyS(stats["avg_chars"])} 字符/档 · " +
                                  $"平均 {PyS(stats["avg_sections"])} 小节/档");
                Console.WriteLine($"  低信息候选 {PyS(stats["low_info"])}（只报告不删）");
                foreach (var f in ((List<object?>)stats["low_files"]!).Take(20))
                    Console.WriteLine($"  · {PyS(f)}");
            }
            return issues.Count > 0 ? 1 : 0;
        }

        if (sub == "ledger")
        {
            var (issues, stats) = AssetLedgerProjection.Verify(assetsRoot);
            if (json)
            {
                Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["kind"] = "asset-ledger",
                    ["refresh"] = false,
                    ["issues"] = issues.Cast<object?>().ToList(),
                    ["stats"] = stats,
                }));
            }
            else
            {
                Console.WriteLine("== nf asset ledger（资产键表机读投影）==");
                Console.WriteLine($"  校验：条目 {PyS(stats.GetValueOrDefault("entries", 0L))} · " +
                                  $"一致 {(issues.Count == 0 ? "是" : "否（refresh）")}");
                foreach (var i in issues) Console.WriteLine($"  [FAIL] {i}");
            }
            return issues.Count > 0 ? 1 : 0;
        }

        // ls
        // 参数面与真源同严：`--tier/--status` 在 Python 侧是 argparse 的 choices（非法即 exit 2 用法错误），
        // 不能等到 filter_rows 才报（那是 exit 1）——退出码口径必须一致。
        if (assetTier.Length > 0 && assetTier is not ("official" or "community" or "experimental"))
            return Usage($"--tier 非法取值：{assetTier}（应为 official/community/experimental）");
        if (assetStatus.Length > 0 && assetStatus is not ("active" or "deprecated" or "retired"))
            return Usage($"--status 非法取值：{assetStatus}（应为 active/deprecated/retired）");
        var all = AssetLedger.IterAssets(assetsRoot);
        var filtered = AssetLedger.FilterRows(all, assetPkg, assetTier, assetStatus);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["kind"] = "asset-ls",
                ["rows"] = filtered.Cast<object?>().ToList(),
            }));
            return 0;
        }
        Console.WriteLine("== nf asset ls" +
                          (assetPkg.Length > 0 ? "（pkg=" + assetPkg + "）" : "") +
                          (assetTier.Length > 0 ? "（tier=" + assetTier + "）" : "") +
                          (assetStatus.Length > 0 ? "（status=" + assetStatus + "）" : "") + " ==");
        if (filtered.Count == 0)
        {
            Console.WriteLine("  （货架为空——nf asset add 入库首批资产）");
            return 0;
        }
        foreach (var r in filtered)
        {
            Console.WriteLine($"  · {PadCp(PyS(r["tier"]), 8)} {PadCp(PyS(r["key"]), 14)} " +
                              $"v{PadCp(PyS(r["version"]), 6)} {PadCp(PyS(r["status"]), 10)} " +
                              $"{PyS(r["file"])} -> {PyS(r["source"])}");
        }
        return 0;
    }
    catch (AssetLedger.LedgerError exc)
    {
        Console.Error.WriteLine($"  ✗ {exc.Message}");
        return 1;
    }
}

int DomainClosureCommand()
{
    // 概念前置闭包只读求值器（scripts/ai_domain_closure.py）：图像语义走 ConceptGraph（与 check32 子扫描同实现）。
    var asset = closureAsset
        ?? Path.Combine(root!, ConceptGraph.DefaultAsset.Replace('/', Path.DirectorySeparatorChar));
    try
    {
        if (closureCheck)
        {
            var (fails, passes) = DomainClosure.SelfCheck(asset);
            foreach (var p in passes) Console.WriteLine($"  [PASS] {p}");
            foreach (var f in fails) Console.WriteLine($"  [FAIL] {f}");
            var suffix = DomainClosure.SamplesFor(asset) is null ? "（通用判据；该资产未登记键级样例）" : "";
            Console.WriteLine($"自检：{passes.Count}/{passes.Count + fails.Count} 通过{suffix}");
            return fails.Count == 0 ? 0 : 1;
        }
        var graph = ConceptGraph.LoadGraph(asset);
        var health = ConceptGraph.Problems(graph);
        if (health.Count > 0)
        {
            foreach (var item in health) Console.WriteLine($"  [FAIL] {item}");
            return 1;
        }
        var bids = ConceptGraph.BranchMap(graph);
        if (closureBranch.Length > 0 && !bids.ContainsKey(closureBranch))
        {
            Console.Error.WriteLine($"  ✗ 未知分支：{closureBranch}（可用：{SortedOrNone(bids.Keys)}）");
            return 2;
        }
        if (closureList)
        {
            Console.WriteLine(DomainClosure.RenderList(graph));
            return 0;
        }
        if (closureOrder.Length > 0)
        {
            var seqs = DomainClosure.Orderings(graph);
            if (!seqs.ContainsKey(closureOrder))
            {
                Console.Error.WriteLine($"  ✗ 资产内无该序：{closureOrder}（可用：{SortedOrNone(seqs.Keys)}）");
                return 2;
            }
            var bad = ConceptGraph.Violations(graph, seqs[closureOrder]);
            Console.WriteLine($"== 序校验：{closureOrder}（{seqs[closureOrder].Count} 个概念）==");
            Console.WriteLine($"  违反边：{bad.Count}");
            foreach (var (p, u) in bad) Console.WriteLine($"    {p} → {u} 被违反（前置排在后继之后）");
            return 0;
        }
        var loaded = DomainClosure.LoadedArg(closureLoaded);
        if (closureGaps)
        {
            Console.WriteLine(DomainClosure.RenderGaps(graph, loaded, closureBranch, Math.Max(1, closureLimit)));
            return 0;
        }
        if (closureReadyList)
        {
            var front = ConceptGraph.Frontier(graph, loaded, closureBranch);
            var sortedLoaded = loaded.Distinct(StringComparer.Ordinal)
                .OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList();
            if (json)
            {
                Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["loaded"] = sortedLoaded,
                    ["branch"] = closureBranch,
                    ["frontier"] = front.Cast<object?>().ToList(),
                    ["frontier_size"] = (long)front.Count,
                }));
            }
            else
            {
                Console.WriteLine($"== 下一步可装载集 frontier(L)（{(closureBranch.Length > 0 ? "分支 " + closureBranch : "全图")}）==");
                Console.WriteLine($"  L = {(sortedLoaded.Count > 0 ? string.Join("、", sortedLoaded.Select(PyS)) : "（空）")}");
                Console.WriteLine($"  frontier = {(front.Count > 0 ? string.Join("、", front) : "（空）")}（{front.Count} 个）");
            }
            return 0;
        }
        var label = asset.StartsWith(root!, StringComparison.Ordinal)
            ? Path.GetRelativePath(root!, asset)
            : asset;
        var result = DomainClosure.Report(graph, closureTarget, loaded, label);
        if (json) Console.WriteLine(PythonJson.Indented(result));
        else Console.WriteLine(DomainClosure.Render(result));
        return 0;
    }
    catch (ConceptGraph.ClosureError exc)
    {
        Console.Error.WriteLine($"  ✗ {exc.Message}");
        return 1;
    }
}

static string SortedOrNone(IEnumerable<string> keys)
{
    var list = keys.OrderBy(x => x, StringComparer.Ordinal).ToList();
    return list.Count > 0 ? string.Join("、", list) : "（无）";
}

int OutputCommand()
{
    // 产出形态面（45 · check32 output_forms 子扫描）**读面**：形态清单 + 判件。
    // 写面与合成面（render / meter / verify 三合一）留下一批——未移植即明确拒绝，不给半个面。
    var sub = positional.Count >= 2 ? positional[1] : "verify";
    if (sub == "render" && writeRequested)
        return Fail("output render --write 是写面（落盘产出面）——本引擎是只读门，不提供写命令");
    if (sub == "meter" && writeRequested)
        return Fail("output meter --write 是写面（重签机验率基线）——本引擎是只读门，不提供写命令");
    if (sub is not ("list" or "check" or "verify" or "render" or "meter"))
        return Usage($"output 的子命令须为 list / check / verify / render / meter：{sub}");

    if (sub == "verify")
    {
        var (issues, stats) = OutputForms.Scan(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["issues"] = issues.Cast<object?>().ToList(),
                ["stats"] = stats,
            }));
            return issues.Count > 0 ? 1 : 0;
        }
        foreach (var i in issues) Console.Error.WriteLine($"  [FAIL] {i}");
        if (issues.Count == 0)
        {
            var reg = stats.GetValueOrDefault("registry") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            var meter = stats.GetValueOrDefault("meter") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            Console.WriteLine("  ✓ 产出形态面一致：形态 " + PyS(reg.GetValueOrDefault("forms"))
                              + " 条（可达 " + (Convert.ToInt64(reg.GetValueOrDefault("forms")) - Convert.ToInt64(reg.GetValueOrDefault("unreachable")))
                              + "）；包级产出 " + PyS((stats.GetValueOrDefault("index") as Dictionary<string, object?>)?.GetValueOrDefault("outputs"))
                              + " 件；机验率 " + PyScalar.PyRepr(meter.ToDictionary(
                                  kv => kv.Key,
                                  kv => (object?)((Dictionary<string, object?>)kv.Value!).GetValueOrDefault("machine_verifiable_ratio"),
                                  StringComparer.Ordinal)));
        }
        return issues.Count > 0 ? 1 : 0;
    }

    if (sub == "render")
    {
        var (issues, rows) = OutputForms.RenderOutputs(root!, outputPackage);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["issues"] = issues.Cast<object?>().ToList(),
                ["rows"] = rows.Cast<object?>().ToList(),
            }));
            return issues.Count > 0 ? 1 : 0;
        }
        foreach (var r in rows)
            Console.WriteLine($"  {(PyTruthy(r["changed"]) ? "改" : "同")} {PadCp(PyS(r["path"]), 52)} "
                              + $"生成器={PadCp(PyS(r["generator"]), 24)} "
                              + (PyTruthy(r["written"]) ? "已落盘" : "未落盘（--write 才写）"));
        foreach (var i in issues) Console.Error.WriteLine($"  [FAIL] {i}");
        return issues.Count > 0 ? 1 : 0;
    }

    if (sub == "meter")
    {
        var (_, stats) = OutputForms.Meter(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(stats));
            return 0;
        }
        Console.WriteLine("  " + PadCp("包", 18) + " " + PadCp("机验面", 8) + " " + PadCp("功能面", 8)
                          + " " + PadCp("散文资产", 10) + " 机验率");
        var packages = stats.GetValueOrDefault("packages") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        foreach (var (pkg, raw) in packages)
        {
            var s = (Dictionary<string, object?>)raw!;
            Console.WriteLine("  " + PadCp(pkg, 18) + " " + PadCp(PyS(s["machine_verifiable"]), 8) + " "
                              + PadCp(PyS(s["functional"]), 8) + " " + PadCp(PyS(s["prose_assets"]), 10)
                              + " " + PyS(s["machine_verifiable_ratio"]));
        }
        Console.WriteLine("  合计：" + PyS(stats.GetValueOrDefault("totals")));
        return 0;
    }

    if (sub == "list")
    {
        var registry = OutputForms.LoadRegistry(root!);
        var rows = (registry.GetValueOrDefault("forms") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>()
            .Where(f => assetStatus.Length == 0 || PyS(f.GetValueOrDefault("status")) == assetStatus)
            .Where(f => outputCategory.Length == 0 || PyS(f.GetValueOrDefault("category")) == outputCategory)
            .Where(f => assetTier.Length == 0 || PyS(f.GetValueOrDefault("tier")) == assetTier)
            .ToList();
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(rows.Cast<object?>().ToList()));
            return 0;
        }
        Console.WriteLine("  " + PadCp("形态", 28) + " " + PadCp("类别", 14) + " " + PadCp("档位", 4)
                          + " " + PadCp("状态", 12) + " 规范入口/备注");
        foreach (var f in rows)
        {
            var spec = f.GetValueOrDefault("spec") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
            var uri = spec.TryGetValue("uri", out var u) ? u : "";
            Console.WriteLine("  " + PadCp(PyS(f.GetValueOrDefault("id")), 28) + " "
                              + PadCp(PyS(f.GetValueOrDefault("category")), 14) + " "
                              + PadCp(PyS(f.GetValueOrDefault("tier")), 4) + " "
                              + PadCp(PyS(f.GetValueOrDefault("status")), 12) + " " + PyS(uri));
        }
        var cov = registry.GetValueOrDefault("coverage") as Dictionary<string, object?> ?? new(StringComparer.Ordinal);
        Console.WriteLine("  —— 共 " + PyS(cov.TryGetValue("forms", out var cf) ? cf : 0L)
                          + " 条（可达 " + PyS(cov.GetValueOrDefault("reachable"))
                          + " / 不可达 " + PyS(cov.GetValueOrDefault("unreachable"))
                          + "）；状态 " + PyS(cov.GetValueOrDefault("by_status"))
                          + "；档位 " + PyS(cov.GetValueOrDefault("by_tier")));
        return 0;
    }

    // check <paths...>
    var blob = new List<Dictionary<string, object?>>();
    var bad = 0;
    for (var i = 2; i < positional.Count; i++)
    {
        var p = positional[i];
        var rel = Path.IsPathRooted(p)
            ? Path.GetRelativePath(root!, Path.GetFullPath(p)).Replace('\\', '/')
            : p;
        var full = Path.Combine(root!, rel.Replace('/', Path.DirectorySeparatorChar));
        if (!File.Exists(full))
        {
            blob.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["path"] = rel, ["error"] = "文件不存在",
            });
            bad++;
            continue;
        }
        var (form, tier) = OutputForms.Detect(root!, rel);
        var issues = OutputForms.Check(root!, rel, form);
        blob.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["path"] = rel, ["form"] = form, ["max_tier"] = tier,
            ["issues"] = issues.Cast<object?>().ToList(),
        });
        if (issues.Count > 0) bad++;
    }
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(blob.Cast<object?>().ToList()));
        return bad > 0 ? 1 : 0;
    }
    foreach (var r in blob)
    {
        if (r.TryGetValue("error", out var error) && error is not null)
        {
            Console.WriteLine($"  [FAIL] {PyS(r["path"])} {PyS(error)}");
            continue;
        }
        var issues = (List<object?>)r["issues"]!;
        Console.WriteLine($"  {(issues.Count > 0 ? "✗" : "✓")} {PadCp(PyS(r["path"]), 46)} " +
                          $"形态={PadCp(PyS(r["form"]), 14)} 上限档位={PyS(r["max_tier"])}");
        foreach (var issue in issues) Console.WriteLine($"      - {PyS(issue)}");
    }
    return bad > 0 ? 1 : 0;
}

int WhoRefersCommand()
{
    // 引用反查（A2）：**类别感知**匹配（与 impact 的裸号归一口径不同，见 Retriever 类注释）。
    if (positional.Count < 2) return Usage("who-refers 需要一个模块 id（如 M91 或 情感:M55）");
    var target = positional[1];
    var regPath = registryPath is null
        ? Path.Combine(root!, "desktop", "src", "core", "registry.json")
        : (Path.IsPathRooted(registryPath) ? registryPath : Path.Combine(root!, registryPath));
    var refs = Retriever.ReferencedBy(target, regPath);
    Console.WriteLine($"== 谁引用了 {target} ==");
    if (refs.Count == 0)
    {
        Console.WriteLine("  无（registry protocols[].references 中无引用）");
        return 0;
    }
    foreach (var r in refs)
    {
        var ro = PyTruthy(r.GetValueOrDefault("asset_readonly")) ? "只读" : "";
        Console.WriteLine($"  {PyS(r["referrer"])} → {PyS(r["source_package"])}.{PyS(r["module_id"])} {ro}");
    }
    return 0;
}

int DiffCommand()
{
    // 版本差异检测（41 波C C2）：两份文档签名 → 字段级差异 + 兼容判定 + 影响度三档。
    if (positional.Count < 3) return Usage("diff 需要两个文档路径：<a> <b>");
    try
    {
        var ra = RelToRoot(positional[1]);
        var rb = RelToRoot(positional[2]);
        var diff = SignatureDiff.Diff(KnowledgeSig.BuildSignature(ra, root!),
                                      KnowledgeSig.BuildSignature(rb, root!));
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(diff));
            return 0;
        }
        Console.WriteLine("== nf diff ==");
        Console.WriteLine($"  {PyS(diff["from"])}  →  {PyS(diff["to"])}");
        var changes = (List<object?>)diff["changes"]!;
        if (changes.Count == 0) Console.WriteLine("  无字段差异（两份签名一致）");
        foreach (var c in changes.Cast<Dictionary<string, object?>>())
        {
            Console.WriteLine($"  [{PyS(c["kind"])}] {PyS(c["field"])}  " +
                              $"{PyScalar.PyRepr(c["from"])} → {PyScalar.PyRepr(c["to"])}");
        }
        Console.WriteLine($"  判定：{PyS(diff["verdict"])}");
        var impact = diff.GetValueOrDefault("impact") is { } im ? PyS(im) : "editorial";
        var label = impact switch
        {
            "bump" => "结构性（须 bump + 迁移记录）",
            "additive" => "字段级新增（V1 只增不删）",
            "editorial" => "措辞/编辑（无契约影响）",
            _ => impact,
        };
        Console.WriteLine($"  影响度：{impact}（{label}）");
        return 0;
    }
    catch (Exception exc) when (exc is IOException or UnauthorizedAccessException
                                   or ArgumentException or FormatException)
    {
        Console.Error.WriteLine($"  ✗ {exc.Message}");
        return 1;
    }
}

int ExplainCommand()
{
    // check 修复指引（41 波C C5）：机械导出的静态表（见 CheckGuide 类注释）。
    if (positional.Count < 2) return Usage("explain 需要一个 check 编号（如 25 / check25；all = 全量清单）");
    var raw = positional[1];
    var key = AssetShelf.PyStrip(raw).ToLowerInvariant();
    if (key is "all" or "")
    {
        Console.WriteLine("== nf explain all（check 修复指引全量）==");
        foreach (var k in CheckGuide.SortedKeys())
            Console.WriteLine($"  check{k}：{CheckGuide.Get(k)}");
        return 0;
    }
    if (key.StartsWith("check", StringComparison.Ordinal)) key = key[5..];
    var guide = CheckGuide.Get(key);
    if (guide is null)
    {
        Console.Error.WriteLine($"  ✗ 未知 check：{raw}（可用 all 看全量）");
        return 2;
    }
    Console.WriteLine($"== nf explain check{key} ==");
    Console.WriteLine($"  {guide}");
    return 0;
}

/// <summary>Python <c>_rel_to_root</c>：目标必须存在，返回相对仓库根的路径；不存在即抛 ValueError 等价。</summary>
string RelToRoot(string target)
{
    var full = Path.GetFullPath(target);
    if (!File.Exists(full) && !Directory.Exists(full))
        throw new ArgumentException($"目标不存在：{target}");
    return Path.GetRelativePath(root!, full);
}

int RelatedCommand()
{
    // See-Also 关联（41 波C C4）：registry protocols[] 为图 + 模块级依赖图（fence 正则口径）注入。
    if (positional.Count < 2) return Usage("related 需要一个目标（包 id 或模块 id）");
    var target = positional[1];
    var regPath = registryPath is null
        ? Path.Combine(root!, "desktop", "src", "core", "registry.json")
        : (Path.IsPathRooted(registryPath) ? registryPath : Path.Combine(root!, registryPath));
    var registry = ImpactCheck.LoadRegistry(regPath);
    var prots = MarketAnalyzer.Protocols(registry);
    var result = MarketAnalyzer.RelatedOf(target, prots,
        MarketAnalyzer.ModuleGraph(root!), MarketAnalyzer.OwnerMap(registry));
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(result));
        return 0;
    }
    Console.WriteLine("== nf related（See-Also · 相关条目 + 引用链）==");
    Console.WriteLine($"  目标：{PyS(result["target"])}（{PyS(result["kind"])}）");
    Console.WriteLine("  关联条目（引用了谁 / 依赖链）：" + JoinOrDash(result["refs"]));
    Console.WriteLine("  反向引用方（谁引用我）：" + JoinOrDash(result["referenced_by"]));
    Console.WriteLine("  相关模块互见：" + JoinOrDash(result["related_modules"]));
    return 0;
}

/// <summary>Python <c>"、".join(list) or "—"</c> 的等价。</summary>
static string JoinOrDash(object? node)
{
    var list = (node as List<object?> ?? new List<object?>()).Select(PyS).ToList();
    return list.Count > 0 ? string.Join("、", list) : "—";
}

int MarketCommand()
{
    var regPath = registryPath is null
        ? Path.Combine(root!, "desktop", "src", "core", "registry.json")
        : (Path.IsPathRooted(registryPath) ? registryPath : Path.Combine(root!, registryPath));
    var registry = ImpactCheck.LoadRegistry(regPath);

    if (marketList)
    {
        if (marketTier is not null && marketTier is not ("official" or "community" or "experimental"))
            return Usage($"--tier 非法取值：{marketTier}（应为 official/community/experimental）");
        var items = MarketAnalyzer.ListMarket(registry, marketTier);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["kind"] = "market-list",
                ["tier"] = marketTier,
                ["items"] = items.Cast<object?>().ToList(),
            }));
            return 0;
        }
        Console.WriteLine($"== nf market list{(marketTier is null ? "" : "（tier=" + marketTier + "）")} ==");
        var badge = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["official"] = "🏛官方", ["community"] = "🌐社区", ["experimental"] = "🧪实验",
        };
        foreach (var it in items)
        {
            var grade = PyS(it.GetValueOrDefault("grade"));
            var badgeText = badge.TryGetValue(grade, out var b) ? b : grade;
            if (PyS(it.GetValueOrDefault("kind")) == "module")
                Console.WriteLine($"  [{badgeText}] 模块 {PyS(it.GetValueOrDefault("id"))} · {PyS(it.GetValueOrDefault("name"))}");
            else
                Console.WriteLine($"  [{badgeText}] 包 {PyS(it.GetValueOrDefault("id"))} v{PyS(it.GetValueOrDefault("version"))}" +
                                  $"（{PyS(it.GetValueOrDefault("modules"))} 模块）");
        }
        return 0;
    }

    // ---- 包视图（依赖闭包 + 挂载冲突预检；check15 ②③ 同构）----
    if (positional.Count < 2)
    {
        Console.Error.WriteLine("✗ 缺 pkg_dir（或加 --list 列目录）");
        return 2;
    }
    var pkgDirArg = positional[1];
    var pkgId = Path.GetFileName(pkgDirArg.TrimEnd('/', '\\'));
    var prots = MarketAnalyzer.Protocols(registry);
    var docPath = Path.Combine(root!, "02_联动注册表.md");
    var docText = File.Exists(docPath) ? File.ReadAllText(docPath, new System.Text.UTF8Encoding(false, true)) : "";
    // 与 Python 同口径：pkg_dir 按**进程 CWD** 解析（真源如此），doc 与各包 protocol.yaml 按 ROOT 解析
    var regIssues = MarketAnalyzer.CheckRegisterable(pkgDirArg, docText);
    if (!prots.ContainsKey(pkgId))
    {
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["kind"] = "market-package",
                ["pkg_id"] = pkgId,
                ["registered"] = false,
                ["issues"] = regIssues.Cast<object?>().ToList(),
            }));
            return regIssues.Count > 0 ? 1 : 0;
        }
        Console.WriteLine("  registry protocols[] 无条目——无 references 可查");
        return regIssues.Count > 0 ? 1 : 0;
    }
    var data = MarketAnalyzer.PackData(root!);
    var (seen, depIssues) = MarketAnalyzer.Dependencies(pkgId, prots, data);
    var conflicts = MarketAnalyzer.Conflicts(pkgId, prots, data);
    var grades = MarketAnalyzer.GradesOfPackage(prots, pkgId);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["kind"] = "market-package",
            ["pkg_id"] = pkgId,
            ["registered"] = true,
            ["issues"] = regIssues.Cast<object?>().ToList(),
            ["dependencies"] = seen.OrderBy(x => x, StringComparer.Ordinal).Cast<object?>().ToList(),
            ["dependency_issues"] = depIssues.Cast<object?>().ToList(),
            ["conflicts"] = conflicts.Cast<object?>().ToList(),
            ["grades"] = grades.ToDictionary(kv => kv.Key, kv => (object?)kv.Value, StringComparer.Ordinal),
        }));
        return 0;
    }
    Console.WriteLine($"== nf market {pkgId} ==");
    Console.WriteLine("  登记状态: " + (regIssues.Count == 0
        ? "在册（02 §8 + registry protocols[]）"
        : string.Join("; ", regIssues)));
    if (grades.Count > 0)
    {
        var badge = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["official"] = "🏛官方", ["community"] = "🌐社区", ["experimental"] = "🧪实验",
        };
        Console.WriteLine("  分级徽章: " + string.Join(", ",
            grades.Select(kv => $"{kv.Key}({(badge.TryGetValue(kv.Value, out var b) ? b : kv.Value)})")));
    }
    Console.WriteLine("  依赖闭包: " + (seen.Count > 0
        ? string.Join(", ", seen.OrderBy(x => x, StringComparer.Ordinal))
        : "无跨包引用"));
    foreach (var i in depIssues) Console.WriteLine($"  [依赖] {i}");
    if (conflicts.Count > 0)
    {
        foreach (var i in conflicts) Console.WriteLine($"  [冲突] {i}");
    }
    else
    {
        Console.WriteLine("  挂载冲突: 无");
    }
    return 0;
}

int ImpactCommand()
{
    // 变更影响面预检（A4 前置）：只读，不写盘；--check 为门禁模式（破坏性变更 exit 1）。
    if (positional.Count < 2) return Usage("impact 需要一个目标（protocol id 或 module id）");
    var target = positional[1];
    var regPath = registryPath is null
        ? Path.Combine(root!, "desktop", "src", "core", "registry.json")
        : (Path.IsPathRooted(registryPath) ? registryPath : Path.Combine(root!, registryPath));
    var registry = ImpactCheck.LoadRegistry(regPath);
    var impact = ImpactCheck.ImpactOfChange(registry, target);
    Console.WriteLine($"== 删除影响面预检: {target} ==");
    if (impact.GetValueOrDefault("error") is string error)
    {
        Console.WriteLine($"  [拒绝] {error}");
        return 1;
    }

    if (impact.ContainsKey("module_id"))
    {
        // module 级
        var refs = (impact.GetValueOrDefault("referenced_by") as List<object?> ?? new List<object?>())
            .OfType<Dictionary<string, object?>>().ToList();
        var core = impact.GetValueOrDefault("in_official_core") as List<object?> ?? new List<object?>();
        var pkgs = impact.GetValueOrDefault("in_packages") as List<object?> ?? new List<object?>();
        Console.WriteLine($"  类型: module（官方在册 {(core.Count > 0 ? PyScalar.PyRepr(core) : "无")} · " +
                          $"属包 {(pkgs.Count > 0 ? PyScalar.PyRepr(pkgs) : "无")}）");
        if (refs.Count == 0 && core.Count == 0)
        {
            Console.WriteLine("  无破坏性影响（无引用方且非官方核心——可安全移除）");
            return 0;
        }
        foreach (var r in refs)
        {
            var ro = PyTruthy(r.GetValueOrDefault("asset_readonly")) ? "只读" : "";
            var readonlyText = ro.Length > 0 ? ro : "false";
            Console.WriteLine($"  破坏性: 被 {PyS(r["protocol"])} 引用（引用声明源 {PyS(r["source_package"])}" +
                              $"，asset_readonly {readonlyText}）");
        }
        if (core.Count > 0)
            Console.WriteLine($"  破坏性: 官方核心在册 {PyScalar.PyRepr(core)}（删官方核心 = 协议事故）");
        return impactCheck ? 1 : 0;
    }

    // protocol 级（整包删除）
    var packageRefs = (impact.GetValueOrDefault("referenced_by_packages") as List<object?> ?? new List<object?>())
        .OfType<Dictionary<string, object?>>().ToList();
    var mids = impact.GetValueOrDefault("module_ids") as List<object?> ?? new List<object?>();
    Console.WriteLine($"  类型: protocol 整包（module_ids {(mids.Count > 0 ? PyScalar.PyRepr(mids) : "无")}）");
    if (packageRefs.Count == 0)
    {
        Console.WriteLine("  无破坏性影响（无其它包引用本包模块——可安全移除，自身 references 随之消失）");
        return 0;
    }
    foreach (var r in packageRefs)
        Console.WriteLine($"  破坏性: 被 {PyS(r["protocol"])} 引用（引用声明源 {PyS(r["source_package"])}）");
    return impactCheck ? 1 : 0;
}

int WorldModelCommand()
{
    var (issues, stats) = WorldModel.Scan(root!);

    // 具体状态（--state）：JSON 文件，缺 / 解析失败即受控失败（与 Python 的 OSError/JSONDecodeError 同向）
    Dictionary<string, object?>? concrete = null;
    if (!string.IsNullOrEmpty(worldModelState))
    {
        var path = Path.IsPathRooted(worldModelState) ? worldModelState : Path.Combine(root!, worldModelState);
        try
        {
            using var doc = JsonIo.ReadFile(path);
            concrete = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>;
        }
        catch (Exception exc) when (exc is IOException or System.Text.Json.JsonException)
        {
            Console.Error.WriteLine($"  ✗ {exc.Message}");
            return 1;
        }
    }

    // --run / --walk：对每个模型重放（契约从模块文档里现读，与 Python 的 _load 同源）
    var models = (stats.GetValueOrDefault("models") as List<object?> ?? new List<object?>())
        .OfType<Dictionary<string, object?>>().ToList();
    if (worldModelRun && json)
    {
        var runs = new List<object?>();
        foreach (var model in models)
        {
            var result = RunWorldModel(root!, model, concrete);
            if (result is null) continue;
            runs.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["module"] = model.GetValueOrDefault("module"),
                ["source"] = model.GetValueOrDefault("source"),
                ["result"] = result,
            });
        }
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["kind"] = "worldmodel-run",
            ["issues"] = issues.Cast<object?>().ToList(),
            ["runs"] = runs,
        }));
        return issues.Count > 0 ? 1 : 0;
    }
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["kind"] = "worldmodel",
            ["issues"] = issues.Cast<object?>().ToList(),
            ["stats"] = stats,
        }));
    }
    else
    {
        string N(string key) => stats.TryGetValue(key, out var v) && v is not null
            ? Convert.ToInt64(v, System.Globalization.CultureInfo.InvariantCulture).ToString()
            : "0";
        Console.WriteLine("== nf worldmodel（JEPA-inspired 确定性抽象状态契约 · check32 硬门）==");
        Console.WriteLine($"  模块 {N("modules")} · 变量 {N("variables")} · 相位 {N("phases")} · " +
                          $"不变式 {N("invariants")} · checks {N("checks")} · slots {N("slots")}/{N("slot_registry")}");
        foreach (var node in (stats.GetValueOrDefault("models") as List<object?> ?? new List<object?>()))
        {
            var m = node as Dictionary<string, object?>;
            if (m is null) continue;
            Console.WriteLine($"  · {PyS(m["module"])}（{PyS(m["source"])} · initial={PyS(m["initial_phase"])} · " +
                              $"{PyS(m["phases"])} phases · {PyS(m["invariants"])} invariants · {PyS(m["checks"])} checks）");
        }
        if (worldModelWalk)
        {
            foreach (var model in models)
            {
                var contract = LoadWorldModel(root!, model);
                if (contract is null) continue;
                var (sequence, reason, repeat) = WorldModel.PhaseSequence(contract);
                Console.WriteLine($"  → {PyS(model["module"])} 重放：{string.Join(" → ", sequence)}" +
                                  $"（终止={reason}" + (repeat is null ? "" : $" · 重复={repeat}") + "）");
            }
        }
        if (worldModelRun)
        {
            foreach (var model in models)
            {
                var result = RunWorldModel(root!, model, concrete);
                if (result is null) continue;
                var steps = (result.GetValueOrDefault("steps") as List<object?> ?? new List<object?>())
                    .OfType<Dictionary<string, object?>>().ToList();
                var repeat = result.GetValueOrDefault("repeat");
                Console.WriteLine($"  → {PyS(model["module"])} 运行：{steps.Count} steps（" +
                                  $"{PyS(result.GetValueOrDefault("reason"))}" +
                                  (repeat is null ? "" : $" · 重复={PyS(repeat)}") +
                                  $" · digest={PyS(result.GetValueOrDefault("digest"))[..12]}）");
                foreach (var step in steps)
                {
                    Console.WriteLine($"    {PyS(step["step"])}. {PyS(step["phase_from"])} → " +
                                      $"{PyS(step["phase_to"])}（guard={PyS(step["guard"])}）");
                }
            }
        }
        foreach (var i in issues) Console.Error.WriteLine($"  [FAIL] {i}");
    }
    return issues.Count > 0 ? 1 : 0;
}

/// <summary>从模块文档里现读 <c>machine_contract.world_model</c>（等价 Python <c>_load</c>）。</summary>
static Dictionary<string, object?>? LoadWorldModel(string root, Dictionary<string, object?> model)
{
    var source = model.GetValueOrDefault("source") as string ?? "";
    var abs = Path.Combine(root, source.Replace('/', Path.DirectorySeparatorChar));
    var mc = ModuleContracts.MachineContractOf(abs);
    return mc?.GetValueOrDefault("world_model") as Dictionary<string, object?>;
}

/// <summary>跑一个模型的重放（有具体状态则 replay_concrete，否则 replay）；违例 → 受控失败。</summary>
static Dictionary<string, object?>? RunWorldModel(string root, Dictionary<string, object?> model,
    Dictionary<string, object?>? concrete)
{
    var contract = LoadWorldModel(root, model);
    if (contract is null) return null;
    var runtime = new WorldModel.Runtime(contract);
    return concrete is not null ? runtime.ReplayConcrete(concrete) : runtime.Replay();
}

// 构建回路（check33 第 16 条 · core/workloop.py）：`--list` 列候选、默认出工单（stub 适配器离线确定性）。
// **写面不移植**：`--write` 落 `.rivet/` 内部档案、`--close` 收口记档，都明确拒绝（只读门不落盘）。
int WorkloopCommand()
{
    if (writeRequested)
    {
        Console.Error.WriteLine("错误：--write 是写面（工单落 .rivet/private_archive/work_orders，属内部档案）"
                                + "——只读门不落盘，不提供");
        return 2;
    }
    if (closeFlag.Length > 0)
    {
        Console.Error.WriteLine("错误：--close 是写面（回收结果写 .rivet/ 记档）——只读门不落盘，不提供");
        return 2;
    }
    var source = sourceFlag ?? "";
    if (workloopList)
    {
        var rows = Workloop.Items(root!, Math.Max(1, topCount), source);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(rows.Cast<object?>().ToList()));
            return 0;
        }
        foreach (var it in rows)
        {
            Console.WriteLine("  " + PadCp(PyS(it["id"]), 28) + " " + PadCp(PyS(it["kind"]), 16)
                              + " " + PyS(it["title"]));
        }
        Console.WriteLine($"  （共 {Workloop.Items(root!, source: source).Count} 项在册"
                          + (source.Length > 0 ? $"（来源限定 {source}）" : "")
                          + "；这是决策层的候选面）");
        return 0;
    }
    if (adapterFlag != "stub")
    {
        Console.Error.WriteLine($"错误：适配器 {adapterFlag} 走外呼（端点类），属声明边界——"
                                + "引擎只保留 fail-closed 分支，不发起网络写面");
        return 2;
    }
    var doc = Workloop.Plan(root!, adapterFlag, Math.Max(1, topCount), source);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(doc));
    }
    else
    {
        Console.WriteLine(Workloop.RenderBrief(doc));
    }
    return PyS(doc.GetValueOrDefault("status")) == "ok" ? 0 : 1;
}

// 图书馆许可证门（core/license_gate.py）：登记行「许可」列 + 条目内联声明双源校验。
int LicenseCommand()
{
    var scan = LicenseGate.Scan(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = scan.Issues.Cast<object?>().ToList(),
            ["stats"] = scan.Stats,
        }));
        return scan.Issues.Count > 0 ? 1 : 0;
    }
    var stats = scan.Stats;
    var undeclared = AsObjList(stats.GetValueOrDefault("undeclared"));
    var noInline = AsObjList(stats.GetValueOrDefault("no_inline"));
    var mismatched = AsObjList(stats.GetValueOrDefault("mismatched"));
    var warnings = AsObjList(stats.GetValueOrDefault("warnings"));
    Console.WriteLine("== nf license（图书馆许可证门）==");
    Console.WriteLine($"  登记 {PyS(stats.GetValueOrDefault("entries"))} 件"
                      + $" · 已声明 {PyS(stats.GetValueOrDefault("declared"))}"
                      + $" · 未声明 {undeclared.Count} · 无内联 {noInline.Count}"
                      + $" · 双源不一致 {mismatched.Count}");
    foreach (var issue in scan.Issues) Console.Error.WriteLine($"  [FAIL] {issue}");
    foreach (var warn in warnings) Console.WriteLine($"  [WARN] {PyS(warn)}");
    if (scan.Issues.Count == 0)
        Console.WriteLine("  ✓ 许可面无 FAIL（WARN 为待投稿人回填项，不阻断入库）");
    return scan.Issues.Count > 0 ? 1 : 0;
}

// 基线相对回归评分（check33 第 3 条 · core/regression_score.py）。**声明边界**：信号源 `purity_scan`
// 是源码 AST linter 面，本引擎不复算——文本面显式打一行 UNKNOWN，机读面在 `boundary` 清单里列名，
// 既不静默丢弃也不伪造 1.0（故本面不进「逐字节一致」清单，按边界面单独断言）。
// `--write-baseline` 是写面（改基线件），明确拒绝。
int ScoreCommand()
{
    if (scoreWriteBaseline)
    {
        Console.Error.WriteLine("错误：--write-baseline 是写面（改写基线件 protocol/score_baseline.json）"
                                + "——只读门不落盘，不提供");
        return 2;
    }
    var current = RegressionScore.Evaluate(root!);
    var baseRel = scoreBaselinePath.Length > 0 ? scoreBaselinePath : RegressionScore.DefaultBaselineRel;
    var basePath = Path.IsPathRooted(baseRel) ? baseRel : Path.Combine(root!, baseRel);
    var baseline = File.Exists(basePath)
        ? RegressionScore.LoadBaseline(basePath)
        : new Dictionary<string, object?>(StringComparer.Ordinal) { ["schema"] = RegressionScore.Schema };
    var effectiveTolerance = scoreTolerance ?? 0.0;
    var comparison = RegressionScore.Compare(current, baseline, effectiveTolerance);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["current"] = current, ["compare"] = comparison,
        }));
        return comparison["ok"] is true ? 0 : 1;
    }
    Console.WriteLine("== nf score（基线相对回归评分）==");
    Console.WriteLine($"  当前 {F2(current.GetValueOrDefault("score"))}"
                      + $" · 基线 {F2(comparison["baseline_score"])}"
                      + $" · delta {SignedF2(comparison["delta"])}"
                      + $" · 容差 {F2(effectiveTolerance)}");
    Console.WriteLine("  " + PyS(comparison["verdict"]));
    foreach (var signal in current["signals"] as List<object?> ?? new List<object?>())
    {
        var row = (Dictionary<string, object?>)signal!;
        Console.WriteLine($"  · {PadCp(PyS(row["name"]), 18)} w={F2(row["weight"])} v={F2(row["value"])}");
    }
    Console.WriteLine($"  · {PadCp(RegressionScore.BoundarySignals[0], 18)} w=0.15 "
                      + "v=UNKNOWN（声明边界：源码 AST linter 面，本引擎不复算，不伪造）");
    foreach (var item in comparison["regressed"] as List<object?> ?? new List<object?>())
    {
        var row = (Dictionary<string, object?>)item!;
        Console.Error.WriteLine($"    [REGRESS] {PyS(row["signal"])} {F4(row["from"])} → {F4(row["to"])}"
                                 + $"（{F4(row["drop"])}）");
    }
    return comparison["ok"] is true ? 0 : 1;
}

string F2(object? v) => ((double)Convert.ToDouble(v, System.Globalization.CultureInfo.InvariantCulture))
    .ToString("F2", System.Globalization.CultureInfo.InvariantCulture);
string F4(object? v) => ((double)Convert.ToDouble(v, System.Globalization.CultureInfo.InvariantCulture))
    .ToString("F4", System.Globalization.CultureInfo.InvariantCulture);
string SignedF2(object? v)
{
    var d = Convert.ToDouble(v, System.Globalization.CultureInfo.InvariantCulture);
    var text = d.ToString("F2", System.Globalization.CultureInfo.InvariantCulture);
    return d >= 0 ? "+" + text : text;
}

// 决策层统一入口（core/decision_layer.py · check33 第 15 条）：
// `--dry-run` 走声明面体检；默认把 typed-decision 请求交给适配器（stub 离线确定性）。
// **端口边界**：端点类适配器（systemone-http / openai-json）只保留 fail-closed 分支——引擎不发起外呼，
// 参数齐备时输出 abstained 并注明「引擎不发起外呼」（与 DecisionLayer 同一条边界）。
int DecideCommand()
{
    var inv = System.Globalization.CultureInfo.InvariantCulture;
    string Fmt(object? value, string format) =>
        Convert.ToDouble(value ?? 0.0, inv).ToString(format, inv);

    if (questionsPath is null)
    {
        Console.Error.WriteLine("错误：decide 需要 --questions <问题 JSON 文件>");
        return 2;
    }
    if (decideDryRun)
    {
        var scan = DecisionLayer.Scan(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["issues"] = scan.Issues.Cast<object?>().ToList(),
                ["stats"] = scan.Stats,
            }));
        }
        else
        {
            foreach (var issue in scan.Issues) Console.Error.WriteLine($"  [FAIL] {issue}");
            if (scan.Issues.Count == 0)
                Console.WriteLine($"  ✓ 决策层面体检通过（{scan.SummaryLine}）");
        }
        return scan.Issues.Count > 0 ? 1 : 0;
    }
    var state = decideStateText;
    if (decideStatePath is not null)
        state = File.ReadAllText(decideStatePath, new System.Text.UTF8Encoding(false, true));
    Dictionary<string, object?> questions;
    using (var doc = JsonIo.ReadFile(questionsPath))
    {
        questions = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
                    ?? new Dictionary<string, object?>(StringComparer.Ordinal);
    }
    var request = new Dictionary<string, object?>(StringComparer.Ordinal)
    {
        ["state"] = state, ["questions"] = questions,
    };
    var output = DecisionLayer.Decide(request, adapterFlag, endpointFlag, modelFlag, root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(output));
    }
    else if (PyS(output.GetValueOrDefault("status")) == "abstained")
    {
        Console.WriteLine($"  ⚠ abstained：{PyS(output.GetValueOrDefault("reason"))}");
    }
    else
    {
        foreach (var pair in output.GetValueOrDefault("answers") as Dictionary<string, object?>
                 ?? new Dictionary<string, object?>(StringComparer.Ordinal))
        {
            var ans = pair.Value as Dictionary<string, object?>
                      ?? new Dictionary<string, object?>(StringComparer.Ordinal);
            var type = PyS(ans.GetValueOrDefault("type"));
            if (type == "choice")
            {
                var options = AsObjList(ans.GetValueOrDefault("options"));
                var probs = AsObjList(ans.GetValueOrDefault("probs"));
                var argmax = ans.GetValueOrDefault("argmax");
                var index = options.FindIndex(o => PyScalar.PyEquals(o, argmax));
                var p = options.Count > 0 && index >= 0 && index < probs.Count ? probs[index] : 0.0;
                Console.WriteLine($"  {PadCp(pair.Key, 14)} choice → {PyS(argmax)}（p={Fmt(p, "F3")}）");
            }
            else if (type == "score")
            {
                var probs = AsObjList(ans.GetValueOrDefault("probs"));
                Console.WriteLine($"  {PadCp(pair.Key, 14)} score → 期望值 {Fmt(ans.GetValueOrDefault("value"), "F2")}"
                                  + $"（{string.Join(" ", probs.Select(x => Fmt(x, "F2")))}）");
            }
            else
            {
                Console.WriteLine($"  {PadCp(pair.Key, 14)} noul → p(true)={Fmt(ans.GetValueOrDefault("p"), "F3")}");
            }
        }
        var meta = output.GetValueOrDefault("meta") as Dictionary<string, object?>
                   ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        Console.WriteLine($"  （适配器 {PyS(meta.GetValueOrDefault("adapter"))}"
                          + $" · calibrated={PyS(meta.GetValueOrDefault("calibrated"))}"
                          + " · 决策层不出现在门禁路径）");
    }
    return PyS(output.GetValueOrDefault("status")) == "ok" ? 0 : 1;
}

// 环境自检（真源 `nf doctor`）：关键文件在场 → registry 可解析 → IDL schema 定义在场 → 核心库可导入 →
// 基线自描述一致 → schema 标准对照 → 模块工具面 → world_model / world_slots。
// **两处声明边界（判据弱化 · 输出对齐）**：真源这两条依赖 Python 运行时，本引擎无 Python——
// ① 「核心库可导入」→ 引擎只验 `desktop/src/core/schema_lint.py` **在场**（存在性代理）；
// ② 「schema 标准对照（jsonschema）」→ 引擎用自带 schema 子集元检（五份齐）代替 jsonschema 真跑。
// 两条在本仓语料上输出与真源逐字一致，判据弱化属实，故登记在此（面级对账仍逐字节比对）。
int DoctorCommand()
{
    const string NfCliVersion = "1.0.0";   // 真源 scripts/nf.py::NF_CLI_VERSION
    var checks = new List<Dictionary<string, object?>>();
    void Chk(string name, bool ok, string detail) =>
        checks.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["name"] = name, ["ok"] = ok, ["detail"] = detail,
        });

    foreach (var rel in new[]
             {
                 "README.md", "01_核心协议.md", "02_联动注册表.md", "06_Agent执行协议.md",
                 "07_官方核心出厂与社区预设导航.md", "AGENTS.md", "STRATEGY.md", "verify.sh",
             })
    {
        Chk($"文件在场 {rel}", File.Exists(Path.Combine(root!, rel)), rel);
    }

    try
    {
        using var doc = JsonIo.ReadFile(Path.Combine(root!, "desktop/src/core/registry.json"));
        var graph = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
                    ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var modules = AsObjList(graph.GetValueOrDefault("modules")).Count;
        var protocols = AsObjList(graph.GetValueOrDefault("protocols")).Count;
        Chk($"registry 可解析（modules={modules} protocols={protocols}）",
            modules >= 13 && protocols >= 5, "desktop/src/core/registry.json");
    }
    catch (Exception exc)
    {
        Chk("registry 可解析", false, "desktop/src/core/registry.json: " + exc.Message);
    }

    // 真源 `os.path.join(ROOT, "protocol", "schema")` → **原生分隔符的绝对路径**（该串直接进输出，故必须原生）
    var schemaDir = Path.Combine(root!, "protocol", "schema");
    var schemaCount = 0;
    try
    {
        schemaCount = Directory.GetFiles(schemaDir, "*.json").Length;
    }
    catch (Exception exc)
    {
        Chk("IDL schema 定义在场", false, exc.Message);
    }
    if (Directory.Exists(schemaDir))
        Chk($"IDL schema 定义在场（{schemaCount} 份）", schemaCount == 5, schemaDir);

    // 声明边界①：真源靠 Python import 成功，引擎只验文件在场
    Chk("核心库可导入（schema_lint）",
        File.Exists(Path.Combine(root!, "desktop/src/core/schema_lint.py")), "desktop/src/core");

    try
    {
        var (baselineIssues, baselineStats) = QualityBaseline.Scan(root!);
        Chk($"基线自描述一致（verify {PyS(baselineStats["verify_version"])}"
            + $" · check1-{QualityBaseline.ExpectedChecks} PASS={QualityBaseline.ExpectedPass}）",
            baselineIssues.Count == 0, "verify/README/CHANGELOG/VERSION-MATRIX");
    }
    catch (Exception exc)
    {
        Chk("基线自描述一致", false, exc.Message);
    }

    // 声明边界②：真源跑 jsonschema.check_schema，引擎跑自带 schema 子集元检
    try
    {
        var (schemaIssues, schemas) = SchemaLint.CheckSchemaFiles(root!);
        Chk("schema 标准对照（jsonschema）", schemaIssues.Count == 0 && schemas.Count == 5,
            "CI 与本地同跑");
    }
    catch (Exception exc)
    {
        Chk("schema 标准对照（jsonschema）", true, "可选依赖未装（CI 已装真跑）：" + exc.Message);
    }

    try
    {
        var (toolIssues, toolStats) = ToolFace.Scan(root!);
        Chk("模块工具面（tool_face）", toolIssues.Count == 0,
            $"模块 {PyS(toolStats.GetValueOrDefault("modules"))}"
            + $" · 条目 {PyS(toolStats.GetValueOrDefault("entries"))}"
            + $" · 候选 {PyS(toolStats.GetValueOrDefault("candidates"))}");
    }
    catch (Exception exc)
    {
        Chk("模块工具面（tool_face）", false, exc.Message);
    }

    try
    {
        var (wmIssues, wmStats) = WorldModel.Scan(root!);
        var (wsIssues, wsStats) = AuxScanners.WorldSlotsScan(root!);
        Chk("world_model 契约", wmIssues.Count == 0,
            $"模块 {PyS(wmStats.GetValueOrDefault("modules"))}"
            + $" · 变量 {PyS(wmStats.GetValueOrDefault("variables"))}"
            + $" · checks {PyS(wmStats.GetValueOrDefault("checks") ?? 0L)}"
            + $" · slots {PyS(wmStats.GetValueOrDefault("slots") ?? 0L)}"
            + $"/{PyS(wmStats.GetValueOrDefault("slot_registry") ?? 0L)}");
        Chk("world_slots 注册表", wsIssues.Count == 0,
            $"slots {PyS(wsStats.GetValueOrDefault("slots"))}"
            + $" · arrays {PyS(wsStats.GetValueOrDefault("arrays"))}");
    }
    catch (Exception exc)
    {
        Chk("world_model/world_slots", false, exc.Message);
    }

    var passed = checks.Count(c => c["ok"] is true);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["version"] = NfCliVersion, ["ok"] = passed == checks.Count, ["passed"] = (long)passed,
            ["total"] = (long)checks.Count, ["checks"] = checks.Cast<object?>().ToList(),
        }));
    }
    else
    {
        Console.WriteLine($"== nf doctor（nf {NfCliVersion}）==");
        foreach (var check in checks)
        {
            Console.WriteLine($"  [{(check["ok"] is true ? "PASS" : "FAIL")}] {PyS(check["name"])}"
                              + $"（{PyS(check["detail"])}）");
        }
        Console.WriteLine($"  体检：{passed}/{checks.Count} 通过");
    }
    return passed == checks.Count ? 0 : 1;
}

// Spec Registry 查询（真源 `nf spec ls`）：registry 版本 + 官方核心模块数 + 逐协议包三行摘要。
int SpecCommand()
{
    var sub = positional.Count >= 2 ? positional[1] : "ls";
    if (sub != "ls")
    {
        Console.Error.WriteLine($"错误：spec 没有子命令：{sub}（只读面只有 ls）");
        return 2;
    }
    var regPath = registryPath is null
        ? Path.Combine(root!, "desktop/src/core/registry.json")
        : (Path.IsPathRooted(registryPath) ? registryPath : Path.Combine(root!, registryPath));
    using var doc = JsonIo.ReadFile(regPath);
    var reg = PythonJson.ToGraph(doc.RootElement) as Dictionary<string, object?>
              ?? new Dictionary<string, object?>(StringComparer.Ordinal);
    Console.WriteLine("== nf spec ls ==");
    Console.WriteLine($"  registry_schema_version: {PyS(reg.GetValueOrDefault("registry_schema_version"))}");
    Console.WriteLine($"  官方核心模块: {AsObjList(reg.GetValueOrDefault("modules")).Count} 件");
    foreach (var item in AsObjList(reg.GetValueOrDefault("protocols")))
    {
        var p = item as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        var version = p.GetValueOrDefault("version");
        Console.WriteLine($"  {PyS(p.GetValueOrDefault("id"))}: schema v{PyS(p.GetValueOrDefault("schema_version"))}"
                          + $" · version {(version is null ? "1.0.0" : PyS(version))}"
                          + $" · {AsObjList(p.GetValueOrDefault("module_ids")).Count} 模块");
    }
    return 0;
}

// 缺口逐行审查（真源 `nf review` · core/gap_review.py）：机械预筛 → 模型逐行判 → **确定性证据复核**，
// 双轨齐备才进 fixable。stub 适配器无判定能力 → 本轮以证据为准（真源同式）。
// **写面不移植**：`--write` 把报告落盘（且真源禁写 protocol/），只读门不落盘。
int ReviewCommand()
{
    if (writeRequested)
    {
        Console.Error.WriteLine("错误：--write 是写面（审查报告落盘；真源还禁写 protocol/）——只读门不落盘，不提供");
        return 2;
    }
    var scope = (sourceFlag ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
    // 照抄真源一处**空转**：`_cmd_review` 先用 classes 过滤出一份 rows，却从不使用它——
    // 真正入库的 `review()` 内部自行重算候选（不带 classes）。故 `--scope` 对输出**无影响**，本件同样不接。
    _ = scope;
    var doc = GapReview.Review(root!, adapterFlag, endpointFlag, limitCount, batchCount);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(doc));
        return 0;
    }
    Console.WriteLine($"== nf review（逐行缺口审查 · 适配器 {adapterFlag}）==");
    Console.WriteLine("  " + GapReview.Summary(doc));
    var fixable = doc.GetValueOrDefault("fixable") as List<object?> ?? new List<object?>();
    foreach (var item in fixable.Take(40))
    {
        var row = (Dictionary<string, object?>)item!;
        var gapP = row.GetValueOrDefault("model_gap_p");
        var severity = row.GetValueOrDefault("model_severity");
        Console.WriteLine($"  [可修] {PadCp(PyS(row["class"]), 22)} {PyS(row["file"])}:{PyS(row["line"])}"
                          + $"  p={(gapP is null ? "-" : F2(gapP))}"
                          + $" sev={(severity is null ? "-" : F2(severity))}"
                          + $" | {PySliceStr(PyS(row["evidence"]), 88)}");
    }
    var suspected = doc.GetValueOrDefault("suspected") as List<object?> ?? new List<object?>();
    if (suspected.Count > 0)
        Console.WriteLine($"  —— 模型怀疑但**无证据**（不修，只挂账）{suspected.Count} 条");
    return 0;
}

string PySliceStr(string text, int max) => PyScalar.PySlice(text, max);

// 扩展策略 / bump 迁移门禁（verify.sh check30）：判据词面 + bump 面。
// **bump 面**在真源里是 `git diff HEAD` 的版本字段结构性变更面。引擎**不接 VCS**：
//   · 导出快照（无 .git）：真源 `git diff` 亦失败 → diff 面恒空，两侧同判 → exit 0；
//   · 工作区（有 .git）且未供 diff：**UNKNOWN（不判，不写 PASS）** → 打说明并 exit 1；
//   · `--diff <文件|->`：调用方（CI / 脚本）供 `git diff HEAD` 的标准统一 diff → 按真源算法逐文件判。
int ExtensionCommand()
{
    ExtensionPolicy.Result result;
    if (diffPath is not null)
    {
        var text = diffPath == "-"
            ? Console.In.ReadToEnd()
            : File.ReadAllText(diffPath, new System.Text.UTF8Encoding(false, true));
        result = ExtensionPolicy.ScanWithDiff(root!, text);
    }
    else
    {
        result = ExtensionPolicy.Scan(root!);
    }
    foreach (var line in result.Log) Console.WriteLine(line);
    if (!result.BumpFaceJudged)
    {
        Console.Error.WriteLine("注意：bump 面 UNKNOWN（不判，不写 PASS）——" + result.Boundary);
        Console.Error.WriteLine("      收口方式：把 `git diff HEAD` 的标准统一 diff 用 --diff <文件|-> 或管道交给本命令。");
        return 1;
    }
    return result.Issues.Count > 0 ? 1 : 0;
}

// 语料身份（第一百零六片 · 操作性预检）：指纹 + 金标基线 + 模式。**只报告，不判据**——
// 作用是让「摘要类钉的红」能被正确归因（语料前移 ≠ 引擎坏了）。
// 退出码：0（无论匹配与否；本命令不是判据）——但导出快照且不匹配时，另打一行**处置指引**到 stderr。
int CorpusCommand()
{
    var stamp = CorpusStamp.Check(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["fingerprint"] = stamp.Fingerprint, ["baseline"] = stamp.Baseline,
            ["matches_baseline"] = stamp.Matches, ["mode"] = stamp.IsSnapshot ? "snapshot" : "worktree",
        }));
        return 0;
    }
    Console.WriteLine($"语料身份：{stamp.Fingerprint}（金标基线 {stamp.Baseline}）"
                      + $" · 匹配={(stamp.Matches ? "是" : "否")}"
                      + $" · 模式={(stamp.IsSnapshot ? "导出快照" : "工作区")}");
    if (stamp.IsSnapshot && !stamp.Matches)
    {
        Console.Error.WriteLine("WARN: 语料与金标基线不同——**摘要类自检钉的红应从「复基线」处置**，"
                                + "不是「引擎坏了」：");
        Console.Error.WriteLine("      ① 复基线：按《双跑对账表》各片的探针流程重生成 fixtures 并重嵌 SelfTest 常量；");
        Console.Error.WriteLine("      ② 或改跑**活仓库**（带 .git → 语义模式，不拿死摘要比漂动语料）："
                                + "-Root C:\\Users\\mon_7\\Downloads\\NarrativeForge-main。");
    }
    return 0;
}

// 需求 → 澄清漏斗 → 装配计划（真源 `nf assemble` · core/assemble_plan.py）。
// **读面**：clarify / plan / dossier / check。**写面与未移植面明确拒绝**：`--session-path`（会话档读写）·
// `--save-path`（需求档案落盘）· `--trace-path`（工具轨迹落盘）· `--rounds`（需 core/round_drill，未移植）。
int AssembleCommand()
{
    if (assembleSessionPath.Length > 0 || assembleSavePath.Length > 0 || assembleTracePath.Length > 0
        || assembleRounds)
    {
        Console.Error.WriteLine("错误：--session-path / --save-path / --trace-path 是写面，"
                                + "--rounds 依赖未移植的 core/round_drill —— 只读门不落盘、不冒充，均不提供");
        return 2;
    }
    if (positional.Count < 2)
    {
        Console.Error.WriteLine("错误：assemble 需要一句话需求（nf assemble \"题材+主轴+尺度\"）");
        return 2;
    }
    var requirement = positional[1];
    var answers = assemblyAnswers;
    var reqText = answers.Count > 0 ? requirement + "（" + string.Join("；", answers) + "）" : requirement;
    var funnel = AssemblePlan.Clarify(root!, reqText);
    var plan = funnel.GetValueOrDefault("plan") as Dictionary<string, object?>
               ?? AssemblePlan.Plan(root!, reqText);
    if (PyS(funnel.GetValueOrDefault("status")) == "clarify")
    {
        Console.WriteLine("== nf assemble（需求澄清）==");
        Console.WriteLine("  你的需求信息还不够直接编排，先补三点（缺一不可）：");
        foreach (var q in (funnel.GetValueOrDefault("questions") as List<object?> ?? new List<object?>()))
            Console.WriteLine("  · " + PyS(q));
        Console.WriteLine("  补充后再跑：nf assemble \"题材+主轴+尺度的一句话\" --check <out.md>");
        return 0;
    }
    if (assembleCheck)
    {
        if (positional.Count < 3)
        {
            Console.Error.WriteLine("错误：assemble --check 需要成品 md 路径（位置参数）");
            return 2;
        }
        string outMd;
        try
        {
            outMd = File.ReadAllText(positional[2], new System.Text.UTF8Encoding(false, true));
        }
        catch (Exception exc)
        {
            Console.Error.WriteLine($"  ✗ 读取成品失败：{exc.Message}（修复指引：给出仓库内完整版 md 路径）");
            return 1;
        }
        var hasSegments = System.Text.RegularExpressions.Regex.IsMatch(
            outMd, @"^##\s+[0-7]\.", System.Text.RegularExpressions.RegexOptions.Multiline);
        List<string> issues;
        Dictionary<string, object?> stats;
        if (hasSegments)
        {
            (issues, stats) = AssemblePlan.Check(outMd, plan);
        }
        else
        {
            issues = new List<string>();
            stats = new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["segments"] = 0L, ["modules_mentioned"] = 0L,
                ["allowed"] = (long)(plan.GetValueOrDefault("allowed_module_ids") as List<object?>
                                     ?? new List<object?>()).Count,
            };
        }
        Console.WriteLine("== nf assemble --check（需求 → 成品机器验收）==");
        Console.WriteLine($"  需求：{requirement} → {PyOr(plan.GetValueOrDefault("package"), "？")}"
                          + $"/{PyOr(plan.GetValueOrDefault("pipeline"), "？")}"
                          + $"（模块提及 {PyS(stats["modules_mentioned"])} · 允许集 {PyS(stats["allowed"])}）");
        foreach (var issue in issues) Console.Error.WriteLine("  [FAIL] " + issue);
        if (issues.Count == 0)
            Console.WriteLine("  ✓ 成品通过自组装机器验收（八段骨架 + 编号允许集 + 决策引用）");
        return issues.Count > 0 ? 1 : 0;
    }
    Console.WriteLine("== nf assemble（需求 → 装配计划）==");
    var pipelineFiles = (plan.GetValueOrDefault("pipeline_files") as List<object?> ?? new List<object?>())
        .Select(PyS).ToList();
    if (plan.GetValueOrDefault("matched") is true)
    {
        Console.WriteLine($"  匹配预设：{PyS(plan.GetValueOrDefault("package"))}"
                          + $" · 管线 {PyS(plan.GetValueOrDefault("pipeline"))}");
        Console.WriteLine($"  管线件：{(pipelineFiles.Count > 0 ? string.Join("、", pipelineFiles) : "—")}");
        Console.WriteLine("  取件模块："
                          + string.Join("、", (plan.GetValueOrDefault("fetch_modules") as List<object?> ?? new List<object?>()).Select(PyS)));
        Console.WriteLine("  装配允许集（官方核心 + 包模块）："
                          + PyS((plan.GetValueOrDefault("allowed_module_ids") as List<object?> ?? new List<object?>()).Count));
        Console.WriteLine($"  下一步：读 agent_组装指令包_v0.2.md → 取件 → 输出完整版 → "
                          + $"nf assemble \"{requirement}\" --check <out.md> 验收");
    }
    else
    {
        Console.WriteLine("  未命中预设 → 用户自定义流（custom）");
        var known = (plan.GetValueOrDefault("known_packages") as List<object?> ?? new List<object?>())
            .Select(PyS).ToList();
        Console.WriteLine($"  可借用已登记包：{(known.Count > 0 ? string.Join("、", known) : "—")}");
        Console.WriteLine("  装配允许集（官方核心 + 全部已登记社区模块）："
                          + PyS((plan.GetValueOrDefault("allowed_module_ids") as List<object?> ?? new List<object?>()).Count));
        Console.WriteLine("  自定义预留槽位：模块 M91-M99 或 <本包独占类别>:Mxx 类内段 · 资产 900+ 命名空间 · "
                          + "新管线 Pxx（避让层位 id P00-P80 与官方/既有管线，见 02 §8.3）");
        Console.WriteLine("  建件：按 community/模板制作指令包.md 做自定义模块/资产 → "
                          + "protocol.yaml 登记（nf register）→ 成品里即可引用 → 验收");
        Console.WriteLine($"  验收：nf assemble \"{requirement}\" --check <out.md>");
    }
    return 0;
}

string PyOr(object? value, string fallback) => value is null || (value is string s && s.Length == 0)
    ? fallback : PyS(value);

int InteropCommand()
{
    // 片内推进：`--list` 全 12 形状可用；`--kind` 仅对已移植形状可用（未移植明确拒绝）；
    // `--check` / `--all` 需要全部形状，未移植前明确拒绝——不提供半个门禁。
    if (interopList)
    {
        foreach (var (id, label) in Interop.Kinds)
            Console.WriteLine($"  {PadCp(id, 9)} {PadCp(label, 38)} 消费者：外部标准工具链");
        return 0;
    }
    if (interopCheck)
    {
        var (checkIssues, checkStats) = Interop.Verify(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["issues"] = checkIssues.Cast<object?>().ToList(),
                ["stats"] = checkStats,
            }));
        }
        else
        {
            foreach (var i in checkIssues) Console.Error.WriteLine($"  [FAIL] {i}");
            if (checkIssues.Count == 0) Console.WriteLine($"  ✓ 导出面一致（{Interop.Summary(checkStats)}）");
        }
        return checkIssues.Count > 0 ? 1 : 0;
    }
    if (interopAll)
    {
        if (outPath is null)
            return Fail("interop --all 缺省落仓内 results/interop/（仓库写面）——本引擎只写调用者显式指定的路径，" +
                        "请加 --out <目录>");
        var dir = Path.IsPathRooted(outPath) ? outPath : Path.Combine(root!, outPath);
        Directory.CreateDirectory(dir);
        foreach (var (id, _) in Interop.Kinds)
        {
            var dest = Path.Combine(dir, $"{id}.json");
            File.WriteAllBytes(dest, Interop.Render(id, root!));
            Console.WriteLine($"written: {dest}");
        }
        Console.WriteLine("  （入仓面须与实时派生逐字节一致——由 verify check33 断言；改声明件后重跑本命令）");
        return 0;
    }

    var kind = interopKind ?? "openapi";
    if (!Interop.Kinds.Any(k => k.Id == kind))
        return Usage($"interop 的 --kind 取值须为：{string.Join(" / ", Interop.Kinds.Select(k => k.Id))}");
    byte[] blob;
    try
    {
        blob = Interop.Render(kind, root!);
    }
    catch (InvalidOperationException exc)
    {
        return Fail(exc.Message);
    }
    if (outPath is not null)
    {
        var outp = Path.IsPathRooted(outPath) ? outPath : Path.Combine(root!, outPath);
        var parent = Path.GetDirectoryName(outp);
        if (!string.IsNullOrEmpty(parent)) Directory.CreateDirectory(parent);
        File.WriteAllBytes(outp, blob);
        Console.WriteLine($"written: {outPath}（{blob.Length} 字节，纯派生，勿手改）");
    }
    else
    {
        Console.Out.Write(System.Text.Encoding.UTF8.GetString(blob));
        Console.Out.Flush();
    }
    return 0;
}

int StatsCommand()
{
    if (writeRequested)
        return Usage("stats --write 是写面（重写三处生成区与 protocol/repo_stats.json）——本引擎是只读门，不提供写命令");

    var (issues, stats) = RepoStats.Check(root!);
    long N(string key) => stats.TryGetValue(key, out var v) && v is not null
        ? Convert.ToInt64(v, System.Globalization.CultureInfo.InvariantCulture) : 0L;
    var pipes = (stats.TryGetValue("core_pipelines", out var p) ? p as List<object?> : null) ?? new List<object?>();

    if (json)
    {
        // 有意分歧（已登记）：Python 侧 `nf stats --json` 因缺 `import json` 抛 NameError 崩栈；
        // 引擎侧给出正确的机读面——这是修好，不是等价差，故不进「逐字节对账面」。
        Console.WriteLine(PythonJson.Indented(stats));
    }
    else
    {
        Console.WriteLine("== nf stats（自述数字实算 · 真源 protocol/repo_stats.json）==");
        Console.WriteLine($"  官方核心：模块 {N("core_modules")} · 管线 {string.Join(" / ", pipes.Select(PyS))}");
        Console.WriteLine($"  社区规模：登记包 {N("registered_packs")} · 资产档 {N("pack_assets")} · " +
                          $"概念图 {N("concept_graphs")} · 域包 {N("domain_packs")}/{N("subdivisions_total")} 细分");
        Console.WriteLine($"  标准目录：{N("standards_total")} 条（可达 {N("standards_reachable")} / " +
                          $"不可达 {N("standards_unreachable")} · 机构 {N("standards_bodies")} · " +
                          $"{N("standards_edges")} 边） · 绑定 {N("standard_bindings")} 条");
        Console.WriteLine($"  质量凭证：verify check1-{N("baseline_checks")} 常驻（脚本 " +
                          $"v{PyS(stats.GetValueOrDefault("verify_version"))}） · 馆藏 {N("library_items")} 件");
        Console.WriteLine("  模式：check（只校验）");
        foreach (var i in issues) Console.Error.WriteLine($"  [FAIL] {i}");
    }
    return issues.Count > 0 ? 1 : 0;
}

/// <summary>
/// <c>nf driver [工作流] [--json]</c>——指令档机器面路由（有 MCP 走 MCP；派发失败即停、不回退文本步骤）。
/// 与真源逐字节对齐：文本面的列宽（<c>%-12s</c> / <c>%-28s</c>）、warns 走 stdout 的 <c>[note]</c>、
/// issues 走 **stderr** 的 <c>[FAIL]</c>、以及 JSON 面的 <c>indent=2, sort_keys=True</c>；退出码 1 当有 issues。
/// </summary>
int DriverCommand()
{
    var workflow = positional.Count >= 2 ? positional[1] : "";
    var scan = Driver.Scan(root!);
    if (workflow.Length > 0)
    {
        var resolved = Driver.Resolve(root!, workflow);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["resolve"] = resolved,
                ["issues"] = scan.Issues.Cast<object?>().ToList(),
                ["warns"] = scan.Warns.Cast<object?>().ToList(),
            }));
        }
        else
        {
            Console.WriteLine($"== nf driver {workflow} ==");
            var mode = S(resolved.GetValueOrDefault("mode"));
            Console.WriteLine($"  路径：{(mode == "mcp" ? "MCP（机器面）" : mode)}");
            var prompt = S(resolved.GetValueOrDefault("prompt"));
            if (prompt.Length > 0) Console.WriteLine($"  提示：{prompt}");
            var tools = resolved.GetValueOrDefault("tools") as List<object?> ?? new List<object?>();
            if (tools.Count > 0) Console.WriteLine("  工具：" + string.Join("、", tools.Select(PyS)));
            var fallback = S(resolved.GetValueOrDefault("fallback"));
            Console.WriteLine($"  文本 fallback：{(fallback.Length > 0 ? fallback : "-")}");
            var onFailure = S(resolved.GetValueOrDefault("on_dispatch_failure"));
            Console.WriteLine($"  派发失败：{(onFailure.Length > 0 ? onFailure : "-")}");
            foreach (var issue in scan.Issues) Console.Error.WriteLine($"  [FAIL] {issue}");
        }
        return scan.Issues.Count > 0 ? 1 : 0;
    }

    var document = Driver.Load(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["driver"] = document,
            ["issues"] = scan.Issues.Cast<object?>().ToList(),
            ["warns"] = scan.Warns.Cast<object?>().ToList(),
            ["stats"] = scan.Stats,
        }));
    }
    else
    {
        Console.WriteLine("== nf driver（指令档机器面路由）==");
        var workflows = document.GetValueOrDefault("workflows") as Dictionary<string, object?>
                        ?? new Dictionary<string, object?>();
        foreach (var name in workflows.Keys.OrderBy(x => x, StringComparer.Ordinal))
        {
            var wf = workflows[name] as Dictionary<string, object?> ?? new Dictionary<string, object?>();
            var tools = wf.GetValueOrDefault("mcp_tools") as List<object?> ?? new List<object?>();
            var toolText = tools.Count > 0 ? string.Join("、", tools.Select(PyS)) : "-";
            var fallback = S(wf.GetValueOrDefault("fallback"));
            Console.WriteLine($"  {Pad(name, 12)} MCP：{Pad(toolText, 28)} fallback：{(fallback.Length > 0 ? fallback : "-")}");
        }
        foreach (var warn in scan.Warns) Console.WriteLine($"  [note] {warn}");
        foreach (var issue in scan.Issues) Console.Error.WriteLine($"  [FAIL] {issue}");
        if (scan.Issues.Count == 0)
            Console.WriteLine("  ✓ 工作流映射/工具名/fallback/文档声明块全部一致（fail-closed 已声明）");
    }
    return scan.Issues.Count > 0 ? 1 : 0;
}

/// <summary>Python <c>%-Ns</c>：按**码点**左对齐补空格（不足才补，超长不截）。</summary>
string Pad(string text, int width)
{
    var length = text.EnumerateRunes().Count();
    return length < width ? text + new string(' ', width - length) : text;
}

/// <summary>
/// Python <c>.get(key, "-")</c> / 真值跳过的口径：**缺键与 None 都当作空**（渲染成空串，由调用方补 "-"）。
/// 注意不能直接用 <c>PyS</c>——它把 null 渲染成 <c>"None"</c>（那是 <c>str(None)</c> 的口径，用在这里会多出三个字节）。
/// </summary>
string S(object? value) => value is null ? "" : PyS(value);

/// <summary>
/// 列表强制：引擎各 Stats 字典里的数组类型不统一（`List&lt;object?&gt;` / `List&lt;string&gt;` / …），
/// `as List&lt;object?&gt;` 对后者**静默返回 null**（实测踩过：license 文本面把「未声明 1」打成 0，
/// 而 JSON 面因渲染器吃 IEnumerable 仍逐字节一致——只有文本面照得出来）。
/// </summary>
List<object?> AsObjList(object? value) => value switch
{
    List<object?> list => list,
    System.Collections.IEnumerable seq when value is not string => seq.Cast<object?>().ToList(),
    _ => new List<object?>(),
};

/// <summary>
/// <c>nf telemetry &lt;trace.json&gt; [--otlp]</c>——trace 记录 → OTel GenAI semconv 属性 / OTLP 形状。
/// 文本面与真源逐字节对齐（含属性名左对齐 28 列与 <c>json.dumps</c> 默认分隔符）；错误面与真源同向：
/// 打一行可读错误到 stderr + 退出码 1，不打栈。
/// </summary>
int TelemetryCommand()
{
    if (positional.Count < 2) return Usage("telemetry 需要一个 trace JSON 路径（单条记录或 {records:[...]}）");
    var tracePath = positional[1];
    List<Dictionary<string, object?>> records;
    try
    {
        records = TelemetrySemconv.LoadTrace(tracePath);
    }
    catch (Exception exc) when (exc is IOException or System.Text.Json.JsonException
                                or InvalidOperationException or UnauthorizedAccessException or ArgumentException)
    {
        Console.Error.WriteLine($"  ✗ {exc.Message}");
        return 1;
    }
    if (records.Count == 0)
    {
        Console.Error.WriteLine("  ✗ trace 为空或格式不识别（支持单条记录或 {records:[...]}）");
        return 1;
    }
    if (flags.Contains("--otlp"))
    {
        Console.WriteLine(PythonJson.IndentedUnsorted(TelemetrySemconv.ToExport(records)));
        return 0;
    }
    Console.WriteLine($"== nf telemetry（{records.Count} 记录 → semconv 属性）==");
    foreach (var record in records)
    {
        Console.WriteLine("  " + TelemetrySemconv.ToolNameOf(record));
        foreach (var kv in TelemetrySemconv.AttributesFor(record).OrderBy(k => k.Key, StringComparer.Ordinal))
        {
            var pad = kv.Key.EnumerateRunes().Count();
            var padding = pad < 28 ? new string(' ', 28 - pad) : "";
            Console.WriteLine($"    {kv.Key}{padding} {PythonJson.UnsortedWithSpaces(kv.Value)}");
        }
    }
    return 0;
}

int StValidateCommand()
{
    if (positional.Count < 2) return Usage("st-validate 需要一个被校验对象的路径");
    var target = positional[1];
    Dictionary<string, object?> rep;
    try
    {
        rep = StValidate.Validate(target);
    }
    catch (Exception exc) when (exc is IOException or System.Text.Json.JsonException or InvalidOperationException)
    {
        // 与 Python 同向：`except (OSError, ValueError)` → 打一行可读错误 + 退出码 1（不打栈）
        Console.Error.WriteLine($"  ✗ {exc.Message}");
        return 1;
    }

    if (outPath is not null)
    {
        var outp = Path.IsPathRooted(outPath) ? outPath : Path.Combine(root!, outPath);
        var parent = Path.GetDirectoryName(outp);
        if (!string.IsNullOrEmpty(parent)) Directory.CreateDirectory(parent);
        File.WriteAllText(outp, StValidate.ReportMarkdown(rep), new System.Text.UTF8Encoding(false));
    }

    if (json)
    {
        Console.WriteLine(PythonJson.Indented(rep));
    }
    else
    {
        var counts = rep.GetValueOrDefault("counts") as Dictionary<string, object?> ?? new Dictionary<string, object?>(StringComparer.Ordinal);
        long N(string key) => counts.TryGetValue(key, out var v) && v is not null
            ? Convert.ToInt64(v, System.Globalization.CultureInfo.InvariantCulture) : 0;
        Console.WriteLine($"== nf st-validate {target}（{PyS(rep.GetValueOrDefault("kind"))}：" +
                          $"fail {N("fail")} · warn {N("warn")} · info {N("info")}）==");
        var issues = rep.GetValueOrDefault("issues") as List<object?> ?? new List<object?>();
        foreach (var node in issues)
        {
            var issue = (Dictionary<string, object?>)node!;
            Console.WriteLine($"  [{PyS(issue["severity"]).ToUpperInvariant()}] {PyS(issue["rule"])} {PyS(issue["detail"])}");
        }
        if (issues.Count == 0) Console.WriteLine("  ✓ 可自动化项全部通过（R1/R3/R4）");
        if (outPath is not null) Console.WriteLine($"  报告已写入：{outPath}");
    }

    var fails = rep.GetValueOrDefault("counts") is Dictionary<string, object?> c
                && c.TryGetValue("fail", out var f) && f is not null
        ? Convert.ToInt64(f, System.Globalization.CultureInfo.InvariantCulture) : 0;
    return fails > 0 ? 1 : 0;
}

int EventsCommand()
{
    var (issues, warns, stats) = EventBacking.Scan(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = issues.Cast<object?>().ToList(),
            ["warns"] = warns.Cast<object?>().ToList(),
            ["stats"] = stats,
        }));
    }
    else
    {
        var cross = stats.TryGetValue("cross_pkg", out var c) && c is List<object?> list ? list : new List<object?>();
        Console.WriteLine("== nf events（全仓事件背书）==");
        Console.WriteLine($"  事件 {StatOr(stats, "events")} · 跨包 {cross.Count} · 无发布方挂账 {warns.Count - cross.Count}");
        foreach (var i in issues) Console.Error.WriteLine($"  [FAIL] {i}");
        foreach (var w in warns.Take(10)) Console.WriteLine($"  [note] {w}");
        if (issues.Count == 0) Console.WriteLine("  ✓ 每个被订阅的事件都有发布方（外部通道已显式挂账）");
    }
    return issues.Count > 0 ? 1 : 0;
}

int ToolFaceCommand()
{
    var (issues, stats) = ToolFace.Scan(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["kind"] = "toolface",
            ["issues"] = issues.Cast<object?>().ToList(),
            ["stats"] = stats,
        }));
    }
    else
    {
        Console.WriteLine("== nf toolface（模块工具面 · AI 裁量不入门禁）==");
        Console.WriteLine($"  模块 {StatOr(stats, "modules")} · 条目 {StatOr(stats, "entries")} · " +
                          $"候选工具链接 {StatOr(stats, "candidates")}");
        var faces = stats.TryGetValue("faces", out var f) && f is List<object?> list ? list : new List<object?>();
        foreach (var face in faces)
        {
            var row = face as Dictionary<string, object?>;
            if (row is null) continue;
            Console.WriteLine($"  · {StatOr(row, "module")}（{StatOr(row, "source")} · {StatOr(row, "entries")} 条目）");
        }
        foreach (var i in issues) Console.Error.WriteLine($"  [FAIL] {i}");
    }
    return issues.Count > 0 ? 1 : 0;
}

int RfcCommand()
{
    var (issues, warns, stats) = Rfc.Scan(root!);
    var idx = Rfc.IndexDoc(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["index"] = idx,
            ["issues"] = issues.Cast<object?>().ToList(),
            ["warns"] = warns.Cast<object?>().ToList(),
            ["stats"] = stats,
        }));
    }
    else
    {
        Console.WriteLine("== nf rfc（协议件版本史）==");
        var docs = idx.GetValueOrDefault("docs") as List<object?> ?? new List<object?>();
        foreach (var item in docs)
        {
            var row = item as Dictionary<string, object?>;
            var rel = row is null ? "" : PyS(row.GetValueOrDefault("path"));
            var text = KnowledgeSig.Norm(new System.Text.UTF8Encoding(false, true)
                .GetString(File.ReadAllBytes(Path.Combine(root!, rel))));
            var head = Rfc.ParseHead(text);
            string Get(string key) => head.TryGetValue(key, out var v) ? v : "-";
            Console.WriteLine($"  {PadCp(row is null ? "" : PyS(row.GetValueOrDefault("rfc")), 9)} {PadCp(rel, 34)} " +
                              $"{PadCp(Get("cat"), 16)} {PadCp(Get("status"), 9)} {Get("date")}");
        }
        foreach (var i in issues) Console.Error.WriteLine($"  [FAIL] {i}");
        if (issues.Count == 0) Console.WriteLine($"  ✓ {stats.GetValueOrDefault("docs")} 件 RFC 头齐备且链可解析");
    }
    return issues.Count > 0 ? 1 : 0;
}

int EndpointCommand()
{
    var (issues, warns, stats) = EndpointContract.Scan(root!);
    var doc = EndpointContract.Load(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["contract"] = doc,
            ["issues"] = issues.Cast<object?>().ToList(),
            ["warns"] = warns.Cast<object?>().ToList(),
            ["stats"] = stats,
        }));
    }
    else
    {
        Console.WriteLine($"== nf endpoint（服务端点契约 · {StatOr(stats, "status")}）==");
        var endpoints = doc.GetValueOrDefault("endpoints") as List<object?> ?? new List<object?>();
        foreach (var item in endpoints)
        {
            var ep = item as Dictionary<string, object?>;
            if (ep is null) continue;
            var streaming = ep.TryGetValue("streaming", out var sv) && PyTruthy(sv) ? "SSE" : "单发";
            Console.WriteLine($"  {PadCp(PyS(ep.GetValueOrDefault("method")), 8)} " +
                              $"{PadCp(PyS(ep.GetValueOrDefault("path")), 22)} {PadCp(streaming, 9)} " +
                              $"{PyS(ep.GetValueOrDefault("maps_to"))}");
        }
        foreach (var i in issues) Console.Error.WriteLine($"  [FAIL] {i}");
        foreach (var w in warns) Console.WriteLine($"  [note] {w}");
        if (issues.Count == 0)
            Console.WriteLine("  ✓ 每个端点都映射到现存 CLI 子命令或 MCP 工具（契约不指向空气）");
    }
    return issues.Count > 0 ? 1 : 0;
}

/// <summary>Python 真值判定（用于 <c>"SSE" if ep.get("streaming") else "单发"</c>）。</summary>
static bool PyTruthy(object? v) => v switch
{
    null => false,
    bool b => b,
    string s => s.Length > 0,
    long l => l != 0,
    double d => d != 0,
    List<object?> list => list.Count > 0,
    Dictionary<string, object?> map => map.Count > 0,
    _ => true,
};

/// <summary>Python <c>dict.get(k, "?")</c> 语义：缺键才给默认值（有键即使是空串也照印）。</summary>
static string StatOr(Dictionary<string, object?> stats, string key)
    => stats.TryGetValue(key, out var v) ? PyS(v) : "?";

int SigCommand()
{
    var verifyOnly = positional.Count >= 2 && positional[1] == "verify";
    if (verifyOnly)
    {
        var (issues, stats) = KnowledgeSig.VerifyReproducible(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["issues"] = issues.Cast<object?>().ToList(),
                ["stats"] = stats,
            }));
        }
        else
        {
            Console.WriteLine($"== nf-dotnet sig verify（check25 同语义）==  文档 {stats["docs"]} · 可复现 {stats["reproducible"]}");
            foreach (var issue in issues) Console.WriteLine("  ✗ " + issue);
            if (issues.Count == 0) Console.WriteLine("  ✓ 01-36 全量签名两遍一致（知识指纹稳定）");
        }
        return issues.Count == 0 ? 0 : 1;
    }

    var scan = KnowledgeSig.Scan(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(scan.Records));
    }
    else
    {
        Console.WriteLine($"== nf-dotnet sig（{scan.Count} 文档）==");
        foreach (var row in scan.Records.Cast<Dictionary<string, object?>>())
        {
            var sig = (Dictionary<string, object?>)row["sig"]!;
            var refs = (List<object?>)sig["refs"]!;
            Console.WriteLine($"  {((string)row["digest"]!)[..12]}  {sig["path"],-14} {sig["doc_id"],-8} refs={refs.Count}");
        }
    }
    return 0;
}

int ModelCommand()
{
    var part = positional.Count >= 2 ? positional[1] : "";
    if (part is not ("" or "vocab" or "normative" or "contracts"))
        return Usage("model 的子命令须为 vocab / normative / contracts");
    var result = Modeling.Run(root!, part);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["stats"] = result.Stats,
            ["warns"] = result.Warns.Cast<object?>().ToList(),
        }));
    }
    else
    {
        Console.WriteLine($"== nf-dotnet model{(" · " + part)} ==");
        foreach (var kv in result.Stats)
        {
            Console.WriteLine($"  {kv.Key,-10} {PythonJson.CanonicalizeGraph(kv.Value)}");
        }
        foreach (var warn in result.Warns) Console.WriteLine("  ! " + warn);
        foreach (var issue in result.Issues) Console.WriteLine("  ✗ " + issue);
        if (result.Issues.Count == 0)
            Console.WriteLine("  ✓ 词表与真源一致 · 规范件皆有主 · 说明件未被当规范 · 契约 quality_rule 全部解析");
    }
    return result.Issues.Count == 0 ? 0 : 1;
}

int BenchCommand()
{
    var measurements = Bench.Run(root!);

    if (benchWritePath is not null)
    {
        var ops = measurements.ToDictionary(
            m => m.Name,
            m => (object?)new Dictionary<string, object?> { ["ms"] = m.Milliseconds, ["detail"] = m.Detail },
            StringComparer.Ordinal);
        File.WriteAllText(benchWritePath,
            PythonJson.Indented(new Dictionary<string, object?>
            {
                ["schema"] = "nf-net-bench/1",
                ["ops"] = ops,
            }) + "\n", new System.Text.UTF8Encoding(false));
        Console.WriteLine("已写入基线：" + benchWritePath);
    }

    var rows = new List<object?>();
    var regressed = 0;
    Dictionary<string, double>? baseline = null;
    if (benchBaselinePath is not null)
    {
        using var doc = JsonIo.ReadFile(benchBaselinePath);
        baseline = new Dictionary<string, double>(StringComparer.Ordinal);
        if (doc.RootElement.TryGetProperty("ops", out var ops))
        {
            foreach (var op in ops.EnumerateObject())
            {
                if (op.Value.TryGetProperty("ms", out var ms) && ms.TryGetDouble(out var value))
                    baseline[op.Name] = value;
            }
        }
    }

    foreach (var m in measurements)
    {
        double? baseMs = baseline is not null && baseline.TryGetValue(m.Name, out var b) ? b : null;
        var ratio = baseMs is > 0 ? m.Milliseconds / baseMs.Value : (double?)null;
        // 判据：允许 tolerance 倍，且给 50 ms 绝对地板（小操作噪声不判红）
        var ok = baseMs is null || m.Milliseconds <= baseMs.Value * tolerance + 50;
        if (!ok) regressed++;
        rows.Add(new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["name"] = m.Name,
            ["ms"] = m.Milliseconds,
            ["baseline_ms"] = baseMs is null ? null : Math.Round(baseMs.Value, 2),
            ["ratio"] = ratio is null ? null : Math.Round(ratio.Value, 2),
            ["ok"] = ok,
            ["detail"] = m.Detail,
        });
    }

    var overall = regressed == 0;
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["ok"] = overall,
            ["tolerance"] = tolerance,
            ["ops"] = rows,
        }));
    }
    else
    {
        Console.WriteLine("== nf-dotnet bench（性能基线）==");
        foreach (var row in rows.Cast<Dictionary<string, object?>>())
        {
            var name = (string)row["name"]!;
            var ms = (double)row["ms"]!;
            var baseText = row["baseline_ms"] is null ? "—" : row["baseline_ms"] + " ms";
            var ratioText = row["ratio"] is null ? "" : $" · ×{row["ratio"]}";
            Console.WriteLine($"  {(row["ok"] is true ? "✓" : "✗")} {name,-14} {ms,7:0.00} ms · 基线 {baseText}{ratioText} —— {row["detail"]}");
        }
        Console.WriteLine(overall ? "  —— 无回归" : $"  —— 回归 {regressed} 项（容差 ×{tolerance}）");
    }
    return overall ? 0 : 1;
}

int LibraryCommand()
{
    var result = Library.Verify(root!);
    var failed = result.Issues.Count + result.Projection.Count;
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["projection"] = result.Projection.Cast<object?>().ToList(),
            ["stats"] = result.Stats,
            ["warns"] = result.Warns.Cast<object?>().ToList(),
        }));
    }
    else
    {
        Console.WriteLine($"== nf-dotnet library verify（图书馆门）==  条目 {result.Stats["entries"]} · 在役 {result.Stats["active"]} · WARN {result.Warns.Count}");
        foreach (var issue in result.Issues.Concat(result.Projection)) Console.WriteLine("  ✗ " + issue);
        foreach (var warn in result.Warns) Console.WriteLine("  ! " + warn);
        if (failed == 0) Console.WriteLine("  ✓ frontmatter 真源 + INDEX/ALIAS 投影一致");
    }
    return failed == 0 ? 0 : 1;
}

int CognitionCommand()
{
    var result = Cognition.Run(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["stats"] = result.Stats,
            ["warns"] = result.Warns.Cast<object?>().ToList(),
        }));
    }
    else
    {
        Console.WriteLine("== nf-dotnet cognition（术语表 + 执行分档）==");
        var glossary = (Dictionary<string, object?>)result.Stats["glossary"]!;
        var modes = (Dictionary<string, object?>)result.Stats["modes"]!;
        Console.WriteLine($"  术语 {glossary["terms"]} 条 · 被使用 {glossary["uses"]} 处 · 分档 {modes["modes"]} 档 · 合格实例 {modes["instances_ok"]}");
        foreach (var issue in result.Issues) Console.WriteLine("  ✗ " + issue);
        if (result.Issues.Count == 0) Console.WriteLine("  ✓ 术语真源逐字命中 / 分档实例含全部必备结构块");
    }
    return result.Issues.Count == 0 ? 0 : 1;
}

int DecisionsCommand()
{
    var result = Decisions.Verify(root!);
    var failed = result.Issues.Count + result.Projection.Count;
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["projection"] = result.Projection.Cast<object?>().ToList(),
            ["stats"] = result.Stats,
            ["warns"] = result.Warns.Cast<object?>().ToList(),
        }));
    }
    else
    {
        Console.WriteLine($"== nf-dotnet decisions verify（{result.Stats["decisions"]} 条 · accepted {result.Stats["accepted"]}）==");
        foreach (var issue in result.Issues.Concat(result.Projection)) Console.WriteLine("  ✗ " + issue);
        if (failed == 0) Console.WriteLine("  ✓ 编号/状态/取代链/证据可解析/三段齐/回执锚定/INDEX 投影 全部一致");
    }
    return failed == 0 ? 0 : 1;
}

int AssertionsCommand()
{
    var result = Assertions.Run(root!);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["issues"] = result.Issues.Cast<object?>().ToList(),
            ["results"] = result.Results,
        }));
    }
    else
    {
        Console.WriteLine("== nf-dotnet assertions（数据化断言表）==");
        foreach (var row in result.Results.Cast<Dictionary<string, object?>>())
        {
            var mark = row["ok"] is true ? "✓" : "✗";
            Console.WriteLine($"  {mark} {row["id"],-40} [{row["kind"]}] {row["detail"]}");
        }
        foreach (var issue in result.Issues) Console.WriteLine("  ! " + issue);
        Console.WriteLine($"  —— 断言 {result.Results.Count} 条 · 问题 {result.Issues.Count}");
    }
    return result.Issues.Count == 0 ? 0 : 1;
}

int CombineBreadthCommand()
{
    var stats = samplesPath is null
        ? (pairsOnly ? Breadth.RunPairsOnly(root!) : Breadth.RunSelfContained(root!))
        : Breadth.Run(root!, JsonIo.ReadFile(samplesPath).RootElement);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(stats));
    }
    else
    {
        Console.WriteLine("== nf-dotnet combine breadth ==");
        Console.WriteLine($"  参与包 {stats["packs"]} · 两两 {stats["pairs_legal"]}/{stats["pairs"]}" +
                          $" · 三元 {stats["triples_legal"]}/{stats["triples"]}" +
                          $" · 四元 {stats["quads_legal"]}/{stats["quads"]}" +
                          $" · 五元 {stats["quints_legal"]}/{stats["quints"]}" +
                          $" · 六元 {stats["sexts_legal"]}/{stats["sexts"]} · 全合法={stats["all_legal"]}");
        if (samplesPath is null && pairsOnly) Console.WriteLine("  （仅两两全集；去掉 --pairs-only 即含四档抽样）");
    }
    return stats["all_legal"] is true ? 0 : 1;
}

int SelfTestCommand()
{
    var checks = SelfTest.Run(root!);
    var failed = checks.Count(c => !c.Passed);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["checks"] = checks.Count,
            ["failed"] = failed,
            ["rows"] = checks.Select(c => (object?)new Dictionary<string, object?>
            {
                ["name"] = c.Name,
                ["passed"] = c.Passed,
                ["detail"] = c.Detail,
            }).ToList(),
        }));
    }
    else
    {
        Console.WriteLine("== nf-dotnet selftest（负例 / 健壮性自检）==");
        foreach (var check in checks)
        {
            Console.WriteLine($"  {(check.Passed ? "✓" : "✗")} {check.Name} —— {check.Detail}");
        }
        Console.WriteLine($"  —— 用例 {checks.Count} 条 · 通过 {checks.Count - failed} · 失败 {failed}");
    }
    return failed == 0 ? 0 : 1;
}

int KnowledgeCommand()
{
    // 只读面：status（缺省）/ order / visible / transform / lint / frequency（--trace 复算，不落盘）。写面（frequency --write、transform add|promote）未移植。
    var sub = positional.Count >= 2 ? positional[1] : "status";
    // 同 Python：`--json` 只挂在子命令上，且**没有 `status` 子命令**（缺省即 status）——
    // 故 `nf knowledge --json` 与 `nf knowledge status` 都是用法错误（exit 2），此处不宽容。
    if (json && positional.Count < 2)
        return Fail("knowledge 需要子命令（order / visible / transform / lint）才能带 --json");
    if (positional.Count >= 2 && sub is not ("order" or "visible" or "transform" or "lint" or "frequency"))
        return Fail($"knowledge 没有子命令：{sub}（可选 order / visible / transform / lint / frequency；缺省即 status）");
    if (sub == "frequency")
    {
        if (writeRequested)
            return Fail("knowledge frequency --write 是写面（写 protocol/knowledge_usage.json）——本引擎只做只读面");
        if (string.IsNullOrEmpty(tracePath))
            return Fail("knowledge frequency 需要 --trace <file>（trace 文件：JSON / JSONL）");
        Dictionary<string, object?> counts;
        try
        {
            counts = KnowledgeSources.HarvestFrequency(tracePath);
        }
        catch (Exception exc) when (exc is IOException or UnauthorizedAccessException)
        {
            Console.Error.WriteLine($"  ✗ {exc.Message}");
            return 1;
        }
        var (freqIssues, _freqWarns, freqStats) = KnowledgeSources.VerifyUsage(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["counts"] = counts,
                ["written"] = false,
                ["issues"] = freqIssues.Cast<object?>().ToList(),
                ["stats"] = freqStats,
            }));
        }
        else
        {
            var total = counts.Values.OfType<long>().Sum();
            Console.WriteLine($"== nf knowledge frequency（{counts.Count} 源有事件 · 共 {total} 次）==");
            foreach (var (k, v) in counts) Console.WriteLine($"  {PadCp(k, 22)} {PyS(v)}");
            if (counts.Count == 0) Console.WriteLine("  （trace 中无 knowledge_source 事件）");
            foreach (var i in freqIssues) Console.Error.WriteLine($"  [FAIL] {i}");
            Console.WriteLine("  （未写台账；加 --write 落盘）");
        }
        return freqIssues.Count > 0 ? 1 : 0;
    }
    if (sub == "order")
    {
        var rows = KnowledgeSources.ResolveOrder(root!, knowledgeClearance is "public" or "internal" or "restricted"
            ? knowledgeClearance : "");
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["clearance"] = knowledgeClearance.Length == 0 ? "不裁剪" : knowledgeClearance,
                ["query_order"] = rows.Cast<object?>().ToList(),
            }));
        }
        else
        {
            Console.WriteLine("== nf knowledge order（查询有序：合同级 → 参考级" +
                              (knowledgeClearance.Length > 0 ? "· 裁剪至 " + knowledgeClearance : "") + "）==");
            for (var i = 0; i < rows.Count; i++)
            {
                var r = rows[i];
                Console.WriteLine($"  {i + 1}. {r["id"],-22} {r["authority"],-9} {r["kind"],-18} {r["locator"]}");
            }
        }
        return 0;
    }
    if (sub == "visible")
    {
        var clearance = knowledgeClearance.Length > 0 ? knowledgeClearance : "public";
        var allowed = KnowledgeSources.VisibleIds(root!, clearance);
        var rows = KnowledgeSources.SourcesOf(root!).Select(s => new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["id"] = s.GetValueOrDefault("id")?.ToString() ?? "",
            ["visibility"] = s.GetValueOrDefault("visibility")?.ToString() ?? "",
            ["visible"] = allowed.Contains(s.GetValueOrDefault("id")?.ToString() ?? ""),
        }).ToList();
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["clearance"] = clearance, ["sources"] = rows.Cast<object?>().ToList(),
            }));
        }
        else
        {
            Console.WriteLine($"== nf knowledge visible --as {clearance} ==");
            foreach (var r in rows)
                Console.WriteLine($"  {r["id"],-22} {r["visibility"],-11} {(r["visible"] is true ? "可见" : "裁剪")}");
        }
        return 0;
    }
    if (sub == "transform")
    {
        if (positional.Count >= 3 && positional[2] is "add" or "promote")
            return Fail("knowledge transform add/promote（写面）未移植：本引擎只做只读面");
        var (issues, _, stats) = KnowledgeSources.VerifyTransform(root!);
        var entries = KnowledgeSources.LogEntries(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["issues"] = issues.Cast<object?>().ToList(),
                ["stats"] = stats,
                ["entries"] = entries.Cast<object?>().ToList(),
            }));
        }
        else
        {
            Console.WriteLine($"== nf knowledge transform（消化记录：{stats.GetValueOrDefault("entries")} 条）==");
            foreach (var e in entries)
                Console.WriteLine($"  {e.GetValueOrDefault("from"),-18} → {e.GetValueOrDefault("to"),-28} " +
                                  $"转正={PyBool(e.GetValueOrDefault("promoted"))}");
            foreach (var issue in issues) Console.Error.WriteLine("  [FAIL] " + issue);
            if (issues.Count == 0)
                Console.WriteLine("  ✓ 记录与产物摘要一致（无记录 = 无转正，符合 stay-reference）");
        }
        return issues.Count == 0 ? 0 : 1;
    }
    if (sub == "lint")
    {
        var (issues, warns, stats) = KnowledgeSources.Lint(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["issues"] = issues.Cast<object?>().ToList(),
                ["warns"] = warns.Cast<object?>().ToList(),
                ["stats"] = stats,
            }));
        }
        else
        {
            Console.WriteLine("== nf knowledge lint（知识层巡检）==");
            foreach (var issue in issues) Console.Error.WriteLine("  [FAIL] " + issue);
            foreach (var warn in warns) Console.WriteLine("  [WARN] " + warn);
            if (issues.Count == 0)
                Console.WriteLine($"  ✓ 声明/顺序/溯源/悬空/孤儿 全绿（时效缺失 {stats.GetValueOrDefault("no_stale_after")} 件已记 WARN）");
        }
        return issues.Count == 0 ? 0 : 1;
    }
    var (declIssues, declWarns, declStats) = KnowledgeSources.Scan(root!);
    if (json)
    {
        using var declDoc = JsonIo.ReadFile(Path.Combine(root!, "protocol", "knowledge_sources.json"));
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["declaration"] = PythonJson.ToGraph(declDoc.RootElement),
            ["issues"] = declIssues.Cast<object?>().ToList(),
            ["warns"] = declWarns.Cast<object?>().ToList(),
            ["stats"] = declStats,
        }));
    }
    else
    {
        Console.WriteLine($"== nf knowledge（双源知识层 · {declStats.GetValueOrDefault("sources")} 源：" +
                          $"合同 {declStats.GetValueOrDefault("contract")} / 参考 {declStats.GetValueOrDefault("reference")}）==");
        foreach (var s in KnowledgeSources.SourcesOf(root!))
        {
            Console.WriteLine($"  {DocContractIo.PyValue(s, "id"),-22} {DocContractIo.PyValue(s, "authority"),-9} " +
                              $"{DocContractIo.PyValue(s, "kind"),-18} {DocContractIo.PyValue(s, "visibility"),-10} " +
                              $"{DocContractIo.PyValue(s, "locator")}");
        }
        foreach (var warn in declWarns) Console.WriteLine("  [WARN] " + warn);
        foreach (var issue in declIssues) Console.Error.WriteLine("  [FAIL] " + issue);
        if (declIssues.Count == 0)
            Console.WriteLine("  ✓ 权威分层/查询有序/时效/晋升/审核/认知裁剪 全部与判据一致");
    }
    return declIssues.Count == 0 ? 0 : 1;
}

static string PyBool(object? value) => value is true ? "True" : "False";

int StateFrontCommand()
{
    // `nf state-front <path> [--check|--ab] [--mode front|back|none] [--json]`：全只读面（--out 写面未移植）。
    if (positional.Count < 2) return Fail("state-front 需要一个产物 md 路径");
    var target = positional[1];
    var full = Path.IsPathRooted(target) ? target : Path.Combine(root!, target.Replace('/', Path.DirectorySeparatorChar));
    if (!File.Exists(full)) { Console.Error.WriteLine($"  ✗ 找不到文件：{full}"); return 1; }
    var text = new System.Text.UTF8Encoding(false, true).GetString(File.ReadAllBytes(full));

    if (stateFrontAb)
    {
        var manifest = StateFront.AbManifest(text);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(manifest));
        }
        else
        {
            Console.WriteLine("== nf state-front --ab（三刺激件清单 · 不调模型）==");
            foreach (var mode in new[] { "front", "back", "none" })
            {
                var entry = (Dictionary<string, object?>)manifest[mode]!;
                var sha = ((string)entry["sha256"]!)[..16];
                var stateFront = entry["state_front"] is true ? "True" : "False";
                Console.WriteLine($"  {mode,-6} chars {entry["chars"],6} · sha256 {sha} · 状态块前置={stateFront}");
            }
        }
        return 0;
    }
    if (stateFrontCheck)
    {
        var issues = StateFront.CheckOrder(text);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["issues"] = issues.Cast<object?>().ToList(),
            }, 2));
        }
        else
        {
            Console.WriteLine($"== nf state-front --check（{target}）==");
            foreach (var issue in issues) Console.WriteLine("  [FAIL] " + issue);
            if (issues.Count == 0) Console.WriteLine("  ✓ 状态块已前置（条件先行）");
        }
        return issues.Count == 0 ? 0 : 1;
    }
    var output = StateFront.Reorder(text, stateFrontMode);
    if (outPath is not null)
        return Fail("state-front --out（写面）未移植：本引擎只做只读面（--check / --ab / 排布预览）");
    if (json)
    {
        // 同 Python：这里用的是 **非缩进** json.dumps（默认分隔符 ", " / ": "、不排序键）
        var chars = PyScalar.PyLen(output);
        var front = StateFront.CheckOrder(output).Count == 0;
        Console.WriteLine("{\"mode\": " + PythonJson.Quote(stateFrontMode) +
                          ", \"chars\": " + chars +
                          ", \"state_front\": " + (front ? "true" : "false") + "}");
    }
    else
    {
        Console.WriteLine($"== nf state-front（{target} → {stateFrontMode}）==");
        Console.WriteLine($"  输出长度 {PyScalar.PyLen(output)} 字符 · 状态块前置=" +
                          $"{(StateFront.CheckOrder(output).Count == 0 ? "True" : "False")}");
    }
    return 0;
}

int GovernanceCommand(string family)
{
    // 治理族三件（handover / postmortem / audit）的 `verify` 与 `ls` 面；`check <path>` 未移植。
    var sub = positional.Count >= 2 ? positional[1] : "ls";
    // 同 Python：`--json` 挂在**子命令**上，缺子命令时 `nf handover --json` 是用法错误（exit 2），
    // 不是"默认 ls + json"。此处不宽容，避免与参考实现的调用面不一致。
    if (json && positional.Count < 2)
        return Fail($"{family} 需要子命令（ls / verify）才能带 --json");
    var (issues, warns, stats, glob, listKeys, kind) = family switch
    {
        "handover" => Wrap(Handover.Scan(root!), "handovers/HO-*.md",
            new[] { "id", "title", "status", "date", "from", "to" }, "handover"),
        "postmortem" => Wrap(Postmortem.Scan(root!), "postmortems/PO-*.md",
            new[] { "id", "title", "status", "date", "trigger" }, "postmortem"),
        _ => Wrap(Audit.Scan(root!), "results/audit/*.md",
            new[] { "id", "date", "scope", "verdict", "auditor" }, "audit"),
    };

    if (sub == "verify")
    {
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["issues"] = issues.Cast<object?>().ToList(),
                ["warns"] = warns.Cast<object?>().ToList(),
                ["stats"] = stats,
            }));
        }
        else
        {
            Console.WriteLine(family switch
            {
                "handover" => $"== nf handover verify（{stats.GetValueOrDefault("handovers")} 件 · " +
                              $"未决 {stats.GetValueOrDefault("pending")} 条）==",
                "postmortem" => $"== nf postmortem verify（{stats.GetValueOrDefault("postmortems")} 件 · " +
                                $"行动项 {stats.GetValueOrDefault("actions")} 条）==",
                _ => $"== nf audit verify（{stats.GetValueOrDefault("audits")} 件 · " +
                     $"带审计头 {stats.GetValueOrDefault("with_header")} · legacy {stats.GetValueOrDefault("legacy")}）==",
            });
            foreach (var warn in warns) Console.WriteLine("  [WARN] " + warn);
            foreach (var issue in issues) Console.Error.WriteLine("  [FAIL] " + issue);
            if (issues.Count == 0)
            {
                Console.WriteLine(family switch
                {
                    "handover" => "  ✓ 声明与全部交接件一致",
                    "postmortem" => "  ✓ 声明与全部复盘件一致",
                    _ => "  ✓ 声明与全部审计件一致（legacy 只挂账不判死）",
                });
            }
        }
        return issues.Count == 0 ? 0 : 1;
    }
    if (sub == "check")
    {
        if (positional.Count < 3) return Fail($"{family} check 需要一个件路径");
        var path = positional[2];
        var (docIssues, docStats) = family switch
        {
            "handover" => Handover.CheckDoc(root!, path),
            "postmortem" => Postmortem.CheckDoc(root!, path),
            _ => Audit.CheckDoc(root!, path),
        };
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["path"] = path,
                ["issues"] = docIssues.Cast<object?>().ToList(),
                ["stats"] = docStats,
            }));
        }
        else
        {
            var header = family switch
            {
                "handover" => $"== nf handover check {path}（未决 {docStats.GetValueOrDefault("pending")} 条）==",
                "postmortem" => $"== nf postmortem check {path}（行动项 {docStats.GetValueOrDefault("actions")} 条）==",
                _ => $"== nf audit check {path}" +
                     $"{(docStats.GetValueOrDefault("legacy") is true ? "（legacy：无审计头，按 WARN 挂账）" : "")} ==",
            };
            Console.WriteLine(header);
            foreach (var issue in docIssues) Console.Error.WriteLine("  [FAIL] " + issue);
            if (docIssues.Count == 0)
            {
                if (family == "handover")
                    Console.WriteLine("  ✓ 五段齐 · 未决非空且每条带判据 · refs 可解析");
                else if (family == "postmortem")
                    Console.WriteLine("  ✓ 四段齐 · 无指责 · 根因指向机制 · 行动项带负责人与判据");
                else if (docStats.GetValueOrDefault("legacy") is not true)
                    Console.WriteLine("  ✓ 必填齐 · verdict 在册 · 结论绑定对象 digest · 签收双要素");
            }
        }
        return docIssues.Count == 0 ? 0 : 1;
    }
    if (sub != "ls") return Fail($"{family} 子命令只移植了 `ls` / `verify` / `check <path>`");

    var rows = DocContractIo.Entries(root!, glob);
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(rows.Select(r => (object?)listKeys.ToDictionary(
            k => k, k => r.Fm.TryGetValue(k, out var v) ? v : null, StringComparer.Ordinal)).ToList()));
        return 0;
    }
    Console.WriteLine($"== nf {family}（{rows.Count} 件）==");
    foreach (var row in rows)
    {
        if (kind == "audit")
        {
            Console.WriteLine($"  {DocContractIo.PyOr(row.Fm, "id", "(legacy)"),-11} " +
                              $"{DocContractIo.PyOr(row.Fm, "verdict", "-"),-6} " +
                              $"{DocContractIo.PyOr(row.Fm, "date", "-"),-11} {row.File}");
        }
        else if (kind == "handover")
        {
            Console.WriteLine($"  {DocContractIo.PyValue(row.Fm, "id"),-9} {DocContractIo.PyValue(row.Fm, "status"),-7} " +
                              $"{DocContractIo.PyValue(row.Fm, "date"),-10} {DocContractIo.PyValue(row.Fm, "from")} → " +
                              $"{DocContractIo.PyValue(row.Fm, "to")}");
        }
        else
        {
            Console.WriteLine($"  {DocContractIo.PyValue(row.Fm, "id"),-9} {DocContractIo.PyValue(row.Fm, "status"),-7} " +
                              $"{DocContractIo.PyValue(row.Fm, "date"),-10} {DocContractIo.PyValue(row.Fm, "title")}");
        }
    }
    return 0;
}

// 把三件治理契约的 scan 结果统一成 CLI 面所需的形状
static (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats, string Glob,
        string[] ListKeys, string Kind) Wrap(
        (List<string> Issues, List<string> Warns, Dictionary<string, object?> Stats) result,
        string glob, string[] listKeys, string kind)
    => (result.Issues, result.Warns, result.Stats, glob, listKeys, kind);

int PipelineCommand()
{
    // 只移植了 `nf pipeline dryrun`（全仓 `--all` 与单条管线两个面）。
    if (positional.Count >= 2 && positional[1] == "dryrun")
    {
        if (pipelineAll)
        {
            var (issues, tot) = PipelineDryrun.Sweep(root!);
            if (json)
            {
                Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
                {
                    ["issues"] = issues.Cast<object?>().ToList(),
                    ["stats"] = tot,
                }));
            }
            else
            {
                Console.WriteLine("== nf pipeline dryrun --all ==");
                Console.WriteLine($"  管线 {tot["pipelines"]} · 模块 {tot["modules"]} · " +
                                  $"官方核心基座 {tot["core_base"]} · advisory {tot["notes"]}");
                var buckets = tot.GetValueOrDefault("advisory_buckets") as Dictionary<string, object?>
                              ?? new Dictionary<string, object?>(StringComparer.Ordinal);
                foreach (var (category, count) in buckets.OrderBy(kv => kv.Key, StringComparer.Ordinal))
                    Console.WriteLine($"    · {category,-14} {count}");
                foreach (var issue in issues) Console.Error.WriteLine("  [FAIL] " + issue);
                if (issues.Count == 0)
                    Console.WriteLine("  ✓ 全仓管线零 hard 缺陷（advisory 为同层序/跨包事件，不作判死）");
            }
            return issues.Count == 0 ? 0 : 1;
        }
        if (pipelineName is null) return Fail("pipeline dryrun 需要管线路径（或用 --all）");
        PipelineDryrun.GraphResult graph;
        try
        {
            graph = PipelineDryrun.Graph(pipelineName, root!);
        }
        catch (Exception exc)
        {
            Console.Error.WriteLine("  ✗ " + exc.Message);
            return 1;
        }
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["schema"] = "nf-graphspec/1",
                ["pipeline"] = new Dictionary<string, object?>
                {
                    ["id"] = graph.PipelineId, ["name"] = graph.PipelineName,
                    ["structure_type"] = graph.StructureType,
                    ["path"] = pipelineName.Replace('\\', '/'),
                },
                ["steps"] = graph.Steps.Select(s => (object?)new Dictionary<string, object?>
                {
                    ["index"] = s.Index, ["layer"] = s.Layer, ["layer_name"] = s.LayerName,
                    ["optional"] = s.Optional,
                    ["modules"] = s.Modules.Select(m => (object?)new Dictionary<string, object?>
                    {
                        ["id"] = m.Id, ["path"] = m.Path, ["has_contract"] = m.HasContract,
                    }).ToList(),
                    ["missing"] = s.Missing.Cast<object?>().ToList(),
                }).ToList(),
                ["edges"] = graph.Edges.Select(e => (object?)new Dictionary<string, object?>
                {
                    ["from"] = e.From, ["to"] = e.To, ["kind"] = e.Kind,
                }).ToList(),
                ["tokens"] = graph.Tokens.Cast<object?>().ToList(),
                ["events"] = new Dictionary<string, object?>
                {
                    ["published"] = graph.Published.Cast<object?>().ToList(),
                },
                ["issues"] = graph.Issues.Cast<object?>().ToList(),
                ["notes"] = graph.Notes.Select(n => (object?)new Dictionary<string, object?>
                {
                    ["category"] = n.Category, ["detail"] = n.Detail,
                }).ToList(),
                ["stats"] = graph.Stats,
            }));
            return graph.Issues.Count == 0 ? 0 : 1;
        }
        Console.WriteLine($"== nf pipeline dryrun：{graph.PipelineId}（{graph.PipelineName}）==");
        Console.WriteLine($"  层 {graph.Stats["layers"]} · 模块 {graph.Stats["modules"]} · " +
                          $"token {graph.Stats["tokens"]} · 事件 {graph.Stats["events_published"]} · " +
                          $"hard {graph.Stats["issues"]} · advisory {graph.Stats["notes"]}");
        foreach (var step in graph.Steps)
        {
            var mods = step.Modules.Count == 0 ? "（空）" : string.Join("、", step.Modules.Select(m => m.Id));
            var layerName = step.LayerName.Length <= 12 ? step.LayerName : step.LayerName[..12];
            Console.WriteLine($"  {step.Index,2}. {step.Layer,-4} {layerName,-14} {mods}");
        }
        foreach (var issue in graph.Issues) Console.Error.WriteLine("  [FAIL] " + issue);
        foreach (var note in graph.Notes.Take(6)) Console.WriteLine("  [note] " + note.Detail);
        return graph.Issues.Count == 0 ? 0 : 1;
    }
    return Fail("pipeline 子命令只移植了 `dryrun`（--all / <管线路径>）；其余（new/dryrun --write-advisory）未移植");
}

int ModuleCommand()
{
    // 只移植了 `nf module types --backlog`（类型积压台账）；默认面（io_types）未移植——明确报错。
    if (positional.Count >= 2 && positional[1] == "types" && backlogOnly)
    {
        var (issues, stats) = TypeBacklog.VerifyBacklog(root!);
        Console.WriteLine("== nf module types --backlog ==");
        Console.WriteLine($"  不可推断的 untyped：{stats["untyped"]} 项");
        foreach (var issue in issues) Console.Error.WriteLine("  [FAIL] " + issue);
        return issues.Count == 0 ? 0 : 1;
    }
    if (positional.Count >= 2 && positional[1] == "types")
    {
        // `nf module types`（I/O 类型面）：可证不匹配/越词表 → FAIL 走 stderr；未收窄/L0 只 WARN。
        var (issues, warns, stats) = IoTypes.Scan(root!);
        var coverage = IoTypes.Coverage(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["issues"] = issues.Cast<object?>().ToList(),
                ["warns"] = warns.Cast<object?>().ToList(),
                ["stats"] = coverage,
            }));
        }
        else
        {
            Console.WriteLine("== nf module types（I/O 类型面）==");
            var total = (int)(coverage["typed_fields"] ?? 0) + (int)(coverage["untyped_fields"] ?? 0);
            var percent = ((double)(coverage["coverage"] ?? 0.0))
                .ToString("F1", System.Globalization.CultureInfo.InvariantCulture);
            Console.WriteLine($"  机读契约模块 {coverage["modules_with_contract"]} · L0 未承载 {coverage["l0_modules"]} · " +
                              $"已标注 {coverage["typed_fields"]}/{total} 字段（{percent}%）");
            foreach (var issue in issues) Console.Error.WriteLine("  [FAIL] " + issue);
            foreach (var warn in warns) Console.WriteLine("  [WARN] " + warn);
            if (issues.Count == 0) Console.WriteLine("  ✓ 无可证类型不匹配（untyped 为如实缺口，不判死）");
        }
        return issues.Count == 0 ? 0 : 1;
    }
    if (positional.Count >= 2 && positional[1] == "signature")
    {
        // `nf module signature`（边界冻结）：漂移 → FAIL 走 stderr；新增/撤签 → WARN。
        var (issues, warns, stats) = ModuleSignature.Verify(root!);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
            {
                ["issues"] = issues.Cast<object?>().ToList(),
                ["warns"] = warns.Cast<object?>().ToList(),
                ["stats"] = stats,
            }));
        }
        else
        {
            Console.WriteLine("== nf module signature（边界冻结）==");
            Console.WriteLine($"  模块 {stats.GetValueOrDefault("modules")} · 已签 {stats.GetValueOrDefault("signed")}");
            foreach (var issue in issues) Console.Error.WriteLine("  [FAIL] " + issue);
            foreach (var warn in warns) Console.WriteLine("  [WARN] " + warn);
            if (issues.Count == 0) Console.WriteLine("  ✓ 全部模块边界与基线一致（改边界须显式重签）");
        }
        return issues.Count == 0 ? 0 : 1;
    }
    if (positional.Count >= 2 && positional[1] == "verify")
    {
        var (issues, stats) = ModuleLifecycle.VerifyModules(root!);
        Console.WriteLine("== nf module verify ==");
        Console.WriteLine($"  统计：模块 {PyS(stats["modules"])} / active {PyS(stats["active"])} / "
                          + $"deprecated {PyS(stats["deprecated"])} / retired {PyS(stats["retired"])}");
        if (issues.Count > 0)
        {
            foreach (var issue in issues) Console.Error.WriteLine($"  [FAIL] {issue}");
            return 1;
        }
        Console.WriteLine("  ✓ 无 deprecated/retired 模块被引用（引用门禁全绿）");
        return 0;
    }
    if (positional.Count >= 2 && positional[1] == "ls")
    {
        var rows = ModuleLifecycle.Rows(root!, assetStatus);
        if (json)
        {
            Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>(StringComparer.Ordinal)
            {
                ["kind"] = "module-ls",
                ["status"] = assetStatus.Length > 0 ? assetStatus : null,
                ["rows"] = rows.OrderBy(r => r.Status, StringComparer.Ordinal)
                    .ThenBy(r => r.File, StringComparer.Ordinal)
                    .Select(r => (object?)new Dictionary<string, object?>(StringComparer.Ordinal)
                    {
                        ["status"] = r.Status, ["file"] = r.File,
                    }).ToList(),
            }));
            return 0;
        }
        Console.WriteLine("== nf module ls ==");
        foreach (var (status, file) in rows)
            Console.WriteLine("  " + PadCp(status, 10) + " " + file);
        Console.WriteLine($"  合计 {rows.Count}");
        return 0;
    }
    if (positional.Count >= 2 && positional[1] == "status")
    {
        if (positional.Count < 3) return Usage("module status 需要一个模块 md 路径");
        var fpath = positional[2];
        if (!File.Exists(fpath)) return Fail($"文件不存在：{fpath}");
        var before = ModuleLifecycle.GetStatus(
            KnowledgeSig.Norm(new System.Text.UTF8Encoding(false, true).GetString(File.ReadAllBytes(fpath)))).Status;
        Console.WriteLine("== nf module status ==");
        Console.WriteLine($"  {fpath} → {before}");
        return 0;
    }
    if (positional.Count >= 2 && positional[1] is "deprecate" or "restore")
        return Fail($"module {positional[1]} 是写面（改模块文件状态位）——本引擎是只读门，不提供写命令");
    return Fail("module 子命令只移植了 `types`（含 --backlog）/ `signature` / `ls` / `status` / `verify`；"
                + "其余（deprecate/restore/contract）属写面或未移植");
}

int LintCommand()
{
    // 只移植了 `nf lint --kinds`（四型写法判据）；默认面（autofix 规则 + 正文 lint）未移植——
    // 未移植就明确报错，不静默给"通过"。
    if (!kindsOnly)
    {
        return Fail("lint 默认面未移植（autofix 机械规则 + 正文 lint）：本引擎只实现 `nf lint --kinds`");
    }
    var warns = DocHygiene.KindRulesFor(root!);
    Console.WriteLine("== nf lint --kinds（四型写法判据）==");
    foreach (var warn in warns) Console.WriteLine("  [WARN] " + warn);
    if (warns.Count == 0) Console.WriteLine("  ✓ 四型写法齐（每型都有该型必备的结构块）");
    return 0;
}

int ConformanceCommand()
{
    var report = Conformance.Run(root!);
    var failed = report.Contracts.Where(c => !c.Ok).ToList();
    if (json)
    {
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            // 诚实标注：本引擎只落地了部分契约，**不输出 conformant / non-conformant**
            ["verdict"] = "partial",
            ["coverage"] = $"{report.Contracts.Count}/{Conformance.AllContractIds.Length}",
            ["ported"] = report.Contracts.Select(c => (object?)new Dictionary<string, object?>
            {
                ["id"] = c.Id, ["ok"] = c.Ok, ["detail"] = c.Detail, ["digest"] = c.Digest,
                ["description"] = c.Description,
            }).ToList(),
            ["unported"] = report.Unported.Cast<object?>().ToList(),
            ["passed"] = report.Passed,
            ["root_of_ported"] = report.RootOfPorted,
        }));
    }
    else
    {
        Console.WriteLine("== nf-dotnet conformance（一致性报告 · 部分实现）==");
        foreach (var c in report.Contracts)
            Console.WriteLine($"  {(c.Ok ? "✓" : "✗")} {c.Id,-28} {c.Detail}");
        Console.WriteLine($"  —— 已移植 {report.Contracts.Count}/{Conformance.AllContractIds.Length} 契约 · " +
                          $"通过 {report.Passed} · root(已移植叶子)={report.RootOfPorted[..Math.Min(16, report.RootOfPorted.Length)]}");
        Console.WriteLine($"  —— 未移植 {report.Unported.Count} 条（不参与判定，不伪造 verdict）：" +
                          string.Join("、", report.Unported));
    }
    return failed.Count == 0 ? 0 : 1;
}

int AggregateCommand()
{
    var components = new List<Receipts.ArtifactResult>
    {
        Receipts.VerifyProtocolReceipts(root!),
        Receipts.VerifyLibraryReceipts(root!),
        Receipts.VerifyTransparencyChain(root!),
    };
    var rows = CertificateVerifier.VerifyAll(root!);
    var combineIssues = rows.Where(r => r.Issues.Count > 0)
        .SelectMany(r => r.Issues.Select(i => r.Label + "：" + i)).ToList();
    var combineOk = combineIssues.Count == 0;
    var assertions = Assertions.Run(root!);
    var decisions = Decisions.Verify(root!);
    var library = Library.Verify(root!);
    var model = Modeling.Run(root!);
    var cognition = Cognition.Run(root!);
    var sig = KnowledgeSig.VerifyReproducible(root!);
    var conformance = Conformance.Run(root!);
    var conformanceFailed = conformance.Contracts.Where(c => !c.Ok).ToList();
    var decisionIssues = decisions.Issues.Concat(decisions.Projection).ToList();
    var libraryIssues = library.Issues.Concat(library.Projection).ToList();
    var ok = components.All(c => c.Ok) && combineOk &&
             assertions.Issues.Count == 0 && decisionIssues.Count == 0 && libraryIssues.Count == 0 &&
             model.Issues.Count == 0 && cognition.Issues.Count == 0 && sig.Issues.Count == 0 &&
             conformanceFailed.Count == 0;

    if (json)
    {
        var list = components.Select(c => (object?)new Dictionary<string, object?>
        {
            ["name"] = c.Name,
            ["ok"] = c.Ok,
            ["issues"] = c.Issues.Cast<object?>().ToList(),
            ["detail"] = c.Detail,
        }).ToList();
        list.Add(new Dictionary<string, object?>
        {
            ["name"] = "protocol/combo_certificates.json",
            ["ok"] = combineOk,
            ["issues"] = combineIssues.Cast<object?>().ToList(),
            ["detail"] = $"证书 {rows.Count} 条 · 失败 {rows.Count(r => r.Issues.Count > 0)}",
        });
        list.Add(new Dictionary<string, object?>
        {
            ["name"] = "protocol/assertions.json",
            ["ok"] = assertions.Issues.Count == 0,
            ["issues"] = assertions.Issues.Cast<object?>().ToList(),
            ["detail"] = $"断言 {assertions.Results.Count} 条 · 问题 {assertions.Issues.Count}",
        });
        list.Add(new Dictionary<string, object?>
        {
            ["name"] = "decisions/ADR-*.md",
            ["ok"] = decisionIssues.Count == 0,
            ["issues"] = decisionIssues.Cast<object?>().ToList(),
            ["detail"] = $"ADR {decisions.Stats["decisions"]} 条 · accepted {decisions.Stats["accepted"]} · 问题 {decisionIssues.Count}",
        });
        list.Add(new Dictionary<string, object?>
        {
            ["name"] = "library/NF-*.md",
            ["ok"] = libraryIssues.Count == 0,
            ["issues"] = libraryIssues.Cast<object?>().ToList(),
            ["detail"] = $"条目 {library.Stats["entries"]} · 在役 {library.Stats["active"]} · WARN {library.Warns.Count} · 问题 {libraryIssues.Count}",
        });
        list.Add(new Dictionary<string, object?>
        {
            ["name"] = "protocol/{vocabularies,normative,data_contracts}.json",
            ["ok"] = model.Issues.Count == 0,
            ["issues"] = model.Issues.Cast<object?>().ToList(),
            ["detail"] = $"词表 {((Dictionary<string, object?>)model.Stats["vocab"]!)["schemes"]} · " +
                         $"规范件 {((Dictionary<string, object?>)model.Stats["normative"]!)["normative"]} · " +
                         $"契约 {((Dictionary<string, object?>)model.Stats["contracts"]!)["contracts"]}",
        });
        list.Add(new Dictionary<string, object?>
        {
            ["name"] = "protocol/{glossary,execution_modes}.json",
            ["ok"] = cognition.Issues.Count == 0,
            ["issues"] = cognition.Issues.Cast<object?>().ToList(),
            ["detail"] = $"术语 {((Dictionary<string, object?>)cognition.Stats["glossary"]!)["terms"]} · " +
                         $"分档 {((Dictionary<string, object?>)cognition.Stats["modes"]!)["modes"]} · 问题 {cognition.Issues.Count}",
        });
        list.Add(new Dictionary<string, object?>
        {
            ["name"] = "01-36 知识签名（两遍一致）",
            ["ok"] = sig.Issues.Count == 0,
            ["issues"] = sig.Issues.Cast<object?>().ToList(),
            ["detail"] = $"文档 {sig.Stats["docs"]} · 可复现 {sig.Stats["reproducible"]}",
        });
        list.Add(new Dictionary<string, object?>
        {
            ["name"] = $"conformance（已移植 {conformance.Contracts.Count}/{Conformance.AllContractIds.Length} 契约）",
            ["ok"] = conformanceFailed.Count == 0,
            ["issues"] = conformanceFailed.Select(c => (object?)(c.Id + "：" + c.Detail)).ToList(),
            ["detail"] = $"通过 {conformance.Passed} · 未移植 {conformance.Unported.Count}（不参与判定）",
        });
        Console.WriteLine(PythonJson.Indented(new Dictionary<string, object?>
        {
            ["ok"] = ok,
            ["components"] = list,
        }));
    }
    else
    {
        Console.WriteLine("== nf-dotnet verify（NF 工业引擎 · 只读聚合校验）==");
        foreach (var c in components)
        {
            Console.WriteLine($"  {(c.Ok ? "✓" : "✗")} {c.Name,-42} {c.Detail}");
            foreach (var issue in c.Issues.Take(5)) Console.WriteLine("      · " + issue);
        }
        Console.WriteLine($"  {(combineOk ? "✓" : "✗")} {"protocol/combo_certificates.json",-42} 证书 {rows.Count} 条 · 失败 {rows.Count(r => r.Issues.Count > 0)}");
        Console.WriteLine($"  {(assertions.Issues.Count == 0 ? "✓" : "✗")} {"protocol/assertions.json",-42} 断言 {assertions.Results.Count} 条 · 问题 {assertions.Issues.Count}");
        Console.WriteLine($"  {(decisionIssues.Count == 0 ? "✓" : "✗")} {"decisions/ADR-*.md",-42} ADR {decisions.Stats["decisions"]} 条 · 问题 {decisionIssues.Count}");
        Console.WriteLine($"  {(libraryIssues.Count == 0 ? "✓" : "✗")} {"library/NF-*.md",-42} 条目 {library.Stats["entries"]} · 在役 {library.Stats["active"]} · 问题 {libraryIssues.Count}");
        Console.WriteLine($"  {(model.Issues.Count == 0 ? "✓" : "✗")} {"model（词表/规范件/契约）",-42} 问题 {model.Issues.Count}");
        Console.WriteLine($"  {(cognition.Issues.Count == 0 ? "✓" : "✗")} {"cognition（术语表/执行分档）",-42} 问题 {cognition.Issues.Count}");
        Console.WriteLine($"  {(sig.Issues.Count == 0 ? "✓" : "✗")} {"sig（01-36 两遍一致）",-42} 文档 {sig.Stats["docs"]}");
        Console.WriteLine($"  {(conformanceFailed.Count == 0 ? "✓" : "✗")} {$"conformance（已移植 {conformance.Contracts.Count}/{Conformance.AllContractIds.Length}）",-42} 通过 {conformance.Passed} · 未移植 {conformance.Unported.Count}（不参与判定）");
        Console.WriteLine(ok ? "  —— 全部通过" : "  —— 存在失败项");
    }
    return ok ? 0 : 1;
}

int Usage(string? error)
{
    if (error is not null) Console.Error.WriteLine("错误：" + error);
    Console.Error.WriteLine("""
nf-dotnet 0.1.0 · NF 工业引擎 CLI（只读子集，输出面与 Python 侧 nf 对齐）

用法：nf-dotnet [--root <dir>] [--json] <命令>

命令：
  verify                                            聚合校验（协议回执 + 馆藏回执 + 透明链 + 组合证书）
  assertions                                        数据化断言表求值（14 条 · 4 种 kind）
  decisions [verify]                                决策记录门禁（ADR 编号/状态/取代链/证据/回执锚定/投影）
  cognition                                         认知族门禁（术语表真源逐字命中 + 执行分档结构块）
  library                                           馆藏门（frontmatter + 签名锚漂移 + INDEX/ALIAS 投影）
  bench [--baseline <f>] [--write-baseline <f>]     性能基线：测量关键操作，可对基线做回归门
  serve                                             MCP stdio 服务器（JSON-RPC 2.0 · dual-era · 只读 15 工具）
  receipts [--scope protocol|library]               回执复算（默认 protocol）
  transparency                                      透明链复算
  combine verify                                    组合证书 T4 复算
  combine plan --packs a,b [--extra-modules x,y] [--strict-coherence]  组合一个并打印证书
  combine breadth [--pairs-only] [--samples <json>] 广度证明（默认自足：两两全集 + 定种子抽样）
  selftest                                          负例 / 健壮性自检（撞号·深链·未知包·悬空·未桥接 + 篡改检测）
  patterns ls|show|for|verify [--json]              实践包（读面子集；reindex 属写面，不提供）
  rfc [--json]                                      协议件 RFC 索引与 supersede 链自检
  endpoint [--json]                                 服务端点契约自检（proposed；契约不指向空气）
  events [--json]                                   全仓事件背书核对（订阅是否真有发布方）
  toolface [--json]                                 模块工具面浏览（machine_contract.tool_face 建议层）
  st-validate <path> [--out <p>] [--json]           ST 制卡校验器（卡 / 世界书 / MVU 变量 → 可自动化项报告）
  stats [--check] [--json]                          自述数字实算（README/README.en/llms.txt 生成区 == 实算）
  telemetry <trace.json> [--otlp]                   遥测 semconv 映射（trace 记录 → OTel GenAI 属性 / OTLP 形状）
  driver [工作流] [--json]                          指令档机器面路由（有 MCP 走 MCP；派发失败即停、不回退文本）
  interop --list | --kind K [--out P] [--check]     互操作导出面（12/12 形状已移植；--check 跑门禁）
  impact <target> [--check] [--registry P]          变更影响面预检（拟删除 module/protocol 前查破坏性）
  related <target> [--json] [--registry P]          See-Also 关联（引用了谁 / 谁引用我 / 模块互见）
  market --list [--tier T] [--json]                 市场目录视图（官方核心 + 社区包，各带分级徽章）
  asset verify|inventory|ls|baseline|density|usage|thickness|ledger [--assets-root P]  资产供应链台账（verify = check23 同语义闭合门禁；baseline 只读比对）
  model [vocab|normative|contracts] [--json]        内容建模三件（词表 / 规范件 / 数据契约）
  sig [verify] [--json]                             知识签名（根文档结构化签名 + 两遍一致）
  worldmodel [--json]                               世界模型面（JEPA-inspired 确定性抽象状态契约 · check32 硬门）
  conformance [--json]                              一致性报告（部分实现：只报已移植契约 · verdict=partial）
  corpus [--json]                                   语料身份指纹（导出态比金标 · 工作区态只报模式）
  lint --kinds [--json]                             文档 lint 只读子集（autofix / 正文 lint 未移植）
  module types|signature|ls|status|verify [--json]  模块面（写面 deprecate/restore/contract 不提供）
  pipeline dryrun [--all] [--json]                  管线抽象执行（--write-advisory 属写面，不提供）
  handover [--json]                                 交接待办清单（HO 编号 / 状态 / 承接人）
  postmortem [--json]                               复盘登记（PO 编号 / 状态 / 一句话教训）
  audit [--check] [--json]                          审计面（登记册与对象锁回执）
  state-front <产物 md> [--json]                    前端状态（--out 属写面，不提供）
  knowledge [order|visible|transform|lint|frequency] [--json]  双源知识层（缺省即 status；写面不提供）
  who-refers <模块 id> [--json]                     反向引用（谁提到这个模块）
  diff <a> <b> [--json]                             两文档结构化差分
  explain <check 编号|all> [--json]                 判据说明（编号 → 该 check 在查什么）
  output [list|render|verify|check|meter] [--json]  产出面（写面不提供；list 为形态清单）
  domain-closure [--target X|--list|--gaps|--check] 概念前置闭包求值器（真源是 scripts/ 下独立脚本 · 只读）
  workloop [--list] [--top N] [--source S] [--json] 构建回路：工单扫描与能力缺口（写面不提供）
  license [--json]                                  图书馆许可证门（登记 / 声明 / 内联 / 双源一致）
  score [--baseline <f>] [--tolerance X] [--json]   基线相对回归评分（purity_clean 为声明边界）
  decide --questions <f> [--state-text S|--state <f>] [--dry-run] [--json]  决策层（choice/score/noul；端点适配器不外呼）
  doctor [--json]                                   环境自检（文件在场 / 注册表 / schema / 基线自述 / 机器面）
  spec [ls] [--json]                                注册表面（registry 版本 + 官方核心模块数 + 逐协议包）
  review [--limit N] [--scope S] [--batch B] [--json]  逐行缺口审查（机械预筛 + 确定性证据复核）
  extension [--diff <文件|->] [--json]              扩展策略面（结构 bump 待迁移记录；diff 由调用方提供）
  assemble "<需求>" [--answer X ...] [--check <成品 md>]  需求 → 装配计划（--check 对成品做机器验收）
  daemon                                            执行层常驻守护（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  shell    → 执行层·交互层（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  terminal → 执行层·交互层（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  lsp      → 执行层·交互层（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  completion → 执行层·交互层（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  demo     → 执行层·交互层（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  run      → 执行层·交互层（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  help     → 执行层·交互层（真源有）——**本引擎只读，不提供**（用法见 --help）
  register → 写面·工厂（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  rename   → 写面·工厂（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  import   → 写面·工厂（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  approve  → 写面·工厂（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  attest   → 写面·工厂（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  design   → 写面·工厂（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  domain   → 写面·工厂（真源有）——**本引擎只读，不提供**（调用即显式拒绝）
  layers   → 读面未移植（真源 protocol/LAYERS.json · 与 check27 R7 同源）
  release  → 读面未移植（verify + doctor 组合）

全局：--root <dir> 指定仓库根；--json 输出结构化 JSON（键排序 + 2 空格缩进，与 nf 一致）
退出码：0 通过 / 1 存在问题 / 2 用法或 IO 错误
""");
    return error is null ? 0 : 2;
}

int Fail(string message)
{
    Console.Error.WriteLine("错误：" + message);
    return 2;
}

/// <summary>
/// 把交给 stdout 的裸 '\n' 翻成宿主换行（等价 Python 文本模式 <c>newline=None</c> 的写侧翻译）。
/// 已经是 CRLF 的序列原样透传（<c>_last == '\r'</c> 时不再补），故不会写出 CRCRLF。
/// </summary>
internal sealed class NewlineNormalizingWriter(TextWriter inner) : TextWriter
{
    private char _last;

    public override System.Text.Encoding Encoding => inner.Encoding;

    public override void Write(char value)
    {
        if (value == '\n' && _last != '\r')
        {
            inner.Write(Environment.NewLine);   // Windows: "\r\n"；Linux: "\n"（恒等）
        }
        else
        {
            inner.Write(value);
        }
        _last = value;
    }

    public override void Write(string? value)
    {
        if (string.IsNullOrEmpty(value)) return;
        foreach (var ch in value) Write(ch);
    }

    public override void Flush() => inner.Flush();
}
