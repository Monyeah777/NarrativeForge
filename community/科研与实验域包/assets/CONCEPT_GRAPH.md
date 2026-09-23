<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 科研与实验（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「科研与实验」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（科研与实验:M01）与收口模块（科研与实验:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 16 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（D20-00 领域通用前置）；节点 28 · 边 52 · 密度 1.8571。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D20-01` | 文献检索与综述 | P40 | — | d20-anchor |
| `D20-02` | 实验设计 | P60 | `D20-01` | d20-anchor |
| `D20-03` | 数据分析与统计 | P40 | `D20-02` | d20-anchor |
| `D20-04` | 代码复现 | P60 | `D20-03`、`D20-01` | d20-anchor |
| `D20-05` | 材料筛选 | P40 | `D20-04`、`D20-02` | d20-anchor |
| `D20-06` | 生物信息注释 | P60 | `D20-05`、`D20-03` | d20-anchor |
| `D20-07` | 论文写作与投稿 | P40 | `D20-06`、`D20-04` | d20-anchor |
| `D20-08` | 评议辅助 | P60 | `D20-07`、`D20-05` | d20-anchor |
| `D20-09` | 基金申报 | P40 | `D20-08`、`D20-06` | d20-anchor |
| `D20-10` | 专利检索 | P60 | `D20-09`、`D20-07` | d20-anchor |
| `D20-11` | 模拟仿真 | P40 | `D20-10`、`D20-08` | d20-anchor |
| `D20-12` | 科研伦理审查 | P60 | `D20-11`、`D20-09` | d20-anchor |
| `STD-bagit` | 标准 · BagIt (RFC 8493)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `D20-07` | std-catalog |
| `STD-datacite` | 标准 · 元数据内核（DataCite｜gov｜实测 ✓） | P80 | `D20-02`、`D20-04`、`D20-06`、`D20-08`、`STD-w3c-xml` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | `D20-01`、`D20-10`、`STD-ietf-json-schema` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `D20-06`、`D20-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `D20-04`、`D20-09` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST｜gov｜实测 ✓） | P80 | `D20-12` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-rocrate` | 标准 · RO-Crate 1.1（Research Object｜gov｜实测 ✓） | P80 | `D20-03`、`D20-05`、`D20-07`、`D20-09`、`D20-11`、`STD-bagit`、`STD-w3c-json-ld` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `D20-02`、`D20-03`、`D20-08`、`D20-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-json-ld` | 标准 · JSON-LD 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `D20-01`、`D20-10`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `D20-05`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D20-文献检索与综述` | `D20-01` |
| `D20-实验设计` | `D20-02` |
| `D20-数据分析与统计` | `D20-03` |
| `D20-代码复现` | `D20-04` |
| `D20-材料筛选` | `D20-05` |
| `D20-生物信息注释` | `D20-06` |
| `D20-论文写作与投稿` | `D20-07` |
| `D20-评议辅助` | `D20-08` |
| `D20-基金申报` | `D20-09` |
| `D20-专利检索` | `D20-10` |
| `D20-模拟仿真` | `D20-11` |
| `D20-科研伦理审查` | `D20-12` |
| `std-bagit` | `STD-bagit` |
| `std-commonmark` | `STD-commonmark` |
| `std-datacite` | `STD-datacite` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-rdf11` | `STD-rdf11` |
| `std-rocrate` | `STD-rocrate` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-json-ld` | `STD-w3c-json-ld` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "科研与实验"
  code: "D20"
  provenance_strength: "external"
  provenance_legend:
    d20-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D20-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "科研与实验 全域"
      nodes:
        - "D20-01"
        - "D20-02"
        - "D20-03"
        - "D20-04"
        - "D20-05"
        - "D20-06"
        - "D20-07"
        - "D20-08"
        - "D20-09"
        - "D20-10"
        - "D20-11"
        - "D20-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-bagit"
        - "STD-commonmark"
        - "STD-datacite"
        - "STD-frictionless-package"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-nist-ai-rmf"
        - "STD-rdf11"
        - "STD-rocrate"
        - "STD-vega-lite"
        - "STD-w3c-json-ld"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
        - "STD-w3c-xml"
  nodes:
    - id: "D20-01"
      name: "文献检索与综述"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d20-anchor"
    - id: "D20-02"
      name: "实验设计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D20-01"
      provenance:
        - "d20-anchor"
    - id: "D20-03"
      name: "数据分析与统计"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D20-02"
      provenance:
        - "d20-anchor"
    - id: "D20-04"
      name: "代码复现"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D20-03"
        - "D20-01"
      provenance:
        - "d20-anchor"
    - id: "D20-05"
      name: "材料筛选"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D20-04"
        - "D20-02"
      provenance:
        - "d20-anchor"
    - id: "D20-06"
      name: "生物信息注释"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D20-05"
        - "D20-03"
      provenance:
        - "d20-anchor"
    - id: "D20-07"
      name: "论文写作与投稿"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D20-06"
        - "D20-04"
      provenance:
        - "d20-anchor"
    - id: "D20-08"
      name: "评议辅助"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D20-07"
        - "D20-05"
      provenance:
        - "d20-anchor"
    - id: "D20-09"
      name: "基金申报"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D20-08"
        - "D20-06"
      provenance:
        - "d20-anchor"
    - id: "D20-10"
      name: "专利检索"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D20-09"
        - "D20-07"
      provenance:
        - "d20-anchor"
    - id: "D20-11"
      name: "模拟仿真"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D20-10"
        - "D20-08"
      provenance:
        - "d20-anchor"
    - id: "D20-12"
      name: "科研伦理审查"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D20-11"
        - "D20-09"
      provenance:
        - "d20-anchor"
    - id: "STD-bagit"
      name: "标准 · BagIt (RFC 8493)"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D20-07"
      provenance:
        - "std-catalog"
    - id: "STD-datacite"
      name: "标准 · 元数据内核"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D20-02"
        - "D20-04"
        - "D20-06"
        - "D20-08"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D20-01"
        - "D20-10"
        - "STD-ietf-json-schema"
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
        - "D20-06"
        - "D20-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D20-04"
        - "D20-09"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D20-12"
      provenance:
        - "std-catalog"
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-rocrate"
      name: "标准 · RO-Crate 1.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D20-03"
        - "D20-05"
        - "D20-07"
        - "D20-09"
        - "D20-11"
        - "STD-bagit"
        - "STD-w3c-json-ld"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D20-02"
        - "D20-03"
        - "D20-08"
        - "D20-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-json-ld"
      name: "标准 · JSON-LD 1.1"
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
        - "D20-01"
        - "D20-10"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D20-05"
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
- 包外前置族（D20-00）不随包交付，装载方须自备领域基础。
