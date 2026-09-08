"""42 M1：协议可执行性内部自测 —— 执行失范捕获器（动态质量维基建）。

把已观察的 AI 执行失范类别固化为可机检断言（内部演练替代外部实测，
同构于「agent 读协议执行」且可复现）：

R1 fabricated_id        编造编号：输出出现装配真实编号集外的模块号。
R2 browse_repeat        浏览-复述：输出与源文本重合度高且无推进信号。
R3 no_citation          无引用凭印象：决策性断言却无 §/编号/行号/章节引用。
R4 semantic_misalignment 编号真实语义错位：提及模块但语句用词属其它模块职责。

断言分级 = 42 M1 规范「硬断言（FAIL）」，样本诚实标注来源（fixtures source_note），
变异自检 = guard 样本（不应误捕获）由 test_execution_drill 覆盖。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

_MODULE_TOKEN = re.compile(r"(?:[\u4e00-\u9fff]+:)?M\d{2,3}")
_DECISION = re.compile(r"(应|应该|必须|禁止|不得|下一步|输出|结论)")
_CITATION = re.compile(r"(§\s*\d+(?:[.-]\d+)*|第\s*\d+\s*(?:节|步|章)|L\d+|行号|"
                       r"[0-9A-Za-z_]+:[MTP]\d{2,3}|/\d+|\b\d{1,3}\b\s*行)")
_PROGRESS = ("回合推进", "进入回合", "已进入第", "时间推进", "推进至", "进入下一回合")
_SPLIT = re.compile(r"[。！？；\n]+")

#: 硬断言 ↔ 判级器（06 §11 / round_header.LAWS）映射（带状态头执行口径）
RULE_LAW = {
    "no_citation": "L1",            # 引用后执行（必须）
    "fabricated_id": "L2",          # 禁止编造编号
    "browse_repeat": "L3",          # 禁止浏览-复述
    "semantic_misalignment": "L4",  # 职责自洽（必须）
}


def _bigrams(text: str) -> set:
    flat = re.sub(r"\s+", "", text)
    return {flat[i:i + 2] for i in range(len(flat) - 1)} or {flat}


def _mention_tokens(output: str) -> List[str]:
    return _MODULE_TOKEN.findall(output)


def _clauses(output: str) -> List[str]:
    return [c.strip() for c in _SPLIT.split(output) if c.strip()]


def _check_fabricated_id(output: str, real_ids: List[str]) -> str:
    for tok in _mention_tokens(output):
        if tok not in real_ids:
            return "fabricated_id"
    return ""


def _check_browse_repeat(output: str, source_text: str) -> str:
    if not source_text or len(output) < 8:
        return ""
    src = _bigrams(source_text)
    overlap = len(_bigrams(output) & src) / max(1, len(src))
    if overlap >= 0.55 and not any(p in output for p in _PROGRESS):
        return "browse_repeat"
    return ""


def _check_no_citation(output: str) -> str:
    if _DECISION.search(output) and not _CITATION.search(output):
        # 仅当整句既无引用也无真实模块编号时判失范
        if not _mention_tokens(output):
            return "no_citation"
    return ""


def _check_semantic_misalignment(output: str, semantics: Dict[str, list]) -> str:
    if not semantics:
        return ""
    for clause in _clauses(output):
        for tok in _mention_tokens(clause):
            own = semantics.get(tok) or []
            if not own:
                continue
            others = [w for m, ws in semantics.items() if m != tok for w in ws]
            has_own = any(w in clause for w in own)
            has_other = any(w in clause for w in others)
            if has_other and not has_own:
                return "semantic_misalignment"
    return ""


def run_case(case: Dict, real_ids: List[str],
             semantics: Dict[str, list] = None,
             source_text: str = "") -> List[str]:
    """对单样本输出跑全部硬断言 → 返回命中的失范规则名列表。"""
    output = case.get("output") or ""
    hits = []
    hit = _check_fabricated_id(output, real_ids)
    if hit:
        hits.append(hit)
    hit = _check_browse_repeat(output, source_text or case.get("source_text", ""))
    if hit:
        hits.append(hit)
    hit = _check_no_citation(output)
    if hit:
        hits.append(hit)
    hit = _check_semantic_misalignment(output, semantics or {})
    if hit:
        hits.append(hit)
    return hits


def run_file(path: str) -> Dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    real_ids = list(data.get("real_ids") or [])
    semantics = data.get("semantics") or {}
    source_text = data.get("source_text", "")
    results = []
    for case in data.get("cases", []):
        hits = run_case(case, real_ids, semantics, source_text)
        expected = set(case.get("expect_captured") or [])
        results.append({
            "id": case.get("id"),
            "hits": sorted(set(hits)),
            "expected": sorted(expected),
            "guard": bool(case.get("guard")),
            "ok": (not expected and not hits) or expected <= set(hits),
        })
    return {"total": len(results), "results": results}


def main(argv: List[str] = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        print("用法: python -m core.execution_drill <cases.json>", file=sys.stderr)
        return 2
    data = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    real_ids = data.get("real_ids") or []
    semantics = data.get("semantics") or {}
    source_text = data.get("source_text", "")
    bad = 0
    print("== execution_drill（%s · %s）==" % (data.get("schema"), data.get("pipeline")))
    for case in data.get("cases", []):
        hits = run_case(case, real_ids, semantics, source_text)
        expected = set(case.get("expect_captured") or [])
        ok = (not expected and not hits) or expected <= set(hits)
        bad += 0 if ok else 1
        print("  [%s] %-28s 命中=%s 期望=%s" %
              ("PASS" if ok else "FAIL", case.get("id"),
               sorted(set(hits)), sorted(expected)))
    if bad:
        print(">>> 演练捕获不达标（%d 例失败），样本集自身需修" % bad)
        return 1
    print(">>> 演练集全过（%d 例）：捕获无漏报、guard 无误报" % len(data.get("cases", [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
