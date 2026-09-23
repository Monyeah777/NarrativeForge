<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 测试与用例生成（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「测试与用例生成」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（测试与用例生成:M01）与收口模块（测试与用例生成:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 4 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（B10-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B10-01` | 单元测试生成 | P40 | `B10-02` | b10-anchor |
| `B10-02` | 边界与等价类 | P60 | — | b10-anchor |
| `B10-03` | 模糊测试用例 | P40 | `B10-02`、`B10-06` | b10-anchor |
| `B10-04` | 接口与契约测试 | P60 | — | b10-anchor |
| `B10-05` | UI 自动化脚本 | P40 | — | b10-anchor |
| `B10-06` | 测试数据构造 | P60 | — | b10-anchor |
| `B10-07` | 回归用例挑选 | P40 | `B10-01` | b10-anchor |
| `B10-08` | 覆盖率提升策略 | P60 | `B10-01` | b10-anchor |
| `B10-09` | 失败归因与复现 | P40 | `B10-07` | b10-anchor |
| `B10-10` | 端到端场景编排 | P60 | `B10-04`、`B10-05` | b10-anchor |
| `B10-11` | 测试可维护性 | P40 | `B10-01` | b10-anchor |
| `B10-12` | CI 集成 | P60 | `B10-10` | b10-anchor |
| `STD-a2a` | 标准 · A2A 协议（Linux Foundation） | P80 | `B10-10` | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema） | P80 | `B10-04` | std-catalog |
| `STD-nist-800-142` | 标准 · SP 800-142 组合测试实践（NIST） | P80 | `B10-01`、`B10-03`、`B10-05`、`B10-07`、`B10-09`、`B10-11` | std-catalog |
| `STD-peps` | 标准 · PEP 体系（含 8/257/621）（Python） | P80 | `B10-02`、`B10-06`、`B10-08`、`B10-12` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B10-单元测试生成` | `B10-01` |
| `B10-边界与等价类` | `B10-02` |
| `B10-模糊测试用例` | `B10-03` |
| `B10-接口与契约测试` | `B10-04` |
| `B10-UI-自动化脚本` | `B10-05` |
| `B10-测试数据构造` | `B10-06` |
| `B10-回归用例挑选` | `B10-07` |
| `B10-覆盖率提升策略` | `B10-08` |
| `B10-失败归因与复现` | `B10-09` |
| `B10-端到端场景编排` | `B10-10` |
| `B10-测试可维护性` | `B10-11` |
| `B10-CI-集成` | `B10-12` |
| `std-a2a` | `STD-a2a` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-nist-800-142` | `STD-nist-800-142` |
| `std-peps` | `STD-peps` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "测试与用例生成"
  code: "B10"
  provenance_strength: "external"
  provenance_legend:
    b10-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B10-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "测试与用例生成 全域"
      nodes:
        - "B10-01"
        - "B10-02"
        - "B10-03"
        - "B10-04"
        - "B10-05"
        - "B10-06"
        - "B10-07"
        - "B10-08"
        - "B10-09"
        - "B10-10"
        - "B10-11"
        - "B10-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-a2a"
        - "STD-ietf-json-schema"
        - "STD-nist-800-142"
        - "STD-peps"
  nodes:
    - id: "B10-01"
      name: "单元测试生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B10-02"
      provenance:
        - "b10-anchor"
    - id: "B10-02"
      name: "边界与等价类"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b10-anchor"
    - id: "B10-03"
      name: "模糊测试用例"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B10-02"
        - "B10-06"
      provenance:
        - "b10-anchor"
    - id: "B10-04"
      name: "接口与契约测试"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b10-anchor"
    - id: "B10-05"
      name: "UI 自动化脚本"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b10-anchor"
    - id: "B10-06"
      name: "测试数据构造"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b10-anchor"
    - id: "B10-07"
      name: "回归用例挑选"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B10-01"
      provenance:
        - "b10-anchor"
    - id: "B10-08"
      name: "覆盖率提升策略"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B10-01"
      provenance:
        - "b10-anchor"
    - id: "B10-09"
      name: "失败归因与复现"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B10-07"
      provenance:
        - "b10-anchor"
    - id: "B10-10"
      name: "端到端场景编排"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B10-04"
        - "B10-05"
      provenance:
        - "b10-anchor"
    - id: "B10-11"
      name: "测试可维护性"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B10-01"
      provenance:
        - "b10-anchor"
    - id: "B10-12"
      name: "CI 集成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B10-10"
      provenance:
        - "b10-anchor"
    - id: "STD-a2a"
      name: "标准 · A2A 协议"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B10-10"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B10-04"
      provenance:
        - "std-catalog"
    - id: "STD-nist-800-142"
      name: "标准 · SP 800-142 组合测试实践"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B10-01"
        - "B10-03"
        - "B10-05"
        - "B10-07"
        - "B10-09"
        - "B10-11"
      provenance:
        - "std-catalog"
    - id: "STD-peps"
      name: "标准 · PEP 体系（含 8/257/621）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B10-02"
        - "B10-06"
        - "B10-08"
        - "B10-12"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B10-00）不随包交付，装载方须自备领域基础。
