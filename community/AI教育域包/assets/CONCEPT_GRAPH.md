<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+教育（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+教育」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI教育:M01）与收口模块（AI教育:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（D06-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D06-01` | 课程设计与教案 | P40 | — | d06-anchor |
| `D06-02` | 题目生成与组卷 | P60 | `D06-01` | d06-anchor |
| `D06-03` | 作业批改与反馈 | P40 | `D06-02` | d06-anchor |
| `D06-04` | 学情分析 | P60 | `D06-03`、`D06-01` | d06-anchor |
| `D06-05` | 个性化学习路径 | P40 | `D06-04`、`D06-02` | d06-anchor |
| `D06-06` | 知识点图谱 | P60 | `D06-05`、`D06-03` | d06-anchor |
| `D06-07` | 教材与讲义撰写 | P40 | `D06-06`、`D06-04` | d06-anchor |
| `D06-08` | 语言学习陪练 | P60 | `D06-07`、`D06-05` | d06-anchor |
| `D06-09` | 教师备课助手 | P40 | `D06-08`、`D06-06` | d06-anchor |
| `D06-10` | 教育评测 | P60 | `D06-09`、`D06-07` | d06-anchor |
| `D06-11` | 学生数据隐私 | P40 | `D06-10`、`D06-08` | d06-anchor |
| `D06-12` | 学术诚信边界 | P60 | `D06-11`、`D06-09` | d06-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D06-课程设计与教案` | `D06-01` |
| `D06-题目生成与组卷` | `D06-02` |
| `D06-作业批改与反馈` | `D06-03` |
| `D06-学情分析` | `D06-04` |
| `D06-个性化学习路径` | `D06-05` |
| `D06-知识点图谱` | `D06-06` |
| `D06-教材与讲义撰写` | `D06-07` |
| `D06-语言学习陪练` | `D06-08` |
| `D06-教师备课助手` | `D06-09` |
| `D06-教育评测` | `D06-10` |
| `D06-学生数据隐私` | `D06-11` |
| `D06-学术诚信边界` | `D06-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+教育"
  code: "D06"
  provenance_strength: "external"
  provenance_legend:
    d06-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "D06-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+教育 全域"
      nodes:
        - "D06-01"
        - "D06-02"
        - "D06-03"
        - "D06-04"
        - "D06-05"
        - "D06-06"
        - "D06-07"
        - "D06-08"
        - "D06-09"
        - "D06-10"
        - "D06-11"
        - "D06-12"
  nodes:
    - id: "D06-01"
      name: "课程设计与教案"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d06-anchor"
    - id: "D06-02"
      name: "题目生成与组卷"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D06-01"
      provenance:
        - "d06-anchor"
    - id: "D06-03"
      name: "作业批改与反馈"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D06-02"
      provenance:
        - "d06-anchor"
    - id: "D06-04"
      name: "学情分析"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D06-03"
        - "D06-01"
      provenance:
        - "d06-anchor"
    - id: "D06-05"
      name: "个性化学习路径"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D06-04"
        - "D06-02"
      provenance:
        - "d06-anchor"
    - id: "D06-06"
      name: "知识点图谱"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D06-05"
        - "D06-03"
      provenance:
        - "d06-anchor"
    - id: "D06-07"
      name: "教材与讲义撰写"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D06-06"
        - "D06-04"
      provenance:
        - "d06-anchor"
    - id: "D06-08"
      name: "语言学习陪练"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D06-07"
        - "D06-05"
      provenance:
        - "d06-anchor"
    - id: "D06-09"
      name: "教师备课助手"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D06-08"
        - "D06-06"
      provenance:
        - "d06-anchor"
    - id: "D06-10"
      name: "教育评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D06-09"
        - "D06-07"
      provenance:
        - "d06-anchor"
    - id: "D06-11"
      name: "学生数据隐私"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D06-10"
        - "D06-08"
      provenance:
        - "d06-anchor"
    - id: "D06-12"
      name: "学术诚信边界"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D06-11"
        - "D06-09"
      provenance:
        - "d06-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D06-00）不随包交付，装载方须自备领域基础。
