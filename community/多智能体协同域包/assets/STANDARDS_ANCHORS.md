<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 多智能体协同

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `C17-01` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `a2a` A2A 协议（Linux Foundation；域码 C17 专属绑定（轮换 0）） |
| `C17-02` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `cncf-cloudevents` CloudEvents 1.0（CNCF；关键词「事件|消息|通道」命中） |
| `C17-03` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `a2a` A2A 协议（Linux Foundation；域码 C17 专属绑定（轮换 0）） |
| `C17-04` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `a2a` A2A 协议（Linux Foundation；域码 C17 专属绑定（轮换 0）） |
| `C17-05` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `mcp` Model Context Protocol（Anthropic/MCP；关键词「工具调用|智能体|工作流|Agent」命中） |
| `C17-06` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `a2a` A2A 协议（Linux Foundation；域码 C17 专属绑定（轮换 0）） |
| `C17-07` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `a2a` A2A 协议（Linux Foundation；域码 C17 专属绑定（轮换 0）） |
| `C17-08` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `a2a` A2A 协议（Linux Foundation；域码 C17 专属绑定（轮换 0）） |
| `C17-09` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；关键词「可观测|遥测|监控|日志|成本|可靠性」命中） |
| `C17-10` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `C17-11` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；关键词「可观测|遥测|监控|日志|成本|可靠性」命中） |
| `C17-12` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `a2a` A2A 协议（Linux Foundation；关键词「多智能体|协同|编排」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
