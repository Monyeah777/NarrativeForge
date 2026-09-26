---
id: AUD-0020
title: 域包自由组合引擎（任意 n 元 × 任意组件）：五不变量 + 传递闭包 + 广度证明（5671 两两全合法）+ 可复算证书
date: 2026-09-23
scope: 作者目标「将所有域包达到任意几个域包可自由任意组合，包内组件（协议/管线/模块/资产）可自由任意组合，理论广度无限组合，深度质量保证，产出组合可机验」——本件记录：组合引擎与五不变量、传递闭包、广度证明实测、证书与门禁、以及引擎抓出并修掉的既有组合包真实缺口
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/pack_combo.py:4c767ec786b38313b8ea3ec7e7c8818f0748bf734b04fa269d33d8135657b5f4
  - desktop/src/core/quality_depth_scan.py:ef33e0c52da8370134c34da56943f3d9188c0f3212727a4b4eea5a80f0732fb1
  - desktop/src/core/doc_hygiene.py:2b0acc2498874f2d37ca7d7e51b8f89d17c1bd5171e9532e75667c58d9d5f5fb
  - scripts/nf.py:383f8301514e05534ec99e0f6a66d0fe7963785938cbb17b0c88e6ee9aaf3625
  - protocol/data_contracts.json:44e394ce811c953bed5f462328544f3b26cda2ac5f48bd986e884daea5b2d588
  - docs/combos.md:4d25fe6d366687213df7090badd52b815bdf07f774df856e598d7cf8a1d130de
  - desktop/tests/test_pack_combo.py:5da27fbf17a0c6d70d7d30d74286b9d6f3282561979ebb15b1118eb0f3f0cc5d
  - community/校园西幻轻混组合包/protocol.yaml:093cc817ae089981b7cfe4aaf57ec7f5d2374455bb63fc8b7af06dc2d29a02a3
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 8 件（组合引擎、聚合扫描、文档卫生表、CLI、数据契约登记、公开文档、单测、被修的既有组合包声明）；**不含派生物**（`protocol/combo_certificates.json` 由引擎可复算，是投影而非源）。

## 一、内部差距（开工依据）

1. 组合能力此前只有**一个手工战例**（校园西幻轻混组合包：2 模块 + 2 条 references），
   没有任何**引擎**：任取两个域包同装会怎样，仓库里答不出来。
2. 100 个域包全部在 P40/P60 挂 default —— 组合时的**层位堆叠**规则、**事件闭包**、
   **依赖闭包**、**资产借阅**四条都没有判据，也没有产出面。
3. 「广度」当时是**不可证**的声称；没有任何机制能说明「任意组合都成立」。

## 二、组合引擎与五不变量（从零构建）

`core/pack_combo.py` + `nf combine plan|breadth|verify`：

| # | 不变量 | 判据字段 |
|---|---|---|
| 1 | 模块唯一可定位 | `module_missing_contract` 必须为空 |
| 2 | 依赖闭合 | `dependency_closure.dangling` 必须为空（inputs ⊆ 组合内 ∪ 官方核心 13 件） |
| 3 | 事件闭合 | `event_closure.unbridged` 必须为空（核心模块的 publish 计入；无人发布者记 `events_unpublished`） |
| 4 | 层位堆叠确定 | `layer_stacks` 按**规范包序 → 模块 id**，与调用者给序无关 |
| 5 | 资产可寻址 | `assets_borrowed` 每条须在源包 provenance 台账，`assets_unresolved` 为空 |

**传递闭包**（本波的关键设计）：`references` 借入的模块会**递归**拉入其 `inputs` 与所需事件的
发布方，逐步记 `why`（如「事件 confession_event 需要发布方（M91 订阅）」）。

## 三、广度证明（不靠枚举）

| 规模 | 数量 | 合法 | 说明 |
|---|---|---|---|
| 两两（全集） | 5671 | **5671** | C(107,2) 穷举 |
| 三元（定种子抽样） | 400 | **400** | seed=20260923 |
| 四元（抽样） | 200 | **200** | 同上 |
| 极限（全 107 包同装） | 1 | **合法** | 235 模块 / 0 悬挂 / 0 未桥 |

单次组合求解 < 2 ms（画像 + 索引进程级缓存），check32 `combos` 子扫描（证书复算 + 广度）≈ 3 s。

## 四、可机验产出（证书）

`protocol/combo_certificates.json` **13 条声明证书**（极限 1 / 跨段对 3 / 三元 3 / 四元 2 /
先例 2 / 跨段对 1 / 组件级混搭 1）。机检三层：① 过 `CERT_SCHEMA`（自家 JSON Schema 子集）；
② 按 `packs + extra_modules` **重算**逐字段比对（T4，含 digest）；③ 广度不变量全成立。
组件级战例：只取三个包的 P40 模块 + 一个跨包只读资产（`量化金融域包:QUANT_METRICS`）→ 合法。

## 五、五条不变量在真实数据上抓出的问题（引擎价值）

1. **既有组合包声明与事实不一致**：轻混包模块订阅 `confession_event` / `npc_action` /
   `relationship_change` / `production_output`，但 `references` 只声明了 M55 与 M17——
   发布方 M43 / M22 / M40 未在册。修法：补 3 条 references（**只读借阅**）+ 包版本
   `1.0.0 → 1.1.0`（additive）+ 02 §9.6 四步迁移记录（check30）。
2. **核心发布事件被漏算**：首版引擎未把「官方核心 13 件随任意组合装载」计入事件闭包，
   导致 `chaos_event` / `minute_tick` 等被误报未桥；修法：核心发布集入闭包（事件面 0 误报）。
3. **层栈顺序非规范**：按调用者给序排序 → 同一组合两次给序不同则摘要不同（T4 假失败）；
   修法：层栈一律按规范包序，`digest` 与给序无关。
4. **旧包 module_id_range 解析漏项**：校园/西幻用「行式裸号 + 行尾注释」写法，首版正则只认
   全限定带引号形式 → 模块集漏到 1 个；修法：两种写法并集 + 容忍注释。
5. **广度性能**：首版每次组合都重解析 235 个模块文档 → 广度跑 174 s；修法：画像/契约/索引
   进程级缓存 → **3.2 s**（含 5671 两两）。
6. **「同源多引用」被两处独立实现误判成环**：轻混包补 3 条校园引用后，
   `core/market_analyzer.dependencies` 与 `verify.sh` check15 ② 各自把「同一源包的多条
   references」当成多条边 → 报「依赖闭包成环」。修法：两处都按**包级依赖去重**
   （同源多引 = 一条边），并加回归测试 `test_multi_reference_same_source_is_one_edge`。
7. **投影测试硬编码引用条数**（`== 2`）：引用条数会随真实依赖增长 → 改为从声明件推导
   （`≥2` 且双源一致），与仓库既有「硬编码计数即误报」的修法同源。
8. **引用写法须类别限定**：校园包内 `情感:M22` 与官方 `事件:M22` 重号，references 里写裸
   `M22` 被 check15 ① 判「不在源包 modules[] 在列」→ 改 `情感:M22`（与源包声明一致）。

## 六、边界与不宣称

- 广度证明 = **两两全集 + 定种子抽样**，不是 2^107 全枚举；抽样覆盖三类交叉面（层位 / 事件 / 依赖），
  不宣称「已证明所有高阶组合」。
- 组合**不改源包**：借阅只读、模块不改号、资产不复制；组合不产生新内容资产。
- 证书只证明**结构合法与可复算**，不证明组合出的内容质量。
