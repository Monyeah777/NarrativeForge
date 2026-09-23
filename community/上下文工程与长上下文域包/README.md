# 上下文工程与长上下文域包（community 非叙事题材域包 · 上下文工程与长上下文装配流）
> 定位：**AI 品类域包**（清单 C12 · C · AI 工程与运维）——把「上下文工程与长上下文」这一域的 12 条细分协议化：口径可判定、判据可机检、锚可复核，并产出**可复算的域报告**与**可机验的形态面**。
> 协议声明：包根 `protocol.yaml`（01 §6.1 Schema，schema_version "2"）为机读真相，本 README 为人读速览，双源一致（check14 ⑥）。
> 结构：modules/（2 域模块 上下文工程与长上下文:M01、上下文工程与长上下文:M02，类内段编号）｜assets/（**3 内容资产**：概念图 CONCEPT_GRAPH、域口径表 DOMAIN_SPEC、权威锚表 STANDARDS_ANCHORS）｜outputs/（**9 机验产出面**）｜pipelines/P55_上下文工程与长上下文装配流管线.md
> 依赖边界（R1）：只依赖官方核心层（M00 / 通用:M10 / M50 / M80，core_only true），官方模块文件不复制进包。

## 1. 包速览

| 项 | 值 |
| --- | --- |
| 管线 | **P55** 上下文工程与长上下文装配流（九层线性回卷，装配自 P00 通用骨架） |
| 自带模块（本包） | 2：上下文工程与长上下文:M01（P40 口径登记） / 上下文工程与长上下文:M02（P60 收口与派生） |
| 资产 | **3 文件**：`CONCEPT_GRAPH.md`（12 概念前置图）· `DOMAIN_SPEC.md`（12 条细分口径）· `STANDARDS_ANCHORS.md`（逐条权威锚 + 可达性实测）
| 机验产出面 | **9 件**：schema 2 / 数据 2 / 可复算 1（T4）/ 图表 1 / 图结构 2 / 系统卡 1 |
| 度量族 | `contract_compliance`（口径公式见 `docs/domain-packs.md`） |

## 2. 复现命令

| 产物 | 命令（仓库根目录） |
| --- | --- |
| 前置闭包 / 装载序 | `python scripts/ai_domain_closure.py --asset community/上下文工程与长上下文域包/assets/CONCEPT_GRAPH.md --target C12-12` |
| 形态与档位机检 | `python scripts/nf.py output verify` |
| 重渲染产出面 | `python scripts/nf.py output render --write --package 上下文工程与长上下文域包` |
| 重新生成整包 | `python scripts/nf.py domain build --spec C12 --write` |

## 3. 边界与不宣称

- 本包是**口径协议 + 机验产出**类域包：**不提供**模型、不执行推理、不做能力承诺。
- 域报告是**样例集上的口径值**（合成夹具，非真实测量），不是模型评测结论。
- 外部权威锚只作口径参照，**不作质量背书**；本包正文自撰。
