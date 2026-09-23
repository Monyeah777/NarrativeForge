<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · 强化学习与决策（概念前置偏序）

> 用途：本域包的**前置闭包求值输入面**——把「强化学习与决策」这一域的 12 个细分概念声明成一张偏序图（DAG），供域内口径模块（强化学习与决策:M01）与收口模块（强化学习与决策:M02）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3 由它导出。
> 覆盖：12 个包内概念 + 4 个**可扩展标准节点**（标准目录绑定）+ 1 个包外前置族（A12-00 领域通用前置）。
> 来源：本件正文自撰；每条细分的权威锚见资产 `DOMAIN_SPEC` 与 `STANDARDS_ANCHORS`（逐条可达性实证）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（本域第 N 条细分）。
- **前置**：装载该概念之前必须先具备的概念（边方向「前置 → 后继」）。
- **层**：该概念在 NF 九层位中的合理驻留层（P00–P80），用于装配定位，不是执行顺序。
- **证据**：节点来源锚（见 §5 图例）；本图所有节点均挂外部可复核锚。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `A12-01` | 策略梯度与 PPO | P40 | — | a12-anchor |
| `A12-02` | 离线强化学习 | P60 | — | a12-anchor |
| `A12-03` | 世界模型强化学习 | P40 | `A12-02` | a12-anchor |
| `A12-04` | 多臂老虎机与 A/B | P60 | — | a12-anchor |
| `A12-05` | 奖励函数设计 | P40 | — | a12-anchor |
| `A12-06` | 仿真环境搭建 | P60 | — | a12-anchor |
| `A12-07` | 多智能体博弈 | P40 | `A12-06` | a12-anchor |
| `A12-08` | 规划与搜索（MCTS） | P60 | `A12-03` | a12-anchor |
| `A12-09` | 推荐系统 RL | P40 | `A12-04` | a12-anchor |
| `A12-10` | 资源调度优化 | P60 | `A12-09` | a12-anchor |
| `A12-11` | RLHF 中的 RL | P40 | `A12-01`、`A12-05` | a12-anchor |
| `A12-12` | 训练稳定性与探索 | P60 | `A12-01`、`A12-10` | a12-anchor |
| `STD-mcp` | 标准 · Model Context Protocol（Anthropic/MCP） | P80 | `A12-07` | std-catalog |
| `STD-mlcommons-bench` | 标准 · MLPerf 基准（可扩展场景）（MLCommons） | P80 | `A12-01`、`A12-05`、`A12-09`、`A12-11`、`A12-12` | std-catalog |
| `STD-nist-ai-rmf` | 标准 · AI 风险管理框架（NIST） | P80 | `A12-02`、`A12-04`、`A12-06`、`A12-08`、`A12-10` | std-catalog |
| `STD-onnx` | 标准 · ONNX（opset 扩展）（Linux Foundation） | P80 | `A12-03` | std-catalog |

## 3. 别名表（求值时 id 与别名等价）

| 别名 | 概念 id |
|---|---|
| `A12-策略梯度与-PPO` | `A12-01` |
| `A12-离线强化学习` | `A12-02` |
| `A12-世界模型强化学习` | `A12-03` |
| `A12-多臂老虎机与-A/B` | `A12-04` |
| `A12-奖励函数设计` | `A12-05` |
| `A12-仿真环境搭建` | `A12-06` |
| `A12-多智能体博弈` | `A12-07` |
| `A12-规划与搜索-MCTS-` | `A12-08` |
| `A12-推荐系统-RL` | `A12-09` |
| `A12-资源调度优化` | `A12-10` |
| `A12-RLHF-中的-RL` | `A12-11` |
| `A12-训练稳定性与探索` | `A12-12` |
| `std-mcp` | `STD-mcp` |
| `std-mlcommons-bench` | `STD-mlcommons-bench` |
| `std-nist-ai-rmf` | `STD-nist-ai-rmf` |
| `std-onnx` | `STD-onnx` |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: "强化学习与决策"
  code: "A12"
  provenance_strength: "external"
  provenance_legend:
    a12-anchor: "域内权威锚（规范 / 论文 / 参考实现），逐条 URL 与可达性实证见资产 STANDARDS_ANCHORS（本波实测）"
    std-catalog: "可扩展标准目录条目（protocol/standards_catalog.json，本机可达性实测）"
  external_prereqs:
    - id: "A12-00"
      name: "领域通用前置族（数学/工程基础，包外）"
  branches:
    - id: "domain"
      name: "强化学习与决策 全域"
      nodes:
        - "A12-01"
        - "A12-02"
        - "A12-03"
        - "A12-04"
        - "A12-05"
        - "A12-06"
        - "A12-07"
        - "A12-08"
        - "A12-09"
        - "A12-10"
        - "A12-11"
        - "A12-12"
    - id: "standards"
      name: "可扩展标准（绑定）"
      nodes:
        - "STD-mcp"
        - "STD-mlcommons-bench"
        - "STD-nist-ai-rmf"
        - "STD-onnx"
  nodes:
    - id: "A12-01"
      name: "策略梯度与 PPO"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a12-anchor"
    - id: "A12-02"
      name: "离线强化学习"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a12-anchor"
    - id: "A12-03"
      name: "世界模型强化学习"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A12-02"
      provenance:
        - "a12-anchor"
    - id: "A12-04"
      name: "多臂老虎机与 A/B"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a12-anchor"
    - id: "A12-05"
      name: "奖励函数设计"
      layer: "P40"
      branch: "domain"
      prereqs: []
      provenance:
        - "a12-anchor"
    - id: "A12-06"
      name: "仿真环境搭建"
      layer: "P60"
      branch: "domain"
      prereqs: []
      provenance:
        - "a12-anchor"
    - id: "A12-07"
      name: "多智能体博弈"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A12-06"
      provenance:
        - "a12-anchor"
    - id: "A12-08"
      name: "规划与搜索（MCTS）"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A12-03"
      provenance:
        - "a12-anchor"
    - id: "A12-09"
      name: "推荐系统 RL"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A12-04"
      provenance:
        - "a12-anchor"
    - id: "A12-10"
      name: "资源调度优化"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A12-09"
      provenance:
        - "a12-anchor"
    - id: "A12-11"
      name: "RLHF 中的 RL"
      layer: "P40"
      branch: "domain"
      prereqs:
        - "A12-01"
        - "A12-05"
      provenance:
        - "a12-anchor"
    - id: "A12-12"
      name: "训练稳定性与探索"
      layer: "P60"
      branch: "domain"
      prereqs:
        - "A12-01"
        - "A12-10"
      provenance:
        - "a12-anchor"
    - id: "STD-mcp"
      name: "标准 · Model Context Protocol"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A12-07"
      provenance:
        - "std-catalog"
    - id: "STD-mlcommons-bench"
      name: "标准 · MLPerf 基准（可扩展场景）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A12-01"
        - "A12-05"
        - "A12-09"
        - "A12-11"
        - "A12-12"
      provenance:
        - "std-catalog"
    - id: "STD-nist-ai-rmf"
      name: "标准 · AI 风险管理框架"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A12-02"
        - "A12-04"
        - "A12-06"
        - "A12-08"
        - "A12-10"
      provenance:
        - "std-catalog"
    - id: "STD-onnx"
      name: "标准 · ONNX（opset 扩展）"
      layer: "P80"
      branch: "standards"
      prereqs:
        - "A12-03"
      provenance:
        - "std-catalog"
```

## 5. 证据与边界

- 每个节点的来源锚（外部规范 / 论文 / 参考实现）逐条登记于 `STANDARDS_ANCHORS`，本图 `provenance_strength = external`（全覆盖，可复核）。
- 图只声明**结构前置**（装载顺序），不声明掌握程度；边为「先具备 → 后展开」的域内常识序。
- 包外前置族（A12-00）不随包交付，装载方须自备领域基础。
