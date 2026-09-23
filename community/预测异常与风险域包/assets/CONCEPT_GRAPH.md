<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 预测、异常与风险（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「预测、异常与风险」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（预测异常与风险:M01）与收口模块（预测异常与风险:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（B18-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B18-01` | 时序预测 | P40 | — | b18-anchor |
| `B18-02` | 需求预测与补货 | P60 | `B18-01` | b18-anchor |
| `B18-03` | 异常检测 | P40 | `B18-02` | b18-anchor |
| `B18-04` | 根因分析 | P60 | `B18-03`、`B18-01` | b18-anchor |
| `B18-05` | 风控评分卡 | P40 | `B18-04`、`B18-02` | b18-anchor |
| `B18-06` | 反欺诈 | P60 | `B18-05`、`B18-03` | b18-anchor |
| `B18-07` | 信用评估 | P40 | `B18-06`、`B18-04` | b18-anchor |
| `B18-08` | 设备预测性维护 | P60 | `B18-07`、`B18-05` | b18-anchor |
| `B18-09` | 舆情预警 | P40 | `B18-08`、`B18-06` | b18-anchor |
| `B18-10` | 保险定价 | P60 | `B18-09`、`B18-07` | b18-anchor |
| `B18-11` | 模型漂移监控 | P40 | `B18-10`、`B18-08` | b18-anchor |
| `B18-12` | 不确定性量化 | P60 | `B18-11`、`B18-09` | b18-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B18-时序预测` | `B18-01` |
| `B18-需求预测与补货` | `B18-02` |
| `B18-异常检测` | `B18-03` |
| `B18-根因分析` | `B18-04` |
| `B18-风控评分卡` | `B18-05` |
| `B18-反欺诈` | `B18-06` |
| `B18-信用评估` | `B18-07` |
| `B18-设备预测性维护` | `B18-08` |
| `B18-舆情预警` | `B18-09` |
| `B18-保险定价` | `B18-10` |
| `B18-模型漂移监控` | `B18-11` |
| `B18-不确定性量化` | `B18-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "预测、异常与风险"
  code: "B18"
  provenance_strength: "external"
  provenance_legend:
    b18-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "B18-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "预测、异常与风险 全域"
      nodes:
        - "B18-01"
        - "B18-02"
        - "B18-03"
        - "B18-04"
        - "B18-05"
        - "B18-06"
        - "B18-07"
        - "B18-08"
        - "B18-09"
        - "B18-10"
        - "B18-11"
        - "B18-12"
  nodes:
    - id: "B18-01"
      name: "时序预测"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b18-anchor"
    - id: "B18-02"
      name: "需求预测与补货"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-01"
      provenance:
        - "b18-anchor"
    - id: "B18-03"
      name: "异常检测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B18-02"
      provenance:
        - "b18-anchor"
    - id: "B18-04"
      name: "根因分析"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-03"
        - "B18-01"
      provenance:
        - "b18-anchor"
    - id: "B18-05"
      name: "风控评分卡"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B18-04"
        - "B18-02"
      provenance:
        - "b18-anchor"
    - id: "B18-06"
      name: "反欺诈"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-05"
        - "B18-03"
      provenance:
        - "b18-anchor"
    - id: "B18-07"
      name: "信用评估"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B18-06"
        - "B18-04"
      provenance:
        - "b18-anchor"
    - id: "B18-08"
      name: "设备预测性维护"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-07"
        - "B18-05"
      provenance:
        - "b18-anchor"
    - id: "B18-09"
      name: "舆情预警"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B18-08"
        - "B18-06"
      provenance:
        - "b18-anchor"
    - id: "B18-10"
      name: "保险定价"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-09"
        - "B18-07"
      provenance:
        - "b18-anchor"
    - id: "B18-11"
      name: "模型漂移监控"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B18-10"
        - "B18-08"
      provenance:
        - "b18-anchor"
    - id: "B18-12"
      name: "不确定性量化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-11"
        - "B18-09"
      provenance:
        - "b18-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B18-00）不随包交付，装载方须自备领域基础。
