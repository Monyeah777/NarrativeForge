<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 交通与出行

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `D13-01` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `covesa-vss` Vehicle Signal Specification（COVESA；关键词「交通|出行|车机|车辆|导航」命中） |
| `D13-02` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；D 段默认绑定（轮换 0）） |
| `D13-03` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；D 段默认绑定（轮换 0）） |
| `D13-04` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；D 段默认绑定（轮换 0）） |
| `D13-05` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `covesa-vss` Vehicle Signal Specification（COVESA；关键词「交通|出行|车机|车辆|导航」命中） |
| `D13-06` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `frictionless-table` Table Schema（Frictionless；关键词「问答|知识库」命中） |
| `D13-07` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；D 段默认绑定（轮换 0）） |
| `D13-08` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `a2a` A2A 协议（Linux Foundation；关键词「多智能体|协同|编排」命中） |
| `D13-09` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；D 段默认绑定（轮换 0）） |
| `D13-10` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；D 段默认绑定（轮换 0）） |
| `D13-11` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `nist-ai-rmf` AI 风险管理框架（NIST；D 段默认绑定（轮换 0）） |
| `D13-12` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP；关键词「安全|越狱|红队|攻击|对抗」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
