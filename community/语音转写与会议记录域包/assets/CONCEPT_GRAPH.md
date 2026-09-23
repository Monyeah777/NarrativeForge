<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 语音转写与会议记录（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「语音转写与会议记录」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（语音转写与会议记录:M01）与收口模块（语音转写与会议记录:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（B13-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B13-01` | 实时转写 | P40 | — | b13-anchor |
| `B13-02` | 说话人分段 | P60 | `B13-01` | b13-anchor |
| `B13-03` | 会议摘要与待办 | P40 | `B13-02` | b13-anchor |
| `B13-04` | 专有名词与热词 | P60 | `B13-03`、`B13-01` | b13-anchor |
| `B13-05` | 术语纠错 | P40 | `B13-04`、`B13-02` | b13-anchor |
| `B13-06` | 时间戳与章节 | P60 | `B13-05`、`B13-03` | b13-anchor |
| `B13-07` | 双语会议 | P40 | `B13-06`、`B13-04` | b13-anchor |
| `B13-08` | 语音搜索索引 | P60 | `B13-07`、`B13-05` | b13-anchor |
| `B13-09` | 转写质量评测 | P40 | `B13-08`、`B13-06` | b13-anchor |
| `B13-10` | 录音隐私与合规 | P60 | `B13-09`、`B13-07` | b13-anchor |
| `B13-11` | 方言会议 | P40 | `B13-10`、`B13-08` | b13-anchor |
| `B13-12` | 行动项跟踪 | P60 | `B13-11`、`B13-09` | b13-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B13-实时转写` | `B13-01` |
| `B13-说话人分段` | `B13-02` |
| `B13-会议摘要与待办` | `B13-03` |
| `B13-专有名词与热词` | `B13-04` |
| `B13-术语纠错` | `B13-05` |
| `B13-时间戳与章节` | `B13-06` |
| `B13-双语会议` | `B13-07` |
| `B13-语音搜索索引` | `B13-08` |
| `B13-转写质量评测` | `B13-09` |
| `B13-录音隐私与合规` | `B13-10` |
| `B13-方言会议` | `B13-11` |
| `B13-行动项跟踪` | `B13-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "语音转写与会议记录"
  code: "B13"
  provenance_strength: "external"
  provenance_legend:
    b13-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "B13-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "语音转写与会议记录 全域"
      nodes:
        - "B13-01"
        - "B13-02"
        - "B13-03"
        - "B13-04"
        - "B13-05"
        - "B13-06"
        - "B13-07"
        - "B13-08"
        - "B13-09"
        - "B13-10"
        - "B13-11"
        - "B13-12"
  nodes:
    - id: "B13-01"
      name: "实时转写"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b13-anchor"
    - id: "B13-02"
      name: "说话人分段"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B13-01"
      provenance:
        - "b13-anchor"
    - id: "B13-03"
      name: "会议摘要与待办"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B13-02"
      provenance:
        - "b13-anchor"
    - id: "B13-04"
      name: "专有名词与热词"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B13-03"
        - "B13-01"
      provenance:
        - "b13-anchor"
    - id: "B13-05"
      name: "术语纠错"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B13-04"
        - "B13-02"
      provenance:
        - "b13-anchor"
    - id: "B13-06"
      name: "时间戳与章节"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B13-05"
        - "B13-03"
      provenance:
        - "b13-anchor"
    - id: "B13-07"
      name: "双语会议"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B13-06"
        - "B13-04"
      provenance:
        - "b13-anchor"
    - id: "B13-08"
      name: "语音搜索索引"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B13-07"
        - "B13-05"
      provenance:
        - "b13-anchor"
    - id: "B13-09"
      name: "转写质量评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B13-08"
        - "B13-06"
      provenance:
        - "b13-anchor"
    - id: "B13-10"
      name: "录音隐私与合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B13-09"
        - "B13-07"
      provenance:
        - "b13-anchor"
    - id: "B13-11"
      name: "方言会议"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B13-10"
        - "B13-08"
      provenance:
        - "b13-anchor"
    - id: "B13-12"
      name: "行动项跟踪"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B13-11"
        - "B13-09"
      provenance:
        - "b13-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B13-00）不随包交付，装载方须自备领域基础。
