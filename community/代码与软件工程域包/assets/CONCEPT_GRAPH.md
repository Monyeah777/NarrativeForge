<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 代码与软件工程（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「代码与软件工程」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（代码与软件工程:M01）与收口模块（代码与软件工程:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（E13-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E13-01` | 需求转代码 | P40 | — | e13-anchor |
| `E13-02` | 补全与重构 | P60 | `E13-01` | e13-anchor |
| `E13-03` | 单测生成 | P40 | `E13-02` | e13-anchor |
| `E13-04` | 代码评审 | P60 | `E13-03`、`E13-01` | e13-anchor |
| `E13-05` | 缺陷定位 | P40 | `E13-04`、`E13-02` | e13-anchor |
| `E13-06` | 依赖升级 | P60 | `E13-05`、`E13-03` | e13-anchor |
| `E13-07` | 文档生成 | P40 | `E13-06`、`E13-04` | e13-anchor |
| `E13-08` | 数据管道与 SQL | P60 | `E13-07`、`E13-05` | e13-anchor |
| `E13-09` | 脚手架与模板 | P40 | `E13-08`、`E13-06` | e13-anchor |
| `E13-10` | 安全扫描修复 | P60 | `E13-09`、`E13-07` | e13-anchor |
| `E13-11` | 多仓协作 | P40 | `E13-10`、`E13-08` | e13-anchor |
| `E13-12` | 研发度量 | P60 | `E13-11`、`E13-09` | e13-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E13-需求转代码` | `E13-01` |
| `E13-补全与重构` | `E13-02` |
| `E13-单测生成` | `E13-03` |
| `E13-代码评审` | `E13-04` |
| `E13-缺陷定位` | `E13-05` |
| `E13-依赖升级` | `E13-06` |
| `E13-文档生成` | `E13-07` |
| `E13-数据管道与-SQL` | `E13-08` |
| `E13-脚手架与模板` | `E13-09` |
| `E13-安全扫描修复` | `E13-10` |
| `E13-多仓协作` | `E13-11` |
| `E13-研发度量` | `E13-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "代码与软件工程"
  code: "E13"
  provenance_strength: "external"
  provenance_legend:
    e13-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "E13-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "代码与软件工程 全域"
      nodes:
        - "E13-01"
        - "E13-02"
        - "E13-03"
        - "E13-04"
        - "E13-05"
        - "E13-06"
        - "E13-07"
        - "E13-08"
        - "E13-09"
        - "E13-10"
        - "E13-11"
        - "E13-12"
  nodes:
    - id: "E13-01"
      name: "需求转代码"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e13-anchor"
    - id: "E13-02"
      name: "补全与重构"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E13-01"
      provenance:
        - "e13-anchor"
    - id: "E13-03"
      name: "单测生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E13-02"
      provenance:
        - "e13-anchor"
    - id: "E13-04"
      name: "代码评审"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E13-03"
        - "E13-01"
      provenance:
        - "e13-anchor"
    - id: "E13-05"
      name: "缺陷定位"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E13-04"
        - "E13-02"
      provenance:
        - "e13-anchor"
    - id: "E13-06"
      name: "依赖升级"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E13-05"
        - "E13-03"
      provenance:
        - "e13-anchor"
    - id: "E13-07"
      name: "文档生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E13-06"
        - "E13-04"
      provenance:
        - "e13-anchor"
    - id: "E13-08"
      name: "数据管道与 SQL"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E13-07"
        - "E13-05"
      provenance:
        - "e13-anchor"
    - id: "E13-09"
      name: "脚手架与模板"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E13-08"
        - "E13-06"
      provenance:
        - "e13-anchor"
    - id: "E13-10"
      name: "安全扫描修复"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E13-09"
        - "E13-07"
      provenance:
        - "e13-anchor"
    - id: "E13-11"
      name: "多仓协作"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E13-10"
        - "E13-08"
      provenance:
        - "e13-anchor"
    - id: "E13-12"
      name: "研发度量"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E13-11"
        - "E13-09"
      provenance:
        - "e13-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E13-00）不随包交付，装载方须自备领域基础。
