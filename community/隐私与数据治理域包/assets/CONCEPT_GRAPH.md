<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 隐私与数据治理（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「隐私与数据治理」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（隐私与数据治理:M01）与收口模块（隐私与数据治理:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（F03-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `F03-01` | 最小必要采集 | P40 | — | f03-anchor |
| `F03-02` | 脱敏与去标识 | P60 | `F03-01` | f03-anchor |
| `F03-03` | 差分隐私 | P40 | `F03-02` | f03-anchor |
| `F03-04` | 联邦学习 | P60 | `F03-03`、`F03-01` | f03-anchor |
| `F03-05` | 数据分级分类 | P40 | `F03-04`、`F03-02` | f03-anchor |
| `F03-06` | 访问控制 | P60 | `F03-05`、`F03-03` | f03-anchor |
| `F03-07` | 数据血缘 | P40 | `F03-06`、`F03-04` | f03-anchor |
| `F03-08` | 生命周期销毁 | P60 | `F03-07`、`F03-05` | f03-anchor |
| `F03-09` | 第三方共享审查 | P40 | `F03-08`、`F03-06` | f03-anchor |
| `F03-10` | 用户权利响应 | P60 | `F03-09`、`F03-07` | f03-anchor |
| `F03-11` | 匿名化评估 | P40 | `F03-10`、`F03-08` | f03-anchor |
| `F03-12` | 隐私计算 | P60 | `F03-11`、`F03-09` | f03-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `F03-最小必要采集` | `F03-01` |
| `F03-脱敏与去标识` | `F03-02` |
| `F03-差分隐私` | `F03-03` |
| `F03-联邦学习` | `F03-04` |
| `F03-数据分级分类` | `F03-05` |
| `F03-访问控制` | `F03-06` |
| `F03-数据血缘` | `F03-07` |
| `F03-生命周期销毁` | `F03-08` |
| `F03-第三方共享审查` | `F03-09` |
| `F03-用户权利响应` | `F03-10` |
| `F03-匿名化评估` | `F03-11` |
| `F03-隐私计算` | `F03-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "隐私与数据治理"
  code: "F03"
  provenance_strength: "external"
  provenance_legend:
    f03-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "F03-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "隐私与数据治理 全域"
      nodes:
        - "F03-01"
        - "F03-02"
        - "F03-03"
        - "F03-04"
        - "F03-05"
        - "F03-06"
        - "F03-07"
        - "F03-08"
        - "F03-09"
        - "F03-10"
        - "F03-11"
        - "F03-12"
  nodes:
    - id: "F03-01"
      name: "最小必要采集"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "f03-anchor"
    - id: "F03-02"
      name: "脱敏与去标识"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F03-01"
      provenance:
        - "f03-anchor"
    - id: "F03-03"
      name: "差分隐私"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F03-02"
      provenance:
        - "f03-anchor"
    - id: "F03-04"
      name: "联邦学习"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F03-03"
        - "F03-01"
      provenance:
        - "f03-anchor"
    - id: "F03-05"
      name: "数据分级分类"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F03-04"
        - "F03-02"
      provenance:
        - "f03-anchor"
    - id: "F03-06"
      name: "访问控制"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F03-05"
        - "F03-03"
      provenance:
        - "f03-anchor"
    - id: "F03-07"
      name: "数据血缘"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F03-06"
        - "F03-04"
      provenance:
        - "f03-anchor"
    - id: "F03-08"
      name: "生命周期销毁"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F03-07"
        - "F03-05"
      provenance:
        - "f03-anchor"
    - id: "F03-09"
      name: "第三方共享审查"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F03-08"
        - "F03-06"
      provenance:
        - "f03-anchor"
    - id: "F03-10"
      name: "用户权利响应"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F03-09"
        - "F03-07"
      provenance:
        - "f03-anchor"
    - id: "F03-11"
      name: "匿名化评估"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F03-10"
        - "F03-08"
      provenance:
        - "f03-anchor"
    - id: "F03-12"
      name: "隐私计算"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F03-11"
        - "F03-09"
      provenance:
        - "f03-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（F03-00）不随包交付，装载方须自备领域基础。
