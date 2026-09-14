"""执行结果跑分台（机制借鉴 ACP `agent/benchmarks/suite`）。

NF 原有 drill 只判「本轮有没有失范」，**没有"同一任务在不同模型/多次运行下的可比跑分"**——
于是外部实测（E1/E2/Y5）即使回填，也没有容器装结论。本模块补这个容器：

- **用例**：`desktop/tests/fixtures/benchmark/suite/<case>/case.json`（需求 + 期望下限 + 默认产物）；
- **跑分**：对任意 agent 产物做**五维确定性评分**，**复用 NF 自己的验收件**，不另造判据：
  - `structure`：八段骨架完整度（`assemble_plan.check`）；
  - `traceability`：编号真值 / 无编造（同上，取"编造类"问题折算）；
  - `closure`：事件闭合自陈（触发/结算计数 + 闭合声明）；
  - `prose`：正文 AI 味（`prose_lint`）；
  - `selfcheck`：自检清单段完整度（≥7 项带 ✅/❌）。
- **产出**：`nf-bench-run/1` 记录（含产物摘要，可比对、可复现）；`compare` 出逐维均值/极差/排名。

纪律：只跑**离线确定性**判据，不调模型；分数是"相对可比量"，不是质量宣称。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

SUITE_REL = "desktop/tests/fixtures/benchmark/suite"
SCHEMA = "nf-bench-run/1"
WEIGHTS = {"structure": 0.30, "traceability": 0.30, "closure": 0.20,
           "prose": 0.10, "selfcheck": 0.10}

_SEG = re.compile(r"^##\s*([0-7])\s*[.、]", re.M)
_TRIGGER = re.compile(r"触发")
_SETTLE = re.compile(r"结算")
_CLOSE = re.compile(r"事件闭合|闭合声明|每个触发必有")
_SELF_CHECK = re.compile(r"^#{2,3}\s*7\s*[.、].*自检", re.M)
#: 自检作答记号：既有 emoji/勾叉，也有 NF 样本常用的 GitHub 复选框（`- [x]` / `- [ ]`）
_MARK = re.compile(r"[✅❌✓✗]|-\s*\[[xX ]\]")


def cases(root: str = ".") -> List[Path]:
    d = Path(root) / SUITE_REL
    return sorted(p for p in d.glob("*/case.json")) if d.is_dir() else []


def load_case(path: Path) -> Dict[str, Any]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    doc["_dir"] = str(Path(path).parent)
    return doc


def _structure_and_trace(artifact: str, requirement: str) -> Tuple[float, float, float, List[str]]:
    from core import assemble_plan as ap

    plan_ = ap.plan(requirement)
    issues, stats = ap.check(artifact, plan_)
    segs = {int(m.group(1)) for m in _SEG.finditer(artifact)}
    structure = len(segs & set(range(8))) / 8.0
    fab = [i for i in issues if "编造" in i or "越界" in i or "不在允许集" in i]
    trace = max(0.0, 1.0 - 0.25 * len(fab))
    return structure, trace, float(stats.get("segments", len(segs))), issues


def _closure(artifact: str) -> float:
    trig, settle = len(_TRIGGER.findall(artifact)), len(_SETTLE.findall(artifact))
    has_close = 1.0 if _CLOSE.search(artifact) else 0.0
    if trig == 0:
        return 0.5 * has_close                      # 无触发声明的样本：只按闭合自陈给分
    ratio = min(1.0, settle / max(1, trig))
    return round(min(1.0, 0.6 * ratio + 0.4 * has_close), 4)


def _prose(artifact: str) -> Tuple[float, int]:
    from core import prose_lint as pl

    found = pl.lint_text(artifact)
    return max(0.0, 1.0 - min(1.0, len(found) / 10.0)), len(found)


def _selfcheck(artifact: str) -> float:
    if not _SELF_CHECK.search(artifact):
        return 0.0
    tail = artifact[_SELF_CHECK.search(artifact).start():]
    marks = len(_MARK.findall(tail))
    return round(min(1.0, marks / 7.0), 4)


def evaluate(root: str, case_path: str, artifact_path: str,
             model: str = "", run_id: str = "") -> Dict[str, Any]:
    """对一件产物跑分 → run 记录（确定性：同输入同分）。"""
    case = load_case(Path(root, case_path) if not Path(case_path).is_absolute()
                     else Path(case_path))
    apath = Path(root, artifact_path) if not Path(artifact_path).is_absolute() \
        else Path(artifact_path)
    text = apath.read_text(encoding="utf-8")
    digest = hashlib.sha256(apath.read_bytes()).hexdigest()
    structure, trace, segs, issues = _structure_and_trace(text, case.get("requirement", ""))
    closure = _closure(text)
    prose, prose_n = _prose(text)
    selfcheck = _selfcheck(text)
    scores = {"structure": round(structure, 4), "traceability": round(trace, 4),
              "closure": closure, "prose": round(prose, 4), "selfcheck": selfcheck}
    total = round(100 * sum(WEIGHTS[k] * v for k, v in scores.items()), 2)
    floor = float((case.get("expected") or {}).get("min_total", 60))
    min_seg = int((case.get("expected") or {}).get("min_segments", 0) or 0)
    meets_seg = (segs >= min_seg) if min_seg else True
    verdict = "pass" if total >= floor else ("warn" if total >= floor - 15 else "fail")
    if not meets_seg:                                 # 声明的下限也是判据，不是装饰
        verdict = "fail"
    return {"schema": SCHEMA, "case": case.get("case", Path(case_path).parent.name),
            "run_id": run_id or digest[:12], "model": model,
            "artifact": str(artifact_path).replace("\\", "/"),
            "artifact_digest": digest, "scores": scores, "total": total,
            "floor": floor, "min_segments": min_seg, "meets_min_segments": meets_seg,
            "verdict": verdict,
            "detail": {"segments": int(segs), "prose_findings": prose_n,
                       "issues": issues[:8]}}


def compare(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """多跑比对：逐维均值/极差/最佳，并标出相对最佳的回落项。"""
    if not runs:
        return {"schema": "nf-bench-compare/1", "runs": 0, "dims": {}, "ranking": []}
    dims: Dict[str, Dict[str, float]] = {}
    for k in WEIGHTS:
        vals = [float((r.get("scores") or {}).get(k, 0.0)) for r in runs]
        dims[k] = {"mean": round(sum(vals) / len(vals), 4),
                   "min": round(min(vals), 4), "max": round(max(vals), 4),
                   "spread": round(max(vals) - min(vals), 4)}
    ranking = sorted(runs, key=lambda r: -float(r.get("total", 0.0)))
    best = ranking[0]
    regressions = []
    for r in ranking[1:]:
        for k in WEIGHTS:
            b = float((best.get("scores") or {}).get(k, 0))
            c = float((r.get("scores") or {}).get(k, 0))
            if c < b:
                regressions.append({"run": r.get("run_id"), "dim": k,
                                    "from": round(b, 4), "to": round(c, 4)})
    return {"schema": "nf-bench-compare/1", "runs": len(runs), "dims": dims,
            "ranking": [{"run": r.get("run_id"), "model": r.get("model"),
                         "total": r.get("total"), "verdict": r.get("verdict")}
                        for r in ranking],
            "best": best.get("run_id"),
            "regressions_vs_best": regressions[:20]}


def report_markdown(compare_doc: Dict[str, Any]) -> str:
    """人读报告（跑分表 + 逐维极差）。"""
    out = ["# NF 执行结果跑分报告", "",
           "| 跑次 | 模型 | 总分 | 判定 |", "|---|---|---|---|"]
    for r in compare_doc.get("ranking") or []:
        out.append("| %s | %s | %s | %s |" % (r.get("run"), r.get("model") or "-",
                                              r.get("total"), r.get("verdict")))
    out += ["", "| 维度 | 均值 | 最低 | 最高 | 极差 |", "|---|---|---|---|---|"]
    for k, v in sorted((compare_doc.get("dims") or {}).items()):
        out.append("| %s | %s | %s | %s | %s |" % (k, v["mean"], v["min"],
                                                   v["max"], v["spread"]))
    out += ["", "> 分数是**相对可比量**（同一用例内多跑对比），不是质量宣称；"
            "判定阈值取用例 `expected.min_total`。"]
    return "\n".join(out) + "\n"
