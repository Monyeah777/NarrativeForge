#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""演练保真度（CLI）：把两套 drill 的结果量化成数字并判达标。

用法：
  python scripts/drill_fidelity.py           # 只读：任一例不达标或找不到载体即 exit 1
  python scripts/drill_fidelity.py --json    # 打印完整度量 JSON
  python scripts/drill_fidelity.py --write   # 落盘 protocol/drill_fidelity.json（供机器消费）
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import drill_fidelity as df  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="演练保真度量化（执行演练 + 回合级回放）")
    ap.add_argument("--write", action="store_true", help="落盘度量结果")
    ap.add_argument("--json", action="store_true", help="打印完整度量")
    args = ap.parse_args(argv)

    if args.write:
        issues, doc = df.write(ROOT)
        print("== 演练保真度 --write ==")
        print("  ✓ 已写入 %s（总保真 %.1f%% · %d/%d）"
              % (df.REPORT_REL, doc["overall"]["fidelity"] * 100,
                 doc["overall"]["passed"], doc["overall"]["cases"]))
        for i in issues[:5]:
            print("  ✗ %s" % i, file=sys.stderr)
        return 1 if issues else 0

    m = df.measure(ROOT)
    if args.json:
        print(json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    issues, warns, _s = df.scan(ROOT)
    ex, rnd, ov = m["execution"], m["rounds"], m["overall"]
    print("== 演练保真度 ==")
    print("  执行演练：%d 例集 / %d 例 · 通过 %d · **保真度 %.1f%%**"
          % (len(ex["sets"]), ex["cases"], ex["passed"], ex["fidelity"] * 100))
    print("  回合级回放：%d 样本 · 复现 %d · **保真度 %.1f%%**"
          % (rnd["total"], rnd["matched"], rnd["fidelity"] * 100))
    print("  总口径：%d/%d · **%.1f%%**" % (ov["passed"], ov["cases"], ov["fidelity"] * 100))
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
