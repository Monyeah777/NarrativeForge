"""LSP 文档级能力：位置换算 / 词法 / 大纲 / 诊断 / 文本编辑。

为什么独立成模块（2026-10-08 拆分）：\\`core/lsp.py\\` 加引用面后到 826 行（越过 800 行上限），
按纪律「能拆就拆」——**文档级能力**（一段文本进来、诊断/大纲/编辑出去，纯函数、无会话状态）
与**会话/传输**（分帧、状态机、能力声明）是两个变化原因。前者的判据是单测 + 帧级金标，
后者的判据是 \\`lsp.check\\` 与两轴同族判据。

口径（历史实证，勿改）：出参列一律 **UTF-16 码元**（与 capabilities 的 positionEncoding 一致）；
诊断必须带真实行/列（旧实现恒为 (0,0)，编辑器定位不到）；\\`text_edits\\` 出参是**单条整篇替换**
（NF 机械修复本身是整篇口径，碎片 edit 会让客户端 apply 顺序敏感），并先用 \\`apply_edits\\` 回放自校，
回放不回去就**不产出 edit**。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from core import autofix

#: 诊断严重度（LSP DiagnosticSeverity.Warning）
SEVERITY_WARNING = 2

def u16_len(s: str) -> int:
    """字符串的 UTF-16 码元长度（LSP 默认位置编码口径）。"""
    return sum(1 if ord(c) < 0x10000 else 2 for c in s)


def u16_col(line: str, cp_col: int) -> int:
    """码点列 → UTF-16 码元列（出口口径；BMP 外字符占 2）。"""
    return u16_len(line[:max(0, min(cp_col, len(line)))])


#: 单词/标识符：ASCII 词字符 + CJK + NF 的 id 形态（冒号/点/连字符/斜杠）
WORD = re.compile(r"[0-9A-Za-z_\u4e00-\u9fff][0-9A-Za-z_\u4e00-\u9fff:.\-/]*")


def word_span(line: str, col: int):
    """(词, 起, 止) 码点列口径；光标在空白处取左侧词，无词则空串。"""
    if not line:
        return "", 0, 0
    col = max(0, min(col, len(line)))
    for m in WORD.finditer(line):
        if m.start() <= col <= m.end():
            return m.group(0), m.start(), m.end()
    left = [m for m in WORD.finditer(line) if m.end() <= col]
    if not left:
        return "", col, col
    m = left[-1]
    return m.group(0), m.start(), m.end()


def prefix_before(line: str, col: int) -> str:
    """光标左侧的**词前缀**（补全面）；空前缀不触发补全。"""
    part = line[:max(0, min(col, len(line)))]
    m = re.search(r"[0-9A-Za-z_\u4e00-\u9fff:.\-/]+$", part)   # 取**末尾**那一段词
    return m.group(0) if m else ""


#: 标题与代码围栏（大纲要跳过围栏里的 # ——它不是标题）
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_FENCE = re.compile("^\\s*(" + chr(96) * 3 + "|~~~)")
#: 标题层级 → LSP SymbolKind（1 级=Module；2=Namespace；3+ 落 Function/Property）
SYMBOL_KIND = {1: 2, 2: 3, 3: 12, 4: 12, 5: 7, 6: 7}


def outline(text: str) -> List[Dict[str, Any]]:
    """标题树（层级嵌套；围栏内 # 不算标题）。"""
    root: List[Dict[str, Any]] = []
    stack: List[Dict[str, Any]] = []
    in_fence = False
    for i, raw in enumerate(text.split("\n")):
        if _FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(raw)
        if not m:
            continue
        level = len(m.group(1))
        node = {"name": m.group(2).strip(), "kind": SYMBOL_KIND.get(level, 12),
                "range": {"start": {"line": i, "character": 0},
                          "end": {"line": i, "character": u16_len(raw)}},
                "selectionRange": {"start": {"line": i, "character": u16_col(raw, level + 1)},
                                   "end": {"line": i, "character": u16_len(raw)}},
                "children": []}
        while stack and stack[-1]["_level"] >= level:
            stack.pop()
        (stack[-1]["children"] if stack else root).append(node)   # 挂到最近的上级标题下
        node["_level"] = level
        stack.append(node)

    def strip(nodes):
        for n in nodes:
            n.pop("_level", None)
            strip(n["children"])
    strip(root)
    return root


# ---------------------------------------------------------------- 折叠
def folding_ranges(text: str) -> List[Dict[str, Any]]:
    """Markdown 折叠区间（行号 0 基；LSP FoldingRange 口径）。

    两部分：**标题小节**（某标题行 → 下一个同级或更高级标题的前一行，直到文末）与**代码围栏**
    （起止围栏整段）。单行区间**不给**——规范允许客户端忽略单行折叠，给了只是噪声。

    为什么值得单列（2026-10-08）：本仓内容里长档很常见（02_联动注册表.md 1151 行、CHANGELOG 1538 行），
    编辑器里没有折叠就只能一路滚；而折叠的**真源**我们本来就有（标题结构 = 大纲判据的同一份口径），
    所以它是「派生自既有真源的能力」，不是新造事实。
    """
    lines = text.split("\n")
    heads: List[tuple] = []              # (行号, 级别)
    fences: List[tuple] = []
    in_fence = False
    fence_start = -1
    for i, raw in enumerate(lines):
        if _FENCE.match(raw):
            if in_fence:
                fences.append((fence_start, i))
                in_fence = False
            else:
                in_fence = True
                fence_start = i
            continue
        if in_fence:
            continue
        m = HEADING.match(raw)
        if m:
            heads.append((i, len(m.group(1))))
    out: List[Dict[str, Any]] = []
    for idx, (line, level) in enumerate(heads):
        end = len(lines) - 1
        for nxt_line, nxt_level in heads[idx + 1:]:
            if nxt_level <= level:
                end = nxt_line - 1
                break
        while end > line and not lines[end].strip():
            end -= 1                      # 尾部空行不折（折了也看不见内容，只是噪声）
        if end > line:
            out.append({"startLine": line, "endLine": end, "kind": "region"})
    for start, end in fences:
        if end > start:
            out.append({"startLine": start, "endLine": end, "kind": "region"})
    out.sort(key=lambda r: (r["startLine"], r["endLine"]))
    return out


# ---------------------------------------------------------------- 诊断
def _range_of(lines: List[str], line_no: int, start: int, end: int) -> Dict[str, Any]:
    """(行号, 码点起, 码点止) → LSP range（UTF-16 码元口径）。"""
    ln = min(max(line_no, 0), max(0, len(lines) - 1))
    body = lines[ln] if lines else ""
    return {"start": {"line": ln, "character": u16_col(body, start)},
            "end": {"line": ln, "character": u16_col(body, end)}}


def diagnose(path: str, text: str, root: str = ".") -> List[Dict[str, Any]]:
    """文档 → LSP 诊断（机械修复项 + 正文 lint 项）。

    内部差距实证（2026-10-05 修）：旧实现每条诊断恒为 (0,0)-(0,0)，编辑器收到的是**定位不到的
    提示**；本函数把每条诊断落到真实行/列（行尾空白指到第一个尾空格，末尾缺换行指到最后一行），
    出参列一律 UTF-16 码元（与 capabilities 的声明一致）。
    """
    lines = text.split("\n")
    out = _machine_diags(path, text, root, lines) + _prose_diags(text, root, lines)
    out.sort(key=lambda d: (d["range"]["start"]["line"], d["range"]["start"]["character"],
                            d["code"]))
    return out


def _machine_diags(path: str, text: str, root: str, lines: List[str]) -> List[Dict[str, Any]]:
    """机械修复项（autofix 规则）→ 诊断；每条都落到真实行/列。"""
    out: List[Dict[str, Any]] = []
    for rule in autofix.lint_rules(path, text, root):
        code = str(rule.get("rule") or "")
        if code == "trailing_ws":
            idx = next((i for i, ln in enumerate(lines) if ln != ln.rstrip()), None)
            if idx is None:
                continue
            body = lines[idx]
            rng = _range_of(lines, idx, len(body.rstrip()), len(body))
        elif code == "final_newline":
            last = max(0, len(lines) - 1)
            rng = _range_of(lines, last, 0, len(lines[last]) if lines else 0)
        else:
            rng = _range_of(lines, 0, 0, 0)
        out.append({"range": rng, "severity": SEVERITY_WARNING, "source": "nf",
                    "code": code, "message": str(rule.get("message") or code)})
    return out


def _prose_diags(text: str, root: str, lines: List[str]) -> List[Dict[str, Any]]:
    """正文 lint 项 → 诊断（源 nf-prose）；lint 不可用即降级为空，不打崩编辑器。"""
    try:
        from core import prose_lint
        findings = prose_lint.lint_text(text, extra_terms=prose_lint.load_custom_terms(root))
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for f in findings:
        line_no = int(f.get("line") or 0)
        snippet = str(f.get("snippet") or "")
        body = lines[line_no - 1] if 0 < line_no <= len(lines) else ""
        start = max(0, body.find(snippet)) if snippet else 0
        out.append({"range": _range_of(lines, line_no - 1, start, start + len(snippet)),
                    "severity": SEVERITY_WARNING, "source": "nf-prose",
                    "code": str(f.get("rule") or ""), "message": str(f.get("message") or "")})
    return out


# ---------------------------------------------------------------- 编辑（最小改动）
def _doc_lines(text: str) -> List[str]:
    return text.split("\n")


def _offset(lines: List[str], line: int, col: int) -> int:
    """（行, 列）码点位置 → 文本偏移（行号越界收敛到文末——不抛，诊断/编辑都不该打崩会话）。"""
    if line >= len(lines):
        return sum(len(x) + 1 for x in lines)
    return sum(len(x) + 1 for x in lines[:max(0, line)]) + max(0, col)


def apply_edits(text: str, edits: List[Dict[str, Any]]) -> str:
    """按 LSP 语义就地应用编辑（**码点列**口径；供最小改动的自校验使用）。"""
    lines = _doc_lines(text)
    spans = []
    for e in edits:
        r = e["range"]
        spans.append((_offset(lines, r["start"]["line"], r["start"]["character"]),
                      _offset(lines, r["end"]["line"], r["end"]["character"]), e["newText"]))
    out = text
    for start, end, rep in sorted(spans, reverse=True):
        out = out[:start] + rep + out[end:]
    return out


def _clamp_line(lines: List[str], i: int) -> int:
    """行号收敛到文档内（越界按文末那一行算——不抛，诊断/编辑都不该打崩会话）。"""
    return min(max(i, 0), max(0, len(lines) - 1))


def _full_range(lines: List[str]) -> Dict[str, Any]:
    """整篇范围（码点列口径）：起点 {0,0}，终点 = 末行行尾。"""
    last = max(0, len(lines) - 1)
    return {"start": {"line": 0, "character": 0},
            "end": {"line": last, "character": len(lines[last]) if lines else 0}}


def _as_u16(edits: List[Dict[str, Any]], lines: List[str]) -> List[Dict[str, Any]]:
    """码点列 range → UTF-16 码元列 range（出口口径，与 capabilities() 的声明一致）。"""
    out = []
    for e in edits:
        r = e["range"]
        out.append({"range": {
            "start": {"line": r["start"]["line"],
                      "character": u16_col(lines[_clamp_line(lines, r["start"]["line"])],
                                           r["start"]["character"])},
            "end": {"line": r["end"]["line"],
                    "character": u16_col(lines[_clamp_line(lines, r["end"]["line"])],
                                         r["end"]["character"])}},
            "newText": e["newText"]})
    return out


def text_edits(before: str, after: str) -> List[Dict[str, Any]]:
    """整篇改动 → **单条** LSP TextEdit（UTF-16 列口径）。

    为什么是整篇而不是逐行碎片：NF 的 quickfix 来源是 autofix.apply_rules——它是**整篇口径**的
    机械修复（行尾空白全篇清、末尾补换行、头部插位）。碎片 edit 会让客户端的 apply 顺序变得敏感，
    且与「一次机械修复 = 一次 applyEdit」的语义不符；单条整篇替换的 newText 天然小于原文
    （判据 test_code_action_edits_are_minimal_and_apply_cleanly 钉着 sum(len(newText)) < len(text)）。
    自校验：先用 apply_edits 回放，回放不回去就**不产出 edit**（宁可不改也不改错）。
    """
    if before == after:
        return []
    lines = _doc_lines(before)
    edits = [{"range": _full_range(lines), "newText": after}]
    if apply_edits(before, edits) != after:     # 出参列口径是 UTF-16，回放前先按码点列自校
        return []
    return _as_u16(edits, lines)
