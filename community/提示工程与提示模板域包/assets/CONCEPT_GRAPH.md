<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 提示工程与提示模板（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「提示工程与提示模板」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（提示工程与提示模板:M01）与收口模块（提示工程与提示模板:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 4 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（C13-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C13-01` | 指令清晰度与约束 | P40 | — | c13-anchor |
| `C13-02` | 少样本示例选择 | P60 | `C13-01` | c13-anchor |
| `C13-03` | 思维链与分解 | P40 | `C13-02` | c13-anchor |
| `C13-04` | 结构化输出约束 | P60 | `C13-03`、`C13-01` | c13-anchor |
| `C13-05` | 角色与语气设定 | P40 | `C13-04`、`C13-02` | c13-anchor |
| `C13-06` | 模板版本管理 | P60 | `C13-05`、`C13-03` | c13-anchor |
| `C13-07` | 提示回归测试 | P40 | `C13-06`、`C13-04` | c13-anchor |
| `C13-08` | 自动提示优化 | P60 | `C13-07`、`C13-05` | c13-anchor |
| `C13-09` | 提示注入防护 | P40 | `C13-08`、`C13-06` | c13-anchor |
| `C13-10` | 多语言提示 | P60 | `C13-09`、`C13-07` | c13-anchor |
| `C13-11` | 提示库组织 | P40 | `C13-10`、`C13-08` | c13-anchor |
| `C13-12` | 提示效果度量 | P60 | `C13-11`、`C13-09` | c13-anchor |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `C13-06`、`C13-07`、`C13-08`、`C13-09`、`C13-10`、`C13-11`、`C13-12` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `C13-03` | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema） | P80 | `C13-01`、`C13-04` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `C13-02`、`C13-05` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C13-指令清晰度与约束` | `C13-01` |
| `C13-少样本示例选择` | `C13-02` |
| `C13-思维链与分解` | `C13-03` |
| `C13-结构化输出约束` | `C13-04` |
| `C13-角色与语气设定` | `C13-05` |
| `C13-模板版本管理` | `C13-06` |
| `C13-提示回归测试` | `C13-07` |
| `C13-自动提示优化` | `C13-08` |
| `C13-提示注入防护` | `C13-09` |
| `C13-多语言提示` | `C13-10` |
| `C13-提示库组织` | `C13-11` |
| `C13-提示效果度量` | `C13-12` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "提示工程与提示模板"
  code: "C13"
  provenance_strength: "external"
  provenance_legend:
    c13-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C13-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "提示工程与提示模板 全域"
      nodes:
        - "C13-01"
        - "C13-02"
        - "C13-03"
        - "C13-04"
        - "C13-05"
        - "C13-06"
        - "C13-07"
        - "C13-08"
        - "C13-09"
        - "C13-10"
        - "C13-11"
        - "C13-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-commonmark"
        - "STD-frictionless-table"
        - "STD-ietf-json-schema"
        - "STD-mlcommons-bench"
  nodes:
    - id: "C13-01"
      name: "指令清晰度与约束"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c13-anchor"
    - id: "C13-02"
      name: "少样本示例选择"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C13-01"
      provenance:
        - "c13-anchor"
    - id: "C13-03"
      name: "思维链与分解"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C13-02"
      provenance:
        - "c13-anchor"
    - id: "C13-04"
      name: "结构化输出约束"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C13-03"
        - "C13-01"
      provenance:
        - "c13-anchor"
    - id: "C13-05"
      name: "角色与语气设定"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C13-04"
        - "C13-02"
      provenance:
        - "c13-anchor"
    - id: "C13-06"
      name: "模板版本管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C13-05"
        - "C13-03"
      provenance:
        - "c13-anchor"
    - id: "C13-07"
      name: "提示回归测试"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C13-06"
        - "C13-04"
      provenance:
        - "c13-anchor"
    - id: "C13-08"
      name: "自动提示优化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C13-07"
        - "C13-05"
      provenance:
        - "c13-anchor"
    - id: "C13-09"
      name: "提示注入防护"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C13-08"
        - "C13-06"
      provenance:
        - "c13-anchor"
    - id: "C13-10"
      name: "多语言提示"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C13-09"
        - "C13-07"
      provenance:
        - "c13-anchor"
    - id: "C13-11"
      name: "提示库组织"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C13-10"
        - "C13-08"
      provenance:
        - "c13-anchor"
    - id: "C13-12"
      name: "提示效果度量"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C13-11"
        - "C13-09"
      provenance:
        - "c13-anchor"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C13-06"
        - "C13-07"
        - "C13-08"
        - "C13-09"
        - "C13-10"
        - "C13-11"
        - "C13-12"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C13-03"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C13-01"
        - "C13-04"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C13-02"
        - "C13-05"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C13-00）不随包交付，装载方须自备领域基础。
