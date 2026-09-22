# AI系统域包（community 非叙事题材域包 · AI系统域装配流）
> 定位：**社区非叙事题材域包**（community 第 6 包、第 2 个非叙事域），独占「AI系统」类（01 §6 R2 / 02 §8 第三方协议登记）。本包承载 NF 此前未表达过的一件事：**概念前置依赖 / 闭包**——以概念图资产声明偏序，以「求值 + 排序」两模块把偏序变成可复算产物（前置闭包 / 缺失清单 / 合法装载序）。经本包自带 **P07 管线**装载（R3 装配契约）。
> 协议声明：包根 `protocol.yaml`（01 §6.1 Schema，schema_version "2"，references 空列表）为**机读真相**，本 README 为**人读速览**，双源一致（check14 ⑥ / check15 ⑤）；登记三要件见 02 §8.3。
> 结构：modules/（2 域模块 AI系统:M25、AI系统:M26，类内段编号）｜assets/（**1 内容资产**：概念图 CONCEPT_GRAPH）｜pipelines/P07_AI系统域装配流管线.md
> 机验产出面（v1.2.0）：outputs/（**6 件**：契约 2 / 数据 1 / 可复算 1 / 图示 2）——系统卡（数据形态）、闭包产物（T4 可复算）、概念图两形态（Mermaid / GraphML，确定性派生）；清单元数据 = `outputs/INDEX.json`，形态与档位口径见 `docs/output-forms.md`。
> 依赖边界（R1）：只依赖官方核心层（M00 / 通用:M10 / M50 / M80 共 4 件 core_modules，core_only true）；**不搬移**官方模块入包 default/available 槽（I5 单一真相源）。
## 1. 包速览
| 项 | 值 |
| --- | --- |
| 管线 | **P07** AI系统域装配流（九层线性回卷，装配自官方 P00 通用骨架） |
| 自带模块（本包） | 2：AI系统:M25 前置闭包求值（P40 行为决策位） / AI系统:M26 装载序与就绪门（P60 长期演变位） |
| 官方核心配合件 | 4：M00 数据槽 / 通用:M10 节拍 / M50 主循环 / M80 输出门（本体驻官方核心位） |
| 总装配 | **6 模块**（核心配合 4 + 本包自带 2；references=[] 无跨包引用） |
| references 引用 | 0（无跨包引用） |
| 资产 | **1 文件**：`assets/CONCEPT_GRAPH.md`（概念前置偏序图：**双支 47 概念**（计算与实现栈 25 / 应用与系统设计栈 22）+ 1 包外前置族 + 概念别名表；人读表 / 别名表 / 机器可读块三形态同源） |
| 主轴 | AI系统域：概念图 `CONCEPT_GRAPH`（P40 解析检索词并求闭包）→ M26 拓扑装载序、就绪门与下一步可装载集（P60）→ M80 官方输出门（P80，gate 唯一出口） |
| 输出风格 | M80 官方输出门（gate 唯一出口）；本包产物（闭包 / 缺失清单 / 装载序 / 就绪清单）供装配方与课程排程类消费者读取；概念可用**条目键 / 别名 / 概念名**三种说法检索（如 `C22` = `PagedAttention` = `vLLM`） |
## 2. 模块装载清单（按层，6 = 核心配合 4 + 自带 2）
> 与 pipelines/P07_AI系统域装配流管线.md 的 layers（default 列）严格一致。
| 层 | 挂载（default） | 模块职责 | 归属 |
| --- | --- | --- | --- |
| P40 行为决策 | **AI系统:M25** | 前置闭包求值：读 CONCEPT_GRAPH → `closure(c)` / `missing(c, L)` → PrereqState（concept_closure_ready / prereq_missing） | 本包 |
| P60 长期演变 | **AI系统:M26** | 装载序与就绪门：`toposort` 确定性装载序 + 逐概念就绪门 + 下一步可装载集 `frontier(L)`（load_order_ready） | 本包 |
| P00 / P10 / P50 / P80 | （空跑位） | 由官方核心 M00 / 通用:M10 / M50 / M80 承载，本包不重复挂载 | 核心 |
## 3. 四件产物与复现命令
| 产物 | 说明 | 复现命令（仓库根目录） |
| --- | --- | --- |
| 前置闭包 `closure(c)` | 目标概念的全部前置（含自身与包外前置族） | `python scripts/ai_domain_closure.py --target C22` |
| 缺失清单 `missing(c, L)` | 相对已装载集 L 还差哪些概念 | `python scripts/ai_domain_closure.py --target C22 --loaded C01,C07,C08,C10,C18` |
| 合法装载序 `load_order` | 拓扑序的确定性线性化（并列按 id 升序） | `python scripts/ai_domain_closure.py --target C22 --json` |
| 下一步可装载集 `frontier(L)` | 前置已齐、尚未装载的概念（可按分支过滤） | `python scripts/ai_domain_closure.py --ready-list --loaded C00,C01,C20 --branch app` |
| **机验产出面（数据 / 可复算 / 图示）** | 系统卡、闭包产物（T4：由概念图重算比对）、概念图两形态（Mermaid / GraphML） | `python scripts/nf.py output verify` · `python scripts/nf.py output render --write` · `python scripts/nf.py output meter` |
> 辅助面：`--list`（条目键全表 + 别名）、`--gaps --branch app`（批量前置缺失清单）、`--order <序 id>`（某份讲序 / 章节序对本图的违反边数）、`--check`（图健康度自检，含负例注入）。别名检索示例：`--target RAG` 与 `--target C28` 同解。
> 求值器只读、确定性、零网络（同输入同输出）；实测数字见 `assets/CONCEPT_GRAPH.md` §6、记录见 `results/audit/docs_audit-50-ai-domain.md` 与 `docs_audit-51-ai-domain-deepen.md`。
## 4. 装载命令（Agent 通道）
```
读 community/AI系统域包/README.md → 按 §2 表装载 P07 管线（P40 AI系统:M25 / P60 AI系统:M26）→ 读 assets/CONCEPT_GRAPH.md 机器可读块（双支 47 概念 + 别名表）→ 按 §3 命令取四件产物
```
## 5. 边界与不宣称
- 本包是**机制型非叙事域包**：自带 2 模块 + 1 内容资产；不产出叙事文本，不替代官方 M00/M50/M80 的任何职责。
- 概念图资产是**内容**：门禁校验其可寻址与可溯源（check23 / check32 资产面）；图内部一致性（无环 / 无悬空 / 边有溯源 / 层位合法 / 别名唯一 / 分支完备）已由 **check32 子扫描**（`concept_graph`）硬门覆盖；闭包正确性由 `scripts/ai_domain_closure.py --check` 与本包测试复算。判据面收口记录见 `results/audit/docs_audit-50-ai-domain.md` §二。
- 概念图的来源为**内容与序的证据**（外部课程体系与论文锚点，逐条标注 provenance）；结构借鉴的署名与许可见资产 §6，本包正文自撰、不复制外部文本。
