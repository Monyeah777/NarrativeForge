# NarrativeForge · 文档生成工坊（规范驱动）

> MIT License · 原创开源 · 衍生/引用请注明来源

**一句话**：NF 是内容契约层——定义“AI 稳定产出长内容”的协议、质量与资产标准；叙事只是官方第一域包，协议本身域中立、模型无关。

`bash verify.sh`（当前基线见下方生成区「质量凭证」行） · `python scripts/nf.py --version`

## ⚡ 如果你是 AI / Agent

- 这是什么：规范驱动的文档工厂，装模块/管线/资产 → 校验 → 输出。
- 入口链：`AGENT_START.md`（开工）→ `AI_ROUTING.md`（选线）→ `DEEP_DIVE.md`（懂得深）。
- 机器凭证：`bash verify.sh`（当前基线见下方生成区的「质量凭证」行，由 `nf stats --write` 写入）；机器入口清单见 `llms.txt`，英文入口见 `README.en.md`（两份入口的机读事实由 check34 断言一致）。
- 要懂 NF 为什么这样设计：读 [DEEP_DIVE.md](DEEP_DIVE.md)。

## 快速开始

人（作者/开发者，5 分钟）：

1. `bash verify.sh`
2. `python scripts/nf.py demo`
3. `python scripts/nf.py --help`
4. `python scripts/nf.py doctor`
5. `python scripts/nf.py completion bash`

AI 装配：

1. 读 `AGENT_START.md`
2. 读 `agent_组装指令包_v0.2.md`
3. 按需取 01/02/06/07 与 community 包
4. 组装完整版并过 `##7` 自检
5. `nf assemble "<需求>" --check <out.md>`

## 能力与资产

<!-- nf:stats:begin -->
**官方核心**：13 模块 · 3 管线（P00 / P01 / P90） · 核心协议件 01–07
**社区规模**：111 登记包 · 363 资产档 · 101 概念图 · 100 域包/1200 细分 · 标准目录 370 条（可达 332 / 不可达 38 · 机构 194 · 206 条依赖边） · 标准绑定 1200 条
**质量凭证**：verify v2.28 · check1-38 · PASS=66（`bash verify.sh` 单入口；期望基线取自 `quality_baseline.EXPECTED_*`） · 馆藏 3 件

分层：data 148 · eng 38 · form 29 · gov 71 · iface 84 （按标准目录 layer）

> 本区由 `python scripts/nf.py stats --write` 生成，禁止手改；口径与实算真源见 `protocol/repo_stats.json`。
<!-- nf:stats:end -->

## 协议链与文档导航

| 层 | 入口 |
|---|---|
| 方向 | `STRATEGY.md` |
| 协议 | `01_核心协议.md` · `02_联动注册表.md` · `06_Agent执行协议.md` · `07_官方核心出厂与社区预设导航.md` · `protocol/WORLD_MODEL.md` |
| 库 | `03_管线库/` · `04_模块库/` · `05_资产库/` |
| 社区 | `community/README.md` · `community/模板制作指令包.md` |
| AI | `AGENT_START.md` · `AI_ROUTING.md` · `DEEP_DIVE.md` |
| 工具 | `docs/mcp.md` · `scripts/nf.py` · `scripts/verify.sh` |
| 馆 | `library/INDEX.md` · `ROUTES.md` |

## 版本块

| 版本 | 状态 |
|---|---|
| v2.11.0 | 当前（2026-09-10）· world_model 确定性抽象状态契约 + world_slots |
| v2.10.0 | 已发布 2026-09-09 · 45 质量纵深 + 基础层 A 组收口 |
| v2.9.0 | 已发布 2026-09-08 · STRATEGY + 43/44 随波 |
| v2.8.0 | 已发布 2026-09-08 · 41/42 波 C 质量收口 |

详细版本演进见 `CHANGELOG.md` 与 `VERSION-MATRIX.md`。
