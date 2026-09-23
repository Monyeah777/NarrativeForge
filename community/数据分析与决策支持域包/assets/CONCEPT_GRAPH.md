<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 数据分析与决策支持（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「数据分析与决策支持」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（数据分析与决策支持:M01）与收口模块（数据分析与决策支持:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 12 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（E14-00 领域通用前置）；节点 24 · 边 49 · 密度 2.0417。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E14-01` | 指标口径 | P40 | — | e14-anchor |
| `E14-02` | 取数语句生成 | P60 | `E14-01` | e14-anchor |
| `E14-03` | 看板搭建 | P40 | `E14-02` | e14-anchor |
| `E14-04` | 异常归因 | P60 | `E14-03`、`E14-01` | e14-anchor |
| `E14-05` | 预测建模 | P40 | `E14-04`、`E14-02` | e14-anchor |
| `E14-06` | 实验设计 | P60 | `E14-05`、`E14-03` | e14-anchor |
| `E14-07` | 自然语言取数 | P40 | `E14-06`、`E14-04` | e14-anchor |
| `E14-08` | 报表自动化 | P60 | `E14-07`、`E14-05` | e14-anchor |
| `E14-09` | 图表规范 | P40 | `E14-08`、`E14-06` | e14-anchor |
| `E14-10` | 假设检验 | P60 | `E14-09`、`E14-07` | e14-anchor |
| `E14-11` | 决策备忘 | P40 | `E14-10`、`E14-08` | e14-anchor |
| `E14-12` | 数据质量 | P60 | `E14-11`、`E14-09` | e14-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `E14-01` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `E14-01`、`E14-07`、`E14-10`、`E14-02`、`E14-05`、`E14-12` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `E14-04`、`E14-12`、`STD-frictionless-package` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `E14-06`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `E14-11` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `E14-03`、`E14-09`、`E14-04`、`E14-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C｜form｜实测 ✓） | P80 | `E14-06`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `E14-02`、`E14-05`、`E14-08`、`E14-11`、`E14-03`、`E14-07`、`E14-09`、`E14-10`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E14-指标口径` | `E14-01` |
| `E14-取数语句生成` | `E14-02` |
| `E14-看板搭建` | `E14-03` |
| `E14-异常归因` | `E14-04` |
| `E14-预测建模` | `E14-05` |
| `E14-实验设计` | `E14-06` |
| `E14-自然语言取数` | `E14-07` |
| `E14-报表自动化` | `E14-08` |
| `E14-图表规范` | `E14-09` |
| `E14-假设检验` | `E14-10` |
| `E14-决策备忘` | `E14-11` |
| `E14-数据质量` | `E14-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "数据分析与决策支持"
  code: "E14"
  provenance_strength: "external"
  provenance_legend:
    e14-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E14-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "数据分析与决策支持 全域"
      nodes:
        - "E14-01"
        - "E14-02"
        - "E14-03"
        - "E14-04"
        - "E14-05"
        - "E14-06"
        - "E14-07"
        - "E14-08"
        - "E14-09"
        - "E14-10"
        - "E14-11"
        - "E14-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-vega-lite"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
        - "STD-w3c-xml"
  nodes:
    - id: "E14-01"
      name: "指标口径"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e14-anchor"
    - id: "E14-02"
      name: "取数语句生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E14-01"
      provenance:
        - "e14-anchor"
    - id: "E14-03"
      name: "看板搭建"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E14-02"
      provenance:
        - "e14-anchor"
    - id: "E14-04"
      name: "异常归因"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E14-03"
        - "E14-01"
      provenance:
        - "e14-anchor"
    - id: "E14-05"
      name: "预测建模"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E14-04"
        - "E14-02"
      provenance:
        - "e14-anchor"
    - id: "E14-06"
      name: "实验设计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E14-05"
        - "E14-03"
      provenance:
        - "e14-anchor"
    - id: "E14-07"
      name: "自然语言取数"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E14-06"
        - "E14-04"
      provenance:
        - "e14-anchor"
    - id: "E14-08"
      name: "报表自动化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E14-07"
        - "E14-05"
      provenance:
        - "e14-anchor"
    - id: "E14-09"
      name: "图表规范"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E14-08"
        - "E14-06"
      provenance:
        - "e14-anchor"
    - id: "E14-10"
      name: "假设检验"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E14-09"
        - "E14-07"
      provenance:
        - "e14-anchor"
    - id: "E14-11"
      name: "决策备忘"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E14-10"
        - "E14-08"
      provenance:
        - "e14-anchor"
    - id: "E14-12"
      name: "数据质量"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E14-11"
        - "E14-09"
      provenance:
        - "e14-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E14-01"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E14-01"
        - "E14-07"
        - "E14-10"
        - "E14-02"
        - "E14-05"
        - "E14-12"
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
        - "E14-04"
        - "E14-12"
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
        - "E14-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E14-11"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E14-03"
        - "E14-09"
        - "E14-04"
        - "E14-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E14-06"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E14-02"
        - "E14-05"
        - "E14-08"
        - "E14-11"
        - "E14-03"
        - "E14-07"
        - "E14-09"
        - "E14-10"
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
- 包外前置族（E14-00）不随包交付，装载方须自备领域基础。
