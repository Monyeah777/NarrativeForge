# NF 零依赖复算样例 v1（外部侧）

> 这是**备件**：给「不在 NF 项目里、也不跑 NF 代码」的一方，用 .NET 引擎独立复算 NF 的组合证书并自验摘要。
> 口径源：`scenario.json`（唯一出处）· 交付形态 f111 · 语料钉在真源 `b1f9a28`（`nf-snap-h8`）。
> **不做宣称**：样例只证明「在这份契约语料上，外部侧可独立复算出同一 digest」；不构成对外质量背书（外部证据线仍由作者闸门控制）。

## 1. 前提

- 一份 NF 契约语料（`git archive <commit>` 解包即可，含 `protocol/` · `community/` · `04_模块库/`）
- 引擎自包含产物（`dist/nf-dotnet-win-x64-f111-2026-09-28/nf-dotnet.exe`；**不需要 .NET 运行时、不需要 Python**）

## 2. 三步复算

```powershell
$Kit = '<本样例所在目录>'
pwsh -NoProfile -File "$Kit\run-recompute.ps1" -Root <语料根> -Cli <引擎 exe> -Scenario small
pwsh -NoProfile -File "$Kit\run-recompute.ps1" -Root <语料根> -Cli <引擎 exe> -Scenario limit
pwsh -NoProfile -File "$Kit\run-recompute.ps1" -Root <语料根> -Cli <引擎 exe> -Scenario all   # 17 条证书全复算
```

产物落 `out/`：`certificate_<index>.json`（引擎原始输出）· `verify_all.json`（17 条复算汇总）· `receipt.json`（绑定：命令行 + 语料指纹 + 输出 sha256 + 期望/实得 digest + 判定）。

## 3. 判定与退出码

| 退出码 | 含义 |
|---|---|
| `0` | **PASS**：语料指纹 = 钉定值，且复算 digest / 模块数 / legal 与 `scenario.json` 逐项相符 |
| `3` | **语料漂移**：digest 相符但指纹 ≠ 钉定值（真源前移过；非引擎问题，须按复基线处置） |
| `1` | **FAIL**：digest 或字段不符（实现分歧） |

## 4. 外部侧自验（不信任本文档的写法）

```powershell
# ① 复算结果与盘上证书逐字节比（台账口径：盘上 digest 不含 label/note）
# ② 两遍运行，receipt.json 必须逐字节相同（确定性）
```

`receipt.json` 是**确定性产物**（不含时间戳、不含本机绝对路径），**同一平台**内可直接做字节比对。

跨平台口径（如实标注）：引擎 stdout 的换行风格是**平台原生**——Windows 为 CRLF、Linux 为 LF（与真源 Python 文本模式一致）。故：

- **摘要不受影响**：证书/回执 digest 按**规范串**计算（与换行无关），跨平台同值；
- **捕获的 stdout 字节受影响**：`out/*.json` 与 `receipt.stdout_newline` / `output_sha256` 只保证**同平台**可比（receipt 里带 `platform` 字段做归属）。

## 5. 边界（如实登记）

| 面 | 状态 |
|---|---|
| Windows / PowerShell 7 | **PASS**（本机实测，见 `out/receipt.json` 判定） |
| Linux / POSIX（`run-recompute.sh`） | **UNKNOWN**——本机无 Linux 运行环境（WSL 无发行版、无 docker/podman）；脚本与 `.ps1` 同参数同判定，**未执行即不标 PASS** |
| 语料非 `b1f9a28` 的检出版本 | 退出码 `3`（语料漂移），需重钉期望值（复基线） |
| 跨平台 stdout 字节 | 同平台可比；跨平台换行风格不同（receipt 已记 `platform` / `stdout_newline`） |
| 写面 | 不涉及：全部命令为只读复算，产物只落本样例的 `out/` |
