<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 文旅与酒店（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「文旅与酒店」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（文旅与酒店:M01）与收口模块（文旅与酒店:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 16 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（D19-00 领域通用前置）；节点 28 · 边 52 · 密度 1.8571。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D19-01` | 行程规划 | P40 | — | d19-anchor |
| `D19-02` | 讲解词生成 | P60 | `D19-01` | d19-anchor |
| `D19-03` | 多语导览 | P40 | `D19-02` | d19-anchor |
| `D19-04` | 客流预测 | P60 | `D19-03`、`D19-01` | d19-anchor |
| `D19-05` | 票务问答 | P40 | `D19-04`、`D19-02` | d19-anchor |
| `D19-06` | 客房服务问答 | P60 | `D19-05`、`D19-03` | d19-anchor |
| `D19-07` | 点评洞察 | P40 | `D19-06`、`D19-04` | d19-anchor |
| `D19-08` | 目的地营销 | P60 | `D19-07`、`D19-05` | d19-anchor |
| `D19-09` | 文物保护 | P40 | `D19-08`、`D19-06` | d19-anchor |
| `D19-10` | 会展策划 | P60 | `D19-09`、`D19-07` | d19-anchor |
| `D19-11` | 签证与出入境 | P40 | `D19-10`、`D19-08` | d19-anchor |
| `D19-12` | 景区安全预警 | P60 | `D19-11`、`D19-09` | d19-anchor |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `D19-04`、`STD-ietf-json-schema` | std-catalog |
| `STD-common-criteria` | 标准 · Common Criteria（ISO 15408）（CCRA｜gov｜实测 ✓） | P80 | `D19-03`、`D19-09` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `D19-05`、`STD-frictionless-package` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `D19-01`、`D19-06`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `D19-09`、`D19-11` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST｜gov｜实测 ✓） | P80 | `D19-01`、`D19-04`、`D19-07`、`D19-10` | std-catalog |
| `STD-oasis-openapi` | 标准 · OpenAPI 3.1（OpenAPI Initiative｜iface｜实测 ✓） | P80 | `D19-06`、`STD-ietf-json-schema` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP｜gov｜实测 ✓） | P80 | `D19-12`、`STD-owasp-top10` | std-catalog |
| `STD-owasp-top10` | 标准 · Web 十大风险（OWASP｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `D19-02`、`D19-03`、`D19-07`、`D19-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `D19-02`、`D19-08`、`D19-11`、`D19-05`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `D19-08`、`D19-10`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D19-行程规划` | `D19-01` |
| `D19-讲解词生成` | `D19-02` |
| `D19-多语导览` | `D19-03` |
| `D19-客流预测` | `D19-04` |
| `D19-票务问答` | `D19-05` |
| `D19-客房服务问答` | `D19-06` |
| `D19-点评洞察` | `D19-07` |
| `D19-目的地营销` | `D19-08` |
| `D19-文物保护` | `D19-09` |
| `D19-会展策划` | `D19-10` |
| `D19-签证与出入境` | `D19-11` |
| `D19-景区安全预警` | `D19-12` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-common-criteria` | `STD-common-criteria` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-oasis-openapi` | `STD-oasis-openapi` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-owasp-top10` | `STD-owasp-top10` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "文旅与酒店"
  code: "D19"
  provenance_strength: "external"
  provenance_legend:
    d19-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D19-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "文旅与酒店 全域"
      nodes:
        - "D19-01"
        - "D19-02"
        - "D19-03"
        - "D19-04"
        - "D19-05"
        - "D19-06"
        - "D19-07"
        - "D19-08"
        - "D19-09"
        - "D19-10"
        - "D19-11"
        - "D19-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-cloudevents"
        - "STD-common-criteria"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-nist-ai-rmf"
        - "STD-oasis-openapi"
        - "STD-owasp-llm"
        - "STD-owasp-top10"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "D19-01"
      name: "行程规划"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d19-anchor"
    - id: "D19-02"
      name: "讲解词生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D19-01"
      provenance:
        - "d19-anchor"
    - id: "D19-03"
      name: "多语导览"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D19-02"
      provenance:
        - "d19-anchor"
    - id: "D19-04"
      name: "客流预测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D19-03"
        - "D19-01"
      provenance:
        - "d19-anchor"
    - id: "D19-05"
      name: "票务问答"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D19-04"
        - "D19-02"
      provenance:
        - "d19-anchor"
    - id: "D19-06"
      name: "客房服务问答"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D19-05"
        - "D19-03"
      provenance:
        - "d19-anchor"
    - id: "D19-07"
      name: "点评洞察"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D19-06"
        - "D19-04"
      provenance:
        - "d19-anchor"
    - id: "D19-08"
      name: "目的地营销"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D19-07"
        - "D19-05"
      provenance:
        - "d19-anchor"
    - id: "D19-09"
      name: "文物保护"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D19-08"
        - "D19-06"
      provenance:
        - "d19-anchor"
    - id: "D19-10"
      name: "会展策划"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D19-09"
        - "D19-07"
      provenance:
        - "d19-anchor"
    - id: "D19-11"
      name: "签证与出入境"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D19-10"
        - "D19-08"
      provenance:
        - "d19-anchor"
    - id: "D19-12"
      name: "景区安全预警"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D19-11"
        - "D19-09"
      provenance:
        - "d19-anchor"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D19-04"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-common-criteria"
      name: "标准 · Common Criteria（ISO 15408）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D19-03"
        - "D19-09"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D19-05"
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
        - "D19-01"
        - "D19-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D19-09"
        - "D19-11"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D19-01"
        - "D19-04"
        - "D19-07"
        - "D19-10"
      provenance:
        - "std-catalog"
    - id: "STD-oasis-openapi"
      name: "标准 · OpenAPI 3.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D19-06"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D19-12"
        - "STD-owasp-top10"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-top10"
      name: "标准 · Web 十大风险"
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
        - "D19-02"
        - "D19-03"
        - "D19-07"
        - "D19-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D19-02"
        - "D19-08"
        - "D19-11"
        - "D19-05"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D19-08"
        - "D19-10"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D19-00）不随包交付，装载方须自备领域基础。
