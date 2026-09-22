#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""量化域功能面单测：口径公式（对可手算的向量）+ 确定性 + 报告与图表产物。

口径判据来自 assets/QUANT_METRICS.md（不是外部项目定义）：
  简单/对数收益、年化因子、年化波动、夏普、最大回撤、卡尔玛、换手、IC、IR。
"""
import math
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import quant_metrics as qm  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = ROOT / "community" / "量化金融域包" / "outputs" / "samples" / "EQUITY_CURVE.csv"


class FormulaTest(unittest.TestCase):
    def test_simple_and_log_returns(self):
        prices = [100.0, 110.0, 99.0]
        r = qm.simple_returns(prices)
        self.assertAlmostEqual(r[0], 0.10)
        self.assertAlmostEqual(r[1], -0.10)
        lg = qm.log_returns([1.0, math.e])
        self.assertAlmostEqual(lg[0], 1.0)

    def test_annual_factor_table(self):
        self.assertEqual(qm.ANNUAL_FACTORS, {"daily": 252, "weekly": 52, "monthly": 12})
        with self.assertRaises(ValueError):
            qm.performance_report({"equity": [1, 2, 3], "dates": ["a", "b", "c"]},
                                  period_start="x", period_end="y", frequency="hourly")

    def test_max_drawdown_and_series(self):
        prices = [1.0, 1.25, 0.75, 1.0]
        self.assertAlmostEqual(qm.max_drawdown(prices), 0.40)   # 1.25 → 0.75
        self.assertAlmostEqual(qm.drawdown_series(prices)[2], 0.40)

    def test_sharpe_matches_manual_formula(self):
        prices = [1.0, 1.01, 1.02, 1.01, 1.03]
        rets = qm.simple_returns(prices)
        mu = sum(rets) / len(rets)
        sd = math.sqrt(sum((x - mu) ** 2 for x in rets) / (len(rets) - 1))
        rf = 0.0
        expect = (mu - rf) / sd * math.sqrt(252)
        self.assertAlmostEqual(qm.sharpe(rets, rf, 252), expect)

    def test_calmar_zero_drawdown_is_zero(self):
        self.assertEqual(qm.calmar(0.2, 0.0), 0.0)

    def test_turnover_single_vs_double_side(self):
        w = [[0.5, 0.5], [1.0, 0.0]]
        self.assertAlmostEqual(qm.turnover(w, single_side=True)[0], 0.5)
        self.assertAlmostEqual(qm.turnover(w, single_side=False)[0], 1.0)

    def test_ic_spearman_and_pearson(self):
        f = [1.0, 2.0, 3.0, 4.0]
        r = [0.1, 0.2, 0.3, 0.4]
        self.assertAlmostEqual(qm.information_coefficient(f, r, "spearman"), 1.0)
        self.assertAlmostEqual(qm.information_coefficient(f, [-x for x in r],
                                                          "spearman"), -1.0)
        with self.assertRaises(ValueError):
            qm.information_coefficient(f, r, "kendall")

    def test_rank_ties_average(self):
        self.assertEqual(qm._rank([1.0, 1.0, 3.0]), [1.5, 1.5, 3.0])


class ReportTest(unittest.TestCase):
    def test_report_is_deterministic_and_disclosed(self):
        series, err = qm.load_equity_curve(SAMPLE)
        self.assertEqual(err, "")
        kw = dict(period_start="2026-06-01", period_end="2026-08-21",
                  currency="CNY", frequency="daily", risk_free_rate_annual=0.015,
                  benchmark_id="NF-SAMPLE-INDEX", cost_bps_fee=3.0,
                  cost_bps_slippage=5.0, fill_rule="next_open", as_of="2026-08-21")
        a = qm.performance_report(series, **kw)
        b = qm.performance_report(series, **kw)
        self.assertEqual(a, b, "同一输入两次装配必须逐字段一致（T4 复算前提）")
        self.assertEqual(a["annual_factor"], 252)
        for key in ("cumulative", "annualized", "volatility_annualized", "sharpe",
                    "max_drawdown", "calmar"):
            self.assertIn(key, a["gross"])
        self.assertGreaterEqual(len(a["disclosures"]), 5)
        self.assertTrue(any("非 GIPS 合规" in d for d in a["disclosures"]),
                        "必须显式声明非合规（不得靠外部标准背书）")
        self.assertEqual(a["costs"]["turnover_basis"], "single_side")

    def test_load_rejects_bad_input(self):
        self.assertTrue(qm.load_equity_curve(ROOT / "nope.csv")[1])
        self.assertIn("缺列", qm.load_equity_curve(
            ROOT / "community" / "量化金融域包" / "outputs" / "INDEX.json")[1])

    def test_charts_are_generated_from_data(self):
        series, _ = qm.load_equity_curve(SAMPLE)
        vl = qm.vega_equity_curve(series)
        self.assertIn("vega-lite", vl["$schema"])
        self.assertEqual(len(vl["data"]["values"]), 2 * len(series["dates"]))
        dd = qm.vega_drawdown(series)
        self.assertTrue(all(v["value"] <= 0 for v in dd["data"]["values"]))
        mermaid = qm.mermaid_declaration_flow()
        self.assertTrue(mermaid.strip().splitlines()[-1].strip().startswith(("D", "H")))


if __name__ == "__main__":
    unittest.main()
