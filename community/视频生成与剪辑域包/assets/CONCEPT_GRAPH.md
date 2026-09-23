<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 视频生成与剪辑（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「视频生成与剪辑」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（视频生成与剪辑:M01）与收口模块（视频生成与剪辑:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（E08-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `E08-01` | 分镜脚本 | P40 | — | e08-anchor |
| `E08-02` | 图生视频 | P60 | `E08-01` | e08-anchor |
| `E08-03` | 口播数字人 | P40 | `E08-02` | e08-anchor |
| `E08-04` | 字幕与转录 | P60 | `E08-03`、`E08-01` | e08-anchor |
| `E08-05` | 自动剪辑节奏 | P40 | `E08-04`、`E08-02` | e08-anchor |
| `E08-06` | 转场与特效 | P60 | `E08-05`、`E08-03` | e08-anchor |
| `E08-07` | 多语配音 | P40 | `E08-06`、`E08-04` | e08-anchor |
| `E08-08` | 素材检索 | P60 | `E08-07`、`E08-05` | e08-anchor |
| `E08-09` | 长视频切片 | P40 | `E08-08`、`E08-06` | e08-anchor |
| `E08-10` | 竖屏适配 | P60 | `E08-09`、`E08-07` | e08-anchor |
| `E08-11` | 封面与缩略图 | P40 | `E08-10`、`E08-08` | e08-anchor |
| `E08-12` | 成片审看 | P60 | `E08-11`、`E08-09` | e08-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `E08-分镜脚本` | `E08-01` |
| `E08-图生视频` | `E08-02` |
| `E08-口播数字人` | `E08-03` |
| `E08-字幕与转录` | `E08-04` |
| `E08-自动剪辑节奏` | `E08-05` |
| `E08-转场与特效` | `E08-06` |
| `E08-多语配音` | `E08-07` |
| `E08-素材检索` | `E08-08` |
| `E08-长视频切片` | `E08-09` |
| `E08-竖屏适配` | `E08-10` |
| `E08-封面与缩略图` | `E08-11` |
| `E08-成片审看` | `E08-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "视频生成与剪辑"
  code: "E08"
  provenance_strength: "external"
  provenance_legend:
    e08-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "E08-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "视频生成与剪辑 全域"
      nodes:
        - "E08-01"
        - "E08-02"
        - "E08-03"
        - "E08-04"
        - "E08-05"
        - "E08-06"
        - "E08-07"
        - "E08-08"
        - "E08-09"
        - "E08-10"
        - "E08-11"
        - "E08-12"
  nodes:
    - id: "E08-01"
      name: "分镜脚本"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "e08-anchor"
    - id: "E08-02"
      name: "图生视频"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E08-01"
      provenance:
        - "e08-anchor"
    - id: "E08-03"
      name: "口播数字人"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E08-02"
      provenance:
        - "e08-anchor"
    - id: "E08-04"
      name: "字幕与转录"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E08-03"
        - "E08-01"
      provenance:
        - "e08-anchor"
    - id: "E08-05"
      name: "自动剪辑节奏"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E08-04"
        - "E08-02"
      provenance:
        - "e08-anchor"
    - id: "E08-06"
      name: "转场与特效"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E08-05"
        - "E08-03"
      provenance:
        - "e08-anchor"
    - id: "E08-07"
      name: "多语配音"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E08-06"
        - "E08-04"
      provenance:
        - "e08-anchor"
    - id: "E08-08"
      name: "素材检索"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E08-07"
        - "E08-05"
      provenance:
        - "e08-anchor"
    - id: "E08-09"
      name: "长视频切片"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E08-08"
        - "E08-06"
      provenance:
        - "e08-anchor"
    - id: "E08-10"
      name: "竖屏适配"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E08-09"
        - "E08-07"
      provenance:
        - "e08-anchor"
    - id: "E08-11"
      name: "封面与缩略图"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "E08-10"
        - "E08-08"
      provenance:
        - "e08-anchor"
    - id: "E08-12"
      name: "成片审看"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "E08-11"
        - "E08-09"
      provenance:
        - "e08-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（E08-00）不随包交付，装载方须自备领域基础。
