<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 数据标注与标注质量（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「数据标注与标注质量」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（数据标注与标注质量:M01）与收口模块（数据标注与标注质量:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（C02-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C02-01` | 标注规范撰写 | P40 | — | c02-anchor |
| `C02-02` | 标注工具与流程 | P60 | `C02-01` | c02-anchor |
| `C02-03` | 众包与专家标注 | P40 | `C02-02` | c02-anchor |
| `C02-04` | 一致性度量（Kappa） | P60 | `C02-03`、`C02-01` | c02-anchor |
| `C02-05` | 标注歧义与仲裁 | P40 | `C02-04`、`C02-02` | c02-anchor |
| `C02-06` | 主动学习抽样 | P60 | `C02-05`、`C02-03` | c02-anchor |
| `C02-07` | 标注成本控制 | P40 | `C02-06`、`C02-04` | c02-anchor |
| `C02-08` | 层级与多标签体系 | P60 | `C02-07`、`C02-05` | c02-anchor |
| `C02-09` | 标注数据版本 | P40 | `C02-08`、`C02-06` | c02-anchor |
| `C02-10` | 标注隐私与合规 | P60 | `C02-09`、`C02-07` | c02-anchor |
| `C02-11` | 标注验收与返工 | P40 | `C02-10`、`C02-08` | c02-anchor |
| `C02-12` | 标注外包管理 | P60 | `C02-11`、`C02-09` | c02-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C02-标注规范撰写` | `C02-01` |
| `C02-标注工具与流程` | `C02-02` |
| `C02-众包与专家标注` | `C02-03` |
| `C02-一致性度量-Kappa-` | `C02-04` |
| `C02-标注歧义与仲裁` | `C02-05` |
| `C02-主动学习抽样` | `C02-06` |
| `C02-标注成本控制` | `C02-07` |
| `C02-层级与多标签体系` | `C02-08` |
| `C02-标注数据版本` | `C02-09` |
| `C02-标注隐私与合规` | `C02-10` |
| `C02-标注验收与返工` | `C02-11` |
| `C02-标注外包管理` | `C02-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "数据标注与标注质量"
  code: "C02"
  provenance_strength: "external"
  provenance_legend:
    c02-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "C02-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "数据标注与标注质量 全域"
      nodes:
        - "C02-01"
        - "C02-02"
        - "C02-03"
        - "C02-04"
        - "C02-05"
        - "C02-06"
        - "C02-07"
        - "C02-08"
        - "C02-09"
        - "C02-10"
        - "C02-11"
        - "C02-12"
  nodes:
    - id: "C02-01"
      name: "标注规范撰写"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c02-anchor"
    - id: "C02-02"
      name: "标注工具与流程"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C02-01"
      provenance:
        - "c02-anchor"
    - id: "C02-03"
      name: "众包与专家标注"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C02-02"
      provenance:
        - "c02-anchor"
    - id: "C02-04"
      name: "一致性度量（Kappa）"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C02-03"
        - "C02-01"
      provenance:
        - "c02-anchor"
    - id: "C02-05"
      name: "标注歧义与仲裁"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C02-04"
        - "C02-02"
      provenance:
        - "c02-anchor"
    - id: "C02-06"
      name: "主动学习抽样"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C02-05"
        - "C02-03"
      provenance:
        - "c02-anchor"
    - id: "C02-07"
      name: "标注成本控制"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C02-06"
        - "C02-04"
      provenance:
        - "c02-anchor"
    - id: "C02-08"
      name: "层级与多标签体系"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C02-07"
        - "C02-05"
      provenance:
        - "c02-anchor"
    - id: "C02-09"
      name: "标注数据版本"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C02-08"
        - "C02-06"
      provenance:
        - "c02-anchor"
    - id: "C02-10"
      name: "标注隐私与合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C02-09"
        - "C02-07"
      provenance:
        - "c02-anchor"
    - id: "C02-11"
      name: "标注验收与返工"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C02-10"
        - "C02-08"
      provenance:
        - "c02-anchor"
    - id: "C02-12"
      name: "标注外包管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C02-11"
        - "C02-09"
      provenance:
        - "c02-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C02-00）不随包交付，装载方须自备领域基础。
