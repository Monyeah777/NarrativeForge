<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 预测、异常与风险

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜细分锚实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）｜标准锚实测日期见下表「标准锚」列（取自 `protocol/standards_catalog.json` 的本机探针记录）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|
| `B18-01` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `w3c-owl-time` OWL-Time 时间本体（W3C｜data｜✓ 2026-09-24；关键词「时间线|时序|日期」命中） | `ietf-ixdtf` IXDTF (RFC 9557)（IETF｜data｜✓ 2026-09-24；载体锚：产出形态「时间」的承载标准） |
| `B18-02` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段默认绑定（轮换 1）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B18-03` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；关键词「采集|清洗|质量|异常|缺失」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B18-04` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段默认绑定（轮换 0）） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；B 段载体锚（轮换 3；与主锚异层）） |
| `B18-05` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute｜gov｜✓ 2026-09-24；关键词「金融|投研|风控|保险|绩效」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B18-06` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；B 段默认绑定（轮换 2）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B18-07` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段默认绑定（轮换 0）） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B18-08` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `opcua` OPC UA 工业互联（OPC Foundation｜iface｜✓ 2026-09-24；关键词「制造|产线|设备|工业」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B18-09` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；B 段默认绑定（轮换 2）） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 3；与主锚异层）） |
| `B18-10` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `gips` GIPS 绩效标准（CFA Institute｜gov｜✓ 2026-09-24；关键词「金融|投研|风控|保险|绩效」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B18-11` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry｜eng｜✓ 2026-09-24；关键词「可观测|遥测|监控|日志|成本|可靠性」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B18-12` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation｜iface｜✓ 2026-09-24；关键词「模型|推理|量化」命中） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- **双锚分工**：主锚 = 该细分依据的域口径标准（可能与细分锚不同源，形成第二证据链）；辅锚 = 该细分产出（数据 / 契约 / 图表 / 图示 / 溯源）所承载的开放标准。
- 标准锚取自 `protocol/standards_catalog.json` 的**本机实测记录**（含取样标题与 sha256），可达性 false 如实标注，不假装可达。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
