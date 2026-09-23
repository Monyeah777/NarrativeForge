<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 模型运营与成本（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「模型运营与成本」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（模型运营与成本:M01）与收口模块（模型运营与成本:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 14 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（F07-00 领域通用前置）；节点 26 · 边 50 · 密度 1.9231。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `F07-01` | 路由与降级 | P40 | — | f07-anchor |
| `F07-02` | 缓存与复用 | P60 | `F07-01` | f07-anchor |
| `F07-03` | 批处理 | P40 | `F07-02` | f07-anchor |
| `F07-04` | 蒸馏与小模型 | P60 | `F07-03`、`F07-01` | f07-anchor |
| `F07-05` | 量化与推理加速 | P40 | `F07-04`、`F07-02` | f07-anchor |
| `F07-06` | 预算控制 | P60 | `F07-05`、`F07-03` | f07-anchor |
| `F07-07` | 服务等级监控 | P40 | `F07-06`、`F07-04` | f07-anchor |
| `F07-08` | 灰度发布 | P60 | `F07-07`、`F07-05` | f07-anchor |
| `F07-09` | 成本核算 | P40 | `F07-08`、`F07-06` | f07-anchor |
| `F07-10` | 供应商比价 | P60 | `F07-09`、`F07-07` | f07-anchor |
| `F07-11` | 容量规划 | P40 | `F07-10`、`F07-08` | f07-anchor |
| `F07-12` | 故障演练 | P60 | `F07-11`、`F07-09` | f07-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `F07-07`、`F07-09` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | — | std-catalog |
| `STD-gfm` | 标准 · GFM 扩展（GitHub｜form｜实测 ✓） | P80 | `F07-02`、`STD-commonmark` | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `F07-01`、`F07-06`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `F07-05`、`F07-08`、`F07-10` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST｜gov｜实测 ✓） | P80 | `F07-01`、`F07-10` | std-catalog |
| `STD-oasis-openapi` | 标准 · OpenAPI 3.1（OpenAPI Initiative｜iface｜实测 ✓） | P80 | `F07-07`、`STD-ietf-json-schema` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `F07-04`、`F07-05`、`STD-protobuf` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX｜gov｜实测 ✓） | P80 | `F07-03`、`F07-06`、`F07-12` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `F07-03`、`F07-04`、`F07-09`、`F07-11`、`F07-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `F07-08`、`F07-11`、`F07-02`、`STD-rdf11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `F07-路由与降级` | `F07-01` |
| `F07-缓存与复用` | `F07-02` |
| `F07-批处理` | `F07-03` |
| `F07-蒸馏与小模型` | `F07-04` |
| `F07-量化与推理加速` | `F07-05` |
| `F07-预算控制` | `F07-06` |
| `F07-服务等级监控` | `F07-07` |
| `F07-灰度发布` | `F07-08` |
| `F07-成本核算` | `F07-09` |
| `F07-供应商比价` | `F07-10` |
| `F07-容量规划` | `F07-11` |
| `F07-故障演练` | `F07-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-gfm` | `STD-gfm` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-oasis-openapi` | `STD-oasis-openapi` |
| `std-onnx` | `STD-onnx` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "模型运营与成本"
  code: "F07"
  provenance_strength: "external"
  provenance_legend:
    f07-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "F07-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "模型运营与成本 全域"
      nodes:
        - "F07-01"
        - "F07-02"
        - "F07-03"
        - "F07-04"
        - "F07-05"
        - "F07-06"
        - "F07-07"
        - "F07-08"
        - "F07-09"
        - "F07-10"
        - "F07-11"
        - "F07-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-gfm"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-nist-ai-rmf"
        - "STD-oasis-openapi"
        - "STD-onnx"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-spdx-licenses"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
  nodes:
    - id: "F07-01"
      name: "路由与降级"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "f07-anchor"
    - id: "F07-02"
      name: "缓存与复用"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F07-01"
      provenance:
        - "f07-anchor"
    - id: "F07-03"
      name: "批处理"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F07-02"
      provenance:
        - "f07-anchor"
    - id: "F07-04"
      name: "蒸馏与小模型"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F07-03"
        - "F07-01"
      provenance:
        - "f07-anchor"
    - id: "F07-05"
      name: "量化与推理加速"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F07-04"
        - "F07-02"
      provenance:
        - "f07-anchor"
    - id: "F07-06"
      name: "预算控制"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F07-05"
        - "F07-03"
      provenance:
        - "f07-anchor"
    - id: "F07-07"
      name: "服务等级监控"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F07-06"
        - "F07-04"
      provenance:
        - "f07-anchor"
    - id: "F07-08"
      name: "灰度发布"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F07-07"
        - "F07-05"
      provenance:
        - "f07-anchor"
    - id: "F07-09"
      name: "成本核算"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F07-08"
        - "F07-06"
      provenance:
        - "f07-anchor"
    - id: "F07-10"
      name: "供应商比价"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F07-09"
        - "F07-07"
      provenance:
        - "f07-anchor"
    - id: "F07-11"
      name: "容量规划"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F07-10"
        - "F07-08"
      provenance:
        - "f07-anchor"
    - id: "F07-12"
      name: "故障演练"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F07-11"
        - "F07-09"
      provenance:
        - "f07-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F07-07"
        - "F07-09"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-gfm"
      name: "标准 · GFM 扩展"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F07-02"
        - "STD-commonmark"
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
        - "F07-01"
        - "F07-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F07-05"
        - "F07-08"
        - "F07-10"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F07-01"
        - "F07-10"
      provenance:
        - "std-catalog"
    - id: "STD-oasis-openapi"
      name: "标准 · OpenAPI 3.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F07-07"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F07-04"
        - "F07-05"
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
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-spdx-licenses"
      name: "标准 · SPDX 许可证清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F07-03"
        - "F07-06"
        - "F07-12"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F07-03"
        - "F07-04"
        - "F07-09"
        - "F07-11"
        - "F07-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F07-08"
        - "F07-11"
        - "F07-02"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（F07-00）不随包交付，装载方须自备领域基础。
