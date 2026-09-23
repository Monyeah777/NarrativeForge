<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 零售与电商（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「零售与电商」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（零售与电商:M01）与收口模块（零售与电商:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 11 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（D11-00 领域通用前置）；节点 23 · 边 48 · 密度 2.0870。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D11-01` | 商品推荐 | P40 | — | d11-anchor |
| `D11-02` | 智能导购 | P60 | `D11-01` | d11-anchor |
| `D11-03` | 评论洞察 | P40 | `D11-02` | d11-anchor |
| `D11-04` | 动态定价 | P60 | `D11-03`、`D11-01` | d11-anchor |
| `D11-05` | 选品与滞销 | P40 | `D11-04`、`D11-02` | d11-anchor |
| `D11-06` | 私域运营 | P60 | `D11-05`、`D11-03` | d11-anchor |
| `D11-07` | 客服与退换 | P40 | `D11-06`、`D11-04` | d11-anchor |
| `D11-08` | 图文详情生成 | P60 | `D11-07`、`D11-05` | d11-anchor |
| `D11-09` | 直播脚本 | P40 | `D11-08`、`D11-06` | d11-anchor |
| `D11-10` | 跨境合规 | P60 | `D11-09`、`D11-07` | d11-anchor |
| `D11-11` | 比价与竞品 | P40 | `D11-10`、`D11-08` | d11-anchor |
| `D11-12` | 库存预测 | P60 | `D11-11`、`D11-09` | d11-anchor |
| `STD-common-criteria` | 标准 · Common Criteria（ISO 15408）（CCRA｜gov｜实测 ✓） | P80 | `D11-03`、`D11-06`、`D11-09`、`D11-12` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU｜gov｜实测 ✓） | P80 | `D11-10` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `D11-01`、`D11-05`、`D11-06`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `D11-04`、`D11-09`、`D11-11` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST｜gov｜实测 ✓） | P80 | `D11-01`、`D11-04`、`D11-07` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `D11-02`、`D11-03`、`D11-07`、`D11-08`、`D11-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `D11-02`、`D11-05`、`D11-08`、`D11-11`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `D11-10`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D11-商品推荐` | `D11-01` |
| `D11-智能导购` | `D11-02` |
| `D11-评论洞察` | `D11-03` |
| `D11-动态定价` | `D11-04` |
| `D11-选品与滞销` | `D11-05` |
| `D11-私域运营` | `D11-06` |
| `D11-客服与退换` | `D11-07` |
| `D11-图文详情生成` | `D11-08` |
| `D11-直播脚本` | `D11-09` |
| `D11-跨境合规` | `D11-10` |
| `D11-比价与竞品` | `D11-11` |
| `D11-库存预测` | `D11-12` |
| `std-common-criteria` | `STD-common-criteria` |
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
  domain: "零售与电商"
  code: "D11"
  provenance_strength: "external"
  provenance_legend:
    d11-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D11-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "零售与电商 全域"
      nodes:
        - "D11-01"
        - "D11-02"
        - "D11-03"
        - "D11-04"
        - "D11-05"
        - "D11-06"
        - "D11-07"
        - "D11-08"
        - "D11-09"
        - "D11-10"
        - "D11-11"
        - "D11-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-common-criteria"
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
    - id: "D11-01"
      name: "商品推荐"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d11-anchor"
    - id: "D11-02"
      name: "智能导购"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D11-01"
      provenance:
        - "d11-anchor"
    - id: "D11-03"
      name: "评论洞察"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D11-02"
      provenance:
        - "d11-anchor"
    - id: "D11-04"
      name: "动态定价"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D11-03"
        - "D11-01"
      provenance:
        - "d11-anchor"
    - id: "D11-05"
      name: "选品与滞销"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D11-04"
        - "D11-02"
      provenance:
        - "d11-anchor"
    - id: "D11-06"
      name: "私域运营"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D11-05"
        - "D11-03"
      provenance:
        - "d11-anchor"
    - id: "D11-07"
      name: "客服与退换"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D11-06"
        - "D11-04"
      provenance:
        - "d11-anchor"
    - id: "D11-08"
      name: "图文详情生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D11-07"
        - "D11-05"
      provenance:
        - "d11-anchor"
    - id: "D11-09"
      name: "直播脚本"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D11-08"
        - "D11-06"
      provenance:
        - "d11-anchor"
    - id: "D11-10"
      name: "跨境合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D11-09"
        - "D11-07"
      provenance:
        - "d11-anchor"
    - id: "D11-11"
      name: "比价与竞品"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D11-10"
        - "D11-08"
      provenance:
        - "d11-anchor"
    - id: "D11-12"
      name: "库存预测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D11-11"
        - "D11-09"
      provenance:
        - "d11-anchor"
    - id: "STD-common-criteria"
      name: "标准 · Common Criteria（ISO 15408）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D11-03"
        - "D11-06"
        - "D11-09"
        - "D11-12"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D11-10"
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
        - "D11-01"
        - "D11-05"
        - "D11-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D11-04"
        - "D11-09"
        - "D11-11"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D11-01"
        - "D11-04"
        - "D11-07"
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
        - "D11-02"
        - "D11-03"
        - "D11-07"
        - "D11-08"
        - "D11-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D11-02"
        - "D11-05"
        - "D11-08"
        - "D11-11"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D11-10"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D11-00）不随包交付，装载方须自备领域基础。
