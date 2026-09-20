# NarrativeForge · Content Contract Workshop (English entry)

> **What this is**: NarrativeForge (NF) is a **content contract layer** — it turns "AI reliably produces long-form content" into loading, quality-gated, reproducible engineering. The protocol itself is domain-neutral and model-agnostic; narrative is only the first official domain package.
> **This file is the minimal English entry.** The authoritative documents are Chinese; this entry covers the machine-checkable facts and the loading paths so an English-only agent can start. It is kept in sync with `README.md` by a machine check (`verify.sh` check34, bilingual anchors).
> 最后更新：2026-09-20

## Quality credential (run locally, not a claim)

`bash verify.sh` → **v2.27 · check1-37 · PASS=61** (WARN=0, FAIL=0). The gate is self-contained and offline.

## Machine entry points

| Entry | Path | For |
|---|---|---|
| Machine index | `llms.txt` | agents: what to read first |
| Core protocol | `01_核心协议.md` | module / pipeline / asset protocols |
| Registry (truth source) | `02_联动注册表.md` | module table, mount points, community package registrations |
| Agent execution protocol | `06_Agent执行协议.md` | runtime constraints for agents |
| Navigation | `07_官方核心出厂与社区预设导航.md` | official-core assembly guide |
| Domain packages | `community/` | official domain packages (narrative + non-narrative domains) |
| Protocol IDL | `protocol/schema/*.json` | machine-readable schemas (contract / module / pipeline / protocol / asset) |
| CLI | `scripts/nf.py --help` | the `nf` toolchain (`market` / `pipeline` / `asset` / `module` / `register` / `score` …) |

## Three loading paths

1. **Official core assembly** — read `07_官方核心出厂与社区预设导航.md` and load the 13 official core modules via pipeline `P01`.
2. **Domain package** — pick a package under `community/`, read its `README.md` + `protocol.yaml`, load its pipeline (e.g. `P02` … `P08`).
3. **Agent self-assembly** — read `AGENT_START.md` → `agent_组装指令包_v0.2.md`, then assemble a self-contained world document.

## What is machine-verified

- `bash verify.sh` — 37 checks in three sections (official core / community packages / code layer). All green is the baseline, not a quality claim.
- `python -m unittest discover -s desktop/tests -q` — core test suite.
- `nf conformance` — conformance report (contracts → Merkle root → verdict).
- `nf score` — baseline-relative regression score (no silent worsening).
- `nf events` — event backing: every subscribed event must have a publisher.

## Scope and licensing

- Repository content: see `LICENSE` (MIT) and per-entry license columns (`library/INDEX.md`, `nf license`).
- Domain packages are self-authored content; external material is used only as evidence (provenance recorded per asset) and is never copied.

> Chinese original: `README.md`. If the two entries disagree on a machine-checkable fact, the check in `verify.sh` (check34) fails — the machine facts must match.
