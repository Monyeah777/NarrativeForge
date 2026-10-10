---
id: AUD-0039
title: 复杂度收敛第二批（decisions/endpoint 两 F 拆净，≥C −2 · ≥D −3）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」复杂度面；承接 AUD-0037。开工依据为内部实测（radon desktop/src：≥C 319 / ≥D 99 / F 20）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/decisions.py:63ce73c77315eea97081b72b5f0f7ffb18a94ab33f79e4cc3774ed9ebda69748
  - desktop/src/core/endpoint.py:ddb7e4b0bbb2f60753f249a8b08fc0a1ba9629ff0f63ea24f91ca348204c373e
  - protocol/code_metrics_baseline.json:127153591f3a2e9a3860ac4c2995b2d368fb341d89af20e1a05d78dc344fd946
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因两模块行数增长按工具指引重冻（见「设计偏差」）。

## 一、内部差距（开工依据）

- `decisions.scan` 复杂度 **48（F）**：单函数内混了「单条目四类校验 + 取代链 + 反向引用」三件事。
- `endpoint.scan` 复杂度 **59（F）**：单函数内混了「契约头 + 逐端点四类校验 + 幂等例外」。

## 二、交付

| 模块 | 拆法 | 结果 |
|---|---|---|
| `decisions.py` | 抽出 `_check_entry_id` / `_check_required_fields` / `_check_sections` / `_check_entry_fields` / `_check_entry_evidence` / `_check_entry_lifecycle` / `_check_supersede_chains` / `_check_supersedes` | `scan` 48(F) → **无 ≥C 函数**（最大 10） |
| `endpoint.py` | 抽出 `_check_ep_basics` / `_check_ep_maps_to` / `_check_deprecated_marked` / `_check_ep_deprecated` / `_check_idem_mode` / `_check_idempotency_exceptions` / `_scan_endpoints` / `_check_contract_header` / `_load_ep_tools` / `_ep_stats` | `scan` 59(F) → **无 ≥C 函数**（最大 9） |

## 三、验收证据（本机实测）

- `radon cc desktop/src`：**≥C 319 → 317 · ≥D 99 → 96 · F 20 → 17**。
- 逐模块 radon：`decisions.py` / `endpoint.py` 均**无 ≥C 函数**（前值 48 / 59）。
- `python -c "from core.endpoint import scan; ..."` → **issues 空**（端点契约门禁行为不变）。
- `python -m unittest`（decisions / decision_layer / governance_faces 等）→ 除**待重签的 conformance 报告**两例外全绿；重签后本批以全量 verify 判。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. **顺带修掉一处真缺陷**：`_scan_endpoints` 初版把 `ids` 留在原函数作用域，`_check_idempotency_exceptions` 引用成未定义名（`NameError`）——由本机直跑 `endpoint.scan` 当场抓出，已改为显式返回 `ids`。
2. **指标张力（如实记）**：拆函数必然**增加模块行数**（185→231 / 146→207），已按工具指引重冻。要同时压「模块行数」与「函数复杂度」，只能做**消解式**重构（合并分支/改查表），不能只切分——下批优先选后者。
3. 余量：`desktop/src` 仍有 **17 个 F**（`interop_export.verify` 168 / `world_model.validate_contract` 105 / `layer_model._rule_issues` 87 …）。
4. 62 §三·②「量化门违反」与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 复杂度降幅可量（≥C −2 / ≥D −3）；verify 双绿 |
| 动态可执行 | → | 不涉执行面（判定语义逐条对齐；端点门禁直跑空 issues） |
| 架构纯度 | ↑ | 单函数不再混三件事，边界按「面」切开 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
