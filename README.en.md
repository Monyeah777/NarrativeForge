# NarrativeForge · Document Generation Workshop (spec-driven) — English mirror

> MIT License · original open source · please cite the source when deriving/referencing

**In one sentence**: NF is a **content contract layer** — it defines the protocols, quality gates and asset standards for "AI reliably produces long-form content"; narrative is only the first official domain package, while the protocol itself is domain-neutral and model-agnostic.

`verify v2.27 · check1-37 · PASS=61` · `python scripts/nf.py --version`

> **Bilingual rule**: this file mirrors `README.md` section by section; the Chinese `README.md` is authoritative. The machine-checkable facts (version, check count, PASS baseline, protocol files, machine entries) are asserted identical by `verify.sh` check34 — a drift fails the gate.
> 最后更新：2026-09-20

## ⚡ If you are an AI / Agent

- What this is: a spec-driven document factory — load modules/pipelines/assets → validate → emit.
- Entry chain: `AGENT_START.md` (start) → `AI_ROUTING.md` (pick a route) → `DEEP_DIVE.md` (go deep).
- Machine credential: `bash verify.sh` → v2.27, check1-37, PASS=61; the machine entry list is `llms.txt`, the English entry is `README.en.md` (both entries' machine facts are asserted consistent by check34).
- To understand why NF is designed this way: read [DEEP_DIVE.md](DEEP_DIVE.md).

## Quick start

Human (author/developer, 5 minutes):

1. `bash verify.sh`
2. `python scripts/nf.py demo`
3. `python scripts/nf.py --help`
4. `python scripts/nf.py doctor`
5. `python scripts/nf.py completion bash`

AI assembly:

1. Read `AGENT_START.md`
2. Read `agent_组装指令包_v0.2.md`
3. Take `01_核心协议.md` / `02_联动注册表.md` / `06_Agent执行协议.md` / `07_官方核心出厂与社区预设导航.md` and community packages as needed
4. Assemble a self-contained full version and pass the `##7` self-check
5. `nf assemble "<requirement>" --check <out.md>`

## Capabilities and assets

48 modules · 10 pipelines · 7 community packages (3 narrative / 3 non-narrative / 1 composite) · 60 asset files / 326 keys · 2 concept graphs (AI systems 47 + quantitative finance 30) · world_model 1 (M50) · library entries 3 · practice packs 3 · knowledge sources 6 (contract 3 / reference 3) · verify check1-37 always on

## Protocol chain and documentation map

| Layer | Entry |
|---|---|
| Direction | `STRATEGY.md` |
| Protocol | `01_核心协议.md` · `02_联动注册表.md` · `06_Agent执行协议.md` · `07_官方核心出厂与社区预设导航.md` · `protocol/WORLD_MODEL.md` |
| Library | `03_管线库/` · `04_模块库/` · `05_资产库/` |
| Community | `community/README.md` · `community/模板制作指令包.md` |
| AI | `AGENT_START.md` · `AI_ROUTING.md` · `DEEP_DIVE.md` |
| Tooling | `docs/mcp.md` · `scripts/nf.py` · `scripts/verify.sh` |
| Collection | `library/INDEX.md` · `ROUTES.md` |

## Version block

| Version | Status |
|---|---|
| v2.11.0 | current (2026-09-10) · world_model deterministic abstract-state contract + world_slots |
| v2.10.0 | released 2026-09-09 · 45 quality depth + foundation-layer wave A |
| v2.9.0 | released 2026-09-08 · STRATEGY + waves 43/44 |
| v2.8.0 | released 2026-09-08 · waves 41/42 quality closure |

Full version history: `CHANGELOG.md` and `VERSION-MATRIX.md`.
