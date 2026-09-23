<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 数学与形式化推理

> 用途：本域包的**内容资产与口径面**——把「数学与形式化推理」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
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
| `A10-01` | 思维链与推理链 | 思维链与推理链的口径：链的粒度、是否允许工具、以及最终答案与过程的分离报告。 | 声明 chain_granularity（步级/自由）、tools（allowed|none）与 answer_vs_process（是否分开报告）。 | 只报最终答案对错（过程不可核）；用工具却宣称纯推理能力。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A10-02` | 形式化定理证明 | 形式化定理证明的口径：证明助手与版本、是否允许未证明公理、以及编译通过判据。 | 声明 prover（Lean/Coq/Isabelle + 版本）、axioms（允许清单）与 pass_criterion（编译零错误 + 无 sorry/admit）。 | 用 sorry 占位通过编译；公理未声明（证明不成立却算通过）。 | `w3c-mathml3` MathML 3（W3C） |
| `A10-03` | 定理证明搜索 | 定理证明搜索的口径：搜索预算（时间/节点数）、启发式来源与成功率定义。 | 声明 budget（秒 + 节点数上限）、heuristic（来源）与 success_definition（在预算内完成才算成功）。 | 不计预算报成功率（时间无上限无意义）；启发式来自测试集（泄漏）。 | `w3c-mathml3` MathML 3（W3C） |
| `A10-04` | 符号计算与 CAS | 符号计算与 CAS 的口径：符号引擎与版本、表达式规范化与等价判定方式。 | 声明 cas（SymPy/Mathematica 等 + 版本）、normalize（展开/因式/三角化简）与 equivalence（符号等价判定方法）。 | 用字符串比较判等价（形式不同即判错）；CAS 版本差异导致结果不同。 | `w3c-mathml3` MathML 3（W3C） |
| `A10-05` | 数学应用题求解 | 数学应用题求解的口径：题目来源、答案格式与单位 / 精度容差。 | 声明 source（数据集 id）、answer_format（数值/表达式/区间）与 tolerance（相对误差或小数位）。 | 容差不声明（数值题判分不可复现）；漏写单位扣分规则未定。 | `w3c-mathml3` MathML 3（W3C） |
| `A10-06` | 竞赛数学基准 | 竞赛数学基准的口径：基准版本、题面格式、评分（精确匹配 / 人工）与污染检查。 | 声明 benchmark（id + 版本）、scoring（exact|人工 + 人数）与 contamination_check（是否与训练集重叠核验）。 | 用训练题评测（污染）；人工评分无一致性统计。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons） |
| `A10-07` | 过程奖励模型 | 过程奖励模型的口径：步骤标注来源、奖励聚合方式与与结果奖励的相关性。 | 声明 step_labels（人工|自动）、aggregation（min|mean|last）与 corr_with_outcome（与最终正确率的相关性）。 | 过程奖励与结果不相关却用于搜索（放大噪声）；标注来源不明。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A10-08` | 自洽性与结果验证 | 自洽性与结果验证的口径：采样数、聚合规则与可独立验证的检查器。 | 声明 samples（采样数）、aggregation（多数表决|加权）与 verifier（是否存在独立校验器 + 类型）。 | 自洽性当正确性（一致错也算对）；无独立校验器。 | `peps` PEP 体系（含 8/257/621）（Python） |
| `A10-09` | 图论与组合推理 | 图论与组合推理的口径：问题规模、图表示格式与构造性证明的检查方式。 | 声明 instance_size（顶点/边量级）、representation（邻接表/边表）与 check_method（构造可验证 vs 仅结论）。 | 只报结论不报构造（无法验证）；规模未声明导致复杂度结论失真。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A10-10` | 数值与误差分析 | 数值与误差分析的口径：浮点模型（FP16/FP64）、舍入方式与误差度量。 | 声明 fp_model（fp16|fp32|fp64）、rounding（IEEE 默认|特定）与 error_metric（绝对/相对/ULP）。 | 混合精度下比较精度结论；误差度量不声明（绝对/相对混用）。 | `ieee-754` 浮点运算标准（IEEE） |
| `A10-11` | 推理幻觉识别 | 推理幻觉识别的口径：幻觉类型（步骤跳步 / 假设无据 / 结论越界）与检出方式。 | 声明 hallucination_types（枚举分列）、detector（人工|规则|模型 + 版本）与 rate（分类型比率）。 | 只给总体幻觉率（无法定位）；检测器与被测模型同源（自评）。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A10-12` | 推理成本优化 | 推理成本优化的口径：成本口径（token/调用/时延）、质量保持阈值与对照基线。 | 声明 cost_metric（token|调用|ms）、quality_floor（可接受质量下限）与 baseline（同任务未优化对照）。 | 只报省了多少不报质量掉了多少；无基线对照。 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`exact_judgement`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `数学与形式化推理:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `数学与形式化推理:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
