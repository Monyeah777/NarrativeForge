#!/usr/bin/env python3
"""联邦规模探针：把社区包**翻倍复制**（改 id 前缀）后，两侧是否仍逐字段一致 + 引擎耗时如何。

为什么单开一面：前面几套探针都在「真实语料 + 定向变异」上工作，没有一面回答
「**联邦长大以后**（社区包翻倍、模块翻倍）引擎还对不对、还扛不扛得住」。
NF 的路线是社区域包规模化扩展，这条必须自己量，不能靠感觉。

做法：复制隔离快照 → 克隆 N 个真实社区包（重写包名与模块 id 前缀，其余字段照抄）
→ 两侧各跑一遍一致性报告 → 逐契约比对 (ok/detail/digest) + 记录耗时。

用法：
    python probes/scale_probe.py --snapshot <隔离快照> --cli <nf-dotnet> [--parity <nfparity>] [--packs 120]
    python probes/scale_probe.py --snapshot <隔离快照> --cli <nf-dotnet> --packs 1000 --engine-only

注：`--engine-only` 跳过 Python 侧（千包规模下 Python 侧要跑一小时量级，不在本面口径内）
——此时**只量引擎侧伸缩与受控性**，不做两侧逐契约对账，输出里会显式声明。

退出码：0 全部逐字段一致；1 有差异或异常。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def clone_packs(work: Path, source_pack: str, count: int) -> int:
    """克隆一个真实社区包 count 次（重写包名与模块 id 前缀），返回实际克隆数。"""
    src = work / "community" / source_pack
    if not src.is_dir():
        raise SystemExit("找不到样板包：%s" % src)
    made = 0
    for i in range(1, count + 1):
        name = "规模P%d域包" % i
        prefix = "规模P%d" % i
        dst = work / "community" / name
        if dst.exists():
            continue
        shutil.copytree(src, dst)
        for path in dst.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            text = text.replace(source_pack, name).replace("AI农业", prefix)
            path.write_text(text, encoding="utf-8", newline="\n")
        made += 1
    return made


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--cli", required=True, help="nf-dotnet（量聚合门用）")
    ap.add_argument("--parity", default="", help="nfparity（读一致性报告用）")
    ap.add_argument("--py-exe", default=sys.executable)
    ap.add_argument("--packs", type=int, default=120)
    ap.add_argument("--work", default="")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--engine-only", action="store_true",
                    help="跳过 Python 侧（千包规模下 Python 跑不动）；只量引擎侧伸缩")
    args = ap.parse_args()

    snap = Path(args.snapshot).resolve()
    work = Path(args.work).resolve() if args.work else snap.parent / (snap.name + "-scale")
    print("样板快照：%s\n规模副本：%s" % (snap, work))
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(snap, work)

    base_packs = len([p for p in (work / "community").iterdir() if p.is_dir()])
    made = clone_packs(work, "AI农业域包", args.packs)
    now_packs = len([p for p in (work / "community").iterdir() if p.is_dir()])
    modules = len(list((work / "community").glob("*/modules/*.md")))
    print("社区包 %d → %d（克隆 %d）· 社区模块文档 %d" % (base_packs, now_packs, made, modules))

    env = dict(os.environ)
    env["PYTHONPATH"] = str(work / "desktop" / "src")
    env["PYTHONIOENCODING"] = "utf-8"

    report = None
    if args.engine_only:
        print("口径声明：--engine-only —— 只量引擎侧伸缩与受控性，不做两侧逐契约对账"
              "（千包规模下 Python 侧不在本面口径内）")
    else:
        start = time.time()
        py = subprocess.run([args.py_exe, str(work / "scripts" / "nf.py"), "conformance", "--json"],
                            cwd=str(work), capture_output=True, env=env)
        py_sec = time.time() - start
        if py.returncode not in (0, 1):
            print("  ✗ Python 侧退出码 %d：%s" % (py.returncode, py.stderr.decode("utf-8", "replace")[-400:]))
            return 1
        report = json.loads(py.stdout.decode("utf-8"))["report"]
        print("Python 一致性报告：%d/%d 契约 · root=%s · %.1fs"
              % (report["passed"], report["total"], report["root"][:16], py_sec))

    start = time.time()
    net = subprocess.run([args.cli, "--root", str(work), "verify"], capture_output=True, env=env)
    net_sec = time.time() - start
    print("引擎聚合只读门：exit=%d · %.1fs" % (net.returncode, net_sec))
    if net.returncode not in (0, 1, 2):
        print("  ✗ 引擎在规模语料上异常退出：%d" % net.returncode)
        return 1

    if args.engine_only:
        start = time.time()
        rows = subprocess.run([args.parity, "--conformance", str(work)], capture_output=True, env=env) \
            if args.parity else None
        if rows is not None:
            ported = json.loads(rows.stdout.decode("utf-8"))["ported"]
            print("引擎一致性报告：%d 条已移植 · %.1fs（仅引擎侧自跑，无 Python 侧对账）"
                  % (len(ported), time.time() - start))
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)
        return 0 if net.returncode in (0, 1) else 1

    if not args.parity:
        print("\n（未给 --parity：只做规模冒烟，不做逐契约对账）")
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)
        return 0 if net.returncode in (0, 1) else 1

    start = time.time()
    rows = subprocess.run([args.parity, "--conformance", str(work)], capture_output=True, env=env)
    parity_sec = time.time() - start
    ported = json.loads(rows.stdout.decode("utf-8"))["ported"]
    by_id = {c["id"]: c for c in report["contracts"]}
    mismatches = []
    for row in ported:
        want = by_id[row["id"]]
        for field in ("ok", "detail", "digest"):
            if want.get(field) != row.get(field):
                mismatches.append((row["id"], field, want.get(field), row.get(field)))
    print("引擎一致性报告：%d 条已移植 · %.1fs" % (len(ported), parity_sec))
    print("\n规模对账：%d 条 · 字段差异 %d" % (len(ported), len(mismatches)))
    for cid, field, want, got in mismatches[:10]:
        print("  [差异] %s.%s\n     py =%r\n     net=%r" % (cid, field, str(want)[:160], str(got)[:160]))
    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
