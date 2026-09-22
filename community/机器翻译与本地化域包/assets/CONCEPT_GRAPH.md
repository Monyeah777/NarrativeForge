<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 机器翻译与本地化（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「机器翻译与本地化」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（机器翻译与本地化:M01）与收口模块（机器翻译与本地化:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（B03-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B03-01` | 通用文本翻译 | P40 | — | b03-anchor |
| `B03-02` | 领域术语翻译 | P60 | `B03-01` | b03-anchor |
| `B03-03` | 文学与风格翻译 | P40 | `B03-01` | b03-anchor |
| `B03-04` | 口语与字幕翻译 | P60 | — | b03-anchor |
| `B03-05` | 格式保留翻译 | P40 | — | b03-anchor |
| `B03-06` | 多语种并行 | P60 | `B03-05` | b03-anchor |
| `B03-07` | 术语库与翻译记忆 | P40 | `B03-02` | b03-anchor |
| `B03-08` | 本地化与地区变体 | P60 | — | b03-anchor |
| `B03-09` | 译后编辑与人工审校 | P40 | `B03-04`、`B03-07` | b03-anchor |
| `B03-10` | 低资源语言 | P60 | `B03-06` | b03-anchor |
| `B03-11` | 翻译质量评估 | P40 | `B03-09`、`B03-02` | b03-anchor |
| `B03-12` | 文化适配与合规 | P60 | `B03-08` | b03-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B03-通用文本翻译` | `B03-01` |
| `B03-领域术语翻译` | `B03-02` |
| `B03-文学与风格翻译` | `B03-03` |
| `B03-口语与字幕翻译` | `B03-04` |
| `B03-格式保留翻译` | `B03-05` |
| `B03-多语种并行` | `B03-06` |
| `B03-术语库与翻译记忆` | `B03-07` |
| `B03-本地化与地区变体` | `B03-08` |
| `B03-译后编辑与人工审校` | `B03-09` |
| `B03-低资源语言` | `B03-10` |
| `B03-翻译质量评估` | `B03-11` |
| `B03-文化适配与合规` | `B03-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "机器翻译与本地化"
  code: "B03"
  provenance_strength: "external"
  provenance_legend:
    b03-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "B03-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "机器翻译与本地化 全域"
      nodes:
        - "B03-01"
        - "B03-02"
        - "B03-03"
        - "B03-04"
        - "B03-05"
        - "B03-06"
        - "B03-07"
        - "B03-08"
        - "B03-09"
        - "B03-10"
        - "B03-11"
        - "B03-12"
  nodes:
    - id: "B03-01"
      name: "通用文本翻译"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b03-anchor"
    - id: "B03-02"
      name: "领域术语翻译"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B03-01"
      provenance:
        - "b03-anchor"
    - id: "B03-03"
      name: "文学与风格翻译"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B03-01"
      provenance:
        - "b03-anchor"
    - id: "B03-04"
      name: "口语与字幕翻译"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b03-anchor"
    - id: "B03-05"
      name: "格式保留翻译"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b03-anchor"
    - id: "B03-06"
      name: "多语种并行"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B03-05"
      provenance:
        - "b03-anchor"
    - id: "B03-07"
      name: "术语库与翻译记忆"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B03-02"
      provenance:
        - "b03-anchor"
    - id: "B03-08"
      name: "本地化与地区变体"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b03-anchor"
    - id: "B03-09"
      name: "译后编辑与人工审校"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B03-04"
        - "B03-07"
      provenance:
        - "b03-anchor"
    - id: "B03-10"
      name: "低资源语言"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B03-06"
      provenance:
        - "b03-anchor"
    - id: "B03-11"
      name: "翻译质量评估"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B03-09"
        - "B03-02"
      provenance:
        - "b03-anchor"
    - id: "B03-12"
      name: "文化适配与合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B03-08"
      provenance:
        - "b03-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B03-00）不随包交付，装载方须自备领域基础。
