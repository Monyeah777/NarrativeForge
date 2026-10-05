# Release orchestration (release)
> ⛔ Operating instruction: this file is the **human-readable projection** of the release policy. The machine source is `protocol/release_policy.json` (validated against `protocol/schema/release.schema.json`); the machine-checked preflight is check38's `release_gate` sub-scan. Read it and run it.
> 最后更新：2026-10-05 (last updated)

## What this solves

Release steps used to live in four places — `nf release` (preflight), `scripts/release_freeze.sh` (golden master snapshot), `scripts/bump_verify.sh` (version relabeling) and a manual checklist — while the **order** and the **preconditions** existed only in prose. Two mechanisms from top-tier peers were adopted: **config-as-contract** (policy in `protocol/release_policy.json` + its JSON Schema, like release-please's `$schema` pattern) and **change collection** (`changes/unreleased/*.md`, like changesets).

```bash
python scripts/nf.py release --plan          # ordered plan (command / output / criterion)
python scripts/nf.py release --plan --json   # machine-readable plan
python scripts/nf.py release                 # preflight (= verify + coverage + e2e + report freshness)
python scripts/nf.py release --json          # deterministic evidence manifest (read-only)
python scripts/nf.py release --freeze --apply --by <approver> --note "<wave note>"
                                             # run the freeze chain in order (default is a dry run)
```

## Freeze chain

The order must not be reversed (see `decisions/ADR-0005-新增NET引擎线.md` and the PO-0001 postmortem): content frozen → conformance report recomputed → content-bound approval → protocol receipts re-signed.

1. `python scripts/nf.py conformance --write` (produces `protocol/conformance_report.json`, must be `conformant`)
2. `nf approve protocol/conformance_report.json --by <approver> --note <note>` (content-bound; invalidated the moment the object changes)
3. `python scripts/nf.py receipts --scope protocol --write` (protocol receipt root + derived faces refreshed)

Receipts must run **last**, after all content changes; otherwise the root covers stale bytes. After changing library content also run `nf library receipts --write`.

## Version faces

Three registrations must not dangle (recompute rules live in `core/quality_baseline.py` and in VERSION-MATRIX's own two-way check):

| Face | Source | Action at release |
|---|---|---|
| `CHANGELOG.md` | latest section `## [X.Y.Z]` | flip "unreleased" to released and record the PASS baseline |
| `VERSION-MATRIX.md` | version × plan × capability row | add a row (version / date-status / plan / capability) |
| `README.md` version block | the "current" row | move the current row to the new version |

`bash verify.sh` is the single gate entry; the expected `PASS` value is a declaration (`quality_baseline.EXPECTED_*`) and is not hand-written here.

## Golden Master

```bash
bash scripts/release_freeze.sh vX.Y.Z
```

Output = `.release-frozen/<tag>/sha256.manifest` (`01_核心协议.md` / `02_联动注册表.md` / `06_Agent执行协议.md` / `07_官方核心出厂与社区预设导航.md` / `verify.sh` + `desktop/src/core/*.py`) plus `sig-fingerprint.txt` (`nf sig --verify` knowledge fingerprint). Snapshots are **historical facts** and are not refreshed; incomplete structure (missing file classes / empty digests) is judged red by the `release_gate` sub-scan.

## Change entries

When a change lands, add one entry under `changes/unreleased/` (`type:` + `note:`, vocabulary identical to `CONTRIBUTING §1`). At release, the plan's `changes-1` step archives them into the CHANGELOG version section and empties the directory. Rules and rationale: `changes/README.md`.

## Boundaries (not claimed)

- This mechanism does **not** replace `verify.sh`: a green gate is a precondition, not a quality claim.
- The plan is **orchestration**, not proof: `--apply` only calls the existing commands in order and adds no write semantics.
- `git tag` is performed by a human (this mechanism only gives the command and the criterion) — tagging is irreversible and stays out of the automated surface.
