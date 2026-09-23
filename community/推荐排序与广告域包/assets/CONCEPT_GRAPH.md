<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 推荐、排序与广告（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「推荐、排序与广告」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（推荐排序与广告:M01）与收口模块（推荐排序与广告:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 14 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（B17-00 领域通用前置）；节点 26 · 边 52 · 密度 2.0000。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B17-01` | 召回与粗排 | P40 | — | b17-anchor |
| `B17-02` | 精排模型 | P60 | `B17-01` | b17-anchor |
| `B17-03` | 冷启动 | P40 | `B17-02` | b17-anchor |
| `B17-04` | 特征工程 | P60 | `B17-03`、`B17-01` | b17-anchor |
| `B17-05` | 序列建模 | P40 | `B17-04`、`B17-02` | b17-anchor |
| `B17-06` | 多目标优化 | P60 | `B17-05`、`B17-03` | b17-anchor |
| `B17-07` | 探索与利用 | P40 | `B17-06`、`B17-04` | b17-anchor |
| `B17-08` | 广告创意生成 | P60 | `B17-07`、`B17-05` | b17-anchor |
| `B17-09` | 出价与预算 | P40 | `B17-08`、`B17-06` | b17-anchor |
| `B17-10` | 归因与增量 | P60 | `B17-09`、`B17-07` | b17-anchor |
| `B17-11` | 反作弊与流量质量 | P40 | `B17-10`、`B17-08` | b17-anchor |
| `B17-12` | 在线实验与评测 | P60 | `B17-11`、`B17-09` | b17-anchor |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `B17-11`、`STD-ietf-json-schema` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `B17-07`、`B17-09` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | `B17-01`、`STD-ietf-json-schema` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `B17-03`、`B17-06`、`B17-09`、`B17-11`、`STD-frictionless-package` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `B17-04`、`B17-07`、`B17-10`、`STD-ietf-json` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `B17-12` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `B17-02`、`STD-protobuf` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `B17-01`、`B17-03`、`B17-05`、`B17-06`、`B17-10`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `B17-04`、`B17-08`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `B17-05`、`B17-08`、`B17-02`、`B17-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B17-召回与粗排` | `B17-01` |
| `B17-精排模型` | `B17-02` |
| `B17-冷启动` | `B17-03` |
| `B17-特征工程` | `B17-04` |
| `B17-序列建模` | `B17-05` |
| `B17-多目标优化` | `B17-06` |
| `B17-探索与利用` | `B17-07` |
| `B17-广告创意生成` | `B17-08` |
| `B17-出价与预算` | `B17-09` |
| `B17-归因与增量` | `B17-10` |
| `B17-反作弊与流量质量` | `B17-11` |
| `B17-在线实验与评测` | `B17-12` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "推荐、排序与广告"
  code: "B17"
  provenance_strength: "external"
  provenance_legend:
    b17-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B17-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "推荐、排序与广告 全域"
      nodes:
        - "B17-01"
        - "B17-02"
        - "B17-03"
        - "B17-04"
        - "B17-05"
        - "B17-06"
        - "B17-07"
        - "B17-08"
        - "B17-09"
        - "B17-10"
        - "B17-11"
        - "B17-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-cloudevents"
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "B17-01"
      name: "召回与粗排"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b17-anchor"
    - id: "B17-02"
      name: "精排模型"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B17-01"
      provenance:
        - "b17-anchor"
    - id: "B17-03"
      name: "冷启动"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B17-02"
      provenance:
        - "b17-anchor"
    - id: "B17-04"
      name: "特征工程"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B17-03"
        - "B17-01"
      provenance:
        - "b17-anchor"
    - id: "B17-05"
      name: "序列建模"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B17-04"
        - "B17-02"
      provenance:
        - "b17-anchor"
    - id: "B17-06"
      name: "多目标优化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B17-05"
        - "B17-03"
      provenance:
        - "b17-anchor"
    - id: "B17-07"
      name: "探索与利用"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B17-06"
        - "B17-04"
      provenance:
        - "b17-anchor"
    - id: "B17-08"
      name: "广告创意生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B17-07"
        - "B17-05"
      provenance:
        - "b17-anchor"
    - id: "B17-09"
      name: "出价与预算"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B17-08"
        - "B17-06"
      provenance:
        - "b17-anchor"
    - id: "B17-10"
      name: "归因与增量"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B17-09"
        - "B17-07"
      provenance:
        - "b17-anchor"
    - id: "B17-11"
      name: "反作弊与流量质量"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B17-10"
        - "B17-08"
      provenance:
        - "b17-anchor"
    - id: "B17-12"
      name: "在线实验与评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B17-11"
        - "B17-09"
      provenance:
        - "b17-anchor"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B17-11"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B17-07"
        - "B17-09"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B17-01"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B17-03"
        - "B17-06"
        - "B17-09"
        - "B17-11"
        - "STD-frictionless-package"
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
        - "B17-04"
        - "B17-07"
        - "B17-10"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B17-12"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B17-02"
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
        - "B17-01"
        - "B17-03"
        - "B17-05"
        - "B17-06"
        - "B17-10"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B17-04"
        - "B17-08"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B17-05"
        - "B17-08"
        - "B17-02"
        - "B17-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B17-00）不随包交付，装载方须自备领域基础。
