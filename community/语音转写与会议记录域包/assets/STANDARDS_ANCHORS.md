<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 语音转写与会议记录

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜细分锚实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）｜标准锚实测日期见下表「标准锚」列（取自 `protocol/standards_catalog.json` 的本机探针记录）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|
| `B13-01` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段默认绑定（轮换 0）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B13-02` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段默认绑定（轮换 1）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B13-03` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；B 段默认绑定（轮换 2）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B13-04` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段默认绑定（轮换 0）） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；B 段载体锚（轮换 3；与主锚异层）） |
| `B13-05` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `w3c-skos` SKOS 词表（W3C｜data｜✓ 2026-09-24；关键词「术语|词表|本体|知识图谱」命中） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；B 段载体锚（轮换 4；与主锚异层）） |
| `B13-06` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `rfc3339` 时间戳（IETF｜data｜✓ 2026-09-24；关键词「时间戳|时区」命中） | `ietf-ixdtf` IXDTF (RFC 9557)（IETF｜data｜✓ 2026-09-24；载体锚：产出形态「时间」的承载标准） |
| `B13-07` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段默认绑定（轮换 0）） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B13-08` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `w3c-webaudio` Web Audio API（W3C｜form｜✓ 2026-09-24；关键词「音频|语音|声学|音乐|歌声」命中） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；B 段载体锚（轮换 4；与主锚异层）） |
| `B13-09` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons｜eng｜✓ 2026-09-24；关键词「评测|基准|排行榜|跑分」命中） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 3；与主锚异层）） |
| `B13-10` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `gdpr` GDPR（EU｜gov｜✓ 2026-09-24；关键词「隐私|个人信息|去标识|合规|监管」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B13-11` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段默认绑定（轮换 1）） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B13-12` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；B 段默认绑定（轮换 2）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- **双锚分工**：主锚 = 该细分依据的域口径标准（可能与细分锚不同源，形成第二证据链）；辅锚 = 该细分产出（数据 / 契约 / 图表 / 图示 / 溯源）所承载的开放标准。
- 标准锚取自 `protocol/standards_catalog.json` 的**本机实测记录**（含取样标题与 sha256），可达性 false 如实标注，不假装可达。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
