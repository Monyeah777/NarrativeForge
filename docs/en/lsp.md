# Editor integration (LSP)
> 最后更新：2026-10-07 (last updated)

## What this is

`nf lsp` is NF's LSP server (stdio, `Content-Length` framing): **diagnostics + domain intelligence + quickfix**.
Diagnostics come from the same source as `nf lint` / `nf lint --prose`; the domain symbol table comes from
`core/nf_language` (module ids / asset keys / event names / layer ids / pipeline ids, all derived from
registry.json, `machine_contract`, the event registry and the file face — no second source of truth is
created). **It never writes to disk** — edits reach the client only through `codeAction`.

**Inbound resource gate**: a single message (header line included) is capped at **8 MiB** — a
`Content-Length` that is over the cap or negative, or a header line that never ends, is treated as a bad
frame and answered with `-32700` while the session **keeps serving** (same cap and same class of evidence as
the MCP face).

### Capability table

| Capability | LSP method | Notes |
|---|---|---|
| Sync | `initialize` → `textDocumentSync` | full-sync (openClose + save); **no incremental sync** |
| Diagnostics | `textDocument/publishDiagnostics` | two sources (`nf` mechanical rules / `nf-prose` prose lint), each with real line/column |
| Fix | `textDocument/codeAction` | `quickfix`: minimal line-level edits (falls back to a whole-document replace if replay verification fails) |
| Completion | `textDocument/completion` | module ids / asset keys / event names / layer ids / pipeline ids (prefix completion) |
| Hover | `textDocument/hover` | symbol metadata (module name and mounts, event publisher/subscribers, owning package of an asset, …) |
| Go to definition | `textDocument/definition` | reference → defining file; **fail-closed on ambiguity** (never guesses, see "Boundaries" below) |
| Outline | `textDocument/documentSymbol` | Markdown heading tree (skips fenced code blocks); hierarchical or flat depending on client capability |
| Workspace symbols | `workspace/symbol` | repository-wide symbol search (modules/assets/events/layers/pipelines) |
| Folding | `textDocument/foldingRange` | heading sections (up to the line before the next heading of the same or higher level) plus code fences; single-line spans are omitted (clients ignore them, so they would be noise) |
| References | `textDocument/references` | **registered relations only** (event ↔ publisher/subscriber modules, module ↔ mount layer, pipeline ← adopting package); every location carries a why, and anything unregistered yields an empty list — **no full-text search** (it would spray false references) |
| Position encoding | `positionEncoding` | fixed to `utf-16` (the LSP default; every client must support it) |

## Three-step setup

Step 1: generate the config (**no hand-copying**) — there is one renderer and it is the source of truth;
the three blocks below are exactly its output:

```bash
python scripts/nf.py lsp --print-config neovim     # emacs / helix work too
```

Step 2: paste the output into your editor config (the LSP client speaks stdio; the path points at the
**absolute repository path**).
Step 3: restart the editor and open any ``.md`` file inside the repository.

Neovim (`init.lua`):

```lua
vim.lsp.start({
  name = "nf-lsp",
  cmd = { "python", "<absolute-repo-path>/scripts/nf.py", "lsp" },
  root_dir = "<absolute-repo-path>",
})
```

Emacs / eglot (`init.el`):

```elisp
(with-eval-after-load 'eglot
  (add-to-list 'eglot-server-programs
               '(markdown-mode . ("python" "<absolute-repo-path>/scripts/nf.py" "lsp"))))
```

Helix (`languages.toml`):

```toml
[[language]]
name = "markdown"
language-servers = ["nf-lsp"]

[language-server.nf-lsp]
command = "python"
args = ["<absolute-repo-path>/scripts/nf.py", "lsp"]
```

## Self-test (no editor required)

```bash
python -m unittest desktop.tests.test_lsp desktop.tests.test_lsp_hardening desktop.tests.test_nf_language -v
```

## Boundaries (stated honestly)

- **Never loaded in a real editor** (this workstation has no VS Code / Neovim / Emacs / Helix) — the protocol
  behaviour is covered by regression tests and by the editor-face criteria of `check33` (capability
  declaration / diagnostic positions / didClose / exit code / domain resolution / completion, hover,
  definition, outline / config generation); loading it into an editor is left to the user — **this
  repository does not claim it has been verified**. The `lsp` face of the interop third-party channel
  **has no card yet** (adding one requires syncing the .NET-line golden; prerequisites are recorded in
  `results/audit/docs_audit-93-three-axis-adapters.md`); until then this document points at no backfill row.
- **No config is generated for VS Code–class clients**: their LSP client needs an extension host and this
  repository has no editor to load one in, so no unverified extension or config is shipped (we do not claim
  support we have not measured). Editors with a built-in LSP client (Neovim / Emacs / Helix) can connect directly.
- Only full-sync + diagnostics + domain intelligence + quickfix + **structured references** + **folding**; no
  incremental sync, no formatting, no semantic highlighting.
- **Ambiguous identifiers are not resolved for go-to-definition**: the bare number `M10` belongs to both
  `通用:M10` and `生存:M10`, and `P00` is both a layer and an official pipeline — such tokens are listed
  in full on hover, while go-to-definition fails closed (it does not pick one).
- **References are not a text search**: only relations registered in `registry.json` produce locations; for a
  colliding token such as `P00` the hits from both the layer and the pipeline relations are listed together
  (each with its why), instead of guessing one.
