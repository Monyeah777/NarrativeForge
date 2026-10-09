---
id: AUD-0027
title: v2.12.0 首例发布（保留式收口 + 发布机制两处缺陷修复 + Golden Master）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §二·1「用新机制发布一次」。首例实战取证暴露发布机制两处缺陷（同版本节替换静默删历史 / 提交扫描无发布边界），先修后收；CHANGELOG 既有 2.12.0 手工节按「不静默丢内容」保留。tag 与 push 属作者动作，本件不含。
verdict: pass
auditor: 本轮执行者
subjects:
  - CHANGELOG.md:812795aaa3f59aeb120a228f12a04478f08049642d6f1342a18bd939e70f0941
  - docs/meta/VERSION-MATRIX.md:abe7adfd40849a0191f738bb4d051ce487e811328d800c3049bbda7add455615
  - README.md:e2c3aaba8f56e8a7ca3a436b8075542d3cad0358e65dc8c62615a671bbddc987
  - desktop/src/core/changelog_gen.py:91f1c9eae7a48bbad209d041b48b2eb6d91dbe2eca36c08ee457ffdf21104e16
  - desktop/tests/test_changelog_gen.py:3ddb12cc2247f8bf5649dc4e64d7521fc40795aba93c90f8dd34fc3df47377b8
  - protocol/release_policy.json:0c8ecfad8f1f23101442dc8a1c301cecb0f0cb9e33d293dd0ceb4caadc94f96d
  - docs/release.md:b4ddbad660793dba16a125e2f1b351ecb3dec462785642107297dc70ff40e1d1
  - scripts/nf.py:f23801bcf642b3ac5a95a15068f776712aeff5a01a0ec20063646ddc1ec36036
  - scripts/release_freeze.sh:30d8ae65f958d71e98411793affdacba75efaa5f0934373dab991e065fe530a3

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物：`protocol/conformance_report.json` / `protocol/RECEIPTS.json` / `protocol/generated/*` / `results/interop/*` / `protocol/approvals/*` / `.release-frozen/*` 均为可复算投影或每次重签即变。

## 一、首例实战取证（开工依据）

1. **同版本节替换会静默删历史**：`insert_into_changelog` 原本无条件用生成节替换同版本节。实测 v2.12.0：1790 行人工未发布节 → 13 行生成节，会丢 333 条。
2. **提交扫描无发布边界**：`commit_subjects` 无 range，`nf changelog` 会把全史 582 条提交主题塞进版本节。
3. **既有 2.12.0 手工节无对应 changes 条目**（机制落地前积累），生成器无法覆盖——这是首例独有的迁移面。
4. **`nf release --freeze --apply` 的 `--apply` 被 argparse 拒收**：解析器只登记了 `--freeze`，而实现读 `args.apply`、帮助与 `docs/release.md` 都写 `[--apply]`——命令实际进不了执行态。
5. **冻结链顺序源指向不存在的属性**：`_release_freeze` 读 `rg.FREEZE_CHAIN`，而真源是策略件 `protocol/release_policy.json` 的 `freeze_chain`（`release_gate` 只有 `DEFAULT_FREEZE_CHAIN` + `policy()`）——该命令必抛「内部错误」。

## 二、交付

| 面 | 落点 |
|---|---|
| 缺陷一修复 | `changelog_gen.insert_into_changelog` 丢内容守卫：同版本节含未被生成覆盖的条目即抛 `ValueError`；写面 rc=2、不落盘、不归档（fail-closed）。`test_changelog_gen` 6 例 |
| 缺陷二修复 | `changelog_gen._last_tag` + `_bullets` 接入发布边界（`v2.11.0..HEAD` = 228 条；无 tag 退化全史）。`test_changelog_gen` +2 例（临时真 git 仓） |
| 收口 | `CHANGELOG.md` `[2.12.0]` 由「未发布」翻为「2026-10-05」（正文零改动）；`changes/unreleased/*` 5 条归档 `changes/2.12.0/`；`changes/unreleased/` 留 `.gitkeep` |
| 版本面 | `docs/meta/VERSION-MATRIX.md` v2.12.0 行落日期/✅ 且终端线/顶尖对标/资产契约三行标「随 v2.12.0 收口」；`README.md` 版本块「当前」切 v2.12.0、v2.11.0 转已发布 |
| 冻结链缺陷修复 | `scripts/nf.py`：补登记 `--apply`（此前被 argparse 拒收）；顺序源改读策略件 `freeze_chain`（此前读不存在的 `rg.FREEZE_CHAIN`，必抛内部错误） |
| 冻结链 | `nf release --freeze --apply`（conformance → approve → receipts） |
| Golden Master | `bash scripts/release_freeze.sh v2.12.0`（`01/02/06/07` + `verify.sh` + `desktop/src/core/*.py` 摘要 + `nf sig --verify` 指纹） |
| 审计 | 本件（AUD-0027） |

## 三、验收证据（本机实测）

- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。
- `nf release --json` → `issues: []`、`release_line: 2.12.0`。
- `nf changelog --version 2.12.0 --date 2026-10-05 --write` → **rc=2 / CHANGELOG 零 diff / 条目不归档**（守卫态；生成器对 2.12.0 不落盘）。
- `nf conformance` → conformant 27/27；`nf receipts --scope protocol` 57 件根一致；`nf approve --verify` 有效。
- `test_changelog_gen` 8 例全绿（含真 git 仓边界两例）。

## 四、遗留与设计偏差

1. **与 62 §二·1 字面命令的偏差（有意）**：v2.12.0 的 `nf changelog --write` 保持守卫态、不落盘；原因即上表缺陷一（会丢 333 条）。生成器的首次自动落盘顺延到下一个版本（目标版本节不存在 + `--since v2.12.0` 边界天然正确）。本波**不宣称生成器已为 2.12.0 落盘**。
2. `tag` / `push` 未执行（「除外部」+ 仓库口径 tag 属人）。`.release-frozen/v2.12.0` 为历史时点快照，不随现状更新。
3. 62 §三·② 余量（量化门违反 / 多语协议执行）、§三·① 存量收敛、§二·2 .NET 重冻（本地受阻）不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 发布机制两处缺陷各有判据；版本面三处不悬空；Golden Master 结构完整 |
| 动态可执行 | ↑ | 守卫与提交边界均有真仓/真 git 仓实测；冻结链与快照可复跑 |
| 架构纯度 | → | 修复落在既有 `changelog_gen` 单点，不新增模块/check 序号 |
| 资产密度 | → | 发布收口为主，不新增内容资产 |
| 文档可执行性 | ↑ | `docs/release.md` 口径与实测一致；首例记录可复现（内部档 + 本件） |
