<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 合规与监管

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `F02-01` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `oasis-openapi` OpenAPI 3.1（OpenAPI Initiative；关键词「接口|API|端点|服务|部署」命中） |
| `F02-02` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；F 段默认绑定（轮换 0）） |
| `F02-03` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；F 段默认绑定（轮换 0）） |
| `F02-04` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；F 段默认绑定（轮换 0）） |
| `F02-05` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `F02-06` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；F 段默认绑定（轮换 0）） |
| `F02-07` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `F02-08` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `F02-09` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `w3c-prov-o` PROV-O 溯源本体（W3C；关键词「溯源|证据链|审计」命中） |
| `F02-10` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `F02-11` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `gdpr` GDPR（EU；关键词「隐私|个人信息|去标识|合规|监管」命中） |
| `F02-12` | spec | https://eur-lex.europa.eu/eli/reg/2024/1689/oj | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；F 段默认绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
