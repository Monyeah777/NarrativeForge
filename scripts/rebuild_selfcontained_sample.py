#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自包含装配样本的重嵌工具（编码漂移修复 · 幂等 · 纯标准库）。

**背景**：自包含装配样本（`library/NF-TECHDOC-*.md` 等）把源文件正文**逐字内嵌**在
` ```markdown ` 围栏里，每段前用 `**4.N <名>** · 归属：… · 溯源：<路径>` 标注来源。
历史产物（2026-09-15 批次）出现**编码漂移**：内嵌正文被 UTF-8/GBK 双重转换，并伴随
行结构合并与围栏重复——产物既不可读，也不可被「按围栏切段」的解析器正确解析。
同一批次另有**管线声明**一段（其来源不在 `溯源：` 标记里，用 `--pipeline` 指定）。

**本工具做什么**：按产物内的 `溯源：` 标记，把各段内嵌正文**从源文件重嵌一遍**——
只替换围栏内的正文，不改 frontmatter、不改状态块、不改骨架文字；同时收掉重复的收尾围栏。
重嵌后正文与源文件**逐字相等**（可用 `--check` 复核），因此本工具幂等。

用法：
    python scripts/rebuild_selfcontained_sample.py --check <产物.md> [更多…] [--pipeline <管线.md>]
    python scripts/rebuild_selfcontained_sample.py --write <产物.md> [更多…] [--pipeline <管线.md>]

退出码：`--check` 有漂移 → 1，无漂移 → 0；`--write` 写回后返回 0。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

MARKER_RE = re.compile(r"^\*\*4\.\d+ .+? · 归属：.+? · 溯源：(.+?)\s*$")
PIPELINE_LEAD = "管线声明原文（内嵌）："
FENCE = "```"
TRAILER_RE = re.compile(r"^## 5\. 资产")
SCAFFOLD_3_RE = re.compile(r"^## 3\. 注册表投影")


def _read_lines(path: str, root: str = ".") -> list:
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    with open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def _next_nonblank(lines: list, i: int) -> int:
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    return j


def _blocks(lines: list, pipeline_src: str) -> list:
    """→ [{open, close, src, kind}]；open/close 为围栏行下标（close 为收尾围栏）。"""
    marks = [(i, m.group(1).strip()) for i, ln in enumerate(lines)
             for m in ([MARKER_RE.match(ln)] if MARKER_RE.match(ln) else [])]
    out = []
    for k, (idx, src) in enumerate(marks):
        op = _next_nonblank(lines, idx)
        if lines[op].strip() != FENCE + "markdown":
            raise SystemExit("标记行 L%d 之后不是 ```markdown 包裹：%r" % (idx + 1, lines[op]))
        if k + 1 < len(marks):
            cl = marks[k + 1][0] - 1
            while cl > op and not lines[cl].strip():
                cl -= 1
        else:
            trailer = next((i for i in range(op, len(lines)) if TRAILER_RE.match(lines[i])), len(lines))
            cl = max(i for i in range(op, trailer) if lines[i].strip() == FENCE)
        if lines[cl].strip() != FENCE:
            raise SystemExit("段 %d 的收尾围栏不在预期位置（L%d）：%r" % (k + 1, cl + 1, lines[cl]))
        out.append({"open": op, "close": cl, "src": src, "kind": "module"})
    # 管线段：以「管线声明原文（内嵌）：」为引，紧跟 ```markdown 包裹
    for i, ln in enumerate(lines):
        if ln.strip().startswith(PIPELINE_LEAD):
            op = _next_nonblank(lines, i)
            if lines[op].strip() != FENCE + "markdown":
                continue
            # 收尾围栏 = 下一节脚手架标题（§3 注册表投影）之前的最后一个围栏
            stop = next((j for j in range(op, len(lines)) if SCAFFOLD_3_RE.match(lines[j])), len(lines))
            cl = max((j for j in range(op, stop) if lines[j].strip() == FENCE), default=None)
            if cl is None:
                raise SystemExit("管线段收尾围栏未找到（引 L%d）" % (i + 1))
            out.append({"open": op, "close": cl, "src": pipeline_src, "kind": "pipeline"})
    return sorted(out, key=lambda b: b["open"])


def rebuild(text_lines: list, pipeline_src: str, root: str = ".") -> tuple:
    """→ (new_lines, changes)。changes = [{src, old_body, new_body, dup_fence}]。"""
    blocks = _blocks(text_lines, pipeline_src)
    out, changes, cursor = [], [], 0
    for b in blocks:
        out.extend(text_lines[cursor:b["open"] + 1])
        src_lines = _read_lines(b["src"], root)
        out.extend(src_lines)
        out.append(FENCE)
        nxt = b["close"] + 1
        dup = 0
        while nxt < len(text_lines) and text_lines[nxt].strip() == FENCE:
            dup += 1
            nxt += 1
        old_body = b["close"] - b["open"] - 1
        changes.append({"src": b["src"], "old_body": old_body, "new_body": len(src_lines),
                        "dup_fence": dup, "kind": b["kind"]})
        cursor = nxt
    out.extend(text_lines[cursor:])
    # 去掉重嵌后可能残留的空行差异：保持与原文一致的换行
    return out, changes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="自包含装配样本重嵌（编码漂移修复）")
    ap.add_argument("paths", nargs="+", help="产物 md 路径")
    ap.add_argument("--pipeline", default="community/技术文档域包/pipelines/P06_技术文档题材装配流管线.md",
                    help="管线声明段的源文件路径")
    ap.add_argument("--root", default=".", help="源路径解析根（缺省 = 当前目录 = 仓库根）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="只报告漂移，不写回")
    g.add_argument("--write", action="store_true", help="写回修复结果")
    args = ap.parse_args(argv)

    drift = 0
    for path in args.paths:
        if not os.path.isfile(path):
            print("缺文件：%s" % path, file=sys.stderr)
            return 2
        lines = _read_lines(path, args.root)
        new_lines, changes = rebuild(lines, args.pipeline, args.root)
        same = new_lines == lines
        mod = [c for c in changes if c["kind"] == "module"]
        pipe = [c for c in changes if c["kind"] == "pipeline"]
        print("%s：段 %d（模块 %d + 管线 %d）· 重复收尾围栏 %d 处 · %s"
              % (path, len(changes), len(mod), len(pipe),
                 sum(c["dup_fence"] for c in changes), "无漂移" if same else "**有漂移**"))
        shifted = [c for c in mod if c["old_body"] != c["new_body"]]
        print("    模块段正文行数不符的段数：%d / %d（不符即说明历史内容被并行/截断）"
              % (len(shifted), len(mod)))
        if not same:
            drift += 1
            if args.write:
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write("\n".join(new_lines) + "\n")
                print("    [OK] 已写回：%s" % path)
    if args.check:
        return 1 if drift else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
