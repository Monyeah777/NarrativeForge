<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 嵌入与检索表示

> 用途：本域包的**内容资产与口径面**——把「嵌入与检索表示」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
> 资产键：`DOMAIN_SPEC`｜机读同源面 = `outputs/DOMAIN_SPEC.json`（双源一致由 check32 output_forms 断言；**本表是唯一人读真相，JSON 是它的机读投影**）。
> **内容档位**：authored（逐条撰写，含领域专属判据与权威锚）。

## 1. 口径纪律

1. **定义可判定**：每条细分的定义必须能回答「什么算做对/做错」，不允许只给形容词。
2. **判据可机检**：每条细分给出可写进校验器的判据（字段 / 范围 / 词表 / 一致性）。
3. **锚可复核**：每条挂一个外部权威锚（规范 / 论文 / 参考实现），URL 与可达性实测记于 `STANDARDS_ANCHORS`。
4. **失效模式显式**：写清该细分最常见的错法——它是质检单，不是介绍页。
5. **口径不合并**：不同细分不共用同一条判据文本；相似即拆细。

## 2. 细分口径表（12 条）

| 条目键 | 细分 | 定义口径 | 可机验判据 | 常见失效模式 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|---|
| `A11-01` | 文本嵌入模型选型 | 文本嵌入模型选型的口径：模型 id 与版本、维度、最大输入长度与多语言覆盖。 | 声明 model_id（含 revision）、dim、max_tokens 与 langs（是否多语言），四项齐备方可比较。 | 只写模型名不给 revision（同一名字权重已变）；最大输入长度不同却直接比检索分。 | `onnx` ONNX（opset 扩展）（iface｜✓） | `commonmark` CommonMark 0.31.2（form｜✓） |
| `A11-02` | 稀疏与稠密混合检索 | 稀疏与稠密混合检索的口径：混合方式（并集 / 加权 / RRF）、权重与归一化。 | 声明 fusion（rrf|weighted|union）、weights（数值）与 score_norm（min-max|z-score|none）。 | 分数未归一化就加权（BM25 与余弦量纲不同）；融合方式未声明导致不可复现。 | `frictionless-package` Data Package（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A11-03` | 重排序模型 | 重排序模型的口径：候选规模、重排深度与延迟预算。 | 声明 candidates（进入重排的候选数）、rerank_depth（最终截断）与 latency_budget_ms。 | 候选规模与重排深度未声明导致跨系统不可比；延迟预算缺失导致线上不可用。 | `onnx` ONNX（opset 扩展）（iface｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A11-04` | 向量维度与压缩 | 向量维度与压缩的口径：降维 / 量化方式、召回损失与存储成本对照。 | 声明 compression（none|PQ|OPQ|int8）、target_dim 与 recall_loss（对照全维度的召回差）。 | 只报存储节省不报召回损失；量化参数未记录导致不可复现。 | `frictionless-package` Data Package（data｜✓） | `mermaid` Mermaid 图语言（form｜✓） |
| `A11-05` | 相似度度量与归一化 | 相似度度量与归一化的口径：度量选择（余弦 / 内积 / 欧氏）、是否归一化与距离变换。 | 声明 metric（cosine|ip|l2）、normalized（true|false）与 distance_transform（若将距离当分数）。 | 内积与余弦混淆（未归一化时结果不同）；距离未做单调变换导致排序反转。 | `arrow` Arrow 列式格式（data｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `A11-06` | 多语言嵌入 | 多语言嵌入的口径：语言覆盖、跨语言检索评测与语言对齐方式。 | 声明 langs、eval_mode（mono|cross）与 alignment（对比学习|显式映射|无）。 | 只测单语检索却宣称跨语言；语言覆盖清单与实际支持不符。 | `frictionless-package` Data Package（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A11-07` | 领域嵌入微调 | 领域嵌入微调的口径：微调数据构造、负样本策略与基线对照。 | 声明 finetune_pairs（正对规模）、negatives（批内|挖掘）与 baseline（同测试集未微调基线）。 | 无基线对照（无法归因收益）；负样本泄漏（测试集对出现在训练对中）。 | `frictionless-package` Data Package（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A11-08` | 多向量与后期交互 | 多向量与后期交互的口径：向量数（每文档）、交互方式与存储代价。 | 声明 vectors_per_doc、interaction（maxsim|sum|late）与 storage_cost（每文档字节数估计）。 | 只报效果不报存储代价；向量数未声明导致索引规模估算错误。 | `frictionless-package` Data Package（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A11-09` | 向量库选型 | 向量库选型的口径：索引类型（HNSW / IVF）、关键参数与召回-延迟曲线。 | 声明 index_type、key_params（如 M/efSearch/nlist/nprobe）与 recall_latency_curve（≥3 点）。 | 只报单点延迟；参数不同（efSearch）直接比召回。 | `frictionless-package` Data Package（data｜✓） | `mermaid` Mermaid 图语言（form｜✓） |
| `A11-10` | 召回评测 | 召回评测的口径：候选库规模、相关性标注来源与指标（R@k / nDCG / MRR）。 | 声明 gallery_size、relevance_source（人工|模型|点击）与 metric（含 k 值）；三者缺一即评测不成立。 | 用模型自标相关性自评；gallery 规模不同直接比 R@k。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（eng｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `A11-11` | 语义去重 | 语义去重的口径：相似阈值、判定粒度（文本 / 段落）与保留策略。 | 声明 threshold、granularity（doc|paragraph）与 keep_policy（最新|最长|来源优先）。 | 阈值不声明（去重率不可复现）；保留策略随意导致信息丢失。 | `arrow` Arrow 列式格式（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A11-12` | 嵌入漂移与版本 | 嵌入漂移与版本的口径：模型 / 归一化变更的检测、重嵌入策略与兼容窗口。 | 声明 drift_check（样本对相似度基线）、reindex_policy（全量|增量）与 compat_window（新旧混用期限）。 | 模型升级不重嵌入导致检索质量静默下降；新旧向量混用无兼容声明。 | `frictionless-package` Data Package（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`retrieval`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `嵌入与检索表示:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `嵌入与检索表示:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
