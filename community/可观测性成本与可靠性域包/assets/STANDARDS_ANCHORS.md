<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 可观测性、成本与可靠性

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `C18-01` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；域码 C18 专属绑定（轮换 0）） |
| `C18-02` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；关键词「可观测|遥测|监控|日志|成本|可靠性」命中） |
| `C18-03` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `onvif-ucum` 统一计量单位代码（UCUM；关键词「单位|量纲|计量」命中） |
| `C18-04` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；关键词「可观测|遥测|监控|日志|成本|可靠性」命中） |
| `C18-05` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；域码 C18 专属绑定（轮换 0）） |
| `C18-06` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；关键词「可观测|遥测|监控|日志|成本|可靠性」命中） |
| `C18-07` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `frictionless-table` Table Schema（Frictionless；关键词「采集|清洗|质量|异常|缺失」命中） |
| `C18-08` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `C18-09` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；域码 C18 专属绑定（轮换 0）） |
| `C18-10` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；域码 C18 专属绑定（轮换 0）） |
| `C18-11` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；域码 C18 专属绑定（轮换 0）） |
| `C18-12` | spec | https://opentelemetry.io/docs/specs/semconv/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；域码 C18 专属绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
