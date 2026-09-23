<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 平台与基础设施（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「平台与基础设施」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（平台与基础设施:M01）与收口模块（平台与基础设施:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 7 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（F08-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `F08-01` | 训练框架 | P40 | — | f08-anchor |
| `F08-02` | 分布式训练 | P60 | `F08-01` | f08-anchor |
| `F08-03` | 数据管道 | P40 | `F08-02` | f08-anchor |
| `F08-04` | 特征存储 | P60 | `F08-03`、`F08-01` | f08-anchor |
| `F08-05` | 推理服务 | P40 | `F08-04`、`F08-02` | f08-anchor |
| `F08-06` | 算力调度 | P60 | `F08-05`、`F08-03` | f08-anchor |
| `F08-07` | 模型仓库 | P40 | `F08-06`、`F08-04` | f08-anchor |
| `F08-08` | 版本与回滚 | P60 | `F08-07`、`F08-05` | f08-anchor |
| `F08-09` | 监控告警 | P40 | `F08-08`、`F08-06` | f08-anchor |
| `F08-10` | 私有化部署 | P60 | `F08-09`、`F08-07` | f08-anchor |
| `F08-11` | 边缘推理 | P40 | `F08-10`、`F08-08` | f08-anchor |
| `F08-12` | 混合云 | P60 | `F08-11`、`F08-09` | f08-anchor |
| `STD-cncf-otel-semconv` | 标准 · 语义约定（可扩展注册表）（OpenTelemetry） | P80 | `F08-09` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `F08-01`、`F08-02` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST） | P80 | `F08-04` | std-catalog |
| `STD-oasis-openapi` | 标准 · OpenAPI 3.1（OpenAPI Initiative） | P80 | `F08-05`、`F08-10` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation） | P80 | `F08-07`、`F08-11` | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX） | P80 | `F08-03`、`F08-06`、`F08-12` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C） | P80 | `F08-08` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `F08-训练框架` | `F08-01` |
| `F08-分布式训练` | `F08-02` |
| `F08-数据管道` | `F08-03` |
| `F08-特征存储` | `F08-04` |
| `F08-推理服务` | `F08-05` |
| `F08-算力调度` | `F08-06` |
| `F08-模型仓库` | `F08-07` |
| `F08-版本与回滚` | `F08-08` |
| `F08-监控告警` | `F08-09` |
| `F08-私有化部署` | `F08-10` |
| `F08-边缘推理` | `F08-11` |
| `F08-混合云` | `F08-12` |
| `std-cncf-otel-semconv` | `STD-cncf-otel-semconv` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-oasis-openapi` | `STD-oasis-openapi` |
| `std-onnx` | `STD-onnx` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "平台与基础设施"
  code: "F08"
  provenance_strength: "external"
  provenance_legend:
    f08-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "F08-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "平台与基础设施 全域"
      nodes:
        - "F08-01"
        - "F08-02"
        - "F08-03"
        - "F08-04"
        - "F08-05"
        - "F08-06"
        - "F08-07"
        - "F08-08"
        - "F08-09"
        - "F08-10"
        - "F08-11"
        - "F08-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-cncf-otel-semconv"
        - "STD-mlcommons-bench"
        - "STD-nist-ai-rmf"
        - "STD-oasis-openapi"
        - "STD-onnx"
        - "STD-spdx-licenses"
        - "STD-w3c-prov-o"
  nodes:
    - id: "F08-01"
      name: "训练框架"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "f08-anchor"
    - id: "F08-02"
      name: "分布式训练"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F08-01"
      provenance:
        - "f08-anchor"
    - id: "F08-03"
      name: "数据管道"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F08-02"
      provenance:
        - "f08-anchor"
    - id: "F08-04"
      name: "特征存储"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F08-03"
        - "F08-01"
      provenance:
        - "f08-anchor"
    - id: "F08-05"
      name: "推理服务"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F08-04"
        - "F08-02"
      provenance:
        - "f08-anchor"
    - id: "F08-06"
      name: "算力调度"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F08-05"
        - "F08-03"
      provenance:
        - "f08-anchor"
    - id: "F08-07"
      name: "模型仓库"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F08-06"
        - "F08-04"
      provenance:
        - "f08-anchor"
    - id: "F08-08"
      name: "版本与回滚"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F08-07"
        - "F08-05"
      provenance:
        - "f08-anchor"
    - id: "F08-09"
      name: "监控告警"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F08-08"
        - "F08-06"
      provenance:
        - "f08-anchor"
    - id: "F08-10"
      name: "私有化部署"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F08-09"
        - "F08-07"
      provenance:
        - "f08-anchor"
    - id: "F08-11"
      name: "边缘推理"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F08-10"
        - "F08-08"
      provenance:
        - "f08-anchor"
    - id: "F08-12"
      name: "混合云"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F08-11"
        - "F08-09"
      provenance:
        - "f08-anchor"
    - id: "STD-cncf-otel-semconv"
      name: "标准 · 语义约定（可扩展注册表）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F08-09"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F08-01"
        - "F08-02"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F08-04"
      provenance:
        - "std-catalog"
    - id: "STD-oasis-openapi"
      name: "标准 · OpenAPI 3.1"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F08-05"
        - "F08-10"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F08-07"
        - "F08-11"
      provenance:
        - "std-catalog"
    - id: "STD-spdx-licenses"
      name: "标准 · SPDX 许可证清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F08-03"
        - "F08-06"
        - "F08-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F08-08"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（F08-00）不随包交付，装载方须自备领域基础。
