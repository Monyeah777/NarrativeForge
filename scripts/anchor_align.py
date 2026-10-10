#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""双向锚定对齐报告（只读）：标准目录利用率（反向）+ 词汇交叉候选（正向）。

用法：
  python scripts/anchor_align.py                      # 人读报告
  python scripts/anchor_align.py --json               # 机器面
  python scripts/anchor_align.py --unbound --layer gov
  python scripts/anchor_align.py --find 模型量化 --layer iface
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="双向锚定对齐（反向利用率 / 正向词汇交叉）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ap.add_argument("--unbound", action="store_true", help="列出未绑定标准")
    ap.add_argument("--layer", default="", help="限定标准 layer：data/iface/form/gov/eng")
    ap.add_argument("--find", default="", help="正向：词汇交叉候选")
    ap.add_argument("--bootstrap", default="", help="正向自举：词汇 → 种子标准 → 依赖扩层")
    ap.add_argument("--depth", type=int, default=1, help="自举展开层数（缺省 1）")
    ap.add_argument("--packs", action="store_true", help="逐域包标准对齐概览（层覆盖宽度升序）")
    ap.add_argument("--shallow", type=int, default=0,
                    help="只列层覆盖宽度 ≤ N 的域包（0=不过滤）")
    ap.add_argument("--limit", type=int, default=20, help="候选上限（缺省 20）")
    args = ap.parse_args(argv)
    from core import anchor_align as aa

    if args.find:
        rows = aa.intersect(ROOT, args.find, layer=args.layer, limit=args.limit)
        if args.json:
            print(json.dumps({"kind": "anchor-align-find", "term": args.find, "rows": rows},
                             ensure_ascii=False, indent=2, sort_keys=True))
        else:
            for r in rows:
                print("  %-16s [%s] hits=%d %s" % (r["id"], r["layer"], r["hits"], r["title"]))
            print("  （%d 条候选）" % len(rows))
        return 0
    if args.packs:
        rows = (aa.shallow_packs(ROOT, args.shallow) if args.shallow > 0
                else aa.pack_stats(ROOT))
        if args.json:
            print(json.dumps({"kind": "anchor-align-packs", "count": len(rows), "rows": rows},
                             ensure_ascii=False, indent=2, sort_keys=True))
        else:
            for r in rows:
                print("  %-8s breadth=%d stds=%-2d bindings=%-2d 缺层=%s %s"
                      % (r["code"], r["layer_breadth"], r["distinct_standards"],
                         r["bindings"], ",".join(r["missing_layers"]) or "-",
                         r["category"]))
            print("  （%d 个域包，按层覆盖宽度升序）" % len(rows))
        return 0
    if args.bootstrap:
        rows = aa.bootstrap(ROOT, args.bootstrap, depth=args.depth, limit=args.limit)
        if args.json:
            print(json.dumps({"kind": "anchor-align-bootstrap", "term": args.bootstrap,
                              "depth": args.depth, "rows": rows},
                             ensure_ascii=False, indent=2, sort_keys=True))
        else:
            for r in rows:
                print("  d%d %-18s [%s] hits=%d via=%s" % (r["depth"], r["id"], r["layer"],
                                                           r["hits"], r["via"]))
            print("  （%d 个节点）" % len(rows))
        return 0
    if args.unbound:
        rows = aa.unbound(ROOT, layer=args.layer)
        if args.json:
            print(json.dumps({"kind": "anchor-align-unbound", "count": len(rows), "rows": rows},
                             ensure_ascii=False, indent=2, sort_keys=True))
        else:
            for r in rows:
                print("  %-16s [%s] %s" % (r["id"], r.get("layer", ""), r.get("title", "")))
            print("  （未绑定 %d 条）" % len(rows))
        return 0
    st = aa.stats(ROOT)
    if args.json:
        print(json.dumps({"kind": "anchor-align", **st}, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(aa.report(ROOT))
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8")
    raise SystemExit(main())
