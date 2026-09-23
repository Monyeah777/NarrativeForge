<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI+食品与餐饮（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「AI+食品与餐饮」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（AI食品与餐饮:M01）与收口模块（AI食品与餐饮:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 4 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（D16-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D16-01` | 菜品研发 | P40 | — | d16-anchor |
| `D16-02` | 菜单与定价 | P60 | `D16-01` | d16-anchor |
| `D16-03` | 食材质检 | P40 | `D16-02` | d16-anchor |
| `D16-04` | 门店选址评估 | P60 | `D16-03`、`D16-01` | d16-anchor |
| `D16-05` | 外卖运营分析 | P40 | `D16-04`、`D16-02` | d16-anchor |
| `D16-06` | 食安风险监测 | P60 | `D16-05`、`D16-03` | d16-anchor |
| `D16-07` | 营养配餐 | P40 | `D16-06`、`D16-04` | d16-anchor |
| `D16-08` | 评论洞察 | P60 | `D16-07`、`D16-05` | d16-anchor |
| `D16-09` | 后厨标准化 | P40 | `D16-08`、`D16-06` | d16-anchor |
| `D16-10` | 食安标签识别 | P60 | `D16-09`、`D16-07` | d16-anchor |
| `D16-11` | 门店排班 | P40 | `D16-10`、`D16-08` | d16-anchor |
| `D16-12` | 食品法规合规 | P60 | `D16-11`、`D16-09` | d16-anchor |
| `STD-gdpr` | 标准 · GDPR（EU） | P80 | `D16-12` | std-catalog |
| `STD-iso-iec-25010` | 标准 · SQuaRE 质量模型（ISO/IEC） | P80 | `D16-03`、`D16-09` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST） | P80 | `D16-01`、`D16-04`、`D16-06`、`D16-07`、`D16-10` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C） | P80 | `D16-02`、`D16-05`、`D16-08`、`D16-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D16-菜品研发` | `D16-01` |
| `D16-菜单与定价` | `D16-02` |
| `D16-食材质检` | `D16-03` |
| `D16-门店选址评估` | `D16-04` |
| `D16-外卖运营分析` | `D16-05` |
| `D16-食安风险监测` | `D16-06` |
| `D16-营养配餐` | `D16-07` |
| `D16-评论洞察` | `D16-08` |
| `D16-后厨标准化` | `D16-09` |
| `D16-食安标签识别` | `D16-10` |
| `D16-门店排班` | `D16-11` |
| `D16-食品法规合规` | `D16-12` |
| `std-gdpr` | `STD-gdpr` |
| `std-iso-iec-25010` | `STD-iso-iec-25010` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "AI+食品与餐饮"
  code: "D16"
  provenance_strength: "external"
  provenance_legend:
    d16-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "D16-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "AI+食品与餐饮 全域"
      nodes:
        - "D16-01"
        - "D16-02"
        - "D16-03"
        - "D16-04"
        - "D16-05"
        - "D16-06"
        - "D16-07"
        - "D16-08"
        - "D16-09"
        - "D16-10"
        - "D16-11"
        - "D16-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-gdpr"
        - "STD-iso-iec-25010"
        - "STD-nist-ai-rmf"
        - "STD-w3c-prov-o"
  nodes:
    - id: "D16-01"
      name: "菜品研发"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d16-anchor"
    - id: "D16-02"
      name: "菜单与定价"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D16-01"
      provenance:
        - "d16-anchor"
    - id: "D16-03"
      name: "食材质检"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D16-02"
      provenance:
        - "d16-anchor"
    - id: "D16-04"
      name: "门店选址评估"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D16-03"
        - "D16-01"
      provenance:
        - "d16-anchor"
    - id: "D16-05"
      name: "外卖运营分析"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D16-04"
        - "D16-02"
      provenance:
        - "d16-anchor"
    - id: "D16-06"
      name: "食安风险监测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D16-05"
        - "D16-03"
      provenance:
        - "d16-anchor"
    - id: "D16-07"
      name: "营养配餐"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D16-06"
        - "D16-04"
      provenance:
        - "d16-anchor"
    - id: "D16-08"
      name: "评论洞察"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D16-07"
        - "D16-05"
      provenance:
        - "d16-anchor"
    - id: "D16-09"
      name: "后厨标准化"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D16-08"
        - "D16-06"
      provenance:
        - "d16-anchor"
    - id: "D16-10"
      name: "食安标签识别"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D16-09"
        - "D16-07"
      provenance:
        - "d16-anchor"
    - id: "D16-11"
      name: "门店排班"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D16-10"
        - "D16-08"
      provenance:
        - "d16-anchor"
    - id: "D16-12"
      name: "食品法规合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D16-11"
        - "D16-09"
      provenance:
        - "d16-anchor"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D16-12"
      provenance:
        - "std-catalog"
    - id: "STD-iso-iec-25010"
      name: "标准 · SQuaRE 质量模型"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D16-03"
        - "D16-09"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D16-01"
        - "D16-04"
        - "D16-06"
        - "D16-07"
        - "D16-10"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "D16-02"
        - "D16-05"
        - "D16-08"
        - "D16-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D16-00）不随包交付，装载方须自备领域基础。
