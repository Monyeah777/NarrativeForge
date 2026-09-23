<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+政务与公共事务（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+政务与公共事务」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI政务与公共事务:M01）与收口模块（AI政务与公共事务:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 18 个**可扩展标准节点**（主锚/辅锚/依赖三层入图：概念 → 主锚、概念 → 辅锚、标准依赖边）+ 1 个包外前置族（D07-00 领域通用前置）；节点 30 · 边 52 · 密度 1.7333。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D07-01` | 政策文件解读 | P40 | — | d07-anchor |
| `D07-02` | 公文写作 | P60 | `D07-01` | d07-anchor |
| `D07-03` | 政务问答坐席 | P40 | `D07-02` | d07-anchor |
| `D07-04` | 审批流程辅助 | P60 | `D07-03`、`D07-01` | d07-anchor |
| `D07-05` | 舆情监测与回应 | P40 | `D07-04`、`D07-02` | d07-anchor |
| `D07-06` | 数据报送统计 | P60 | `D07-05`、`D07-03` | d07-anchor |
| `D07-07` | 法规合规检查 | P40 | `D07-06`、`D07-04` | d07-anchor |
| `D07-08` | 民生服务知识库 | P60 | `D07-07`、`D07-05` | d07-anchor |
| `D07-09` | 城市治理工单 | P40 | `D07-08`、`D07-06` | d07-anchor |
| `D07-10` | 政务信息公开 | P60 | `D07-09`、`D07-07` | d07-anchor |
| `D07-11` | 权限与保密 | P40 | `D07-10`、`D07-08` | d07-anchor |
| `D07-12` | 无障碍服务 | P60 | `D07-11`、`D07-09` | d07-anchor |
| `STD-cncf-cloudevents` | 标准 · CloudEvents 1.0（CNCF｜iface｜实测 ✓） | P80 | `D07-04`、`STD-ietf-json-schema` | std-catalog |
| `STD-common-criteria` | 标准 · Common Criteria（ISO 15408）（CCRA｜gov｜实测 ✓） | P80 | `D07-06` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark｜form｜实测 ✓） | P80 | `D07-02` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU｜gov｜实测 ✓） | P80 | `D07-07` | std-catalog |
| `STD-ietf-bcp47` | 标准 · 语言标签 (RFC 5646)（IETF｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json` | 标准 · JSON (RFC 8259)（IETF｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema｜data｜实测 ✓） | P80 | `D07-01`、`D07-05`、`D07-06`、`STD-ietf-json` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid｜form｜实测 ✓） | P80 | `D07-04`、`D07-09` | std-catalog |
| `STD-nist-800-188` | 标准 · SP 800-188 去标识化（NIST｜gov｜实测 ✓） | P80 | `D07-09`、`D07-11`、`STD-nist-privacy` | std-catalog |
| `STD-nist-privacy` | 标准 · 隐私框架（NIST｜gov｜实测 ✓） | P80 | — | std-catalog |
| `STD-oasis-openapi` | 标准 · OpenAPI 3.1（OpenAPI Initiative｜iface｜实测 ✓） | P80 | `D07-08`、`D07-12`、`STD-ietf-json-schema` | std-catalog |
| `STD-oecd-ai` | 标准 · OECD AI 原则（OECD｜gov｜实测 ✓） | P80 | `D07-01`、`D07-03`、`D07-10` | std-catalog |
| `STD-rdf11` | 标准 · RDF 1.1（W3C｜data｜实测 ✓） | P80 | — | std-catalog |
| `STD-vega-lite` | 标准 · Vega-Lite v5（Vega｜form｜实测 ✓） | P80 | `D07-03`、`D07-07`、`D07-08`、`STD-ietf-json-schema` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C｜gov｜实测 ✓） | P80 | `D07-02`、`D07-05`、`STD-rdf11` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C｜data｜实测 ✓） | P80 | `D07-10`、`STD-ietf-bcp47` | std-catalog |
| `STD-w3c-vc` | 标准 · Verifiable Credentials 2.0（W3C｜gov｜实测 ✓） | P80 | `D07-11`、`STD-rdf11` | std-catalog |
| `STD-w3c-wcag22` | 标准 · WCAG 2.2（W3C｜gov｜实测 ✓） | P80 | `D07-12` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D07-政策文件解读` | `D07-01` |
| `D07-公文写作` | `D07-02` |
| `D07-政务问答坐席` | `D07-03` |
| `D07-审批流程辅助` | `D07-04` |
| `D07-舆情监测与回应` | `D07-05` |
| `D07-数据报送统计` | `D07-06` |
| `D07-法规合规检查` | `D07-07` |
| `D07-民生服务知识库` | `D07-08` |
| `D07-城市治理工单` | `D07-09` |
| `D07-政务信息公开` | `D07-10` |
| `D07-权限与保密` | `D07-11` |
| `D07-无障碍服务` | `D07-12` |
| `std-cncf-cloudevents` | `STD-cncf-cloudevents` |
| `std-common-criteria` | `STD-common-criteria` |
| `std-commonmark` | `STD-commonmark` |
| `std-gdpr` | `STD-gdpr` |
| `std-ietf-bcp47` | `STD-ietf-bcp47` |
| `std-ietf-json` | `STD-ietf-json` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mermaid` | `STD-mermaid` |
| `std-nist-800-188` | `STD-nist-800-188` |
| `std-nist-privacy` | `STD-nist-privacy` |
| `std-oasis-openapi` | `STD-oasis-openapi` |
| `std-oecd-ai` | `STD-oecd-ai` |
| `std-rdf11` | `STD-rdf11` |
| `std-vega-lite` | `STD-vega-lite` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-vc` | `STD-w3c-vc` |
| `std-w3c-wcag22` | `STD-w3c-wcag22` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+政务与公共事务"
  code: "D07"
  provenance_strength: "external"
  provenance_legend:
    d07-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D07-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+政务与公共事务 全域"
      nodes:
        - "D07-01"
        - "D07-02"
        - "D07-03"
        - "D07-04"
        - "D07-05"
        - "D07-06"
        - "D07-07"
        - "D07-08"
        - "D07-09"
        - "D07-10"
        - "D07-11"
        - "D07-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-cloudevents"
        - "STD-common-criteria"
        - "STD-commonmark"
        - "STD-gdpr"
        - "STD-ietf-bcp47"
        - "STD-ietf-json"
        - "STD-ietf-json-schema"
        - "STD-mermaid"
        - "STD-nist-800-188"
        - "STD-nist-privacy"
        - "STD-oasis-openapi"
        - "STD-oecd-ai"
        - "STD-rdf11"
        - "STD-vega-lite"
        - "STD-w3c-prov-o"
        - "STD-w3c-tabular-data"
        - "STD-w3c-vc"
        - "STD-w3c-wcag22"
  nodes:
    - id: "D07-01"
      name: "政策文件解读"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d07-anchor"
    - id: "D07-02"
      name: "公文写作"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-01"
      provenance:
        - "d07-anchor"
    - id: "D07-03"
      name: "政务问答坐席"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D07-02"
      provenance:
        - "d07-anchor"
    - id: "D07-04"
      name: "审批流程辅助"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-03"
        - "D07-01"
      provenance:
        - "d07-anchor"
    - id: "D07-05"
      name: "舆情监测与回应"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D07-04"
        - "D07-02"
      provenance:
        - "d07-anchor"
    - id: "D07-06"
      name: "数据报送统计"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-05"
        - "D07-03"
      provenance:
        - "d07-anchor"
    - id: "D07-07"
      name: "法规合规检查"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D07-06"
        - "D07-04"
      provenance:
        - "d07-anchor"
    - id: "D07-08"
      name: "民生服务知识库"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-07"
        - "D07-05"
      provenance:
        - "d07-anchor"
    - id: "D07-09"
      name: "城市治理工单"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D07-08"
        - "D07-06"
      provenance:
        - "d07-anchor"
    - id: "D07-10"
      name: "政务信息公开"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-09"
        - "D07-07"
      provenance:
        - "d07-anchor"
    - id: "D07-11"
      name: "权限与保密"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D07-10"
        - "D07-08"
      provenance:
        - "d07-anchor"
    - id: "D07-12"
      name: "无障碍服务"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D07-11"
        - "D07-09"
      provenance:
        - "d07-anchor"
    - id: "STD-cncf-cloudevents"
      name: "标准 · CloudEvents 1.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-04"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-common-criteria"
      name: "标准 · Common Criteria（ISO 15408）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-06"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-02"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-07"
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
        - "D07-01"
        - "D07-05"
        - "D07-06"
        - "STD-ietf-json"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-04"
        - "D07-09"
      provenance:
        - "std-catalog"
    - id: "STD-nist-800-188"
      name: "标准 · SP 800-188 去标识化"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-09"
        - "D07-11"
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
        - "D07-08"
        - "D07-12"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-oecd-ai"
      name: "标准 · OECD AI 原则"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-01"
        - "D07-03"
        - "D07-10"
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
        - "D07-03"
        - "D07-07"
        - "D07-08"
        - "STD-ietf-json-schema"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-02"
        - "D07-05"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-10"
        - "STD-ietf-bcp47"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-vc"
      name: "标准 · Verifiable Credentials 2.0"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-11"
        - "STD-rdf11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-wcag22"
      name: "标准 · WCAG 2.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D07-12"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D07-00）不随包交付，装载方须自备领域基础。
