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
    ap.add_argument("--check", action="store_true", help="注册表完整性：未声明的引擎目录即 exit 1")
    ap.add_argument("--abi", action="store_true", help="动态加载 ABI 探针：装载平台 C 运行库并调用一次")
    args = ap.parse_args(argv)
    from core import engine_registry as er

    if args.abi:
        from core import engine_loader as el
        doc = el.abi_probe()
        if args.json:
            print(json.dumps({"kind": "engine-abi", **doc}, ensure_ascii=False,
                             indent=2, sort_keys=True))
        else:
            print("  ABI 机制：%s（%s）" % ("可用" if doc["ok"] else "不可用", doc["detail"]))
        return 0 if doc["ok"] else 1

    if args.check:
        bad = er.issues(ROOT)
        if args.json:
            print(json.dumps({"kind": "engine-check", "ok": not bad, "issues": bad,
                              "engine_dirs": er.engine_dirs(ROOT)},
                             ensure_ascii=False, indent=2, sort_keys=True))
        else:
            for b in bad:
                print("  [FAIL] " + b)
            print("  引擎目录 %d · 未声明 %d" % (len(er.engine_dirs(ROOT)), len(bad)))
        return 1 if bad else 0

    if args.json:
        print(json.dumps({"kind": "engine-status", "status": er.status(ROOT),
                          "matrix": er.matrix(ROOT)},
                         ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    from core import engine_loader as el
    for line in er.report_lines(ROOT):
        print(line)
    for d in er.engine_dirs(ROOT):
        libs = el.provider_libs(ROOT, d)
        print("  engine/%s/ 候选共享库 %d%s" % (
            d, len(libs), ("：" + "、".join(libs[:2])) if libs else ""))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8")
    raise SystemExit(main())
