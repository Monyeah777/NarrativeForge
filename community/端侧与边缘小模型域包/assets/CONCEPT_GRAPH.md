<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 端侧与边缘小模型（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「端侧与边缘小模型」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（端侧与边缘小模型:M01）与收口模块（端侧与边缘小模型:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 22 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A14-00 领域通用前置）；节点 34 · 边 43 · 密度 1.2647。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A14-01` | 小模型蒸馏与裁剪 | P40 | — | a14-anchor |
| `A14-02` | 模型量化压缩部署 | P60 | `A14-01` | a14-anchor |
| `A14-03` | 端侧推理框架 | P40 | `A14-02` | a14-anchor |
| `A14-04` | 内存与功耗预算 | P60 | `A14-03` | a14-anchor |
| `A14-05` | 隐私本地推理 | P40 | — | a14-anchor |
| `A14-06` | 端云协同策略 | P60 | `A14-05` | a14-anchor |
| `A14-07` | 体积与延迟评测 | P40 | `A14-04` | a14-anchor |
| `A14-08` | 移动端多模态 | P60 | `A14-03` | a14-anchor |
| `A14-09` | 车机与 IoT 端侧 | P40 | `A14-06` | a14-anchor |
| `A14-10` | 端侧工具调用 | P60 | `A14-03` | a14-anchor |
| `A14-11` | 固件与 OTA 更新 | P40 | `A14-04` | a14-anchor |
| `A14-12` | 端侧模型安全 | P60 | `A14-05` | a14-anchor |
| `STD-a2a` | 标准 · A2A 协议（Linux Foundation｜iface｜实测 ✓） | P80 | `A14-06` | std-catalog |
| `STD-covesa-vss` | 标准 · Vehicle Signal Specification（COVESA｜iface｜实测 ✓） | P80 | `A14-09` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU｜gov｜实测 ✓） | P80 | `A14-05` | std-catalog |
| `STD-ieee-754` | 标准 · 浮点运算标准（IEEE｜data｜实测 ✓） | P80 | `A14-04`、`A14-08` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A14-01`、`A14-05`、`A14-06`、`A14-11`、`STD-ietf-json` | std-catalog |
| `STD-jose` | 标准 · JOSE 签名与加密（JWS/JWE）（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-jsonrpc` | 标准 · JSON-RPC 2.0（JSON-RPC｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-mcp` | 标准 · Model Context Protocol（Anthropic/MCP｜iface｜实测 ✓） | P80 | `A14-10`、`STD-jsonrpc` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `A14-04`、`A14-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A14-07` | std-catalog |
| `STD-oasis-openapi` | 标准 · OpenAPI 3.1（OpenAPI Initiative｜iface｜实测 ✓） | P80 | `A14-02`、`STD-ietf-json-schema` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `A14-01`、`A14-03`、`STD-protobuf` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP｜gov｜实测 ✓） | P80 | `A14-12`、`STD-owasp-top10` | std-catalog |
| `STD-owasp-top10` | 标准 · Web 十大风险（OWASP｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-uptane` | 标准 · OTA 安全框架（Uptane｜gov｜实测 ✓） | P80 | `A14-11`、`STD-jose` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A14-03`、`A14-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `A14-10`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A14-02`、`A14-07`、`A14-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A14-小模型蒸馏与裁剪` | `A14-01` |
| `A14-模型量化压缩部署` | `A14-02` |
| `A14-端侧推理框架` | `A14-03` |
| `A14-内存与功耗预算` | `A14-04` |
| `A14-隐私本地推理` | `A14-05` |
| `A14-端云协同策略` | `A14-06` |
| `A14-体积与延迟评测` | `A14-07` |
| `A14-移动端多模态` | `A14-08` |
| `A14-车机与-IoT-端侧` | `A14-09` |
| `A14-端侧工具调用` | `A14-10` |
| `A14-固件与-OTA-更新` | `A14-11` |
| `A14-端侧模型安全` | `A14-12` |
| `std-a2a` | `STD-a2a` |
| `std-covesa-vss` | `STD-covesa-vss` |
| `std-gdpr` | `STD-gdpr` |
| `std-ieee-754` | `STD-ieee-754` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-jose` | `STD-jose` |
| `std-jsonrpc` | `STD-jsonrpc` |
| `std-mcp` | `STD-mcp` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-oasis-openapi` | `STD-oasis-openapi` |
| `std-onnx` | `STD-onnx` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-owasp-top10` | `STD-owasp-top10` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-uptane` | `STD-uptane` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "端侧与边缘小模型"
  code: "A14"
  provenance_strength: "external"
  provenance_legend:
    a14-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A14-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "端侧与边缘小模型 全域"
      nodes:
        - "A14-01"
        - "A14-02"
        - "A14-03"
        - "A14-04"
        - "A14-05"
        - "A14-06"
        - "A14-07"
        - "A14-08"
        - "A14-09"
        - "A14-10"
        - "A14-11"
        - "A14-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-a2a"
        - "STD-covesa-vss"
        - "STD-gdpr"
        - "STD-ieee-754"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-jose"
        - "STD-jsonrpc"
        - "STD-mcp"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-oasis-openapi"
        - "STD-onnx"
        - "STD-owasp-llm"
        - "STD-owasp-top10"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-uptane"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "A14-01"
      name: "小模型蒸馏与裁剪"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a14-anchor"
    - id: "A14-02"
      name: "模型量化压缩部署"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A14-01"
      provenance:
        - "a14-anchor"
    - id: "A14-03"
      name: "端侧推理框架"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A14-02"
      provenance:
        - "a14-anchor"
    - id: "A14-04"
      name: "内存与功耗预算"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A14-03"
      provenance:
        - "a14-anchor"
    - id: "A14-05"
      name: "隐私本地推理"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a14-anchor"
    - id: "A14-06"
      name: "端云协同策略"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A14-05"
      provenance:
        - "a14-anchor"
    - id: "A14-07"
      name: "体积与延迟评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A14-04"
      provenance:
        - "a14-anchor"
    - id: "A14-08"
      name: "移动端多模态"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A14-03"
      provenance:
        - "a14-anchor"
    - id: "A14-09"
      name: "车机与 IoT 端侧"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A14-06"
      provenance:
        - "a14-anchor"
    - id: "A14-10"
      name: "端侧工具调用"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A14-03"
      provenance:
        - "a14-anchor"
    - id: "A14-11"
      name: "固件与 OTA 更新"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A14-04"
      provenance:
        - "a14-anchor"
    - id: "A14-12"
      name: "端侧模型安全"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A14-05"
      provenance:
        - "a14-anchor"
    - id: "STD-a2a"
      name: "标准 · A2A 协议"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-06"
      provenance:
        - "std-catalog"
    - id: "STD-covesa-vss"
      name: "标准 · Vehicle Signal Specification"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-09"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-05"
      provenance:
        - "std-catalog"
    - id: "STD-ieee-754"
      name: "标准 · 浮点运算标准"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-04"
        - "A14-08"
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
        - "A14-01"
        - "A14-05"
        - "A14-06"
        - "A14-11"
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
        - "A14-10"
        - "STD-jsonrpc"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-04"
        - "A14-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-07"
      provenance:
        - "std-catalog"
    - id: "STD-oasis-openapi"
      name: "标准 · OpenAPI 3.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-02"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-01"
        - "A14-03"
        - "STD-protobuf"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-12"
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
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
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
        - "A14-11"
        - "STD-jose"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-03"
        - "A14-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-10"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A14-02"
        - "A14-07"
        - "A14-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A14-00）不随包交付，装载方须自备领域基础。
