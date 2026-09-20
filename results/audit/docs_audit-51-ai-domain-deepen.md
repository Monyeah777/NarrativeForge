---
id: AUD-0003
title: AI 系统域包深化 —— 双支概念图 / 别名检索 / 就绪清单；四仓借鉴逐条实证
date: 2026-09-20
scope: 域包深化（概念图 v1.1 扩面 + 检索词面 + 就绪清单面 + 声明面同步）＋两条机制缺口补修（registry_sync 投影版本透传 / check30 判据修正）与四份外部输入的「机制借鉴 → 逐条实证」判定；门禁收口
verdict: pass
auditor: 本轮执行者
subjects:
  - community/AI系统域包/protocol.yaml:13e26c88057987be2c5933a879d214ed75a1f33e5bc8da4371a36dbcc04bf7b1
  - community/AI系统域包/assets/CONCEPT_GRAPH.md:93058b9d94fe7828a4d2fc887fff493f65b14b67b7740457fbd3b3408f62e3eb
  - community/AI系统域包/modules/M25_前置闭包求值.md:2118a73922271efa1c38095e6ff430b9cec1b34031d7c316306afbb45a0cd1bd
  - community/AI系统域包/modules/M26_装载序就绪门.md:fbc7c16d73989bdce1240748407497baf2e811f90337dc6da211645487663448
  - scripts/ai_domain_closure.py:1b7a2ab0d46534d4dda00f968e4ddd11c5492037963389ab53e9b053d5cb1679
  - desktop/tests/test_ai_domain_closure.py:1f7e0e7749f2bf52edee010ff080b3b3a0ee23d4e51e5275eda7787a57c7fb02
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。

## 一、本波做了什么（结果形态）

| 面 | v1.0 | v1.1（本波） |
|---|---|---|
| 概念图覆盖面 | 计算与实现栈 24 概念（C01–C24） | **双支 47 概念**：计算与实现栈 25（+C46 训练与适配）+ 应用与系统设计栈 22（C25–C45、C47） |
| 检索词面 | 仅条目键 | 条目键 / **别名** / 概念名三路同解（别名唯一性入图健康度判据） |
| 产物面 | 闭包 / 缺失清单 / 装载序 | ＋**下一步可装载集 frontier(L)**（就绪清单，可分支过滤）与批量缺失清单 |
| 序判据 | 2 条来源序 | ＋第三条来源序（指南章节序），实测违反边 1 |
| 声明面 | M25 interfaces 2 项；M26 outputs 2 项 | M25 interfaces 4 项；M26 outputs 3 项（新增 `ready_frontier`）＋ PrereqState 增 `branch` |
| 包内容版本 | `1.0.0` | **`1.1.0`**（02 §8 档位映射：概念扩面 + 产出键新增 = **additive → MINOR**；已发布版本不原地改写） |
| bump 迁移记录 | 无 | `protocol.yaml` 内嵌四步（现状快照 / bump 声明 / 迁移说明 / 校验回读）——本波为首个 `package.version` bump，check30 对**任何** `: <数字>` 变更行都要求四步记录（其 `tok` 正则为死代码，见 §五.6） |

复现（仓库根目录，只读求值器）：

```
python scripts/ai_domain_closure.py --check                      # 自检 15/15（含 5 类负例）
python scripts/ai_domain_closure.py --list                       # 条目键全表（48 键 + 别名）
python scripts/ai_domain_closure.py --target RAG --loaded C00,C01,C20,C27
python scripts/ai_domain_closure.py --ready-list --loaded C00,C01,C20 --branch app
python scripts/ai_domain_closure.py --gaps --loaded C00,C01 --branch app --limit 10
python scripts/ai_domain_closure.py --order design-guide-chapter-order
```

实测样本（别名检索与就绪清单，逐字节可复现）：

```
$ python scripts/ai_domain_closure.py --target RAG --loaded C00,C01,C20,C27
资产：community/AI系统域包/assets/CONCEPT_GRAPH.md（v1.1 · 域 AI系统 · 节点 47 + 包外前置 1 · 分支 app=22 / compute=25）
目标：C28（检索增强生成（RAG）：外部上下文接地）· 分支 app
[1] 前置闭包 closure(C28)：11 个概念
    C00、C01、C07、C08、C09、C10、C20、C25、C27、C28、C43
[2] 缺失清单 missing(C28, L)：7 个概念

$ python scripts/ai_domain_closure.py --ready-list --loaded C00,C01,C20 --branch app
  frontier = C25、C27（2 个）

$ python scripts/ai_domain_closure.py --gaps --loaded C00,C01 --branch app --limit 5
  C42  治理、合规与成本：策略、审计、成本与路由           缺 21：C07、C08、C09、C10、C11、C12、C15、C16…
  C41  护栏与可靠性模式：输出护栏、集成冗余、降级          缺 19：C07、C08、C09、C10、C11、C12、C15、C16…
```

## 二、四份外部输入的借鉴判定（机制借鉴 → 逐条过仓库实证）

> 口径：外部输入只作**机制借鉴候选**，每条都过仓内实证；判定只用内部证据（仓内文件 / 本波落地）。原始勘验记录属计划期产物，留本地内部档案（`05_借鉴勘验记录_四仓筛选.md`），仓库只留结论。

| 候选输入（类型） | 判定 | 仓内实证依据 |
|---|---|---|
| AI 系统设计指南（知识结构，MIT） | **净吸收（主借鉴）：覆盖面 + 一条来源序** | 章节结构 → 应用栈 21 概念（C25–C45）与 C46 / C47；章节序落为 `orderings.design-guide-chapter-order`，实测违反边 1（`C40 → C41`）——教学序不是前置序，与既有两条序判据同构 |
| Agent 系统提示词合集（内容，MIT 等） | **部分吸收（仅取结构事实）** | 「提示 / 上下文工程是独立知识面」→ 概念 C25 / C26；其机制类条目（角色 / 工具 / 分步 / 拒绝 / 语气）在仓内已有更机械等价物：`machine_contract` 机读契约 + `tool_face` + `nf driver` 机器面路由 + `cognition` 执行分档——**已具备，不重做** |
| 提示词与工具定义合集（内容，GPL-3.0） | **剔除** | 内容为提示词文本，非本域知识结构；许可为 copyleft，结构借鉴亦有摩擦；其唯一机制面（工具面声明）同上已具备 |
| OSINT 情报整合系统（工程实现，Apache-2.0） | **部分吸收（结构证据）** | 管线阶段（采集 → 清洗 → 向量化 → 检索 → 聚合 / 相似度跳转）→ 概念 C43 与 C29 的边证据；采集实现 / 向量库选型 / Web 服务属实现层，NF 是内容契约层——**不适面剔除** |

**纪律声明**：以上判定不改变任何立项理由（本波立项靶子仍是 AUD-0002 的命题 P：判据面缺口与域中立战例），外部输入未用作质量背书；外部文本未进仓库，结构借鉴处逐条注明来源与许可（资产 §7）。

## 三、覆盖面的可证性（为什么扩面没有变成「堆词条」）

1. **每个新节点都要立得住**：全部 47 概念都有层位、前置边、provenance；结构类来源只提供覆盖面证据，不单独立边（`conflict_rules` 第 4 条）——把「有案例 / 有章节」与「有前置」分开。
2. **图健康度机检**：`problems()` 判无环 / 无悬空 / 有溯源 / 层位合法 / id 唯一 / **别名唯一** / **分支完备**；`--check` 以负例注入（环 / 悬空 / 重复别名 / 分支缺口 / 逆序）证明判据有捕获力，15/15 通过。
3. **跨支边是最有信息量的部分**：如 `C42 治理与成本 ← C22 服务调度`（成本口径要踩在服务调度上）、`C40 评价与可观测 ← C24 评测与可靠性`（应用侧评测要踩在系统侧口径上）——这些边是「单支目录抄写」抄不出来的。
4. **序判据可复现**：三条来源序（讲序 0 / 目录序 5 / 章节序 1）逐条给出命令与数字，范围写明「仅该序列内概念之间的边」。

## 四、门禁与验收

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | PASS=61 · WARN=0 · FAIL=0（check1-37 常驻；未新增 check、未改 Schema） |
| `python -m unittest discover -s desktop/tests -q` | 全绿（域包单测 16 → **31** 例：新增别名 / 分支 / 就绪清单 / 用法错误 / 四类新负例） |
| `python -m ruff check .` · `python -m compileall -q desktop/src scripts` | 零违规 |
| `nf pipeline dryrun --all` | 9 条管线零 hard（P07 声明面变更后仍零 hard） |
| `nf score` | 100.00 · 无回归（资产键密度 165 → **215** 键 / 56 档） |
| 资产台账 | `nf asset verify` 闭合（台账 2 · 托管资产 3 · 孤儿头 0；本包资产 version 1.0 → 1.1 同步） |
| 登记三要件 / 投影 | `nf register --check` 幂等（module_id_range、pipeline、categories、assets 数未变）；模块边界与 golden 已重签 |

## 五、遗留与下一步

1. **判据面缺口仍在**（AUD-0002 §六）：图内部一致性只由域包自带求值器 + 单测覆盖，未进 verify check 族；本波把覆盖面扩大后，该缺口的价值面同步放大（47 概念、3 条来源序、别名唯一性），最小可行补法不变（既有 check 内追加一条图健康度断言）。
2. **应用栈的边以结构类证据为主**：待有实现类证据（可复现系统工作）再收窄；`C45`（模式 / 反模式）与 `C24` 的 `inferred` 部分同属高抽象节点。
3. **运行时裸号歧义**（AUD-0002 §六）：本波新增概念键为 `Cxx`，不触及 `Mxx` 裸号面；该缺口的补法仍在作者裁决队列。
4. **双端推送待作者指示**（本波提交后）。
5. **`nf register` 投影不带 `version` 字段**（机制缺口，本波实测）：`registry_sync._normalize` 的键集不含 `version`，故**新增**包经 `nf register --apply` 写入的 `protocols[]` 条目缺 version（check14 ⑦ 两侧按 `or "1.0.0"` 缺省比对，1.0.0 时无感）；包内容版本 bump 后须**手工补一次投影**（本波 1.0.0 → 1.1.0 即如此处置；对已存在条目该键不会被覆盖或删除，故补后稳定，`nf register --check` 复测幂等）。最小可行修法：`_normalize` 键集加 `version`（核心一行改动），交作者裁决。
6. **check30 的版本判据过宽 + 一处死代码**（机制缺口，本波实测）：`verify.sh check30` 先定义 `tok`（限定 `schema_version` / `registry_schema_version`）却**从未使用**，实际用不限定的 `parse_version` 扫全部 `±` 行——故任何含 `: <数字>` 的变更行（含 `package.version`、甚至注释里 `= 1.0.0`）都会触发「版本结构性变更」，并要求该文件 diff 内出现四步迁移记录；JSON 类文件（`registry.json`）无法内嵌迁移记录，只能靠「纯插入式改法」让 old 侧为空而绕开判据。最小可行修法二选一：① 让判据真正使用 `tok`（只扫 schema 版本键）；② 把四步记录改为「同一次提交内可寻址的迁移档」（如 `02 §9.x` 段落 + 提交信息），不再要求内嵌于被扫文件 diff。交作者裁决。

## 六、五维自评

1. **静态可核验**：verify 全绿、conformance 契约全过、回执与批准链重签一致。
2. **动态可执行**：四件产物全部有可复现命令与样本；就绪清单给出了「装配方下一步装什么」的直接答案。
3. **架构纯度**：概念是内容（资产）、求值是模块能力、排序是派生量；未新增核心代码、未改 Schema、未新增 check；外部文本零复制。
4. **资产密度**：1 内容资产 / 48 条目键 + 别名面；密度归一 3.84 键/档（基线 3.0）。
5. **文档可执行性**：README（四件产物 + 辅助面）、模块（数据槽 / 就绪清单契约）、资产（人读表 + 别名表 + 机读块）三处互指且命令可粘贴执行。

**差在哪**：应用栈的边仍未全部拿到实现类证据；判据面仍靠域包自带质控——两条都如实记在上面。

## 七、补修记录（同日收口 · §五 两条机制缺口已修）

| 缺口（原挂账） | 修法 | 回归测试（可复现） | 复测结论 |
|---|---|---|---|
| `nf register` 投影不带 `version`（新增包条目缺包内容版本；bump 后 check14 ⑦ 失配，只能手工补投影） | `registry_sync._normalize` 键集补 `version`（缺省 `or "1.0.0"`，与 check14 ⑦ 兜底同口径） | `desktop/tests/test_registry_sync.py::VersionProjectionTest`（投影带 version / merge 写入新版本 / 缺省兜底，3 例） | 6 个已登记包 `nf register --check` **全部幂等**（修正未产生伪 diff）；AI系统域包双源一致 `1.1.0` |
| `check30` 判据过宽（`tok` 为死代码：任何 `: <数字>` 变更行都触发）+ JSON 类文件无迁移记录通道 | ① 判据真正收敛到**版本字段行**（`tok` 同时认 YAML `version:` 与 JSON `"version":`）；② 记录面 = 该文件 diff **∪** `02 §9` / `protocol/EXTENSION.md` 的同次提交 diff | `desktop/tests/test_check30_bump.py`（6 例：两条正例通道 / 三条负例（无记录、JSON 无记录、四步缺一）/ 一条误判回归），**取 `verify.sh` 内嵌程序真件**在独立 git 夹具上执行 | 记录档落 `02 §9.4`（四步齐备）；`protocol.yaml` 只留指针（记录单一真相源）；verify 全绿 |

**性质声明**（防「修判据 = 放宽判据」误读）：

1. 记录要求**未放宽**——仍是四步齐备、且必须随**本次变更**可见（新增的只是「记录该在的地方」多了一条：迁移记录档），JSON 文件由「结构上不可满足」变为「有明确合规通道」。
2. 检测面**变准而非变松**——收敛到版本字段行后，非版本字段的数值改动（如 `assets.count`）与注释里的数字**不再**误判；该语义由回归测试钉住（`test_non_version_numeric_change_not_flagged`）。
3. 两条修正均**不新增 check 序号、不改 Schema**；check30 的序号与门禁位次不变。
