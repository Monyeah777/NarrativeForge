<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 知识问答与检索增强

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `B06-01` | paper | https://arxiv.org/abs/2005.11401 | ✓ 200 | `frictionless-package` Data Package（Frictionless；关键词「检索|向量|嵌入|召回」命中） |
| `B06-02` | paper | https://arxiv.org/abs/2004.05150 | ✓ 200 | `gfm` GFM 扩展（GitHub；关键词「缓存|分块|上下文」命中） |
| `B06-03` | paper | https://arxiv.org/abs/2305.15294 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B06-04` | paper | https://arxiv.org/abs/2210.11934 | ✓ 200 | `frictionless-package` Data Package（Frictionless；关键词「检索|向量|嵌入|召回」命中） |
| `B06-05` | paper | https://arxiv.org/abs/1908.10084 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B06-06` | paper | https://arxiv.org/abs/2310.04408 | ✓ 200 | `gfm` GFM 扩展（GitHub；关键词「缓存|分块|上下文」命中） |
| `B06-07` | paper | https://arxiv.org/abs/2305.14627 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B06-08` | paper | https://arxiv.org/abs/1809.09600 | ✓ 200 | `frictionless-table` Table Schema（Frictionless；关键词「问答|知识库」命中） |
| `B06-09` | paper | https://arxiv.org/abs/2005.11401 | ✓ 200 | `frictionless-table` Table Schema（Frictionless；关键词「问答|知识库」命中） |
| `B06-10` | paper | https://arxiv.org/abs/2207.05221 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B06-11` | paper | https://arxiv.org/abs/2309.15217 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `B06-12` | paper | https://arxiv.org/abs/2305.14251 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
