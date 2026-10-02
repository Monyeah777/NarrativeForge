#!/usr/bin/env python3
"""正文 lint + 文档命令面（check33 第 5 / 12 面 · `core/prose_lint.py`）双跑对账探针。

与 `license_gate_probe.py` 同构：**真源模块原文**（从快照 `desktop/src/core/` 导入，不改一个字节）
在**真仓快照**与**合成树**上各跑一遍，按下面这套**统一渲染规则**落日志，再与引擎侧 `ProseLint` 同式摘要比对。

渲染规则（两侧同一套，本探针是规则的唯一出处）：
    command_face:
        [FAIL] <issue>                       ← 逐条
        [STAT] docs=N commands_checked=N cli_commands=N mcp_tools=N
    lint_text:
        [FIND] <rule> line=<n> <message> | <snippet>   ← 逐条
        [STAT] findings=N

用法：
    python probes/prose_lint_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                      [--expect-embedded <SelfTest.cs>]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

# 同 license_gate_probe：**导入**真源模块时别写 `.pyc`（测量快照要保持干净）。
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_prose_lint_golden.json")
_NF_PY = '''"""探针合成语料：只提供 add_parser 注册名，供 command_face 抽取。"""
import argparse

sub = argparse.ArgumentParser().add_subparsers()
p = sub.add_parser("assemble")
p = sub.add_parser("verify")
'''

_README = """# 合成语料 · 入口文档

用 `nf assemble` 装配一个组合包。

用 `nf nope` 是不存在的子命令（应判出）。

`registry_query（MCP 工具）` 在册；`not_a_tool（MCP 工具）` 不在册（应判出）。

```bash
nf verify --all
nf bogus-cmd
```
"""

_DOCS_X = """# 合成语料 · docs 面

散文里写 nf 不带反引号不算命令面（本行不该被判）。

`nf assemble` 在册（不该被判）。
"""

#: 正文 lint 语料：八条规则各至少命中一次（含段首连接词复用与模糊限定词过密两条「跨行/全文」规则）
_PROSE = """# 合成语料 · 正文 lint

在这个问题上，我们需要谨慎。

总而言之，我们应该继续。

这不是速度问题，而是方向问题。

统筹兼顾、稳中求进、进退有据地推进。

这是一句中文,带英文逗号。

然而情况先变了。

然而时间又不够。

也许大概或许似乎仿佛可能某种程度上，事情还有转机。
"""

SYNTH_FILES = {
    "scripts/nf.py": _NF_PY.encode("utf-8"),
    "README.md": _README.encode("utf-8"),
    "docs/x.md": _DOCS_X.encode("utf-8"),
    "prose_sample.md": _PROSE.encode("utf-8"),
}


def load_source(snap: Path, module_name: str = "prose_lint"):
    src = str(snap / "desktop" / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    return importlib.import_module(f"core.{module_name}")


def digest32(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


def render_command_face(issues, stats) -> list:
    lines = ["[FAIL] %s" % i for i in issues]
    lines.append("[STAT] docs=%s commands_checked=%s cli_commands=%s mcp_tools=%s"
                 % (stats["docs"], stats["commands_checked"], stats["cli_commands"], stats["mcp_tools"]))
    return lines


def render_lint_text(findings) -> list:
    lines = ["[FIND] %s line=%d %s | %s" % (f["rule"], f["line"], f["message"], f["snippet"])
             for f in findings]
    lines.append("[STAT] findings=%d" % len(findings))
    return lines


def write_tree(base: Path, files: dict) -> None:
    for rel, blob in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)


def decode_console(raw: bytes) -> str:
    for enc in ("utf-8", "gbk", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    pl = load_source(snap)
    results = {}

    iss, st = pl.command_face(str(snap))
    log = render_command_face(iss, st)
    results["real_command_face"] = {"log": log, "digest32": digest32(log), "fails": len(iss)}
    print(f"  真仓命令面：FAIL {len(iss)} · docs {st['docs']} · checked {st['commands_checked']} "
          f"· cli {st['cli_commands']} · mcp {st['mcp_tools']} · 摘要 {results['real_command_face']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-prose-") as tmp:
        tree = Path(tmp)
        write_tree(tree, SYNTH_FILES)
        iss2, st2 = pl.command_face(str(tree))
        findings = pl.lint_text((tree / "prose_sample.md").read_text(encoding="utf-8"))
    log_cmd = render_command_face(iss2, st2)
    log_lint = render_lint_text(findings)
    results["synthetic_command_face"] = {
        "log": log_cmd, "digest32": digest32(log_cmd), "fails": len(iss2),
        "files_b64": {rel: base64.b64encode(b).decode("ascii") for rel, b in SYNTH_FILES.items()},
    }
    results["synthetic_lint_text"] = {
        "log": log_lint, "digest32": digest32(log_lint), "findings": len(findings),
        "rules": sorted({f["rule"] for f in findings}),
    }
    print(f"  合成命令面：FAIL {len(iss2)} · docs {st2['docs']} · checked {st2['commands_checked']} "
          f"· 摘要 {results['synthetic_command_face']['digest32']}")
    print(f"  合成正文 lint：findings {len(findings)} · 规则 {results['synthetic_lint_text']['rules']} "
          f"· 摘要 {results['synthetic_lint_text']['digest32']}")

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-prose-lint-golden/1",
            "generated": "2026-09-27",
            "source": "desktop/src/core/prose_lint.py 原文导入执行（快照内那份），统一渲染规则见探针头",
            "snapshot": _paths.portable(snap),
            "digest_rule": 'sha256("\\n".join(渲染行))[:32]  ← 与引擎侧摘要同式',
            "cases": results,
        }
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n"：见 text_hygiene_probe 同处注释——否则复基线后的夹具是 CRLF，入包判红。
        fixture_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8", newline="\n")
        print(f"已写金标向量：{fixture_path}")
    else:
        if not fixture_path.exists():
            print(f"FAIL: 缺金标向量 {fixture_path}（用 --write-fixture 生成）")
            return 1
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        drift = []
        for key in ("real_command_face", "synthetic_command_face", "synthetic_lint_text"):
            want, got = fixture["cases"][key]["digest32"], results[key]["digest32"]
            print(f"  [{'OK ' if want == got else '漂移'}] {key}: 金标 {want} / 本轮 {got}")
            if want != got:
                drift.append(key)
        if drift:
            print(f"FAIL: 真源输出已漂移 {drift}（先看是否换了 HEAD，再决定是否重签金标）")
            return 1
        print("OK: 金标向量与真源本轮输出一致（三条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = [rel for rel, b64 in results["synthetic_command_face"]["files_b64"].items() if b64 not in cs]
        for key in ("real_command_face", "synthetic_command_face", "synthetic_lint_text"):
            if results[key]["digest32"] not in cs:
                missing.append(f"<{key} 摘要>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 合成树 base64 与三条摘要均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=900)
        rows = json.loads(decode_console(proc.stdout))["rows"]
        case_map = (("真仓命令面", "real_command_face"),
                    ("合成命令面", "synthetic_command_face"),
                    ("合成正文", "synthetic_lint_text"))
        bad = []
        for prefix, case in case_map:
            hit = [r for r in rows if r["name"].startswith(f"文档面·{prefix}")]
            if len(hit) != 1:
                print(f"FAIL: 找不到唯一引擎钉「文档面·{prefix}」（实得 {len(hit)}）")
                return 1
            m = re.search(r"摘要 (\w{32})", hit[0]["detail"])
            got = m.group(1) if m else None
            want = results[case]["digest32"]
            print(f"  [{'OK ' if got == want else '不一致'}] 引擎 {case}: {got} / 真源 {want}")
            if got != want:
                bad.append(case)
        if bad:
            print(f"FAIL: 引擎侧与真源输出不一致：{bad}")
            return 1
        print("OK: 引擎侧文档面输出与真源逐字节同摘要（真材料 + 合成树）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
