<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 三维与世界模型（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「三维与世界模型」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（三维与世界模型:M01）与收口模块（三维与世界模型:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（A08-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A08-01` | 三维重建与辐射场 | P40 | — | a08-anchor |
| `A08-02` | 点云处理 | P60 | — | a08-anchor |
| `A08-03` | 纹理与材质生成 | P40 | `A08-01` | a08-anchor |
| `A08-04` | 文生 3D 资产 | P60 | `A08-01` | a08-anchor |
| `A08-05` | 场景生成与布局 | P40 | `A08-02`、`A08-04` | a08-anchor |
| `A08-06` | 物理仿真与碰撞 | P60 | `A08-05` | a08-anchor |
| `A08-07` | 世界模型与状态预测 | P40 | `A08-06` | a08-anchor |
| `A08-08` | SLAM 与定位 | P60 | `A08-02` | a08-anchor |
| `A08-09` | 数字孪生 | P40 | `A08-05` | a08-anchor |
| `A08-10` | 3D 资产格式与管线 | P60 | — | a08-anchor |
| `A08-11` | 骨骼绑定与动画 | P40 | `A08-10` | a08-anchor |
| `A08-12` | 三维评测 | P60 | `A08-07` | a08-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A08-三维重建与辐射场` | `A08-01` |
| `A08-点云处理` | `A08-02` |
| `A08-纹理与材质生成` | `A08-03` |
| `A08-文生-3D-资产` | `A08-04` |
| `A08-场景生成与布局` | `A08-05` |
| `A08-物理仿真与碰撞` | `A08-06` |
| `A08-世界模型与状态预测` | `A08-07` |
| `A08-SLAM-与定位` | `A08-08` |
| `A08-数字孪生` | `A08-09` |
| `A08-3D-资产格式与管线` | `A08-10` |
| `A08-骨骼绑定与动画` | `A08-11` |
| `A08-三维评测` | `A08-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "三维与世界模型"
  code: "A08"
  provenance_strength: "external"
  provenance_legend:
    a08-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "A08-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "三维与世界模型 全域"
      nodes:
        - "A08-01"
        - "A08-02"
        - "A08-03"
        - "A08-04"
        - "A08-05"
        - "A08-06"
        - "A08-07"
        - "A08-08"
        - "A08-09"
        - "A08-10"
        - "A08-11"
        - "A08-12"
  nodes:
    - id: "A08-01"
      name: "三维重建与辐射场"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a08-anchor"
    - id: "A08-02"
      name: "点云处理"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a08-anchor"
    - id: "A08-03"
      name: "纹理与材质生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A08-01"
      provenance:
        - "a08-anchor"
    - id: "A08-04"
      name: "文生 3D 资产"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A08-01"
      provenance:
        - "a08-anchor"
    - id: "A08-05"
      name: "场景生成与布局"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A08-02"
        - "A08-04"
      provenance:
        - "a08-anchor"
    - id: "A08-06"
      name: "物理仿真与碰撞"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A08-05"
      provenance:
        - "a08-anchor"
    - id: "A08-07"
      name: "世界模型与状态预测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A08-06"
      provenance:
        - "a08-anchor"
    - id: "A08-08"
      name: "SLAM 与定位"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A08-02"
      provenance:
        - "a08-anchor"
    - id: "A08-09"
      name: "数字孪生"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A08-05"
      provenance:
        - "a08-anchor"
    - id: "A08-10"
      name: "3D 资产格式与管线"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a08-anchor"
    - id: "A08-11"
      name: "骨骼绑定与动画"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A08-10"
      provenance:
        - "a08-anchor"
    - id: "A08-12"
      name: "三维评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A08-07"
      provenance:
        - "a08-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A08-00）不随包交付，装载方须自备领域基础。
