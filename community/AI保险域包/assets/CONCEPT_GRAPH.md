<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+保险（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+保险」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI保险:M01）与收口模块（AI保险:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 12 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（D05-00 领域通用前置）；节点 24 · 边 48 · 密度 2.0000。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D05-01` | 保险条款解读 | P40 | — | d05-anchor |
| `D05-02` | 核保规则 | P60 | `D05-01` | d05-anchor |
| `D05-03` | 理赔材料审核 | P40 | `D05-02` | d05-anchor |
| `D05-04` | 理赔定损 | P60 | `D05-03`、`D05-01` | d05-anchor |
| `D05-05` | 精算建模 | P40 | `D05-04`、`D05-02` | d05-anchor |
| `D05-06` | 产品条款生成 | P60 | `D05-05`、`D05-03` | d05-anchor |
| `D05-07` | 保险客服问答 | P40 | `D05-06`、`D05-04` | d05-anchor |
| `D05-08` | 销售话术合规 | P60 | `D05-07`、`D05-05` | d05-anchor |
| `D05-09` | 反欺诈 | P40 | `D05-08`、`D05-06` | d05-anchor |
| `D05-10` | 保险法律合规 | P60 | `D05-09`、`D05-07` | d05-anchor |
| `D05-11` | 再保与风险 | P40 | `D05-10`、`D05-08` | d05-anchor |
| `D05-12` | 保单结构化 | P60 | `D05-11`、`D05-09` | d05-anchor |
| `STD-common-criteria` | 标准 · Common Criteria（ISO 15408）（CCRA｜gov｜实测 ✓） | P80 | `D05-03`、`D05-06`、`D05-09`、`D05-12` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU｜gov｜实测 ✓） | P80 | `D05-08`、`D05-10` | std-catalog |
| `STD-gips` | 标准 · GIPS 绩效标准（CFA Institute｜gov｜实测 ✓） | P80 | `D05-01`、`D05-07` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `D05-01`、`D05-05`、`D05-06`、`D05-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `D05-04`、`D05-09` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST｜gov｜实测 ✓） | P80 | `D05-04`、`D05-11` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `D05-02`、`D05-03`、`D05-07`、`D05-08`、`D05-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `D05-02`、`D05-05`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `D05-10`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D05-保险条款解读` | `D05-01` |
| `D05-核保规则` | `D05-02` |
| `D05-理赔材料审核` | `D05-03` |
| `D05-理赔定损` | `D05-04` |
| `D05-精算建模` | `D05-05` |
| `D05-产品条款生成` | `D05-06` |
| `D05-保险客服问答` | `D05-07` |
| `D05-销售话术合规` | `D05-08` |
| `D05-反欺诈` | `D05-09` |
| `D05-保险法律合规` | `D05-10` |
| `D05-再保与风险` | `D05-11` |
| `D05-保单结构化` | `D05-12` |
| `std-common-criteria` | `STD-common-criteria` |
| `std-gdpr` | `STD-gdpr` |
| `std-gips` | `STD-gips` |
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
  domain: "AI+保险"
  code: "D05"
  provenance_strength: "external"
  provenance_legend:
    d05-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D05-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+保险 全域"
      nodes:
        - "D05-01"
        - "D05-02"
        - "D05-03"
        - "D05-04"
        - "D05-05"
        - "D05-06"
        - "D05-07"
        - "D05-08"
        - "D05-09"
        - "D05-10"
        - "D05-11"
        - "D05-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-common-criteria"
        - "STD-gdpr"
        - "STD-gips"
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
    - id: "D05-01"
      name: "保险条款解读"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d05-anchor"
    - id: "D05-02"
      name: "核保规则"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-01"
      provenance:
        - "d05-anchor"
    - id: "D05-03"
      name: "理赔材料审核"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D05-02"
      provenance:
        - "d05-anchor"
    - id: "D05-04"
      name: "理赔定损"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-03"
        - "D05-01"
      provenance:
        - "d05-anchor"
    - id: "D05-05"
      name: "精算建模"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D05-04"
        - "D05-02"
      provenance:
        - "d05-anchor"
    - id: "D05-06"
      name: "产品条款生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-05"
        - "D05-03"
      provenance:
        - "d05-anchor"
    - id: "D05-07"
      name: "保险客服问答"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D05-06"
        - "D05-04"
      provenance:
        - "d05-anchor"
    - id: "D05-08"
      name: "销售话术合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-07"
        - "D05-05"
      provenance:
        - "d05-anchor"
    - id: "D05-09"
      name: "反欺诈"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D05-08"
        - "D05-06"
      provenance:
        - "d05-anchor"
    - id: "D05-10"
      name: "保险法律合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-09"
        - "D05-07"
      provenance:
        - "d05-anchor"
    - id: "D05-11"
      name: "再保与风险"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D05-10"
        - "D05-08"
      provenance:
        - "d05-anchor"
    - id: "D05-12"
      name: "保单结构化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-11"
        - "D05-09"
      provenance:
        - "d05-anchor"
    - id: "STD-common-criteria"
      name: "标准 · Common Criteria（ISO 15408）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-03"
        - "D05-06"
        - "D05-09"
        - "D05-12"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-08"
        - "D05-10"
      provenance:
        - "std-catalog"
    - id: "STD-gips"
      name: "标准 · GIPS 绩效标准"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-01"
        - "D05-07"
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
        - "D05-01"
        - "D05-05"
        - "D05-06"
        - "D05-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-04"
        - "D05-09"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-04"
        - "D05-11"
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
        - "D05-02"
        - "D05-03"
        - "D05-07"
        - "D05-08"
        - "D05-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-02"
        - "D05-05"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-10"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D05-00）不随包交付，装载方须自备领域基础。
