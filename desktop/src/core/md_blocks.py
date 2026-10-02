"""Markdown 列表块的**唯一解析出处**：一条 bullet 含其后的缩进续行（换行续写算同一条）。

为什么单独成件（2026-10-01）：静态扫「重复函数体」时抓到 `handover._bullet_blocks` 与
`postmortem._bullet_blocks` 是**逐字相同的两份拷贝**（各 15 行，同语义：交接的「未决项」
与复盘的「行动项」都按 bullet 块切分）。同一件事两份实现的风险是**改一份忘一份**——
这正是本仓「单一真相源」纪律要清的那类逻辑垃圾。

纪律：纯标准库叶子件（不 import 任何 core 模块）——按 SDP，越稳定的约定越该沉到叶子，
由不稳侧（handover / postmortem）依赖它。
"""
from __future__ import annotations

import re
from typing import List

#: bullet 行（`- x` / `* x`，允许前导空白）
BULLET_RE = re.compile(r"^\s*[-*]\s+")


def bullet_blocks(text: str) -> List[str]:
    """把列表按「bullet 块」切分：一条 bullet 含其后续缩进续行（换行续写算同一条）。"""
    blocks: List[str] = []
    cur: List[str] = []
    for line in text.splitlines():
        if BULLET_RE.match(line):
            if cur:
                blocks.append("\n".join(cur).strip())
            cur = [line]
        elif cur and line.strip():
            cur.append(line)
        elif cur:
            blocks.append("\n".join(cur).strip())
            cur = []
    if cur:
        blocks.append("\n".join(cur).strip())
    return blocks
