---
id: AUD-0031
title: 类型分批收敛第四批（lsp / purity_scan / asset_contract 归零）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」；承接 AUD-0030。开工依据为内部实测（mypy desktop/src 137 条）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/lsp.py:304e8edabe0c2878bc6fe997d957281cdc8b7cdfa7474b271bc25871690bc107
  - desktop/src/core/purity_scan.py:dcb81f0bab7511d9861e44e0511fcb7b1ce18d26213415a5add4cd533f891c30
  - desktop/src/core/asset_contract.py:9a4e9ee0e73d03032218af84a0d6def58ab62b70bb84c8f697ab9f5e0743249c
  - protocol/code_metrics_baseline.json:078af3cef3c54af58af44f4e6eac1df58d53ea08a1bea9a52991cd673610ead4
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因 `asset_contract`/`purity_scan` 行数增长按工具指引评审后重冻。

## 一、内部差距（开工依据）

- 承接 AUD-0030：`mypy desktop/src` 137 条；本批取误差集中且判据在场的三模块（`lsp` 8 / `purity_scan` 7 / `asset_contract` 11）。

## 二、交付

| 模块 | 修前 | 修法 |
|---|---|---|
| `desktop/src/core/lsp.py` | 8 | `read_message` 返回哨兵 `_BAD_FRAME`（`object()`），返回标注由 `Optional[Dict]` 改为 `Any`（哨兵语义不变）；规则集键取 `str(d.get("code"))` |
| `desktop/src/core/purity_scan.py` | 7 | `shell/private/seen` 拆三行显式标注；`delta`/`stats` 显式 `Dict[str, Any]`；补 `Any/Dict/List` typing 导入 |
| `desktop/src/core/asset_contract.py` | 11 | `_read` 后的 `text`/`sch_text` 统一补空串默认（`or ""`，原路径契约上非空）；`seeds`/`pairs` 显式标注 |

## 三、验收证据（本机实测）

- `python -m mypy desktop/src --ignore-missing-imports` → **137 → 112 行**（三受改模块各自 rc=0）。
- `python -m unittest desktop.tests.test_lsp desktop.tests.test_purity_scan desktop.tests.test_asset_contract` → **78 例全绿**。
- `python scripts/code_metrics.py` → `asset_contract`（737→740、最长函数 44→45）/`purity_scan`（530→532）按工具指引重冻。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. 累计收敛 **91/203**（19+23+24+25）；余 112 条（集中于 `terminal.py` 31）与 radon 复杂度继续分批。
2. `read_message` 的 `Any` 返回是有依据的放宽：真源本身用 `object()` 哨兵（调用方 `is _BAD_FRAME` 判定），强标 `Dict|None` 与实现不符。
3. 62 §三·② 余量与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 三模块 mypy 归零；78 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面 |
| 架构纯度 | → | 只改类型写法与默认值补齐 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
