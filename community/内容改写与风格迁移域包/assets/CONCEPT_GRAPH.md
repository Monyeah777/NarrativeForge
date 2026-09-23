<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 内容改写与风格迁移（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「内容改写与风格迁移」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（内容改写与风格迁移:M01）与收口模块（内容改写与风格迁移:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 3 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（E05-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E05-01` | 降 AI 味 | P40 | — | e05-anchor |
| `E05-02` | 口语化改写 | P60 | `E05-01` | e05-anchor |
| `E05-03` | 学术润色 | P40 | `E05-02` | e05-anchor |
| `E05-04` | 营销文案 | P60 | `E05-03`、`E05-01` | e05-anchor |
| `E05-05` | 多版本 A/B | P40 | `E05-04`、`E05-02` | e05-anchor |
| `E05-06` | 摘要与扩写 | P60 | `E05-05`、`E05-03` | e05-anchor |
| `E05-07` | 敏感词替换 | P40 | `E05-06`、`E05-04` | e05-anchor |
| `E05-08` | 风格模仿 | P60 | `E05-07`、`E05-05` | e05-anchor |
| `E05-09` | 语体转换 | P40 | `E05-08`、`E05-06` | e05-anchor |
| `E05-10` | 标题党规避 | P60 | `E05-09`、`E05-07` | e05-anchor |
| `E05-11` | 字数控制 | P40 | `E05-10`、`E05-08` | e05-anchor |
| `E05-12` | 相似度检查 | P60 | `E05-11`、`E05-09` | e05-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `E05-01`、`E05-04`、`E05-07`、`E05-10` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C） | P80 | `E05-03`、`E05-06`、`E05-09`、`E05-12` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `E05-02`、`E05-05`、`E05-08`、`E05-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E05-降-AI-味` | `E05-01` |
| `E05-口语化改写` | `E05-02` |
| `E05-学术润色` | `E05-03` |
| `E05-营销文案` | `E05-04` |
| `E05-多版本-A/B` | `E05-05` |
| `E05-摘要与扩写` | `E05-06` |
| `E05-敏感词替换` | `E05-07` |
| `E05-风格模仿` | `E05-08` |
| `E05-语体转换` | `E05-09` |
| `E05-标题党规避` | `E05-10` |
| `E05-字数控制` | `E05-11` |
| `E05-相似度检查` | `E05-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "内容改写与风格迁移"
  code: "E05"
  provenance_strength: "external"
  provenance_legend:
    e05-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E05-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "内容改写与风格迁移 全域"
      nodes:
        - "E05-01"
        - "E05-02"
        - "E05-03"
        - "E05-04"
        - "E05-05"
        - "E05-06"
        - "E05-07"
        - "E05-08"
        - "E05-09"
        - "E05-10"
        - "E05-11"
        - "E05-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "E05-01"
      name: "降 AI 味"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e05-anchor"
    - id: "E05-02"
      name: "口语化改写"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E05-01"
      provenance:
        - "e05-anchor"
    - id: "E05-03"
      name: "学术润色"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E05-02"
      provenance:
        - "e05-anchor"
    - id: "E05-04"
      name: "营销文案"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E05-03"
        - "E05-01"
      provenance:
        - "e05-anchor"
    - id: "E05-05"
      name: "多版本 A/B"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E05-04"
        - "E05-02"
      provenance:
        - "e05-anchor"
    - id: "E05-06"
      name: "摘要与扩写"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E05-05"
        - "E05-03"
      provenance:
        - "e05-anchor"
    - id: "E05-07"
      name: "敏感词替换"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E05-06"
        - "E05-04"
      provenance:
        - "e05-anchor"
    - id: "E05-08"
      name: "风格模仿"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E05-07"
        - "E05-05"
      provenance:
        - "e05-anchor"
    - id: "E05-09"
      name: "语体转换"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E05-08"
        - "E05-06"
      provenance:
        - "e05-anchor"
    - id: "E05-10"
      name: "标题党规避"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E05-09"
        - "E05-07"
      provenance:
        - "e05-anchor"
    - id: "E05-11"
      name: "字数控制"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E05-10"
        - "E05-08"
      provenance:
        - "e05-anchor"
    - id: "E05-12"
      name: "相似度检查"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E05-11"
        - "E05-09"
      provenance:
        - "e05-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E05-01"
        - "E05-04"
        - "E05-07"
        - "E05-10"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E05-03"
        - "E05-06"
        - "E05-09"
        - "E05-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E05-02"
        - "E05-05"
        - "E05-08"
        - "E05-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E05-00）不随包交付，装载方须自备领域基础。
