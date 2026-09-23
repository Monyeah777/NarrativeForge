<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 交通与出行（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「交通与出行」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（交通与出行:M01）与收口模块（交通与出行:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（D13-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D13-01` | 交通流预测 | P40 | — | d13-anchor |
| `D13-02` | 信号配时 | P60 | `D13-01` | d13-anchor |
| `D13-03` | 事故识别 | P40 | `D13-02` | d13-anchor |
| `D13-04` | 驾驶行为分析 | P60 | `D13-03`、`D13-01` | d13-anchor |
| `D13-05` | 出行助手 | P40 | `D13-04`、`D13-02` | d13-anchor |
| `D13-06` | 票务问答 | P60 | `D13-05`、`D13-03` | d13-anchor |
| `D13-07` | 延误处置 | P40 | `D13-06`、`D13-04` | d13-anchor |
| `D13-08` | 车路协同 | P60 | `D13-07`、`D13-05` | d13-anchor |
| `D13-09` | 充电桩调度 | P40 | `D13-08`、`D13-06` | d13-anchor |
| `D13-10` | 路况播报 | P60 | `D13-09`、`D13-07` | d13-anchor |
| `D13-11` | 运力撮合 | P40 | `D13-10`、`D13-08` | d13-anchor |
| `D13-12` | 交通安全宣教 | P60 | `D13-11`、`D13-09` | d13-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D13-交通流预测` | `D13-01` |
| `D13-信号配时` | `D13-02` |
| `D13-事故识别` | `D13-03` |
| `D13-驾驶行为分析` | `D13-04` |
| `D13-出行助手` | `D13-05` |
| `D13-票务问答` | `D13-06` |
| `D13-延误处置` | `D13-07` |
| `D13-车路协同` | `D13-08` |
| `D13-充电桩调度` | `D13-09` |
| `D13-路况播报` | `D13-10` |
| `D13-运力撮合` | `D13-11` |
| `D13-交通安全宣教` | `D13-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "交通与出行"
  code: "D13"
  provenance_strength: "external"
  provenance_legend:
    d13-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "D13-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "交通与出行 全域"
      nodes:
        - "D13-01"
        - "D13-02"
        - "D13-03"
        - "D13-04"
        - "D13-05"
        - "D13-06"
        - "D13-07"
        - "D13-08"
        - "D13-09"
        - "D13-10"
        - "D13-11"
        - "D13-12"
  nodes:
    - id: "D13-01"
      name: "交通流预测"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d13-anchor"
    - id: "D13-02"
      name: "信号配时"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D13-01"
      provenance:
        - "d13-anchor"
    - id: "D13-03"
      name: "事故识别"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D13-02"
      provenance:
        - "d13-anchor"
    - id: "D13-04"
      name: "驾驶行为分析"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D13-03"
        - "D13-01"
      provenance:
        - "d13-anchor"
    - id: "D13-05"
      name: "出行助手"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D13-04"
        - "D13-02"
      provenance:
        - "d13-anchor"
    - id: "D13-06"
      name: "票务问答"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D13-05"
        - "D13-03"
      provenance:
        - "d13-anchor"
    - id: "D13-07"
      name: "延误处置"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D13-06"
        - "D13-04"
      provenance:
        - "d13-anchor"
    - id: "D13-08"
      name: "车路协同"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D13-07"
        - "D13-05"
      provenance:
        - "d13-anchor"
    - id: "D13-09"
      name: "充电桩调度"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D13-08"
        - "D13-06"
      provenance:
        - "d13-anchor"
    - id: "D13-10"
      name: "路况播报"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D13-09"
        - "D13-07"
      provenance:
        - "d13-anchor"
    - id: "D13-11"
      name: "运力撮合"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D13-10"
        - "D13-08"
      provenance:
        - "d13-anchor"
    - id: "D13-12"
      name: "交通安全宣教"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D13-11"
        - "D13-09"
      provenance:
        - "d13-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D13-00）不随包交付，装载方须自备领域基础。
