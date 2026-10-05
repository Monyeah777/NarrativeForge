---
id: AUD-0028
title: 类型分批收敛第一批（io_types / world_model / knowledge 三模块 mypy 归零）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」；开工依据为内部实测（mypy desktop/src 203 条，审计-64 挂账）。本批只做行为不变的类型收敛，不引外部。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/io_types.py:09296daf865db85bda582fb646cece708c51f97e190a9e91c0eecd07252475f7
  - desktop/src/core/world_model.py:55ac4cbfaa4c81a9d04e6d9c90ab749ddeb418ca27863fd552028289eebee42c
  - desktop/src/core/knowledge.py:01677496cd14fa3b3e2cf37cc396056634ba5a5ba82cbb9502721768f74485ad
  - protocol/code_metrics_baseline.json:777b3636b9e986c12b938597708ee75422404a1115f2a0e7ae74833aa1800b2c

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因本轮模块增长按工具指引「评审后重冻」。

## 一、内部差距（开工依据）

- 审计-64（AUD-0016）挂账：mypy 106 条（数字随代码增长，本波实测 **203 条 / desktop/src**）、radon ≥C/D 存量。收敛路径 = 逐文件读语义 + 分批改；本批为**第一批**，取三只小而独立、改动可机械复核的模块。

## 二、交付

| 模块 | 修前 | 修法（行为不变） |
|---|---|---|
| `desktop/src/core/io_types.py` | 4 | 正则 `match` 存变量后 `if m:` 再取 `group`；`inject` 里 `block` 变量改名（`block_text`）消除同函数两型复用 |
| `desktop/src/core/world_model.py` | 4 | 分支变量显式 `Any`；`flow_spec` 改名（与后段 `spec` 解耦）；`_matches` 的 `kind` 取 `or ""` |
| `desktop/src/core/knowledge.py` | 11 | `fresh`/`prom`/`rev`/`cog` 四处「isinstance 守卫 + 字典」拆成先取原始值再判型（消除 `Any \| dict \| None` 的 union-attr）；`records` 同样拆变量 |

## 三、验收证据（本机实测）

- `python -m mypy desktop/src --ignore-missing-imports` → **203 → 184 行**（三个受改模块各自 **rc=0**）。
- `python -m unittest desktop.tests.test_io_types desktop.tests.test_world_model desktop.tests.test_knowledge` → **65 例全绿**。
- `python scripts/code_metrics.py` → 模块行数按工具指引评审后重冻（`io_types` 250→252 / `knowledge` 482→487、最长函数 100→104）。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. 本批只收敛 **19 条**（203→184）；radon 复杂度与其余 mypy 存量按同法逐批收，未在本件宣称收敛完成。
2. 修法是**类型面收敛**，不改任何运行时分支语义；唯一语义等价替换是 `_matches(..., spec.get("kind") or "")`（原 `None` 与 `""` 在该函数都落到默认 `False` 分支）。
3. 62 §三·② 余量（量化门违反 / 多语协议执行）与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 三模块 mypy 归零；相关 65 例单测与全量 verify 双绿 |
| 动态可执行 | → | 本轮不涉执行面 |
| 架构纯度 | → | 只改类型写法与变量命名，不加层 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
