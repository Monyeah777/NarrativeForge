<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 角色扮演与角色卡（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「角色扮演与角色卡」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（角色扮演与角色卡:M01）与收口模块（角色扮演与角色卡:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 12 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（E02-00 领域通用前置）；节点 24 · 边 49 · 密度 2.0417。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E02-01` | 人设卡撰写 | P40 | — | e02-anchor |
| `E02-02` | 性格一致性 | P60 | `E02-01` | e02-anchor |
| `E02-03` | 世界观绑定 | P40 | `E02-02` | e02-anchor |
| `E02-04` | 开场白设计 | P60 | `E02-03`、`E02-01` | e02-anchor |
| `E02-05` | 状态栏与变量 | P40 | `E02-04`、`E02-02` | e02-anchor |
| `E02-06` | 多角色群像 | P60 | `E02-05`、`E02-03` | e02-anchor |
| `E02-07` | 记忆与关系网 | P40 | `E02-06`、`E02-04` | e02-anchor |
| `E02-08` | 口癖与语料 | P60 | `E02-07`、`E02-05` | e02-anchor |
| `E02-09` | 安全边界 | P40 | `E02-08`、`E02-06` | e02-anchor |
| `E02-10` | 卡包封装 | P60 | `E02-09`、`E02-07` | e02-anchor |
| `E02-11` | 跨平台导入导出 | P40 | `E02-10`、`E02-08` | e02-anchor |
| `E02-12` | 角色卡评测 | P60 | `E02-11`、`E02-09` | e02-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `E02-01`、`E02-04`、`E02-07`、`E02-10`、`E02-02`、`E02-05`、`E02-12` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `E02-01`、`E02-06`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `E02-11` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `E02-12` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP｜gov｜实测 ✓） | P80 | `E02-09`、`STD-owasp-top10` | std-catalog |
| `STD-owasp-top10` | 标准 · Web 十大风险（OWASP｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `E02-08`、`E02-09`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C｜form｜实测 ✓） | P80 | `E02-03`、`E02-06`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `E02-02`、`E02-05`、`E02-08`、`E02-11`、`E02-03`、`E02-04`、`E02-07`、`E02-10`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E02-人设卡撰写` | `E02-01` |
| `E02-性格一致性` | `E02-02` |
| `E02-世界观绑定` | `E02-03` |
| `E02-开场白设计` | `E02-04` |
| `E02-状态栏与变量` | `E02-05` |
| `E02-多角色群像` | `E02-06` |
| `E02-记忆与关系网` | `E02-07` |
| `E02-口癖与语料` | `E02-08` |
| `E02-安全边界` | `E02-09` |
| `E02-卡包封装` | `E02-10` |
| `E02-跨平台导入导出` | `E02-11` |
| `E02-角色卡评测` | `E02-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-owasp-top10` | `STD-owasp-top10` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "角色扮演与角色卡"
  code: "E02"
  provenance_strength: "external"
  provenance_legend:
    e02-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "E02-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "角色扮演与角色卡 全域"
      nodes:
        - "E02-01"
        - "E02-02"
        - "E02-03"
        - "E02-04"
        - "E02-05"
        - "E02-06"
        - "E02-07"
        - "E02-08"
        - "E02-09"
        - "E02-10"
        - "E02-11"
        - "E02-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-owasp-llm"
        - "STD-owasp-top10"
        - "STD-vega-lite"
        - "STD-w3c-epub33"
        - "STD-w3c-tabular-data"
        - "STD-w3c-xml"
  nodes:
    - id: "E02-01"
      name: "人设卡撰写"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e02-anchor"
    - id: "E02-02"
      name: "性格一致性"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E02-01"
      provenance:
        - "e02-anchor"
    - id: "E02-03"
      name: "世界观绑定"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E02-02"
      provenance:
        - "e02-anchor"
    - id: "E02-04"
      name: "开场白设计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E02-03"
        - "E02-01"
      provenance:
        - "e02-anchor"
    - id: "E02-05"
      name: "状态栏与变量"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E02-04"
        - "E02-02"
      provenance:
        - "e02-anchor"
    - id: "E02-06"
      name: "多角色群像"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E02-05"
        - "E02-03"
      provenance:
        - "e02-anchor"
    - id: "E02-07"
      name: "记忆与关系网"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E02-06"
        - "E02-04"
      provenance:
        - "e02-anchor"
    - id: "E02-08"
      name: "口癖与语料"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E02-07"
        - "E02-05"
      provenance:
        - "e02-anchor"
    - id: "E02-09"
      name: "安全边界"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E02-08"
        - "E02-06"
      provenance:
        - "e02-anchor"
    - id: "E02-10"
      name: "卡包封装"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E02-09"
        - "E02-07"
      provenance:
        - "e02-anchor"
    - id: "E02-11"
      name: "跨平台导入导出"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E02-10"
        - "E02-08"
      provenance:
        - "e02-anchor"
    - id: "E02-12"
      name: "角色卡评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E02-11"
        - "E02-09"
      provenance:
        - "e02-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E02-01"
        - "E02-04"
        - "E02-07"
        - "E02-10"
        - "E02-02"
        - "E02-05"
        - "E02-12"
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
        - "E02-01"
        - "E02-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E02-11"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E02-12"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E02-09"
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
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E02-08"
        - "E02-09"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E02-03"
        - "E02-06"
        - "STD-w3c-xml"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "E02-02"
        - "E02-05"
        - "E02-08"
        - "E02-11"
        - "E02-03"
        - "E02-04"
        - "E02-07"
        - "E02-10"
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
- 包外前置族（E02-00）不随包交付，装载方须自备领域基础。
