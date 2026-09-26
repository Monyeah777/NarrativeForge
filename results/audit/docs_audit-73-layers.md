---
id: AUD-0025
title: 抽象阶梯 v2 落地 —— 两轴 + 纵切 + 适应度函数（契约/资产/引擎/出口 × 入口面 × 验证纵切）
date: 2026-09-26
scope: 作者指令「对标顶尖架构设计再改一版」。把 NF 的分层从「混装的梯子」收成两轴 + 纵切，并落成有判据的协议件：真源 protocol/LAYERS.json + 语义判据 core/layer_model.py（并入 check27 R7）+ 生成投影 docs/layers.md + ADR-0004。外部只作机制借鉴（多视图描述 / 稳定依赖与依赖倒置 / 适应度函数 / 单一真源+生成投影 / ADR / 退役治理），开工依据全部来自仓库内部差距实证（见正文），不作立项理由或质量背书（STRATEGY §3.2/§3.3）。
verdict: pass
auditor: 本轮执行者
subjects:
  - protocol/LAYERS.json:bec48abcec388184847b424c14b4a1bbea0a7138e76a319963b7f86a6079c37c
  - desktop/src/core/layer_model.py:44de798ee24a97e569ad6ec72f1f12932b6971b54c5bac4433c4e7fed31ac686
  - desktop/tests/test_layer_model.py:e224d782a0f00daf345702bfe27a50563987233017f3dc0528af41b0f957855f
  - desktop/src/core/purity_scan.py:223ccbb2fc52c4a15362e1eff06b97341fa00de2094c97f93409d5bbadcb676a
  - desktop/tests/test_purity_scan.py:487bc7719509a312779afaf1474002b0fc0e0acf85f36b7628bf2975b008191b
  - scripts/nf.py:3943f407624fb9df03ae090a4f1b86f46e9d26192fcf4179dee02cd2fc5cdb40
  - verify.sh:8fbc94910bb6dda962e5e5996e443844608b3dfc3c05b849eda28225939886e0
  - docs/layers.md:c16bc46c91dbcf1a1d96cce4ff616d4cf6dbc7ac0952831c1576d9447e934534
  - docs/L3_FROZEN.md:9dad824e749aac75ee4cf583adb48d0ede9c02a0a717ff43d314cbbfcb3cf3af
  - protocol/assertions.json:b2dae0ac8dc5fc76df5b182f629f8857ca68dee5e052d055fed15b86a05f5102
  - protocol/data_contracts.json:44e394ce811c953bed5f462328544f3b26cda2ac5f48bd986e884daea5b2d588
  - protocol/normative.json:3ea1e37d1879cee532b930e83ba3029fbc171efe99606fd42bc775f0968b84a5
  - protocol/glossary.json:4561ddb5a221f8fc5beca4cfcca07580b3ea4dd403eb23434549a8eaa8409a60
  - desktop/src/core/receipts.py:d0149187ad077db555fac3a2877f3ddc846cb5544125cff7fcfc48ae9ce7f9ee
  - desktop/src/core/doc_hygiene.py:2b0acc2498874f2d37ca7d7e51b8f89d17c1bd5171e9532e75667c58d9d5f5fb
  - decisions/ADR-0004-抽象阶梯两轴与纵切.md:9881ef04d900dd8d9f44748d7e4477ca32c8914abc717fbccb7b7072c6167674
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物：`protocol/RECEIPTS.json`、`protocol/conformance_report.json`、
> `protocol/generated/*`、`results/interop/*`、`decisions/INDEX.md` 均为可复算投影或每次重签即变，
> 按既有口径不入审计绑定（分别由 check35 / check31 / check33 / check36 自证）。

## 一、内部差距（开工依据）

1. **分层是文档不是架构**：L3 端壳退役前**零判据**——一个「阶」可以整体消失而无任何 check 察觉，
   能力重分派只能事后靠 check39 兜住。阶梯若无适应度函数，必然复现同类事故。
2. **角色与物混装**：此前「终端执行层 / 协议层 / 资产层 / AI 装配」把**谁在动**与**被加工的物**
   放进同一根梯子，于是出现「终端在最底、AI 在顶」的错位（本轮对话实证）。
3. **阶之间没有接口面**：`protocol/module_signatures.json` 已冻结 248 个**模块**边界，但
   「契约/资产/引擎/出口」之间没有接口面声明——改实现与改接口无法区分。
4. **文档必然漂移**：验证卡册实测漂移（卡数 37/38/39、行数 1797/2409，生成器未随仓库分发）——
   分层表若手写，会以同样方式腐烂。
5. **退役无规程**：L3 退役是临时动作（临场分派 + 事后补判据），没有「能力重分派 → 入口补齐 →
   判据改判 + 记录」的可复用流程。

## 二、交付

| 面 | 落点 |
|---|---|
| 真源 | `protocol/LAYERS.json`（nf-layers/1）：四阶 ×（真源面/接口面/实现面/变更档/judged_by/status）+ 资产五子级 + 入口面 + 验证纵切 + derived 豁免名单 + 退役规程 |
| 语义判据 | `desktop/src/core/layer_model.py` 的 L1–L10（真源在位 / 归属互斥 / 接口子集 / 依赖向下无环 / 入口非真源 / 引擎不反向 import 入口 / 退役阶不被依赖 / 判据可解析 / 豁免诚实 / 生成区==实时渲染） |
| 门禁接线 | 纯度体检 check27 新增 **R7**（把阶梯 issues 汇入既有纯度报告）——**不新增 check 序号**（ADR-0002），基线仍 v2.29 · check1-39 · PASS=68 |
| 形状类断言 | `protocol/assertions.json` 增 3 条（layers-declaration-in-place / layers-generated-region / layers-no-abs-path），11 → 14 条（kind 仍封闭四类，ADR-0003） |
| 生成投影 | `docs/layers.md` 阶梯表进 `nf:layers` 生成区，`nf layers --write` 渲染（L10 断言逐字一致） |
| CLI | `nf layers` / `--json` / `--verify` / `--write` |
| 决策 | `decisions/ADR-0004-抽象阶梯两轴与纵切.md`（accepted，已入回执锚定），`decisions/INDEX.md` 重投影 |
| 术语 | `protocol/glossary.json` 增 **抽象阶梯**、**验证纵切**（逐字命中真源与使用面） |
| 登记 | `protocol/normative.json` 收 LAYERS.json；`protocol/data_contracts.json` 29 → 30 件（quality_rule=check27）；`protocol/RECEIPTS.json` 49 → 51 件（+LAYERS.json +ADR-0004） |
| 单元测试 | `test_layer_model.py` 21 例（L1–L10 各一变异样本 + 真仓库零 issue + 渲染幂等 + LF 落盘 + CLI 面）；`test_purity_scan.py` 增 R7 接线与「无阶梯件不误伤」2 例 |

## 三、验收证据（本机实测）

- `bash verify.sh` → **PASS=68 · WARN=0 · FAIL=0**，`check` 数仍为 **39**（证明「并入不涨号」）。
- `nf layers --verify` → 通过（阶 4 · 资产子级 5 · 入口面 4 · 纵切件 6 · 规则 10）。
- 真实面规模（防空面假绿）：契约 52 件 · 资产 2218 件 · 引擎 255 件 · 出口 26 件；派生物豁免 9 件。
- `nf conformance` → **conformant 27/27**；`nf decisions verify` → 4 条 accepted 全一致；
  `nf receipts` → 51 件根一致；`nf approve --verify` 有效；`nf interop --check` 逐字节一致；
  `nf stats --check` 一致；`purity_scan` 0 issue；`text_hygiene` 0 issue。
- 变异捕获力：L1–L10 每条规则各有一个违规样本被单测钉住（含「接口面超出真源面」「退役阶被依赖」
  「生成区被手改」三类最容易漏的形态）。

## 四、遗留与设计偏差

1. **阶归属判据是有界的**：只判阶梯自己声明的真源面，不给全树逐文件贴标签——全树归属是另一个量级的
   承诺，未纳入本波（避免造没人消费的重台账）。
2. **未新增违规基线台账**：阶梯是新增面、无存量违规；个别例外如需挂账，复用纯度体检既有的
   `IMPORT_RESIDUE` 机制（按需装配：不产无消费者的件）。
3. **旧审计摘要重绑**：本波改动触及既有审计的被审对象，按仓库既有实践（commit `ba1cb08`）
   重绑 digest 使审计面自洽——**每轮改动后重绑一次**（含修 `nf` 的 stderr 编码缺陷、以及
   check27/卡册的描述面补齐），三轮共 **63 条 subject 记录**；重绑只校准摘要、不重写旧结论，
   本波实际改动面由本件承担记录责任。
4. **本轮不做**：`desktop/` 目录去端壳化改名（独立一波需作者立项）；`docs/L3_FROZEN.md` 退役事实改写
   （只加互链，不改写历史）；给阶梯开独立 check 序号（遵 ADR-0002）。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | L1–L10 十条语义判据 + 3 条形状类断言 + 21 例单测变异覆盖；基线不涨号仍全绿 |
| 动态可执行 | ↑ | `nf layers --verify` 与 check27 同源可复跑；生成区由真源渲染，手改即红 |
| 架构纯度 | ↑↑ | 角色与物分离、跨阶只依接口面、依赖向下无环、入口非真源——纯度为第一次有「阶」维度 |
| 资产密度 | → | 不新增内容资产（本波是架构面） |
| 文档可执行性 | ↑ | `docs/layers.md` 读到即能跑；阶梯表为投影，双语入口与四型清单同步登记 |
