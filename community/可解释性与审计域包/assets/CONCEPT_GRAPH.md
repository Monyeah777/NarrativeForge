<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 可解释性与审计（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「可解释性与审计」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（可解释性与审计:M01）与收口模块（可解释性与审计:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 5 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（F06-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `F06-01` | 决策归因 | P40 | — | f06-anchor |
| `F06-02` | 推理过程披露 | P60 | `F06-01` | f06-anchor |
| `F06-03` | 模型卡与数据卡 | P40 | `F06-02` | f06-anchor |
| `F06-04` | 影响评估 | P60 | `F06-03`、`F06-01` | f06-anchor |
| `F06-05` | 第三方审计 | P40 | `F06-04`、`F06-02` | f06-anchor |
| `F06-06` | 日志证据链 | P60 | `F06-05`、`F06-03` | f06-anchor |
| `F06-07` | 偏差检测 | P40 | `F06-06`、`F06-04` | f06-anchor |
| `F06-08` | 公平性度量 | P60 | `F06-07`、`F06-05` | f06-anchor |
| `F06-09` | 风险分级 | P40 | `F06-08`、`F06-06` | f06-anchor |
| `F06-10` | 责任划分 | P60 | `F06-09`、`F06-07` | f06-anchor |
| `F06-11` | 监管沙盒 | P40 | `F06-10`、`F06-08` | f06-anchor |
| `F06-12` | 事故复盘 | P60 | `F06-11`、`F06-09` | f06-anchor |
| `STD-gdpr` | 标准 · GDPR（EU） | P80 | `F06-11` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST） | P80 | `F06-01`、`F06-04`、`F06-07`、`F06-09`、`F06-10` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation） | P80 | `F06-02`、`F06-03` | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX） | P80 | `F06-12` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C） | P80 | `F06-05`、`F06-06`、`F06-08` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `F06-决策归因` | `F06-01` |
| `F06-推理过程披露` | `F06-02` |
| `F06-模型卡与数据卡` | `F06-03` |
| `F06-影响评估` | `F06-04` |
| `F06-第三方审计` | `F06-05` |
| `F06-日志证据链` | `F06-06` |
| `F06-偏差检测` | `F06-07` |
| `F06-公平性度量` | `F06-08` |
| `F06-风险分级` | `F06-09` |
| `F06-责任划分` | `F06-10` |
| `F06-监管沙盒` | `F06-11` |
| `F06-事故复盘` | `F06-12` |
| `std-gdpr` | `STD-gdpr` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-onnx` | `STD-onnx` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "可解释性与审计"
  code: "F06"
  provenance_strength: "external"
  provenance_legend:
    f06-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "F06-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "可解释性与审计 全域"
      nodes:
        - "F06-01"
        - "F06-02"
        - "F06-03"
        - "F06-04"
        - "F06-05"
        - "F06-06"
        - "F06-07"
        - "F06-08"
        - "F06-09"
        - "F06-10"
        - "F06-11"
        - "F06-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-gdpr"
        - "STD-nist-ai-rmf"
        - "STD-onnx"
        - "STD-spdx-licenses"
        - "STD-w3c-prov-o"
  nodes:
    - id: "F06-01"
      name: "决策归因"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "f06-anchor"
    - id: "F06-02"
      name: "推理过程披露"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F06-01"
      provenance:
        - "f06-anchor"
    - id: "F06-03"
      name: "模型卡与数据卡"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F06-02"
      provenance:
        - "f06-anchor"
    - id: "F06-04"
      name: "影响评估"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F06-03"
        - "F06-01"
      provenance:
        - "f06-anchor"
    - id: "F06-05"
      name: "第三方审计"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F06-04"
        - "F06-02"
      provenance:
        - "f06-anchor"
    - id: "F06-06"
      name: "日志证据链"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F06-05"
        - "F06-03"
      provenance:
        - "f06-anchor"
    - id: "F06-07"
      name: "偏差检测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F06-06"
        - "F06-04"
      provenance:
        - "f06-anchor"
    - id: "F06-08"
      name: "公平性度量"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F06-07"
        - "F06-05"
      provenance:
        - "f06-anchor"
    - id: "F06-09"
      name: "风险分级"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F06-08"
        - "F06-06"
      provenance:
        - "f06-anchor"
    - id: "F06-10"
      name: "责任划分"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F06-09"
        - "F06-07"
      provenance:
        - "f06-anchor"
    - id: "F06-11"
      name: "监管沙盒"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F06-10"
        - "F06-08"
      provenance:
        - "f06-anchor"
    - id: "F06-12"
      name: "事故复盘"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F06-11"
        - "F06-09"
      provenance:
        - "f06-anchor"
    - id: "STD-gdpr"
      name: "标准 · GDPR"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F06-11"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F06-01"
        - "F06-04"
        - "F06-07"
        - "F06-09"
        - "F06-10"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F06-02"
        - "F06-03"
      provenance:
        - "std-catalog"
    - id: "STD-spdx-licenses"
      name: "标准 · SPDX 许可证清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F06-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F06-05"
        - "F06-06"
        - "F06-08"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（F06-00）不随包交付，装载方须自备领域基础。
