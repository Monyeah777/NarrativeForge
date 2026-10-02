#!/usr/bin/env python3
"""构建回路（check33 第 16 条 · `core/workloop.py`）双跑对账探针。

真源侧直接 import `core.workloop` 调 `scan('.')`，按 **check33 的框法**渲染：
每条 issue 一行 `[FAIL] 构建回路：…`，末行 `构建回路：<summary>`；引擎侧自检钉用同一份语料复算，
摘要必须逐字节相同。用例：
  workloop_real       真仓（待办 1229 项 · stub 工单确定）
  workloop_synthetic  合成语料（含 CLI ↔ 声明件漏同步 → deepen 候选；工单成形）
  workloop_empty      空树（待办真源为空 → 问题面为空 → 逐条判出）

用法：
    python probes/workloop_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                    [--expect-embedded <SelfTest.cs>]
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

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_workloop_golden.json")
def digest32(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


def load_real(snap: Path):
    src = str(snap / "desktop" / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from core import workloop as wl
    return wl


def workloop_log(wl) -> list:
    issues, stats = wl.scan(".")
    lines = ["[FAIL] 构建回路：%s" % i for i in issues]
    lines.append("构建回路：%s" % wl.summary(stats))
    return lines


DECISION_LAYER = {
    "schema": "nf-decision-layer/1",
    "primitives": {"choice": "在调用方给定选项上给概率分布 + argmax",
                   "noul": "对是非问题报概率 p",
                   "score": "对有序等级报概率分布 + 期望值"},
    "adapters": [
        {"id": "stub", "kind": "offline-deterministic", "in_gate_path": True, "calibrated": False,
         "note": "门禁用的离线确定性适配器（合成语料）"},
    ],
    "candidates": [
        {"id": "合成候选", "source": "hf:合成/候选", "license": "apache-2.0", "evidence": "合成语料",
         "pulled": True, "local": {"how": "h", "runtime": "r", "served_by": "s"}},
    ],
    "boundaries": ["不执行动作", "不生成正文", "不入门禁路径"],
}

NF_PY = (
    'import argparse\n'
    'def build(sub):\n'
    '    sub.add_parser("decisions")\n'
    '    sub.add_parser("score")\n'
    '    sub.add_parser("workloop")\n'
    '    sub.add_parser("receipts")\n'
    '    sub.add_parser("endpoint")\n'
    '    p = sub.add_parser("interop")\n'
    '    p.add_argument("--kind", default="openapi", choices=["openapi", "asyncapi"])\n'
)


def synthetic_tree() -> dict:
    return {
        "protocol/type_backlog.json": json.dumps(
            {"count": 2, "fields": [{"event": "ev.alpha", "field": "payload.x", "note": "待核"},
                                    {"event": "ev.beta", "field": "payload.y"}]},
            ensure_ascii=False, indent=1),
        "protocol/pipeline_advisory.json": json.dumps(
            {"count": 1, "counts": {"跨包/外部事件": 1},
             "items": [{"pipeline": "P09", "category": "跨包/外部事件", "detail": "合成样本"}]},
            ensure_ascii=False, indent=1),
        "protocol/decision_layer.json": json.dumps(DECISION_LAYER, ensure_ascii=False, indent=1),
        "scripts/nf.py": NF_PY,
    }


def write_tree(files: dict, root: Path) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    wl = load_real(snap)
    results: dict = {}
    cwd = os.getcwd()

    def record(name, lines, extra=None):
        results[name] = {"log": lines, "digest32": digest32(lines),
                         "fails": sum(1 for l in lines if l.startswith("[FAIL] "))}
        if extra:
            results[name].update(extra)
        print(f"  {name}: FAIL {results[name]['fails']} · 摘要 {results[name]['digest32']}")
        for line in lines[:2]:
            print("     ", line[:110])

    os.chdir(snap)
    try:
        record("workloop_real", workloop_log(wl))
    finally:
        os.chdir(cwd)

    with tempfile.TemporaryDirectory(prefix="nf-wl-syn-") as tmp:
        tree = Path(tmp)
        files = synthetic_tree()
        write_tree(files, tree)
        os.chdir(tree)
        try:
            record("workloop_synthetic", workloop_log(wl),
                   {"files_b64": {rel: base64.b64encode(text.encode("utf-8")).decode("ascii")
                                  for rel, text in files.items()}})
        finally:
            os.chdir(cwd)

    with tempfile.TemporaryDirectory(prefix="nf-wl-empty-") as tmp:
        tree = Path(tmp)
        os.chdir(tree)
        try:
            record("workloop_empty", workloop_log(wl))
        finally:
            os.chdir(cwd)

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-workloop-golden/1",
            "generated": "2026-09-27",
            "source": "真源 core/workloop.py::scan + summary（check33 第 16 条框法）",
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
        drift = []
        for key in ("workloop_real", "workloop_synthetic", "workloop_empty"):
            want, got = fixture["cases"][key]["digest32"], results[key]["digest32"]
            print(f"  [{'OK ' if want == got else '漂移'}] {key}: 金标 {want} / 本轮 {got}")
            if want != got:
                drift.append(key)
        if drift:
            print(f"FAIL: 真源输出已漂移 {drift}")
            return 1
        print("OK: 金标向量与真源本轮输出一致（三条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = [f"<{k} 摘要>" for k in ("workloop_real", "workloop_synthetic", "workloop_empty")
                   if results[k]["digest32"] not in cs]
        for rel, b64 in results["workloop_synthetic"].get("files_b64", {}).items():
            if b64 not in cs:
                missing.append(f"<workloop_synthetic:{rel} base64>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 三条摘要 + 合成语料均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=1800)
        rows = json.loads(proc.stdout.decode("utf-8", errors="replace"))["rows"]
        mapping = (("构建回路·真仓", "workloop_real"),
                   ("构建回路·合成语料", "workloop_synthetic"),
                   ("构建回路·空树", "workloop_empty"))
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
        print("OK: 引擎侧构建回路三条与真源逐字节同摘要")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
