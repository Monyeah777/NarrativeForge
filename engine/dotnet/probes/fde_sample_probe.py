"""FDE 样例（check38 子扫描 4 · scripts/fde_sample_run.py）双跑对账探针。

真源侧按 check38 的框法渲染：`[FAIL] <issue>` 逐条 + 末行 `FDE 样例 子扫描：<零缺口|FAIL N>`；
引擎侧自检钉用**同一棵树**（快照整树拷贝，跳过 .git）复算，摘要必须逐字节相同。用例：
  fde_real               真仓（四件证据齐 · manifest 忽略 generated_at 后全同）
  fde_tampered_deliverable 证据被手改（交付物多一行）
  fde_gate_failure       删掉一个「已声明但不被交付物读取」的产出面 → G1 FAIL 传导到 gates/result/manifest
  fde_manifest_tampered  manifest 的 facts 被手改（验 generated_at 豁免不是「整件不比」）

用法：
    python probes/fde_sample_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                      [--expect-embedded <SelfTest.cs>]
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_fde_sample_golden.json")
EV = "docs/fde-sample/evidence"


def digest32(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


def load_real(snap: Path):
    spec = importlib.util.spec_from_file_location("fde", str(snap / "scripts" / "fde_sample_run.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fde_log(fde, root: str) -> list:
    issues, _stats = fde.check(root)
    lines = ["[FAIL] %s" % i for i in issues]
    lines.append("FDE 样例 子扫描：%s" % ("零缺口" if not issues else "FAIL %d" % len(issues)))
    return lines


def fresh_copy(snap: Path, work: Path) -> Path:
    tree = work / "tree"
    if tree.exists():
        shutil.rmtree(tree)
    shutil.copytree(snap, tree, ignore=shutil.ignore_patterns(".git"))
    return tree


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    fde = load_real(snap)
    results: dict = {}

    def record(name, lines, extra=None):
        results[name] = {"log": lines, "digest32": digest32(lines),
                         "fails": sum(1 for l in lines if l.startswith("[FAIL] "))}
        if extra:
            results[name].update(extra)
        print(f"  {name}: FAIL {results[name]['fails']} · 摘要 {results[name]['digest32']}")
        for line in lines[:2]:
            print("     ", line[:120])

    record("fde_real", fde_log(fde, str(snap)))

    with tempfile.TemporaryDirectory(prefix="nf-fde-") as tmp:
        work = Path(tmp)

        tree = fresh_copy(snap, work)
        target = tree / EV / "deliverable.md"
        target.write_text(target.read_text(encoding="utf-8") + "- 手改一行（合成篡改）\n",
                          encoding="utf-8", newline="")
        record("fde_tampered_deliverable", fde_log(fde, str(tree)))

        tree = fresh_copy(snap, work)
        (tree / "community/AI系统域包/outputs/charts/CONCEPT_DAG.mmd").unlink()
        record("fde_gate_failure", fde_log(fde, str(tree)))

        tree = fresh_copy(snap, work)
        mpath = tree / EV / "manifest.json"
        doc = json.loads(mpath.read_text(encoding="utf-8"))
        doc["facts"]["standards"] = 999
        mpath.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8", newline="")
        record("fde_manifest_tampered", fde_log(fde, str(tree)))

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-fde-sample-golden/1",
            "generated": "2026-09-27",
            "source": "真源 scripts/fde_sample_run.py::check（check38 子扫描 4 框法）",
            "snapshot": str(snap),
            "digest_rule": 'sha256("\\n".join(渲染行))[:32]  ← 与引擎侧同式',
            "tamper_recipe": {
                "fde_tampered_deliverable": "交付物末尾追加一行",
                "fde_gate_failure": "删 community/AI系统域包/outputs/charts/CONCEPT_DAG.mmd（已声明但交付物不读）",
                "fde_manifest_tampered": "manifest.facts.standards = 999",
            },
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
        for key in ("fde_real", "fde_tampered_deliverable", "fde_gate_failure", "fde_manifest_tampered"):
            want, got = fixture["cases"][key]["digest32"], results[key]["digest32"]
            print(f"  [{'OK ' if want == got else '漂移'}] {key}: 金标 {want} / 本轮 {got}")
            if want != got:
                drift.append(key)
        if drift:
            print(f"FAIL: 真源输出已漂移 {drift}")
            return 1
        print("OK: 金标向量与真源本轮输出一致（四条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = [f"<{k} 摘要>" for k in
                   ("fde_real", "fde_tampered_deliverable", "fde_gate_failure", "fde_manifest_tampered")
                   if results[k]["digest32"] not in cs]
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 四条摘要均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=3600)
        rows = json.loads(proc.stdout.decode("utf-8", errors="replace"))["rows"]
        mapping = (("FDE 样例·真仓", "fde_real"),
                   ("FDE 样例·交付物被手改", "fde_tampered_deliverable"),
                   ("FDE 样例·门失败传导", "fde_gate_failure"),
                   ("FDE 样例·manifest 被手改", "fde_manifest_tampered"))
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
        print("OK: 引擎侧 FDE 样例四条与真源逐字节同摘要")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
