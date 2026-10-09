#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""机械文本改写（**默认干跑**）：先给「文件:行号 + 改前 → 改后」对照表，人核后再 --write。

为什么需要（两次自伤换来的，2026-10-08）：
- 第一次：脚本按「起点标记 → 终点标记」切片搬运代码，边界取样错，删掉 270 行实现；
- 第二次：为修一处生成笔误写了**全仓批量替换**，把五处**合法正文**（行尾反斜杠续行说明、
  Windows 路径写法说明、`nf diff` 帮助）里的反斜杠悄悄削掉——语法不报、判据不报。
本仓已有的同类纪律（参照）：`core.atomic_write` 单写面、`rebind_audits.py --check` 干跑、
各生成器的 `--write/--check` 双态。本工具把这套惯例收敛成一个**通用**改写入口：
干跑优先、逐行对照、**爆炸半径闸门**（命中数超上限即拒绝，除非显式抬高）、原子写、UTF-8 钉死。

用法：
  python scripts/rewrite_text.py --find "旧文" --replace "新文" --include "desktop/**/*.py"
  python scripts/rewrite_text.py ... --write        # 确认无误后再落盘
  python scripts/rewrite_text.py ... --check        # 落盘后复验：还有命中即 rc=1
参数是**字面量**（不是正则）：改写这种动作不该有隐式转义解释。
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from typing import List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import atomic_write  # noqa: E402

#: 实际扫描/改写的根（默认仓根；可指向别处——判据在临时树上跑真流程，同 interop_thirdparty_kit）
BASE = ROOT

#: 爆炸半径默认上限：命中行数超过它就必须显式抬高（防「一处笔误改成全仓事故」）
DEFAULT_MAX_HITS = 50
#: 永不改写的目录（构建产物/缓存/版本库）
SKIP_DIRS = (".git", "node_modules", "__pycache__", ".rivet")


def iter_files(include: List[str]) -> List[str]:
    """按 include 模式列文件（相对 BASE、正斜杠口径）。"""
    out: List[str] = []
    for dirpath, dirnames, filenames in os.walk(BASE):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), BASE).replace(os.sep, "/")
            if any(fnmatch.fnmatch(rel, pat) or
                   (pat.startswith("**/") and fnmatch.fnmatch(rel, pat[3:]))
                   for pat in include):
                out.append(rel)          # 前导 **/ 也匹配根层（fnmatch 自身不这么算）
    return sorted(out)


def scan(files: List[str], find: str, repl: str) -> Tuple[List[Tuple[str, int, str, str]], List[str]]:
    """→ (命中 [(路径, 行号, 改前, 改后)], 跳过 [(路径, 原因)])；只处理能按 UTF-8 解开的文本件。"""
    hits: List[Tuple[str, int, str, str]] = []
    skipped: List[str] = []
    for rel in files:
        try:
            text = open(os.path.join(BASE, rel), encoding="utf-8").read()
        except (OSError, UnicodeDecodeError) as exc:
            skipped.append((rel, type(exc).__name__))
            continue
        for i, line in enumerate(text.split("\n"), 1):
            if find in line:
                hits.append((rel, i, line, line.replace(find, repl)))
    return hits, skipped


def render(hits, skipped, find, repl) -> None:
    for rel, i, before, after in hits:
        print("%s:%d" % (rel, i))
        print("  -  %s" % before.strip()[:160])
        print("  +  %s" % after.strip()[:160])
    for rel, why in skipped:
        print("  跳过 %s（%s）" % (rel, why))
    print("命中 %d 行 / %d 件（字面量 %r → %r）" % (len(hits), len({h[0] for h in hits}), find, repl))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="机械文本改写（默认干跑；--write 才落盘）")
    ap.add_argument("--find", required=True, help="要查找的**字面量**（非正则）")
    ap.add_argument("--replace", required=True, help="替换成的字面量")
    ap.add_argument("--include", action="append", required=True,
                    help="glob（可重复），如 desktop/**/*.py")
    ap.add_argument("--root", default="", help="扫描根（默认仓根；判据在临时树上跑真流程）")
    ap.add_argument("--max-hits", type=int, default=DEFAULT_MAX_HITS,
                    help="命中行数上限（默认 %d）；超限即拒绝，防误伤" % DEFAULT_MAX_HITS)
    ap.add_argument("--write", action="store_true", help="确认后落盘（默认只干跑）")
    ap.add_argument("--check", action="store_true", help="只验「还有没有命中」：有则 rc=1")
    args = ap.parse_args(argv)
    global BASE
    BASE = os.path.abspath(args.root) if args.root else ROOT

    files = iter_files(args.include)
    hits, skipped = scan(files, args.find, args.replace)
    if args.check:
        print("复验：仍命中 %d 处（include=%s）" % (len(hits), " ".join(args.include)))
        return 1 if hits else 0
    render(hits, skipped, args.find, args.replace)
    if not hits:
        return 0
    if len(hits) > args.max_hits:
        print("✗ 命中 %d 行 > 上限 %d：拒绝执行（防误伤）。确认无误后显式抬高 --max-hits"
              % (len(hits), args.max_hits))
        return 2
    if not args.write:
        print("（干跑完毕；确认对照表后加 --write 落盘）")
        return 0
    touched = {}
    for rel in sorted({h[0] for h in hits}):
        path = os.path.join(BASE, rel)
        text = open(path, encoding="utf-8").read()
        touched[rel] = text.count(args.find)
        atomic_write.write_text(path, text.replace(args.find, args.replace))
    left, _ = scan(sorted(touched), args.find, args.replace)
    print("已改写 %d 件、共 %d 处；复验残留 %d 处" % (len(touched), sum(touched.values()), len(left)))
    return 1 if left else 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
