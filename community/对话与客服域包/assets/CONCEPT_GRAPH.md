<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 对话与客服（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「对话与客服」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（对话与客服:M01）与收口模块（对话与客服:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 4 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（E18-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E18-01` | 意图识别 | P40 | — | e18-anchor |
| `E18-02` | 多轮澄清 | P60 | `E18-01` | e18-anchor |
| `E18-03` | 知识问答 | P40 | `E18-02` | e18-anchor |
| `E18-04` | 工单分类 | P60 | `E18-03`、`E18-01` | e18-anchor |
| `E18-05` | 情绪安抚 | P40 | `E18-04`、`E18-02` | e18-anchor |
| `E18-06` | 转人工策略 | P60 | `E18-05`、`E18-03` | e18-anchor |
| `E18-07` | 满意度分析 | P40 | `E18-06`、`E18-04` | e18-anchor |
| `E18-08` | 话术优化 | P60 | `E18-07`、`E18-05` | e18-anchor |
| `E18-09` | 多语客服 | P40 | `E18-08`、`E18-06` | e18-anchor |
| `E18-10` | 质检抽检 | P60 | `E18-09`、`E18-07` | e18-anchor |
| `E18-11` | 坐席辅助 | P40 | `E18-10`、`E18-08` | e18-anchor |
| `E18-12` | 渠道接入 | P60 | `E18-11`、`E18-09` | e18-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `E18-01`、`E18-04`、`E18-07`、`E18-10` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `E18-03` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C） | P80 | `E18-06`、`E18-09`、`E18-12` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `E18-02`、`E18-05`、`E18-08`、`E18-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E18-意图识别` | `E18-01` |
| `E18-多轮澄清` | `E18-02` |
| `E18-知识问答` | `E18-03` |
| `E18-工单分类` | `E18-04` |
| `E18-情绪安抚` | `E18-05` |
| `E18-转人工策略` | `E18-06` |
| `E18-满意度分析` | `E18-07` |
| `E18-话术优化` | `E18-08` |
| `E18-多语客服` | `E18-09` |
| `E18-质检抽检` | `E18-10` |
| `E18-坐席辅助` | `E18-11` |
| `E18-渠道接入` | `E18-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "对话与客服"
  code: "E18"
  provenance_strength: "external"
  provenance_legend:
    e18-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E18-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "对话与客服 全域"
      nodes:
        - "E18-01"
        - "E18-02"
        - "E18-03"
        - "E18-04"
        - "E18-05"
        - "E18-06"
        - "E18-07"
        - "E18-08"
        - "E18-09"
        - "E18-10"
        - "E18-11"
        - "E18-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-frictionless-table"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "E18-01"
      name: "意图识别"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e18-anchor"
    - id: "E18-02"
      name: "多轮澄清"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E18-01"
      provenance:
        - "e18-anchor"
    - id: "E18-03"
      name: "知识问答"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E18-02"
      provenance:
        - "e18-anchor"
    - id: "E18-04"
      name: "工单分类"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E18-03"
        - "E18-01"
      provenance:
        - "e18-anchor"
    - id: "E18-05"
      name: "情绪安抚"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E18-04"
        - "E18-02"
      provenance:
        - "e18-anchor"
    - id: "E18-06"
      name: "转人工策略"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E18-05"
        - "E18-03"
      provenance:
        - "e18-anchor"
    - id: "E18-07"
      name: "满意度分析"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E18-06"
        - "E18-04"
      provenance:
        - "e18-anchor"
    - id: "E18-08"
      name: "话术优化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E18-07"
        - "E18-05"
      provenance:
        - "e18-anchor"
    - id: "E18-09"
      name: "多语客服"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E18-08"
        - "E18-06"
      provenance:
        - "e18-anchor"
    - id: "E18-10"
      name: "质检抽检"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E18-09"
        - "E18-07"
      provenance:
        - "e18-anchor"
    - id: "E18-11"
      name: "坐席辅助"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E18-10"
        - "E18-08"
      provenance:
        - "e18-anchor"
    - id: "E18-12"
      name: "渠道接入"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E18-11"
        - "E18-09"
      provenance:
        - "e18-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E18-01"
        - "E18-04"
        - "E18-07"
        - "E18-10"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E18-03"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E18-06"
        - "E18-09"
        - "E18-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E18-02"
        - "E18-05"
        - "E18-08"
        - "E18-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E18-00）不随包交付，装载方须自备领域基础。
