# -*- coding: utf-8 -*-
"""基线相对回归评分单测（绝对门之上的 no-silent-worsening 面）。"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import regression_score as rs  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


def _sig(name, value, weight=0.5):
    return {"name": name, "weight": weight, "value": value, "note": ""}


class TestRegressionScore(unittest.TestCase):
    def test_evaluate_bounded_and_reproducible(self):
        """真实仓库：分值有界且两遍一致（可复现 = 可作基线）。"""
        a = rs.evaluate(ROOT)
        b = rs.evaluate(ROOT)
        self.assertGreaterEqual(a["score"], 0.0)
        self.assertLessEqual(a["score"], 100.0)
        self.assertEqual(a["score"], b["score"])
        self.assertEqual(a["signals"], b["signals"])
        self.assertEqual(a["schema"], "nf-score/1")

    def test_scanner_unavailable_is_not_zero_issues(self):
        """逐行审查回归：扫描器不可用**不得**当零问题（fail-closed），且要记 issues。

        修前行为：`_count` 异常一律 `return 0` → 该信号满分 → 总分不变（坏扫描器 = 假绿）。
        """
        from core import quality_depth_scan as qd
        base = rs.evaluate(ROOT)
        orig = qd.scan
        qd.scan = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            bad = rs.evaluate(ROOT)
        finally:
            qd.scan = orig
        self.assertLess(bad["score"], base["score"], "扫描器坏掉必须让分值下降")
        self.assertTrue(any("扫描器不可用" in i for i in bad["issues"]), bad["issues"])
        sig = {s["name"]: s["value"] for s in bad["signals"]}
        self.assertEqual(sig["depth_clean"], 0.0, "不可用 = 0 分，不是满分")

    def test_compare_flags_signal_regression(self):
        """单信号回落 → 判回归（即便整体分数靠其它信号撑住）。"""
        base = {"score": 90.0, "signals": [_sig("a", 1.0), _sig("b", 1.0)]}
        cur = {"score": 95.0, "signals": [_sig("a", 1.0), _sig("b", 0.5)]}
        out = rs.compare(cur, base)
        self.assertFalse(out["ok"])
        self.assertEqual([r["signal"] for r in out["regressed"]], ["b"])
        self.assertGreater(out["delta"], 0)

    def test_compare_tolerance_allows_small_drop(self):
        """整体小幅下降在容差内且无单信号回落 → 通过。"""
        base = {"score": 90.0, "signals": [_sig("a", 1.0)]}
        cur = {"score": 89.5, "signals": [_sig("a", 1.0)]}
        self.assertTrue(rs.compare(cur, base, tolerance=1.0)["ok"])
        self.assertFalse(rs.compare(cur, base, tolerance=0.1)["ok"])

    def test_compare_exception_is_auditable(self):
        """审计例外：标注理由后放行，但仍列在 exempted（不隐藏回归）。"""
        base = {"score": 90.0, "signals": [_sig("a", 1.0)]}
        cur = {"score": 88.0, "signals": [_sig("a", 0.8)]}
        out = rs.compare(cur, base, exceptions=[
            {"signal": "a", "reason": "已立项修复，本波放行"}])
        self.assertTrue(out["ok"])
        self.assertEqual(out["regressed"], [])
        self.assertEqual(out["exempted"][0]["signal"], "a")
        self.assertIn("审计例外", out["verdict"])

    def test_missing_baseline_reports_only(self):
        cur = rs.evaluate(ROOT)
        out = rs.compare(cur, {"schema": "nf-score/1"})
        self.assertIn("无基线", out["verdict"])

    def test_save_load_roundtrip(self):
        ev = rs.evaluate(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            p = str(Path(tmp, "b.json"))
            rs.save_baseline(p, ev, recorded_at="2026-09-14", note="t")
            loaded = rs.load_baseline(p)
            self.assertEqual(loaded["score"], ev["score"])
            self.assertTrue(rs.compare(ev, loaded)["ok"])


if __name__ == "__main__":
    unittest.main()
