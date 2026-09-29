---
id: ADR-0005
title: 新增 .NET 引擎线（engine/dotnet/）作为只读判据的第二个实现
status: accepted
date: 2026-09-28
supersedes: —
superseded_by: —
evidence: [engine/dotnet/src/Nf.Engine/Nf.Engine.csproj, engine/dotnet/tools/nf-dotnet/nf-dotnet.csproj, .github/workflows/net-engine.yml, protocol/combo_certificates.json, protocol/conformance_report.json]
---

## 背景

1. **现有门禁是 bash + Python 单实现**：`verify.sh`（39 道 check）与 `desktop/src/core` 的判据逻辑同源同语言，任何隐含语义都只被验证一次；仓内自陈的真实约束是「Bus Factor 1」，而「第二个实现」一直是缺口（`STRATEGY` P0 他证互操作的内核）。
2. **判据面已有机器可读产物可对账**：组合证书（17 条，含极限 111 包 / 235 模块）、两套回执（51 + 3）、透明链（51 节）、断言表（14 条）、决策门禁（ADR 在册）、馆藏门、建模三件、知识签名——共同构成「同输入必得同输出」的可验证面。
3. **平台面**：仓库门禁依赖 bash（Windows 侧需 MSYS）；而 `nf serve`（MCP）与只读工具面已有外部消费者形态，值得有第二个可分发实现。

## 决策

新增 **.NET 引擎线**，定位为**只读判据的第二个实现**，与 Python 侧**并列**（不替代、不写盘）：

1. **落位**：`engine/dotnet/src/Nf.Engine`（引擎库）+ `engine/dotnet/tools/nf-dotnet`（CLI）+ `engine/dotnet/tools/nfparity`（对账工具）+ `engine/dotnet/probes`（判据探针）+ `.github/workflows/net-engine.yml`（CI）。
2. **职责边界**：只读判据面（解析 / 组合求解与证书 / 回执与透明链 / 广度证明 / 断言 / 决策 / 认知 / 馆藏 / 建模 / 知识签名 / 性能基线）+ MCP stdio 服务；**写面（`--write` 类）不实现**——真源仍只在 Python 侧，避免两套真源。
3. **依赖纪律**：**BCL-only**（无 NuGet 依赖）+ 显式 invariant culture；越出解析子集一律 fail-closed。
4. **等价判据**：同一输入下与 Python 侧**逐字节一致**（机器面 `--json` 与 MCP `tools/call` 文本），**错误面亦一致**；`nfparity` 与对账表为常驻验收件。
5. **不新增 check 序号**（ADR-0002）：本线不改变 `verify.sh` 基线，只作为**独立的第二道只读门**存在。
6. **只读不变量**：写面一律拒绝并**零写盘**（判据：读面母树整树指纹零改动 · 写面 20 条全拒且不偷写 · 显式落盘只落调用者给的路径）。
7. **可复现**：构建期 `PathMap` 归一 ⇒ 同一 RID 异地重建逐字节全等；机器面输出不嵌运行期临时路径。

## 后果

**正面**

- 判据获得**跨语言、跨运行时**的复核：**183 面**机器面 + MCP 同名工具已实测逐字节一致；任一侧语义漂移立刻显形。
- 外部消费端（MCP 客户端 / .NET 生态）可**只读装载**同一套判据，且不必装 bash / Python：聚合门与 227 例自检可在**无 Python** 环境跑通（已实测）。
- 交付面补齐：自包含产物（win/linux）+ 标准 .NET 工具包 + 引擎库包（零依赖，第三方只引包即可复算）+ CI 工作流。

**代价与风险**

- 新增一条**并行实现**，长期存在漂移成本 → 以对账表 + `nfparity` + 42 条判据探针作为常驻门（漂移即红）。
- 引擎覆盖面**不完整**：对照 `verify.sh` 39 道为 **覆盖 32 / 不适用 6（有对应物）/ 范围外 1**；**不得对外宣称「可替代 verify.sh」**。
- 已知未覆盖/边界项须显式在场：`purity-clean`（源码 AST linter 面，范围外）· ssh-sig 真实验签（需外部工具链）· 端点类适配器不发起外呼 · linux-x64 **运行**冒烟待有 Linux 主机时补（CI 上跑 ubuntu job 即为该冒烟）。

## 落地前置（并入时须完成）

1. 目录入库（`engine/dotnet/**`）+ `.github/workflows/net-engine.yml`；actions 版本按仓库纪律**钉 commit SHA**（本 workflow 只复用仓库既有的 `actions/checkout` 钉法，不新增未钉依赖）。
2. `README` / `CONTRIBUTING` 增一句式说明：本线为**只读第二实现**，真源仍在 Python 侧。
3. 若纳入 CI 必跑项，须声明对 `verify.sh` 基线的**无影响**（不新增 check 序号）。
4. 本 ADR 转 `accepted` 时，按冻结链顺序重签：内容 → `nf conformance --write` → `nf approve` → `nf receipts --write`（PO-0001 事故教训）。
