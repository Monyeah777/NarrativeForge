<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 代码审查与缺陷检测（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「代码审查与缺陷检测」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（代码审查与缺陷检测:M01）与收口模块（代码审查与缺陷检测:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 12 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（B09-00 领域通用前置）；节点 24 · 边 39 · 密度 1.6250。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B09-01` | 静态审查规则 | P40 | — | b09-anchor |
| `B09-02` | 漏洞模式识别 | P60 | `B09-01` | b09-anchor |
| `B09-03` | 代码异味 | P40 | `B09-01` | b09-anchor |
| `B09-04` | 依赖与供应链风险 | P60 | — | b09-anchor |
| `B09-05` | 提交信息与 PR 描述 | P40 | `B09-04` | b09-anchor |
| `B09-06` | 变更影响面分析 | P60 | — | b09-anchor |
| `B09-07` | 测试覆盖缺口 | P40 | `B09-03` | b09-anchor |
| `B09-08` | 性能反模式 | P60 | `B09-06` | b09-anchor |
| `B09-09` | 审查意见生成 | P40 | `B09-02` | b09-anchor |
| `B09-10` | 误报率控制 | P60 | `B09-09` | b09-anchor |
| `B09-11` | 审查优先级排序 | P40 | `B09-07` | b09-anchor |
| `B09-12` | 自动化门禁集成 | P60 | `B09-10`、`B09-11` | b09-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `B09-04`、`B09-09` | std-catalog |
| `STD-cwe` | 标准 · CWE 缺陷枚举（MITRE｜gov｜实测 ✓） | P80 | `B09-02`、`B09-05`、`B09-08`、`B09-11` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `B09-01`、`B09-05`、`B09-06`、`B09-11`、`STD-ietf-json` | std-catalog |
| `STD-oasis-sarif` | 标准 · SARIF 2.1.0（OASIS｜iface｜实测 ✓） | P80 | `B09-01`、`B09-07`、`B09-10`、`STD-ietf-json-schema` | std-catalog |
| `STD-osv` | 标准 · OSV 漏洞格式（Google/OSV｜gov｜实测 ✓） | P80 | `B09-03`、`B09-06`、`B09-09`、`B09-12` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-spdx-3` | 标准 · SPDX 3.0（含 AI profile）（SPDX｜gov｜实测 ✓） | P80 | `B09-04` | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `B09-03`、`B09-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `B09-10`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `B09-02`、`B09-07`、`B09-12`、`STD-ietf-bcp47` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B09-静态审查规则` | `B09-01` |
| `B09-漏洞模式识别` | `B09-02` |
| `B09-代码异味` | `B09-03` |
| `B09-依赖与供应链风险` | `B09-04` |
| `B09-提交信息与-PR-描述` | `B09-05` |
| `B09-变更影响面分析` | `B09-06` |
| `B09-测试覆盖缺口` | `B09-07` |
| `B09-性能反模式` | `B09-08` |
| `B09-审查意见生成` | `B09-09` |
| `B09-误报率控制` | `B09-10` |
| `B09-审查优先级排序` | `B09-11` |
| `B09-自动化门禁集成` | `B09-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-cwe` | `STD-cwe` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-oasis-sarif` | `STD-oasis-sarif` |
| `std-osv` | `STD-osv` |
| `std-rdf11` | `STD-rdf11` |
| `std-spdx-3` | `STD-spdx-3` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "代码审查与缺陷检测"
  code: "B09"
  provenance_strength: "external"
  provenance_legend:
    b09-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B09-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "代码审查与缺陷检测 全域"
      nodes:
        - "B09-01"
        - "B09-02"
        - "B09-03"
        - "B09-04"
        - "B09-05"
        - "B09-06"
        - "B09-07"
        - "B09-08"
        - "B09-09"
        - "B09-10"
        - "B09-11"
        - "B09-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-cwe"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-oasis-sarif"
        - "STD-osv"
        - "STD-rdf11"
        - "STD-spdx-3"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
  nodes:
    - id: "B09-01"
      name: "静态审查规则"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b09-anchor"
    - id: "B09-02"
      name: "漏洞模式识别"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B09-01"
      provenance:
        - "b09-anchor"
    - id: "B09-03"
      name: "代码异味"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B09-01"
      provenance:
        - "b09-anchor"
    - id: "B09-04"
      name: "依赖与供应链风险"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b09-anchor"
    - id: "B09-05"
      name: "提交信息与 PR 描述"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B09-04"
      provenance:
        - "b09-anchor"
    - id: "B09-06"
      name: "变更影响面分析"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b09-anchor"
    - id: "B09-07"
      name: "测试覆盖缺口"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B09-03"
      provenance:
        - "b09-anchor"
    - id: "B09-08"
      name: "性能反模式"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B09-06"
      provenance:
        - "b09-anchor"
    - id: "B09-09"
      name: "审查意见生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B09-02"
      provenance:
        - "b09-anchor"
    - id: "B09-10"
      name: "误报率控制"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B09-09"
      provenance:
        - "b09-anchor"
    - id: "B09-11"
      name: "审查优先级排序"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B09-07"
      provenance:
        - "b09-anchor"
    - id: "B09-12"
      name: "自动化门禁集成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B09-10"
        - "B09-11"
      provenance:
        - "b09-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B09-04"
        - "B09-09"
      provenance:
        - "std-catalog"
    - id: "STD-cwe"
      name: "标准 · CWE 缺陷枚举"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B09-02"
        - "B09-05"
        - "B09-08"
        - "B09-11"
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
        - "B09-01"
        - "B09-05"
        - "B09-06"
        - "B09-11"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-oasis-sarif"
      name: "标准 · SARIF 2.1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B09-01"
        - "B09-07"
        - "B09-10"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-osv"
      name: "标准 · OSV 漏洞格式"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B09-03"
        - "B09-06"
        - "B09-09"
        - "B09-12"
      provenance:
        - "std-catalog"
    - id: "STD-rdf11"
      name: "标准 · RDF 1.1"
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
        - "B09-04"
      provenance:
        - "std-catalog"
    - id: "STD-vega-lite"
      name: "标准 · Vega-Lite v5"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B09-03"
        - "B09-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B09-10"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B09-02"
        - "B09-07"
        - "B09-12"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B09-00）不随包交付，装载方须自备领域基础。
