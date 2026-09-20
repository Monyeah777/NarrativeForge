---
id: AUD-0004
title: 外部输入筛选台账 —— data-engineer-handbook（批次二；判定：无净吸收项）
date: 2026-09-20
scope: 机制借鉴类外部输入的筛选与逐条仓内实证（STRATEGY §3.2 第二角色）；本批对象 = DataExpert-io/data-engineer-handbook。批次一（node.cool → awesome-nodejs）见 docs_audit-51 §八
verdict: pass
auditor: 本轮执行者
subjects:
  - .github/PULL_REQUEST_TEMPLATE.md:27e7688cf590aded0bbd4574235d0a8e47d5aa1680284ad99450daeda2a8e66d
  - CONTRIBUTING.md:0a4dc584550fd42508a952c2f74b40b4ffc2af3b7fb54acfe8df628a50ea5899
  - desktop/src/core/asset_density.py:27221a9540bc3b001d8f09a617464abcaf4db796461504d3b5898d853e005d63
  - desktop/src/core/asset_line_baseline.py:c62eda98405249b1a31fbd17bf08256b29426eeb171dd3a2bfeb2ecbcd8120e1
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 语义：本件是「外部输入筛选」结论，绑定的四条是**判定所依据的仓内证据件**——它们一改，本件结论即须重审（审计协议同款语义）。

## 一、对象与形态（先取证）

筛选对象：`github.com/DataExpert-io/data-engineer-handbook`（浅克隆只读勘验；124 文件 / 232 MB）。

| 面 | 实况 |
|---|---|
| 主件 | `README.md`（28 KB）= 手册脊柱：`# The Data Engineering Handbook` / `## Getting started` / `## Resources`，其余为分件资源清单 |
| 分件清单 | `books.md` · `communities.md` · `data_cleaning.md` · `interviews.md` · `newsletters.md` · `projects.md` |
| 课程件 | `beginner-bootcamp/`（introduction / software）· `intermediate-bootcamp/`（introduction / software / **materials/** 8 个模块目录，共 107 文件）· `databricks-ai-bootcamp/`（day-1/2/3 + README 的 Curriculum / Suggested preparation） |
| 素材形态 | 模块目录内混装：课件 CSV（最大 58 MB）· Postgres `data.dump`（49 MB）· 讲义 PDF · **可视化笔记 PNG**（如 `visual notes/02__Idempotency_SCD.png`） |
| 指针件 | 根级 `read_this_for_application_fundamentals_for_python`（36 字节，内容仅一条外链） |
| 许可 | **顶层无 LICENSE / COPYING**（未声明） |
| 商业面 | Trendshift 徽章 + 训练营报名导流链接（README 与各课程件） |

## 二、逐条实证（口径：已具备不重做 / 不适面剔除 / 净吸收）

| 候选机制（实况） | 判定 | NF 侧对应（仓内实证） |
|---|---|---|
| 课程 / 路线图形态（Getting started → bootcamp → 进阶） | 已具备（更机检） | 域包即「知识路线」的机检形态：概念图 + 前置闭包 + `load_order` + **就绪清单 frontier**（`community/AI系统域包/`，AUD-0003）；`docs/` 四型（Diátaxis 写法判据）+ 演练集 |
| 分件资源清单（books / communities / newsletters / interviews / projects） | 已具备（更机检） | `library/`（frontmatter 真源 + INDEX·ALIAS 机读投影 + 许可列双源校验）· `patterns/`（实践包 INDEX）· `nf market`（tier 徽章）· check34/check36 投影一致断言 |
| 环境前置件（`software.md`：需要装什么） | 已具备 | `AGENT_START.md` + README「五分钟快速开始」+ `nf doctor`（环境自检） |
| 素材随章节分发（materials/⟨模块⟩/{data,slides,notes}） | 已具备（分组方式不同，见 §三.①） | 资产随域包分发（`community/⟨包⟩/assets/`）+ `nf asset` 台账（溯源 / 版本 / 状态 / 可发现，check23）+ 资产密度 / 引用度 / 厚度体检（check32） |
| 投稿与协作入口（PR / Issue 面） | 已具备（更具体） | `.github/PULL_REQUEST_TEMPLATE.md`（改动域 + 三条门禁自检）+ 4 个 issue 模板 + CONTRIBUTING 六节（含社区包协作流程五步） |
| 「指针文件」入口（文件名即指令，正文仅一条链接） | 剔除 | 与 NF 入口纪律相悖：NF 用**统一入口清单**（`llms.txt` / `AGENT_START.md` / `ROUTES.md` / 07 导航）+ 四型归属机检（check34）承载入口；散落指针件制造第二真相源 |
| 商业导流与徽章（报名链接 / Trendshift 徽章） | 剔除（文案纪律） | STRATEGY §四 + 公开文案纪律：仓库只承载方向 / 结果 / 使用者文档；不做导流与推崇叙事 |
| 大体积二进制素材（58 MB CSV / 49 MB dump / PDF / PNG） | 剔除（不适面） | NF 资产面是**内容文本**（`.md` 键表条目）；仓库轻量纪律；本域（内容契约层）不承载数据集与课件二进制 |
| 许可未声明（顶层无 LICENSE） | 剔除（**结构亦不吸收**） | 04 §3 纪律要求借鉴处注明「来源 + 许可」；无许可声明 = 无法注明授权，故本件**不把其结构落进任何资产 / 溯源图例**，只作观察记录 |
| 外链资源的版权状态（清单直链某书的第三方托管 PDF） | 剔除（超出 NF 判据面） | NF 能管的是**仓内**条目许可（`license_gate`：登记列 + 内联声明双源）与 reference 级源的来源标注 / 时效（check37）；不裁判外部资源版权，也不把「链了盗版」当 NF 问题 |

**结论**：**无净吸收项**——该仓是「课程 / 清单聚合 + 课件素材仓」形态，NF 侧同类机制均已存在且多有机检对应物；其独有之处（大二进制素材、指针文件、导流文案、无许可）逐条属不适面或纪律冲突。

## 三、观察候选（不吸收，交作者裁决）

① **素材分组形态 vs NF 单层货架**（本批唯一有机制意味的观察）：该仓按 `materials/⟨模块⟩/{data,slides,notes}` **嵌套**组织素材；NF 资产货架是**单层**——三个机读面（`asset_density` / `asset_ledger_projection` / `asset_line_baseline`）均以非递归 glob `community/*/assets/*.md` 取件（本件 subjects 已绑其中两件），而 `nf asset add/verify` 的台账面走 `os.walk`（**递归**）。
  - 现象：嵌套存放的资产文件「台账可见、密度 / 投影 / 基线不可见」——三面与一面口径不一致，且无门禁提示。
  - 影响：今天为零（实测三个包 `assets/` 子目录数均为 0）；但资产数上量或需要分组时，会静默丢口径。
  - 最小可行补法二选一（**不擅自实施**）：a) 在既有 check 内追加断言「`community/*/assets` 不得含子目录」（守住单层不变量，最省）；b) 三面 glob 改递归并与台账面统一（表达力扩展，需评估投影体量）。
② **数据集 / 课件类二进制在 NF 无资产位**：若未来某域包的资产天然是大文件，NF 现有资产面（.md 文本条目 + 轻量仓库）不承接；是否增设「外部托管 + 指针条目的机检形态」需另行立项（本波不做）。

## 四、边界与纪律

- 只读勘验（浅克隆到本地临时目录），**未复制其文本**，未把任何结构落入资产 / 溯源图例；本记录只写判定。
- 筛选结论不构成任何立项理由（STRATEGY §3.3 禁令一）；本批未引用外部规模 / 评价类指标作论据。
- 原始勘验证据（克隆清单、目录树、许可探测、子件体量）留本地内部档案 `06_借鉴勘验记录_node.cool_awesome-nodejs.md` 与 `07_借鉴勘验记录_data-engineer-handbook.md`（同一档案目录）。

## 五、验收与后续

- 本批**未改任何资产 / 模块 / 门禁**（无净吸收项 → 不产无消费者的变更）；仅本记录 + RESULTS 索引 + 内部档案。
- 门禁：`bash verify.sh` 全绿；`nf conformance` conformant；审计契约对本件按「0 新增 legacy + 1 新增带审计头」重算（见本轮收口）。
- 仍挂在作者裁决队列：概念图内部一致性入 check（判据面缺口）· 运行时裸号歧义 · 外投闸门强度 · **本件 §三.① 资产货架口径统一**。
