---
mode: full
target: CLI 工具链顶尖化（内部工程 W1-W7 收口）
verdict: 通过（CLI 内部顶尖验收线达成；外部实测类按封闭期冻结）
date: 2026-09-08
auditor: 天枢（基于项目现状取证）
related: [scripts/nf.py, desktop/tests/test_nf_cli.py, README.md 五分钟快速开始, CHANGELOG [Unreleased] CLI 波次注记]
---

# M_AUDIT CLI 工具链工程审计（44 · CLI 顶尖化 W1-W7）

> **审计问题**：CLI 工具链的「顶尖化」改造是否按内部差距审计落地（立项理由 = 内部差距，不引外部背书），七波交付是否如实、验收结论只由内部链产生。

## 1. 交付对账

| 波次 | 内容 | 落点 |
|---|---|---|
| W1 | `--version` / 无参 help / `help <cmd>` / `doctor`（含 `--json`）/ SIGPIPE 断管安全 / explain 补全 check1-11+26-31 | `4266091` |
| W2 | `market --list --json` / `related --json` | `42417fa` |
| W3 | `asset ls`/`asset inventory`/`module ls` 增 `--json`；全 34 子命令帮助页补 description | `742a0d6` |
| W4 | `completion bash/zsh/fish`（argparse 命令面自省生成） | `6a6ede7` |
| W5 | 退出码矩阵测试（子进程 0/2 语义）+ README 命令速查第 7 步 + audit 建档 | `bd45ff6` |
| W6 | `market <pkg>` 增 `--json`；退出码语义逐命令归一（校验/运行失败 1，用法 2）；`cli()` 未预期异常一句式兜底（NF_DEBUG 透出堆栈） | 本收口 commit |
| W7 | 命令面自洽矩阵自动化（根 + 全子命令 description/help 逐点断言 + JSON 面逐点 + root --version）——「逐命令穷举」由手写转机检 | 本收口 commit |

验收证据：verify v2.20 check1-31 PASS=49 全绿（W1-W7 每波提交前复核）；CLI 单测 7→26；py_compile 通过。

## 2. 支持侧最强论据

- 立项依据全部来自内部差距审计（无参 exit2 / 缺 --version / explain 只到 check25 / 无自检与补全 / 数据面 JSON 不齐 / 帮助页无描述），GitHub 项目仅作机制借鉴（`help` 子命令、`--version`、断管与退出码约定），公开文案一句式结论、无推崇叙事——符合 STRATEGY §3。
- 每波独立提交且门禁保持 PASS=49，无跨波债务；新增测试为可复现断言（非冒烟拍脑袋）。

## 3. 反对侧最强论据（= 距全量顶尖的挂账）

- 退出码「1=运行失败 / 2=用法错误」已主流化，但个别命令校验失败仍返 2（如 register 三要件校验失败）——语义未逐命令归一。
- completion 覆盖命令 + flags + 二级子命令（按位置分层），未到按选项上下文精细化——开放增强，非验收阻断。
- 逐命令输出样例快照（golden 化比对）未做全量；README/版本号基线随下个内容波发布更新。

## 4. 评估结论

**结论**：通过。骨架、机器可读面、帮助质量、补全、退出码语义与自洽矩阵均已系统化并机检常驻——按 STRATEGY 内部质量链（verify 全绿 + audit + 五维自评）CLI 达到内部验收线；「顶尖」的外部语义（生态级 benchmark）按封闭期口径冻结，不作为本结论依据。

## 5. 五维自评段

① 静态可核验：verify PASS=49 + CLI 单测 26 + 命令面自洽矩阵机检常驻；② 动态可执行：真实命令在子进程跑通（exit matrix/doctor/completion/market-pkg）；③ 架构纯度：单一 nf.py 入口 + argparse 自省生成，无散落重复逻辑；④ 资产密度：帮助/指引/补全/自检互为可查；⑤ 文档可执行性：README 快速开始第 7 步覆盖新命令面。水位：骨架、语义与自洽矩阵达线；开放增强（completion 上下文精细化、输出快照 golden）见 §3。
