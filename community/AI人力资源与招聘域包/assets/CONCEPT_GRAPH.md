<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+人力资源与招聘（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+人力资源与招聘」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI人力资源与招聘:M01）与收口模块（AI人力资源与招聘:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（D14-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D14-01` | 简历解析与筛选 | P40 | — | d14-anchor |
| `D14-02` | 岗位画像 | P60 | `D14-01` | d14-anchor |
| `D14-03` | 人岗匹配 | P40 | `D14-02` | d14-anchor |
| `D14-04` | 面试题生成 | P60 | `D14-03`、`D14-01` | d14-anchor |
| `D14-05` | 面试记录分析 | P40 | `D14-04`、`D14-02` | d14-anchor |
| `D14-06` | 流失预警 | P60 | `D14-05`、`D14-03` | d14-anchor |
| `D14-07` | 绩效评语辅助 | P40 | `D14-06`、`D14-04` | d14-anchor |
| `D14-08` | 培训内容生成 | P60 | `D14-07`、`D14-05` | d14-anchor |
| `D14-09` | 薪酬对标分析 | P40 | `D14-08`、`D14-06` | d14-anchor |
| `D14-10` | 劳动法问答 | P60 | `D14-09`、`D14-07` | d14-anchor |
| `D14-11` | 内部知识助手 | P40 | `D14-10`、`D14-08` | d14-anchor |
| `D14-12` | 招聘合规审查 | P60 | `D14-11`、`D14-09` | d14-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D14-简历解析与筛选` | `D14-01` |
| `D14-岗位画像` | `D14-02` |
| `D14-人岗匹配` | `D14-03` |
| `D14-面试题生成` | `D14-04` |
| `D14-面试记录分析` | `D14-05` |
| `D14-流失预警` | `D14-06` |
| `D14-绩效评语辅助` | `D14-07` |
| `D14-培训内容生成` | `D14-08` |
| `D14-薪酬对标分析` | `D14-09` |
| `D14-劳动法问答` | `D14-10` |
| `D14-内部知识助手` | `D14-11` |
| `D14-招聘合规审查` | `D14-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+人力资源与招聘"
  code: "D14"
  provenance_strength: "external"
  provenance_legend:
    d14-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "D14-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+人力资源与招聘 全域"
      nodes:
        - "D14-01"
        - "D14-02"
        - "D14-03"
        - "D14-04"
        - "D14-05"
        - "D14-06"
        - "D14-07"
        - "D14-08"
        - "D14-09"
        - "D14-10"
        - "D14-11"
        - "D14-12"
  nodes:
    - id: "D14-01"
      name: "简历解析与筛选"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d14-anchor"
    - id: "D14-02"
      name: "岗位画像"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D14-01"
      provenance:
        - "d14-anchor"
    - id: "D14-03"
      name: "人岗匹配"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D14-02"
      provenance:
        - "d14-anchor"
    - id: "D14-04"
      name: "面试题生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D14-03"
        - "D14-01"
      provenance:
        - "d14-anchor"
    - id: "D14-05"
      name: "面试记录分析"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D14-04"
        - "D14-02"
      provenance:
        - "d14-anchor"
    - id: "D14-06"
      name: "流失预警"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D14-05"
        - "D14-03"
      provenance:
        - "d14-anchor"
    - id: "D14-07"
      name: "绩效评语辅助"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D14-06"
        - "D14-04"
      provenance:
        - "d14-anchor"
    - id: "D14-08"
      name: "培训内容生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D14-07"
        - "D14-05"
      provenance:
        - "d14-anchor"
    - id: "D14-09"
      name: "薪酬对标分析"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D14-08"
        - "D14-06"
      provenance:
        - "d14-anchor"
    - id: "D14-10"
      name: "劳动法问答"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D14-09"
        - "D14-07"
      provenance:
        - "d14-anchor"
    - id: "D14-11"
      name: "内部知识助手"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D14-10"
        - "D14-08"
      provenance:
        - "d14-anchor"
    - id: "D14-12"
      name: "招聘合规审查"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D14-11"
        - "D14-09"
      provenance:
        - "d14-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D14-00）不随包交付，装载方须自备领域基础。
