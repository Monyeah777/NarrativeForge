# NarrativeForge · 文档生成工坊（规范驱动）

<!-- nf:locales --> 语言 / Languages：**中文** · [English](README.en.md) · [日本語](README.ja.md)

[![门禁 ci-verify](https://github.com/Monyeah777/NarrativeForge/actions/workflows/ci-verify.yml/badge.svg)](https://github.com/Monyeah777/NarrativeForge/actions/workflows/ci-verify.yml)

**NF 终端（TUI）演示** —— 全屏人机入口（纯标准库）；菜单与动作是 `nf` CLI 真命令的受控调用方。
键位按顶尖终端约定：`Tab` 切面板、`↑↓` 在当前面板内移动、`/` 过滤、`?` 看键位。

```
┌ NF TUI v1.0.0 · NarrativeForge 内容契约层 ───────────────────────────────────────────────────┐
│仓库 NarrativeForge · 能力区 9                                    焦点 动作 · 就绪（0 项待办）│
├────────────────────────┬─────────────────────────────────────────────────────────────────────┤
│  能力区 1/9            │▍ 动作 · 环境自检（2）                                               │
│▸ 0 环境自检（2）       │❯ 只读体检   nf doctor                                               │
│  1 一键演示世界（1）   │  体检（机器面）                                                     │
│  2 需求 → 装配计划（2）│                                                                     │
│  3 全链生产（2）       ├─────────────────────────────────────────────────────────────────────┤
│  4 校验与体检（4）     │  输出 · 1-3/3 · 已跟随                                              │
│  5 货架与资产（4）     │❯ nf doctor   （退出码 0 · 0.42s）                                   │
│  6 管线与模块（4）     │环境自检：Python 3.11 · 仓库在场 · 模块 13 · 管线 3                  │
│  7 帮助与命令面（2）   │✔ 只读体检通过：无缺件 / 无越界 / 无非确定性输出                     │
│  8 写盘表单（13）      │                                                                     │
│                        │                                                                     │
│                        │                                                                     │
│                        │                                                                     │
│                        │                                                                     │
│                        │                                                                     │
│                        │                                                                     │
│                        │                                                                     │
│                        │                                                                     │
│                        │                                                                     │
│                        │                                                                     │
├────────────────────────┴─────────────────────────────────────────────────────────────────────┤
│ Tab 切面板 · ↑↓ 移动 · / 过滤 · Enter 运行 · ? 帮助 · q 退出                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

`python tui/nf.py` 进全屏界面；`--selftest` 跑安全自检，`--demo` 打印上面这帧，`--exec "nf doctor"` 是脚本面
（无 TTY 亦可：`--list-actions --json` 给 agent 列动作与退出码）。命令在后台线程跑，运行中 `Ctrl-C` 只取消该命令；
路径参数过仓库包含性判据、写盘需键入 `yes` 确认、密钥只从环境变量读并遮蔽显示。细节见 `tui/README.md`。

> MIT License · 原创开源 · 衍生/引用请注明来源

NF 是内容契约层——定义“AI 稳定产出长内容”的协议、质量与资产标准；协议本身域中立、模型无关。

**别名与检索词**：NF · NarrativeForge · 叙事工坊 · 内容契约层（content contract layer）· 规范驱动的内容工厂 · 长内容生成协议 · 装配式内容生产 · 模块/管线/资产 · 质量门禁 · 域包 · MCP 接入。

**不是什么**：不是模型、不是提示词模板集、不是某厂商 SDK——协议本体域中立、模型无关；MCP 只是可对接的连接协议之一。

`bash verify.sh`（当前基线见下方生成区「质量凭证」行） · `python scripts/nf.py --version`

## ⚡ 如果你是 AI / Agent

- 这是什么：规范驱动的文档工厂，装模块/管线/资产 → 校验 → 输出。
- 入口链：`AGENT_START.md`（开工）→ `AI_ROUTING.md`（选线）→ `DEEP_DIVE.md`（懂得深）。
- 机器凭证：`bash verify.sh`（当前基线见下方生成区的「质量凭证」行，由 `nf stats --write` 写入）；机器入口清单见 `llms.txt`；语言面见 `README.en.md` · `README.ja.md`（三面的机读事实与语言切换行由 check34 的语言面扫描断言一致；注册表 = `protocol/locales.json`）。
- 要懂 NF 为什么这样设计：读 [DEEP_DIVE.md](DEEP_DIVE.md)。

## 快速开始

作者/开发者，5 分钟：

1. `bash verify.sh`
2. `python scripts/nf.py shell`（交互终端：端壳退役后的人机入口，见 `docs/terminal.md`）
3. `python scripts/nf.py demo`
4. `python scripts/nf.py --help`
5. `python scripts/nf.py doctor`
6. `python scripts/nf.py completion bash`

AI 装配：

1. 读 `AGENT_START.md`
2. 读 `agent_组装指令包_v0.2.md`
3. 按需取 01/02/06/07 与 community 包
4. 组装完整版并过 `##7` 自检
5. `nf assemble "<需求>" --build --dest <目录>`（组装式命令：直接产「完整版」单文件）
6. `nf assemble "<需求>" --check <out.md>`

### 常见问题（FAQ）

- **NF 是什么？** 内容契约层：把「AI 稳定产出长内容」定义成协议 + 质量门 + 资产标准，使产出可装载、可质检、可复现。
- **NF 是 MCP 服务器吗？** 不是必须。协议与资产都是纯文本，克隆或直链即可装载；`nf serve` 才额外提供 MCP 接入面。
- **支持哪些模型？** 模型无关：任何能读文本的 AI 都能按协议装配与装载，不绑定某家模型或某个连接协议。
- **必须联网吗？** 不必。仓库本身就是 markdown 源件；`bash verify.sh` 只读本地，可离线跑。
- **产出怎么判合格？** 判据只来自内部链：verify 门禁（静态可核）+ 五维纵深自评 + 真实战例；外部评价不作为质量背书。
- **怎么引用？** MIT 许可；引用请注明来源，机读元数据见仓库根引用文件（`CITATION.cff`）。

## 能力与资产

<!-- nf:stats:begin -->
**官方核心**：13 模块 · 3 管线（P00 / P01 / P90） · 核心协议件 01–07
**社区规模**：111 登记包 · 363 资产档 · 101 概念图 · 100 域包/1200 细分 · 标准目录 370 条（可达 332 / 不可达 38 · 机构 194 · 206 条依赖边） · 标准绑定 1200 条
**质量凭证**：verify v2.30 · check1-40 · PASS=72（`bash verify.sh` 单入口；期望基线取自 `quality_baseline.EXPECTED_*`） · 馆藏 3 件

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
| 工具 | `docs/mcp.md` · `docs/terminal.md` · `docs/layers.md` · `docs/release.md` · `scripts/nf.py` · `tui/nf.py` · `verify.sh` |
| 接入面 | `integrations/README.md`（MCP / LSP / CLI / TUI / 图书馆 / Skill / npm / Rust / .NET / A2A） |
| 馆 | `library/INDEX.md` · `ROUTES.md` |

## 版本块

| 版本 | 状态 |
|---|---|
| v2.12.0 | 当前（2026-10-05）· 知识层 + 终端线 + 顶尖对标补齐 + 数字资产契约层 |
| v2.11.0 | 已发布 2026-09-10 · world_model 确定性抽象状态契约 + world_slots |
| v2.10.0 | 已发布 2026-09-09 · 45 质量纵深 + 基础层 A 组收口 |
| v2.9.0 | 已发布 2026-09-08 · STRATEGY + 43/44 随波 |
| v2.8.0 | 已发布 2026-09-08 · 41/42 波 C 质量收口 |

详细版本演进见 `CHANGELOG.md` 与 `VERSION-MATRIX.md`。
