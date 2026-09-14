---
name: narrativeforge
description: Use NarrativeForge to assemble long-form content from protocol modules, browse assets and packages, run the nf CLI/MCP, and verify outputs. Use for NarrativeForge tasks; not for generic writing or unrelated repositories.
license: MIT
---

# NarrativeForge 用户技能

NarrativeForge（NF）是**内容契约层**：把长内容生产变成可装载、可质检、可复现的工程。叙事只是官方第一个域包，协议本身域中立、模型无关。本 skill 面向**外部使用者**，覆盖 NF 的核心使用面：装配内容、浏览模块/管线/资产、运行 CLI/MCP、验收产物。

若你的任务是**修改 NF 仓库本身**，先读仓库内 `AGENTS.md` 和 `STRATEGY.md`，本 skill 只负责“怎么用”。

## 快速选路

| 用户想做什么 | 入口 |
|---|---|
| 不安装任何东西，直接让 AI 组装内容 | `AGENT_START.md` → `agent_组装指令包_v0.2.md` |
| 本地跑全部 CLI 功能 | 克隆仓库，`python scripts/nf.py --help` |
| 看模块/管线/资产市场 | `python scripts/nf.py market --list` |
| 一句话需求 → 自动装配计划 | `python scripts/nf.py assemble "<需求>"` |
| 跑 MCP 深度集成 | `nf serve`，详见 `docs/mcp.md` |
| 验收成品或仓库状态 | `python scripts/nf.py assemble --check <成品.md>` / `bash verify.sh` |
| 按编号取馆藏内容 / 检索馆藏 | `nf library search "<关键词>"` · `nf library show <编号>`（MCP：`library_search`/`library_read`，资源 `nf://repo/library/{编号}`） |
| 验证馆藏条目没被换过 | `nf library receipts --entry <编号>`（本地折叠 inclusion proof 到全馆根） |
| 给馆藏条目加签名锚 | `nf library attest <编号> --key-file <密钥>` → `nf library verify --key-file <密钥>` |
| 让别人独立验证馆藏 | `python scripts/nf_verify.py --entry <编号>`（读者侧，纯标准库，不依赖 NF） |
| 检查一条管线跑不跑得通 | `nf pipeline dryrun --pipeline <管线.md>`（抽象执行 → 执行图；hard 缺陷与 advisory 分列） |
| 让指令档走机器面（有 MCP 走 MCP，派发失败即停） | `nf driver <工作流>`（真源 `protocol/driver.json`；指令档头部 `DRIVER OVERRIDE` 块） |
| 查协议件版本史 / supersede 链 | `nf rfc`（`protocol/rfc_index.json`；01=NF-0001 … 07=NF-0004） |
| 取可发布的最佳实践包 | `nf patterns ls` · `nf patterns show <id>` · `nf patterns for <文件>`（真源 = 各包 frontmatter，适用面/证据须仓库内可证） |
| 给 AI 产物跑分 / 多跑比对 | `nf bench run --case <用例> [--model <名>]` · `nf bench compare <runs.json>` |
| 看服务端点契约形状 | `nf endpoint`（`status: proposed`——服务本体未实现，契约只固定形状） |
| 一键发布前体检 | `nf conformance`（16 契约 → Merkle 根 + verdict）· `nf release` · `bash verify.sh` |

详细步骤见 `references/quickstart.md`、`references/commands.md`、`references/assembly.md`。

## 核心能力总览

- **装配**：从协议层 01–07 与 `community/` 领域包取模块、管线、资产，组成单文件完整版 `.md`。
- **CLI**：`scripts/nf.py` 是统一入口，覆盖 `run / assemble / market / asset / library / pipeline / module / render / serve / conformance / approve / sig / attest / score / lint / lsp / license / telemetry / doctor / release / worldmodel / driver / rfc / patterns / bench / endpoint` 等。
- **图书馆机器面**：条目 frontmatter = 单一真相源（OKF 借鉴），INDEX/ALIAS 为投影；正文级检索、生命周期流转、回执单根（MMR）。
- **可验证性**：`nf conformance` 产 Merkle 根封缄的一致性报告（16 契约）；`nf approve` 写内容绑定批准记录（对象一改即失效）。
- **治理声明与机器面**：`protocol/CONFORMANCE.md` 是一致性**声明**（符合哪些规范版本 + scope 白名单 + 显式排除清单，版本逐条与真源比对）；01/02/06/07 带 RFC 版本史头（`nf rfc`）；指令档带 `DRIVER OVERRIDE` 块（有 MCP 走 MCP、派发失败即停、禁止回退成文本步骤）；`patterns/` 是实践包货架；`nf bench` 是对 agent 产物的五维确定性跑分台；`protocol/endpoint_contract.json` 固定（未实现的）服务端点契约形状。
- **MCP**：`nf serve <mcp.json 快照>` 提供标准 stdio JSON-RPC 运行时。
- **质检**：`verify.sh`、`assemble --check`、`assemble --rounds`、`worldmodel --run`、`asset verify` 等构成内部验收链。
- **世界模型**：`protocol/WORLD_MODEL.md` + `protocol/world_slots.json`，可用 `nf worldmodel --walk/--run` 验证确定性状态契约。

## 使用铁律

- **零编造**：模块号、资产键、依赖、版本拿不准就留空并注明，不要猜。
- **内部验收优先**：先跑对应 check / verify，再交付；外部项目只是机制参考，不作为 NF 质量背书。
- **引用真实件**：装配时按仓库真实文件取内容，不凭训练记忆复述协议。
- **产物自包含**：完整版输出应为单个 `.md`，另一个人或 AI 拿到即可按产物内的装载指引开跑。

## 阅读顺序

1. `references/quickstart.md` — 安装 skill、克隆仓库、环境自检、最快跑通。
2. `references/assembly.md` — AI 装配完整流程与出口自检。
3. `references/commands.md` — CLI 命令族与典型示例。

## 停止条件

- 删除、覆盖、破坏性操作先说明并等待用户确认。
- 外部实测/发布/tag 只在用户明确要求时执行；不要自行扩展任务范围。
