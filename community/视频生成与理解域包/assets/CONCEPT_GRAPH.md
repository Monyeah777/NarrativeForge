<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 视频生成与理解（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「视频生成与理解」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（视频生成与理解:M01）与收口模块（视频生成与理解:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（A06-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A06-01` | 文生视频 | P40 | — | a06-anchor |
| `A06-02` | 图生视频 | P60 | `A06-01` | a06-anchor |
| `A06-03` | 视频编辑与重绘 | P40 | `A06-02`、`A06-07` | a06-anchor |
| `A06-04` | 视频超分与修复 | P60 | `A06-03` | a06-anchor |
| `A06-05` | 镜头分割与关键帧 | P40 | — | a06-anchor |
| `A06-06` | 长视频时序一致性 | P60 | `A06-04`、`A06-05` | a06-anchor |
| `A06-07` | 动作可控生成 | P40 | — | a06-anchor |
| `A06-08` | 视频字幕与描述 | P60 | `A06-05` | a06-anchor |
| `A06-09` | 视频问答 | P40 | `A06-08` | a06-anchor |
| `A06-10` | 视频检索 | P60 | `A06-08` | a06-anchor |
| `A06-11` | 口型同步与数字人驱动 | P40 | — | a06-anchor |
| `A06-12` | 视频生成评测 | P60 | `A06-11` | a06-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A06-文生视频` | `A06-01` |
| `A06-图生视频` | `A06-02` |
| `A06-视频编辑与重绘` | `A06-03` |
| `A06-视频超分与修复` | `A06-04` |
| `A06-镜头分割与关键帧` | `A06-05` |
| `A06-长视频时序一致性` | `A06-06` |
| `A06-动作可控生成` | `A06-07` |
| `A06-视频字幕与描述` | `A06-08` |
| `A06-视频问答` | `A06-09` |
| `A06-视频检索` | `A06-10` |
| `A06-口型同步与数字人驱动` | `A06-11` |
| `A06-视频生成评测` | `A06-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "视频生成与理解"
  code: "A06"
  provenance_strength: "external"
  provenance_legend:
    a06-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "A06-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "视频生成与理解 全域"
      nodes:
        - "A06-01"
        - "A06-02"
        - "A06-03"
        - "A06-04"
        - "A06-05"
        - "A06-06"
        - "A06-07"
        - "A06-08"
        - "A06-09"
        - "A06-10"
        - "A06-11"
        - "A06-12"
  nodes:
    - id: "A06-01"
      name: "文生视频"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a06-anchor"
    - id: "A06-02"
      name: "图生视频"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-01"
      provenance:
        - "a06-anchor"
    - id: "A06-03"
      name: "视频编辑与重绘"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A06-02"
        - "A06-07"
      provenance:
        - "a06-anchor"
    - id: "A06-04"
      name: "视频超分与修复"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-03"
      provenance:
        - "a06-anchor"
    - id: "A06-05"
      name: "镜头分割与关键帧"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a06-anchor"
    - id: "A06-06"
      name: "长视频时序一致性"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-04"
        - "A06-05"
      provenance:
        - "a06-anchor"
    - id: "A06-07"
      name: "动作可控生成"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a06-anchor"
    - id: "A06-08"
      name: "视频字幕与描述"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-05"
      provenance:
        - "a06-anchor"
    - id: "A06-09"
      name: "视频问答"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A06-08"
      provenance:
        - "a06-anchor"
    - id: "A06-10"
      name: "视频检索"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-08"
      provenance:
        - "a06-anchor"
    - id: "A06-11"
      name: "口型同步与数字人驱动"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a06-anchor"
    - id: "A06-12"
      name: "视频生成评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A06-11"
      provenance:
        - "a06-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A06-00）不随包交付，装载方须自备领域基础。
