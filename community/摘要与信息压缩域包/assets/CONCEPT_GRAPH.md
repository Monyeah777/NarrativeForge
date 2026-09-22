<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 摘要与信息压缩（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「摘要与信息压缩」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（摘要与信息压缩:M01）与收口模块（摘要与信息压缩:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（B02-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B02-01` | 抽取式摘要 | P40 | — | b02-anchor |
| `B02-02` | 生成式摘要 | P60 | `B02-01` | b02-anchor |
| `B02-03` | 多文档摘要 | P40 | `B02-02` | b02-anchor |
| `B02-04` | 会议纪要压缩 | P60 | — | b02-anchor |
| `B02-05` | 层级摘要 | P40 | `B02-03`、`B02-04` | b02-anchor |
| `B02-06` | 要点抽取与结构化 | P60 | — | b02-anchor |
| `B02-07` | 长文压缩比控制 | P40 | `B02-06` | b02-anchor |
| `B02-08` | 忠实性与幻觉检测 | P60 | `B02-07` | b02-anchor |
| `B02-09` | 要点权重排序 | P40 | `B02-06` | b02-anchor |
| `B02-10` | 多语言摘要 | P60 | `B02-05` | b02-anchor |
| `B02-11` | 摘要质量评测 | P40 | `B02-08` | b02-anchor |
| `B02-12` | 增量摘要 | P60 | `B02-03` | b02-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B02-抽取式摘要` | `B02-01` |
| `B02-生成式摘要` | `B02-02` |
| `B02-多文档摘要` | `B02-03` |
| `B02-会议纪要压缩` | `B02-04` |
| `B02-层级摘要` | `B02-05` |
| `B02-要点抽取与结构化` | `B02-06` |
| `B02-长文压缩比控制` | `B02-07` |
| `B02-忠实性与幻觉检测` | `B02-08` |
| `B02-要点权重排序` | `B02-09` |
| `B02-多语言摘要` | `B02-10` |
| `B02-摘要质量评测` | `B02-11` |
| `B02-增量摘要` | `B02-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "摘要与信息压缩"
  code: "B02"
  provenance_strength: "external"
  provenance_legend:
    b02-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "B02-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "摘要与信息压缩 全域"
      nodes:
        - "B02-01"
        - "B02-02"
        - "B02-03"
        - "B02-04"
        - "B02-05"
        - "B02-06"
        - "B02-07"
        - "B02-08"
        - "B02-09"
        - "B02-10"
        - "B02-11"
        - "B02-12"
  nodes:
    - id: "B02-01"
      name: "抽取式摘要"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b02-anchor"
    - id: "B02-02"
      name: "生成式摘要"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B02-01"
      provenance:
        - "b02-anchor"
    - id: "B02-03"
      name: "多文档摘要"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B02-02"
      provenance:
        - "b02-anchor"
    - id: "B02-04"
      name: "会议纪要压缩"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b02-anchor"
    - id: "B02-05"
      name: "层级摘要"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B02-03"
        - "B02-04"
      provenance:
        - "b02-anchor"
    - id: "B02-06"
      name: "要点抽取与结构化"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b02-anchor"
    - id: "B02-07"
      name: "长文压缩比控制"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B02-06"
      provenance:
        - "b02-anchor"
    - id: "B02-08"
      name: "忠实性与幻觉检测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B02-07"
      provenance:
        - "b02-anchor"
    - id: "B02-09"
      name: "要点权重排序"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B02-06"
      provenance:
        - "b02-anchor"
    - id: "B02-10"
      name: "多语言摘要"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B02-05"
      provenance:
        - "b02-anchor"
    - id: "B02-11"
      name: "摘要质量评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B02-08"
      provenance:
        - "b02-anchor"
    - id: "B02-12"
      name: "增量摘要"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B02-03"
      provenance:
        - "b02-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B02-00）不随包交付，装载方须自备领域基础。
