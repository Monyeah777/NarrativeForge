# FDE 交付样例（可跑 · 可复算）

> 定位：证明「NF 是 FDE 的 AI infra 中游标准」——一次完整交付从 **brief** 走到 **证据包**，全程本地、确定性、无网络。
> 栈位说明见 [`../fde-stack.md`](../fde-stack.md)。本样例是那条契约的一次真实行走。

## 一、样例对象

| 项 | 值 |
|---|---|
| 域包 | `community/AI系统域包`（系统卡 + 概念图 48 节点 + 闭包产物 + 自带装配流 P07） |
| 交付形态 | 技术文档（techdoc）——交付物 `evidence/deliverable.md` |
| 客户侧输入 | [`brief.md`](brief.md)（客户需求） |
| 照做步骤 | [`run.md`](run.md)（命令原文 + 期望输出 + 退出码） |
| 证据 | `evidence/`：`deliverable.md` · `gates.txt` · `result.jsonl` · `manifest.json` |

## 二、怎么跑（两条命令）

```bash
python scripts/fde_sample_run.py --run     # 跑一遍并落证据（幂等：可重复跑）
python scripts/fde_sample_run.py --check   # 逐字节比对证据与当前仓库状态（防样例腐烂）
```

## 三、五道门（样例的验收判据）

| 门 | 判据 | 为什么它算「中游」证据 |
|---|---|---|
| G1 | 包内 `outputs/INDEX.json` 声明的产出面全部在场且可解析 | 交付面不是口头承诺，是声明 + 实物 |
| G2 | T2 schema ↔ T3 data 逐对通过 JSON Schema 子集校验 | 客户拿到的产物有契约，不是自由文本 |
| G3 | `assets/CONCEPT_GRAPH.md` 概念图健康（无环 / 无悬空 / 别名唯一 / 分支完备） | 装配前提可机检 |
| G4 | 装配链四件（protocol.yaml + 管线 + 两模块）在场可指认 | 交付过程可被第三方照做 |
| G5 | `nf stats --check` 与 `geo_export.py --check` 同时绿 | 交付所引用的数字与标准锚都是实算生成物 |

**当前实跑结果**（`evidence/gates.txt`）：五门全 PASS——G3 的图规模 48 节点 / 拓扑序 47 / 证据强度 `external`；G5 覆盖 370 条标准锚。

## 四、复算与失败处置

- 任一 `--check` 报 FAIL → 说明仓库状态变了而证据未刷新：重跑 `--run`；若 `--run` 本身报 FAIL（G1–G4），按门名定位（G1 产出面缺失 / G2 契约违规 / G3 图缺陷 / G4 装配链缺件）。
- G5 失败通常意味着自述数字或 GEO 出口落后：先跑 `python scripts/nf.py stats --write` 与 `python scripts/geo_export.py --write`。
- 本样例**不引入新真源**：全部输入来自域包自身产物与协议层声明。
