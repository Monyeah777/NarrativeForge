<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 内容分发与社区运营（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「内容分发与社区运营」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（内容分发与社区运营:M01）与收口模块（内容分发与社区运营:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（E19-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E19-01` | 账号定位 | P40 | — | e19-anchor |
| `E19-02` | 选题日历 | P60 | `E19-01` | e19-anchor |
| `E19-03` | 平台适配改写 | P40 | `E19-02` | e19-anchor |
| `E19-04` | 标签与话题 | P60 | `E19-03`、`E19-01` | e19-anchor |
| `E19-05` | 发布节奏 | P40 | `E19-04`、`E19-02` | e19-anchor |
| `E19-06` | 评论互动 | P60 | `E19-05`、`E19-03` | e19-anchor |
| `E19-07` | 舆情与风险 | P40 | `E19-06`、`E19-04` | e19-anchor |
| `E19-08` | 社群分层 | P60 | `E19-07`、`E19-05` | e19-anchor |
| `E19-09` | 种子用户 | P40 | `E19-08`、`E19-06` | e19-anchor |
| `E19-10` | 数据复盘 | P60 | `E19-09`、`E19-07` | e19-anchor |
| `E19-11` | 达人合作 | P40 | `E19-10`、`E19-08` | e19-anchor |
| `E19-12` | 违规申诉 | P60 | `E19-11`、`E19-09` | e19-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E19-账号定位` | `E19-01` |
| `E19-选题日历` | `E19-02` |
| `E19-平台适配改写` | `E19-03` |
| `E19-标签与话题` | `E19-04` |
| `E19-发布节奏` | `E19-05` |
| `E19-评论互动` | `E19-06` |
| `E19-舆情与风险` | `E19-07` |
| `E19-社群分层` | `E19-08` |
| `E19-种子用户` | `E19-09` |
| `E19-数据复盘` | `E19-10` |
| `E19-达人合作` | `E19-11` |
| `E19-违规申诉` | `E19-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "内容分发与社区运营"
  code: "E19"
  provenance_strength: "external"
  provenance_legend:
    e19-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "E19-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "内容分发与社区运营 全域"
      nodes:
        - "E19-01"
        - "E19-02"
        - "E19-03"
        - "E19-04"
        - "E19-05"
        - "E19-06"
        - "E19-07"
        - "E19-08"
        - "E19-09"
        - "E19-10"
        - "E19-11"
        - "E19-12"
  nodes:
    - id: "E19-01"
      name: "账号定位"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e19-anchor"
    - id: "E19-02"
      name: "选题日历"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E19-01"
      provenance:
        - "e19-anchor"
    - id: "E19-03"
      name: "平台适配改写"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E19-02"
      provenance:
        - "e19-anchor"
    - id: "E19-04"
      name: "标签与话题"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E19-03"
        - "E19-01"
      provenance:
        - "e19-anchor"
    - id: "E19-05"
      name: "发布节奏"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E19-04"
        - "E19-02"
      provenance:
        - "e19-anchor"
    - id: "E19-06"
      name: "评论互动"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E19-05"
        - "E19-03"
      provenance:
        - "e19-anchor"
    - id: "E19-07"
      name: "舆情与风险"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E19-06"
        - "E19-04"
      provenance:
        - "e19-anchor"
    - id: "E19-08"
      name: "社群分层"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E19-07"
        - "E19-05"
      provenance:
        - "e19-anchor"
    - id: "E19-09"
      name: "种子用户"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E19-08"
        - "E19-06"
      provenance:
        - "e19-anchor"
    - id: "E19-10"
      name: "数据复盘"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E19-09"
        - "E19-07"
      provenance:
        - "e19-anchor"
    - id: "E19-11"
      name: "达人合作"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E19-10"
        - "E19-08"
      provenance:
        - "e19-anchor"
    - id: "E19-12"
      name: "违规申诉"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E19-11"
        - "E19-09"
      provenance:
        - "e19-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E19-00）不随包交付，装载方须自备领域基础。
