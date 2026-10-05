"""静默跳过的**成文理由**判据（单一真相源）。

为什么单独成模块：同一条纪律此前有**两份实现**——门禁
`desktop/tests/test_silent_skip_reasons.py`（AST 版：窗口 = `try` 行及其上三行 + handler 体行）
与缺口引擎 `core/gap_review._silent_skip_candidates`（行扫版：只认**紧邻上一行**或 except 行内联）。
口径一宽一窄 ⇒ 2026-10-01 `nf review` 在真仓报出 **8 条假缺口**（逐条核过：全是有理由的站点——
理由写在内层 `try` 体那一行，或 `try` 行上三行内）。判据与引擎对同一件事必须同口径，故规则
收敛到这里，两边都调它（`test_silent_skip_reasons` 仍保留全部断言与变异自证，只是不再自带实现）。

口径（与门禁历史写法逐字一致，未放宽）：
- **站点** = `try` 的某个 handler 体**只有** `pass` 或 `continue`；
- **成文理由** = `try` 行及其上三行、或 handler 体那一行里出现 `#`（任一行即可）。

另收录第二种吞错形态 `silent_returns`（`except → return 空值` 且**完全不留痕**），同样由门禁调用。
"""
from __future__ import annotations

import ast


def silent_skips(text: str) -> list:
    """→ `[(try 行号, handler 行号, 'pass'|'continue', 是否有注释)]`（纯函数）。"""
    lines = text.splitlines()
    out: list = []
    try:
        tree = ast.parse(text)
    except SyntaxError:                    # 语法都不成立的件交给语法级判据（ruff/py_compile）报
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        for h in node.handlers:
            body = h.body
            if len(body) != 1 or not isinstance(body[0], (ast.Pass, ast.Continue)):
                continue
            lo, hi = node.lineno - 1, body[0].lineno - 1
            block = lines[lo:hi + 1] + lines[max(0, lo - 3):lo]
            kind = "pass" if isinstance(body[0], ast.Pass) else "continue"
            out.append((node.lineno, h.lineno, kind, any("#" in ln for ln in block)))
    return out


def unjustified(text: str) -> list:
    """→ 没有成文理由的站点（纯函数，变异自证直接喂它）。"""
    return [s for s in silent_skips(text) if not s[3]]


#: 文档级理由的标记词（函数 docstring 里写清「失败怎么办」也算成文理由）
DOC_MARKS = ("失败", "不可读", "缺件", "坏件", "跳过", "等价", "如实", "降级", "退回",
             "AUD-0016", "保守", "容错", "忽略", "不静默")


def _falsy(v) -> bool:
    if v is None:
        return True
    if isinstance(v, ast.Constant):
        return v.value in (None, False, 0, "")
    return isinstance(v, (ast.List, ast.Dict, ast.Tuple, ast.Set)) and not (
        getattr(v, "elts", None) or getattr(v, "keys", None))


def silent_returns(text: str) -> list:
    """→ `except → return <空值>` **且完全不留痕**的站点（纯函数）。

    「不留痕」= handler 体里没有任何字符串（没带错误消息）+ 该 `except`/`try`/其上三行无注释 +
    所属函数 docstring 没交代失败语义。这类站点把异常**整条丢掉**，调用方只能看到一个空值
    ——`library.verify` 的旧写法（读不到条目 = 当作未漂移）就是这么来的。
    """
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError:                    # 同上：交给语法级判据
        return []
    parents = {}
    for n in ast.walk(tree):
        for ch in ast.iter_child_nodes(n):
            parents[ch] = n
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        fn: ast.AST = node
        while fn in parents and not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn = parents[fn]
        doc = ast.get_docstring(fn) or "" if isinstance(
            fn, (ast.FunctionDef, ast.AsyncFunctionDef)) else ""
        for h in node.handlers:
            body = h.body
            if len(body) != 1 or not isinstance(body[0], ast.Return):
                continue
            if not _falsy(body[0].value):
                continue
            if any(isinstance(x, ast.Constant) and isinstance(x.value, str)
                   for x in ast.walk(body[0])):
                continue                   # 带了消息 ⇒ 不是静默
            lo, hi = node.lineno - 1, body[0].lineno - 1
            if any("#" in ln for ln in lines[lo:hi + 1] + lines[max(0, lo - 3):lo]):
                continue                   # 行内理由
            if any(m in doc for m in DOC_MARKS):
                continue                   # 文档级理由
            out.append((node.lineno, h.lineno))
    return out
