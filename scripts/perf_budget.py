#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""性能预算（CLI）：声明 → 实测 N 次 → 落证据 → 判新鲜度与预算。

用法：
  python scripts/perf_budget.py              # 只读校验（缺记录/过期/超预算即 exit 1）
  python scripts/perf_budget.py --list       # 列声明与最近实测
  python scripts/perf_budget.py --record     # 全部实测并写证据（缺省）
  python scripts/perf_budget.py --record --only nf_score
"""
import argparse
import os
import shlex
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import perf_budget as pb  # noqa: E402


def _runner(cmd: str, runs: int):
    """真跑 N 次 → (last_exit_code, [ms,...])；argv 列表执行（无 shell）。"""
    argv = shlex.split(cmd)
    if not argv:
        return 1, []
    if argv[0] in ("python", "python3"):
        argv[0] = sys.executable
    elif shutil.which(argv[0]) is None:
        for cand in (os.environ.get("NF_BASH", ""), r"C:\comfyui\Git\bin\bash.exe",
                     r"C:\Program Files\Git\bin\bash.exe"):
            if cand and os.path.isfile(cand):
                argv[0] = cand
                break
    times, code = [], 1
    for _ in range(max(1, runs)):
        t0 = time.perf_counter()
        try:
            p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=1800)
            code = p.returncode
        except (OSError, subprocess.SubprocessError):
            code = 1
        times.append((time.perf_counter() - t0) * 1000.0)
    return code, times


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="性能预算（ISO 25010 性能效率面）")
    ap.add_argument("--record", action="store_true", help="实测并写证据")
    ap.add_argument("--only", default="all", help="all / <目标 id>（缺省 all）")
    ap.add_argument("--list", action="store_true", help="列声明与最近实测")
    args = ap.parse_args(argv)

    if args.list:
        doc, issues = pb.load(ROOT)
        for i in issues:
            print("  ✗ %s" % i, file=sys.stderr)
        if not doc:
            return 1
        ev = doc.get("evidence") or {}
        print("== 性能预算（%d 条） · 参考机 %s ==" % (len(doc.get("entries") or []),
                                                      doc.get("reference_host", "?")))
        for e in doc["entries"]:
            r = ev.get(e["id"]) or {}
            print("  %-14s 预算 %6.0f ms · %s"
                  % (e["id"], float(e.get("budget_ms") or 0),
                     ("实测中位 %6.0f ms（%s · min %.0f / max %.0f）"
                      % (r.get("median_ms", 0), r.get("measured_at"), r.get("min_ms", 0),
                         r.get("max_ms", 0))) if r else "（无实测记录）"))
        return 0 if not issues else 1

    if args.record:
        bad, doc = pb.record(ROOT, only=args.only, runner=_runner)
        print("== 性能预算实测（only=%s） ==" % args.only)
        for eid, r in sorted((doc.get("evidence") or {}).items()):
            flag = "✗ 超预算" if eid in bad else "✓"
            print("  %s %-14s 中位 %7.0f ms · 预算 %7.0f ms · exit=%s"
                  % (flag, eid, r.get("median_ms", 0), float(r.get("budget_ms") or 0),
                     r.get("exit_code")))
        if bad:
            print("  ✗ 超预算：%s（修复指引：定位退化点或评审后调整预算）" % "、".join(bad),
                  file=sys.stderr)
        return 1 if bad else 0

    issues, warns, stats = pb.scan(ROOT)
    print("== 性能预算校验 ==")
    print("  声明 %d 条 · 有记录 %d 条 · 超预算 %d 条"
          % (stats["declared"], stats["recorded"], stats["over_budget"]))
    for w in warns:
        print("  [WARN] %s" % w)
    for i in issues[:10]:
        print("  ✗ %s" % i, file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    # stdio 钉 UTF-8：Windows 控制台 GBK 下 ✓/✗ 即 UnicodeEncodeError（同 nf.py）
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
