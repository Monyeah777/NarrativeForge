---
id: AUD-0035
title: 类型收敛扩面到 scripts（19 条清零，8 个脚本）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」；承接 AUD-0034（desktop/src 已清零）。开工依据为内部实测（mypy scripts 错误条数 19）。
verdict: pass
auditor: 本轮执行者
subjects:
  - scripts/rebuild_selfcontained_sample.py:a03129592c21f6db459a6b69fcc9819e71aeb80418517fb9a43c2bbfc81c8e68
  - scripts/fde_sample_run.py:a891a76e559c4d68260ecc8ea03b9d76109a793e859e53cb42a0bc5b0edf9560
  - scripts/serve_decision_model.py:69c401a98c6fcc81a7a04a274f061e65e20d0190bb38ccff1ba3fe2f6fa03db2
  - scripts/interop_thirdparty_kit.py:05772f664348a3682b94a0f5dceaa5e9a39a91c0701ba7614bf121ac5f450202
  - scripts/build_verification_cards.py:08e105daceb38ca1b907193b408dfeaec8ea5cb8943b47902c5301d2107d0960
  - scripts/geo_export.py:616992be1e6f5e8251b5a9aa98abc8d27dfee22ddb9152a335538f17e28ea06a
  - scripts/nf.py:afd588678bd58127a051f4dabef7ccfdae5be784ba4b75eeaa24cb79a22d13f4
  - scripts/check_external_links.py:ce954ac27b7fdc632b48e68a8867361f3415b5e2920d4d4dfd2f306574a60909
  - protocol/code_metrics_baseline.json:0a550fc7daa2118e73018333d4b871ba07f2b298f03e8cce269b031337384290

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因 4 个脚本行数或圈复杂度增长按工具指引重冻。

## 一、结果

`python -m mypy scripts --ignore-missing-imports` 错误条数 **19 → 0**。

## 二、交付

| 脚本 | 修法 |
|---|---|
| `scripts/nf.py` | ① `argparse._`/`ngettext` 两处**有意猴补**补 `# type: ignore[attr-defined(,assignment)]`（原 ignore 只盖 assignment）；② daemon bench 的 `rows` 显式 `List[Dict[str, Any]]`；③ `signal.SIGPIPE` 改 `getattr(..., None)` 判空（Windows 无该信号，原靠 except 兜住，行为等价） |
| `scripts/check_external_links.py` | `breaker` 参数如实标 `Optional[DomainBreaker]`（函数内已 `breaker=None 即不熔断`）；报告接收端显式 `Dict[str, Any]`——7 条一并消 |
| `scripts/rebuild_selfcontained_sample.py` | 标记行改为显式循环取 `group`（消 `Match\\|None`）；管线段收尾围栏变量 `cl`→`close_idx`（与上文同名变量解耦） |
| `scripts/fde_sample_run.py` | `module_from_spec` 前补 `spec is None` 守卫（带修复指引） |
| `scripts/serve_decision_model.py` | 进程内单例 `AGENT: Any = None`（加载前恒为 None，`predict` 前由 500 兜底） |
| `scripts/interop_thirdparty_kit.py` | 循环变量 `e`→`ent`（避开同函数 `except ... as e` 的变量删除语义） |
| `scripts/build_verification_cards.py` | 基线两处 `re.search` 结果判空（缺常量即带修复指引退出） |
| `scripts/geo_export.py` | 绑定行显式 `List[Dict[str, Any]]` 后再排序（消 `object` 算术） |

## 三、验收证据（本机实测）

- `mypy scripts` 错误条数 **19 → 0**。
- `python -m unittest`（本批相关 4 组）→ **65 例全绿**。
- `python scripts/code_metrics.py` → 4 脚本按工具指引重冻。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. `desktop/tests` 仍有 66 条 mypy（测试面，未纳入本线）；radon 复杂度仍为存量。
2. `nf.py` 的两处 `# type: ignore` 是**猴补 stdlib** 的必要逃生口（模块级补丁，typeshed 不可能知道）；已在**紧邻注释**里写明短路理由，不建豁免表。
3. 62 §三·② 余量与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | `scripts` mypy 归零；65 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 两处守卫收窄到原路径，信号分支语义等价 |
| 架构纯度 | → | 只改类型标注/取值方式 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
