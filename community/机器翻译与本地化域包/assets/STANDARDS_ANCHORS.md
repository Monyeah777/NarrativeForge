<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 机器翻译与本地化

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `B03-01` | paper | https://arxiv.org/abs/1609.08144 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B03-02` | dataset | https://iate.europa.eu/ | ✓ 200 | `w3c-skos` SKOS 词表（W3C；关键词「术语|词表|本体|知识图谱」命中） |
| `B03-03` | doc | https://www.statmt.org/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B03-04` | dataset | https://opus.nlpl.eu/ | ✓ 200 | `oci-image` 镜像清单（OCI；关键词「视频|剪辑|字幕」命中） |
| `B03-05` | spec | https://docs.oasis-open.org/xliff/xliff-core/v2.1/os/xliff-core-v2.1-os.html | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B03-06` | paper | https://arxiv.org/abs/2207.04672 | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B03-07` | repo | https://pypi.org/project/translate-toolkit/ | ✓ 200 | `w3c-skos` SKOS 词表（W3C；关键词「术语|词表|本体|知识图谱」命中） |
| `B03-08` | spec | https://cldr.unicode.org/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B03-09` | spec | https://themqm.org/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B03-10` | repo | https://www.masakhane.io/ | ✓ 200 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema；B 段默认绑定（轮换 0）） |
| `B03-11` | paper | https://arxiv.org/abs/2009.09025 | ✓ 200 | `frictionless-table` Table Schema（Frictionless；关键词「采集|清洗|质量|异常|缺失」命中） |
| `B03-12` | spec | https://www.w3.org/International/ | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
