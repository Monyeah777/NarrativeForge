<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 多轮对话与角色扮演

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜细分锚实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）｜标准锚实测日期见下表「标准锚」列（取自 `protocol/standards_catalog.json` 的本机探针记录）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|
| `B07-01` | paper | https://arxiv.org/abs/1801.07243 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段默认绑定（轮换 0）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B07-02` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段默认绑定（轮换 1）） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；载体锚：产出形态「契约」的承载标准） |
| `B07-03` | paper | https://arxiv.org/abs/2307.03172 | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；B 段默认绑定（轮换 2）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B07-04` | paper | https://arxiv.org/abs/1810.00278 | ✓ 200 | `gfm` GFM 扩展（GitHub｜form｜✓ 2026-09-24；关键词「缓存|分块|上下文」命中） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；B 段载体锚（轮换 4；与主锚异层）） |
| `B07-05` | paper | https://arxiv.org/abs/2308.07201 | ✓ 200 | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；B 段默认绑定（轮换 1）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B07-06` | paper | https://arxiv.org/abs/2212.08073 | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP｜gov｜✓ 2026-09-24；关键词「安全|越狱|红队|攻击|对抗」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B07-07` | paper | https://arxiv.org/abs/2106.01144 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段默认绑定（轮换 0）） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |
| `B07-08` | spec | https://www.w3.org/TR/owl-time/ | ✓ 200 | `w3c-owl-time` OWL-Time 时间本体（W3C｜data｜✓ 2026-09-24；关键词「时间线|时序|日期」命中） | `ietf-ixdtf` IXDTF (RFC 9557)（IETF｜data｜✓ 2026-09-24；载体锚：产出形态「时间」的承载标准） |
| `B07-09` | paper | https://arxiv.org/abs/2005.14165 | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；B 段默认绑定（轮换 2）） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；B 段载体锚（轮换 3；与主锚异层）） |
| `B07-10` | paper | https://arxiv.org/abs/2310.08560 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段默认绑定（轮换 0）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 1；与主锚异层）） |
| `B07-11` | paper | https://arxiv.org/abs/2310.00746 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons｜eng｜✓ 2026-09-24；关键词「评测|基准|排行榜|跑分」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；B 段载体锚（轮换 0；与主锚异层）） |
| `B07-12` | paper | https://arxiv.org/abs/2106.01144 | ✓ 200 | `frictionless-table` Table Schema（Frictionless｜data｜✓ 2026-09-24；B 段默认绑定（轮换 2）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；B 段载体锚（轮换 2；与主锚异层）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- **双锚分工**：主锚 = 该细分依据的域口径标准（可能与细分锚不同源，形成第二证据链）；辅锚 = 该细分产出（数据 / 契约 / 图表 / 图示 / 溯源）所承载的开放标准。
- 标准锚取自 `protocol/standards_catalog.json` 的**本机实测记录**（含取样标题与 sha256），可达性 false 如实标注，不假装可达。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
