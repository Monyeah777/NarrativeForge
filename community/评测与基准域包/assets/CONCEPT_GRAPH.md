<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 评测与基准（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「评测与基准」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（评测与基准:M01）与收口模块（评测与基准:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（F05-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `F05-01` | 能力基准 | P40 | — | f05-anchor |
| `F05-02` | 垂直领域基准 | P60 | `F05-01` | f05-anchor |
| `F05-03` | 主观质量评分 | P40 | `F05-02` | f05-anchor |
| `F05-04` | 人机对比 | P60 | `F05-03`、`F05-01` | f05-anchor |
| `F05-05` | 鲁棒性测试 | P40 | `F05-04`、`F05-02` | f05-anchor |
| `F05-06` | 长文本评测 | P60 | `F05-05`、`F05-03` | f05-anchor |
| `F05-07` | 多模态评测 | P40 | `F05-06`、`F05-04` | f05-anchor |
| `F05-08` | 安全评测 | P60 | `F05-07`、`F05-05` | f05-anchor |
| `F05-09` | 评测集构建 | P40 | `F05-08`、`F05-06` | f05-anchor |
| `F05-10` | 评测报告规范 | P60 | `F05-09`、`F05-07` | f05-anchor |
| `F05-11` | 回归门禁 | P40 | `F05-10`、`F05-08` | f05-anchor |
| `F05-12` | 榜单治理 | P60 | `F05-11`、`F05-09` | f05-anchor |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `F05-03` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `F05-01`、`F05-02`、`F05-06`、`F05-07`、`F05-09`、`F05-10` | std-catalog |
| `STD-nist-800-188` | 标准 · SP 800-188 去标识化（NIST） | P80 | `F05-12` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST） | P80 | `F05-04` | std-catalog |
| `STD-owasp-llm` | 标准 · LLM 应用十大风险（OWASP） | P80 | `F05-08` | std-catalog |
| `STD-w3c-prov-o` | 标准 · PROV-O 溯源本体（W3C） | P80 | `F05-05`、`F05-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `F05-能力基准` | `F05-01` |
| `F05-垂直领域基准` | `F05-02` |
| `F05-主观质量评分` | `F05-03` |
| `F05-人机对比` | `F05-04` |
| `F05-鲁棒性测试` | `F05-05` |
| `F05-长文本评测` | `F05-06` |
| `F05-多模态评测` | `F05-07` |
| `F05-安全评测` | `F05-08` |
| `F05-评测集构建` | `F05-09` |
| `F05-评测报告规范` | `F05-10` |
| `F05-回归门禁` | `F05-11` |
| `F05-榜单治理` | `F05-12` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-nist-800-188` | `STD-nist-800-188` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-owasp-llm` | `STD-owasp-llm` |
| `std-w3c-prov-o` | `STD-w3c-prov-o` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "评测与基准"
  code: "F05"
  provenance_strength: "external"
  provenance_legend:
    f05-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "F05-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "评测与基准 全域"
      nodes:
        - "F05-01"
        - "F05-02"
        - "F05-03"
        - "F05-04"
        - "F05-05"
        - "F05-06"
        - "F05-07"
        - "F05-08"
        - "F05-09"
        - "F05-10"
        - "F05-11"
        - "F05-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-frictionless-table"
        - "STD-mlcommons-bench"
        - "STD-nist-800-188"
        - "STD-nist-ai-rmf"
        - "STD-owasp-llm"
        - "STD-w3c-prov-o"
  nodes:
    - id: "F05-01"
      name: "能力基准"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "f05-anchor"
    - id: "F05-02"
      name: "垂直领域基准"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F05-01"
      provenance:
        - "f05-anchor"
    - id: "F05-03"
      name: "主观质量评分"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F05-02"
      provenance:
        - "f05-anchor"
    - id: "F05-04"
      name: "人机对比"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F05-03"
        - "F05-01"
      provenance:
        - "f05-anchor"
    - id: "F05-05"
      name: "鲁棒性测试"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F05-04"
        - "F05-02"
      provenance:
        - "f05-anchor"
    - id: "F05-06"
      name: "长文本评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F05-05"
        - "F05-03"
      provenance:
        - "f05-anchor"
    - id: "F05-07"
      name: "多模态评测"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F05-06"
        - "F05-04"
      provenance:
        - "f05-anchor"
    - id: "F05-08"
      name: "安全评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F05-07"
        - "F05-05"
      provenance:
        - "f05-anchor"
    - id: "F05-09"
      name: "评测集构建"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F05-08"
        - "F05-06"
      provenance:
        - "f05-anchor"
    - id: "F05-10"
      name: "评测报告规范"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F05-09"
        - "F05-07"
      provenance:
        - "f05-anchor"
    - id: "F05-11"
      name: "回归门禁"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F05-10"
        - "F05-08"
      provenance:
        - "f05-anchor"
    - id: "F05-12"
      name: "榜单治理"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F05-11"
        - "F05-09"
      provenance:
        - "f05-anchor"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F05-03"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F05-01"
        - "F05-02"
        - "F05-06"
        - "F05-07"
        - "F05-09"
        - "F05-10"
      provenance:
        - "std-catalog"
    - id: "STD-nist-800-188"
      name: "标准 · SP 800-188 去标识化"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F05-12"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F05-04"
      provenance:
        - "std-catalog"
    - id: "STD-owasp-llm"
      name: "标准 · LLM 应用十大风险"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F05-08"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-prov-o"
      name: "标准 · PROV-O 溯源本体"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "F05-05"
        - "F05-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（F05-00）不随包交付，装载方须自备领域基础。
