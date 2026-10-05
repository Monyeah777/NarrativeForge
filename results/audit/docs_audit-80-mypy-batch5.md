---
id: AUD-0032
title: 类型分批收敛第五批（七模块 mypy 归零；口径更正为错误条数）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」；承接 AUD-0031。开工依据为内部实测（mypy desktop/src **错误条数 95**）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/semantic_conflict.py:eb11b7e32ac07c52400c4c4a457ed877f434decc05a77fd69ef6d0bf2ddcf131
  - desktop/src/core/storage.py:a2077fe8eb54943883b374427168d943c359b5170a187dc7a66c940f425fc436
  - desktop/src/core/receipts.py:afc48b24b00775b04b67200055d954c5ad735eff980921da9571e87ee13f169f
  - desktop/src/core/intake.py:23007fd42c627df44dcce7ffa6873a28f5679a68f3b00351f32e728bb25dcbe0
  - desktop/src/core/world_slots.py:4d7dc220020f9b63b7aeef6f3cd74d1647fe575bbcd804778d61d9de5840aea4
  - desktop/src/core/pipelinerun.py:551bfd5e16424e630cc132fc32926d00bf7031f7e87163ff01cacc30698053bb
  - desktop/src/core/mcp_runtime.py:00e30d272b7badcf6698c10e17a635b0444f393f40883e547d6c9bdb27c6113e
  - protocol/code_metrics_baseline.json:dce9f86a733d0d5f26517b15f5fc31efad5b42819d377e92c90c457cea71b72b

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因 `intake`/`world_slots` 行数与最长函数增长按工具指引评审后重冻。

## 一、口径更正（记一笔）

前四批 AUD-0028…0031 报的 203→112 是 **mypy 输出行数**（`Measure-Object -Line`，含 note 行）；本件起改用**错误条数**（`' error: '` 行）并回溯核对：本批前 **95** 条、本批后 **68** 条（本批 **27** 条）。两条口径不可混用，此前报告的「行」字面没错，但容易与条数混淆，故在此更正。

## 二、交付（本批七模块）

| 模块 | 修前 | 修法 |
|---|---|---|
| `desktop/src/core/semantic_conflict.py` | 3 | `fences`/`buf`/`out`/`publishers` 显式类型（PEP 585 小写） |
| `desktop/src/core/storage.py` | 3 | 三处 `out` 显式 `List[Path]/[AssetPack]/[Preset]` |
| `desktop/src/core/receipts.py` | 4 | `merkle_root` 可空返回在非空切片处补 `or b""`（契约上不可达 None） |
| `desktop/src/core/intake.py` | 3 | `channels` 拆原始值再判型 |
| `desktop/src/core/world_slots.py` | 3 | 两处 `slots` 拆原始值再判型 |
| `desktop/src/core/pipelinerun.py` | 5 | `notes` 由 `List[str]` 更正为 `List[Dict[str, str]]`（真源全为 dict）；`total` 显式 `Dict[str, Any]` |
| `desktop/src/core/mcp_runtime.py` | 6 | `out.sort` 键 `str()`；`payload`/`item`/`out` 显式 `Dict[str, Any]` |

## 三、验收证据（本机实测）

- `python -m mypy desktop/src --ignore-missing-imports` → 错误条数 **95 → 68**（七受改模块各自 rc=0）。
- `python -m unittest`（本批相关 7 组）→ **106 例全绿**。
- `python scripts/code_metrics.py` → `intake`（96→97、最长函数 50→51）/`world_slots`（83→85、30→32）按工具指引重冻。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. 余 **68 条**（`terminal.py` 25 / `atomic_write.py` 6 等）+ radon 复杂度。
2. `pipelinerun.notes` 的 `List[str]`→`List[Dict[str,str]]` 是**如实更正**（三处 append 全为 dict），非放宽。
3. 62 §三·② 余量与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 七模块 mypy 归零；106 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面 |
| 架构纯度 | → | 只改类型写法与默认值补齐 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
