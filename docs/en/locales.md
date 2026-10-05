# Locales and localization (locales)
> ⛔ Operating instruction: this file is the **declaration** of the language and localization policy; the judge lives in check34 (core/locales.py). Read it and run it.
> 最后更新：2026-10-05 (last updated)

## What this is

NF has two language surfaces: the **entry surface** (README.md / README.en.md / README.ja.md) and the **document surface** (docs/<lang>/...). The source of truth is protocol/locales.json: per-language entry, code owner, coverage declaration, and document translations with their **source digest**.

## Rules (all machine-checked)

1. **Entry surface**: every entry must carry the same machine-fact anchors, the language switcher line (enumerating all present languages), aligned H2 structure, and every .md file referenced by the canonical entry.
2. **Document surface**: a translation path must **mirror** the source (docs/<lang>/<source-relative-path>); each translation records source_sha256, so **any source edit marks it stale**.
3. **Honest coverage**: a locale declared coverage=entry must not ship document translations; coverage=entry+guides must ship every translation the registry declares.
4. **Undeclared is red**: a file under docs/<lang>/ that the registry does not declare fails the gate (no unmanaged second language surface).

## Adding a translation

(1) write the translation at docs/<lang>/<source-relative-path>;
(2) register its path in protocol/locales.json under docs[].translations;
(3) run python scripts/nf.py locales --write to re-sign the source digest;
(4) run python scripts/nf.py locales to self-check - stale / non-mirrored / missing locale / undeclared all turn red.

## Status and boundaries

- Entry surface: **3 languages** (Chinese / English / Japanese). The document surface currently covers five guides: release, localization, MCP access, terminal, and the abstract ladder.
- The rest of the documentation is still single-language - **explicitly declared** by the registry, not silently monolingual; new translations follow the four steps above.
- No external translation platform and **no machine translation**: content quality is the translator's responsibility; the judge only guarantees that what is declared exists and is not stale.
- Language owners live in the registry's codeowner field (same meaning as Home Assistant codeowners).
