<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 数据分析与表格理解

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜细分锚实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）｜标准锚实测日期见下表「标准锚」列（取自 `protocol/standards_catalog.json` 的本机探针记录）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|
| `B11-01` | paper | https://arxiv.org/abs/1909.00754 | ✓ 200 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；关键词「表格|CSV|列式」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B11-02` | paper | https://arxiv.org/abs/2004.07360 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation｜iface｜✓ 2026-09-24；关键词「模型|推理|量化」命中） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；载体锚：产出形态「表」的承载标准） |
| `B11-03` | spec | https://vega.github.io/schema/vega-lite/v5.json | ✓ 200 | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；关键词「图表|可视化|看板」命中） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；载体锚：产出形态「表」的承载标准） |
| `B11-04` | spec | https://specs.frictionlessdata.io/table-schema/ | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；关键词「采集|清洗|质量|异常|缺失」命中） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 3；与主锚异层）） |
| `B11-05` | spec | https://www.cfainstitute.org/en/ethics-standards/codes/gips-standards | ✓ 200 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段默认绑定（轮换 1）） | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry｜eng｜✓ 2026-09-24；载体锚：产出形态「遥测」的承载标准） |
| `B11-06` | doc | https://www.sqlite.org/lang.html | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；B 段默认绑定（轮换 2）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B11-07` | doc | https://scikit-learn.org/stable/modules/outlier_detection.html | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；关键词「采集|清洗|质量|异常|缺失」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B11-08` | doc | https://www.statsmodels.org/stable/tsa.html | ✓ 200 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段默认绑定（轮换 1）） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；B 段载体锚（轮换 3；与主锚异层）） |
| `B11-09` | doc | https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/view-dashboard-json-model/ | ✓ 200 | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；关键词「图表|可视化|看板」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B11-10` | paper | https://arxiv.org/abs/2305.14251 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段默认绑定（轮换 0）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B11-11` | paper | https://arxiv.org/abs/1706.04599 | ✓ 200 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段默认绑定（轮换 1）） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B11-12` | spec | https://csrc.nist.gov/pubs/sp/800/188/final | ✓ 200 | `nist-800-188` SP 800-188 去标识化（NIST｜gov｜✓ 2026-09-24；关键词「权限|访问控制|治理」命中） | `w3c-vc` Verifiable Credentials 2.0（W3C｜gov｜✓ 2026-09-24；载体锚：产出形态「身份」的承载标准） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- **双锚分工**：主锚 = 该细分依据的域口径标准（可能与细分锚不同源，形成第二证据链）；辅锚 = 该细分产出（数据 / 契约 / 图表 / 图示 / 溯源）所承载的开放标准。
- 标准锚取自 `protocol/standards_catalog.json` 的**本机实测记录**（含取样标题与 sha256），可达性 false 如实标注，不假装可达。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
