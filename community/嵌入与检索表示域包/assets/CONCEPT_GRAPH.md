<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 嵌入与检索表示（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「嵌入与检索表示」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（嵌入与检索表示:M01）与收口模块（嵌入与检索表示:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 11 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A11-00 领域通用前置）；节点 23 · 边 38 · 密度 1.6522。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A11-01` | 文本嵌入模型选型 | P40 | — | a11-anchor |
| `A11-02` | 稀疏与稠密混合检索 | P60 | `A11-05` | a11-anchor |
| `A11-03` | 重排序模型 | P40 | `A11-02` | a11-anchor |
| `A11-04` | 向量维度与压缩 | P60 | `A11-01` | a11-anchor |
| `A11-05` | 相似度度量与归一化 | P40 | `A11-01` | a11-anchor |
| `A11-06` | 多语言嵌入 | P60 | — | a11-anchor |
| `A11-07` | 领域嵌入微调 | P40 | `A11-06` | a11-anchor |
| `A11-08` | 多向量与后期交互 | P60 | — | a11-anchor |
| `A11-09` | 向量库选型 | P40 | `A11-04` | a11-anchor |
| `A11-10` | 召回评测 | P60 | `A11-03` | a11-anchor |
| `A11-11` | 语义去重 | P40 | `A11-02` | a11-anchor |
| `A11-12` | 嵌入漂移与版本 | P60 | `A11-07`、`A11-04` | a11-anchor |
| `STD-arrow` | 标准 · Arrow 列式格式（Apache｜data｜实测 ✓） | P80 | `A11-05`、`A11-11` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `A11-01` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | `A11-02`、`A11-04`、`A11-06`、`A11-07`、`A11-08`、`A11-09`、`A11-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `A11-04`、`A11-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A11-10` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `A11-01`、`A11-03`、`STD-protobuf` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A11-02`、`A11-03`、`A11-06`、`A11-07`、`A11-08`、`A11-11`、`A11-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `A11-05`、`A11-10`、`STD-rdf11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A11-文本嵌入模型选型` | `A11-01` |
| `A11-稀疏与稠密混合检索` | `A11-02` |
| `A11-重排序模型` | `A11-03` |
| `A11-向量维度与压缩` | `A11-04` |
| `A11-相似度度量与归一化` | `A11-05` |
| `A11-多语言嵌入` | `A11-06` |
| `A11-领域嵌入微调` | `A11-07` |
| `A11-多向量与后期交互` | `A11-08` |
| `A11-向量库选型` | `A11-09` |
| `A11-召回评测` | `A11-10` |
| `A11-语义去重` | `A11-11` |
| `A11-嵌入漂移与版本` | `A11-12` |
| `std-arrow` | `STD-arrow` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "嵌入与检索表示"
  code: "A11"
  provenance_strength: "external"
  provenance_legend:
    a11-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A11-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "嵌入与检索表示 全域"
      nodes:
        - "A11-01"
        - "A11-02"
        - "A11-03"
        - "A11-04"
        - "A11-05"
        - "A11-06"
        - "A11-07"
        - "A11-08"
        - "A11-09"
        - "A11-10"
        - "A11-11"
        - "A11-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-arrow"
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
  nodes:
    - id: "A11-01"
      name: "文本嵌入模型选型"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a11-anchor"
    - id: "A11-02"
      name: "稀疏与稠密混合检索"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A11-05"
      provenance:
        - "a11-anchor"
    - id: "A11-03"
      name: "重排序模型"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A11-02"
      provenance:
        - "a11-anchor"
    - id: "A11-04"
      name: "向量维度与压缩"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A11-01"
      provenance:
        - "a11-anchor"
    - id: "A11-05"
      name: "相似度度量与归一化"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A11-01"
      provenance:
        - "a11-anchor"
    - id: "A11-06"
      name: "多语言嵌入"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a11-anchor"
    - id: "A11-07"
      name: "领域嵌入微调"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A11-06"
      provenance:
        - "a11-anchor"
    - id: "A11-08"
      name: "多向量与后期交互"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a11-anchor"
    - id: "A11-09"
      name: "向量库选型"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A11-04"
      provenance:
        - "a11-anchor"
    - id: "A11-10"
      name: "召回评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A11-03"
      provenance:
        - "a11-anchor"
    - id: "A11-11"
      name: "语义去重"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A11-02"
      provenance:
        - "a11-anchor"
    - id: "A11-12"
      name: "嵌入漂移与版本"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A11-07"
        - "A11-04"
      provenance:
        - "a11-anchor"
    - id: "STD-arrow"
      name: "标准 · Arrow 列式格式"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A11-05"
        - "A11-11"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A11-01"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A11-02"
        - "A11-04"
        - "A11-06"
        - "A11-07"
        - "A11-08"
        - "A11-09"
        - "A11-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A11-04"
        - "A11-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A11-10"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A11-01"
        - "A11-03"
        - "STD-protobuf"
      provenance:
        - "std-catalog"
    - id: "STD-protobuf"
      name: "标准 · Protocol Buffers proto3"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A11-02"
        - "A11-03"
        - "A11-06"
        - "A11-07"
        - "A11-08"
        - "A11-11"
        - "A11-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A11-05"
        - "A11-10"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A11-00）不随包交付，装载方须自备领域基础。
