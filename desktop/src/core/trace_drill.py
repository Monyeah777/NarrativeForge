"""45 #3 · trace → drill 自动比对器（遥测消费方）。

把 nf assemble --check --trace 落盘的 trace（含 source/requirement/ok）喂回 drill：
- 用 requirement 重建装配允许集；
- 对 source 转录重跑 round_drill；
- 断言「重跑判定 == trace.ok」——不一致 = 遥测与实现漂移（FAIL）。

判定口径分档（2026-09-30 统一）：`ok` 是**命令总判定**，只有加了 `--rounds` 才含回合级；
新写的 trace 逐字带 `rounds:{checked,ok}`。有该键时按它核（`checked=False` ⇒ 返回
`verdict_scope="none"`，即**不适用**，不做漂移断言）；老 trace（无该键）沿用总判定。
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
    # 判定口径分档（2026-09-30）：`nf assemble --check --trace` 的总判定 `ok` 只在加了
    # `--rounds` 时才含回合级；新写法的 trace 逐字带 `rounds:{checked,ok}`。有它就用它
    # （checked=False ⇒ **不适用**，不做漂移断言，详见返回的 verdict_scope），
    # 老 trace（无该键）沿用总判定，保持向后兼容。
    scope = trace.get("rounds") if isinstance(trace.get("rounds"), dict) else None
    if scope is not None and scope.get("checked") is False:
        return (["trace 未含回合级判定（写时未加 --rounds）⇒ 不做漂移断言"],
                {"transcript_turns": r_stats["turns"], "expected_ok": None,
                 "actual_ok": not r_issues, "verdict_scope": "none"})
    if scope is not None and scope.get("checked") and scope.get("ok") is not None:
        expected_ok = bool(scope["ok"])
        verdict_scope = "rounds"
    else:
        expected_ok = bool(trace.get("ok"))
        verdict_scope = "overall"
    actual_ok = not r_issues
    if actual_ok != expected_ok:
        issues.append("verdict 漂移：trace 记录 %s（口径=%s）· 重跑判定 %s（issue=%s）"
                      % (expected_ok, verdict_scope, actual_ok, r_issues[:3]))
    return issues, {"transcript_turns": r_stats["turns"],
                    "expected_ok": expected_ok, "actual_ok": actual_ok,
                    "verdict_scope": verdict_scope}
