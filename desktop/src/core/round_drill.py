"""45 A2 · 回合级执行 drill（在 execution_drill 句子级之上加“回合级”断言）。

对整段执行转录按「回合」切块，逐回合断言：
- R-R1 本回合至少一条引用（§/第N节|步|章/L行/模块编号）——对齐 no_citation（句子级）；
- R-R2 本回合有推进/状态留痕（推进/进入/写回/快照/存档/状态）——对齐 browse_repeat 反向；
- R-R3 本回合不得出现允许集外编号（编造编号，对齐 fabricated_id）；
- R-R4 回合计数连续（第 N 回合后应接第 N+1，容许跳号则标 WARN 清单，不 FAIL）。

转录标记约定：行首 `回合 N：` 或 `第 N 回合` 开新回合。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

_TURN = re.compile(r"^[#>\s]*(?:回合\s*(\d+)\s*[:：]|第\s*(\d+)\s*回合)", re.M)
_CITE = re.compile(r"(§\s*\d+(?:[.-]\d+)*|第\s*\d+\s*(?:节|步|章)|L\d+|"
                   r"[0-9A-Za-z_]+:[MTP]\d{2,3}|\b\d{1,3}\b\s*行)")
_PROGRESS = ("推进", "进入", "写回", "快照", "存档", "状态", "回合")
_MODULE = re.compile(r"(?:[\u4e00-\u9fff]+:)?M\d{2,3}")


def scan(transcript: str, allowed: List[str]) -> Tuple[List[str], Dict[str, Any]]:
    issues: List[str] = []
    matches = list(_TURN.finditer(transcript))
    turns = []
    for idx, m in enumerate(matches):
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(transcript)
        num = int(m.group(1) or m.group(2))
        body = transcript[start:end]
        turns.append((num, body))
    if not turns:
        issues.append("未检测到回合标记（转录需含 回合 N： / 第 N 回合）")
        return issues, {"turns": 0, "warn_gaps": []}
    allowed = set(allowed)
    gaps = []
    for i, (num, body) in enumerate(turns):
        if not _CITE.search(body):
            issues.append("第 %d 回合缺引用（R-R1）" % num)
        if not any(k in body for k in _PROGRESS):
            issues.append("第 %d 回合无推进/状态留痕（R-R2）" % num)
        for tok in _MODULE.findall(body):
            if tok not in allowed and tok.split(":", 1)[-1] not in {
                    a.split(":", 1)[-1] for a in allowed}:
                issues.append("第 %d 回合出现允许集外编号 %s（R-R3）" % (num, tok))
        if i > 0 and num != turns[i - 1][0] + 1:
            gaps.append((turns[i - 1][0], num))
    return issues, {"turns": len(turns), "warn_gaps": gaps}
