<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 对齐与偏好优化（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「对齐与偏好优化」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（对齐与偏好优化:M01）与收口模块（对齐与偏好优化:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 13 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（C07-00 领域通用前置）；节点 25 · 边 50 · 密度 2.0000。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C07-01` | RLHF 全流程 | P40 | — | c07-anchor |
| `C07-02` | DPO 与变体 | P60 | `C07-01` | c07-anchor |
| `C07-03` | 偏好数据采集 | P40 | `C07-02` | c07-anchor |
| `C07-04` | 奖励模型训练 | P60 | `C07-03`、`C07-01` | c07-anchor |
| `C07-05` | 奖励黑客与过优化 | P40 | `C07-04`、`C07-02` | c07-anchor |
| `C07-06` | 安全对齐 | P60 | `C07-05`、`C07-03` | c07-anchor |
| `C07-07` | 拒绝行为设计 | P40 | `C07-06`、`C07-04` | c07-anchor |
| `C07-08` | 价值观对齐 | P60 | `C07-07`、`C07-05` | c07-anchor |
| `C07-09` | 对齐税评估 | P40 | `C07-08`、`C07-06` | c07-anchor |
| `C07-10` | 对齐评测 | P60 | `C07-09`、`C07-07` | c07-anchor |
| `C07-11` | 多目标权衡 | P40 | `C07-10`、`C07-08` | c07-anchor |
| `C07-12` | 对齐事故复盘 | P60 | `C07-11`、`C07-09` | c07-anchor |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `C07-01`、`STD-ietf-json-schema` | std-catalog |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `C07-07` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `C07-05`、`C07-06`、`C07-10`、`C07-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `C07-01`、`C07-04`、`C07-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `C07-02`、`C07-03`、`C07-05`、`C07-08`、`C07-09`、`C07-10`、`C07-11`、`C07-12` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `C07-04`、`STD-protobuf` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP｜gov｜实测 ✓） | P80 | `C07-06`、`STD-owasp-top10` | std-catalog |
| `STD-owasp-top10` | 标准 · Web 十大风险（OWASP｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `C07-03`、`C07-07`、`C07-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `C07-02`、`C07-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C07-RLHF-全流程` | `C07-01` |
| `C07-DPO-与变体` | `C07-02` |
| `C07-偏好数据采集` | `C07-03` |
| `C07-奖励模型训练` | `C07-04` |
| `C07-奖励黑客与过优化` | `C07-05` |
| `C07-安全对齐` | `C07-06` |
| `C07-拒绝行为设计` | `C07-07` |
| `C07-价值观对齐` | `C07-08` |
| `C07-对齐税评估` | `C07-09` |
| `C07-对齐评测` | `C07-10` |
| `C07-多目标权衡` | `C07-11` |
| `C07-对齐事故复盘` | `C07-12` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-owasp-top10` | `STD-owasp-top10` |
| `std-protobuf` | `STD-protobuf` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "对齐与偏好优化"
  code: "C07"
  provenance_strength: "external"
  provenance_legend:
    c07-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C07-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "对齐与偏好优化 全域"
      nodes:
        - "C07-01"
        - "C07-02"
        - "C07-03"
        - "C07-04"
        - "C07-05"
        - "C07-06"
        - "C07-07"
        - "C07-08"
        - "C07-09"
        - "C07-10"
        - "C07-11"
        - "C07-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-cloudevents"
        - "STD-cncf-otel-semconv"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-owasp-llm"
        - "STD-owasp-top10"
        - "STD-protobuf"
        - "STD-vega-lite"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "C07-01"
      name: "RLHF 全流程"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c07-anchor"
    - id: "C07-02"
      name: "DPO 与变体"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C07-01"
      provenance:
        - "c07-anchor"
    - id: "C07-03"
      name: "偏好数据采集"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C07-02"
      provenance:
        - "c07-anchor"
    - id: "C07-04"
      name: "奖励模型训练"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C07-03"
        - "C07-01"
      provenance:
        - "c07-anchor"
    - id: "C07-05"
      name: "奖励黑客与过优化"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C07-04"
        - "C07-02"
      provenance:
        - "c07-anchor"
    - id: "C07-06"
      name: "安全对齐"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C07-05"
        - "C07-03"
      provenance:
        - "c07-anchor"
    - id: "C07-07"
      name: "拒绝行为设计"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C07-06"
        - "C07-04"
      provenance:
        - "c07-anchor"
    - id: "C07-08"
      name: "价值观对齐"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C07-07"
        - "C07-05"
      provenance:
        - "c07-anchor"
    - id: "C07-09"
      name: "对齐税评估"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C07-08"
        - "C07-06"
      provenance:
        - "c07-anchor"
    - id: "C07-10"
      name: "对齐评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C07-09"
        - "C07-07"
      provenance:
        - "c07-anchor"
    - id: "C07-11"
      name: "多目标权衡"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C07-10"
        - "C07-08"
      provenance:
        - "c07-anchor"
    - id: "C07-12"
      name: "对齐事故复盘"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C07-11"
        - "C07-09"
      provenance:
        - "c07-anchor"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C07-01"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C07-07"
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
        - "C07-05"
        - "C07-06"
        - "C07-10"
        - "C07-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C07-01"
        - "C07-04"
        - "C07-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C07-02"
        - "C07-03"
        - "C07-05"
        - "C07-08"
        - "C07-09"
        - "C07-10"
        - "C07-11"
        - "C07-12"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C07-04"
        - "STD-protobuf"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C07-06"
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
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C07-03"
        - "C07-07"
        - "C07-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C07-02"
        - "C07-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C07-00）不随包交付，装载方须自备领域基础。
