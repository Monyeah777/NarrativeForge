<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 预测、异常与风险（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「预测、异常与风险」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（预测异常与风险:M01）与收口模块（预测异常与风险:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 19 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（B18-00 领域通用前置）；节点 31 · 边 52 · 密度 1.6774。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B18-01` | 时序预测 | P40 | — | b18-anchor |
| `B18-02` | 需求预测与补货 | P60 | `B18-01` | b18-anchor |
| `B18-03` | 异常检测 | P40 | `B18-02` | b18-anchor |
| `B18-04` | 根因分析 | P60 | `B18-03`、`B18-01` | b18-anchor |
| `B18-05` | 风控评分卡 | P40 | `B18-04`、`B18-02` | b18-anchor |
| `B18-06` | 反欺诈 | P60 | `B18-05`、`B18-03` | b18-anchor |
| `B18-07` | 信用评估 | P40 | `B18-06`、`B18-04` | b18-anchor |
| `B18-08` | 设备预测性维护 | P60 | `B18-07`、`B18-05` | b18-anchor |
| `B18-09` | 舆情预警 | P40 | `B18-08`、`B18-06` | b18-anchor |
| `B18-10` | 保险定价 | P60 | `B18-09`、`B18-07` | b18-anchor |
| `B18-11` | 模型漂移监控 | P40 | `B18-10`、`B18-08` | b18-anchor |
| `B18-12` | 不确定性量化 | P60 | `B18-11`、`B18-09` | b18-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `B18-11` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `B18-07`、`B18-09` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `B18-03`、`B18-06`、`B18-09`、`STD-frictionless-package` | std-catalog |
| `STD-gips` | 标准 · GIPS 绩效标准（CFA Institute｜gov｜实测 ✓） | P80 | `B18-05`、`B18-10` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-ixdtf` | 标准 · IXDTF (RFC 9557)（IETF｜data｜实测 ✓） | P80 | `B18-01`、`STD-rfc3339` | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `B18-04`、`B18-07`、`B18-05`、`B18-10`、`B18-11`、`STD-ietf-json` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `B18-12`、`STD-protobuf` | std-catalog |
| `STD-opcua` | 标准 · OPC UA 工业互联（OPC Foundation｜iface｜实测 ✓） | P80 | `B18-08` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-rfc3339` | 标准 · 时间戳（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `B18-02`、`B18-03`、`B18-06`、`B18-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-owl-time` | 标准 · OWL-Time 时间本体（W3C｜data｜实测 ✓） | P80 | `B18-01`、`STD-w3c-owl2` | std-catalog |
| `STD-w3c-owl2` | 标准 · OWL 2 本体语言（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `B18-04`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `B18-02`、`B18-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B18-时序预测` | `B18-01` |
| `B18-需求预测与补货` | `B18-02` |
| `B18-异常检测` | `B18-03` |
| `B18-根因分析` | `B18-04` |
| `B18-风控评分卡` | `B18-05` |
| `B18-反欺诈` | `B18-06` |
| `B18-信用评估` | `B18-07` |
| `B18-设备预测性维护` | `B18-08` |
| `B18-舆情预警` | `B18-09` |
| `B18-保险定价` | `B18-10` |
| `B18-模型漂移监控` | `B18-11` |
| `B18-不确定性量化` | `B18-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-gips` | `STD-gips` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-ixdtf` | `STD-ietf-ixdtf` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-onnx` | `STD-onnx` |
| `std-opcua` | `STD-opcua` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-rfc3339` | `STD-rfc3339` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-owl-time` | `STD-w3c-owl-time` |
| `std-w3c-owl2` | `STD-w3c-owl2` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "预测、异常与风险"
  code: "B18"
  provenance_strength: "external"
  provenance_legend:
    b18-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B18-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "预测、异常与风险 全域"
      nodes:
        - "B18-01"
        - "B18-02"
        - "B18-03"
        - "B18-04"
        - "B18-05"
        - "B18-06"
        - "B18-07"
        - "B18-08"
        - "B18-09"
        - "B18-10"
        - "B18-11"
        - "B18-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-gips"
        - "STD-ietf-bcp47"
        - "STD-ietf-ixdtf"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-onnx"
        - "STD-opcua"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-rfc3339"
        - "STD-vega-lite"
        - "STD-w3c-owl-time"
        - "STD-w3c-owl2"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "B18-01"
      name: "时序预测"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b18-anchor"
    - id: "B18-02"
      name: "需求预测与补货"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-01"
      provenance:
        - "b18-anchor"
    - id: "B18-03"
      name: "异常检测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B18-02"
      provenance:
        - "b18-anchor"
    - id: "B18-04"
      name: "根因分析"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-03"
        - "B18-01"
      provenance:
        - "b18-anchor"
    - id: "B18-05"
      name: "风控评分卡"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B18-04"
        - "B18-02"
      provenance:
        - "b18-anchor"
    - id: "B18-06"
      name: "反欺诈"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-05"
        - "B18-03"
      provenance:
        - "b18-anchor"
    - id: "B18-07"
      name: "信用评估"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B18-06"
        - "B18-04"
      provenance:
        - "b18-anchor"
    - id: "B18-08"
      name: "设备预测性维护"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-07"
        - "B18-05"
      provenance:
        - "b18-anchor"
    - id: "B18-09"
      name: "舆情预警"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B18-08"
        - "B18-06"
      provenance:
        - "b18-anchor"
    - id: "B18-10"
      name: "保险定价"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-09"
        - "B18-07"
      provenance:
        - "b18-anchor"
    - id: "B18-11"
      name: "模型漂移监控"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B18-10"
        - "B18-08"
      provenance:
        - "b18-anchor"
    - id: "B18-12"
      name: "不确定性量化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B18-11"
        - "B18-09"
      provenance:
        - "b18-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B18-11"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B18-07"
        - "B18-09"
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
        - "B18-03"
        - "B18-06"
        - "B18-09"
        - "STD-frictionless-package"
      provenance:
        - "std-catalog"
    - id: "STD-gips"
      name: "标准 · GIPS 绩效标准"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B18-05"
        - "B18-10"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-bcp47"
      name: "标准 · 语言标签 (RFC 5646)"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-ietf-ixdtf"
      name: "标准 · IXDTF (RFC 9557)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B18-01"
        - "STD-rfc3339"
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
        - "B18-04"
        - "B18-07"
        - "B18-05"
        - "B18-10"
        - "B18-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B18-12"
        - "STD-protobuf"
      provenance:
        - "std-catalog"
    - id: "STD-opcua"
      name: "标准 · OPC UA 工业互联"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B18-08"
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
    - id: "STD-rfc3339"
      name: "标准 · 时间戳"
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
        - "B18-02"
        - "B18-03"
        - "B18-06"
        - "B18-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-owl-time"
      name: "标准 · OWL-Time 时间本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B18-01"
        - "STD-w3c-owl2"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-owl2"
      name: "标准 · OWL 2 本体语言"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B18-04"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B18-02"
        - "B18-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B18-00）不随包交付，装载方须自备领域基础。
