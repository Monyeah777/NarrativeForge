<!-- nf-asset: key="QUANT_GRAPH" version="1.0" status="active" -->
# 概念图 · 量化金融域（概念前置偏序）

> 用途：量化金融域包的**前置闭包求值输入面**——把「量化金融」这一域的概念前置关系声明成偏序图（DAG），供只读求值器（`scripts/ai_domain_closure.py --asset <本件>`）与 verify check32 的 `concept_graph` 子扫描消费。
> 资产键：`QUANT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**。
> 覆盖：**三支**——基础（Q01、Q06–Q08）＋ 数据与基础设施（Q02–Q05）＋ 研究与交易（Q09–Q27），另含包外前置族 Q00；共 **27 个包内概念** + 1 个外部前置族。
> **内容自撰与证据强度声明**：本件正文（概念定义、图层、边、别名）**全部自撰**；**未引用任何外部清单 / 仓库的结构**（作为本波触发输入的那份清单未声明许可，按纪律不传导其结构）。因此本图的边以域内「**产物 → 输入** 的可复算依赖」为主，溯源统一标 `domain-logic`（本件推断、可复核），少数标 `inferred`；**证据强度低于 AI 系统域包**（后者有课程讲序与论文锚点），该差异见 §5 与 §6。

## 1. 读法

- **概念**：一个可独立装载的知识单元（如「因子分析」「回测引擎与偏差控制」），有稳定 id 与所属能力层。
- **分支**：`foundations`（基础：总览 / 工具生态 / 统计时序 / 计量回归）、`data`（数据与基础设施：行情 / 清洗 / 另类数据 / 存储）、`research`（研究与交易：因子 → 信号 → 组合 → 回测 → 绩效 / 风控 / 执行 / 治理）。分支只用于过滤与呈现，闭包按全图求。
- **条目键**：概念 id 即条目键（`QUANT_GRAPH` + `Q17` 唯一寻址）。**别名**见 §3（中英 / 缩写 / 惯例名），求值时与条目键等价。
- **前置（prereqs）**：装载该概念**之前必须已具备**的概念——方向「前置 → 后继」。
- **层（layer）**：该概念在 NF 九层位（P00–P80）中的合理驻留层，用于装配定位，**不是**执行顺序。
- **包外前置（Q00）**：只声明存在、不建模块（数学 / 统计 / 编程 / 金融常识属读者侧前置）。

## 2. 条目键表（一概念一键，asset_get 寻址）

### 2.1 基础（分支 foundations）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `Q00` | 外部前置族：概率统计 / 编程与数据工具 / 金融市场常识 | —（包外） | — | inferred |
| `Q01` | 量化研究总览：市场与资产类别、研究流程、角色分工 | P00 | `Q00` | domain-logic |
| `Q06` | 工具与框架生态：研究环境、数据接口、回测框架的选型口径 | P50 | `Q01` | domain-logic |
| `Q07` | 统计与时间序列基础：分布、平稳性、自相关、频率对齐 | P20 | `Q00` | domain-logic |
| `Q08` | 计量经济学与回归：OLS、面板、稳健标准误、因果视角 | P20 | `Q07` | domain-logic |

### 2.2 数据与基础设施（分支 data）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `Q02` | 市场数据与数据源：行情、成交、复权、频率与字段口径 | P00 | `Q01` | domain-logic |
| `Q03` | 数据管道与清洗：时点对齐、缺失与异常、交易日历、存活偏差口径 | P50 | `Q02` | domain-logic |
| `Q04` | 基本面与另类数据：财报与公告、情绪文本、另类数据源 | P50 | `Q02` | domain-logic |
| `Q05` | 数据存储与查询：时序 / 列存、研究数据层、查询可复现 | P60 | `Q03` | domain-logic |

### 2.3 研究与交易（分支 research）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `Q09` | 因子分析：因子定义、标准化、极值处理、中性化、IC / 分层 | P40 | `Q03`、`Q04`、`Q08` | domain-logic |
| `Q10` | 技术指标与规则信号：价格派生指标、形态规则、信号口径 | P40 | `Q02`、`Q07` | domain-logic |
| `Q11` | 多因子合成：打分、权重、组合信号与拥挤度意识 | P40 | `Q09`、`Q10` | domain-logic |
| `Q12` | 组合优化：均值方差、风险平价、换手与权重约束 | P50 | `Q11`、`Q07` | domain-logic |
| `Q13` | 风险模型与暴露：因子风险、协方差估计、行业与风格暴露 | P50 | `Q08`、`Q09` | domain-logic |
| `Q14` | 交易成本与容量：费率、滑点、冲击成本、策略容量 | P50 | `Q12` | domain-logic |
| `Q15` | 回测引擎与偏差控制：成交假设、前视偏差、数据泄漏、样本外切分 | P50 | `Q03`、`Q12` | domain-logic |
| `Q16` | 绩效评估与归因：收益与风险调整指标、收益归因分解 | P80 | `Q15`、`Q13` | domain-logic |
| `Q17` | 稳健性与过拟合防护：样本外、滚动验证、多重检验、参数敏感性 | P60 | `Q10`、`Q11`、`Q16` | domain-logic |
| `Q18` | 执行与交易：下单、算法执行、交易成本分析（TCA） | P50 | `Q14`、`Q15` | domain-logic |
| `Q19` | 组合风险管理：回撤、风险预算、敞口与限额、止损口径 | P60 | `Q13`、`Q16` | domain-logic |
| `Q20` | 实盘运维与监控：实盘与回测偏差、漂移检测、告警 | P60 | `Q18`、`Q19` | domain-logic |
| `Q21` | 合规与治理：交易合规、留痕与审计、信息披露 | P80 | `Q19` | domain-logic |
| `Q22` | 机器学习在量化：特征学习、非线性模型、模型风险 | P60 | `Q09`、`Q17` | domain-logic |
| `Q23` | 高频与市场微结构：订单簿、做市、延迟与撮合口径 | P50 | `Q18`、`Q07` | domain-logic |
| `Q24` | 衍生品与定价：期权定价直觉、隐含波动、希腊字母与对冲口径 | P50 | `Q07`、`Q12` | domain-logic |
| `Q25` | 多资产与宏观配置：资产类别、宏观因子、再平衡口径 | P60 | `Q12`、`Q13` | domain-logic |
| `Q26` | 研究与复现纪律：研究版本、口径一致、可复现产物 | P60 | `Q15`、`Q17` | domain-logic |
| `Q27` | 可视化与研究报告：绩效图表、风险呈现、报告面口径 | P80 | `Q16`、`Q26` | domain-logic |

## 3. 概念别名表（检索词 → 条目键）

> 别名与 id 等价；别名在图内**必须唯一**（重复即拒）。概念名本身也可直接作为检索词。

| 条目键 | 别名（中英 / 缩写 / 惯例名） |
|---|---|
| `Q01` | 量化总览、Quant Overview、卖方 / 买方研究流程 |
| `Q02` | 行情数据、市场数据、复权、频率口径 |
| `Q03` | 数据清洗、时点对齐、存活偏差、交易日历 |
| `Q04` | 基本面数据、另类数据、情绪数据、财报 |
| `Q05` | 时序库、列存、研究数据层 |
| `Q06` | 工具生态、研究环境、回测框架 |
| `Q07` | 时间序列、平稳性、自相关、频率对齐 |
| `Q08` | 计量经济学、回归、面板数据、稳健标准误 |
| `Q09` | 因子、因子分析、中性化、IC、分层回测 |
| `Q10` | 技术指标、规则信号、形态 |
| `Q11` | 多因子、因子合成、打分、拥挤度 |
| `Q12` | 组合优化、均值方差、风险平价、权重约束 |
| `Q13` | 风险模型、协方差、暴露、风格因子 |
| `Q14` | 交易成本、滑点、冲击成本、容量 |
| `Q15` | 回测、前视偏差、数据泄漏、成交假设 |
| `Q16` | 绩效、归因、夏普、回撤 |
| `Q17` | 过拟合、样本外、滚动验证、多重检验 |
| `Q18` | 执行、算法交易、TCA、下单 |
| `Q19` | 风控、回撤、风险预算、限额 |
| `Q20` | 实盘、监控、漂移、告警 |
| `Q21` | 合规、留痕、审计、披露 |
| `Q22` | 机器学习、特征学习、模型风险 |
| `Q23` | 高频、订单簿、微结构、做市、延迟 |
| `Q24` | 期权、隐含波动、希腊字母、对冲 |
| `Q25` | 多资产、宏观配置、再平衡 |
| `Q26` | 复现、研究版本、口径一致 |
| `Q27` | 可视化、研究报告、绩效图表 |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: 量化金融
  date: "2026-09-20"
  intent: 概念前置依赖的偏序声明（前置闭包求值的输入面）
  closure_rules:
    closure: "closure(c) = {c} ∪ ⋃ closure(p)，p ∈ prereqs(c)（传递闭包）"
    missing: "missing(c, L) = closure(c) − L（L = 已装载概念集）"
    readiness: "readiness(c, L) = (missing(c, L) 为空)"
    load_order: "toposort(G) 的任一线性化即合法装载序（并列按 id 升序）"
    frontier: "frontier(L) = {c ∉ L : prereqs(c) ⊆ L}（下一步可装载集）"
    determinism: "同一 (G, L) 下 missing / load_order / frontier 逐字节可复现"
    alias: "检索词解析顺序 = 条目键 → 别名 → 概念名（大小写与首尾空白无关）；别名重复即拒"
  branches:
    - id: foundations
      name: 基础（总览 / 工具生态 / 统计时序 / 计量回归）
      nodes: [Q01, Q06, Q07, Q08]
    - id: data
      name: 数据与基础设施（行情 / 清洗 / 另类数据 / 存储）
      nodes: [Q02, Q03, Q04, Q05]
    - id: research
      name: 研究与交易（因子 → 信号 → 组合 → 回测 → 绩效 / 风控 / 执行 / 治理）
      nodes: [Q09, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20, Q21, Q22, Q23, Q24, Q25, Q26, Q27]
  provenance_legend:
    domain-logic: 本件按域内「产物 → 输入」的可复算依赖自撰（可复核；无外部结构证据）
    inferred: 本件推断（无来源，待实现类证据收窄）
  external_prereqs:
    - id: Q00
      name: 外部前置族：概率统计 / 编程与数据工具 / 金融市场常识
      in_package: false
      provenance: [inferred]
      note: 包外前置，只声明不建模块（域包不承担通识教学职能）
  nodes:
    - {id: Q01, branch: foundations, name: 量化研究总览：市场与资产类别、研究流程、角色分工, layer: P00, prereqs: [Q00], provenance: [domain-logic], aliases: [量化总览, Quant Overview]}
    - {id: Q02, branch: data, name: 市场数据与数据源：行情、成交、复权、频率与字段口径, layer: P00, prereqs: [Q01], provenance: [domain-logic], aliases: [行情数据, 市场数据, 复权]}
    - {id: Q03, branch: data, name: 数据管道与清洗：时点对齐、缺失与异常、交易日历、存活偏差口径, layer: P50, prereqs: [Q02], provenance: [domain-logic], aliases: [数据清洗, 时点对齐, 存活偏差, 交易日历]}
    - {id: Q04, branch: data, name: 基本面与另类数据：财报与公告、情绪文本、另类数据源, layer: P50, prereqs: [Q02], provenance: [domain-logic], aliases: [基本面数据, 另类数据, 情绪数据]}
    - {id: Q05, branch: data, name: 数据存储与查询：时序 / 列存、研究数据层、查询可复现, layer: P60, prereqs: [Q03], provenance: [domain-logic], aliases: [时序库, 列存, 研究数据层]}
    - {id: Q06, branch: foundations, name: 工具与框架生态：研究环境、数据接口、回测框架的选型口径, layer: P50, prereqs: [Q01], provenance: [domain-logic], aliases: [工具生态, 研究环境, 回测框架]}
    - {id: Q07, branch: foundations, name: 统计与时间序列基础：分布、平稳性、自相关、频率对齐, layer: P20, prereqs: [Q00], provenance: [domain-logic], aliases: [时间序列, 平稳性, 自相关]}
    - {id: Q08, branch: foundations, name: 计量经济学与回归：OLS、面板、稳健标准误、因果视角, layer: P20, prereqs: [Q07], provenance: [domain-logic], aliases: [计量经济学, 回归, 面板数据]}
    - {id: Q09, branch: research, name: 因子分析：因子定义、标准化、极值处理、中性化、IC / 分层, layer: P40, prereqs: [Q03, Q04, Q08], provenance: [domain-logic], aliases: [因子, 因子分析, 中性化, IC]}
    - {id: Q10, branch: research, name: 技术指标与规则信号：价格派生指标、形态规则、信号口径, layer: P40, prereqs: [Q02, Q07], provenance: [domain-logic], aliases: [技术指标, 规则信号]}
    - {id: Q11, branch: research, name: 多因子合成：打分、权重、组合信号与拥挤度意识, layer: P40, prereqs: [Q09, Q10], provenance: [domain-logic], aliases: [多因子, 因子合成, 打分]}
    - {id: Q12, branch: research, name: 组合优化：均值方差、风险平价、换手与权重约束, layer: P50, prereqs: [Q11, Q07], provenance: [domain-logic], aliases: [组合优化, 均值方差, 风险平价]}
    - {id: Q13, branch: research, name: 风险模型与暴露：因子风险、协方差估计、行业与风格暴露, layer: P50, prereqs: [Q08, Q09], provenance: [domain-logic], aliases: [风险模型, 协方差, 暴露]}
    - {id: Q14, branch: research, name: 交易成本与容量：费率、滑点、冲击成本、策略容量, layer: P50, prereqs: [Q12], provenance: [domain-logic], aliases: [交易成本, 滑点, 容量]}
    - {id: Q15, branch: research, name: 回测引擎与偏差控制：成交假设、前视偏差、数据泄漏、样本外切分, layer: P50, prereqs: [Q03, Q12], provenance: [domain-logic], aliases: [回测, 前视偏差, 数据泄漏]}
    - {id: Q16, branch: research, name: 绩效评估与归因：收益与风险调整指标、收益归因分解, layer: P80, prereqs: [Q15, Q13], provenance: [domain-logic], aliases: [绩效, 归因, 夏普]}
    - {id: Q17, branch: research, name: 稳健性与过拟合防护：样本外、滚动验证、多重检验、参数敏感性, layer: P60, prereqs: [Q10, Q11, Q16], provenance: [domain-logic], aliases: [过拟合, 样本外, 多重检验]}
    - {id: Q18, branch: research, name: 执行与交易：下单、算法执行、交易成本分析（TCA）, layer: P50, prereqs: [Q14, Q15], provenance: [domain-logic], aliases: [执行, 算法交易, TCA]}
    - {id: Q19, branch: research, name: 组合风险管理：回撤、风险预算、敞口与限额、止损口径, layer: P60, prereqs: [Q13, Q16], provenance: [domain-logic], aliases: [风控, 回撤, 风险预算]}
    - {id: Q20, branch: research, name: 实盘运维与监控：实盘与回测偏差、漂移检测、告警, layer: P60, prereqs: [Q18, Q19], provenance: [domain-logic], aliases: [实盘, 监控, 漂移]}
    - {id: Q21, branch: research, name: 合规与治理：交易合规、留痕与审计、信息披露, layer: P80, prereqs: [Q19], provenance: [domain-logic], aliases: [合规, 留痕, 披露]}
    - {id: Q22, branch: research, name: 机器学习在量化：特征学习、非线性模型、模型风险, layer: P60, prereqs: [Q09, Q17], provenance: [domain-logic], aliases: [机器学习, 特征学习, 模型风险]}
    - {id: Q23, branch: research, name: 高频与市场微结构：订单簿、做市、延迟与撮合口径, layer: P50, prereqs: [Q18, Q07], provenance: [domain-logic], aliases: [高频, 订单簿, 做市]}
    - {id: Q24, branch: research, name: 衍生品与定价：期权定价直觉、隐含波动、希腊字母与对冲口径, layer: P50, prereqs: [Q07, Q12], provenance: [domain-logic], aliases: [期权, 隐含波动, 希腊字母]}
    - {id: Q25, branch: research, name: 多资产与宏观配置：资产类别、宏观因子、再平衡口径, layer: P60, prereqs: [Q12, Q13], provenance: [domain-logic], aliases: [多资产, 宏观配置, 再平衡]}
    - {id: Q26, branch: research, name: 研究与复现纪律：研究版本、口径一致、可复现产物, layer: P60, prereqs: [Q15, Q17], provenance: [domain-logic], aliases: [复现, 研究版本, 口径一致]}
    - {id: Q27, branch: research, name: 可视化与研究报告：绩效图表、风险呈现、报告面口径, layer: P80, prereqs: [Q16, Q26], provenance: [domain-logic], aliases: [可视化, 研究报告]}
  conflict_rules:
    - 互为前置（成环）→ 归并为并列节点并记档，不得留环
    - 单源 / 无源推断边须在 provenance 显式标注（本图统一 domain-logic / inferred）
    - 外部结构类来源若未声明许可，不得据其立边或写图（本图即按此纪律：全部自撰）
```

## 5. 闭包语义（求值口径）

```
closure(c)    = {c} ∪ ⋃ closure(p)      for p ∈ prereqs(c)     # 传递闭包（DAG 保证终止）
missing(c, L) = closure(c) − L                                   # L = 已装载概念集
readiness(c, L) = (missing(c, L) 为空)
frontier(L)   = {c ∉ L : prereqs(c) ⊆ L}                         # 下一步可装载集
load_order(G) = toposort(G) 的任一线性化（确定性：同入度按 id 升序）
```

复现（仓库根目录，只读、确定性）：

```
python scripts/ai_domain_closure.py --asset community/量化金融域包/assets/QUANT_GRAPH.md --target Q17
python scripts/ai_domain_closure.py --asset community/量化金融域包/assets/QUANT_GRAPH.md --ready-list --loaded Q00,Q01,Q02,Q07
```

## 6. 溯源与已知缺口（诚实边界）

- **无外部结构证据**：本图未引用任何外部清单 / 仓库 / 课程的结构（输入仓未声明许可；且清单类来源不提供前置关系）。故所有边均为**域内可复算依赖**（`domain-logic`），少数节点标 `inferred`。
- **证据强度分级**：与 AI 系统域包（有课程讲序 + 论文锚点，可做「序违反边 = 0」的交叉验证）相比，本图**缺实现类证据**——未取回教材 / 课程前置表或可复现系统工作作为边证据。
- **无 orderings**：本图不携带任何来源序（无外部序证据），故不提供 `--order` 校验对象；序校验对象仅存在于有来源序的域包。
- **门禁面**：图内部一致性由 verify check32 的 `concept_graph` 子扫描保证（无环 / 无悬空 / 边有溯源 / 层位合法 / 别名唯一 / 分支完备）；但**证据强度本身无判据**（门禁不判「边是否有足够证据」）——该缺口属判据面，记档于 `results/audit/docs_audit-55-quant-domain.md` §三。
