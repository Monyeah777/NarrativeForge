#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""门禁机器可读报告（CLI）：`protocol/verification_report.json`。

用法：
  python scripts/verify_report.py            # 只打印摘要（不落盘）
  python scripts/verify_report.py --json     # 打印完整 JSON
  python scripts/verify_report.py --write    # 落盘 protocol/verification_report.json
  python scripts/verify_report.py --check    # 已落盘报告 == 实时重算（CI 用；败即 exit 1）
  python scripts/verify_report.py --fresh    # 只判新鲜度（不看 FAIL 数；供入口指令自证，见下）

`--check` 与 `--fresh` 的分工（2026-09-29）：`--check` 是**闸门**（新鲜度 + 零 FAIL/ERROR，
CI 用）；`--fresh` 只判新鲜度。入口指令 `nf release` 与实测记录里的 `report` 用 `--fresh`——
它们的成败若包含「报告自身的 FAIL 数」，就与报告里的 `instruction_evidence` 判据构成不动点
（release 要绿 ⇒ 报告要零 FAIL ⇒ 要求 release 记录为绿 ⇒ 循环），闸门那侧的牙齿由
`--check` 与 `verify.sh` 保留，不靠入口指令兜。
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import verify_report as vr  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="门禁机器可读报告（静态可核验面）")
    ap.add_argument("--write", action="store_true",
                    help="落盘 protocol/verification_report.json")
    ap.add_argument("--check", action="store_true",
                    help="已落盘报告 == 实时重算（不一致即 exit 1）")
    ap.add_argument("--fresh", action="store_true",
                    help="只判新鲜度：已落盘 == 实时重算（不看 FAIL 数）")
    ap.add_argument("--json", action="store_true", help="打印完整 JSON")
    args = ap.parse_args(argv)

    if args.check or args.fresh:
        issues, report = vr.check(ROOT)
        if args.json:
            print(vr.render(report), end="")
        print("== 门禁机器可读报告 check ==", file=sys.stderr)
        print("  %s" % vr.summary_line(report), file=sys.stderr)
        for i in issues:
            print("  ✗ %s" % i, file=sys.stderr)
        if issues:
            return 1
        print("  ✓ 已落盘报告与实时重算一致", file=sys.stderr)
        if args.fresh:
            return 0
        return 0 if report["summary"]["fail"] == 0 and report["summary"]["error"] == 0 else 1

    if args.write:
        issues, report = vr.write(ROOT)
        print("== 门禁机器可读报告 write ==")
        print("  ✓ 已写入 %s" % vr.REPORT_REL)
        print("  %s" % vr.summary_line(report))
        for i in issues:
            print("  ✗ %s" % i, file=sys.stderr)
        return 1 if issues else 0

    report = vr.build(ROOT)
    if args.json:
        print(vr.render(report), end="")
    else:
        print("== 门禁机器可读报告（只读摘要） ==")
        print("  %s" % vr.summary_line(report))
        for i in report["items"]:
            if i["status"] != "pass":
                print("  [%s] %-20s issues=%d warns=%d%s"
                      % (i["status"].upper(), i["id"], i["issues"], i["warns"],
                         ("；例：" + i["sample"][0][:90]) if i["sample"] else ""))
    return 0 if report["summary"]["fail"] == 0 and report["summary"]["error"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
