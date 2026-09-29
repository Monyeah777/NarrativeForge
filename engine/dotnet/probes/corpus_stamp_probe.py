"""语料身份（操作性预检）双跑对账探针：让「摘要类钉的红」能被正确归因。

本探针不跑真源 Python——它验的是**量具自己的口径**，四件事：
  1. **基线诚实**：引擎里记的金标基线必须等于**钉死快照**的实测指纹（否则基线已腐烂）；
  2. **确定性**：同语料两遍同值；
  3. **一字节敏感**：改一个字节即变（同内容重写不变）；
  4. **归因可用**：拿**另一份快照**（若在场，如作者 7 提交后的 `nf-snap-h6`）跑门，指纹应不匹配，
     且引擎把归因写在钉 detail 里（「语料与金标基线不同 → 从『复基线』处置」）——这正是第一百零六片
     实测踩到的操作性陷阱：当时只有一条摘要钉红、看不出是语料前移还是引擎坏了。

用法：
    python probes/corpus_stamp_probe.py --snap <钉死快照> --cli <nf-dotnet> [--other <另一份快照>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
DEFAULT_SNAP = _paths.SNAP
DEFAULT_OTHER = _paths.SNAP_OTHER
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
def fingerprint(root: Path) -> str:
    """与引擎同式的独立实现（跳 `.git` **与 Python 字节码缓存**；逐件 相对路径\\0 字节数\\0 sha256 拼行 → 整体 sha256[:16]）。"""
    rows = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if ".git" in path.relative_to(root).parts or "__pycache__" in path.relative_to(root).parts:
            continue
        if rel.endswith((".pyc", ".pyo")):
            continue
        rows.append((rel, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()))
    rows.sort(key=lambda r: r[0])
    blob = "".join(f"{rel}\0{size}\0{digest}\n" for rel, size, digest in rows).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def run_cli(cli: str, root: str, *args: str) -> tuple[int, str, str]:
    proc = subprocess.run([cli, "--root", root, *args], capture_output=True, timeout=1800)
    return (proc.returncode,
            proc.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n"),
            proc.stderr.decode("utf-8", errors="replace").replace("\r\n", "\n"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--other", default=DEFAULT_OTHER)
    ap.add_argument("--cli", default=DEFAULT_CLI)
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    problems = []

    # 1) 基线诚实：引擎记的基线 == 钉死快照的实测指纹
    code, out, _ = run_cli(args.cli, str(snap), "corpus", "--json")
    doc = json.loads(out)
    measured = fingerprint(snap)
    engine_recorded = doc["fingerprint"]
    baseline = doc["baseline"]
    print(f"① 钉死快照指纹：独立实现 {measured} · 引擎实测 {engine_recorded} · 引擎金标基线 {baseline}")
    if not (measured == engine_recorded == baseline):
        problems.append(f"基线不诚实：独立 {measured} / 引擎 {engine_recorded} / 金标 {baseline}")
    if doc["matches_baseline"] is not True or doc["mode"] != "snapshot":
        problems.append(f"钉死快照应报匹配且为快照模式，实得 {doc}")

    # 2/3) 确定性 + 一字节敏感（临时小树）
    with tempfile.TemporaryDirectory(prefix="nf-corpus-") as tmp:
        tree = Path(tmp)
        (tree / "a.md").write_text("一\n", encoding="utf-8", newline="")
        (tree / "sub").mkdir()
        (tree / "sub" / "b.md").write_text("二\n", encoding="utf-8", newline="")
        f1, f2 = fingerprint(tree), fingerprint(tree)
        (tree / "a.md").write_text("一\n", encoding="utf-8", newline="")
        f3 = fingerprint(tree)
        (tree / "a.md").write_text("一!\n", encoding="utf-8", newline="")
        f4 = fingerprint(tree)
        print(f"② 确定性：{f1} == {f2} → {f1 == f2}"
              f" · 同内容重写不变 → {f1 == f3} · 改一字节变 → {f1 != f4}（{f4}）")
        if not (f1 == f2 and f1 == f3 and f1 != f4):
            problems.append("指纹的确定性/一字节敏感性不成立")

    # 4) 归因可用：另一份快照应不匹配，且引擎把归因写进钉 detail
    other = Path(args.other)
    if other.is_dir():
        other_fp = fingerprint(other)
        code2, out2, _ = run_cli(args.cli, str(other), "corpus", "--json")
        doc2 = json.loads(out2)
        print(f"④ 另一份快照 {other.name}：指纹 {other_fp} · 匹配={doc2['matches_baseline']}"
              f" · 模式={doc2['mode']}")
        if doc2["matches_baseline"] is not False:
            problems.append("另一份快照竟与金标基线匹配（基线口径可疑）")
        code3, out3, _ = run_cli(args.cli, str(other), "selftest", "--json")
        rows = json.loads(out3)["rows"]
        stamp_pin = [r for r in rows if r["name"].startswith("语料身份·真仓")]
        if len(stamp_pin) != 1:
            problems.append(f"找不到语料身份钉（实得 {len(stamp_pin)}）")
        else:
            detail = stamp_pin[0]["detail"]
            attributed = ("从「复基线」处置" in detail) and (other_fp in detail)
            print(f"   语料身份钉 passed={stamp_pin[0]['passed']} · 含归因={attributed}")
            if stamp_pin[0]["passed"] or not attributed:
                problems.append("另一份快照下，语料身份钉未给出可读归因")
            others = [r["name"] for r in rows if not r["passed"] and not r["name"].startswith("语料身份")]
            print(f"   同快照下其余红钉：{len(others)} 条 → {others[:3]}")
    else:
        print(f"④ 另一份快照不在场（{other}）——跳过归因用例")

    if problems:
        print("FAIL:")
        for p in problems:
            print("  -", p)
        return 1
    print("OK: 语料身份口径成立（基线诚实 · 确定 · 一字节敏感 · 归因可读）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
