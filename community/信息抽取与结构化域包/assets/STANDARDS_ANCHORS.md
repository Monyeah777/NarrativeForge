<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 信息抽取与结构化

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `B05-01` | paper | https://arxiv.org/abs/1810.04805 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B05-02` | paper | https://arxiv.org/abs/1906.03158 | ✓ 200 | `rdf11` RDF 1.1（W3C；关键词「三元组|关系抽取」命中） |
| `B05-03` | paper | https://arxiv.org/abs/2004.13625 | ✓ 200 | `cncf-cloudevents` CloudEvents 1.0（CNCF；关键词「事件|消息|通道」命中） |
| `B05-04` | paper | https://arxiv.org/abs/2003.02320 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B05-05` | paper | https://arxiv.org/abs/2110.00061 | ✓ 200 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C；关键词「表格|CSV|列式」命中） |
| `B05-06` | paper | https://arxiv.org/abs/2110.01799 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B05-07` | repo | https://pypi.org/project/pyresparser/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B05-08` | paper | https://arxiv.org/abs/2103.14470 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B05-09` | paper | https://arxiv.org/abs/2003.02320 | ✓ 200 | `w3c-skos` SKOS 词表（W3C；关键词「术语|词表|本体|知识图谱」命中） |
| `B05-10` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；关键词「约束|校验|schema|形状|契约」命中） |
| `B05-11` | spec | https://specs.frictionlessdata.io/table-schema/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「训练|微调|对齐|蒸馏|偏好」命中） |
| `B05-12` | paper | https://arxiv.org/abs/2102.04664 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
