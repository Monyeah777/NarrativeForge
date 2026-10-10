---
id: AUD-0041
title: 复杂度收敛第四批（interop_export.verify 168→按面 13 个校验器）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」复杂度面；承接 AUD-0040。开工依据为内部实测（radon desktop/src：全仓最大圈复杂度 **150**、≥C 315 / ≥D 95 / F 16）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/interop_export.py:520aaf0edb53d5ab679d3a1568c315f45ce8301ead3df90411e3e67572dc269a
  - protocol/code_metrics_baseline.json:2c2a8b4aa398f2d37947cd6744e7570c4a09c506fee6e8b181292849a7e5fc37
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因该模块行数增长按工具指引重冻。

## 一、内部差距（开工依据）

- `interop_export.verify` 复杂度 **168（F）· 单函数 234 行**：十三个派生面（OpenAPI / AsyncAPI / in-toto / SBOM / 确定性 / SLSA / A2A / PROV / CycloneDX / VC / C2PA / CID / 决策面）的校验全挤在一个函数里。
- **本批新发现**：radon 把每处 `or` 记为一个分支，而导出面满屏 `x.get(...) or {}` / `or []`——该函数 168 的复杂度**大半来自「空值回退」而非真正的业务分支**。

## 二、交付

| 面 | 落点 |
|---|---|
| 按派生面拆校验器 | `_check_openapi` / `_check_asyncapi` / `_check_intoto` / `_check_sbom` / `_check_determinism` / `_check_slsa` / `_check_a2a` / `_check_prov` / `_check_cyclonedx` / `_check_vc` / `_check_c2pa` / `_check_cid` / `_check_decision`；`verify` 只负责读真源 + fail-closed + 依次分派 + 汇 stats |
| 回退单点化 | 新增 `_obj` / `_arr`（`x if isinstance(x, T) else 空`），把 70 处 `or {}` / `or []` 从调用点收成两个函数 |
| 二次消解 | 四个仍在 C 的校验器再抽 `_check_prov_relations` / `_check_cyclonedx_deps` / `_vc_issuer_ok` / `_c2pa_hash`，全部落到 B 以下 |

## 三、验收证据（本机实测）

- `radon cc desktop/src`：**最大圈复杂度 150 → 113**（本仓全局最大值）；**≥C 315 → 314 · ≥D 95 → 94 · F 16 → 15**。
- 该文件：`verify` 168(F) → 全 13 个校验器均 <11（B 以下）；余下 C/D 是其**上游文档生成器**（`prov_document` 30 / `openapi_doc` 25 / `decision_surface` 19 …）。
- `python -m unittest desktop.tests.test_interop_export` → **25 例全绿**。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. **过程实证**：把 `or {}` 批量换成 `_obj(...)` 的脚本正则**误伤两处**——`(_obj(a)).get("k") or {}` 被拼成 `(_obj(a))._obj(get("k"))`，5 例单测当场 `AttributeError` 判红；已改回 `_obj(_obj(a).get("k"))`。结论：批量改写必须**逐点复核 + 靠测试兜底**。
2. **行为偏差（如实记）**：`(v or {})` 对「真值非字典」（如非空列表）会原样返回并让后续 `.get` 抛错；`_obj` 改为返回 `{}`。即**畸形真源**从崩栈变为空面——测试的变异样本覆盖 5 类畸形，全部仍判红（门禁不失明）。
3. **指标方法学**：本批证明「按面拆」对 **≥C 计数**是负向的（一个 F 变若干 C），必须配合「回退单点化」这类**消解**才能净降；后续批次以「最大圈复杂度 + ≥D」为主要口径。
4. 余量：全仓仍有 **15 个 F**、最大 113（`world_model.validate_contract` 等），逐批推进。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑↑ | 全仓最大圈复杂度 150→113；25 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面（校验点与消息逐条对齐） |
| 架构纯度 | ↑↑ | 「一个派生面一个校验器」；空值回退从 N 处调用点收成 2 个函数 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
