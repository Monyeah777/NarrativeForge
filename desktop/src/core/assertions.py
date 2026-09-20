"""断言表 runner（数据化断言，机制借鉴 Schematron 的 patterns→rules→assertions）。

真源 `protocol/assertions.json`：每条断言 = id / severity / kind / params / message / fix。
**kind 是封闭集**（四个），只做确定性形状判定；不引入第三方依赖、不自造 DSL。

边界（写在声明里，这里也钉一遍）：
- 只搬「已在别处被判定过的形状类断言」，不在这里新增语义政策；
- 业务语义断言（需要上下文推理的）留在 check 代码里；
- 每条断言必须有 fix——没有修复指引的断言不许入表。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

DECL_REL = "protocol/assertions.json"
SCHEMA = "nf-assertions/1"
SEVERITIES = ("fail", "warn")
REQUIRED = ("id", "severity", "kind", "params", "message", "fix")


def load(root: str = ".") -> Dict[str, Any]:
    p = Path(root) / DECL_REL
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _glob(root: str, pattern: str) -> List[str]:
    r = Path(root)
    if any(ch in pattern for ch in "*?["):
        return sorted(str(p) for p in r.glob(pattern) if p.is_file())
    p = r / pattern
    return [str(p)] if p.is_file() else []


def _k_regex_absent(root: str, params: Dict[str, Any]) -> Tuple[bool, str]:
    pat = re.compile(str(params.get("pattern") or ""))
    hits = []
    for g in params.get("globs") or []:
        for f in _glob(root, str(g)):
            if pat.search(Path(f).read_text(encoding="utf-8")):
                hits.append(f)
    return (not hits, "零命中" if not hits else "命中：%s" % ", ".join(hits[:2]))


def _k_regex_present(root: str, params: Dict[str, Any]) -> Tuple[bool, str]:
    path = Path(root) / str(params.get("path") or "")
    if not path.is_file():
        return False, "目标件不存在：%s" % params.get("path")
    text = path.read_text(encoding="utf-8")
    miss = [p for p in (params.get("patterns") or []) if p not in text]
    return (not miss, "%d 锚点齐" % len(params.get("patterns") or [])
            if not miss else "缺：%s" % ", ".join(miss[:3]))


def _k_count_at_least(root: str, params: Dict[str, Any]) -> Tuple[bool, str]:
    n = len(_glob(root, str(params.get("glob") or "")))
    want = int(params.get("min") or 0)
    return (n >= want, "%d ≥ %d" % (n, want))


def _k_json_value(root: str, params: Dict[str, Any]) -> Tuple[bool, str]:
    path = Path(root) / str(params.get("path") or "")
    if not path.is_file():
        return False, "目标件不存在：%s" % params.get("path")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return False, "JSON 不可解析：%s" % exc
    cur: Any = doc
    for part in str(params.get("key") or "").split("."):
        if not isinstance(cur, dict) or part not in cur:
            return False, "缺键：%s" % params.get("key")
        cur = cur[part]
    op = str(params.get("op") or "")
    val = params.get("value")
    if op == "exists":
        return True, "键在场"
    if op == "nonempty":
        ok = bool(cur)
        return (ok, "非空" if ok else "空值")
    if op == "equals":
        return (cur == val, "= %s" % val)
    if op == "in_vocab":
        ok = cur in (val or [])
        return (ok, "%s ∈ 词表" % cur if ok else "%s 越词表" % cur)
    if op == "contains_keys":
        miss = [k for k in (val or []) if k not in (cur or {})]
        return (not miss, "键齐" if not miss else "缺：%s" % ", ".join(miss))
    return False, "未知 op：%s（封闭集：exists/nonempty/equals/in_vocab/contains_keys）" % op


KINDS = {"regex_absent": _k_regex_absent, "regex_present": _k_regex_present,
         "count_at_least": _k_count_at_least, "json_value": _k_json_value}


def scan(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """断言表自身的合法性（防"表里塞了跑不动的断言"）。"""
    issues: List[str] = []
    doc = load(root)
    if not doc:
        return ["缺断言表 %s" % DECL_REL], {}
    if str(doc.get("schema") or "") != SCHEMA:
        issues.append("断言表 schema 不匹配（期望 %s）" % SCHEMA)
    if tuple(doc.get("severity_vocabulary") or ()) != SEVERITIES:
        issues.append("severity 词表与判据不一致（期望 %s）" % "/".join(SEVERITIES))
    if tuple(doc.get("kind_vocabulary") or ()) != tuple(KINDS):
        issues.append("kind 词表必须与 runner 封闭集逐项一致（%s）" % "/".join(KINDS))
    seen = set()
    for a in doc.get("assertions") or []:
        aid = str(a.get("id") or "")
        for k in REQUIRED:
            if not a.get(k) and a.get(k) != {}:
                issues.append("断言 %s 缺必填字段：%s" % (aid or "(无名)", k))
        if aid in seen:
            issues.append("断言 id 重复：%s" % aid)
        seen.add(aid)
        if str(a.get("severity")) not in SEVERITIES:
            issues.append("断言 %s severity 越词表：%s" % (aid, a.get("severity")))
        if str(a.get("kind")) not in KINDS:
            issues.append("断言 %s kind 不在封闭集：%s" % (aid, a.get("kind")))
        if not str(a.get("fix") or "").strip():
            issues.append("断言 %s 缺 fix（无修复指引不许入表）" % aid)
    return issues, {"assertions": len(doc.get("assertions") or [])}


def run(root: str = ".") -> Tuple[List[Dict[str, Any]], List[str]]:
    """跑全部断言 → (results, issues)。results 每项含 ok/severity/kind/detail。"""
    decl_issues, _stats = scan(root)
    issues = list(decl_issues)
    results: List[Dict[str, Any]] = []
    for a in load(root).get("assertions") or []:
        kind = str(a.get("kind"))
        fn = KINDS.get(kind)
        if fn is None:
            issues.append("断言 %s 的 kind 不在封闭集：%s" % (a.get("id"), kind))
            continue
        try:
            ok, detail = fn(root, a.get("params") or {})
        except Exception as exc:                      # 断言自身异常 = 该条不通过
            ok, detail = False, "断言执行异常：%s" % exc
        results.append({"id": a.get("id"), "severity": a.get("severity"), "kind": kind,
                        "ok": bool(ok), "detail": detail, "message": a.get("message"),
                        "fix": a.get("fix"), "evidence": a.get("evidence")})
        if not ok and str(a.get("severity")) == "fail":
            issues.append("%s 不通过：%s（修复指引：%s）"
                          % (a.get("id"), detail, a.get("fix")))
    return results, issues
