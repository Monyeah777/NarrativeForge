<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 记忆体与个性化（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「记忆体与个性化」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（记忆体与个性化:M01）与收口模块（记忆体与个性化:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 12 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（C14-00 领域通用前置）；节点 24 · 边 49 · 密度 2.0417。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C14-01` | 短期与长期记忆划分 | P40 | — | c14-anchor |
| `C14-02` | 用户画像建模 | P60 | `C14-01` | c14-anchor |
| `C14-03` | 记忆写入策略 | P40 | `C14-02` | c14-anchor |
| `C14-04` | 记忆检索与遗忘 | P60 | `C14-03`、`C14-01` | c14-anchor |
| `C14-05` | 记忆冲突消解 | P40 | `C14-04`、`C14-02` | c14-anchor |
| `C14-06` | 隐私与授权 | P60 | `C14-05`、`C14-03` | c14-anchor |
| `C14-07` | 跨会话一致性 | P40 | `C14-06`、`C14-04` | c14-anchor |
| `C14-08` | 记忆压缩 | P60 | `C14-07`、`C14-05` | c14-anchor |
| `C14-09` | 记忆评测 | P40 | `C14-08`、`C14-06` | c14-anchor |
| `C14-10` | 记忆形态选型 | P60 | `C14-09`、`C14-07` | c14-anchor |
| `C14-11` | 记忆注入污染 | P40 | `C14-10`、`C14-08` | c14-anchor |
| `C14-12` | 个性化冷启动 | P60 | `C14-11`、`C14-09` | c14-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry｜eng｜实测 ✓） | P80 | `C14-01`、`C14-07`、`C14-10` | std-catalog |
| `STD-creativecommons` | 标准 · 许可与权利表达（Creative Commons｜gov｜实测 ✓） | P80 | `C14-06` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | `C14-04`、`STD-ietf-json-schema` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless｜data｜实测 ✓） | P80 | `C14-03`、`C14-12`、`STD-frictionless-package` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `C14-01`、`C14-05`、`C14-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `C14-04`、`C14-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `C14-02`、`C14-05`、`C14-08`、`C14-09`、`C14-11` | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX｜gov｜实测 ✓） | P80 | `C14-06` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `C14-03`、`C14-07`、`C14-08`、`C14-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `C14-02`、`C14-10`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C14-短期与长期记忆划分` | `C14-01` |
| `C14-用户画像建模` | `C14-02` |
| `C14-记忆写入策略` | `C14-03` |
| `C14-记忆检索与遗忘` | `C14-04` |
| `C14-记忆冲突消解` | `C14-05` |
| `C14-隐私与授权` | `C14-06` |
| `C14-跨会话一致性` | `C14-07` |
| `C14-记忆压缩` | `C14-08` |
| `C14-记忆评测` | `C14-09` |
| `C14-记忆形态选型` | `C14-10` |
| `C14-记忆注入污染` | `C14-11` |
| `C14-个性化冷启动` | `C14-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-creativecommons` | `STD-creativecommons` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "记忆体与个性化"
  code: "C14"
  provenance_strength: "external"
  provenance_legend:
    c14-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C14-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "记忆体与个性化 全域"
      nodes:
        - "C14-01"
        - "C14-02"
        - "C14-03"
        - "C14-04"
        - "C14-05"
        - "C14-06"
        - "C14-07"
        - "C14-08"
        - "C14-09"
        - "C14-10"
        - "C14-11"
        - "C14-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-creativecommons"
        - "STD-frictionless-package"
        - "STD-frictionless-table"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-spdx-licenses"
        - "STD-vega-lite"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "C14-01"
      name: "短期与长期记忆划分"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c14-anchor"
    - id: "C14-02"
      name: "用户画像建模"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C14-01"
      provenance:
        - "c14-anchor"
    - id: "C14-03"
      name: "记忆写入策略"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C14-02"
      provenance:
        - "c14-anchor"
    - id: "C14-04"
      name: "记忆检索与遗忘"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C14-03"
        - "C14-01"
      provenance:
        - "c14-anchor"
    - id: "C14-05"
      name: "记忆冲突消解"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C14-04"
        - "C14-02"
      provenance:
        - "c14-anchor"
    - id: "C14-06"
      name: "隐私与授权"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C14-05"
        - "C14-03"
      provenance:
        - "c14-anchor"
    - id: "C14-07"
      name: "跨会话一致性"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C14-06"
        - "C14-04"
      provenance:
        - "c14-anchor"
    - id: "C14-08"
      name: "记忆压缩"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C14-07"
        - "C14-05"
      provenance:
        - "c14-anchor"
    - id: "C14-09"
      name: "记忆评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C14-08"
        - "C14-06"
      provenance:
        - "c14-anchor"
    - id: "C14-10"
      name: "记忆形态选型"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C14-09"
        - "C14-07"
      provenance:
        - "c14-anchor"
    - id: "C14-11"
      name: "记忆注入污染"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C14-10"
        - "C14-08"
      provenance:
        - "c14-anchor"
    - id: "C14-12"
      name: "个性化冷启动"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C14-11"
        - "C14-09"
      provenance:
        - "c14-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C14-01"
        - "C14-07"
        - "C14-10"
      provenance:
        - "std-catalog"
    - id: "STD-creativecommons"
      name: "标准 · 许可与权利表达"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C14-06"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C14-04"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C14-03"
        - "C14-12"
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
        - "C14-01"
        - "C14-05"
        - "C14-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C14-04"
        - "C14-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C14-02"
        - "C14-05"
        - "C14-08"
        - "C14-09"
        - "C14-11"
      provenance:
        - "std-catalog"
    - id: "STD-spdx-licenses"
      name: "标准 · SPDX 许可证清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C14-06"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C14-03"
        - "C14-07"
        - "C14-08"
        - "C14-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C14-02"
        - "C14-10"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C14-00）不随包交付，装载方须自备领域基础。
