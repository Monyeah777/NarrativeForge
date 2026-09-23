<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 文本生成与创作

> 用途：本域包的**内容资产与口径面**——把「文本生成与创作」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
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
| `B01-01` | 长文结构与大纲 | 长文结构与大纲的口径：层级深度、每节目标字数与「大纲 → 正文」的一致性要求。 | 声明 outline_depth（层级）、per_section_words（目标字数）与 outline_adherence（是否有一致性检查）。 | 无大纲直接长文生成导致中段漂移；只给总字数不给分节预算。 | `ietf-json-schema` JSON Schema 2020-12（data｜✓） | `commonmark` CommonMark 0.31.2（form｜✓） |
| `B01-02` | 文风与语体控制 | 文风与语体控制的口径：控制变量（人称 / 时态 / 语域 / 句长分布）与判定方式。 | 声明 control_vars（枚举）、判定方式（规则|模型|人工）与容差（如句长 Ziel 区间）。 | 只用形容词描述文风（无法判定）；控制变量变了却与旧稿直接比质量。 | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `B01-03` | 续写与改写 | 续写与改写的口径：上下文窗口、改写强度与事实保留约束。 | 声明 context_window（token 数）、rewrite_strength（0–1）与 fact_preserve（required|optional + 校验方式）。 | 改写后事实漂移无校验；上下文超出窗口被静默截断。 | `frictionless-table` Table Schema（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `B01-04` | 扩写与压缩 | 扩写与压缩的口径：目标比率、允许增删的信息类型与复查方式。 | 声明 target_ratio（如 ≤0.4 压缩率）、allowed_ops（增/删/改三类是否允许）与 fact_check 方式。 | 压缩率无上限定义导致「压缩」实为改写；删掉关键限定语却称忠实。 | `ietf-json-schema` JSON Schema 2020-12（data｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `B01-05` | 标题与导语生成 | 标题与导语生成的口径：字数上限、信息覆盖要求与去重规则。 | 声明 max_chars、coverage_rule（须覆盖的关键要素）与 dedup（与正文重复率上限）。 | 标题与正文首句完全重复（信息零增益）；字数不设上限导致版式崩坏。 | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `B01-06` | 营销文案 | 营销文案的口径：卖点清单、合规禁令与行动号召（CTA）要求。 | 声明 selling_points（清单）、forbidden_claims（禁用宣称清单）与 cta（必须存在的动作号召）。 | 出现绝对化或无依据疗效宣称；无 CTA 导致文案不可用。 | `frictionless-table` Table Schema（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `B01-07` | 公文与技术写作 | 公文与技术写作的口径：体例（章节 / 编号）、术语一致性与引用规范。 | 声明 style_guide（体例来源）、term_consistency（同义词合并表）与 citation_format（引用格式）。 | 同义词混用导致检索失效；引用格式不统一导致审校返工。 | `ietf-json-schema` JSON Schema 2020-12（data｜✓） | `commonmark` CommonMark 0.31.2（form｜✓） |
| `B01-08` | 创意写作与诗歌 | 创意写作与诗歌的口径：约束（韵律 / 格律 / 字数）、创作自由度与评审方式。 | 声明 constraints（韵律/格律/字数等枚举）、freedom（受约束 vs 自由）与评审方式（人工 / 规则）。 | 格律约束未声明导致「不合格也当合格」；用自动指标替代人工文学评审。 | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） | `commonmark` CommonMark 0.31.2（form｜✓） |
| `B01-09` | 去 AI 味与人类化改写 | 去 AI 味与人类化改写的口径：可检测特征（句长方差 / 连接词密度 / 套路词表）与目标阈值。 | 声明 feature_set（可量化特征清单）、target_threshold（各特征目标值）与检测器版本（若用检测器）。 | 只靠删「首先/其次」当人类化；检测器版本未固定导致效果不可复现。 | `frictionless-table` Table Schema（data｜✓） | `commonmark` CommonMark 0.31.2（form｜✓） |
| `B01-10` | 事实一致性与引用 | 事实一致性与引用的口径：可核查主张的抽取、证据绑定与不一致处置。 | 声明 claim_extraction（方法）、evidence_binding（每条主张须绑来源 id）与 handling（contradict → 阻断或标注）。 | 主张无来源 id（无法复核）；发现矛盾仅改措辞不改事实。 | `ietf-json-schema` JSON Schema 2020-12（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `B01-11` | 多轮编辑与版本管理 | 多轮编辑与版本管理的口径：版本标识、变更记录粒度与回滚可行性。 | 声明 version_id 规则、change_log 粒度（段落 / 句子）与 rollback（是否可逐版回滚）。 | 覆盖式改写导致不可回滚；变更记录只写「润色」不指范围。 | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） | `commonmark` CommonMark 0.31.2（form｜✓） |
| `B01-12` | 生成质量评估 | 生成质量评估的口径：自动指标、人工评审与一致性统计三分量。 | 声明 auto_metrics（清单含版本）、human_protocol（人数 / 量表）与 agreement（如 kappa）。 | 只用单一自动指标下「质量」结论；人工评审无一致性统计。 | `frictionless-table` Table Schema（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`generation`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `文本生成与创作:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `文本生成与创作:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
