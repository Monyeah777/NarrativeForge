<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 产业与商业落地（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「产业与商业落地」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（产业与商业落地:M01）与收口模块（产业与商业落地:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 10 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（F10-00 领域通用前置）；节点 22 · 边 48 · 密度 2.1818。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `F10-01` | 需求评估 | P40 | — | f10-anchor |
| `F10-02` | 场景选型 | P60 | `F10-01` | f10-anchor |
| `F10-03` | 概念验证设计 | P40 | `F10-02` | f10-anchor |
| `F10-04` | 投入产出测算 | P60 | `F10-03`、`F10-01` | f10-anchor |
| `F10-05` | 采购与招标 | P40 | `F10-04`、`F10-02` | f10-anchor |
| `F10-06` | 集成交付 | P60 | `F10-05`、`F10-03` | f10-anchor |
| `F10-07` | 变革管理 | P40 | `F10-06`、`F10-04` | f10-anchor |
| `F10-08` | 培训赋能 | P60 | `F10-07`、`F10-05` | f10-anchor |
| `F10-09` | 供应商评估 | P40 | `F10-08`、`F10-06` | f10-anchor |
| `F10-10` | 行业方案打包 | P60 | `F10-09`、`F10-07` | f10-anchor |
| `F10-11` | 服务定价 | P40 | `F10-10`、`F10-08` | f10-anchor |
| `F10-12` | 项目复盘 | P60 | `F10-11`、`F10-09` | f10-anchor |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `F10-01`、`F10-05`、`F10-06`、`F10-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `F10-10` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST｜gov｜实测 ✓） | P80 | `F10-01`、`F10-04`、`F10-07`、`F10-10` | std-catalog |
| `STD-oasis-openapi` | 标准 · OpenAPI 3.1（OpenAPI Initiative｜iface｜实测 ✓） | P80 | `F10-11`、`STD-ietf-json-schema` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX｜gov｜实测 ✓） | P80 | `F10-03`、`F10-06`、`F10-09`、`F10-12` | std-catalog |
| `STD-unesco-ai` | 标准 · AI 伦理建议书（UNESCO｜gov｜实测 ✓） | P80 | `F10-08` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `F10-02`、`F10-03`、`F10-04`、`F10-07`、`F10-08`、`F10-09`、`F10-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `F10-02`、`F10-05`、`STD-rdf11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `F10-需求评估` | `F10-01` |
| `F10-场景选型` | `F10-02` |
| `F10-概念验证设计` | `F10-03` |
| `F10-投入产出测算` | `F10-04` |
| `F10-采购与招标` | `F10-05` |
| `F10-集成交付` | `F10-06` |
| `F10-变革管理` | `F10-07` |
| `F10-培训赋能` | `F10-08` |
| `F10-供应商评估` | `F10-09` |
| `F10-行业方案打包` | `F10-10` |
| `F10-服务定价` | `F10-11` |
| `F10-项目复盘` | `F10-12` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-oasis-openapi` | `STD-oasis-openapi` |
| `std-rdf11` | `STD-rdf11` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-unesco-ai` | `STD-unesco-ai` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "产业与商业落地"
  code: "F10"
  provenance_strength: "external"
  provenance_legend:
    f10-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "F10-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "产业与商业落地 全域"
      nodes:
        - "F10-01"
        - "F10-02"
        - "F10-03"
        - "F10-04"
        - "F10-05"
        - "F10-06"
        - "F10-07"
        - "F10-08"
        - "F10-09"
        - "F10-10"
        - "F10-11"
        - "F10-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-nist-ai-rmf"
        - "STD-oasis-openapi"
        - "STD-rdf11"
        - "STD-spdx-licenses"
        - "STD-unesco-ai"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
  nodes:
    - id: "F10-01"
      name: "需求评估"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "f10-anchor"
    - id: "F10-02"
      name: "场景选型"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F10-01"
      provenance:
        - "f10-anchor"
    - id: "F10-03"
      name: "概念验证设计"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F10-02"
      provenance:
        - "f10-anchor"
    - id: "F10-04"
      name: "投入产出测算"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F10-03"
        - "F10-01"
      provenance:
        - "f10-anchor"
    - id: "F10-05"
      name: "采购与招标"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F10-04"
        - "F10-02"
      provenance:
        - "f10-anchor"
    - id: "F10-06"
      name: "集成交付"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F10-05"
        - "F10-03"
      provenance:
        - "f10-anchor"
    - id: "F10-07"
      name: "变革管理"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F10-06"
        - "F10-04"
      provenance:
        - "f10-anchor"
    - id: "F10-08"
      name: "培训赋能"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F10-07"
        - "F10-05"
      provenance:
        - "f10-anchor"
    - id: "F10-09"
      name: "供应商评估"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F10-08"
        - "F10-06"
      provenance:
        - "f10-anchor"
    - id: "F10-10"
      name: "行业方案打包"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F10-09"
        - "F10-07"
      provenance:
        - "f10-anchor"
    - id: "F10-11"
      name: "服务定价"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F10-10"
        - "F10-08"
      provenance:
        - "f10-anchor"
    - id: "F10-12"
      name: "项目复盘"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F10-11"
        - "F10-09"
      provenance:
        - "f10-anchor"
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
        - "F10-01"
        - "F10-05"
        - "F10-06"
        - "F10-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F10-10"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F10-01"
        - "F10-04"
        - "F10-07"
        - "F10-10"
      provenance:
        - "std-catalog"
    - id: "STD-oasis-openapi"
      name: "标准 · OpenAPI 3.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F10-11"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-spdx-licenses"
      name: "标准 · SPDX 许可证清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F10-03"
        - "F10-06"
        - "F10-09"
        - "F10-12"
      provenance:
        - "std-catalog"
    - id: "STD-unesco-ai"
      name: "标准 · AI 伦理建议书"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F10-08"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F10-02"
        - "F10-03"
        - "F10-04"
        - "F10-07"
        - "F10-08"
        - "F10-09"
        - "F10-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F10-02"
        - "F10-05"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（F10-00）不随包交付，装载方须自备领域基础。
