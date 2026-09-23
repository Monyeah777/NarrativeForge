<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 个人助理与日常生活（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「个人助理与日常生活」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（个人助理与日常生活:M01）与收口模块（个人助理与日常生活:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 3 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（E16-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E16-01` | 日程与提醒 | P40 | — | e16-anchor |
| `E16-02` | 邮件处理 | P60 | `E16-01` | e16-anchor |
| `E16-03` | 会议纪要与待办 | P40 | `E16-02` | e16-anchor |
| `E16-04` | 差旅规划 | P60 | `E16-03`、`E16-01` | e16-anchor |
| `E16-05` | 家庭事务 | P40 | `E16-04`、`E16-02` | e16-anchor |
| `E16-06` | 购物决策 | P60 | `E16-05`、`E16-03` | e16-anchor |
| `E16-07` | 习惯打卡 | P40 | `E16-06`、`E16-04` | e16-anchor |
| `E16-08` | 记账与理财 | P60 | `E16-07`、`E16-05` | e16-anchor |
| `E16-09` | 订阅摘要 | P40 | `E16-08`、`E16-06` | e16-anchor |
| `E16-10` | 家务与装修计划 | P60 | `E16-09`、`E16-07` | e16-anchor |
| `E16-11` | 社交回复草稿 | P40 | `E16-10`、`E16-08` | e16-anchor |
| `E16-12` | 个人知识沉淀 | P60 | `E16-11`、`E16-09` | e16-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `E16-01`、`E16-04`、`E16-07`、`E16-10` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C） | P80 | `E16-03`、`E16-06`、`E16-09`、`E16-12` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `E16-02`、`E16-05`、`E16-08`、`E16-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E16-日程与提醒` | `E16-01` |
| `E16-邮件处理` | `E16-02` |
| `E16-会议纪要与待办` | `E16-03` |
| `E16-差旅规划` | `E16-04` |
| `E16-家庭事务` | `E16-05` |
| `E16-购物决策` | `E16-06` |
| `E16-习惯打卡` | `E16-07` |
| `E16-记账与理财` | `E16-08` |
| `E16-订阅摘要` | `E16-09` |
| `E16-家务与装修计划` | `E16-10` |
| `E16-社交回复草稿` | `E16-11` |
| `E16-个人知识沉淀` | `E16-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "个人助理与日常生活"
  code: "E16"
  provenance_strength: "external"
  provenance_legend:
    e16-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E16-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "个人助理与日常生活 全域"
      nodes:
        - "E16-01"
        - "E16-02"
        - "E16-03"
        - "E16-04"
        - "E16-05"
        - "E16-06"
        - "E16-07"
        - "E16-08"
        - "E16-09"
        - "E16-10"
        - "E16-11"
        - "E16-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "E16-01"
      name: "日程与提醒"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e16-anchor"
    - id: "E16-02"
      name: "邮件处理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E16-01"
      provenance:
        - "e16-anchor"
    - id: "E16-03"
      name: "会议纪要与待办"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E16-02"
      provenance:
        - "e16-anchor"
    - id: "E16-04"
      name: "差旅规划"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E16-03"
        - "E16-01"
      provenance:
        - "e16-anchor"
    - id: "E16-05"
      name: "家庭事务"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E16-04"
        - "E16-02"
      provenance:
        - "e16-anchor"
    - id: "E16-06"
      name: "购物决策"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E16-05"
        - "E16-03"
      provenance:
        - "e16-anchor"
    - id: "E16-07"
      name: "习惯打卡"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E16-06"
        - "E16-04"
      provenance:
        - "e16-anchor"
    - id: "E16-08"
      name: "记账与理财"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E16-07"
        - "E16-05"
      provenance:
        - "e16-anchor"
    - id: "E16-09"
      name: "订阅摘要"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E16-08"
        - "E16-06"
      provenance:
        - "e16-anchor"
    - id: "E16-10"
      name: "家务与装修计划"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E16-09"
        - "E16-07"
      provenance:
        - "e16-anchor"
    - id: "E16-11"
      name: "社交回复草稿"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E16-10"
        - "E16-08"
      provenance:
        - "e16-anchor"
    - id: "E16-12"
      name: "个人知识沉淀"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E16-11"
        - "E16-09"
      provenance:
        - "e16-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E16-01"
        - "E16-04"
        - "E16-07"
        - "E16-10"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E16-03"
        - "E16-06"
        - "E16-09"
        - "E16-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E16-02"
        - "E16-05"
        - "E16-08"
        - "E16-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E16-00）不随包交付，装载方须自备领域基础。
