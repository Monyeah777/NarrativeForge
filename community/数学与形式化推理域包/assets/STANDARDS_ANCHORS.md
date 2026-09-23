<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 数学与形式化推理

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `A10-01` | paper | https://arxiv.org/abs/2201.11903 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `A10-02` | doc | https://leanprover.github.io/ | ✓ 200 | `w3c-mathml3` MathML 3（W3C；关键词「公式|数学|符号|证明」命中） |
| `A10-03` | doc | http://us.metamath.org/ | ✓ 200 | `w3c-mathml3` MathML 3（W3C；关键词「公式|数学|符号|证明」命中） |
| `A10-04` | doc | https://docs.sympy.org/latest/index.html | ✓ 200 | `w3c-mathml3` MathML 3（W3C；关键词「公式|数学|符号|证明」命中） |
| `A10-05` | paper | https://arxiv.org/abs/2110.14168 | ✓ 200 | `w3c-mathml3` MathML 3（W3C；关键词「公式|数学|符号|证明」命中） |
| `A10-06` | paper | https://arxiv.org/abs/2103.03874 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `A10-07` | paper | https://arxiv.org/abs/2305.20050 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `A10-08` | paper | https://arxiv.org/abs/2203.11171 | ✓ 200 | `w3c-mathml3` MathML 3（W3C；域码 A10 专属绑定（轮换 0）） |
| `A10-09` | doc | https://networkx.org/documentation/stable/ | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `A10-10` | doc | https://docs.python.org/3/tutorial/floatingpoint.html | ✓ 200 | `ieee-754` 浮点运算标准（IEEE；关键词「浮点|数值|精度|误差」命中） |
| `A10-11` | paper | https://arxiv.org/abs/2305.14251 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `A10-12` | paper | https://arxiv.org/abs/2211.10438 | ✓ 200 | `cncf-otel-semconv` 语义约定（可扩展注册表）（OpenTelemetry；关键词「可观测|遥测|监控|日志|成本|可靠性」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
