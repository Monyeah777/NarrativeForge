# 决策层（decide）
> ⛔ 操作指令：阅读即执行——本文含可直接执行的命令与判定，勿当资料阅读。
> 最后更新：2026-09-22

## 是什么

决策层把 NF 里的**选择**（选哪些模块、走哪条管线、这一步该不该继续）写成**类型化问题**，
交给决策模型作答：机制借鉴非自回归 typed-decision 模型的三原语——
**`choice`（候选集上的概率分布 + argmax）/ `noul`（是非概率）/ `score`（有序等级的分布 + 期望值）**，
模型**不生成正文、不执行动作**。

声明真源：`protocol/decision_layer.json`（原语 / 应答契约 / 适配器 / 候选模型 / 边界）。

## 为什么（可核验的三件事）

1. **形状可核验**——问题与答案都有 schema：模型不得自造候选、不得只回自然语言；
2. **决策可审计**——每个决策带概率、适配器、模型与延迟（可回放：同输入同指纹）；
3. **失败不猜**——适配器不可用 / 超时 / 输出不合 schema → `status=abstained` + `reason`（fail-closed）。

架构纪律（`STRATEGY.md`「定内容，不定模型」）：本层是**端口**，模型在端口之外——
换模型不改协议、不改内容资产；`stub` 之外的一切适配器**不入门禁路径**。

## 怎么用

问题文件（JSON）：问题是**类型化**的，候选集由调用方给：

```json
{
  "pipeline": {"type": "choice", "instructions": "选择装配管线",
               "options": ["P02 校园情感流", "P03 西幻生存流"]},
  "need_multilingual": {"type": "noul", "true_hints": ["中文", "多语"]},
  "risk": {"type": "score", "levels": ["低", "中", "高"]}
}
```

```bash
# 离线确定性（门禁 / CI / 演练口径，calibrated=false）
python scripts/nf.py decide --state-text "雨天走廊 校园情感 中文" \
  --questions .rivet/scratch/decide/questions.json --adapter stub

# 面体检（声明完整 + stub 确定性 + fail-closed）
python scripts/nf.py decide --questions .rivet/scratch/decide/questions.json --dry-run

# 接本地 typed-decision 服务（Jev / Laya 系；非门禁）
python scripts/nf.py decide --adapter systemone-http \
  --endpoint http://127.0.0.1:8791/v1/systemone \
  --state <state.txt> --questions <questions.json>

# 候选模型：列 / 打印拉取命令 / 真拉取（默认只打印，不擅自下载）
python scripts/pull_decision_model.py --list
python scripts/pull_decision_model.py --candidate laya-multilingual --serve
python scripts/pull_decision_model.py --candidate laya-multilingual --run --yes
```

## 候选模型（2026-09-21 取回模型卡与配置的实证）

| 候选 | 来源 | 许可 | 规模 / 形态 | 语言 | 实证要点 | 边界 |
|---|---|---|---|---|---|---|
| `laya-typed-decisions` | `hf:convaiinnovations/laya-typed-decisions` | apache-2.0 | ModernBERT-large · 421M · ctx 1024 | en | accuracy 0.766 / Brier 0.062 / **ECE 0.213**；四 workflow 专用 | 英文专用；作者自述 specialist，勿作静默默认；选项建议 <20 |
| `laya-multilingual` | `hf:convaiinnovations/laya-multilingual` | apache-2.0 | mmBERT-base · 322M · ctx 1024 | **100+ 语言（含中文）** | 同族多语面 | 中文 state 应优先此变体而非英文专用 checkpoint |
| `open-jev-9b` | `hf:ZefanCai/Open-Jev-9B` | apache-2.0 | Qwen3.5-9B 的 **LoRA 适配器 + 决策头**（非自回归） | 取决于 base | 只评调用方给的候选；`/v1/systemone` 服务口径；需 base 精确 revision `c2022362…` | 需 GPU + Open-Jev loader；`AutoPeftModel` 直调不实现该接口 |

三者 `pulled=false`：**NF 不替作者决定下载数 GB 权重**（`pull_decision_model.py` 默认只打印命令，
`--run --yes` 才执行）。

## 判据（门禁 · check33 第 15 面）

1. **声明完整**：三原语齐全、适配器带 `kind/in_gate_path/calibrated/note`、候选带
   `source/license/evidence/pulled`、`boundaries` 非空；
2. **门禁只许 stub**：任何 `in_gate_path=true` 的非 stub 适配器即 FAIL（门禁必须离线确定）；
3. **stub 确定性**：同输入两次结果逐字段一致，且自称 `calibrated=false`；
4. **fail-closed**：未登记适配器 / 缺 endpoint / 请求不合规 / 输出不合 schema → `abstained` + `reason`；
5. **应答契约**：概率和 ≈1（容差 1e-6）、长度对齐候选数、`argmax` 落在候选集内、
   `meta.non_gate=true`。

## 边界（不宣称）

- **不执行动作**：决策层只给决策与概率，动作仍由人/上层流程决定；
- **不生成正文**：非自回归；内容由内容契约层（协议 + 模块 + 资产）承担；
- **概率不是证书**：`calibrated=true` 只表示模型系以 proper scoring rule 训练；
  Laya 系自述仍过自信（ECE 0.213），**用前须在你自己的留出集上复核**；
- **本机未跑通任何真实模型**：本仓只完成端口、声明、拉取脚手架与离线 stub 的验证；
  真实模型的推理结果属外部运行事实，未经作者拉取与运行前不作任何性能声明。

## 构建回路（让决策模型替你干活 · 2026-09-22）

**先说清能力边界**：Laya 是编码器分类模型、Open-Jev 是非自回归决策头 ——
**两者都不会写代码或正文**。所以回路的职责分工是：

```
决策模型（挑活/判风险/定能不能安全做）  →  生成式 worker（人 / Codex / 生成式模型）落笔  →  NF 门禁验收
```

待办真源是**公开声明件**（不另造队列）：`protocol/type_backlog.json`（未定型事件字段）+
`protocol/pipeline_advisory.json`（管线 advisory）。

```bash
python scripts/nf.py workloop --list --top 10        # 看候选面（决策层能挑的活）
python scripts/nf.py workloop --top 5                # 决策层挑出一项 → 打印工单
python scripts/nf.py workloop --top 5 --write         # 工单落内部档案 .rivet/private_archive/work_orders/
python scripts/nf.py workloop --close WO-xxxx --outcome landed --gate "PASS=61" --note "…"
```

工单自带：目标 / 条目 / 证据 / 落点提示 / **完成判据** / **验收命令**；决策元信息含
所选概率、风险期望、`gate_safe` 概率与适配器（`stub` 时 `calibrated=false`，只是排序信号）。

四条不可协商（写进 `protocol/decision_layer.json: workloop.non_negotiables`，门禁判）：
① 决策层不生成内容；② 工单只落内部档案（计划类产品内部消化，公开仓只收结果 + audit）；
③ 落笔方必须是 worker；④ 验收只认 `verify.sh` / `nf conformance`。

实测（本仓 2026-09-22）：待办 **206 项**（未定型字段 104 + advisory 102），
stub 工单确定性可复现（`WO-c9618c9f6e8a`，选择 `TB-001:beat_tick.buffered`）。
