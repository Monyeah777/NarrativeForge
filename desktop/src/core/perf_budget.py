"""性能预算（ISO 25010 性能效率面 · 顶层化「更多维度」）。

为什么需要：并发会话持续做性能优化（`nf score 6816→176 ms`、磁盘缓存、逐包键复用…），
但**优化收益没有任何判据守着**——下次谁改回去都没人知道。本模块把「性能」变成可核验面：

- **声明面**（真源）= `protocol/perf_budget.json` 的 `entries`（id / cmd / budget_ms /
  runs / max_age_days / note），预算按**本机实测中位 ×2.5~3** 定，只拦数量级回归；
- **证据面** = 同件 `evidence`（`--record` 真跑 N 次写入：中位/最小/最大毫秒 + 退出码 + 时间）；
- **判据**：① 每条声明须有记录（缺 = FAIL）；② 记录须在 `max_age_days` 内（过期 = FAIL）；
  ③ **中位耗时 ≤ 预算**（超标 = FAIL）；④ 记录键须都是已声明项（凭空记录 = FAIL）。

**刻意不判的正确性**：本判据**不看退出码**——正确性由 `verify_report` 的其余判据承担；
在这里重复判会让性能面因无关原因抖动（实测：棘轮/报告在并发改写期会是红的，但耗时仍可测）。

纪律：纯标准库；本模块不自己执行命令（执行在 `scripts/perf_budget.py --record` 里显式发生）。
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

DECL_REL = "protocol/perf_budget.json"
SCHEMA = "nf-perf-budget/1"


def load(root: str = ".") -> Tuple[Dict[str, Any], List[str]]:
    p = Path(root) / DECL_REL
    if not p.is_file():
        return {}, ["缺性能预算声明件 %s（修复指引：声明目标命令与预算毫秒，再跑 "
                    "python scripts/perf_budget.py --record）" % DECL_REL]
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        return {}, ["%s 不是合法 JSON：%s（修复指引：修好 JSON 语法）" % (DECL_REL, exc)]
    issues: List[str] = []
    if doc.get("schema") != SCHEMA:
        issues.append("%s schema 不匹配（期望 %s）" % (DECL_REL, SCHEMA))
    if not isinstance(doc.get("entries"), list) or not doc["entries"]:
        issues.append("%s 缺 entries 声明（修复指引：至少声明一条性能目标）" % DECL_REL)
    return doc, issues


def _age_days(stamp: str, today: _dt.date) -> int:
    try:
        return (today - _dt.date.fromisoformat(str(stamp)[:10])).days
    except ValueError:
        return 10 ** 6


def scan(root: str = ".", today: _dt.date | None = None
         ) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """→ (issues, warns, stats)：缺记录 / 过期 / 超预算 / 凭空记录 = FAIL。"""
    doc, issues = load(root)
    warns: List[str] = []
    if not doc or issues:
        return issues, warns, {"declared": 0, "recorded": 0, "over_budget": 0}
    today = today or _dt.date.today()  # noqa: DTZ011 - 本地日历日期是有意语义（UTC 会在跨零点给出错误「今天」）
    entries = doc.get("entries") or []
    ev = doc.get("evidence") or {}
    over = 0
    for e in entries:
        eid = str((e or {}).get("id") or "")
        if not eid:
            issues.append("%s 有声明项缺 id（修复指引：补齐 id/cmd/budget_ms）" % DECL_REL)
            continue
        rec = ev.get(eid)
        if not isinstance(rec, dict):
            issues.append("性能目标 %s（%s）无实测记录（修复指引：python scripts/"
                          "perf_budget.py --record）" % (eid, e.get("cmd")))
            continue
        budget = float(e.get("budget_ms") or 0)
        med = float(rec.get("median_ms") or 0)
        if budget and med > budget:
            over += 1
            issues.append("性能超预算 %s：中位 %.0f ms > 预算 %.0f ms（超出 %.0f%%）"
                          "（修复指引：先定位退化点，再 --record 重测；确因预算定得过紧须评审后改预算）"
                          % (eid, med, budget, (med - budget) / budget * 100))
        age = _age_days(str(rec.get("measured_at") or ""), today)
        max_age = int(e.get("max_age_days", 30) or 30)
        if age > max_age:
            issues.append("性能记录过期 %s：%d 天 > 上限 %d 天（修复指引：python scripts/"
                          "perf_budget.py --record --only %s）" % (eid, age, max_age, eid))
    known = {str((e or {}).get("id") or "") for e in entries}
    for eid in sorted(set(ev) - known):
        issues.append("记录 %s 无对应声明（修复指引：在 %s 声明它，或删掉记录）" % (eid, DECL_REL))
    stats = {"declared": len(known), "recorded": len(set(ev) & known), "over_budget": over}
    return issues, warns, stats


def record(root: str = ".", only: str = "", runner=None, today: _dt.date | None = None
           ) -> Tuple[List[str], Dict[str, Any]]:
    """真跑声明命令 N 次并写回证据 → (bad_ids, doc)。

    `runner(cmd) -> (exit_code, ms_list)` 由调用方注入，便于单测注入假计时器。
    """
    doc, issues = load(root)
    if not doc or issues:
        return issues, doc
    today = today or _dt.date.today()  # noqa: DTZ011 - 本地日历日期是有意语义（UTC 会在跨零点给出错误「今天」）
    ev = doc.setdefault("evidence", {})
    bad: List[str] = []
    for e in doc.get("entries") or []:
        eid = str((e or {}).get("id") or "")
        if not eid:
            continue
        if only and only not in ("all", eid):
            continue
        code, times = runner(str(e.get("cmd") or ""), int(e.get("runs", 3) or 3))
        times = sorted(float(t) for t in times) or [0.0]
        mid = times[len(times) // 2]
        ev[eid] = {"cmd": e.get("cmd"), "exit_code": int(code), "measured_at": today.isoformat(),
                   "median_ms": round(mid, 1), "min_ms": round(times[0], 1),
                   "max_ms": round(times[-1], 1), "runs": len(times),
                   "budget_ms": e.get("budget_ms")}
        if float(e.get("budget_ms") or 0) and mid > float(e.get("budget_ms") or 0):
            bad.append(eid)
    p = Path(root) / DECL_REL
    from core import atomic_write              # 在仓协议件：原子落盘（2026-10-01）
    atomic_write.write_text(p, json.dumps(doc, ensure_ascii=False, indent=2,
                                          sort_keys=True) + "\n")
    return bad, doc
