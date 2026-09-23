<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 数学与形式化推理（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「数学与形式化推理」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（数学与形式化推理:M01）与收口模块（数学与形式化推理:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（A10-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A10-01` | 思维链与推理链 | P40 | — | a10-anchor |
| `A10-02` | 形式化定理证明 | P60 | — | a10-anchor |
| `A10-03` | 定理证明搜索 | P40 | `A10-02` | a10-anchor |
| `A10-04` | 符号计算与 CAS | P60 | — | a10-anchor |
| `A10-05` | 数学应用题求解 | P40 | — | a10-anchor |
| `A10-06` | 竞赛数学基准 | P60 | `A10-05`、`A10-09` | a10-anchor |
| `A10-07` | 过程奖励模型 | P40 | `A10-01` | a10-anchor |
| `A10-08` | 自洽性与结果验证 | P60 | `A10-01` | a10-anchor |
| `A10-09` | 图论与组合推理 | P40 | — | a10-anchor |
| `A10-10` | 数值与误差分析 | P60 | `A10-04` | a10-anchor |
| `A10-11` | 推理幻觉识别 | P40 | `A10-06`、`A10-08` | a10-anchor |
| `A10-12` | 推理成本优化 | P60 | `A10-10`、`A10-07` | a10-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry） | P80 | `A10-12` | std-catalog |
| `STD-ieee-754` | 标准 · 浮点运算标准（IEEE） | P80 | `A10-10` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `A10-06` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation） | P80 | `A10-01`、`A10-07`、`A10-09`、`A10-11` | std-catalog |
| `STD-peps` | 标准 · PEP 体系（含 8/257/621）（Python） | P80 | `A10-08` | std-catalog |
| `STD-w3c-mathml3` | 标准 · MathML 3（W3C） | P80 | `A10-02`、`A10-03`、`A10-04`、`A10-05` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A10-思维链与推理链` | `A10-01` |
| `A10-形式化定理证明` | `A10-02` |
| `A10-定理证明搜索` | `A10-03` |
| `A10-符号计算与-CAS` | `A10-04` |
| `A10-数学应用题求解` | `A10-05` |
| `A10-竞赛数学基准` | `A10-06` |
| `A10-过程奖励模型` | `A10-07` |
| `A10-自洽性与结果验证` | `A10-08` |
| `A10-图论与组合推理` | `A10-09` |
| `A10-数值与误差分析` | `A10-10` |
| `A10-推理幻觉识别` | `A10-11` |
| `A10-推理成本优化` | `A10-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-ieee-754` | `STD-ieee-754` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-peps` | `STD-peps` |
| `std-w3c-mathml3` | `STD-w3c-mathml3` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "数学与形式化推理"
  code: "A10"
  provenance_strength: "external"
  provenance_legend:
    a10-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A10-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "数学与形式化推理 全域"
      nodes:
        - "A10-01"
        - "A10-02"
        - "A10-03"
        - "A10-04"
        - "A10-05"
        - "A10-06"
        - "A10-07"
        - "A10-08"
        - "A10-09"
        - "A10-10"
        - "A10-11"
        - "A10-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-ieee-754"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-peps"
        - "STD-w3c-mathml3"
  nodes:
    - id: "A10-01"
      name: "思维链与推理链"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a10-anchor"
    - id: "A10-02"
      name: "形式化定理证明"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a10-anchor"
    - id: "A10-03"
      name: "定理证明搜索"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A10-02"
      provenance:
        - "a10-anchor"
    - id: "A10-04"
      name: "符号计算与 CAS"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a10-anchor"
    - id: "A10-05"
      name: "数学应用题求解"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a10-anchor"
    - id: "A10-06"
      name: "竞赛数学基准"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A10-05"
        - "A10-09"
      provenance:
        - "a10-anchor"
    - id: "A10-07"
      name: "过程奖励模型"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A10-01"
      provenance:
        - "a10-anchor"
    - id: "A10-08"
      name: "自洽性与结果验证"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A10-01"
      provenance:
        - "a10-anchor"
    - id: "A10-09"
      name: "图论与组合推理"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a10-anchor"
    - id: "A10-10"
      name: "数值与误差分析"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A10-04"
      provenance:
        - "a10-anchor"
    - id: "A10-11"
      name: "推理幻觉识别"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A10-06"
        - "A10-08"
      provenance:
        - "a10-anchor"
    - id: "A10-12"
      name: "推理成本优化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A10-10"
        - "A10-07"
      provenance:
        - "a10-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-12"
      provenance:
        - "std-catalog"
    - id: "STD-ieee-754"
      name: "标准 · 浮点运算标准"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-10"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-06"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-01"
        - "A10-07"
        - "A10-09"
        - "A10-11"
      provenance:
        - "std-catalog"
    - id: "STD-peps"
      name: "标准 · PEP 体系（含 8/257/621）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-08"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-mathml3"
      name: "标准 · MathML 3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A10-02"
        - "A10-03"
        - "A10-04"
        - "A10-05"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A10-00）不随包交付，装载方须自备领域基础。
