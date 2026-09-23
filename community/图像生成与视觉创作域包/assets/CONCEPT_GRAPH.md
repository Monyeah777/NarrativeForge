<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 图像生成与视觉创作（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「图像生成与视觉创作」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（图像生成与视觉创作:M01）与收口模块（图像生成与视觉创作:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 11 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（E07-00 领域通用前置）；节点 23 · 边 48 · 密度 2.0870。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E07-01` | 提示词结构 | P40 | — | e07-anchor |
| `E07-02` | 风格与画师词 | P60 | `E07-01` | e07-anchor |
| `E07-03` | 构图与镜头 | P40 | `E07-02` | e07-anchor |
| `E07-04` | 角色一致性 | P60 | `E07-03`、`E07-01` | e07-anchor |
| `E07-05` | 局部重绘 | P40 | `E07-04`、`E07-02` | e07-anchor |
| `E07-06` | 姿态与线稿控制 | P60 | `E07-05`、`E07-03` | e07-anchor |
| `E07-07` | 放大与修复 | P40 | `E07-06`、`E07-04` | e07-anchor |
| `E07-08` | 批量出图 | P60 | `E07-07`、`E07-05` | e07-anchor |
| `E07-09` | 素材合规 | P40 | `E07-08`、`E07-06` | e07-anchor |
| `E07-10` | 商用授权 | P60 | `E07-09`、`E07-07` | e07-anchor |
| `E07-11` | 图文排版 | P40 | `E07-10`、`E07-08` | e07-anchor |
| `E07-12` | 色彩管理 | P60 | `E07-11`、`E07-09` | e07-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `E07-01`、`E07-04`、`E07-07`、`E07-02`、`E07-05` | std-catalog |
| `STD-creativecommons` | 标准 · 许可与权利表达（Creative Commons｜gov｜实测 ✓） | P80 | `E07-10` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU｜gov｜实测 ✓） | P80 | `E07-09` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `E07-01`、`E07-06`、`STD-ietf-json` | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX｜gov｜实测 ✓） | P80 | `E07-10` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `E07-03`、`E07-08`、`E07-09`、`E07-11`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C｜form｜实测 ✓） | P80 | `E07-03`、`E07-06`、`E07-11`、`E07-12`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `E07-02`、`E07-05`、`E07-08`、`E07-04`、`E07-07`、`E07-12`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E07-提示词结构` | `E07-01` |
| `E07-风格与画师词` | `E07-02` |
| `E07-构图与镜头` | `E07-03` |
| `E07-角色一致性` | `E07-04` |
| `E07-局部重绘` | `E07-05` |
| `E07-姿态与线稿控制` | `E07-06` |
| `E07-放大与修复` | `E07-07` |
| `E07-批量出图` | `E07-08` |
| `E07-素材合规` | `E07-09` |
| `E07-商用授权` | `E07-10` |
| `E07-图文排版` | `E07-11` |
| `E07-色彩管理` | `E07-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-creativecommons` | `STD-creativecommons` |
| `std-gdpr` | `STD-gdpr` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "图像生成与视觉创作"
  code: "E07"
  provenance_strength: "external"
  provenance_legend:
    e07-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E07-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "图像生成与视觉创作 全域"
      nodes:
        - "E07-01"
        - "E07-02"
        - "E07-03"
        - "E07-04"
        - "E07-05"
        - "E07-06"
        - "E07-07"
        - "E07-08"
        - "E07-09"
        - "E07-10"
        - "E07-11"
        - "E07-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-creativecommons"
        - "STD-gdpr"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-spdx-licenses"
        - "STD-vega-lite"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
        - "STD-w3c-xml"
  nodes:
    - id: "E07-01"
      name: "提示词结构"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e07-anchor"
    - id: "E07-02"
      name: "风格与画师词"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E07-01"
      provenance:
        - "e07-anchor"
    - id: "E07-03"
      name: "构图与镜头"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E07-02"
      provenance:
        - "e07-anchor"
    - id: "E07-04"
      name: "角色一致性"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E07-03"
        - "E07-01"
      provenance:
        - "e07-anchor"
    - id: "E07-05"
      name: "局部重绘"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E07-04"
        - "E07-02"
      provenance:
        - "e07-anchor"
    - id: "E07-06"
      name: "姿态与线稿控制"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E07-05"
        - "E07-03"
      provenance:
        - "e07-anchor"
    - id: "E07-07"
      name: "放大与修复"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E07-06"
        - "E07-04"
      provenance:
        - "e07-anchor"
    - id: "E07-08"
      name: "批量出图"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E07-07"
        - "E07-05"
      provenance:
        - "e07-anchor"
    - id: "E07-09"
      name: "素材合规"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E07-08"
        - "E07-06"
      provenance:
        - "e07-anchor"
    - id: "E07-10"
      name: "商用授权"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E07-09"
        - "E07-07"
      provenance:
        - "e07-anchor"
    - id: "E07-11"
      name: "图文排版"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E07-10"
        - "E07-08"
      provenance:
        - "e07-anchor"
    - id: "E07-12"
      name: "色彩管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E07-11"
        - "E07-09"
      provenance:
        - "e07-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E07-01"
        - "E07-04"
        - "E07-07"
        - "E07-02"
        - "E07-05"
      provenance:
        - "std-catalog"
    - id: "STD-creativecommons"
      name: "标准 · 许可与权利表达"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E07-10"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E07-09"
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
        - "E07-01"
        - "E07-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-spdx-licenses"
      name: "标准 · SPDX 许可证清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E07-10"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E07-03"
        - "E07-08"
        - "E07-09"
        - "E07-11"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E07-03"
        - "E07-06"
        - "E07-11"
        - "E07-12"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E07-02"
        - "E07-05"
        - "E07-08"
        - "E07-04"
        - "E07-07"
        - "E07-12"
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
- 包外前置族（E07-00）不随包交付，装载方须自备领域基础。
