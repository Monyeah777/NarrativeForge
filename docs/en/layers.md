# NF abstraction ladder (layers)

> 最后更新：2026-09-26 (last updated)

> ⛔ Operating instruction: this file contains commands and criteria you can run directly. Read it and run it; do not treat it as background reading.

## What this file solves

NF already had four ways of talking about "layers": **L0–L3** (dependency-governance numbering, see `L3_FROZEN.md`), **P00–P80** (pipeline rungs),
**mount_layers** (module mount layers), and **standard-directory layer** (data/eng/form/gov/iface). Each of the four means something, but
"who is acting" (terminal, AI, external tools) and "what is being processed" (protocols, assets) used to sit on the same ladder — so there appeared
misplacements like "the terminal at the bottom, AI at the top", treating a **role** as a **layer**. Retiring the end-shell already proved the cost of that conflation: a role
was treated as a layer, and when the whole layer retired its capability had nowhere to live, so criteria had to be patched in afterwards to contain it.

This ladder separates the two and turns the rules into criteria that **run on every commit** (not prose slogans):

- **Four rungs on the abstraction axis**: contract → asset → engine → exit. The lower you go, the more stable and the more expensive to change; dependencies may only point downward.
- **Entry surface**: registers roles only (human–machine / AI assembly line / MCP / library pickup), and is **never a source of truth**.
- **Verification vertical slice**: gates and evidence cut across all four rungs, so it is not a "layer".

Naming discipline: this ladder uses only "**rung / surface / vertical slice**" and does not reuse any of the four vocabularies above.

## How to use

```bash
python scripts/nf.py layers            # human-readable ladder (with interface-surface and implementation-surface annotations)
python scripts/nf.py layers --json     # machine-readable (per-rung source-of-truth surface / interface surface / criteria)
python scripts/nf.py layers --verify   # run the ladder health check (same source as verify check27; the exit code carries the gate semantics)
python scripts/nf.py layers --write    # refresh the generated region of this file (must run after changing the source of truth)
```

Before changing anything, ask three questions; the answers are written in the table below:

1. **Which rung does it belong to?** (decided by the source-of-truth surface)
2. **Which surface do others depend on?** (only the interface surface may be depended on across rungs; the implementation surface can be changed freely)
3. **What change class is this?** (editorial / additive / bump — the same vocabulary as `protocol/EXTENSION.md`)

## The ladder (generated region · source of truth = `protocol/LAYERS.json`)

<!-- nf:layers:begin -->
### The abstraction axis: four rungs

| Rung | Source-of-truth surface | Interface surface (the only thing cross-rung dependency may rely on) | Existing criteria | Status / change class |
|---|---|---|---|---|
| **Contract** | `01_核心协议.md`, `02_联动注册表.md`, `06_Agent执行协议.md`, `07_官方核心出厂与社区预设导航.md`, `STRATEGY.md`, `protocol/*.md`, `protocol/*.json`, `protocol/schema/*.json`, `desktop/src/core/registry.json` | `protocol/schema/*.json`, `protocol/CONFORMANCE.md`, `desktop/src/core/registry.json` | check13, check28, check29, check30, check31 | active (bump) |
| **Asset** | `03_管线库/*.md`, `04_模块库/*/*.md`, `05_资产库/**/*`, `community/**/*`, `library/*.md` | `community/*/protocol.yaml`, `05_资产库/provenance.json` | check7, check8, check9, check10, check11, check14, check15, check16, check23, check24, check34 | active (additive) |
| **Engine** | `desktop/src/core/*.py`, `desktop/tests/**/*.py`, `desktop/scripts/*.py`, `scripts/*.py`, `scripts/*.sh`, `scripts/nf`, `scripts/nf.cmd` | `scripts/nf.py` | check12, check17, check18, check19, check20, check21, check22, check27, check32, check33 | active (additive) |
| **Exit** | `results/interop/*.json`, `docs/standards/*.md`, `docs/fde-sample/**/*` | `results/interop/*.json`, `docs/standards/index.md` | check18, check19, check22, check33, check38 | active (editorial) |

### The five sublevels of the asset rung (heterogeneous within one cell — assess their costs separately)

| Sublevel | Source-of-truth surface | Existing criteria | Framing |
|---|---|---|---|
| **Declaration** | `community/*/protocol.yaml` | check14 | An instance of the contract: changing it must go through the three registration requirements (01 §6.1 + 02 §8.3 + registry projection). |
| **Content** | `03_管线库/*.md`, `04_模块库/*/*.md`, `community/*/modules/*.md`, `community/*/pipelines/*.md` | check7, check9, check24 | Module and pipeline bodies: bound by the numbering namespace and the mount layers. |
| **Data** | `05_资产库/**/*`, `community/*/assets/*.md` | check8, check11, check23 | Asset keys and the provenance ledger: the criteria are addressable / traceable / no orphan keys. |
| **Knowledge** | `protocol/knowledge_sources.json`, `protocol/transform_log.json` | check37 | Dual-source knowledge layer: the criteria are authority tiering / ordered queries / freshness / traceable ingestion (a different framing from entry-type assets). |
| **Ontology** | `protocol/standards_catalog.json`, `protocol/standards_binding.json`, `protocol/domain_packs.json` | check32 | Concept graph and standards catalog/binding: the criteria are concept density / standards reachability / data truthfulness. |

### Entry surface (registers roles only, never a source of truth)

| Surface | Entry artifact | Serves rung | Framing |
|---|---|---|---|
| **Human–machine entry** | `scripts/nf`, `scripts/nf.cmd`, `scripts/nf.py` | engine | With no arguments it enters the terminal (nf shell → desktop/src/core/terminal.py); all other arguments pass through to the CLI. |
| **AI assembly line** | `AGENT_START.md`, `agent_组装指令包_v0.2.md`, `AI_ROUTING.md` | asset | Any agent can self-serve and assemble the "full edition" from the repository URL alone; the same tier as line A (human–machine), with no model presupposed. |
| **MCP service surface** | `docs/mcp.md`, `protocol/mcp_package.json` | engine | Long-running runtime entry = nf serve (the CLI surface of the engine rung); this surface registers only the contract and the usage documentation. |
| **Library pickup surface** | `ROUTES.md`, `library/INDEX.md`, `library/ALIAS.md` | asset | Address by number + mirrored routing; the holdings themselves belong to the asset rung, and this surface only handles "how to find it". |

### Verification vertical slice (cuts across all four rungs, not a layer)

| Artifact | Landing point | Existing criteria |
|---|---|---|
| **verify** | `verify.sh` | check27 |
| **conformance** | `protocol/conformance_report.json` | check35 |
| **audit** | `results/audit` | check36 |
| **receipts** | `protocol/RECEIPTS.json` | check35 |
| **attest** | `docs/attest.md` | check33 |
| **provenance** | `05_资产库/provenance.json` | check23 |

> This region is rendered by `nf layers --write`; hand-editing is forbidden. Source of truth = `protocol/LAYERS.json`.
<!-- nf:layers:end -->

## The five disciplines (criteria in L1–L10 of `desktop/src/core/layer_model.py`)

- **Dependencies point downward only**: the contract depends on no rung; the asset depends only on the contract; the engine depends on the contract and the assets (read-only); the exit depends on the engine.
- **Cross-rung dependency uses the interface surface only**: `02 §8` registry entries, `protocol.yaml`, the asset provenance ledger, the CLI command surface — these are the commitments;
  everything else (module bodies, core internal functions) belongs to the implementation surface and may be rewritten freely.
- **The entry is not the source of truth**: entries can be replaced (end-shell → terminal was one such replacement), and no rung may take an entry artifact as a source of truth or depend on it in reverse.
- **Retirement is a first-class citizen**: retiring a rung must follow the three steps "capability reassignment → entry completion → criterion revision + record + adjudication by the author".
- **Vertical slices do not take part in ownership**: evidence and derivatives such as `results/audit/**` and `protocol/RECEIPTS.json` are exempted through the `derived` list,
  not through an implicit convention.
