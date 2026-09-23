<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 分类与情感分析（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「分类与情感分析」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（分类与情感分析:M01）与收口模块（分类与情感分析:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 12 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（B04-00 领域通用前置）；节点 24 · 边 39 · 密度 1.6250。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B04-01` | 意图识别 | P40 | — | b04-anchor |
| `B04-02` | 话题与标签分类 | P60 | `B04-01`、`B04-08` | b04-anchor |
| `B04-03` | 情感极性 | P40 | — | b04-anchor |
| `B04-04` | 细粒度情绪 | P60 | `B04-03` | b04-anchor |
| `B04-05` | 立场与观点检测 | P40 | `B04-04` | b04-anchor |
| `B04-06` | 垃圾与违规识别 | P60 | — | b04-anchor |
| `B04-07` | 情感强度与演化 | P40 | `B04-03` | b04-anchor |
| `B04-08` | 少样本分类 | P60 | — | b04-anchor |
| `B04-09` | 层级多标签 | P40 | `B04-02` | b04-anchor |
| `B04-10` | 阈值与概率校准 | P60 | `B04-06` | b04-anchor |
| `B04-11` | 标注一致性校验 | P40 | — | b04-anchor |
| `B04-12` | 分类评测指标 | P60 | `B04-10`、`B04-11`、`B04-05` | b04-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `B04-12` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `B04-07`、`B04-09`、`B04-11` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `B04-03`、`B04-06`、`B04-09`、`STD-frictionless-package` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `B04-01`、`B04-04`、`B04-07`、`B04-10`、`B04-11`、`STD-ietf-json` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `B04-12` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `B04-01`、`B04-02`、`B04-03`、`B04-05`、`B04-06`、`B04-10`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `B04-04`、`B04-08`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `B04-02`、`B04-05`、`B04-08`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B04-意图识别` | `B04-01` |
| `B04-话题与标签分类` | `B04-02` |
| `B04-情感极性` | `B04-03` |
| `B04-细粒度情绪` | `B04-04` |
| `B04-立场与观点检测` | `B04-05` |
| `B04-垃圾与违规识别` | `B04-06` |
| `B04-情感强度与演化` | `B04-07` |
| `B04-少样本分类` | `B04-08` |
| `B04-层级多标签` | `B04-09` |
| `B04-阈值与概率校准` | `B04-10` |
| `B04-标注一致性校验` | `B04-11` |
| `B04-分类评测指标` | `B04-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "分类与情感分析"
  code: "B04"
  provenance_strength: "external"
  provenance_legend:
    b04-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B04-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "分类与情感分析 全域"
      nodes:
        - "B04-01"
        - "B04-02"
        - "B04-03"
        - "B04-04"
        - "B04-05"
        - "B04-06"
        - "B04-07"
        - "B04-08"
        - "B04-09"
        - "B04-10"
        - "B04-11"
        - "B04-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mlcommons-bench"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "B04-01"
      name: "意图识别"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b04-anchor"
    - id: "B04-02"
      name: "话题与标签分类"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B04-01"
        - "B04-08"
      provenance:
        - "b04-anchor"
    - id: "B04-03"
      name: "情感极性"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b04-anchor"
    - id: "B04-04"
      name: "细粒度情绪"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B04-03"
      provenance:
        - "b04-anchor"
    - id: "B04-05"
      name: "立场与观点检测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B04-04"
      provenance:
        - "b04-anchor"
    - id: "B04-06"
      name: "垃圾与违规识别"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b04-anchor"
    - id: "B04-07"
      name: "情感强度与演化"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B04-03"
      provenance:
        - "b04-anchor"
    - id: "B04-08"
      name: "少样本分类"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b04-anchor"
    - id: "B04-09"
      name: "层级多标签"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B04-02"
      provenance:
        - "b04-anchor"
    - id: "B04-10"
      name: "阈值与概率校准"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B04-06"
      provenance:
        - "b04-anchor"
    - id: "B04-11"
      name: "标注一致性校验"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b04-anchor"
    - id: "B04-12"
      name: "分类评测指标"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B04-10"
        - "B04-11"
        - "B04-05"
      provenance:
        - "b04-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B04-12"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B04-07"
        - "B04-09"
        - "B04-11"
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
        - "B04-03"
        - "B04-06"
        - "B04-09"
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
        - "B04-01"
        - "B04-04"
        - "B04-07"
        - "B04-10"
        - "B04-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B04-12"
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
        - "B04-01"
        - "B04-02"
        - "B04-03"
        - "B04-05"
        - "B04-06"
        - "B04-10"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B04-04"
        - "B04-08"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B04-02"
        - "B04-05"
        - "B04-08"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B04-00）不随包交付，装载方须自备领域基础。
