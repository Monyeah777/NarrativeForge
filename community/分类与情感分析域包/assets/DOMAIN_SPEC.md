<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 分类与情感分析

> 用途：本域包的**内容资产与口径面**——把「分类与情感分析」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
> 资产键：`DOMAIN_SPEC`｜机读同源面 = `outputs/DOMAIN_SPEC.json`（双源一致由 check32 output_forms 断言；**本表是唯一人读真相，JSON 是它的机读投影**）。
> **内容档位**：authored（逐条撰写，含领域专属判据与权威锚）。

## 1. 口径纪律

1. **定义可判定**：每条细分的定义必须能回答「什么算做对/做错」，不允许只给形容词。
2. **判据可机检**：每条细分给出可写进校验器的判据（字段 / 范围 / 词表 / 一致性）。
3. **锚可复核**：每条挂一个外部权威锚（规范 / 论文 / 参考实现），URL 与可达性实测记于 `STANDARDS_ANCHORS`。
4. **失效模式显式**：写清该细分最常见的错法——它是质检单，不是介绍页。
5. **口径不合并**：不同细分不共用同一条判据文本；相似即拆细。

## 2. 细分口径表（12 条）

| 条目键 | 细分 | 定义口径 | 可机验判据 | 常见失效模式 | 可扩展标准（绑定） |
|---|---|---|---|---|---|
| `B04-01` | 意图识别 | 意图识别的口径：意图集合封闭性、域内 / 域外处理与置信阈值。 | 声明 intent_set（封闭词表 id 或 none 兜底）、oos_policy（reject|unknown 类）与 threshold（置信阈值）。 | 无兜底类导致域外输入被硬分到某意图；阈值未声明导致拒答率不可控。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B04-02` | 话题与标签分类 | 话题与标签分类的口径：标签体系、多标签处理与长尾报告。 | 声明 label_taxonomy（体系 + 版本）、multilabel（true|false）与 long_tail_report（尾类单独指标）。 | 只报 macro/micro 平均掩盖尾类归零；标签体系版本漂移未记录。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `B04-03` | 情感极性 | 情感极性的口径：极性分级、否定与转折处理、以及中性类定义。 | 声明 polarity_levels（二/三/五级）、negation_handling（规则 id）与 neutral_rule（中性的判定条件）。 | 中性类定义随数据集漂移；否定与转折未处理导致极性反转漏判。 | `frictionless-table` Table Schema（Frictionless） |
| `B04-04` | 细粒度情绪 | 细粒度情绪的口径：情绪体系来源、标注人数与标注一致性。 | 声明 emotion_taxonomy（体系来源）、annotators_per_item（人数）与 agreement（kappa 或 alpha）。 | 单标注者数据当金标准；情绪体系混杂（Ekman 与 Plutchik 混用）。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B04-05` | 立场与观点检测 | 立场与观点检测的口径：目标实体、立场取值与目标缺失处理。 | 声明 target_entity（须绑定目标 id）、stance_values（枚举）与 notarget_policy（跳过|单列）。 | 不绑定目标就判立场（同一句对不同目标立场可相反）；目标缺失样本混入分母。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `B04-06` | 垃圾与违规识别 | 垃圾与违规识别的口径：违规类别体系、误伤成本与申诉通道要求。 | 声明 violation_taxonomy、threshold（按类分别给）与 appeal_path（申诉与复核机制声明）。 | 单阈值覆盖所有违规类（误伤高）；无申诉机制（不可运营）。 | `frictionless-table` Table Schema（Frictionless） |
| `B04-07` | 情感强度与演化 | 情感强度与演化的口径：强度标尺、时间切片与演化指标。 | 声明 intensity_scale（如 −4..4）、time_bucket（小时/天）与 evolution_metric（差分 / 斜率）。 | 强度标尺未声明导致跨研究不可比；时间切片改变后趋势结论反转。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B04-08` | 少样本分类 | 少样本分类的口径：样本数与选择策略、提示方式与基线对照。 | 声明 shots_per_class（每类样本数）、selection（随机|语义）、prompt_form（有|无）与同池基线对照。 | 样本选择偏向易例；只报少样本结果不与全监督基线对照。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `B04-09` | 层级多标签 | 层级多标签的口径：层级深度、父子约束与违反率统计。 | 声明 hierarchy_depth、parent_child_constraint（是否强制）与 violation_rate（越层预测占比）。 | 预测出无父节点的子类（结构非法）；层级深度不同却比较 F1。 | `frictionless-table` Table Schema（Frictionless） |
| `B04-10` | 阈值与概率校准 | 阈值与概率校准的口径：阈值选取依据、校准方法与可靠性指标。 | 声明 threshold_policy（按类 / 全局 + 选取数据）、calibration（none|温度|等渗）与 ECE（含分箱数）。 | 在测试集上选阈值（泄漏）；只报准确率不报校准误差。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B04-11` | 标注一致性校验 | 标注一致性校验的口径：一致性指标、可接受下限与冲突裁决流程。 | 声明 agreement_metric（kappa|alpha）、accept_floor（可接受下限）与 arbitration（裁决人 / 规则）。 | 一致性低仍直接训练（噪声放大）；无裁决流程导致冲突永久滞留。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B04-12` | 分类评测指标 | 分类评测指标的口径：指标集合（P/R/F1/AUC）、平均方式与置信区间。 | 声明 metric_set、averaging（macro|micro|weighted）与 CI（bootstrap 次数或区间方法）。 | averaging 不同却比较 F1；无置信区间就断言「更优」。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`classification`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `分类与情感分析:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `分类与情感分析:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
