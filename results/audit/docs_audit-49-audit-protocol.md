---
id: AUD-0001
title: W4 审计/验收协议化 —— 自审
date: 2026-09-16
scope: 长期计划 W4：审计报告的格式与判据升为规范件；审计内容仍属说明件（分层消解既有冲突）
verdict: pass
auditor: 本轮执行者
subjects:
  - protocol/audit.json:914c5dfe05763ecab52cea35cb72fd34026cd2522ca37fbebc0a86596a1d01eb
  - desktop/src/core/audit.py:e3af0ec66fd6bef523e5c592f58a0d7217568e02002b9ffa7e8384d6c47947d0
accepted_by: 作者
accepted_at: 2026-09-16
---

## 一、审什么

W4 的两件新规：`protocol/audit.json`（审计该怎么写的约束）与 `desktop/src/core/audit.py`（判据实现）。
本报告的 `subjects` 把这两件的 sha256 绑进结论——**任一被审对象再被改动，本审计立即失效**，必须重审。

## 二、结论（verdict = pass）

1. 审计**内容**（某时刻查到了什么）仍属说明件：`results/audit/**` 未被加入回执覆盖面，
   符合 `protocol/normative.json`「说明件不得被回执锚定」；
2. 审计**格式与判据**已升为规范件：`protocol/audit.json` 进入回执覆盖面；
3. 结论绑定 digest 已可机检：对象改动 → `nf audit verify` 报「旧审计失效」；
4. 验收签收双要素（`accepted_by` + `accepted_at`）已判据化；
5. 存量 11 件无审计头的审计件按 **WARN** 挂账（不判死），符合"先可数、再逐回合收"。

## 三、未覆盖（如实挂账）

- **基线数字可复算**只写进 `rules`，尚未做成常驻断言（属断言表可搬运的形状类判据，留给下一波）；
- 存量 11 件 legacy 审计头的回填未做（每件都要绑当时的被审对象 digest，属历史时点事实，
  不能事后补 digest——**建议永久保持 legacy + WARN**，而不是补一个假的过去状态）。
