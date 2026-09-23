<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+金融投研与风控（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+金融投研与风控」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI金融投研与风控:M01）与收口模块（AI金融投研与风控:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（D04-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D04-01` | 财报解析与摘要 | P40 | — | d04-anchor |
| `D04-02` | 研报生成 | P60 | `D04-01` | d04-anchor |
| `D04-03` | 估值建模 | P40 | `D04-02` | d04-anchor |
| `D04-04` | 行业研究 | P60 | `D04-03`、`D04-01` | d04-anchor |
| `D04-05` | 舆情与事件驱动 | P40 | `D04-04`、`D04-02` | d04-anchor |
| `D04-06` | 风控规则与评分 | P60 | `D04-05`、`D04-03` | d04-anchor |
| `D04-07` | 反洗钱 | P40 | `D04-06`、`D04-04` | d04-anchor |
| `D04-08` | 合规审查 | P60 | `D04-07`、`D04-05` | d04-anchor |
| `D04-09` | 投顾话术合规 | P40 | `D04-08`、`D04-06` | d04-anchor |
| `D04-10` | 金融问答 | P60 | `D04-09`、`D04-07` | d04-anchor |
| `D04-11` | 市场数据分析 | P40 | `D04-10`、`D04-08` | d04-anchor |
| `D04-12` | 披露与免责 | P60 | `D04-11`、`D04-09` | d04-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D04-财报解析与摘要` | `D04-01` |
| `D04-研报生成` | `D04-02` |
| `D04-估值建模` | `D04-03` |
| `D04-行业研究` | `D04-04` |
| `D04-舆情与事件驱动` | `D04-05` |
| `D04-风控规则与评分` | `D04-06` |
| `D04-反洗钱` | `D04-07` |
| `D04-合规审查` | `D04-08` |
| `D04-投顾话术合规` | `D04-09` |
| `D04-金融问答` | `D04-10` |
| `D04-市场数据分析` | `D04-11` |
| `D04-披露与免责` | `D04-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+金融投研与风控"
  code: "D04"
  provenance_strength: "external"
  provenance_legend:
    d04-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "D04-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+金融投研与风控 全域"
      nodes:
        - "D04-01"
        - "D04-02"
        - "D04-03"
        - "D04-04"
        - "D04-05"
        - "D04-06"
        - "D04-07"
        - "D04-08"
        - "D04-09"
        - "D04-10"
        - "D04-11"
        - "D04-12"
  nodes:
    - id: "D04-01"
      name: "财报解析与摘要"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d04-anchor"
    - id: "D04-02"
      name: "研报生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D04-01"
      provenance:
        - "d04-anchor"
    - id: "D04-03"
      name: "估值建模"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D04-02"
      provenance:
        - "d04-anchor"
    - id: "D04-04"
      name: "行业研究"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D04-03"
        - "D04-01"
      provenance:
        - "d04-anchor"
    - id: "D04-05"
      name: "舆情与事件驱动"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D04-04"
        - "D04-02"
      provenance:
        - "d04-anchor"
    - id: "D04-06"
      name: "风控规则与评分"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D04-05"
        - "D04-03"
      provenance:
        - "d04-anchor"
    - id: "D04-07"
      name: "反洗钱"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D04-06"
        - "D04-04"
      provenance:
        - "d04-anchor"
    - id: "D04-08"
      name: "合规审查"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D04-07"
        - "D04-05"
      provenance:
        - "d04-anchor"
    - id: "D04-09"
      name: "投顾话术合规"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D04-08"
        - "D04-06"
      provenance:
        - "d04-anchor"
    - id: "D04-10"
      name: "金融问答"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D04-09"
        - "D04-07"
      provenance:
        - "d04-anchor"
    - id: "D04-11"
      name: "市场数据分析"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D04-10"
        - "D04-08"
      provenance:
        - "d04-anchor"
    - id: "D04-12"
      name: "披露与免责"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D04-11"
        - "D04-09"
      provenance:
        - "d04-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D04-00）不随包交付，装载方须自备领域基础。
