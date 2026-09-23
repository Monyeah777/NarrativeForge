<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 开源与开发者生态（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「开源与开发者生态」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（开源与开发者生态:M01）与收口模块（开源与开发者生态:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 17 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（F09-00 领域通用前置）；节点 29 · 边 50 · 密度 1.7241。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `F09-01` | 开源许可选择 | P40 | — | f09-anchor |
| `F09-02` | 权重发布 | P60 | `F09-01` | f09-anchor |
| `F09-03` | SDK 与接口设计 | P40 | `F09-02` | f09-anchor |
| `F09-04` | 文档与示例 | P60 | `F09-03`、`F09-01` | f09-anchor |
| `F09-05` | 插件与工具市场 | P40 | `F09-04`、`F09-02` | f09-anchor |
| `F09-06` | 社区治理 | P60 | `F09-05`、`F09-03` | f09-anchor |
| `F09-07` | 贡献者规范 | P40 | `F09-06`、`F09-04` | f09-anchor |
| `F09-08` | 评测共建 | P60 | `F09-07`、`F09-05` | f09-anchor |
| `F09-09` | 商业与开源边界 | P40 | `F09-08`、`F09-06` | f09-anchor |
| `F09-10` | 镜像与分发 | P60 | `F09-09`、`F09-07` | f09-anchor |
| `F09-11` | 安全响应 | P40 | `F09-10`、`F09-08` | f09-anchor |
| `F09-12` | 生态合作 | P60 | `F09-11`、`F09-09` | f09-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `F09-04` | std-catalog |
| `STD-creativecommons` | 标准 · 许可与权利表达（Creative Commons｜gov｜实测 ✓） | P80 | `F09-01` | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `F09-06`、`F09-11`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `F09-05`、`F09-10` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `F09-08` | std-catalog |
| `STD-nist-800-188` | 标准 · SP 800-188 去标识化（NIST｜gov｜实测 ✓） | P80 | `F09-06`、`STD-nist-privacy` | std-catalog |
| `STD-nist-privacy` | 标准 · 隐私框架（NIST｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-oasis-openapi` | 标准 · OpenAPI 3.1（OpenAPI Initiative｜iface｜实测 ✓） | P80 | `F09-03`、`STD-ietf-json-schema` | std-catalog |
| `STD-osi-osd` | 标准 · 开源定义（OSI｜gov｜实测 ✓） | P80 | `F09-05`、`F09-07`、`F09-09` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP｜gov｜实测 ✓） | P80 | `F09-11`、`STD-owasp-top10` | std-catalog |
| `STD-owasp-top10` | 标准 · Web 十大风险（OWASP｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-spdx-3` | 标准 · SPDX 3.0（含 AI profile）（SPDX｜gov｜实测 ✓） | P80 | `F09-03`、`F09-08` | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX｜gov｜实测 ✓） | P80 | `F09-02`、`F09-10`、`F09-12`、`F09-01`、`F09-09` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `F09-02`、`F09-07`、`F09-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C｜form｜实测 ✓） | P80 | `F09-04`、`STD-w3c-xml` | std-catalog |
| `STD-w3c-xml` | 标准 · XML 1.0（W3C｜data｜实测 ✓） | P80 | — | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `F09-开源许可选择` | `F09-01` |
| `F09-权重发布` | `F09-02` |
| `F09-SDK-与接口设计` | `F09-03` |
| `F09-文档与示例` | `F09-04` |
| `F09-插件与工具市场` | `F09-05` |
| `F09-社区治理` | `F09-06` |
| `F09-贡献者规范` | `F09-07` |
| `F09-评测共建` | `F09-08` |
| `F09-商业与开源边界` | `F09-09` |
| `F09-镜像与分发` | `F09-10` |
| `F09-安全响应` | `F09-11` |
| `F09-生态合作` | `F09-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-creativecommons` | `STD-creativecommons` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-nist-800-188` | `STD-nist-800-188` |
| `std-nist-privacy` | `STD-nist-privacy` |
| `std-oasis-openapi` | `STD-oasis-openapi` |
| `std-osi-osd` | `STD-osi-osd` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-owasp-top10` | `STD-owasp-top10` |
| `std-spdx-3` | `STD-spdx-3` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-xml` | `STD-w3c-xml` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "开源与开发者生态"
  code: "F09"
  provenance_strength: "external"
  provenance_legend:
    f09-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "F09-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "开源与开发者生态 全域"
      nodes:
        - "F09-01"
        - "F09-02"
        - "F09-03"
        - "F09-04"
        - "F09-05"
        - "F09-06"
        - "F09-07"
        - "F09-08"
        - "F09-09"
        - "F09-10"
        - "F09-11"
        - "F09-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-creativecommons"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-nist-800-188"
        - "STD-nist-privacy"
        - "STD-oasis-openapi"
        - "STD-osi-osd"
        - "STD-owasp-llm"
        - "STD-owasp-top10"
        - "STD-spdx-3"
        - "STD-spdx-licenses"
        - "STD-vega-lite"
        - "STD-w3c-epub33"
        - "STD-w3c-xml"
  nodes:
    - id: "F09-01"
      name: "开源许可选择"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "f09-anchor"
    - id: "F09-02"
      name: "权重发布"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F09-01"
      provenance:
        - "f09-anchor"
    - id: "F09-03"
      name: "SDK 与接口设计"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F09-02"
      provenance:
        - "f09-anchor"
    - id: "F09-04"
      name: "文档与示例"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F09-03"
        - "F09-01"
      provenance:
        - "f09-anchor"
    - id: "F09-05"
      name: "插件与工具市场"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F09-04"
        - "F09-02"
      provenance:
        - "f09-anchor"
    - id: "F09-06"
      name: "社区治理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F09-05"
        - "F09-03"
      provenance:
        - "f09-anchor"
    - id: "F09-07"
      name: "贡献者规范"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F09-06"
        - "F09-04"
      provenance:
        - "f09-anchor"
    - id: "F09-08"
      name: "评测共建"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F09-07"
        - "F09-05"
      provenance:
        - "f09-anchor"
    - id: "F09-09"
      name: "商业与开源边界"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F09-08"
        - "F09-06"
      provenance:
        - "f09-anchor"
    - id: "F09-10"
      name: "镜像与分发"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F09-09"
        - "F09-07"
      provenance:
        - "f09-anchor"
    - id: "F09-11"
      name: "安全响应"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F09-10"
        - "F09-08"
      provenance:
        - "f09-anchor"
    - id: "F09-12"
      name: "生态合作"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F09-11"
        - "F09-09"
      provenance:
        - "f09-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-04"
      provenance:
        - "std-catalog"
    - id: "STD-creativecommons"
      name: "标准 · 许可与权利表达"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-01"
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
        - "F09-06"
        - "F09-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-05"
        - "F09-10"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-08"
      provenance:
        - "std-catalog"
    - id: "STD-nist-800-188"
      name: "标准 · SP 800-188 去标识化"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-06"
        - "STD-nist-privacy"
      provenance:
        - "std-catalog"
    - id: "STD-nist-privacy"
      name: "标准 · 隐私框架"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-oasis-openapi"
      name: "标准 · OpenAPI 3.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-03"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-osi-osd"
      name: "标准 · 开源定义"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-05"
        - "F09-07"
        - "F09-09"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-11"
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
    - id: "STD-spdx-3"
      name: "标准 · SPDX 3.0（含 AI profile）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-03"
        - "F09-08"
      provenance:
        - "std-catalog"
    - id: "STD-spdx-licenses"
      name: "标准 · SPDX 许可证清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-02"
        - "F09-10"
        - "F09-12"
        - "F09-01"
        - "F09-09"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-02"
        - "F09-07"
        - "F09-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F09-04"
        - "STD-w3c-xml"
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
- 包外前置族（F09-00）不随包交付，装载方须自备领域基础。
