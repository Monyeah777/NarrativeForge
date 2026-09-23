<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 数据采集与清洗

> 用途：本域包的**内容资产与口径面**——把「数据采集与清洗」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
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
| `C01-01` | 网页抓取与合规 | 网页抓取的合规口径：robots 与站点条款遵守、抓取频率上限、以及抓取内容的许可范围。 | 声明 robots_policy（遵守 true / 例外清单）、rate_limit（QPS 或并发上限）与 content_license（逐站点许可来源）。 | 无视 robots 与条款批量抓取；限速缺失导致被封禁并污染采集统计。 | `gdpr` GDPR（EU） |
| `C01-02` | 去重与相似度 | 去重与相似度的口径：去重粒度（文档 / 段落 / 行）、相似度方法与阈值、以及保留策略。 | 声明 dedup_unit（doc|paragraph|line）、method（minhash|simhash|embedding）、threshold 与 keep_policy（最新 / 最长 / 来源优先）。 | 只做精确去重（近似重复泄漏进训练集）；阈值未声明导致去重率不可复现。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `C01-03` | 噪声过滤 | 噪声过滤的口径：噪声类型（模板 / 乱码 / 广告 / 导航）、过滤规则与误删率。 | 声明 noise_types（枚举）、rules（规则集 + 版本）与 false_drop_rate（人工抽检误删率）。 | 正则过宽把正文一起删（误删率不测）；模板变体未覆盖导致噪声残留。 | `frictionless-table` Table Schema（Frictionless） |
| `C01-04` | 格式归一化 | 格式归一化的口径：编码、换行、空白、标点与结构化字段的归一规则。 | 声明 encoding（UTF-8 强制 + NFC/NFKC 选择）、newline（LF）、whitespace_rule 与 field_schema（结构化字段）。 | 混用 NFC/NFKC 导致同一文本两种形态；全角半角未归一造成检索漏召。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `C01-05` | 缺失与异常值 | 缺失与异常值的口径：缺失语义（空 / 哨兵 / 未采集）、异常判定方法与处置策略。 | 声明 missing_semantics（空|NaN|哨兵值）、outlier_method（IQR|z-score|业务规则）与 action（丢弃|插补|标注）。 | 把缺失当 0（统计失真）；插补未记录（无法回溯真实缺失率）。 | `frictionless-table` Table Schema（Frictionless） |
| `C01-06` | 隐私脱敏 | 隐私脱敏的口径：PII 类型清单、脱敏方法（掩码 / 泛化 / 哈希）与可逆性要求。 | 声明 pii_types（枚举）、method（mask|generalize|hash + 盐）与 reversibility（不可逆 true/false + 依据）。 | 只脱敏手机号而漏掉地址与身份证；哈希无盐可被字典反查。 | `gdpr` GDPR（EU） |
| `C01-07` | 多语言清洗 | 多语言清洗的口径：语言识别方法、混排处理与逐语言质量分组报告。 | 声明 lid_method（fasttext|规则 + 版本）、mixed_script_policy 与 per_lang_report（逐语言指标，禁只报平均）。 | 用单语规则清多语数据（弱语言被清空）；只报总体平均掩盖单语崩塌。 | `frictionless-table` Table Schema（Frictionless） |
| `C01-08` | 语料配比与统计 | 语料配比与统计的口径：来源配比、域分布与统计口径（字符 / token / 文档数）。 | 声明 ratio_target（逐源目标占比 ± 容差）、unit（char|token|doc）与 dist_report（域分布统计）。 | 配比按文档数而非 token（实际权重偏差数倍）；统计口径未声明导致跨版本不可比。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `C01-09` | 数据版本与快照 | 数据版本与快照的口径：版本命名、快照粒度、以及可复现的还原方式。 | 声明 version_scheme（日期 + 序号或内容哈希）、snapshot_granularity（全量|增量）与 restore_cmd（可复现还原命令）。 | 覆盖式更新（无法回到旧版本）；快照无校验和导致还原不可验证。 | `frictionless-table` Table Schema（Frictionless） |
| `C01-10` | 数据血缘 | 数据血缘的口径：来源标识、转换步骤记录与字段级溯源能力。 | 声明 source_ids（逐源标识）、transform_log（步骤 + 工具版本）与 field_lineage（字段级是否可追）。 | 只记整表级血缘（字段错无法定位）；转换脚本版本未记录。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |
| `C01-11` | 质量打分 | 质量打分的口径：评分维度、权重与阈值分流（入池 / 复核 / 丢弃）。 | 声明 score_dims（维度清单）、weights（合计 1.0）与 thresholds（三段阈值 + 分流动作）。 | 打分维度与业务目标无关（分数好看但不可用）；阈值未声明导致入池标准漂移。 | `frictionless-table` Table Schema（Frictionless） |
| `C01-12` | 脏数据回溯 | 脏数据回溯的口径：发现渠道、影响面评估与回滚 / 修复流程。 | 声明 discovery_channel（监控|抽样|上报）、impact_analysis（受影响数据集与版本清单）与 rollback（修复或回滚命令）。 | 脏数据已入训练却无影响面清单（无法评估后果）；无回滚路径。 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`contract_compliance`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `数据采集与清洗:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `数据采集与清洗:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
