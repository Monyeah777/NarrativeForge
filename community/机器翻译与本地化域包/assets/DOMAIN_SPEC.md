<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 机器翻译与本地化

> 用途：本域包的**内容资产与口径面**——把「机器翻译与本地化」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
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
| `B03-01` | 通用文本翻译 | 通用文本翻译的口径：语言对方向、句级 / 段级切分与 BLEU 类指标口径。 | 声明 lang_pair（方向含变体标签）、segment_unit（sentence|paragraph）与 metric（BLEU 变体 + tokenizer 口径）。 | 不同 tokenizer 的 BLEU 直接比较；句级切分不同导致段级质量被掩盖。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B03-02` | 领域术语翻译 | 领域术语翻译的口径：术语来源、强制约束方式与违反统计。 | 声明 term_source（术语库 id）、constraint_mode（hard|soft）与 violation_rate（术语违反率）。 | 声称术语一致却不报违反率；软约束当硬约束宣传。 | `w3c-skos` SKOS 词表（W3C） |
| `B03-03` | 文学与风格翻译 | 文学与风格翻译的口径：风格目标、译者干预边界与评审方式。 | 声明 style_target（枚举）、intervention（允许的编辑操作）与 review（人工评审协议）。 | 用 BLEU 评价文学翻译质量；无人工评审就宣称「保留了风格」。 | `frictionless-table` Table Schema（Frictionless） |
| `B03-04` | 口语与字幕翻译 | 口语与字幕翻译的口径：口语化处理、字符 / 行数与 CPS（每秒字符数）约束。 | 声明 max_chars_per_line、max_lines 与 max_cps（每秒字符数），并给违规字幕占比。 | 忽略时长约束导致字幕读不完；口语化处理无标准导致跨版本不可比。 | `oci-image` 镜像清单（OCI） |
| `B03-05` | 格式保留翻译 | 格式保留翻译的口径：标记保护范围、占位符规则与还原校验。 | 声明 protected_tags（清单）、placeholder_rule（规则）与 restore_check（还原校验通过率）。 | 标签在译后被破坏（文件不可解析）；占位符顺序错乱。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `B03-06` | 多语种并行 | 多语种并行翻译的口径：语种集合、共享参数证据与质量一致性报告。 | 声明 langs（清单）、pivot（直译|枢轴）与 per_lang_metric（逐语种指标，禁止只报平均）。 | 只报多语平均分掩盖低资源语言崩塌；枢轴翻译的误差未计入。 | `frictionless-table` Table Schema（Frictionless） |
| `B03-07` | 术语库与翻译记忆 | 术语库与翻译记忆的口径：记忆匹配阈值、模糊匹配策略与冲突处理。 | 声明 tm_threshold（模糊匹配阈值）、conflict_policy（新覆盖/最频/人工）与单元键（句级 / 片段级）。 | 低相似度记忆被强制套用；术语与记忆冲突无裁决规则。 | `w3c-skos` SKOS 词表（W3C） |
| `B03-08` | 本地化与地区变体 | 本地化与地区变体的口径：区域标签、日期 / 数字 / 货币格式与内容合规差异。 | 声明 locale_tags（BCP 47 列表）、format_source（CLDR 版本）与 compliance_diffs（地区合规差异清单）。 | 语言标签只到语言级（忽略地区变体）；日期与货币格式硬编码。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `B03-09` | 译后编辑与人工审校 | 译后编辑与人工审校的口径：编辑类型、编辑工作量（编辑距离）与审校层级。 | 声明 edit_types（错误维度清单）、effort_metric（如 HTER / 编辑距离）与 review_level（单审|双审）。 | 无编辑工作量数据导致「可用性」结论无据；审校层级不声明。 | `frictionless-table` Table Schema（Frictionless） |
| `B03-10` | 低资源语言 | 低资源语言的口径：资源规模、数据来源许可与评估可行性声明。 | 声明 data_size（句对量级）、data_license（逐源）与 eval_feasibility（是否有母语评审）。 | 用非母语评审宣称质量；训练与测试同源（无泛化证据）。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `B03-11` | 翻译质量评估 | 翻译质量评估的口径：自动指标（COMET 类）、人工 MQM 分数与二者相关性。 | 声明 auto_metric（id + 版本）、human_scale（MQM 维度）与 correlation（自动与人工的相关性报告）。 | 只报自动指标不报相关性；人工量表维度未定义。 | `frictionless-table` Table Schema（Frictionless） |
| `B03-12` | 文化适配与合规 | 文化适配与合规的口径：禁忌检查清单、文化改写范围与合规复核。 | 声明 taboo_checklist（来源）、rewrite_scope（可改写范围）与 compliance_review（复核人 / 规则）。 | 文化禁忌无清单（漏检靠运气）；改写越界改动事实。 | `gdpr` GDPR（EU） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`generation`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `机器翻译与本地化:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `机器翻译与本地化:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
