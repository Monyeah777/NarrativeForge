<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 代码大模型（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「代码大模型」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（代码大模型:M01）与收口模块（代码大模型:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 16 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（A09-00 领域通用前置）；节点 28 · 边 41 · 密度 1.4643。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A09-01` | 代码补全与上下文 | P40 | — | a09-anchor |
| `A09-02` | 仓库级代码理解 | P60 | `A09-01` | a09-anchor |
| `A09-03` | 代码检索与索引 | P40 | `A09-02` | a09-anchor |
| `A09-04` | 多语言代码翻译 | P60 | `A09-01` | a09-anchor |
| `A09-05` | 缺陷与漏洞检测 | P40 | `A09-02` | a09-anchor |
| `A09-06` | 单元测试生成 | P60 | `A09-05` | a09-anchor |
| `A09-07` | SQL 生成与优化 | P40 | — | a09-anchor |
| `A09-08` | Shell 与运维脚本 | P60 | — | a09-anchor |
| `A09-09` | 重构与迁移 | P40 | `A09-03` | a09-anchor |
| `A09-10` | 代码解释与注释 | P60 | `A09-07` | a09-anchor |
| `A09-11` | 代码评测基准 | P40 | `A09-05` | a09-anchor |
| `A09-12` | 私有代码安全 | P60 | `A09-08`、`A09-11` | a09-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | — | std-catalog |
| `STD-cwe` | 标准 · CWE 缺陷枚举（MITRE｜gov｜实测 ✓） | P80 | `A09-02`、`A09-05`、`A09-08` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless｜data｜实测 ✓） | P80 | `A09-03`、`STD-ietf-json-schema` | std-catalog |
| `STD-gfm` | 标准 · GFM 扩展（GitHub｜form｜实测 ✓） | P80 | `A09-01`、`STD-commonmark` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `A09-01`、`A09-05`、`A09-06`、`A09-10`、`A09-11`、`STD-ietf-json` | std-catalog |
| `STD-jsonrpc` | 标准 · JSON-RPC 2.0（JSON-RPC｜iface｜实测 ✓） | P80 | — | std-catalog |
| `STD-lsp` | 标准 · Language Server Protocol（Microsoft｜iface｜实测 ✓） | P80 | `A09-06`、`A09-09`、`STD-jsonrpc` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `A09-04`、`A09-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons｜eng｜实测 ✓） | P80 | `A09-11` | std-catalog |
| `STD-osv` | 标准 · OSV 漏洞格式（Google/OSV｜gov｜实测 ✓） | P80 | `A09-04`、`A09-07`、`A09-10` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP｜gov｜实测 ✓） | P80 | `A09-12`、`STD-owasp-top10` | std-catalog |
| `STD-owasp-top10` | 标准 · Web 十大风险（OWASP｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `A09-03`、`A09-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `A09-02`、`A09-07`、`A09-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A09-代码补全与上下文` | `A09-01` |
| `A09-仓库级代码理解` | `A09-02` |
| `A09-代码检索与索引` | `A09-03` |
| `A09-多语言代码翻译` | `A09-04` |
| `A09-缺陷与漏洞检测` | `A09-05` |
| `A09-单元测试生成` | `A09-06` |
| `A09-SQL-生成与优化` | `A09-07` |
| `A09-Shell-与运维脚本` | `A09-08` |
| `A09-重构与迁移` | `A09-09` |
| `A09-代码解释与注释` | `A09-10` |
| `A09-代码评测基准` | `A09-11` |
| `A09-私有代码安全` | `A09-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-cwe` | `STD-cwe` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-gfm` | `STD-gfm` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-jsonrpc` | `STD-jsonrpc` |
| `std-lsp` | `STD-lsp` |
| `std-mermaid` | `STD-mermaid` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-osv` | `STD-osv` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-owasp-top10` | `STD-owasp-top10` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "代码大模型"
  code: "A09"
  provenance_strength: "external"
  provenance_legend:
    a09-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A09-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "代码大模型 全域"
      nodes:
        - "A09-01"
        - "A09-02"
        - "A09-03"
        - "A09-04"
        - "A09-05"
        - "A09-06"
        - "A09-07"
        - "A09-08"
        - "A09-09"
        - "A09-10"
        - "A09-11"
        - "A09-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-cwe"
        - "STD-frictionless-package"
        - "STD-gfm"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-jsonrpc"
        - "STD-lsp"
        - "STD-mermaid"
        - "STD-mlcommons-bench"
        - "STD-osv"
        - "STD-owasp-llm"
        - "STD-owasp-top10"
        - "STD-vega-lite"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "A09-01"
      name: "代码补全与上下文"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a09-anchor"
    - id: "A09-02"
      name: "仓库级代码理解"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A09-01"
      provenance:
        - "a09-anchor"
    - id: "A09-03"
      name: "代码检索与索引"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A09-02"
      provenance:
        - "a09-anchor"
    - id: "A09-04"
      name: "多语言代码翻译"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A09-01"
      provenance:
        - "a09-anchor"
    - id: "A09-05"
      name: "缺陷与漏洞检测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A09-02"
      provenance:
        - "a09-anchor"
    - id: "A09-06"
      name: "单元测试生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A09-05"
      provenance:
        - "a09-anchor"
    - id: "A09-07"
      name: "SQL 生成与优化"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a09-anchor"
    - id: "A09-08"
      name: "Shell 与运维脚本"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a09-anchor"
    - id: "A09-09"
      name: "重构与迁移"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A09-03"
      provenance:
        - "a09-anchor"
    - id: "A09-10"
      name: "代码解释与注释"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A09-07"
      provenance:
        - "a09-anchor"
    - id: "A09-11"
      name: "代码评测基准"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A09-05"
      provenance:
        - "a09-anchor"
    - id: "A09-12"
      name: "私有代码安全"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A09-08"
        - "A09-11"
      provenance:
        - "a09-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs: []
      provenance:
        - "std-catalog"
    - id: "STD-cwe"
      name: "标准 · CWE 缺陷枚举"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A09-02"
        - "A09-05"
        - "A09-08"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A09-03"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-gfm"
      name: "标准 · GFM 扩展"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A09-01"
        - "STD-commonmark"
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
        - "A09-01"
        - "A09-05"
        - "A09-06"
        - "A09-10"
        - "A09-11"
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
    - id: "STD-lsp"
      name: "标准 · Language Server Protocol"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A09-06"
        - "A09-09"
        - "STD-jsonrpc"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A09-04"
        - "A09-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A09-11"
      provenance:
        - "std-catalog"
    - id: "STD-osv"
      name: "标准 · OSV 漏洞格式"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A09-04"
        - "A09-07"
        - "A09-10"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A09-12"
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
        - "A09-03"
        - "A09-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A09-02"
        - "A09-07"
        - "A09-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A09-00）不随包交付，装载方须自备领域基础。
