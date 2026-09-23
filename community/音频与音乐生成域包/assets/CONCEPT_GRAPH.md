<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 音频与音乐生成（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「音频与音乐生成」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（音频与音乐生成:M01）与收口模块（音频与音乐生成:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 15 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A05-00 领域通用前置）；节点 27 · 边 40 · 密度 1.4815。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A05-01` | 音乐生成与编曲 | P40 | `A05-03` | a05-anchor |
| `A05-02` | 伴奏与人声分离 | P60 | `A05-01` | a05-anchor |
| `A05-03` | 乐谱与 MIDI 理解 | P40 | — | a05-anchor |
| `A05-04` | 风格与情绪标签 | P60 | — | a05-anchor |
| `A05-05` | 音频修复与降噪 | P40 | — | a05-anchor |
| `A05-06` | 声音事件检测 | P60 | — | a05-anchor |
| `A05-07` | 空间音频与混音 | P40 | — | a05-anchor |
| `A05-08` | 音效合成 | P60 | `A05-07` | a05-anchor |
| `A05-09` | 版权与采样合规 | P40 | `A05-02` | a05-anchor |
| `A05-10` | 音乐推荐与歌单 | P60 | `A05-04` | a05-anchor |
| `A05-11` | 歌声合成 | P40 | `A05-06`、`A05-01` | a05-anchor |
| `A05-12` | 音频质量评测 | P60 | `A05-05`、`A05-08`、`A05-04` | a05-anchor |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `A05-06`、`STD-ietf-json-schema` | std-catalog |
| `STD-creativecommons` | 标准 · 许可与权利表达（Creative Commons｜gov｜实测 ✓） | P80 | `A05-09` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A05-04`、`A05-01`、`A05-06`、`A05-11`、`STD-ietf-json` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A05-02`、`A05-08`、`A05-12` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation｜iface｜实测 ✓） | P80 | `A05-03`、`STD-protobuf` | std-catalog |
| `STD-opengeospatial` | 标准 · OGC 标准（含 GeoJSON/3D Tiles）（OGC｜data｜实测 ✓） | P80 | `A05-07` | std-catalog |
| `STD-protobuf` | 标准 · Protocol Buffers proto3（Google｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX｜gov｜实测 ✓） | P80 | `A05-09` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A05-03`、`A05-07`、`A05-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `A05-04`、`A05-05`、`A05-10`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A05-02`、`A05-12`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-webaudio` | 标准 · Web Audio API（W3C｜form｜实测 ✓） | P80 | `A05-01`、`A05-05`、`A05-10`、`A05-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A05-音乐生成与编曲` | `A05-01` |
| `A05-伴奏与人声分离` | `A05-02` |
| `A05-乐谱与-MIDI-理解` | `A05-03` |
| `A05-风格与情绪标签` | `A05-04` |
| `A05-音频修复与降噪` | `A05-05` |
| `A05-声音事件检测` | `A05-06` |
| `A05-空间音频与混音` | `A05-07` |
| `A05-音效合成` | `A05-08` |
| `A05-版权与采样合规` | `A05-09` |
| `A05-音乐推荐与歌单` | `A05-10` |
| `A05-歌声合成` | `A05-11` |
| `A05-音频质量评测` | `A05-12` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-creativecommons` | `STD-creativecommons` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-opengeospatial` | `STD-opengeospatial` |
| `std-protobuf` | `STD-protobuf` |
| `std-rdf11` | `STD-rdf11` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-webaudio` | `STD-w3c-webaudio` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "音频与音乐生成"
  code: "A05"
  provenance_strength: "external"
  provenance_legend:
    a05-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A05-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "音频与音乐生成 全域"
      nodes:
        - "A05-01"
        - "A05-02"
        - "A05-03"
        - "A05-04"
        - "A05-05"
        - "A05-06"
        - "A05-07"
        - "A05-08"
        - "A05-09"
        - "A05-10"
        - "A05-11"
        - "A05-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-cloudevents"
        - "STD-creativecommons"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-opengeospatial"
        - "STD-protobuf"
        - "STD-rdf11"
        - "STD-spdx-licenses"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
        - "STD-w3c-webaudio"
  nodes:
    - id: "A05-01"
      name: "音乐生成与编曲"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A05-03"
      provenance:
        - "a05-anchor"
    - id: "A05-02"
      name: "伴奏与人声分离"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A05-01"
      provenance:
        - "a05-anchor"
    - id: "A05-03"
      name: "乐谱与 MIDI 理解"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a05-anchor"
    - id: "A05-04"
      name: "风格与情绪标签"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a05-anchor"
    - id: "A05-05"
      name: "音频修复与降噪"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a05-anchor"
    - id: "A05-06"
      name: "声音事件检测"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a05-anchor"
    - id: "A05-07"
      name: "空间音频与混音"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a05-anchor"
    - id: "A05-08"
      name: "音效合成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A05-07"
      provenance:
        - "a05-anchor"
    - id: "A05-09"
      name: "版权与采样合规"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A05-02"
      provenance:
        - "a05-anchor"
    - id: "A05-10"
      name: "音乐推荐与歌单"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A05-04"
      provenance:
        - "a05-anchor"
    - id: "A05-11"
      name: "歌声合成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A05-06"
        - "A05-01"
      provenance:
        - "a05-anchor"
    - id: "A05-12"
      name: "音频质量评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A05-05"
        - "A05-08"
        - "A05-04"
      provenance:
        - "a05-anchor"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A05-06"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-creativecommons"
      name: "标准 · 许可与权利表达"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A05-09"
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
        - "A05-04"
        - "A05-01"
        - "A05-06"
        - "A05-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A05-02"
        - "A05-08"
        - "A05-12"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A05-03"
        - "STD-protobuf"
      provenance:
        - "std-catalog"
    - id: "STD-opengeospatial"
      name: "标准 · OGC 标准（含 GeoJSON/3D Tiles）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A05-07"
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
        - "A05-09"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A05-03"
        - "A05-07"
        - "A05-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A05-04"
        - "A05-05"
        - "A05-10"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A05-02"
        - "A05-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-webaudio"
      name: "标准 · Web Audio API"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A05-01"
        - "A05-05"
        - "A05-10"
        - "A05-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A05-00）不随包交付，装载方须自备领域基础。
