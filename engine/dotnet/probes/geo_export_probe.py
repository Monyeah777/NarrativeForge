"""GEO 出口（check38 子扫描 3 · scripts/geo_export.py）双跑对账探针。

真源侧按 check38 的框法渲染：`[FAIL] <issue>` 逐条 + 末行 `GEO 出口 子扫描：<零缺口|FAIL N>`；
引擎侧自检钉用同一份语料复算，摘要必须逐字节相同。用例：
  geo_real               真仓（370 条标准 / 70 条被绑定 / 8 件生成物 · 零缺口）
  geo_synthetic_ok       合成语料（真源 write() 产出的**盘上原件** → 引擎重算须逐字节命中）
  geo_synthetic_tampered 合成语料 + 删掉一个索引锚点（漂移 + 锚点集合各报一条）
  geo_synthetic_absent   只有真源、没有生成物（逐件报缺 + 锚点集合报差）

用法：
    python probes/geo_export_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                      [--expect-embedded <SelfTest.cs>]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
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
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_geo_export_golden.json")
CATALOG = {
    "standards": [
        {"id": "a2", "title": "甲标准", "body": "机构甲", "url": "https://a.example/a2",
         "layer": "form", "ext_points": ["x-ext", "y-ext"],
         "evidence": {"reachable": True, "http_status": 200, "probe_date": "2026-01-01",
                      "sha256_sample": "abc"}},
        {"id": "b1", "title": "乙标准", "layer": "eng", "ext_points": [],
         "evidence": {"reachable": False, "http_status": 0, "probe_date": "2026-01-02",
                      "error": "URLError: boom"}},
    ],
    "coverage": {"standards": 2, "reachable": 1, "unreachable": 1, "bodies": 1,
                 "depends_edges": 1, "by_layer": {"eng": 1, "form": 1}},
}
BINDING = {"packs": [{"bindings": [{"standard": "a2", "support_standard": "b1"},
                                   {"standard": "a2"}]}]}


def digest32(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


def load_real(snap: Path):
    spec = importlib.util.spec_from_file_location("geo_export", str(snap / "scripts" / "geo_export.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def geo_log(geo, root: str) -> list:
    issues, _stats = geo.check(root)
    lines = ["[FAIL] %s" % i for i in issues]
    lines.append("GEO 出口 子扫描：%s" % ("零缺口" if not issues else "FAIL %d" % len(issues)))
    return lines


def snapshot_b64(root: Path) -> dict:
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[path.relative_to(root).as_posix()] = base64.b64encode(path.read_bytes()).decode("ascii")
    return out


def write_sources(tree: Path) -> None:
    (tree / "protocol").mkdir(parents=True, exist_ok=True)
    (tree / "protocol" / "standards_catalog.json").write_text(
        json.dumps(CATALOG, ensure_ascii=False, indent=2), encoding="utf-8", newline="")
    (tree / "protocol" / "standards_binding.json").write_text(
        json.dumps(BINDING, ensure_ascii=False, indent=2), encoding="utf-8", newline="")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    geo = load_real(snap)
    results: dict = {}

    def record(name, lines, extra=None):
        results[name] = {"log": lines, "digest32": digest32(lines),
                         "fails": sum(1 for l in lines if l.startswith("[FAIL] "))}
        if extra:
            results[name].update(extra)
        print(f"  {name}: FAIL {results[name]['fails']} · 摘要 {results[name]['digest32']}")
        for line in lines[:2]:
            print("     ", line[:110])

    record("geo_real", geo_log(geo, str(snap)))

    with tempfile.TemporaryDirectory(prefix="nf-geo-ok-") as tmp:
        tree = Path(tmp)
        write_sources(tree)
        geo.write(str(tree))
        record("geo_synthetic_ok", geo_log(geo, str(tree)), {"files_b64": snapshot_b64(tree)})

    with tempfile.TemporaryDirectory(prefix="nf-geo-tamper-") as tmp:
        tree = Path(tmp)
        write_sources(tree)
        geo.write(str(tree))
        idx = tree / "docs" / "standards" / "index.md"
        text = idx.read_text(encoding="utf-8")
        assert "### `a2`\n" in text
        idx.write_text(text.replace("### `a2`\n", "", 1), encoding="utf-8", newline="")
        record("geo_synthetic_tampered", geo_log(geo, str(tree)), {"files_b64": snapshot_b64(tree)})

    with tempfile.TemporaryDirectory(prefix="nf-geo-absent-") as tmp:
        tree = Path(tmp)
        write_sources(tree)
        record("geo_synthetic_absent", geo_log(geo, str(tree)), {"files_b64": snapshot_b64(tree)})

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-geo-export-golden/1",
            "generated": "2026-09-27",
            "source": "真源 scripts/geo_export.py::check（check38 子扫描 3 框法）",
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
        for key in ("geo_real", "geo_synthetic_ok", "geo_synthetic_tampered", "geo_synthetic_absent"):
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
                   ("geo_real", "geo_synthetic_ok", "geo_synthetic_tampered", "geo_synthetic_absent")
                   if results[k]["digest32"] not in cs]
        for key in ("geo_synthetic_ok", "geo_synthetic_tampered", "geo_synthetic_absent"):
            for rel, b64 in results[key]["files_b64"].items():
                if b64 not in cs:
                    missing.append(f"<{key}:{rel} base64>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 四条摘要 + 三份合成语料均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=1800)
        rows = json.loads(proc.stdout.decode("utf-8", errors="replace"))["rows"]
        mapping = (("GEO 出口·真仓", "geo_real"),
                   ("GEO 出口·合成语料", "geo_synthetic_ok"),
                   ("GEO 出口·合成漂移", "geo_synthetic_tampered"),
                   ("GEO 出口·缺生成物", "geo_synthetic_absent"))
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
        print("OK: 引擎侧 GEO 出口四条与真源逐字节同摘要")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
