<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 数据分析与表格理解（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「数据分析与表格理解」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（数据分析与表格理解:M01）与收口模块（数据分析与表格理解:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（B11-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B11-01` | 表格问答 | P40 | — | b11-anchor |
| `B11-02` | 多表关联推理 | P60 | `B11-01` | b11-anchor |
| `B11-03` | 图表理解与生成 | P40 | — | b11-anchor |
| `B11-04` | 数据清洗建议 | P60 | — | b11-anchor |
| `B11-05` | 指标口径定义 | P40 | — | b11-anchor |
| `B11-06` | SQL 与自然语言互译 | P60 | `B11-02` | b11-anchor |
| `B11-07` | 异常值识别 | P40 | `B11-04` | b11-anchor |
| `B11-08` | 趋势与归因分析 | P60 | `B11-05` | b11-anchor |
| `B11-09` | BI 看板配置 | P40 | — | b11-anchor |
| `B11-10` | 数据故事讲述 | P60 | `B11-03`、`B11-08`、`B11-09` | b11-anchor |
| `B11-11` | 分析结论可解释性 | P40 | `B11-07`、`B11-06` | b11-anchor |
| `B11-12` | 数据权限与敏感 | P60 | `B11-11` | b11-anchor |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `B11-04`、`B11-06`、`B11-07` | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema） | P80 | `B11-10` | std-catalog |
| `STD-nist-800-188` | 标准 · SP 800-188 去标识化（NIST） | P80 | `B11-12` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation） | P80 | `B11-02` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega） | P80 | `B11-03`、`B11-09` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `B11-01`、`B11-05`、`B11-08`、`B11-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B11-表格问答` | `B11-01` |
| `B11-多表关联推理` | `B11-02` |
| `B11-图表理解与生成` | `B11-03` |
| `B11-数据清洗建议` | `B11-04` |
| `B11-指标口径定义` | `B11-05` |
| `B11-SQL-与自然语言互译` | `B11-06` |
| `B11-异常值识别` | `B11-07` |
| `B11-趋势与归因分析` | `B11-08` |
| `B11-BI-看板配置` | `B11-09` |
| `B11-数据故事讲述` | `B11-10` |
| `B11-分析结论可解释性` | `B11-11` |
| `B11-数据权限与敏感` | `B11-12` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-nist-800-188` | `STD-nist-800-188` |
| `std-onnx` | `STD-onnx` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "数据分析与表格理解"
  code: "B11"
  provenance_strength: "external"
  provenance_legend:
    b11-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B11-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "数据分析与表格理解 全域"
      nodes:
        - "B11-01"
        - "B11-02"
        - "B11-03"
        - "B11-04"
        - "B11-05"
        - "B11-06"
        - "B11-07"
        - "B11-08"
        - "B11-09"
        - "B11-10"
        - "B11-11"
        - "B11-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-frictionless-table"
        - "STD-ietf-json-schema"
        - "STD-nist-800-188"
        - "STD-onnx"
        - "STD-vega-lite"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "B11-01"
      name: "表格问答"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b11-anchor"
    - id: "B11-02"
      name: "多表关联推理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B11-01"
      provenance:
        - "b11-anchor"
    - id: "B11-03"
      name: "图表理解与生成"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b11-anchor"
    - id: "B11-04"
      name: "数据清洗建议"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b11-anchor"
    - id: "B11-05"
      name: "指标口径定义"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b11-anchor"
    - id: "B11-06"
      name: "SQL 与自然语言互译"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B11-02"
      provenance:
        - "b11-anchor"
    - id: "B11-07"
      name: "异常值识别"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B11-04"
      provenance:
        - "b11-anchor"
    - id: "B11-08"
      name: "趋势与归因分析"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B11-05"
      provenance:
        - "b11-anchor"
    - id: "B11-09"
      name: "BI 看板配置"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b11-anchor"
    - id: "B11-10"
      name: "数据故事讲述"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B11-03"
        - "B11-08"
        - "B11-09"
      provenance:
        - "b11-anchor"
    - id: "B11-11"
      name: "分析结论可解释性"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B11-07"
        - "B11-06"
      provenance:
        - "b11-anchor"
    - id: "B11-12"
      name: "数据权限与敏感"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B11-11"
      provenance:
        - "b11-anchor"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B11-04"
        - "B11-06"
        - "B11-07"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B11-10"
      provenance:
        - "std-catalog"
    - id: "STD-nist-800-188"
      name: "标准 · SP 800-188 去标识化"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B11-12"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B11-02"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B11-03"
        - "B11-09"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B11-01"
        - "B11-05"
        - "B11-08"
        - "B11-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B11-00）不随包交付，装载方须自备领域基础。
