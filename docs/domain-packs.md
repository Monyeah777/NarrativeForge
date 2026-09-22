# AI 品类域包（domain packs）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-23

## 是什么

NF 的「域包」= 一个内容域的**口径协议 + 可机验产出 + 装载管线**。本工程按 AI 品类清单
（100 大类 / 1200 细分）逐类建包：每个包把该域的 **12 条细分**写成可判定口径，
并产出**可复算的数**与**可机验的形态面**——不是资料页。

每包固定 16 件生成物：

| 件 | 内容 | 机检档位 |
|---|---|---|
| `protocol.yaml` | 登记三要件①（机读真相） | — |
| `README.md` | 人读速览（含包名 / 管线 / 资产数，双源一致） | — |
| `modules/<码>a_*.md` `modules/<码>b_*.md` | P40 口径登记 + P60 收口派生（机读契约 + 事件载荷） | L2 |
| `pipelines/Pxx_*.md` | 派生自 P00 骨架的九层装配流 | 管线 dry-run 零 hard |
| `assets/CONCEPT_GRAPH.md` | 12 概念前置偏序图（机读块 = 唯一真相） | 图健康六判据 |
| `assets/DOMAIN_SPEC.md` | 12 条细分口径（定义 / 判据 / 失效模式） | 双源一致 |
| `assets/STANDARDS_ANCHORS.md` | 逐条权威锚 + 可达性实测 | 锚状态非 0 |
| `assets/provenance.json` | 资产供应链台账 | 头 ↔ 台账双源一致 |
| `outputs/`（10 面） | 契约 3 / 数据 3 / 可复算 1 / 图表 1 / 图示 2 | **全部 ≥T2** |

## 机验率与「≥95%」口径

**可机验占比 = 该包 `outputs/INDEX.json` 声明的产出面里档位 ≥T2 的比例**，
门槛 **0.95**，由 `check32 domain_packs` 子扫描硬判（低于门槛即 FAIL）。
14 个域包的实测值：**产出面占比 1.0000**（10/10）；
若把 `assets/*.md` 散文面也算进分母，包级比率为 **0.7692**（10 面 / 13 面）——
两个口径都写在映射表与名录里，不混用。

其中 **T4（可复算）** 面是硬要求：域报告由 `outputs/samples/CASES.csv`（确定性合成夹具）
经 `core/domain_metrics.evaluate()` 重算，`check32` 逐字段比对——口径改了没重算就 FAIL。

## 命令

```
python scripts/nf.py domain specs                    # 列域规格与建包状态
python scripts/nf.py domain build --spec A09 --write # 生成/更新一个域包（幂等）
python scripts/nf.py domain verify --spec A09        # 生成物 ≡ 生成器（逐字节）+ 登记三处到位
python scripts/nf.py output verify                   # 全量产出面机检（含 T4 复算）
python scripts/nf.py output meter --write            # 机验率 / 功能面 + 重签基线
python scripts/nf.py register community/<包名> --apply # 投影 registry protocols[]（三要件②③）
```

新增一个域的完整流程（作者侧）：写域规格（12 条细分 × 定义 / 权威锚 / 可机检判据 / 失效模式）
→ 锚可达性实测 → `domain build --write` → `register --apply` → 重签基线（资产行 / golden /
ledger / advisory / 模块签名 / 回执 / conformance）→ `bash verify.sh` 全绿。

## 已建 14 包（A 段模型与能力 + B 段任务类型）

| 域码 | 域包 | 管线 | 度量族（T4 口径） | 细分 |
|---|---|---|---|---|
| A01 | 大语言模型域包 | P09 | generation | 12 |
| A02 | 多模态大模型域包 | P11 | extraction | 12 |
| A03 | 视觉模型域包 | P12 | classification | 12 |
| A04 | 语音识别与合成域包 | P13 | generation | 12 |
| A05 | 音频与音乐生成域包 | P14 | preference | 12 |
| A06 | 视频生成与理解域包 | P15 | retrieval | 12 |
| A07 | 图像生成与编辑域包 | P16 | classification | 12 |
| A09 | 代码大模型域包 | P22 | exact_judgement | 12 |
| A11 | 嵌入与检索表示域包 | P23 | retrieval | 12 |
| A13 | 具身智能与机器人域包 | P24 | exact_judgement | 12 |
| B01 | 文本生成与创作域包 | P17 | generation | 12 |
| B02 | 摘要与信息压缩域包 | P18 | generation | 12 |
| B03 | 机器翻译与本地化域包 | P19 | generation | 12 |
| B04 | 分类与情感分析域包 | P21 | classification | 12 |

A09 / A11 / A13 的顺序由**决策模型**（本地 Laya，热路径）在 12 个候选里选出
（A13 p=0.1989 / A11 0.1547 / A09 0.1324，继续扩面 p=0.8978），
并按「能否落成可复算度量」这一判据落地；冷链路（Jev 契约三步：真伪 → 类别 → 归属）
对本波三条自述断言给出可判定性 p≈0.99 与归属意见。

## 度量族（T4 口径，全部本仓实现、零第三方依赖）

`classification`（P/R/F1/混淆矩阵/ROC-AUC）· `retrieval`（R@k / MRR / nDCG / MAP）·
`extraction`（EM + 字段级 P/R/F1）· `generation`（EM / 字符 F1 / 词集 F1）·
`regression`（MAE/RMSE/R²/MAPE）· `calibration`（ECE/Brier/可靠性桶）·
`agreement`（Cohen's kappa）· `preference`（一致率/胜率）·
`exact_judgement`（pass@1 / pass@k 无偏估计）· `latency_cost`（分位时延/成本）·
`drift`（PSI）· `contract_compliance`（合规率/缺字段分布）。
每个族的公式与边界处理写在 `core/domain_metrics.py` 的 docstring 与单测里。

## 边界（不宣称）

- **样例是合成夹具**：域报告是「口径可复算」的证明，不是真实模型/系统能力的测量结论。
- **锚只作口径参照**：外部规范/论文/仓库登记入口与可达性，不复制文本、不作质量背书。
- **覆盖 14/100 类**：其余 86 类未建包（清单与队列见内部档案）。域包**不宣称完备**。
- 不可达锚如实记 ✗（并给替代锚），不假装可达。
