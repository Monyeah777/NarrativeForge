<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 图像生成与编辑（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「图像生成与编辑」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（图像生成与编辑:M01）与收口模块（图像生成与编辑:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 18 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A07-00 领域通用前置）；节点 30 · 边 43 · 密度 1.4333。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A07-01` | 扩散模型与采样器 | P40 | — | a07-anchor |
| `A07-02` | 流匹配与整流流 | P60 | `A07-01` | a07-anchor |
| `A07-03` | 结构条件控制 | P40 | `A07-01` | a07-anchor |
| `A07-04` | 图像修复与扩图 | P60 | `A07-03` | a07-anchor |
| `A07-05` | 风格化与风格迁移 | P40 | `A07-03` | a07-anchor |
| `A07-06` | 超分与画质增强 | P60 | `A07-04` | a07-anchor |
| `A07-07` | 背景替换与抠图 | P40 | `A07-03` | a07-anchor |
| `A07-08` | 人像美化与换脸边界 | P60 | `A07-07` | a07-anchor |
| `A07-09` | LoRA 与个性化微调 | P40 | — | a07-anchor |
| `A07-10` | 提示词与美学控制 | P60 | `A07-09` | a07-anchor |
| `A07-11` | 生成水印与溯源 | P40 | — | a07-anchor |
| `A07-12` | 生成质量评测 | P60 | `A07-10`、`A07-11` | a07-anchor |
| `STD-c2pa-spec` | 标准 · 内容凭证规范（C2PA｜gov｜实测 ✓） | P80 | `A07-11`、`STD-cbor`、`STD-cose` | std-catalog |
| `STD-cbor` | 标准 · CBOR (RFC 8949)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `A07-02`、`STD-ietf-json-schema` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `A07-10` | std-catalog |
| `STD-cose` | 标准 · COSE 签名与加密（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A07-01`、`A07-06`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `A07-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A07-02`、`A07-05`、`A07-08`、`A07-09`、`A07-12` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `A07-01`、`A07-03`、`STD-protobuf` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A07-03`、`A07-04`、`A07-07`、`A07-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `A07-05`、`A07-10`、`A07-11`、`STD-rdf11` | std-catalog |
| `STD-w3c-svg2` | 标准 · SVG 2（W3C｜form｜实测 ✓） | P80 | `A07-04`、`A07-06`、`A07-07`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A07-12`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A07-扩散模型与采样器` | `A07-01` |
| `A07-流匹配与整流流` | `A07-02` |
| `A07-结构条件控制` | `A07-03` |
| `A07-图像修复与扩图` | `A07-04` |
| `A07-风格化与风格迁移` | `A07-05` |
| `A07-超分与画质增强` | `A07-06` |
| `A07-背景替换与抠图` | `A07-07` |
| `A07-人像美化与换脸边界` | `A07-08` |
| `A07-LoRA-与个性化微调` | `A07-09` |
| `A07-提示词与美学控制` | `A07-10` |
| `A07-生成水印与溯源` | `A07-11` |
| `A07-生成质量评测` | `A07-12` |
| `std-c2pa-spec` | `STD-c2pa-spec` |
| `std-cbor` | `STD-cbor` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-commonmark` | `STD-commonmark` |
| `std-cose` | `STD-cose` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-svg2` | `STD-w3c-svg2` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "图像生成与编辑"
  code: "A07"
  provenance_strength: "external"
  provenance_legend:
    a07-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A07-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "图像生成与编辑 全域"
      nodes:
        - "A07-01"
        - "A07-02"
        - "A07-03"
        - "A07-04"
        - "A07-05"
        - "A07-06"
        - "A07-07"
        - "A07-08"
        - "A07-09"
        - "A07-10"
        - "A07-11"
        - "A07-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-c2pa-spec"
        - "STD-cbor"
        - "STD-cncf-cloudevents"
        - "STD-commonmark"
        - "STD-cose"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-svg2"
        - "STD-w3c-tabular-data"
        - "STD-w3c-xml"
  nodes:
    - id: "A07-01"
      name: "扩散模型与采样器"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a07-anchor"
    - id: "A07-02"
      name: "流匹配与整流流"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A07-01"
      provenance:
        - "a07-anchor"
    - id: "A07-03"
      name: "结构条件控制"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A07-01"
      provenance:
        - "a07-anchor"
    - id: "A07-04"
      name: "图像修复与扩图"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A07-03"
      provenance:
        - "a07-anchor"
    - id: "A07-05"
      name: "风格化与风格迁移"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A07-03"
      provenance:
        - "a07-anchor"
    - id: "A07-06"
      name: "超分与画质增强"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A07-04"
      provenance:
        - "a07-anchor"
    - id: "A07-07"
      name: "背景替换与抠图"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A07-03"
      provenance:
        - "a07-anchor"
    - id: "A07-08"
      name: "人像美化与换脸边界"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A07-07"
      provenance:
        - "a07-anchor"
    - id: "A07-09"
      name: "LoRA 与个性化微调"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a07-anchor"
    - id: "A07-10"
      name: "提示词与美学控制"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A07-09"
      provenance:
        - "a07-anchor"
    - id: "A07-11"
      name: "生成水印与溯源"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a07-anchor"
    - id: "A07-12"
      name: "生成质量评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A07-10"
        - "A07-11"
      provenance:
        - "a07-anchor"
    - id: "STD-c2pa-spec"
      name: "标准 · 内容凭证规范"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A07-11"
        - "STD-cbor"
        - "STD-cose"
      provenance:
        - "std-catalog"
    - id: "STD-cbor"
      name: "标准 · CBOR (RFC 8949)"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A07-02"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A07-10"
      provenance:
        - "std-catalog"
    - id: "STD-cose"
      name: "标准 · COSE 签名与加密"
      layer: "P80"
      branch: "standards"
      prereqs: []
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
        - "A07-01"
        - "A07-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A07-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A07-02"
        - "A07-05"
        - "A07-08"
        - "A07-09"
        - "A07-12"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A07-01"
        - "A07-03"
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
        - "A07-03"
        - "A07-04"
        - "A07-07"
        - "A07-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A07-05"
        - "A07-10"
        - "A07-11"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-svg2"
      name: "标准 · SVG 2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A07-04"
        - "A07-06"
        - "A07-07"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A07-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-xml"
      name: "标准 · XML 1.0"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A07-00）不随包交付，装载方须自备领域基础。
