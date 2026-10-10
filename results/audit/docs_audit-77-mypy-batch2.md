---
id: AUD-0029
title: 类型分批收敛第二批（domain_pack / prose_lint 两模块 mypy 归零）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」；承接 AUD-0028。开工依据为内部实测（mypy desktop/src 184 条），只做行为不变的类型收敛。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/domain_pack.py:336cbd097598ec272f15bfb2a912da3289ad95b5b1172a8c49948683df546a6a
  - desktop/src/core/prose_lint.py:d3d6789bc60e9fe664fa4c7af24c10d380f9aced70f2a494e812246da74d1a69
  - protocol/code_metrics_baseline.json:68f54b9b0e43aeddcca49e89a13226e4789748db6d7e065749faa0d6b27fd506
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因模块行数增长按工具指引评审后重冻。

## 一、内部差距（开工依据）

- 承接 AUD-0028：`mypy desktop/src` 184 条；本批取两只误差集中、改动可机械复核的模块（`domain_pack` 17 条、`prose_lint` 2 条）。

## 二、交付

| 模块 | 修前 | 修法（行为不变） |
|---|---|---|
| `desktop/src/core/domain_pack.py` | 17 | `pipe`→`pipe_id`（与上面的正则 `Match` 解耦）；`prereq` 显式 `Dict[str, List[str]]`；`std`→`std_entry`（与 `for sid, std in bound.items()` 解耦）；`sub_ev` 分支统一为 tuple；`doc` 显式 `Dict[str, Any]` |
| `desktop/src/core/prose_lint.py` | 2 | `summarize` 里 `rule = str(f["rule"])` 后再计数（键由 object 归 str） |

## 三、验收证据（本机实测）

- `python -m mypy desktop/src --ignore-missing-imports` → **184 → 161 行**（两受改模块各自 rc=0）。
- `python -m unittest desktop.tests.test_prose_lint desktop.tests.test_domain_pack` → **30 例全绿**。
- `python scripts/code_metrics.py` → `prose_lint` 模块行数 225→226 按工具指引重冻。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. 累计收敛 **42/203**（AUD-0028 19 + 本件 23）；radon 复杂度与 rest mypy 存量按同法继续分批。
2. 修法均为类型写法/变量命名级改动；`sub_ev` 由 list 改为 tuple 仅换容器类型（下游只迭代/取元素），语义等价。
3. 62 §三·② 余量与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 两模块 mypy 归零；30 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面 |
| 架构纯度 | → | 只改类型写法与变量命名 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
