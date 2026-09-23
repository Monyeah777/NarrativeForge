<!-- nf-asset: key="STANDARDS_ANCHORS" version="1.0" status="active" -->
# 权威锚表 · 图像生成与编辑

> 用途：本域 12 条细分各自的**外部权威锚**（规范 / 论文 / 参考实现）与**可达性实证**。外部锚只作口径与机制参照，**不作品质背书**（STRATEGY §3.2/§3.3）。
> 资产键：`STANDARDS_ANCHORS`｜细分锚实测日期：2026-09-22（本机 GET，HTTP 状态见下表；不可达如实记 `✗`，不假装可达）｜标准锚实测日期见下表「标准锚」列（取自 `protocol/standards_catalog.json` 的本机探针记录）。

## 1. 锚表

| 条目键 | 锚类型 | URL | 可达性 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|
| `A07-01` | paper | https://arxiv.org/abs/2006.11239 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation｜iface｜✓ 2026-09-24；关键词「模型|推理|量化」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；A 段载体锚（轮换 0；与主锚异层）） |
| `A07-02` | paper | https://arxiv.org/abs/2210.02747 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons｜eng｜✓ 2026-09-24；A 段默认绑定（轮换 1）） | `cncf-cloudevents` CloudEvents 1.0（CNCF｜iface｜✓ 2026-09-24；载体锚：产出形态「事件」的承载标准） |
| `A07-03` | paper | https://arxiv.org/abs/2302.05543 | ✓ 200 | `onnx` ONNX（opset 扩展）（Linux Foundation｜iface｜✓ 2026-09-24；A 段默认绑定（轮换 2）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |
| `A07-04` | paper | https://arxiv.org/abs/2109.07161 | ✓ 200 | `w3c-svg2` SVG 2（W3C｜form｜✓ 2026-09-24；关键词「图像|视觉|扩散|超分|抠图」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；载体锚：产出形态「图」的承载标准） |
| `A07-05` | paper | https://arxiv.org/abs/1703.06868 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons｜eng｜✓ 2026-09-24；A 段默认绑定（轮换 1）） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；A 段载体锚（轮换 4；与主锚异层）） |
| `A07-06` | paper | https://arxiv.org/abs/2107.10833 | ✓ 200 | `w3c-svg2` SVG 2（W3C｜form｜✓ 2026-09-24；关键词「图像|视觉|扩散|超分|抠图」命中） | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema｜data｜✓ 2026-09-24；A 段载体锚（轮换 0；与主锚异层）） |
| `A07-07` | paper | https://arxiv.org/abs/2011.11961 | ✓ 200 | `w3c-svg2` SVG 2（W3C｜form｜✓ 2026-09-24；关键词「图像|视觉|扩散|超分|抠图」命中） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；载体锚：产出形态「图」的承载标准） |
| `A07-08` | paper | https://arxiv.org/abs/1901.08971 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons｜eng｜✓ 2026-09-24；A 段默认绑定（轮换 1）） | `vega-lite` Vega-Lite v5（Vega｜form｜✓ 2026-09-24；A 段载体锚（轮换 2；与主锚异层）） |
| `A07-09` | paper | https://arxiv.org/abs/2106.09685 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons｜eng｜✓ 2026-09-24；关键词「训练|微调|对齐|蒸馏|偏好」命中） | `mermaid` Mermaid 图语言（Mermaid｜form｜✓ 2026-09-24；A 段载体锚（轮换 3；与主锚异层）） |
| `A07-10` | paper | https://arxiv.org/abs/2207.12598 | ✓ 200 | `commonmark` CommonMark 0.31.2（CommonMark｜form｜✓ 2026-09-24；关键词「提示|指令|模板」命中） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；A 段载体锚（轮换 4；与主锚异层）） |
| `A07-11` | spec | https://c2pa.org/specifications/specifications/1.3/index.html | ✓ 200 | `c2pa-spec` 内容凭证规范（C2PA｜gov｜✓ 2026-09-24；关键词「水印|溯源|凭证|内容来源」命中） | `w3c-prov-o` PROV-O 溯源本体（W3C｜gov｜✓ 2026-09-24；载体锚：产出形态「溯源」的承载标准） |
| `A07-12` | paper | https://arxiv.org/abs/1706.08500 | ✓ 200 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons｜eng｜✓ 2026-09-24；关键词「评测|基准|排行榜|跑分」命中） | `w3c-tabular-data` Tabular Data Model (CSVW)（W3C｜data｜✓ 2026-09-24；A 段载体锚（轮换 1；与主锚异层）） |

## 2. 使用边界

- 锚用于**口径复核**（该细分的通行定义/评测口径从何而来），不表示 NF 复制了外部文本；本包正文自撰。
- **双锚分工**：主锚 = 该细分依据的域口径标准（可能与细分锚不同源，形成第二证据链）；辅锚 = 该细分产出（数据 / 契约 / 图表 / 图示 / 溯源）所承载的开放标准。
- 标准锚取自 `protocol/standards_catalog.json` 的**本机实测记录**（含取样标题与 sha256），可达性 false 如实标注，不假装可达。
- 锚不可达时按不可达记档，不影响本包口径面的机检（判据落在本包 schema 与度量族）。
- 锚版本漂移（规范改版）由维护者按需复核；本表不做自动追踪。
