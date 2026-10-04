# NarrativeForge · Document Generation Workshop (spec-driven) — English mirror

[![verify gate ci-verify](https://github.com/Monyeah777/NarrativeForge/actions/workflows/ci-verify.yml/badge.svg)](https://github.com/Monyeah777/NarrativeForge/actions/workflows/ci-verify.yml)

**NF terminal (TUI) demo** — a full-screen human entry built on the standard library only; its menu and actions are controlled callers of the real `nf` CLI.
Keybindings follow the mainstream terminal conventions: `Tab` switches panes, `↑↓` moves inside the focused pane, `/` filters, `?` opens the keymap.

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

`python tui/nf.py` opens the full-screen UI; `--selftest` runs the security self-check, `--demo` prints exactly the frame above, and `--exec "nf doctor"` is the scriptable surface
(no TTY needed either: `--list-actions --json` gives agents the actions and exit codes). Commands run on a worker thread, so `Ctrl-C` while running cancels just that command;
path arguments pass repository-containment checks, writes require typing `yes`, and API keys are read from the environment and masked. A single-file executable is shipped alongside.
Details: `tui/README.md`.

> MIT License · original open source · please cite the source when deriving/referencing

**In one sentence**: NF is a **content contract layer** — it defines the protocols, quality gates and asset standards for "AI reliably produces long-form content"; narrative is only the first official domain package, while the protocol itself is domain-neutral and model-agnostic.

**Aliases & keywords**: NF · NarrativeForge · 叙事工坊 · content contract layer · spec-driven content factory · long-form content generation · assembly-based content production · module/pipeline/asset · quality gate · domain pack · MCP.

**What it is not**: not a model, not a prompt-template collection, not a vendor SDK — the protocol itself is domain-neutral and model-agnostic, and MCP is just one supported connection protocol.

`bash verify.sh`（check 数与脚本版本以生成的统计区为准；本文档不钉运行时计数） · `python scripts/nf.py stats --check`

> **Bilingual rule**: this file mirrors `README.md` section by section; the Chinese `README.md` is authoritative. The machine-checkable facts (version, check count, PASS baseline, protocol files, machine entries) are asserted identical by `verify.sh` check34 — a drift fails the gate.
> 最后更新：2026-09-20

## ⚡ If you are an AI / Agent

- What this is: a spec-driven document factory — load modules/pipelines/assets → validate → emit.
- Entry chain: `AGENT_START.md` (start) → `AI_ROUTING.md` (pick a route) → `DEEP_DIVE.md` (go deep).
- Machine credential: `bash verify.sh` (run it locally — the static check count and script version live in the generated stats block below; runtime counters are deliberately not pinned in prose); the machine entry list is `llms.txt`, the English entry is `README.en.md` (both entries' machine facts are asserted consistent by check34).
- To understand why NF is designed this way: read [DEEP_DIVE.md](DEEP_DIVE.md).

## Quick start

Human (author/developer, 5 minutes):

1. `bash verify.sh`
2. `python scripts/nf.py shell` (interactive terminal — the human entry after the shell line retired; see `docs/terminal.md`)
3. `python scripts/nf.py demo`
4. `python scripts/nf.py --help`
5. `python scripts/nf.py doctor`
6. `python scripts/nf.py completion bash`

AI assembly:

1. Read `AGENT_START.md`
2. Read `agent_组装指令包_v0.2.md`
3. Take `01_核心协议.md` / `02_联动注册表.md` / `06_Agent执行协议.md` / `07_官方核心出厂与社区预设导航.md` and community packages as needed
4. Assemble a self-contained full version and pass the `##7` self-check
5. `nf assemble "<requirement>" --build --dest <dir>` (assembly command: emits an "full version" single file directly)
6. `nf assemble "<requirement>" --check <out.md>`

### FAQ

- **What is NF?** A content contract layer: protocols + quality gates + asset standards that make "AI reliably produces long-form content" loadable, checkable and reproducible.
- **Is NF an MCP server?** Not necessarily — protocols and assets are plain text, so a clone or a raw link is enough; `nf serve` adds an MCP surface.
- **Which models are supported?** Model-agnostic: any text-capable AI can assemble and load the protocols; nothing is bound to a vendor or a connection protocol.
- **Does it need network access?** No. The repository is markdown source; `bash verify.sh` is local-only and runs offline.
- **How is output judged?** Only by the internal chain: the verify gate (statically checkable) + the five-axis depth review + real drills. External praise is not used as quality evidence.
- **How do I cite it?** MIT license; please credit the source — machine-readable metadata lives in `CITATION.cff` at the repository root.

## Capabilities and assets

<!-- nf:stats:begin -->
**Official core**: 13 modules · 3 pipelines (P00 / P01 / P90) · protocol files 01-07
**Community scale**: 111 registered packs · 363 asset files · 101 concept graphs · 100 domain packs / 1200 subdivisions · standards catalog 370 (reachable 332 / unreachable 38 · 194 bodies · 206 dependency edges) · standard bindings 1200
**Quality evidence**: verify v2.30 · check1-40 · PASS=70 (`bash verify.sh`; expectations from `quality_baseline.EXPECTED_*`) · library 3 items

> Generated by `python scripts/nf.py stats --write`. Do not edit by hand; sources in `protocol/repo_stats.json`.
<!-- nf:stats:end -->

## Protocol chain and documentation map

| Layer | Entry |
|---|---|
| Direction | `STRATEGY.md` |
| Protocol | `01_核心协议.md` · `02_联动注册表.md` · `06_Agent执行协议.md` · `07_官方核心出厂与社区预设导航.md` · `protocol/WORLD_MODEL.md` |
| Library | `03_管线库/` · `04_模块库/` · `05_资产库/` |
| Community | `community/README.md` · `community/模板制作指令包.md` |
| AI | `AGENT_START.md` · `AI_ROUTING.md` · `DEEP_DIVE.md` |
| Tooling | `docs/mcp.md` · `docs/terminal.md` · `docs/layers.md` · `scripts/nf.py` · `tui/nf.py` · `verify.sh` |
| Collection | `library/INDEX.md` · `ROUTES.md` |

## Version block

| Version | Status |
|---|---|
| v2.11.0 | current (2026-09-10) · world_model deterministic abstract-state contract + world_slots |
| v2.10.0 | released 2026-09-09 · 45 quality depth + foundation-layer wave A |
| v2.9.0 | released 2026-09-08 · STRATEGY + waves 43/44 |
| v2.8.0 | released 2026-09-08 · waves 41/42 quality closure |

Full version history: `CHANGELOG.md` and `VERSION-MATRIX.md`.
