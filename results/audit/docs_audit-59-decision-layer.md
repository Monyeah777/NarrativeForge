---
id: AUD-0011
title: 决策层端口（typed-decision 三原语）与 Jev / Laya 候选模型实证
date: 2026-09-22
scope: 作者指令「拉取 jev 或 laya 这种模型作为决策层」——名称实证、契约提炼、端口落地、候选声明与拉取脚手架；本件只对本波落地的决策层机制与声明面作实证建档（不含任何真实模型推理结果）
verdict: pass
auditor: 本轮执行者
subjects:
  - verify.sh:e62c132448d12805177e17a45b8c1b51d0fc3717364800b39aa81c9345050d35
  - protocol/decision_layer.json:8429b9ccd1a9ce690f581de96d924034453027eb6c752ac204a25829cdd5e88f
  - protocol/normative.json:0c9c21945def2250462392e5f932a3d30f3b3f9c366b4f67cbdec45f9329c943
  - protocol/data_contracts.json:2888c0e45d0a0a67303d1ba69bf271509d7690679546a1b696ce2c372f4d24eb
  - desktop/src/core/decision_layer.py:4105c5e1b61adcc5a0b8b49568ec38df05705c2a02f2cdbb4d3f3c109b94aa99
  - desktop/src/core/receipts.py:afc48b24b00775b04b67200055d954c5ad735eff980921da9571e87ee13f169f
  - desktop/src/core/doc_hygiene.py:d44fc429edeed9e556e00d380053473ba89448a94eac7fb12880b72f11e72adb
  - desktop/tests/test_decision_layer.py:785d68441b202b9ab208e86df7a34644207cb3b992818f57325e09f0b2f8dc54
  - scripts/nf.py:b72ff59088f3c063f2283cc249e2054dde10c2ba2ba2031ec5bcdd0d807135c2
  - scripts/pull_decision_model.py:f9344c0acb2a3e2761681dd2aff2b7f257153f8674e5d7582df9b0738220d347
  - docs/decision-layer.md:46cd91d13c1b98120318b6aff5d720fc3abe22541de8b1b1762db57a0e8dbeeb

---

> 签收位：本件**未填 `accepted_by`/`accepted_at`**——验收签收属作者动作，执行者不自签。
> subjects = 本波承重件十一件（门禁 / 决策层声明 / 两份登记册 / 端口模块 / 回执覆盖面 / 文档分类表 / 单测 / CLI / 拉取脚手架 / 对外文档）；任一件再改，本件结论即失效须重审。
> **口径**：subjects **不含派生物**——`protocol/RECEIPTS.json` 每次重签都会变，绑进审计只会制造假失效；
> 它由 check35 回执门自证（协议层回执件数 49 在本件正文里作证据引用）。

## 一、名称实证（先求证，不猜）

「jev」「laya」都查到真实模型（HuggingFace API + GitHub 检索实测）：

| 名称 | 落点 | 性质 |
|---|---|---|
| `laya` 系 | `convaiinnovations/laya`（apache-2.0 · ModernBERT-large 421M · 1823 likes）· `laya-multilingual`（mmBERT-base 322M）· **`laya-typed-decisions`**（421M · ctx 1024） | **非自回归 System-1 决策模型族**（typed-decisions / calibrated-decisions / routing 标签） |
| `jev` 系 | `ZefanCai/Open-Jev-9B`（apache-2.0 · Qwen3.5-9B 的 **LoRA + 决策头**）· `com-kotobalabs/open-jev-deberta-v3-large` | 同为 typed-decision，带 `/v1/systemone` 服务口径 |
| 排除 | `mizoreww/laya-mlx`(3972★) 是 MLX 端口；`receptron/laya`(181★) 与决策无关；LayaAir 是游戏引擎 | 与"决策层"无关，不入候选 |

## 二、契约提炼（决定怎么接，而不是抄）

两者共用同一套类型化决策原语（各自模型卡实证）：`choice`（候选集概率 + argmax）/ `noul`（是非概率）/
`score`（有序等级分布 + 期望值）；**非自回归**（只评调用方给的候选、不生成正文）、
**服务不执行动作**、概率以 proper scoring rule 训练（故有 `calibrated` 语义）。

## 三、本波交付

| 类 | 件 | 要点 |
|---|---|---|
| 声明 | `protocol/decision_layer.json` | 三原语 + 应答契约（概率和 ≈1 / 长度对齐 / argmax 在候选集内 / `meta.non_gate`）+ 3 适配器（只有 `stub` 声明 `in_gate_path`）+ 3 候选（含来源/许可/实证/`pulled=false`）+ 5 条边界；**按登记三要件入册**：`normative.json` + `data_contracts.json`（quality_rule=**check33**）+ `receipts.py` 覆盖面（48 → **49 件**） |
| 端口 | `desktop/src/core/decision_layer.py` | 纯标准库：形状校验（请求/应答双向）· 离线确定性 `stub` · `systemone-http`（Jev/Laya 系本地服务）· `openai-json`（聊天模型，`calibrated=false`）· `fingerprint` 可回放 · **任一失败 → `abstained` + reason（fail-closed）** |
| 入口 | `nf decide` | `--dry-run`（面体检）/ `--adapter` / `--endpoint` / `--json`；stub 走门禁口径、外部适配器为非门禁任务 |
| 脚手架 | `scripts/pull_decision_model.py` | 候选/许可/实证可列；**默认只打印 argv（不经 shell）**；`--run --yes` 才下载；缺 `hf` CLI 即 fail-closed 给修复指引 |
| 测试 | `desktop/tests/test_decision_layer.py`（12 例） | 声明完整 / 只有 stub 在门禁路径 / stub 确定性与 `calibrated=false` / 请求形状三负例 / 应答形状四负例（概率和、argmax、漏答、non_gate）/ fail-closed 三路 / 拉取脚手架四条 |
| 文档 | `docs/decision-layer.md` | 入 `doc_hygiene` 三表；含候选实证表与"本机未跑通真实模型"的边界声明 |

## 四、门禁与验收

| 判据 | 结果 |
|---|---|
| `bash verify.sh` | PASS=61 · WARN=0 · FAIL=0（check1-37 不变；决策层面并入 check33 第 15 面） |
| `nf decide --dry-run` | 面体检通过（原语 3 · 适配器 3 · 候选 3 · stub ok） |
| `nf decide --adapter stub` | 三原语各回一条（choice→argmax / noul→p(true) / score→期望值），`calibrated=false` |
| `nf decide --adapter systemone-http`（无 endpoint） | `abstained` + reason ✔ fail-closed |
| `nf receipts` | 协议层回执 **49 件**（新增 decision_layer.json 在册）；`nf conformance` conformant 27/27 |
| 纯度自检（R6） | **本波自查抓掉自己的一处 `subprocess(shell=True)`**（拉取脚手架执行路径）→ 改 argv 列表执行，零 sink 违规 |

## 五、遗留与不宣称

1. **未拉取、未运行任何真实模型**：三个候选 `pulled=false`；本环境不下载数 GB 权重、无 GPU 对照——
   文档与声明**不含任何性能声明**。真实推理结果属外部运行事实，须作者拉取后另立实证。
2. **中文 state 的默认建议**：`laya-multilingual`（322M，100+ 语言）优先于英文专用的
   `laya-typed-decisions`；后者指标更工整但**仅英文**（模型卡自述 specialist、ECE 0.213 过自信）。
3. **`calibrated=true` 不是质量保证**：只表示该系模型以 proper scoring rule 训练；
   用前须在自己的留出集上复核校准（模型卡亦如此建议）。
4. **决策层不进内容生产链**：它只回答被问的类型化问题；正文仍由协议 + 模块 + 资产承担
   （`STRATEGY`「定内容，不定模型」照旧）。
