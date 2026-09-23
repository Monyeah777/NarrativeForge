<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 合成数据生成（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「合成数据生成」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（合成数据生成:M01）与收口模块（合成数据生成:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（C03-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C03-01` | 指令数据合成 | P40 | — | c03-anchor |
| `C03-02` | 角色对话合成 | P60 | `C03-01` | c03-anchor |
| `C03-03` | 领域语料扩写 | P40 | `C03-02` | c03-anchor |
| `C03-04` | 数据配比与去污染 | P60 | `C03-03`、`C03-01` | c03-anchor |
| `C03-05` | 合成数据质检 | P40 | `C03-04`、`C03-02` | c03-anchor |
| `C03-06` | 教师模型蒸馏数据 | P60 | `C03-05`、`C03-03` | c03-anchor |
| `C03-07` | 多样性控制 | P40 | `C03-06`、`C03-04` | c03-anchor |
| `C03-08` | 难例合成 | P60 | `C03-07`、`C03-05` | c03-anchor |
| `C03-09` | 合成数据许可 | P40 | `C03-08`、`C03-06` | c03-anchor |
| `C03-10` | 评测集构造 | P60 | `C03-09`、`C03-07` | c03-anchor |
| `C03-11` | 合成与真实混合 | P40 | `C03-10`、`C03-08` | c03-anchor |
| `C03-12` | 合成数据偏差 | P60 | `C03-11`、`C03-09` | c03-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C03-指令数据合成` | `C03-01` |
| `C03-角色对话合成` | `C03-02` |
| `C03-领域语料扩写` | `C03-03` |
| `C03-数据配比与去污染` | `C03-04` |
| `C03-合成数据质检` | `C03-05` |
| `C03-教师模型蒸馏数据` | `C03-06` |
| `C03-多样性控制` | `C03-07` |
| `C03-难例合成` | `C03-08` |
| `C03-合成数据许可` | `C03-09` |
| `C03-评测集构造` | `C03-10` |
| `C03-合成与真实混合` | `C03-11` |
| `C03-合成数据偏差` | `C03-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "合成数据生成"
  code: "C03"
  provenance_strength: "external"
  provenance_legend:
    c03-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "C03-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "合成数据生成 全域"
      nodes:
        - "C03-01"
        - "C03-02"
        - "C03-03"
        - "C03-04"
        - "C03-05"
        - "C03-06"
        - "C03-07"
        - "C03-08"
        - "C03-09"
        - "C03-10"
        - "C03-11"
        - "C03-12"
  nodes:
    - id: "C03-01"
      name: "指令数据合成"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c03-anchor"
    - id: "C03-02"
      name: "角色对话合成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C03-01"
      provenance:
        - "c03-anchor"
    - id: "C03-03"
      name: "领域语料扩写"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C03-02"
      provenance:
        - "c03-anchor"
    - id: "C03-04"
      name: "数据配比与去污染"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C03-03"
        - "C03-01"
      provenance:
        - "c03-anchor"
    - id: "C03-05"
      name: "合成数据质检"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C03-04"
        - "C03-02"
      provenance:
        - "c03-anchor"
    - id: "C03-06"
      name: "教师模型蒸馏数据"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C03-05"
        - "C03-03"
      provenance:
        - "c03-anchor"
    - id: "C03-07"
      name: "多样性控制"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C03-06"
        - "C03-04"
      provenance:
        - "c03-anchor"
    - id: "C03-08"
      name: "难例合成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C03-07"
        - "C03-05"
      provenance:
        - "c03-anchor"
    - id: "C03-09"
      name: "合成数据许可"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C03-08"
        - "C03-06"
      provenance:
        - "c03-anchor"
    - id: "C03-10"
      name: "评测集构造"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C03-09"
        - "C03-07"
      provenance:
        - "c03-anchor"
    - id: "C03-11"
      name: "合成与真实混合"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C03-10"
        - "C03-08"
      provenance:
        - "c03-anchor"
    - id: "C03-12"
      name: "合成数据偏差"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C03-11"
        - "C03-09"
      provenance:
        - "c03-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C03-00）不随包交付，装载方须自备领域基础。
