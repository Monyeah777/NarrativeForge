---
id: AUD-0012
title: 构建回路（决策模型挑活 → 生成式 worker 落笔 → 门禁验收）——「让模型替我干活构建 NF」的落地形态
date: 2026-09-22
scope: 作者澄清「让这些模型替我干活，来构建 NF」——把决策层从「NF 运行时的决策模块」改判为「构建 NF 过程里的决策者」；本件只对回路机制、工单契约与实测数据建档（不含任何真实模型推理结果）
verdict: pass
auditor: 本轮执行者
subjects:
  - verify.sh:ab1369c65279cd9061d500eb7af5d0685ece0e6a7b15eda655793a675c1ffcee
  - protocol/decision_layer.json:8429b9ccd1a9ce690f581de96d924034453027eb6c752ac204a25829cdd5e88f
  - desktop/src/core/workloop.py:25df02cccb732a1a06b71e7ca55ddf82cb136bfb273f9488e184fb47c0a58d8d
  - desktop/src/core/decision_layer.py:44f194ec3f2803a35669f6bdec179685bbf6c42fe43856bf11d8fae469f6e80f
  - scripts/nf.py:480a8614a2b70ed66829d21fc714f2c612ca061ae222da938d0d655f1f35202b
  - desktop/tests/test_decision_layer.py:40521a5b641df92f0c4b4f28386c2a4118e5bee44ae050f924a3206fc74d3bc9
  - docs/decision-layer.md:85ac1dc81c879cf98a15a0c089ba1c825c67649fe3ee431a9172336c09b04314
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 本波承重件七件（门禁 / 决策层声明（含 workloop 块）/ 回路模块 / 决策端口 / CLI / 单测 / 对外文档）；任一件再改，本件结论即失效须重审。
> **口径**：subjects 不含派生物（`protocol/RECEIPTS.json`、`protocol/generated/*` 等重签即变，由 check31/check33/check35 自证）。

## 一、判定改口（承接 AUD-0011）

AUD-0011 把 Laya / Open-Jev 接成 **NF 运行时**的决策端口；作者 2026-09-22 澄清真意是
**让模型替人干构建 NF 的活**——于是本波把定位改判为**构建过程的决策者**，并保留运行时段口
（两者共用同一 `core/decision_layer.py`，不是两套代码）。

**能力边界（决定分工，不可含糊）**：Laya 是编码器分类（ModernBERT-large + 决策头）、
Open-Jev 是非自回归 + 决策头 —— **都不会写代码或正文**。因此回路三段分工：

```
决策模型：挑下一个工作项 / 判改动面风险 / 定「能否在不碰回执锚定件的条件下完成」
   ↓（工单：目标 + 证据 + 落点 + 完成判据 + 验收命令）
生成式 worker（人 / Codex / 生成式模型）：按工单落笔
   ↓
NF 门禁：verify.sh 全绿 + nf conformance conformant（唯一验收口）
```

## 二、本波交付

| 类 | 件 | 要点 |
|---|---|---|
| 模块 | `desktop/src/core/workloop.py` | 待办真源 = **公开声明件**（`type_backlog.json` 104 未定型字段 + `pipeline_advisory.json` 102 advisory）；`state()` 快照 / `items()` 工作项 / `questions()` 类型化提问 / `plan()` 出工单 / `write_order()`+`close()` 内部档案记档 / `scan()` 回路体检 |
| 提问契约 | 每轮 = 1×`choice`（挑活）+ N×`score`（风险：低/中/高）+ N×`noul`（能否安全做） | **请求自带候选证据**（id/title/detail/where）——这类模型只对给定 state 作答，不给候选正文它们无从判断（本波自查修正过一次） |
| 工单契约 | `nf-workorder/1` | 必带 `goal/evidence/where/done_when/accept/worker_role`；`accept` 固定为门禁命令；`decision.note` 明写「决策层只给选择与概率；**它不写内容**」 |
| 入口 | `nf workloop` | `--list`（候选面）/ 默认出工单 / `--write`（落 `.rivet/private_archive/work_orders/`）/ `--close --outcome --gate --note`（收口记档） |
| 四条不可协商 | `protocol/decision_layer.json: workloop.non_negotiables` | ① 决策层不生成内容；② 工单只落内部档案（计划类产品内部消化）；③ 落笔方必须是 worker；④ 验收只认门禁 |
| 门禁 | check33 第 16 面 | 待办真源非空且 id 唯一 / 工作项六字段齐 / 问题形状合规（复用 decision_layer 判据）/ **stub 工单确定性** / 所选在候选集内 / 工单目录在内部档案前缀下 |
| 测试 | `test_decision_layer.py` +6 例（合计 18） | 回路体检零 issue / 工作项来自公开声明 / 工单确定性与验收命令 / 工单只落内部档案 + 收口 / 适配器不可用即 abstained / 空真源 → `empty` |
| 文档 | `docs/decision-layer.md` 增「构建回路」节 | 含分工图、命令、四条不可协商、实测数据 |

## 三、实测（本仓 2026-09-22）

| 判据 | 结果 |
|---|---|
| `nf workloop --list` | 待办 **206 项**在册（未定型字段 104 + advisory 102） |
| `nf workloop --top 5` | 工单成形：`WO-c9618c9f6e8a` · 所选 `TB-001:beat_tick.buffered` · `gate_safe=1.00` · `risk_level=2.00`（stub `calibrated=false`，只是排序信号） |
| 确定性 | 同输入两次工单**逐字段一致** |
| 落点纪律 | 工单/收口件只落 `.rivet/private_archive/work_orders/`（公开仓零新增过程件） |
| fail-closed | `--adapter systemone-http` 缺 endpoint → 回路 `abstained` + reason |
| `bash verify.sh` | PASS=61 · WARN=0 · FAIL=0（check1-37 不变；回路并入 check33 第 16 面） |

## 四、遗留与不宣称

1. **仍未拉取/运行真实模型**：`pulled=false` 不变 —— 本波验证的是**回路机制**（挑活 → 工单 → 验收），
   不是模型质量；真实模型的挑选结果属外部运行事实，须拉取后另立实证。
2. **stub 的风险评估无信号**（均匀分布）：它只按关键词计分，`calibrated=false` 已标注；
   要真判断风险必须接真模型（`--adapter systemone-http`）或换 `openai-json`（同样 `calibrated=false`）。
3. **回路不自动落笔**：本波按 `STRATEGY §四`（计划内部消化）坚持"工单只落内部档案"，
   公开仓只收**结果形态**（代码 + 收口注记 + audit）。
4. **待办真源的口径**：回路只认公开声明件里的待办（type_backlog / pipeline_advisory）；
   其他缺口（如外部输入队列）若需入回路，须先成为**声明件**（不新造私有队列）。

## 五、首轮回路实战（落笔记录 · 2026-09-22）

回路第一次**真关环**（决策层挑活 → 生成式 worker 落笔 → 门禁验收 → 收口）：

| 段 | 事实 |
|---|---|
| 决策 | `WO-c9618c9f6e8a`，所选 `TB-001:beat_tick.buffered`（`gate_safe=1.00`，stub `calibrated=false`） |
| 落笔（worker = 本轮执行者） | 查明根因：该字段无从定型**不是**缺证据，而是 M94 正文用 `produce:`，而收割器只认 `event:`/`name:`/`publish:` → 在 M94 §4 补**机读事件契约**（`event: beat_tick` + `payload: { tick: number, day: number, minute: number, origin: string, buffered: boolean }` + 语义注记，全部与 §3 同源） |
| 机制反应 | `nf module types --harvest --write` 收窄 **2 字段**（`origin→string`、`buffered→boolean`，note 标「正文 payload 收割，证据可溯」）；事件载荷类型覆盖 **42.9% → 44.0%**；`type_backlog` **104 → 102** 项 |
| 连带精化 | `nf module types --write` 按同一证据链回溯补标 **15 件**模块 `io_types`：**35.4% → 41.7%**（91/218 字段） |
| 门禁反应 | `module-signature` 报 15 件边界漂移（类型精化 = 接口面变化）→ 按设计**显式重冻结** `protocol/module_signatures.json`（48 模块）；旧审计（AUD-0002 等）摘要重绑 |
| 验收 | `bash verify.sh` **PASS=61 · WARN=0 · FAIL=0**；`nf conformance` **27/27 conformant**；unittest **981 例全绿** |
| 收口 | `.rivet/private_archive/work_orders/WO-c9618c9f6e8a.close.json`（outcome=landed · gate=PASS=61 · 27/27） |
| 下一步 | 回路随即产出下一张工单 `WO-c04a3bb64192`（`campus_anonymous_gift.item`）——待办真源变化后候选面自动前移 |

**方法论收获（写进机制而非日记）**：① 类型缺口有三种，只有第三种需要「补内容」——**缺证据**（正文没写）、
**证据不可读**（写法不在收割器语法内，如本例的 `produce:`）、**证据冲突**（正文与注册表不一致，只报告不改）；
② 类型精化会触发边界签名重签，这是**设计意图**（接口面变了就要留痕），不是噪声——本波按提示显式重冻结，
而非为省事放宽判据。
