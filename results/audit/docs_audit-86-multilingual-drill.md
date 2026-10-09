---
id: AUD-0038
title: 多语协议执行（lexicon 参数化 + 英文同构演练集 + Rust 镜像）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·②「演练仿真扩面」第三条「多语协议执行」；承接 AUD-0026（失范类型扩容）/ AUD-0036（回合级 R1–R4）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/execution_drill.py:7f291a20d779213d3acedaaf042722d4ec7223ba3333ee2477be6b5285152dea
  - desktop/src/core/drill_fidelity.py:42d1064477b9f14821e222c3abe89b27d5b624f011c19d166d7077b1aff7ee71
  - desktop/tests/fixtures/execution/p07_en_drill_cases.json:0fea6393ea0cbaf089e0499dd59364ca10f5f51c0ef9080cf34a747cafde9bb7
  - engine/rust/src/drill_fidelity.rs:54fb9760bd7e2fa83b110b4b1c29e54f821434ca5a19b7d63ff0e1d4195e9e20
  - protocol/drill_fidelity.json:235c028d1d817085a67c79303b7e1b4f8bb92b68885e43b49bfea209e51c6c91
  - docs/44_M1_执行演练扩展.md:12e58d6ae4d1cab23faaaff5e98d0a0bc9a6455c7a17552bab0d57e0cf30866c
  - protocol/code_metrics_baseline.json:a5d5b487b13e999ab31dbb0bceadfd1d0a8a97489e2048b67363dc8e4302fa81
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物（Rust 产物 `nf-rs` 不入册）；`protocol/code_metrics_baseline.json` 因两模块行数/复杂度增长按工具指引重冻。

## 一、内部差距（开工依据）

- `execution_drill` 的判定词表（decision/citation/progress）**硬编码中文**：非中文输出既漏 `no_citation` 也漏 `browse_repeat`——「协议可执行性」只覆盖单语。

## 二、交付

| 面 | 落点 |
|---|---|
| 词表参数化 | `run_case(..., lexicon=)`；`lexicon.decision`/`progress` 为字面子串、`lexicon.citation` 为 regex 源串列表，`_compile_citation` 合成为 `(?:p1)|(?:p2)…`；**缺省沿用中文内置词表**（行为零变化） |
| 贯通调用 | `run_file`/`main`/`drill_fidelity._exec_sets` 均透传 fixture 的 `lexicon` |
| 英文同构集 | `p07_en_drill_cases.json`（9 例：6 失范覆盖 R1–R4 全六规则 + 3 guard），词表与样本**同文件声明**，样本来源仍诚实标注 `inferred` |
| Rust 快线镜像 | `exec_lexicon` + `check_no_citation/check_browse_repeat` 接词表参数；`EXEC_DECISION` 常量替代原 `decision_re` |
| 文档 | `docs/44_M1_执行演练扩展.md`：覆盖表加 P07 行、补「判定词表由 fixture 声明，引擎不硬编码语言」段、集数 7→8 |

## 三、验收证据（本机实测）

- `python scripts/drill_fidelity.py --write` → **总保真 100.0%（74/74）**（执行演练 69/69 · 8 集 + 回合级 5/5）。
- `python -m unittest test_execution_drill test_drill_fidelity test_round_drill test_rust_fastlane` → **38 例全绿**（skipped=1：无 Rust 产物时跳过的那例本次在场）。
- Rust `cargo build --release --offline` 通过；**native ⇄ Python 逐字节对账**（test_rust_fastlane）通过。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. **语言面无外推**：只加了英文这一集；词表机制可承载任意语言，但**没有**为其它语言造样本（不编造）。
2. 62 §三·② 余量仍余「量化门违反」（须先立可判定的数值口径，未编造）；§三·① radon 存量与 §二·2 .NET 重冻不在本件范围。
3. `lexicon.citation` 由 fixture 直接给 regex 源串：fixture 是**测试载体**而非公开协议面，故未新增协议字段；若日后升为协议面须单独评审。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 保真度 74/74 可量化；38 例单测 + 全量 verify 双绿 |
| 动态可执行 | ↑↑ | 「协议可执行性」由单语扩到多语（词表可声明），直击 STRATEGY 五维② |
| 架构纯度 | ↑ | 判定口径从硬编码常量改为**入参 + 缺省**，无隐式分支 |
| 资产密度 | ↑ | 新增 1 集 9 例样本（诚实标注 inferred） |
| 文档可执行性 | ↑ | 覆盖表/口径/集数同步 |
