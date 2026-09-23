<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+医疗健康（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+医疗健康」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI医疗健康:M01）与收口模块（AI医疗健康:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 13 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（D01-00 领域通用前置）；节点 25 · 边 49 · 密度 1.9600。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D01-01` | 临床辅助决策 | P40 | — | d01-anchor |
| `D01-02` | 病历结构化与质控 | P60 | `D01-01` | d01-anchor |
| `D01-03` | 医学影像辅助诊断 | P40 | `D01-02` | d01-anchor |
| `D01-04` | 医学术语与编码 | P60 | `D01-03`、`D01-01` | d01-anchor |
| `D01-05` | 门诊问诊助手 | P40 | `D01-04`、`D01-02` | d01-anchor |
| `D01-06` | 随访与慢病管理 | P60 | `D01-05`、`D01-03` | d01-anchor |
| `D01-07` | 患者教育材料 | P40 | `D01-06`、`D01-04` | d01-anchor |
| `D01-08` | 医疗文书撰写 | P60 | `D01-07`、`D01-05` | d01-anchor |
| `D01-09` | 医学文献综述 | P40 | `D01-08`、`D01-06` | d01-anchor |
| `D01-10` | 医疗问答科普 | P60 | `D01-09`、`D01-07` | d01-anchor |
| `D01-11` | 合规与免责边界 | P40 | `D01-10`、`D01-08` | d01-anchor |
| `D01-12` | 医疗数据隐私 | P60 | `D01-11`、`D01-09` | d01-anchor |
| `STD-dicom` | 标准 · DICOM 标准（DICOM｜data｜实测 ✓） | P80 | `D01-06` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU｜gov｜实测 ✓） | P80 | `D01-11`、`D01-12` | std-catalog |
| `STD-hl7-fhir` | 标准 · FHIR（资源扩展机制）（HL7｜iface｜实测 ✓） | P80 | `D01-01`、`D01-02`、`D01-03`、`D01-05`、`D01-08`、`D01-09`、`D01-10` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `D01-01`、`D01-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `D01-04`、`D01-09` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-unesco-ai` | 标准 · AI 伦理建议书（UNESCO｜gov｜实测 ✓） | P80 | `D01-07` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `D01-03`、`D01-07`、`D01-08`、`D01-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `D01-02`、`D01-06`、`STD-rdf11` | std-catalog |
| `STD-w3c-skos` | 标准 · SKOS 词表（W3C｜data｜实测 ✓） | P80 | `D01-04`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `D01-05`、`D01-10`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D01-临床辅助决策` | `D01-01` |
| `D01-病历结构化与质控` | `D01-02` |
| `D01-医学影像辅助诊断` | `D01-03` |
| `D01-医学术语与编码` | `D01-04` |
| `D01-门诊问诊助手` | `D01-05` |
| `D01-随访与慢病管理` | `D01-06` |
| `D01-患者教育材料` | `D01-07` |
| `D01-医疗文书撰写` | `D01-08` |
| `D01-医学文献综述` | `D01-09` |
| `D01-医疗问答科普` | `D01-10` |
| `D01-合规与免责边界` | `D01-11` |
| `D01-医疗数据隐私` | `D01-12` |
| `std-dicom` | `STD-dicom` |
| `std-gdpr` | `STD-gdpr` |
| `std-hl7-fhir` | `STD-hl7-fhir` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-rdf11` | `STD-rdf11` |
| `std-unesco-ai` | `STD-unesco-ai` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-skos` | `STD-w3c-skos` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+医疗健康"
  code: "D01"
  provenance_strength: "external"
  provenance_legend:
    d01-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D01-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+医疗健康 全域"
      nodes:
        - "D01-01"
        - "D01-02"
        - "D01-03"
        - "D01-04"
        - "D01-05"
        - "D01-06"
        - "D01-07"
        - "D01-08"
        - "D01-09"
        - "D01-10"
        - "D01-11"
        - "D01-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-dicom"
        - "STD-gdpr"
        - "STD-hl7-fhir"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-rdf11"
        - "STD-unesco-ai"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-skos"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "D01-01"
      name: "临床辅助决策"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d01-anchor"
    - id: "D01-02"
      name: "病历结构化与质控"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D01-01"
      provenance:
        - "d01-anchor"
    - id: "D01-03"
      name: "医学影像辅助诊断"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D01-02"
      provenance:
        - "d01-anchor"
    - id: "D01-04"
      name: "医学术语与编码"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D01-03"
        - "D01-01"
      provenance:
        - "d01-anchor"
    - id: "D01-05"
      name: "门诊问诊助手"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D01-04"
        - "D01-02"
      provenance:
        - "d01-anchor"
    - id: "D01-06"
      name: "随访与慢病管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D01-05"
        - "D01-03"
      provenance:
        - "d01-anchor"
    - id: "D01-07"
      name: "患者教育材料"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D01-06"
        - "D01-04"
      provenance:
        - "d01-anchor"
    - id: "D01-08"
      name: "医疗文书撰写"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D01-07"
        - "D01-05"
      provenance:
        - "d01-anchor"
    - id: "D01-09"
      name: "医学文献综述"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D01-08"
        - "D01-06"
      provenance:
        - "d01-anchor"
    - id: "D01-10"
      name: "医疗问答科普"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D01-09"
        - "D01-07"
      provenance:
        - "d01-anchor"
    - id: "D01-11"
      name: "合规与免责边界"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D01-10"
        - "D01-08"
      provenance:
        - "d01-anchor"
    - id: "D01-12"
      name: "医疗数据隐私"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D01-11"
        - "D01-09"
      provenance:
        - "d01-anchor"
    - id: "STD-dicom"
      name: "标准 · DICOM 标准"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D01-06"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D01-11"
        - "D01-12"
      provenance:
        - "std-catalog"
    - id: "STD-hl7-fhir"
      name: "标准 · FHIR（资源扩展机制）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D01-01"
        - "D01-02"
        - "D01-03"
        - "D01-05"
        - "D01-08"
        - "D01-09"
        - "D01-10"
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
        - "D01-01"
        - "D01-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D01-04"
        - "D01-09"
      provenance:
        - "std-catalog"
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-unesco-ai"
      name: "标准 · AI 伦理建议书"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D01-07"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D01-03"
        - "D01-07"
        - "D01-08"
        - "D01-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D01-02"
        - "D01-06"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-skos"
      name: "标准 · SKOS 词表"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D01-04"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D01-05"
        - "D01-10"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D01-00）不随包交付，装载方须自备领域基础。
