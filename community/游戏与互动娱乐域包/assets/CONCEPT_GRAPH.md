<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 游戏与互动娱乐（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「游戏与互动娱乐」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（游戏与互动娱乐:M01）与收口模块（游戏与互动娱乐:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 1 个包外前置族（D18-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `D18-01` | NPC 对话 | P40 | — | d18-anchor |
| `D18-02` | 关卡生成 | P60 | `D18-01` | d18-anchor |
| `D18-03` | 数值平衡 | P40 | `D18-02` | d18-anchor |
| `D18-04` | 玩家行为分析 | P60 | `D18-03`、`D18-01` | d18-anchor |
| `D18-05` | 反作弊 | P40 | `D18-04`、`D18-02` | d18-anchor |
| `D18-06` | 剧情分支 | P60 | `D18-05`、`D18-03` | d18-anchor |
| `D18-07` | 美术资产生成 | P40 | `D18-06`、`D18-04` | d18-anchor |
| `D18-08` | 本地化配音 | P60 | `D18-07`、`D18-05` | d18-anchor |
| `D18-09` | 社群运营 | P40 | `D18-08`、`D18-06` | d18-anchor |
| `D18-10` | UGC 审核 | P60 | `D18-09`、`D18-07` | d18-anchor |
| `D18-11` | 陪练与教学 | P40 | `D18-10`、`D18-08` | d18-anchor |
| `D18-12` | 测试用例生成 | P60 | `D18-11`、`D18-09` | d18-anchor |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `D18-NPC-对话` | `D18-01` |
| `D18-关卡生成` | `D18-02` |
| `D18-数值平衡` | `D18-03` |
| `D18-玩家行为分析` | `D18-04` |
| `D18-反作弊` | `D18-05` |
| `D18-剧情分支` | `D18-06` |
| `D18-美术资产生成` | `D18-07` |
| `D18-本地化配音` | `D18-08` |
| `D18-社群运营` | `D18-09` |
| `D18-UGC-审核` | `D18-10` |
| `D18-陪练与教学` | `D18-11` |
| `D18-测试用例生成` | `D18-12` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "游戏与互动娱乐"
  code: "D18"
  provenance_strength: "external"
  provenance_legend:
    d18-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
  external_prereqs:
    - id: "D18-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "游戏与互动娱乐 全域"
      nodes:
        - "D18-01"
        - "D18-02"
        - "D18-03"
        - "D18-04"
        - "D18-05"
        - "D18-06"
        - "D18-07"
        - "D18-08"
        - "D18-09"
        - "D18-10"
        - "D18-11"
        - "D18-12"
  nodes:
    - id: "D18-01"
      name: "NPC 对话"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "d18-anchor"
    - id: "D18-02"
      name: "关卡生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D18-01"
      provenance:
        - "d18-anchor"
    - id: "D18-03"
      name: "数值平衡"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D18-02"
      provenance:
        - "d18-anchor"
    - id: "D18-04"
      name: "玩家行为分析"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D18-03"
        - "D18-01"
      provenance:
        - "d18-anchor"
    - id: "D18-05"
      name: "反作弊"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D18-04"
        - "D18-02"
      provenance:
        - "d18-anchor"
    - id: "D18-06"
      name: "剧情分支"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D18-05"
        - "D18-03"
      provenance:
        - "d18-anchor"
    - id: "D18-07"
      name: "美术资产生成"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D18-06"
        - "D18-04"
      provenance:
        - "d18-anchor"
    - id: "D18-08"
      name: "本地化配音"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D18-07"
        - "D18-05"
      provenance:
        - "d18-anchor"
    - id: "D18-09"
      name: "社群运营"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D18-08"
        - "D18-06"
      provenance:
        - "d18-anchor"
    - id: "D18-10"
      name: "UGC 审核"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D18-09"
        - "D18-07"
      provenance:
        - "d18-anchor"
    - id: "D18-11"
      name: "陪练与教学"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "D18-10"
        - "D18-08"
      provenance:
        - "d18-anchor"
    - id: "D18-12"
      name: "测试用例生成"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "D18-11"
        - "D18-09"
      provenance:
        - "d18-anchor"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（D18-00）不随包交付，装载方须自备领域基础。
