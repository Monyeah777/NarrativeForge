<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 音频音乐与语音（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「音频音乐与语音」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（音频音乐与语音:M01）与收口模块（音频音乐与语音:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 10 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（E09-00 领域通用前置）；节点 22 · 边 48 · 密度 2.1818。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E09-01` | 音色设计 | P40 | — | e09-anchor |
| `E09-02` | 语音转写 | P60 | `E09-01` | e09-anchor |
| `E09-03` | 情感与韵律 | P40 | `E09-02` | e09-anchor |
| `E09-04` | 歌声合成 | P60 | `E09-03`、`E09-01` | e09-anchor |
| `E09-05` | 配乐生成 | P40 | `E09-04`、`E09-02` | e09-anchor |
| `E09-06` | 音效设计 | P60 | `E09-05`、`E09-03` | e09-anchor |
| `E09-07` | 降噪与修复 | P40 | `E09-06`、`E09-04` | e09-anchor |
| `E09-08` | 播客制作 | P60 | `E09-07`、`E09-05` | e09-anchor |
| `E09-09` | 有声书 | P40 | `E09-08`、`E09-06` | e09-anchor |
| `E09-10` | 语音克隆伦理 | P60 | `E09-09`、`E09-07` | e09-anchor |
| `E09-11` | 多语发音 | P40 | `E09-10`、`E09-08` | e09-anchor |
| `E09-12` | 音频对齐 | P60 | `E09-11`、`E09-09` | e09-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `E09-01`、`E09-07`、`E09-05` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `E09-01`、`E09-06`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `E09-11` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `E09-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C｜form｜实测 ✓） | P80 | `E09-03`、`E09-06`、`E09-09`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `E09-05`、`E09-08`、`E09-11`、`E09-02`、`E09-03`、`E09-04`、`E09-07`、`E09-09`、`E09-10`、`E09-12`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-webaudio` | 标准 · Web Audio API（W3C｜form｜实测 ✓） | P80 | `E09-02`、`E09-04`、`E09-10`、`E09-12` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E09-音色设计` | `E09-01` |
| `E09-语音转写` | `E09-02` |
| `E09-情感与韵律` | `E09-03` |
| `E09-歌声合成` | `E09-04` |
| `E09-配乐生成` | `E09-05` |
| `E09-音效设计` | `E09-06` |
| `E09-降噪与修复` | `E09-07` |
| `E09-播客制作` | `E09-08` |
| `E09-有声书` | `E09-09` |
| `E09-语音克隆伦理` | `E09-10` |
| `E09-多语发音` | `E09-11` |
| `E09-音频对齐` | `E09-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-webaudio` | `STD-w3c-webaudio` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "音频音乐与语音"
  code: "E09"
  provenance_strength: "external"
  provenance_legend:
    e09-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E09-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "音频音乐与语音 全域"
      nodes:
        - "E09-01"
        - "E09-02"
        - "E09-03"
        - "E09-04"
        - "E09-05"
        - "E09-06"
        - "E09-07"
        - "E09-08"
        - "E09-09"
        - "E09-10"
        - "E09-11"
        - "E09-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-vega-lite"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
        - "STD-w3c-webaudio"
        - "STD-w3c-xml"
  nodes:
    - id: "E09-01"
      name: "音色设计"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e09-anchor"
    - id: "E09-02"
      name: "语音转写"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E09-01"
      provenance:
        - "e09-anchor"
    - id: "E09-03"
      name: "情感与韵律"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E09-02"
      provenance:
        - "e09-anchor"
    - id: "E09-04"
      name: "歌声合成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E09-03"
        - "E09-01"
      provenance:
        - "e09-anchor"
    - id: "E09-05"
      name: "配乐生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E09-04"
        - "E09-02"
      provenance:
        - "e09-anchor"
    - id: "E09-06"
      name: "音效设计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E09-05"
        - "E09-03"
      provenance:
        - "e09-anchor"
    - id: "E09-07"
      name: "降噪与修复"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E09-06"
        - "E09-04"
      provenance:
        - "e09-anchor"
    - id: "E09-08"
      name: "播客制作"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E09-07"
        - "E09-05"
      provenance:
        - "e09-anchor"
    - id: "E09-09"
      name: "有声书"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E09-08"
        - "E09-06"
      provenance:
        - "e09-anchor"
    - id: "E09-10"
      name: "语音克隆伦理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E09-09"
        - "E09-07"
      provenance:
        - "e09-anchor"
    - id: "E09-11"
      name: "多语发音"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E09-10"
        - "E09-08"
      provenance:
        - "e09-anchor"
    - id: "E09-12"
      name: "音频对齐"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E09-11"
        - "E09-09"
      provenance:
        - "e09-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E09-01"
        - "E09-07"
        - "E09-05"
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
        - "E09-01"
        - "E09-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E09-11"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E09-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E09-03"
        - "E09-06"
        - "E09-09"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E09-05"
        - "E09-08"
        - "E09-11"
        - "E09-02"
        - "E09-03"
        - "E09-04"
        - "E09-07"
        - "E09-09"
        - "E09-10"
        - "E09-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-webaudio"
      name: "标准 · Web Audio API"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E09-02"
        - "E09-04"
        - "E09-10"
        - "E09-12"
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
- 包外前置族（E09-00）不随包交付，装载方须自备领域基础。
