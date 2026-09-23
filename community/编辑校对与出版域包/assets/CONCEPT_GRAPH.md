<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 编辑校对与出版（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「编辑校对与出版」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（编辑校对与出版:M01）与收口模块（编辑校对与出版:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 15 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（E10-00 领域通用前置）；节点 27 · 边 51 · 密度 1.8889。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E10-01` | 错别字与标点 | P40 | — | e10-anchor |
| `E10-02` | 语法与逻辑 | P60 | `E10-01` | e10-anchor |
| `E10-03` | 事实一致性 | P40 | `E10-02` | e10-anchor |
| `E10-04` | 引用规范化 | P60 | `E10-03`、`E10-01` | e10-anchor |
| `E10-05` | 排版与样式 | P40 | `E10-04`、`E10-02` | e10-anchor |
| `E10-06` | 审校流程 | P60 | `E10-05`、`E10-03` | e10-anchor |
| `E10-07` | 敏感内容筛查 | P40 | `E10-06`、`E10-04` | e10-anchor |
| `E10-08` | 多版本比对 | P60 | `E10-07`、`E10-05` | e10-anchor |
| `E10-09` | 出版元数据 | P40 | `E10-08`、`E10-06` | e10-anchor |
| `E10-10` | 电子书转换 | P60 | `E10-09`、`E10-07` | e10-anchor |
| `E10-11` | 版权与署名 | P40 | `E10-10`、`E10-08` | e10-anchor |
| `E10-12` | 读者反馈处理 | P60 | `E10-11`、`E10-09` | e10-anchor |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `E10-06`、`STD-ietf-json-schema` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `E10-02`、`E10-12` | std-catalog |
| `STD-creativecommons` | 标准 · 许可与权利表达（Creative Commons｜gov｜实测 ✓） | P80 | `E10-11` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `E10-01`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `E10-06`、`E10-08` | std-catalog |
| `STD-mlcommons-croissant` | 标准 · Croissant 数据集元数据（MLCommons｜data｜实测 ✓） | P80 | `E10-09`、`STD-schema-org` | std-catalog |
| `STD-schema-org` | 标准 · 结构化数据词表（Schema.org｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX｜gov｜实测 ✓） | P80 | `E10-11` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `E10-04`、`E10-09`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-epub-a11y` | 标准 · EPUB 无障碍 1.1（W3C｜gov｜实测 ✓） | P80 | `E10-02`、`E10-04`、`E10-08`、`E10-10`、`E10-12`、`STD-w3c-epub33` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C｜form｜实测 ✓） | P80 | `E10-01`、`E10-03`、`E10-05`、`E10-07`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `E10-03`、`E10-05`、`E10-07`、`E10-10`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E10-错别字与标点` | `E10-01` |
| `E10-语法与逻辑` | `E10-02` |
| `E10-事实一致性` | `E10-03` |
| `E10-引用规范化` | `E10-04` |
| `E10-排版与样式` | `E10-05` |
| `E10-审校流程` | `E10-06` |
| `E10-敏感内容筛查` | `E10-07` |
| `E10-多版本比对` | `E10-08` |
| `E10-出版元数据` | `E10-09` |
| `E10-电子书转换` | `E10-10` |
| `E10-版权与署名` | `E10-11` |
| `E10-读者反馈处理` | `E10-12` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-commonmark` | `STD-commonmark` |
| `std-creativecommons` | `STD-creativecommons` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-croissant` | `STD-mlcommons-croissant` |
| `std-schema-org` | `STD-schema-org` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-epub-a11y` | `STD-w3c-epub-a11y` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "编辑校对与出版"
  code: "E10"
  provenance_strength: "external"
  provenance_legend:
    e10-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E10-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "编辑校对与出版 全域"
      nodes:
        - "E10-01"
        - "E10-02"
        - "E10-03"
        - "E10-04"
        - "E10-05"
        - "E10-06"
        - "E10-07"
        - "E10-08"
        - "E10-09"
        - "E10-10"
        - "E10-11"
        - "E10-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-cloudevents"
        - "STD-commonmark"
        - "STD-creativecommons"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-croissant"
        - "STD-schema-org"
        - "STD-spdx-licenses"
        - "STD-vega-lite"
        - "STD-w3c-epub-a11y"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
        - "STD-w3c-xml"
  nodes:
    - id: "E10-01"
      name: "错别字与标点"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e10-anchor"
    - id: "E10-02"
      name: "语法与逻辑"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E10-01"
      provenance:
        - "e10-anchor"
    - id: "E10-03"
      name: "事实一致性"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E10-02"
      provenance:
        - "e10-anchor"
    - id: "E10-04"
      name: "引用规范化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E10-03"
        - "E10-01"
      provenance:
        - "e10-anchor"
    - id: "E10-05"
      name: "排版与样式"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E10-04"
        - "E10-02"
      provenance:
        - "e10-anchor"
    - id: "E10-06"
      name: "审校流程"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E10-05"
        - "E10-03"
      provenance:
        - "e10-anchor"
    - id: "E10-07"
      name: "敏感内容筛查"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E10-06"
        - "E10-04"
      provenance:
        - "e10-anchor"
    - id: "E10-08"
      name: "多版本比对"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E10-07"
        - "E10-05"
      provenance:
        - "e10-anchor"
    - id: "E10-09"
      name: "出版元数据"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E10-08"
        - "E10-06"
      provenance:
        - "e10-anchor"
    - id: "E10-10"
      name: "电子书转换"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E10-09"
        - "E10-07"
      provenance:
        - "e10-anchor"
    - id: "E10-11"
      name: "版权与署名"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E10-10"
        - "E10-08"
      provenance:
        - "e10-anchor"
    - id: "E10-12"
      name: "读者反馈处理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E10-11"
        - "E10-09"
      provenance:
        - "e10-anchor"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E10-06"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E10-02"
        - "E10-12"
      provenance:
        - "std-catalog"
    - id: "STD-creativecommons"
      name: "标准 · 许可与权利表达"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E10-11"
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
        - "E10-01"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E10-06"
        - "E10-08"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-croissant"
      name: "标准 · Croissant 数据集元数据"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E10-09"
        - "STD-schema-org"
      provenance:
        - "std-catalog"
    - id: "STD-schema-org"
      name: "标准 · 结构化数据词表"
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
        - "E10-11"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E10-04"
        - "E10-09"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub-a11y"
      name: "标准 · EPUB 无障碍 1.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E10-02"
        - "E10-04"
        - "E10-08"
        - "E10-10"
        - "E10-12"
        - "STD-w3c-epub33"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E10-01"
        - "E10-03"
        - "E10-05"
        - "E10-07"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E10-03"
        - "E10-05"
        - "E10-07"
        - "E10-10"
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
- 包外前置族（E10-00）不随包交付，装载方须自备领域基础。
