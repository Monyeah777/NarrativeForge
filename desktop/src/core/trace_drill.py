"""45 #3 · trace → drill 自动比对器（遥测消费方）。

把 nf assemble --check --trace 落盘的 trace（含 source/requirement/ok）喂回 drill：
- 用 requirement 重建装配允许集；
- 对 source 转录重跑 round_drill；
- 断言「重跑判定 == trace.ok」——不一致 = 遥测与实现漂移（FAIL）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parents[3]


def analyze(trace_path: str, root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    r = Path(root)
    issues: List[str] = []
    trace = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    source = trace.get("source")
    requirement = trace.get("requirement") or ""
    if not source:
        return ["trace 缺 source（须由 nf assemble --check --trace 生成）"], {}
    transcript = Path(source) if Path(source).is_absolute() else r / source
    if not transcript.is_file():
        return ["trace.source 文件不存在：%s" % source], {}

    from core import assemble_plan as ap
    from core import round_drill as rd

    plan_ = ap.plan(requirement)
    allowed = plan_.get("allowed_module_ids") or []
    r_issues, r_stats = rd.scan(transcript.read_text(encoding="utf-8"), allowed)
    expected_ok = bool(trace.get("ok"))
    actual_ok = not r_issues
    if actual_ok != expected_ok:
        issues.append("verdict 漂移：trace.ok=%s 重跑判定=%s（issue=%s）"
                      % (expected_ok, actual_ok, r_issues[:3]))
    return issues, {"transcript_turns": r_stats["turns"],
                    "expected_ok": expected_ok, "actual_ok": actual_ok}
