<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 传媒与新闻（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「传媒与新闻」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（传媒与新闻:M01）与收口模块（传媒与新闻:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（D17-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D17-01` | 选题策划 | P40 | — | d17-anchor |
| `D17-02` | 采访提纲 | P60 | `D17-01` | d17-anchor |
| `D17-03` | 稿件撰写 | P40 | `D17-02` | d17-anchor |
| `D17-04` | 事实核查 | P60 | `D17-03`、`D17-01` | d17-anchor |
| `D17-05` | 多语编译 | P40 | `D17-04`、`D17-02` | d17-anchor |
| `D17-06` | 标题与摘要 | P60 | `D17-05`、`D17-03` | d17-anchor |
| `D17-07` | 分发策略 | P40 | `D17-06`、`D17-04` | d17-anchor |
| `D17-08` | 热点监测 | P60 | `D17-07`、`D17-05` | d17-anchor |
| `D17-09` | 版权与引用 | P40 | `D17-08`、`D17-06` | d17-anchor |
| `D17-10` | 数据新闻可视化 | P60 | `D17-09`、`D17-07` | d17-anchor |
| `D17-11` | 播客脚本 | P40 | `D17-10`、`D17-08` | d17-anchor |
| `D17-12` | 舆情分级 | P60 | `D17-11`、`D17-09` | d17-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D17-选题策划` | `D17-01` |
| `D17-采访提纲` | `D17-02` |
| `D17-稿件撰写` | `D17-03` |
| `D17-事实核查` | `D17-04` |
| `D17-多语编译` | `D17-05` |
| `D17-标题与摘要` | `D17-06` |
| `D17-分发策略` | `D17-07` |
| `D17-热点监测` | `D17-08` |
| `D17-版权与引用` | `D17-09` |
| `D17-数据新闻可视化` | `D17-10` |
| `D17-播客脚本` | `D17-11` |
| `D17-舆情分级` | `D17-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "传媒与新闻"
  code: "D17"
  provenance_strength: "external"
  provenance_legend:
    d17-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "D17-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "传媒与新闻 全域"
      nodes:
        - "D17-01"
        - "D17-02"
        - "D17-03"
        - "D17-04"
        - "D17-05"
        - "D17-06"
        - "D17-07"
        - "D17-08"
        - "D17-09"
        - "D17-10"
        - "D17-11"
        - "D17-12"
  nodes:
    - id: "D17-01"
      name: "选题策划"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d17-anchor"
    - id: "D17-02"
      name: "采访提纲"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D17-01"
      provenance:
        - "d17-anchor"
    - id: "D17-03"
      name: "稿件撰写"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D17-02"
      provenance:
        - "d17-anchor"
    - id: "D17-04"
      name: "事实核查"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D17-03"
        - "D17-01"
      provenance:
        - "d17-anchor"
    - id: "D17-05"
      name: "多语编译"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D17-04"
        - "D17-02"
      provenance:
        - "d17-anchor"
    - id: "D17-06"
      name: "标题与摘要"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D17-05"
        - "D17-03"
      provenance:
        - "d17-anchor"
    - id: "D17-07"
      name: "分发策略"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D17-06"
        - "D17-04"
      provenance:
        - "d17-anchor"
    - id: "D17-08"
      name: "热点监测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D17-07"
        - "D17-05"
      provenance:
        - "d17-anchor"
    - id: "D17-09"
      name: "版权与引用"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D17-08"
        - "D17-06"
      provenance:
        - "d17-anchor"
    - id: "D17-10"
      name: "数据新闻可视化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D17-09"
        - "D17-07"
      provenance:
        - "d17-anchor"
    - id: "D17-11"
      name: "播客脚本"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D17-10"
        - "D17-08"
      provenance:
        - "d17-anchor"
    - id: "D17-12"
      name: "舆情分级"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D17-11"
        - "D17-09"
      provenance:
        - "d17-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D17-00）不随包交付，装载方须自备领域基础。
