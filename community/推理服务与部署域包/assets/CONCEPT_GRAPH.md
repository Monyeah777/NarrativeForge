<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 推理服务与部署（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「推理服务与部署」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（推理服务与部署:M01）与收口模块（推理服务与部署:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 16 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（C11-00 领域通用前置）；节点 28 · 边 53 · 密度 1.8929。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C11-01` | 推理服务框架 | P40 | — | c11-anchor |
| `C11-02` | 网关与路由 | P60 | `C11-01` | c11-anchor |
| `C11-03` | 多模型编排 | P40 | `C11-02` | c11-anchor |
| `C11-04` | 自动扩缩容 | P60 | `C11-03`、`C11-01` | c11-anchor |
| `C11-05` | 限流与队列 | P40 | `C11-04`、`C11-02` | c11-anchor |
| `C11-06` | 缓存策略 | P60 | `C11-05`、`C11-03` | c11-anchor |
| `C11-07` | 灰度与回滚 | P40 | `C11-06`、`C11-04` | c11-anchor |
| `C11-08` | A/B 模型切换 | P60 | `C11-07`、`C11-05` | c11-anchor |
| `C11-09` | 监控与告警 | P40 | `C11-08`、`C11-06` | c11-anchor |
| `C11-10` | 成本核算 | P60 | `C11-09`、`C11-07` | c11-anchor |
| `C11-11` | 私有化部署 | P40 | `C11-10`、`C11-08` | c11-anchor |
| `C11-12` | SLA 与容量规划 | P60 | `C11-11`、`C11-09` | c11-anchor |
| `STD-a2a` | 标准 · A2A 协议（Linux Foundation｜iface｜实测 ✓） | P80 | `C11-03` | std-catalog |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `C11-05`、`STD-ietf-json-schema` | std-catalog |
| `STD-cncf-otel-otlp` | 标准 · OTLP 协议（OpenTelemetry｜iface｜实测 ✓） | P80 | `C11-02`、`C11-04`、`C11-12`、`STD-protobuf` | std-catalog |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `C11-09`、`C11-10` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | — | std-catalog |
| `STD-gfm` | 标准 · GFM 扩展（GitHub｜form｜实测 ✓） | P80 | `C11-06`、`STD-commonmark` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `C11-01`、`C11-06`、`C11-09`、`C11-11`、`STD-ietf-json` | std-catalog |
| `STD-k8s-crd` | 标准 · Kubernetes CRD/API 扩展（CNCF｜iface｜实测 ✓） | P80 | `C11-05`、`C11-07`、`STD-oasis-openapi` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `C11-04` | std-catalog |
| `STD-oasis-openapi` | 标准 · OpenAPI 3.1（OpenAPI Initiative｜iface｜实测 ✓） | P80 | `C11-01`、`C11-11`、`STD-ietf-json-schema` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `C11-08`、`STD-protobuf` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `C11-03`、`C11-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `C11-02`、`C11-07`、`C11-10`、`C11-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C11-推理服务框架` | `C11-01` |
| `C11-网关与路由` | `C11-02` |
| `C11-多模型编排` | `C11-03` |
| `C11-自动扩缩容` | `C11-04` |
| `C11-限流与队列` | `C11-05` |
| `C11-缓存策略` | `C11-06` |
| `C11-灰度与回滚` | `C11-07` |
| `C11-A/B-模型切换` | `C11-08` |
| `C11-监控与告警` | `C11-09` |
| `C11-成本核算` | `C11-10` |
| `C11-私有化部署` | `C11-11` |
| `C11-SLA-与容量规划` | `C11-12` |
| `std-a2a` | `STD-a2a` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-cncf-otel-otlp` | `STD-cncf-otel-otlp` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-gfm` | `STD-gfm` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-k8s-crd` | `STD-k8s-crd` |
| `std-mermaid` | `STD-mermaid` |
| `std-oasis-openapi` | `STD-oasis-openapi` |
| `std-onnx` | `STD-onnx` |
| `std-protobuf` | `STD-protobuf` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "推理服务与部署"
  code: "C11"
  provenance_strength: "external"
  provenance_legend:
    c11-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C11-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "推理服务与部署 全域"
      nodes:
        - "C11-01"
        - "C11-02"
        - "C11-03"
        - "C11-04"
        - "C11-05"
        - "C11-06"
        - "C11-07"
        - "C11-08"
        - "C11-09"
        - "C11-10"
        - "C11-11"
        - "C11-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-a2a"
        - "STD-cncf-cloudevents"
        - "STD-cncf-otel-otlp"
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-gfm"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-k8s-crd"
        - "STD-mermaid"
        - "STD-oasis-openapi"
        - "STD-onnx"
        - "STD-protobuf"
        - "STD-vega-lite"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "C11-01"
      name: "推理服务框架"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c11-anchor"
    - id: "C11-02"
      name: "网关与路由"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-01"
      provenance:
        - "c11-anchor"
    - id: "C11-03"
      name: "多模型编排"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C11-02"
      provenance:
        - "c11-anchor"
    - id: "C11-04"
      name: "自动扩缩容"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-03"
        - "C11-01"
      provenance:
        - "c11-anchor"
    - id: "C11-05"
      name: "限流与队列"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C11-04"
        - "C11-02"
      provenance:
        - "c11-anchor"
    - id: "C11-06"
      name: "缓存策略"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-05"
        - "C11-03"
      provenance:
        - "c11-anchor"
    - id: "C11-07"
      name: "灰度与回滚"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C11-06"
        - "C11-04"
      provenance:
        - "c11-anchor"
    - id: "C11-08"
      name: "A/B 模型切换"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-07"
        - "C11-05"
      provenance:
        - "c11-anchor"
    - id: "C11-09"
      name: "监控与告警"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C11-08"
        - "C11-06"
      provenance:
        - "c11-anchor"
    - id: "C11-10"
      name: "成本核算"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-09"
        - "C11-07"
      provenance:
        - "c11-anchor"
    - id: "C11-11"
      name: "私有化部署"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C11-10"
        - "C11-08"
      provenance:
        - "c11-anchor"
    - id: "C11-12"
      name: "SLA 与容量规划"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C11-11"
        - "C11-09"
      provenance:
        - "c11-anchor"
    - id: "STD-a2a"
      name: "标准 · A2A 协议"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C11-03"
      provenance:
        - "std-catalog"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C11-05"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-cncf-otel-otlp"
      name: "标准 · OTLP 协议"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C11-02"
        - "C11-04"
        - "C11-12"
        - "STD-protobuf"
      provenance:
        - "std-catalog"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C11-09"
        - "C11-10"
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
        - "C11-06"
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
        - "C11-01"
        - "C11-06"
        - "C11-09"
        - "C11-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-k8s-crd"
      name: "标准 · Kubernetes CRD/API 扩展"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C11-05"
        - "C11-07"
        - "STD-oasis-openapi"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C11-04"
      provenance:
        - "std-catalog"
    - id: "STD-oasis-openapi"
      name: "标准 · OpenAPI 3.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C11-01"
        - "C11-11"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C11-08"
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
        - "C11-03"
        - "C11-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C11-02"
        - "C11-07"
        - "C11-10"
        - "C11-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C11-00）不随包交付，装载方须自备领域基础。
