---
id: AUD-0040
title: 复杂度收敛第三批（terminal.dispatch 查表化，55→2）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」复杂度面；承接 AUD-0039。开工依据为内部实测（radon desktop/src：≥C 317 / ≥D 96 / F 20）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/terminal.py:783e4db328ee2405c211666a26a4c450915d6f898be11fe5909461aa533cd6fc
  - protocol/code_metrics_baseline.json:0a9483aa50592982fb1a8b4beb405bd5d833252dc019dc2d3346847e9254cfbc
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因 terminal 模块行数增长按工具指引重冻（见「设计偏差」）。

## 一、内部差距（开工依据）

- `Session.dispatch` 复杂度 **55（F）**：一个 18 分支的 if/elif 链（empty/quit/help/menu/zone/search/commands/map/complete/set/form/cancel/replay/replay-list/history/unknown/run），每加一个意图就要动控制流。

## 二、交付（本批刻意选「消解式」而非「切分式」）

| 面 | 落点 |
|---|---|
| 查表替代分支链 | `_handlers()` 返回「意图 → 处理器」表；`dispatch` 本体只剩 **2** 个判定（表单抢占 + 查表分派） |
| 处理器归一 | `_h_empty`/`_h_quit`/`_h_help` + `_view`（菜单/分区/检索/命令表/地图/补全/重放清单七种只读视图）· `_set_cmd` · `_form_cmd`（含 form/cancel）· `_replay` · `_history_cmd` · `_unknown` · `_run` |
| 横切面抽出 | `_form_preempt`（表单进行中把输入当回答）· `_record`（落历史 + 可重放类别登记）——两者原先都压在 dispatch 尾部 |

## 三、验收证据（本机实测）

- `radon cc desktop/src/core/terminal.py`：`Session.dispatch` **55(F) → 2(A)**；`_handlers` 1(A)；新处理器最大 10（`_run_block`）。
- `radon cc desktop/src`：**≥C 317 → 315 · ≥D 96 → 95 · F 20 → 16**（第三批含前两批累计）。
- `python -m unittest desktop.tests.test_terminal desktop.tests.test_nf_tui` → **189 例全绿**。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. **过程实证（值得记）**：首版漏搬 `set` 意图分支，`/set` 当场落到 run 分支（测试判 `('set', 2) != ('set', 0)`）——查表化重构的典型风险是「表漏项」，本批靠既有 189 例单测兜住。现已把 `set` 补回处理器表。
2. **指标张力（如实记）**：即便用查表，处理器拆分仍使模块行数 2341→2394（+53），已按工具指引重冻。彻底两全需**减少总行数**（合并重复文案/共享渲染），属另一类工程。
3. 余量：`desktop/src` 仍有 **16 个 F**（`interop_export.verify` 168 / `world_model.validate_contract` 105 / `layer_model._rule_issues` 87 …）。
4. 62 §三·②「量化门违反」与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 最大降幅一批（dispatch 55→2）；189 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面（终端分派语义逐条对齐） |
| 架构纯度 | ↑↑ | 「新增意图只加一行」——扩展点从控制流变为数据 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
