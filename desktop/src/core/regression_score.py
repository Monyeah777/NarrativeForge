"""基线相对回归评分（内部差距实证：NF 现有门禁全是**绝对门**——PASS/FAIL 二值，
quality_baseline 只校验「声明自洽」，仓库全域无 score/delta/回归判据）。

绝对门能回答「有没有坏」，回答不了「比上次差了多少」。本模块补这一面：

- **信号面**：复用既有扫描器（schema/纯度/卫生/一致性/资产/纵深）算可复现分值；
- **基线面**：与存盘基线逐信号比对，给出 delta 与回归清单；
- **门禁面**：整体 delta 越过容差、或任一非豁免信号回落 → 判不可接受（no silent worsening）；
- **例外面**：可审计例外（信号 + 理由 + 记录人），例外不隐藏回归，只标注放行理由。

纪律：纯标准库；复用既有扫描器不重造判据；分值只作**回归相对量**，不作为质量宣称
（「分数不降」≠「质量达标」——门禁绿是底线，不是顶尖）。
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

SCHEMA = "nf-score/1"

#: 基线文件默认位（机读面，与 protocol/ 其余机读件同域）
DEFAULT_BASELINE = "protocol/score_baseline.json"

#: 信号表：(名, 权重, 说明)。权重和 = 1.0
SIGNAL_SPECS: Tuple[Tuple[str, float, str], ...] = (
    ("schema_clean", 0.20, "IDL schema 零漂移（schema_lint）"),
    ("conformance_clean", 0.20, "机读契约/一致性分级零虚标（conformance_scan）"),
    ("purity_clean", 0.15, "架构纯度零违规（purity_scan）"),
    ("doc_hygiene", 0.15, "文档卫生零缺口（doc_hygiene）"),
    ("depth_clean", 0.15, "质量纵深零缺口（quality_depth_scan）"),
    ("asset_density", 0.15, "资产键密度归一（asset_density）"),
)

#: 资产密度归一分母（键/档）：项目实测基线均值 = 3.0
DENSITY_TARGET = 3.0


def _penalty(issue_count: int, step: float = 0.1) -> float:
    """问题数 → 0..1 得分：0 问题满分，逐条扣 step，扣到 0 为止。"""
    return max(0.0, 1.0 - issue_count * step)


def _count(root: str, module: str, fn: str) -> Optional[int]:
    """调用 core.<module>.<fn>(root) → issues 数；**扫描器不可用 → None**（哨兵，不是 0）。

    逐行审查修正（2026-09-20）：此前异常一律 `return 0`，等于把**坏掉的扫描器判成
    "零问题"**（信号满分 → 总分不变 → 回归门看不见 = 假绿）。改为返回哨兵，由调用方
    按 0 分计并写进 issues（fail-closed：不可用 ≠ 干净）。
    """
    try:
        mod = __import__("core.%s" % module, fromlist=[fn])
        issues = getattr(mod, fn)(root)
    except Exception:
        return None
    if isinstance(issues, tuple):
        issues = issues[0]
    return len(issues or [])


def evaluate(root: str = ".") -> Dict[str, Any]:
    """算当前分值：{schema, score, signals[], issues[]}（可复现，纯读）。"""
    issues: List[str] = []
    values: Dict[str, float] = {}

    def scan_signal(module: str, fn: str, step: float = 0.1) -> float:
        """扫描器 → 0..1 分值；**扫描器不可用 = 0 分 + issues**（不得当零问题）。"""
        n = _count(root, module, fn)
        if n is None:
            issues.append("扫描器不可用：core.%s.%s（评分按 0 分计，修复后重跑——"
                          "不可用不等于零问题）" % (module, fn))
            return 0.0
        return _penalty(n, step=step)

    values["schema_clean"] = scan_signal("schema_lint", "scan")
    values["conformance_clean"] = scan_signal("conformance_scan", "scan")
    values["purity_clean"] = scan_signal("purity_scan", "scan")
    _mk = _markers(root)
    if _mk is None:
        issues.append("扫描器不可用：core.doc_hygiene.check_markers（评分按 0 分计）")
        values["doc_hygiene"] = 0.0
    else:
        values["doc_hygiene"] = _penalty(len(_mk), step=0.2)
    values["depth_clean"] = scan_signal("quality_depth_scan", "scan")

    keys, files = 0, 0
    try:
        from core import asset_density
        _di, stats = asset_density.scan(root)
        keys = int(stats.get("keys") or 0)
        files = int(stats.get("files") or 0)
    except Exception as exc:
        issues.append("资产档扫描不可用：%s（评分按 0 分计）" % exc)
    density = (keys / files) if files else 0.0
    values["asset_density"] = max(0.0, min(1.0, density / DENSITY_TARGET))
    if not files:
        issues.append("资产档扫描为空（asset_density 未取到文件数）")

    signals = []
    total = 0.0
    for name, weight, desc in SIGNAL_SPECS:
        v = round(float(values.get(name, 0.0)), 4)
        total += weight * v
        signals.append({"name": name, "weight": weight, "value": v,
                        "note": desc})
    return {
        "schema": SCHEMA,
        "score": round(total * 100.0, 2),
        "signals": signals,
        "metrics": {"asset_keys": keys, "asset_files": files},
        "issues": issues,
    }


def _markers(root: str) -> Optional[list]:
    """doc_hygiene 检查项；**不可用 → None**（与 _count 同语义：不静默当干净）。"""
    try:
        from core import doc_hygiene
        return doc_hygiene.check_markers(root)
    except Exception:
        return None


def compare(current: Dict[str, Any], baseline: Dict[str, Any],
            tolerance: float = 0.0,
            exceptions: Optional[List[Dict[str, str]]] = None,
            eps: float = 1e-9) -> Dict[str, Any]:
    """当前 vs 基线 → {ok, delta, verdict, regressed[], exempted[]}。

    判定：整体 delta < -tolerance → 失败；任一**非豁免**信号回落 → 失败
    （no silent worsening：分数不降掩盖不了单信号恶化）。
    """
    exc = {e.get("signal"): e for e in (exceptions or []) if e.get("signal")}
    base_sig = {s["name"]: float(s.get("value") or 0.0)
                for s in (baseline.get("signals") or [])}
    cur_sig = {s["name"]: float(s.get("value") or 0.0)
               for s in (current.get("signals") or [])}
    regressed, exempted = [], []
    for name in sorted(set(base_sig) & set(cur_sig)):
        b, c = base_sig[name], cur_sig[name]
        if c < b - eps:
            item = {"signal": name, "from": round(b, 4), "to": round(c, 4),
                    "drop": round(b - c, 4)}
            if name in exc:
                item["reason"] = exc[name].get("reason", "")
                exempted.append(item)
            else:
                regressed.append(item)
    base_score = float(baseline.get("score") or 0.0)
    cur_score = float(current.get("score") or 0.0)
    delta = round(cur_score - base_score, 2)
    # 审计例外同时释放整体门预算：被豁免的回落按 权重×跌幅 折算成额度，
    # 避免「已批准的单信号回归」被整体分二次判死（额度不外溢到未豁免信号）。
    weights = {s["name"]: float(s.get("weight") or 0.0)
               for s in (current.get("signals") or [])}
    exempt_budget = sum(weights.get(e["signal"], 0.0) * e["drop"] * 100.0
                        for e in exempted)
    ok = (delta >= -(abs(tolerance) + exempt_budget)) and not regressed
    if not baseline.get("signals"):
        verdict = "无基线（只报当前分值，未做回归判定）"
    elif not ok and regressed:
        verdict = "回归（信号回落）：%s" % "、".join(r["signal"] for r in regressed)
    elif not ok:
        verdict = "回归（整体分下降 %.2f > 容差 %.2f）" % (-delta, abs(tolerance))
    elif exempted:
        verdict = "通过（含 %d 项审计例外）" % len(exempted)
    else:
        verdict = "通过（无回归）"
    return {"ok": ok, "delta": delta, "baseline_score": base_score,
            "current_score": cur_score, "regressed": regressed,
            "exempted": exempted, "verdict": verdict}


def load_baseline(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_baseline(path: str, evaluation: Dict[str, Any],
                  recorded_at: str = "", note: str = "") -> None:
    """写基线（只保留可比字段；recorded_at/note 为审计注记）。"""
    payload = {
        "schema": SCHEMA,
        "score": evaluation.get("score"),
        "signals": evaluation.get("signals"),
        "metrics": evaluation.get("metrics"),
        "recorded_at": recorded_at,
        "note": note,
    }
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, indent=2,
                            sort_keys=True) + "\n")
