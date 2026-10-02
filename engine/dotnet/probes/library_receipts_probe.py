"""馆藏回执（`core/receipts.py` 馆藏作用域 · check35 第二条腿）双跑对账探针。

真源侧 import `core.receipts`，用真源 `build()` 造出**盘上原件**，再按六种破坏方式改语料，逐例跑
`verify(doc, root)`；引擎侧自检钉用同一份语料复算。取行口径（与 check35 第二条腿同框）：
每条 issue 一行 `[FAIL] 馆藏回执：…`，末行 `馆藏回执 子扫描：<零缺口|FAIL N>`。

用例：
  lib_real            真仓（3 条 · 根 be9562d619c4… 零缺口）
  lib_entry_tampered  条目正文被改（→ 根不一致 + 条目内容已变）
  lib_entry_removed   回执少一条（→ 回执条数 N-1 ≠ 馆藏条数 N）
  lib_ghost_entry     回执指向不存在的条目
  lib_schema          回执 schema 不匹配（真源立刻返回，不做折叠判定）
  lib_proof_tampered  条目 leaf 被改（→ 包含证明不折叠到根）
  lib_new_entry       盘上多一条馆藏而回执未更新（→ 根不一致 + 条数不等）

用法：
    python probes/library_receipts_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                            [--expect-embedded <SelfTest.cs>]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
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
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_library_receipts_golden.json")
ENTRY_TMPL = """---
id: NF-{n}
type: guide
title: 合成条目{n}
description: 合成馆藏条目（探针语料）
license: MIT
status: active
---

# 合成条目 {n}

正文第 {n} 条（探针语料）。
"""


def digest32(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


def load_real(snap: Path):
    src = str(snap / "desktop" / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from core import receipts
    return receipts


def lib_log(receipts, root: str) -> list:
    doc = receipts.load(root)
    issues, _stats = receipts.verify(doc, root)
    lines = ["[FAIL] 馆藏回执：%s" % i for i in issues]
    lines.append("馆藏回执 子扫描：%s" % ("零缺口" if not issues else "FAIL %d" % len(issues)))
    return lines


def write_library(tree: Path, n_entries: int = 3) -> None:
    lib = tree / "library"
    lib.mkdir(parents=True, exist_ok=True)
    for n in range(1, n_entries + 1):
        (lib / ("NF-%d.md" % n)).write_text(ENTRY_TMPL.format(n=n), encoding="utf-8", newline="")


def write_receipts(receipts, tree: Path) -> None:
    doc = receipts.build(str(tree))
    (tree / "library" / "RECEIPTS.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="")


def read_receipts(tree: Path) -> dict:
    return json.loads((tree / "library" / "RECEIPTS.json").read_text(encoding="utf-8"))


def write_receipts_doc(tree: Path, doc: dict) -> None:
    (tree / "library" / "RECEIPTS.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="")


def snapshot_b64(root: Path) -> dict:
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[path.relative_to(root).as_posix()] = base64.b64encode(path.read_bytes()).decode("ascii")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    receipts = load_real(snap)
    results: dict = {}

    def record(name, lines, extra=None):
        results[name] = {"log": lines, "digest32": digest32(lines),
                         "fails": sum(1 for l in lines if l.startswith("[FAIL] "))}
        if extra:
            results[name].update(extra)
        print(f"  {name}: FAIL {results[name]['fails']} · 摘要 {results[name]['digest32']}")
        for line in lines[:2]:
            print("     ", line[:120])

    record("lib_real", lib_log(receipts, str(snap)))

    with tempfile.TemporaryDirectory(prefix="nf-lib-") as tmp:
        base = Path(tmp) / "base"
        write_library(base)
        write_receipts(receipts, base)

        def case(name, mutate):
            tree = Path(tmp) / name
            if tree.exists():
                import shutil
                shutil.rmtree(tree)
            import shutil as _sh
            _sh.copytree(base, tree)
            mutate(tree)
            record(name, lib_log(receipts, str(tree)), {"files_b64": snapshot_b64(tree)})

        def tamper_entry(tree):
            p = tree / "library" / "NF-1.md"
            p.write_text(p.read_text(encoding="utf-8") + "\n篡改一行。\n", encoding="utf-8", newline="")

        def drop_entry(tree):
            doc = read_receipts(tree)
            doc["entries"] = doc["entries"][:-1]
            write_receipts_doc(tree, doc)

        def ghost_entry(tree):
            doc = read_receipts(tree)
            doc["entries"][0]["id"] = "NF-999"
            write_receipts_doc(tree, doc)

        def bad_schema(tree):
            doc = read_receipts(tree)
            doc["schema"] = "nf-receipts/2"
            write_receipts_doc(tree, doc)

        def bad_proof(tree):
            doc = read_receipts(tree)
            doc["entries"][1]["leaf"] = "00" * 32
            write_receipts_doc(tree, doc)

        def new_entry(tree):
            (tree / "library" / "NF-4.md").write_text(ENTRY_TMPL.format(n=4), encoding="utf-8", newline="")

        case("lib_entry_tampered", tamper_entry)
        case("lib_entry_removed", drop_entry)
        case("lib_ghost_entry", ghost_entry)
        case("lib_schema", bad_schema)
        case("lib_proof_tampered", bad_proof)
        case("lib_new_entry", new_entry)

    fixture_path = Path(args.fixture)
    cases = ("lib_real", "lib_entry_tampered", "lib_entry_removed", "lib_ghost_entry",
             "lib_schema", "lib_proof_tampered", "lib_new_entry")
    if args.write_fixture:
        payload = {
            "schema": "nf-library-receipts-golden/1",
            "generated": "2026-09-27",
            "source": "真源 core/receipts.py::build + verify（馆藏作用域 · check35 第二条腿框法）",
            "snapshot": _paths.portable(snap),
            "digest_rule": 'sha256("\\n".join(渲染行))[:32]  ← 与引擎侧同式',
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
        drift = [k for k in cases if fixture["cases"][k]["digest32"] != results[k]["digest32"]]
        for k in cases:
            want, got = fixture["cases"][k]["digest32"], results[k]["digest32"]
            print(f"  [{'OK ' if want == got else '漂移'}] {k}: 金标 {want} / 本轮 {got}")
        if drift:
            print(f"FAIL: 真源输出已漂移 {drift}")
            return 1
        print("OK: 金标向量与真源本轮输出一致（七条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = [f"<{k} 摘要>" for k in cases if results[k]["digest32"] not in cs]
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 七条摘要均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=3600)
        rows = json.loads(proc.stdout.decode("utf-8", errors="replace"))["rows"]
        mapping = (("馆藏回执·真仓", "lib_real"),
                   ("馆藏回执·条目被改", "lib_entry_tampered"),
                   ("馆藏回执·回执少一条", "lib_entry_removed"),
                   ("馆藏回执·幽灵条目", "lib_ghost_entry"),
                   ("馆藏回执·schema 不匹配", "lib_schema"),
                   ("馆藏回执·leaf 被改", "lib_proof_tampered"),
                   ("馆藏回执·盘上多一条", "lib_new_entry"))
        bad = []
        for prefix, case in mapping:
            hit = [r for r in rows if r["name"].startswith(prefix)]
            if len(hit) != 1:
                print(f"FAIL: 找不到唯一引擎钉「{prefix}」（实得 {len(hit)}）")
                return 1
            match = re.search(r"摘要 (\w{32})", hit[0]["detail"])
            got, want = (match.group(1) if match else None), results[case]["digest32"]
            print(f"  [{'OK ' if got == want else '不一致'}] 引擎 {case}: {got} / 真源 {want}")
            if got != want:
                bad.append(case)
        if bad:
            print(f"FAIL: 引擎侧与真源输出不一致：{bad}")
            return 1
        print("OK: 引擎侧馆藏回执七条与真源逐字节同摘要")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
