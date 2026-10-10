---
id: AUD-0026
title: 文档面 i18n 扩容（mcp/terminal/layers 三份指南 en/ja）+ 演练扩面（跨管线串号 / 资产键编造 / 回合级 R1–R4 样本）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——对应 62 计划 §二·3 文档面 i18n 扩容与 §三·② 演练仿真扩面；开工依据为内部差距实证（文档面仅 2 份指南有译件；失范类型与回合级样本覆盖不全），不引外部背书。
verdict: pass
auditor: 本轮执行者
subjects:
  - protocol/locales.json:27383fbcc44c6fbcae39156ad2d24f69ae9dd933b3ebaabffc04d99e8b17c05a
  - docs/locales.md:cf3a21039dad98832b3cd92ead92adaa6559b38bd9c96006fea87f0af81a6dc7
  - docs/en/locales.md:348a2b32a6f04cf830cb332b47b0b05f59265332c2fe37ec79ee63c0563168fa
  - docs/ja/locales.md:7f870e599fc00ab10c998eb115350b7ceda21655a2ebfcf870f6a2b8300e5f34
  - docs/en/mcp.md:c27f0e22f7bdcb6dd983ff1e88db87d06b1b76ef7fec3b92d5ec63fa02be0c2d
  - docs/ja/mcp.md:477e3fddc1a8c67d1f24e8d6779fe6b5d93dae30a0221ff3f1fea93f99c7edf0
  - docs/en/terminal.md:19fd82dd77b72366c4fb0cde2ce62294f9d14b7eac10242d1bf2f08480fee862
  - docs/ja/terminal.md:673e4869c326ba148893df4ed4e42f35a929f245269ce05ad9f7315235345783
  - docs/en/layers.md:f92b4dcea20068c253a2a7455d21fb63bbf3c9493e80f81cb6460d4e464d6c20
  - docs/ja/layers.md:1f3edfbad694b98228bb720574a54267f7b3b544fbc89436179d77950fde3d57
  - docs/44_M1_执行演练扩展.md:12e58d6ae4d1cab23faaaff5e98d0a0bc9a6455c7a17552bab0d57e0cf30866c
  - docs/45_M2_回合级drill.md:55bf60d989aba4fe653bd30396b59c12af587151a3b100da9b65f3d2979429e0
  - desktop/src/core/execution_drill.py:7f291a20d779213d3acedaaf042722d4ec7223ba3333ee2477be6b5285152dea
  - desktop/src/core/drill_fidelity.py:42d1064477b9f14821e222c3abe89b27d5b624f011c19d166d7077b1aff7ee71
  - desktop/tests/test_execution_drill.py:f5f880b8eae0b5b00c7c6a94376922e291d079a9fd1c2c50ae1d8adf7eaaa2b2
  - desktop/tests/test_round_drill.py:67e963dace7dfdbf1a77385bc18dcc230ad102cf3934ea93209c49cb5cf3bab3
  - desktop/tests/fixtures/execution/p04_drill_cases.json:9237e2713bab59df20ed8cc4df18f8a4f9bd1fe0437a4acf642b03ccdd9c5d07
  - desktop/tests/fixtures/execution/rounds/bad_r2.json:9498fba916ea03db23cd75fb9279335ad92127850aab54adb73f5032f6b20d24
  - desktop/tests/fixtures/execution/rounds/bad_r3.json:985bc52b5a755bb6ca33a94817cb706beb9bfe6d9d13f7933f7bbcfe0ca46e8a
  - desktop/tests/fixtures/execution/rounds/gap_ok.json:55d09b1102f7729f31439fd68cf8ad25c7e0db55e0a9064db713a0ee582d4914
  - protocol/code_metrics_baseline.json:127153591f3a2e9a3860ac4c2995b2d368fb341d89af20e1a05d78dc344fd946
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物：`protocol/RECEIPTS.json`、`protocol/conformance_report.json`、`protocol/generated/*`、`results/interop/*`、`protocol/approvals/*` 均为可复算投影或每次重签即变；`protocol/drill_fidelity.json` 由 `scripts/drill_fidelity.py` 从样本重算，同样不入绑定。

## 一、内部差距（开工依据）

1. **文档面 i18n 只覆盖 2 份指南**（`docs/locales.md` 自述「发布」与「本地化」），而对接方第一跳 `docs/mcp.md`、agent 人机入口 `docs/terminal.md`、架构面 `docs/layers.md` 仍单语——注册机制（文件即真源 + 声明式增长）已立，缺的是译件本身。
2. **执行失范类型只有 4 类**（句子级 fabricated_id / browse_repeat / no_citation / semantic_misalignment），62 计划点名的「跨管线串号」「资产键编造」无判据——编号真实但属其它管线、资产键编造会**静默通过**。
3. **回合级样本只覆盖 R1**（`bad.json` 同时命中 R1/R3；R2 与 R4 跳号无语料）——**样本集覆盖 ≠ 断言集覆盖**。

## 二、交付

| 面 | 落点 |
|---|---|
| 文档面译件 | 新增 `docs/en/{mcp,terminal,layers}.md` + `docs/ja/{mcp,terminal,layers}.md`（逐节镜像；代码块/命令/路径/内联锚点逐字保留） |
| 语言面注册 | `protocol/locales.json` 文档译件 2 → 5 份（10 件译件）；`docs/locales.md` 及两语译件覆盖面声明同步；`nf locales --write` 重签 source_sha256 |
| 句子级失范扩容 | `core/execution_drill.py` 增 `cross_pipeline_id`（跨管线串号：编号真实但属其它管线）与 `fabricated_asset_key`（资产键编造）两条硬断言；`RULE_LAW` 4 → 6 条（L1×1 / L2×3 / L3×1 / L4×1，无越级） |
| 演练语料 | `p04_drill_cases.json` 8 → 12 例（+2 失范 +2 变异对照），新规则各有「命中 + 不误报」成对样本 |
| 回合级覆盖 | `rounds/` 新增 `bad_r2.json`（R2）/ `bad_r3.json`（R3）/ `gap_ok.json`（R4 跳号仅 WARN、verdict 仍合规） |
| 判据 | `test_execution_drill` / `test_round_drill` 增例；判级映射断言 4 → 6；`drill_fidelity._exec_sets` 透传 other_ids/asset_keys |
| 量化 | `protocol/drill_fidelity.json` 重算：执行 60 例 + 回合 5 例 = **65/65（100%）** |
| 文档 | `docs/44_M1_执行演练扩展.md` / `docs/45_M2_回合级drill.md` 口径同步 |
| 基线 | `protocol/code_metrics_baseline.json` 重冻（新增规则使 `execution_drill` 行数/圈复杂度上升，按工具指引「确需上调须评审后重冻」执行） |

## 三、验收证据（本机实测）

- `python scripts/verify_run.py`（= `bash verify.sh`）→ **PASS=72 · WARN=0 · FAIL=0**。
- `nf locales` → zh/en/ja · 文档译件 **10 件** · rc=0。
- `python scripts/drill_fidelity.py --write` → 总保真 **100%（65/65）**。
- `python -m core.execution_drill p04_drill_cases.json` → 12 例全过（失范无漏报、guard 无误报）。
- `python -m unittest desktop.tests.test_execution_drill desktop.tests.test_round_drill desktop.tests.test_drill_fidelity` → **18 例全绿**。
- `nf conformance --write` → conformant **27/27**；`nf receipts --scope protocol --write` 根一致（57 件）；`python scripts/verify_report.py --write` → 判据 28 条 PASS 27 / FAIL 0 / WARN 1。

## 四、遗留与设计偏差

1. 62 计划 §三·② 的三条方向**只完成两条**：失范类型补 2 类（仍缺「量化门违反」，须先定「门」的数值口径，未编造）、回合级 R1–R4 样本补齐；**多语协议执行未做**——`execution_drill` 的决策/引用/推进正则仍是中文口径，扩多语须先立词法面。
2. 译件属**译者责任**（机制不做机器翻译）；判据只保证「声明的都在场且不过期」。译件与原文不逐行等长（原文硬换行），但标题层级、代码围栏、命令与内联锚点已机械核对一致。
3. 62 计划 §二·2`.NET 线重冻`**本地未完成**：实测卡在引擎与 Python 真源漂移（prose_lint cli 106↔107、深化面 FAIL 2↔0），非夹具重签可了结；实测与复现路径见内部档 `.rivet/private_archive/62_附录_dotnet重冻本地实测_2026-10-05.md`（不入库）。
4. 62 计划 §二·1「首例发布」、§三·① 存量复杂度/类型收敛未在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | locales 判据现覆盖 5 份指南；drill 断言 6 条各有判级映射；code_metrics 重冻有本件评审记录 |
| 动态可执行 | ↑↑ | 两类新失范在真语料上「命中 + 不误报」成对；回合级 R1–R4 样本覆盖，保真度 100% |
| 架构纯度 | → | 新判据落在既有 `execution_drill` 单一实现内，不新增模块/check 序号 |
| 资产密度 | ↑ | +6 份译件、+4 条演练语料（含一组新对照） |
| 文档可执行性 | ↑ | 对接方第一跳 mcp / 终端 / 台阶三份指南补齐 en/ja；演练口径随实现同步 |
