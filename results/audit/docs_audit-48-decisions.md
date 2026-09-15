# docs_audit · 48 决策族（ADR）落地 · 2026-09-15

> 来源：`NF_协议品类池_调研_v1`（9 族缺口）× 长期计划 W1。
> 基线：`verify v2.27 · check1-37 · PASS=61`（本波不新增 check）。

## 一、本波补的内部差距

调研稿族 4 判「高缺」：**决策无独立品类**——「为什么这样定」散在备忘录、对话与 audit 叙述里，
没有可编号、可追溯、**不可被偷改**的载体。而 ADR 的硬规则（一条一编号；采纳后不改不删，只可被取代）
与 NF 已有机制同构（RFC 头 + supersede 链 / 馆藏签名锚 / approvals / EXTENSION bump 四步），
故实现成本低、判据强。

## 二、落地的件

| 件 | 形态 | 作用 |
|---|---|---|
| `decisions/ADR-0001..0003.md` | 三条**真实**决策 | 双源知识层落位（不升模块层）/ 门禁不注水 / 断言表 kind 封闭集 |
| `decisions/README.md` | 品类说明 | 与 RFC 头 / 审计报告 / 迁移记录**划清分工**（防混装） |
| `decisions/INDEX.md` | 投影 | 由 frontmatter 重生成（`nf decisions reindex`） |
| `desktop/src/core/decisions.py` | 门禁 | 编号/状态/日期/三段齐/取代链/证据可解析/回执锚定/投影一致 |
| `nf decisions [show\|verify\|reindex]` | 机器面 | 取用与自检 |
| conformance 契约 `decisions` | 报告 | 19 → **20 契约**；回执 35 → **39 件**（3 ADR + INDEX 入锚） |

## 三、关键设计选择：不新造「不可改」机制

「采纳后不可改」**没有**引入自摘要或第二套锁——直接用已在跑的**协议回执**：`status: accepted` 的 ADR
必须已被 `protocol/RECEIPTS.json` 锚定，正文一改回执即失效，于是"改了"必然被 check35 抓住。
**判据复用既有机器**，符合 ADR-0002（门禁不注水）。

## 四、本波抓到的真缺陷（否定用例的产出）

门禁初版把「回执文件存在但**为空**」当成"无回执"而跳过锚定校验——等于给"删空回执即可偷改"留了后门。
已修为**只以文件是否存在为准**，任一 accepted 未被锚定即 FAIL。此缺陷由 `test_unanchored_accepted_is_fail` 抓出。

## 五、五维水位（W1）

静态可核验 ↑（新契约 + 8 项单测，含 6 类否定用例）· 架构纯度 ↑（决策有独立品类，不再混在 audit 叙述里）·
文档可执行性 ↑（`decisions/README.md` 指令式 + 分工表）· 动态可执行 =、资产密度 =。

## 六、遗留（W2–W5）

W2 交接族（SBAR 四段 + 空未决即不合格）· W3 复盘族（根因指向机制、行动项可指派可验）·
W4 审计/验收协议化（结论须指向被审对象 digest；与 `normative.json` 的"results 属说明件"冲突须显式裁决）·
W5 认知族（NF 行话术语表；06 按 Runbook/Playbook 分档）。W2–W4 复用本波产出的 evidence 解析器与锚定判据。
