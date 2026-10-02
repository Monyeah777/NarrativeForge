#!/usr/bin/env python3
"""出口/派生面两腿双跑对账探针：

- **他证通道**（check38 第二腿 · `scripts/interop_thirdparty_kit.py::check`）：回填状态表体检；
- **互操作入仓一致性**（check33 第 14 条）：`results/interop/*.json` vs `core.interop_export.render` 逐字节。

两腿都**直接用真源代码**：他证通道以 importlib 加载脚本后调 `check`；入仓面按 check33 第 14 条的原文逻辑
（`for kind in ie.KINDS: 在盘 bytes vs ie.render(kind)`）复跑。产物写入**真源侧**日志口径：
他证通道按 check38 的框法（FAIL 行 + `<label> 子扫描：<零缺口|FAIL N>`），入仓面只列 FAIL 行（真源该条成功时不打印任何内容）。

用法：
    python probes/exit_faces_probe.py --snap <snapshot> [--cli <nf-dotnet>] [--write-fixture]
                                      [--expect-embedded <SelfTest.cs>]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
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
DEFAULT_FIXTURE = _paths.engine("probes", "_fixtures", "_exit_faces_golden.json")
KIT_REL = "scripts/interop_thirdparty_kit.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_core(snap: Path):
    src = str(snap / "desktop" / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    import core.interop_export as ie  # noqa: PLC0415
    return ie


def digest32(lines) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:32]


def decode(raw: bytes) -> str:
    for enc in ("utf-8", "gbk", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def thirdparty_log(kit, root: Path, label: str = "他证通道") -> tuple[list, dict]:
    issues, stats = kit.check(str(root))
    lines = ["[FAIL] %s" % i for i in issues]
    lines.append("%s 子扫描：%s" % (label, "零缺口" if not issues else "FAIL %d" % len(issues)))
    return lines, stats


def inrepo_issues(ie, root: Path) -> list:
    """check33 第 14 条的原文逻辑（缺件与漂移各汇总一条）。"""
    missing, drift = [], []
    directory = root / "results" / "interop"
    if not directory.is_dir():
        return []
    for kind in ie.KINDS:
        path = directory / ("%s.json" % kind)
        if not path.is_file():
            missing.append(kind)
            continue
        if path.read_bytes() != ie.render(kind, str(root)):
            drift.append(kind)
    issues = []
    if missing:
        issues.append("互操作入仓面缺件：%s（修复指引：nf interop --all --out results/interop）"
                      % ",".join(missing))
    if drift:
        issues.append("互操作入仓面与实时派生不一致：%s（修复指引：重跑 nf interop --all "
                      "——入仓面是派生投影，不是真源）" % ",".join(drift))
    return issues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snap", default=DEFAULT_SNAP)
    ap.add_argument("--cli", default="")
    ap.add_argument("--fixture", default=DEFAULT_FIXTURE)
    ap.add_argument("--write-fixture", action="store_true")
    ap.add_argument("--expect-embedded", default="")
    args = ap.parse_args()

    snap = Path(args.snap).resolve()
    kit = load_module(snap / KIT_REL, "nf_thirdparty_kit")
    ie = load_core(snap)
    results = {}

    # 他证通道：真仓
    lines, stats = thirdparty_log(kit, snap)
    results["thirdparty_real"] = {"log": lines, "digest32": digest32(lines),
                                  "fails": len(lines) - 1, "stats": {k: v for k, v in stats.items()}}
    print(f"  他证通道·真仓：FAIL {results['thirdparty_real']['fails']} · stats {stats} "
          f"· 摘要 {results['thirdparty_real']['digest32']}")

    # 他证通道：篡改（删一面行 + 坏 sha256 + not-applicable 空 note）
    with tempfile.TemporaryDirectory(prefix="nf-ef-kit-") as tmp:
        tree = Path(tmp)
        (tree / "results").mkdir(parents=True, exist_ok=True)
        (tree / "docs").mkdir(parents=True, exist_ok=True)
        src = (snap / kit.STATUS_REL).read_text(encoding="utf-8").splitlines()
        kept, dropped, done_sha, done_note = [], False, False, False
        for line in src:
            cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("| `") else []
            if len(cells) >= 11 and cells[0].strip("`") == "ccv3" and not dropped:
                dropped = True                      # 整行删掉 → 状态表缺面
                continue
            if len(cells) >= 11 and cells[8] and not done_sha:
                cells[8] = "deadbeef"               # sha256 不是 64 位十六进制
                line = "| " + " | ".join(cells) + " |"
                done_sha = True
            if len(cells) >= 11 and cells[10] == "" and not done_note:
                cells[10] = ""                      # not-applicable 面 note 留空
                line = "| " + " | ".join(cells) + " |"
                done_note = True
            kept.append(line)
        (tree / kit.STATUS_REL).write_text("\n".join(kept) + "\n", encoding="utf-8", newline="")
        shutil.copyfile(snap / kit.DOC_REL, tree / kit.DOC_REL)
        lines, stats = thirdparty_log(kit, tree)
        tampered_bytes = (tree / kit.STATUS_REL).read_bytes()
    results["thirdparty_tampered"] = {
        "log": lines, "digest32": digest32(lines), "fails": len(lines) - 1,
        "files_b64": {kit.STATUS_REL: base64.b64encode(tampered_bytes).decode("ascii")},
    }
    print(f"  他证通道·篡改：FAIL {results['thirdparty_tampered']['fails']} "
          f"· 摘要 {results['thirdparty_tampered']['digest32']}")
    for line in lines[:3]:
        print("     ", line[:110])

    # 他证通道：缺状态表
    with tempfile.TemporaryDirectory(prefix="nf-ef-nokit-") as tmp:
        lines, stats = thirdparty_log(kit, Path(tmp))
    results["thirdparty_absent"] = {"log": lines, "digest32": digest32(lines), "fails": len(lines) - 1}
    print(f"  他证通道·缺件：FAIL {results['thirdparty_absent']['fails']} · 摘要 {results['thirdparty_absent']['digest32']}")

    # 入仓面：真仓 + 篡改一个 kind
    issues = inrepo_issues(ie, snap)
    log = ["[FAIL] %s" % i for i in issues]
    results["inrepo_real"] = {"log": log, "digest32": digest32(log), "fails": len(issues)}
    print(f"  入仓面·真仓：FAIL {len(issues)} · 摘要 {results['inrepo_real']['digest32']}")

    with tempfile.TemporaryDirectory(prefix="nf-ef-inrepo-") as tmp:
        tree = Path(tmp)
        # 全量复制快照：入仓面渲染根 = root，缺源会让 render 退化成空文档 → 假漂移。
        # 只篡改一个 kind，必须整棵拷贝才能保证「恰好一个 kind 漂移」。
        shutil.copytree(snap, tree / "tree")
        tree = tree / "tree"
        target = tree / "results" / "interop" / "sbom.json"
        target.write_bytes(target.read_bytes().replace(b'"created"', b'"created_x"', 1))
        issues = inrepo_issues(ie, tree)
    log = ["[FAIL] %s" % i for i in issues]
    results["inrepo_tampered"] = {"log": log, "digest32": digest32(log), "fails": len(issues)}
    print(f"  入仓面·篡改：FAIL {len(issues)} · 摘要 {results['inrepo_tampered']['digest32']}")
    for line in log[:2]:
        print("     ", line[:110])

    fixture_path = Path(args.fixture)
    if args.write_fixture:
        payload = {
            "schema": "nf-exit-faces-golden/1",
            "generated": "2026-09-27",
            "source": "他证通道=真源脚本 check()；入仓面=check33 第 14 条原文逻辑（ie.KINDS × render 逐字节）",
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
        for key in ("thirdparty_real", "thirdparty_tampered", "thirdparty_absent",
                    "inrepo_real", "inrepo_tampered"):
            want, got = fixture["cases"][key]["digest32"], results[key]["digest32"]
            print(f"  [{'OK ' if want == got else '漂移'}] {key}: 金标 {want} / 本轮 {got}")
            if want != got:
                drift.append(key)
        if drift:
            print(f"FAIL: 真源输出已漂移 {drift}")
            return 1
        print("OK: 金标向量与真源本轮输出一致（五条用例）")

    if args.expect_embedded:
        cs = Path(args.expect_embedded).read_text(encoding="utf-8")
        missing = [rel for rel, b64 in results["thirdparty_tampered"]["files_b64"].items() if b64 not in cs]
        for key in ("thirdparty_real", "thirdparty_tampered", "thirdparty_absent",
                    "inrepo_real", "inrepo_tampered"):
            if results[key]["digest32"] not in cs:
                missing.append(f"<{key} 摘要>")
        if missing:
            print(f"FAIL: 机械导出纪律——以下内容未出现在 {args.expect_embedded}：{missing}")
            return 1
        print(f"OK: 篡改件 base64 与五条摘要均已写进 {Path(args.expect_embedded).name}")

    if args.cli:
        proc = subprocess.run([args.cli, "--root", str(snap), "selftest", "--json"],
                              capture_output=True, timeout=900)
        rows = json.loads(decode(proc.stdout))["rows"]
        bad = []
        for prefix, case in (("出口面·他证通道·真仓", "thirdparty_real"),
                             ("出口面·他证通道·篡改", "thirdparty_tampered"),
                             ("出口面·他证通道·缺件", "thirdparty_absent"),
                             ("出口面·入仓一致·真仓", "inrepo_real"),
                             ("出口面·入仓一致·篡改", "inrepo_tampered")):
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
        print("OK: 引擎侧出口面两腿与真源逐字节同摘要（真材 + 合成树）")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
