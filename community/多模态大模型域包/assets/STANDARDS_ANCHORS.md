<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 多模态大模型

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 可扩展标准（绑定） |
|---|---|---|---|---|
| `A02-01` | paper | https://arxiv.org/abs/2103.00020 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「训练|微调|对齐|蒸馏|偏好」命中） |
| `A02-02` | paper | https://arxiv.org/abs/2010.11929 | ✓ 200 | `w3c-svg2` SVG 2（W3C；关键词「图像|视觉|扩散|超分|抠图」命中） |
| `A02-03` | paper | https://arxiv.org/abs/2301.12597 | ✓ 200 | `w3c-svg2` SVG 2（W3C；域码 A02 专属绑定（轮换 0）） |
| `A02-04` | paper | https://arxiv.org/abs/2204.14198 | ✓ 200 | `w3c-svg2` SVG 2（W3C；域码 A02 专属绑定（轮换 0）） |
| `A02-05` | paper | https://arxiv.org/abs/2306.12925 | ✓ 200 | `oci-image` 镜像清单（OCI；关键词「视频|剪辑|字幕」命中） |
| `A02-06` | paper | https://arxiv.org/abs/2304.08485 | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark；关键词「提示|指令|模板」命中） |
| `A02-07` | spec | https://www.nist.gov/itl/ai-risk-management-framework | ✓ 200 | `frictionless-table` Table Schema（Frictionless；关键词「采集|清洗|质量|异常|缺失」命中） |
| `A02-08` | paper | https://arxiv.org/abs/2305.10355 | ✓ 200 | `w3c-svg2` SVG 2（W3C；域码 A02 专属绑定（轮换 0）） |
| `A02-09` | paper | https://arxiv.org/abs/1610.01465 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons；关键词「评测|基准|排行榜|跑分」命中） |
| `A02-10` | paper | https://arxiv.org/abs/1608.00272 | ✓ 200 | `w3c-svg2` SVG 2（W3C；关键词「图像|视觉|扩散|超分|抠图」命中） |
| `A02-11` | paper | https://arxiv.org/abs/2303.08774 | ✓ 200 | `mcp` Model Context Protocol（Anthropic/MCP；关键词「工具调用|智能体|工作流|Agent」命中） |
| `A02-12` | paper | https://arxiv.org/abs/2310.03744 | ✓ 200 | `w3c-svg2` SVG 2（W3C；域码 A02 专属绑定（轮换 0）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
