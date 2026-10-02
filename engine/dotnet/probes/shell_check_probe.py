#!/usr/bin/env python3
"""**真源 shell 检查函数** oracle 探针（第八十八片起用）。

背景：`verify.sh` 里的 check 分两类——一部分内嵌 Python（可原文抽出执行），另一部分是**纯 bash**
（`check1` 目录结构、`check7` 社区两包结构…）。后者此前只能靠「我按我读到的 bash 语义复述」当证据，
那是**自证**。本探针换个做法：把 **bash 函数本体原文抽出来**，配上真源同款的 `ok/no/wn` 助手
（`  [PASS|FAIL|WARN] <文本>` + 计数器）后交给 `bash` 执行——**真源 shell 自己就是 oracle**。

为什么现在才做：本机 bash 在 `C:\\comfyui\\Git\\bin\\bash.exe`（Git for Windows 自带），此前一直按
「无 bash」处理（`run-gate.ps1` 的注释也是这么写的）。第八十八片把它找出来了。

用法：
    python probes/shell_check_probe.py --snap <snapshot> [--bash <path>] [--cli <nf-dotnet>]
                                       [--checks check1,check7] [--write-fixture]
                                       [--expect-embedded <SelfTest.cs>]

**摘要口径（重要）**：只取 `  [PASS]` / `  [FAIL]` / `  [WARN]` **裁决行**——
函数内的 `echo '== [N/6·A] … =='` 表头行、以及 check11 委派的 `reconcile_assets.sh` 的
汇总/结论行（子进程直接打 stdout）**都不进摘要**。理由：这些是**进度与说明**，判定面是裁决行与退出码；
把它们算进来只会让摘要随排版变化而漂。
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
import _paths  # 默认路径唯一出处（探针可移植）

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

DEFAULT_SNAP = _paths.SNAP
DEFAULT_BASH = _paths.BASH
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_shell_check_golden.json")
#: 真源助手（逐字对齐 verify.sh 第 61/67/68 行；_gha_note 在本地无 GITHUB_ACTIONS 时是空操作）
HELPERS = r"""set -u
PASS=0; FAIL=0; WARN=0
NFL_TMP="$(mktemp -d 2>/dev/null || echo /tmp/nf_probe_$$)"
_gha_note(){ [ "${GITHUB_ACTIONS:-}" = "true" ] || return 0; printf '::%s title=verify.sh::%s\n' "$1" "${2//$'\n'/%0A}"; }
ok(){ PASS=$((PASS+1)); printf '  [PASS] %s\n' "$1"; }
no(){ FAIL=$((FAIL+1)); printf '  [FAIL] %s\n' "$1"; _gha_note error "$1"; }
wn(){ WARN=$((WARN+1)); printf '  [WARN] %s\n' "$1"; _gha_note warning "$1"; }
PY3='python'
"""

#: 合成树②（缺件为主）：空树 → check1 全缺、check7 两个包都不在场
EMPTY_FILES: dict = {}

#: 合成树③（跨源不一致为主）：02 登记 2 / 3 件，实存 2 / 1 件；资产 1 / 0 件
_REG_TWO = """## 8. 社区领域包登记表

### 8.1 校园情感领域包（community/校园情感领域包/）
> 模块（2）：叙事 2 件。

### 8.2 西幻生存领域包（community/西幻生存领域包/）
> 模块（3）：生存 3 件。

### 8.3 第三方协议登记
"""

MISMATCH_FILES = {
    "02_联动注册表.md": _REG_TWO.encode("utf-8"),
    "community/校园情感领域包/modules/M01_甲.md": "# 模块 M01\n".encode("utf-8"),
    "community/校园情感领域包/modules/M02_乙.md": "# 模块 M02\n".encode("utf-8"),
    "community/校园情感领域包/assets/A1.md": "资产一\n".encode("utf-8"),
    "community/校园情感领域包/README.md": "# 校园情感领域包\n".encode("utf-8"),
    "community/校园情感领域包/pipelines/P02_校园情感流管线.md": "# P02\n".encode("utf-8"),
    "community/西幻生存领域包/modules/M01_丙.md": "# 模块 M01\n".encode("utf-8"),
}


def extract_function(text: str, name: str) -> str:
    """从 verify.sh 抽出 `name(){ … }` 原文（到首个独占一行的 `}` 为止）。"""
    start = text.index(name + "(){")
    end = text.index("\n}\n", start)
    return text[start:end + 2]


def build_harness(functions: list, names: list) -> str:
    body = "".join(extract_function(f, n) + "\n" for n, f in zip(names, functions))
    tail = "; ".join(names) + '; printf "COUNTS=%s/%s/%s\\n" "$PASS" "$FAIL" "$WARN"\n'
    return HELPERS + body + tail


def digest32(text: str) -> str:
    return hashlib.sha256("\n".join(text.splitlines()).encode("utf-8")).hexdigest()[:32]


def run_harness(bash: str, script_text: str, tree: Path) -> tuple[int, str, str]:
    path = Path(tempfile.mkdtemp(prefix="nf-shell-")) / "harness.sh"
    path.write_text(script_text, encoding="utf-8", newline="\n")
    proc = subprocess.run([bash, str(path)], cwd=str(tree), capture_output=True, timeout=300)
    out = decode(proc.stdout)
    err = decode(proc.stderr)
    return proc.returncode, out, err


def decode(raw: bytes) -> str:
    for enc in ("utf-8", "gbk", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def write_tree(base: Path, files: dict) -> None:
    for rel, blob in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)


def summarize(exit_code: int, stdout: str) -> dict:
    lines = [l for l in stdout.splitlines() if l.startswith("  [")]
    counts = [l for l in stdout.splitlines() if l.startswith("COUNTS=")]
    return {"bash_exit": exit_code, "digest32": digest32("\n".join(lines)),
            "pass": sum(1 for l in lines if l.startswith("  [PASS]")),
            "fail": sum(1 for l in lines if l.startswith("  [FAIL]")),
            "warn": sum(1 for l in lines if l.startswith("  [WARN]")),
            "counts_line": counts[0] if counts else "", "log": lines}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--bash", default=DEFAULT_BASH)
    ap.add_argument("--cli", default="")
    ap.add_argument("--checks", default="check1,check7")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    ap.add_argument("--pin-prefix", default="结构面",
                    help="引擎自检钉名的前缀（结构面 / 锚点面…）——不同 check 组对应不同钉")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    if not Path(args.bash).is_file():
        print(f"FAIL: 找不到 bash：{args.bash}")
        return 1
    names = [c.strip() for c in args.checks.split(",") if c.strip()]
    verify = (snap / "verify.sh").read_text(encoding="utf-8")
    script = build_harness([verify] * len(names), names)
    print(f"bash={args.bash} · 抽出函数 {names}（{len(script.splitlines())} 行 harness）")

    results = {}
    code, out, err = run_harness(args.bash, script, snap)
    results["real"] = summarize(code, out)
    print(f"  真材：PASS {results['real']['pass']} · FAIL {results['real']['fail']} "
          f"· WARN {results['real']['warn']} · 摘要 {results['real']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-shell-empty-") as tmp:
        tree = Path(tmp)
        write_tree(tree, EMPTY_FILES)
        code, out, err = run_harness(args.bash, script, tree)
    results["synthetic_empty"] = summarize(code, out)
    print(f"  合成（空树）：PASS {results['synthetic_empty']['pass']} · FAIL {results['synthetic_empty']['fail']} "
          f"· WARN {results['synthetic_empty']['warn']} · 摘要 {results['synthetic_empty']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-shell-mismatch-") as tmp:
        tree = Path(tmp)
        write_tree(tree, MISMATCH_FILES)
        code, out, err = run_harness(args.bash, script, tree)
    results["synthetic_mismatch"] = summarize(code, out)
    results["synthetic_mismatch"]["files_b64"] = {
        rel: base64.b64encode(b).decode("ascii") for rel, b in MISMATCH_FILES.items()
    }
    print(f"  合成（跨源不一致）：PASS {results['synthetic_mismatch']['pass']} "
          f"· FAIL {results['synthetic_mismatch']['fail']} · WARN {results['synthetic_mismatch']['warn']} "
          f"· 摘要 {results['synthetic_mismatch']['digest32']}")

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-shell-check-golden/1",
            "generated": "2026-09-27",
            "source": f"verify.sh 抽出 {'/'.join(names)} 函数本体 + 真源同款 ok/no/wn 助手，交 {Path(args.bash).name} 执行",
            "snapshot": _paths.portable(snap),
            "digest_rule": 'sha256("\\n".join(仅 [PASS]/[FAIL]/[WARN] 行))[:32]',
            "cases": results,
        }
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"已写金标向量：{fixture_path}")
    else:
        if not fixture_path.exists():
            print(f"FAIL: 缺金标向量 {fixture_path}（用 --write-fixture 生成）")
            return 1
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        drift = []
        for key in ("real", "synthetic_empty", "synthetic_mismatch"):
            want, got = fixture["cases"][key]["digest32"], results[key]["digest32"]
            print(f"  [{'OK ' if want == got else '漂移'}] {key}: 金标 {want} / 本轮 {got}")
            if want != got:
                drift.append(key)
        if drift:
            print(f"FAIL: 真源输出已漂移 {drift}")
            return 1
        print("OK: 金标向量与真源 shell 本轮输出一致（三条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = [rel for rel, b64 in results["synthetic_mismatch"]["files_b64"].items() if b64 not in cs]
        for key in ("real", "synthetic_empty", "synthetic_mismatch"):
            if results[key]["digest32"] not in cs:
                missing.append(f"<{key} 摘要>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 合成树 base64 与三条摘要均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=900)
        rows = json.loads(decode(proc.stdout))["rows"]
        bad = []
        pfx = args.pin_prefix
        for prefix, case in ((pfx + "·真仓", "real"), (pfx + "·空树", "synthetic_empty"),
                             (pfx + "·跨源不一致", "synthetic_mismatch")):
            hit = [r for r in rows if r["name"].startswith(prefix)]
            if len(hit) != 1:
                print(f"FAIL: 找不到唯一引擎钉「{prefix}」（实得 {len(hit)}）")
                return 1
            m = re.search(r"摘要 (\w{32})", hit[0]["detail"])
            got = m.group(1) if m else None
            want = results[case]["digest32"]
            print(f"  [{'OK ' if got == want else '不一致'}] 引擎 {case}: {got} / 真源 {want}")
            if got != want:
                bad.append(case)
        if bad:
            print(f"FAIL: 引擎侧与真源 shell 输出不一致：{bad}")
            return 1
        print(f"OK: 引擎侧{pfx}与真源 shell 逐字节同摘要（真材 + 两棵合成树）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
