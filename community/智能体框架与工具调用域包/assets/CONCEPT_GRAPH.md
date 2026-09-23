<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 智能体框架与工具调用（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「智能体框架与工具调用」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（智能体框架与工具调用:M01）与收口模块（智能体框架与工具调用:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（C16-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C16-01` | 工具 Schema 设计 | P40 | — | c16-anchor |
| `C16-02` | 函数调用契约 | P60 | `C16-01` | c16-anchor |
| `C16-03` | 工具选择与路由 | P40 | `C16-02` | c16-anchor |
| `C16-04` | 参数校验与纠错 | P60 | `C16-03`、`C16-01` | c16-anchor |
| `C16-05` | 多步任务规划 | P40 | `C16-04`、`C16-02` | c16-anchor |
| `C16-06` | 失败重试与回滚 | P60 | `C16-05`、`C16-03` | c16-anchor |
| `C16-07` | 沙箱与权限 | P40 | `C16-06`、`C16-04` | c16-anchor |
| `C16-08` | 工具结果解析 | P60 | `C16-07`、`C16-05` | c16-anchor |
| `C16-09` | MCP 与协议对接 | P40 | `C16-08`、`C16-06` | c16-anchor |
| `C16-10` | 并发与状态管理 | P60 | `C16-09`、`C16-07` | c16-anchor |
| `C16-11` | 工具评测 | P40 | `C16-10`、`C16-08` | c16-anchor |
| `C16-12` | 成本与步数控制 | P60 | `C16-11`、`C16-09` | c16-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry） | P80 | `C16-12` | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema） | P80 | `C16-02`、`C16-04` | std-catalog |
| `STD-mcp` | 标准 · Model Context Protocol（Anthropic/MCP） | P80 | `C16-01`、`C16-03`、`C16-05`、`C16-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `C16-11` | std-catalog |
| `STD-nist-800-188` | 标准 · SP 800-188 去标识化（NIST） | P80 | `C16-07` | std-catalog |
| `STD-oasis-openapi` | 标准 · OpenAPI 3.1（OpenAPI Initiative） | P80 | `C16-06`、`C16-08`、`C16-10` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C16-工具-Schema-设计` | `C16-01` |
| `C16-函数调用契约` | `C16-02` |
| `C16-工具选择与路由` | `C16-03` |
| `C16-参数校验与纠错` | `C16-04` |
| `C16-多步任务规划` | `C16-05` |
| `C16-失败重试与回滚` | `C16-06` |
| `C16-沙箱与权限` | `C16-07` |
| `C16-工具结果解析` | `C16-08` |
| `C16-MCP-与协议对接` | `C16-09` |
| `C16-并发与状态管理` | `C16-10` |
| `C16-工具评测` | `C16-11` |
| `C16-成本与步数控制` | `C16-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mcp` | `STD-mcp` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-nist-800-188` | `STD-nist-800-188` |
| `std-oasis-openapi` | `STD-oasis-openapi` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "智能体框架与工具调用"
  code: "C16"
  provenance_strength: "external"
  provenance_legend:
    c16-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C16-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "智能体框架与工具调用 全域"
      nodes:
        - "C16-01"
        - "C16-02"
        - "C16-03"
        - "C16-04"
        - "C16-05"
        - "C16-06"
        - "C16-07"
        - "C16-08"
        - "C16-09"
        - "C16-10"
        - "C16-11"
        - "C16-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-ietf-json-schema"
        - "STD-mcp"
        - "STD-mlcommons-bench"
        - "STD-nist-800-188"
        - "STD-oasis-openapi"
  nodes:
    - id: "C16-01"
      name: "工具 Schema 设计"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c16-anchor"
    - id: "C16-02"
      name: "函数调用契约"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C16-01"
      provenance:
        - "c16-anchor"
    - id: "C16-03"
      name: "工具选择与路由"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C16-02"
      provenance:
        - "c16-anchor"
    - id: "C16-04"
      name: "参数校验与纠错"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C16-03"
        - "C16-01"
      provenance:
        - "c16-anchor"
    - id: "C16-05"
      name: "多步任务规划"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C16-04"
        - "C16-02"
      provenance:
        - "c16-anchor"
    - id: "C16-06"
      name: "失败重试与回滚"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C16-05"
        - "C16-03"
      provenance:
        - "c16-anchor"
    - id: "C16-07"
      name: "沙箱与权限"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C16-06"
        - "C16-04"
      provenance:
        - "c16-anchor"
    - id: "C16-08"
      name: "工具结果解析"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C16-07"
        - "C16-05"
      provenance:
        - "c16-anchor"
    - id: "C16-09"
      name: "MCP 与协议对接"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C16-08"
        - "C16-06"
      provenance:
        - "c16-anchor"
    - id: "C16-10"
      name: "并发与状态管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C16-09"
        - "C16-07"
      provenance:
        - "c16-anchor"
    - id: "C16-11"
      name: "工具评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C16-10"
        - "C16-08"
      provenance:
        - "c16-anchor"
    - id: "C16-12"
      name: "成本与步数控制"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C16-11"
        - "C16-09"
      provenance:
        - "c16-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C16-12"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C16-02"
        - "C16-04"
      provenance:
        - "std-catalog"
    - id: "STD-mcp"
      name: "标准 · Model Context Protocol"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C16-01"
        - "C16-03"
        - "C16-05"
        - "C16-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C16-11"
      provenance:
        - "std-catalog"
    - id: "STD-nist-800-188"
      name: "标准 · SP 800-188 去标识化"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C16-07"
      provenance:
        - "std-catalog"
    - id: "STD-oasis-openapi"
      name: "标准 · OpenAPI 3.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C16-06"
        - "C16-08"
        - "C16-10"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C16-00）不随包交付，装载方须自备领域基础。
