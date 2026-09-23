<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 多语翻译与本地化（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「多语翻译与本地化」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（多语翻译与本地化:M01）与收口模块（多语翻译与本地化:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 15 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（E06-00 领域通用前置）；节点 27 · 边 50 · 密度 1.8519。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E06-01` | 术语库 | P40 | — | e06-anchor |
| `E06-02` | 风格指南 | P60 | `E06-01` | e06-anchor |
| `E06-03` | 字幕翻译 | P40 | `E06-02` | e06-anchor |
| `E06-04` | 配音对口型 | P60 | `E06-03`、`E06-01` | e06-anchor |
| `E06-05` | 游戏本地化 | P40 | `E06-04`、`E06-02` | e06-anchor |
| `E06-06` | 法律与医学翻译 | P60 | `E06-05`、`E06-03` | e06-anchor |
| `E06-07` | 文化适配 | P40 | `E06-06`、`E06-04` | e06-anchor |
| `E06-08` | 回译校验 | P60 | `E06-07`、`E06-05` | e06-anchor |
| `E06-09` | 译后编辑 | P40 | `E06-08`、`E06-06` | e06-anchor |
| `E06-10` | 多语排版 | P60 | `E06-09`、`E06-07` | e06-anchor |
| `E06-11` | 格式与时区 | P40 | `E06-10`、`E06-08` | e06-anchor |
| `E06-12` | 质量评估 | P60 | `E06-11`、`E06-09` | e06-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `E06-04`、`E06-07`、`E06-01`、`E06-02`、`E06-05`、`E06-08`、`E06-11`、`E06-12` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `E06-12`、`STD-frictionless-package` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `E06-08`、`E06-06`、`STD-ietf-json` | std-catalog |
| `STD-iso-8601` | 标准 · 日期时间（含 8601-2 扩展）（ISO｜data｜实测 ✗） | P80 | — | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `E06-03` | std-catalog |
| `STD-oci-image` | 标准 · 镜像清单（OCI｜iface｜实测 ✓） | P80 | `E06-03` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-rfc3339` | 标准 · 时间戳（IETF｜data｜实测 ✓） | P80 | `E06-11`、`STD-iso-8601` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C｜form｜实测 ✓） | P80 | `E06-06`、`E06-09`、`E06-10`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-skos` | 标准 · SKOS 词表（W3C｜data｜实测 ✓） | P80 | `E06-01`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `E06-02`、`E06-05`、`E06-04`、`E06-07`、`E06-09`、`E06-10`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E06-术语库` | `E06-01` |
| `E06-风格指南` | `E06-02` |
| `E06-字幕翻译` | `E06-03` |
| `E06-配音对口型` | `E06-04` |
| `E06-游戏本地化` | `E06-05` |
| `E06-法律与医学翻译` | `E06-06` |
| `E06-文化适配` | `E06-07` |
| `E06-回译校验` | `E06-08` |
| `E06-译后编辑` | `E06-09` |
| `E06-多语排版` | `E06-10` |
| `E06-格式与时区` | `E06-11` |
| `E06-质量评估` | `E06-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-iso-8601` | `STD-iso-8601` |
| `std-mermaid` | `STD-mermaid` |
| `std-oci-image` | `STD-oci-image` |
| `std-rdf11` | `STD-rdf11` |
| `std-rfc3339` | `STD-rfc3339` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-skos` | `STD-w3c-skos` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "多语翻译与本地化"
  code: "E06"
  provenance_strength: "external"
  provenance_legend:
    e06-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E06-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "多语翻译与本地化 全域"
      nodes:
        - "E06-01"
        - "E06-02"
        - "E06-03"
        - "E06-04"
        - "E06-05"
        - "E06-06"
        - "E06-07"
        - "E06-08"
        - "E06-09"
        - "E06-10"
        - "E06-11"
        - "E06-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-iso-8601"
        - "STD-mermaid"
        - "STD-oci-image"
        - "STD-rdf11"
        - "STD-rfc3339"
        - "STD-w3c-epub33"
        - "STD-w3c-skos"
        - "STD-w3c-tabular-data"
        - "STD-w3c-xml"
  nodes:
    - id: "E06-01"
      name: "术语库"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e06-anchor"
    - id: "E06-02"
      name: "风格指南"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E06-01"
      provenance:
        - "e06-anchor"
    - id: "E06-03"
      name: "字幕翻译"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E06-02"
      provenance:
        - "e06-anchor"
    - id: "E06-04"
      name: "配音对口型"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E06-03"
        - "E06-01"
      provenance:
        - "e06-anchor"
    - id: "E06-05"
      name: "游戏本地化"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E06-04"
        - "E06-02"
      provenance:
        - "e06-anchor"
    - id: "E06-06"
      name: "法律与医学翻译"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E06-05"
        - "E06-03"
      provenance:
        - "e06-anchor"
    - id: "E06-07"
      name: "文化适配"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E06-06"
        - "E06-04"
      provenance:
        - "e06-anchor"
    - id: "E06-08"
      name: "回译校验"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E06-07"
        - "E06-05"
      provenance:
        - "e06-anchor"
    - id: "E06-09"
      name: "译后编辑"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E06-08"
        - "E06-06"
      provenance:
        - "e06-anchor"
    - id: "E06-10"
      name: "多语排版"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E06-09"
        - "E06-07"
      provenance:
        - "e06-anchor"
    - id: "E06-11"
      name: "格式与时区"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E06-10"
        - "E06-08"
      provenance:
        - "e06-anchor"
    - id: "E06-12"
      name: "质量评估"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E06-11"
        - "E06-09"
      provenance:
        - "e06-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E06-04"
        - "E06-07"
        - "E06-01"
        - "E06-02"
        - "E06-05"
        - "E06-08"
        - "E06-11"
        - "E06-12"
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
        - "E06-12"
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
        - "E06-08"
        - "E06-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-iso-8601"
      name: "标准 · 日期时间（含 8601-2 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E06-03"
      provenance:
        - "std-catalog"
    - id: "STD-oci-image"
      name: "标准 · 镜像清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E06-03"
      provenance:
        - "std-catalog"
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-rfc3339"
      name: "标准 · 时间戳"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E06-11"
        - "STD-iso-8601"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E06-06"
        - "E06-09"
        - "E06-10"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-skos"
      name: "标准 · SKOS 词表"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E06-01"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E06-02"
        - "E06-05"
        - "E06-04"
        - "E06-07"
        - "E06-09"
        - "E06-10"
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
- 包外前置族（E06-00）不随包交付，装载方须自备领域基础。
