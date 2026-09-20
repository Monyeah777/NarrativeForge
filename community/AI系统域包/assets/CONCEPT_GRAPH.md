<!-- nf-asset: key="CONCEPT_GRAPH" version="1.0" status="active" -->
# 概念图 · AI 系统域（概念前置偏序）

> 用途：AI系统域包的**前置闭包求值输入面**——把「AI 系统」这一域的概念前置关系声明成一张偏序图（DAG），供前置闭包求值（AI系统:M25）与装载序就绪门（AI系统:M26）消费。
> 资产键：`CONCEPT_GRAPH`｜形态：人读表（§2）+ 机器可读块（§3）双形态同源——**§3 围栏块是唯一机读真相**，§2 表与 §5 校验数字由它导出。
> 来源：本件正文自撰，不从任何外部仓库复制文本；结构（五大模块 / 24 子单元）与序（两门课程的讲序）作为**内容证据**逐条标注在 §6，边级溯源见 §3 `provenance`。
> 许可：本件随 AI系统域包分发（仓库 LICENSE）；结构借鉴来源的许可与署名见 §6。

## 1. 读法

- **概念**：一个可独立装载的知识单元（如「自动微分」「KV cache 分页」），有稳定 id（`C01`–`C24`）与所属能力层。
- **条目键**：概念 id 即条目键——资产键 `CONCEPT_GRAPH` + 条目键（如 `C22`）构成唯一寻址（`asset_get('CONCEPT_GRAPH','C22')`），一概念一键，与其余资产键表同构。
- **前置（prereqs）**：装载该概念**之前必须先具备**的概念——图的边，方向为「前置 → 后继」。
- **层（layer）**：该概念在 NF 九层位（P00–P80）中的合理驻留层，用于装配时定位，**不是**执行顺序。
- **证据（provenance）**：该节点的内容与前置关系来自哪条来源线（§6 图例），`inferred` 表示本件推断、需复核。
- **包外前置（C00）**：只声明存在、不建模块——域包不承担数学/编程/系统基础的教学职能（否则退化为课程包）。

## 2. 条目键表（一概念一键，asset_get 寻址）

| 条目键 | 概念 | 层 | 直接前置 | 证据 |
|---|---|---|---|---|
| `C00` | 外部前置族：数学基础 / 编程与算法 / 计算机系统基础（体系结构·OS·并行） | —（包外） | — | cs2023 |
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
| `C19` | 模型压缩：量化 / 蒸馏 / 剪枝 | P60 | `C10`、`C18` | aisystem |
| `C20` | Transformer 与注意力：结构族、KV cache | P40 | `C08`、`C10` | cmu-mlsys、cmu-dlsys |
| `C21` | 注意力 IO 优化：分块、重算、精确注意力 | P50 | `C20`、`C14` | flash-attention |
| `C22` | 服务调度与批处理：连续批处理、迭代级调度、KV 分页 | P50 | `C18`、`C20`、`C16` | orca、vllm |
| `C23` | Kernel 层推理优化：融合 kernel、mega-kernel | P50 | `C14`、`C18` | aisystem、cmu-mlsys |
| `C24` | 评测与可靠性：吞吐 / 延迟口径、回归基线、对齐与幻觉 | P80 | `C18`、`C22` | cs2023、inferred |

## 3. 机器可读块（唯一机读真相）

```yaml
concept_graph:
  version: "1.0"
  domain: AI系统
  date: "2026-09-20"
  intent: 概念前置依赖的偏序声明（前置闭包求值的输入面）
  closure_rules:
    closure: "closure(c) = {c} ∪ ⋃ closure(p)，p ∈ prereqs(c)（传递闭包）"
    missing: "missing(c, L) = closure(c) − L（L = 已装载概念集）"
    readiness: "readiness(c, L) = (missing(c, L) 为空)"
    load_order: "toposort(G) 的任一线性化即合法装载序（并列节点共享层位）"
    determinism: "同一 (G, L) 下 missing 与 load_order 逐字节可复现"
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
    inferred: 本件推断（无直接来源，待复核）
  external_prereqs:
    - id: C00
      name: 外部前置族：数学基础 / 编程与算法 / 计算机系统基础（体系结构·OS·并行）
      in_package: false
      provenance: [cs2023]
      note: 包外前置，只声明不建模块（域包不承担通识教学职能）
  nodes:
    - {id: C01, name: AI 系统全栈概览：算法 × 框架 × 体系结构, layer: P00, prereqs: [C00], provenance: [aisystem, cmu-mlsys]}
    - {id: C02, name: AI 计算体系：神经网络计算模式、并行度来源, layer: P00, prereqs: [C01], provenance: [aisystem]}
    - {id: C03, name: 芯片基础：CPU/GPU/NPU、SIMT、内存层次, layer: P00, prereqs: [C02], provenance: [aisystem]}
    - {id: C04, name: GPU 体系：SM / warp / 占用率、协作与同步, layer: P10, prereqs: [C03], provenance: [aisystem]}
    - {id: C05, name: 硬件加速实践：算术强度、Roofline、GPU GEMM, layer: P10, prereqs: [C04], provenance: [cmu-mlsys]}
    - {id: C06, name: CUDA 编程：kernel / 共享内存 / 同步 / 访存, layer: P30, prereqs: [C05], provenance: [cmu-mlsys]}
    - {id: C07, name: 深度学习编程抽象：张量、算子、图 vs 即时, layer: P40, prereqs: [C01], provenance: [cmu-mlsys]}
    - {id: C08, name: 自动微分：反向模式、计算图、内存开销, layer: P40, prereqs: [C07], provenance: [cmu-mlsys, cmu-dlsys, aisystem]}
    - {id: C09, name: 计算图：图优化 / 执行 / 控制流表达, layer: P40, prereqs: [C08], provenance: [aisystem]}
    - {id: C10, name: 框架工程：NN 库实现、算子与内存管理, layer: P50, prereqs: [C07, C09], provenance: [cmu-dlsys, aisystem]}
    - {id: C11, name: 传统编译原理：IR / SSA / 优化 / 后端, layer: P30, prereqs: [C00], provenance: [aisystem, mlir]}
    - {id: C12, name: AI 编译器与多级 IR：图级 / 算子级 / kernel 级, layer: P40, prereqs: [C11, C09], provenance: [aisystem, tvm, mlir, dlc-survey], note: 本节点有两个前置（传统编译 + 计算图），单链叙事会隐藏这一点}
    - {id: C13, name: 前端优化：算子融合、常量折叠、布局改写, layer: P40, prereqs: [C12], provenance: [aisystem]}
    - {id: C14, name: 后端与 Kernel 优化：调度、自动调优、多面体, layer: P50, prereqs: [C13, C06], provenance: [aisystem, cmu-mlsys], note: 跨层前置边——不接触硬件（C06）写不出 kernel 优化}
    - {id: C15, name: 分布式训练：数据并行与集合通信, layer: P50, prereqs: [C07, C00], provenance: [cmu-mlsys]}
    - {id: C16, name: 显存与内存优化：激活重算、优化器状态分片, layer: P60, prereqs: [C15, C08], provenance: [zero, cmu-mlsys]}
    - {id: C17, name: 并行训练工程：张量 / 流水并行、MoE, layer: P60, prereqs: [C15, C16], provenance: [cmu-mlsys]}
    - {id: C18, name: 推理系统与引擎：图转换、运行时、调度, layer: P50, prereqs: [C09, C12], provenance: [aisystem]}
    - {id: C19, name: 模型压缩：量化 / 蒸馏 / 剪枝, layer: P60, prereqs: [C10, C18], provenance: [aisystem]}
    - {id: C20, name: Transformer 与注意力：结构族、KV cache, layer: P40, prereqs: [C08, C10], provenance: [cmu-mlsys, cmu-dlsys]}
    - {id: C21, name: 注意力 IO 优化：分块、重算、精确注意力, layer: P50, prereqs: [C20, C14], provenance: [flash-attention]}
    - {id: C22, name: 服务调度与批处理：连续批处理、迭代级调度、KV 分页, layer: P50, prereqs: [C18, C20, C16], provenance: [orca, vllm]}
    - {id: C23, name: Kernel 层推理优化：融合 kernel、mega-kernel, layer: P50, prereqs: [C14, C18], provenance: [aisystem, cmu-mlsys]}
    - {id: C24, name: 评测与可靠性：吞吐 / 延迟口径、回归基线、对齐与幻觉, layer: P80, prereqs: [C18, C22], provenance: [cs2023, inferred]}
  orderings:
    - id: cmu-mlsys
      seq: [C01, C07, C08, C05, C06, C20, C15, C16, C22, C17, C21, C23, C24]
      expectation: 对该 DAG 的违反边数应为 0（合法线性化）
    - id: aisystem-module-order
      seq: [C01, C02, C03, C04, C05, C11, C12, C13, C14, C18, C19, C10, C07, C08, C09]
      expectation: 对该 DAG 存在违反边（目录序是可读性排序，不是前置序）
  conflict_rules:
    - 两条独立来源都要求的序 → 硬前置边（进 prereqs）
    - 仅单源要求的序 → 软前置边（进 prereqs 并在 provenance 标注单源）
    - 互为前置（成环）→ 归并为并列节点并记档，不得留环
```

## 4. 闭包语义（求值口径）

```
closure(c)   = {c} ∪ ⋃ closure(p)      for p ∈ prereqs(c)        # 传递闭包（DAG 保证终止）
missing(c, L) = closure(c) − L                                        # L = 已装载概念集
readiness(c, L) = (missing(c, L) 为空)                                # 是否可装载
load_order(G) = toposort(G) 的任一线性化（确定性：同层按 id 升序）
```

- **确定性纪律**：同一 `(G, L)` 下 `missing` 与 `load_order` 必须逐字节可复现（NF 全局纪律：同输入同输出）；求值器见 `scripts/ai_domain_closure.py`。
- **去环**：图必须是无环的；若来源要求互为前置，按 §5 冲突规则归并为并列节点，不留环。
- **包外前置**：C00 计入闭包但标 `external`——`missing` 会把「读者侧前置未具备」与「包内概念未装载」分开呈现。

## 5. 序冲突与目录序（本波实测）

材料的**目录序**与**前置序**是两件事，本件把这条差别做成可复现判据（§3 `orderings` + 求值器 `--order` 校验，复现命令与实测数字如下）：

| 序 | 复现命令 | 范围 | 违反边（实测） | 读法 |
|---|---|---|---|---|
| cmu-mlsys 讲序 | `python scripts/ai_domain_closure.py --order cmu-mlsys` | 13 个概念 | **0** | 合法线性化：该边集与一条独立来源相容（强证据） |
| aisystem-module-order 目录序 | `python scripts/ai_domain_closure.py --order aisystem-module-order` | 15 个概念 | **5** | 目录序把框架/自动微分/计算图排在编译器之后，而编译器前端优化必须踩在计算图上 |

违反边判定范围 = **该序列自身出现的概念之间的边**（序列未含的概念不参与判定，故数字只对该序列可读，不可跨序列比较）。
结论：**材料源的章节目录是可读性排序，不得当前置序使用**——这正是「依赖闭包型知识域」必须显式声明偏序、而不是抄一份目录的理由。

## 6. 溯源与许可

| 图例键 | 来源 | 取回内容 | 许可与署名 |
|---|---|---|---|
| aisystem | 开源课程《AI 系统》（Infrasys-AI） | 五大模块 + 24 子单元目录；「AI 系统 = 算法 × 框架 × 体系结构」 | Apache-2.0，Copyright 2018-2023 ZOMI |
| cmu-mlsys | CMU 15-442/642 Machine Learning Systems | 逐讲 slides 文件名序（01 课程导论 … 19 mega-kernel） | 课程页公开；仅取序，不引用课件内容 |
| cmu-dlsys | CMU 10-414/714 Deep Learning Systems | notebook 实现序（自动微分 → NN 库实现 → 硬件加速 → 结构族 → 生成模型） | 同上 |
| cs2023 | ACM/IEEE-CS/AAAI CS2023 | 17 个 Knowledge Area 名单（AL/AR/AI/DM/…/SF） | 课程报告公开；仅引用 KA 名单 |
| tvm / mlir / dlc-survey / flash-attention / zero / orca / vllm | 论文锚点（见 §3 图例） | 标题、作者与年份级事实 | 各按原页声明；本件不摘录论文段落 |

> 纪律：外部资料在本件只承担**内容与序的证据**角色。概念定义、图层与闭包口径均为本件自撰；不复制外部仓库文本。

## 7. 已知缺口（诚实边界）

- CS2023 只取到 **Knowledge Area 名单页**，未取 KA 之间的前置表——故 C00 → C01 的边标为「课程序列」而非「已证前置」。
- `C24` 的 `inferred` 部分（对齐与幻觉维度）无直接来源，落盘时保留标注，待有可核来源再收窄。
- 本件是**内容资产**：门禁校验其可寻址与可溯源（check23 / check32），但**不校验图内部一致性**（无环 / 无悬空 / 闭包正确）——该缺口属判据面，记档于 `results/audit/docs_audit-50-ai-domain.md`。
