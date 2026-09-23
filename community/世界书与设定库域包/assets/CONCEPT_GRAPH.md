<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 世界书与设定库（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「世界书与设定库」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（世界书与设定库:M01）与收口模块（世界书与设定库:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 4 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（E03-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E03-01` | 条目切分 | P40 | — | e03-anchor |
| `E03-02` | 关键词与正则触发 | P60 | `E03-01` | e03-anchor |
| `E03-03` | 常驻条目设计 | P40 | `E03-02` | e03-anchor |
| `E03-04` | 层级与优先级 | P60 | `E03-03`、`E03-01` | e03-anchor |
| `E03-05` | 设定冲突检测 | P40 | `E03-04`、`E03-02` | e03-anchor |
| `E03-06` | 设定扩展联动 | P60 | `E03-05`、`E03-03` | e03-anchor |
| `E03-07` | 世界书体检 | P40 | `E03-06`、`E03-04` | e03-anchor |
| `E03-08` | Token 预算 | P60 | `E03-07`、`E03-05` | e03-anchor |
| `E03-09` | 多世界书合并 | P40 | `E03-08`、`E03-06` | e03-anchor |
| `E03-10` | 设定版本管理 | P60 | `E03-09`、`E03-07` | e03-anchor |
| `E03-11` | 导入导出规范 | P40 | `E03-10`、`E03-08` | e03-anchor |
| `E03-12` | 设定检索问答 | P60 | `E03-11`、`E03-09` | e03-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `E03-01`、`E03-04`、`E03-07`、`E03-10` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless） | P80 | `E03-12` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C） | P80 | `E03-03`、`E03-06`、`E03-09` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `E03-02`、`E03-05`、`E03-08`、`E03-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E03-条目切分` | `E03-01` |
| `E03-关键词与正则触发` | `E03-02` |
| `E03-常驻条目设计` | `E03-03` |
| `E03-层级与优先级` | `E03-04` |
| `E03-设定冲突检测` | `E03-05` |
| `E03-设定扩展联动` | `E03-06` |
| `E03-世界书体检` | `E03-07` |
| `E03-Token-预算` | `E03-08` |
| `E03-多世界书合并` | `E03-09` |
| `E03-设定版本管理` | `E03-10` |
| `E03-导入导出规范` | `E03-11` |
| `E03-设定检索问答` | `E03-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "世界书与设定库"
  code: "E03"
  provenance_strength: "external"
  provenance_legend:
    e03-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E03-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "世界书与设定库 全域"
      nodes:
        - "E03-01"
        - "E03-02"
        - "E03-03"
        - "E03-04"
        - "E03-05"
        - "E03-06"
        - "E03-07"
        - "E03-08"
        - "E03-09"
        - "E03-10"
        - "E03-11"
        - "E03-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "E03-01"
      name: "条目切分"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e03-anchor"
    - id: "E03-02"
      name: "关键词与正则触发"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E03-01"
      provenance:
        - "e03-anchor"
    - id: "E03-03"
      name: "常驻条目设计"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E03-02"
      provenance:
        - "e03-anchor"
    - id: "E03-04"
      name: "层级与优先级"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E03-03"
        - "E03-01"
      provenance:
        - "e03-anchor"
    - id: "E03-05"
      name: "设定冲突检测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E03-04"
        - "E03-02"
      provenance:
        - "e03-anchor"
    - id: "E03-06"
      name: "设定扩展联动"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E03-05"
        - "E03-03"
      provenance:
        - "e03-anchor"
    - id: "E03-07"
      name: "世界书体检"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E03-06"
        - "E03-04"
      provenance:
        - "e03-anchor"
    - id: "E03-08"
      name: "Token 预算"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E03-07"
        - "E03-05"
      provenance:
        - "e03-anchor"
    - id: "E03-09"
      name: "多世界书合并"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E03-08"
        - "E03-06"
      provenance:
        - "e03-anchor"
    - id: "E03-10"
      name: "设定版本管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E03-09"
        - "E03-07"
      provenance:
        - "e03-anchor"
    - id: "E03-11"
      name: "导入导出规范"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E03-10"
        - "E03-08"
      provenance:
        - "e03-anchor"
    - id: "E03-12"
      name: "设定检索问答"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E03-11"
        - "E03-09"
      provenance:
        - "e03-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E03-01"
        - "E03-04"
        - "E03-07"
        - "E03-10"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E03-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E03-03"
        - "E03-06"
        - "E03-09"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E03-02"
        - "E03-05"
        - "E03-08"
        - "E03-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E03-00）不随包交付，装载方须自备领域基础。
