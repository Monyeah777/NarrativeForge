<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+能源与电力（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+能源与电力」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI能源与电力:M01）与收口模块（AI能源与电力:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 8 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（D09-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D09-01` | 电网调度规程 | P40 | — | d09-anchor |
| `D09-02` | 设备巡检与缺陷识别 | P60 | `D09-01` | d09-anchor |
| `D09-03` | 新能源功率预测 | P40 | `D09-02` | d09-anchor |
| `D09-04` | 电力交易策略 | P60 | `D09-03`、`D09-01` | d09-anchor |
| `D09-05` | 能耗碳排核算 | P40 | `D09-04`、`D09-02` | d09-anchor |
| `D09-06` | 安全作业规程 | P60 | `D09-05`、`D09-03` | d09-anchor |
| `D09-07` | 故障诊断知识库 | P40 | `D09-06`、`D09-04` | d09-anchor |
| `D09-08` | 储能运维 | P60 | `D09-07`、`D09-05` | d09-anchor |
| `D09-09` | 需求侧响应 | P40 | `D09-08`、`D09-06` | d09-anchor |
| `D09-10` | 油气管线监测 | P60 | `D09-09`、`D09-07` | d09-anchor |
| `D09-11` | 能源合规 | P40 | `D09-10`、`D09-08` | d09-anchor |
| `D09-12` | 能源问答助手 | P60 | `D09-11`、`D09-09` | d09-anchor |
| `STD-cwe` | 标准 · CWE 缺陷枚举（MITRE） | P80 | `D09-02` | std-catalog |
| `STD-gdpr` | 标准 · GDPR（EU） | P80 | `D09-11` | std-catalog |
| `STD-hl7-fhir` | 标准 · FHIR（资源扩展机制）（HL7） | P80 | `D09-07` | std-catalog |
| `STD-iso-iec-25010` | 标准 · SQuaRE 质量模型（ISO/IEC） | P80 | `D09-09` | std-catalog |
| `STD-iso-iec-42010` | 标准 · 架构描述（ISO/IEC） | P80 | `D09-01`、`D09-03`、`D09-04`、`D09-12` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST） | P80 | `D09-10` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP） | P80 | `D09-06` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C） | P80 | `D09-05`、`D09-08` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D09-电网调度规程` | `D09-01` |
| `D09-设备巡检与缺陷识别` | `D09-02` |
| `D09-新能源功率预测` | `D09-03` |
| `D09-电力交易策略` | `D09-04` |
| `D09-能耗碳排核算` | `D09-05` |
| `D09-安全作业规程` | `D09-06` |
| `D09-故障诊断知识库` | `D09-07` |
| `D09-储能运维` | `D09-08` |
| `D09-需求侧响应` | `D09-09` |
| `D09-油气管线监测` | `D09-10` |
| `D09-能源合规` | `D09-11` |
| `D09-能源问答助手` | `D09-12` |
| `std-cwe` | `STD-cwe` |
| `std-gdpr` | `STD-gdpr` |
| `std-hl7-fhir` | `STD-hl7-fhir` |
| `std-iso-iec-25010` | `STD-iso-iec-25010` |
| `std-iso-iec-42010` | `STD-iso-iec-42010` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+能源与电力"
  code: "D09"
  provenance_strength: "external"
  provenance_legend:
    d09-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D09-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+能源与电力 全域"
      nodes:
        - "D09-01"
        - "D09-02"
        - "D09-03"
        - "D09-04"
        - "D09-05"
        - "D09-06"
        - "D09-07"
        - "D09-08"
        - "D09-09"
        - "D09-10"
        - "D09-11"
        - "D09-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cwe"
        - "STD-gdpr"
        - "STD-hl7-fhir"
        - "STD-iso-iec-25010"
        - "STD-iso-iec-42010"
        - "STD-nist-ai-rmf"
        - "STD-owasp-llm"
        - "STD-w3c-prov-o"
  nodes:
    - id: "D09-01"
      name: "电网调度规程"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d09-anchor"
    - id: "D09-02"
      name: "设备巡检与缺陷识别"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D09-01"
      provenance:
        - "d09-anchor"
    - id: "D09-03"
      name: "新能源功率预测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D09-02"
      provenance:
        - "d09-anchor"
    - id: "D09-04"
      name: "电力交易策略"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D09-03"
        - "D09-01"
      provenance:
        - "d09-anchor"
    - id: "D09-05"
      name: "能耗碳排核算"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D09-04"
        - "D09-02"
      provenance:
        - "d09-anchor"
    - id: "D09-06"
      name: "安全作业规程"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D09-05"
        - "D09-03"
      provenance:
        - "d09-anchor"
    - id: "D09-07"
      name: "故障诊断知识库"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D09-06"
        - "D09-04"
      provenance:
        - "d09-anchor"
    - id: "D09-08"
      name: "储能运维"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D09-07"
        - "D09-05"
      provenance:
        - "d09-anchor"
    - id: "D09-09"
      name: "需求侧响应"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D09-08"
        - "D09-06"
      provenance:
        - "d09-anchor"
    - id: "D09-10"
      name: "油气管线监测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D09-09"
        - "D09-07"
      provenance:
        - "d09-anchor"
    - id: "D09-11"
      name: "能源合规"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D09-10"
        - "D09-08"
      provenance:
        - "d09-anchor"
    - id: "D09-12"
      name: "能源问答助手"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D09-11"
        - "D09-09"
      provenance:
        - "d09-anchor"
    - id: "STD-cwe"
      name: "标准 · CWE 缺陷枚举"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D09-02"
      provenance:
        - "std-catalog"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D09-11"
      provenance:
        - "std-catalog"
    - id: "STD-hl7-fhir"
      name: "标准 · FHIR（资源扩展机制）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D09-07"
      provenance:
        - "std-catalog"
    - id: "STD-iso-iec-25010"
      name: "标准 · SQuaRE 质量模型"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D09-09"
      provenance:
        - "std-catalog"
    - id: "STD-iso-iec-42010"
      name: "标准 · 架构描述"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D09-01"
        - "D09-03"
        - "D09-04"
        - "D09-12"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D09-10"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D09-06"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D09-05"
        - "D09-08"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D09-00）不随包交付，装载方须自备领域基础。
