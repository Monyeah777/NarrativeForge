---
id: AUD-0002
title: AI 系统域包 —— 概念前置依赖 / 闭包在 NF 现有机制下的三层判定（第 6 件社区包 / 第 2 个非叙事域）
date: 2026-09-20
scope: 命题 P（依赖闭包型知识域能否在 NF 现有机制下自然表达）——声明面 / 判据面 / 求值面三层实测 + 域包落地（包 / 管线 / 资产 / 登记三要件）+ 门禁收口
verdict: pass
auditor: 本轮执行者
subjects:
  - community/AI系统域包/protocol.yaml:13e26c88057987be2c5933a879d214ed75a1f33e5bc8da4371a36dbcc04bf7b1
  - community/AI系统域包/assets/CONCEPT_GRAPH.md:bd666baaf1bc9eccc0fbd319c37e922f2dc5abba09020003e74a1ec41c321894
  - community/AI系统域包/modules/M25_前置闭包求值.md:2118a73922271efa1c38095e6ff430b9cec1b34031d7c316306afbb45a0cd1bd
  - community/AI系统域包/modules/M26_装载序就绪门.md:fbc7c16d73989bdce1240748407497baf2e811f90337dc6da211645487663448
  - scripts/ai_domain_closure.py:d886f926456343326bbebbbe7a642e3f78414e00282b1600c2f25b3376b8a928
  - desktop/tests/test_ai_domain_closure.py:1f7e0e7749f2bf52edee010ff080b3b3a0ee23d4e51e5275eda7787a57c7fb02
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签（待作者回话后补写，补写即触发本件重审）。

## 一、命题 P（冻结原文，先写后做）

> 用第二个非叙事域验证——「**依赖闭包型知识域**」能否在 NF **现有机制**下自然表达。

两个出口都算本波成功：表达得了 → 域中立多一个战例（域包可跑、可装配、可出「前置缺失清单」）；表达不了 → 点名**哪一层**表达不了 + 最小可行补法，本波**不擅自扩 schema / 不擅自加 check**。

判定前先冻结的靶子：NF 现有 13 件官方核心里没有任何一件表达「概念前置依赖 / 闭包」；既有唯一的「闭包」判据在**模块依赖图**上（`02 §8.4` 规则② + `verify.sh check15 ②`：references 展开依赖闭包、叶节点 ⊆ 官方核心 13 件）——概念级前置闭包既无声明面、也无判据面。

## 二、三层判定（实测取代开工前预判）

| 层 | 问题 | 实测结论 | 证据 |
|---|---|---|---|
| **声明面** | 概念前置依赖在哪声明？ | **表达得了，但只落在内容面**：`contract.schema.json` 是封闭词表（`additionalProperties: false`），无「概念前置」专字段；本波把偏序声明为**资产机器可读块**（`CONCEPT_GRAPH` 的 ```yaml``` 围栏），键/边/层/溯源齐备，但**门禁不认识它**——它是内容，不是契约 | `community/AI系统域包/assets/CONCEPT_GRAPH.md` §3；`protocol/schema/contract.schema.json` properties 词表（无概念前置键） |
| **判据面** | 闭包闭合 / 无环 / 无悬空谁机检？ | **表达不了（真缺口）**：check 全绿与图质量无关——概念图落在资产里就是内容，`check15 ②` 只在**模块依赖图**上判闭包，`check26` 只扫机读契约的事件断链与挂载漂移，`check28` 只判 schema 形状；图有环 / 悬空 / 闭包算错，verify 一条都不会红。缺口点名为**判据面**，最小可行补法见 §六 | 本波以「注入环 / 悬空 / 缺溯源」三种负例实测：verify 不动（仍全绿），只有本包的只读求值器与单测能捕获（`desktop/tests/test_ai_domain_closure.py` NegativeCaseTest 7 例） |
| **求值面** | 给定目标概念，谁算闭包 + 缺失清单？ | **表达得了**：域包自带模块（AI系统:M25 求值 / AI系统:M26 排序与就绪门）在既有装配面内承载，事件与数据槽按 01 §1.1 词法与 check16 ④ 校验通过；三件产物可逐字节复现（见 §三） | `verify.sh` check14 ②-⑧ / check16 / check20 / check24 / check28 / check32 全绿；`nf events` 零缺口；`nf pipeline dryrun` P07 零 hard |

**命题结论**：NF 现有机制**可表达**依赖闭包型知识域——**求值面成立、声明面以内容形态成立、判据面留缺口**。域中立因此多一个战例（第 2 个非叙事域，第 6 件社区包），而缺口的层位被点名（判据面），不是笼统的「表达不了」。

## 三、三件产物（复现命令 + 输出样本）

求值器只读、确定性、零网络：`scripts/ai_domain_closure.py`（非 nf 子命令、非门禁、不改 Schema）。

```
$ python scripts/ai_domain_closure.py --target C22 --loaded C01,C07,C08,C10,C18
== AI 系统域 · 前置闭包求值（只读）==
资产：community/AI系统域包/assets/CONCEPT_GRAPH.md（v1.0 · 域 AI系统 · 节点 24 + 包外前置 1）
[1] 前置闭包 closure(C22)：13 个概念
    C00、C01、C07、C08、C09、C10、C11、C12、C15、C16、C18、C20、C22
[2] 缺失清单 missing(C22, L)：8 个概念
    C00、C09、C11、C12、C15、C16、C20、C22
[3] 合法装载序 load_order（toposort 确定性线性化）：24 个概念
    C01、C02、C03、C04、C05、C06、C07、C08、C09、C10、C11、C12、C13、C14、C15、C16、C17、C18、C19、C20、C21、C22、C23、C24
已装载集 L：5 个 · 就绪判定 readiness：未就绪
    其中包外前置（读者侧应已具备，不建模块）：C00
```

```
$ python scripts/ai_domain_closure.py --check            # 自检 9/9（含三种负例注入）
$ python scripts/ai_domain_closure.py --order cmu-mlsys  # 违反边 0（合法线性化）
$ python scripts/ai_domain_closure.py --order aisystem-module-order   # 违反边 5
```

## 四、验收判据与证据

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | PASS=61 · WARN=0 · FAIL=0（check1-37 常驻，**未新增 check、未改 Schema**） |
| `python -m unittest discover -s desktop/tests -q` | 全绿（基线 780 + 本波新增 16 例，无删除无跳过） |
| `python -m ruff check .` / `python -m compileall -q desktop/src scripts` | 零违规 |
| `nf pipeline dryrun --all` | 全仓 8 → **9 条管线**，零 hard 缺陷（P07 自身 0 hard / 10 advisory，advisory 全为官方核心跨包事件订阅，与既有管线同源） |
| `nf market --list` | 新包在列（AI系统域包 v1.0.0 · 2 模块 · 徽章 community） |
| `nf events` | 事件背书零缺口（39 事件：36 + 本波 3） |
| 三件产物 | §三 复现命令与输出样本（闭包 13 / 缺失 8 / 装载序 24） |
| 登记三要件 | protocol.yaml + `02 §8.5` 在册 + registry `protocols[]` 第 6 条（`nf register --apply`，check14 ⑦ 元素级自证） |

## 五、计划件数字的三处实测修正（不开工前改题，只如实改数）

1. **`closure(C22)` 记为 12 个概念 → 实测 13**：按资产 §4 定义 `closure(c) = {c} ∪ ⋃ closure(p)`，闭包**含目标自身**；实测闭包 = 13，其中「缺失 8」自洽（13 − 已装载 5 = 8）。开工件里的 12 是「不含自身」的误算，本件以可复现命令为准。
2. **目录序违反边记为 19 → 实测 5**：本件判据范围 = **被校验序列自身出现的概念之间的边**（`--order` 语义），故 `aisystem-module-order`（15 概念）实测违反边 5；开工件的 19 未附范围界定与命令，无法复现，本件不沿用未复现数字（**结论方向未变**：目录序不是前置序）。
3. **资产台账落位：`05_资产库` → 包内 `community/AI系统域包/assets/provenance.json`**：`nf asset add --root` 的根目录即台账目录，且实现层拒绝跨越台账根的路径（防逃逸），故跨根托管不可行；改落**包内货架**（`tier: community`），`nf asset verify` 实测闭合（台账 2 · 托管资产 3 · 孤儿头 0）。

## 六、本波新发现：运行时模块索引的**裸号歧义**（判据面第二个缺口）

**现象**（实测，非推演）：本波初稿按开工件拟用类内段编号 `AI系统:M01` / `AI系统:M02`，落盘后 `pipelinerun._module_files()` 的裸号键 `M01` / `M02` 被本包抢先占用（索引按 `setdefault` 先到先得，包目录名 `AI系统域包` 的排序在既有中文包之前），于是**西幻 P03 管线里的裸号引用 `M01, M02, M19` 解析到了本包模块**——既有管线的执行图被新包静默改写（advisory 台账可见：同层依赖序 2→1、跨包/外部事件 74→85）。

**影响**：跨包静默干扰。check14 ⑤b 只判**全限定 id**（`AI系统:Mxx`）唯一与类别在册，**不覆盖运行时的裸号索引**；check 族全绿也拦不住。

**本波处置**：选号规避——改用 `AI系统:M25` / `AI系统:M26`（类内段内唯一 + 不占用官方核心与既有社区包的裸号）；复测 `pipelinerun._module_files()` 的 `M01/M02` 已回到西幻包，advisory 台账的「同层依赖序」回到基线值 2（干扰消除，P07 自身 10 条 advisory 全为官方核心跨包事件订阅）。判据已写进 `02 §8.5` 选号判据行。

**最小可行补法（交作者裁决，本波不擅自动手）**：在既有 check 内（**不新增 check 序号**）给 check14 ⑤b 追加一条断言——「同一裸号（文件名 stem）在 community/*/modules 下不得出现于两个以上包」。它纯静态、零新 schema，与既有 ⑤b 同一段代码路径，属「门禁只增不减」的既有 check 内追加。

## 七、遗留（挂账，本波不做）

1. **概念图内部一致性的门禁化**：本波以只读求值器 + 单测（16 例，含 7 负例）覆盖，未进 verify check 族（守「不新增 check / 不改 Schema」）。缺口层位 = **判据面**，最小可行补法 = 「资产机器可读块 + 既有 check 内一条图健康度断言（无环 / 无悬空 / 边有溯源）」，交作者裁决。
2. **裸号歧义判据**（§六）未落 check，本波以选号规避。
3. **CS2023 KA 之间的前置表未取回**：`C00 → C01` 的边只标「课程序列」，未标「已证前置」（资产 §7 已记）。
4. **`nf assemble` 需求路由未登记本包**：本波未改核心路由表（`assemble_plan.DOMAIN_MAP`）——属消费侧入口扩展，与本波「不改核心代码」边界一致，留待作者裁量是否纳入下一波。
5. **`C24`（评测与可靠性）部分边为 `inferred`**：无直接来源，保留标注待复核。
6. **Windows 换行面：`nf register --apply` 会把 `registry.json` 落成 CRLF**（写盘未显式 `newline="\n"`）。本波实测：CRLF 工作副本下重签的协议回执，其 digest 只在 Windows 工作树成立——同一提交在 LF 检出（Linux/CI）会判「文件内容已变」。本波以**落盘后归一为 LF 再重签回执**处置（提交内 registry.json 为 LF，回执跨平台可复现）；机制侧修法（写盘统一 `newline="\n"`）属核心代码改动，留待作者裁决。

## 八、设计偏差（与开工件的差）

| # | 开工件写法 | 本波落地 | 原因 |
|---|---|---|---|
| 1 | 资产经 `05_资产库` 台账登记 | 包内 `assets/provenance.json`（tier community） | `nf asset add --root` 禁止跨根路径；包内货架是机制上唯一可行且更符合「一册一货架」的落位（§五.3） |
| 2 | 编号拟 `AI系统:M01` / `AI系统:M02` | `AI系统:M25` / `AI系统:M26` | 裸号歧义实测干扰既有管线（§六） |
| 3 | 「不新增命令」（`nf` 侧） | 未新增 nf 子命令——但**新增了一个只读求值脚本** `scripts/ai_domain_closure.py` | 开工件未指定求值器落位，而「命题 P 的判据」要求可复现命令 + 输出样本；落 `scripts/`（仓库既有工具架）而非 core（避免域内逻辑进机制层） |

## 九、五维自评

1. **静态可核验**：verify PASS=61 / WARN=0 / FAIL=0（未新增 check、未改 Schema）；conformance 契约全过、verdict=conformant。
2. **动态可执行**：域包可被门禁识别、可被 `nf market` 列出、可经 P07 装配（dryrun 零 hard）；三件产物逐字节可复现（两遍一致 + 16 例单测含 7 负例）。
3. **架构纯度**：零私货——概念图是内容（资产），闭包是机制（模块声明的能力面）；未复制官方模块入包（core_only 引用），未改核心代码。
4. **资产密度**：1 内容资产 / 26 键（资产键 + 24 条目键 + 包外前置键），密度归一 3.41 键/档 ≥ 基线 3.0——**水位说明**：这是「一概念一键」的条目寻址形态，不是语义厚度的自我宣称。
5. **文档可执行性**：包 README（速览 + 装载命令）、P07 管线（层位/允许段/契约闭合）、资产（人读表 + 机器可读块双形态同源）三件互指；求值命令与输出样本见本件 §三。

**差在哪**：判据面仍靠域包自带质控（求值器 + 单测），不在仓库统一门禁内——这是本波明确点名的缺口，不是「已达标」。

## 十、复审记录（同日第二波 · 深化波次后）

**触发**：`nf conformance` 报 `audit` 契约不通过——本件 subjects 原绑 v1.0 资产 / 模块 / 求值器 / 测试，深化波次（概念图 v1.1 双支扩面 + 别名面 + 就绪清单，见 `docs_audit-51-ai-domain-deepen.md`）改动了这些对象。按审计协议「对象一改，旧审计即失效，须重审并更新摘要」，本件**重审**而非绕过。

**复审结论（逐条复核，命题段与三层判定不改）**：

1. 命题 P 结论不变：求值面仍可表达（四件产物可复现）、声明面仍以内容形态成立、**判据面缺口仍在**（图内部一致性仍不在 verify check 族内，缺口价值面随覆盖面扩大而上升）。
2. 本件引用的数字在 v1.1 内容上重新实测：`closure(C22)` 仍 **13**、`missing(C22, {C01,C07,C08,C10,C18})` 仍 **8**、`load_order` 覆盖全图（24 → 47 概念）；域包自检 9 → **15** 项、单测 16 → **31** 例（新增别名 / 分支 / 就绪清单 / 用法错误与四类负例）。
3. `verify.sh` 仍 PASS=61 / WARN=0 / FAIL=0（未新增 check、未改 Schema）。
4. §六「运行时裸号歧义」与 §八 三处设计偏差在 v1.1 下仍成立（本波新增概念键为 `Cxx`，不触及 `Mxx` 裸号面）。
5. 包内容版本随内容变更走 additive 档：`1.0.0 → 1.1.0`（`protocol.yaml` 摘要同步更新）。

**第三波复审（2026-09-20 · 作者裁决四项执行）**：本件 §二 的**判据面缺口已关闭**——概念图内部一致性现由 verify check32 的 `concept_graph` 子扫描承担（无环 / 无悬空 / 边有溯源 / 层位合法 / 节点 id 唯一 / 别名唯一 / 分支完备），且只读求值器与门禁**同源**（`desktop/src/core/concept_graph.py` 单一实现）。命题 P 的三层口径结论不变（求值面可表达 / 声明面以内容形态成立 / 判据面原缺口），第三波所做的正是把该缺口的**最小可行补法**兑现。subjects 中资产与求值器摘要已随之更新；详录见 `docs_audit-53-authors-decisions.md`。

**摘要更新**：subjects 六条已更新为 v1.1 内容摘要；本件结论对新内容有效。
