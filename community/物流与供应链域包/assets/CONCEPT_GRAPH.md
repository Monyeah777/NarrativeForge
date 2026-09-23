<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 物流与供应链（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「物流与供应链」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（物流与供应链:M01）与收口模块（物流与供应链:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（D12-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D12-01` | 路径规划 | P40 | — | d12-anchor |
| `D12-02` | 运力调度 | P60 | `D12-01` | d12-anchor |
| `D12-03` | 仓储拣选 | P40 | `D12-02` | d12-anchor |
| `D12-04` | 需求预测 | P60 | `D12-03`、`D12-01` | d12-anchor |
| `D12-05` | 单据识别 | P40 | `D12-04`、`D12-02` | d12-anchor |
| `D12-06` | 异常件处置 | P60 | `D12-05`、`D12-03` | d12-anchor |
| `D12-07` | 冷链监控 | P40 | `D12-06`、`D12-04` | d12-anchor |
| `D12-08` | 供应商评估 | P60 | `D12-07`、`D12-05` | d12-anchor |
| `D12-09` | 关务合规 | P40 | `D12-08`、`D12-06` | d12-anchor |
| `D12-10` | 碳排核算 | P60 | `D12-09`、`D12-07` | d12-anchor |
| `D12-11` | 末端配送 | P40 | `D12-10`、`D12-08` | d12-anchor |
| `D12-12` | 供应链风险预警 | P60 | `D12-11`、`D12-09` | d12-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D12-路径规划` | `D12-01` |
| `D12-运力调度` | `D12-02` |
| `D12-仓储拣选` | `D12-03` |
| `D12-需求预测` | `D12-04` |
| `D12-单据识别` | `D12-05` |
| `D12-异常件处置` | `D12-06` |
| `D12-冷链监控` | `D12-07` |
| `D12-供应商评估` | `D12-08` |
| `D12-关务合规` | `D12-09` |
| `D12-碳排核算` | `D12-10` |
| `D12-末端配送` | `D12-11` |
| `D12-供应链风险预警` | `D12-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "物流与供应链"
  code: "D12"
  provenance_strength: "external"
  provenance_legend:
    d12-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "D12-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "物流与供应链 全域"
      nodes:
        - "D12-01"
        - "D12-02"
        - "D12-03"
        - "D12-04"
        - "D12-05"
        - "D12-06"
        - "D12-07"
        - "D12-08"
        - "D12-09"
        - "D12-10"
        - "D12-11"
        - "D12-12"
  nodes:
    - id: "D12-01"
      name: "路径规划"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d12-anchor"
    - id: "D12-02"
      name: "运力调度"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D12-01"
      provenance:
        - "d12-anchor"
    - id: "D12-03"
      name: "仓储拣选"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D12-02"
      provenance:
        - "d12-anchor"
    - id: "D12-04"
      name: "需求预测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D12-03"
        - "D12-01"
      provenance:
        - "d12-anchor"
    - id: "D12-05"
      name: "单据识别"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D12-04"
        - "D12-02"
      provenance:
        - "d12-anchor"
    - id: "D12-06"
      name: "异常件处置"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D12-05"
        - "D12-03"
      provenance:
        - "d12-anchor"
    - id: "D12-07"
      name: "冷链监控"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D12-06"
        - "D12-04"
      provenance:
        - "d12-anchor"
    - id: "D12-08"
      name: "供应商评估"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D12-07"
        - "D12-05"
      provenance:
        - "d12-anchor"
    - id: "D12-09"
      name: "关务合规"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D12-08"
        - "D12-06"
      provenance:
        - "d12-anchor"
    - id: "D12-10"
      name: "碳排核算"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D12-09"
        - "D12-07"
      provenance:
        - "d12-anchor"
    - id: "D12-11"
      name: "末端配送"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D12-10"
        - "D12-08"
      provenance:
        - "d12-anchor"
    - id: "D12-12"
      name: "供应链风险预警"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D12-11"
        - "D12-09"
      provenance:
        - "d12-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D12-00）不随包交付，装载方须自备领域基础。
