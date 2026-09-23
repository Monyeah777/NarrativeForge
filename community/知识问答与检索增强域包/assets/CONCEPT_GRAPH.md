<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 知识问答与检索增强（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「知识问答与检索增强」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（知识问答与检索增强:M01）与收口模块（知识问答与检索增强:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（B06-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B06-01` | 检索-生成管线设计 | P40 | `B06-02`、`B06-09` | b06-anchor |
| `B06-02` | 分块策略 | P60 | — | b06-anchor |
| `B06-03` | 查询改写与扩展 | P40 | `B06-01` | b06-anchor |
| `B06-04` | 混合检索 | P60 | `B06-03` | b06-anchor |
| `B06-05` | 重排序 | P40 | `B06-04` | b06-anchor |
| `B06-06` | 上下文压缩 | P60 | `B06-05` | b06-anchor |
| `B06-07` | 引用与归因 | P40 | `B06-01` | b06-anchor |
| `B06-08` | 多跳问答 | P60 | `B06-04` | b06-anchor |
| `B06-09` | 知识库构建与更新 | P40 | — | b06-anchor |
| `B06-10` | 拒答与不确定性 | P60 | `B06-07` | b06-anchor |
| `B06-11` | 检索增强评测 | P40 | — | b06-anchor |
| `B06-12` | 幻觉与冲突消解 | P60 | `B06-10` | b06-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B06-检索-生成管线设计` | `B06-01` |
| `B06-分块策略` | `B06-02` |
| `B06-查询改写与扩展` | `B06-03` |
| `B06-混合检索` | `B06-04` |
| `B06-重排序` | `B06-05` |
| `B06-上下文压缩` | `B06-06` |
| `B06-引用与归因` | `B06-07` |
| `B06-多跳问答` | `B06-08` |
| `B06-知识库构建与更新` | `B06-09` |
| `B06-拒答与不确定性` | `B06-10` |
| `B06-检索增强评测` | `B06-11` |
| `B06-幻觉与冲突消解` | `B06-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "知识问答与检索增强"
  code: "B06"
  provenance_strength: "external"
  provenance_legend:
    b06-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "B06-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "知识问答与检索增强 全域"
      nodes:
        - "B06-01"
        - "B06-02"
        - "B06-03"
        - "B06-04"
        - "B06-05"
        - "B06-06"
        - "B06-07"
        - "B06-08"
        - "B06-09"
        - "B06-10"
        - "B06-11"
        - "B06-12"
  nodes:
    - id: "B06-01"
      name: "检索-生成管线设计"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B06-02"
        - "B06-09"
      provenance:
        - "b06-anchor"
    - id: "B06-02"
      name: "分块策略"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b06-anchor"
    - id: "B06-03"
      name: "查询改写与扩展"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B06-01"
      provenance:
        - "b06-anchor"
    - id: "B06-04"
      name: "混合检索"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B06-03"
      provenance:
        - "b06-anchor"
    - id: "B06-05"
      name: "重排序"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B06-04"
      provenance:
        - "b06-anchor"
    - id: "B06-06"
      name: "上下文压缩"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B06-05"
      provenance:
        - "b06-anchor"
    - id: "B06-07"
      name: "引用与归因"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B06-01"
      provenance:
        - "b06-anchor"
    - id: "B06-08"
      name: "多跳问答"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B06-04"
      provenance:
        - "b06-anchor"
    - id: "B06-09"
      name: "知识库构建与更新"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b06-anchor"
    - id: "B06-10"
      name: "拒答与不确定性"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B06-07"
      provenance:
        - "b06-anchor"
    - id: "B06-11"
      name: "检索增强评测"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b06-anchor"
    - id: "B06-12"
      name: "幻觉与冲突消解"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B06-10"
      provenance:
        - "b06-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B06-00）不随包交付，装载方须自备领域基础。
