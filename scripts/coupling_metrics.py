#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模块级耦合度量 + 存量债棘轮（Martin 包度量 / SDP）。

用法：
  python scripts/coupling_metrics.py           # 只读：新增环/新增 SDP 违例即 exit 1
  python scripts/coupling_metrics.py --json    # 打印逐模块 Ca/Ce/I
  python scripts/coupling_metrics.py --write    # 评审后把存量债登记进基线
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import coupling_metrics as cm  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="模块级耦合度量（Martin 包度量 / SDP / 环）")
    ap.add_argument("--write", action="store_true", help="登记当前存量耦合债")
    ap.add_argument("--json", action="store_true", help="打印逐模块 Ca/Ce/I")
    args = ap.parse_args(argv)

    if args.write:
        issues, doc = cm.write(ROOT)
        print("== 登记耦合基线 ==")
        print("  ✓ 已写入 %s（环 %d · SDP %d · 模块 %d）"
              % (cm.BASELINE_REL, len(doc["cycles"]), len(doc["sdp"]), len(doc["metrics"])))
        return 1 if issues else 0

    deps, metrics = cm.graph(ROOT)
    if args.json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    issues, warns, stats = cm.scan(ROOT)
    print("== 模块级耦合度量 ==")
    print("  模块 %d · 环 %d（登记 %d）· SDP 违例 %d（登记 %d）"
          % (stats["modules"], stats["cycles"], stats["registered_cycles"],
             stats["sdp"], stats["registered_sdp"]))
    for w in warns:
        print("  [WARN] %s" % w)
    for i in issues[:10]:
        print("  ✗ %s" % i, file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
