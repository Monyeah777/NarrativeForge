"""图书馆入库许可证门（内部差距实证：library 登记表只有 编号/标题/形态/投稿人/日期/一句话，
**无许可列**；第三方投稿的共享条款只写在投稿须知里，入库产物与登记行都不承载它。
仓库全域 license 命中仅 tool_face 的 candidate 字段校验，content 侧没有许可门）。

判据（与 INDEX 投稿须知同源，不另造新标准）：
- 每条登记行的「许可」列必须有值，且取值 ∈ 许可词表（SPDX 子集 / 专有 / 未声明）；
- 取值 `未声明` 允许存在（投稿人未回填），但计入 WARN 挂账——**入口不静默通过**；
- 条目文件应带内联许可声明（`> 许可：…` 或 frontmatter `license: …`），
  存量pre-gate 条目缺失时同样记 WARN（不回填不阻断，但不隐身）。

纪律：本门只判「许可声明是否在场/合规」，不判内容质量，也不替投稿人做授权判断。
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Tuple

INDEX_REL = "library/INDEX.md"
UNDECLARED = "未声明"

#: 许可词表（SPDX 子集 + 专有 + 未声明）
ALLOWED = {
    "MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "ISC",
    "CC-BY-4.0", "CC-BY-SA-4.0", "CC0-1.0", "专有", UNDECLARED,
}

_ROW = re.compile(r"^\|\s*(NF-[A-Za-z0-9\-]+)\s*\|")
_INLINE = re.compile(r"(?m)^\s*(?:>\s*)?(?:许可|license)\s*[:：]\s*([^\s（(]+)")


def _cells(row: str) -> List[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def parse_index(root: str = ".") -> List[Dict[str, Any]]:
    """解析登记表数据行 → [{id, title, topic, author, date, license, cells}]。"""
    path = os.path.join(root, INDEX_REL)
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            if not _ROW.match(ln):
                continue
            c = _cells(ln)
            if len(c) < 6:
                continue
            rows.append({"id": c[0], "title": c[1], "topic": c[2], "author": c[3],
                         "date": c[4], "license": c[5] if len(c) >= 7 else "",
                         "cells": c})
    return rows


def inline_license(root: str, entry_id: str) -> str:
    """条目文件内联许可声明（缺 = 空串）。"""
    path = os.path.join(root, "library", "%s.md" % entry_id)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        head = fh.read(4000)
    m = _INLINE.search(head)
    return m.group(1).strip() if m else ""


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """→ (issues, stats)。issues = FAIL 级；未声明/无内联 = WARN 级（在 stats 内）。"""
    issues: List[str] = []
    warnings: List[str] = []
    rows = parse_index(root)
    undeclared, unknown, no_inline, mismatched = [], [], [], []
    for r in rows:
        lic = r["license"]
        if not lic:
            issues.append("登记行缺「许可」列值：%s（修复指引：按许可词表补值，"
                          "投稿人未回填写「%s」）" % (r["id"], UNDECLARED))
            continue
        if lic not in ALLOWED:
            issues.append("许可取值不在词表：%s = %s（允许：%s）"
                          % (r["id"], lic, "、".join(sorted(ALLOWED))))
            unknown.append(r["id"])
            continue
        if lic == UNDECLARED:
            warnings.append("许可未声明（待投稿人确认）：%s" % r["id"])
            undeclared.append(r["id"])
        inner = inline_license(root, r["id"])
        if not inner:
            warnings.append("条目文件缺内联许可声明：%s（修复指引：文件头补 "
                            "「> 许可：<SPDX>」）" % r["id"])
            no_inline.append(r["id"])
        elif inner != lic:
            warnings.append("许可双源不一致：%s 登记=%s 文件=%s"
                            % (r["id"], lic, inner))
            mismatched.append(r["id"])
    stats = {"entries": len(rows), "declared": len(rows) - len(undeclared) - len(unknown),
             "undeclared": undeclared, "unknown": unknown,
             "no_inline": no_inline, "mismatched": mismatched,
             "warnings": warnings}
    return issues, stats
