<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 可观测性、成本与可靠性（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「可观测性、成本与可靠性」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（可观测性成本与可靠性:M01）与收口模块（可观测性成本与可靠性:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（C18-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C18-01` | 链路追踪 | P40 | — | c18-anchor |
| `C18-02` | 日志与提示留存 | P60 | `C18-01` | c18-anchor |
| `C18-03` | Token 计量与计费 | P40 | `C18-02` | c18-anchor |
| `C18-04` | 成本归因 | P60 | `C18-03`、`C18-01` | c18-anchor |
| `C18-05` | 延迟分解 | P40 | `C18-04`、`C18-02` | c18-anchor |
| `C18-06` | SLA 监控 | P60 | `C18-05`、`C18-03` | c18-anchor |
| `C18-07` | 异常检测与降级 | P40 | `C18-06`、`C18-04` | c18-anchor |
| `C18-08` | 模型版本管理 | P60 | `C18-07`、`C18-05` | c18-anchor |
| `C18-09` | 实验平台 | P40 | `C18-08`、`C18-06` | c18-anchor |
| `C18-10` | 回放与复现 | P60 | `C18-09`、`C18-07` | c18-anchor |
| `C18-11` | 数据回流 | P40 | `C18-10`、`C18-08` | c18-anchor |
| `C18-12` | 事故复盘 | P60 | `C18-11`、`C18-09` | c18-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C18-链路追踪` | `C18-01` |
| `C18-日志与提示留存` | `C18-02` |
| `C18-Token-计量与计费` | `C18-03` |
| `C18-成本归因` | `C18-04` |
| `C18-延迟分解` | `C18-05` |
| `C18-SLA-监控` | `C18-06` |
| `C18-异常检测与降级` | `C18-07` |
| `C18-模型版本管理` | `C18-08` |
| `C18-实验平台` | `C18-09` |
| `C18-回放与复现` | `C18-10` |
| `C18-数据回流` | `C18-11` |
| `C18-事故复盘` | `C18-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "可观测性、成本与可靠性"
  code: "C18"
  provenance_strength: "external"
  provenance_legend:
    c18-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "C18-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "可观测性、成本与可靠性 全域"
      nodes:
        - "C18-01"
        - "C18-02"
        - "C18-03"
        - "C18-04"
        - "C18-05"
        - "C18-06"
        - "C18-07"
        - "C18-08"
        - "C18-09"
        - "C18-10"
        - "C18-11"
        - "C18-12"
  nodes:
    - id: "C18-01"
      name: "链路追踪"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c18-anchor"
    - id: "C18-02"
      name: "日志与提示留存"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C18-01"
      provenance:
        - "c18-anchor"
    - id: "C18-03"
      name: "Token 计量与计费"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C18-02"
      provenance:
        - "c18-anchor"
    - id: "C18-04"
      name: "成本归因"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C18-03"
        - "C18-01"
      provenance:
        - "c18-anchor"
    - id: "C18-05"
      name: "延迟分解"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C18-04"
        - "C18-02"
      provenance:
        - "c18-anchor"
    - id: "C18-06"
      name: "SLA 监控"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C18-05"
        - "C18-03"
      provenance:
        - "c18-anchor"
    - id: "C18-07"
      name: "异常检测与降级"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C18-06"
        - "C18-04"
      provenance:
        - "c18-anchor"
    - id: "C18-08"
      name: "模型版本管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C18-07"
        - "C18-05"
      provenance:
        - "c18-anchor"
    - id: "C18-09"
      name: "实验平台"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C18-08"
        - "C18-06"
      provenance:
        - "c18-anchor"
    - id: "C18-10"
      name: "回放与复现"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C18-09"
        - "C18-07"
      provenance:
        - "c18-anchor"
    - id: "C18-11"
      name: "数据回流"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C18-10"
        - "C18-08"
      provenance:
        - "c18-anchor"
    - id: "C18-12"
      name: "事故复盘"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C18-11"
        - "C18-09"
      provenance:
        - "c18-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C18-00）不随包交付，装载方须自备领域基础。
