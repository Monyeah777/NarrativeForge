---
id: AUD-0008
title: 六项裁决一次收口（各取最优解）+ 六个量化项目吸收与域包深化（第 4/5 件资产、3 个新概念）
date: 2026-09-20
scope: ① 执行作者裁决队列六项（闭包跨域形态 / 证据强度入判据 / 多语言入口 / 外链巡检 / 跨包裸号白名单 / 货架嵌套），每项给出最优解与理由；② 对六个量化开源项目做机制借鉴筛选与净吸收，用于量化金融域包深化
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/concept_graph.py:5a4f5b6dc61f825c3d51a648eae84e434ac3cc475114db7c3f50e256ae193ca2
  - verify.sh:f4fd5b2aff8a57246ab64c435fc44cc2f472d5c04942b018c079c13288a6846c
  - README.en.md:3431128ea3b63304bbc0f28a0fae594117c935ef89ba7a83e883fab45063313f
  - scripts/check_external_links.py:4167e9e27e453a9f495870c9a69820d9c8886023cfd2d10d4457ae3686f15515
  - community/量化金融域包/assets/DATA_CONTRACT.md:3815cd420ce535b571149a1ca0725b2d5c1757660e83d0edd8ed1d5c14ed2af1
  - community/量化金融域包/assets/STRATEGY_SPECS.md:9174638b5caf2d5d8586b80d07ed9aeca5d221e16f01ec19ce0e4c0f50859e65
  - community/量化金融域包/assets/QUANT_GRAPH.md:331d63943effe51462440c41832202df3b8e6bb2553734472947ac77927e094c
  - .github/workflows/external-links.yml:85b42364e385a25a3920bb0321a2bc0b33c3cfd464eddf6be2d7a41dfb0f6850
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 本波承重件（判据实现 / 门禁 / 双语入口 / 巡检工具 / 三件资产）；任一件再改，本件结论即失效须重审。

## 一、六项裁决：逐项最优解与理由

| # | 挂账 | **选定解** | 理由（内部口径） |
|---|---|---|---|
| ① | 模块级闭包跨域形态（三选一） | **a) 保持现状 + 落规则**：闭包是**机制面**能力（`core/concept_graph.py` + 只读求值器 `--asset` + check32 子扫描），**内容面**随域包；域包可自带模块级闭包但**不跨包共享、不上提通用模块** | 当前**无该消费者**——第二域包（量化金融）已由通用面满足（`--asset` 直接可用）；上提通用模块 = 空转机制 + 跨包契约耦合；b) 引入跨包 references 会改 AI系统域包契约（参数化图键）而无收益。已写入 `02 §8`（概念图与闭包求值形态规则） |
| ② | 证据强度是否入判据 | **入，但只判可判定部分**：门禁要求 ① 图声明 `provenance_strength ∈ {external, domain-logic, inferred}`；② `external` 须有非推断图例键；③ 节点 `provenance` 的**每个键都须在图例在册** | 「证据是否真的充分」不可判定（硬判=造假判据）；可判的是**声明在场 + 与图例自洽**。顺带修掉真缺口：此前只查 provenance 非空、**不查键是否在图例**（图例漂移会静默）。落点在既有 check32 子扫描内 |
| ③ | 多语言入口面 | **开「最小英文入口 + 一致性判据」**：新增 `README.en.md`（机读事实：协议件 / 三条装载路径 / 质量凭证 / 许可），`llms.txt` 加锚点；**check34 增双语机读锚点一致性断言**（期望值取自 `quality_baseline`，不写字面量） | 外部实证：某清单双语面无判据 → 中文面腐烂到英文面 ~54%。NF 的解法 = 开面的同时**带判据**；范围控制在「机读事实 + 装载路径」，不做全量翻译（避免双源维护面爆炸） |
| ④ | 外链巡检是否开 | **开，但只作「非门禁独立任务」**：`scripts/check_external_links.py`（默认只解析、`--fetch` 才联网、`--write` 落 `results/`；**拒绝写入 `protocol/`**） | NF 门禁须静态可复现（同输入同输出）→ 外链可达性不进 verify 基线；同时补上「对外链接无巡检」的真空，且不脆化门禁 |
| ⑤ | 跨包裸号引用白名单化 | **不立（挂账关闭）**：`check15 ①` 已断言 references 的 module_id 须在源包在列，`check14 ⑤c①` 又保证同一裸号**全库唯一** → 裸号引用无歧义，白名单属重复机制 | 已写入 `02 §8`（跨包裸号引用无需额外白名单条）——机制不重复立，是本仓「零冗余」的直接应用 |
| ⑥ | 资产货架嵌套分组 | **保持单层不变量 + 给规范替代与触发条件**：分组用「键表 + 一包多文件 + 资产内条目键」；**触发条件** = 单包 > 30 件内容资产或出现明确子域分组消费方，届时另提裁决（属表达力扩展，须同时改密度 / 投影 / 基线三面） | 今天无嵌套需求（三货架子目录均为 0）；单层不变量已在 check23 硬门，规范替代写进 `05_资产库 README`，触发条件把「什么时候该重新讨论」写明 |

## 二、六仓勘验与净吸收（机制借鉴 → 逐条实证）

| 仓 | 许可 | 形态 | 判定 | 落点 |
|---|---|---|---|---|
| `QUANTAXIS`（573 文件） | **MIT** | 中国市场量化框架：`QAData/QAFetch/QADataBridge`（数据桥）/ `QAEngine` / `QAFactor` / `QAIndicator` / `QAMarket` / `QAPubSub`（发布订阅）/ `QASchedule`（调度）/ `QAStrategy` / `QIFI`（**统一交易接口对象**）/ `QARSBridge` | **部分吸收（机制观察）** | ① 「统一交易接口/账户对象」→ 新资产 `DATA_CONTRACT` §5（账户 / 委托 / 成交对象）+ 新概念 `Q30 交易对象与账户口径`；② 调度与发布订阅 → **已具备**（NF M50 调度 + 事件总线） |
| `zvt`（580 文件） | **MIT** | 数据—因子—记录器分层：`src/zvt/{domain, recorders, factors, contract, trader, sched, tag, informer, ml, api}` | **部分吸收（机制观察）** | 「领域对象 + 记录器 + 合约元数据」→ `DATA_CONTRACT` §3（合约与标的元数据）+ §6（数据源抽象与标准化）+ 新概念 `Q28` |
| `QuantDinger`（961 文件） | Apache-2.0 | 「AI 交易操作系统」：`backend_api_python` + **`mcp_server`** + `docs/{AGENT_QUICKSTART, MCP_SETUP, openapi.yaml, agent-openapi.json}` | **已具备（不重做）** | 给 agent 的接入面（MCP + OpenAPI + agent 快速开始）↔ NF `nf serve`（MCP）+ `llms.txt` + `AGENT_START.md` + `protocol/endpoint_contract.json`；其「想法→策略→回测→模拟→实盘→监控」全链 ↔ 本域图 Q09–Q20 已覆盖 |
| `OpenBB`（2191 文件） | **AGPL-3.0** | 开放数据平台：`openbb_platform/{core, extensions, providers}`（provider 抽象 + 核心 + 扩展插件） | **仅机制观察（不传导结构）** | 「provider 抽象 + 标准字段模型」是多源接入的公认机制 → 新概念 `Q28 数据源抽象与标准化` 的**存在性**观察；但 AGPL-3.0 属强 copyleft → **不入资产图例、不引用其结构**，概念与边仍标 `domain-logic` |
| `QuantEcon.py`（270 文件） | **MIT** | 经济学数值库：`quantecon/{game_theory, markov, optimize, random, util}`（Markov DP / LQ / ARMA / 谱分析…）+ 教程 | **部分吸收（概念面）** | 数值方法与动态规划是域内独立能力面 → 新概念 `Q29 数值方法与动态规划`（**独立成支，不并入组合优化 prereqs**——弱工具依赖不立边） |
| `quant-trading`（177 文件） | Apache-2.0 | 策略示例集：每策略一脚本 + `data/` + 主题项目（Monte Carlo / Oil Money / Ore Money / Smart Farmers） | **部分吸收（内容形态）** | 「策略示例集」形态 → 新资产 `STRATEGY_SPECS`（**自撰规格**：7 例 × 适用概念 / 必要前置 / 口径清单；只给规格不给代码、不给收益承诺） |

**纪律声明**：以上判定不构成立项理由（本波依据 = 作者指示 + 域包深化需求）；外部文本零复制；AGPL 仓不入图例；入图例与否由许可与证据类型决定，逐条写明。

## 三、本波交付（量化域包深化 + 机制三项）

| 类 | 件 | 要点 |
|---|---|---|
| 资产 | `DATA_CONTRACT.md`（第 3 件） | 五条契约纪律 + 行情 11 字段 + 标的合约 7 字段 + 基本面 / 另类 5 字段 + 账户交易对象 5 组 + 数据源抽象 4 项 + 三个口径陷阱（复权 / 停牌 / 退市） |
| 资产 | `STRATEGY_SPECS.md`（第 4 件） | 7 个策略族规格（趋势 / 均值回归 / 配对 / 多因子 / 事件 / 期权 / 日内），每例给「适用概念 + 必要前置 + 口径清单」，并强制两条偏差口径 |
| 概念图 | `QUANT_GRAPH` 30 概念（+3） | `Q28` 数据源抽象与标准化（data 支）/ `Q29` 数值方法与动态规划、`Q30` 交易对象与账户口径（research 支）；新增 `provenance_strength: domain-logic`；边只立「必须」依赖（弱工具依赖不立边） |
| 包登记 | `protocol.yaml` assets 2 → 4 + registry 同步 | check14 ⑦ 元素级自证 |
| 机制 | `concept_graph.py` 证据面判据 | 声明词表 + 图例自洽 + 节点 provenance 键在册（两张图同步加声明：AI系统 = `external`，量化金融 = `domain-logic`） |
| 机制 | 双语入口 + 一致性判据 | `README.en.md` + `llms.txt` 锚点 + check34 双语机读锚点断言（期望值取自 `quality_baseline`） |
| 机制 | 外链巡检工具（非门禁） | `scripts/check_external_links.py`（默认只解析；`--fetch` 联网；拒绝写 `protocol/`） |
| 文档 | `02 §8` 两条新规则、`05_资产库 README` 规范替代与触发条件 | 挂账 ①⑤⑥ 的规则化落点 |

## 四、门禁与验收

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | PASS=61 · WARN=0 · FAIL=0（**不新增 check 序号、不改 Schema**：六项与吸收项全部落在既有 check14/23/32/34 内） |
| `python -m unittest discover -s desktop/tests -q` | 全绿（本波新增 24 例：双语入口 4 + 外链工具 6 + 量化包 14 更新；概念图门禁测试计数更新为 2 图 77 节点） |
| `python -m ruff check .` · `python -m compileall -q desktop/src scripts` | 零违规 |
| 资产面 | `nf asset verify` 闭合（台账 3 · 托管资产 7 · 孤儿头 0）；量化包 assets 2 → 4 双源一致 |
| 事件 / 管线 / 市场 | `nf events` 43 零缺口；`nf pipeline dryrun --all` 10 条零 hard；`nf market --list` 列出量化金融域包 |
| 跨域求值 | `--asset …/QUANT_GRAPH.md --target Q17` 仍可复现；`frontier(--branch research)` 现含 Q29 |

## 五、遗留与不宣称

1. `Q29/Q30/Q28` 的边仍为 `domain-logic`（无实现类来源证据）——量化图整体维持 `domain-logic` 强度声明，不因本次吸收而升格。
2. 外链巡检**未接入任何自动化**（本地/定时任务自行调用）；如需定时跑，属运维面，不在本仓门禁内。
3. 英文入口只覆盖机读事实与装载路径，**不是**中文文档的全量翻译（避免双源维护面爆炸）——`README.md` 仍是权威版本。
4. 六个项目的**代码与数据零吸收**（只取机制观察与形态）；AGPL 仓连结构也不传导。

## 六、跟进（同日 · 三条挂账一并执行）

| 挂账 | 处置 | 实测 |
|---|---|---|
| ① 量化图证据强度升格 | **取回权威来源当外部锚**：Crossref REST API 取回 **10 条**经典工作元数据（Markowitz 1952 / Sharpe 1964·1966 / Black-Scholes 1973 / Fama-French 1993 / Jegadeesh-Titman 1993 / Kyle 1985 / Almgren-Chriss 2001 / Harvey-Liu-Zhu 2015 / Cont 2001，含 DOI 与年份），arXiv 摘要页取回 **3 条**（Deep Learning for Portfolio Optimization 2020-05-27 / Momentum Transformer 2021-12-16 / Deep Learning for Limit Order Books 2016-01-08）；据此给 **14/30 节点**挂外部来源键，资产新增 §6 外部证据表与取回失败清单 | 强度声明 `domain-logic` → **`mixed`**；判据同步升级为**四级阶梯 + 覆盖自洽**（`external` 须全覆盖 / `mixed` 须部分覆盖 / `domain-logic` 须零外部键）。AI系统域包实测 **external（47/47 全覆盖）**，量化金融 **mixed（14/30）**——都是机检结论，不是自述 |
| ② 外链巡检接自动化 | 新增工作流 `.github/workflows/external-links.yml`：`workflow_dispatch` + **每周一 cron**；权限最小化（`contents: read`）；先跑离线 scan（恒绿）再跑 `--fetch`（失败即 job 红）；报告上传为 artifact（**不写回仓库**） | 网络抖动可手动重跑；门禁基线不受影响（外链巡检始终在 verify 之外）。**首跑即抓出工具自身三处缺陷并当场修正**：① 行内代码里的 URL 带尾随反引号未剥离；② 骨架示例 URL（含 `{路径}` 占位符）被当死链；③ 非 ASCII 路径未百分号编码 → urllib `UnicodeEncodeError`。修正后复测 **20/20 取样链接全部可达、0 失败**，并补 2 例单测（占位符跳过 / 尾引号剥离） |
| ③ 英文入口扩到全量 | `README.en.md` 重写为**逐节镜像**（5 个 H2 与 `README.md` 一一对应：AI/Agent 入口 / 快速开始 / 能力与资产 / 协议链导航 / 版本块），并顺带**校正中文 README 的能力块陈旧数字**（44 模块 · 8 管线 · 5 社区包 · 55 档/165 键 · 馆藏 2 件 → 48 模块 · 10 管线 · 7 社区包 · 60 档/326 键 · 概念图 2 · 馆藏 3 件）；check34 增两条断言：**H2 章节数一致** + **中文入口引用的 ASCII 名 .md 件在英文入口同样出现** | 单测同步加 2 例；「双语面腐烂」类事故因此变成门禁可拦 |

**取回失败与修正如实记录**：arXiv API 端点返回 406（改走摘要页）· Merton 1973 的 DOI 失效（1 条未取回）· MIT OCW `/pages/calendar/` 重定向环、`/pages/lecture-notes/` 讲座清单为前端渲染、QuantEcon 站点返回 JS 桩 → **课程体系序未取回**，故量化图仍无 orderings（不造序）· 一次 arXiv ID 猜测取回无关论文（1904.08900 = CornerNet-Lite）**已弃用不入图例**。
