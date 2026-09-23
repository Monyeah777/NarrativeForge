<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 智能体与工作流编排（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「智能体与工作流编排」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（智能体与工作流编排:M01）与收口模块（智能体与工作流编排:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 7 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（E12-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E12-01` | 多智能体分工 | P40 | — | e12-anchor |
| `E12-02` | 工具调用 | P60 | `E12-01` | e12-anchor |
| `E12-03` | 规划与反思 | P40 | `E12-02` | e12-anchor |
| `E12-04` | 任务分解 | P60 | `E12-03`、`E12-01` | e12-anchor |
| `E12-05` | 状态机与重试 | P40 | `E12-04`、`E12-02` | e12-anchor |
| `E12-06` | 人工审批节点 | P60 | `E12-05`、`E12-03` | e12-anchor |
| `E12-07` | 事件触发 | P40 | `E12-06`、`E12-04` | e12-anchor |
| `E12-08` | 长任务记忆 | P60 | `E12-07`、`E12-05` | e12-anchor |
| `E12-09` | 失败兜底 | P40 | `E12-08`、`E12-06` | e12-anchor |
| `E12-10` | 成本控制 | P60 | `E12-09`、`E12-07` | e12-anchor |
| `E12-11` | 可观测性 | P40 | `E12-10`、`E12-08` | e12-anchor |
| `E12-12` | 编排规范定义 | P60 | `E12-11`、`E12-09` | e12-anchor |
| `STD-a2a` | 标准 · A2A 协议（Linux Foundation） | P80 | `E12-12` | std-catalog |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF） | P80 | `E12-07` | std-catalog |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry） | P80 | `E12-10`、`E12-11` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `E12-04` | std-catalog |
| `STD-mcp` | 标准 · Model Context Protocol（Anthropic/MCP） | P80 | `E12-01`、`E12-02` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C） | P80 | `E12-03`、`E12-06`、`E12-09` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `E12-05`、`E12-08` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E12-多智能体分工` | `E12-01` |
| `E12-工具调用` | `E12-02` |
| `E12-规划与反思` | `E12-03` |
| `E12-任务分解` | `E12-04` |
| `E12-状态机与重试` | `E12-05` |
| `E12-人工审批节点` | `E12-06` |
| `E12-事件触发` | `E12-07` |
| `E12-长任务记忆` | `E12-08` |
| `E12-失败兜底` | `E12-09` |
| `E12-成本控制` | `E12-10` |
| `E12-可观测性` | `E12-11` |
| `E12-编排规范定义` | `E12-12` |
| `std-a2a` | `STD-a2a` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-mcp` | `STD-mcp` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "智能体与工作流编排"
  code: "E12"
  provenance_strength: "external"
  provenance_legend:
    e12-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E12-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "智能体与工作流编排 全域"
      nodes:
        - "E12-01"
        - "E12-02"
        - "E12-03"
        - "E12-04"
        - "E12-05"
        - "E12-06"
        - "E12-07"
        - "E12-08"
        - "E12-09"
        - "E12-10"
        - "E12-11"
        - "E12-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-a2a"
        - "STD-cncf-cloudevents"
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-mcp"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "E12-01"
      name: "多智能体分工"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e12-anchor"
    - id: "E12-02"
      name: "工具调用"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E12-01"
      provenance:
        - "e12-anchor"
    - id: "E12-03"
      name: "规划与反思"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E12-02"
      provenance:
        - "e12-anchor"
    - id: "E12-04"
      name: "任务分解"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E12-03"
        - "E12-01"
      provenance:
        - "e12-anchor"
    - id: "E12-05"
      name: "状态机与重试"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E12-04"
        - "E12-02"
      provenance:
        - "e12-anchor"
    - id: "E12-06"
      name: "人工审批节点"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E12-05"
        - "E12-03"
      provenance:
        - "e12-anchor"
    - id: "E12-07"
      name: "事件触发"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E12-06"
        - "E12-04"
      provenance:
        - "e12-anchor"
    - id: "E12-08"
      name: "长任务记忆"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E12-07"
        - "E12-05"
      provenance:
        - "e12-anchor"
    - id: "E12-09"
      name: "失败兜底"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E12-08"
        - "E12-06"
      provenance:
        - "e12-anchor"
    - id: "E12-10"
      name: "成本控制"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E12-09"
        - "E12-07"
      provenance:
        - "e12-anchor"
    - id: "E12-11"
      name: "可观测性"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E12-10"
        - "E12-08"
      provenance:
        - "e12-anchor"
    - id: "E12-12"
      name: "编排规范定义"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E12-11"
        - "E12-09"
      provenance:
        - "e12-anchor"
    - id: "STD-a2a"
      name: "标准 · A2A 协议"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E12-12"
      provenance:
        - "std-catalog"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E12-07"
      provenance:
        - "std-catalog"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E12-10"
        - "E12-11"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E12-04"
      provenance:
        - "std-catalog"
    - id: "STD-mcp"
      name: "标准 · Model Context Protocol"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E12-01"
        - "E12-02"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E12-03"
        - "E12-06"
        - "E12-09"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E12-05"
        - "E12-08"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E12-00）不随包交付，装载方须自备领域基础。
