<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 安全与对齐（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「安全与对齐」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（安全与对齐:M01）与收口模块（安全与对齐:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（F01-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `F01-01` | 越狱与红队 | P40 | — | f01-anchor |
| `F01-02` | 提示注入防御 | P60 | `F01-01` | f01-anchor |
| `F01-03` | 有害内容拦截 | P40 | `F01-02` | f01-anchor |
| `F01-04` | 价值观对齐 | P60 | `F01-03`、`F01-01` | f01-anchor |
| `F01-05` | 拒答策略 | P40 | `F01-04`、`F01-02` | f01-anchor |
| `F01-06` | 多模态安全 | P60 | `F01-05`、`F01-03` | f01-anchor |
| `F01-07` | 水印与溯源 | P40 | `F01-06`、`F01-04` | f01-anchor |
| `F01-08` | 滥用监测 | P60 | `F01-07`、`F01-05` | f01-anchor |
| `F01-09` | 边界声明 | P40 | `F01-08`、`F01-06` | f01-anchor |
| `F01-10` | 安全评测 | P60 | `F01-09`、`F01-07` | f01-anchor |
| `F01-11` | 应急演练 | P40 | `F01-10`、`F01-08` | f01-anchor |
| `F01-12` | 安全运营 | P60 | `F01-11`、`F01-09` | f01-anchor |
| `STD-c2pa-spec` | 标准 · 内容凭证规范（C2PA） | P80 | `F01-07` | std-catalog |
| `STD-commonmark` | 标准 · CommonMark 0.31.2（CommonMark） | P80 | `F01-02` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `F01-04` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP） | P80 | `F01-01`、`F01-06`、`F01-10`、`F01-12` | std-catalog |
| `STD-spdx-licenses` | 标准 · SPDX 许可证清单（SPDX） | P80 | `F01-03`、`F01-09` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C） | P80 | `F01-05`、`F01-08`、`F01-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `F01-越狱与红队` | `F01-01` |
| `F01-提示注入防御` | `F01-02` |
| `F01-有害内容拦截` | `F01-03` |
| `F01-价值观对齐` | `F01-04` |
| `F01-拒答策略` | `F01-05` |
| `F01-多模态安全` | `F01-06` |
| `F01-水印与溯源` | `F01-07` |
| `F01-滥用监测` | `F01-08` |
| `F01-边界声明` | `F01-09` |
| `F01-安全评测` | `F01-10` |
| `F01-应急演练` | `F01-11` |
| `F01-安全运营` | `F01-12` |
| `std-c2pa-spec` | `STD-c2pa-spec` |
| `std-commonmark` | `STD-commonmark` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-spdx-licenses` | `STD-spdx-licenses` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "安全与对齐"
  code: "F01"
  provenance_strength: "external"
  provenance_legend:
    f01-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "F01-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "安全与对齐 全域"
      nodes:
        - "F01-01"
        - "F01-02"
        - "F01-03"
        - "F01-04"
        - "F01-05"
        - "F01-06"
        - "F01-07"
        - "F01-08"
        - "F01-09"
        - "F01-10"
        - "F01-11"
        - "F01-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-c2pa-spec"
        - "STD-commonmark"
        - "STD-mlcommons-bench"
        - "STD-owasp-llm"
        - "STD-spdx-licenses"
        - "STD-w3c-prov-o"
  nodes:
    - id: "F01-01"
      name: "越狱与红队"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "f01-anchor"
    - id: "F01-02"
      name: "提示注入防御"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F01-01"
      provenance:
        - "f01-anchor"
    - id: "F01-03"
      name: "有害内容拦截"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F01-02"
      provenance:
        - "f01-anchor"
    - id: "F01-04"
      name: "价值观对齐"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F01-03"
        - "F01-01"
      provenance:
        - "f01-anchor"
    - id: "F01-05"
      name: "拒答策略"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F01-04"
        - "F01-02"
      provenance:
        - "f01-anchor"
    - id: "F01-06"
      name: "多模态安全"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F01-05"
        - "F01-03"
      provenance:
        - "f01-anchor"
    - id: "F01-07"
      name: "水印与溯源"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F01-06"
        - "F01-04"
      provenance:
        - "f01-anchor"
    - id: "F01-08"
      name: "滥用监测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F01-07"
        - "F01-05"
      provenance:
        - "f01-anchor"
    - id: "F01-09"
      name: "边界声明"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F01-08"
        - "F01-06"
      provenance:
        - "f01-anchor"
    - id: "F01-10"
      name: "安全评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F01-09"
        - "F01-07"
      provenance:
        - "f01-anchor"
    - id: "F01-11"
      name: "应急演练"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F01-10"
        - "F01-08"
      provenance:
        - "f01-anchor"
    - id: "F01-12"
      name: "安全运营"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F01-11"
        - "F01-09"
      provenance:
        - "f01-anchor"
    - id: "STD-c2pa-spec"
      name: "标准 · 内容凭证规范"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F01-07"
      provenance:
        - "std-catalog"
    - id: "STD-commonmark"
      name: "标准 · CommonMark 0.31.2"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F01-02"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F01-04"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F01-01"
        - "F01-06"
        - "F01-10"
        - "F01-12"
      provenance:
        - "std-catalog"
    - id: "STD-spdx-licenses"
      name: "标准 · SPDX 许可证清单"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F01-03"
        - "F01-09"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F01-05"
        - "F01-08"
        - "F01-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（F01-00）不随包交付，装载方须自备领域基础。
