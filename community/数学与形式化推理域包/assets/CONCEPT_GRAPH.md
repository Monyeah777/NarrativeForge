<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 数学与形式化推理（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「数学与形式化推理」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（数学与形式化推理:M01）与收口模块（数学与形式化推理:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 16 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A10-00 领域通用前置）；节点 28 · 边 41 · 密度 1.4643。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A10-01` | 思维链与推理链 | P40 | — | a10-anchor |
| `A10-02` | 形式化定理证明 | P60 | — | a10-anchor |
| `A10-03` | 定理证明搜索 | P40 | `A10-02` | a10-anchor |
| `A10-04` | 符号计算与 CAS | P60 | — | a10-anchor |
| `A10-05` | 数学应用题求解 | P40 | — | a10-anchor |
| `A10-06` | 竞赛数学基准 | P60 | `A10-05`、`A10-09` | a10-anchor |
| `A10-07` | 过程奖励模型 | P40 | `A10-01` | a10-anchor |
| `A10-08` | 自洽性与结果验证 | P60 | `A10-01` | a10-anchor |
| `A10-09` | 图论与组合推理 | P40 | — | a10-anchor |
| `A10-10` | 数值与误差分析 | P60 | `A10-04` | a10-anchor |
| `A10-11` | 推理幻觉识别 | P40 | `A10-06`、`A10-08` | a10-anchor |
| `A10-12` | 推理成本优化 | P60 | `A10-10`、`A10-07` | a10-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `A10-12` | std-catalog |
| `STD-ieee-754` | 标准 · 浮点运算标准（IEEE｜data｜实测 ✓） | P80 | `A10-10` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A10-01`、`A10-06`、`A10-11`、`STD-ietf-json` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A10-06` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `A10-01`、`A10-07`、`A10-09`、`A10-11`、`STD-protobuf` | std-catalog |
| `STD-peps` | 标准 · PEP 体系（含 8/257/621）（Python｜eng｜实测 ✓） | P80 | `A10-08`、`STD-rst-docutils` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-rst-docutils` | 标准 · reStructuredText 指令/角色（Docutils｜form｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A10-08`、`A10-09`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-mathml3` | 标准 · MathML 3（W3C｜form｜实测 ✓） | P80 | `A10-02`、`A10-03`、`A10-04`、`A10-05`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `A10-03`、`A10-04`、`A10-05`、`A10-10`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A10-02`、`A10-07`、`A10-12`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A10-思维链与推理链` | `A10-01` |
| `A10-形式化定理证明` | `A10-02` |
| `A10-定理证明搜索` | `A10-03` |
| `A10-符号计算与-CAS` | `A10-04` |
| `A10-数学应用题求解` | `A10-05` |
| `A10-竞赛数学基准` | `A10-06` |
| `A10-过程奖励模型` | `A10-07` |
| `A10-自洽性与结果验证` | `A10-08` |
| `A10-图论与组合推理` | `A10-09` |
| `A10-数值与误差分析` | `A10-10` |
| `A10-推理幻觉识别` | `A10-11` |
| `A10-推理成本优化` | `A10-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-ieee-754` | `STD-ieee-754` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-peps` | `STD-peps` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-rst-docutils` | `STD-rst-docutils` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-mathml3` | `STD-w3c-mathml3` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "数学与形式化推理"
  code: "A10"
  provenance_strength: "external"
  provenance_legend:
    a10-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A10-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "数学与形式化推理 全域"
      nodes:
        - "A10-01"
        - "A10-02"
        - "A10-03"
        - "A10-04"
        - "A10-05"
        - "A10-06"
        - "A10-07"
        - "A10-08"
        - "A10-09"
        - "A10-10"
        - "A10-11"
        - "A10-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-ieee-754"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-peps"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-rst-docutils"
        - "STD-vega-lite"
        - "STD-w3c-mathml3"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
        - "STD-w3c-xml"
  nodes:
    - id: "A10-01"
      name: "思维链与推理链"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a10-anchor"
    - id: "A10-02"
      name: "形式化定理证明"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a10-anchor"
    - id: "A10-03"
      name: "定理证明搜索"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A10-02"
      provenance:
        - "a10-anchor"
    - id: "A10-04"
      name: "符号计算与 CAS"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a10-anchor"
    - id: "A10-05"
      name: "数学应用题求解"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a10-anchor"
    - id: "A10-06"
      name: "竞赛数学基准"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A10-05"
        - "A10-09"
      provenance:
        - "a10-anchor"
    - id: "A10-07"
      name: "过程奖励模型"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A10-01"
      provenance:
        - "a10-anchor"
    - id: "A10-08"
      name: "自洽性与结果验证"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A10-01"
      provenance:
        - "a10-anchor"
    - id: "A10-09"
      name: "图论与组合推理"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a10-anchor"
    - id: "A10-10"
      name: "数值与误差分析"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A10-04"
      provenance:
        - "a10-anchor"
    - id: "A10-11"
      name: "推理幻觉识别"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A10-06"
        - "A10-08"
      provenance:
        - "a10-anchor"
    - id: "A10-12"
      name: "推理成本优化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A10-10"
        - "A10-07"
      provenance:
        - "a10-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-12"
      provenance:
        - "std-catalog"
    - id: "STD-ieee-754"
      name: "标准 · 浮点运算标准"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-10"
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
        - "A10-01"
        - "A10-06"
        - "A10-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-06"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-01"
        - "A10-07"
        - "A10-09"
        - "A10-11"
        - "STD-protobuf"
      provenance:
        - "std-catalog"
    - id: "STD-peps"
      name: "标准 · PEP 体系（含 8/257/621）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-08"
        - "STD-rst-docutils"
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
    - id: "STD-rst-docutils"
      name: "标准 · reStructuredText 指令/角色"
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
        - "A10-08"
        - "A10-09"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-mathml3"
      name: "标准 · MathML 3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-02"
        - "A10-03"
        - "A10-04"
        - "A10-05"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-03"
        - "A10-04"
        - "A10-05"
        - "A10-10"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-02"
        - "A10-07"
        - "A10-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-xml"
      name: "标准 · XML 1.0"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A10-00）不随包交付，装载方须自备领域基础。
