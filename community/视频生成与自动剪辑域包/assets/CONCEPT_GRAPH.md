<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 视频生成与自动剪辑（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「视频生成与自动剪辑」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（视频生成与自动剪辑:M01）与收口模块（视频生成与自动剪辑:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 12 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（B16-00 领域通用前置）；节点 24 · 边 50 · 密度 2.0833。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B16-01` | 脚本到分镜 | P40 | — | b16-anchor |
| `B16-02` | 自动剪辑节奏 | P60 | `B16-01` | b16-anchor |
| `B16-03` | 字幕与贴纸 | P40 | `B16-02` | b16-anchor |
| `B16-04` | 配乐与音效匹配 | P60 | `B16-03`、`B16-01` | b16-anchor |
| `B16-05` | 竖屏与横屏适配 | P40 | `B16-04`、`B16-02` | b16-anchor |
| `B16-06` | 封面与缩略图 | P60 | `B16-05`、`B16-03` | b16-anchor |
| `B16-07` | 素材检索与拼接 | P40 | `B16-06`、`B16-04` | b16-anchor |
| `B16-08` | 长视频切片 | P60 | `B16-07`、`B16-05` | b16-anchor |
| `B16-09` | 虚拟拍摄与合成 | P40 | `B16-08`、`B16-06` | b16-anchor |
| `B16-10` | 视频合规审核 | P60 | `B16-09`、`B16-07` | b16-anchor |
| `B16-11` | 渲染与转码参数 | P40 | `B16-10`、`B16-08` | b16-anchor |
| `B16-12` | 成片质量评估 | P60 | `B16-11`、`B16-09` | b16-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `B16-09`、`B16-11` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | `B16-07`、`STD-ietf-json-schema` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `B16-06`、`B16-09`、`B16-12`、`STD-frictionless-package` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU｜gov｜实测 ✓） | P80 | `B16-10` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `B16-01`、`B16-04`、`B16-10`、`STD-ietf-json` | std-catalog |
| `STD-oci-image` | 标准 · 镜像清单（OCI｜iface｜实测 ✓） | P80 | `B16-02`、`B16-03`、`B16-08` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `B16-01`、`B16-03`、`B16-05`、`B16-06`、`B16-07`、`B16-08`、`B16-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `B16-04`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `B16-05`、`B16-11`、`B16-02`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B16-脚本到分镜` | `B16-01` |
| `B16-自动剪辑节奏` | `B16-02` |
| `B16-字幕与贴纸` | `B16-03` |
| `B16-配乐与音效匹配` | `B16-04` |
| `B16-竖屏与横屏适配` | `B16-05` |
| `B16-封面与缩略图` | `B16-06` |
| `B16-素材检索与拼接` | `B16-07` |
| `B16-长视频切片` | `B16-08` |
| `B16-虚拟拍摄与合成` | `B16-09` |
| `B16-视频合规审核` | `B16-10` |
| `B16-渲染与转码参数` | `B16-11` |
| `B16-成片质量评估` | `B16-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-gdpr` | `STD-gdpr` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-oci-image` | `STD-oci-image` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "视频生成与自动剪辑"
  code: "B16"
  provenance_strength: "external"
  provenance_legend:
    b16-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B16-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "视频生成与自动剪辑 全域"
      nodes:
        - "B16-01"
        - "B16-02"
        - "B16-03"
        - "B16-04"
        - "B16-05"
        - "B16-06"
        - "B16-07"
        - "B16-08"
        - "B16-09"
        - "B16-10"
        - "B16-11"
        - "B16-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-gdpr"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-oci-image"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "B16-01"
      name: "脚本到分镜"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b16-anchor"
    - id: "B16-02"
      name: "自动剪辑节奏"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B16-01"
      provenance:
        - "b16-anchor"
    - id: "B16-03"
      name: "字幕与贴纸"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B16-02"
      provenance:
        - "b16-anchor"
    - id: "B16-04"
      name: "配乐与音效匹配"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B16-03"
        - "B16-01"
      provenance:
        - "b16-anchor"
    - id: "B16-05"
      name: "竖屏与横屏适配"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B16-04"
        - "B16-02"
      provenance:
        - "b16-anchor"
    - id: "B16-06"
      name: "封面与缩略图"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B16-05"
        - "B16-03"
      provenance:
        - "b16-anchor"
    - id: "B16-07"
      name: "素材检索与拼接"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B16-06"
        - "B16-04"
      provenance:
        - "b16-anchor"
    - id: "B16-08"
      name: "长视频切片"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B16-07"
        - "B16-05"
      provenance:
        - "b16-anchor"
    - id: "B16-09"
      name: "虚拟拍摄与合成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B16-08"
        - "B16-06"
      provenance:
        - "b16-anchor"
    - id: "B16-10"
      name: "视频合规审核"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B16-09"
        - "B16-07"
      provenance:
        - "b16-anchor"
    - id: "B16-11"
      name: "渲染与转码参数"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B16-10"
        - "B16-08"
      provenance:
        - "b16-anchor"
    - id: "B16-12"
      name: "成片质量评估"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B16-11"
        - "B16-09"
      provenance:
        - "b16-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B16-09"
        - "B16-11"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B16-07"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B16-06"
        - "B16-09"
        - "B16-12"
        - "STD-frictionless-package"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B16-10"
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
        - "B16-01"
        - "B16-04"
        - "B16-10"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-oci-image"
      name: "标准 · 镜像清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B16-02"
        - "B16-03"
        - "B16-08"
      provenance:
        - "std-catalog"
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
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
        - "B16-01"
        - "B16-03"
        - "B16-05"
        - "B16-06"
        - "B16-07"
        - "B16-08"
        - "B16-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B16-04"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B16-05"
        - "B16-11"
        - "B16-02"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B16-00）不随包交付，装载方须自备领域基础。
