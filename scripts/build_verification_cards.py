#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证卡册生成器（`docs/verification-cards.md` 的**可复现**投影）。

为什么入库：卡册此前自称由 `build_verification_cards.ps1` 生成，而该脚本**不在仓库**——
对外是「不可复现的产物」，漂移已经实际发生（卡册写 2409 行，verify.sh 实为 2516 行）。
本脚本以 `verify.sh` 为**单一真源**，重建两处**生成区**（全册概况表 + 卡片索引表），
不动卡片正文；`--check` 只读校验（生成区 == 实时重算）。

用法：
  python scripts/build_verification_cards.py           # 只校验（不一致即 exit 1）
  python scripts/build_verification_cards.py --write   # 重写生成区
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "desktop" / "src"))    # core.*（原子写单源；2026-10-01 普查补齐）
from core import atomic_write  # noqa: E402
DOC = ROOT / "docs" / "verification-cards.md"
VERIFY = ROOT / "verify.sh"

_CHECK = re.compile(r"^check(\d+)\(\)\{", re.M)
_FIRST_ECHO = re.compile(r"echo '([^']*)'")
_TITLE = re.compile(r"\[(\d+)/(\d+)·([ABC])\]")

SEGMENT = {"A": "段A", "B": "段B", "C": "段C"}


def _checks() -> list:
    """→ [{n, title, segment, kind}]，按 verify.sh 出现顺序。"""
    text = VERIFY.read_text(encoding="utf-8")
    marks = list(_CHECK.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[m.end():end]
        head = _FIRST_ECHO.search(body)
        title = head.group(1) if head else "（缺 echo 标题）"
        seg = _TITLE.search(title)
        kind = "真实单测（unittest）" if "unittest" in body else "结构断言"
        out.append({"n": int(m.group(1)), "title": title,
                    "segment": SEGMENT.get(seg.group(3), "段C") if seg else "段C",
                    "kind": kind})
    return out


def _baseline() -> tuple:
    src = (ROOT / "desktop" / "src" / "core" / "quality_baseline.py").read_text(encoding="utf-8")
    checks = re.search(r"EXPECTED_CHECKS = (\d+)", src)
    passed = re.search(r"EXPECTED_PASS = (\d+)", src)
    return int(checks.group(1)), int(passed.group(1))


def render() -> str:
    """重建两处生成区 → 文档全文（其余部分原样保留）。"""
    doc = DOC.read_text(encoding="utf-8")
    rows = _checks()
    n_checks, n_pass = _baseline()
    n_lines = len(VERIFY.read_text(encoding="utf-8").splitlines())
    seg_count = {k: sum(1 for r in rows if r["segment"] == k) for k in ("段A", "段B", "段C")}
    n_unit = sum(1 for r in rows if r["kind"].startswith("真实单测"))
    overview = [
        "| 项 | 值 |",
        "|---|---|",
        "| 卡片总数 | %d（= verify.sh 的 check 函数数，实测） |" % len(rows),
        "| 门禁脚本 | %d 行（verify.sh 实测） |" % n_lines,
        "| 声明基线 | check1-%d · PASS=%d（源自 quality_baseline.EXPECTED_*） |"
        % (n_checks, n_pass),
        "| 段位分布 | 段A 官方核心 %d · 段B 社区包 %d · 段C 代码层 %d |"
        % (seg_count["段A"], seg_count["段B"], seg_count["段C"]),
        "| 断言种类 | 真实单测 %d 条 · 结构断言 %d 条 |" % (n_unit, len(rows) - n_unit),
        "| 复跑入口 | `bash verify.sh`（全量）；单条见各卡片的「复跑命令」 |",
    ]
    index = ["| # | 段位 | 门禁标题 | 断言种类 |", "|---|---|---|---|"]
    index += ["| %d | %s | %s | %s |" % (r["n"], r["segment"], r["title"], r["kind"])
              for r in rows]
    doc = _replace_block(doc, "## 全册概况（由生成器统计，非手写）", overview)
    doc = _replace_block(doc, "## 卡片索引", index)
    return doc


def _replace_block(doc: str, heading: str, table: list) -> str:
    """把 heading 之后的第一段表格换成 table（保留 heading 行与后续小节，空白规范化）。"""
    i = doc.index(heading)
    head_end = doc.index("\n", i) + 1
    lines = doc[head_end:].splitlines(keepends=True)
    j = 0
    while j < len(lines) and (lines[j].strip() == "" or lines[j].startswith("|")):
        j += 1
    return doc[:head_end] + "\n" + "\n".join(table) + "\n" + "".join(lines[j:])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="验证卡册生成（真源 = verify.sh）")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="重写生成区（缺省只校验）")
    # `--check` 是 docstring 与调用方都写着的那面旗标；收显式（缺省同义），免得照抄文档
    # 反而吃 argparse 的用法错误（「照抄就能跑」——与本件同门的文档示例门禁同一条纪律）。
    mode.add_argument("--check", action="store_true", help="只校验（缺省行为，显式可读）")
    args = ap.parse_args(argv)
    want = render()
    cur = DOC.read_text(encoding="utf-8")
    if want == cur:
        print("  ✓ 验证卡册生成区与 verify.sh 一致（%d 条）" % len(_checks()))
        return 0
    if args.write:
        atomic_write.write_text(DOC, want)
        print("  ✓ 已重写生成区：%d 条 check" % len(_checks()))
        return 0
    print("  ✗ 验证卡册生成区与 verify.sh 不一致（修复指引：python scripts/"
          "build_verification_cards.py --write）", file=sys.stderr)
    return 1


if __name__ == "__main__":
    # stdio 钉 UTF-8：Windows 控制台 GBK 下 ✓/✗ 即 UnicodeEncodeError（同 nf.py）
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
