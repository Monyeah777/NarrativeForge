<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 语音合成与配音（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「语音合成与配音」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（语音合成与配音:M01）与收口模块（语音合成与配音:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 6 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（B14-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B14-01` | 多角色配音 | P40 | — | b14-anchor |
| `B14-02` | 情感与语调 | P60 | `B14-01` | b14-anchor |
| `B14-03` | 语速与停顿控制 | P40 | `B14-02` | b14-anchor |
| `B14-04` | 有声书制作 | P60 | `B14-03`、`B14-01` | b14-anchor |
| `B14-05` | 播客与广告配音 | P40 | `B14-04`、`B14-02` | b14-anchor |
| `B14-06` | 多语言配音 | P60 | `B14-05`、`B14-03` | b14-anchor |
| `B14-07` | 音色一致性 | P40 | `B14-06`、`B14-04` | b14-anchor |
| `B14-08` | 授权声音与版权 | P60 | `B14-07`、`B14-05` | b14-anchor |
| `B14-09` | 配音与口型对齐 | P40 | `B14-08`、`B14-06` | b14-anchor |
| `B14-10` | 发音词典与专名 | P60 | `B14-09`、`B14-07` | b14-anchor |
| `B14-11` | 实时语音对话 | P40 | `B14-10`、`B14-08` | b14-anchor |
| `B14-12` | 合成质量评测 | P60 | `B14-11`、`B14-09` | b14-anchor |
| `STD-creativecommons` | 标准 · 许可与权利表达（Creative Commons） | P80 | `B14-08` | std-catalog |
| `STD-frictionless-table` | 标准 · Table Schema（Frictionless） | P80 | `B14-03`、`B14-06` | std-catalog |
| `STD-ietf-json-schema` | 标准 · JSON Schema 2020-12（IETF/JSON Schema） | P80 | `B14-01`、`B14-04`、`B14-07`、`B14-10` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `B14-09`、`B14-12` | std-catalog |
| `STD-w3c-tabular-data` | 标准 · Tabular Data Model (CSVW)（W3C） | P80 | `B14-02`、`B14-05` | std-catalog |
| `STD-w3c-webaudio` | 标准 · Web Audio API（W3C） | P80 | `B14-11` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B14-多角色配音` | `B14-01` |
| `B14-情感与语调` | `B14-02` |
| `B14-语速与停顿控制` | `B14-03` |
| `B14-有声书制作` | `B14-04` |
| `B14-播客与广告配音` | `B14-05` |
| `B14-多语言配音` | `B14-06` |
| `B14-音色一致性` | `B14-07` |
| `B14-授权声音与版权` | `B14-08` |
| `B14-配音与口型对齐` | `B14-09` |
| `B14-发音词典与专名` | `B14-10` |
| `B14-实时语音对话` | `B14-11` |
| `B14-合成质量评测` | `B14-12` |
| `std-creativecommons` | `STD-creativecommons` |
| `std-frictionless-table` | `STD-frictionless-table` |
| `std-ietf-json-schema` | `STD-ietf-json-schema` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-w3c-tabular-data` | `STD-w3c-tabular-data` |
| `std-w3c-webaudio` | `STD-w3c-webaudio` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "语音合成与配音"
  code: "B14"
  provenance_strength: "external"
  provenance_legend:
    b14-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "B14-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "语音合成与配音 全域"
      nodes:
        - "B14-01"
        - "B14-02"
        - "B14-03"
        - "B14-04"
        - "B14-05"
        - "B14-06"
        - "B14-07"
        - "B14-08"
        - "B14-09"
        - "B14-10"
        - "B14-11"
        - "B14-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-creativecommons"
        - "STD-frictionless-table"
        - "STD-ietf-json-schema"
        - "STD-mlcommons-bench"
        - "STD-w3c-tabular-data"
        - "STD-w3c-webaudio"
  nodes:
    - id: "B14-01"
      name: "多角色配音"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b14-anchor"
    - id: "B14-02"
      name: "情感与语调"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B14-01"
      provenance:
        - "b14-anchor"
    - id: "B14-03"
      name: "语速与停顿控制"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B14-02"
      provenance:
        - "b14-anchor"
    - id: "B14-04"
      name: "有声书制作"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B14-03"
        - "B14-01"
      provenance:
        - "b14-anchor"
    - id: "B14-05"
      name: "播客与广告配音"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B14-04"
        - "B14-02"
      provenance:
        - "b14-anchor"
    - id: "B14-06"
      name: "多语言配音"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B14-05"
        - "B14-03"
      provenance:
        - "b14-anchor"
    - id: "B14-07"
      name: "音色一致性"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B14-06"
        - "B14-04"
      provenance:
        - "b14-anchor"
    - id: "B14-08"
      name: "授权声音与版权"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B14-07"
        - "B14-05"
      provenance:
        - "b14-anchor"
    - id: "B14-09"
      name: "配音与口型对齐"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B14-08"
        - "B14-06"
      provenance:
        - "b14-anchor"
    - id: "B14-10"
      name: "发音词典与专名"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B14-09"
        - "B14-07"
      provenance:
        - "b14-anchor"
    - id: "B14-11"
      name: "实时语音对话"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B14-10"
        - "B14-08"
      provenance:
        - "b14-anchor"
    - id: "B14-12"
      name: "合成质量评测"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B14-11"
        - "B14-09"
      provenance:
        - "b14-anchor"
    - id: "STD-creativecommons"
      name: "标准 · 许可与权利表达"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B14-08"
      provenance:
        - "std-catalog"
    - id: "STD-frictionless-table"
      name: "标准 · Table Schema"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B14-03"
        - "B14-06"
      provenance:
        - "std-catalog"
    - id: "STD-ietf-json-schema"
      name: "标准 · JSON Schema 2020-12"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B14-01"
        - "B14-04"
        - "B14-07"
        - "B14-10"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B14-09"
        - "B14-12"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-tabular-data"
      name: "标准 · Tabular Data Model (CSVW)"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B14-02"
        - "B14-05"
      provenance:
        - "std-catalog"
    - id: "STD-w3c-webaudio"
      name: "标准 · Web Audio API"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "B14-11"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B14-00）不随包交付，装载方须自备领域基础。
