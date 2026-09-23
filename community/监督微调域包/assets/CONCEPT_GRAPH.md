<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 监督微调（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「监督微调」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（监督微调:M01）与收口模块（监督微调:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（C05-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C05-01` | 指令数据集构造 | P40 | — | c05-anchor |
| `C05-02` | 多轮样本格式 | P60 | `C05-01` | c05-anchor |
| `C05-03` | 提示模板对齐 | P40 | `C05-02` | c05-anchor |
| `C05-04` | 过拟合控制 | P60 | `C05-03`、`C05-01` | c05-anchor |
| `C05-05` | 灾难性遗忘 | P40 | `C05-04`、`C05-02` | c05-anchor |
| `C05-06` | 领域 SFT | P60 | `C05-05`、`C05-03` | c05-anchor |
| `C05-07` | 风格 SFT | P40 | `C05-06`、`C05-04` | c05-anchor |
| `C05-08` | 样本配比 | P60 | `C05-07`、`C05-05` | c05-anchor |
| `C05-09` | 训练超参 | P40 | `C05-08`、`C05-06` | c05-anchor |
| `C05-10` | LoRA 与全参取舍 | P60 | `C05-09`、`C05-07` | c05-anchor |
| `C05-11` | 评测对比 | P40 | `C05-10`、`C05-08` | c05-anchor |
| `C05-12` | SFT 数据许可 | P60 | `C05-11`、`C05-09` | c05-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry） | P80 | `C05-04`、`C05-07`、`C05-10` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `C05-03` | std-catalog |
| `STD-creativecommons` | 标准 · 许可与权利表达（Creative Commons） | P80 | `C05-12` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `C05-06` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `C05-02`、`C05-05`、`C05-08`、`C05-09`、`C05-11` | std-catalog |
| `STD-mlcommons-croissant` | 标准 · Croissant 数据集元数据（MLCommons） | P80 | `C05-01` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C05-指令数据集构造` | `C05-01` |
| `C05-多轮样本格式` | `C05-02` |
| `C05-提示模板对齐` | `C05-03` |
| `C05-过拟合控制` | `C05-04` |
| `C05-灾难性遗忘` | `C05-05` |
| `C05-领域-SFT` | `C05-06` |
| `C05-风格-SFT` | `C05-07` |
| `C05-样本配比` | `C05-08` |
| `C05-训练超参` | `C05-09` |
| `C05-LoRA-与全参取舍` | `C05-10` |
| `C05-评测对比` | `C05-11` |
| `C05-SFT-数据许可` | `C05-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-creativecommons` | `STD-creativecommons` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-mlcommons-croissant` | `STD-mlcommons-croissant` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "监督微调"
  code: "C05"
  provenance_strength: "external"
  provenance_legend:
    c05-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C05-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "监督微调 全域"
      nodes:
        - "C05-01"
        - "C05-02"
        - "C05-03"
        - "C05-04"
        - "C05-05"
        - "C05-06"
        - "C05-07"
        - "C05-08"
        - "C05-09"
        - "C05-10"
        - "C05-11"
        - "C05-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-creativecommons"
        - "STD-frictionless-table"
        - "STD-mlcommons-bench"
        - "STD-mlcommons-croissant"
  nodes:
    - id: "C05-01"
      name: "指令数据集构造"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c05-anchor"
    - id: "C05-02"
      name: "多轮样本格式"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C05-01"
      provenance:
        - "c05-anchor"
    - id: "C05-03"
      name: "提示模板对齐"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C05-02"
      provenance:
        - "c05-anchor"
    - id: "C05-04"
      name: "过拟合控制"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C05-03"
        - "C05-01"
      provenance:
        - "c05-anchor"
    - id: "C05-05"
      name: "灾难性遗忘"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C05-04"
        - "C05-02"
      provenance:
        - "c05-anchor"
    - id: "C05-06"
      name: "领域 SFT"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C05-05"
        - "C05-03"
      provenance:
        - "c05-anchor"
    - id: "C05-07"
      name: "风格 SFT"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C05-06"
        - "C05-04"
      provenance:
        - "c05-anchor"
    - id: "C05-08"
      name: "样本配比"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C05-07"
        - "C05-05"
      provenance:
        - "c05-anchor"
    - id: "C05-09"
      name: "训练超参"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C05-08"
        - "C05-06"
      provenance:
        - "c05-anchor"
    - id: "C05-10"
      name: "LoRA 与全参取舍"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C05-09"
        - "C05-07"
      provenance:
        - "c05-anchor"
    - id: "C05-11"
      name: "评测对比"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C05-10"
        - "C05-08"
      provenance:
        - "c05-anchor"
    - id: "C05-12"
      name: "SFT 数据许可"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C05-11"
        - "C05-09"
      provenance:
        - "c05-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C05-04"
        - "C05-07"
        - "C05-10"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C05-03"
      provenance:
        - "std-catalog"
    - id: "STD-creativecommons"
      name: "标准 · 许可与权利表达"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C05-12"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C05-06"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C05-02"
        - "C05-05"
        - "C05-08"
        - "C05-09"
        - "C05-11"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-croissant"
      name: "标准 · Croissant 数据集元数据"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C05-01"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C05-00）不随包交付，装载方须自备领域基础。
