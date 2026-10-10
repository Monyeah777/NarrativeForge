---
id: AUD-0043
title: 复杂度收敛第六批（layer_model._rule_issues 87→L1-L10 十三个校验器）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」复杂度面；承接 AUD-0042。开工依据为内部实测（radon desktop/src：≥C 313 / ≥D 93 / F 14；下一点 = `layer_model._rule_issues` 87）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/layer_model.py:4b09c50a53884d1e3a5ed5541e42cc4bf8499bc031d5e00eebf38bc66c9b40d1
  - protocol/code_metrics_baseline.json:2c2a8b4aa398f2d37947cd6744e7570c4a09c506fee6e8b181292849a7e5fc37
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因该模块行数增长按工具指引重冻。

## 一、内部差距（开工依据）

- `layer_model._rule_issues` 复杂度 **87（F）· 单函数 178 行**：L1–L10 十条阶梯规则全挤在一个函数里。
- 与第四/五批同源：`or {}` / `or []` 空值回退满屏（本函数 17 处），radon 每处记一个分支。

## 二、交付

| 面 | 落点 |
|---|---|
| 按 L1-L10 拆 | `_rule_l1`（+`_rule_l1_assets`/`_rule_l1_files`）· `_rule_l2` · `_rule_l3` · `_rule_l4`（+`_walk_cycle`）· `_rule_l5` · `_rule_l6` · `_rule_l7` · `_rule_l8`（+`_collect_judged_refs`）· `_rule_l9` · `_rule_l10`；`_rule_issues` 只做缓存/派生面准备与依次分派 |
| 判据单点化 | 新增 `_obj` / `_arr`（本函数 17 处回退收成两处） |

## 三、验收证据（本机实测）

- `radon cc desktop/src/core/layer_model.py`：`_rule_issues` **87(F) → 不在 ≥C 名单**；新校验器最大 9。
- `radon cc desktop/src`：**≥C 313 → 312 · ≥D 93 → 92 · F 14 → 13**；全量最大圈复杂度 **87 → 84**（`json_schema._check`）。
- `python -m unittest desktop.tests.test_layer_model` → **27 例全绿**。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. **行为偏差（如实记）**：`_obj`/`_arr` 对「真值非字典/非列表」的畸形真源从原 `or` 语义（原样返回）改为回退空面——与第四/五批同一处口径，本批 27 例单测（含 L1-L10 各面变异）全绿。
2. **指标方法学**：六批一致结论——「按面拆对 ≥C 是负向的，必须配合回退/形态判据单点化才能净降」。
3. 余量：全仓仍有 **13 个 F**，最大 84（`json_schema._check`）；`render_markdown` D(26)、`patterns` D(22) 等文档生成器属下一批候选。
4. 62 §三·②「量化门违反」与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑↑ | 最大圈复杂度 150→84（六批累计）；27 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面（十条规则校验点与消息逐条对齐） |
| 架构纯度 | ↑↑ | 「一条阶梯规则一个校验器」；空值回退单点化 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
