<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 大语言模型（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「大语言模型」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（大语言模型:M01）与收口模块（大语言模型:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 15 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A01-00 领域通用前置）；节点 27 · 边 40 · 密度 1.4815。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A01-01` | 基座模型选型与对比 | P40 | — | a01-anchor |
| `A01-02` | 模型规模与架构 | P60 | `A01-01` | a01-anchor |
| `A01-03` | 分词器与词表 | P40 | — | a01-anchor |
| `A01-04` | 训练数据配比与质检 | P60 | — | a01-anchor |
| `A01-05` | 上下文窗口与位置编码 | P40 | `A01-03`、`A01-02`、`A01-06` | a01-anchor |
| `A01-06` | 注意力机制变体 | P60 | — | a01-anchor |
| `A01-07` | 模型能力边界与失效模式 | P40 | — | a01-anchor |
| `A01-08` | 开源与闭源许可条款 | P60 | `A01-01` | a01-anchor |
| `A01-09` | 蒸馏与师生训练 | P40 | `A01-04` | a01-anchor |
| `A01-10` | 模型合并与权重插值 | P60 | `A01-07`、`A01-09` | a01-anchor |
| `A01-11` | 量化格式与权重存储 | P40 | `A01-02` | a01-anchor |
| `A01-12` | 推理参数与采样策略 | P60 | `A01-06` | a01-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | — | std-catalog |
| `STD-creativecommons` | 标准 · 许可与权利表达（Creative Commons｜gov｜实测 ✓） | P80 | `A01-08` | std-catalog |
| `STD-gfm` | 标准 · GFM 扩展（GitHub｜form｜实测 ✓） | P80 | `A01-05`、`STD-commonmark` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A01-01`、`A01-06`、`A01-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `A01-04`、`A01-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A01-04`、`A01-06`、`A01-09` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `A01-01`、`A01-02`、`A01-07`、`A01-10`、`A01-11`、`A01-12`、`STD-protobuf` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX｜gov｜实测 ✓） | P80 | `A01-08` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `A01-05`、`A01-10`、`STD-rdf11` | std-catalog |
| `STD-w3c-skos` | 标准 · SKOS 词表（W3C｜data｜实测 ✓） | P80 | `A01-03`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A01-02`、`A01-03`、`A01-07`、`A01-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A01-基座模型选型与对比` | `A01-01` |
| `A01-模型规模与架构` | `A01-02` |
| `A01-分词器与词表` | `A01-03` |
| `A01-训练数据配比与质检` | `A01-04` |
| `A01-上下文窗口与位置编码` | `A01-05` |
| `A01-注意力机制变体` | `A01-06` |
| `A01-模型能力边界与失效模式` | `A01-07` |
| `A01-开源与闭源许可条款` | `A01-08` |
| `A01-蒸馏与师生训练` | `A01-09` |
| `A01-模型合并与权重插值` | `A01-10` |
| `A01-量化格式与权重存储` | `A01-11` |
| `A01-推理参数与采样策略` | `A01-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-creativecommons` | `STD-creativecommons` |
| `std-gfm` | `STD-gfm` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-skos` | `STD-w3c-skos` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "大语言模型"
  code: "A01"
  provenance_strength: "external"
  provenance_legend:
    a01-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A01-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "大语言模型 全域"
      nodes:
        - "A01-01"
        - "A01-02"
        - "A01-03"
        - "A01-04"
        - "A01-05"
        - "A01-06"
        - "A01-07"
        - "A01-08"
        - "A01-09"
        - "A01-10"
        - "A01-11"
        - "A01-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-creativecommons"
        - "STD-gfm"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-spdx-licenses"
        - "STD-w3c-prov-o"
        - "STD-w3c-skos"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "A01-01"
      name: "基座模型选型与对比"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a01-anchor"
    - id: "A01-02"
      name: "模型规模与架构"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A01-01"
      provenance:
        - "a01-anchor"
    - id: "A01-03"
      name: "分词器与词表"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a01-anchor"
    - id: "A01-04"
      name: "训练数据配比与质检"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a01-anchor"
    - id: "A01-05"
      name: "上下文窗口与位置编码"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A01-03"
        - "A01-02"
        - "A01-06"
      provenance:
        - "a01-anchor"
    - id: "A01-06"
      name: "注意力机制变体"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a01-anchor"
    - id: "A01-07"
      name: "模型能力边界与失效模式"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a01-anchor"
    - id: "A01-08"
      name: "开源与闭源许可条款"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A01-01"
      provenance:
        - "a01-anchor"
    - id: "A01-09"
      name: "蒸馏与师生训练"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A01-04"
      provenance:
        - "a01-anchor"
    - id: "A01-10"
      name: "模型合并与权重插值"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A01-07"
        - "A01-09"
      provenance:
        - "a01-anchor"
    - id: "A01-11"
      name: "量化格式与权重存储"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A01-02"
      provenance:
        - "a01-anchor"
    - id: "A01-12"
      name: "推理参数与采样策略"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A01-06"
      provenance:
        - "a01-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-creativecommons"
      name: "标准 · 许可与权利表达"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A01-08"
      provenance:
        - "std-catalog"
    - id: "STD-gfm"
      name: "标准 · GFM 扩展"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A01-05"
        - "STD-commonmark"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-bcp47"
      name: "标准 · 语言标签 (RFC 5646)"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json"
      name: "标准 · JSON (RFC 8259)"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A01-01"
        - "A01-06"
        - "A01-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A01-04"
        - "A01-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A01-04"
        - "A01-06"
        - "A01-09"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A01-01"
        - "A01-02"
        - "A01-07"
        - "A01-10"
        - "A01-11"
        - "A01-12"
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
    - id: "STD-spdx-licenses"
      name: "标准 · SPDX 许可证清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A01-08"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A01-05"
        - "A01-10"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-skos"
      name: "标准 · SKOS 词表"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A01-03"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A01-02"
        - "A01-03"
        - "A01-07"
        - "A01-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A01-00）不随包交付，装载方须自备领域基础。
