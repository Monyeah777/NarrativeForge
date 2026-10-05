---
id: AUD-0030
title: 类型分批收敛第三批（mcp_package / conformance_scan / pack_combo 归零 + 一处隐患修复）
date: 2026-10-05
scope: 作者指令「按 rivet 62 计划执行（除外部）」——62 计划 §三·①「存量复杂度/类型分批收敛」；承接 AUD-0029。开工依据为内部实测（mypy desktop/src 161 条）。
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/mcp_package.py:bc7d0a06a139427ca1d1f4988fcaa2b413d851556e6652254cb09c051578c273
  - desktop/src/core/conformance_scan.py:66fa09027a4f0f047c1bd4a2e14ac30ff8637dd46d9679b2fdffac97150dcacc
  - desktop/src/core/pack_combo.py:29b1b4d401ffd6d70d81a31be60262d00c6a3e132f79779effe9ad75b0300bf9
  - protocol/code_metrics_baseline.json:6799bce34acc607422bfb485f33bcbe5f546f988d6fc48f13630d3f6f4c2daae

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects 不含派生物；`protocol/code_metrics_baseline.json` 因三模块各 +1 行按工具指引评审后重冻。

## 一、内部差距（开工依据）

- 承接 AUD-0029：`mypy desktop/src` 161 条；本批取误差集中且判据较密的三个模块（`mcp_package` 8 / `conformance_scan` 2 / `pack_combo` 8）。

## 二、交付

| 模块 | 修前 | 修法 |
|---|---|---|
| `desktop/src/core/mcp_package.py` | 8 | `pkg` 的「isinstance 守卫 + 字典」拆原始值再判型（消 `Any \\| dict \\| None`） |
| `desktop/src/core/conformance_scan.py` | 2 | `_DIR_MEMO` 键为元组，标注放宽为 `Dict[Any, Any]`；调用点先捕获局部引用再判空（mypy 对模块全局不放宽） |
| `desktop/src/core/pack_combo.py` | 8 | 两处 `rec` 显式 `Dict[str, Any]`；`for m in ms` 改名 `mid`（与上文正则 `m` 解耦）；`borrow` 显式类型 |

### 顺带修出的隐患（非类型面）

`pack_combo._append_domain_list` 用 `text[:m.start()] + …` 插 §9，而 `m = re.search(r"(?m)^## 9\.", text)` 可能未命中（文档尚无 §9）——**未命中即 `AttributeError` 崩**。改为 `pos = m.start() if m else len(text)`：命中行为不变，未命中改为文末追加（原路径本就不可达地崩）。

## 三、验收证据（本机实测）

- `python -m mypy desktop/src --ignore-missing-imports` → **161 → 137 行**（三受改模块各自 rc=0）。
- `python -m unittest desktop.tests.test_conformance_scan desktop.tests.test_pack_combo` → 58 例全绿；`test_mcp_packaging` → 11 例全绿。
- `python scripts/code_metrics.py` → 三模块 +1 行按工具指引重冻。
- `python scripts/verify_run.py` → **PASS=72 · WARN=0 · FAIL=0**。

## 四、遗留与设计偏差

1. 累计收敛 **66/203**（19 + 23 + 24）；余 137 条与 radon 复杂度继续分批。
2. `_DIR_MEMO` 改为调用点捕获局部引用：单会话单线程语义不变；不引入线程语义承诺。
3. 62 §三·② 余量与 §二·2 .NET 重冻不在本件范围。

## 五、五维自评

| 维度 | 本波水位 | 说明 |
|---|---|---|
| 静态可核验 | ↑ | 三模块 mypy 归零；69 例单测 + 全量 verify 双绿 |
| 动态可执行 | ↑ | `pack_combo` 的 §9 未命中路径不再崩（原为不可达崩点） |
| 架构纯度 | → | 只改类型写法与变量命名 |
| 资产密度 | → | 不新增内容资产 |
| 文档可执行性 | → | 文档未动 |
