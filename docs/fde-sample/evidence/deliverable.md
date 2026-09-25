# FDE 交付样例 · AI 系统域包 → 技术文档交付物

> 本文件由 `python scripts/fde_sample_run.py --run` 生成（生成物，禁止手改）。
> 交付形态：技术文档（techdoc）。中游位置：NF 契约层夹在「模型/传输协议」与「客户交付物」之间。

## 1. 交付对象（系统卡摘要）

- 系统：AI系统域包（NF-AI-DOMAIN-PACK · v1.1.0 · domain-package）
- 用途：把「AI 系统」这一域的**概念前置关系**协议化：给出概念图资产（47 个包内概念 + 1 个包外前置族）、前置闭包求值（M25）与装载序就绪门（M26）两个模块，使任何客户端可按闭包装载该域知识。
- 模型无关：True · 上游模型：—
- 限制：概念图覆盖率以 v1.1 声明的双支（compute/app）为界，未覆盖的相邻领域必须显式登记为新概念，不得默认继承；边级溯源中 provenance=inferred 的边属本件推断，未经外部复核——装配备注为『待复核』；闭包求值只判**结构前置**（是否已装载），不判概念被理解的程度；包外前置族 C00 不随包交付，装载方须自备前置
- 风险框架：NIST AI RMF 1.0

## 2. 概念闭包（装配前提）

- 目标：`C42` · 闭包大小 23 · 装载序长度 47
- 概念节点 48 · 拓扑序 47 · 证据强度 `external`

## 3. 交付面清单（包自持声明）

| 面 | 形态 | 档位 | 角色 |
|---|---|---|---|
| `outputs/schemas/SYSTEM_CARD.schema.json` | json-schema | T2 | schema |
| `outputs/SYSTEM_CARD.json` | system-card | T3 | data |
| `outputs/schemas/CONCEPT_CLOSURE.schema.json` | json-schema | T2 | schema |
| `outputs/CONCEPT_CLOSURE.json` | concept-closure | T4 | functional |
| `outputs/charts/CONCEPT_DAG.mmd` | mermaid | T3 | diagram |
| `outputs/CONCEPT_DAG.graphml` | graphml | T3 | diagram |

## 4. 装配步骤（FDE 侧照做）

1. 装载域包声明：`community/AI系统域包/protocol.yaml`
2. 求前置闭包：模块 `M25_前置闭包求值`（本样例结果见 §2）
3. 过装载序就绪门：模块 `M26_装载序就绪门`
4. 走本包管线：`community/AI系统域包/pipelines/P07_AI系统域装配流管线.md`
5. 交付出面：按 §3 清单产出（T2 schema / T3 data）

## 5. 验收判据（本样例实跑的四道门 + 中游层核验）

| 门 | 判据 | 证据 |
|---|---|---|
| G1 | 声明产出面全部在场且可解析 | `evidence/gates.txt` |
| G2 | T2 schema ↔ T3 data 逐对合规 | `evidence/gates.txt` |
| G3 | 概念图健康（无环/无悬空/别名唯一/分支完备） | `evidence/gates.txt` |
| G4 | 装配链四件在场可指认 | `evidence/gates.txt` |
| G5 | 中游出口成立（`nf stats --check` + `geo_export --check`） | `evidence/result.jsonl` |

> 复算：`python scripts/fde_sample_run.py --check`（逐字节比对本目录证据与当前仓库状态）。
