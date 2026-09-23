<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 强化学习与决策

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `A12-01` | paper | https://arxiv.org/abs/1707.06347 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；域码 A12 专属绑定（轮换 0）） |
| `A12-02` | paper | https://arxiv.org/abs/2006.04779 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；域码 A12 专属绑定（轮换 0）） |
| `A12-03` | paper | https://arxiv.org/abs/2301.04104 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation；关键词「模型|推理|量化」命中） |
| `A12-04` | paper | https://arxiv.org/abs/1204.5721 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；域码 A12 专属绑定（轮换 0）） |
| `A12-05` | paper | https://arxiv.org/abs/1706.03741 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；域码 A12 专属绑定（轮换 0）） |
| `A12-06` | doc | https://gymnasium.farama.org/ | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；域码 A12 专属绑定（轮换 0）） |
| `A12-07` | paper | https://arxiv.org/abs/1706.02275 | ✓ 200 | `mcp` Model Context Protocol（Anthropic/MCP；关键词「工具调用|智能体|工作流|Agent」命中） |
| `A12-08` | paper | https://arxiv.org/abs/1911.08265 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；域码 A12 专属绑定（轮换 0）） |
| `A12-09` | paper | https://arxiv.org/abs/1909.04847 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；域码 A12 专属绑定（轮换 0）） |
| `A12-10` | paper | https://arxiv.org/abs/1810.01963 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；域码 A12 专属绑定（轮换 0）） |
| `A12-11` | paper | https://arxiv.org/abs/2203.02155 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；域码 A12 专属绑定（轮换 0）） |
| `A12-12` | paper | https://arxiv.org/abs/1709.06560 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「训练|微调|对齐|蒸馏|偏好」命中） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
