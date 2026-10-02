#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规范入口指令的实测记录（CLI）：声明 → 真跑 → 落证据 → 判新鲜度。

用法：
  python scripts/instruction_evidence.py              # 只读校验（缺记录/非零/过期即 exit 1）
  python scripts/instruction_evidence.py --list       # 列声明与最近实测
  python scripts/instruction_evidence.py --record --only fast   # 只跑轻档指令并写证据
  python scripts/instruction_evidence.py --record --only all    # 全跑（含 verify / release）
  python scripts/instruction_evidence.py --record --only verify # 只跑某条

纪律：argv 列表执行、**不用 shell**（purity R6 危险 sink 面）；`python X` 一律替换为当前解释器。
"""
import argparse
import os
import shlex
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import instruction_evidence as ie  # noqa: E402
from core import posix_shell as psh  # noqa: E402


def _runner(cmd: str):
    """声明里的命令 → argv 列表执行（无 shell）；返回 (exit_code, output)。"""
    argv = shlex.split(cmd)
    if not argv:
        return 1, "空命令"
    if argv[0] in ("python", "python3"):
        argv[0] = sys.executable
    elif argv[0] in ("bash", "sh") and shutil.which(argv[0]) is None:
        # POSIX shell 统一走 core.posix_shell（PATH → NF_BASH → Git for Windows 反推 → Unix 常规位）：
        # 本机（Windows 原生）`bash` 不在 PATH，不解析就会把「本机环境差异」误记成
        # 「指令不可执行」——那是假证据。
        argv[0] = psh.posix_shell()
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=3600)
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, "执行失败：%s" % exc
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="规范入口指令实测记录（文档可执行性面）")
    ap.add_argument("--record", action="store_true", help="真跑并把证据写回声明件")
    ap.add_argument("--only", default="fast", help="all / fast / <指令 id>（缺省 fast）")
    ap.add_argument("--list", action="store_true", help="列声明与最近实测")
    args = ap.parse_args(argv)

    if args.list:
        doc, issues = ie.load(ROOT)
        for i in issues:
            print("  ✗ %s" % i, file=sys.stderr)
        if not doc:
            return 1
        ev = doc.get("evidence") or {}
        print("== 规范入口指令（%d 条） ==" % len(doc.get("instructions") or []))
        for it in doc["instructions"]:
            rec = ev.get(it["id"]) or {}
            print("  %-14s %-46s %s" % (it["id"], it["cmd"],
                                        ("✓ %s exit=%s" % (rec.get("ran_at"), rec.get("exit_code")))
                                        if rec else "（无实测记录）"))
        return 0 if not issues else 1

    if args.record:
        bad, doc = ie.record(ROOT, only=args.only, runner=_runner)
        print("== 指令实测记录（only=%s） ==" % args.only)
        for iid, rec in sorted((doc.get("evidence") or {}).items()):
            print("  %-14s exit=%s · %s" % (iid, rec.get("exit_code"), rec.get("ran_at")))
        if bad:
            print("  ✗ 退出码非 0：%s（修复指引：先修到 0 再 --record）" % "、".join(bad),
                  file=sys.stderr)
        return 1 if bad else 0

    issues, warns, stats = ie.scan(ROOT)
    print("== 指令实测记录校验 ==")
    print("  声明 %d 条 · 有记录 %d 条" % (stats.get("declared", 0), stats.get("recorded", 0)))
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
