<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 参数高效微调（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「参数高效微调」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（参数高效微调:M01）与收口模块（参数高效微调:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（C06-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C06-01` | LoRA 与 QLoRA | P40 | — | c06-anchor |
| `C06-02` | 适配器与软提示 | P60 | `C06-01` | c06-anchor |
| `C06-03` | 秩与目标层选择 | P40 | `C06-02` | c06-anchor |
| `C06-04` | 合并与卸载 | P60 | `C06-03`、`C06-01` | c06-anchor |
| `C06-05` | 多适配器管理 | P40 | `C06-04`、`C06-02` | c06-anchor |
| `C06-06` | 显存与速度权衡 | P60 | `C06-05`、`C06-03` | c06-anchor |
| `C06-07` | 效果上限评估 | P40 | `C06-06`、`C06-04` | c06-anchor |
| `C06-08` | 适配器版本管理 | P60 | `C06-07`、`C06-05` | c06-anchor |
| `C06-09` | 微调数据复用 | P40 | `C06-08`、`C06-06` | c06-anchor |
| `C06-10` | 推理期切换 | P60 | `C06-09`、`C06-07` | c06-anchor |
| `C06-11` | 适配器安全 | P40 | `C06-10`、`C06-08` | c06-anchor |
| `C06-12` | PEFT 工具链 | P60 | `C06-11`、`C06-09` | c06-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry） | P80 | `C06-01`、`C06-04`、`C06-07` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `C06-02` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `C06-03`、`C06-06`、`C06-12` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `C06-05`、`C06-08`、`C06-09` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation） | P80 | `C06-10` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP） | P80 | `C06-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C06-LoRA-与-QLoRA` | `C06-01` |
| `C06-适配器与软提示` | `C06-02` |
| `C06-秩与目标层选择` | `C06-03` |
| `C06-合并与卸载` | `C06-04` |
| `C06-多适配器管理` | `C06-05` |
| `C06-显存与速度权衡` | `C06-06` |
| `C06-效果上限评估` | `C06-07` |
| `C06-适配器版本管理` | `C06-08` |
| `C06-微调数据复用` | `C06-09` |
| `C06-推理期切换` | `C06-10` |
| `C06-适配器安全` | `C06-11` |
| `C06-PEFT-工具链` | `C06-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-onnx` | `STD-onnx` |
| `std-owasp-llm` | `STD-owasp-llm` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "参数高效微调"
  code: "C06"
  provenance_strength: "external"
  provenance_legend:
    c06-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C06-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "参数高效微调 全域"
      nodes:
        - "C06-01"
        - "C06-02"
        - "C06-03"
        - "C06-04"
        - "C06-05"
        - "C06-06"
        - "C06-07"
        - "C06-08"
        - "C06-09"
        - "C06-10"
        - "C06-11"
        - "C06-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-frictionless-table"
        - "STD-mlcommons-bench"
        - "STD-onnx"
        - "STD-owasp-llm"
  nodes:
    - id: "C06-01"
      name: "LoRA 与 QLoRA"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c06-anchor"
    - id: "C06-02"
      name: "适配器与软提示"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C06-01"
      provenance:
        - "c06-anchor"
    - id: "C06-03"
      name: "秩与目标层选择"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C06-02"
      provenance:
        - "c06-anchor"
    - id: "C06-04"
      name: "合并与卸载"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C06-03"
        - "C06-01"
      provenance:
        - "c06-anchor"
    - id: "C06-05"
      name: "多适配器管理"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C06-04"
        - "C06-02"
      provenance:
        - "c06-anchor"
    - id: "C06-06"
      name: "显存与速度权衡"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C06-05"
        - "C06-03"
      provenance:
        - "c06-anchor"
    - id: "C06-07"
      name: "效果上限评估"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C06-06"
        - "C06-04"
      provenance:
        - "c06-anchor"
    - id: "C06-08"
      name: "适配器版本管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C06-07"
        - "C06-05"
      provenance:
        - "c06-anchor"
    - id: "C06-09"
      name: "微调数据复用"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C06-08"
        - "C06-06"
      provenance:
        - "c06-anchor"
    - id: "C06-10"
      name: "推理期切换"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C06-09"
        - "C06-07"
      provenance:
        - "c06-anchor"
    - id: "C06-11"
      name: "适配器安全"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C06-10"
        - "C06-08"
      provenance:
        - "c06-anchor"
    - id: "C06-12"
      name: "PEFT 工具链"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C06-11"
        - "C06-09"
      provenance:
        - "c06-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C06-01"
        - "C06-04"
        - "C06-07"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C06-02"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C06-03"
        - "C06-06"
        - "C06-12"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C06-05"
        - "C06-08"
        - "C06-09"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C06-10"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C06-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C06-00）不随包交付，装载方须自备领域基础。
