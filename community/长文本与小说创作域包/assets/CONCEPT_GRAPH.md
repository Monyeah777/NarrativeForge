<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 长文本与小说创作（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「长文本与小说创作」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（长文本与小说创作:M01）与收口模块（长文本与小说创作:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 3 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（E04-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E04-01` | 长篇大纲 | P40 | — | e04-anchor |
| `E04-02` | 卷章结构 | P60 | `E04-01` | e04-anchor |
| `E04-03` | 伏笔回收 | P40 | `E04-02` | e04-anchor |
| `E04-04` | 节拍与张弛 | P60 | `E04-03`、`E04-01` | e04-anchor |
| `E04-05` | 视角管理 | P40 | `E04-04`、`E04-02` | e04-anchor |
| `E04-06` | 人物弧光 | P60 | `E04-05`、`E04-03` | e04-anchor |
| `E04-07` | 对话撰写 | P40 | `E04-06`、`E04-04` | e04-anchor |
| `E04-08` | 场景与氛围 | P60 | `E04-07`、`E04-05` | e04-anchor |
| `E04-09` | 文风 DNA | P40 | `E04-08`、`E04-06` | e04-anchor |
| `E04-10` | 续写与改写 | P60 | `E04-09`、`E04-07` | e04-anchor |
| `E04-11` | 一致性对账 | P40 | `E04-10`、`E04-08` | e04-anchor |
| `E04-12` | 连载节奏 | P60 | `E04-11`、`E04-09` | e04-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `E04-01`、`E04-04`、`E04-07`、`E04-10` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C） | P80 | `E04-03`、`E04-06`、`E04-09`、`E04-12` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `E04-02`、`E04-05`、`E04-08`、`E04-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E04-长篇大纲` | `E04-01` |
| `E04-卷章结构` | `E04-02` |
| `E04-伏笔回收` | `E04-03` |
| `E04-节拍与张弛` | `E04-04` |
| `E04-视角管理` | `E04-05` |
| `E04-人物弧光` | `E04-06` |
| `E04-对话撰写` | `E04-07` |
| `E04-场景与氛围` | `E04-08` |
| `E04-文风-DNA` | `E04-09` |
| `E04-续写与改写` | `E04-10` |
| `E04-一致性对账` | `E04-11` |
| `E04-连载节奏` | `E04-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "长文本与小说创作"
  code: "E04"
  provenance_strength: "external"
  provenance_legend:
    e04-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E04-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "长文本与小说创作 全域"
      nodes:
        - "E04-01"
        - "E04-02"
        - "E04-03"
        - "E04-04"
        - "E04-05"
        - "E04-06"
        - "E04-07"
        - "E04-08"
        - "E04-09"
        - "E04-10"
        - "E04-11"
        - "E04-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "E04-01"
      name: "长篇大纲"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e04-anchor"
    - id: "E04-02"
      name: "卷章结构"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E04-01"
      provenance:
        - "e04-anchor"
    - id: "E04-03"
      name: "伏笔回收"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E04-02"
      provenance:
        - "e04-anchor"
    - id: "E04-04"
      name: "节拍与张弛"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E04-03"
        - "E04-01"
      provenance:
        - "e04-anchor"
    - id: "E04-05"
      name: "视角管理"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E04-04"
        - "E04-02"
      provenance:
        - "e04-anchor"
    - id: "E04-06"
      name: "人物弧光"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E04-05"
        - "E04-03"
      provenance:
        - "e04-anchor"
    - id: "E04-07"
      name: "对话撰写"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E04-06"
        - "E04-04"
      provenance:
        - "e04-anchor"
    - id: "E04-08"
      name: "场景与氛围"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E04-07"
        - "E04-05"
      provenance:
        - "e04-anchor"
    - id: "E04-09"
      name: "文风 DNA"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E04-08"
        - "E04-06"
      provenance:
        - "e04-anchor"
    - id: "E04-10"
      name: "续写与改写"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E04-09"
        - "E04-07"
      provenance:
        - "e04-anchor"
    - id: "E04-11"
      name: "一致性对账"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E04-10"
        - "E04-08"
      provenance:
        - "e04-anchor"
    - id: "E04-12"
      name: "连载节奏"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E04-11"
        - "E04-09"
      provenance:
        - "e04-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E04-01"
        - "E04-04"
        - "E04-07"
        - "E04-10"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E04-03"
        - "E04-06"
        - "E04-09"
        - "E04-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E04-02"
        - "E04-05"
        - "E04-08"
        - "E04-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E04-00）不随包交付，装载方须自备领域基础。
