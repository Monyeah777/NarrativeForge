<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 视频生成与理解

> 用途：本域包的**内容资产与口径面**——把「视频生成与理解」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
> 资产键：`DOMAIN_SPEC`｜机读同源面 = `outputs/DOMAIN_SPEC.json`（双源一致由 check32 output_forms 断言；**本表是唯一人读真相，JSON 是它的机读投影**）。

## 1. 口径纪律

1. **定义可判定**：每条细分的定义必须能回答「什么算做对/做错」，不允许只给形容词。
2. **判据可机检**：每条细分给出可写进校验器的判据（字段 / 范围 / 词表 / 一致性）。
3. **锚可复核**：每条挂一个外部权威锚（规范 / 论文 / 参考实现），URL 与可达性实测记于 `STANDARDS_ANCHORS`。
4. **失效模式显式**：写清该细分最常见的错法——它是质检单，不是介绍页。
5. **口径不合并**：不同细分不共用同一条判据文本；相似即拆细。

## 2. 细分口径表（12 条）

| 条目键 | 细分 | 定义口径 | 可机验判据 | 常见失效模式 |
|---|---|---|---|---|
| `A06-01` | 文生视频 | 文生视频的口径：分辨率与帧率、时长上限、评估维度（画质 / 时序 / 语义一致）。 | 声明 resolution（宽×高）、fps、max_duration_s 与 eval_dims（三者分列），缺一即口径未定。 | 只报画质不报时序一致性；用短片段成绩代表长视频能力。 |
| `A06-02` | 图生视频 | 图生视频的口径：参考帧数量、首帧严格度与运动幅度控制。 | 声明 ref_frames（数量与位置）、first_frame_strict（true|false）、motion_control（none|camera|trajectory）。 | 首帧不严格却宣称「图生视频保真」；运动幅度未控导致评测集不可比。 |
| `A06-03` | 视频编辑与重绘 | 视频编辑与重绘的口径：编辑类型（局部 / 全局 / 时序）、掩码来源与一致性约束。 | 声明 edit_scope（local|global|temporal）、mask_source（手工|模型|自动）与 consistency_loss（有|无 + 权重）。 | 编辑后未做时序一致性检查导致闪烁；掩码来源未声明使复现不可能。 |
| `A06-04` | 视频超分与修复 | 视频超分与修复的口径：退化模型（模糊 / 压缩 / 噪声）、放大倍数与时间一致性。 | 声明 degradation_model（枚举 + 参数）、scale_factor（整数）、temporal_consistency_metric（如 tOF/tLP）。 | 退化模型未声明导致 PSNR 不可比；缺时间一致性指标掩盖闪烁。 |
| `A06-05` | 镜头分割与关键帧 | 镜头分割与关键帧的口径：切换类型（硬切 / 渐变）、判定阈值与关键帧选择规则。 | 声明 transition_types（hard|gradual）、threshold（数值）与 keyframe_rule（等间隔|内容自适应）。 | 只测硬切却在真实素材（含渐变）上宣称可用；阈值不同导致召回不可比。 |
| `A06-06` | 长视频时序一致性 | 长视频时序一致性的口径：一致性指标、窗口长度与漂移度量方式。 | 声明 consistency_metric（枚举）、window_s（窗口长度）与 drift_measure（主体 / 背景 / 光照分列）。 | 只在短窗口内测一致性；主体漂移与背景漂移混为一个数字。 |
| `A06-07` | 动作可控生成 | 动作可控生成的口径：控制信号（骨架 / 深度 / 轨迹）、控制强度与保真权衡。 | 声明 control_signal（pose|depth|trajectory）、control_strength（0–1）与 fidelity_tradeoff 报告方式。 | 只报可控性不报保真损失；控制强度未声明导致不可复现。 |
| `A06-08` | 视频字幕与描述 | 视频字幕与描述的口径：描述粒度（片段 / 全片）、时间对齐要求与指标（CIDEr / SPICE）。 | 声明 caption_granularity（clip|video）、temporal_alignment（required|none）与指标（CIDEr|SPICE 等）。 | 片段级字幕当全片摘要；指标与切分不同导致跨报告不可比。 |
| `A06-09` | 视频问答 | 视频问答的口径：问题类型分布、时序依赖程度与答案形式（开放 / 多选）。 | 声明 q_type_dist（类型分布）、temporal_dependency（yes|no 标注）与 answer_form（open|mc）。 | 多选题成绩当开放问答能力；时序依赖未标注导致「单帧即可答」混入统计。 |
| `A06-10` | 视频检索 | 视频检索的口径：查询模态、候选库规模与指标（R@k / mAP）口径。 | 声明 query_modality（text|image|video）、gallery_size 与 metric（R@k / mAP）+ 是否取平均。 | 候选库规模不同直接比 R@1；多模态查询混在一张表里。 |
| `A06-11` | 口型同步与数字人驱动 | 口型同步与数字人驱动的口径：驱动信号（音频 / 文本）、同步指标（LSE-C / LSE-D）与身份保持。 | 声明 driving_signal（audio|text）、sync_metric（LSE-C|LSE-D|人工）与 identity_metric（如 ID 相似度）。 | 只报同步不报身份漂移；用同一人脸库自测自评。 |
| `A06-12` | 视频生成评测 | 视频生成评测的口径：分布级指标（FVD）、逐样本指标与评测集规模。 | 声明 distribution_metric（FVD 等）、per_sample_metrics（清单）、eval_set_size（≥1000 建议）与随机种子数。 | 用极小的评测集报 FVD；单次采样不报方差导致结论不稳。 |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`retrieval`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `视频生成与理解:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `视频生成与理解:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
