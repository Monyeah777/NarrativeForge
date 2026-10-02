#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""代码规模/复杂度上限（CLI）：棘轮式冻结 + 只增不减校验。

用法：
  python scripts/code_metrics.py            # 只读扫描（超线即 exit 1）
  python scripts/code_metrics.py --json     # 打印逐文件度量
  python scripts/code_metrics.py --write    # 评审后冻结当前度量为基线
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import code_metrics as cm  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="代码规模/复杂度上限（架构纯度面）")
    ap.add_argument("--write", action="store_true", help="冻结当前度量为基线")
    ap.add_argument("--json", action="store_true", help="打印逐文件度量 JSON")
    args = ap.parse_args(argv)

    if args.write:
        issues, doc = cm.write(ROOT)
        print("== 冻结代码度量基线 ==")
        print("  ✓ 已写入 %s（%d 件）" % (cm.BASELINE_REL, len(doc["files"])))
        for i in issues:
            print("  ✗ %s" % i, file=sys.stderr)
        return 1 if issues else 0

    if args.json:
        print(json.dumps(cm.measure(ROOT), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    issues, warns, stats = cm.scan(ROOT)
    print("== 代码规模/复杂度上限 ==")
    print("  文件 %d（基线 %d）· 最大行数 %d · 最长函数 %d 行 · 最大圈复杂度 %d"
          % (stats["files"], stats["baseline"], stats["max_lines"],
             stats["max_fn_lines"], stats["max_fn_cc"]))
    for w in warns:
        print("  [WARN] %s" % w)
    for i in issues[:20]:
        print("  ✗ %s" % i, file=sys.stderr)
    if len(issues) > 20:
        print("  … 其余 %d 条同类" % (len(issues) - 20), file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    # stdio 钉 UTF-8：Windows 控制台 GBK 下 ✓/✗ 即 UnicodeEncodeError（同 nf.py）
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
