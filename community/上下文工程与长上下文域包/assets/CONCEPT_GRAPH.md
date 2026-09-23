<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 上下文工程与长上下文（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「上下文工程与长上下文」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（上下文工程与长上下文:M01）与收口模块（上下文工程与长上下文:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（C12-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C12-01` | 上下文分层与预算 | P40 | — | c12-anchor |
| `C12-02` | 压缩与摘要记忆 | P60 | `C12-01` | c12-anchor |
| `C12-03` | 检索式上下文 | P40 | `C12-02` | c12-anchor |
| `C12-04` | 结构化上下文格式 | P60 | `C12-03`、`C12-01` | c12-anchor |
| `C12-05` | 指令优先级 | P40 | `C12-04`、`C12-02` | c12-anchor |
| `C12-06` | 上下文污染与冲突 | P60 | `C12-05`、`C12-03` | c12-anchor |
| `C12-07` | 位置偏差利用 | P40 | `C12-06`、`C12-04` | c12-anchor |
| `C12-08` | 长文失忆 | P60 | `C12-07`、`C12-05` | c12-anchor |
| `C12-09` | 上下文档位测试 | P40 | `C12-08`、`C12-06` | c12-anchor |
| `C12-10` | 多文档拼接 | P60 | `C12-09`、`C12-07` | c12-anchor |
| `C12-11` | 会话状态持久化 | P40 | `C12-10`、`C12-08` | c12-anchor |
| `C12-12` | 上下文成本控制 | P60 | `C12-11`、`C12-09` | c12-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry） | P80 | `C12-07`、`C12-12` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `C12-05` | std-catalog |
| `STD-frictionless-package` | 标准 · Data Package（Frictionless） | P80 | `C12-03` | std-catalog |
| `STD-gfm` | 标准 · GFM 扩展（GitHub） | P80 | `C12-01`、`C12-04`、`C12-06` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `C12-02`、`C12-08`、`C12-11` | std-catalog |
| `STD-w3c-epub33` | 标准 · EPUB 3.3（W3C） | P80 | `C12-09`、`C12-10` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `C12-上下文分层与预算` | `C12-01` |
| `C12-压缩与摘要记忆` | `C12-02` |
| `C12-检索式上下文` | `C12-03` |
| `C12-结构化上下文格式` | `C12-04` |
| `C12-指令优先级` | `C12-05` |
| `C12-上下文污染与冲突` | `C12-06` |
| `C12-位置偏差利用` | `C12-07` |
| `C12-长文失忆` | `C12-08` |
| `C12-上下文档位测试` | `C12-09` |
| `C12-多文档拼接` | `C12-10` |
| `C12-会话状态持久化` | `C12-11` |
| `C12-上下文成本控制` | `C12-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-commonmark` | `STD-commonmark` |
| `std-frictionless-package` | `STD-frictionless-package` |
| `std-gfm` | `STD-gfm` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-w3c-epub33` | `STD-w3c-epub33` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "上下文工程与长上下文"
  code: "C12"
  provenance_strength: "external"
  provenance_legend:
    c12-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "C12-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "上下文工程与长上下文 全域"
      nodes:
        - "C12-01"
        - "C12-02"
        - "C12-03"
        - "C12-04"
        - "C12-05"
        - "C12-06"
        - "C12-07"
        - "C12-08"
        - "C12-09"
        - "C12-10"
        - "C12-11"
        - "C12-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-commonmark"
        - "STD-frictionless-package"
        - "STD-gfm"
        - "STD-mlcommons-bench"
        - "STD-w3c-epub33"
  nodes:
    - id: "C12-01"
      name: "上下文分层与预算"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "c12-anchor"
    - id: "C12-02"
      name: "压缩与摘要记忆"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C12-01"
      provenance:
        - "c12-anchor"
    - id: "C12-03"
      name: "检索式上下文"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C12-02"
      provenance:
        - "c12-anchor"
    - id: "C12-04"
      name: "结构化上下文格式"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C12-03"
        - "C12-01"
      provenance:
        - "c12-anchor"
    - id: "C12-05"
      name: "指令优先级"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C12-04"
        - "C12-02"
      provenance:
        - "c12-anchor"
    - id: "C12-06"
      name: "上下文污染与冲突"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C12-05"
        - "C12-03"
      provenance:
        - "c12-anchor"
    - id: "C12-07"
      name: "位置偏差利用"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C12-06"
        - "C12-04"
      provenance:
        - "c12-anchor"
    - id: "C12-08"
      name: "长文失忆"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C12-07"
        - "C12-05"
      provenance:
        - "c12-anchor"
    - id: "C12-09"
      name: "上下文档位测试"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C12-08"
        - "C12-06"
      provenance:
        - "c12-anchor"
    - id: "C12-10"
      name: "多文档拼接"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C12-09"
        - "C12-07"
      provenance:
        - "c12-anchor"
    - id: "C12-11"
      name: "会话状态持久化"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "C12-10"
        - "C12-08"
      provenance:
        - "c12-anchor"
    - id: "C12-12"
      name: "上下文成本控制"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "C12-11"
        - "C12-09"
      provenance:
        - "c12-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C12-07"
        - "C12-12"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C12-05"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-package"
      name: "标准 · Data Package"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C12-03"
      provenance:
        - "std-catalog"
    - id: "STD-gfm"
      name: "标准 · GFM 扩展"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C12-01"
        - "C12-04"
        - "C12-06"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C12-02"
        - "C12-08"
        - "C12-11"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-epub33"
      name: "标准 · EPUB 3.3"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "C12-09"
        - "C12-10"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（C12-00）不随包交付，装载方须自备领域基础。
