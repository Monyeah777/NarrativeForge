<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 三维与世界模型（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「三维与世界模型」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（三维与世界模型:M01）与收口模块（三维与世界模型:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 12 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A08-00 领域通用前置）；节点 24 · 边 39 · 密度 1.6250。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A08-01` | 三维重建与辐射场 | P40 | — | a08-anchor |
| `A08-02` | 点云处理 | P60 | — | a08-anchor |
| `A08-03` | 纹理与材质生成 | P40 | `A08-01` | a08-anchor |
| `A08-04` | 文生 3D 资产 | P60 | `A08-01` | a08-anchor |
| `A08-05` | 场景生成与布局 | P40 | `A08-02`、`A08-04` | a08-anchor |
| `A08-06` | 物理仿真与碰撞 | P60 | `A08-05` | a08-anchor |
| `A08-07` | 世界模型与状态预测 | P40 | `A08-06` | a08-anchor |
| `A08-08` | SLAM 与定位 | P60 | `A08-02` | a08-anchor |
| `A08-09` | 数字孪生 | P40 | `A08-05` | a08-anchor |
| `A08-10` | 3D 资产格式与管线 | P60 | — | a08-anchor |
| `A08-11` | 骨骼绑定与动画 | P40 | `A08-10` | a08-anchor |
| `A08-12` | 三维评测 | P60 | `A08-07` | a08-anchor |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A08-04`、`A08-10`、`A08-06`、`A08-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `A08-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A08-05`、`A08-08`、`A08-11` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `A08-03`、`A08-06`、`A08-07`、`A08-09`、`STD-protobuf` | std-catalog |
| `STD-opengeospatial` | 标准 · OGC 标准（含 GeoJSON/3D Tiles）（OGC｜data｜实测 ✓） | P80 | `A08-01`、`A08-02`、`A08-12` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A08-01`、`A08-02`、`A08-03`、`A08-08`、`A08-10`、`A08-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `A08-04`、`A08-05`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A08-07`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A08-三维重建与辐射场` | `A08-01` |
| `A08-点云处理` | `A08-02` |
| `A08-纹理与材质生成` | `A08-03` |
| `A08-文生-3D-资产` | `A08-04` |
| `A08-场景生成与布局` | `A08-05` |
| `A08-物理仿真与碰撞` | `A08-06` |
| `A08-世界模型与状态预测` | `A08-07` |
| `A08-SLAM-与定位` | `A08-08` |
| `A08-数字孪生` | `A08-09` |
| `A08-3D-资产格式与管线` | `A08-10` |
| `A08-骨骼绑定与动画` | `A08-11` |
| `A08-三维评测` | `A08-12` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-opengeospatial` | `STD-opengeospatial` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "三维与世界模型"
  code: "A08"
  provenance_strength: "external"
  provenance_legend:
    a08-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A08-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "三维与世界模型 全域"
      nodes:
        - "A08-01"
        - "A08-02"
        - "A08-03"
        - "A08-04"
        - "A08-05"
        - "A08-06"
        - "A08-07"
        - "A08-08"
        - "A08-09"
        - "A08-10"
        - "A08-11"
        - "A08-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-opengeospatial"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "A08-01"
      name: "三维重建与辐射场"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a08-anchor"
    - id: "A08-02"
      name: "点云处理"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a08-anchor"
    - id: "A08-03"
      name: "纹理与材质生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A08-01"
      provenance:
        - "a08-anchor"
    - id: "A08-04"
      name: "文生 3D 资产"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A08-01"
      provenance:
        - "a08-anchor"
    - id: "A08-05"
      name: "场景生成与布局"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A08-02"
        - "A08-04"
      provenance:
        - "a08-anchor"
    - id: "A08-06"
      name: "物理仿真与碰撞"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A08-05"
      provenance:
        - "a08-anchor"
    - id: "A08-07"
      name: "世界模型与状态预测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A08-06"
      provenance:
        - "a08-anchor"
    - id: "A08-08"
      name: "SLAM 与定位"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A08-02"
      provenance:
        - "a08-anchor"
    - id: "A08-09"
      name: "数字孪生"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A08-05"
      provenance:
        - "a08-anchor"
    - id: "A08-10"
      name: "3D 资产格式与管线"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a08-anchor"
    - id: "A08-11"
      name: "骨骼绑定与动画"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A08-10"
      provenance:
        - "a08-anchor"
    - id: "A08-12"
      name: "三维评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A08-07"
      provenance:
        - "a08-anchor"
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
        - "A08-04"
        - "A08-10"
        - "A08-06"
        - "A08-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A08-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A08-05"
        - "A08-08"
        - "A08-11"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A08-03"
        - "A08-06"
        - "A08-07"
        - "A08-09"
        - "STD-protobuf"
      provenance:
        - "std-catalog"
    - id: "STD-opengeospatial"
      name: "标准 · OGC 标准（含 GeoJSON/3D Tiles）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A08-01"
        - "A08-02"
        - "A08-12"
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
        - "A08-01"
        - "A08-02"
        - "A08-03"
        - "A08-08"
        - "A08-10"
        - "A08-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A08-04"
        - "A08-05"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A08-07"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A08-00）不随包交付，装载方须自备领域基础。
