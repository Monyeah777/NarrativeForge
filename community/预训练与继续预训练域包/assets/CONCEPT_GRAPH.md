<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 预训练与继续预训练（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「预训练与继续预训练」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（预训练与继续预训练:M01）与收口模块（预训练与继续预训练:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 4 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（C04-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C04-01` | 数据配比与课程学习 | P40 | — | c04-anchor |
| `C04-02` | 训练框架与并行 | P60 | `C04-01` | c04-anchor |
| `C04-03` | 显存与吞吐优化 | P40 | `C04-02` | c04-anchor |
| `C04-04` | 学习率与稳定性 | P60 | `C04-03`、`C04-01` | c04-anchor |
| `C04-05` | 数据去污染 | P40 | `C04-04`、`C04-02` | c04-anchor |
| `C04-06` | 领域继续预训练 | P60 | `C04-05`、`C04-03` | c04-anchor |
| `C04-07` | 词表扩展 | P40 | `C04-06`、`C04-04` | c04-anchor |
| `C04-08` | 训练日志与断点 | P60 | `C04-07`、`C04-05` | c04-anchor |
| `C04-09` | 成本估算 | P40 | `C04-08`、`C04-06` | c04-anchor |
| `C04-10` | 检查点管理 | P60 | `C04-09`、`C04-07` | c04-anchor |
| `C04-11` | 评测回归 | P40 | `C04-10`、`C04-08` | c04-anchor |
| `C04-12` | 训练事故复盘 | P60 | `C04-11`、`C04-09` | c04-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry） | P80 | `C04-01`、`C04-04`、`C04-08`、`C04-09`、`C04-10` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `C04-03` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `C04-02`、`C04-05`、`C04-06`、`C04-11`、`C04-12` | std-catalog |
| `STD-w3c-skos` | 标准 · SKOS 词表（W3C） | P80 | `C04-07` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C04-数据配比与课程学习` | `C04-01` |
| `C04-训练框架与并行` | `C04-02` |
| `C04-显存与吞吐优化` | `C04-03` |
| `C04-学习率与稳定性` | `C04-04` |
| `C04-数据去污染` | `C04-05` |
| `C04-领域继续预训练` | `C04-06` |
| `C04-词表扩展` | `C04-07` |
| `C04-训练日志与断点` | `C04-08` |
| `C04-成本估算` | `C04-09` |
| `C04-检查点管理` | `C04-10` |
| `C04-评测回归` | `C04-11` |
| `C04-训练事故复盘` | `C04-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-w3c-skos` | `STD-w3c-skos` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "预训练与继续预训练"
  code: "C04"
  provenance_strength: "external"
  provenance_legend:
    c04-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C04-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "预训练与继续预训练 全域"
      nodes:
        - "C04-01"
        - "C04-02"
        - "C04-03"
        - "C04-04"
        - "C04-05"
        - "C04-06"
        - "C04-07"
        - "C04-08"
        - "C04-09"
        - "C04-10"
        - "C04-11"
        - "C04-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-frictionless-table"
        - "STD-mlcommons-bench"
        - "STD-w3c-skos"
  nodes:
    - id: "C04-01"
      name: "数据配比与课程学习"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c04-anchor"
    - id: "C04-02"
      name: "训练框架与并行"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C04-01"
      provenance:
        - "c04-anchor"
    - id: "C04-03"
      name: "显存与吞吐优化"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C04-02"
      provenance:
        - "c04-anchor"
    - id: "C04-04"
      name: "学习率与稳定性"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C04-03"
        - "C04-01"
      provenance:
        - "c04-anchor"
    - id: "C04-05"
      name: "数据去污染"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C04-04"
        - "C04-02"
      provenance:
        - "c04-anchor"
    - id: "C04-06"
      name: "领域继续预训练"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C04-05"
        - "C04-03"
      provenance:
        - "c04-anchor"
    - id: "C04-07"
      name: "词表扩展"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C04-06"
        - "C04-04"
      provenance:
        - "c04-anchor"
    - id: "C04-08"
      name: "训练日志与断点"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C04-07"
        - "C04-05"
      provenance:
        - "c04-anchor"
    - id: "C04-09"
      name: "成本估算"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C04-08"
        - "C04-06"
      provenance:
        - "c04-anchor"
    - id: "C04-10"
      name: "检查点管理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C04-09"
        - "C04-07"
      provenance:
        - "c04-anchor"
    - id: "C04-11"
      name: "评测回归"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C04-10"
        - "C04-08"
      provenance:
        - "c04-anchor"
    - id: "C04-12"
      name: "训练事故复盘"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C04-11"
        - "C04-09"
      provenance:
        - "c04-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C04-01"
        - "C04-04"
        - "C04-08"
        - "C04-09"
        - "C04-10"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C04-03"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C04-02"
        - "C04-05"
        - "C04-06"
        - "C04-11"
        - "C04-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-skos"
      name: "标准 · SKOS 词表"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C04-07"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C04-00）不随包交付，装载方须自备领域基础。
