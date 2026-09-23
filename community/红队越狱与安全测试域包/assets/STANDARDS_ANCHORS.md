<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 红队、越狱与安全测试

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜细分锚实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）｜标准锚实测日期见下表「标准锚」列（取自 `protocol/standards_catalog.json` 的本机探针记录）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|
| `C09-01` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；关键词「提示|指令|模板」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；C 段载体锚（轮换 0；与主锚异层）） |
| `C09-02` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP｜gov｜✓ 2026-09-24；关键词「安全|越狱|红队|攻击|对抗」命中） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；C 段载体锚（轮换 1；与主锚异层）） |
| `C09-03` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；关键词「提示|指令|模板」命中） | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry｜eng｜✓ 2026-09-24；C 段载体锚（轮换 4；与主锚异层）） |
| `C09-04` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry｜eng｜✓ 2026-09-24；C 段默认绑定（轮换 0）） | `mermaid` Mermaid 图语言（Mermaid｜form｜✓ 2026-09-24；C 段载体锚（轮换 3；与主锚异层）） |
| `C09-05` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP｜gov｜✓ 2026-09-24；关键词「安全|越狱|红队|攻击|对抗」命中） | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry｜eng｜✓ 2026-09-24；C 段载体锚（轮换 4；与主锚异层）） |
| `C09-06` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；C 段默认绑定（轮换 2）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；C 段载体锚（轮换 2；与主锚异层）） |
| `C09-07` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry｜eng｜✓ 2026-09-24；C 段默认绑定（轮换 0）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；C 段载体锚（轮换 2；与主锚异层）） |
| `C09-08` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP｜gov｜✓ 2026-09-24；关键词「安全|越狱|红队|攻击|对抗」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；C 段载体锚（轮换 2；与主锚异层）） |
| `C09-09` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP｜gov｜✓ 2026-09-24；关键词「安全|越狱|红队|攻击|对抗」命中） | `mermaid` Mermaid 图语言（Mermaid｜form｜✓ 2026-09-24；C 段载体锚（轮换 3；与主锚异层）） |
| `C09-10` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP｜gov｜✓ 2026-09-24；关键词「安全|越狱|红队|攻击|对抗」命中） | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry｜eng｜✓ 2026-09-24；C 段载体锚（轮换 4；与主锚异层）） |
| `C09-11` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons｜eng｜✓ 2026-09-24；C 段默认绑定（轮换 1）） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；C 段载体锚（轮换 0；与主锚异层）） |
| `C09-12` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `cwe` CWE 缺陷枚举（MITRE｜gov｜✓ 2026-09-24；关键词「漏洞|缺陷|弱点」命中） | `mermaid` Mermaid 图语言（Mermaid｜form｜✓ 2026-09-24；载体锚：产出形态「图示」的承载标准） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- **双锚分工**：主锚 = 该细分依据的域口径标准（可能与细分锚不同源，形成第二证据链）；辅锚 = 该细分产出（数据 / 契约 / 图表 / 图示 / 溯源）所承载的开放标准。
- 标准锚取自 `protocol/standards_catalog.json` 的**本机实测记录**（含取样标题与 sha256），可达性 false 如实标注，不假装可达。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
