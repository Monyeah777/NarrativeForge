<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 数据采集与清洗

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `C01-01` | spec | https://www.rfc-editor.org/rfc/rfc9309.txt | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `C01-02` | spec | https://specs.frictionlessdata.io/table-schema/ | ✓ 200 | `frictionless-table` Table Schema（Frictionless；域码 C01 专属绑定（轮换 0）） |
| `C01-03` | spec | https://www.w3.org/TR/tabular-data-model/ | ✓ 200 | `frictionless-table` Table Schema（Frictionless；域码 C01 专属绑定（轮换 0）） |
| `C01-04` | spec | https://www.unicode.org/reports/ | ✓ 200 | `frictionless-table` Table Schema（Frictionless；域码 C01 专属绑定（轮换 0）） |
| `C01-05` | spec | https://specs.frictionlessdata.io/table-schema/ | ✓ 200 | `frictionless-table` Table Schema（Frictionless；关键词「采集|清洗|质量|异常|缺失」命中） |
| `C01-06` | spec | https://csrc.nist.gov/pubs/sp/800/188/final | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `C01-07` | spec | https://www.rfc-editor.org/rfc/rfc5646.txt | ✓ 200 | `frictionless-table` Table Schema（Frictionless；关键词「采集|清洗|质量|异常|缺失」命中） |
| `C01-08` | spec | https://docs.mlcommons.org/croissant/docs/croissant-spec.html | ✓ 200 | `frictionless-table` Table Schema（Frictionless；域码 C01 专属绑定（轮换 0）） |
| `C01-09` | spec | https://www.rfc-editor.org/rfc/rfc8493.txt | ✓ 200 | `frictionless-table` Table Schema（Frictionless；域码 C01 专属绑定（轮换 0）） |
| `C01-10` | spec | https://www.w3.org/TR/prov-o/ | ✓ 200 | `frictionless-table` Table Schema（Frictionless；域码 C01 专属绑定（轮换 0）） |
| `C01-11` | spec | https://json-schema.org/draft/2020-12/json-schema-core | ✓ 200 | `frictionless-table` Table Schema（Frictionless；关键词「采集|清洗|质量|异常|缺失」命中） |
| `C01-12` | spec | https://www.w3.org/TR/prov-o/ | ✓ 200 | `frictionless-table` Table Schema（Frictionless；域码 C01 专属绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
