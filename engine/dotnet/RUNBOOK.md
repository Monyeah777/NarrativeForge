# NF .NET 引擎线 · 维护手册（RUNBOOK）

> 面向**接手这条线的人**（包括未来的编制者）。只讲「怎么维护 / 怎么排错」，不讲「它是什么」——那在 `README.md`。
> **贯穿纪律**：本线是**只读第二实现**，任何时刻都不许写被测语料。

## 0. 三条日常命令

| 目的 | 命令 |
|---|---|
| 一键门（聚合 11 件 + 227 例自检 + 性能基线） | `pwsh -NoProfile -File engine/dotnet/run-gate.ps1 -Root <语料> -Cli <nf-dotnet>` |
| 全量判据跑批（默认 core 档） | `pwsh -NoProfile -File engine/dotnet/run-probes.ps1 -Tier core` |
| 单条判据 | `python engine/dotnet/probes/<probe>.py --snap <语料> --cli <nf-dotnet>` |

两个 PS1 的默认值按「**环境变量 → `probes/_paths.local.json` → PATH 通用名**」三级解析：换机器时只写本地配置，或设
`NF_SNAPSHOT` / `NF_SNAPSHOT_OTHER` / `NF_CLI` / `NF_PYTHON` / `NF_DOTNET` / `NF_BASH`。
## 0.1 C ABI 共享库出口（`src/Nf.Engine.Native/`）

给 `desktop/src/core/engine_loader.py` 一个**可 dlopen 的原生库**：`NativeExports.cs` 用
`[UnmanagedCallersOnly(EntryPoint = "nf_engine_abi_version")]` 导出与 Rust 线**同名同义**的 C ABI 符号。

```powershell
dotnet publish engine/dotnet/src/Nf.Engine.Native/Nf.Engine.Native.csproj -c Release -r win-x64 -o engine/dotnet/dist
# → engine/dotnet/dist/nf_engine_native.dll
python -c "import sys;sys.path.insert(0,'desktop/src');from core import engine_loader as el;print(el.engine_abi('engine/dotnet/dist/nf_engine_native.dll'))"
```

> **前置条件（2026-10-10 实测）**：`PublishAot=true` 需要 **Desktop Development for C++**（MSVC `link.exe` + Windows SDK）；
> 缺它时 ILC 报 `Platform linker not found`（ILCompiler 8.0.31）；`dotnet build` 本身零警告零错误。
> 本机装 VS Build Tools（`VC.Tools.x86.x64` + `Windows11SDK.22621`）后 **publish 成功**：产出
> `nf_engine_native.dll`（1.1 MB），`engine_loader.engine_abi(...)` → **1**（真 dlopen + 调 C ABI），
> `python scripts/engine_status.py` 列出该候选库。产物落 `engine/dotnet/dist/`（`.gitignore` 的 `dist/`，不入库）。
> 本件是**独立的"原生出口壳"**，不改 `Nf.Engine` 主库的 **BCL-only** 依赖姿态（ADR-0005）。


## 1. 加一条判据（标准流程）

1. 写 `probes/<name>_probe.py`：`argparse` 接 `--snap` / `--cli` 等，默认值从 `_paths` 取；开头设 `sys.dont_write_bytecode = True`；
   **先证它会红**（加负对照，否则"只增不减"型判据最容易恒绿）。
2. 登记进 `probes/probe_manifest.json`（**跑批口径的唯一出处**）：`name` / `script` / `tier` / `args` / `note`。
   跑批器的「清单 ↔ 磁盘」守卫会在漏登记或写错脚本名时**直接红**。
3. 跑 `run-probes.ps1 -Only <name>`，再跑 `-Tier core` 确认不连累别条。
4. 计数变了就更新基线：`python probes/no_regression_probe.py --update`。
5. 更新文档数字并收口：`probes/handoff_integrity_probe.py`（工作区文档数字 = 实测）·
   `probes/bundle_integrity_probe.py`（**入库包**文档数字 = 实测）。

## 2. 真源变了怎么办（**一条命令**）

**第一百二十二片起：复基线已工具化** —— `run-rebaseline.ps1`：

```bash
# 先把新 HEAD 导出成快照（CJK 名安全：git archive → Python tarfile 解包）
# 先 dry-run 看它会改什么（夹具改了会还原、源码不动），确认后加 -Apply
pwsh -NoProfile -File run-rebaseline.ps1 -Snap <新快照> -SnapName nf-snap-hN            # dry-run
pwsh -NoProfile -File run-rebaseline.ps1 -Snap <新快照> -SnapName nf-snap-hN -Apply    # 落改 + 重建三类产物 + 跑门
```

它做六件事：① 预检（新快照在场、指纹 ≠ 当前金标）→ ② 重生成三份**语料锚定夹具**（text_hygiene / prose_lint / regression_score）→ ③ 读出三个摘要与三处计数 → ④ **断言式**改写常量（`CorpusStamp.Baseline` · `SelfTest` 三个摘要 + 三处计数 + 两处钉名 · 可选改**默认快照名**，且只改 `SNAP` 不动 `SNAP_OTHER`）→ ⑤ 重建 **Nf.Engine / nf-dotnet / nfparity**（后者自带判据库副本，**漏了会假红**）→ ⑥ 对新快照跑一键门。

### 手工路径（工具没覆盖到时）

- **先归因，别先改引擎**：`nf-dotnet --root <语料> corpus --json` 看语料身份。
  - 指纹**不匹配**（且是导出态）⇒ 语料换了：**从「复基线」处置**（重生成 fixtures、重嵌常量、更新金标摘要）。
  - 指纹**匹配**而某条判据红了 ⇒ 才是真的语义/实现问题。
- **两类根**：导出快照（无 `.git`）按**金标摘要**断；工作区（有 `.git`）按**语义不变量**断。要在活仓库上体检，直接 `-Root <仓库>`。
- 单探针夹具重生成：`--write-fixture`（**有意变更**才用；它改的是判据真源）。

## 3. 红了怎么排（归因顺序）

1. **看归因提示**：`run-gate.ps1` 自检失败会打印失败钉名与 detail；语料不匹配时另打「先复基线再判引擎」。
2. **看是不是抖动**：`stability_probe.py` 失败会把**全部重复轮次的完整输出**写进 `probes/_stout/_stability_fail_<面>.txt`。
3. **保留现场**：多数探针支持 `--keep`（保留临时树/副本）。
4. **顺序**：语料身份 → 金标锚定 → 别面回归 → 引擎缺陷。**别拿"再跑一次看看"当结论**。

## 4. 入库 / 发布链（作者闸门之后）

落地 **8 步**：EOL 归一到 LF → 落内容 → **`.gitignore`（`engine/dotnet/**/{bin,obj}`）** →
`nf interop --all --out results/interop` → `nf conformance --write` →
`nf approve protocol/conformance_report.json --by <作者>` → `nf receipts --scope protocol --write` → `bash verify.sh`。

CI 配方：**树外构建**（`cp -r engine/dotnet "$RUNNER_TEMP/build"`）+ **门跑工作树**（有 `.git` ⇒ 语义模式）。
两条**已证伪**的变体（树内构建 / 导出快照当语料）写在 `.github/workflows/net-engine.yml` 的注释里，别再走。

## 5. 纪律清单（每条都有实测出处）

- **只读**：写面一律拒绝；引擎不写被测语料（判据：`readonly_invariant_probe.py`）。
- **EOL = LF**：真源侧（`core/text_hygiene.py`）的扫描面 = 「仓库件」单点判据（`core/paths.py::walk_repo_paths`：静态目录名 + `.gitignore` 覆盖面）——**被忽略的构建产物不进面**（2026-10-03 收口）；引擎探针侧仍按自己的豁免表判。把内容写到**未忽略**的树内路径仍会假红。
- **不在仓库树内构建**：构建输出指到树外。
- **包元数据只许影响包**：`Authors` / `Product` / `Description` 会经程序集属性改字节（作废已验产物）；要加就属**有意变更**（重发 dist + 重跑判据）。
- **辅助模块 / 夹具用 `_` 前缀**：跑批器与体检探针据此区分"探针"与"辅助件"。
- **本机配置不进包**：`probes/_paths.local.json` 只写本机 quirks（PATH 上的工具名优先）。
- **具名记录件由探针重算**：重算前先报备（属本仓高危闸门）。
