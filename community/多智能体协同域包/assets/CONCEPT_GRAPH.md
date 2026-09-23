<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 多智能体协同（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「多智能体协同」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（多智能体协同:M01）与收口模块（多智能体协同:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 12 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（C17-00 领域通用前置）；节点 24 · 边 49 · 密度 2.0417。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C17-01` | 角色分工与协议 | P40 | — | c17-anchor |
| `C17-02` | 消息传递格式 | P60 | `C17-01` | c17-anchor |
| `C17-03` | 任务分解与分配 | P40 | `C17-02` | c17-anchor |
| `C17-04` | 共识与仲裁 | P60 | `C17-03`、`C17-01` | c17-anchor |
| `C17-05` | 工作流 DAG | P40 | `C17-04`、`C17-02` | c17-anchor |
| `C17-06` | 条件分支与循环 | P60 | `C17-05`、`C17-03` | c17-anchor |
| `C17-07` | 人工介入节点 | P40 | `C17-06`、`C17-04` | c17-anchor |
| `C17-08` | 失败隔离 | P60 | `C17-07`、`C17-05` | c17-anchor |
| `C17-09` | 编排可观测性 | P40 | `C17-08`、`C17-06` | c17-anchor |
| `C17-10` | 多智能体评测 | P60 | `C17-09`、`C17-07` | c17-anchor |
| `C17-11` | 成本与并发控制 | P40 | `C17-10`、`C17-08` | c17-anchor |
| `C17-12` | 编排模式库 | P60 | `C17-11`、`C17-09` | c17-anchor |
| `STD-a2a` | 标准 · A2A 协议（Linux Foundation｜iface｜实测 ✓） | P80 | `C17-01`、`C17-03`、`C17-07`、`C17-12` | std-catalog |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `C17-02`、`C17-05`、`STD-ietf-json-schema` | std-catalog |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `C17-09`、`C17-11` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `C17-01`、`C17-06`、`C17-09`、`C17-10`、`STD-ietf-json` | std-catalog |
| `STD-jsonrpc` | 标准 · JSON-RPC 2.0（JSON-RPC｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-mcp` | 标准 · Model Context Protocol（Anthropic/MCP｜iface｜实测 ✓） | P80 | `C17-04`、`C17-05`、`C17-06`、`C17-08`、`STD-jsonrpc` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `C17-04` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `C17-10` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `C17-03`、`C17-08`、`C17-11`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `C17-02`、`C17-07`、`C17-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C17-角色分工与协议` | `C17-01` |
| `C17-消息传递格式` | `C17-02` |
| `C17-任务分解与分配` | `C17-03` |
| `C17-共识与仲裁` | `C17-04` |
| `C17-工作流-DAG` | `C17-05` |
| `C17-条件分支与循环` | `C17-06` |
| `C17-人工介入节点` | `C17-07` |
| `C17-失败隔离` | `C17-08` |
| `C17-编排可观测性` | `C17-09` |
| `C17-多智能体评测` | `C17-10` |
| `C17-成本与并发控制` | `C17-11` |
| `C17-编排模式库` | `C17-12` |
| `std-a2a` | `STD-a2a` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-jsonrpc` | `STD-jsonrpc` |
| `std-mcp` | `STD-mcp` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "多智能体协同"
  code: "C17"
  provenance_strength: "external"
  provenance_legend:
    c17-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C17-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "多智能体协同 全域"
      nodes:
        - "C17-01"
        - "C17-02"
        - "C17-03"
        - "C17-04"
        - "C17-05"
        - "C17-06"
        - "C17-07"
        - "C17-08"
        - "C17-09"
        - "C17-10"
        - "C17-11"
        - "C17-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-a2a"
        - "STD-cncf-cloudevents"
        - "STD-cncf-otel-semconv"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-jsonrpc"
        - "STD-mcp"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-vega-lite"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "C17-01"
      name: "角色分工与协议"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c17-anchor"
    - id: "C17-02"
      name: "消息传递格式"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C17-01"
      provenance:
        - "c17-anchor"
    - id: "C17-03"
      name: "任务分解与分配"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C17-02"
      provenance:
        - "c17-anchor"
    - id: "C17-04"
      name: "共识与仲裁"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C17-03"
        - "C17-01"
      provenance:
        - "c17-anchor"
    - id: "C17-05"
      name: "工作流 DAG"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C17-04"
        - "C17-02"
      provenance:
        - "c17-anchor"
    - id: "C17-06"
      name: "条件分支与循环"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C17-05"
        - "C17-03"
      provenance:
        - "c17-anchor"
    - id: "C17-07"
      name: "人工介入节点"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C17-06"
        - "C17-04"
      provenance:
        - "c17-anchor"
    - id: "C17-08"
      name: "失败隔离"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C17-07"
        - "C17-05"
      provenance:
        - "c17-anchor"
    - id: "C17-09"
      name: "编排可观测性"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C17-08"
        - "C17-06"
      provenance:
        - "c17-anchor"
    - id: "C17-10"
      name: "多智能体评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C17-09"
        - "C17-07"
      provenance:
        - "c17-anchor"
    - id: "C17-11"
      name: "成本与并发控制"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C17-10"
        - "C17-08"
      provenance:
        - "c17-anchor"
    - id: "C17-12"
      name: "编排模式库"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C17-11"
        - "C17-09"
      provenance:
        - "c17-anchor"
    - id: "STD-a2a"
      name: "标准 · A2A 协议"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C17-01"
        - "C17-03"
        - "C17-07"
        - "C17-12"
      provenance:
        - "std-catalog"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C17-02"
        - "C17-05"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C17-09"
        - "C17-11"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-bcp47"
      name: "标准 · 语言标签 (RFC 5646)"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json"
      name: "标准 · JSON (RFC 8259)"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C17-01"
        - "C17-06"
        - "C17-09"
        - "C17-10"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-jsonrpc"
      name: "标准 · JSON-RPC 2.0"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-mcp"
      name: "标准 · Model Context Protocol"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C17-04"
        - "C17-05"
        - "C17-06"
        - "C17-08"
        - "STD-jsonrpc"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C17-04"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C17-10"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C17-03"
        - "C17-08"
        - "C17-11"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C17-02"
        - "C17-07"
        - "C17-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C17-00）不随包交付，装载方须自备领域基础。
