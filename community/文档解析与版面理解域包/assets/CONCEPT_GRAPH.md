<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 文档解析与版面理解（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「文档解析与版面理解」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（文档解析与版面理解:M01）与收口模块（文档解析与版面理解:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（B12-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `B12-01` | OCR 文本识别 | P40 | — | b12-anchor |
| `B12-02` | 版面与阅读顺序 | P60 | `B12-01` | b12-anchor |
| `B12-03` | 表格结构还原 | P40 | `B12-02` | b12-anchor |
| `B12-04` | 公式识别 | P60 | — | b12-anchor |
| `B12-05` | 手写体识别 | P40 | `B12-04` | b12-anchor |
| `B12-06` | 票据与表单 | P60 | `B12-03` | b12-anchor |
| `B12-07` | PDF 与扫描件处理 | P40 | `B12-06` | b12-anchor |
| `B12-08` | 多栏与图注关联 | P60 | `B12-02` | b12-anchor |
| `B12-09` | 文档分类与归档 | P40 | `B12-02` | b12-anchor |
| `B12-10` | 关键信息定位 | P60 | `B12-09` | b12-anchor |
| `B12-11` | 解析置信度与复核 | P40 | `B12-07` | b12-anchor |
| `B12-12` | 多语言文档 | P60 | `B12-11` | b12-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `B12-OCR-文本识别` | `B12-01` |
| `B12-版面与阅读顺序` | `B12-02` |
| `B12-表格结构还原` | `B12-03` |
| `B12-公式识别` | `B12-04` |
| `B12-手写体识别` | `B12-05` |
| `B12-票据与表单` | `B12-06` |
| `B12-PDF-与扫描件处理` | `B12-07` |
| `B12-多栏与图注关联` | `B12-08` |
| `B12-文档分类与归档` | `B12-09` |
| `B12-关键信息定位` | `B12-10` |
| `B12-解析置信度与复核` | `B12-11` |
| `B12-多语言文档` | `B12-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "文档解析与版面理解"
  code: "B12"
  provenance_strength: "external"
  provenance_legend:
    b12-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "B12-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "文档解析与版面理解 全域"
      nodes:
        - "B12-01"
        - "B12-02"
        - "B12-03"
        - "B12-04"
        - "B12-05"
        - "B12-06"
        - "B12-07"
        - "B12-08"
        - "B12-09"
        - "B12-10"
        - "B12-11"
        - "B12-12"
  nodes:
    - id: "B12-01"
      name: "OCR 文本识别"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "b12-anchor"
    - id: "B12-02"
      name: "版面与阅读顺序"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B12-01"
      provenance:
        - "b12-anchor"
    - id: "B12-03"
      name: "表格结构还原"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B12-02"
      provenance:
        - "b12-anchor"
    - id: "B12-04"
      name: "公式识别"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "b12-anchor"
    - id: "B12-05"
      name: "手写体识别"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B12-04"
      provenance:
        - "b12-anchor"
    - id: "B12-06"
      name: "票据与表单"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B12-03"
      provenance:
        - "b12-anchor"
    - id: "B12-07"
      name: "PDF 与扫描件处理"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B12-06"
      provenance:
        - "b12-anchor"
    - id: "B12-08"
      name: "多栏与图注关联"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B12-02"
      provenance:
        - "b12-anchor"
    - id: "B12-09"
      name: "文档分类与归档"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B12-02"
      provenance:
        - "b12-anchor"
    - id: "B12-10"
      name: "关键信息定位"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B12-09"
      provenance:
        - "b12-anchor"
    - id: "B12-11"
      name: "解析置信度与复核"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "B12-07"
      provenance:
        - "b12-anchor"
    - id: "B12-12"
      name: "多语言文档"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "B12-11"
      provenance:
        - "b12-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（B12-00）不随包交付，装载方须自备领域基础。
