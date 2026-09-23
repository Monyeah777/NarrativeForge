---
id: AUD-0018
title: AI 品类域包工程（域包工厂 + 14 包 / 168 细分 / 154 机验面 / 16 T4 面）+ 决策模型热冷裁决
date: 2026-09-23
scope: 作者指令「八小时内按 AI 品类清单逐项建域包；参照 AI系统/量化金融两包、**必须深度分析 NF 本体**、保功能性、可检索外部权威、用决策模型（Laya 热路径 / Jev 冷链路）、产出形态覆盖全域、**NF 可机验、可机验率 ≥95%**、缺则从零构建、每项过专业路径与质量验证」——本件记录：工厂机制、14 包落地、机验率口径与实测、决策模型裁决、本波修掉的四处真问题、覆盖边界与队列
verdict: pass
auditor: 本轮执行者
subjects:
  - desktop/src/core/domain_pack.py:59ef53148d9874f130912b25faf704d500981388ec4310f714c4a9752249ae2c
  - desktop/src/core/domain_metrics.py:a870ce5e38e1efb1c4be35407876718c6c3f19cda0bbc40e934433f1f510c397
  - desktop/src/core/output_forms.py:50830a219470f9e3aadfd461c7b45212810cad4a5e4dbcc21810a79d56c85a5e
  - desktop/src/core/quality_depth_scan.py:2af96a08d6b8e0e07e3a86b041507c706c9de1d4609fdbf4f8eae8b4b598b59e
  - desktop/src/core/doc_hygiene.py:ee315d685c82a6e1841aeb7859fb885684a9fa52f856f951e05484201afffc74
  - scripts/nf.py:3484f46ff1fcde7180a6c8fa5a46d8b406181782304140e820a26e83e5bdc54d
  - docs/domain-packs.md:7b61173388a7e6f636d0dedc18e2e2f83a50ba28bb4f2cb3bcb1a6398d3b4b87
  - docs/output-forms.md:98716fc96333cdd1d8e012e307fb3911ead53888672c37a012761f3d41a8db4e
  - desktop/tests/test_domain_pack.py:bd3e36a8e81cd89a4ca4afb785295002cbe7d68fe762b776e816925bafd11ed7
  - verify.sh:f14c8e40f7501a54bd6132ae571492e975bc747c1288d7a7dcdd1929399395f2
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 11 件（工厂、度量引擎、产出形态面、聚合扫描、文档卫生、CLI、名录、两份公开文档、工厂单测、门禁脚本）；**不含派生物**（`protocol/generated/*`、`results/interop/*`、基线台账、域包生成物本体——它们由生成器可复算，绑进来会每次重签即失效）。

## 一、内部差距（开工依据）

1. 清单 100 大类 / 1200 细分要求「逐项建域包」——**手工复制 100 遍 = 每包漂移一处就静默破门禁**；
   仓库当时没有「包工厂」这一层，新增域包的成本与出错率都不可控。
2. 已建 2 个非叙事域包（AI系统 / 量化金融）虽已带机验产出面，但**没有「域内容 → 可复算度量」的通路**：
   域知识仍主要在散文里，功能性靠个别包自带模块，无法规模化。
3. 产物形态层（AUD-0017）给了档位与机验率计量，但**没有「域包必须 ≥95% 可机验」的硬门**。

## 二、机制（从零构建）

| 件 | 作用 | 判据（谁在守） |
|---|---|---|
| `core/domain_pack.py` | 一个域规格 → 16 件生成物（含 9 机验产出面）+ 自动登记 02 §8 / verify DOMAIN / 名录 | `nf domain verify` 逐字节；check14 ⑦；check32 domain_packs |
| `core/domain_metrics.py` | 12 个确定性度量族 + 合成夹具（纯函数、无墙钟/随机） | 15 例单测逐族钉公式；check32 T4 复算 |
| `nf domain build/verify/specs` | 操作面 | `test_nf_cli` 命令面自洽 |
| `protocol/domain_packs.json` | 公开名录（域码/类别/管线/模块/面数/机验占比/规格摘要） | check32 domain_packs |
| `docs/domain-packs.md` | 使用者文档（含 ≥95% 口径与两个比率、边界） | doc_hygiene 四型 |

**可机验率口径（本波定义，写进名录与文档，不混用）**：
`output_face_ratio = 声明产出面中档位 ≥T2 的比例`（硬门 **0.95**）——
实测 **1.0000**（10/10）；`pack_ratio`（把散文资产计入分母）= **0.7692**（10/13），
仅作并列报告。**T4 面为硬要求**：每包必须有 1 个可复算面（域报告），否则 FAIL。

## 三、14 包落地（168 条细分，真内容 + 锚逐条实测）

A01 大语言模型 · A02 多模态大模型 · A03 视觉模型 · A04 语音识别与合成 ·
A05 音频与音乐生成 · A06 视频生成与理解 · A07 图像生成与编辑 · A09 代码大模型 ·
A11 嵌入与检索表示 · A13 具身智能与机器人 · B01 文本生成与创作 · B02 摘要与信息压缩 ·
B03 机器翻译与本地化 · B04 分类与情感分析。

每条细分 = 定义口径（可判定）+ 可机检判据（字段/范围/词表）+ 常见失效模式 + 权威锚；
锚可达性**本机实测**（168 条），不可达/错题者换锚后复测（例：`arXiv` 误命中被标题核出、
ISO 403、GitHub 本机不通 → 换 PyPI / 标准 / 官方文档类可达锚）。锚表逐条记 ✓/✗ 与日期。

度量族分布：generation ×5 · classification ×3 · retrieval ×2 · exact_judgement ×2 ·
extraction/preference ×1（每族的公式与边界在 `core/domain_metrics.py`）。

## 四、决策模型裁决（Laya 热路径 + Jev 契约冷链路；非门禁）

真模型（本地 `laya-multilingual`）：12 个候选域 → 选中 **A13 具身智能与机器人**
（p=0.1989）、次选 **A11 嵌入与检索表示**（0.1547）、**A09 代码大模型**（0.1324）；
`worth_continuing p=0.8978`。三项按模型排序落地（A13/A11/A09 均已建包并过门禁）。
冷链路三步（真伪 → 类别 → 归属）对本波三条自述断言给出可判定性 p=0.9957 / 0.9874 / 0.9914
（归属意见「本波执行者」）——与机制一致：三条断言分别由 `nf domain verify`、
check32 T4 复算、check32 占比门槛守。记录：`.rivet/private_archive/ai_packs/decision_next_domains.json`。

## 五、本波实测修掉的四处真问题（均为门禁抓出）

1. **`nf register --apply` 写 registry.json 为 CRLF**（Windows 文本模式默认）→ 编码卫生 FAIL。
   修法：写入显式 `newline="\n"`（与 AUD-0017 的 CRLF 教训同源）。
2. **事件名跨域重名**：14 个包发布同名事件 → 违「发布方唯一」（check16 ④）。
   修法：事件名按域码命名空间 `<码>_spec_ready|conflict`，并清理 4 条本波自造的死注册。
3. **`check7` 段号正则误命中**：`^### 8\.1` 会把 `### 8.10` 一起吞（域包 ≥10 个即误取在册数，
   实测「校园包 modules 实存 9 ≠ 在册 9」）→ 锚定 `### 8.N `（后随空格）。
4. **AUD-0017 误绑派生件**（`protocol/output_forms_baseline.json`）→ 基线一重签审计即失效；
   修法：subjects 去派生物（口径同 §「审计不绑派生物」）。

## 六、边界与不宣称（重要）

- **覆盖 14/100 类（168/1200 细分）**：其余 86 类未建包，队列（含每类 12 条细分名）在内部档案；
  本波**不宣称**清单已覆盖完。
- **域报告是样例口径值**：夹具为确定性合成数据，证明「口径可复算」，**不是**真实模型能力测量。
- **锚只作口径参照**：登记入口与可达性，未做规范全文比对，不作品质背书。
- 每个包都声明自己的覆盖边界（12 条细分以内），相邻主题不自动继承。
- 外部接触（客户端装载实测）仍按 STRATEGY 封存。

## 七、实测结果

`bash verify.sh` **PASS=61 · WARN=0 · FAIL=0**；`nf conformance` **27/27**；
`nf domain verify` 14/14 逐字节一致；`nf output verify` 154 面全绿（含 16 个 T4 复算面）；
unittest 含本波 15 例工厂/口径单测全绿；顺带收益：事件载荷类型覆盖 **55.7% → 75.4%**。
