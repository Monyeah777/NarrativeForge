---
id: AUD-0037
title: 复杂度收敛第一批（import_adapter.parse_ccv3 46→20，含死代码删除）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」复杂度面；开工依据为内部实测（radon desktop/src：≥C 319 / ≥D 99，最大 interop_export.verify 168）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/import_adapter.py:f5fb23d18e5d54eb561d48aee6d4556917de7cc63c1b0c33da6035e39222cbf7

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；本轮模块行数净减，`code_metrics` 未触发重冻。

## 一、内部差距（开工依据）

- `desktop/src` radon：**C=220 / D=59 / E=20 / F=20**（≥C 319 · ≥D 99）。`import_adapter.parse_ccv3` 复杂度 **46（F）**，主因是 chara 与 world 两段**逐字重复**的条目入册循环，外加一个**从未被调用**的内嵌 `place`。

## 二、交付

| 面 | 落点 |
|---|---|
| 提取单点 | `_record_asset`（资产条目入册）· `_place_module`（归层/入 extra）· `_skip_entry`（world 侧去重）——三者各自复杂度 <11 |
| 合并重复 | `_ingest_entries(... dedupe=)` 承接 chara/world 两段同构循环（`dedupe=True` 时保留原「无 id / 已在册即跳过」语义） |
| 删死代码 | 内嵌 `place` 定义后**从未被调用**，删除；原逻辑由 `_place_module` 承接 |

## 三、验收证据（本机实测）

- `radon cc desktop/src/core/import_adapter.py`：`parse_ccv3` **46(F) → 20(C)**；该文件 ≥C 函数仍为 4（无新增超标函数）。
- `radon cc desktop/src`：**≥C 319（持平）· ≥D 99 → 98 · F 20 → 19**。
- `python -m unittest desktop.tests.test_import_adapter` → **24 例全绿**。
- `python scripts/code_metrics.py` → 通过（模块行数净减，未触发棘轮）。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差（如实）

1. **本批只动了 1 个 F**：≥C 持平是因为「一个 F 拆成若干 C」几乎必然把计数搬平——要真降 ≥C，得把拆出来的助手也压到 <11 或重构到 B 级；本件已按此做（三个助手均 <11），但 `parse_ccv3` 本体仍停在 20（C）。
2. 余量：`interop_export.verify`（168）· `world_model.validate_contract`（105）· `layer_model._rule_issues`（87）等 18 个 F 未动；复杂度面仍是**逐批**工程。
3. 62 §三·② 余量与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 最差函数降级可量；24 例单测 + 全量 verify 双绿 |
| 动态可执行 | → | 不涉执行面（`parse_ccv3` 两段循环语义逐条对齐） |
| 架构纯度 | ↑ | 删掉一处从未被调用的死函数 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
