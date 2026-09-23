<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 推理优化与加速（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「推理优化与加速」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（推理优化与加速:M01）与收口模块（推理优化与加速:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 15 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（C10-00 领域通用前置）；节点 27 · 边 51 · 密度 1.8889。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C10-01` | 低比特量化 | P40 | — | c10-anchor |
| `C10-02` | KV Cache 优化 | P60 | `C10-01` | c10-anchor |
| `C10-03` | 投机解码 | P40 | `C10-02` | c10-anchor |
| `C10-04` | 批处理与连续批 | P60 | `C10-03`、`C10-01` | c10-anchor |
| `C10-05` | 算子融合 | P40 | `C10-04`、`C10-02` | c10-anchor |
| `C10-06` | 编译与图优化 | P60 | `C10-05`、`C10-03` | c10-anchor |
| `C10-07` | 并行与流水线 | P40 | `C10-06`、`C10-04` | c10-anchor |
| `C10-08` | 显存管理 | P60 | `C10-07`、`C10-05` | c10-anchor |
| `C10-09` | 吞吐与延迟权衡 | P40 | `C10-08`、`C10-06` | c10-anchor |
| `C10-10` | 长上下文加速 | P60 | `C10-09`、`C10-07` | c10-anchor |
| `C10-11` | 硬件适配 | P40 | `C10-10`、`C10-08` | c10-anchor |
| `C10-12` | 加速效果评测 | P60 | `C10-11`、`C10-09` | c10-anchor |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `C10-07`、`STD-ietf-json-schema` | std-catalog |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `C10-04`、`C10-07`、`C10-10` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | — | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `C10-03`、`C10-06`、`C10-09`、`STD-frictionless-package` | std-catalog |
| `STD-gfm` | 标准 · GFM 扩展（GitHub｜form｜实测 ✓） | P80 | `C10-10`、`STD-commonmark` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `C10-01`、`C10-05`、`C10-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `C10-04`、`C10-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `C10-02`、`C10-05`、`C10-08`、`C10-11`、`C10-12` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `C10-01`、`STD-protobuf` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `C10-03`、`C10-06`、`C10-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `C10-02`、`C10-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C10-低比特量化` | `C10-01` |
| `C10-KV-Cache-优化` | `C10-02` |
| `C10-投机解码` | `C10-03` |
| `C10-批处理与连续批` | `C10-04` |
| `C10-算子融合` | `C10-05` |
| `C10-编译与图优化` | `C10-06` |
| `C10-并行与流水线` | `C10-07` |
| `C10-显存管理` | `C10-08` |
| `C10-吞吐与延迟权衡` | `C10-09` |
| `C10-长上下文加速` | `C10-10` |
| `C10-硬件适配` | `C10-11` |
| `C10-加速效果评测` | `C10-12` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-gfm` | `STD-gfm` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-protobuf` | `STD-protobuf` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "推理优化与加速"
  code: "C10"
  provenance_strength: "external"
  provenance_legend:
    c10-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C10-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "推理优化与加速 全域"
      nodes:
        - "C10-01"
        - "C10-02"
        - "C10-03"
        - "C10-04"
        - "C10-05"
        - "C10-06"
        - "C10-07"
        - "C10-08"
        - "C10-09"
        - "C10-10"
        - "C10-11"
        - "C10-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-cloudevents"
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-gfm"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-protobuf"
        - "STD-vega-lite"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "C10-01"
      name: "低比特量化"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c10-anchor"
    - id: "C10-02"
      name: "KV Cache 优化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C10-01"
      provenance:
        - "c10-anchor"
    - id: "C10-03"
      name: "投机解码"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C10-02"
      provenance:
        - "c10-anchor"
    - id: "C10-04"
      name: "批处理与连续批"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C10-03"
        - "C10-01"
      provenance:
        - "c10-anchor"
    - id: "C10-05"
      name: "算子融合"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C10-04"
        - "C10-02"
      provenance:
        - "c10-anchor"
    - id: "C10-06"
      name: "编译与图优化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C10-05"
        - "C10-03"
      provenance:
        - "c10-anchor"
    - id: "C10-07"
      name: "并行与流水线"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C10-06"
        - "C10-04"
      provenance:
        - "c10-anchor"
    - id: "C10-08"
      name: "显存管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C10-07"
        - "C10-05"
      provenance:
        - "c10-anchor"
    - id: "C10-09"
      name: "吞吐与延迟权衡"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C10-08"
        - "C10-06"
      provenance:
        - "c10-anchor"
    - id: "C10-10"
      name: "长上下文加速"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C10-09"
        - "C10-07"
      provenance:
        - "c10-anchor"
    - id: "C10-11"
      name: "硬件适配"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C10-10"
        - "C10-08"
      provenance:
        - "c10-anchor"
    - id: "C10-12"
      name: "加速效果评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C10-11"
        - "C10-09"
      provenance:
        - "c10-anchor"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C10-07"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C10-04"
        - "C10-07"
        - "C10-10"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C10-03"
        - "C10-06"
        - "C10-09"
        - "STD-frictionless-package"
      provenance:
        - "std-catalog"
    - id: "STD-gfm"
      name: "标准 · GFM 扩展"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C10-10"
        - "STD-commonmark"
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
        - "C10-01"
        - "C10-05"
        - "C10-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C10-04"
        - "C10-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C10-02"
        - "C10-05"
        - "C10-08"
        - "C10-11"
        - "C10-12"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C10-01"
        - "STD-protobuf"
      provenance:
        - "std-catalog"
    - id: "STD-protobuf"
      name: "标准 · Protocol Buffers proto3"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C10-03"
        - "C10-06"
        - "C10-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C10-02"
        - "C10-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C10-00）不随包交付，装载方须自备领域基础。
