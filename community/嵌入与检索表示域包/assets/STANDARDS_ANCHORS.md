<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 嵌入与检索表示

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜细分锚实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）｜标准锚实测日期见下表「标准锚」列（取自 `protocol/standards_catalog.json` 的本机探针记录）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|
| `A11-01` | paper | https://arxiv.org/abs/2212.03533 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation｜iface｜✓ 2026-09-24；关键词「模型|推理|量化」命中） | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；载体锚：产出形态「文本」的承载标准） |
| `A11-02` | paper | https://arxiv.org/abs/2210.11934 | ✓ 200 | `frictionless-package` Data Package（Frictionless｜data｜✓ 2026-09-24；关键词「检索|向量|嵌入|召回」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |
| `A11-03` | paper | https://arxiv.org/abs/1908.10084 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation｜iface｜✓ 2026-09-24；关键词「模型|推理|量化」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |
| `A11-04` | paper | https://arxiv.org/abs/1702.08734 | ✓ 200 | `frictionless-package` Data Package（Frictionless｜data｜✓ 2026-09-24；关键词「检索|向量|嵌入|召回」命中） | `mermaid` Mermaid 图语言（Mermaid｜form｜✓ 2026-09-24；A 段载体锚（轮换 3；与主锚异层）） |
| `A11-05` | doc | https://scikit-learn.org/stable/modules/metrics.html | ✓ 200 | `arrow` Arrow 列式格式（Apache｜data｜✓ 2026-09-24；域码 A11 专属绑定（轮换 0）） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；A 段载体锚（轮换 4；与主锚异层）） |
| `A11-06` | paper | https://arxiv.org/abs/2004.09813 | ✓ 200 | `frictionless-package` Data Package（Frictionless｜data｜✓ 2026-09-24；关键词「检索|向量|嵌入|召回」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |
| `A11-07` | paper | https://arxiv.org/abs/2112.07899 | ✓ 200 | `frictionless-package` Data Package（Frictionless｜data｜✓ 2026-09-24；关键词「检索|向量|嵌入|召回」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |
| `A11-08` | paper | https://arxiv.org/abs/2112.01488 | ✓ 200 | `frictionless-package` Data Package（Frictionless｜data｜✓ 2026-09-24；关键词「检索|向量|嵌入|召回」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |
| `A11-09` | paper | https://arxiv.org/abs/1603.09320 | ✓ 200 | `frictionless-package` Data Package（Frictionless｜data｜✓ 2026-09-24；关键词「检索|向量|嵌入|召回」命中） | `mermaid` Mermaid 图语言（Mermaid｜form｜✓ 2026-09-24；A 段载体锚（轮换 3；与主锚异层）） |
| `A11-10` | paper | https://arxiv.org/abs/2104.08663 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons｜eng｜✓ 2026-09-24；关键词「评测|基准|排行榜|跑分」命中） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；A 段载体锚（轮换 4；与主锚异层）） |
| `A11-11` | paper | https://arxiv.org/abs/2107.06499 | ✓ 200 | `arrow` Arrow 列式格式（Apache｜data｜✓ 2026-09-24；域码 A11 专属绑定（轮换 0）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |
| `A11-12` | paper | https://arxiv.org/abs/2210.07316 | ✓ 200 | `frictionless-package` Data Package（Frictionless｜data｜✓ 2026-09-24；关键词「检索|向量|嵌入|召回」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- **双锚分工**：主锚 = 该细分依据的域口径标准（可能与细分锚不同源，形成第二证据链）；辅锚 = 该细分产出（数据 / 契约 / 图表 / 图示 / 溯源）所承载的开放标准。
- 标准锚取自 `protocol/standards_catalog.json` 的**本机实测记录**（含取样标题与 sha256），可达性 false 如实标注，不假装可达。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
