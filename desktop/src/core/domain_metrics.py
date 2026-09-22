"""域功能引擎：把「AI 品类域」的口径变成**可复算的数**（产出形态 T4 面）。

背景（内部差距）：用户清单里 100 个 AI 品类，如果每个域包只产出散文，等于把「AI 域知识」
退化成资料页——NF 的质量函数要求产出**功能性 + 可机验**。本模块提供一族**确定性评测口径**，
每个族对应一类域的真实度量（分类 / 检索 / 抽取 / 生成 / 回归 / 校准 / 一致性 / 排序偏好 /
形式化判定 / 时延成本 / 漂移 / 契约合规），域包各自声明用哪一族 + 输入样例，
门禁用本模块重算产出并与在盘报告逐字段比对（T4 可复算）。

纪律：
- **口径显式**：每个族写明公式与统计口径（判据、边界处理），不默认任何隐含约定；
- **确定性**：纯函数、无墙钟、无随机、四舍五入到固定位数 → 同输入逐字节一致；
- **不夸口**：算的是**样例集上的口径值**，不是模型能力声明；报告里必须带 sample 规模与族名。
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence, Tuple

DIGITS = 6


def _r(x: float) -> float:
    return round(float(x), DIGITS)


def _safe_div(a: float, b: float) -> float:
    return 0.0 if b == 0 else a / b


# ------------------------------------------------------------------ 输入装载

def load_rows(path: str | Path) -> Tuple[List[Dict[str, str]], str]:
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        return [], "不可读：%s" % exc
    rows = [dict(r) for r in csv.DictReader(text.splitlines())]
    if not rows:
        return [], "空表（%s）" % p.name
    return rows, ""


def _num(row: Dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, ""))
    except (TypeError, ValueError):
        raise ValueError("列 %s 非数值：%r" % (key, row.get(key)))


def _flag(row: Dict[str, str], key: str) -> int:
    v = str(row.get(key, "")).strip().lower()
    if v in ("1", "true", "yes", "y", "正", "是"):
        return 1
    if v in ("0", "false", "no", "n", "负", "否"):
        return 0
    raise ValueError("列 %s 非 0/1：%r" % (key, row.get(key)))


# ------------------------------------------------------------------ 度量族

def classification(rows: Sequence[Dict[str, str]], **kw) -> Dict[str, Any]:
    """分类口径：accuracy / macro P-R-F1 / 混淆矩阵（混淆键 = 出现过的 gold 标签，字典序）。"""
    labels = sorted({str(r["gold"]) for r in rows} | {str(r["pred"]) for r in rows})
    cm = {g: {p: 0 for p in labels} for g in labels}
    for r in rows:
        cm[str(r["gold"])][str(r["pred"])] += 1
    n = len(rows)
    correct = sum(cm[l][l] for l in labels)
    per: Dict[str, Dict[str, float]] = {}
    for l in labels:
        tp = cm[l][l]
        fp = sum(cm[g][l] for g in labels if g != l)
        fn = sum(cm[l][p] for p in labels if p != l)
        p = _safe_div(tp, tp + fp)
        rc = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * p * rc, p + rc)
        per[l] = {"precision": _r(p), "recall": _r(rc), "f1": _r(f1),
                  "support": tp + fn}
    macro = {k: _r(sum(per[l][k] for l in labels) / len(labels))
             for k in ("precision", "recall", "f1")}
    out: Dict[str, Any] = {
        "family": "classification",
        "n": n,
        "accuracy": _r(correct / n),
        "macro": macro,
        "confusion": {g: cm[g] for g in labels},
        "per_label": per,
    }
    if all(str(r["gold"]) in ("0", "1") for r in rows) and all("score" in r for r in rows):
        out["roc_auc"] = _r(_auc([(float(r["score"]), _flag(r, "gold")) for r in rows]))
    return out


def _auc(pairs: Sequence[Tuple[float, int]]) -> float:
    """ROC-AUC（Mann-Whitney 口径，并列取平均秩）。"""
    pos = [s for s, y in pairs if y == 1]
    neg = [s for s, y in pairs if y == 0]
    if not pos or not neg:
        return 0.0
    wins = 0.0
    for s in pos:
        for t in neg:
            wins += 1.0 if s > t else (0.5 if s == t else 0.0)
    return wins / (len(pos) * len(neg))


def retrieval(rows: Sequence[Dict[str, str]], k: int = 5, **kw) -> Dict[str, Any]:
    """检索口径：recall@k / precision@k / MRR / NDCG@k / MAP（按 query_id 分组，rank 升序）。"""
    groups: Dict[str, List[Tuple[int, int]]] = {}
    for r in rows:
        groups.setdefault(str(r["query_id"]), []).append(
            (int(_num(r, "rank")), _flag(r, "relevant")))
    recalls, precisions, rrs, ndcgs, aps = [], [], [], [], []
    for _q, items in sorted(groups.items()):
        items = sorted(items)
        rel = [y for _rk, y in items]
        topk = rel[:k]
        total_rel = sum(rel)
        recalls.append(_safe_div(sum(topk), total_rel))
        precisions.append(_safe_div(sum(topk), k))
        rr = 0.0
        for i, y in enumerate(rel, 1):
            if y:
                rr = 1.0 / i
                break
        rrs.append(rr)
        dcg = sum(y / math.log2(i + 1) for i, y in enumerate(rel[:k], 1))
        ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(total_rel, k) + 1))
        ndcgs.append(_safe_div(dcg, ideal))
        hits, ap = 0, 0.0
        for i, y in enumerate(rel, 1):
            if y:
                hits += 1
                ap += hits / i
        aps.append(_safe_div(ap, total_rel))
    return {
        "family": "retrieval", "k": k, "queries": len(groups), "n": len(rows),
        "recall_at_k": _r(sum(recalls) / len(recalls) if recalls else 0.0),
        "precision_at_k": _r(sum(precisions) / len(precisions) if precisions else 0.0),
        "mrr": _r(sum(rrs) / len(rrs) if rrs else 0.0),
        "ndcg_at_k": _r(sum(ndcgs) / len(ndcgs) if ndcgs else 0.0),
        "map": _r(sum(aps) / len(aps) if aps else 0.0),
    }


def extraction(rows: Sequence[Dict[str, str]], **kw) -> Dict[str, Any]:
    """抽取口径：整条精确匹配 + 字段级 P/R/F1（gold_fields / pred_fields = JSON 数组）。"""
    em, tp, fp, fn = 0, 0, 0, 0
    for r in rows:
        g = set(json.loads(r["gold_fields"]))
        p = set(json.loads(r["pred_fields"]))
        if g == p:
            em += 1
        tp += len(g & p)
        fp += len(p - g)
        fn += len(g - p)
    pr = _safe_div(tp, tp + fp)
    rc = _safe_div(tp, tp + fn)
    return {"family": "extraction", "n": len(rows), "exact_match": _r(em / len(rows)),
            "field_precision": _r(pr), "field_recall": _r(rc),
            "field_f1": _r(_safe_div(2 * pr * rc, pr + rc)),
            "tp": tp, "fp": fp, "fn": fn}


def generation(rows: Sequence[Dict[str, str]], **kw) -> Dict[str, Any]:
    """生成口径（确定性代理）：精确匹配率 + 字符级 F1 + 词序不敏感的集合 F1。"""
    em, char_f1, set_f1 = 0, [], []
    for r in rows:
        g, p = str(r["reference"]), str(r["output"])
        if g == p:
            em += 1
        gs, ps = set(g), set(p)
        prec, rec = _safe_div(len(gs & ps), len(ps)), _safe_div(len(gs & ps), len(gs))
        char_f1.append(_safe_div(2 * prec * rec, prec + rec))
        gt, pt = set(g.split()), set(p.split())
        p2, r2 = _safe_div(len(gt & pt), len(pt)), _safe_div(len(gt & pt), len(gt))
        set_f1.append(_safe_div(2 * p2 * r2, p2 + r2))
    n = len(rows)
    return {"family": "generation", "n": n, "exact_match": _r(em / n),
            "char_f1": _r(sum(char_f1) / n), "token_set_f1": _r(sum(set_f1) / n)}


def regression(rows: Sequence[Dict[str, str]], **kw) -> Dict[str, Any]:
    """回归口径：MAE / RMSE / R² / MAPE（MAPE 仅在 gold≠0 的样本上计算，样本数显式给出）。"""
    g = [_num(r, "gold") for r in rows]
    p = [_num(r, "pred") for r in rows]
    n = len(rows)
    mae = sum(abs(a - b) for a, b in zip(g, p)) / n
    rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(g, p)) / n)
    mg = sum(g) / n
    ss_tot = sum((a - mg) ** 2 for a in g)
    ss_res = sum((a - b) ** 2 for a, b in zip(g, p))
    nz = [(a, b) for a, b in zip(g, p) if a != 0]
    mape = (sum(abs((a - b) / a) for a, b in nz) / len(nz)) if nz else 0.0
    return {"family": "regression", "n": n, "mae": _r(mae), "rmse": _r(rmse),
            "r2": _r(1 - _safe_div(ss_res, ss_tot)), "mape": _r(mape),
            "mape_samples": len(nz)}


def calibration(rows: Sequence[Dict[str, str]], bins: int = 10, **kw) -> Dict[str, Any]:
    """校准口径：ECE（等宽分箱，空箱跳过并给出非空箱数）/ Brier / 可靠性桶明细。"""
    pairs = [(_num(r, "prob"), _flag(r, "gold")) for r in rows]
    if any(not (0.0 <= p <= 1.0) for p, _ in pairs):
        raise ValueError("prob 必须在 [0,1]")
    n = len(pairs)
    brier = sum((p - y) ** 2 for p, y in pairs) / n
    buckets: List[Dict[str, Any]] = []
    ece = 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        sel = [(p, y) for p, y in pairs if (lo <= p < hi) or (b == bins - 1 and p == 1.0)]
        if not sel:
            continue
        conf = sum(p for p, _ in sel) / len(sel)
        acc = sum(y for _, y in sel) / len(sel)
        ece += (len(sel) / n) * abs(conf - acc)
        buckets.append({"range": "[%.1f,%.1f]" % (lo, hi), "n": len(sel),
                        "confidence": _r(conf), "accuracy": _r(acc),
                        "gap": _r(abs(conf - acc))})
    return {"family": "calibration", "n": n, "bins": bins,
            "nonempty_bins": len(buckets), "ece": _r(ece), "brier": _r(brier),
            "buckets": buckets}


def agreement(rows: Sequence[Dict[str, str]], **kw) -> Dict[str, Any]:
    """标注一致性口径：Cohen's kappa（两标注者，公式 κ = (po − pe)/(1 − pe)）+ 原始一致率。"""
    labels = sorted({str(r["a"]) for r in rows} | {str(r["b"]) for r in rows})
    n = len(rows)
    cm = {x: {y: 0 for y in labels} for x in labels}
    for r in rows:
        cm[str(r["a"])][str(r["b"])] += 1
    po = sum(cm[l][l] for l in labels) / n
    pe = sum((sum(cm[l].values()) / n) * (sum(cm[g][l] for g in labels) / n)
             for l in labels)
    return {"family": "agreement", "n": n, "labels": len(labels),
            "observed_agreement": _r(po), "expected_agreement": _r(pe),
            "cohen_kappa": _r(_safe_div(po - pe, 1 - pe)),
            "confusion": {x: cm[x] for x in labels}}


def preference(rows: Sequence[Dict[str, str]], **kw) -> Dict[str, Any]:
    """偏好/对齐口径：一致率 + 胜率（ties 单列，不计入胜率分母之外）。"""
    n = len(rows)
    agree = sum(1 for r in rows if str(r["judge"]).strip() == str(r["human"]).strip())
    win = sum(1 for r in rows if str(r["judge"]).strip() == "a")
    loss = sum(1 for r in rows if str(r["judge"]).strip() == "b")
    tie = n - win - loss
    return {"family": "preference", "n": n, "agreement": _r(agree / n),
            "win": win, "loss": loss, "tie": tie,
            "win_rate_excl_tie": _r(_safe_div(win, win + loss))}


def exact_judgement(rows: Sequence[Dict[str, str]], k: int = 4, **kw) -> Dict[str, Any]:
    """形式化/问答判定口径：pass@1 与 pass@k（无偏估计，Chen et al. 2021 口径）。

    pass@k = 1 − C(n−c, k)/C(n, k)，n = 每题采样数，c = 其中通过数；c=0 记为 0，n<k 时该题跳过并计数。
    """
    groups: Dict[str, List[int]] = {}
    for r in rows:
        groups.setdefault(str(r["task_id"]), []).append(_flag(r, "passed"))
    pass1, passk, skipped, used = [], [], 0, 0
    for _t, ys in sorted(groups.items()):
        n, c = len(ys), sum(ys)
        pass1.append(c / n)
        if n < k:
            skipped += 1
            continue
        used += 1
        if c == 0:
            passk.append(0.0)
            continue
        if n - c < k:
            passk.append(1.0)
            continue
        num = 1.0
        for i in range(k):
            num *= (n - c - i) / (n - i)
        passk.append(1 - num)
    return {"family": "exact_judgement", "k": k, "tasks": len(groups), "n": len(rows),
            "pass_at_1": _r(sum(pass1) / len(pass1) if pass1 else 0.0),
            "pass_at_k": _r(sum(passk) / len(passk) if passk else 0.0),
            "tasks_used_for_passk": used, "tasks_skipped_insufficient_samples": skipped}


def latency_cost(rows: Sequence[Dict[str, str]], price_per_1k_in: float = 0.0,
                 price_per_1k_out: float = 0.0, **kw) -> Dict[str, Any]:
    """服务口径：时延分位（最近秩法，显式说明）+ 吞吐 + 成本/1k 调用（单价显式传入）。"""
    lat = sorted(_num(r, "latency_ms") for r in rows)

    def pct(q: float) -> float:
        idx = max(0, min(len(lat) - 1, math.ceil(q * len(lat)) - 1))
        return _r(lat[idx])

    tin = sum(_num(r, "tokens_in") for r in rows)
    tout = sum(_num(r, "tokens_out") for r in rows)
    n = len(rows)
    cost = (tin / 1000.0) * price_per_1k_in + (tout / 1000.0) * price_per_1k_out
    return {"family": "latency_cost", "n": n,
            "p50_ms": pct(0.50), "p95_ms": pct(0.95), "p99_ms": pct(0.99),
            "mean_ms": _r(sum(lat) / n), "max_ms": _r(lat[-1]),
            "tokens_in": int(tin), "tokens_out": int(tout),
            "price_per_1k_in": _r(price_per_1k_in),
            "price_per_1k_out": _r(price_per_1k_out),
            "cost_total": _r(cost), "cost_per_1k_calls": _r(cost / n * 1000)}


def drift(rows: Sequence[Dict[str, str]], **kw) -> Dict[str, Any]:
    """分布漂移口径：PSI（Population Stability Index）= Σ(p−q)·ln(p/q)，空桶用 1e-6 平滑并显式记档。"""
    eps = 1e-6
    psi = 0.0
    detail = []
    for r in rows:
        p = _num(r, "expected") + eps
        q = _num(r, "actual") + eps
        term = (p - q) * math.log(p / q)
        psi += term
        detail.append({"bucket": r.get("bucket", ""), "expected": _r(p), "actual": _r(q),
                       "term": _r(term)})
    return {"family": "drift", "buckets": len(rows), "psi": _r(psi),
            "smoothing_epsilon": eps, "detail": detail}


def contract_compliance(rows: Sequence[Dict[str, str]], **kw) -> Dict[str, Any]:
    """契约合规口径：合规率 + 缺字段分布（缺字段数最多的前 5 项，便于定位修复）。"""
    n = len(rows)
    ok = sum(1 for r in rows if _flag(r, "valid") == 1)
    missing: Dict[str, int] = {}
    for r in rows:
        for f in str(r.get("missing_fields", "")).replace("|", ",").replace(";", ",").split(","):
            f = f.strip()
            if f:
                missing[f] = missing.get(f, 0) + 1
    top = sorted(missing.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return {"family": "contract_compliance", "n": n, "compliance_rate": _r(ok / n),
            "violations": n - ok,
            "missing_top": [{"field": k, "count": v} for k, v in top]}


FAMILIES: Dict[str, Callable[..., Dict[str, Any]]] = {
    "classification": classification,
    "retrieval": retrieval,
    "extraction": extraction,
    "generation": generation,
    "regression": regression,
    "calibration": calibration,
    "agreement": agreement,
    "preference": preference,
    "exact_judgement": exact_judgement,
    "latency_cost": latency_cost,
    "drift": drift,
    "contract_compliance": contract_compliance,
}


# ------------------------------------------------------------------ 确定性夹具

class _Rng:
    """线性同余（确定性夹具专用）：同种子同序列；不使用 random（避免全局状态）。"""

    def __init__(self, seed: str) -> None:
        self.state = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12], 16)

    def next(self) -> float:
        self.state = (1103515245 * self.state + 12345) % (2 ** 31)
        return self.state / float(2 ** 31)

    def pick(self, items: Sequence[Any]) -> Any:
        return items[int(self.next() * len(items)) % len(items)]

    def between(self, lo: float, hi: float) -> float:
        return lo + (hi - lo) * self.next()


def synthesize(family: str, seed: str, n: int = 0) -> List[Dict[str, str]]:
    """按族生成确定性样例夹具（**合成数据**：口径可复算、可核；不代表真实测量结果）。"""
    r = _Rng("%s|%s" % (family, seed))
    rows: List[Dict[str, str]] = []
    if family == "classification":
        for i in range(n or 24):
            gold = r.pick(["pos", "neg"])
            hit = r.next() < 0.8
            pred = gold if hit else ("neg" if gold == "pos" else "pos")
            rows.append({"case_id": "c%02d" % i, "gold": gold, "pred": pred,
                         "score": "%.4f" % (r.between(0.55, 0.99) if gold == "pos"
                                            else r.between(0.01, 0.45))})
    elif family == "retrieval":
        for q in range(n or 3):
            rel_idx = {int(r.between(0, 6)), int(r.between(0, 6))}
            for rk in range(6):
                rows.append({"query_id": "q%d" % q, "rank": str(rk + 1),
                             "relevant": "1" if rk in rel_idx else "0"})
    elif family == "extraction":
        fields = ["品牌", "型号", "价格", "日期", "数量", "单位"]
        for i in range(n or 12):
            gold = sorted({r.pick(fields), r.pick(fields)})
            pred = sorted(set(gold) | ({r.pick(fields)} if r.next() < 0.3 else set()))
            rows.append({"case_id": "e%02d" % i,
                         "gold_fields": json.dumps(gold, ensure_ascii=False),
                         "pred_fields": json.dumps(pred, ensure_ascii=False)})
    elif family == "generation":
        words = ["模型", "口径", "评测", "样本", "结论", "边界"]
        for i in range(n or 12):
            ref = "".join(r.pick(words) for _ in range(5))
            out = ref if r.next() < 0.4 else "".join(r.pick(words) for _ in range(5))
            rows.append({"case_id": "g%02d" % i, "reference": ref, "output": out})
    elif family == "regression":
        for i in range(n or 16):
            gold = r.between(-2.0, 2.0)
            rows.append({"case_id": "r%02d" % i, "gold": "%.4f" % gold,
                         "pred": "%.4f" % (gold + r.between(-0.25, 0.25))})
    elif family == "calibration":
        for i in range(n or 20):
            p = r.between(0.05, 0.95)
            rows.append({"case_id": "k%02d" % i, "prob": "%.4f" % p,
                         "gold": "1" if r.next() < p else "0"})
    elif family == "agreement":
        for i in range(n or 20):
            a = r.pick(["T", "F"])
            rows.append({"case_id": "a%02d" % i, "a": a,
                         "b": a if r.next() < 0.85 else ("F" if a == "T" else "T")})
    elif family == "preference":
        for i in range(n or 16):
            human = r.pick(["a", "b"])
            rows.append({"case_id": "p%02d" % i, "human": human,
                         "judge": human if r.next() < 0.7 else r.pick(["a", "b", "tie"])})
    elif family == "exact_judgement":
        for t in range(n or 4):
            for i in range(4):
                rows.append({"task_id": "t%d" % t, "sample": str(i + 1),
                             "passed": "1" if r.next() < 0.5 else "0"})
    elif family == "latency_cost":
        for i in range(n or 20):
            rows.append({"case_id": "l%02d" % i,
                         "latency_ms": "%.1f" % r.between(120.0, 900.0),
                         "tokens_in": str(int(r.between(200, 1800))),
                         "tokens_out": str(int(r.between(50, 600)))})
    elif family == "drift":
        for i in range(n or 8):
            e = r.between(0.05, 0.20)
            rows.append({"bucket": "b%d" % i, "expected": "%.4f" % e,
                         "actual": "%.4f" % max(0.001, e + r.between(-0.03, 0.03))})
    elif family == "contract_compliance":
        fields = ["available_ts", "unit", "currency", "version", "owner"]
        for i in range(n or 20):
            ok = r.next() < 0.8
            miss = "" if ok else "|".join(sorted({r.pick(fields), r.pick(fields)}))
            rows.append({"case_id": "v%02d" % i, "valid": "1" if ok else "0",
                         "missing_fields": miss})
    else:
        raise ValueError("未登记夹具族：%r" % family)
    return rows


def rows_to_csv(rows: Sequence[Dict[str, str]]) -> str:
    """夹具 → CSV（列序 = 首行键序；确定性）。"""
    if not rows:
        return ""
    cols = list(rows[0].keys())
    out = [",".join(cols)]
    for r in rows:
        out.append(",".join('"%s"' % str(r.get(c, "")).replace('"', '""') for c in cols))
    return "\n".join(out) + "\n"


def evaluate(family: str, rows: Sequence[Dict[str, str]], **params) -> Dict[str, Any]:
    fn = FAMILIES.get(family)
    if fn is None:
        raise ValueError("未登记度量族：%r（可选：%s）" % (family, sorted(FAMILIES)))
    body = fn(rows, **params)
    body["digits"] = DIGITS
    body["note"] = ("样例集上的口径值（非模型能力声明）；口径公式见 docs/domain-packs.md；"
                    "本报告由 core/domain_metrics.py 确定性复算（T4）")
    return body
