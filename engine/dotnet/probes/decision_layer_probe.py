#!/usr/bin/env python3
"""决策层面（check33 第 15 条 · `core/decision_layer.py`）双跑对账探针。

做法同 license_gate_probe：**真源模块原文导入**（快照里的那份，不复制不改写），按 **check33 的框法**
落日志（issues → `[FAIL] 决策层：…`；再一行 `决策层面：<summary>`；声明缺失时 summary 抛 KeyError →
按 check33 的 except 打成 `决策层面：不可用`），与引擎侧 `DecisionLayer.Result.Log` 比同式摘要。

三用例：real（真仓）/ synthetic_tampered（篡改声明：适配器缺 note + 候选 pulled=true 缺 local）/
synthetic_absent（无声明件）。

用法：
    python probes/decision_layer_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
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
sys.dont_write_bytecode = True

import _paths  # 默认路径唯一出处（探针可移植）
DEFAULT_SNAP = _paths.SNAP
DEFAULT_CLI = _paths.engine("tools", "nf-dotnet", "bin", "Release", "net8.0", "nf-dotnet.exe")
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_decision_layer_golden.json")
def load_source(snap: Path):
    src = str(snap / "desktop" / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    return importlib.import_module("core.decision_layer")


def render(dl, issues, stats) -> list:
    """check33 第 15 条的框法（见模块头注释）。"""
    lines = ["[FAIL] 决策层：%s" % i for i in issues]
    try:
        lines.append("决策层面：%s" % dl.summary(stats))
    except Exception as exc:  # noqa: BLE001 —— 照抄 check33 的 except
        lines.append("决策层面：不可用")
        print(f"  （summary 抛 {type(exc).__name__}：{exc}）")
    return lines


def digest32(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


def decode(raw: bytes) -> str:
    for enc in ("utf-8", "gbk", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def tampered_decl(snap: Path) -> bytes:
    doc = json.loads((snap / "protocol" / "decision_layer.json").read_text(encoding="utf-8"))
    for adapter in doc.get("adapters", []):
        if adapter.get("id") == "stub":
            adapter.pop("note", None)                      # 适配器缺 note
    for candidate in doc.get("candidates", []):
        if candidate.get("id") == "laya-multilingual":
            candidate["pulled"] = True                     # 声明已拉取……
            candidate.pop("local", None)                   # ……却没有 local 证据
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    dl = load_source(snap)
    results = {}

    issues, stats = dl.scan(str(snap))
    log = render(dl, issues, stats)
    results["real"] = {"log": log, "digest32": digest32(log), "fails": len(issues)}
    print(f"  真仓：FAIL {len(issues)} · {log[-1][:70]} · 摘要 {results['real']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-dl-") as tmp:
        tree = Path(tmp)
        (tree / "protocol").mkdir(parents=True, exist_ok=True)
        (tree / "protocol" / "decision_layer.json").write_bytes(tampered_decl(snap))
        issues, stats = dl.scan(str(tree))
        log = render(dl, issues, stats)
    results["synthetic_tampered"] = {
        "log": log, "digest32": digest32(log), "fails": len(issues),
        "files_b64": {"protocol/decision_layer.json":
                      base64.b64encode(tampered_decl(snap)).decode("ascii")},
    }
    print(f"  合成（篡改声明）：FAIL {len(issues)} · 摘要 {results['synthetic_tampered']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-dl-absent-") as tmp:
        tree = Path(tmp)
        issues, stats = dl.scan(str(tree))
        log = render(dl, issues, stats)
    results["synthetic_absent"] = {"log": log, "digest32": digest32(log), "fails": len(issues)}
    print(f"  合成（无声明件）：FAIL {len(issues)} · {log[-1]} · 摘要 {results['synthetic_absent']['digest32']}")

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-decision-layer-golden/1",
            "generated": "2026-09-27",
            "source": "desktop/src/core/decision_layer.py 原文导入执行（快照内那份）+ check33 的框法",
            "snapshot": _paths.portable(snap),
            "digest_rule": 'sha256("\\n".join(渲染行))[:32]  ← 与引擎 Result.LogDigest 同式',
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
        for key in ("real", "synthetic_tampered", "synthetic_absent"):
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
        missing = [rel for rel, b64 in results["synthetic_tampered"]["files_b64"].items() if b64 not in cs]
        for key in ("real", "synthetic_tampered", "synthetic_absent"):
            if results[key]["digest32"] not in cs:
                missing.append(f"<{key} 摘要>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 篡改件 base64 与三条摘要均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=900)
        rows = json.loads(decode(proc.stdout))["rows"]
        bad = []
        for prefix, case in (("决策层·真仓", "real"), ("决策层·篡改声明", "synthetic_tampered"),
                             ("决策层·无声明件", "synthetic_absent")):
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
            print(f"FAIL: 引擎侧与真源输出不一致：{bad}")
            return 1
        print("OK: 引擎侧决策层输出与真源逐字节同摘要（真材 + 两棵合成树）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
