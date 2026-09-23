<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 合规与监管（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「合规与监管」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（合规与监管:M01）与收口模块（合规与监管:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 5 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（F02-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `F02-01` | 服务备案 | P40 | — | f02-anchor |
| `F02-02` | 合成内容标识 | P60 | `F02-01` | f02-anchor |
| `F02-03` | 数据出境 | P40 | `F02-02` | f02-anchor |
| `F02-04` | 行业准入 | P60 | `F02-03`、`F02-01` | f02-anchor |
| `F02-05` | 算法推荐合规 | P40 | `F02-04`、`F02-02` | f02-anchor |
| `F02-06` | 未成年人保护 | P60 | `F02-05`、`F02-03` | f02-anchor |
| `F02-07` | 广告合规 | P40 | `F02-06`、`F02-04` | f02-anchor |
| `F02-08` | 跨境合规 | P60 | `F02-07`、`F02-05` | f02-anchor |
| `F02-09` | 留痕与审计 | P40 | `F02-08`、`F02-06` | f02-anchor |
| `F02-10` | 监管报送 | P60 | `F02-09`、`F02-07` | f02-anchor |
| `F02-11` | 合规培训 | P40 | `F02-10`、`F02-08` | f02-anchor |
| `F02-12` | 法规跟踪 | P60 | `F02-11`、`F02-09` | f02-anchor |
| `STD-gdpr` | 标准 · GDPR（EU） | P80 | `F02-05`、`F02-07`、`F02-08`、`F02-10`、`F02-11` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST） | P80 | `F02-04` | std-catalog |
| `STD-oasis-openapi` | 标准 · OpenAPI 3.1（OpenAPI Initiative） | P80 | `F02-01` | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX） | P80 | `F02-03`、`F02-06`、`F02-12` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C） | P80 | `F02-02`、`F02-09` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `F02-服务备案` | `F02-01` |
| `F02-合成内容标识` | `F02-02` |
| `F02-数据出境` | `F02-03` |
| `F02-行业准入` | `F02-04` |
| `F02-算法推荐合规` | `F02-05` |
| `F02-未成年人保护` | `F02-06` |
| `F02-广告合规` | `F02-07` |
| `F02-跨境合规` | `F02-08` |
| `F02-留痕与审计` | `F02-09` |
| `F02-监管报送` | `F02-10` |
| `F02-合规培训` | `F02-11` |
| `F02-法规跟踪` | `F02-12` |
| `std-gdpr` | `STD-gdpr` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-oasis-openapi` | `STD-oasis-openapi` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "合规与监管"
  code: "F02"
  provenance_strength: "external"
  provenance_legend:
    f02-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "F02-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "合规与监管 全域"
      nodes:
        - "F02-01"
        - "F02-02"
        - "F02-03"
        - "F02-04"
        - "F02-05"
        - "F02-06"
        - "F02-07"
        - "F02-08"
        - "F02-09"
        - "F02-10"
        - "F02-11"
        - "F02-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-gdpr"
        - "STD-nist-ai-rmf"
        - "STD-oasis-openapi"
        - "STD-spdx-licenses"
        - "STD-w3c-prov-o"
  nodes:
    - id: "F02-01"
      name: "服务备案"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "f02-anchor"
    - id: "F02-02"
      name: "合成内容标识"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F02-01"
      provenance:
        - "f02-anchor"
    - id: "F02-03"
      name: "数据出境"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F02-02"
      provenance:
        - "f02-anchor"
    - id: "F02-04"
      name: "行业准入"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F02-03"
        - "F02-01"
      provenance:
        - "f02-anchor"
    - id: "F02-05"
      name: "算法推荐合规"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F02-04"
        - "F02-02"
      provenance:
        - "f02-anchor"
    - id: "F02-06"
      name: "未成年人保护"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F02-05"
        - "F02-03"
      provenance:
        - "f02-anchor"
    - id: "F02-07"
      name: "广告合规"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F02-06"
        - "F02-04"
      provenance:
        - "f02-anchor"
    - id: "F02-08"
      name: "跨境合规"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F02-07"
        - "F02-05"
      provenance:
        - "f02-anchor"
    - id: "F02-09"
      name: "留痕与审计"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F02-08"
        - "F02-06"
      provenance:
        - "f02-anchor"
    - id: "F02-10"
      name: "监管报送"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F02-09"
        - "F02-07"
      provenance:
        - "f02-anchor"
    - id: "F02-11"
      name: "合规培训"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F02-10"
        - "F02-08"
      provenance:
        - "f02-anchor"
    - id: "F02-12"
      name: "法规跟踪"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F02-11"
        - "F02-09"
      provenance:
        - "f02-anchor"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F02-05"
        - "F02-07"
        - "F02-08"
        - "F02-10"
        - "F02-11"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F02-04"
      provenance:
        - "std-catalog"
    - id: "STD-oasis-openapi"
      name: "标准 · OpenAPI 3.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F02-01"
      provenance:
        - "std-catalog"
    - id: "STD-spdx-licenses"
      name: "标准 · SPDX 许可证清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F02-03"
        - "F02-06"
        - "F02-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F02-02"
        - "F02-09"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（F02-00）不随包交付，装载方须自备领域基础。
