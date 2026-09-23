<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+农业（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+农业」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI农业:M01）与收口模块（AI农业:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 17 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（D10-00 领域通用前置）；节点 29 · 边 50 · 密度 1.7241。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D10-01` | 作物病虫害识别 | P40 | — | d10-anchor |
| `D10-02` | 农事作业建议 | P60 | `D10-01` | d10-anchor |
| `D10-03` | 气象与灾害预警 | P40 | `D10-02` | d10-anchor |
| `D10-04` | 土壤与施肥决策 | P60 | `D10-03`、`D10-01` | d10-anchor |
| `D10-05` | 农产品分级 | P40 | `D10-04`、`D10-02` | d10-anchor |
| `D10-06` | 养殖管理助手 | P60 | `D10-05`、`D10-03` | d10-anchor |
| `D10-07` | 农机作业调度 | P40 | `D10-06`、`D10-04` | d10-anchor |
| `D10-08` | 农业政策问答 | P60 | `D10-07`、`D10-05` | d10-anchor |
| `D10-09` | 溯源与品牌 | P40 | `D10-08`、`D10-06` | d10-anchor |
| `D10-10` | 农业知识科普 | P60 | `D10-09`、`D10-07` | d10-anchor |
| `D10-11` | 遥感长势监测 | P40 | `D10-10`、`D10-08` | d10-anchor |
| `D10-12` | 农资合规 | P60 | `D10-11`、`D10-09` | d10-anchor |
| `STD-c2pa-spec` | 标准 · 内容凭证规范（C2PA｜gov｜实测 ✓） | P80 | `D10-09`、`STD-cbor`、`STD-cose` | std-catalog |
| `STD-cbor` | 标准 · CBOR (RFC 8949)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-common-criteria` | 标准 · Common Criteria（ISO 15408）（CCRA｜gov｜实测 ✓） | P80 | `D10-03` | std-catalog |
| `STD-cose` | 标准 · COSE 签名与加密（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-fao-food` | 标准 · 食品安全与质量（FAO｜gov｜实测 ✓） | P80 | `D10-06`、`D10-10` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU｜gov｜实测 ✓） | P80 | `D10-12` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `D10-01`、`D10-05`、`D10-06`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `D10-04` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST｜gov｜实测 ✓） | P80 | `D10-01`、`D10-04`、`D10-07` | std-catalog |
| `STD-oecd-ai` | 标准 · OECD AI 原则（OECD｜gov｜实测 ✓） | P80 | `D10-08` | std-catalog |
| `STD-opengeospatial` | 标准 · OGC 标准（含 GeoJSON/3D Tiles）（OGC｜data｜实测 ✓） | P80 | `D10-11` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `D10-02`、`D10-03`、`D10-07`、`D10-08`、`D10-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `D10-02`、`D10-05`、`D10-09`、`D10-11`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `D10-10`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D10-作物病虫害识别` | `D10-01` |
| `D10-农事作业建议` | `D10-02` |
| `D10-气象与灾害预警` | `D10-03` |
| `D10-土壤与施肥决策` | `D10-04` |
| `D10-农产品分级` | `D10-05` |
| `D10-养殖管理助手` | `D10-06` |
| `D10-农机作业调度` | `D10-07` |
| `D10-农业政策问答` | `D10-08` |
| `D10-溯源与品牌` | `D10-09` |
| `D10-农业知识科普` | `D10-10` |
| `D10-遥感长势监测` | `D10-11` |
| `D10-农资合规` | `D10-12` |
| `std-c2pa-spec` | `STD-c2pa-spec` |
| `std-cbor` | `STD-cbor` |
| `std-common-criteria` | `STD-common-criteria` |
| `std-cose` | `STD-cose` |
| `std-fao-food` | `STD-fao-food` |
| `std-gdpr` | `STD-gdpr` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-oecd-ai` | `STD-oecd-ai` |
| `std-opengeospatial` | `STD-opengeospatial` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+农业"
  code: "D10"
  provenance_strength: "external"
  provenance_legend:
    d10-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D10-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+农业 全域"
      nodes:
        - "D10-01"
        - "D10-02"
        - "D10-03"
        - "D10-04"
        - "D10-05"
        - "D10-06"
        - "D10-07"
        - "D10-08"
        - "D10-09"
        - "D10-10"
        - "D10-11"
        - "D10-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-c2pa-spec"
        - "STD-cbor"
        - "STD-common-criteria"
        - "STD-cose"
        - "STD-fao-food"
        - "STD-gdpr"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-nist-ai-rmf"
        - "STD-oecd-ai"
        - "STD-opengeospatial"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "D10-01"
      name: "作物病虫害识别"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d10-anchor"
    - id: "D10-02"
      name: "农事作业建议"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D10-01"
      provenance:
        - "d10-anchor"
    - id: "D10-03"
      name: "气象与灾害预警"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D10-02"
      provenance:
        - "d10-anchor"
    - id: "D10-04"
      name: "土壤与施肥决策"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D10-03"
        - "D10-01"
      provenance:
        - "d10-anchor"
    - id: "D10-05"
      name: "农产品分级"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D10-04"
        - "D10-02"
      provenance:
        - "d10-anchor"
    - id: "D10-06"
      name: "养殖管理助手"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D10-05"
        - "D10-03"
      provenance:
        - "d10-anchor"
    - id: "D10-07"
      name: "农机作业调度"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D10-06"
        - "D10-04"
      provenance:
        - "d10-anchor"
    - id: "D10-08"
      name: "农业政策问答"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D10-07"
        - "D10-05"
      provenance:
        - "d10-anchor"
    - id: "D10-09"
      name: "溯源与品牌"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D10-08"
        - "D10-06"
      provenance:
        - "d10-anchor"
    - id: "D10-10"
      name: "农业知识科普"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D10-09"
        - "D10-07"
      provenance:
        - "d10-anchor"
    - id: "D10-11"
      name: "遥感长势监测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D10-10"
        - "D10-08"
      provenance:
        - "d10-anchor"
    - id: "D10-12"
      name: "农资合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D10-11"
        - "D10-09"
      provenance:
        - "d10-anchor"
    - id: "STD-c2pa-spec"
      name: "标准 · 内容凭证规范"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D10-09"
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
    - id: "STD-common-criteria"
      name: "标准 · Common Criteria（ISO 15408）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D10-03"
      provenance:
        - "std-catalog"
    - id: "STD-cose"
      name: "标准 · COSE 签名与加密"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-fao-food"
      name: "标准 · 食品安全与质量"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D10-06"
        - "D10-10"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D10-12"
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
        - "D10-01"
        - "D10-05"
        - "D10-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D10-04"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D10-01"
        - "D10-04"
        - "D10-07"
      provenance:
        - "std-catalog"
    - id: "STD-oecd-ai"
      name: "标准 · OECD AI 原则"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D10-08"
      provenance:
        - "std-catalog"
    - id: "STD-opengeospatial"
      name: "标准 · OGC 标准（含 GeoJSON/3D Tiles）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D10-11"
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
        - "D10-02"
        - "D10-03"
        - "D10-07"
        - "D10-08"
        - "D10-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D10-02"
        - "D10-05"
        - "D10-09"
        - "D10-11"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D10-10"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D10-00）不随包交付，装载方须自备领域基础。
