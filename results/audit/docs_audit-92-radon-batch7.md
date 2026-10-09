---
id: AUD-0044
title: 复杂度收敛第七批（json_schema._check 84→按关键字类拆分）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」复杂度面；承接 AUD-0043。开工依据为内部实测（radon desktop/src：≥C 312 / ≥D 92 / F 13；下一点 = `json_schema._check` 84）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/json_schema.py:6de58ac9c73b5165d2bcd924fe7f8210e1f5cd6907b26085f8b89e566497f9da
  - protocol/code_metrics_baseline.json:078af3cef3c54af58af44f4e6eac1df58d53ea08a1bea9a52991cd673610ead4
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因该模块行数增长按工具指引重冻。

## 一、内部差距（开工依据）

- `json_schema._check` 复杂度 **84（F）· 单函数 142 行**：JSON Schema 子集的**十一类关键字**（unsupported 登记 / $ref / type / const+enum / 字符串 / 数值 / 数组 / 对象 / allOf·anyOf·oneOf / not）全在一个递归函数里。

## 二、交付

| 面 | 落点 |
|---|---|
| 按关键字类拆 | `_collect_unsupported` · `_check_ref` · `_check_type` · `_check_const_enum` · `_check_string` · `_check_number` · `_check_array`（+`_check_unique_items`/`_check_prefix_items`/`_check_items`）· `_check_object`（+`_check_required_fields`/`_check_property`/`_check_property_names`）· `_check_combinators`（+`_report_combinator`）· `_check_not`；`_check` 本体（**5·A**）只做深度守卫 + 分派 + 汇总 |
| 回退单点化 | 新增 `_obj` / `_arr`（`or {}` / `or []` 回退） |

## 三、验收证据（本机实测）

- `radon cc desktop/src/core/json_schema.py`：`_check` **84(F) → 5(A)**；各关键字校验器最大 10。
- `radon cc desktop/src`：**≥C 312 → 311 · ≥D 92 → 91 · F 13 → 12**；全量最大圈复杂度 **84 → 83**（`pack_combo.combine`）。
- `python -m unittest desktop.tests.test_output_forms desktop.tests.test_trust_boundary desktop.tests.test_schema_reference` → **65 例全绿**。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. **行为等价性**：纯分派重构，递归语义（`_depth+1`、`root_schema`/`unsupported` 透传、错误顺序）逐条保持；65 例单测双覆盖（输出形态 + 信任边界）全绿。
2. **指标方法学（七批定论）**：radon 把每处 `or` 记一个分支，因此「满屏 `or {}`」的文件天然虚高；**按面拆必须配合回退单点化**才能净降 ≥C。
3. 余量：全仓仍有 **12 个 F**，最大 83（`pack_combo.combine`）；`render_markdown` D(26) · `prov_document` D(30) · `openapi_doc` D(25) 等生成器为下一批候选。
4. 62 §三·②「量化门违反」与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑↑ | 最大圈复杂度 150→83（七批累计）；65 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面 |
| 架构纯度 | ↑↑ | 「一类关键字一个校验器」；递归本体退化为分派器 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
