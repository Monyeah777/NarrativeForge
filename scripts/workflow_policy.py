#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作流供应链策略机检（CLI）：`python scripts/workflow_policy.py [--json]`。

判据本体见 `core/workflow_policy.py`（外部标准：ossf/scorecard 的
Pinned-Dependencies / Token-Permissions，2026-09-29 取源）。
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import workflow_policy as wp  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="工作流供应链策略（actions 钉 SHA + permissions 最小）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = ap.parse_args(argv)
    issues, warns, stats = wp.scan(ROOT)
    if args.json:
        print(json.dumps({"issues": issues, "warns": warns, "stats": stats},
                         ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if issues else 0
    print("== 工作流供应链策略 ==")
    print("  工作流 %d 件 · 已钉 SHA 的 uses %d 条 · 显式 permissions 的工作流 %d 件"
          % (stats["workflows"], stats["pinned_uses"], stats["with_explicit_permissions"]))
    for w in warns:
        print("  [WARN] %s" % w)
    for i in issues[:10]:
        print("  ✗ %s" % i, file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
