#!/usr/bin/env python3
"""深化面门禁（check35）双跑对账探针。

check35 是 **verify.sh 内嵌 Python**（无 nf 子命令面），故按本工程既有做法把该段**原文抽出**执行，
与引擎侧 `DeepeningGate.Check35` 同树双跑、比同式摘要。

三用例：
  1. real        —— 真仓快照（八条子项全绿）；
  2. synthetic_empty —— 空树（逐条报缺）；
  3. synthetic_stale —— 真仓副本 + **篡改在盘一致性报告的 verdict**（验「报告过期/被改」这条腿）。

摘要口径：**stdout 全文**（check35 的 stdout 只有 FAIL 行与最后那行统计，没有进度噪声）。

用法：
    python probes/deepening_gate_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                          [--expect-embedded <SelfTest.cs>]
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
import _paths  # 默认路径唯一出处（探针可移植）

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_deepening_gate_golden.json")
def extract_body(verify_sh: Path) -> str:
    text = verify_sh.read_text(encoding="utf-8")
    start = text.index("check35(){")
    m = re.search(r"<<'PYEOF'[^\n]*\n(.*?)\nPYEOF\n", text[start:], re.S)
    if not m:
        raise SystemExit("找不到 check35 的 PYEOF 片段")
    return m.group(1)


def digest32(text: str) -> str:
    return hashlib.sha256("\n".join(text.splitlines()).encode("utf-8")).hexdigest()[:32]


def run_body(body: str, tree: Path) -> tuple[int, str, str]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([sys.executable, "-c", body], cwd=str(tree), env=env,
                          capture_output=True, text=True, encoding="utf-8", timeout=900)
    return proc.returncode, proc.stdout, proc.stderr


def summarize(exit_code: int, stdout: str) -> dict:
    lines = stdout.splitlines()
    return {"python_exit": exit_code, "digest32": digest32(stdout),
            "fails": sum(1 for l in lines if l.startswith("[FAIL]")),
            "last": lines[-1] if lines else "", "log": lines}


def prepare_tree(tree: Path, snap: Path, extra: tuple = ()) -> None:
    """真源要 `from core import …`，故合成树必须带 `desktop/src`；再按需拷入在盘工件。"""
    shutil.copytree(snap / "desktop" / "src", tree / "desktop" / "src",
                    ignore=shutil.ignore_patterns("__pycache__"))
    for rel in extra:
        src = snap / rel
        if not src.is_file():
            continue
        dst = tree / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)


def decode(raw: bytes) -> str:
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
    body = extract_body(snap / "verify.sh")
    print(f"check35 源码片段：{len(body.splitlines())} 行")
    results = {}

    code, out, err = run_body(body, snap)
    results["real"] = summarize(code, out)
    print(f"  真材：exit={code} · FAIL {results['real']['fails']} · {results['real']['last'][:70]} "
          f"· 摘要 {results['real']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-deep-empty-") as tmp:
        tree = Path(tmp)
        prepare_tree(tree, snap)
        code, out, err = run_body(body, tree)
    results["synthetic_empty"] = summarize(code, out)
    print(f"  合成（空树）：exit={code} · FAIL {results['synthetic_empty']['fails']} "
          f"· 摘要 {results['synthetic_empty']['digest32']}")

    # 篡改在盘一致性报告的 verdict：真源 verify_committed 应当报「verdict 不一致」
    with tempfile.TemporaryDirectory(prefix="nf-deep-stale-") as tmp:
        tree = Path(tmp)
        prepare_tree(tree, snap, extra=("protocol/conformance_report.json", "protocol/RECEIPTS.json",
                                        "library/RECEIPTS.json", "protocol/pipeline_advisory.json",
                                        "desktop/tests/fixtures/fixes/fix_cases.json",
                                        "desktop/tests/test_invalid_corpus.py"))
        report = tree / "protocol" / "conformance_report.json"
        doc = json.loads(report.read_text(encoding="utf-8"))
        doc["verdict"] = "partial"
        report.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8", newline="")
        code, out, err = run_body(body, tree)
    results["synthetic_stale"] = summarize(code, out)
    # 边界：真源的统计行用 **live verdict**（要跑未移植的 purity-clean 才算得出），引擎按声明边界
    # **读在盘 verdict** → 该用例**不比摘要**，只作「引擎侧能不能抓出被改的 verdict」的旁证。
    results["synthetic_stale"]["boundary"] = True
    print(f"  合成（篡改报告 verdict）：exit={code} · FAIL {results['synthetic_stale']['fails']} "
          f"· 摘要 {results['synthetic_stale']['digest32']}")
    for line in results["synthetic_stale"]["log"][:3]:
        print("     ", line[:110])

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-deepening-gate-golden/1",
            "generated": "2026-09-27",
            "source": "verify.sh check35 内联 Python 原文（机械抽取后执行）",
            "snapshot": str(snap),
            "digest_rule": 'sha256("\\n".join(stdout.splitlines()))[:32]  ← 与引擎 Result.LogDigest 同式',
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
        for key in ("real", "synthetic_empty"):
            want, got = fixture["cases"][key]["digest32"], results[key]["digest32"]
            print(f"  [{'OK ' if want == got else '漂移'}] {key}: 金标 {want} / 本轮 {got}")
            if want != got:
                drift.append(key)
        stale = fixture["cases"]["synthetic_stale"]
        print(f"  [--] synthetic_stale：**声明边界**（真源统计行用 live verdict；引擎读在盘 verdict）"
              f"——不比摘要，真源仍报 {results['synthetic_stale']['fails']} 条 FAIL")
        if results["synthetic_stale"]["fails"] == 0:
            drift.append("synthetic_stale(真源未报错)")
        if drift:
            print(f"FAIL: 真源输出已漂移 {drift}")
            return 1
        print("OK: 金标向量与真源本轮输出一致（三条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = [key for key in ("real", "synthetic_empty") if results[key]["digest32"] not in cs]
        if "声明边界" not in cs:
            missing.append("<边界说明>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 两条摘要与边界说明均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=900)
        rows = json.loads(decode(proc.stdout))["rows"]
        bad = []
        for prefix, case in (("深化面·真仓", "real"), ("深化面·空树", "synthetic_empty")):
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
        stalePin = [r for r in rows if r["name"].startswith("深化面·篡改报告")]
        if len(stalePin) != 1:
            print(f"FAIL: 找不到唯一引擎钉「深化面·篡改报告」（实得 {len(stalePin)}）")
            return 1
        staleOk = "verdict 非 conformant" in stalePin[0]["detail"] and "声明边界" in stalePin[0]["detail"]
        print(f"  [{'OK ' if staleOk else '不一致'}] 引擎 synthetic_stale：抓出被改的 verdict 且标了声明边界")
        if not staleOk:
            bad.append("synthetic_stale")
        if bad:
            print(f"FAIL: 引擎侧与真源输出不一致：{bad}")
            return 1
        print("OK: 引擎侧深化面输出与真源逐字节同摘要（真材 + 空树），篡改用例按声明边界单独断言")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
