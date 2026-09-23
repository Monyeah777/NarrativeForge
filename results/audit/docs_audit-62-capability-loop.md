---
id: AUD-0014
title: 决策模型驱动「扩展 / 深化 / 创新」——能力缺口候选池 + 真模型选 innovatie 项落地（决策面接入互操作导出）
date: 2026-09-22
scope: 作者指令「利用决策模型来进行 NF 项目内目前已有的功能的扩展深化创新等」——把能力缺口机械派生为第三类候选源，让真模型在 extend/deepen/innovate 三族里选择，并落笔其选定项；本件只记录可复现事实
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/workloop.py:25df02cccb732a1a06b71e7ca55ddf82cb136bfb273f9488e184fb47c0a58d8d
  - desktop/src/core/interop_export.py:1fc35ff29f0b7b0a95ae8fa150f8e05534a7e65bf821f6749d95491dcd1ab8a6
  - scripts/nf.py:3484f46ff1fcde7180a6c8fa5a46d8b406181782304140e820a26e83e5bdc54d
  - scripts/check_interop_schemas.py:6cae41b5247e8ea594b3825ff61bc3b9186caf21c170bc122d31861d30974c74
  - docs/interop.md:f884a0533ed89aae8c83a2a44da491afb334c083dc05051158ac3a91e88e4f5c
  - desktop/tests/test_interop_export.py:5d47f3aa9c894c36360652a45d8ae5ac3dcf072402a10e72126b20f520aaae98
  - desktop/tests/test_decision_layer.py:40521a5b641df92f0c4b4f28386c2a4118e5bee44ae050f924a3206fc74d3bc9
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 七件（回路模块 / 导出模块 / CLI / 外部校验工具 / 对外文档 / 两份单测）。
> **口径**：subjects **不含派生物**——`results/interop/*.json` 每次重生成都会变（本次 AUD-0014 初稿
> 曾误把它列作被审对象并因此假失效，已按既有口径移除）；派生物由 check33 入仓面逐字节断言自证。

## 一、把「扩展/深化/创新」变成**可核验的候选**（不靠想象）

新增第三种待办源 `capability-gaps`（`core/workloop.py`），三族候选**全部机械派生**：

| 族 | 判据（机械派生） | 本波实测候选 |
|---|---|---|
| **extend** | 已有只读面未接 MCP（CLI 只读治理面 24 个 vs MCP 工具 10 个） | `CAP-EXTEND-MCP-READONLY`（19 个未接） |
| **deepen** | 同一事实两处声明却无一致性判据 | `CAP-DEEPEN-DECL-CONSISTENCY`（实测抓到：CLI `--kind` 缺 `a2a`、`c2pa`） |
| **innovate** | 两个既有面之间尚未接线 | `CAP-INNOVATE-DECISION-INTEROP`（决策层 ⇄ 互操作导出未接） |

**关键设计**：候选**随状态自动撤单**——缺口被补掉，候选即消失（不是静态待办清单）。
本波实测：修掉 CLI 漏同步后 deepen 候选消失；决策面接好后 innovate 候选消失 → 池中只剩 extend 一条。

## 二、真模型的选择（Laya multilingual · 本地 HTTP）

`nf workloop --adapter systemone-http --source capability-gaps --top 3`（真模型跑在本地 8791）：

| 项 | 值 |
|---|---|
| 选定 | **`CAP-INNOVATE-DECISION-INTEROP`**（p=**0.5769**） |
| 风险 | 期望 **2.2065**（probs [0.006, 0.781, 0.213] → 押「中」） |
| gate_safe | **0.4464** —— 它正确识别出这项会碰回执锚定面（低） |

## 三、落笔（worker）与结果

1. **新增导出面 `decisions`（决策面）**：纯派生自 `protocol/decision_layer.json` + `results/audit/*.md`
   frontmatter → 外部工具链可读到「原语 / 应答契约 / 适配器（含是否在门禁路径、是否校准）/
   候选模型（含拉取状态与本地证据）/ 边界 / workloop 四条不可协商 / **公开裁决索引**（13 条）」；
   并**显式声明逐次工单不入公开面**（`STRATEGY §四` 计划内部消化，门禁判该声明在位）。
   互操作面 **11 → 12**；`results/interop/decisions.json` 入仓，check33 逐字节断言一致。
2. **顺带修掉侦察抓到的真 bug**：CLI `--kind` 手工列表**第二次**漏同步（缺 `a2a`、`c2pa`）→
   改为**派生自 `interop_export.KINDS`**（构造上消除该类错误）；并新增单测
   **逐个声明面实跑**（此前漏同步时 `--kind c2pa` 会直接报错）。
3. **外部校验口径登记**：`decisions` 面在 `check_interop_schemas` 记 `no-schema` 并写明理由
   （NF 自有形状，判据落本仓 check33）→ 外部核验面 **13 → 14**，全绿。

## 四、门禁与验收

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | **PASS=61 · WARN=0 · FAIL=0**（check1-37 不变；决策面并入既有 check33 入仓面断言） |
| `python -m unittest discover -s desktop/tests -q` | **983 例全绿**（+2：CLI 派生逐面实跑 / 决策面内部边界） |
| `nf conformance` | **27/27 conformant** |
| `scripts/check_interop_schemas.py --fetch` | **14 面**：官方 schema 通过 5 + 上游源码字面量通过 1 + `no-schema` 7 + `unavailable` 1 |
| 回路收口 | `.rivet/private_archive/work_orders/WO-140e9166e433.close.json`（landed · PASS=61 · 27/27） |
| 候选池自收敛 | capability-gaps 由 3 → **1**（deepen/innovate 因缺口已补而撤单） |

## 五、遗留与不宣称

1. **extend 未做**：`CAP-EXTEND-MCP-READONLY`（19 个只读治理面未接 MCP）仍在池中——真模型本轮选了 innovate，
   按"模型定选"的约定不擅自扩大；下一轮可让模型在 extend 上选（或缩小到最有价值的 3–5 个面）。
2. **MCP 工具面仍只读**：任何新增工具必须保持只读（无写路径），该约束由 check33 与 `protocol/mcp_package.json` 共同守着。
3. **不做质量宣称**：决策面只证明"决策能力与公开裁决可被外部读"，不宣称模型决策质量；
   模型的置信度与概率已随面导出，但校准性未在自有留出集复核。
4. **候选池判据是"机械派生"而非"创意生成"**：三族候选只反映**可核验缺口**；真正的创新仍由 worker 落笔，
   模型负责挑与排序（这也是本轮回路的固定分工）。
