<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 向量库与检索管线

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `C15-01` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `arrow` Arrow 列式格式（Apache；域码 C15 专属绑定（轮换 0）） |
| `C15-02` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `arrow` Arrow 列式格式（Apache；域码 C15 专属绑定（轮换 0）） |
| `C15-03` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `mlcommons-croissant` Croissant 数据集元数据（MLCommons；关键词「数据集|元数据|标注」命中） |
| `C15-04` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `frictionless-package` Data Package（Frictionless；关键词「检索|向量|嵌入|召回」命中） |
| `C15-05` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `arrow` Arrow 列式格式（Apache；域码 C15 专属绑定（轮换 0）） |
| `C15-06` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `arrow` Arrow 列式格式（Apache；域码 C15 专属绑定（轮换 0）） |
| `C15-07` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `frictionless-package` Data Package（Frictionless；关键词「检索|向量|嵌入|召回」命中） |
| `C15-08` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `arrow` Arrow 列式格式（Apache；域码 C15 专属绑定（轮换 0）） |
| `C15-09` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `C15-10` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `nist-800-188` SP 800-188 去标识化（NIST；关键词「权限|访问控制|治理」命中） |
| `C15-11` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `arrow` Arrow 列式格式（Apache；域码 C15 专属绑定（轮换 0）） |
| `C15-12` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；关键词「可观测|遥测|监控|日志|成本|可靠性」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
