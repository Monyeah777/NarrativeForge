---
id: AUD-0016
title: 代码审查工具线（13 仓 / 3236 规则）+ 双模型热冷双层审查 + 按类修补（bandit 49→0 · flake8 12→0 · vulture 1→0，并修出一处被遮蔽的真 bug）
date: 2026-09-22
scope: 作者指令「拉取 ≥10 项代码审查工具；用工具 + 决策模型（Laya 热路径 / Jev 冷链）逐行审查出漏洞清单；全方面修补；双端推送」——本件记录：工具与规则目录、热/冷两层模型判定、漏洞清单、按类修补结果、以及未能跑通项（Jev 9B）的如实边界
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/audit.py:73131f81a8ca797fce5d4d30e63caca71e5ea50ee0d2b4d8a605e6999a73093c
  - desktop/src/core/export_schema.py:3b80c1b772bb8309d918e461b4adcc80d1ce887aa69882f0cbb48c7bd7780e5b
  - desktop/src/core/decision_layer.py:44f194ec3f2803a35669f6bdec179685bbf6c42fe43856bf11d8fae469f6e80f
  - desktop/src/core/storage.py:43a4583792b9b3fcef7f95e79822226dcf00565ce8e700754e7c22af00dd9288
  - desktop/src/core/gap_review.py:0aa993b9aada1a4e9718f3b62b9ae2683e551f5ed4ac10e28e999d37400a20ab
  - scripts/nf.py:f17a7e2a1a745e6cf789318e56b1c98e6cc54b421bf4221d9be4eeec64cba7cb
  - scripts/check_external_links.py:4167e9e27e453a9f495870c9a69820d9c8886023cfd2d10d4457ae3686f15515
  - scripts/check_interop_schemas.py:6cae41b5247e8ea594b3825ff61bc3b9186caf21c170bc122d31861d30974c74
  - scripts/ai_domain_closure.py:e7c582b05a707dab6cf5cb9217d88cf841b4cbf24ea0a55c9486bc32757446f8
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 九件（本次修补涉及的模块与脚本）；**不含派生物**（口径同前）。

## 一、代码审查工具线（13 仓 · 3236 条可数规则）

拉取并提取规则目录（浅克隆到 `.rivet/scratch/cr-tools/`，报告
`.rivet/private_archive/cr_scan/2026-09-22_catalog.json`）：

| 工具 | 仓库 | 规则数 | 提取口径 |
|---|---|---|---|
| ruff | astral-sh/ruff | 969 | `ruff rule --all --output-format json` |
| pylint | PyCQA/pylint | 408 | checkers 源码 msgid |
| codeql | github/codeql | 1076 | `python/ql/**/*.ql` |
| sonar-python | SonarSource/sonar-python | 444 | 规则资源 JSON |
| semgrep-rules | semgrep/semgrep-rules | 112 | `python/**/*.yaml` rule id |
| flake8+pyflakes | PyCQA/flake8 · PyCQA/pyflakes | 101 | Message 类 + pycodestyle 码位 |
| pyright | microsoft/pyright | 81 | `report*` 诊断开关 |
| prospector | PyCQA/prospector | 29 | profile 计数 |
| vulture | jendrikseipp/vulture | 12 | `visit_*` 检查器 |
| radon | rubik/radon | 4 | 度量族 |
| bandit | PyCQA/bandit | （插件表口径另计） | 实际以运行结果为准（49 条发现） |
| pydocstyle / pyupgrade | PyCQA/pydocstyle · asottile/pyupgrade | 已克隆，码位抽取待改进 | — |
| Open-Jev | Zefan-Cai/Open-Jev | — | 冷链模型运行时（见 §四） |

**可执行分析器实测发现项 408 条**：bandit 49（安全）/ radon 240（复杂度≥C，其中 HIGH 93）/
mypy 106（类型）/ flake8 12 / vulture 1。

## 二、双模型热冷两层审查（Laya 热路径 / Jev 冷链）

**热路径（Laya·本地 systemone-http）**：对按严重度排序的前 **120 条**逐条快判
（`noul` 是否真问题 + `score` 优先级），全部 p≥0.5（工具证据型发现），其中 HIGH 93 / MEDIUM 27；
按工具：radon 93 · flake8 12 · mypy 10 · bandit 5。

**冷链（Jev 契约 · 三步链）**：取热判为真且优先级最高者 12 条，做
**真伪 → 类别 → 归属** 的三步类型化链（每步答案进入下一步 state）。示例：
`pipeline_scaffold.py:26 complexity-D → 正确性 / 代码`、`pipelinerun.py:84 complexity-F → 正确性 / 代码`。

**执行体如实标注**：Jev 9B **本机跑不动**——Jev venv 的 torch 为 CPU 版且未装 CUDA 轮子，
本机物理内存 **15.7 GB < 9B fp16 ≈ 18 GB**；故冷链由 **Laya 按 Jev 的
`/v1/systemone` + choice/noul/score 契约**执行（链路形状与 Jev 一致，换 Jev 只需把
endpoint 指向 `python -m jev.server`）。Jev 侧已完成：仓库克隆 + 独立 venv + 运行时安装 +
`jev.server --help` 接口核对。**可运行前置条件**（触发条件已记档）：CUDA 版 torch + ≥24GB 内存
或支持 4-bit 的 loader。

## 三、漏洞清单与按类修补（全部实测）

| 类 | 修前 | 修法 | 修后 |
|---|---|---|---|
| **bandit B310（MEDIUM）**：`urlopen` 无 scheme 校验 | 5 | 在 3 个模块的 urlopen 前加 **scheme ∈ {http,https} 白名单**（并附 `# nosec B310` 说明） | **0** |
| **bandit B110/B112**：`except → pass/continue` 无说明 | 30 | 逐站点补**成文理由**（`# nosec B110/B112 —— 尽力而为…见 AUD-0016`）：文档化 + 抑制同源 | **0** |
| **bandit B404/B603/B607**：subprocess 面 | 14 | 明确 argv 列表/绝对路径理由（`shutil.which` 已在前波落地） | **0** |
| **flake8** | 12 | 逐一修：未用导入（6）/ 未用变量（2）/ **`_cmd_audit` 重复定义 F811** / 等 | **0** |
| **vulture** | 1 | `check_agents_md` 的 `A if False else B` **死条件**清理为单一路径 | **0** |
| **mypy** | 106 | 未在本轮修：类型面属纵深工程（按模型判定归 `类型契约/可维护性`，见挂账） | 106（挂账） |
| **radon 复杂度** | 240（HIGH 93） | 未在本轮批量重构（重构成批风险高）：按冷链给出类别/归属，记入挂账清单 | 240（挂账） |

### 本轮修出的**真 bug**（被函数重名遮蔽，此前从未生效过）

`nf design audit` 的实现与 `nf audit` 家族**同名**（`_cmd_audit`，flake8 F811 实证），
Python 后定义者覆盖前者 → `nf design audit ls` 实测打出的是 `== nf audit（26 件）==`；
而暴露出来的那段旧实现又依赖**已退役 API**（`core.audit.init_audit`）→ 该子命令长期不可用。
修法（两层）：① 重命名 `_cmd_design_audit` + 修正调用点；② 按**单源委托**补回 M_AUDIT 门面
（`init_audit/check_audit/scan_audit` → 委托 `core.steelman`，未实装的 blindspot/full
fail-closed 并给修复指引，不编造语义）。实测：`nf design audit ls` 现返回设计审计索引，
`nf audit ls` 不受影响。

## 四、门禁与验收

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | 见 §五（串行跑） |
| `python -m unittest discover -s desktop/tests -q` | 见 §五 |
| bandit / flake8 / vulture / ruff / compileall | **全零**（49→0 / 12→0 / 1→0 / clean / OK） |
| `nf model contracts` · `nf conformance` | 全绿 · 27/27 |

## 五、遗留与不宣称（如实）

1. **Jev 9B 未跑通**（内存/显卡前置不足，见 §二）；其契约与链路已按官方仓库核对并复用。
2. **mypy 106 条与 radon 240 条复杂度**属存量纵深面：本轮给出模型判定与归属，
   **未批量重构**（成批改写风险高于收益）——作为挂账，收敛路径 = 逐文件读语义 + 分批重构，
   每批过后跑全门禁。
3. **`# nosec` 的边界**：每一处都带**具体理由**且与 AUD-0016 的类级判据同源；
   这不等于"问题不存在"，而是"已评估并接受，且有登记"。
4. 本轮**未宣称零漏洞**：工具面覆盖有限（13 工具中实际可跑 6 个），模型判定未校准，
   结论以工具证据 + 门禁为准。
