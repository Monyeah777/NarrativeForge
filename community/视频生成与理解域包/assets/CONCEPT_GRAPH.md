<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 视频生成与理解（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「视频生成与理解」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（视频生成与理解:M01）与收口模块（视频生成与理解:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 14 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A06-00 领域通用前置）；节点 26 · 边 40 · 密度 1.5385。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A06-01` | 文生视频 | P40 | — | a06-anchor |
| `A06-02` | 图生视频 | P60 | `A06-01` | a06-anchor |
| `A06-03` | 视频编辑与重绘 | P40 | `A06-02`、`A06-07` | a06-anchor |
| `A06-04` | 视频超分与修复 | P60 | `A06-03` | a06-anchor |
| `A06-05` | 镜头分割与关键帧 | P40 | — | a06-anchor |
| `A06-06` | 长视频时序一致性 | P60 | `A06-04`、`A06-05` | a06-anchor |
| `A06-07` | 动作可控生成 | P40 | — | a06-anchor |
| `A06-08` | 视频字幕与描述 | P60 | `A06-05` | a06-anchor |
| `A06-09` | 视频问答 | P40 | `A06-08` | a06-anchor |
| `A06-10` | 视频检索 | P60 | `A06-08` | a06-anchor |
| `A06-11` | 口型同步与数字人驱动 | P40 | — | a06-anchor |
| `A06-12` | 视频生成评测 | P60 | `A06-11` | a06-anchor |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-ixdtf` | 标准 · IXDTF (RFC 9557)（IETF｜data｜实测 ✓） | P80 | `A06-06`、`STD-rfc3339` | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A06-07`、`A06-01`、`A06-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `A06-04`、`A06-07`、`A06-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A06-05`、`A06-11`、`A06-12` | std-catalog |
| `STD-oci-image` | 标准 · 镜像清单（OCI｜iface｜实测 ✓） | P80 | `A06-01`、`A06-02`、`A06-03`、`A06-04`、`A06-08`、`A06-09`、`A06-10` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-rfc3339` | 标准 · 时间戳（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A06-02`、`A06-03`、`A06-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-owl-time` | 标准 · OWL-Time 时间本体（W3C｜data｜实测 ✓） | P80 | `A06-06`、`STD-w3c-owl2` | std-catalog |
| `STD-w3c-owl2` | 标准 · OWL 2 本体语言（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `A06-05`、`A06-10`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A06-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A06-文生视频` | `A06-01` |
| `A06-图生视频` | `A06-02` |
| `A06-视频编辑与重绘` | `A06-03` |
| `A06-视频超分与修复` | `A06-04` |
| `A06-镜头分割与关键帧` | `A06-05` |
| `A06-长视频时序一致性` | `A06-06` |
| `A06-动作可控生成` | `A06-07` |
| `A06-视频字幕与描述` | `A06-08` |
| `A06-视频问答` | `A06-09` |
| `A06-视频检索` | `A06-10` |
| `A06-口型同步与数字人驱动` | `A06-11` |
| `A06-视频生成评测` | `A06-12` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-ixdtf` | `STD-ietf-ixdtf` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-oci-image` | `STD-oci-image` |
| `std-rdf11` | `STD-rdf11` |
| `std-rfc3339` | `STD-rfc3339` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-owl-time` | `STD-w3c-owl-time` |
| `std-w3c-owl2` | `STD-w3c-owl2` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "视频生成与理解"
  code: "A06"
  provenance_strength: "external"
  provenance_legend:
    a06-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A06-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "视频生成与理解 全域"
      nodes:
        - "A06-01"
        - "A06-02"
        - "A06-03"
        - "A06-04"
        - "A06-05"
        - "A06-06"
        - "A06-07"
        - "A06-08"
        - "A06-09"
        - "A06-10"
        - "A06-11"
        - "A06-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-ietf-bcp47"
        - "STD-ietf-ixdtf"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-oci-image"
        - "STD-rdf11"
        - "STD-rfc3339"
        - "STD-vega-lite"
        - "STD-w3c-owl-time"
        - "STD-w3c-owl2"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "A06-01"
      name: "文生视频"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a06-anchor"
    - id: "A06-02"
      name: "图生视频"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-01"
      provenance:
        - "a06-anchor"
    - id: "A06-03"
      name: "视频编辑与重绘"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A06-02"
        - "A06-07"
      provenance:
        - "a06-anchor"
    - id: "A06-04"
      name: "视频超分与修复"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-03"
      provenance:
        - "a06-anchor"
    - id: "A06-05"
      name: "镜头分割与关键帧"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a06-anchor"
    - id: "A06-06"
      name: "长视频时序一致性"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-04"
        - "A06-05"
      provenance:
        - "a06-anchor"
    - id: "A06-07"
      name: "动作可控生成"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a06-anchor"
    - id: "A06-08"
      name: "视频字幕与描述"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-05"
      provenance:
        - "a06-anchor"
    - id: "A06-09"
      name: "视频问答"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A06-08"
      provenance:
        - "a06-anchor"
    - id: "A06-10"
      name: "视频检索"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-08"
      provenance:
        - "a06-anchor"
    - id: "A06-11"
      name: "口型同步与数字人驱动"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a06-anchor"
    - id: "A06-12"
      name: "视频生成评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-11"
      provenance:
        - "a06-anchor"
    - id: "STD-ietf-bcp47"
      name: "标准 · 语言标签 (RFC 5646)"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-ietf-ixdtf"
      name: "标准 · IXDTF (RFC 9557)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A06-06"
        - "STD-rfc3339"
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
        - "A06-07"
        - "A06-01"
        - "A06-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A06-04"
        - "A06-07"
        - "A06-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A06-05"
        - "A06-11"
        - "A06-12"
      provenance:
        - "std-catalog"
    - id: "STD-oci-image"
      name: "标准 · 镜像清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A06-01"
        - "A06-02"
        - "A06-03"
        - "A06-04"
        - "A06-08"
        - "A06-09"
        - "A06-10"
      provenance:
        - "std-catalog"
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-rfc3339"
      name: "标准 · 时间戳"
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
        - "A06-02"
        - "A06-03"
        - "A06-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-owl-time"
      name: "标准 · OWL-Time 时间本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A06-06"
        - "STD-w3c-owl2"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-owl2"
      name: "标准 · OWL 2 本体语言"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A06-05"
        - "A06-10"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A06-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A06-00）不随包交付，装载方须自备领域基础。
