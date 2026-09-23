<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 多模态大模型（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「多模态大模型」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（多模态大模型:M01）与收口模块（多模态大模型:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 18 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A02-00 领域通用前置）；节点 30 · 边 42 · 密度 1.4000。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A02-01` | 图文对齐与对比学习 | P40 | — | a02-anchor |
| `A02-02` | 视觉编码器接入 | P60 | — | a02-anchor |
| `A02-03` | 跨模态投影层 | P40 | `A02-01`、`A02-02` | a02-anchor |
| `A02-04` | 交错图文输入 | P60 | `A02-03` | a02-anchor |
| `A02-05` | 音视频统一建模 | P40 | — | a02-anchor |
| `A02-06` | 多模态指令数据 | P60 | `A02-04`、`A02-05` | a02-anchor |
| `A02-07` | 模态缺失鲁棒性 | P40 | — | a02-anchor |
| `A02-08` | 多模态幻觉 | P60 | `A02-07` | a02-anchor |
| `A02-09` | 图文评测基准 | P40 | `A02-08`、`A02-12` | a02-anchor |
| `A02-10` | 视觉定位与引用 | P60 | `A02-09` | a02-anchor |
| `A02-11` | 多模态 Agent | P40 | `A02-06` | a02-anchor |
| `A02-12` | 任意分辨率与切图策略 | P60 | — | a02-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `A02-06` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `A02-07`、`STD-frictionless-package` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A02-06`、`A02-11`、`STD-ietf-json` | std-catalog |
| `STD-jsonrpc` | 标准 · JSON-RPC 2.0（JSON-RPC｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-mcp` | 标准 · Model Context Protocol（Anthropic/MCP｜iface｜实测 ✓） | P80 | `A02-11`、`STD-jsonrpc` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A02-01`、`A02-09` | std-catalog |
| `STD-mlcommons-croissant` | 标准 · Croissant 数据集元数据（MLCommons｜data｜实测 ✓） | P80 | `A02-04`、`A02-08`、`A02-12`、`STD-schema-org` | std-catalog |
| `STD-oci-image` | 标准 · 镜像清单（OCI｜iface｜实测 ✓） | P80 | `A02-05` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-schema-org` | 标准 · 结构化数据词表（Schema.org｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A02-01`、`A02-04`、`A02-07`、`A02-08`、`A02-09`、`A02-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `A02-03`、`A02-05`、`A02-10`、`STD-rdf11` | std-catalog |
| `STD-w3c-svg2` | 标准 · SVG 2（W3C｜form｜实测 ✓） | P80 | `A02-02`、`A02-03`、`A02-10`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A02-02`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A02-图文对齐与对比学习` | `A02-01` |
| `A02-视觉编码器接入` | `A02-02` |
| `A02-跨模态投影层` | `A02-03` |
| `A02-交错图文输入` | `A02-04` |
| `A02-音视频统一建模` | `A02-05` |
| `A02-多模态指令数据` | `A02-06` |
| `A02-模态缺失鲁棒性` | `A02-07` |
| `A02-多模态幻觉` | `A02-08` |
| `A02-图文评测基准` | `A02-09` |
| `A02-视觉定位与引用` | `A02-10` |
| `A02-多模态-Agent` | `A02-11` |
| `A02-任意分辨率与切图策略` | `A02-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-jsonrpc` | `STD-jsonrpc` |
| `std-mcp` | `STD-mcp` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-mlcommons-croissant` | `STD-mlcommons-croissant` |
| `std-oci-image` | `STD-oci-image` |
| `std-rdf11` | `STD-rdf11` |
| `std-schema-org` | `STD-schema-org` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-svg2` | `STD-w3c-svg2` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "多模态大模型"
  code: "A02"
  provenance_strength: "external"
  provenance_legend:
    a02-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A02-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "多模态大模型 全域"
      nodes:
        - "A02-01"
        - "A02-02"
        - "A02-03"
        - "A02-04"
        - "A02-05"
        - "A02-06"
        - "A02-07"
        - "A02-08"
        - "A02-09"
        - "A02-10"
        - "A02-11"
        - "A02-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-jsonrpc"
        - "STD-mcp"
        - "STD-mlcommons-bench"
        - "STD-mlcommons-croissant"
        - "STD-oci-image"
        - "STD-rdf11"
        - "STD-schema-org"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-svg2"
        - "STD-w3c-tabular-data"
        - "STD-w3c-xml"
  nodes:
    - id: "A02-01"
      name: "图文对齐与对比学习"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a02-anchor"
    - id: "A02-02"
      name: "视觉编码器接入"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a02-anchor"
    - id: "A02-03"
      name: "跨模态投影层"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A02-01"
        - "A02-02"
      provenance:
        - "a02-anchor"
    - id: "A02-04"
      name: "交错图文输入"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A02-03"
      provenance:
        - "a02-anchor"
    - id: "A02-05"
      name: "音视频统一建模"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a02-anchor"
    - id: "A02-06"
      name: "多模态指令数据"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A02-04"
        - "A02-05"
      provenance:
        - "a02-anchor"
    - id: "A02-07"
      name: "模态缺失鲁棒性"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a02-anchor"
    - id: "A02-08"
      name: "多模态幻觉"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A02-07"
      provenance:
        - "a02-anchor"
    - id: "A02-09"
      name: "图文评测基准"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A02-08"
        - "A02-12"
      provenance:
        - "a02-anchor"
    - id: "A02-10"
      name: "视觉定位与引用"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A02-09"
      provenance:
        - "a02-anchor"
    - id: "A02-11"
      name: "多模态 Agent"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A02-06"
      provenance:
        - "a02-anchor"
    - id: "A02-12"
      name: "任意分辨率与切图策略"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a02-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A02-06"
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
        - "A02-07"
        - "STD-frictionless-package"
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
        - "A02-06"
        - "A02-11"
        - "STD-ietf-json"
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
        - "A02-11"
        - "STD-jsonrpc"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A02-01"
        - "A02-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-croissant"
      name: "标准 · Croissant 数据集元数据"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A02-04"
        - "A02-08"
        - "A02-12"
        - "STD-schema-org"
      provenance:
        - "std-catalog"
    - id: "STD-oci-image"
      name: "标准 · 镜像清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A02-05"
      provenance:
        - "std-catalog"
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-schema-org"
      name: "标准 · 结构化数据词表"
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
        - "A02-01"
        - "A02-04"
        - "A02-07"
        - "A02-08"
        - "A02-09"
        - "A02-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A02-03"
        - "A02-05"
        - "A02-10"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-svg2"
      name: "标准 · SVG 2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A02-02"
        - "A02-03"
        - "A02-10"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A02-02"
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
- 包外前置族（A02-00）不随包交付，装载方须自备领域基础。
