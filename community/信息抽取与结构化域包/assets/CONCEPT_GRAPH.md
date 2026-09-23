<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 信息抽取与结构化（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「信息抽取与结构化」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（信息抽取与结构化:M01）与收口模块（信息抽取与结构化:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（B05-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B05-01` | 命名实体识别 | P40 | — | b05-anchor |
| `B05-02` | 关系抽取 | P60 | `B05-01` | b05-anchor |
| `B05-03` | 事件抽取 | P40 | `B05-02` | b05-anchor |
| `B05-04` | 属性值抽取 | P60 | `B05-01` | b05-anchor |
| `B05-05` | 表格转结构化 | P40 | `B05-04` | b05-anchor |
| `B05-06` | 合同与条款抽取 | P60 | `B05-04` | b05-anchor |
| `B05-07` | 简历解析 | P40 | `B05-05` | b05-anchor |
| `B05-08` | 发票与票据识别 | P60 | `B05-05` | b05-anchor |
| `B05-09` | 知识图谱构建 | P40 | `B05-02` | b05-anchor |
| `B05-10` | Schema 定义与校验 | P60 | — | b05-anchor |
| `B05-11` | 结果对齐与去重 | P40 | `B05-10` | b05-anchor |
| `B05-12` | 抽取质量评测 | P60 | `B05-11` | b05-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B05-命名实体识别` | `B05-01` |
| `B05-关系抽取` | `B05-02` |
| `B05-事件抽取` | `B05-03` |
| `B05-属性值抽取` | `B05-04` |
| `B05-表格转结构化` | `B05-05` |
| `B05-合同与条款抽取` | `B05-06` |
| `B05-简历解析` | `B05-07` |
| `B05-发票与票据识别` | `B05-08` |
| `B05-知识图谱构建` | `B05-09` |
| `B05-Schema-定义与校验` | `B05-10` |
| `B05-结果对齐与去重` | `B05-11` |
| `B05-抽取质量评测` | `B05-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "信息抽取与结构化"
  code: "B05"
  provenance_strength: "external"
  provenance_legend:
    b05-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "B05-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "信息抽取与结构化 全域"
      nodes:
        - "B05-01"
        - "B05-02"
        - "B05-03"
        - "B05-04"
        - "B05-05"
        - "B05-06"
        - "B05-07"
        - "B05-08"
        - "B05-09"
        - "B05-10"
        - "B05-11"
        - "B05-12"
  nodes:
    - id: "B05-01"
      name: "命名实体识别"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b05-anchor"
    - id: "B05-02"
      name: "关系抽取"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B05-01"
      provenance:
        - "b05-anchor"
    - id: "B05-03"
      name: "事件抽取"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B05-02"
      provenance:
        - "b05-anchor"
    - id: "B05-04"
      name: "属性值抽取"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B05-01"
      provenance:
        - "b05-anchor"
    - id: "B05-05"
      name: "表格转结构化"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B05-04"
      provenance:
        - "b05-anchor"
    - id: "B05-06"
      name: "合同与条款抽取"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B05-04"
      provenance:
        - "b05-anchor"
    - id: "B05-07"
      name: "简历解析"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B05-05"
      provenance:
        - "b05-anchor"
    - id: "B05-08"
      name: "发票与票据识别"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B05-05"
      provenance:
        - "b05-anchor"
    - id: "B05-09"
      name: "知识图谱构建"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B05-02"
      provenance:
        - "b05-anchor"
    - id: "B05-10"
      name: "Schema 定义与校验"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b05-anchor"
    - id: "B05-11"
      name: "结果对齐与去重"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B05-10"
      provenance:
        - "b05-anchor"
    - id: "B05-12"
      name: "抽取质量评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B05-11"
      provenance:
        - "b05-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B05-00）不随包交付，装载方须自备领域基础。
