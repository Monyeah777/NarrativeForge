<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 代码审查与缺陷检测

> 用途：本域包的**内容资产与口径面**——把「代码审查与缺陷检测」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
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
| `B09-01` | 静态审查规则 | 静态分析与规则引擎的口径：规则集与版本、扫描范围与规则命中口径。 | 声明 ruleset（来源 + 版本）、scan_scope（路径 / 语言）与 hit_definition（单条=一处代码位置）。 | 规则集版本漂移（两次扫描结果不同）；命中定义不同（按文件/按行）导致计数不可比。 | `oasis-sarif` SARIF 2.1.0（iface｜✓） | `ietf-json-schema` JSON Schema 2020-12（data｜✓） |
| `B09-02` | 漏洞模式识别 | 漏洞类型与分类体系的口径：CWE / OWASP 映射与严重度分级依据。 | 声明 taxonomy（CWE|OWASP + 版本）、severity_scheme（CVSS 或自定义 + 依据）与 mapping（逐条映射表）。 | 严重度凭感觉（不可比）；无分类映射导致修复优先级失真。 | `cwe` CWE 缺陷枚举（gov｜✓） | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） |
| `B09-03` | 代码异味 | 代码异味与复杂度的口径：度量（圈复杂度 / 认知复杂度 / 函数长度）与阈值来源。 | 声明 metrics（度量清单）、thresholds（各项阈值 + 来源）与 counting_rule（是否含布尔分支）。 | 阈值不声明（结论不可复现）；复杂度计数规则不同横向比。 | `osv` OSV 漏洞格式（gov｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `B09-04` | 依赖与供应链风险 | 依赖与供应链风险的口径：依赖清单来源、漏洞库版本与可修复性判定。 | 声明 lockfile（来源与格式）、vuln_db（OSV/NVD + 抓取日期）与 fixability（有无可用升级版本）。 | 漏洞库过期（漏报）；不区分「可修/不可修」导致告警积压。 | `spdx-3` SPDX 3.0（含 AI profile）（gov｜✓） | `commonmark` CommonMark 0.31.2（form｜✓） |
| `B09-05` | 提交信息与 PR 描述 | 密钥与敏感信息泄露的口径：检测规则、误报基线与泄露后的处置流程。 | 声明 rules（规则集 + 版本）、false_positive_baseline（对照基线）与 response_sop（轮换 / 撤销步骤）。 | 只扫不处置（密钥仍在）；无基线导致误报淹没真报。 | `cwe` CWE 缺陷枚举（gov｜✓） | `ietf-json-schema` JSON Schema 2020-12（data｜✓） |
| `B09-06` | 变更影响面分析 | 测试覆盖与回归的口径：覆盖率口径（行 / 分支）、增量覆盖与回归门阈值。 | 声明 coverage_kind（line|branch）、delta_coverage（增量 vs 全量）与 gate_threshold（合入阈值）。 | 只看全量覆盖率（新增代码裸奔）；口径（行/分支）混用。 | `osv` OSV 漏洞格式（gov｜✓） | `ietf-json-schema` JSON Schema 2020-12（data｜✓） |
| `B09-07` | 测试覆盖缺口 | 审查意见质量与去噪的口径：意见可操作性、优先级与噪声率控制。 | 声明 actionability（每条须含位置 + 建议）、priority（分级规则）与 noise_rate（被作者标记为无效的比例）。 | 泛泛而谈（不可执行）；噪声率不统计导致审查疲劳。 | `oasis-sarif` SARIF 2.1.0（iface｜✓） | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） |
| `B09-08` | 性能反模式 | 增量审查与 diff 范围的口径：审查范围定义、历史上下文取舍与重复评论抑制。 | 声明 review_scope（diff|文件|全仓）、history_context（是否带历史）与 dedup_rule（同问题不重复报）。 | 每次全仓重报（噪声爆炸）；diff 基线不明导致漏审。 | `cwe` CWE 缺陷枚举（gov｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `B09-09` | 审查意见生成 | 缺陷预测与排序的口径：特征 / 模型来源、排序指标与人工复核比例。 | 声明 prediction_source（规则|模型 + 版本）、ranking_metric（如 recall@10）与 human_audit_ratio。 | 只报准确率不报排序质量（前几条没用）；不抽检。 | `osv` OSV 漏洞格式（gov｜✓） | `commonmark` CommonMark 0.31.2（form｜✓） |
| `B09-10` | 误报率控制 | 修复建议与补丁正确性的口径：补丁验证方式（测试驱动）、回归风险与回滚点。 | 声明 patch_validation（测试执行 + 通过判据）、regression_check（原有测试是否仍过）与 rollback_point。 | 补丁未经测试就建议合入；不查回归。 | `oasis-sarif` SARIF 2.1.0（iface｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `B09-11` | 审查优先级排序 | 误报治理与基线的口径：误报定义、基线快照与抑制规则的生命周期。 | 声明 fp_definition（判据）、baseline_snapshot（时间 + 计数）与 suppression_ttl（抑制有效期 + 复审）。 | 抑制无期限（永久掩盖）；基线不更新导致趋势失真。 | `cwe` CWE 缺陷枚举（gov｜✓） | `ietf-json-schema` JSON Schema 2020-12（data｜✓） |
| `B09-12` | 自动化门禁集成 | 审查结果可机验的口径：输出格式（SARIF 等）、字段完整性与消费方。 | 声明 output_format（SARIF 2.1.0 等）、required_fields（ruleId/level/location）与 consumers（IDE|CI|门禁）。 | 输出纯文本（无法门禁化）；字段缺失导致定位失败。 | `osv` OSV 漏洞格式（gov｜✓） | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`classification`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `代码审查与缺陷检测:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `代码审查与缺陷检测:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
