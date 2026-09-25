---
id: AUD-0006
title: 外部输入筛选台账 —— awesome-shell（批次三；判定：无净吸收项）
date: 2026-09-20
scope: 机制借鉴类外部输入的筛选与逐条仓内实证（STRATEGY §3.2 第二角色）；本批对象 = alebcay/awesome-shell。批次一（node.cool → awesome-nodejs）见 docs_audit-51 §八；批次二（data-engineer-handbook）见 docs_audit-52
verdict: pass
auditor: 本轮执行者
subjects:
  - CONTRIBUTING.md:2a3e7848221cc8a642e6dac9aa4f08da3437a63b2c0fca5a5bfe3473a784efe2
  - skills/narrativeforge/SKILL.md:8742a5f651473d1ecb5770b4ac2c1e190bce998e1205cfa7c424e677010982d0
  - library/INDEX.md:bb92ed10beeeb80ec2b5a95ddace2ad8cac6f7cd8b28095b1ad778b1dfdc3ebc
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 语义：本件是「外部输入筛选」结论，绑定的三条是**判定所依据的仓内证据件**（准入面 / 语言面 / 索引面）——它们一改，本件结论即须重审。

## 一、对象与形态（先取证）

筛选对象：`github.com/alebcay/awesome-shell`（浅克隆只读勘验；5 文件 / 74.6 KB）。

| 面 | 实况 |
|---|---|
| 主件 | `README.md`（44 KB，英文）**11 章节 / ~366 条正文条目** |
| 第二语言面 | `README_ZH-CN.md`（22 KB，中文）**10 章节 / ~197 条正文条目** |
| 准入 | `CONTRIBUTING.md`：判据 = **scope**（收 CLI 应用 / shell 扩展 / 指南；**拒**终端模拟器并指向邻居清单 `terminals-are-sexy`）+ **notability**（GitHub 项目 **≥50 stars**；自我推广允许） |
| 门禁 | `.github/workflows/ci.yml` = **单一作业**：`lycheeverse/lychee-action` 对两份 README 做**外链可达性巡检**（排除一个已知站点）；无形态 lint、无双语一致断言、无投稿模板 |
| 许可 | CC0-1.0 |
| 治理自述 | CONTRIBUTING 开头：「本仓此前基本无人管（收与不收无准则），现补本文档并**逐步重构清理**」 |

## 二、逐条实证（口径：已具备不重做 / 不适面剔除 / 净吸收）

| 候选机制（实况） | 判定 | NF 侧对应（仓内实证） |
|---|---|---|
| 精选清单形态（Contents 锚点 + 分类 + 条目短句） | 已具备（更机检） | `library/` frontmatter 真源 + INDEX·ALIAS 机读投影（check34 投影一致断言）· `patterns/` INDEX · `nf market` tier 徽章 |
| 准入的 **scope 判据**（收什么 / 拒什么 / 拒后指向邻居清单） | 已具备（更结构化） | 01 §6 R1/R2/R3（依赖边界 / 类别独占 / 装配契约）+ 02 §8.3 登记三要件 + 入馆唯一硬标准（自包含可召回）；「拒后指路」= 07 导航 + `community/模板制作指令包.md` + 各 issue 模板 |
| 准入的 **notability ≥50 stars** | **剔除（与方向层冲突）** | STRATEGY §2：决策函数只含**质量**一个变量，star / 热度类指标**显式排除**（不当目标、不当参考、不进入立项与排期论证）——与批次一（≥100 stars）同判 |
| **外链可达性巡检（lychee）** | **剔除（离线纪律）** | NF 门禁须**静态可复现**（同输入同输出），网络可达性依赖第三方站点状态 → 会引入不稳定门禁；NF knowledge 层以「来源标注必填 + 时效 ttl/no-cache」声明外部引用（check37），执行面**刻意零网络**（L2 core 零第三方依赖红线）——与批次一 / 二同判 |
| **多语言入口面（EN + ZH-CN）** | 已具备「纪律」，**无当前消费者 → 不产** | NF 现有对外入口为中文主体（README / llms.txt / AGENT_START / ROUTES），唯 `skills/narrativeforge/SKILL.md` 的 name/description 为英文（供英文侧工具发现）——故「英文发现面」已存在最小形态；而**该仓自身证明**：开了第二语言面却**无一致性判据**（CI 只巡检链接）→ 中文面腐烂到 EN 的 **~54%**（10 章/~197 条 vs 11 章/~366 条）。NF 的双源纪律（check14 ⑥ / check15 ⑤ / check34 投影一致）正是防此病的机制——**纪律已在场**，是否增开英文面属方向层取舍（封闭期 + 按需装配），本批不擅自动手 |
| CC0 许可 | 无需吸收 | NF：代码 MIT + 内容许可分列（`license_gate` 双源校验） |
| 「此前基本无人管 → 逐步清理」的治理自述 | 观察（反向验证） | NF 侧对应：机检门禁族（check1-37）+ audit 建档 + CHANGELOG 对账 + 生命周期流转（deprecated/retired）——**该自述是 NF 路线的反证样本**，不构成吸收 |

**结论**：**无净吸收项**——该仓是「单清单 + 单 CI 作业」形态：清单形态与准入面 NF 侧更结构化，notability 与网络巡检两项判定剔除（与批次一 / 二同理由），多语言面若有价值须带一致性判据（NF 已有该纪律）。

## 三、观察候选（不吸收，交作者裁决）

① **多语言入口面**（本批唯一有机制意味的观察）：若未来要让**非中文 AI / 读者**自助装载（STRATEGY §一.4「任一 AI 拿到仓库即可按协议生产或装载」的边界情形），需要一个英文发现面；届时**必须**配套一致性判据（否则同该仓：第二语言面会腐烂到无判据可查）。当前零消费者（封闭式发育 + 现有入口为中文）→ 本批只记档。
② 外链巡检若开：应作**独立非门禁任务**（不影响 verify 基线的可复现性），且与 knowledge 层的时效声明联动——本批不实施。

## 四、边界与纪律

- 只读勘验（浅克隆到本地临时目录），**未复制其文本**，未把任何结构落入资产 / 溯源图例；本记录只写判定与数字。
- 筛选结论不构成任何立项理由（STRATEGY §3.3 禁令一）；未引用其规模 / 评价类指标作论据。
- 原始勘验证据（克隆清单、README/CI/CONTRIBUTING 实况、双语条目计数）留本地内部档案 `08_借鉴勘验记录_awesome-shell.md`。

## 五、验收与后续

- 本批**未改任何资产 / 模块 / 门禁**（无净吸收项 → 不产无消费者的变更）；仅本记录 + RESULTS 索引 + 内部档案。
- 门禁：`bash verify.sh` 全绿；`nf conformance` conformant（审计件数变化 → 报告重签）。
- 作者裁决队列（本批新增一条）：**多语言入口面**是否需要（若需要，须带一致性判据）。
