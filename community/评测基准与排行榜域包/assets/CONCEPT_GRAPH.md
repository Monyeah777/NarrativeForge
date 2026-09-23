<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 评测、基准与排行榜（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「评测、基准与排行榜」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（评测基准与排行榜:M01）与收口模块（评测基准与排行榜:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 9 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（C08-00 领域通用前置）；节点 21 · 边 48 · 密度 2.2857。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C08-01` | 基准集选型 | P40 | — | c08-anchor |
| `C08-02` | 私有评测集构建 | P60 | `C08-01` | c08-anchor |
| `C08-03` | 评测指标设计 | P40 | `C08-02` | c08-anchor |
| `C08-04` | LLM-as-judge | P60 | `C08-03`、`C08-01` | c08-anchor |
| `C08-05` | 人类评估协议 | P40 | `C08-04`、`C08-02` | c08-anchor |
| `C08-06` | 竞技场 Elo | P60 | `C08-05`、`C08-03` | c08-anchor |
| `C08-07` | 领域能力评测 | P40 | `C08-06`、`C08-04` | c08-anchor |
| `C08-08` | 鲁棒性与扰动 | P60 | `C08-07`、`C08-05` | c08-anchor |
| `C08-09` | 长上下文评测 | P40 | `C08-08`、`C08-06` | c08-anchor |
| `C08-10` | Agent 任务评测 | P60 | `C08-09`、`C08-07` | c08-anchor |
| `C08-11` | 评测污染检测 | P40 | `C08-10`、`C08-08` | c08-anchor |
| `C08-12` | 评测报告规范 | P60 | `C08-11`、`C08-09` | c08-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `C08-03` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `C08-01`、`C08-05`、`C08-06`、`C08-10`、`C08-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `C08-04`、`C08-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `C08-01`、`C08-05`、`C08-07`、`C08-09`、`C08-10`、`C08-11`、`C08-12` | std-catalog |
| `STD-oasis-sarif` | 标准 · SARIF 2.1.0（OASIS｜iface｜实测 ✓） | P80 | `C08-02`、`C08-04`、`C08-06`、`C08-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `C08-03`、`C08-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `C08-02`、`C08-07`、`C08-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C08-基准集选型` | `C08-01` |
| `C08-私有评测集构建` | `C08-02` |
| `C08-评测指标设计` | `C08-03` |
| `C08-LLM-as-judge` | `C08-04` |
| `C08-人类评估协议` | `C08-05` |
| `C08-竞技场-Elo` | `C08-06` |
| `C08-领域能力评测` | `C08-07` |
| `C08-鲁棒性与扰动` | `C08-08` |
| `C08-长上下文评测` | `C08-09` |
| `C08-Agent-任务评测` | `C08-10` |
| `C08-评测污染检测` | `C08-11` |
| `C08-评测报告规范` | `C08-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-oasis-sarif` | `STD-oasis-sarif` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "评测、基准与排行榜"
  code: "C08"
  provenance_strength: "external"
  provenance_legend:
    c08-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C08-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "评测、基准与排行榜 全域"
      nodes:
        - "C08-01"
        - "C08-02"
        - "C08-03"
        - "C08-04"
        - "C08-05"
        - "C08-06"
        - "C08-07"
        - "C08-08"
        - "C08-09"
        - "C08-10"
        - "C08-11"
        - "C08-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-oasis-sarif"
        - "STD-vega-lite"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "C08-01"
      name: "基准集选型"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c08-anchor"
    - id: "C08-02"
      name: "私有评测集构建"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C08-01"
      provenance:
        - "c08-anchor"
    - id: "C08-03"
      name: "评测指标设计"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C08-02"
      provenance:
        - "c08-anchor"
    - id: "C08-04"
      name: "LLM-as-judge"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C08-03"
        - "C08-01"
      provenance:
        - "c08-anchor"
    - id: "C08-05"
      name: "人类评估协议"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C08-04"
        - "C08-02"
      provenance:
        - "c08-anchor"
    - id: "C08-06"
      name: "竞技场 Elo"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C08-05"
        - "C08-03"
      provenance:
        - "c08-anchor"
    - id: "C08-07"
      name: "领域能力评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C08-06"
        - "C08-04"
      provenance:
        - "c08-anchor"
    - id: "C08-08"
      name: "鲁棒性与扰动"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C08-07"
        - "C08-05"
      provenance:
        - "c08-anchor"
    - id: "C08-09"
      name: "长上下文评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C08-08"
        - "C08-06"
      provenance:
        - "c08-anchor"
    - id: "C08-10"
      name: "Agent 任务评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C08-09"
        - "C08-07"
      provenance:
        - "c08-anchor"
    - id: "C08-11"
      name: "评测污染检测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C08-10"
        - "C08-08"
      provenance:
        - "c08-anchor"
    - id: "C08-12"
      name: "评测报告规范"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C08-11"
        - "C08-09"
      provenance:
        - "c08-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C08-03"
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
        - "C08-01"
        - "C08-05"
        - "C08-06"
        - "C08-10"
        - "C08-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C08-04"
        - "C08-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C08-01"
        - "C08-05"
        - "C08-07"
        - "C08-09"
        - "C08-10"
        - "C08-11"
        - "C08-12"
      provenance:
        - "std-catalog"
    - id: "STD-oasis-sarif"
      name: "标准 · SARIF 2.1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C08-02"
        - "C08-04"
        - "C08-06"
        - "C08-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C08-03"
        - "C08-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C08-02"
        - "C08-07"
        - "C08-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C08-00）不随包交付，装载方须自备领域基础。
