<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 摘要与信息压缩

> 用途：本域包的**内容资产与口径面**——把「摘要与信息压缩」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
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
| `B02-01` | 抽取式摘要 | 抽取式摘要的口径：句子打分依据、选择策略与冗余抑制方法。 | 声明 scoring（特征清单）、selection（贪心/ILP）与 redundancy（MMR 等去冗余方式 + 参数）。 | 无去冗余导致句子重复；打分特征未声明导致不可复现。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B02-02` | 生成式摘要 | 生成式摘要的口径：覆盖度与忠实度权衡、长度约束与复制机制。 | 声明 length_constraint（min/max token）、copy_mechanism（有|无）与 faithfulness_check 方法。 | 长度不设上限导致「摘要」比原文还长；无忠实度检查。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `B02-03` | 多文档摘要 | 多文档摘要的口径：文档集合构造、跨文档去重与来源可追溯性。 | 声明 doc_count（集合规模）、cross_doc_dedup（策略）与 provenance（每条要点可回指源文 id）。 | 要点不可回指来源（无法核实）；同一事实被算作多个要点。 | `w3c-epub33` EPUB 3.3（W3C） |
| `B02-04` | 会议纪要压缩 | 会议纪要压缩的口径：说话人归因、决议抽取与行动项格式。 | 声明 speaker_attribution（required|optional）、decision_extraction（有|无）与 action_item_format（字段清单）。 | 决议与闲聊混在一起；行动项缺负责人与截止日期字段。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B02-05` | 层级摘要 | 层级摘要的口径：层级定义、每层长度预算与向上抽象的一致性。 | 声明 levels（层级数 + 每层长度）、abstraction_check（下层要点须被上层覆盖）与 loss_policy（超预算截断规则）。 | 上层摘要出现下层没有的新事实（幻觉升级）；每层长度不设预算。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `B02-06` | 要点抽取与结构化 | 要点抽取与结构化的口径：要点粒度、去重与输出结构（字段 / 层级）。 | 声明 granularity（句|段|全文）、dedup_threshold（相似度阈值）与 schema（输出字段清单）。 | 要点粒度不一致导致计数类结论失真；输出无 schema 无法机读。 | `frictionless-table` Table Schema（Frictionless） |
| `B02-07` | 长文压缩比控制 | 长文压缩比控制的口径：压缩比定义（字符 / token / 信息单元）与实现方式。 | 声明 ratio_metric（char|token|info-unit）、target_ratio 与 clamp（截断策略）。 | 不同压缩比定义混比；超长输入未分块导致中段信息丢失。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B02-08` | 忠实性与幻觉检测 | 忠实性与幻觉检测的口径：一致性判定方法、抽样规模与阈值。 | 声明 method（NLI|QA|规则）、sample_size 与 threshold（判定阈值），并给不一致率。 | 只报流畅度不报不一致率；抽样规模过小却下总体结论。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `B02-09` | 要点权重排序 | 要点权重排序的口径：权重定义（频次 / 位置 / 模型分）与排序稳定性要求。 | 声明 weight_source（频次|位置|模型）、tie_break（并列处理）与 stability（重跑排序一致率）。 | 并列键无确定处理导致输出抖动；权重来源未声明导致不可比。 | `frictionless-table` Table Schema（Frictionless） |
| `B02-10` | 多语言摘要 | 多语言摘要的口径：语言覆盖、跨语言评测方式与长度单位（字符 vs token）。 | 声明 langs（语言清单）、eval_mode（同语|跨语）与 length_unit（char|token）。 | 中英混用同一长度单位导致预算失真；跨语评测用单语指标替代。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B02-11` | 摘要质量评测 | 摘要质量评测的口径：ROUGE 变体与版本、语义指标与人工要点覆盖。 | 声明 rouge_variant（R1/R2/RL + 版本）、semantic_metric（如 BERTScore）与 human_coverage（要点覆盖统计）。 | 只报 ROUGE-L 且不报版本；用参考摘要唯一性强的数据集下泛化结论。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons） |
| `B02-12` | 增量摘要 | 增量摘要的口径：更新触发条件、已有摘要的复用策略与一致性维护。 | 声明 trigger（时间|事件|长度）、reuse_policy（重建|追加|合并）与 consistency_check（新旧摘要冲突处理）。 | 每次全量重写（成本不可控）；新旧摘要矛盾未处理。 | `frictionless-table` Table Schema（Frictionless） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`generation`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `摘要与信息压缩:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `摘要与信息压缩:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
