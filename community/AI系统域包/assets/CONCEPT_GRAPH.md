<!-- nf-asset: key="CONCEPT_GRAPH" version="1.1" status="active" -->
# 概念图 · AI 系统域（概念前置偏序）

> 用途：AI系统域包的**前置闭包求值输入面**——把「AI 系统」这一域的概念前置关系声明成一张偏序图（DAG），供前置闭包求值（AI系统:M25）与装载序就绪门（AI系统:M26）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）/ 别名表（§3）/ 机器可读块（§4）三形态同源——**§4 围栏块是唯一机读真相**，§2/§3/§6 由它导出。
> 覆盖：**双支**——计算与实现栈（C01–C24、C46）＋ 应用与系统设计栈（C25–C45、C47），另含包外前置族 C00；共 47 个包内概念 + 1 个外部前置族。
> 来源：本件正文自撰，不从任何外部仓库复制文本；结构与序作为**内容证据**逐条标注（来源与许可见 §7），边级溯源见 §4 `provenance`。
> 版本：v1.1（本波扩面：新增应用栈 21 概念 + 训练适配 / 模型版图 2 概念 + 概念别名面；v1.0 = 计算栈 24 概念）。

## 1. 读法

- **概念**：一个可独立装载的知识单元（如「自动微分」「KV cache 分页」），有稳定 id 与所属能力层。
- **分支**：`compute` = 计算与实现栈（芯片 → 编译 → 框架 → 训练 → 推理服务）；`app` = 应用与系统设计栈（提示 → 检索 → Agent → 记忆 → 安全 → 评测 → 治理）。分支只用于**过滤与呈现**，闭包按全图求值。
- **条目键**：概念 id 即条目键——资产键 `CONCEPT_GRAPH` + 条目键（如 `C22`）构成唯一寻址（`asset_get('CONCEPT_GRAPH','C22')`），一概念一键。
- **别名**：同一概念的常用检索词（中英文 / 缩写 / 惯例名，如 `RAG`、`PagedAttention`、`ReAct`）——见 §3；求值时 id 与别名等价。
- **前置（prereqs）**：装载该概念**之前必须先具备**的概念——图的边，方向「前置 → 后继」；跨分支的边是本图最有信息量的部分（如「服务调度」是「治理与成本」的前置）。
- **层（layer）**：该概念在 NF 九层位（P00–P80）中的合理驻留层，用于装配定位，**不是**执行顺序。
- **证据（provenance）**：该节点内容与前置关系来自哪条来源线（§7 图例）；`inferred` = 本件推断，待复核。
- **包外前置（C00）**：只声明存在、不建模块（域包不承担数学 / 编程 / 系统基础的教学职能）。

## 2. 条目键表（一概念一键，asset_get 寻址）

### 2.1 计算与实现栈（分支 compute）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C00` | 外部前置族：数学基础 / 编程与算法 / 计算机系统基础 | —（包外） | — | cs2023 |
| `C01` | AI 系统全栈概览：算法 × 框架 × 体系结构 | P00 | `C00` | aisystem、cmu-mlsys |
| `C02` | AI 计算体系：神经网络计算模式、并行度来源 | P00 | `C01` | aisystem |
| `C03` | 芯片基础：CPU/GPU/NPU、SIMT、内存层次 | P00 | `C02` | aisystem |
| `C04` | GPU 体系：SM / warp / 占用率、协作与同步 | P10 | `C03` | aisystem |
| `C05` | 硬件加速实践：算术强度、Roofline、GPU GEMM | P10 | `C04` | cmu-mlsys |
| `C06` | CUDA 编程：kernel / 共享内存 / 同步 / 访存 | P30 | `C05` | cmu-mlsys |
| `C07` | 深度学习编程抽象：张量、算子、图 vs 即时 | P40 | `C01` | cmu-mlsys |
| `C08` | 自动微分：反向模式、计算图、内存开销 | P40 | `C07` | cmu-mlsys、cmu-dlsys、aisystem |
| `C09` | 计算图：图优化 / 执行 / 控制流表达 | P40 | `C08` | aisystem |
| `C10` | 框架工程：NN 库实现、算子与内存管理 | P50 | `C07`、`C09` | cmu-dlsys、aisystem |
| `C11` | 传统编译原理：IR / SSA / 优化 / 后端 | P30 | `C00` | aisystem、mlir |
| `C12` | AI 编译器与多级 IR：图级 / 算子级 / kernel 级 | P40 | `C11`、`C09` | aisystem、tvm、mlir、dlc-survey |
| `C13` | 前端优化：算子融合、常量折叠、布局改写 | P40 | `C12` | aisystem |
| `C14` | 后端与 Kernel 优化：调度、自动调优、多面体 | P50 | `C13`、`C06` | aisystem、cmu-mlsys |
| `C15` | 分布式训练：数据并行与集合通信 | P50 | `C07`、`C00` | cmu-mlsys |
| `C16` | 显存与内存优化：激活重算、优化器状态分片 | P60 | `C15`、`C08` | zero、cmu-mlsys |
| `C17` | 并行训练工程：张量 / 流水并行、MoE | P60 | `C15`、`C16` | cmu-mlsys |
| `C18` | 推理系统与引擎：图转换、运行时、调度 | P50 | `C09`、`C12` | aisystem |
| `C19` | 模型压缩：量化 / 蒸馏 / 剪枝 | P60 | `C10`、`C18`、`C46` | aisystem |
| `C20` | Transformer 与注意力：结构族、KV cache | P40 | `C08`、`C10` | cmu-mlsys、cmu-dlsys |
| `C21` | 注意力 IO 优化：分块、重算、精确注意力 | P50 | `C20`、`C14` | flash-attention |
| `C22` | 服务调度与批处理：连续批处理、迭代级调度、KV 分页 | P50 | `C18`、`C20`、`C16` | orca、vllm |
| `C23` | Kernel 层推理优化：融合 kernel、mega-kernel | P50 | `C14`、`C18` | aisystem、cmu-mlsys |
| `C24` | 评测与可靠性：吞吐 / 延迟口径、回归基线、对齐与幻觉 | P80 | `C18`、`C22` | cs2023、inferred |
| `C46` | 训练与适配方法：预训练、微调、参数高效适配、对齐、合成数据 | P60 | `C15`、`C08` | guide-03 |

### 2.2 应用与系统设计栈（分支 app）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C25` | 提示与上下文工程：少样本、思维链、上下文装配 | P40 | `C01`、`C20` | guide-05、prompt-libs |
| `C26` | 结构化生成与输出契约：模式约束解码、可解析输出 | P40 | `C25` | guide-05 |
| `C27` | 向量表示与嵌入：编码模型、向量空间 | P40 | `C20` | guide-01、guide-06 |
| `C28` | 检索增强生成（RAG）：外部上下文接地 | P50 | `C25`、`C27`、`C43` | guide-06 |
| `C29` | 向量索引与向量库：ANN、混合检索 | P50 | `C27` | guide-06、iis-osint |
| `C30` | 重排与检索质量：交叉编码、后交互、上下文检索 | P50 | `C28`、`C29` | guide-06 |
| `C31` | 图谱增强检索：GraphRAG、Agentic RAG | P50 | `C28`、`C30` | guide-06 |
| `C32` | Agent 基础与推理循环：ReAct、观察-行动回合 | P40 | `C25`、`C18` | guide-07 |
| `C33` | 工具使用与工具面：函数调用、工具协议、能力声明 | P50 | `C32` | guide-07、guide-17 |
| `C34` | 多智能体编排：角色分工、交接、仲裁 | P50 | `C32`、`C33` | guide-07 |
| `C35` | 记忆与状态：短期上下文、长期记忆、状态管理 | P60 | `C32`、`C29` | guide-08 |
| `C36` | 规划与任务分解：计划-执行、子目标拆解 | P50 | `C32` | guide-07 |
| `C37` | 错误处理与持久执行：重试、断点续跑、循环工程 | P50 | `C32`、`C36` | guide-07 |
| `C38` | 人在环路与审批门：人工确认、可回滚动作 | P60 | `C32`、`C37` | guide-07 |
| `C39` | 沙箱与 Agent 安全：提示注入防御、越权面、权限边界 | P60 | `C25`、`C32`、`C33` | guide-12、guide-07 |
| `C40` | 评价与可观测：离线评测、在线观测、基准口径 | P80 | `C24`、`C28`、`C32` | guide-14 |
| `C41` | 护栏与可靠性模式：输出护栏、集成冗余、降级 | P60 | `C25`、`C32`、`C40` | guide-13 |
| `C42` | 治理、合规与成本：策略、审计、成本与路由 | P80 | `C22`、`C40`、`C41`、`C47` | guide-11、guide-13 |
| `C43` | 数据与文档处理管线：抽取、清洗、分块、数据工程 | P50 | `C27` | guide-06、guide-10、iis-osint |
| `C44` | 多模态与实时语音交互：跨模态生成、实时会话 | P50 | `C18`、`C20` | guide-18、guide-19 |
| `C45` | 系统设计模式与反模式：可复用模式、常见反模式 | P80 | `C28`、`C32`、`C40` | guide-15、guide-16 |
| `C47` | 模型版图与选型：模型家族、能力评估、定价口径 | P60 | `C01`、`C20`、`C24` | guide-02 |

## 3. 概念别名表（检索词 → 条目键）

> 别名与 id 等价（求值时同解）；别名在同一图内**必须唯一**（重复即拒，防歧义）。概念名本身也可直接作为检索词。

| 条目键 | 别名（中英 / 缩写 / 惯例名） |
|---|---|
| `C01` | AI系统全栈、ML Systems、机器学习系统 |
| `C05` | 算术强度、Roofline、GPU GEMM |
| `C06` | CUDA、kernel 编程 |
| `C08` | 自动微分、autodiff、反向模式 |
| `C09` | 计算图、图执行 |
| `C11` | 传统编译原理、SSA |
| `C12` | AI 编译器、多级 IR、TVM |
| `C13` | 算子融合、前端优化 |
| `C14` | 后端优化、自动调优、多面体 |
| `C15` | 数据并行、集合通信 |
| `C16` | ZeRO、激活重算、优化器状态分片 |
| `C17` | 张量并行、流水并行、MoE |
| `C18` | 推理系统、推理引擎、运行时 |
| `C19` | 模型压缩、量化、蒸馏、剪枝 |
| `C20` | Transformer、注意力机制、KV cache |
| `C21` | FlashAttention、IO 感知注意力、分块注意力 |
| `C22` | PagedAttention、vLLM、连续批处理、迭代级调度、KV 分页 |
| `C23` | Mega-kernel、推理 kernel 融合 |
| `C24` | 吞吐延迟口径、回归基线、幻觉 |
| `C25` | 提示工程、Prompt Engineering、上下文工程、思维链、CoT、Few-shot |
| `C26` | 结构化生成、JSON 模式、输出契约 |
| `C27` | 嵌入、embeddings、向量表示、向量空间 |
| `C28` | RAG、检索增强生成 |
| `C29` | 向量库、向量数据库、ANN、混合检索 |
| `C30` | 重排、rerank、ColBERT、后交互、上下文检索 |
| `C31` | GraphRAG、Agentic RAG、图谱增强检索 |
| `C32` | Agent、智能体、ReAct、推理循环 |
| `C33` | 工具使用、function calling、MCP、工具面 |
| `C34` | 多智能体、multi-agent、编排 |
| `C35` | 记忆、memory、长期记忆、状态管理 |
| `C36` | 规划、任务分解、plan-and-execute |
| `C37` | 错误恢复、持久执行、循环工程 |
| `C38` | 人在环路、HITL、审批门 |
| `C39` | 沙箱、提示注入、越权、Agent 安全 |
| `C40` | 评测、evaluation、观测性、observability、基准 |
| `C41` | 护栏、guardrails、可靠性模式、集成冗余 |
| `C42` | 治理、合规、FinOps、成本优化、模型路由 |
| `C43` | 数据管线、文档处理、OCR、分块、数据工程 |
| `C44` | 多模态、语音、实时语音、音视频 |
| `C45` | 设计模式、反模式、design patterns |
| `C46` | 训练与适配、预训练、微调、LoRA、PEFT、RLHF、DPO、合成数据 |
| `C47` | 模型版图、模型选型、能力评估、定价 |

## 4. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.1"
  domain: AI系统
  date: "2026-09-20"
  intent: 概念前置依赖的偏序声明（前置闭包求值的输入面）
  closure_rules:
    closure: "closure(c) = {c} ∪ ⋃ closure(p)，p ∈ prereqs(c)（传递闭包）"
    missing: "missing(c, L) = closure(c) − L（L = 已装载概念集）"
    readiness: "readiness(c, L) = (missing(c, L) 为空)"
    load_order: "toposort(G) 的任一线性化即合法装载序（并列按 id 升序）"
    frontier: "frontier(L) = {c ∉ L : prereqs(c) ⊆ L}（下一步可装载集；等价于 missing(c,L) = {c}）"
    determinism: "同一 (G, L) 下 missing / load_order / frontier 逐字节可复现"
    alias: "检索词解析顺序 = 条目键 → 别名 → 概念名（大小写与首尾空白无关）；别名重复即拒"
  branches:
    - id: compute
      name: 计算与实现栈（芯片 → 编译 → 框架 → 训练 → 推理服务）
      nodes: [C01, C02, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, C13, C14, C15, C16, C17, C18, C19, C20, C21, C22, C23, C24, C46]
    - id: app
      name: 应用与系统设计栈（提示 → 检索 → Agent → 记忆 → 安全 → 评测 → 治理）
      nodes: [C25, C26, C27, C28, C29, C30, C31, C32, C33, C34, C35, C36, C37, C38, C39, C40, C41, C42, C43, C44, C45, C47]
  provenance_legend:
    aisystem: 开源课程《AI 系统》五模块 24 子单元（Infrasys-AI，Apache-2.0，Copyright 2018-2023 ZOMI）
    cmu-mlsys: CMU 15-442/642 Machine Learning Systems 讲序（slides 文件名序）
    cmu-dlsys: CMU 10-414/714 Deep Learning Systems 实现序（notebook 序）
    cs2023: ACM/IEEE-CS/AAAI CS2023 Knowledge Area 名单
    tvm: TVM OSDI'18（端到端优化编译器）
    mlir: arXiv:2002.11054（多级 IR 编译器基础设施）
    dlc-survey: arXiv:2002.03794（深度学习编译器综述）
    flash-attention: arXiv:2205.14135（IO 感知的精确注意力）
    zero: arXiv:1910.02054（优化器状态分片与激活重算）
    orca: OSDI'22 Orca（迭代级调度与选择性批处理）
    vllm: arXiv:2309.06180（KV cache 分页与跨请求共享）
    guide-01: AI 系统设计指南 §01 foundations（LLM 内部机制 / 分词 / 注意力 / 嵌入 / 推理管线）
    guide-02: 同指南 §02 model landscape（模型分类 / 能力评估 / 定价 / 选型）
    guide-03: 同指南 §03 training-and-adaptation（预训练 / 微调 / 参数高效适配 / 对齐 / 蒸馏 / 合成数据）
    guide-05: 同指南 §05 prompting-and-context（提示工程 / 少样本 / 思维链 / 上下文工程 / 结构化生成 / 注入防御）
    guide-06: 同指南 §06 retrieval-systems（RAG / 分块 / 嵌入模型 / 向量库 / 混合检索 / 重排 / 图检索 / 检索评测）
    guide-07: 同指南 §07 agentic-systems（Agent 基础 / 推理循环 / 工具与协议 / 多智能体 / 记忆 / 规划 / 恢复 / 人在环路 / 安全）
    guide-08: 同指南 §08 memory-and-state（记忆架构 / 短期 / 长期 / 状态管理）
    guide-10: 同指南 §10 document-processing（OCR 与版面）
    guide-11: 同指南 §11 infrastructure-and-mlops（基础设施 / CI-CD / 网关与路由 / 成本）
    guide-12: 同指南 §12 security-and-access（LLM 安全 / 访问控制）
    guide-13: 同指南 §13 reliability-and-safety（护栏 / 集成方法 / 可靠性模式 / 治理合规）
    guide-14: 同指南 §14 evaluation-and-observability（评测 / 观测 / 基准）
    guide-15: 同指南 §15 ai-design-patterns（设计模式 / 反模式）
    guide-16: 同指南 §16 case-studies（案例集，作覆盖面证据，不作前置来源）
    guide-17: 同指南 §17 tool-use-and-computer-agents（工具面 / 架构模式 / 计算机操作 Agent）
    guide-18: 同指南 §18 voice-and-audio-agents（实时语音 Agent）
    guide-19: 同指南 §19 multimodal-generation（多模态生成）
    prompt-libs: 公开 Agent 系统提示词合集（结构证据：提示 / 上下文工程是 AI 系统的独立知识面）——仅取「该面存在」这一结构事实，不取文本
    iis-osint: OSINT 情报整合系统（结构证据：采集 → 清洗 → 向量化 → 检索 → 聚合 的知识管线与相似度跳转）
    inferred: 本件推断（无直接来源，待复核）
  external_prereqs:
    - id: C00
      name: 外部前置族：数学基础 / 编程与算法 / 计算机系统基础（体系结构·OS·并行）
      in_package: false
      provenance: [cs2023]
      note: 包外前置，只声明不建模块（域包不承担通识教学职能）
  nodes:
    - {id: C01, branch: compute, name: AI 系统全栈概览：算法 × 框架 × 体系结构, layer: P00, prereqs: [C00], provenance: [aisystem, cmu-mlsys], aliases: [AI系统全栈, ML Systems, 机器学习系统]}
    - {id: C02, branch: compute, name: AI 计算体系：神经网络计算模式、并行度来源, layer: P00, prereqs: [C01], provenance: [aisystem]}
    - {id: C03, branch: compute, name: 芯片基础：CPU/GPU/NPU、SIMT、内存层次, layer: P00, prereqs: [C02], provenance: [aisystem]}
    - {id: C04, branch: compute, name: GPU 体系：SM / warp / 占用率、协作与同步, layer: P10, prereqs: [C03], provenance: [aisystem]}
    - {id: C05, branch: compute, name: 硬件加速实践：算术强度、Roofline、GPU GEMM, layer: P10, prereqs: [C04], provenance: [cmu-mlsys], aliases: [算术强度, Roofline, GPU GEMM]}
    - {id: C06, branch: compute, name: CUDA 编程：kernel / 共享内存 / 同步 / 访存, layer: P30, prereqs: [C05], provenance: [cmu-mlsys], aliases: [CUDA]}
    - {id: C07, branch: compute, name: 深度学习编程抽象：张量、算子、图 vs 即时, layer: P40, prereqs: [C01], provenance: [cmu-mlsys]}
    - {id: C08, branch: compute, name: 自动微分：反向模式、计算图、内存开销, layer: P40, prereqs: [C07], provenance: [cmu-mlsys, cmu-dlsys, aisystem], aliases: [自动微分, autodiff, 反向模式]}
    - {id: C09, branch: compute, name: 计算图：图优化 / 执行 / 控制流表达, layer: P40, prereqs: [C08], provenance: [aisystem], aliases: [计算图]}
    - {id: C10, branch: compute, name: 框架工程：NN 库实现、算子与内存管理, layer: P50, prereqs: [C07, C09], provenance: [cmu-dlsys, aisystem]}
    - {id: C11, branch: compute, name: 传统编译原理：IR / SSA / 优化 / 后端, layer: P30, prereqs: [C00], provenance: [aisystem, mlir], aliases: [传统编译原理, SSA]}
    - {id: C12, branch: compute, name: AI 编译器与多级 IR：图级 / 算子级 / kernel 级, layer: P40, prereqs: [C11, C09], provenance: [aisystem, tvm, mlir, dlc-survey], aliases: [AI编译器, 多级IR, TVM], note: 本节点有两个前置（传统编译 + 计算图），单链叙事会隐藏这一点}
    - {id: C13, branch: compute, name: 前端优化：算子融合、常量折叠、布局改写, layer: P40, prereqs: [C12], provenance: [aisystem], aliases: [前端优化, 算子融合]}
    - {id: C14, branch: compute, name: 后端与 Kernel 优化：调度、自动调优、多面体, layer: P50, prereqs: [C13, C06], provenance: [aisystem, cmu-mlsys], aliases: [后端优化, 自动调优, 多面体], note: 跨层前置边——不接触硬件（C06）写不出 kernel 优化}
    - {id: C15, branch: compute, name: 分布式训练：数据并行与集合通信, layer: P50, prereqs: [C07, C00], provenance: [cmu-mlsys], aliases: [数据并行, 集合通信]}
    - {id: C16, branch: compute, name: 显存与内存优化：激活重算、优化器状态分片, layer: P60, prereqs: [C15, C08], provenance: [zero, cmu-mlsys], aliases: [ZeRO, 激活重算, 优化器状态分片]}
    - {id: C17, branch: compute, name: 并行训练工程：张量 / 流水并行、MoE, layer: P60, prereqs: [C15, C16], provenance: [cmu-mlsys], aliases: [张量并行, 流水并行, MoE]}
    - {id: C18, branch: compute, name: 推理系统与引擎：图转换、运行时、调度, layer: P50, prereqs: [C09, C12], provenance: [aisystem], aliases: [推理系统, 推理引擎]}
    - {id: C19, branch: compute, name: 模型压缩：量化 / 蒸馏 / 剪枝, layer: P60, prereqs: [C10, C18, C46], provenance: [aisystem], aliases: [模型压缩, 量化, 蒸馏, 剪枝]}
    - {id: C20, branch: compute, name: Transformer 与注意力：结构族、KV cache, layer: P40, prereqs: [C08, C10], provenance: [cmu-mlsys, cmu-dlsys], aliases: [Transformer, 注意力机制, KV cache]}
    - {id: C21, branch: compute, name: 注意力 IO 优化：分块、重算、精确注意力, layer: P50, prereqs: [C20, C14], provenance: [flash-attention], aliases: [FlashAttention, IO感知注意力, 分块注意力]}
    - {id: C22, branch: compute, name: 服务调度与批处理：连续批处理、迭代级调度、KV 分页, layer: P50, prereqs: [C18, C20, C16], provenance: [orca, vllm], aliases: [PagedAttention, vLLM, 连续批处理, 迭代级调度, KV分页]}
    - {id: C23, branch: compute, name: Kernel 层推理优化：融合 kernel、mega-kernel, layer: P50, prereqs: [C14, C18], provenance: [aisystem, cmu-mlsys], aliases: [Mega-kernel]}
    - {id: C24, branch: compute, name: 评测与可靠性：吞吐 / 延迟口径、回归基线、对齐与幻觉, layer: P80, prereqs: [C18, C22], provenance: [cs2023, inferred], aliases: [吞吐延迟口径, 回归基线, 幻觉]}
    - {id: C46, branch: compute, name: 训练与适配方法：预训练、微调、参数高效适配、对齐、合成数据, layer: P60, prereqs: [C15, C08], provenance: [guide-03], aliases: [训练与适配, 预训练, 微调, LoRA, PEFT, RLHF, DPO, 合成数据]}
    - {id: C25, branch: app, name: 提示与上下文工程：少样本、思维链、上下文装配, layer: P40, prereqs: [C01, C20], provenance: [guide-05, prompt-libs], aliases: [提示工程, Prompt Engineering, 上下文工程, 思维链, CoT, Few-shot]}
    - {id: C26, branch: app, name: 结构化生成与输出契约：模式约束解码、可解析输出, layer: P40, prereqs: [C25], provenance: [guide-05], aliases: [结构化生成, JSON模式, 输出契约]}
    - {id: C27, branch: app, name: 向量表示与嵌入：编码模型、向量空间, layer: P40, prereqs: [C20], provenance: [guide-01, guide-06], aliases: [嵌入, embeddings, 向量表示]}
    - {id: C43, branch: app, name: 数据与文档处理管线：抽取、清洗、分块、数据工程, layer: P50, prereqs: [C27], provenance: [guide-06, guide-10, iis-osint], aliases: [数据管线, 文档处理, OCR, 分块, 数据工程]}
    - {id: C28, branch: app, name: 检索增强生成（RAG）：外部上下文接地, layer: P50, prereqs: [C25, C27, C43], provenance: [guide-06], aliases: [RAG, 检索增强生成]}
    - {id: C29, branch: app, name: 向量索引与向量库：ANN、混合检索, layer: P50, prereqs: [C27], provenance: [guide-06, iis-osint], aliases: [向量库, 向量数据库, ANN, 混合检索]}
    - {id: C30, branch: app, name: 重排与检索质量：交叉编码、后交互、上下文检索, layer: P50, prereqs: [C28, C29], provenance: [guide-06], aliases: [重排, rerank, ColBERT, 上下文检索]}
    - {id: C31, branch: app, name: 图谱增强检索：GraphRAG、Agentic RAG, layer: P50, prereqs: [C28, C30], provenance: [guide-06], aliases: [GraphRAG, Agentic RAG]}
    - {id: C32, branch: app, name: Agent 基础与推理循环：ReAct、观察-行动回合, layer: P40, prereqs: [C25, C18], provenance: [guide-07], aliases: [Agent, 智能体, ReAct, 推理循环]}
    - {id: C33, branch: app, name: 工具使用与工具面：函数调用、工具协议、能力声明, layer: P50, prereqs: [C32], provenance: [guide-07, guide-17], aliases: [工具使用, function calling, MCP, 工具面]}
    - {id: C34, branch: app, name: 多智能体编排：角色分工、交接、仲裁, layer: P50, prereqs: [C32, C33], provenance: [guide-07], aliases: [多智能体, multi-agent, 编排]}
    - {id: C35, branch: app, name: 记忆与状态：短期上下文、长期记忆、状态管理, layer: P60, prereqs: [C32, C29], provenance: [guide-08], aliases: [记忆, memory, 长期记忆, 状态管理]}
    - {id: C36, branch: app, name: 规划与任务分解：计划-执行、子目标拆解, layer: P50, prereqs: [C32], provenance: [guide-07], aliases: [规划, 任务分解]}
    - {id: C37, branch: app, name: 错误处理与持久执行：重试、断点续跑、循环工程, layer: P50, prereqs: [C32, C36], provenance: [guide-07], aliases: [错误恢复, 持久执行, 循环工程]}
    - {id: C38, branch: app, name: 人在环路与审批门：人工确认、可回滚动作, layer: P60, prereqs: [C32, C37], provenance: [guide-07], aliases: [人在环路, HITL, 审批门]}
    - {id: C39, branch: app, name: 沙箱与 Agent 安全：提示注入防御、越权面、权限边界, layer: P60, prereqs: [C25, C32, C33], provenance: [guide-12, guide-07], aliases: [沙箱, 提示注入, 越权, Agent安全]}
    - {id: C40, branch: app, name: 评价与可观测：离线评测、在线观测、基准口径, layer: P80, prereqs: [C24, C28, C32], provenance: [guide-14], aliases: [评测, evaluation, 观测性, observability, 基准]}
    - {id: C41, branch: app, name: 护栏与可靠性模式：输出护栏、集成冗余、降级, layer: P60, prereqs: [C25, C32, C40], provenance: [guide-13], aliases: [护栏, guardrails, 可靠性模式, 集成冗余]}
    - {id: C44, branch: app, name: 多模态与实时语音交互：跨模态生成、实时会话, layer: P50, prereqs: [C18, C20], provenance: [guide-18, guide-19], aliases: [多模态, 语音, 实时语音]}
    - {id: C47, branch: app, name: 模型版图与选型：模型家族、能力评估、定价口径, layer: P60, prereqs: [C01, C20, C24], provenance: [guide-02], aliases: [模型版图, 模型选型, 能力评估, 定价]}
    - {id: C42, branch: app, name: 治理、合规与成本：策略、审计、成本与路由, layer: P80, prereqs: [C22, C40, C41, C47], provenance: [guide-11, guide-13], aliases: [治理, 合规, FinOps, 成本优化, 模型路由]}
    - {id: C45, branch: app, name: 系统设计模式与反模式：可复用模式、常见反模式, layer: P80, prereqs: [C28, C32, C40], provenance: [guide-15, guide-16], aliases: [设计模式, 反模式]}
  orderings:
    - id: cmu-mlsys
      seq: [C01, C07, C08, C05, C06, C20, C15, C16, C22, C17, C21, C23, C24]
      expectation: 对该 DAG 的违反边数应为 0（合法线性化）
    - id: aisystem-module-order
      seq: [C01, C02, C03, C04, C05, C11, C12, C13, C14, C18, C19, C10, C07, C08, C09]
      expectation: 对该 DAG 存在违反边（目录序是可读性排序，不是前置序）
    - id: design-guide-chapter-order
      seq: [C20, C47, C46, C22, C25, C26, C27, C43, C28, C29, C30, C31, C32, C33, C36, C37, C34, C35, C38, C39, C41, C40, C42, C44, C45]
      expectation: 为该指南每章取代表性概念的章节序；对导出偏序存在违反边（教学序 ≠ 前置序，实测见 §6）
  conflict_rules:
    - 两条独立来源都要求的序 → 硬前置边（进 prereqs）
    - 仅单源要求的序 → 软前置边（进 prereqs 并在 provenance 标注单源）
    - 互为前置（成环）→ 归并为并列节点并记档，不得留环
    - 结构类来源（课程 / 指南章节）只提供覆盖面与教学序证据，不单独立边；落为边时须另有实现类证据或标 inferred
```

## 5. 闭包语义（求值口径）

```
closure(c)    = {c} ∪ ⋃ closure(p)      for p ∈ prereqs(c)     # 传递闭包（DAG 保证终止）
missing(c, L) = closure(c) − L                                   # L = 已装载概念集
readiness(c, L) = (missing(c, L) 为空)                           # 是否可装载
frontier(L)   = {c ∉ L : prereqs(c) ⊆ L}                         # 下一步可装载集（就绪清单）
load_order(G) = toposort(G) 的任一线性化（确定性：同入度按 id 升序）
```

- **确定性纪律**：同一 `(G, L)` 下 `missing` / `frontier` / `load_order` 必须逐字节可复现；求值器见 `scripts/ai_domain_closure.py`。
- **检索词**：`id → 别名 → 概念名` 顺序解析，别名重复即拒（§3）。
- **分支过滤**：`--branch compute|app` 只影响呈现与就绪清单的范围，不影响闭包计算（闭包始终按全图求）。
- **去环**：图必须无环；若来源要求互为前置，按 `conflict_rules` 归并为并列节点，不留环。
- **包外前置**：C00 计入闭包但标 `external`——`missing` 会把「读者侧前置未具备」与「包内概念未装载」分开呈现。

## 6. 序冲突与目录序（本波实测）

材料的**目录序 / 章节序**与**前置序**是两件事，本件把这条差别做成可复现判据（§4 `orderings` + 求值器 `--order` 校验，复现命令与实测数字如下）：

| 序 | 复现命令 | 范围 | 违反边（实测） | 读法 |
|---|---|---|---|---|
| cmu-mlsys 讲序 | `python scripts/ai_domain_closure.py --order cmu-mlsys` | 13 个概念 | **0** | 合法线性化：该边集与一条独立来源相容（强证据） |
| aisystem-module-order 目录序 | `python scripts/ai_domain_closure.py --order aisystem-module-order` | 15 个概念 | **5** | 目录序把框架 / 自动微分 / 计算图排在编译器之后，而编译器前端优化必须踩在计算图上 |
| design-guide-chapter-order 章节序 | `python scripts/ai_domain_closure.py --order design-guide-chapter-order` | 25 个概念 | **1** | 教学序把可靠性（13 章）排在评测（14 章）之前，而护栏（C41）依赖评测信号（C40）→ 违反边 1（`C40 → C41`） |

违反边判定范围 = **该序列自身出现的概念之间的边**（序列未含的概念不参与判定，故数字只对该序列可读，不可跨序列比较）。
结论：**结构类来源（课程目录 / 指南章节）是可读性排序，不得当前置序使用**——这正是「依赖闭包型知识域」必须显式声明偏序、而不是抄一份目录的理由。

## 7. 溯源与许可

| 图例键 | 来源 | 取回内容 | 许可与署名 |
|---|---|---|---|
| aisystem | 开源课程《AI 系统》（Infrasys-AI） | 五大模块 + 24 子单元目录；「AI 系统 = 算法 × 框架 × 体系结构」 | Apache-2.0，Copyright 2018-2023 ZOMI |
| cmu-mlsys | CMU 15-442/642 Machine Learning Systems | 逐讲 slides 文件名序（01 课程导论 … 19 mega-kernel） | 课程页公开；仅取序，不引用课件内容 |
| cmu-dlsys | CMU 10-414/714 Deep Learning Systems | notebook 实现序（自动微分 → NN 库实现 → 硬件加速 → 结构族 → 生成模型） | 同上 |
| cs2023 | ACM/IEEE-CS/AAAI CS2023 | 17 个 Knowledge Area 名单（AL/AR/AI/DM/…/SF） | 课程报告公开；仅引用 KA 名单 |
| tvm / mlir / dlc-survey / flash-attention / zero / orca / vllm | 论文锚点（见 §4 图例） | 标题、作者与年份级事实 | 各按原页声明；本件不摘录论文段落 |
| guide-* | AI 系统设计指南（20 章）｜`github.com/ombharatiya/ai-system-design-guide` | **章节与子章的覆盖面**（标题级结构），用作应用栈概念与分支结构的证据 | MIT License |
| prompt-libs | 公开 Agent 系统提示词合集（`dontriskit/awesome-ai-system-prompts` 等） | 仅取「提示 / 上下文工程是独立知识面」这一结构事实 | MIT 及其余合集许可不一；本件不复制其文本，不入本图内容 |
| iis-osint | OSINT 情报整合系统｜`github.com/SleepySoft/IntelligenceIntegrationSystem` | 管线阶段结构（采集 → 清洗 → 向量化 → 检索 → 聚合 / 相似度跳转） | Apache-2.0 |

> 纪律：外部资料在本件只承担**内容与序的证据**角色；概念定义、图层、闭包口径与别名表均为本件自撰，不复制外部仓库文本。结构类来源只提供覆盖面证据（见 §4 `conflict_rules` 第 4 条）。

## 8. 已知缺口（诚实边界）

- CS2023 只取到 **Knowledge Area 名单页**，未取 KA 之间的前置表——故 C00 → C01 的边标为「课程序列」而非「已证前置」。
- 应用栈（C25–C47）的边以**结构类证据 + 本件自撰**为主：指南章节序提供覆盖面与教学序，不单独充当实现级前置证据；待有实现类证据再收窄。
- `C24` 的 `inferred` 部分（对齐与幻觉维度）与 `C45`（模式 / 反模式）同属高抽象节点，前置边只保留已能举出实例的几条。
- 本件是**内容资产**：门禁校验其可寻址与可溯源（check23 / check32 资产面），但**不校验图内部一致性**（无环 / 无悬空 / 闭包正确）——该缺口属判据面，记档于 `results/audit/docs_audit-50-ai-domain.md` §六 与 `results/audit/docs_audit-51-ai-domain-deepen.md`。
