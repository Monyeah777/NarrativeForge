"""量化金融域功能面：把「指标只写在散文里」变成**可复算的引擎**。

背景（内部差距）：`community/量化金融域包/assets/QUANT_METRICS.md` 把夏普 / 最大回撤 /
卡尔玛 / 换手 / IC / IR 的公式写成 Markdown 表格——人能读，机器既算不出，也判不了
「同一口径」。本模块按该资产的口径**逐条实现**，产出的报告是 T4 档位：check32 会用
本模块重算在盘报告，逐字段比对，口径漂移即 FAIL。

口径纪律（与 QUANT_METRICS.md 一一对应，不另立门派）：
- 简单收益 `r_t = P_t / P_{t-1} − 1`；对数收益 `ln(P_t / P_{t-1})`（两者不混用）；
- 年化因子按频率取 252 / 52 / 12（**必须显式声明**，不得默认 365）；
- 夏普 `(mean(r) − rf_period) / std(r) × sqrt(af)`（样本标准差 ddof=1）；
- 最大回撤按**净值**序列的历史峰值口径；
- 卡尔玛 = 年化收益 / 最大回撤（分子分母同源区间）；
- 换手按单边声明（`sum(|Δw|)/2`），双边须显式声明；
- IC = 因子值与随后期收益的截面秩相关（spearman）。

确定性：所有输出四舍五入到固定小数位，纯函数、无墙钟、无随机——同一输入两次调用
逐字节一致（check32 复算比对的前提）。
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

ANNUAL_FACTORS = {"daily": 252, "weekly": 52, "monthly": 12}
DIGITS = 6
#: 本仓口径与 GIPS 的关系：只有「口径 + 披露面」对齐，**不构成 GIPS 合规声明**
GIPS_ALIGNMENT = ("口径与披露面（收益口径/年化因子/无风险利率/基准/费用与成交假设）"
                  "逐项显式；**非 GIPS 合规声明**——合规需第三方鉴证与合成组合全量数据")


def _r(x: float) -> float:
    return round(float(x), DIGITS)


# ------------------------------------------------------------------ 数据装载

def load_equity_curve(path: str | Path) -> Tuple[Dict[str, Any], str]:
    """读净值曲线 CSV（表头须含 date,equity[,benchmark]）；口径错误即返回错误串。"""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, "不可读：%s" % exc
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        return {}, "空表"
    cols = {c.strip().lower() for c in (rows[0].keys() if rows else []) if c}
    for need in ("date", "equity"):
        if need not in cols:
            return {}, "缺列 %s（实际列：%s）" % (need, sorted(cols))
    dates: List[str] = []
    equity: List[float] = []
    bench: List[float] = []
    has_bench = "benchmark" in cols
    for i, row in enumerate(rows, 2):
        try:
            dates.append(str(row.get("date") or row.get("Date") or "").strip())
            equity.append(float(row.get("equity") or row.get("Equity")))
            if has_bench:
                bench.append(float(row.get("benchmark") or row.get("Benchmark")))
        except (TypeError, ValueError):
            return {}, "第 %d 行数值不可解析" % i
    if len(equity) < 3:
        return {}, "样本过短（< 3 个净值点）"
    if any(v <= 0 for v in equity):
        return {}, "净值须为正数（口径：净值序列，非累计收益）"
    return {"dates": dates, "equity": equity,
            "benchmark": bench if has_bench else None}, ""


# ------------------------------------------------------------------ 基础口径

def simple_returns(prices: Sequence[float]) -> List[float]:
    return [prices[i] / prices[i - 1] - 1.0 for i in range(1, len(prices))]


def log_returns(prices: Sequence[float]) -> List[float]:
    return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]


def returns(prices: Sequence[float], kind: str = "simple") -> List[float]:
    if kind == "simple":
        return simple_returns(prices)
    if kind == "log":
        return log_returns(prices)
    raise ValueError("收益口径只支持 simple / log，实为 %r" % kind)


def _geo_link(rets: Sequence[float]) -> float:
    acc = 1.0
    for x in rets:
        acc *= (1.0 + x)
    return acc


def cumulative_return(prices: Sequence[float]) -> float:
    return prices[-1] / prices[0] - 1.0


def annualized_return(prices: Sequence[float], annual_factor: int) -> float:
    n = len(prices) - 1
    if n <= 0:
        return 0.0
    growth = prices[-1] / prices[0]
    return growth ** (annual_factor / n) - 1.0


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _stdev(xs: Sequence[float]) -> float:
    """样本标准差（ddof=1）——与 empyrical / pandas 默认口径一致。"""
    n = len(xs)
    if n < 2:
        return 0.0
    mu = _mean(xs)
    return math.sqrt(sum((x - mu) ** 2 for x in xs) / (n - 1))


def annualized_volatility(rets: Sequence[float], annual_factor: int) -> float:
    return _stdev(rets) * math.sqrt(annual_factor)


def max_drawdown(prices: Sequence[float]) -> float:
    peak = prices[0]
    mdd = 0.0
    for p in prices:
        peak = max(peak, p)
        mdd = max(mdd, (peak - p) / peak)
    return mdd


def drawdown_series(prices: Sequence[float]) -> List[float]:
    peak = prices[0]
    out = []
    for p in prices:
        peak = max(peak, p)
        out.append((peak - p) / peak)
    return out


def sharpe(rets: Sequence[float], risk_free_annual: float, annual_factor: int) -> float:
    sd = _stdev(rets)
    if sd == 0:
        return 0.0
    rf_period = (1.0 + risk_free_annual) ** (1.0 / annual_factor) - 1.0
    return (_mean(rets) - rf_period) / sd * math.sqrt(annual_factor)


def calmar(annual_ret: float, mdd: float) -> float:
    return 0.0 if mdd == 0 else annual_ret / mdd


def tracking_error(rets: Sequence[float], bench: Sequence[float], annual_factor: int) -> float:
    n = min(len(rets), len(bench))
    if n < 2:
        return 0.0
    active = [rets[i] - bench[i] for i in range(n)]
    return _stdev(active) * math.sqrt(annual_factor)


def information_ratio(rets: Sequence[float], bench: Sequence[float],
                      annual_factor: int) -> float:
    n = min(len(rets), len(bench))
    if n < 2:
        return 0.0
    active = [rets[i] - bench[i] for i in range(n)]
    sd = _stdev(active)
    if sd == 0:
        return 0.0
    return _mean(active) / sd * math.sqrt(annual_factor)


def _rank(xs: Sequence[float]) -> List[float]:
    """平均秩（并列取平均）——spearman 的秩定义，避免并列值造成口径漂移。"""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(a: Sequence[float], b: Sequence[float]) -> float:
    n = min(len(a), len(b))
    if n < 2:
        return 0.0
    ma, mb = _mean(a[:n]), _mean(b[:n])
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((a[i] - ma) ** 2 for i in range(n)))
    db = math.sqrt(sum((b[i] - mb) ** 2 for i in range(n)))
    return 0.0 if da == 0 or db == 0 else num / (da * db)


def information_coefficient(factor: Sequence[float], forward_return: Sequence[float],
                            method: str = "spearman") -> float:
    if method == "spearman":
        return _pearson(_rank(factor), _rank(forward_return))
    if method == "pearson":
        return _pearson(factor, forward_return)
    raise ValueError("IC 口径只支持 spearman / pearson，实为 %r" % method)


def turnover(weights: Sequence[Sequence[float]], single_side: bool = True) -> List[float]:
    """换手率：`sum(|Δw|)/2`（单边，缺省）或 `sum(|Δw|)`（双边）——口径必须声明。"""
    out = []
    for i in range(1, len(weights)):
        gross = sum(abs(weights[i][j] - weights[i - 1][j])
                    for j in range(min(len(weights[i]), len(weights[i - 1]))))
        out.append(gross / 2.0 if single_side else gross)
    return out


# ------------------------------------------------------------------ 报告装配

def _block(prices: Sequence[float], annual_factor: int, risk_free_annual: float,
           ret_kind: str) -> Dict[str, float]:
    rets = returns(prices, ret_kind)
    ann = annualized_return(prices, annual_factor)
    mdd = max_drawdown(prices)
    return {
        "cumulative": _r(cumulative_return(prices)),
        "annualized": _r(ann),
        "volatility_annualized": _r(annualized_volatility(rets, annual_factor)),
        "sharpe": _r(sharpe(rets, risk_free_annual, annual_factor)),
        "max_drawdown": _r(mdd),
        "calmar": _r(calmar(ann, mdd)),
    }


def performance_report(series: Dict[str, Any], *, period_start: str, period_end: str,
                       currency: str = "CNY", return_basis: str = "simple",
                       frequency: str = "daily", risk_free_rate_annual: float = 0.0,
                       benchmark_id: str = "", cost_bps_fee: float = 0.0,
                       cost_bps_slippage: float = 0.0, fill_rule: str = "next_open",
                       single_side_turnover: bool = True,
                       as_of: str = "") -> Dict[str, Any]:
    """GIPS 对齐的绩效报告（口径 + 披露面显式）；纯函数，可逐字节复算。"""
    if frequency not in ANNUAL_FACTORS:
        raise ValueError("频率须在 %s 中，实为 %r" % (sorted(ANNUAL_FACTORS), frequency))
    af = ANNUAL_FACTORS[frequency]
    equity = series["equity"]
    bench = series.get("benchmark")
    gross = _block(equity, af, risk_free_rate_annual, return_basis)
    doc: Dict[str, Any] = {
        "kind": "nf-performance/1",
        "as_of": as_of or period_end,
        "currency": currency,
        "return_basis": return_basis,
        "frequency": frequency,
        "annual_factor": af,
        "risk_free_rate_annual": _r(risk_free_rate_annual),
        "period": {"start": period_start, "end": period_end,
                   "observations": len(equity)},
        "gross": gross,
        "benchmark": None,
        "excess": None,
        "costs": {"fee_bps": _r(cost_bps_fee), "slippage_bps": _r(cost_bps_slippage),
                  "fill_rule": fill_rule,
                  "turnover_basis": "single_side" if single_side_turnover else "double_side"},
        "disclosures": [
            "收益口径 = %s；年化因子 = %d（%s）；无风险利率年化 = %s"
            % (return_basis, af, frequency, _r(risk_free_rate_annual)),
            "绩效为**毛口径**（未扣费）；费用与滑点按申报值计（fee=%s bps, slippage=%s bps）"
            % (_r(cost_bps_fee), _r(cost_bps_slippage)),
            "成交价假设 = %s（须晚于信号时点；前视偏差口径见 DATA_CONTRACT §7）" % fill_rule,
            "最大回撤 / 卡尔玛按净值序列口径；卡尔玛分子分母同区间",
            GIPS_ALIGNMENT,
        ],
    }
    if bench:
        doc["benchmark"] = {"id": benchmark_id or "UNSPECIFIED", **_block(
            bench, af, risk_free_rate_annual, return_basis)}
        rets, brets = returns(equity, return_basis), returns(bench, return_basis)
        doc["excess"] = {
            "annualized": _r(doc["gross"]["annualized"] - doc["benchmark"]["annualized"]),
            "tracking_error": _r(tracking_error(rets, brets, af)),
            "information_ratio": _r(information_ratio(rets, brets, af)),
        }
    return doc


# ------------------------------------------------------------------ 图表规格

def vega_equity_curve(series: Dict[str, Any], title: str = "净值曲线") -> Dict[str, Any]:
    """Vega-Lite v5 规格（图表即数据）——确定性：同输入逐字节一致。"""
    data = [{"date": d, "series": "策略", "value": v}
            for d, v in zip(series["dates"], series["equity"])]
    if series.get("benchmark"):
        data += [{"date": d, "series": "基准", "value": v}
                 for d, v in zip(series["dates"], series["benchmark"])]
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": title,
        "data": {"values": data},
        "mark": {"type": "line", "point": False},
        "encoding": {
            "x": {"field": "date", "type": "temporal", "title": "日期"},
            "y": {"field": "value", "type": "quantitative", "title": "净值",
                  "scale": {"zero": False}},
            "color": {"field": "series", "type": "nominal", "title": ""},
        },
    }


def vega_drawdown(series: Dict[str, Any], title: str = "回撤曲线") -> Dict[str, Any]:
    dd = drawdown_series(series["equity"])
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": title,
        "data": {"values": [{"date": d, "value": -abs(v)}
                            for d, v in zip(series["dates"], dd)]},
        "mark": {"type": "area", "line": True},
        "encoding": {
            "x": {"field": "date", "type": "temporal", "title": "日期"},
            "y": {"field": "value", "type": "quantitative", "title": "回撤",
                  "scale": {"zero": True}},
        },
    }


def mermaid_declaration_flow() -> str:
    """口径声明依赖（Mermaid 图即数据）：缺一环即口径未定义。"""
    return "\n".join([
        "%% 口径声明链（QUANT_METRICS 口径纪律的可视化，非新增真源）",
        "flowchart LR",
        "  A[收益口径 simple/log] --> D[绩效报告]",
        "  B[年化因子 252/52/12] --> D",
        "  C[无风险利率 rf] --> D",
        "  E[净值序列] --> D",
        "  D --> F[披露面 disclosures]",
        "  G[成本与滑点申报] --> F",
        "  H[基准与成交价假设] --> F",
    ]) + "\n"
