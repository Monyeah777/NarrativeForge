# Trace as State（客观摘要）

> 材料：**Trace as State: Reasoning Traces as Conditional States for Long-Context Transformers**
> 引用格式：`arXiv:2609.02702（2026-09-02，预印本）`
> 作者 / 机构：Xu Zou（Z.ai / 智谱 AI）· Jie Tang（清华大学）
> 本页性质：**客观摘要**——不含对 NF 的结论或承诺（对 NF 的参考含义另见 T2 映射表）

## 1. 命题

Transformer 的因果处理与长上下文推理之间存在错位：某些推理必须依赖「后来才被发现的任务状态」。
对因果状态更新处理器，**条件在前（condition first）**比条件在后，在最坏情况下可省**指数级内存**。

## 2. 机制

把收集到的**推理轨迹（trace）作为任务状态的文本代理**，放在长上下文块**之前**（fresh pass），
让先前推导引导重读（Trace → Context → Question）。

## 3. 对照与关键结果

| 项 | 内容 |
|---|---|
| 对照组 | **Trace Append**——同一代理，但放在上下文**之后** |
| 总体 | 3 模型 × 3 数据集 **27 个组合中 26 个胜出** |
| GraphWalks Parents（精确匹配） | DeepSeek V4 Pro Preview：29.2% →（Append）43.0% → **81.8%**；GLM-5.2：66.4% → 83.2% → **100.0%** |

## 4. 结构（便于按图索骥）

Intro / Related Work（长上下文架构、推理因果序、重读与文本反馈、推理轨迹即状态）/
Methodology（因果状态更新、文本状态代理）/ Experiments（GraphWalks、MRCRv2、NUB-1M）/
附录（命题证明、评分、模板、Token 用量）。

## 5. 本页不做什么

- 不评估该论文与 NF 的因果关系；不给 NF 侧的结论；
- 不复制原文（原文见本地素材包 `trace_as_state_full.txt`）；
- 数字均转自备忘 v1 的核实档案（同一素材包内）。
