<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 提示工程与指令设计（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「提示工程与指令设计」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（提示工程与指令设计:M01）与收口模块（提示工程与指令设计:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（E01-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E01-01` | 系统提示撰写 | P40 | — | e01-anchor |
| `E01-02` | 指令分层 | P60 | `E01-01` | e01-anchor |
| `E01-03` | 少样本示例 | P40 | `E01-02` | e01-anchor |
| `E01-04` | 思维链设计 | P60 | `E01-03`、`E01-01` | e01-anchor |
| `E01-05` | 结构化输出约束 | P40 | `E01-04`、`E01-02` | e01-anchor |
| `E01-06` | 工具编排 | P60 | `E01-05`、`E01-03` | e01-anchor |
| `E01-07` | 上下文预算 | P40 | `E01-06`、`E01-04` | e01-anchor |
| `E01-08` | 提示模板库 | P60 | `E01-07`、`E01-05` | e01-anchor |
| `E01-09` | 提示版本管理 | P40 | `E01-08`、`E01-06` | e01-anchor |
| `E01-10` | 跨模型迁移 | P60 | `E01-09`、`E01-07` | e01-anchor |
| `E01-11` | 提示评测回归 | P40 | `E01-10`、`E01-08` | e01-anchor |
| `E01-12` | 防注入设计 | P60 | `E01-11`、`E01-09` | e01-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E01-系统提示撰写` | `E01-01` |
| `E01-指令分层` | `E01-02` |
| `E01-少样本示例` | `E01-03` |
| `E01-思维链设计` | `E01-04` |
| `E01-结构化输出约束` | `E01-05` |
| `E01-工具编排` | `E01-06` |
| `E01-上下文预算` | `E01-07` |
| `E01-提示模板库` | `E01-08` |
| `E01-提示版本管理` | `E01-09` |
| `E01-跨模型迁移` | `E01-10` |
| `E01-提示评测回归` | `E01-11` |
| `E01-防注入设计` | `E01-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "提示工程与指令设计"
  code: "E01"
  provenance_strength: "external"
  provenance_legend:
    e01-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "E01-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "提示工程与指令设计 全域"
      nodes:
        - "E01-01"
        - "E01-02"
        - "E01-03"
        - "E01-04"
        - "E01-05"
        - "E01-06"
        - "E01-07"
        - "E01-08"
        - "E01-09"
        - "E01-10"
        - "E01-11"
        - "E01-12"
  nodes:
    - id: "E01-01"
      name: "系统提示撰写"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e01-anchor"
    - id: "E01-02"
      name: "指令分层"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E01-01"
      provenance:
        - "e01-anchor"
    - id: "E01-03"
      name: "少样本示例"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E01-02"
      provenance:
        - "e01-anchor"
    - id: "E01-04"
      name: "思维链设计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E01-03"
        - "E01-01"
      provenance:
        - "e01-anchor"
    - id: "E01-05"
      name: "结构化输出约束"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E01-04"
        - "E01-02"
      provenance:
        - "e01-anchor"
    - id: "E01-06"
      name: "工具编排"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E01-05"
        - "E01-03"
      provenance:
        - "e01-anchor"
    - id: "E01-07"
      name: "上下文预算"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E01-06"
        - "E01-04"
      provenance:
        - "e01-anchor"
    - id: "E01-08"
      name: "提示模板库"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E01-07"
        - "E01-05"
      provenance:
        - "e01-anchor"
    - id: "E01-09"
      name: "提示版本管理"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E01-08"
        - "E01-06"
      provenance:
        - "e01-anchor"
    - id: "E01-10"
      name: "跨模型迁移"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E01-09"
        - "E01-07"
      provenance:
        - "e01-anchor"
    - id: "E01-11"
      name: "提示评测回归"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E01-10"
        - "E01-08"
      provenance:
        - "e01-anchor"
    - id: "E01-12"
      name: "防注入设计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E01-11"
        - "E01-09"
      provenance:
        - "e01-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E01-00）不随包交付，装载方须自备领域基础。
