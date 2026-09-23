<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+法律与合规（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+法律与合规」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI法律与合规:M01）与收口模块（AI法律与合规:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 15 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（D03-00 领域通用前置）；节点 27 · 边 50 · 密度 1.8519。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D03-01` | 法条与判例检索 | P40 | — | d03-anchor |
| `D03-02` | 合同审查与条款比对 | P60 | `D03-01` | d03-anchor |
| `D03-03` | 合同生成与模板 | P40 | `D03-02` | d03-anchor |
| `D03-04` | 诉讼文书撰写 | P60 | `D03-03`、`D03-01` | d03-anchor |
| `D03-05` | 法律意见书 | P40 | `D03-04`、`D03-02` | d03-anchor |
| `D03-06` | 合规清单检索 | P60 | `D03-05`、`D03-03` | d03-anchor |
| `D03-07` | 监管政策跟踪 | P40 | `D03-06`、`D03-04` | d03-anchor |
| `D03-08` | 知识产权检索 | P60 | `D03-07`、`D03-05` | d03-anchor |
| `D03-09` | 商标与专利分析 | P40 | `D03-08`、`D03-06` | d03-anchor |
| `D03-10` | 尽职调查 | P60 | `D03-09`、`D03-07` | d03-anchor |
| `D03-11` | 法律问答科普 | P40 | `D03-10`、`D03-08` | d03-anchor |
| `D03-12` | 执业边界与免责 | P60 | `D03-11`、`D03-09` | d03-anchor |
| `STD-common-criteria` | 标准 · Common Criteria（ISO 15408）（CCRA｜gov｜实测 ✓） | P80 | `D03-09`、`D03-12` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `D03-03` | std-catalog |
| `STD-creativecommons` | 标准 · 许可与权利表达（Creative Commons｜gov｜实测 ✓） | P80 | `D03-08` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | `D03-01`、`STD-ietf-json-schema` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `D03-11`、`STD-frictionless-package` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU｜gov｜实测 ✓） | P80 | `D03-06`、`D03-07` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `D03-05`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `D03-04`、`D03-09` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST｜gov｜实测 ✓） | P80 | `D03-04`、`D03-10` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `D03-02`、`D03-07`、`D03-08`、`D03-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `D03-02`、`D03-05`、`D03-01`、`D03-11`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `D03-03`、`D03-06`、`D03-10`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D03-法条与判例检索` | `D03-01` |
| `D03-合同审查与条款比对` | `D03-02` |
| `D03-合同生成与模板` | `D03-03` |
| `D03-诉讼文书撰写` | `D03-04` |
| `D03-法律意见书` | `D03-05` |
| `D03-合规清单检索` | `D03-06` |
| `D03-监管政策跟踪` | `D03-07` |
| `D03-知识产权检索` | `D03-08` |
| `D03-商标与专利分析` | `D03-09` |
| `D03-尽职调查` | `D03-10` |
| `D03-法律问答科普` | `D03-11` |
| `D03-执业边界与免责` | `D03-12` |
| `std-common-criteria` | `STD-common-criteria` |
| `std-commonmark` | `STD-commonmark` |
| `std-creativecommons` | `STD-creativecommons` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-gdpr` | `STD-gdpr` |
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
  domain: "AI+法律与合规"
  code: "D03"
  provenance_strength: "external"
  provenance_legend:
    d03-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D03-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+法律与合规 全域"
      nodes:
        - "D03-01"
        - "D03-02"
        - "D03-03"
        - "D03-04"
        - "D03-05"
        - "D03-06"
        - "D03-07"
        - "D03-08"
        - "D03-09"
        - "D03-10"
        - "D03-11"
        - "D03-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-common-criteria"
        - "STD-commonmark"
        - "STD-creativecommons"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-gdpr"
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
    - id: "D03-01"
      name: "法条与判例检索"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d03-anchor"
    - id: "D03-02"
      name: "合同审查与条款比对"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D03-01"
      provenance:
        - "d03-anchor"
    - id: "D03-03"
      name: "合同生成与模板"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D03-02"
      provenance:
        - "d03-anchor"
    - id: "D03-04"
      name: "诉讼文书撰写"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D03-03"
        - "D03-01"
      provenance:
        - "d03-anchor"
    - id: "D03-05"
      name: "法律意见书"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D03-04"
        - "D03-02"
      provenance:
        - "d03-anchor"
    - id: "D03-06"
      name: "合规清单检索"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D03-05"
        - "D03-03"
      provenance:
        - "d03-anchor"
    - id: "D03-07"
      name: "监管政策跟踪"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D03-06"
        - "D03-04"
      provenance:
        - "d03-anchor"
    - id: "D03-08"
      name: "知识产权检索"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D03-07"
        - "D03-05"
      provenance:
        - "d03-anchor"
    - id: "D03-09"
      name: "商标与专利分析"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D03-08"
        - "D03-06"
      provenance:
        - "d03-anchor"
    - id: "D03-10"
      name: "尽职调查"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D03-09"
        - "D03-07"
      provenance:
        - "d03-anchor"
    - id: "D03-11"
      name: "法律问答科普"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D03-10"
        - "D03-08"
      provenance:
        - "d03-anchor"
    - id: "D03-12"
      name: "执业边界与免责"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D03-11"
        - "D03-09"
      provenance:
        - "d03-anchor"
    - id: "STD-common-criteria"
      name: "标准 · Common Criteria（ISO 15408）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D03-09"
        - "D03-12"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D03-03"
      provenance:
        - "std-catalog"
    - id: "STD-creativecommons"
      name: "标准 · 许可与权利表达"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D03-08"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D03-01"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D03-11"
        - "STD-frictionless-package"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D03-06"
        - "D03-07"
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
        - "D03-05"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D03-04"
        - "D03-09"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D03-04"
        - "D03-10"
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
        - "D03-02"
        - "D03-07"
        - "D03-08"
        - "D03-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D03-02"
        - "D03-05"
        - "D03-01"
        - "D03-11"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D03-03"
        - "D03-06"
        - "D03-10"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D03-00）不随包交付，装载方须自备领域基础。
