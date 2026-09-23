<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 企业培训与组织学习（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「企业培训与组织学习」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（企业培训与组织学习:M01）与收口模块（企业培训与组织学习:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（E15-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E15-01` | 新员工培训 | P40 | — | e15-anchor |
| `E15-02` | 培训合规要求 | P60 | `E15-01` | e15-anchor |
| `E15-03` | 销售话术训练 | P40 | `E15-02` | e15-anchor |
| `E15-04` | 岗位技能图谱 | P60 | `E15-03`、`E15-01` | e15-anchor |
| `E15-05` | 微课生成 | P40 | `E15-04`、`E15-02` | e15-anchor |
| `E15-06` | 陪练与考核 | P60 | `E15-05`、`E15-03` | e15-anchor |
| `E15-07` | 培训效果评估 | P40 | `E15-06`、`E15-04` | e15-anchor |
| `E15-08` | 知识沉淀 | P60 | `E15-07`、`E15-05` | e15-anchor |
| `E15-09` | 讲师助手 | P40 | `E15-08`、`E15-06` | e15-anchor |
| `E15-10` | 学习路径设计 | P60 | `E15-09`、`E15-07` | e15-anchor |
| `E15-11` | 跨文化培训 | P40 | `E15-10`、`E15-08` | e15-anchor |
| `E15-12` | 培训记录管理 | P60 | `E15-11`、`E15-09` | e15-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `E15-04`、`E15-10` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU） | P80 | `E15-02` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `E15-03` | std-catalog |
| `STD-unesco-ai` | 标准 · AI 伦理建议书（UNESCO） | P80 | `E15-01`、`E15-07`、`E15-11`、`E15-12` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C） | P80 | `E15-06`、`E15-09` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `E15-05`、`E15-08` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E15-新员工培训` | `E15-01` |
| `E15-培训合规要求` | `E15-02` |
| `E15-销售话术训练` | `E15-03` |
| `E15-岗位技能图谱` | `E15-04` |
| `E15-微课生成` | `E15-05` |
| `E15-陪练与考核` | `E15-06` |
| `E15-培训效果评估` | `E15-07` |
| `E15-知识沉淀` | `E15-08` |
| `E15-讲师助手` | `E15-09` |
| `E15-学习路径设计` | `E15-10` |
| `E15-跨文化培训` | `E15-11` |
| `E15-培训记录管理` | `E15-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-gdpr` | `STD-gdpr` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-unesco-ai` | `STD-unesco-ai` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "企业培训与组织学习"
  code: "E15"
  provenance_strength: "external"
  provenance_legend:
    e15-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E15-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "企业培训与组织学习 全域"
      nodes:
        - "E15-01"
        - "E15-02"
        - "E15-03"
        - "E15-04"
        - "E15-05"
        - "E15-06"
        - "E15-07"
        - "E15-08"
        - "E15-09"
        - "E15-10"
        - "E15-11"
        - "E15-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-gdpr"
        - "STD-mlcommons-bench"
        - "STD-unesco-ai"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "E15-01"
      name: "新员工培训"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e15-anchor"
    - id: "E15-02"
      name: "培训合规要求"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E15-01"
      provenance:
        - "e15-anchor"
    - id: "E15-03"
      name: "销售话术训练"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E15-02"
      provenance:
        - "e15-anchor"
    - id: "E15-04"
      name: "岗位技能图谱"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E15-03"
        - "E15-01"
      provenance:
        - "e15-anchor"
    - id: "E15-05"
      name: "微课生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E15-04"
        - "E15-02"
      provenance:
        - "e15-anchor"
    - id: "E15-06"
      name: "陪练与考核"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E15-05"
        - "E15-03"
      provenance:
        - "e15-anchor"
    - id: "E15-07"
      name: "培训效果评估"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E15-06"
        - "E15-04"
      provenance:
        - "e15-anchor"
    - id: "E15-08"
      name: "知识沉淀"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E15-07"
        - "E15-05"
      provenance:
        - "e15-anchor"
    - id: "E15-09"
      name: "讲师助手"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E15-08"
        - "E15-06"
      provenance:
        - "e15-anchor"
    - id: "E15-10"
      name: "学习路径设计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E15-09"
        - "E15-07"
      provenance:
        - "e15-anchor"
    - id: "E15-11"
      name: "跨文化培训"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E15-10"
        - "E15-08"
      provenance:
        - "e15-anchor"
    - id: "E15-12"
      name: "培训记录管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E15-11"
        - "E15-09"
      provenance:
        - "e15-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E15-04"
        - "E15-10"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E15-02"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E15-03"
      provenance:
        - "std-catalog"
    - id: "STD-unesco-ai"
      name: "标准 · AI 伦理建议书"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E15-01"
        - "E15-07"
        - "E15-11"
        - "E15-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E15-06"
        - "E15-09"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E15-05"
        - "E15-08"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E15-00）不随包交付，装载方须自备领域基础。
