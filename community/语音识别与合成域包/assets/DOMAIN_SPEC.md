<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 语音识别与合成

> 用途：本域包的**内容资产与口径面**——把「语音识别与合成」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
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
| `A04-01` | 端到端 ASR 声学建模 | 端到端 ASR 的建模口径：声学前端、词表单位（字符 / BPE / 词）、解码方式与语言模型融合。 | 声明 acoustic_frontend（帧长/帧移 ms）、token_unit（char|bpe|word）、decoding（greedy|beam+LM）三项。 | 用不同语言模型融合强度比较 WER；前端帧移未记录导致流式与离线数字不可比。 | `w3c-webaudio` Web Audio API（form｜✓） | `ietf-json-schema` JSON Schema 2020-12（data｜✓） |
| `A04-02` | 语音活动检测与切分 | 语音活动检测与切分的口径：判定阈值、最短语音段、最大静音切分与尾部保留。 | 声明 vad_threshold、min_speech_ms、max_silence_ms、tail_padding_ms 四个数值。 | 切分过碎导致识别上下文丢失；尾部静音截断导致尾音丢失。 | `w3c-webaudio` Web Audio API（form｜✓） | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） |
| `A04-03` | 说话人分离与识别 | 说话人分离与识别的口径：说话人数量假设、聚类阈值与评测指标（DER / EER）。 | 声明 num_speakers（已知|自动）、clustering_threshold、metric（DER|EER）+ 评分帧长与主说话人定义。 | 重叠语音不显式声明（collar 处理不同）导致 DER 不可比；说话人数假设不同直接比 EER。 | `onnx` ONNX（opset 扩展）（iface｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A04-04` | 方言与口音适应 | 方言与口音适应的口径：适配数据规模、微调范围与基线对照。 | 声明 adapt_data_hours（小时数）、adapt_scope（frontend|encoder|decoder|full）、以及未适配基线的同集 WER。 | 只报适配后 WER 不报基线；把数据泄漏（测试口音出现在适配集）当适配收益。 | `ietf-json-schema` JSON Schema 2020-12（data｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `A04-05` | 噪声与远场鲁棒 | 噪声与远场鲁棒的口径：信噪比范围、混响时间与增强前端是否进入链路。 | 声明 snr_db（范围）、t60_s（混响时间）、enhancement（none|denoise|dereverb）三项，并给各噪声条件下的 WER。 | 只报干净集 WER；增强前端的训练集泄漏（同噪声同说话人）导致虚高。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（eng｜✓） | `w3c-prov-o` PROV-O 溯源本体（gov｜✓） |
| `A04-06` | 流式低延迟识别 | 流式低延迟识别的口径：块大小、延迟定义（首字延迟 / 稳定延迟）与回退策略。 | 声明 chunk_ms、latency_metric（first_partial|stable_hypothesis）、以及允许的回退窗口（ms）。 | 用整句离线 WER 宣称流式性能；延迟定义未声明导致与产品 SLA 对不上。 | `onnx` ONNX（opset 扩展）（iface｜✓） | `cncf-cloudevents` CloudEvents 1.0（iface｜✓） |
| `A04-07` | TTS 声学模型与声码器 | TTS 声学模型与声码器的口径：声学特征、采样率、声码器类型与推理步数。 | 声明 acoustic_feature（mel 维数 + 帧移）、sample_rate（Hz）、vocoder（id + 版本）、inference_steps。 | 采样率不一致造成听感对比无效；声码器版本未记录导致音质回归无法归因。 | `onnx` ONNX（opset 扩展）（iface｜✓） | `w3c-tabular-data` Tabular Data Model (CSVW)（data｜✓） |
| `A04-08` | 音色克隆与声音转换 | 音色克隆与声音转换的口径：参考音频时长、是否需要授权声明、相似度评测方法。 | 声明 ref_audio_sec（参考时长）、consent（授权声明文件名）、similarity_metric（MOS|SECS）与评分人数。 | 无授权就克隆音色（合规红线）；用自评 MOS 代替第三方听测。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（eng｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A04-09` | 韵律与情感控制 | 韵律与情感控制的口径：控制维度（音高 / 时长 / 能量）、控制粒度与标注来源。 | 声明 control_dims（枚举）、granularity（utterance|word|phoneme）、以及情感标注来源（人工|模型）。 | 标注来源是模型却报成人工标注；控制粒度不同导致控制精度不可比。 | `onnx` ONNX（opset 扩展）（iface｜✓） | `mermaid` Mermaid 图语言（form｜✓） |
| `A04-10` | 多语种混说 | 多语种混说（code-switching）的口径：语种切换点标注、语种识别粒度与指标口径。 | 声明 switch_point_annotation（人工|规则）、lid_granularity（句|词|字符）与指标（WER|MER）。 | 用单语测试集宣称混说能力；切换点标注口径不同导致 MER 不可比。 | `ietf-json-schema` JSON Schema 2020-12（data｜✓） | `vega-lite` Vega-Lite v5（form｜✓） |
| `A04-11` | 语音评测与打分 | 语音评测与打分的口径：评分维度、评分人一致性、以及分数映射（原始分 → 报告分）。 | 声明 score_dims（发音/流利度/完整度等枚举）、inter_rater_agreement（如 Cohen kappa）、score_mapping（分段函数或分位映射）。 | 无评分人一致性就报分数可靠；分数映射未公开导致跨版本不可比。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（eng｜✓） | `ietf-json-schema` JSON Schema 2020-12（data｜✓） |
| `A04-12` | 字幕时间轴对齐 | 字幕时间轴对齐的口径：对齐单位、允许偏差与时间基准。 | 声明 align_unit（词|字符|句）、tolerance_ms（允许偏差）与 time_base（音频起点定义）。 | 不声明容差就把手工校对与自动对齐混比；音频起点未定义导致整体偏移。 | `oci-image` 镜像清单（iface｜✓） | `ietf-ixdtf` IXDTF (RFC 9557)（data｜✓） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`generation`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `语音识别与合成:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `语音识别与合成:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
