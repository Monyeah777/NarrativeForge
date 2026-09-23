<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+制造业（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+制造业」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI制造业:M01）与收口模块（AI制造业:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 18 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（D08-00 领域通用前置）；节点 30 · 边 51 · 密度 1.7000。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D08-01` | 工艺参数与 SOP | P40 | — | d08-anchor |
| `D08-02` | 设备手册与故障库 | P60 | `D08-01` | d08-anchor |
| `D08-03` | 质检图像判定 | P40 | `D08-02` | d08-anchor |
| `D08-04` | 排产与调度 | P60 | `D08-03`、`D08-01` | d08-anchor |
| `D08-05` | 工艺知识问答 | P40 | `D08-04`、`D08-02` | d08-anchor |
| `D08-06` | 图纸与 BOM 解析 | P60 | `D08-05`、`D08-03` | d08-anchor |
| `D08-07` | 供应链协同 | P40 | `D08-06`、`D08-04` | d08-anchor |
| `D08-08` | 能耗优化 | P60 | `D08-07`、`D08-05` | d08-anchor |
| `D08-09` | 安全生产规程 | P40 | `D08-08`、`D08-06` | d08-anchor |
| `D08-10` | 预测性维护 | P60 | `D08-09`、`D08-07` | d08-anchor |
| `D08-11` | 工单与 MES 交互 | P40 | `D08-10`、`D08-08` | d08-anchor |
| `D08-12` | 质量追溯 | P60 | `D08-11`、`D08-09` | d08-anchor |
| `STD-common-criteria` | 标准 · Common Criteria（ISO 15408）（CCRA｜gov｜实测 ✓） | P80 | `D08-06` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `D08-05`、`D08-12`、`STD-frictionless-package` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `D08-01`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `D08-04`、`D08-09`、`D08-11` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST｜gov｜实测 ✓） | P80 | `D08-01`、`D08-04`、`D08-10` | std-catalog |
| `STD-opcua` | 标准 · OPC UA 工业互联（OPC Foundation｜iface｜实测 ✓） | P80 | `D08-02` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP｜gov｜实测 ✓） | P80 | `D08-09`、`STD-owasp-top10` | std-catalog |
| `STD-owasp-top10` | 标准 · Web 十大风险（OWASP｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-spdx-3` | 标准 · SPDX 3.0（含 AI profile）（SPDX｜gov｜实测 ✓） | P80 | `D08-07` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `D08-03`、`D08-06`、`D08-07`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `D08-08`、`D08-11`、`D08-02`、`D08-05`、`D08-12`、`STD-rdf11` | std-catalog |
| `STD-w3c-svg2` | 标准 · SVG 2（W3C｜form｜实测 ✓） | P80 | `D08-03`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `D08-08`、`D08-10`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D08-工艺参数与-SOP` | `D08-01` |
| `D08-设备手册与故障库` | `D08-02` |
| `D08-质检图像判定` | `D08-03` |
| `D08-排产与调度` | `D08-04` |
| `D08-工艺知识问答` | `D08-05` |
| `D08-图纸与-BOM-解析` | `D08-06` |
| `D08-供应链协同` | `D08-07` |
| `D08-能耗优化` | `D08-08` |
| `D08-安全生产规程` | `D08-09` |
| `D08-预测性维护` | `D08-10` |
| `D08-工单与-MES-交互` | `D08-11` |
| `D08-质量追溯` | `D08-12` |
| `std-common-criteria` | `STD-common-criteria` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-opcua` | `STD-opcua` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-owasp-top10` | `STD-owasp-top10` |
| `std-rdf11` | `STD-rdf11` |
| `std-spdx-3` | `STD-spdx-3` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-svg2` | `STD-w3c-svg2` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+制造业"
  code: "D08"
  provenance_strength: "external"
  provenance_legend:
    d08-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D08-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+制造业 全域"
      nodes:
        - "D08-01"
        - "D08-02"
        - "D08-03"
        - "D08-04"
        - "D08-05"
        - "D08-06"
        - "D08-07"
        - "D08-08"
        - "D08-09"
        - "D08-10"
        - "D08-11"
        - "D08-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-common-criteria"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-nist-ai-rmf"
        - "STD-opcua"
        - "STD-owasp-llm"
        - "STD-owasp-top10"
        - "STD-rdf11"
        - "STD-spdx-3"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-svg2"
        - "STD-w3c-tabular-data"
        - "STD-w3c-xml"
  nodes:
    - id: "D08-01"
      name: "工艺参数与 SOP"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d08-anchor"
    - id: "D08-02"
      name: "设备手册与故障库"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D08-01"
      provenance:
        - "d08-anchor"
    - id: "D08-03"
      name: "质检图像判定"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D08-02"
      provenance:
        - "d08-anchor"
    - id: "D08-04"
      name: "排产与调度"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D08-03"
        - "D08-01"
      provenance:
        - "d08-anchor"
    - id: "D08-05"
      name: "工艺知识问答"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D08-04"
        - "D08-02"
      provenance:
        - "d08-anchor"
    - id: "D08-06"
      name: "图纸与 BOM 解析"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D08-05"
        - "D08-03"
      provenance:
        - "d08-anchor"
    - id: "D08-07"
      name: "供应链协同"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D08-06"
        - "D08-04"
      provenance:
        - "d08-anchor"
    - id: "D08-08"
      name: "能耗优化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D08-07"
        - "D08-05"
      provenance:
        - "d08-anchor"
    - id: "D08-09"
      name: "安全生产规程"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D08-08"
        - "D08-06"
      provenance:
        - "d08-anchor"
    - id: "D08-10"
      name: "预测性维护"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D08-09"
        - "D08-07"
      provenance:
        - "d08-anchor"
    - id: "D08-11"
      name: "工单与 MES 交互"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D08-10"
        - "D08-08"
      provenance:
        - "d08-anchor"
    - id: "D08-12"
      name: "质量追溯"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D08-11"
        - "D08-09"
      provenance:
        - "d08-anchor"
    - id: "STD-common-criteria"
      name: "标准 · Common Criteria（ISO 15408）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D08-06"
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
        - "D08-05"
        - "D08-12"
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
        - "D08-01"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D08-04"
        - "D08-09"
        - "D08-11"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D08-01"
        - "D08-04"
        - "D08-10"
      provenance:
        - "std-catalog"
    - id: "STD-opcua"
      name: "标准 · OPC UA 工业互联"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D08-02"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D08-09"
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
    - id: "STD-spdx-3"
      name: "标准 · SPDX 3.0（含 AI profile）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D08-07"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D08-03"
        - "D08-06"
        - "D08-07"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D08-08"
        - "D08-11"
        - "D08-02"
        - "D08-05"
        - "D08-12"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-svg2"
      name: "标准 · SVG 2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D08-03"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D08-08"
        - "D08-10"
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
- 包外前置族（D08-00）不随包交付，装载方须自备领域基础。
