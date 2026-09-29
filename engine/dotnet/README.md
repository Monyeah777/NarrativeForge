# NF .NET 引擎线（`engine/dotnet/`）

> **定位：只读判据的第二个实现。**与 Python 侧（`verify.sh` + `desktop/src`）**并列**——不替代、不写盘、不改 `verify.sh` 基线。
> 依据：`decisions/ADR-0005-新增NET引擎线.md`；**维护手册见 `RUNBOOK.md`**。

## 这是什么

同一份语料上，本线用 C# **独立复算**判据面，并与 Python 侧**逐字节对账**。它要解决的不是"更快"，而是一直以来的缺口：**同一语义只被一个实现验证过**。

| 面 | 现状（实测） |
|---|---|
| 一致性契约 | **26 / 27** 已移植并逐契约对账；唯一未移植项 `purity-clean` 属源码 AST linter 面，已显式裁定范围外（不伪造） |
| 命令行面 | **183 面逐字节全同 + 1 边界面**（组合证书 / 回执 / 透明链 / 馆藏 / 建模 / 知识签名 / 决策 / 断言 / 认知 / 指令档 / 装配 / 审查 / 评分 / 许可证 / 环境自检 / 注册表 …） |
| 负例自检 | **227 例**（撞号 / 深链 / 未知包 / 悬空 / 未桥接 / 四类篡改 / 破坏输入 / 并行不变性 / 契约正反对照） |
| `verify.sh` 覆盖率 | 39 道 check：**覆盖 32 / 不适用 6（有对应物）/ 范围外 1**；判据面无「部分」、无「未覆盖」 |
| 判据探针 | **45 条**（`probes/`，跑法见 `RUNBOOK.md` §0） |
| 分发 | 引擎库包 `NarrativeForge.Engine`（**零 NuGet 依赖**）+ CLI 工具包 `NarrativeForge.Engine.Cli` + 自包含多文件产物（当片 **f112**：win/linux 各 189 文件 / 72.4 MB） |
| 可复现构建 | 同 RID 异地重建 **189/189 文件逐字节全等**（`Directory.Build.props` 的 `PathMap` 归一） |
| 复基线 | **一条命令**：`run-rebaseline.ps1 -Snap <新快照> -SnapName <名> -Head <sha>`（预检 → 重生成夹具 → 断言式改写常量与**金标出处** → 重建三类产物 → 跑门；缺省 dry-run） |
| 外部侧样例 | `samples/zero-dep-recompute/`：不跑 NF 代码、不依赖 Python，用自包含产物复算证书并自验（含 111 包极限工况与负对照） |

**明确边界（不得对外宣称的）**

- **不能替代 `verify.sh`**：本线是**第二道门**，真源仍在 Python 侧；
- **写面不实现**：所有 `--write` 类命令一律 **fail-closed 拒绝**（只读门不落盘；实测写面 20 条全拒、且母树指纹零改动）；
- **执行层/交互层不提供**，且**显式拒绝**而非"未知命令"：`daemon` / `shell` / `terminal` / `lsp` / `completion` / `demo` / `run` / `help`；写面/工厂 `register` / `rename` / `import` / `approve` / `attest` / `design` / `domain` 同（共 **16 条**，由 `probes/cli_surface_probe.py` 守帮助表可达）；
- 未移植项与已知缺口的逐条清单见 `RUNBOOK.md` §5 与 ADR-0005 的「代价与风险」段；**未移植的读面**：`layers`（与 check27 R7 同源）/ `release`（verify+doctor 组合）。

## 构建与运行

```bash
# 构建（BCL-only：无需 NuGet 源）
dotnet build engine/dotnet/src/Nf.Engine/Nf.Engine.csproj -c Release
dotnet build engine/dotnet/tools/nf-dotnet/nf-dotnet.csproj -c Release

# 只读门：聚合 11 件 + 227 例负例自检 + 性能基线（Windows 用 …/nf-dotnet.exe，Linux/macOS 无后缀）
pwsh -NoProfile -File engine/dotnet/run-gate.ps1 -Root . -Cli engine/dotnet/tools/nf-dotnet/bin/Release/net8.0/nf-dotnet
```

## 判据探针（45 条）

`probes/` 下每条都是**可复跑的判据**（不是脚本集合）：等价对账、负例、差分模糊、敌意输入、规模、可复现构建、只读不变量、打包消费、API 面冻结、抖动、不倒退、入库包体检、CLI 面可达。**口径的唯一出处是 `probes/probe_manifest.json`**（哪条用 `nf-dotnet`、哪条用 `nfparity`、要传哪些路径），跑批器**不硬编码参数**：

```bash
pwsh -NoProfile -File engine/dotnet/run-probes.ps1 -Tier core   # 默认集合
pwsh -NoProfile -File engine/dotnet/run-probes.ps1 -Tier all    # 含重型（两道门同判 / 规模 / 模糊 / 敌意输入）
```

探针的破坏性用例**只在临时副本上跑**；跑批只写 `probes/_stout/`（不碰语料、不覆盖具名记录件——每条会写记录件的探针都在清单里带 `--record` 重定向）。

## 依赖与姿态

- **BCL-only**：无 NuGet 依赖（包内 `<dependency>` 数为 0）；YAML 用自研子集解析器，**越出子集即 fail-closed**。
- **零外部进程、零外呼**：源码无 `Process.Start`；端点类适配器只保留 fail-closed 分支。
- **确定性**：全部 culture 调用显式 invariant；构建期 `PathMap` 归一；`selftest --json` 输出把运行期临时根归一到 `<tmp>`。
- **公开 API 面已冻结**：`api/Nf.Engine.PublicAPI.txt`（176 类型 / 2264 成员），漂移即由探针判红。
- **不倒退**：`api/no_regression_baseline.json` 记录五类可数基线（已移植契约集合 / 未移植集合 / 自检例数 / 探针条数 / 对账面数），只增不减。
