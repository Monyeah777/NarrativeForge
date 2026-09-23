<!-- nf-asset: key="DOMAIN_SPEC" version="1.0" status="active" -->
# 域口径表 · 音频与音乐生成

> 用途：本域包的**内容资产与口径面**——把「音频与音乐生成」这一域的 12 条细分写成可判定的口径（定义 / 可机验判据 / 常见失效模式），并逐条挂权威锚。
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
| `A05-01` | 音乐生成与编曲 | 音乐生成与编曲的口径：生成条件（文本 / 和弦 / 旋律）、时长上限、采样率与结构控制。 | 声明 condition_type（text|chord|melody）、max_duration_s、sample_rate（Hz）、structure_control（none|段标记）。 | 不报生成时长上限就把短片段质量当整曲质量；采样率不一致导致听测不可比。 | `w3c-webaudio` Web Audio API（W3C） |
| `A05-02` | 伴奏与人声分离 | 伴奏与人声分离的口径：分离声道数、评测指标（SDR / SIR / SAR）与混合方式。 | 声明 stems（声道枚举 2|4|6）、metric（SDR|SIR|SAR 组合）、以及测试混合来源（同源|跨源）。 | 用同源混合测试再宣称真实录音性能；只报 SDR 不报干扰与伪影分量。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons） |
| `A05-03` | 乐谱与 MIDI 理解 | 乐谱与 MIDI 理解的口径：输入格式（MIDI / MusicXML / 图像谱）、量化精度与拍速基准。 | 声明 input_format、quantization（如 1/16 音符）、tempo_basis（BPM 来源）与调号处理。 | 量化精度不同导致音符数不可比；拍速基准缺失造成节奏类结论失真。 | `onnx` ONNX（opset 扩展）（Linux Foundation） |
| `A05-04` | 风格与情绪标签 | 音乐风格与情绪标签的口径：标签体系来源、多标签与单标签设定、以及评测切分。 | 声明 tag_taxonomy（体系来源）、multilabel（true|false）、split（artist-wise|random）。 | 随机切分让同一艺人跨集，指标虚高；标签体系不同却比较 mAP。 | `ietf-json-schema` JSON Schema 2020-12（IETF/JSON Schema） |
| `A05-05` | 音频修复与降噪 | 音频修复与降噪的口径：退化类型（噪声 / 削波 / 丢帧）、输入信噪比与是否端到端。 | 声明 degradation_type（枚举）、input_snr_db（范围）、以及是否端到端（end_to_end true|false）。 | 只报降噪后 PESQ 不报引入的伪影；训练噪声与测试噪声同源。 | `w3c-webaudio` Web Audio API（W3C） |
| `A05-06` | 声音事件检测 | 声音事件检测（SED）的口径：事件类别体系、时间分辨率（段级 / 帧级）与重叠处理。 | 声明 event_taxonomy、temporal_resolution（segment|frame + 时长）、overlap_policy（allow|exclude）。 | 段级与帧级指标混比；重叠事件被排除却宣称覆盖真实场景。 | `cncf-cloudevents` CloudEvents 1.0（CNCF） |
| `A05-07` | 空间音频与混音 | 空间音频与混音的口径：声道布局、渲染方式与听测环境声明。 | 声明 channel_layout（mono|stereo|5.1|ambisonic）、renderer（HRTF|amplitude panning）、listening_env（耳机|音箱）。 | 不同渲染方式直接比主观分；听测环境未声明导致结论不可复现。 | `opengeospatial` OGC 标准（含 GeoJSON/3D Tiles）（OGC） |
| `A05-08` | 音效合成 | 音效合成的口径：条件输入（文本 / 参考音频）、时长与可控性（音色 / 空间）。 | 声明 condition（text|audio-ref）、max_duration_s、controllable_dims（音色|空间|时长）。 | 无法控时长却宣称音效库可替代；参考音频来源未标许可。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons） |
| `A05-09` | 版权与采样合规 | 版权与采样合规的口径：训练数据许可、采样来源与输出权属声明。 | 声明 data_license（每个来源的 CC/商业许可枚举）、sample_provenance（可追溯标识）与 output_ownership 声明。 | 训练集含未授权采样却在输出端宣称可商用；许可链未逐源登记。 | `creativecommons` 许可与权利表达（Creative Commons） |
| `A05-10` | 音乐推荐与歌单 | 音乐推荐与歌单的口径：候选集规模、排序目标与离线 / 在线指标分离。 | 声明 candidate_size、objective（CTR|时长|完播）、offline_metric 与 online_metric 各自口径。 | 用离线召回率替代在线完播结论；候选集规模未声明导致可比性断裂。 | `w3c-webaudio` Web Audio API（W3C） |
| `A05-11` | 歌声合成 | 歌声合成的口径：音素 / 音高输入、发音时长控制与音质评测方法。 | 声明 input_representation（phoneme+note|lyrics+melody）、duration_control（none|explicit）与评测方法（MOS|A/B）。 | 自评 MOS 无听测人数与筛查标准；时长控制缺失导致翻唱对不上拍。 | `w3c-webaudio` Web Audio API（W3C） |
| `A05-12` | 音频质量评测 | 音频质量评测的口径：客观指标（PESQ / STOI / SI-SDR）与主观听测协议。 | 声明客观指标清单 + 版本口径、主观协议（人数 / 筛查 / 量表）、以及退化条件（采样率、码率）。 | 用不同采样率下的 PESQ 比较；主观听测人数不足且无筛查标准。 | `mlcommons-bench` MLPerf 基准（可扩展场景）（MLCommons） |

## 3. 机读投影契约

- `outputs/DOMAIN_SPEC.json`：本表的结构化等价物（`kind = nf-domain-spec/1`）；键集与本节**双向一致**（多一键或少一键即 FAIL）。
- `outputs/REPORT.json`：域内度量的**可复算报告**（T4）——由 `outputs/samples/CASES.csv` 按声明的度量族重算，check32 逐字段比对。
- 度量族：`preference`（口径公式见 `docs/domain-packs.md`）。

## 4. 与模块的关系

- `音频与音乐生成:M01`（P40）：读本表登记口径，校验判据齐备性，越界即发口径冲突事件。
- `音频与音乐生成:M02`（P60）：收口度量报告与形态产出，保证「口径 → 数 → 图」三段同源。
