# NF terminal (`nf shell`) — the human entry point after the desktop shell retired

> 最后更新：2026-10-03 (last updated)

> ⛔ Operating instruction: this file contains directly executable commands and verdicts — read it and run it; do not read it as reference material.

## What this terminal is

The NF desktop GUI shell was permanently retired on 2026-09-09 (recorded in `L3_FROZEN.md`), and the public surface converged to "protocol + core library + CLI". That left a vacuum in the human-computer interaction surface, and `nf shell` fills exactly that layer: it organizes the **existing** CLI command surface into an interactive session by capability menu — read a line → parse → gate → dispatch → print.

Three hard constraints (from the same root as the repository red lines):

1. **Zero third-party dependencies**: Python stdlib only; no curses (absent on Windows) and no GUI toolkit.
2. **Determinism**: the same input run twice is byte-for-byte identical (`--exec` is the regression face).
3. **Safety gate**: write-class commands are refused by default and require explicit confirmation (typing yes interactively, or an explicit `--yes`).

## Fastest start (two commands)

```sh
./scripts/nf                       # POSIX: with no arguments it enters the interactive terminal
python scripts/nf.py shell         # cross-platform equivalent (Windows can also use scripts\nf.cmd)
```

The three launch paths and what each is for (**do not mix them**): `scripts/nf` (POSIX) carries the **daemon fast path** and, together with `eval "$(nf daemon shell-init bash)"`, is a millisecond-scale client; `scripts\nf.cmd` also has a fast path (slower than the POSIX launcher) — cmd.exe has no built-in sockets, so `scripts/nf_client.py` (**pure stdlib**, started with `python -S`, importing no repository modules) performs one socket round trip on its behalf and falls back to a direct run when no daemon answers (the same contract as the POSIX launcher); `python scripts/nf.py` is the single source-of-truth entry, and the first two are only launchers for it.

Once inside: type `0`–`8` to see capability-zone examples, `/menu` to redisplay the menu, `/help` for usage, `quit` to exit.
Any command passes straight through, e.g. `nf doctor`, `nf market --list`, `nf assemble "西幻生存"`.

## Capability menu (the desktop shell’s seven zones → the CLI command surface)

| Key | Capability zone | Corresponding command surface (examples) |
|---|---|---|
| 0 | Environment self-check | `nf doctor` |
| 1 | One-command world demo | `nf demo` |
| 2 | Requirement → assembly plan | `nf assemble "<需求>"` · `nf assemble … --check <成品.md>` |
| 3 | Full-chain production | `nf run --pipeline <管线.md> --modules … [--seed]` |
| 4 | Validation and health check | `nf lint` · `nf conformance` · `nf module verify` |
| 5 | Shelf and assets | `nf market --list` · `nf asset ls` · `nf asset inventory` |
| 6 | Pipelines and modules | `nf pipeline new …` · `nf module ls` |
| 7 | Help and command surface | `nf --help` · `nf help <cmd>` |
| 8 | Write forms | `/form <id>` item-by-item prompting (13 forms, see "Write forms" below) — this zone **keeps no action literals**: the actions are projected from `FORMS` |

The menu’s source of truth is `ZONES` in `desktop/src/core/terminal.py`; **the menu may only point at real commands** — verify check39 and `desktop/tests/test_terminal.py` share one criterion and assert this line by line (`terminal.example_resolves`), so a new capability must land in the CLI before it is registered in the menu. A zone’s **actions** likewise come from the source of truth: explicit `actions`, or (for the form zone) projected from `FORMS` by `terminal.zone_action_dicts()`.

## Interactive syntax

| Input | Behavior |
|---|---|
| `0`–`8` | See the description and copy-pasteable examples of that capability zone |
| `/menu` `/zone 4` | Redisplay the menu / see one zone’s examples |
| `/find <词>` (`/search` is a synonym) | Search across **all command surfaces** (a hit gives the command + a one-line purpose; a miss gives candidates) |
| `/commands [过滤]` | List every reachable command (top-level + second-level, filterable by substring) |
| `/map [族或片段]` | **Capability map**: present every top-level command curated by capability family (8 families), filterable |
| `/complete <前缀>` · trailing `Tab` | **Completion**: commands / second-level subcommands / flags / slash commands / capability-family prefixes |
| `/history [n]` | View history (the most recent n entries); `quit` and Tab lines are not recorded |
| `/set [k=v …]` | Change view settings (`color` / `width` / `limit`); with no arguments, print the current values |
| `/form [id]` | **Write form**: without an id, list all; with an id, start item-by-item prompting (fill in every parameter → assemble the command → second confirmation) |
| `/cancel` | Abort the in-progress form / action (nothing is written to disk) |
| `/help` or `/help <cmd>` | Delegate to the CLI help surface (equivalent to `nf help …`) |
| `nf <args…>` or `<args…>` | Pass through to the CLI (the `nf` prefix is optional) |
| `quit` `exit` `q` `退出` | Exit the session |

Robustness (the few things a top-tier CLI terminal is expected to have): **Ctrl-C cancels only the current line, it does not kill the session**; a trailing `\` **continues the line** (multi-line commands); an in-line `#` starts a comment (a `#` inside quotes is preserved); a mistyped command gets a **typo suggestion** (edit distance ≤ 3) instead of sixty commands’ worth of usage dumped in your face.

## Command-surface search (discoverability for "the fullest feature set")

The bottleneck of a terminal was never a shortage of commands but **not being able to find them** — the CLI has 64 top-level commands and 135 entries including second-level ones. Three entry points solve this:

```bash
python scripts/nf.py shell --map                 # capability map: partitioned by capability family, covers all commands
python scripts/nf.py shell --map 治理            # show only one family (also filterable by command fragment)
python scripts/nf.py shell --commands            # list every reachable command (top-level + second-level)
python scripts/nf.py shell --commands asset      # filter by substring
python scripts/nf.py shell --search 装配         # search by keyword (exit 2 on a miss, scriptable)
python scripts/nf.py shell --verify              # terminal self-check (index / curation / menu faces, the exit code is the verdict)
python scripts/nf.py shell --verify --deep       # live tier: really run one read-only command + landing-point writability + environment facts
python scripts/nf.py shell --verify --json       # machine face (pure JSON: ok / issues / stats)
python scripts/nf.py shell --complete "/ma"      # slash-command completion → /map, /menu…
python scripts/nf.py shell --complete "nf layers --"   # flag completion → --json / --verify / --write
python scripts/nf.py shell --history <文件>      # cross-session history (defaults to <NF_HOME>/shell_history)
```

The in-session equivalents are `/map [族]`, `/commands [过滤]` and `/find <词>`. Three layers ensure that "fullest" is not just a claim:

① **The index is derived from the CLI’s argparse surface** (the terminal keeps no second command table); ② **the capability map places every command in exactly one family** (`start / forge / shelf / verify / library / govern / integrate / meta`), and anything "uncurated" is reported; ③ the criterion has a **single source** — `nf shell --verify` (for humans) and verify check39 (for the gate) call the same `terminal.self_check`, so "the terminal says it is fine" and "the gate says it is fine" always mean the same thing.

## Live self-check and machine faces

### Top-tier CLI baseline (checkable item by item, not adjectives)

```bash
python scripts/nf.py shell --baseline          # run the evidence commands line by line and give a verdict (17 items)
python scripts/nf.py shell --baseline --json   # machine face (pure JSON: ok / stats / rows)
```

The baseline’s source of truth is `TERMINAL_BASELINE` in `desktop/src/core/terminal.py`: each line = one capability + **one evidence command** (+ fragments that must appear / must not appear + the expected exit code, and where needed + stdin input + **a file expected on disk**). The current **20 lines** cover (the table below groups them by theme — the 4 write-gate lines are merged into one item; see `terminal.py` for the line-by-line list): command-surface reachability / keyword search / capability map / typo suggestion / **write gate (should be refused)** / **recursive long-running interception (should be refused)** / completion / length-limit notice / no color on non-TTY / script face / **history replay** / **history written to disk** / **session persistence** / **menu↔family cross-labeling** / form dry-run / pure-JSON machine face / live self-check.

Four disciplines: ① evidence lines **only read the repository** (a flag such as `--write` / `--apply` / `--yes` makes the baseline itself fail the line); ② a line may declare "should be refused" (`expect_exit: 2` + the reason for refusal), which brings the safety surface inside the baseline too; ③ interactive-mode evidence (history/session) expands the `{TMP}` placeholder into the fixed directory `<临时目录>/nf_baseline` under the **system temp directory** (outside the repository; a fixed name avoids `mkdtemp` piling up here because it cannot be deleted in this environment), and uses "a file expected on disk" to assert that the state was **really written**; ④ verify check39 asserts the same table line by line — **the completeness of "top-tier CLI parity" is checkable item by item**, not a matter of impression.

- **`--verify --deep` (live tier)**: on top of the static faces (index / curation / menu), it additionally checks **the local environment and executability** — ① really run one read-only command (`nf layers --verify`) and check the exit code; ② run `nf <cmd> --help` **for every command** (currently 64, read-only, about 11 seconds) and check the exit codes — this upgrades "the fullest feature set" from "findable in the index" to "the commands really run"; ③ probe the **writability** of the history/session landing point (judged along ancestor directories, **no probe file is written**); ④ report the current TTY / readline / pager situation honestly. All conclusions use the same conventions as the static tier (`terminal.deep_check` calls `self_check`), and the exit code is the verdict.
- **Machine faces (`--json`)**: `--commands --json` (per-command + summary + flags), `--map --json` (family partition), `--form --json` (form source of truth) / `--form <id> --json` (assembly-plan argv), `--verify [--deep] --json` (ok / issues / stats). **The output must be pure JSON** — live output is captured into a field rather than mixed into stdout, and check39 asserts exactly that.

- **Face discriminator key (all-command convention · closed 2026-10-01)**: on any face that declares `--json`, a successful output is always an **object** whose top level carries the face discriminator key `kind` (protocol-document faces use `schema`); a failure is always `{"ok": false, "error": … , "exit": N}`. Previously two envelope generations coexisted (actually running the 64 `--json` faces that can run without arguments: 17 carried the key / 47 did not, and 7 of those were bare arrays — success returns an array, failure returns an object, so a consumer **could not tell them apart**); this round unified them. **The only exemption is `nf interop`**: what it exports is third-party standard documents (OpenAPI / AsyncAPI / SPDX / CycloneDX / in-toto / VC / C2PA / CID) and it **must not** add NF private keys (doing so is judged out of bounds by the official meta-schema, measured in AUD-0010); instead it identifies itself by the specification’s own version key. Criterion: `desktop/tests/test_cli_json_face.py` (static dictionary faces + dynamic real runs + exemption faces named one by one).

- **Success faces must not echo back local absolute paths (closed 2026-10-01)**: the same discipline previously lived only in failure messages (`_no_machine_paths`), committed files (`conformance_report._c_public_surface`) and `test_leak_surface`; in practice three **success faces** — `nf doctor --json` / `nf toolface --json` / `nf daemon status --json` — still wrote `C:\\Users\\<用户名>\\…` verbatim. They now use **repository-relative** paths (doctor details, toolface’s `source`) or a **portable form** (the daemon’s `root` / `state_file` → `~/…`, see `_portable_path`). The criterion is folded into `test_cli_json_face` (it scans both the machine faces and the human-readable faces for the shape of a local path).

## Single source of truth · many views (projection faces)

The terminal surface has only **one source of truth**: the curation tables in `desktop/src/core/terminal.py` (`ZONES` capability zones + action catalog / `FAMILIES` capability families / `FORMS` write forms / the three write-gate tables / `BLOCKED_IN_SHELL`), plus the argparse surface in `scripts/nf.py` (a command’s **existence**). Everything else is a **projection** of it:

| View | What it presents | Entry point |
|---|---|---|
| Line-mode terminal | menu examples / capability-family map / write-form item-by-item prompting | `nf shell` (the sections above in this file) |
| Full-screen TUI | action catalog (including the **write-form zone**: each of the 13 forms is an enter-to-run action) | `python tui/nf.py` |
| Machine face | whole-surface snapshot (JSON) | `nf shell --surface --json` |
| Generated artifact | offline input for the full-screen view (zero core dependencies) | `tui/_surface.py` |

```bash
python scripts/nf.py shell --surface            # human-readable face: list actions and gate counts zone by zone
python scripts/nf.py shell --surface --json     # machine face: kind=nf-terminal-surface
python scripts/nf.py shell --surface-write      # regenerate tui/_surface.py (must be run after any source-of-truth change)
```

Three disciplines:

1. **A view may not keep a second table.** The full-screen TUI is frozen into a single-file exe and cannot import core, so it used to hand-copy the command whitelist / gate table / action catalog — and the hand-copied gate table missed the "command + flag writes" pairing table (`terminal.CONFIRM_FLAG_PAIRS`), letting write faces such as `nf interop --all` **execute in the full-screen view without confirmation**. Now the TUI only does `import _surface` (the generated artifact), and the convention is held solely by the source of truth; a view may **explicitly** tighten further (e.g. the TUI lists the whole `daemon` family as refuse-to-run, with the reason in `TUI_EXTRA_LONG_RUNNING` — view policy, not a fork).

2. **A projection must be reconcilable.** `tui/_surface.py` is a **generated artifact** (its header states the source of truth and the regeneration command). If the source of truth changes without regeneration ⇒ both `nf shell --verify` and verify check39 turn red: the projection is recomputed and compared **byte for byte** against the file present, reporting the first mismatching line and giving the regeneration command.

3. **A view’s convention may only be stricter, never looser.** check39 compares item by item: the full-screen view’s write flags / write verbs / command + flag pairings must **cover** the three source-of-truth tables; the command whitelist must match the argparse surface; an action’s `argv[0]` must be a real command; the number of capability zones must match the source of truth. Write faces on the view side are gated too: an action materialized from a form must be judged `write` (enumerated line by line in unit tests), and an empty optional parameter is dropped together with its flag (the same convention as `terminal.build_argv`, to avoid leaving a dangling `--reason`).

Where the criteria live: `verify.sh` check39 (projection byte-for-byte + the view no weaker than the source of truth), `desktop/tests/test_terminal.py` (`TerminalSurfaceTest`), `desktop/tests/test_nf_tui.py` (`SurfaceSingleSourceTest`), and `python tui/nf.py --selftest` (the two lines "gate convention (single source)" and "projection same source").

## Write forms and session state (repo-changing actions are driven safely by a human)

Every write command of `nf` needs complete parameters + `--yes`, which is a burden for a human. The terminal breaks it into **item-by-item prompting**: `/form <id>` starts it, one item at a time (an optional item is **skipped with a blank line**), and once everything is filled in it prints the **assembled command** and asks `yes/no`, executing only after confirmation — and it still goes through the same **write gate** in the end (the terminal does not bypass it). The current **13 forms** cover the common write points: `deprecate-module` / `restore-module` / `types-write` / `stats-write` / `asset-add` / `register-apply` / `rename-apply` / `receipts-write` / `preset-save` / `library-deprecate` / `library-restore` / `pipeline-new` / `approve-subject`. **Every other write face is registered one by one in `terminal.FORM_EXEMPT`** (stating why no form is built for it), and the criterion guarantees that "every write face in the gate table either has a form or has a reason" — a new write face entering the gate without anyone remembering to pair a form turns red.

These 13 forms are **also the full-screen view’s actions**: zone 8 of `ZONES` (`id=forms`) is marked `forms: True`, and its actions are projected from `FORMS` by `terminal.zone_action_dicts()` — so "there is only one form source of truth" (editing a form edits both views, with no second registration). A parameter with `kind: "path"` in a form step becomes a **path parameter** in the full-screen view: it is appended to argv only after passing the repository containment criterion.

It also works non-interactively (dry-run first):

```bash
python scripts/nf.py shell --form                                # list all forms
python scripts/nf.py shell --form stats-write                    # assemble + print only (dry-run)
python scripts/nf.py shell --form deprecate-module --answer file=community/x/M1.md --answer reason=重复
python scripts/nf.py shell --form stats-write --yes              # only an explicit go-ahead really executes
```

- **Parameter source of truth**: the `{key}` in a form template is filled by a step; a template may only point at a **real CLI verb** (asserted by check39), and an empty value is dropped together with its flag (no dangling `--reason`). A **boolean flag** is expressed as a "single placeholder": put `{key}` in a cell by itself; filling in `--force` carries it, leaving it blank drops it (see `preset-save`).
- **Second confirmation**: `yes/no` in interactive mode; non-interactive mode requires an explicit `--yes` (the default is dry-run only).
- **Session state**: `--session <文件>` persists view settings and the last partition (written to disk immediately after `/set`). Guard: the path must be **absolute** and **must not fall inside the repository** — a state file left in the repository gets swallowed by `git add -A` (a tmp-file incident was actually observed on 2026-09-26).

## Efficiency (making "fast" a criterion too)

The terminal’s two kinds of efficiency each have their own criterion:

**① In-process overhead (mechanism cost)**

- **The command surface is built only once**: building the argparse surface measured **96–118 ms each**, while one terminal command used to build it 3+ times (index + command tree + actual parse), and `--verify --deep`’s all-command scan as many as **64 times**. Now `_build_parser()` / `_collect_cli_tree()` / `_shell_command_index()` are all cached in-process.
- **`--version` short-circuit**: the most frequently called probe command no longer builds the command surface (its output is word-for-word identical to argparse’s version action).
- **Width-query cache**: `char_width()` carries `lru_cache(4096)` — list rendering is a hot path that asks for the width character by character.
- **Abstraction-ladder source-face expansion (v13)**: `nf layers --verify` is the only read-only command that still has a ~1 s fixed cost, and the cost is almost entirely glob expansion — L1/L2/L3 of `_rule_issues` expand the same batch of 43 patterns repeatedly (about 10.5k `stat` calls), and L6 also runs a full `ast.parse` over core. Now: within each scan the expansion is cached per pattern, each subtree is `os.walk`ed only once + glob→regex matching (character classes and other proprietary semantics fall back to the reference implementation), and L6 pre-filters on text before parsing the AST. The fast path is **equivalent pattern by pattern** to the reference implementation (the source of truth’s 43 patterns + 5 shapes: character classes / `?` / `**` / fixed files / empty subtrees; 0 mismatches), and the four-tier face scale is unchanged (contracts 52 / assets 2218 / engines 256 / exports 26).
- **Core-scan deduplication (v14)**: read-only commands outside the terminal were tightened under the same discipline — `nf conformance` used to **run the eighteen contracts twice** (compare, then print), now only once; in `nf doctor`, the machine-contract blocks of 248 module documents were parsed **496 times** (74% of the health check), now parsing is cached by **the text itself** (change the text and the key changes, so no staleness risk); the pipeline dry-run’s `sweep()` built a full-repo module index once per each of 228 pipelines (≈56k disk reads), now it is built once; the purity scan walked the same tree four times, now **one parse + one walk** gathers all four kinds of fact; the breadth proof called `Path.resolve()` (a Windows syscall) once for the cache key of every combination, now it uses `os.path.abspath` — **saving 3.8 s across 6888 combinations**. Equivalence is held by item-by-item comparison with the reference implementation (purity issues/stats fully equal, breadth combination count and well-formedness fully equal).
- **Recomputation on identical text switched to content-keyed caching (v15)**: the asset-reference census (1499 keys × 3.5 MB of exact per-key counting ≈ 2.9 s) is cached by the **sha256 of the corpus and the key set** — the key is content, not path, and changes as soon as the content changes, so there is no staleness risk; the second census within the same process went 2.94 s → 0.88 s. Two purely duplicated I/Os were also fixed: `conformance_scan` used to re-read registry.json inside the loop for **every community pack** (112 times), and `asset_density._keys_of` used to re-read text the caller had just read. **Two "speedups" were rejected by measurement**: `bytes.count` is slower (UTF-8 dilution), and a single-pass alternation undercounts when keys overlap at the same position (it makes "zero-reference keys" falsely zero) — exact semantics come first.
- **Unified YAML loader switched to libyaml (v16)**: attribution found that the remaining YAML cost was **not duplicate parsing but a slow parser** (`schema_lint`’s 473 parses had zero duplicates, and `concept_graph`’s 102 concept graphs were genuine parses). `CSafeLoader` measured **7.8× faster** than `SafeLoader`; a shared entry point `conformance_scan.load_yaml()` was added (libyaml first, falling back to pure Python when absent), and four hot parse sites were folded in. Equivalence was **shown block by block**: for the repository’s 1395 YAML text blocks (584 files) the two loaders’ results and exception behavior are **fully equal** (now frozen as a regression assertion). The first version used `yaml.load(...)` and was judged a CWE-502 dangerous sink by the project’s own purity criterion R6 — it was changed to instantiating the safe loader directly (the same semantics as `yaml.safe_load`), not to calling the banned surface back.

Measured (this machine, single runs):

| Scenario | Before | After |
|---|---|---|
| `nf shell --verify --deep` (64 `--help` runs + one `layers --verify`) | ~11.3 s | **~1.9 s** |
| `nf shell --baseline` (17 lines, one by one) | seconds-scale (dragged down by rebuilds) | **1.95 s** (16 lines ≤ 4.3 ms) |
| `nf shell --commands` (cold start) | 363 ms | **281 ms** |
| `nf --version` (cold start) | 223 ms | **242 ms** (of which interpreter ~60 ms, file execution/AV ~100 ms, imports ~20 ms) |
| `nf layers --verify` (abstraction-ladder full-repo scan) | ~1.18 s | **~0.5 s** (`layer_model.scan` 801 ms → 281 ms) |
| `nf conformance` (eighteen contracts + on-disk comparison) | ~40 s | **~5.1 s** |
| `nf doctor` (environment health check) | ~1.0 s | **~0.94 s** (in-process 1.97 s → 0.69 s) |
| `nf score` (four signal paths + depth scan) | 17.1 s | **13.3 s** (breadth proof 4.86 s → 0.30 s) |
| `nf shell --baseline` (in-process, 17 lines) | 1.95 s | **0.38 s** |
| `nf score` (after v15) | 13.3 s | **12.6 s** (the census is not recomputed for identical content) |
| Full unit-test suite (1241 cases, the main cost of `verify` check12) | 253.3 s | **206.8 s** |
| Scale regression case for 300 holdings (`library.search`’s O(n²)) | 25.4 s | **1.07 s** |
| `nf conformance` (after v16, unified YAML loader) | 5.1 s | **3.1 s** |
| `nf score` (after v16) | 12.6 s | **9.3 s** |
| Full unit-test suite (after v16) | 206.8 s | **187.3 s** |

**② Latency budget (each baseline line carries its own `max_ms`)**

`nf shell --baseline` now **times every evidence line** and shows it alongside the human-readable output (`✔ … 1.7 ms nf shell --commands …`): a light line’s default budget is **300 ms** (measured ~1–2 ms, a 100× margin, still enough to catch regressions such as "the parser cache stops working → grows to the ~300 ms range"), while the `--verify --deep` line gets **6000 ms** on its own (recalibrated from measurement on 2026-09-29: that line’s main cost is the **full-repo abstraction-ladder scan** `nf layers --verify` — ~0.5–1.7 s idle, 2.4–3.7 s on this machine fully loaded; the old calibration’s premise of "~320 ms in-process, a 6× margin" no longer holds, and 2000 ms left only a 1.15× margin, going green on one run and red on another on the same tree. 6000 ms ≈ a 3.5× idle margin, and still enough to catch an order-of-magnitude regression such as "the all-command scan grows back to ~11 s"), and **a line over budget is measured twice more and the smallest sample is taken** (min of N is this repository’s standing performance convention — the budget measures mechanism cost, not this machine’s mood at the time). Over budget means the line fails → check39 red → it does not go up.

**③ Fewer keystrokes (user efficiency)**

- **Unique-prefix completion**: typing `scor` completes to `score` automatically (this applies only when there is **exactly one candidate**, and it is marked explicitly; with ambiguity it still gives a typo suggestion and does not guess and execute — for example `stat` hits both the stats and state-front candidates).
- Together with the existing completion (Tab / `/complete`), history replay (`!!` / `!n` / `!前缀`), the capability map and search, common actions take single-digit keystrokes.

**④ Read shape (making "no duplicate reads" a criterion)**

A wall-clock assertion jitters on CI / concurrent machines, but "how many times the same file is read within one scan" is **deterministic** — so the defect class fixed this round is pinned down as read-count criteria: `library.search` over 300 holdings has **≤ 2 reads per file and a total read count linear in the number of files** (a mutation sample further shows the bound catches the old implementation’s O(n²) shape); one depth scan has **≤ 14 reads for any single file** (measured mean 3.5, max for a single file 9). A regression of the same kind (re-running a full read for every entry / every result) turns red immediately, instead of "just getting slower".

## Output experience (column width / length limit / coloring / paging)

- **Column alignment**: CJK and emoji are counted as **display width 2** (`display_width` / `pad_to` / `clip`), so two-column lists do not skew in a CJK terminal; the width comes from `--width`, otherwise the `COLUMNS` environment variable, otherwise 100.
- **Length limit and notice**: `--limit N` (0 = all) applies to long lists, and truncation explicitly says "… M more (`--limit 0` to see all, or add a filter word to narrow down)", never truncating silently.
- **Restrained coloring**: `--color=auto|always|never` (default auto). auto colors **only on a real TTY with `NO_COLOR` unset**; `NO_COLOR` vetoes auto outright, while `always` is an explicit request and is unaffected by it. In-session, `/set color=never` turns it off at any time.
- **Determinism contract (hard)**: non-TTY (pipe / CI / test / `--exec` / `--file`) is always **colorless, unpaged and byte-for-byte reproducible** — verify check39 directly asserts that the default output contains no control characters.
- **Optional paging**: only `--pager=auto` takes over long output, on a real TTY and when `less` / `more` are present; the default is `never` (guaranteeing redirection and diff-ability).

## Completion and history (zero-dependency convention)

The feel of a top-tier CLI comes down to two things: **you can complete half-typed input** and **you can scroll back to the previous round**. NF makes both **criteria** rather than platform features:

- **Completion**: `complete()` is a pure function (usable on any platform: `/complete <前缀>`, a trailing `Tab`, `nf shell --complete`), and its candidates cover commands / second-level subcommands / flags / slash commands / capability families; on POSIX, if `readline` is available it takes over Tab automatically (`install_readline`), and on Windows, where that module is absent, it falls back to a candidate list — `nf shell --verify` honestly reports which path is currently in use.
- **History**: written to `<NF_HOME>/shell_history` only in **interactive mode** (`--history <文件>` changes the path, `--no-history` turns it off); `quit` and Tab lines are not recorded; `--exec` / `--file` **never write it** — script-face determinism is a hard contract (a unit test directly asserts that `run_lines` has no history hook).

Three classes of command are **not executed** in-session (to avoid hanging the terminal): `serve` (the long-running MCP service), `lsp` (the resident stdio service, waiting for the editor to send Content-Length frames — the same type as `serve`, added 2026-10-01) and `shell` (a recursive session; `nf terminal` is its alias and is blocked the same way) — the terminal only gives guidance; open another terminal or let your IDE start it.

## Write gate

**Source of truth = the three tables in `desktop/src/core/terminal.py`** (`CONFIRM_FLAGS` / `CONFIRM_VERBS` / `CONFIRM_FLAG_PAIRS`); this page gives only the convention and an **excerpt** list, and the criterion checks that every item appearing on this page is really in the tables (guarding against documentation drift). Matching any of the following forms marks a write / irreversible face, refused by default (exit code 2 + remediation guidance):

- Flag markers: `--write` `--apply` `--register` `--force` `--out` `--dest` `--build`, plus those that **do not have `--write` in the name but write to disk just the same**: `--write-baseline` (`nf score` re-signs the regression baseline; `nf asset baseline` re-signs with `--write`), `--fix` (`nf lint` mechanical fix edits source files in place), `--harvest` (`nf module types` writes the event payload registry), `--write-advisory` (`nf pipeline dryrun` writes the pipeline advisory ledger), `--certify` (`nf combine plan` writes the combination certificate), `--save` (`nf assemble` writes an archive file **that you name**, which may be a repository-relative path ⇒ the same class as `--out`), `--surface-write` (`nf shell`’s **own** generator flag: it projects the terminal-face source of truth into `tui/_surface.py`; reachable only from the CLI’s top level — `shell` is refused in-session)
- Verbs (**they change repository files directly even with no flags at all**): `register` / `import` / `rename` / `release` / `approve` (writes `protocol/approvals/*.json`) / `asset add|rm|deprecate|restore` / `module deprecate|restore|signature` / `pipeline new` / `decisions reindex` / `patterns reindex` / `knowledge transform` (writes `protocol/transform_log.json`) / `library reindex|deprecate|restore|supersede|attest`

- Command + flag pairings: `interop --all` (writes `results/interop/*`; the identically named `interop --check` is read-only and is not blocked — likewise `pipeline dryrun --all`); `--trace` / `--session` **count as writes only on `nf assemble`** (they write a file you name) — `nf knowledge frequency --trace` is a **read**, and `nf shell --session` has its own hard gate ("must be an absolute path and must not fall inside the repository"), so neither is blocked

There are only two ways to let it through: answer `yes` in place in an interactive session (which lets through only that one run), or pass an explicit `--yes` from the caller.

**Which face the gate guards (convention)**: it guards only **text-driven** faces — interactive input, `nf shell --exec`, `nf shell --file` (all three may carry **pasted/injected** text, and the machine does not decide for a human whether "this line should run"). The **explicit-argv** face has no such gate: a direct `nf <cmd> …` run and `nf daemon exec <argv>` are equivalent to a command the operator typed themselves (the latter’s documentation states outright that "the output/exit code match a direct run"). Measured contrast: `nf shell --exec "nf stats --write"` → exit 2 (refused), and adding `--yes` lets it through; `nf daemon exec stats --write` → runs as-is.

## Non-interactive mode (CI / scripts / regression)

## Persistent execution layer (`nf daemon`) — millisecond-scale response

Every `nf <命令>` starts an interpreter. Measured on this machine (2026-09-29, min of N): **bare interpreter 47 ms**, `nf --version` **215 ms** — the fixed cost ≈ interpreter startup + imports (~10 ms) + **argparse command-surface construction (measured 117 ms, 65 subcommands)**. `nf daemon` moves execution into a resident process, and the client does a single socket round trip (in a hot process, `--version` **1.5 ms**; measured with bash’s built-in `$EPOCHREALTIME`, zero forks, no `date` bias).

| Path | `--version` | `stats --check` | `doctor` |
|---|---|---|---|
| python direct run (original path, one interpreter per command) | 215 ms | 288 ms | 634 ms |
| `scripts/nf` launcher (**no daemon**: falls back to a direct python run) | 296 ms | 365 ms | 713 ms |
| `scripts/nf` launcher (through the daemon) | 48 ms | 48 ms | 48 ms |
| **bash function (zero subprocess, through the daemon)** | **1.5 ms** | **1.6 ms** | **1.6 ms** |

The launcher itself now has only **the bash startup floor (~39 ms on this machine) + one socket round trip** left. Before the fix it was **164 ms slower** than "a direct python run of the same command" — all three fixed costs were charged **per command**: external `dirname` + subshell ≈58 ms, one command substitution (the Store-stub path test) ≈30 ms, and the final decision to "really start an interpreter" ≈60 ms (hitting the Microsoft Store alias stub for real costs ~300 ms). After changing the three to parameter expansion, per-platform selection (Windows wants `python` first), and **caching** the final decision by "interpreter name + platform": the launcher through the daemon went **175 ms → 48 ms**, and without a daemon **428 ms → 296 ms**. The criterion is the **number of interpreter launches** (a shim is placed on PATH: it records one count before forwarding to the real interpreter, independent of machine speed) — a fast-path hit is **0 launches**, a fallback is **exactly 1 in steady state** (2 per command before the fix), and when `python3` is a stub it must switch to the one that runs (`test_launcher.InterpreterLaunchBudgetTest`).

> **2026-10-02 re-measurement under the same convention (min of 5, same method)**: bash floor **40.8 ms**, `scripts/nf --version` through the daemon **71.9 ms** (not a single interpreter launched), without a daemon **260.9 ms** (exactly 1), `python scripts/nf.py --version` **189.3 ms**. That is, the components of the table’s "through the daemon 48 ms" are now **floor 41 ms + socket round trip ≈31 ms** (the round trip was ≈9 ms back then), while the combination (floor + one round trip) is unchanged; "without a daemon 296 ms" is the same order of magnitude as today’s 261 ms.
> A convention reminder: the numbers in this section are **dated measurement records**, not promises — the **mechanism face** (how many interpreters the fast path launches, how many the fallback launches in steady state) is deterministically guarded by `test_launcher.InterpreterLaunchBudgetTest`, while **wall-clock numbers** drift with machine and load, so when re-measuring, keep to the method of "measuring wall clock + launch count in the same round" (the first version measured only wall clock, not compared against launch count in the same round, and once read the no-daemon path as the same speed as the fast path).

Residency is just as effective for **heavy commands** (content-keyed caches persist across requests; measured on this machine, min of N):

| Command | Cold-start direct run | Daemon steady state |
|---|---|---|
| `nf score` | 7.5–8.4 s | **~3.5 s** (after derived results are content-keyed) |
| `nf doctor` | 697 ms | **212–385 ms** (within same-machine jitter) |
| `nf conformance` | 3.07 s | **2.19 s** |

The criterion face (all in check12, machine-independent): AST-fact **content-key** semantics (identical text hits / edited text recomputes), the next scan after an edit must see the new result, resident reuse (**counting `ast.parse`**: the second time permits only the very few from L6 pre-filtering, an order of magnitude fewer), and **the launcher fast path beating a direct python run (3× on POSIX)**.

Command-surface latency panorama (24 representative commands; cold = a fresh process’s direct run, daemon = resident hot run; measured on this machine):

| Command | Cold | Daemon |
|---|---|---|
| `nf score` | 7729 ms | **3624 ms** |
| `nf conformance` | 3202 ms | **2403 ms** |
| `nf layers --verify` / `nf doctor` / `nf pipeline dryrun --all` | 550 / 716 / 555 ms | **304 / 227 / 204 ms** |
| `nf interop --check` · `nf toolface` · `nf module ls` · `nf worldmodel` · `nf stats --check` | 384 / 407 / 305 / 400 / 315 ms | **135 / 132 / 131 / 100 / 89 ms** |
| The other 14 (audit / decisions / receipts / sig / patterns / library / cognition / state-front / knowledge / market / output / assertions / approve / domain) | 225–313 ms | **2–41 ms** |

That is: **apart from two "full-repo tools", the whole command surface is down to the millisecond / hundred-millisecond range**; the exit codes of all 24 match a direct run one by one. This panorama is guarded by a criterion too — the **open-file count for the 11 light commands is ≤ 60** (measured 0–36, against about 2354 files in the repository); anyone who stuffs a full-repo scan into a light command turns check12 red on the spot.

**The heavy command’s cost structure** (hot run of `regression_score.evaluate`): **reading + opening files ≈25%**, **metadata (stat/scandir etc.) ≈35%**, **computation ≈40%**. Cross-call **content-keyed** caching (fenced YAML / reference census / derived results) and **sharing the corpus within one read-only call** (read cache + directory-walk/subtree-listing caches, both cleared on exit) bring this bill down to a measured **~2.0 s** (2461 opens, 2456 distinct files — within one read-only call the corpus is essentially read once).

### No recomputation: directory watching + response cache (`nf daemon start --watch`, optional)

The path of "inferring whether something changed from mtime/size" was explicitly rejected (an unchanged fingerprint ≠ an unchanged file; Windows timestamp granularity ~15.6 ms). This wave takes a path that **does not ask "does it look changed" but only "has it changed"**: the daemon installs a directory watcher (on Windows: `ReadDirectoryChangesW`, recursive over subtrees), maintains a **tree generation**, caches the **entire response** of read-only commands by `(argv, cwd)`, and **reuses it only when the generation is unchanged**.

| Path | `nf score` |
|---|---|
| Cold-start direct run | 7.7 s |
| Daemon steady state (a genuine recompute every time) | ~2.2 s |
| **Daemon + `--watch` (tree unchanged → whole-response reuse)** | **~0.18 s** (the difference is `bash scripts/nf`’s process startup) |
| Same, with the zero-subprocess client | **5 ms/run** (3 rounds × 20 samples; protocol round trip, no subprocess) |

Measured (this machine): running `nf score` twice in a row on the same tree → **6816 ms / 176 ms**; after adding and deleting a temporary file in the repository → **2087 ms (recompute)**, and running once more → **177 ms**.

Disciplines (fail-closed, all with criteria):

- **Treat "a change notification was received" as the only "it changed"**: watcher unavailable / handle invalidated / thread exception → the cache is disabled wholesale (no hits, and old entries are invalidated along with it), with behavior identical to an ordinary daemon; a buffer overflow is honestly reported as `overflowed` and makes the generation jump (better to invalidate everything than to answer wrongly).
- **If the daemon itself has executed a "non-admitted" command ⇒ invalidate the whole cache immediately**, **without waiting for the watcher thread to notice asynchronously**: invalidation used to rely only on the watcher’s few-millisecond window, and a scripted back-to-back run like `nf conformance --write; nf score` could fall inside that window and get the pre-write stale response (a deterministic criterion guards this, not timing). **The residual window is honestly recorded**: when an external process changes the repository and a request arrives a few milliseconds before the watcher notices, it may still hit a stale response — this is inherent to a notification-based cache; daemon-side writes have already been made **deterministic** to invalidate by the rule above.
- **Two fail-closed gates (a successfully opened handle ≠ notifications will arrive)**: ① **volume type** — enabled only on local fixed disks (notification semantics on network shares SMB/UNC are unreliable and silently drop events → the generation would never advance = permanently replaying old results); ② **mechanism self-check** — at startup it really exercises "create / modify / delete" in a **temp directory**, and the watcher counts as usable only if all three notification kinds arrive. Failing either one means "watcher unavailable" and the cache is disabled wholesale. The cost is measured at only ~70–90 ms (`nf daemon start --watch` 565 → ~650 ms, one-off).
- **Changes under `.git/` do not invalidate the response cache**: everyday `git status/add/commit` writes to `.git/`, and if those invalidated as before, every git command would push the next `nf score` back to a ~2.2 s recompute (measured: before the fix, after a `.git` probe, a mean of **151 ms**; after the fix, **10 ms**). The safety premise is a **criterion-backed fact** — tracing every open and attempted open in one `evaluate`, paths containing `.git/` must be **0** (measured 2560 files in the repository, 0 under `.git`), and the cached read-only commands do not call git. A mixed batch, an unparseable path, or a buffer overflow **all turn dirty as before** (only the case where "this entire batch falls inside the ignore face" is ignored).
- **The admission list is by argv prefix** (not by top-level command name): only forms that are **purely read-only and byte-for-byte reproducible on the same tree** are cacheable — `--version` / `score` / `conformance` / `layers` / `stats` / `doctor` / `interop` / `toolface` / `assertions` / `cognition`, plus `patterns ls|show|for|verify` / `module ls|status|verify` / `decisions verify|show`. Anything carrying a write switch such as `--write` bypasses it entirely.
  "By prefix" is mandatory: top-level commands such as `module` / `decisions` / `patterns` **have both read and write subcommands** (`module deprecate`, `decisions reindex`, `patterns reindex`), and admitting by top-level name alone would let the write forms in too. Both admission criteria are executable: ① running twice in a row on the same tree gives byte-identical exit code / stdout / stderr; ② `git status` is unchanged before and after running each one (the 12 candidates measured were all both clean and reproducible).
- **This wave implements Windows watching only**: on other platforms `watch.available()` is false and the daemon degrades automatically — no code is written for platforms it has not run on.
- **Autostart (on by default · non-blocking; `NF_AUTOSTART=0` disables it)**: when no daemon is running, the launcher **throws a `--watch` daemon into the background**, and **this command still goes through a direct python run without waiting for it** (`daemon` / `shell` / `terminal` / `serve` / `lsp` do not go through the daemon anyway and do not trigger it). **Why it is on by default**: starting a daemon takes ~0.65 s, but starting it in the background **does not consume this command’s time** (the first command only pays one extra fork ≈10 ms), and **from the second command onward, commands land on the daemon fast path**. Measured (this machine, 7 consecutive runs each, median; **numbers vary by machine, for order-of-magnitude reference only**): `python scripts/nf.py stats --json` **≈223 ms** (a cold interpreter start per command) · `bash scripts/nf stats --json` **≈123 ms** · `scripts/nf.cmd stats --json` **≈194 ms** (since 2026-10-01 it takes the fast path via `scripts/nf_client.py`; **previously ≈391 ms**). The `.cmd` tier is still **slower than the POSIX launcher** (one extra cmd.exe shell, and ≈40 ms more than its own client `python -S scripts/nf_client.py` ≈155 ms) — the millisecond tier is the POSIX launcher `scripts/nf` with `eval "$(nf daemon shell-init bash)"`. The default path is therefore millisecond-scale for "agents making dense repeated calls"; if you only run one-off commands and do not want a resident daemon, `NF_AUTOSTART=0` turns it off (`nf daemon exec` has the same semantics: it starts one by default, and `--no-start` refuses).

### No re-reading: resident corpus + directory index (invalidated **precisely** by watcher changes)

The response cache only covers the "tree unchanged" tier; what about **after one file changes**? Measured (this machine, min of N): running `nf score` immediately after an edit, the **first** one in the daemon takes **1.6–2.0 s** — because those shared corpus caches have "one call" as their scope boundary, so the next request has to **re-enumerate** the whole corpus (1484 directories / ~2000 `scandir` calls) and **re-read** it (~2500 opens), when often only one file actually changed.

This wave adds a **resident layer** (`conformance_scan._RESIDENT`: text + directory entries), installed only when the daemon has a **healthy watcher**, covering only files **under the watch root**, and invalidated **only by the known paths the watcher provides**: text is deleted per file, directory entries per parent directory (an add or a delete both change the parent’s listing). **If it cannot be stated clearly, invalidate the whole batch** (buffer overflow / an unparseable path / a generation bump with no paths given).

| Scenario (daemon hot run, the first `nf score` right after an edit) | Resident layer off | Resident layer on |
|---|---|---|
| Editing a file such as `CHANGELOG.md` that is **not on any input face** | 1591 ms | **872 ms** |
| Dropping a file into `04_模块库/通用类/` (**landing inside an input face**) | 1625 ms | **951 ms** |

(Same machine, median of 3 rounds each; the switch is `NF_NO_RESIDENT=1`, which reverts to the old behavior for comparison at any time.)

Why it **trusts nothing more** than the response cache: the response cache already relies on the same criterion, "generation unchanged ⇒ tree unchanged", and that criterion is guarded by the volume-type gate + mechanism self-check + overflow reporting. The resident layer merely applies the same trust to more data, and it **adds no new invalidation path** — when the watcher cannot state things clearly, it invalidates the whole batch, which is more conservative than the response cache (which keeps the old response but bumps the generation). Criteria (deterministic, no wall clock): the change face reports paths and refuses to pretend to know (`DirWatcherTest`), the layer covers only files under the root, a known path given must invalidate immediately, an unclear case must zero the whole batch, and the daemon really installs it and zeroes it after `_bump()` (`ResidentLayerTest` + `WatchDaemonIntegrationTest`).

The next layer down is **derived results**: a scanner’s results are all "pure functions of the input content", so they are cached by the **input-face content fingerprint** (two layers, in-process + on disk; the key also includes the code face and the runtime). Two disciplines determine the shape:

- **Narrow faces are cached in any process** (the two asset-density functions, the ledger projection) — a witness costs only tens of milliseconds, so it is worth it.
- **Wide faces are cached only when the resident layer is in place** (`schema_lint` / ladder / purity: their declared faces cover the whole corpus) — in a cold process, a wide-face fingerprint would have to re-read the corpus (measured ~1.0 s), costing more than computing directly, so it is **better not to compute it** (`require_resident`).

And the **witness** itself has been driven to nearly zero: **per-file digests live in the resident layer alongside the text**, invalidated **per file** by watcher changes. Measured across 8 input faces (including a wide face with 3439 files), the witness cost went **228 → ~30 ms**, with the **fingerprint values bit-for-bit unchanged** (same file, same payload ⇒ same digest). End to end (this machine, median of 3 independent rounds, a fresh daemon each round):

| The first `nf score` right after an edit | Before | After |
|---|---|---|
| Unrelated change (editing a file not on any input face) | 1591 ms | **545 ms** |
| Related change (editing a file on an input face, **a genuinely new content state**, end to end) | 1625 ms (4.6–6.3 s before Aho) | **≈1.25 s** (a repeat of the same state ~52 ms) |
| Tree unchanged (whole-response reuse) | — | **51 ms** |

**The phrase "new content state" matters a great deal**: running the same content state a second time hits the on-disk entry (~50 ms), whereas **every real edit is a new state**. Only by measuring this distinction clearly does the real culprit emerge — the reference census used per-key `str.count` to count 1499 keys × 3.5 MB of corpus = **5.2 GB of character scanning = 3.11 s**, repaid for every new state. It is now **Aho–Corasick** (one pass over the corpus + non-overlapping greedy counting per key set, **semantically byte-for-byte identical** to `str.count`): on the real corpus, **2895 → 323 ms** (total references 31323, per-key identical), `usage_scan` overall ~3.1 s → **296 ms**, with equivalence guarded by three criteria: 400 random strings + overlapping/nested/empty-key boundaries + a real-corpus subset.

One step further (2026-09-29): the census was changed to **count per file and then sum**, caching per-file results by **file content** — equivalence is provable (an asset id contains no newline ⇒ no cross-file match exists), so **one real edit only recomputes the one file that changed**: with the per-file cache hot, `usage_scan` went **296 → 28 ms**, and end to end "the first heavy command after a real edit" went **1.95 s → 0.35 s** (a repeat of the same state is still ~50 ms; a cold process is ~1.87 s, unchanged).

**Convention discipline (trodden on three times, pinned down here)**: whenever something is called a "new content state", the probe must write a **one-off, unique body** (timestamp + counter); otherwise from the second run onward it hits the derived result of the **same content state** on disk, and what is measured is "replaying the same content" rather than a new state. Re-measured under this discipline: **unique new state · first one in the daemon ≈ 1.25 s**, same state again ~52 ms, tree unchanged ~50 ms, cold process ~1.9 s.

**Shared reads are now "one physical read serving two conventions"**: the lower layer reads only the **raw bytes** and puts them in the resident layer, and text is decoded by `TextIOWrapper(BytesIO(raw), encoding="utf-8", newline=None)` (**byte-for-byte identical** to `Path.read_text`’s universal-newline semantics; the criterion `ResidentRawEquivalenceTest` compares file by file against the real corpus). So "the same file read both as text and as bytes" (`ET.parse`, the byte comparison in `_recompute_entry`, etc.) no longer reads it a second time — the actual disk reads for one "new content state" recompute fell from **1047 to 38** (distinct files 1039 → 33).

The depth roll-up (`quality_depth_scan`, the check32 gate face) **runs a dozen-plus sub-scanners one by one** itself, so it too was given content-keyed caching (input face = the union of the sub-scanners’ faces) — it was the biggest remaining item on the bill, and after hooking it up, in-process `evaluate` went **476 → 43 ms**. At the same time, "table lookup" itself was made cheaper: the path key (`normcase(abspath())`) was memoized (measured: within one `evaluate` it is called 17628 times and alone consumes 71 ms).

**The code face (whose code really depends on whose) is also part of the content key**, and a monolithic code face (119 files) means "editing any one core file ⇒ every derived result changes key". It is now refined by **import closure**: each derived result keys only on "the `core.*` modules it statically imports" (the transitive closure). Three fail-closed rules: unparseable / a dynamic import construct (`__import__` / `importlib`) appears in the closure / the closure is empty ⇒ always **fall back to the monolithic code face**; there is also a **runtime integrity criterion** — really run that derived result in a fresh interpreter, and every `core.*` imported during the run must be inside the closure (a static-analysis miss turns red on the spot). Deterministic evidence: after editing `desktop/src/core/terminal.py`, the number of sites changing key fell from **9/9** to **0/9**.

One more self-defeating behavior on the daemon side was fixed: when judging "the code changed version", it would detach and reload the whole `core.*` block (to guarantee no stale code runs), which left the new module’s resident corpus layer empty — now the layer is taken out before the version change and put back after (what it holds is repository fact, independent of the code). End to end: **the first heavy command after a one-line code edit went 2609 → 870 ms** (another edit, 440 ms).

**Two boundaries to remember**: ① a cold process (no daemon) does **not** use the wide-face cache — `nf score` ~1.9 s, `nf conformance` ~2.3 s, the same as before it was hooked up (speed is not traded for readings); ② those derived results that audit code as **data** (purity / ladder / depth roll-up) **must** recompute after a code change — that is a real dependency, not waste.

**Boundary (must know)**: editing any file under `desktop/src`/`scripts` ⇒ the code face enters the key ⇒ all on-disk derived entries change key at once, and **the next heavy command pays one full recompute** (measured ~4.9 s). This is the price of the existing discipline "the code face enters the key": better to recompute than to treat a bill computed by the old algorithm as the new one. The criterion is `test_conformance_scan.DerivedResultCacheTest` (8 sites, table-driven; the rule "every file read must fall inside a declared input face" turns red first when a new read is added to a scanner — this round it caught two missing declarations on the spot).

```sh
nf daemon start                      # start the daemon (background; binds 127.0.0.1 only + a one-time token)
nf daemon start --watch              # separately: directory watching + read-only response cache (reuse the whole response when the tree is unchanged)
eval "$(nf daemon shell-init bash)"  # install into the current shell: zero-subprocess client (true millisecond scale)
nf daemon bench                      # re-run the table above (--json for machines)
nf daemon stop                       # stop it: immediately back to a direct python run, changing no availability
```

Disciplines (consistent with the whole repository, all with criteria):

- **Only faster, never different**: the daemon’s `(exit, stdout, stderr)` are **byte-for-byte identical** to a real subprocess direct run (`test_daemon` compares command by command).
- **A hot process must not go stale**: before every request, caches keyed **by path** are cleared (`pack_combo` profiles / the `registry_loader` registry), while **content-keyed** caches are kept (fenced YAML, the reference census — the key is the content, so it is naturally never stale); separately, a **source fingerprint** of `core/scripts` decides whether to reload the whole block, never answering with old code.
- **Security boundary**: binds `127.0.0.1` only (**no** switch opens it to the internet) + a one-time token (loopback is not a trust boundary) + a 1 MiB request cap; long-running/self-referential commands (`serve` / `shell` / `terminal` / `lsp` / `daemon`) are **refused** inside the daemon, and the daemon stays alive after the refusal. **Aliases get the same treatment as resident faces** (fixed 2026-10-01): `terminal` is an alias of `shell`, and `lsp` is a resident stdio service; they were previously not in the refusal table ⇒ through the daemon fast path they would **silently exit 0 with no output**, while a direct run really starts the service.
- **Always fall back**: if any step fails (no state file / no bash / cannot connect / wrong protocol header), the launcher **silently falls back** to a direct python run.

```sh
python scripts/nf.py shell --exec "nf doctor" --no-banner
python scripts/nf.py shell --exec "/zone 5" --json --no-banner
python scripts/nf.py shell --file tour.nf                    # script file (# comments / blank lines skipped / in-line ; re-separates)
python scripts/nf.py shell --file tour.nf --json             # the machine face of the same execution chain
```

- `--exec` separates with `;` (a newline counts as a separator too), and `--file` executes line by line; the two **share the same execution chain** (the same Session / index / write gate), so "what you can type in the terminal" and "what you can run in a script" always have the same semantics.
- It executes entry by entry and gives `kind/exit` for each; the exit code = the maximum of them.
- With `--json` it outputs `{"kind": "nf-shell", …}`, a machine face recording each entry (with argv / exit / out / err).
- `--no-banner` removes the opening banner (for logging scenarios).

## Boundaries

- **Not a full-screen TUI**: NF’s interactive face deliberately stays "line-by-line read/write" — redirectable, diffable, CI-friendly; a full-screen TUI would introduce terminal-capability coupling and third-party dependencies, conflicting with core’s "zero third-party dependencies" red line.
- **Not a second command surface**: the terminal does not duplicate business logic; the command source of truth is always `scripts/nf.py`’s argparse surface.
- **A new GUI / new shell**: out of scope for this file; per §4 of `STRATEGY.md` and the decision record, a new ruling from the author is required before it is chartered separately.