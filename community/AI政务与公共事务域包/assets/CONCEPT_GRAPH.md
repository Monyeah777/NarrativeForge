<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+政务与公共事务（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+政务与公共事务」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI政务与公共事务:M01）与收口模块（AI政务与公共事务:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（D07-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D07-01` | 政策文件解读 | P40 | — | d07-anchor |
| `D07-02` | 公文写作 | P60 | `D07-01` | d07-anchor |
| `D07-03` | 政务问答坐席 | P40 | `D07-02` | d07-anchor |
| `D07-04` | 审批流程辅助 | P60 | `D07-03`、`D07-01` | d07-anchor |
| `D07-05` | 舆情监测与回应 | P40 | `D07-04`、`D07-02` | d07-anchor |
| `D07-06` | 数据报送统计 | P60 | `D07-05`、`D07-03` | d07-anchor |
| `D07-07` | 法规合规检查 | P40 | `D07-06`、`D07-04` | d07-anchor |
| `D07-08` | 民生服务知识库 | P60 | `D07-07`、`D07-05` | d07-anchor |
| `D07-09` | 城市治理工单 | P40 | `D07-08`、`D07-06` | d07-anchor |
| `D07-10` | 政务信息公开 | P60 | `D07-09`、`D07-07` | d07-anchor |
| `D07-11` | 权限与保密 | P40 | `D07-10`、`D07-08` | d07-anchor |
| `D07-12` | 无障碍服务 | P60 | `D07-11`、`D07-09` | d07-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D07-政策文件解读` | `D07-01` |
| `D07-公文写作` | `D07-02` |
| `D07-政务问答坐席` | `D07-03` |
| `D07-审批流程辅助` | `D07-04` |
| `D07-舆情监测与回应` | `D07-05` |
| `D07-数据报送统计` | `D07-06` |
| `D07-法规合规检查` | `D07-07` |
| `D07-民生服务知识库` | `D07-08` |
| `D07-城市治理工单` | `D07-09` |
| `D07-政务信息公开` | `D07-10` |
| `D07-权限与保密` | `D07-11` |
| `D07-无障碍服务` | `D07-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+政务与公共事务"
  code: "D07"
  provenance_strength: "external"
  provenance_legend:
    d07-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "D07-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+政务与公共事务 全域"
      nodes:
        - "D07-01"
        - "D07-02"
        - "D07-03"
        - "D07-04"
        - "D07-05"
        - "D07-06"
        - "D07-07"
        - "D07-08"
        - "D07-09"
        - "D07-10"
        - "D07-11"
        - "D07-12"
  nodes:
    - id: "D07-01"
      name: "政策文件解读"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d07-anchor"
    - id: "D07-02"
      name: "公文写作"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-01"
      provenance:
        - "d07-anchor"
    - id: "D07-03"
      name: "政务问答坐席"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D07-02"
      provenance:
        - "d07-anchor"
    - id: "D07-04"
      name: "审批流程辅助"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-03"
        - "D07-01"
      provenance:
        - "d07-anchor"
    - id: "D07-05"
      name: "舆情监测与回应"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D07-04"
        - "D07-02"
      provenance:
        - "d07-anchor"
    - id: "D07-06"
      name: "数据报送统计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-05"
        - "D07-03"
      provenance:
        - "d07-anchor"
    - id: "D07-07"
      name: "法规合规检查"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D07-06"
        - "D07-04"
      provenance:
        - "d07-anchor"
    - id: "D07-08"
      name: "民生服务知识库"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-07"
        - "D07-05"
      provenance:
        - "d07-anchor"
    - id: "D07-09"
      name: "城市治理工单"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D07-08"
        - "D07-06"
      provenance:
        - "d07-anchor"
    - id: "D07-10"
      name: "政务信息公开"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-09"
        - "D07-07"
      provenance:
        - "d07-anchor"
    - id: "D07-11"
      name: "权限与保密"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D07-10"
        - "D07-08"
      provenance:
        - "d07-anchor"
    - id: "D07-12"
      name: "无障碍服务"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-11"
        - "D07-09"
      provenance:
        - "d07-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D07-00）不随包交付，装载方须自备领域基础。
