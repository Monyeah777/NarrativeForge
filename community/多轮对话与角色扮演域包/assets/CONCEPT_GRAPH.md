<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 多轮对话与角色扮演（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「多轮对话与角色扮演」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（多轮对话与角色扮演:M01）与收口模块（多轮对话与角色扮演:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 7 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（B07-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B07-01` | 人设与语气一致性 | P40 | `B07-02`、`B07-03` | b07-anchor |
| `B07-02` | 角色卡字段规范 | P60 | — | b07-anchor |
| `B07-03` | 世界书与设定注入 | P40 | — | b07-anchor |
| `B07-04` | 对话状态与上下文管理 | P60 | `B07-01` | b07-anchor |
| `B07-05` | 多角色群聊调度 | P40 | `B07-04` | b07-anchor |
| `B07-06` | 越界与安全边界 | P60 | — | b07-anchor |
| `B07-07` | 情感走向与关系进度 | P40 | `B07-04` | b07-anchor |
| `B07-08` | 场景切换与时间线 | P60 | `B07-04` | b07-anchor |
| `B07-09` | 开场白与示例对话 | P40 | — | b07-anchor |
| `B07-10` | 长期记忆与回溯 | P60 | `B07-09` | b07-anchor |
| `B07-11` | 角色扮演评测 | P40 | `B07-10`、`B07-08` | b07-anchor |
| `B07-12` | 沉浸感与打断处理 | P60 | `B07-06` | b07-anchor |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `B07-03`、`B07-09`、`B07-12` | std-catalog |
| `STD-gfm` | 标准 · GFM 扩展（GitHub） | P80 | `B07-04` | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema） | P80 | `B07-01`、`B07-07`、`B07-10` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `B07-11` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP） | P80 | `B07-06` | std-catalog |
| `STD-w3c-owl-time` | 标准 · OWL-Time 时间本体（W3C） | P80 | `B07-08` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `B07-02`、`B07-05` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B07-人设与语气一致性` | `B07-01` |
| `B07-角色卡字段规范` | `B07-02` |
| `B07-世界书与设定注入` | `B07-03` |
| `B07-对话状态与上下文管理` | `B07-04` |
| `B07-多角色群聊调度` | `B07-05` |
| `B07-越界与安全边界` | `B07-06` |
| `B07-情感走向与关系进度` | `B07-07` |
| `B07-场景切换与时间线` | `B07-08` |
| `B07-开场白与示例对话` | `B07-09` |
| `B07-长期记忆与回溯` | `B07-10` |
| `B07-角色扮演评测` | `B07-11` |
| `B07-沉浸感与打断处理` | `B07-12` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-gfm` | `STD-gfm` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-w3c-owl-time` | `STD-w3c-owl-time` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "多轮对话与角色扮演"
  code: "B07"
  provenance_strength: "external"
  provenance_legend:
    b07-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B07-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "多轮对话与角色扮演 全域"
      nodes:
        - "B07-01"
        - "B07-02"
        - "B07-03"
        - "B07-04"
        - "B07-05"
        - "B07-06"
        - "B07-07"
        - "B07-08"
        - "B07-09"
        - "B07-10"
        - "B07-11"
        - "B07-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-frictionless-table"
        - "STD-gfm"
        - "STD-ietf-json-schema"
        - "STD-mlcommons-bench"
        - "STD-owasp-llm"
        - "STD-w3c-owl-time"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "B07-01"
      name: "人设与语气一致性"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B07-02"
        - "B07-03"
      provenance:
        - "b07-anchor"
    - id: "B07-02"
      name: "角色卡字段规范"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b07-anchor"
    - id: "B07-03"
      name: "世界书与设定注入"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b07-anchor"
    - id: "B07-04"
      name: "对话状态与上下文管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B07-01"
      provenance:
        - "b07-anchor"
    - id: "B07-05"
      name: "多角色群聊调度"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B07-04"
      provenance:
        - "b07-anchor"
    - id: "B07-06"
      name: "越界与安全边界"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b07-anchor"
    - id: "B07-07"
      name: "情感走向与关系进度"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B07-04"
      provenance:
        - "b07-anchor"
    - id: "B07-08"
      name: "场景切换与时间线"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B07-04"
      provenance:
        - "b07-anchor"
    - id: "B07-09"
      name: "开场白与示例对话"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b07-anchor"
    - id: "B07-10"
      name: "长期记忆与回溯"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B07-09"
      provenance:
        - "b07-anchor"
    - id: "B07-11"
      name: "角色扮演评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B07-10"
        - "B07-08"
      provenance:
        - "b07-anchor"
    - id: "B07-12"
      name: "沉浸感与打断处理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B07-06"
      provenance:
        - "b07-anchor"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B07-03"
        - "B07-09"
        - "B07-12"
      provenance:
        - "std-catalog"
    - id: "STD-gfm"
      name: "标准 · GFM 扩展"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B07-04"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B07-01"
        - "B07-07"
        - "B07-10"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B07-11"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B07-06"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-owl-time"
      name: "标准 · OWL-Time 时间本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B07-08"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B07-02"
        - "B07-05"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B07-00）不随包交付，装载方须自备领域基础。
