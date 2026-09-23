<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 知识管理与检索增强（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「知识管理与检索增强」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（知识管理与检索增强:M01）与收口模块（知识管理与检索增强:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（E11-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E11-01` | 切片策略 | P40 | — | e11-anchor |
| `E11-02` | 向量化与嵌入 | P60 | `E11-01` | e11-anchor |
| `E11-03` | 混合检索 | P40 | `E11-02` | e11-anchor |
| `E11-04` | 结果重排 | P60 | `E11-03`、`E11-01` | e11-anchor |
| `E11-05` | 图谱构建 | P40 | `E11-04`、`E11-02` | e11-anchor |
| `E11-06` | 多跳问答 | P60 | `E11-05`、`E11-03` | e11-anchor |
| `E11-07` | 引用溯源 | P40 | `E11-06`、`E11-04` | e11-anchor |
| `E11-08` | 知识库更新 | P60 | `E11-07`、`E11-05` | e11-anchor |
| `E11-09` | 私有语料清洗 | P40 | `E11-08`、`E11-06` | e11-anchor |
| `E11-10` | 权限与保密 | P60 | `E11-09`、`E11-07` | e11-anchor |
| `E11-11` | 检索评测 | P40 | `E11-10`、`E11-08` | e11-anchor |
| `E11-12` | 失效知识治理 | P60 | `E11-11`、`E11-09` | e11-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E11-切片策略` | `E11-01` |
| `E11-向量化与嵌入` | `E11-02` |
| `E11-混合检索` | `E11-03` |
| `E11-结果重排` | `E11-04` |
| `E11-图谱构建` | `E11-05` |
| `E11-多跳问答` | `E11-06` |
| `E11-引用溯源` | `E11-07` |
| `E11-知识库更新` | `E11-08` |
| `E11-私有语料清洗` | `E11-09` |
| `E11-权限与保密` | `E11-10` |
| `E11-检索评测` | `E11-11` |
| `E11-失效知识治理` | `E11-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "知识管理与检索增强"
  code: "E11"
  provenance_strength: "external"
  provenance_legend:
    e11-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "E11-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "知识管理与检索增强 全域"
      nodes:
        - "E11-01"
        - "E11-02"
        - "E11-03"
        - "E11-04"
        - "E11-05"
        - "E11-06"
        - "E11-07"
        - "E11-08"
        - "E11-09"
        - "E11-10"
        - "E11-11"
        - "E11-12"
  nodes:
    - id: "E11-01"
      name: "切片策略"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e11-anchor"
    - id: "E11-02"
      name: "向量化与嵌入"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E11-01"
      provenance:
        - "e11-anchor"
    - id: "E11-03"
      name: "混合检索"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E11-02"
      provenance:
        - "e11-anchor"
    - id: "E11-04"
      name: "结果重排"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E11-03"
        - "E11-01"
      provenance:
        - "e11-anchor"
    - id: "E11-05"
      name: "图谱构建"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E11-04"
        - "E11-02"
      provenance:
        - "e11-anchor"
    - id: "E11-06"
      name: "多跳问答"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E11-05"
        - "E11-03"
      provenance:
        - "e11-anchor"
    - id: "E11-07"
      name: "引用溯源"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E11-06"
        - "E11-04"
      provenance:
        - "e11-anchor"
    - id: "E11-08"
      name: "知识库更新"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E11-07"
        - "E11-05"
      provenance:
        - "e11-anchor"
    - id: "E11-09"
      name: "私有语料清洗"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E11-08"
        - "E11-06"
      provenance:
        - "e11-anchor"
    - id: "E11-10"
      name: "权限与保密"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E11-09"
        - "E11-07"
      provenance:
        - "e11-anchor"
    - id: "E11-11"
      name: "检索评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E11-10"
        - "E11-08"
      provenance:
        - "e11-anchor"
    - id: "E11-12"
      name: "失效知识治理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E11-11"
        - "E11-09"
      provenance:
        - "e11-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E11-00）不随包交付，装载方须自备领域基础。
