<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 语音识别与合成（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「语音识别与合成」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（语音识别与合成:M01）与收口模块（语音识别与合成:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 16 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A04-00 领域通用前置）；节点 28 · 边 41 · 密度 1.4643。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A04-01` | 端到端 ASR 声学建模 | P40 | `A04-02` | a04-anchor |
| `A04-02` | 语音活动检测与切分 | P60 | — | a04-anchor |
| `A04-03` | 说话人分离与识别 | P40 | — | a04-anchor |
| `A04-04` | 方言与口音适应 | P60 | `A04-01` | a04-anchor |
| `A04-05` | 噪声与远场鲁棒 | P40 | `A04-01` | a04-anchor |
| `A04-06` | 流式低延迟识别 | P60 | `A04-01` | a04-anchor |
| `A04-07` | TTS 声学模型与声码器 | P40 | — | a04-anchor |
| `A04-08` | 音色克隆与声音转换 | P60 | `A04-07` | a04-anchor |
| `A04-09` | 韵律与情感控制 | P40 | `A04-07` | a04-anchor |
| `A04-10` | 多语种混说 | P60 | `A04-03` | a04-anchor |
| `A04-11` | 语音评测与打分 | P40 | `A04-01`、`A04-09` | a04-anchor |
| `A04-12` | 字幕时间轴对齐 | P60 | `A04-06` | a04-anchor |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `A04-06`、`STD-ietf-json-schema` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-ixdtf` | 标准 · IXDTF (RFC 9557)（IETF｜data｜实测 ✓） | P80 | `A04-12`、`STD-rfc3339` | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A04-04`、`A04-10`、`A04-01`、`A04-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `A04-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A04-05`、`A04-08`、`A04-11` | std-catalog |
| `STD-oci-image` | 标准 · 镜像清单（OCI｜iface｜实测 ✓） | P80 | `A04-12` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `A04-03`、`A04-06`、`A04-07`、`A04-09`、`STD-protobuf` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-rfc3339` | 标准 · 时间戳（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A04-03`、`A04-08`、`A04-10`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `A04-04`、`A04-05`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A04-02`、`A04-07`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-webaudio` | 标准 · Web Audio API（W3C｜form｜实测 ✓） | P80 | `A04-01`、`A04-02` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A04-端到端-ASR-声学建模` | `A04-01` |
| `A04-语音活动检测与切分` | `A04-02` |
| `A04-说话人分离与识别` | `A04-03` |
| `A04-方言与口音适应` | `A04-04` |
| `A04-噪声与远场鲁棒` | `A04-05` |
| `A04-流式低延迟识别` | `A04-06` |
| `A04-TTS-声学模型与声码器` | `A04-07` |
| `A04-音色克隆与声音转换` | `A04-08` |
| `A04-韵律与情感控制` | `A04-09` |
| `A04-多语种混说` | `A04-10` |
| `A04-语音评测与打分` | `A04-11` |
| `A04-字幕时间轴对齐` | `A04-12` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-ixdtf` | `STD-ietf-ixdtf` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-oci-image` | `STD-oci-image` |
| `std-onnx` | `STD-onnx` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-rfc3339` | `STD-rfc3339` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-webaudio` | `STD-w3c-webaudio` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "语音识别与合成"
  code: "A04"
  provenance_strength: "external"
  provenance_legend:
    a04-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A04-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "语音识别与合成 全域"
      nodes:
        - "A04-01"
        - "A04-02"
        - "A04-03"
        - "A04-04"
        - "A04-05"
        - "A04-06"
        - "A04-07"
        - "A04-08"
        - "A04-09"
        - "A04-10"
        - "A04-11"
        - "A04-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-cloudevents"
        - "STD-ietf-bcp47"
        - "STD-ietf-ixdtf"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-oci-image"
        - "STD-onnx"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-rfc3339"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
        - "STD-w3c-webaudio"
  nodes:
    - id: "A04-01"
      name: "端到端 ASR 声学建模"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A04-02"
      provenance:
        - "a04-anchor"
    - id: "A04-02"
      name: "语音活动检测与切分"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a04-anchor"
    - id: "A04-03"
      name: "说话人分离与识别"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a04-anchor"
    - id: "A04-04"
      name: "方言与口音适应"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A04-01"
      provenance:
        - "a04-anchor"
    - id: "A04-05"
      name: "噪声与远场鲁棒"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A04-01"
      provenance:
        - "a04-anchor"
    - id: "A04-06"
      name: "流式低延迟识别"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A04-01"
      provenance:
        - "a04-anchor"
    - id: "A04-07"
      name: "TTS 声学模型与声码器"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a04-anchor"
    - id: "A04-08"
      name: "音色克隆与声音转换"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A04-07"
      provenance:
        - "a04-anchor"
    - id: "A04-09"
      name: "韵律与情感控制"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A04-07"
      provenance:
        - "a04-anchor"
    - id: "A04-10"
      name: "多语种混说"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A04-03"
      provenance:
        - "a04-anchor"
    - id: "A04-11"
      name: "语音评测与打分"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A04-01"
        - "A04-09"
      provenance:
        - "a04-anchor"
    - id: "A04-12"
      name: "字幕时间轴对齐"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A04-06"
      provenance:
        - "a04-anchor"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A04-06"
        - "STD-ietf-json-schema"
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
        - "A04-12"
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
        - "A04-04"
        - "A04-10"
        - "A04-01"
        - "A04-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A04-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A04-05"
        - "A04-08"
        - "A04-11"
      provenance:
        - "std-catalog"
    - id: "STD-oci-image"
      name: "标准 · 镜像清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A04-12"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A04-03"
        - "A04-06"
        - "A04-07"
        - "A04-09"
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
        - "A04-03"
        - "A04-08"
        - "A04-10"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A04-04"
        - "A04-05"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A04-02"
        - "A04-07"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-webaudio"
      name: "标准 · Web Audio API"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A04-01"
        - "A04-02"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A04-00）不随包交付，装载方须自备领域基础。
