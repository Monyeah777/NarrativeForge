<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 建筑与房地产（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「建筑与房地产」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（建筑与房地产:M01）与收口模块（建筑与房地产:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 10 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（D15-00 领域通用前置）；节点 22 · 边 48 · 密度 2.1818。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D15-01` | 图纸审查 | P40 | — | d15-anchor |
| `D15-02` | 算量与造价 | P60 | `D15-01` | d15-anchor |
| `D15-03` | 施工进度识别 | P40 | `D15-02` | d15-anchor |
| `D15-04` | 危险作业检测 | P60 | `D15-03`、`D15-01` | d15-anchor |
| `D15-05` | 物业客服 | P40 | `D15-04`、`D15-02` | d15-anchor |
| `D15-06` | 房源描述生成 | P60 | `D15-05`、`D15-03` | d15-anchor |
| `D15-07` | 选房推荐 | P40 | `D15-06`、`D15-04` | d15-anchor |
| `D15-08` | 租赁合同审查 | P60 | `D15-07`、`D15-05` | d15-anchor |
| `D15-09` | 楼宇自控 | P40 | `D15-08`、`D15-06` | d15-anchor |
| `D15-10` | 工地巡检报告 | P60 | `D15-09`、`D15-07` | d15-anchor |
| `D15-11` | 建材选型 | P40 | `D15-10`、`D15-08` | d15-anchor |
| `D15-12` | 城市更新研究 | P60 | `D15-11`、`D15-09` | d15-anchor |
| `STD-common-criteria` | 标准 · Common Criteria（ISO 15408）（CCRA｜gov｜实测 ✓） | P80 | `D15-03`、`D15-06`、`D15-09`、`D15-12` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `D15-05`、`D15-06`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `D15-04`、`D15-09`、`D15-11` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST｜gov｜实测 ✓） | P80 | `D15-01`、`D15-04`、`D15-07`、`D15-10` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `D15-01`、`D15-02`、`D15-03`、`D15-07`、`D15-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `D15-02`、`D15-05`、`D15-08`、`D15-11`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `D15-08`、`D15-10`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D15-图纸审查` | `D15-01` |
| `D15-算量与造价` | `D15-02` |
| `D15-施工进度识别` | `D15-03` |
| `D15-危险作业检测` | `D15-04` |
| `D15-物业客服` | `D15-05` |
| `D15-房源描述生成` | `D15-06` |
| `D15-选房推荐` | `D15-07` |
| `D15-租赁合同审查` | `D15-08` |
| `D15-楼宇自控` | `D15-09` |
| `D15-工地巡检报告` | `D15-10` |
| `D15-建材选型` | `D15-11` |
| `D15-城市更新研究` | `D15-12` |
| `std-common-criteria` | `STD-common-criteria` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "建筑与房地产"
  code: "D15"
  provenance_strength: "external"
  provenance_legend:
    d15-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D15-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "建筑与房地产 全域"
      nodes:
        - "D15-01"
        - "D15-02"
        - "D15-03"
        - "D15-04"
        - "D15-05"
        - "D15-06"
        - "D15-07"
        - "D15-08"
        - "D15-09"
        - "D15-10"
        - "D15-11"
        - "D15-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-common-criteria"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-nist-ai-rmf"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "D15-01"
      name: "图纸审查"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d15-anchor"
    - id: "D15-02"
      name: "算量与造价"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D15-01"
      provenance:
        - "d15-anchor"
    - id: "D15-03"
      name: "施工进度识别"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D15-02"
      provenance:
        - "d15-anchor"
    - id: "D15-04"
      name: "危险作业检测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D15-03"
        - "D15-01"
      provenance:
        - "d15-anchor"
    - id: "D15-05"
      name: "物业客服"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D15-04"
        - "D15-02"
      provenance:
        - "d15-anchor"
    - id: "D15-06"
      name: "房源描述生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D15-05"
        - "D15-03"
      provenance:
        - "d15-anchor"
    - id: "D15-07"
      name: "选房推荐"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D15-06"
        - "D15-04"
      provenance:
        - "d15-anchor"
    - id: "D15-08"
      name: "租赁合同审查"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D15-07"
        - "D15-05"
      provenance:
        - "d15-anchor"
    - id: "D15-09"
      name: "楼宇自控"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D15-08"
        - "D15-06"
      provenance:
        - "d15-anchor"
    - id: "D15-10"
      name: "工地巡检报告"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D15-09"
        - "D15-07"
      provenance:
        - "d15-anchor"
    - id: "D15-11"
      name: "建材选型"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D15-10"
        - "D15-08"
      provenance:
        - "d15-anchor"
    - id: "D15-12"
      name: "城市更新研究"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D15-11"
        - "D15-09"
      provenance:
        - "d15-anchor"
    - id: "STD-common-criteria"
      name: "标准 · Common Criteria（ISO 15408）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D15-03"
        - "D15-06"
        - "D15-09"
        - "D15-12"
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
        - "D15-05"
        - "D15-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D15-04"
        - "D15-09"
        - "D15-11"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D15-01"
        - "D15-04"
        - "D15-07"
        - "D15-10"
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
        - "D15-01"
        - "D15-02"
        - "D15-03"
        - "D15-07"
        - "D15-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D15-02"
        - "D15-05"
        - "D15-08"
        - "D15-11"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D15-08"
        - "D15-10"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D15-00）不随包交付，装载方须自备领域基础。
