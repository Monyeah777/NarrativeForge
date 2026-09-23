<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 大语言模型

> 用途：本域包的**内容资产与口径面**——把「大语言模型」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
> 资产键：`DOMAIN_SPEC`｜机读同源面 = `outputs/DOMAIN_SPEC.json`（双源一致由 check32 output_forms 断言；**本表是唯一人读真相，JSON 是它的机读投影**）。
> **内容档位**：authored（逐条撰写，含领域专属判据与权威锚）。

## 1. 口径纪律

1. **定义可判定**：每条细分的定义必须能回答「什么算做对/做错」，不允许只给形容词。
2. **判据可机检**：每条细分给出可写进校验器的判据（字段 / 范围 / 词表 / 一致性）。
3. **锚可复核**：每条挂一个外部权威锚（规范 / 论文 / 参考实现），URL 与可达性实测记于 `STANDARDS_ANCHORS`。
4. **失效模式显式**：写清该细分最常见的错法——它是质检单，不是介绍页。
5. **口径不合并**：不同细分不共用同一条判据文本；相似即拆细。

## 2. 细分口径表（12 条）

| 条目键 | 细分 | 定义口径 | 可机验判据 | 常见失效模式 | 可扩展标准（绑定） |
|---|---|---|---|---|---|
| `A01-01` | 基座模型选型与对比 | 在给定任务族与预算约束下选定基座模型，并给出可复核的对照口径（能力 / 许可 / 上下文 / 部署成本四项齐备）。 | 选型单必须含四字段：license_id（合法 SPDX 表达式）、context_limit（正整数 token）、benchmark_scores（≥2 个基准 + 各自版本号）、cost_per_1k_calls（数值 + 单位）；缺一即口径未定。 | 只用榜单排名决策而忽略许可与上下文限制；混用不同榜单版本导致数字不可比。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A01-02` | 模型规模与架构 | 参数量、层数、隐层宽、注意力头数与激活参数的口径，含 MoE 的「总参数 / 激活参数」区分。 | 参数表须给 total_params 与 active_params（MoE 必填；稠密模型两者相等）并注明是否含嵌入层；两值均为正整数且 active ≤ total。 | 把 MoE 总参数量当作计算量；把词表嵌入算进计算参数造成成本高估。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A01-03` | 分词器与词表 | 子词切分算法与词表规模口径（归一化、特殊符号、字节回退），它决定 token 计数与上下文预算。 | vocab_size 必须等于实际 tokenizer 长度；normalization 与 byte_fallback 两项取值显式登记（none/nfkc 等枚举）。 | 用字符数近似 token 数做上下文预算；多语言场景未标 byte_fallback 导致计数系统偏差。 | `w3c-skos` SKOS 词表（W3C） |
| `A01-04` | 训练数据配比与质检 | 语料来源、去重、污染检测与配比的口径，含许可与个人信息边界声明。 | 数据卡须给 source 清单（每源 license）、dedup_ratio（0–1 数值）、contamination_check（基准名 + 命中率）；三项缺一即数据口径未定。 | 缺污染检测使评测分数不可比；去重只在单源内做导致跨源重复泄漏。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons） |
| `A01-05` | 上下文窗口与位置编码 | 训练窗口、有效窗口与外推方式（RoPE 缩放 / 插值 / ALiBi）的口径。 | 同时声明 train_ctx 与 effective_ctx；effective > train 时必须附外推方法与长文验证基准名，否则判夸大。 | 把「支持 1M 上下文」当成「在 1M 上可靠」；外推未在长文基准验证。 | `gfm` GFM 扩展（GitHub） |
| `A01-06` | 注意力机制变体 | 注意力实现与稀疏化口径（MHA / MQA / GQA / 滑窗 / 稀疏），直接影响显存与吞吐。 | 必须声明 kv_heads（正整数）与 attn_impl（枚举，如 eager/flash_attention_2）；有窗口者给 window_size。 | 只报总头数不报 KV 头数，导致显存与吞吐估算失真。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons） |
| `A01-07` | 模型能力边界与失效模式 | 该模型在目标域的能力边界与已知失效模式（幻觉 / 长尾 / 格式崩坏 / 拒答边界）。 | 失效清单每条须含 trigger（可复现输入模式）+ observed（可观察行为）+ severity（枚举 低/中/高）；「偶发」类描述不接受。 | 用「偶发」描述失效导致不可复现；把 prompt 敏感问题一律归因于模型缺陷。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A01-08` | 开源与闭源许可条款 | 权重与输出的许可口径（SPDX 表达式）与商用 / 分发 / 衍生三类边界。 | license_id 须为合法 SPDX 表达式；商用 / 分发 / 衍生三项各给 allow|deny|conditional，conditional 须附条件文本。 | 把「开源模型」等同「可商用」；忽略输出内容的使用限制条款。 | `creativecommons` 许可与权利表达（Creative Commons） |
| `A01-09` | 蒸馏与师生训练 | 教师-学生结构与蒸馏目标（logits / 序列 / 中间层）的口径与数据归属。 | 声明 teacher_id、distill_target（枚举 logits|sequence|hidden）、temperature（数值 >0）；教师许可须允许衍生，否则判越界。 | 教师许可禁衍生却产出学生权重；只在 logits 上蒸馏却宣称「能力对齐」。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons） |
| `A01-10` | 模型合并与权重插值 | 合并方法与系数口径（线性插值 / TIES / DARE）及合并后能力面变化的报告要求。 | 合并卡须给 method、source_models（≥2 + 各自许可）、coefficients（和=1 或显式说明），并报告合并前后每个基准的变化（不只平均分）。 | 合并许可不兼容的权重；只报平均分掩盖单基准退化。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A01-11` | 量化格式与权重存储 | 量化位宽 / 分组 / 格式（GGUF / AWQ / GPTQ / INT4 / FP8）与精度-显存权衡口径。 | 声明 quant_scheme、bits（枚举 4|8|16|bf16）、group_size（分组量化必填）与质量变化量（困惑度或基准差值）。 | 只报显存节省不报质量损失；混合精度未标注哪些层保持高精度。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A01-12` | 推理参数与采样策略 | 解码参数口径（temperature / top_p / top_k / 重复惩罚 / 停止条件）与可复现性要求。 | 生成请求须记录 temperature、top_p、seed（若支持）与 stop 条件；同 seed 同参数须可复现，不可复现须显式声明原因。 | 未固定 seed 却宣称「同输入同输出」；temperature 与 top_p 同时激进导致跨系统不可比。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`generation`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `大语言模型:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `大语言模型:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
