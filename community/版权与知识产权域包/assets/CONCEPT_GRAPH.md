<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 版权与知识产权（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「版权与知识产权」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（版权与知识产权:M01）与收口模块（版权与知识产权:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（F04-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `F04-01` | 训练数据来源审查 | P40 | — | f04-anchor |
| `F04-02` | 授权与许可 | P60 | `F04-01` | f04-anchor |
| `F04-03` | 生成物权属 | P40 | `F04-02` | f04-anchor |
| `F04-04` | 相似度比对 | P60 | `F04-03`、`F04-01` | f04-anchor |
| `F04-05` | 侵权应对 | P40 | `F04-04`、`F04-02` | f04-anchor |
| `F04-06` | 权利人通知机制 | P60 | `F04-05`、`F04-03` | f04-anchor |
| `F04-07` | 素材库合规 | P40 | `F04-06`、`F04-04` | f04-anchor |
| `F04-08` | 商标与形象权 | P60 | `F04-07`、`F04-05` | f04-anchor |
| `F04-09` | 开源协议 | P40 | `F04-08`、`F04-06` | f04-anchor |
| `F04-10` | 字体与音乐授权 | P60 | `F04-09`、`F04-07` | f04-anchor |
| `F04-11` | 署名与引用 | P40 | `F04-10`、`F04-08` | f04-anchor |
| `F04-12` | 商用风险清单 | P60 | `F04-11`、`F04-09` | f04-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `F04-训练数据来源审查` | `F04-01` |
| `F04-授权与许可` | `F04-02` |
| `F04-生成物权属` | `F04-03` |
| `F04-相似度比对` | `F04-04` |
| `F04-侵权应对` | `F04-05` |
| `F04-权利人通知机制` | `F04-06` |
| `F04-素材库合规` | `F04-07` |
| `F04-商标与形象权` | `F04-08` |
| `F04-开源协议` | `F04-09` |
| `F04-字体与音乐授权` | `F04-10` |
| `F04-署名与引用` | `F04-11` |
| `F04-商用风险清单` | `F04-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "版权与知识产权"
  code: "F04"
  provenance_strength: "external"
  provenance_legend:
    f04-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "F04-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "版权与知识产权 全域"
      nodes:
        - "F04-01"
        - "F04-02"
        - "F04-03"
        - "F04-04"
        - "F04-05"
        - "F04-06"
        - "F04-07"
        - "F04-08"
        - "F04-09"
        - "F04-10"
        - "F04-11"
        - "F04-12"
  nodes:
    - id: "F04-01"
      name: "训练数据来源审查"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "f04-anchor"
    - id: "F04-02"
      name: "授权与许可"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F04-01"
      provenance:
        - "f04-anchor"
    - id: "F04-03"
      name: "生成物权属"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F04-02"
      provenance:
        - "f04-anchor"
    - id: "F04-04"
      name: "相似度比对"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F04-03"
        - "F04-01"
      provenance:
        - "f04-anchor"
    - id: "F04-05"
      name: "侵权应对"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F04-04"
        - "F04-02"
      provenance:
        - "f04-anchor"
    - id: "F04-06"
      name: "权利人通知机制"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F04-05"
        - "F04-03"
      provenance:
        - "f04-anchor"
    - id: "F04-07"
      name: "素材库合规"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F04-06"
        - "F04-04"
      provenance:
        - "f04-anchor"
    - id: "F04-08"
      name: "商标与形象权"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F04-07"
        - "F04-05"
      provenance:
        - "f04-anchor"
    - id: "F04-09"
      name: "开源协议"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F04-08"
        - "F04-06"
      provenance:
        - "f04-anchor"
    - id: "F04-10"
      name: "字体与音乐授权"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F04-09"
        - "F04-07"
      provenance:
        - "f04-anchor"
    - id: "F04-11"
      name: "署名与引用"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "F04-10"
        - "F04-08"
      provenance:
        - "f04-anchor"
    - id: "F04-12"
      name: "商用风险清单"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "F04-11"
        - "F04-09"
      provenance:
        - "f04-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（F04-00）不随包交付，装载方须自备领域基础。
