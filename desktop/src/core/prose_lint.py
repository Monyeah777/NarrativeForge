"""正文级 lint（内部差距实证：NF 的风格门是 M80 的**档位 DNA 资产**——靠执行方自觉比对，
没有机器可跑的正文检查；仓库全域无正文 lint 件）。

本模块把「风格门」补上**执行侧机检**：对正文段落跑确定性规则，输出可寻址的发现项
（行号 + 规则 + 片段），供 `nf lint --prose` 与 LSP 诊断消费。

规则取向 = 「AI 味」的可判定面（不判文笔好坏，只标机械特征）：
`cliche_open` 陈词滥调开头 / `summary_tail` 总结腔收尾 / `lecture_tone` 说教腔 /
`binary_parallel` 对称句式 / `triple_adj` 四字词堆砌 / `repeat_connector` 段首连接词复用 /
`hedge_overuse` 模糊限定词过密 / `punct_mix` 中英标点混用。

纪律：只报告不阻断（正文质量不由机器判死刑）；规则集可由资产键 `PROSE_LINT` 扩展
（05_资产库/用户自定义），与 NF「风格档位化」同源——不在协议层内嵌固定风格条目。
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

CLICHES = ("在这个", "随着时代", "众所周知", "不言而喻", "无论如何", "某种程度上",
           "在当今", "如今的社会", "无需多言")
SUMMARY_TAILS = ("总而言之", "综上所述", "总之", "总的来说", "综上")
LECTURE = ("我们应该", "让我们", "请记住", "要知道", "我们必须")
CONNECTORS = ("然而", "与此同时", "值得一提的是", "不仅如此", "更重要的是", "毫无疑问")
HEDGES = ("似乎", "仿佛", "或许", "也许", "可能", "大概", "某种程度上")

#: 触发阈值（可按档位覆盖）
HEDGE_PER_1000 = 12.0
TRIPLE_ADJ_MIN = 3

_BINARY = re.compile(r"不是[^。；\n]{1,20}而是|不仅[^。；\n]{1,20}而且|"
                     r"既要[^。；\n]{1,20}又要")
_QUAD = re.compile(r"(?:[\u4e00-\u9fa5]{4}、){2,}[\u4e00-\u9fa5]{4}")
_PUNCT = re.compile(r"[\u4e00-\u9fa5][,;:!?]")
_FENCE = re.compile(r"^\s*```")

#: 资产扩展槽（存在则并入自定义词表）
CUSTOM_ASSET = "05_资产库/用户自定义/PROSE_LINT.md"


def load_custom_terms(root: str = ".") -> List[str]:
    """读资产槽里的自定义禁用词（每行一个；缺文件 = 空）。"""
    path = os.path.join(root, CUSTOM_ASSET)
    if not os.path.exists(path):
        return []
    terms = []
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith(("#", ">", "-", "|")):
                terms.append(ln)
    return terms


def _prose_lines(text: str) -> List[tuple]:
    """正文行 = 非代码围栏内的非结构行（跳过标题/引用/表格/列表/分隔线）。"""
    out, in_fence = [], False
    for i, ln in enumerate(text.splitlines(), 1):
        if _FENCE.match(ln):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        s = ln.strip()
        if not s or s[0] in "#>|" or s.startswith("- ") or s.startswith("* "):
            continue
        if re.match(r"^\d+[.、]", s):
            continue
        out.append((i, s))
    return out


def lint_text(text: str, extra_terms: Optional[List[str]] = None,
              hedge_per_1000: float = HEDGE_PER_1000) -> List[Dict[str, object]]:
    """正文 → 发现项列表 [{rule, line, message, snippet}]（1 基行号）。"""
    out: List[Dict[str, object]] = []
    lines = _prose_lines(text)
    body = "".join(s for _i, s in lines)
    terms = list(CLICHES) + list(extra_terms or [])

    for no, s in lines:
        hit = next((w for w in terms if w in s), None)
        if hit:
            out.append({"rule": "cliche_open", "line": no,
                        "message": "陈词滥调/套话：「%s」" % hit, "snippet": s[:40]})
        tail = next((w for w in SUMMARY_TAILS if w in s), None)
        if tail:
            out.append({"rule": "summary_tail", "line": no,
                        "message": "总结腔：「%s」" % tail, "snippet": s[:40]})
        lec = next((w for w in LECTURE if w in s), None)
        if lec:
            out.append({"rule": "lecture_tone", "line": no,
                        "message": "说教腔：「%s」" % lec, "snippet": s[:40]})
        m = _BINARY.search(s)
        if m:
            out.append({"rule": "binary_parallel", "line": no,
                        "message": "对称句式（AI 腔高发）：%s" % m.group(0)[:20],
                        "snippet": s[:40]})
        q = _QUAD.search(s)
        if q and q.group(0).count("、") + 1 >= TRIPLE_ADJ_MIN:
            out.append({"rule": "triple_adj", "line": no,
                        "message": "四字词堆砌（≥%d 连）：%s"
                                   % (TRIPLE_ADJ_MIN, q.group(0)[:24]),
                        "snippet": s[:40]})
        p = _PUNCT.search(s)
        if p:
            out.append({"rule": "punct_mix", "line": no,
                        "message": "中英标点混用：%s" % p.group(0), "snippet": s[:40]})

    starts = [s[:4] for _no, s in lines]
    for c in CONNECTORS:
        hits = [i for i, st in enumerate(starts) if st.startswith(c)]
        if len(hits) >= 2:
            out.append({"rule": "repeat_connector", "line": lines[hits[1]][0],
                        "message": "段首连接词复用 %d 次：「%s」" % (len(hits), c),
                        "snippet": c})

    if body:
        n_hedge = sum(body.count(w) for w in HEDGES)
        per_1k = n_hedge * 1000.0 / max(1, len(body))
        if per_1k > hedge_per_1000:
            out.append({"rule": "hedge_overuse", "line": 0,
                        "message": "模糊限定词过密：%.1f 次/千字（阈值 %.1f）"
                                   % (per_1k, hedge_per_1000), "snippet": ""})
    out.sort(key=lambda f: (f["line"], f["rule"]))
    return out


def summarize(findings: List[Dict[str, object]]) -> Dict[str, int]:
    """按规则计数（便于门禁/报告聚合）。"""
    counts: Dict[str, int] = {}
    for f in findings:
        counts[f["rule"]] = counts.get(f["rule"], 0) + 1
    return counts
