<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+保险（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+保险」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI保险:M01）与收口模块（AI保险:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 5 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（D05-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D05-01` | 保险条款解读 | P40 | — | d05-anchor |
| `D05-02` | 核保规则 | P60 | `D05-01` | d05-anchor |
| `D05-03` | 理赔材料审核 | P40 | `D05-02` | d05-anchor |
| `D05-04` | 理赔定损 | P60 | `D05-03`、`D05-01` | d05-anchor |
| `D05-05` | 精算建模 | P40 | `D05-04`、`D05-02` | d05-anchor |
| `D05-06` | 产品条款生成 | P60 | `D05-05`、`D05-03` | d05-anchor |
| `D05-07` | 保险客服问答 | P40 | `D05-06`、`D05-04` | d05-anchor |
| `D05-08` | 销售话术合规 | P60 | `D05-07`、`D05-05` | d05-anchor |
| `D05-09` | 反欺诈 | P40 | `D05-08`、`D05-06` | d05-anchor |
| `D05-10` | 保险法律合规 | P60 | `D05-09`、`D05-07` | d05-anchor |
| `D05-11` | 再保与风险 | P40 | `D05-10`、`D05-08` | d05-anchor |
| `D05-12` | 保单结构化 | P60 | `D05-11`、`D05-09` | d05-anchor |
| `STD-gdpr` | 标准 · GDPR（EU） | P80 | `D05-08`、`D05-10` | std-catalog |
| `STD-gips` | 标准 · GIPS 绩效标准（CFA Institute） | P80 | `D05-01`、`D05-07` | std-catalog |
| `STD-iso-iec-25010` | 标准 · SQuaRE 质量模型（ISO/IEC） | P80 | `D05-03`、`D05-06`、`D05-09`、`D05-12` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST） | P80 | `D05-04`、`D05-11` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C） | P80 | `D05-02`、`D05-05` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D05-保险条款解读` | `D05-01` |
| `D05-核保规则` | `D05-02` |
| `D05-理赔材料审核` | `D05-03` |
| `D05-理赔定损` | `D05-04` |
| `D05-精算建模` | `D05-05` |
| `D05-产品条款生成` | `D05-06` |
| `D05-保险客服问答` | `D05-07` |
| `D05-销售话术合规` | `D05-08` |
| `D05-反欺诈` | `D05-09` |
| `D05-保险法律合规` | `D05-10` |
| `D05-再保与风险` | `D05-11` |
| `D05-保单结构化` | `D05-12` |
| `std-gdpr` | `STD-gdpr` |
| `std-gips` | `STD-gips` |
| `std-iso-iec-25010` | `STD-iso-iec-25010` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+保险"
  code: "D05"
  provenance_strength: "external"
  provenance_legend:
    d05-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D05-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+保险 全域"
      nodes:
        - "D05-01"
        - "D05-02"
        - "D05-03"
        - "D05-04"
        - "D05-05"
        - "D05-06"
        - "D05-07"
        - "D05-08"
        - "D05-09"
        - "D05-10"
        - "D05-11"
        - "D05-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-gdpr"
        - "STD-gips"
        - "STD-iso-iec-25010"
        - "STD-nist-ai-rmf"
        - "STD-w3c-prov-o"
  nodes:
    - id: "D05-01"
      name: "保险条款解读"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d05-anchor"
    - id: "D05-02"
      name: "核保规则"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-01"
      provenance:
        - "d05-anchor"
    - id: "D05-03"
      name: "理赔材料审核"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D05-02"
      provenance:
        - "d05-anchor"
    - id: "D05-04"
      name: "理赔定损"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-03"
        - "D05-01"
      provenance:
        - "d05-anchor"
    - id: "D05-05"
      name: "精算建模"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D05-04"
        - "D05-02"
      provenance:
        - "d05-anchor"
    - id: "D05-06"
      name: "产品条款生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-05"
        - "D05-03"
      provenance:
        - "d05-anchor"
    - id: "D05-07"
      name: "保险客服问答"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D05-06"
        - "D05-04"
      provenance:
        - "d05-anchor"
    - id: "D05-08"
      name: "销售话术合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-07"
        - "D05-05"
      provenance:
        - "d05-anchor"
    - id: "D05-09"
      name: "反欺诈"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D05-08"
        - "D05-06"
      provenance:
        - "d05-anchor"
    - id: "D05-10"
      name: "保险法律合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-09"
        - "D05-07"
      provenance:
        - "d05-anchor"
    - id: "D05-11"
      name: "再保与风险"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D05-10"
        - "D05-08"
      provenance:
        - "d05-anchor"
    - id: "D05-12"
      name: "保单结构化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D05-11"
        - "D05-09"
      provenance:
        - "d05-anchor"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-08"
        - "D05-10"
      provenance:
        - "std-catalog"
    - id: "STD-gips"
      name: "标准 · GIPS 绩效标准"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-01"
        - "D05-07"
      provenance:
        - "std-catalog"
    - id: "STD-iso-iec-25010"
      name: "标准 · SQuaRE 质量模型"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-03"
        - "D05-06"
        - "D05-09"
        - "D05-12"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-04"
        - "D05-11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D05-02"
        - "D05-05"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D05-00）不随包交付，装载方须自备领域基础。
