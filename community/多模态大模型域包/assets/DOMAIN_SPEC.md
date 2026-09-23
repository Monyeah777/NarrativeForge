<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 多模态大模型

> 用途：本域包的**内容资产与口径面**——把「多模态大模型」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
> 资产键：`DOMAIN_SPEC`｜机读同源面 = `outputs/DOMAIN_SPEC.json`（双源一致由 check32 output_forms 断言；**本表是唯一人读真相，JSON 是它的机读投影**）。
> **内容档位**：authored（逐条撰写，含领域专属判据与权威锚）。

## 1. 口径纪律

1. **定义可判定**：每条细分的定义必须能回答「什么算做对/做错」，不允许只给形容词。
2. **判据可机检**：每条细分给出可写进校验器的判据（字段 / 范围 / 词表 / 一致性）。
3. **锚可复核**：每条挂一个外部权威锚（规范 / 论文 / 参考实现），URL 与可达性实测记于 `STANDARDS_ANCHORS`。
4. **失效模式显式**：写清该细分最常见的错法——它是质检单，不是介绍页。
5. **口径不合并**：不同细分不共用同一条判据文本；相似即拆细。

## 2. 细分口径表（12 条）

| 条目键 | 细分 | 定义口径 | 可机验判据 | 常见失效模式 | 主锚（域口径标准） | 辅锚（产出承载标准） |
|---|---|---|---|---|---|---|
| `A02-01` | 图文对齐与对比学习 | 用对比目标把图像与文本映射到同一表示空间的口径：正负样本构造、温度系数、批内负样本策略。 | 必须声明 batch_negatives（是否用批内负样本）、temperature（正数）、以及检索指标口径（R@k 的候选集大小）；缺候选集大小即口径未定。 | 用不同候选集大小的 R@1 直接横向比较；温度未记录导致分数不可复现。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（eng｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A02-02` | 视觉编码器接入 | 视觉主干的选择与冻结策略口径：patch 大小、输入分辨率、是否分层取特征。 | 声明 backbone_id、patch_size、input_resolution、trainable（frozen|partial|full）四项，均须确定取值。 | 只写「用 ViT」不给分辨率与 patch 大小导致结果不可比；解冻策略未记录导致训练异常归因错误。 | `w3c-svg2` SVG 2（form｜✓） | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） |
| `A02-03` | 跨模态投影层 | 连接视觉与语言空间的投影结构（线性 / MLP / Q-Former）与对齐阶段口径。 | 声明 projector_type（linear|mlp|qformer）、输出 token 数（正整数）、是否分两阶段（先对齐后指令）。 | 跳过对齐阶段直接指令微调造成模态鸿沟；投影层规模未记录导致显存估算失真。 | `w3c-svg2` SVG 2（form｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `A02-04` | 交错图文输入 | 多图多文交错序列的编码口径：图像 token 插入位置、门控交叉注意力与序列长度上限。 | 声明 interleave 结构（每图 token 数）+ 门控方式 + 序列长度上限（token 数）；缺上限即判为会静默截断。 | 交错序列长度上限未声明导致长图序列被静默截断；每图 token 数不定导致成本不可估。 | `mlcommons-croissant` Croissant 数据集元数据（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A02-05` | 音视频统一建模 | 同一模型处理语音与文本（乃至视频帧）的统一 token 化口径与模态标识。 | 声明每个模态的 modality tag token 与 tokenizer 共享/分离策略；音频须给采样率与帧移（ms）。 | 缺模态标识导致跨模态混淆；采样率未归一化造成训练与推理不一致。 | `oci-image` 镜像清单（iface｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `A02-06` | 多模态指令数据 | 多模态指令数据构造口径：图像-指令-回答三元组的来源、许可与重复度。 | 数据卡须给三元组计数、每源许可、以及 image_repeat_ratio（同图多指令占比，0–1 数值）。 | 同图造大量指令导致对评测集过拟合；未标许可导致数据不可发布。 | `commonmark` CommonMark 0.31.2（form｜✓） | `ietf-json-schema` JSON Schema 2020-12（data｜✓） |
| `A02-07` | 模态缺失鲁棒性 | 模态缺失（缺图 / 缺音 / 缺文）时系统的可降级口径与测试要求。 | 必须声明 missing_modality_policy（reject|degrade|impute 三选一）并给出缺失模态的实测降级幅度（数值 + 基准名）。 | 缺失时静默用占位符而非显式降级；无降级幅度实测却在文档里写「鲁棒」。 | `frictionless-table` Table Schema（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A02-08` | 多模态幻觉 | 多模态幻觉的口径与检测方式（对象存在性、属性、关系三类幻觉）。 | 声明幻觉检测方法（polling / 人工标注 / 规则）与 hallucination_rate（0–1 数值）+ 基准名；三类幻觉须分列。 | 只报总体幻觉率不分三类；用同一批问题自评自测。 | `mlcommons-croissant` Croissant 数据集元数据（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A02-09` | 图文评测基准 | 图文评测基准的口径：基准版本、切分、评分脚本与候选集。 | 基准四要素：benchmark_id + version、split（val/test 是否公开）、scorer（脚本 + 版本）、候选集规模。 | 用 val 调参后报 val 分数；评分脚本版本未记录导致跨报告不可比。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（eng｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A02-10` | 视觉定位与引用 | 视觉定位与引用（referring / grounding）的判定口径：框的匹配阈值与输出格式。 | 声明 IoU 阈值（如 0.5）、框格式（xyxy|xywh|归一化）、以及指标（Acc@IoU / F1）。 | IoU 阈值与框格式未声明导致数字不可比；只给「定位正确」而不定阈值。 | `w3c-svg2` SVG 2（form｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `A02-11` | 多模态 Agent | 多模态 Agent 的工具调用与状态口径：可观测状态、工具集与失败恢复。 | 声明 tool_set（枚举）、state_schema（字段名与类型）、以及失败恢复策略（retry|fallback|abort）三选一。 | 工具失败无恢复策略导致静默错误；状态字段未定型导致回放不可复现。 | `mcp` Model Context Protocol（iface｜✓） | `ietf-json-schema` JSON Schema 2020-12（data｜✓） |
| `A02-12` | 任意分辨率与切图策略 | 任意分辨率输入的处理口径：原图尺寸上限、切图策略（切片数与重叠）与拼接方式。 | 声明 max_pixels（整数）、tile_count（切片数）、overlap（像素）与拼接策略；缺任一项即判分辨率口径未定。 | 对超大图静默降采样却宣称原分辨率；切片重叠未声明导致边界目标漏检。 | `mlcommons-croissant` Croissant 数据集元数据（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`extraction`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `多模态大模型:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `多模态大模型:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
