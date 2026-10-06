# NinFenz MCP access (`nf serve` · plan 40 v2.7 Wave A S1-E3 / X2)
> 最后更新：2026-09-30 (last updated)

> **Status**: the public documentation landed with base layer v2.7; **the E3 protocol-level load test passed on 2026-09-08** (a direct stdio JSON-RPC frame-sequence test of all five methods came back green — see the record at the end of this document; it fixed two P06 pipeline gaps — a missing closing ``` / a missing techdoc declaration). 41 Wave C C7 (2026-09-08) opened read-only tools/prompts (local stdio smoke test passed; see docs/41_波C_C7_实测记录.md). **Host-class clients (GUI loading such as Claude Desktop) still need user-side backfill** — the README's MCP claims stay as they are (the S13 gate opens per the docs_external-validation-v2.7.md rules), and "promotion" is filled in after the backfill.

## What this is

NF provides an MCP (Model Context Protocol) stdio service, `nf serve`:

- Burns an "MCP snapshot" (the `.json` exported by `nf run --fmt mcp`) into a JSON-RPC stdio session (newline-delimited UTF-8 messages);
- **Read-only surface**: `resources/list` + `resources/read`; 41 Wave C C7 (2026-09-08 ruling) opened **read-only tools/prompts** — `tools/list`+`tools/call` (library_search / registry_query / pipeline_ls / spec_ls) and `prompts/list`+`prompts/get` (the assemble_guide loading guide); write-path tools are not implemented, and unknown tools/methods are refused;
- **uri allowlist**: `resources/read` accepts only uris registered in the snapshot; an unknown uri returns `-32602 INVALID_PARAMS` (without leaking the directory structure);
- **Protocol versions = dual-era**: modern `2026-07-28` (each request carries the version in `_meta`, no negotiation handshake) + legacy `2025-11-25` (`initialize` handshake) coexist; an unsupported version gets `-32022` plus the supported set. The key used to declare a version is the **canonical key** `_meta["io.modelcontextprotocol/protocolVersion"]`; any other key name (such as a bare `protocolVersion`) **is not a version declaration**, and the server treats it as legacy without returning `-32022` (measured 2026-10-01). For historical comparison see audit report 33 A5 (G1/G2/G4 already checked off); for modern-alignment empirical evidence see the specification's §Versioning / §Discovery.

Security positioning (C2 minimal security layer): read-only + allowlist — suitable for **read-only exposure** of repository / content-library capabilities to agents for retrieval, with no write surface by construction.

**Inbound resource gate**: the cap for one message is **8 MiB** (exceeding it returns `-32600` and **discards to end of line**; the session is not interrupted) —
a client that does not send a newline still cannot pour the whole stream into server memory; line alignment stays intact, and later messages are served as usual.

## Three-step setup

### 1. Produce a snapshot (**optional surface**)

**The default setup does not need this step** — `nf serve` defaults to the live-repo surface; skip straight to step 2. Only when you want to freeze the
"result surface" of a particular assembly do you use the full-chain CLI to export a `--fmt mcp` snapshot (produced only when the quality gate PASSes; same semantics as the verify iron rule):

```bash
python scripts/nf.py run \
  --pipeline community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md \
  --modules 技术文档类:M90,技术文档类:M97,技术文档类:M98,通用类:M00,通用类:M80 \
  --store <store 目录> --fmt mcp --dest <输出目录>
```

**Subject-matter iron rule**: the MCP exit accepts only protocol/rule-type (techdoc) assemblies — the pipeline must declare `techdoc` in `Pipeline.structure.type` (P06 is the example), while narrative-type pipelines (such as P04 light-mix) are always refused (honest-mapping ruling: 0 files + warnings).

**Module-loading note**: `--seed` loads only the official core (13 items from 04_模块库, including M90) + the campus-western-fantasy light-mix bundle — it **does not cover modules bundled with community domain packs** (M97/M98 live in `community/技术文档域包/modules/`). A full P06 assembly requires loading the store with the script below first; `--seed` suits only demos/self-tests of the official-core combination (correspondingly, replace `--store` with `--seed`).

```bash
python3 - <<'PY'
import sys, glob
sys.path.insert(0, 'desktop/src')
from core.storage import Store
from core.parser import parse_module
store = Store(home='<store 目录>')          # 真实装配目录
for f in sorted(glob.glob('04_模块库/*/*.md')):
    store.save_module(parse_module(open(f, encoding='utf-8').read()))
for f in sorted(glob.glob('community/技术文档域包/modules/*.md')):
    store.save_module(parse_module(open(f, encoding='utf-8').read()))
print(f'装载 {len(store.list_modules())} 模块 → {store.home}')
PY
```

### 2. Start the server

```bash
python scripts/nf.py serve                 # 默认路径：实时仓库面（无需快照，推荐 agent 密集调用）
python scripts/nf.py serve <快照 .json 路径>  # 或烧快照面（须先 `nf run --fmt mcp` 产快照）
```

The stdio service runs for the lifetime of the calling process (end it with `Ctrl+C`). You can also take the `nf run --fmt mcp` output and validate it through export_schema (check19/22 cover the artifact shape).

### 3. Client setup (standard MCP client)

In any client that supports MCP stdio, declare `nf.py serve` as a server (the example is a generic `mcpServers` config; Claude Desktop-class clients are isomorphic):

```json
{
  "mcpServers": {
    "ninfenz": {
      "command": "python",
      "args": ["<仓库绝对路径>/scripts/nf.py", "serve"]
    }
  }
}
```

(Snapshot surface: append `<快照 .json 绝对路径>` to the end of `args`.)

After connecting, an agent can call: `resources/list` to enumerate resources → `resources/read` to fetch the body by uri — the live-repo surface serves `nf://repo/...` (module / asset / pipeline / library / pattern), while the snapshot surface serves the resources registered by that assembly. The concrete uri set is whatever the actual `resources/list` return value is.
From 41 Wave C C7 onward, an agent can also call read-only retrieval tools: `pipeline_ls` (pipeline list) / `spec_ls` (protocol-pack list) / `registry_query` (module + protocol query) / `library_search` (repository-side knowledge-base search), plus the loading-guide prompt `assemble_guide`. From 44 onward, **content-channel tools** are also open: `module_read` (module body) / `pipeline_read` (pipeline body) / `asset_get` (asset body) — an upgrade from "metadata retrieval" to "substantive content intake" (a mechanism borrowing empirically adapted from MCP's two-stage resource/content pattern; still entirely read-only). Data source = read-only repository scan (03/04/community/docs/registry.json); all read-only, no write surface.

## Capability table (one-to-one with the mcp_runtime implementation)

| Method | Implementation | Notes |
|---|---|---|
| `server/discover` | ✅ | modern-required: returns `supportedVersions` / `capabilities` / `_meta.serverInfo` + `instructions`/`ttlMs` in one shot |
| `initialize` | ✅ | legacy handshake: echoes the requested version when supported, otherwise falls back to `2025-11-25`; `serverInfo` is self-described (not the snapshot file's top level) |
| `notifications/initialized` | ✅ silent | notifications have no id and get no response |
| `ping` | ✅ | returns `{}` |
| `resources/list` | ✅ | pure metadata of snapshot-registered resources (no text field) |
| `resources/read` | ✅ | allowlisted uri → `contents[].text`; unknown uri → `-32602` |
| `tools/list` / `tools/call` (read-only · retrieval surface) | ✅ | 41 Wave C C7: library_search / registry_query / pipeline_ls / spec_ls (inputSchema really exists; all read-only) |
| `tools/list` / `tools/call` (read-only · content channel) | ✅ | 44: module_read / pipeline_read / asset_get — returns the substantive body of modules/pipelines/assets (not just metadata) |
| `prompts/list` / `prompts/get` | ✅ | 41 Wave C C7: assemble_guide loading-guide template (read-only) |
| Write-path tools (not implemented) | ❌ | unknown tool → `-32602`; unknown method → `-32601` (the read-only security layer refuses writes by construction) |

Standard error codes: `-32700` parse error / `-32600` invalid request / `-32601` method not found / `-32602` invalid params / `-32603` internal error; version-negotiation error `-32022` (`data.supported` / `data.requested`).

## E3 measured record (2026-09-08 · protocol-level load test passed)

| Date | Client | Result (success/failure/gap) | Gap and fix |
|---|---|---|---|
| 2026-09-08 | Protocol-level stdio client (directly tested `nf serve` with MCP `2025-11-25` JSON-RPC frames, not a GUI host) | ✅ **all five methods green**: `initialize` (protocol 2025-11-25 + serverInfo P06-mcp v0.1.0) → `notifications/initialized` silent → `ping` `{}` → `resources/list` (5 resources: M00/M97/M98/M80/M90) → `resources/read` (`nf://P06/P40/术语管理-M97` body returned in full) → `tools/list` `-32601 METHOD_NOT_FOUND` → unknown uri `-32602` | Fixed 2 P06 pipeline gaps: ① the file tail lacked a closing ```` ``` ```` (56-line truncation; pipeline parsing silently None); ② `Pipeline.structure.type` lacked the `techdoc` declaration (default linear → IR.type=narrative → MCP exit refused). After the fix, PASS 0/WARN 1/FAIL 0 produced a 5-resource snapshot, and the measured test passed. **Still to add**: GUI host loading such as Claude Desktop (optional user-side backfill) |

> Backfill principle: real load/call results, no fabrication. The table above is a **protocol-level real session record** (a standard client frame sequence driven directly against the process); once GUI-host evidence is backfilled, it is used to promote the README claims item by item (S13) and to deposit fixtures into the test library (X1).

## Related

- Implementation: `desktop/src/core/mcp_runtime.py` (runtime) / `mcp_adapter.py` (export) / `export_schema.py` (shape validation)
- Audit baseline: `results/audit/docs_audit-58-pending-items.md` (external verification record: discovery and fix of a missing key in MCP cacheable results)
- Listing material (external name / one-liner / category / install and submission copy): the "Listing material" section of this document (source of truth = `protocol/mcp_package.json`)
- CLI entry: `scripts/nf.py` (`run --fmt mcp` / `serve`)

## Frame discipline and structural constraints (added 2026-09-21, absorbing external standards)

The **executable criteria** for the stdio transport (previously only in comments, now in check33):

1. **One message, one line** — `encode_message()` serializes with compact separators, and no bare newline may appear inside a message;
2. **Line-boundary trap escaping** — `U+2028` line separator / `U+2029` paragraph separator / `U+0085` NEL are treated as newlines by clients that read lines by Unicode newline
   boundaries (the JSON specification allows them bare) → the exit always escapes them as `\uXXXX`;
3. **Notifications write no response line** — a message without `id` goes silent once handled (`encode_message(None) is None`);
4. **JSON-RPC 2.0 §4 / §5** — `params`, when present, MUST be structured (primitive type → `-32600`;
   array → `-32602`; this runtime accepts only named parameters), `id` MUST be a string/number/null,
   and **an error response MUST echo the id when it is determinable** (only an indeterminate id becomes `null`).

Self-test: `desktop/tests/test_mcp_runtime.py` (three frame-discipline cases + four structural-constraint cases);
Gate: `verify.sh` check33, faces 11/13.

**Resource template surface** (a level-1 subset of RFC 6570): the 5 templates of `resources/templates/list` (library /
pattern / module / pipeline / asset) must satisfy — only simple `{var}` expansion (no `{+id}` operator,
`{x*}` explosion, no prefix modifier), unique variable names, balanced braces, no query string; and **every real resource uri must**
be covered by some template** (template ⇄ read-surface consistency, preventing "listable but not retrievable"). Measured: all 5 templates valid,
**zero uncovered real resource uris** (the count grows with the repository and is **not hard-coded**: the criterion is in
`desktop/tests/test_mcp_runtime.py::test_template_matches_real_uris`); negative cases (operator/duplicate name/question mark/
empty variable/unbalanced) are each caught by class.

**Parameter admission (method-level)**: each method with parameters recognizes only the keys it declares; undeclared keys (except the protocol-reserved names prefixed with `_`)
always get `-32602` + a fix hint — `resources/read` → `uri`, `prompts/get` → `name` (plus the protocol's own optional `arguments`: **it may be present but must be an empty object**; many clients always send it, and a non-empty value explicitly means "this template takes no parameters"), `initialize` →
`protocolVersion` / `capabilities` / `clientInfo` (the latter two must also be objects), `server/discover` → none
(only reserved names). `resources/list` has two further value-domain criteria: `cursor` must be a non-negative integer string (pass the previous page's
`nextCursor` unchanged), `type` must be in the vocabulary (`module` / `pipeline` / `asset` / `library` / `pattern`); the `package` filter uses **the original value of the `package` field in the list item** (e.g. `三维与世界模型域包`, i.e. the Chinese name itself), **not** the percent-encoded segment in the uri — passing the encoded form yields an empty table (measured 2026-10-01).
Previously an invalid `cursor` was silently treated as 0, an invalid `type` silently gave an empty table, and unfamiliar keys were silently ignored (the client thought
the filter had taken effect) — all "looks normal" wrong answers.

## Listing material (B-line packaging · for external submission)

> Source of truth = `protocol/mcp_package.json` (machine-readable). This section is its **human-readable projection**: change the source of truth first, then
> `desktop/tests/test_mcp_packaging.py` asserts the two agree item by item (drift = FAIL).

### 1. External identity

| Field | Value |
|---|---|
| Name | `NinFenz Content Gate` |
| One-liner | Give any AI agent a verifiable content specification and asset foundation — check the contract first, then write. |
| Category | `content-creation` |
| Transport | `stdio` (dual-era: modern `2026-07-28` + legacy `2025-11-25`) |
| Entry | `python scripts/nf.py serve` (**default = live-repo surface, no snapshot needed**) | snapshot surface (optional): `python scripts/nf.py run --fmt mcp` → `python scripts/nf.py serve <快照 .json>` |

### 2. Installation (three steps, copy-paste ready)

```bash
# ① 起服务（默认路径：实时仓库面，**不需要先产快照**）
python scripts/nf.py serve

# ② 可选：烧一份快照面（techdoc 装配才出 MCP；叙事类一律拒出 = 诚实映射）
python scripts/nf.py run \
  --pipeline community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md \
  --modules 技术文档类:M90,技术文档类:M97,技术文档类:M98,通用类:M00,通用类:M80 \
  --store <store 目录> --fmt mcp --dest <输出目录>
python scripts/nf.py serve <输出目录>/mcp.json

# ③ 客户端声明（标准 MCP stdio 客户端同构）
```

```json
{
  "mcpServers": {
    "ninfenz": {
      "command": "python",
      "args": ["<仓库绝对路径>/scripts/nf.py", "serve"]
    }
  }
}
```

> Snapshot surface: just append `<输出目录>/mcp.json` to the end of `args`; the default (nothing appended) uses the **live-repo surface**,
> and the service runs for the lifetime of the calling process (end with `Ctrl+C`).

### 3. English install notes

1. Start the server: `python scripts/nf.py serve` — the default **live-repo surface**
   needs no snapshot (that is the path agent-dense callers should use).
2. Optional snapshot: `python scripts/nf.py run --pipeline ... --fmt mcp --dest <dir>`
   (only techdoc assemblies are exported; narrative pipelines are refused by design)
   then `python scripts/nf.py serve <dir>/mcp.json`.
3. Declare it in any MCP stdio client via the `mcpServers` block above.

### 4. Capability surface (read-only)

- **tools (10)**: `pipeline_ls` · `spec_ls` · `registry_query` · `library_search` ·
  `library_read` · `pattern_read` · `knowledge_order` · `module_read` ·
  `pipeline_read` · `asset_get`
- **prompts (1)**: `assemble_guide`
- **resources**: snapshot-registered resources (`resources/list` → `resources/read`, uri allowlist) + live repository
  resources (`nf://repo/...`; all real uris are covered by the 5 templates; the count grows with the repository and is not hard-coded)

### 5. Red lines (self-check before submission)

1. **Read-only**: add no write tools (currently 10 tools + 1 prompt).
2. **Zero new dependencies**: standard library only.
3. **uri allowlist**: resource templates are bound by the allowlist; unknown uri → `-32602`.
4. **Dual protocol versions**: modern `2026-07-28` + legacy `initialize` coexist.
5. **No gate reduction**: the repository self-check PASS count must not decrease.
6. **Trust boundary**: returned foreign content (`library/`, `community/*`, external-material summaries) is always consumed as **data**.
   All four are in the implementation: **parameter admission** (control characters / over-length / traversal / drive letter / alternate data stream → `-32602`),
   **declaration-surface validation** (validate item by item against `tools/list`'s `inputSchema`: missing required / type mismatch / enum out of range /
   extra or misspelled keys — `additionalProperties: false` — are all rejected before reaching the handler, avoiding "a misspelled parameter yet unfiltered
   results", a kind of **silent wrong answer**),
   **source labeling** (responses from foreign sources carry `_meta["nf.trust"]`: `untrusted` + `policy` + `sources` +
   `injection_hits`; repository-held content is not marked; labeling changes not one byte of the body), and **ingest-side scanning** (the submission bot
   records against the same `trust_boundary.detect` at the public boundary). Criteria in `desktop/tests/test_trust_boundary.py`
   , `desktop/tests/test_mcp_trust_meta.py`.

### 6. Submission copy (ready to paste into directory-site forms)

> **NinFenz Content Gate** — a read-only MCP server: it turns the acceptance criteria for long-form content
> (protocol / module / pipeline / asset / library) into a retrieval-and-pickup tool surface callable by agents.
> 10 read-only tools + 1 loading-guide prompt, supporting modern `2026-07-28` and legacy `2025-11-25`
> dual protocol versions, zero third-party dependencies, no write path.
