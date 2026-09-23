<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 搜索与信息聚合（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「搜索与信息聚合」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（搜索与信息聚合:M01）与收口模块（搜索与信息聚合:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（E17-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E17-01` | 查询理解 | P40 | — | e17-anchor |
| `E17-02` | 多源聚合 | P60 | `E17-01` | e17-anchor |
| `E17-03` | 结果去重 | P40 | `E17-02` | e17-anchor |
| `E17-04` | 时效判定 | P60 | `E17-03`、`E17-01` | e17-anchor |
| `E17-05` | 信源可信度 | P40 | `E17-04`、`E17-02` | e17-anchor |
| `E17-06` | 快讯生成 | P60 | `E17-05`、`E17-03` | e17-anchor |
| `E17-07` | 监控与预警 | P40 | `E17-06`、`E17-04` | e17-anchor |
| `E17-08` | 订阅推送 | P60 | `E17-07`、`E17-05` | e17-anchor |
| `E17-09` | 比价与选型 | P40 | `E17-08`、`E17-06` | e17-anchor |
| `E17-10` | 问答式搜索 | P60 | `E17-09`、`E17-07` | e17-anchor |
| `E17-11` | 垂直检索 | P40 | `E17-10`、`E17-08` | e17-anchor |
| `E17-12` | 内容抽取清洗 | P60 | `E17-11`、`E17-09` | e17-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E17-查询理解` | `E17-01` |
| `E17-多源聚合` | `E17-02` |
| `E17-结果去重` | `E17-03` |
| `E17-时效判定` | `E17-04` |
| `E17-信源可信度` | `E17-05` |
| `E17-快讯生成` | `E17-06` |
| `E17-监控与预警` | `E17-07` |
| `E17-订阅推送` | `E17-08` |
| `E17-比价与选型` | `E17-09` |
| `E17-问答式搜索` | `E17-10` |
| `E17-垂直检索` | `E17-11` |
| `E17-内容抽取清洗` | `E17-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "搜索与信息聚合"
  code: "E17"
  provenance_strength: "external"
  provenance_legend:
    e17-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "E17-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "搜索与信息聚合 全域"
      nodes:
        - "E17-01"
        - "E17-02"
        - "E17-03"
        - "E17-04"
        - "E17-05"
        - "E17-06"
        - "E17-07"
        - "E17-08"
        - "E17-09"
        - "E17-10"
        - "E17-11"
        - "E17-12"
  nodes:
    - id: "E17-01"
      name: "查询理解"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e17-anchor"
    - id: "E17-02"
      name: "多源聚合"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E17-01"
      provenance:
        - "e17-anchor"
    - id: "E17-03"
      name: "结果去重"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E17-02"
      provenance:
        - "e17-anchor"
    - id: "E17-04"
      name: "时效判定"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E17-03"
        - "E17-01"
      provenance:
        - "e17-anchor"
    - id: "E17-05"
      name: "信源可信度"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E17-04"
        - "E17-02"
      provenance:
        - "e17-anchor"
    - id: "E17-06"
      name: "快讯生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E17-05"
        - "E17-03"
      provenance:
        - "e17-anchor"
    - id: "E17-07"
      name: "监控与预警"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E17-06"
        - "E17-04"
      provenance:
        - "e17-anchor"
    - id: "E17-08"
      name: "订阅推送"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E17-07"
        - "E17-05"
      provenance:
        - "e17-anchor"
    - id: "E17-09"
      name: "比价与选型"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E17-08"
        - "E17-06"
      provenance:
        - "e17-anchor"
    - id: "E17-10"
      name: "问答式搜索"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E17-09"
        - "E17-07"
      provenance:
        - "e17-anchor"
    - id: "E17-11"
      name: "垂直检索"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E17-10"
        - "E17-08"
      provenance:
        - "e17-anchor"
    - id: "E17-12"
      name: "内容抽取清洗"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E17-11"
        - "E17-09"
      provenance:
        - "e17-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E17-00）不随包交付，装载方须自备领域基础。
