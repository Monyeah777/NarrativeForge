---
id: AUD-0005
title: 作者裁决四项执行 —— 概念图判据面 / 运行时裸号歧义 / 投稿闸门声明化 / 资产货架口径
date: 2026-09-20
scope: 收口四项作者裁决的挂账（均取自本会话外挂账队列）：判据面缺口、命名空间运行时歧义、投稿闸门可见性、资产货架单层口径；四项皆「既有 check 内追加断言」，不新增 check 序号、不改 Schema
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/concept_graph.py:5a4f5b6dc61f825c3d51a648eae84e434ac3cc475114db7c3f50e256ae193ca2
  - desktop/src/core/intake.py:6a0d584c81dcdeb1439bf4e3f16b201e08e618c8d6296e80a63c6f5266447e56
  - desktop/src/core/asset_ledger.py:f45329c6ac19c864799ee5113f4246474d2a0e41521942bea10f90e379e9e236
  - scripts/ai_domain_closure.py:215309a9027c548129b72b7fc3108ba6ade7d593019c8cc6a474008cd189bd15
  - library/intake.json:28288978a5c4dcbdcff5017bdac52a027f83ec2478f81034f39415c181190533
  - verify.sh:00bb02e959eda5a85a218b7eb2eb4a08a6d523d634243886aab386016f9d1dd0
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 四项执行的**承重件**（任一件再改，本件结论即失效，须重审）。

> 重审（2026-09-21 · D1-D5 修复波）：`ai_domain_closure.py` 自检样例按资产登记通用化（闭包语义不变）——结论复核不变，subjects 依「重审并更新 digest」处置。

## 一、执行清单（四项 · 逐项给判据与回归）

### ① 概念图内部一致性入判据面（原 AUD-0002 §二 缺口）

| 面 | 落地 |
|---|---|
| 实现 | 新增 `desktop/src/core/concept_graph.py`：**图语义单一实现**（闭包 / 缺失清单 / 就绪清单 frontier / 确定性拓扑 / 违反边 / 别名解析 / 分支映射 + 健康体检 `problems()` + 全仓扫描 `scan()`） |
| 门禁 | 作为**既有 check32 的子扫描**接入（`quality_depth_scan.scan()` 的 `concept_graph` 项）——判据：无环 / 无悬空 / 边有溯源 / 层位合法 / 节点 id 唯一 / 别名唯一 / 分支完备；无图资产**中性通过**（不误伤既有包与用户资产） |
| 同源 | 只读求值器 `scripts/ai_domain_closure.py` 改为 `from core.concept_graph import ...`，不再自带一套算法（门禁与工具同解，杜绝双源漂移） |
| 回归 | `desktop/tests/test_concept_graph_gate.py` 12 例：仓库真源零 issue（47 节点 / 87 边）+ 门禁与求值器同源四断言 + 中性两例 + **七类图缺陷负例**（环 / 悬空 / 重复别名 / 未归支 / 缺溯源 / 节点 id 重复 / 层位越界）+ 缺陷带资产路径前缀 |

### ② 运行时裸号歧义收口（原 AUD-0002 §六 缺口）

| 面 | 落地 |
|---|---|
| 实现 | `verify.sh check14 ⑤` 段内追加三条断言（**不新增 check 序号**）：① 同一裸号不得属两个及以上社区包；② 同包内文件名裸号不得重复；③ 包自有裸号若被官方核心 / 他包占用，则本包管线不得以**裸号**引用（须全限定 `<类别>:Mxx`） |
| 依据 | 运行时模块索引（`pipelinerun._module_files`）以文件名裸号为键、`setdefault` 先到先得——实测战例：`AI系统:M01/M02` 曾把西幻 P03 的裸号引用解析改指本包（advisory 台账可见、门禁全绿） |
| 文档 | `02 §8.3` 增「裸号索引不变量」条（含战例与三条断言） |
| 回归 | `desktop/tests/test_module_namespace.py` 7 → **12 例**（取 check14 **真件**在独立树上跑）：跨包重号 / 同包重复 / 裸号引用歧义三负例 + 「各包裸号互不相同的单包自引」与「改用全限定即清零」两正例对照 |

### ③ 投稿闸门声明化（原 AUD-0004 §三 观察 + AUD-0003 §五 挂账）

| 面 | 落地 |
|---|---|
| 声明面 | 新增机读声明 `library/intake.json`（`schema: nf-intake/1`；通道 `gitee` = `open`、`github` = `author_only`+白名单；`after_action: lifecycle`；每通道带须出现在须知的 `index_label`） |
| 执行面 | 两个入库机器人**运行时读声明**（`library_ingest.load_gate()`，Gitee 机器人复用）：`open` 直投 / `author_only` 校白名单 / **`paused` 一键关闸**；声明不可读即 **fail-closed 暂停**（不静默放行）——闸门从此不再隐藏于代码常量 |
| 判据面 | 新增 `desktop/src/core/intake.py` 做**三方一致**断言（声明 ⇄ `library/INDEX.md` 投稿须知措辞 ⇄ 两个机器人引用声明件），并入**既有 check34** |
| 人读面 | `library/INDEX.md` 投稿须知增「闸门声明（机读真相）」条（通道措辞与声明逐字一致） |
| 回归 | `desktop/tests/test_intake_gate.py` 11 例：仓库真源两通道零 issue + 机器人已接线 + **九类负例**（缺声明 / JSON 坏 / schema 错 / updated 非法 / 缺 after_action / channels 空 / mode 越词表 / author_only 无白名单 / index_label 未出现在须知 / 机器人未引用）+ `paused` 合法开关例 |

### ④ 资产货架口径统一（原 AUD-0004 §三.①）

| 面 | 落地 |
|---|---|
| 实现 | `asset_ledger.verify_shelf_shape()`：货架（`community/*/assets`、`05_资产库/用户自定义`）**不得含子目录**；`verify_root()` 聚合该项（`nf asset verify` 与 **verify check23** 同步生效） |
| 依据 | 三面扫描（密度 / 键表投影 / 行数基线）非递归，台账面 `os.walk` 递归——子目录会造成「台账可见、三面不可见」（静默丢口径） |
| 文档 | `05_资产库/README.md` 增「单层货架不变量」条（含修复指引：分组用键表 / 一包多文件） |
| 回归 | `desktop/tests/test_asset_ledger.py` 15 → **20 例**（单层通过 / 包货架子目录被抓 / 用户货架同样覆盖 / `verify_root` 聚合与 shelves 统计 / 仓库真源四货架实测单层） |

## 二、门禁与验收

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | PASS=61 · WARN=0 · FAIL=0（check1-37 常驻；四项均为**既有 check 内追加**，无新增 check 序号、无 Schema 改动） |
| `python -m unittest discover -s desktop/tests -q` | 全绿（本波新增 28 例：概念图 12 + 裸号 5 + 闸门 11 + 货架 5 减去既有重复计数，见各测试文件） |
| `python -m ruff check .` · `python -m compileall -q desktop/src scripts` | 零违规 |
| `nf pipeline dryrun --all` · `nf score` | 9 条管线零 hard；评分 100.00 无回归 |
| 资产面 | `nf asset verify` 闭合（含新货架不变量）；台账 / 键表投影 / 行数基线三面同步重签 |

## 三、边界与遗留

- 四项**均未新增表达力**（除 ③ 的声明件是新机制面，但其消费方 = 既有两个机器人与其须知，即「有人消费才产」）与**未放宽任何判据**：①②④ 只加判据/不变量，③ 把隐蔽常量变成可机检的三方一致。
- 仍开放（不在本波）：多包组合的裸号跨包引用白名单化（当前以「不得裸号引用」收口）；资产货架若未来需要嵌套分组，需按「表达力扩展」另提裁决（本波守单层不变量）。
