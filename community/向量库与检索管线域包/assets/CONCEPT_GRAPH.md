<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 向量库与检索管线（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「向量库与检索管线」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（向量库与检索管线:M01）与收口模块（向量库与检索管线:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（C15-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C15-01` | 索引与分片 | P40 | — | c15-anchor |
| `C15-02` | ANN 算法选型 | P60 | `C15-01` | c15-anchor |
| `C15-03` | 元数据过滤 | P40 | `C15-02` | c15-anchor |
| `C15-04` | 混合检索权重 | P60 | `C15-03`、`C15-01` | c15-anchor |
| `C15-05` | 增量更新 | P40 | `C15-04`、`C15-02` | c15-anchor |
| `C15-06` | 多租户隔离 | P60 | `C15-05`、`C15-03` | c15-anchor |
| `C15-07` | 召回延迟优化 | P40 | `C15-06`、`C15-04` | c15-anchor |
| `C15-08` | 重建与迁移 | P60 | `C15-07`、`C15-05` | c15-anchor |
| `C15-09` | 检索评测 | P40 | `C15-08`、`C15-06` | c15-anchor |
| `C15-10` | 权限与脱敏 | P60 | `C15-09`、`C15-07` | c15-anchor |
| `C15-11` | 容量规划 | P40 | `C15-10`、`C15-08` | c15-anchor |
| `C15-12` | 检索可观测性 | P60 | `C15-11`、`C15-09` | c15-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C15-索引与分片` | `C15-01` |
| `C15-ANN-算法选型` | `C15-02` |
| `C15-元数据过滤` | `C15-03` |
| `C15-混合检索权重` | `C15-04` |
| `C15-增量更新` | `C15-05` |
| `C15-多租户隔离` | `C15-06` |
| `C15-召回延迟优化` | `C15-07` |
| `C15-重建与迁移` | `C15-08` |
| `C15-检索评测` | `C15-09` |
| `C15-权限与脱敏` | `C15-10` |
| `C15-容量规划` | `C15-11` |
| `C15-检索可观测性` | `C15-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "向量库与检索管线"
  code: "C15"
  provenance_strength: "external"
  provenance_legend:
    c15-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "C15-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "向量库与检索管线 全域"
      nodes:
        - "C15-01"
        - "C15-02"
        - "C15-03"
        - "C15-04"
        - "C15-05"
        - "C15-06"
        - "C15-07"
        - "C15-08"
        - "C15-09"
        - "C15-10"
        - "C15-11"
        - "C15-12"
  nodes:
    - id: "C15-01"
      name: "索引与分片"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c15-anchor"
    - id: "C15-02"
      name: "ANN 算法选型"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C15-01"
      provenance:
        - "c15-anchor"
    - id: "C15-03"
      name: "元数据过滤"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C15-02"
      provenance:
        - "c15-anchor"
    - id: "C15-04"
      name: "混合检索权重"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C15-03"
        - "C15-01"
      provenance:
        - "c15-anchor"
    - id: "C15-05"
      name: "增量更新"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C15-04"
        - "C15-02"
      provenance:
        - "c15-anchor"
    - id: "C15-06"
      name: "多租户隔离"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C15-05"
        - "C15-03"
      provenance:
        - "c15-anchor"
    - id: "C15-07"
      name: "召回延迟优化"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C15-06"
        - "C15-04"
      provenance:
        - "c15-anchor"
    - id: "C15-08"
      name: "重建与迁移"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C15-07"
        - "C15-05"
      provenance:
        - "c15-anchor"
    - id: "C15-09"
      name: "检索评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C15-08"
        - "C15-06"
      provenance:
        - "c15-anchor"
    - id: "C15-10"
      name: "权限与脱敏"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C15-09"
        - "C15-07"
      provenance:
        - "c15-anchor"
    - id: "C15-11"
      name: "容量规划"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C15-10"
        - "C15-08"
      provenance:
        - "c15-anchor"
    - id: "C15-12"
      name: "检索可观测性"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C15-11"
        - "C15-09"
      provenance:
        - "c15-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C15-00）不随包交付，装载方须自备领域基础。
