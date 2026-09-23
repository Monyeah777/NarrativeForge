<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 图像生成与视觉设计（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「图像生成与视觉设计」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（图像生成与视觉设计:M01）与收口模块（图像生成与视觉设计:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 5 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（B15-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B15-01` | 海报与 Banner | P40 | — | b15-anchor |
| `B15-02` | 电商主图与场景图 | P60 | `B15-01` | b15-anchor |
| `B15-03` | 插画与概念设定 | P40 | `B15-02` | b15-anchor |
| `B15-04` | 品牌视觉一致性 | P60 | `B15-03`、`B15-01` | b15-anchor |
| `B15-05` | 版式与配色建议 | P40 | `B15-04`、`B15-02` | b15-anchor |
| `B15-06` | 素材扩图与适配 | P60 | `B15-05`、`B15-03` | b15-anchor |
| `B15-07` | 图标与 UI 素材 | P40 | `B15-06`、`B15-04` | b15-anchor |
| `B15-08` | 印刷与色彩管理 | P60 | `B15-07`、`B15-05` | b15-anchor |
| `B15-09` | 生成版权与商用边界 | P40 | `B15-08`、`B15-06` | b15-anchor |
| `B15-10` | 设计评审与迭代 | P60 | `B15-09`、`B15-07` | b15-anchor |
| `B15-11` | A/B 视觉测试 | P40 | `B15-10`、`B15-08` | b15-anchor |
| `B15-12` | 多尺寸批量产出 | P60 | `B15-11`、`B15-09` | b15-anchor |
| `STD-creativecommons` | 标准 · 许可与权利表达（Creative Commons） | P80 | `B15-09` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `B15-03`、`B15-06`、`B15-12` | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema） | P80 | `B15-01`、`B15-07`、`B15-10` | std-catalog |
| `STD-w3c-svg2` | 标准 · SVG 2（W3C） | P80 | `B15-04`、`B15-11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `B15-02`、`B15-05`、`B15-08` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B15-海报与-Banner` | `B15-01` |
| `B15-电商主图与场景图` | `B15-02` |
| `B15-插画与概念设定` | `B15-03` |
| `B15-品牌视觉一致性` | `B15-04` |
| `B15-版式与配色建议` | `B15-05` |
| `B15-素材扩图与适配` | `B15-06` |
| `B15-图标与-UI-素材` | `B15-07` |
| `B15-印刷与色彩管理` | `B15-08` |
| `B15-生成版权与商用边界` | `B15-09` |
| `B15-设计评审与迭代` | `B15-10` |
| `B15-A/B-视觉测试` | `B15-11` |
| `B15-多尺寸批量产出` | `B15-12` |
| `std-creativecommons` | `STD-creativecommons` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-w3c-svg2` | `STD-w3c-svg2` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "图像生成与视觉设计"
  code: "B15"
  provenance_strength: "external"
  provenance_legend:
    b15-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B15-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "图像生成与视觉设计 全域"
      nodes:
        - "B15-01"
        - "B15-02"
        - "B15-03"
        - "B15-04"
        - "B15-05"
        - "B15-06"
        - "B15-07"
        - "B15-08"
        - "B15-09"
        - "B15-10"
        - "B15-11"
        - "B15-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-creativecommons"
        - "STD-frictionless-table"
        - "STD-ietf-json-schema"
        - "STD-w3c-svg2"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "B15-01"
      name: "海报与 Banner"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b15-anchor"
    - id: "B15-02"
      name: "电商主图与场景图"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B15-01"
      provenance:
        - "b15-anchor"
    - id: "B15-03"
      name: "插画与概念设定"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B15-02"
      provenance:
        - "b15-anchor"
    - id: "B15-04"
      name: "品牌视觉一致性"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B15-03"
        - "B15-01"
      provenance:
        - "b15-anchor"
    - id: "B15-05"
      name: "版式与配色建议"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B15-04"
        - "B15-02"
      provenance:
        - "b15-anchor"
    - id: "B15-06"
      name: "素材扩图与适配"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B15-05"
        - "B15-03"
      provenance:
        - "b15-anchor"
    - id: "B15-07"
      name: "图标与 UI 素材"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B15-06"
        - "B15-04"
      provenance:
        - "b15-anchor"
    - id: "B15-08"
      name: "印刷与色彩管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B15-07"
        - "B15-05"
      provenance:
        - "b15-anchor"
    - id: "B15-09"
      name: "生成版权与商用边界"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B15-08"
        - "B15-06"
      provenance:
        - "b15-anchor"
    - id: "B15-10"
      name: "设计评审与迭代"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B15-09"
        - "B15-07"
      provenance:
        - "b15-anchor"
    - id: "B15-11"
      name: "A/B 视觉测试"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B15-10"
        - "B15-08"
      provenance:
        - "b15-anchor"
    - id: "B15-12"
      name: "多尺寸批量产出"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B15-11"
        - "B15-09"
      provenance:
        - "b15-anchor"
    - id: "STD-creativecommons"
      name: "标准 · 许可与权利表达"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B15-09"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B15-03"
        - "B15-06"
        - "B15-12"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B15-01"
        - "B15-07"
        - "B15-10"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-svg2"
      name: "标准 · SVG 2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B15-04"
        - "B15-11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B15-02"
        - "B15-05"
        - "B15-08"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B15-00）不随包交付，装载方须自备领域基础。
