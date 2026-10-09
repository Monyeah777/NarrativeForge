---
id: AUD-0033
title: 类型分批收敛第六批（terminal / assemble_plan / asset_ledger / atomic_write 归零）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」；承接 AUD-0032。开工依据为内部实测（mypy desktop/src 错误条数 68）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/terminal.py:783e4db328ee2405c211666a26a4c450915d6f898be11fe5909461aa533cd6fc
  - desktop/src/core/assemble_plan.py:b628126479e1d2ac6f58bfe7967df67b43ed184007f981db69557856df39363e
  - desktop/src/core/asset_ledger.py:2f679a74ebf76707aabd873136976b57aa395e57c92683cf76720f4130bd28c5
  - desktop/src/core/atomic_write.py:5bc7318e23a5e6dbd5433624186df8584e86d44b13a7a11e93ddea0790617df0
  - protocol/code_metrics_baseline.json:0a9483aa50592982fb1a8b4beb405bd5d833252dc019dc2d3346847e9254cfbc
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因 `assemble_plan`/`atomic_write`/`terminal` 行数增长按工具指引评审后重冻。

## 一、内部差距（开工依据）

- 承接 AUD-0032：`mypy desktop/src` 错误条数 68；本批取 `terminal`（25，最大块）+ `assemble_plan`/`asset_ledger`/`atomic_write`（各 3/3/6）。

## 二、交付

| 模块 | 修前 | 修法 |
|---|---|---|
| `desktop/src/core/terminal.py` | 25 | **根因是四张模块级声明表**（`ZONES`/`FAMILIES`/`FORMS`/`TERMINAL_BASELINE` + `SLASH_WORDS`）无标注，值被推成 `object` 并沿调用面扩散；补 `tuple[dict[str, Any], ...]` 后一次性消掉 17 条。余：`seen`/`history`/`commands` 标注、`self.active_form` 显式可空、两处表单取值改写 |
| `desktop/src/core/assemble_plan.py` | 3 | `questions`/`answers` 参数由 `List[str]` 改 `Sequence[str]`（默认 `()` 合法）；`pkg`/`pipeline` 显式可空；`if pkg is None or not matched` 收窄 |
| `desktop/src/core/asset_ledger.py` | 3 | `_load_for_update` 的 `ledger_path` 如实标 `str \\| None`（函数内本就 `or default_...`）；`issues` 标注 |
| `desktop/src/core/atomic_write.py` | 6 | 读回函数由「`**kwargs` 三元」拆成 binary/text 两分支（消 `open` 重载歧义）；`fcntl` 两行加 `# type: ignore[attr-defined]`（typeshed 平台面） |

## 三、验收证据（本机实测）

- `python -m mypy desktop/src --ignore-missing-imports` → 错误条数 **68 → 31**（四受改模块各自 rc=0）。
- `python -m unittest desktop.tests.test_terminal desktop.tests.test_nf_tui desktop.tests.test_assemble_build desktop.tests.test_asset_ledger desktop.tests.test_atomic_write` → **237 例**（中途一次 1 例红，见下）。
- **过程实证（值得记）**：`terminal` 两处表单取值首版写成 `active.get("answers") or {}`——空字典是假值，`or` 会返回**新字典**，于是 `_answer_form` 的写入不再落回 `self.active_form["answers"]`，`FormTest.test_session_form_flow_executes_after_confirm` 当场判红；改为 `active["answers"] if active else {}`（保留原对象引用）后转绿。这条正是「行为不变」承诺的看门判据。
- `python scripts/code_metrics.py` → 三模块行数增长按工具指引重冻。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. 余 **31 条**（`nf.py`/`scripts` 面与零散 core）；radon 复杂度未动。
2. `atomic_write` 的 `fcntl` 用**两处** `# type: ignore`（仓库首次引入该逃生口）：理由是 typeshed 的 `fcntl` 面随平台收窄，而该分支只在 Unix 执行；已就地写明，不建豁免表。
3. 62 §三·② 余量与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑↑ | 四模块 mypy 归零（含最大块 terminal）；237 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面 |
| 架构纯度 | → | 只改类型写法与取值方式（含一处别名回归的修正） |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
