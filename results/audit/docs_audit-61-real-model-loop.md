---
id: AUD-0013
title: 真模型接入构建回路并落定两项——laya-multilingual 本地跑通（CPU）· 判据按实测修正 · 两项类型缺口闭环
date: 2026-09-22
scope: 作者指令「执行」（承接「让这些模型替我干活，来构建 NF」）——真拉取 laya-multilingual、写 NF 口径本地服务、用真模型驱动回路挑活并落笔两项、按实测修正概率判据；本件只对可复现的本地运行事实建档
verdict: pass
auditor: 本轮执行者
subjects:
  - scripts/serve_decision_model.py:130920912feb38b20cd463f1181fa39f4e6fba45b0e4ad059e1dc74a49bfa4f7
  - desktop/src/core/decision_layer.py:44f194ec3f2803a35669f6bdec179685bbf6c42fe43856bf11d8fae469f6e80f
  - desktop/src/core/purity_scan.py:1c9bcf3c0396ec43a55df57e558acdf13fd9896cd37413c422347177de851cc8
  - protocol/decision_layer.json:8429b9ccd1a9ce690f581de96d924034453027eb6c752ac204a25829cdd5e88f
  - community/通用核心基础包/modules/M94_通用节拍桥.md:5c9605e3becbec64e87d5d3ab32b7e25a22150d949d3b8cf787eaa1e01f0e2c4
  - community/校园西幻轻混组合包/modules/M92_轻混装配执行.md:1e261dcc10d0b7134d8194f6e548ecae0d7230d9ba8e258d48825627503360d6
  - docs/decision-layer.md:85ac1dc81c879cf98a15a0c089ba1c825c67649fe3ee431a9172336c09b04314
  - desktop/tests/test_decision_layer.py:40521a5b641df92f0c4b4f28386c2a4118e5bee44ae050f924a3206fc74d3bc9
---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 本波承重件八件（服务 shim / 决策端口 / 纯度登记 / 决策层声明 / 两个被落笔的模块 / 对外文档 / 单测）。
> **口径**：subjects 不含派生物（回执 / 生成物等由 check31/check33/check35 自证）。

## 一、真模型接入（可复现步骤与实测数字）

| 步 | 事实 |
|---|---|
| 装运行时 | `python -m pip install laya` → **laya 0.3.5**（依赖 torch 2.14.0 / transformers 5.17.0 / huggingface_hub 1.32.0；装到用户级 site-packages） |
| 拉权重 | `snapshot_download('convaiinnovations/laya-multilingual', local_dir='.rivet/scratch/models/laya-multilingual')` → **0.63 GB**（`.rivet/` 内，`.gitignore` 已加 `checkpoints/`、`*.safetensors`、`*.gguf` 防误提交） |
| 起服务 | 新增 `scripts/serve_decision_model.py`：**NF 口径 shim**（stdlib HTTP；`laya` 为**软依赖**并登记进 `purity_scan.SOFT_IMPORTS`）；把 NF 的 `choice.options` → Laya `criteria` 字典、`score.levels` → `criteria` 列表、`noul` → 仅 instructions；返回概率归一 + `confidence` + `usage` |
| 首跑（真值） | 604 input tokens；`next_item` p=0.6067（选中 `TB-001`）· `risk` 期望 1.29 · **`gate_safe` noul=0.9857**，CPU 单次预测 ~数秒（加载 ~25s） |

## 二、判据按实测修正（真模型第一次就撞上自家门禁）

真模型回传的概率**四舍五入到 4 位**（和 = 0.9999），被 NF 原来的 `|Σp−1| ≤ 1e-6` 判据判为不合规 →
`abstained`。这不是模型的错，是**判据没考虑真值量的量化**：

| 处置 | 内容 |
|---|---|
| 容差 | `PROB_TOL` **1e-6 → 1e-3**（4 位小数的量化误差上界），注释里写明实证来源与日期 |
| 归一化 | 适配器侧 `normalize_probs()` 先归一再入档，并把**原始概率和**记进 `meta.raw_prob_sums`（**判据放松、证据不放松**） |
| 附带上报 | `meta.confidence`（模型自报置信度）与 `meta.usage`（token 用量）随决策一起留档 |

## 三、真模型驱动的两轮落笔（决策 → 落笔 → 验收 → 收口）

| 轮 | 决策（真模型/stub） | 落笔（worker） | 结果 |
|---|---|---|---|
| 1 | stub `WO-c9618c9f6e8a` → `TB-001:beat_tick.buffered` | M94 补机读事件契约（`origin=string` / `buffered=boolean`） | 载荷覆盖 **42.9%→44.0%**；backlog **104→102**；io_types 35.4%→41.7% |
| 2 | **真模型 `WO-870f096918d6`** → `TB-003:campus_anonymous_gift.source_package`（p=0.275 · risk 期望 **2.15** · risk_probs [0.032, 0.785, 0.183] · **gate_safe=0.9852**） | M92 补机读事件契约（`item`/`source_package`/`origin` 定型为 string；`qty`/`quality`/`tick` 透传数值） | 载荷覆盖 **44.0%→45.6%**；backlog **102→99**；io_types **41.7%→43.1%** |

两轮的门禁反应一致且被遵守：`module-signature` 报边界漂移 → **显式重冻结**（48 模块），旧审计摘要重绑；
`bash verify.sh` 最终 **PASS=61 · WARN=0 · FAIL=0**，`nf conformance` **27/27**，unittest **981 例全绿**。
收口件：`.rivet/private_archive/work_orders/WO-*.close.json`（两份，均 landed · PASS=61 · 27/27）。

## 四、声明面同步（状态不许含糊）

`protocol/decision_layer.json: candidates[laya-multilingual]` 置 `pulled: true` 并附 `local`
（怎么拉 / 体积 / 运行时 / 由谁服务 / 真跑记录含 tokens、选中项、置信度与那条判据教训）；
门禁同步加判据：**`pulled` 必须为布尔，且 `pulled=true` 必须自带 `local.how/runtime/served_by`**
（拉取是显式动作，状态要可追溯）——原有的"候选默认未拉取"测试随之升级为"已拉取须带本地证据 +
至少保留未拉取候选（拉取按模型逐个授权）"。

## 五、遗留与不宣称

1. **只在 CPU、单机、单模型上跑通**：本轮验证 `laya-multilingual`（322M）在 CPU 上可用；
   未测 `laya-typed-decisions`（英文专用）与 `open-jev-9b`（需 GPU + 专属 loader），二者仍 `pulled=false`。
2. **不做质量宣称**：模型给的是**选择与概率**，其校准性按模型卡自述仍偏自信（ECE 0.213 那个检查点；
   本轮用的多语 checkpoint 未做校准复核）——用前须在自有留出集上复核，本件不作效果声明。
3. **服务是本地开发件**：`serve_decision_model.py` 只监听回环、不入门禁路径；关掉进程即回到 stub 口径
   （回路与门禁都不依赖它）。
4. **决策仍不等于落笔**：两轮的实际改动都由 worker（本轮执行者）完成；模型只提供排序与概率。
