# 量化金融域包（community 非叙事题材域包 · 量化金融域装配流）
> 定位：**社区非叙事题材域包**（community 第 7 包、第 3 个非叙事域），独占「量化金融」类（01 §6 R2 / 02 §8 第三方协议登记）。本包把量化研究里最容易出错、也最需要**事前说清**的两件事协议化：**因子与信号口径**（FactorSpec）与**回测与绩效口径**（BacktestSpec）——并随包携带该域的**概念前置图**（「依赖闭包型」域包形态的第二实例）。经本包自带 **P08 管线**装载（R3 装配契约）。
> 协议声明：包根 `protocol.yaml`（01 §6.1 Schema，schema_version "2"，references 空列表）为**机读真相**，本 README 为**人读速览**，双源一致（check14 ⑥ / check15 ⑤）；登记三要件见 02 §8.3。
> 结构：modules/（2 域模块 量化金融:M31、量化金融:M32，类内段编号）｜assets/（**2 内容资产**：概念前置图 QUANT_GRAPH、绩效与风控口径表 QUANT_METRICS）｜pipelines/P08_量化金融域装配流管线.md
> 依赖边界（R1）：只依赖官方核心层（M00 / 通用:M10 / M50 / M80 共 4 件 core_modules，core_only true）；**不搬移**官方模块入包 default/available 槽（I5 单一真相源）。
> 内容自撰声明：本包正文（概念定义、口径规则、图层与别名）全部自撰；**未引用外部清单 / 仓库的结构**（外部输入只作本波触发与对照，判定见 `results/audit/docs_audit-55-quant-domain.md`）。
## 1. 包速览
| 项 | 值 |
| --- | --- |
| 管线 | **P08** 量化金融域装配流（九层线性回卷，装配自官方 P00 通用骨架） |
| 自带模块（本包） | 2：量化金融:M31 因子与信号口径（P40 行为决策位） / 量化金融:M32 回测与绩效口径（P60 长期演变位） |
| 官方核心配合件 | 4：M00 数据槽 / 通用:M10 节拍 / M50 主循环 / M80 输出门（本体驻官方核心位） |
| 总装配 | **6 模块**（核心配合 4 + 本包自带 2；references=[] 无跨包引用） |
| references 引用 | 0（无跨包引用） |
| 资产 | **4 文件**：`QUANT_GRAPH.md`（概念前置图：3 支 **30 概念** + 1 包外前置族 + 别名表 + 证据强度声明）· `QUANT_METRICS.md`（绩效与风控口径表）· `DATA_CONTRACT.md`（数据与对象契约：行情 / 标的 / 基本面 / 账户 / 数据源标准化 + 三个口径陷阱）· `STRATEGY_SPECS.md`（策略口径示例 7 例：适用概念 + 必要前置 + 口径清单） |
| 主轴 | 量化金融域：概念图 `QUANT_GRAPH`（P40 因子与信号口径）→ M32 回测与绩效口径收口（P60）→ M80 官方输出门（P80，gate 唯一出口） |
| 输出风格 | M80 官方输出门（gate 唯一出口）；本包产物（因子口径 / 回测与绩效口径 / 概念前置清单）供研究方与评审方读取 |
## 2. 模块装载清单（按层，6 = 核心配合 4 + 自带 2）
> 与 pipelines/P08_量化金融域装配流管线.md 的 layers（default 列）严格一致。
| 层 | 挂载（default） | 模块职责 | 归属 |
| --- | --- | --- | --- |
| P40 行为决策 | **量化金融:M31** | 因子与信号口径：维护 FactorSpec（定义 / 标准化 / 极值 / 中性化基准 / 频率对齐），发布 `factor_spec_ready` / `factor_spec_conflict` | 本包 |
| P60 长期演变 | **量化金融:M32** | 回测与绩效口径：维护 BacktestSpec（成本与成交假设 / 样本外切分 / 指标口径），发布 `backtest_spec_ready` / `backtest_spec_conflict` | 本包 |
| P00 / P10 / P50 / P80 | （空跑位） | 由官方核心 M00 / 通用:M10 / M50 / M80 承载，本包不重复挂载 | 核心 |
## 3. 本包产物与复现命令
| 产物 | 说明 | 复现命令（仓库根目录） |
| --- | --- | --- |
| 概念前置闭包 | 目标概念的全部前置（含包外前置族） | `python scripts/ai_domain_closure.py --asset community/量化金融域包/assets/QUANT_GRAPH.md --target Q17` |
| 缺失清单 | 相对已装载集 L 还差哪些概念 | `python scripts/ai_domain_closure.py --asset community/量化金融域包/assets/QUANT_GRAPH.md --target Q17 --loaded Q00,Q01,Q02,Q07` |
| 就绪清单（下一步可装载） | 前置已齐、尚未装载的概念 | `python scripts/ai_domain_closure.py --asset community/量化金融域包/assets/QUANT_GRAPH.md --ready-list --loaded Q00,Q01,Q02,Q03,Q04,Q05,Q06,Q07,Q08 --branch research` |
| 条目键全表 + 别名 | 概念可用条目键 / 别名 / 概念名检索 | `python scripts/ai_domain_closure.py --asset community/量化金融域包/assets/QUANT_GRAPH.md --list` |
> 求值器只读、确定性、零网络（同输入同输出），与 verify check32 的 `concept_graph` 子扫描**同源**（`desktop/src/core/concept_graph.py` 单一实现）——**本包不需要自带闭包求值模块**（机制复用；模块级闭包事件 / 数据槽仍是 AI系统域包私有，若要跨域复用须先裁决参数化，见 audit §三）。
## 4. 装载命令（Agent 通道）
```
读 community/量化金融域包/README.md → 按 §2 表装载 P08 管线（P40 量化金融:M31 / P60 量化金融:M32）→ 读 assets/QUANT_GRAPH.md 机器可读块（3 支 30 概念 + 别名表）与三张口径 / 契约表 → 按 §3 命令取前置闭包 / 缺失清单 / 就绪清单
```
## 5. 边界与不宣称
- 本包是**口径协议 + 知识前置**类域包：**不提供**数据、不执行交易、不做收益承诺；它管的是「口径是否说清、前置是否齐备」。
- 概念图是**内容资产**：门禁校验其可寻址与可溯源（check23 / check32 资产面）与**图内部一致性**（check32 的 `concept_graph` 子扫描：无环 / 无悬空 / 边有溯源 / 层位合法 / 别名唯一 / 分支完备）。
- **证据强度声明**：本图**无外部结构证据**（输入仓未声明许可，按纪律不传导其结构），边以域内「产物 → 输入」的可复算依赖为主、溯源标 `domain-logic`——证据强度低于 AI系统域包（后者有课程与论文锚点），该差异如实记档于 `assets/QUANT_GRAPH.md` §7 与 `results/audit/docs_audit-55-quant-domain.md`。
