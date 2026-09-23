<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 对齐与偏好优化

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `C07-01` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `mermaid` Mermaid 图语言（Mermaid；关键词「流程|结构图|示意」命中） |
| `C07-02` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；C 段默认绑定（轮换 0）） |
| `C07-03` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「训练|微调|对齐|蒸馏|偏好」命中） |
| `C07-04` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `C07-05` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；C 段默认绑定（轮换 0）） |
| `C07-06` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `owasp-llm` LLM 应用十大风险（OWASP；关键词「安全|越狱|红队|攻击|对抗」命中） |
| `C07-07` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；C 段默认绑定（轮换 0）） |
| `C07-08` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「训练|微调|对齐|蒸馏|偏好」命中） |
| `C07-09` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「训练|微调|对齐|蒸馏|偏好」命中） |
| `C07-10` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `C07-11` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；C 段默认绑定（轮换 0）） |
| `C07-12` | spec | https://mlcommons.org/benchmarks/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「训练|微调|对齐|蒸馏|偏好」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
