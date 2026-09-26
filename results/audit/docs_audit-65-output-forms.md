---
id: AUD-0017
title: 产出形态层（116 条形态逐条外部实证）+ 两域包机验产出面（数据/图表/图示/契约 + T4 可复算）+ 决策模型热冷裁决
date: 2026-09-22
scope: 作者指令「两个域包产出几乎都是文本…产出没有功能性；要求数据（所有形态）/图表（所有形态）/结构/专业规范/接口全形态支持，缺则从零构建；质量由功能完备程度与可机验率决定；用决策模型（Laya 热路径 / Jev 冷链路）升级」——本件记录：外部检索与逐条实证、从零构建的机制、两包落地、门禁接入、决策模型裁决与**未落地项的如实边界**
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/output_forms.py:0e87152c7a267e5645825f9c5d447fdc56b53b493ab7f7417a7131bad65348a6
  - desktop/src/core/quant_metrics.py:fef3a30d38387f4aefcedbe2ecbb68867a488e705fb4b2576a9dddaa0a85e6a0
  - desktop/src/core/quality_depth_scan.py:ef33e0c52da8370134c34da56943f3d9188c0f3212727a4b4eea5a80f0732fb1
  - desktop/src/core/doc_hygiene.py:2b0acc2498874f2d37ca7d7e51b8f89d17c1bd5171e9532e75667c58d9d5f5fb
  - scripts/nf.py:26bc147a5ce1ce439c90ae151cdc779fadde206d257cac23a4724ea588ca628d
  - protocol/output_forms.json:aff71eccf1cd0b57c51a86681c613580e79d346bb6e5dfdd97a873a2436943e9
  - community/量化金融域包/outputs/INDEX.json:cfe9272a362e138f9cb6d15615176cbb348716336d31b372bf411645f74a7bb6
  - community/AI系统域包/outputs/INDEX.json:95103926c6736571fb38e5c95f8234b76dddf26ee286270e3bdbdf3fd4c33a99
  - docs/output-forms.md:98716fc96333cdd1d8e012e307fb3911ead53888672c37a012761f3d41a8db4e
  - desktop/tests/test_output_forms.py:c748c0a476a53a3118670953df4ae8effcb136744d543d4bbfa0eb7a619bd691
  - desktop/tests/test_quant_metrics.py:bed9322e0961f98df2b7f588fd0d81f1b2ff92b45373e0ecfc3cc7da8739d4f3
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 12 件（本波新写/改动的机制、声明、文档与测试）；**不含派生物**（`protocol/generated/*`、`results/interop/*`、`protocol/RECEIPTS.json` 均不入 subjects——否则每次重生成都假失效）。

## 一、内部差距（开工依据）

两个非叙事域包（AI系统域包 / 量化金融域包）的**产出全是散文**：数据契约、指标口径、
策略规格、概念图**都是 Markdown 表格**——人能读，机器判不了形状、判不了单位、更复算不了数。
既有门禁能机检「资产键是否可寻址 / 图是否无环」，但**对产出形态本身零判据**：
没有任何一处断言「这份产出是数据、能被 schema 校验、能被重算」。

## 二、外部检索与逐条实证（只作形态入口 + 机制借鉴，不作质量背书）

本机 GET 实测 **116 条**形态（12 类别），**可达 110**、不可达 6（ISO 付费墙 403 / 限流 429 /
链接漂移 404——如实记 `evidence.reachable=false`）。GitHub API 元数据检索 4 组命中
（`topic:json-schema` 4207 · `topic:backtesting` 4658 · `topic:data-validation` 1750 ·
`topic:model-card` 60 仓），另 2 组撞限流（403）已记。逐条台账：
`.rivet/private_archive/59_产出形态清单_逐条实证.md`；采集与判定脚本在 `.rivet/scratch/output_forms/`。

## 三、从零构建的机制

| 件 | 作用 | 判据 |
|---|---|---|
| `protocol/output_forms.json` | 形态清单真源（116 条：类别 / 档位 / 状态 / 规范入口 / 可达性实证 sha256） | 结构自洽 + id 唯一 + 每条带可达性 |
| `core/output_forms.py` | 形态识别 + **自带 JSON Schema 2020-12 子集校验器** + 结构校验器 + 双源一致 + T4 复算 + 机验率 | 不支持的官方关键字**显式上报**，绝不静默通过 |
| `protocol/output_forms_baseline.json` | 机验率/功能面基线（可重签） | **回退即 FAIL**（口径同 check8 资产行基线） |
| `community/<包>/outputs/INDEX.json` | 包级产出面清单（路径 / 形态 / 档位 / 角色 / schema / 双源 / 复算） | 逐件形态与档位实测比对 |
| `nf output`（list / check / verify / render / meter） | 操作面 | 命令面自洽（`test_nf_cli` 全覆盖） |
| `docs/output-forms.md` | 使用者文档（含**未做项**边界） | doc_hygiene 四型覆盖 |

档位 = **本仓判定强度**（不是格式高低）：T0 散文 → T1 良构 → T2 形状 → T3 语义 → T4 **可复算**。

## 四、两包落地（功能性从零到有）

**量化金融域包（v1.0.0 → v1.1.0，8 件产出面）**：口径注册表（与资产 §2–§4 **双源一致**，
16 条键双向对齐；每个 `engine` 必须在 `core/quant_metrics.py` 真实存在）、**绩效报告（T4）**、
净值/回撤图（Vega-Lite，由数据生成）、口径声明依赖图（Mermaid）。`core/quant_metrics.py`
按该资产口径逐条实现：简单/对数收益、年化因子、年化波动、夏普、最大回撤、卡尔玛、换手、
IC（秩相关，含并列平均秩）、IR；输出四舍五入固定位 → 同输入逐字节一致（T4 复算前提）。
披露面显式写 **非 GIPS 合规**（不得靠外部标准背书）。

**AI系统域包（v1.1.0 → v1.2.0，6 件产出面）**：系统卡（用途/限制/数据/评测/人审/
NIST AI RMF 字段映射/**不宣称**清单）、**闭包产物（T4：由概念图重算 C42 闭包与全图装载序）**、
概念图两形态（Mermaid 按层分组 / GraphML，确定性派生）。概念图的**唯一机读真相仍是资产
§4 围栏块**——产出面是派生结果，不造第二真源。

机验率（机验面 /（机验面 + 散文资产））：**AI系统域包 0.8571**、**量化金融域包 0.6667**；
功能面（T4）各 1 件。

## 五、门禁接入（**不新增 check 序号**）

check32 增 `output_forms` 子扫描：形态清单自洽 + 包级产出面逐件校验（形态/档位/schema/
双源/T4 复算）+ 机验率基线不回落。两包 `package.version` additively bump，02 §9.5 落四步
迁移记录（check30）。实测：`bash verify.sh` **PASS=61 · WARN=0 · FAIL=0**；
`nf conformance` **27/27**；unittest **1013 例**全绿（含本波新增 30 例）；
ruff / flake8 / bandit（3 处 XML 面 nosec + 前置 DTD/ENTITY 守卫）/ vulture(≥80) 全零。

## 六、决策模型裁决（Laya 热路径 + Jev 契约冷链路；非门禁）

真模型（`laya-multilingual` 本地 `systemone-http`，2301 input tokens / 3250 ms）：

- **热路径**：在 10 个「已登记触发条件」的候选里选下一件吸收 → **`spdx3`（SPDX 3.0 含 AI profile）**
  `p=0.2325`（次高 `iso42001` `0.2259`）；**`confidence=0.0752`**（接近均匀分布 1/10 = 平坦，
  即模型**并不确信**）；风险期望 **2.157**（中高）；`worth_another_wave p=0.7449`。
- **处置（按本波预设判据）**：**本波不落地 `spdx3`**——判据是「改动面小 + 不触碰回执锚定件」，
  而升级 SPDX 3.0 必须动互操作导出面（RECEIPTS/conformance 锚定），且模型置信度仅 0.0752。
  故按机制登记为**下一波候选**（触发条件：需要外部 JSON Schema 核验 + 互操作面同步重签）。
  这与「决策模型只排序、不进修复清单必须有确定性证据」的既往纪律一致。
- **冷链路（真伪 → 类别 → 归属，每步答案进下一步 state）**：
  C1（vega-lite 可达 T3）真伪 `p=0.9948` → 类别 argmax「证据不可读」→ 归属「挂账待裁决」；
  C2（engine 宣称=实现）真伪 `p=0.9975` → 类别 argmax「**证据冲突**」→ 归属「**本波执行者**」；
  C3（基线能挡回退）真伪 `p=0.9979` → 类别「证据不可读」→ 归属「模块作者」。
  **对 C2 的归属裁决当场执行**：本波补齐「每个 engine 必须真实存在」的**双证据**——
  `_check_quant_metrics` 运行时检查 + `test_quant_engine_claim_covers_all_engines` 单测断言。
  C1/C3 的归属意见（挂账/模块作者）**如实记录不改判**：两处判据均已在门禁路径，无待办。
  记录：`.rivet/private_archive/59_output_forms_decision.json`。

## 七、本波自己引入又修掉的回归（如实记档）

1. **生成器写出 CRLF**：Windows 文本模式默认 `\n → \r\n`，产出面 10 件被 check33 编码卫生判 FAIL。
   根因：`write_text` 未显式 `newline="\n"`；且渲染比对用 `read_text`（自动归一化 EOL）→
   「内容相同」假象掩盖 EOL 漂移。修法：写入显式 LF + 比对改**逐字节**（EOL 属产物契约）。
2. **`nf output` 二级子命令缺 description**：被 `test_nf_cli` 命令面自洽矩阵拦下（5 处）→ 补齐。
3. **JSON Schema 子集与官方语义的两处坑**：`additionalProperties:false` 与 `$ref` 同层
   （benchmark `allOf` 写法导致必然失败）→ 改为自含 `$defs`；`type: number` 下 Python `bool`
   是 `int` 子类 → 显式排除并写单测。
4. **改声明件后未重签**：`scripts/nf.py` 改动使旧审计摘要失效（check12/conformance 红）→
   按标准循环重绑（reaudit → receipts → conformance → approve → receipts）。

## 八、未做 / 边界（不宣称）

- 形态清单 **61 planned / 11 deferred / 6 unfit** 是**明确未做**（每条写清触发条件或前置）；
  Parquet/Arrow/HDF5 前置是二进制依赖（与 core 零依赖红线冲突），OData/WSDL/容器镜像属不适面。
- 自带 schema 校验器是**子集**：`if/then/else`、`unevaluatedProperties`、`$dynamicRef`、
  远程 `$ref` 等显式报 unsupported。
- 6 条形态规范入口本机不可达（ISO 付费墙 403 四例 / 限流 429 一例 / 链接漂移 404 一例），
  按不可达记档（HDF5 与 Prometheus 出口经 URL 修正与补测转为可达，同样记档）。
- 机验率是**本仓口径的覆盖率**，不是内容质量分；它挡的是回退，不是「打磨完成」。
- 外部接触（客户端装载实测）仍按 STRATEGY 封存，本波零外部实测宣称。

## 九、推送阶段新暴露的两处（已修，同一波内收口）

本波在 `git push` 的 pre-push 体检（`nf release` = verify.sh + 逐模块覆盖率 ≥30%）里又抓到两处
**存量**缺口——都不是本波新写代码引入，但都由本波的推送动作暴露：

1. **工具临时件打断门禁**：`scripts/per_module_coverage.sh` 正常路径自删 `_cov_tmp.json`，
   一旦中断就留在仓库根；编码卫生把它当仓库件扫 → `check12` 单测与 `check33` 编码卫生双红、
   体检拦推。修法（根因面）：`core/text_hygiene.EXCLUDE_FILES` + `.gitignore` 补排除
   （与 `.mypy_cache`/`.pytest_cache` 同类处理——工具缓存不该进内容扫描）。
2. **逐模块覆盖率实测 `gap_review.py` = 0.0%**（AUD-0015 落地时无随行单测）→ 补
   `desktop/tests/test_gap_review.py` 6 例：候选筛法确定性 / 类别过滤 / 证据面 / **双轨纪律
   （无确定性证据的行不得进 `fixable`）** / stub shape 与 `limit` 语义。实测
   `files=109 below=0（min=30）`。

两处修完后的发布体检：**verify 全绿 + 逐模块覆盖率 ≥ min30 → pre-push 通过**；
双端推送后三处 ref 一致（本地 = GitHub = Gitee = `7a5637a`）。
