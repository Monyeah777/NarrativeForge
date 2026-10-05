---
id: AUD-0042
title: 复杂度收敛第五批（world_model.validate_contract 105→按面 12 个校验器）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」复杂度面；承接 AUD-0041。开工依据为内部实测（radon desktop/src：≥C 314 / ≥D 94 / F 15；下一点 = `world_model.validate_contract` 105）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/world_model.py:20108d40e0f708716df4c1b6c3df66081d14c51fdc2064d5bd32b77a5af9987c
  - protocol/code_metrics_baseline.json:f778061df0ffc6781829ce67de4f9222666e1f3f3656b2c2bac08aa469eaa019

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因该模块行数增长按工具指引重冻。

## 一、内部差距（开工依据）

- `world_model.validate_contract` 复杂度 **105（F）· 单函数 229 行**：abstract_state / variables / initial / transition / phases / 可达性 / invariants / checks / slot_registry **九个面**全挤在一个函数里。
- 与第四批同源问题：**radon 把每处 `or` 记为一个分支**，而该函数的形态校验满屏 `not isinstance(x, str) or not x.strip()`（全文件 13 处）。

## 二、交付

| 面 | 落点 |
|---|---|
| 按契约面拆 | `_abstract_parts` · `_variables`/`_check_variable` · `_check_initial_keys`/`_check_initial_values` · `_transition_parts` · `_phases`/`_check_phase` · `_check_reachability` · `_check_invariants` · `_check_checks`/`_check_check_item` · `_check_slot_registry` |
| 判据单点化 | 新增 `_nonempty`（「非空字符串」），13 处 `not isinstance(x, str) or not x.strip()` 收成一处；再抽 `_check_slot_value` / `_reachable_from` / `_check_values` / `_check_finite_sequence` 二次消解 |

## 三、验收证据（本机实测）

- `radon cc desktop/src/core/world_model.py`：`validate_contract` **105(F) → 不在 ≥C 名单**（B 以下）；新校验器最大 10。
- `radon cc desktop/src`：**≥C 314 → 313 · ≥D 94 → 93 · F 15 → 14**；全量最大圈复杂度 **150 → 87**（`layer_model._rule_issues`）。
- `python -m unittest desktop.tests.test_world_model` → **20 例全绿**。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. **行为等价性**：`_check_phase` 原先「相位名非法 → `continue`（不建边）」，改为 `return` 提前退出；`_check_variable` 的 slot 分支整体搬到 `_check_slot_value`（含 None 放行）。20 例单测覆盖全部九个面，无红。
2. **指标方法学（承接第四批）**：本批再次验证「按面拆对 ≥C 计数是负向的，必须配合判据单点化才能净降」——本批若只拆不收，≥C 会升 4。
3. 余量：全仓仍有 **14 个 F**，最大 87（`layer_model._rule_issues`，同属「`or`/形态判据满屏」型，可复用本批手法）。
4. 62 §三·②「量化门违反」与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑↑ | 最大圈复杂度降至 87（起点 150）；20 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面（九面校验点与消息逐条对齐） |
| 架构纯度 | ↑↑ | 「一个契约面一个校验器」；形态判据从 13 处调用点收成 1 个函数 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
