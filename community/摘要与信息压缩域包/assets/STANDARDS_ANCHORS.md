<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 摘要与信息压缩

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `B02-01` | repo | https://pypi.org/project/sumy/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B02-02` | paper | https://arxiv.org/abs/1704.04368 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B02-03` | paper | https://arxiv.org/abs/1906.01749 | ✓ 200 | `w3c-epub33` EPUB 3.3（W3C；关键词「文档|出版|排版|校对」命中） |
| `B02-04` | dataset | https://groups.inf.ed.ac.uk/ami/corpus/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B02-05` | paper | https://arxiv.org/abs/1912.08777 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B02-06` | repo | https://pypi.org/project/yake/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B02-07` | paper | https://arxiv.org/abs/2004.05150 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B02-08` | paper | https://arxiv.org/abs/2111.09525 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B02-09` | paper | https://pypi.org/project/sumy/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B02-10` | paper | https://arxiv.org/abs/2010.11934 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B02-11` | paper | https://arxiv.org/abs/1904.09675 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `B02-12` | paper | https://arxiv.org/abs/1906.01749 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
