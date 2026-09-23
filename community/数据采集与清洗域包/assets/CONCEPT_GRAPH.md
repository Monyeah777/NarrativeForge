<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 数据采集与清洗（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「数据采集与清洗」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（数据采集与清洗:M01）与收口模块（数据采集与清洗:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 3 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（C01-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C01-01` | 网页抓取与合规 | P40 | — | c01-anchor |
| `C01-02` | 去重与相似度 | P60 | `C01-01` | c01-anchor |
| `C01-03` | 噪声过滤 | P40 | `C01-02` | c01-anchor |
| `C01-04` | 格式归一化 | P60 | `C01-03`、`C01-01` | c01-anchor |
| `C01-05` | 缺失与异常值 | P40 | `C01-04`、`C01-02` | c01-anchor |
| `C01-06` | 隐私脱敏 | P60 | `C01-05`、`C01-03` | c01-anchor |
| `C01-07` | 多语言清洗 | P40 | `C01-06`、`C01-04` | c01-anchor |
| `C01-08` | 语料配比与统计 | P60 | `C01-07`、`C01-05` | c01-anchor |
| `C01-09` | 数据版本与快照 | P40 | `C01-08`、`C01-06` | c01-anchor |
| `C01-10` | 数据血缘 | P60 | `C01-09`、`C01-07` | c01-anchor |
| `C01-11` | 质量打分 | P40 | `C01-10`、`C01-08` | c01-anchor |
| `C01-12` | 脏数据回溯 | P60 | `C01-11`、`C01-09` | c01-anchor |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `C01-03`、`C01-05`、`C01-07`、`C01-09`、`C01-11` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU） | P80 | `C01-01`、`C01-06` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `C01-02`、`C01-04`、`C01-08`、`C01-10`、`C01-12` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C01-网页抓取与合规` | `C01-01` |
| `C01-去重与相似度` | `C01-02` |
| `C01-噪声过滤` | `C01-03` |
| `C01-格式归一化` | `C01-04` |
| `C01-缺失与异常值` | `C01-05` |
| `C01-隐私脱敏` | `C01-06` |
| `C01-多语言清洗` | `C01-07` |
| `C01-语料配比与统计` | `C01-08` |
| `C01-数据版本与快照` | `C01-09` |
| `C01-数据血缘` | `C01-10` |
| `C01-质量打分` | `C01-11` |
| `C01-脏数据回溯` | `C01-12` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-gdpr` | `STD-gdpr` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "数据采集与清洗"
  code: "C01"
  provenance_strength: "external"
  provenance_legend:
    c01-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C01-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "数据采集与清洗 全域"
      nodes:
        - "C01-01"
        - "C01-02"
        - "C01-03"
        - "C01-04"
        - "C01-05"
        - "C01-06"
        - "C01-07"
        - "C01-08"
        - "C01-09"
        - "C01-10"
        - "C01-11"
        - "C01-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-frictionless-table"
        - "STD-gdpr"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "C01-01"
      name: "网页抓取与合规"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c01-anchor"
    - id: "C01-02"
      name: "去重与相似度"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C01-01"
      provenance:
        - "c01-anchor"
    - id: "C01-03"
      name: "噪声过滤"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C01-02"
      provenance:
        - "c01-anchor"
    - id: "C01-04"
      name: "格式归一化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C01-03"
        - "C01-01"
      provenance:
        - "c01-anchor"
    - id: "C01-05"
      name: "缺失与异常值"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C01-04"
        - "C01-02"
      provenance:
        - "c01-anchor"
    - id: "C01-06"
      name: "隐私脱敏"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C01-05"
        - "C01-03"
      provenance:
        - "c01-anchor"
    - id: "C01-07"
      name: "多语言清洗"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C01-06"
        - "C01-04"
      provenance:
        - "c01-anchor"
    - id: "C01-08"
      name: "语料配比与统计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C01-07"
        - "C01-05"
      provenance:
        - "c01-anchor"
    - id: "C01-09"
      name: "数据版本与快照"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C01-08"
        - "C01-06"
      provenance:
        - "c01-anchor"
    - id: "C01-10"
      name: "数据血缘"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C01-09"
        - "C01-07"
      provenance:
        - "c01-anchor"
    - id: "C01-11"
      name: "质量打分"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C01-10"
        - "C01-08"
      provenance:
        - "c01-anchor"
    - id: "C01-12"
      name: "脏数据回溯"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C01-11"
        - "C01-09"
      provenance:
        - "c01-anchor"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C01-03"
        - "C01-05"
        - "C01-07"
        - "C01-09"
        - "C01-11"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C01-01"
        - "C01-06"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C01-02"
        - "C01-04"
        - "C01-08"
        - "C01-10"
        - "C01-12"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C01-00）不随包交付，装载方须自备领域基础。
