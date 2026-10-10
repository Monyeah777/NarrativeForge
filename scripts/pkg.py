#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NF 包管理器面（只读）：定义库品类的枚举 / 取件 / 检索。

底层 = core.category_registry（品类真源）+ core.package_index（取件面）。本脚本是它们的
用户面入口（与 nf CLI 同源依赖，不新开 core 边）。

用法：
  python scripts/pkg.py categories                    # 品类总表（含 LAYERS 归属标记）
  python scripts/pkg.py ls core-pipelines             # 品类条目
  python scripts/pkg.py show community-pipelines:P04  # 按 品类:id 取件（附首 3 行）
  python scripts/pkg.py find M55                      # 跨品类按 id 检索
  python scripts/pkg.py check                         # 品类注册表自检（含归属缺口）
  （以上均可加 --json）
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))


def _emit(kind, payload, as_json, lines):
    """人读逐行打印 / 机器面 JSON（kind 判别键与仓库机器面口径一致）。"""
    if as_json:
        print(json.dumps(dict(kind=kind, **payload), ensure_ascii=False, indent=2, sort_keys=True))
        return
    for ln in lines:
        print(ln)


def _cmd_categories(as_json):
    from core import category_registry as cr
    cats = cr.categories(ROOT)
    rows = [{"id": c["id"], "title": c["title"], "tier": c["tier"],
             "attributed": bool(c.get("attributed")),
             "files": len(cr.files(ROOT, c["id"])),
             "globs": list(c["globs"])} for c in cats]
    lines = ["== 定义库品类（%d）==" % len(rows)]
    for r in rows:
        lines.append("  %-24s %-8s attributed=%-5s files=%-4d %s"
                     % (r["id"], r["tier"], r["attributed"], r["files"],
                        r["globs"][0] if r["globs"] else ""))
    _emit("pkg-categories", {"count": len(rows), "rows": rows}, as_json, lines)


def _cmd_ls(cat, as_json):
    from core import package_index as pi
    rows = pi.entries(ROOT, cat)
    lines = ["== %s（%d 条）==" % (cat, len(rows))]
    for r in rows:
        lines.append("  %-20s %s" % (r["id"], r["path"]))
    _emit("pkg-ls", {"category": cat, "count": len(rows), "rows": rows}, as_json, lines)


def _cmd_show(ref, as_json):
    from core import package_index as pi
    hits = pi.find(ROOT, ref)
    head = pi.read_text(ROOT, hits[0]["category"], hits[0]["id"]).splitlines()[:3] if hits else []
    lines = ["== %s（%d 命中）==" % (ref, len(hits))]
    for h in hits:
        lines.append("  %-20s [%s] %s" % (h["id"], h["category"], h["path"]))
    if head:
        lines.append("--- 首 3 行 ---")
        lines.extend(head)
    _emit("pkg-show", {"ref": ref, "count": len(hits), "rows": hits, "head": head}, as_json, lines)


def _cmd_check(as_json):
    """品类注册表自检：id 唯一 / glob 命中 / LAYERS 归属缺口（消费 category_registry.scan）。"""
    from core import category_registry as cr
    issues, warns, stats = cr.scan(ROOT)
    if as_json:
        print(json.dumps({"kind": "pkg-check", "ok": not issues, "issues": issues,
                          "warns": warns, "stats": stats},
                         ensure_ascii=False, indent=2, sort_keys=True))
        return 1 if issues else 0
    print("== 品类注册表自检 ==")
    print("  品类 %d · LAYERS 归属 %d · 未归属 %d"
          % (stats.get("categories", 0), stats.get("attributed", 0),
             stats.get("unattributed", 0)))
    for w in warns:
        print("  [WARN] " + w)
    for i in issues:
        print("  [FAIL] " + i)
    return 1 if issues else 0


def _cmd_find(ref, as_json):
    from core import package_index as pi
    rows = pi.find(ROOT, ref)
    lines = ["== find %s（%d 命中）==" % (ref, len(rows))]
    for r in rows:
        lines.append("  %-20s [%s] %s" % (r["id"], r["category"], r["path"]))
    _emit("pkg-find", {"ref": ref, "count": len(rows), "rows": rows}, as_json, lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="NF 包管理器面（只读）")
    ap.add_argument("cmd", choices=("categories", "ls", "show", "find", "check"))
    ap.add_argument("arg", nargs="?", default="", help="品类名（ls）/ 引用（show/find）")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = ap.parse_args(argv)
    if args.cmd == "categories":
        _cmd_categories(args.json)
    elif args.cmd == "ls":
        _cmd_ls(args.arg, args.json)
    elif args.cmd == "show":
        _cmd_show(args.arg, args.json)
    elif args.cmd == "check":
        return _cmd_check(args.json)
    else:
        _cmd_find(args.arg, args.json)
    return 0


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        if hasattr(_s, "reconfigure"):
            _s.reconfigure(encoding="utf-8")
    raise SystemExit(main())
