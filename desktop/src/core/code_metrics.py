"""代码规模与复杂度上限（架构纯度面 · 顶层化目标 GAP-4）。

为什么需要：此前「模块规模上限」**无判据**（顶层化度量实测：命中的只是别处一个 `--limit`
参数）。于是仓库里长成了 `scripts/nf.py` 5416 行、单函数 **951 行**、圈复杂度 **150** 的模块，
而门禁对此完全沉默——可维护性没有闸门。

口径（棘轮式，只增不减的反向）：
- **存量冻结**：`protocol/code_metrics_baseline.json` 记录每个文件在冻结时的
  `lines / max_fn_lines / max_fn_cc`；之后任一项**超过记录值**即 FAIL（可降不可升）。
  冻结动作是显式的 `--write`（评审后重冻），不由扫描器偷偷写。
- **新增限值**：基线里没有的文件按 `LIMITS` 判（新文件不该再造 2000 行的怪物）。
- 度量口径（McCabe 圈复杂度 + 函数长度）：判定分支 `if/for/while/except/with/assert/
  三元/布尔运算` 计 1（布尔每多一个操作数再加 1）——与 SonarSource 认知复杂度、
  McCabe 圈复杂度的通行定义同向，但只取**结构可静态判定**的那部分（不做嵌套加权，
  以免出现「阈值靠感觉调」的口径）。

纪律：纯标准库；只读扫描（唯 `write()` 落盘）；错误消息带修复指引。
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

BASELINE_REL = "protocol/code_metrics_baseline.json"
SCHEMA = "nf-code-metrics/1"

#: 新增文件的绝对上限（存量按基线冻结，不受此限）
LIMITS = {"lines": 800, "max_fn_lines": 120, "max_fn_cc": 25}
#: 扫描面：core 与 scripts 的 .py（与 purity R5/R6 同口径）
SCAN_DIRS = ("desktop/src/core", "scripts")


def _fn_cc(fn: ast.AST) -> int:
    """函数体圈复杂度：1 + 判定点计数（McCabe 口径）。"""
    cc = 1
    for node in ast.walk(fn):
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler,
                             ast.With, ast.AsyncWith, ast.IfExp, ast.Assert)):
            cc += 1
        elif isinstance(node, ast.BoolOp):
            cc += max(0, len(node.values) - 1)
    return cc


def metrics_of(path: str) -> Dict[str, Any]:
    """单文件度量 → {lines, max_fn_lines, max_fn_cc, worst_fn}；语法坏 → 记 syntax_error。"""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    out: Dict[str, Any] = {"lines": len(text.splitlines()), "max_fn_lines": 0,
                           "max_fn_cc": 0, "worst_fn": ""}
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        out["syntax_error"] = "%s（修复指引：先修语法，度量需要可解析的 AST）" % exc
        return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            ln = int(end) - int(node.lineno) + 1
            if ln > out["max_fn_lines"]:
                out["max_fn_lines"] = ln
            cc = _fn_cc(node)
            if cc > out["max_fn_cc"]:
                out["max_fn_cc"] = cc
                out["worst_fn"] = "%s（%d 行 / cc=%d）" % (node.name, ln, cc)
    return out


def measure(root: str = ".") -> Dict[str, Dict[str, Any]]:
    """全量度量 → {仓库相对路径: 度量}（键排序，便于逐字节比对）。"""
    r = Path(root)
    out: Dict[str, Dict[str, Any]] = {}
    for d in SCAN_DIRS:
        for p in sorted((r / d).glob("*.py")):
            rel = p.relative_to(r).as_posix()
            out[rel] = metrics_of(str(p))
    return out


def load_baseline(root: str = ".") -> Dict[str, Any]:
    p = Path(root) / BASELINE_REL
    if not p.is_file():
        return {}
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    return (doc.get("files") or {}) if isinstance(doc, dict) else {}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)：超冻结值 / 新文件超限 = FAIL；语法坏 = FAIL。"""
    cur = measure(root)
    base = load_baseline(root)
    issues: List[str] = []
    warns: List[str] = []
    for rel, m in sorted(cur.items()):
        if m.get("syntax_error"):
            issues.append("%s %s" % (rel, m["syntax_error"]))
            continue
        if rel in base:
            for key, label in (("lines", "模块行数"), ("max_fn_lines", "最长函数行数"),
                               ("max_fn_cc", "最大圈复杂度")):
                cap = int((base[rel] or {}).get(key, 0) or 0)
                if cap and int(m[key]) > cap:
                    issues.append("%s %s %d > 冻结值 %d（修复指引：拆分该模块/函数；确需上调须"
                                  "评审后重冻基线 python scripts/code_metrics.py --write）"
                                  % (rel, label, int(m[key]), cap))
        else:
            for key, label in (("lines", "模块行数"), ("max_fn_lines", "最长函数行数"),
                               ("max_fn_cc", "最大圈复杂度")):
                if int(m[key]) > LIMITS[key]:
                    issues.append("%s 新文件 %s %d > 限值 %d（修复指引：拆分后再入库；"
                                  "确需放宽须评审后冻结基线）"
                                  % (rel, label, int(m[key]), LIMITS[key]))
    stats = {"files": len(cur), "baseline": len(base),
             "max_lines": max((m["lines"] for m in cur.values()), default=0),
             "max_fn_lines": max((m["max_fn_lines"] for m in cur.values()), default=0),
             "max_fn_cc": max((m["max_fn_cc"] for m in cur.values()), default=0)}
    if not base:
        warns.append("无基线 %s（当前按新文件限值判；修复指引："
                     "python scripts/code_metrics.py --write 冻结存量）" % BASELINE_REL)
    return issues, warns, stats


def write(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """冻结当前度量为基线（显式动作）→ (issues, doc)。"""
    cur = measure(root)
    doc = {"schema": SCHEMA,
           "note": "存量冻结的规模/复杂度上限（棘轮：只可下降；上调须评审后重冻）",
           "limits": dict(LIMITS),
           "files": {rel: {k: m[k] for k in ("lines", "max_fn_lines", "max_fn_cc")}
                     for rel, m in sorted(cur.items()) if not m.get("syntax_error")}}
    out = Path(root) / BASELINE_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    issues = [rel for rel, m in cur.items() if m.get("syntax_error")]
    return issues, doc
