"""演练保真度**量化**（动态可执行面 · 顶层化：drill 全绿 / 回合级回放 / 保真度量化）。

为什么需要：既有两套演练此前只有「逐例 PASS/FAIL」的文本结论——**没有一个数**。于是
「保真度」无法比较、无法回归、无法作为发布判据（顶层化实测：全仓 `保真` 一词只出现在
`import_adapter` 的「高保真重建」，与演练无关）。

本模块把演练结果压成**保真度数字**并给判据：

- **执行演练保真度**：逐个用例集跑 `execution_drill.run_case`，判「捕获无漏报
  （expect_captured ⊆ hits）+ guard 无误报（无期望命中时不得有命中）」，保真度 = 通过例数 / 总例数。
- **回合级回放保真度**：对 `fixtures/execution/rounds/*.json` 逐个回放，判实测 verdict
  是否复现样本声明（`good → conformant` / `bad → non-conformant`），保真度 = 复现数 / 样本数。
- **判据**：任一例不达标 → FAIL（保真度必须 100%）；**找不到用例/样本 → FAIL**（标准不得无载体）。

纪律：纯标准库；只读（唯 `write()` 落盘度量结果供机器消费）；错误消息带修复指引。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

EXEC_GLOB = "desktop/tests/fixtures/execution/p*_drill_cases.json"
ROUND_GLOB = "desktop/tests/fixtures/execution/rounds/*.json"
REPORT_REL = "protocol/drill_fidelity.json"
SCHEMA = "nf-drill-fidelity/1"
#: 回合级样本的 verdict 词表 → 判据口径（样本侧写 good/bad，drill 侧吐 conformant/non-conformant）
VERDICT_MAP = {"good": "conformant", "conformant": "conformant",
               "bad": "non-conformant", "non-conformant": "non-conformant"}


def _exec_sets(root: Path) -> List[Dict[str, Any]]:
    from core import execution_drill as ed

    out: List[Dict[str, Any]] = []
    for f in sorted(root.glob(EXEC_GLOB)):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as exc:
            out.append({"set": f.name, "cases": 0, "passed": 0, "error": "JSON 不可解析：%s" % exc})
            continue
        real, sem, src = data.get("real_ids") or [], data.get("semantics") or {}, data.get("source_text", "")
        n = ok = 0
        for case in data.get("cases", []):
            hits = ed.run_case(case, real, sem, src)
            expect = set(case.get("expect_captured") or [])
            good = (not expect and not hits) or expect <= set(hits)
            n += 1
            ok += 1 if good else 0
        out.append({"set": f.name, "cases": n, "passed": ok})
    return out


def _round_samples(root: Path) -> List[Dict[str, Any]]:
    from core import round_drill as rd

    out: List[Dict[str, Any]] = []
    for f in sorted(root.glob(ROUND_GLOB)):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as exc:
            out.append({"sample": f.name, "declared": "?", "live": "error", "matched": False,
                        "error": "JSON 不可解析：%s" % exc})
            continue
        issues, stats = rd.scan(str(d.get("transcript") or ""), list(d.get("allowed") or []))
        live = "non-conformant" if issues else "conformant"
        declared = VERDICT_MAP.get(str(d.get("verdict") or "").lower(), str(d.get("verdict")))
        out.append({"sample": f.name, "declared": declared, "live": live,
                    "turns": stats.get("turns"), "matched": declared == live,
                    "first_issue": (issues[0] if issues else "")})
    return out


def measure(root: str = ".") -> Dict[str, Any]:
    """→ 保真度度量（执行演练 + 回合级回放 + 总口径）。"""
    r = Path(root)
    ex = _exec_sets(r)
    rnd = _round_samples(r)
    ex_cases = sum(s["cases"] for s in ex)
    ex_pass = sum(s["passed"] for s in ex)
    rnd_total = len(rnd)
    rnd_pass = sum(1 for s in rnd if s.get("matched"))
    total, passed = ex_cases + rnd_total, ex_pass + rnd_pass
    return {"schema": SCHEMA,
            "execution": {"sets": ex, "cases": ex_cases, "passed": ex_pass,
                          "fidelity": round(ex_pass / ex_cases, 4) if ex_cases else 0.0},
            "rounds": {"samples": rnd, "total": rnd_total, "matched": rnd_pass,
                       "fidelity": round(rnd_pass / rnd_total, 4) if rnd_total else 0.0},
            "overall": {"cases": total, "passed": passed,
                        "fidelity": round(passed / total, 4) if total else 0.0}}


def scan(root: str = ".") -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)：任一例不达标 / 无载体 = FAIL。"""
    m = measure(root)
    issues: List[str] = []
    warns: List[str] = []
    if m["execution"]["cases"] == 0:
        issues.append("找不到执行演练用例（修复指引：%s 下须有 p*_drill_cases.json）" % EXEC_GLOB)
    if m["rounds"]["total"] == 0:
        issues.append("找不到回合级回放样本（修复指引：%s 下须有样本，含 transcript/allowed/verdict）"
                      % ROUND_GLOB)
    for s in m["execution"]["sets"]:
        if s.get("error"):
            issues.append("%s %s" % (s["set"], s["error"]))
        elif s["passed"] != s["cases"]:
            issues.append("执行演练保真度不足：%s %d/%d（修复指引：先修样本集自身或捕获逻辑，"
                          "演练集不达标不得入库）" % (s["set"], s["passed"], s["cases"]))
    for s in m["rounds"]["samples"]:
        if not s.get("matched"):
            issues.append("回合级回放未复现声明：%s 声明=%s 实测=%s（%s）（修复指引：修样本或"
                          "回合断言——回放须可复现声明结论）"
                          % (s["sample"], s.get("declared"), s.get("live"),
                             str(s.get("first_issue"))[:60]))
    stats = m["overall"]
    stats.update({"exec_sets": len(m["execution"]["sets"]), "round_samples": m["rounds"]["total"]})
    return issues, warns, stats


def write(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """把度量结果落盘（供机器消费）→ (issues, doc)。"""
    m = measure(root)
    p = Path(root) / REPORT_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(m, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                 encoding="utf-8", newline="\n")
    issues, _w, _s = scan(root)
    return issues, m
