<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+制药与生物（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+制药与生物」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI制药与生物:M01）与收口模块（AI制药与生物:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（D02-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D02-01` | 靶点与分子筛选 | P40 | — | d02-anchor |
| `D02-02` | 蛋白结构预测 | P60 | `D02-01` | d02-anchor |
| `D02-03` | 化合物库分析 | P40 | `D02-02` | d02-anchor |
| `D02-04` | 临床试验方案生成 | P60 | `D02-03`、`D02-01` | d02-anchor |
| `D02-05` | 药物警戒信号 | P40 | `D02-04`、`D02-02` | d02-anchor |
| `D02-06` | 法规申报文档 | P60 | `D02-05`、`D02-03` | d02-anchor |
| `D02-07` | 生物信息学流程 | P40 | `D02-06`、`D02-04` | d02-anchor |
| `D02-08` | 基因数据解读 | P60 | `D02-07`、`D02-05` | d02-anchor |
| `D02-09` | 电子实验记录 | P40 | `D02-08`、`D02-06` | d02-anchor |
| `D02-10` | 科研文献图谱 | P60 | `D02-09`、`D02-07` | d02-anchor |
| `D02-11` | 专利与独占分析 | P40 | `D02-10`、`D02-08` | d02-anchor |
| `D02-12` | 研发知识管理 | P60 | `D02-11`、`D02-09` | d02-anchor |
| `STD-hl7-fhir` | 标准 · FHIR（资源扩展机制）（HL7） | P80 | `D02-04` | std-catalog |
| `STD-iso-iec-25010` | 标准 · SQuaRE 质量模型（ISO/IEC） | P80 | `D02-03`、`D02-09`、`D02-12` | std-catalog |
| `STD-mermaid` | 标准 · Mermaid 图语言（Mermaid） | P80 | `D02-07` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST） | P80 | `D02-01`、`D02-10` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C） | P80 | `D02-06` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C） | P80 | `D02-02`、`D02-05`、`D02-08`、`D02-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D02-靶点与分子筛选` | `D02-01` |
| `D02-蛋白结构预测` | `D02-02` |
| `D02-化合物库分析` | `D02-03` |
| `D02-临床试验方案生成` | `D02-04` |
| `D02-药物警戒信号` | `D02-05` |
| `D02-法规申报文档` | `D02-06` |
| `D02-生物信息学流程` | `D02-07` |
| `D02-基因数据解读` | `D02-08` |
| `D02-电子实验记录` | `D02-09` |
| `D02-科研文献图谱` | `D02-10` |
| `D02-专利与独占分析` | `D02-11` |
| `D02-研发知识管理` | `D02-12` |
| `std-hl7-fhir` | `STD-hl7-fhir` |
| `std-iso-iec-25010` | `STD-iso-iec-25010` |
| `std-mermaid` | `STD-mermaid` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-w3c-epub33` | `STD-w3c-epub33` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+制药与生物"
  code: "D02"
  provenance_strength: "external"
  provenance_legend:
    d02-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D02-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+制药与生物 全域"
      nodes:
        - "D02-01"
        - "D02-02"
        - "D02-03"
        - "D02-04"
        - "D02-05"
        - "D02-06"
        - "D02-07"
        - "D02-08"
        - "D02-09"
        - "D02-10"
        - "D02-11"
        - "D02-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-hl7-fhir"
        - "STD-iso-iec-25010"
        - "STD-mermaid"
        - "STD-nist-ai-rmf"
        - "STD-w3c-epub33"
        - "STD-w3c-prov-o"
  nodes:
    - id: "D02-01"
      name: "靶点与分子筛选"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d02-anchor"
    - id: "D02-02"
      name: "蛋白结构预测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D02-01"
      provenance:
        - "d02-anchor"
    - id: "D02-03"
      name: "化合物库分析"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D02-02"
      provenance:
        - "d02-anchor"
    - id: "D02-04"
      name: "临床试验方案生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D02-03"
        - "D02-01"
      provenance:
        - "d02-anchor"
    - id: "D02-05"
      name: "药物警戒信号"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D02-04"
        - "D02-02"
      provenance:
        - "d02-anchor"
    - id: "D02-06"
      name: "法规申报文档"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D02-05"
        - "D02-03"
      provenance:
        - "d02-anchor"
    - id: "D02-07"
      name: "生物信息学流程"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D02-06"
        - "D02-04"
      provenance:
        - "d02-anchor"
    - id: "D02-08"
      name: "基因数据解读"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D02-07"
        - "D02-05"
      provenance:
        - "d02-anchor"
    - id: "D02-09"
      name: "电子实验记录"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D02-08"
        - "D02-06"
      provenance:
        - "d02-anchor"
    - id: "D02-10"
      name: "科研文献图谱"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D02-09"
        - "D02-07"
      provenance:
        - "d02-anchor"
    - id: "D02-11"
      name: "专利与独占分析"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D02-10"
        - "D02-08"
      provenance:
        - "d02-anchor"
    - id: "D02-12"
      name: "研发知识管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D02-11"
        - "D02-09"
      provenance:
        - "d02-anchor"
    - id: "STD-hl7-fhir"
      name: "标准 · FHIR（资源扩展机制）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D02-04"
      provenance:
        - "std-catalog"
    - id: "STD-iso-iec-25010"
      name: "标准 · SQuaRE 质量模型"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D02-03"
        - "D02-09"
        - "D02-12"
      provenance:
        - "std-catalog"
    - id: "STD-mermaid"
      name: "标准 · Mermaid 图语言"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D02-07"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D02-01"
        - "D02-10"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D02-06"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D02-02"
        - "D02-05"
        - "D02-08"
        - "D02-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D02-00）不随包交付，装载方须自备领域基础。
