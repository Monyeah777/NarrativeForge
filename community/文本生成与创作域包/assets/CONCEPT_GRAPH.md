<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 文本生成与创作（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「文本生成与创作」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（文本生成与创作:M01）与收口模块（文本生成与创作:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 10 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（B01-00 领域通用前置）；节点 22 · 边 39 · 密度 1.7727。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B01-01` | 长文结构与大纲 | P40 | — | b01-anchor |
| `B01-02` | 文风与语体控制 | P60 | — | b01-anchor |
| `B01-03` | 续写与改写 | P40 | `B01-01`、`B01-02` | b01-anchor |
| `B01-04` | 扩写与压缩 | P60 | `B01-03` | b01-anchor |
| `B01-05` | 标题与导语生成 | P40 | — | b01-anchor |
| `B01-06` | 营销文案 | P60 | `B01-05` | b01-anchor |
| `B01-07` | 公文与技术写作 | P40 | — | b01-anchor |
| `B01-08` | 创意写作与诗歌 | P60 | `B01-07` | b01-anchor |
| `B01-09` | 去 AI 味与人类化改写 | P40 | `B01-08`、`B01-02` | b01-anchor |
| `B01-10` | 事实一致性与引用 | P60 | — | b01-anchor |
| `B01-11` | 多轮编辑与版本管理 | P40 | `B01-04` | b01-anchor |
| `B01-12` | 生成质量评估 | P60 | `B01-10`、`B01-11` | b01-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `B01-01`、`B01-07`、`B01-08`、`B01-09`、`B01-11` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `B01-03`、`B01-06`、`B01-09`、`B01-12`、`STD-frictionless-package` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `B01-01`、`B01-04`、`B01-07`、`B01-10`、`STD-ietf-json` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `B01-02`、`B01-03`、`B01-05`、`B01-06`、`B01-10`、`B01-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `B01-04`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `B01-02`、`B01-05`、`B01-08`、`B01-11`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B01-长文结构与大纲` | `B01-01` |
| `B01-文风与语体控制` | `B01-02` |
| `B01-续写与改写` | `B01-03` |
| `B01-扩写与压缩` | `B01-04` |
| `B01-标题与导语生成` | `B01-05` |
| `B01-营销文案` | `B01-06` |
| `B01-公文与技术写作` | `B01-07` |
| `B01-创意写作与诗歌` | `B01-08` |
| `B01-去-AI-味与人类化改写` | `B01-09` |
| `B01-事实一致性与引用` | `B01-10` |
| `B01-多轮编辑与版本管理` | `B01-11` |
| `B01-生成质量评估` | `B01-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "文本生成与创作"
  code: "B01"
  provenance_strength: "external"
  provenance_legend:
    b01-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B01-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "文本生成与创作 全域"
      nodes:
        - "B01-01"
        - "B01-02"
        - "B01-03"
        - "B01-04"
        - "B01-05"
        - "B01-06"
        - "B01-07"
        - "B01-08"
        - "B01-09"
        - "B01-10"
        - "B01-11"
        - "B01-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "B01-01"
      name: "长文结构与大纲"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b01-anchor"
    - id: "B01-02"
      name: "文风与语体控制"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b01-anchor"
    - id: "B01-03"
      name: "续写与改写"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B01-01"
        - "B01-02"
      provenance:
        - "b01-anchor"
    - id: "B01-04"
      name: "扩写与压缩"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B01-03"
      provenance:
        - "b01-anchor"
    - id: "B01-05"
      name: "标题与导语生成"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b01-anchor"
    - id: "B01-06"
      name: "营销文案"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B01-05"
      provenance:
        - "b01-anchor"
    - id: "B01-07"
      name: "公文与技术写作"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b01-anchor"
    - id: "B01-08"
      name: "创意写作与诗歌"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B01-07"
      provenance:
        - "b01-anchor"
    - id: "B01-09"
      name: "去 AI 味与人类化改写"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B01-08"
        - "B01-02"
      provenance:
        - "b01-anchor"
    - id: "B01-10"
      name: "事实一致性与引用"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b01-anchor"
    - id: "B01-11"
      name: "多轮编辑与版本管理"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B01-04"
      provenance:
        - "b01-anchor"
    - id: "B01-12"
      name: "生成质量评估"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B01-10"
        - "B01-11"
      provenance:
        - "b01-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B01-01"
        - "B01-07"
        - "B01-08"
        - "B01-09"
        - "B01-11"
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
        - "B01-03"
        - "B01-06"
        - "B01-09"
        - "B01-12"
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
        - "B01-01"
        - "B01-04"
        - "B01-07"
        - "B01-10"
        - "STD-ietf-json"
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
        - "B01-02"
        - "B01-03"
        - "B01-05"
        - "B01-06"
        - "B01-10"
        - "B01-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B01-04"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B01-02"
        - "B01-05"
        - "B01-08"
        - "B01-11"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B01-00）不随包交付，装载方须自备领域基础。
