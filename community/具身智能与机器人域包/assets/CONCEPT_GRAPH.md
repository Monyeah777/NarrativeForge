<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 具身智能与机器人（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「具身智能与机器人」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（具身智能与机器人:M01）与收口模块（具身智能与机器人:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 18 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A13-00 领域通用前置）；节点 30 · 边 42 · 密度 1.4000。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A13-01` | 机器人运动规划 | P40 | — | a13-anchor |
| `A13-02` | 抓取与精细操作 | P60 | `A13-01` | a13-anchor |
| `A13-03` | 视觉语言动作模型 | P40 | `A13-02` | a13-anchor |
| `A13-04` | 遥操作与示教 | P60 | — | a13-anchor |
| `A13-05` | 仿真到现实迁移 | P40 | `A13-04` | a13-anchor |
| `A13-06` | 多传感器感知融合 | P60 | `A13-05` | a13-anchor |
| `A13-07` | 任务与技能库 | P40 | `A13-03` | a13-anchor |
| `A13-08` | 人机协作安全 | P60 | `A13-06` | a13-anchor |
| `A13-09` | 移动机器人与导航 | P40 | `A13-01` | a13-anchor |
| `A13-10` | 机械臂标定 | P60 | `A13-02` | a13-anchor |
| `A13-11` | 数据集与基准 | P40 | `A13-04` | a13-anchor |
| `A13-12` | 具身 Agent | P60 | `A13-07` | a13-anchor |
| `STD-covesa-vss` | 标准 · Vehicle Signal Specification（COVESA｜iface｜实测 ✓） | P80 | `A13-09` | std-catalog |
| `STD-eu-machinery` | 标准 · 机械条例 2023/1230（EU｜gov｜实测 ✓） | P80 | `A13-01`、`A13-05`、`A13-07`、`A13-10` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A13-01`、`A13-05`、`A13-06`、`A13-10`、`STD-ietf-json` | std-catalog |
| `STD-jose` | 标准 · JOSE 签名与加密（JWS/JWE）（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-jsonrpc` | 标准 · JSON-RPC 2.0（JSON-RPC｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-mcp` | 标准 · Model Context Protocol（Anthropic/MCP｜iface｜实测 ✓） | P80 | `A13-12`、`STD-jsonrpc` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `A13-04`、`A13-09` | std-catalog |
| `STD-mlcommons-croissant` | 标准 · Croissant 数据集元数据（MLCommons｜data｜实测 ✓） | P80 | `A13-11`、`STD-schema-org` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `A13-03`、`STD-protobuf` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP｜gov｜实测 ✓） | P80 | `A13-08`、`STD-owasp-top10` | std-catalog |
| `STD-owasp-top10` | 标准 · Web 十大风险（OWASP｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-schema-org` | 标准 · 结构化数据词表（Schema.org｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-uptane` | 标准 · OTA 安全框架（Uptane｜gov｜实测 ✓） | P80 | `A13-02`、`A13-04`、`A13-06`、`STD-jose` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A13-03`、`A13-08`、`A13-11`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A13-02`、`A13-07`、`A13-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A13-机器人运动规划` | `A13-01` |
| `A13-抓取与精细操作` | `A13-02` |
| `A13-视觉语言动作模型` | `A13-03` |
| `A13-遥操作与示教` | `A13-04` |
| `A13-仿真到现实迁移` | `A13-05` |
| `A13-多传感器感知融合` | `A13-06` |
| `A13-任务与技能库` | `A13-07` |
| `A13-人机协作安全` | `A13-08` |
| `A13-移动机器人与导航` | `A13-09` |
| `A13-机械臂标定` | `A13-10` |
| `A13-数据集与基准` | `A13-11` |
| `A13-具身-Agent` | `A13-12` |
| `std-covesa-vss` | `STD-covesa-vss` |
| `std-eu-machinery` | `STD-eu-machinery` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-jose` | `STD-jose` |
| `std-jsonrpc` | `STD-jsonrpc` |
| `std-mcp` | `STD-mcp` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-croissant` | `STD-mlcommons-croissant` |
| `std-onnx` | `STD-onnx` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-owasp-top10` | `STD-owasp-top10` |
| `std-protobuf` | `STD-protobuf` |
| `std-schema-org` | `STD-schema-org` |
| `std-uptane` | `STD-uptane` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "具身智能与机器人"
  code: "A13"
  provenance_strength: "external"
  provenance_legend:
    a13-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A13-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "具身智能与机器人 全域"
      nodes:
        - "A13-01"
        - "A13-02"
        - "A13-03"
        - "A13-04"
        - "A13-05"
        - "A13-06"
        - "A13-07"
        - "A13-08"
        - "A13-09"
        - "A13-10"
        - "A13-11"
        - "A13-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-covesa-vss"
        - "STD-eu-machinery"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-jose"
        - "STD-jsonrpc"
        - "STD-mcp"
        - "STD-mermaid"
        - "STD-mlcommons-croissant"
        - "STD-onnx"
        - "STD-owasp-llm"
        - "STD-owasp-top10"
        - "STD-protobuf"
        - "STD-schema-org"
        - "STD-uptane"
        - "STD-vega-lite"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "A13-01"
      name: "机器人运动规划"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a13-anchor"
    - id: "A13-02"
      name: "抓取与精细操作"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A13-01"
      provenance:
        - "a13-anchor"
    - id: "A13-03"
      name: "视觉语言动作模型"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A13-02"
      provenance:
        - "a13-anchor"
    - id: "A13-04"
      name: "遥操作与示教"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a13-anchor"
    - id: "A13-05"
      name: "仿真到现实迁移"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A13-04"
      provenance:
        - "a13-anchor"
    - id: "A13-06"
      name: "多传感器感知融合"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A13-05"
      provenance:
        - "a13-anchor"
    - id: "A13-07"
      name: "任务与技能库"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A13-03"
      provenance:
        - "a13-anchor"
    - id: "A13-08"
      name: "人机协作安全"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A13-06"
      provenance:
        - "a13-anchor"
    - id: "A13-09"
      name: "移动机器人与导航"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A13-01"
      provenance:
        - "a13-anchor"
    - id: "A13-10"
      name: "机械臂标定"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A13-02"
      provenance:
        - "a13-anchor"
    - id: "A13-11"
      name: "数据集与基准"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A13-04"
      provenance:
        - "a13-anchor"
    - id: "A13-12"
      name: "具身 Agent"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A13-07"
      provenance:
        - "a13-anchor"
    - id: "STD-covesa-vss"
      name: "标准 · Vehicle Signal Specification"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A13-09"
      provenance:
        - "std-catalog"
    - id: "STD-eu-machinery"
      name: "标准 · 机械条例 2023/1230"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A13-01"
        - "A13-05"
        - "A13-07"
        - "A13-10"
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
        - "A13-01"
        - "A13-05"
        - "A13-06"
        - "A13-10"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-jose"
      name: "标准 · JOSE 签名与加密（JWS/JWE）"
      layer: "P80"
      branch: "standards"
      prereqs: []
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
        - "A13-12"
        - "STD-jsonrpc"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A13-04"
        - "A13-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-croissant"
      name: "标准 · Croissant 数据集元数据"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A13-11"
        - "STD-schema-org"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A13-03"
        - "STD-protobuf"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A13-08"
        - "STD-owasp-top10"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-top10"
      name: "标准 · Web 十大风险"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-protobuf"
      name: "标准 · Protocol Buffers proto3"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-schema-org"
      name: "标准 · 结构化数据词表"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-uptane"
      name: "标准 · OTA 安全框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A13-02"
        - "A13-04"
        - "A13-06"
        - "STD-jose"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A13-03"
        - "A13-08"
        - "A13-11"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A13-02"
        - "A13-07"
        - "A13-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A13-00）不随包交付，装载方须自备领域基础。
