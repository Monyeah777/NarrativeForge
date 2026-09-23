<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 代码大模型

> 用途：本域包的**内容资产与口径面**——把「代码大模型」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
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
| `A09-01` | 代码补全与上下文 | 代码补全与上下文的口径：上下文窗口构造（前后文 / 跨文件）、触发方式与补全长度上限。 | 声明 context_mode（prefix|prefix+suffix|repo）、window_tokens 与 max_completion_tokens。 | 只给前缀（无后缀）导致插入式补全不成立；长度上限未声明导致截断不可见。 | `gfm` GFM 扩展（GitHub） |
| `A09-02` | 仓库级代码理解 | 仓库级代码理解的口径：符号索引粒度、跨文件依赖解析与上下文裁剪策略。 | 声明 symbol_index（函数|类|文件）、cross_file（true|false + 解析方式）与 pruning（裁剪策略）。 | 把「多文件拼接」当仓库理解；裁剪无策略导致关键定义被切掉。 | `cwe` CWE 缺陷枚举（MITRE） |
| `A09-03` | 代码检索与索引 | 代码检索与索引的口径：索引单位（文本 / AST / 向量）、刷新时机与检索指标。 | 声明 index_unit（text|ast|embedding）、refresh（增量|全量 + 触发）与 metric（MRR|R@k）。 | 索引不刷新导致检索到旧代码；指标口径与候选库规模未声明。 | `frictionless-package` Data Package（Frictionless） |
| `A09-04` | 多语言代码翻译 | 多语言代码翻译的口径：源 / 目标语言对、语义等价判定与测试驱动验证。 | 声明 lang_pair、equivalence_check（测试驱动|人工）与 test_coverage（执行用例数）。 | 只比文本相似度（不等价也判对）；无测试执行证据。 | `osv` OSV 漏洞格式（Google/OSV） |
| `A09-05` | 缺陷与漏洞检测 | 缺陷与漏洞检测的口径：缺陷类型体系（CWE 等）、误报基线与修复建议要求。 | 声明 defect_taxonomy（CWE id 或自定义词表）、false_positive_baseline（对照工具/基线）与 fix_suggestion（有|无）。 | 只报「发现漏洞数」不给误报基线；缺陷不绑 CWE 类导致无法评测。 | `cwe` CWE 缺陷枚举（MITRE） |
| `A09-06` | 单元测试生成 | 单元测试生成的口径：覆盖率来源、断言质量与可执行性验证。 | 声明 coverage_tool（含版本）、assertion_count（每测试断言数）与 executability（生成测试实测通过率）。 | 无断言测试（只跑不验）；覆盖率由被测代码自报而非工具实测。 | `lsp` Language Server Protocol（Microsoft） |
| `A09-07` | SQL 生成与优化 | SQL 生成与优化的口径：模式（schema）注入方式、结果等价判定与执行计划对比。 | 声明 schema_injection（DDL|摘要）、equivalence（结果集比对|执行计划比对）与 db_engine（含版本）。 | 只看 SQL 字符串相似度；方言与版本未声明导致行为差异。 | `osv` OSV 漏洞格式（Google/OSV） |
| `A09-08` | Shell 与运维脚本 | Shell 与运维脚本的口径：目标 shell / 平台、幂等性要求与危险操作防护。 | 声明 target_shell（bash|zsh|powershell + 版本）、idempotent（true|false）与 dangerous_ops_guard（删改命令确认机制）。 | 脚本不可重跑（破坏幂等）；无危险操作防护（rm -rf 类无确认）。 | `cwe` CWE 缺陷枚举（MITRE） |
| `A09-09` | 重构与迁移 | 重构与迁移的口径：行为保持的证据（测试前后通过率）、变更范围与回滚点。 | 声明 behavior_preserve（重构前后测试通过率）、change_scope（文件/符号清单）与 rollback_point（提交/标签）。 | 无测试证据就宣称行为保持；变更范围超出声明（顺带改逻辑）。 | `lsp` Language Server Protocol（Microsoft） |
| `A09-10` | 代码解释与注释 | 代码解释与注释的口径：解释粒度、术语一致性与误导防护。 | 声明 granularity（函数|模块|行）、term_consistency（术语表引用）与 claim_check（解释中的事实性断言是否可复核）。 | 解释里编造不存在的参数；术语与代码不一致（阅读者被误导）。 | `osv` OSV 漏洞格式（Google/OSV） |
| `A09-11` | 代码评测基准 | 代码评测基准的口径：基准名与版本、通过判据（测试执行）与污染检查。 | 声明 benchmark（id + 版本）、pass_criterion（测试执行|文本匹配）与 contamination_check（训练集污染检查）。 | 用文本匹配当通过判据（虚高）；训练集含基准题（污染）。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons） |
| `A09-12` | 私有代码安全 | 私有代码安全的口径：数据出域边界、检索范围隔离与审计留痕。 | 声明 egress_policy（本地|私有云|公网）、index_isolation（按仓库/租户隔离）与 audit_trail（请求与检索留痕字段）。 | 私有代码进入外部训练/日志；索引跨租户共享。 | `owasp-llm` LLM 应用十大风险（OWASP） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`exact_judgement`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `代码大模型:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `代码大模型:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
