#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引擎 provider 状态（只读）：有哪些引擎实现 / 语言与工具链 / 本机能否装载。

用法：
  python scripts/engine_status.py           # 人读
  python scripts/engine_status.py --json    # 机器面
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="引擎 provider 状态（Registry Pattern）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = ap.parse_args(argv)
    from core import engine_registry as er

    if args.json:
        print(json.dumps({"kind": "engine-status", "status": er.status(ROOT),
                          "matrix": er.matrix(ROOT)},
                         ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    for line in er.report_lines(ROOT):
        print(line)
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8")
    raise SystemExit(main())
