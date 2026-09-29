#!/usr/bin/env python3
"""回归面（check33 第 3 条 + check29 + check32 聚合 + doc_hygiene 信号）双跑对账探针。

两侧都以**真源代码**为 oracle：本探针 import 真源模块（regression_score / conformance_scan /
quality_depth_scan / doc_hygiene）拿输出，按**与引擎同式的取行口径**渲染成行并摘要；
引擎侧自检钉用同一份语料 + 同一份取行口径复算，摘要必须逐字节相同。

用例：
  conformance_real / conformance_negative（合成虚标语料）
  depth_real（14 件子扫描器聚合）
  markers_real / markers_negative（合成缺标识语料）
  score_real（五信号 + 可复算子集分 + 边界）
  compare_cases（compare() 纯函数六例）

用法：
    python probes/regression_score_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                            [--expect-embedded <SelfTest.cs>]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_regression_score_golden.json")
#: 真源 quality_depth_scan.scan 的子扫描器名（同序）
DEPTH_NAMES = ("payload_registry", "asset_ledger", "instruction_audit", "concept_graph", "output_forms",
               "domain_packs", "combos", "asset_density", "asset_thickness", "asset_usage_strict",
               "tool_face", "world_model", "world_slots", "payload_consumer")

BOUNDARY = ("purity_clean",)


def digest32(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


def load_real(snap: Path):
    src = str(snap / "desktop" / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from core import (conformance_scan as csc, doc_hygiene as dh,
                      quality_depth_scan as qd, regression_score as rs)
    return csc, dh, qd, rs


def conformance_log(issues, stats) -> list:
    lines = ["[FAIL] %s" % i for i in issues]
    lines.append("Conformance 统计：机读块 %d / 协议包 %d / 导出面 %d"
                 % (stats["modules_mc"], stats["packages"], stats["export_items"]))
    return lines


def depth_log(issues) -> list:
    ok = sum(1 for name in DEPTH_NAMES
             if not any(i.startswith(name + ": ") for i in issues))
    lines = ["[FAIL] %s" % i for i in issues]
    lines.append("质量纵深 子扫描：%d/%d 零缺口" % (ok, len(DEPTH_NAMES)))
    return lines


def markers_log(issues) -> list:
    lines = ["[FAIL] %s" % i for i in issues]
    lines.append("文档卫生：%s" % ("零缺口" if not issues else "FAIL %d" % len(issues)))
    return lines


def score_log(ev, boundary=BOUNDARY) -> list:
    """可复算子集口径（与引擎同式）：剔除边界信号 + 在剩余权重上归一。"""
    kept = [s for s in ev["signals"] if s["name"] not in boundary]
    weight = sum(s["weight"] for s in kept)
    score = round(sum(s["weight"] * s["value"] for s in kept) / weight * 100.0, 2) if weight else 0.0
    lines = ["%s=%r" % (s["name"], s["value"]) for s in kept]
    lines.append("score=%r" % score)
    lines.append("boundary=%s" % ",".join(boundary))
    issues = ev["issues"]
    lines.append("issues=%s" % ("零缺口" if not issues else "FAIL %d" % len(issues)))
    return lines


def compare_log(rs, pairs) -> list:
    lines = []
    for pair in pairs:
        out = rs.compare(pair["current"], pair["baseline"],
                         pair.get("tolerance", 0.0), pair.get("exceptions"))
        lines.append("%s: ok=%r delta=%r verdict=%s"
                     % (pair["case"], out["ok"], out["delta"], out["verdict"]))
    return lines


def synthetic_conformance() -> dict:
    reg = {"modules": [{"id": "M01"}], "protocols": [{"id": "P01", "module_ids": ["M02"]}]}
    fence = "```yaml\nmachine_contract:\n  id: %s\n  conformance: %s\n```\n"
    return {
        "desktop/src/core/registry.json": json.dumps(reg, ensure_ascii=False, indent=1),
        "verify.sh": "# 版本 : v1.0\ncheck18\ncheck22\n",
        "a.txt": "x\n",
        "protocol/export_conformance.json": json.dumps({
            "conformance_version": "1",
            "items": [
                {"id": "x", "conformance": "L3",
                 "evidence": ["a.txt", "missing.txt"], "gates": ["check18", "check99"]},
                {"id": "y", "conformance": "L2", "evidence": [], "gates": []},
            ],
        }, ensure_ascii=False, indent=1),
        "04_模块库/通用类/T01.md": "# T01\n" + fence % ("M01", "L2"),
        "04_模块库/通用类/T02.md": "# T02\n" + fence % ("M99", "L3"),
        "04_模块库/通用类/T03.md": "# T03\n" + fence % ("M01", "L0"),
        "community/入库包/protocol.yaml": 'package:\n  conformance: "L1"\n  id: P01\n',
        "community/测试包/protocol.yaml": 'package:\n  conformance: "L2"\n  id: 测试包\n',
    }


def synthetic_markers() -> dict:
    return {
        "01_核心协议.md": "# 核心协议\n正文\n",
        "docs/ai-menu.md": "> 最后更新：2026-01-01\n正文\n",
    }


def write_tree(files: dict, root: Path) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")


def compare_pairs() -> list:
    def side(score, values, weak=False):
        return {"score": score,
                "signals": [{"name": n, "weight": w, "value": (0.8 if weak and n == "schema_clean" else v)}
                            for n, w, v in values]}

    spec = [("schema_clean", 0.2, 1.0), ("conformance_clean", 0.2, 1.0),
            ("doc_hygiene", 0.15, 1.0), ("depth_clean", 0.15, 1.0),
            ("asset_density", 0.15, 1.0)]
    base = side(100.0, spec)
    return [
        {"case": "no_regression", "current": side(100.0, spec), "baseline": base},
        {"case": "signal_drop", "current": side(96.0, spec, weak=True), "baseline": base},
        {"case": "overall_drop_only", "current": side(90.0, spec), "baseline": base},
        {"case": "within_tolerance", "current": side(95.0, spec), "baseline": base, "tolerance": 5.0},
        {"case": "exempted", "current": side(98.0, spec, weak=True), "baseline": base,
         "exceptions": [{"signal": "schema_clean", "reason": "已批准的单信号回归（合成例）"}]},
        {"case": "no_baseline", "current": side(80.0, spec), "baseline": {"score": 0.0, "signals": []}},
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    csc, dh, qd, rs = load_real(snap)
    results: dict = {}

    def record(name, lines, extra=None):
        results[name] = {"log": lines, "digest32": digest32(lines),
                         "fails": sum(1 for l in lines if l.startswith("[FAIL] "))}
        if extra:
            results[name].update(extra)
        print(f"  {name}: FAIL {results[name]['fails']} · 摘要 {results[name]['digest32']}")
        for line in lines[:2]:
            print("     ", line[:110])

    cwd = os.getcwd()
    os.chdir(snap)
    try:
        record("conformance_real", conformance_log(*csc.scan(".")))
        record("depth_real", depth_log(qd.scan(".")[0]))
        record("markers_real", markers_log(dh.check_markers(".")))
        record("score_real", score_log(rs.evaluate(".")))
        record("compare_cases", compare_log(rs, compare_pairs()))
    finally:
        os.chdir(cwd)

    import tempfile
    with tempfile.TemporaryDirectory(prefix="nf-reg-csc-") as tmp:
        tree = Path(tmp)
        files = synthetic_conformance()
        write_tree(files, tree)
        os.chdir(tree)
        try:
            record("conformance_negative", conformance_log(*csc.scan(".")),
                   {"files_b64": {rel: base64.b64encode(text.encode("utf-8")).decode("ascii")
                                  for rel, text in files.items()}})
        finally:
            os.chdir(cwd)

    with tempfile.TemporaryDirectory(prefix="nf-reg-mark-") as tmp:
        tree = Path(tmp)
        files = synthetic_markers()
        write_tree(files, tree)
        os.chdir(tree)
        try:
            record("markers_negative", markers_log(dh.check_markers(".")),
                   {"files_b64": {rel: base64.b64encode(text.encode("utf-8")).decode("ascii")
                                  for rel, text in files.items()}})
        finally:
            os.chdir(cwd)

    pairs = compare_pairs()
    pairs_b64 = base64.b64encode(
        json.dumps(pairs, ensure_ascii=False, indent=1).encode("utf-8")).decode("ascii")
    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-regression-score-golden/1",
            "generated": "2026-09-27",
            "source": ("真源模块原文：regression_score.evaluate/compare · conformance_scan.scan · "
                       "quality_depth_scan.scan · doc_hygiene.check_markers"),
            "snapshot": str(snap),
            "digest_rule": 'sha256("\\n".join(渲染行))[:32]  ← 与引擎侧同式',
            "boundary": list(BOUNDARY),
            "compare_pairs": pairs,
            "compare_pairs_b64": pairs_b64,
            "cases": results,
        }
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n"：与同文件第 141 行（已带 newline=""）同一条纪律——夹具必须是 LF。
        fixture_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                                encoding="utf-8", newline="\n")
        print(f"已写金标向量：{fixture_path}")
    else:
        if not fixture_path.exists():
            print(f"FAIL: 缺金标向量 {fixture_path}（用 --write-fixture 生成）")
            return 1
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        drift = []
        for key in ("conformance_real", "conformance_negative", "depth_real", "markers_real",
                    "markers_negative", "score_real", "compare_cases"):
            want, got = fixture["cases"][key]["digest32"], results[key]["digest32"]
            print(f"  [{'OK ' if want == got else '漂移'}] {key}: 金标 {want} / 本轮 {got}")
            if want != got:
                drift.append(key)
        if drift:
            print(f"FAIL: 真源输出已漂移 {drift}")
            return 1
        print("OK: 金标向量与真源本轮输出一致（七条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = []
        for key in ("conformance_real", "conformance_negative", "depth_real", "markers_real",
                    "markers_negative", "score_real", "compare_cases"):
            if results[key]["digest32"] not in cs:
                missing.append(f"<{key} 摘要>")
        for key in ("conformance_negative", "markers_negative"):
            for rel, b64 in results[key]["files_b64"].items():
                if b64 not in cs:
                    missing.append(f"<{key}:{rel} base64>")
        if pairs_b64 not in cs:
            missing.append("<compare_pairs 语料 base64>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 七条摘要 + 两份合成语料 + compare 语料均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=1800)
        rows = json.loads(proc.stdout.decode("utf-8", errors="replace"))["rows"]
        mapping = (("回归面·conformance·真仓", "conformance_real"),
                   ("回归面·conformance·合成虚标", "conformance_negative"),
                   ("回归面·纵深聚合·真仓", "depth_real"),
                   ("回归面·文档卫生·真仓", "markers_real"),
                   ("回归面·文档卫生·合成缺标识", "markers_negative"),
                   ("回归面·分值·真仓", "score_real"),
                   ("回归面·比对口径", "compare_cases"))
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
        print("OK: 引擎侧回归面七条与真源逐字节同摘要")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
