#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""性能预算（`core/perf_budget.py`）回归测试 —— ISO 25010 性能效率面。

全部用注入计时器 + 临时根；不依赖真实耗时与工作区状态。
"""
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import perf_budget as pb  # noqa: E402


def _decl(tmp: str, entries, evidence=None) -> None:
    p = Path(tmp) / pb.DECL_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"schema": pb.SCHEMA, "note": "t", "reference_host": "test",
                             "entries": entries, "evidence": evidence or {}},
                            ensure_ascii=False), encoding="utf-8")


ONE = [{"id": "x", "cmd": "python -c pass", "budget_ms": 100, "runs": 3, "max_age_days": 7}]


class LoadTest(unittest.TestCase):
    def test_missing_declaration_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, _w, _s = pb.scan(tmp)
        self.assertTrue(any(pb.DECL_REL in i and "修复指引" in i for i in issues), issues)

    def test_empty_entries_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, [])
            issues, _w, _s = pb.scan(tmp)
        self.assertTrue(any("entries" in i for i in issues), issues)


class ScanTest(unittest.TestCase):
    def test_missing_record_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE)
            issues, _w, _s = pb.scan(tmp)
        self.assertTrue(any("无实测记录" in i for i in issues), issues)

    def test_over_budget_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE, {"x": {"median_ms": 250, "measured_at": dt.date.today().isoformat()}})
            issues, _w, stats = pb.scan(tmp)
        self.assertTrue(any("超预算" in i and "250" in i for i in issues), issues)
        self.assertEqual(1, stats["over_budget"])

    def test_within_budget_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE, {"x": {"median_ms": 80, "measured_at": dt.date.today().isoformat()}})
            issues, _w, _s = pb.scan(tmp)
        self.assertEqual([], issues)

    def test_stale_record_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = (dt.date.today() - dt.timedelta(days=30)).isoformat()
            _decl(tmp, ONE, {"x": {"median_ms": 80, "measured_at": old}})
            issues, _w, _s = pb.scan(tmp)
        self.assertTrue(any("过期" in i for i in issues), issues)

    def test_undeclared_record_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE, {"x": {"median_ms": 80, "measured_at": dt.date.today().isoformat()},
                             "ghost": {"median_ms": 1, "measured_at": dt.date.today().isoformat()}})
            issues, _w, _s = pb.scan(tmp)
        self.assertTrue(any("ghost" in i for i in issues), issues)

    def test_exit_code_is_not_judged(self):
        """性能面只看耗时与新鲜度；正确性归 verify_report——故 exit_code 非 0 不该 FAIL。"""
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE, {"x": {"median_ms": 50, "exit_code": 1,
                                   "measured_at": dt.date.today().isoformat()}})
            issues, _w, _s = pb.scan(tmp)
        self.assertEqual([], issues)


class RecordTest(unittest.TestCase):
    def test_record_writes_median_and_scan_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE)
            bad, doc = pb.record(tmp, only="all", runner=lambda cmd, n: (0, [90, 110, 70]))
            rec = doc["evidence"]["x"]
            self.assertEqual(90, rec["median_ms"], "中位数须取排序后中位（70,90,110 → 90）")
            self.assertEqual(70, rec["min_ms"])
            self.assertEqual(110, rec["max_ms"])
            self.assertEqual([], bad)
            issues, _w, _s = pb.scan(tmp)
        self.assertEqual([], issues)

    def test_record_reports_over_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE)
            bad, _doc = pb.record(tmp, only="all", runner=lambda cmd, n: (0, [500, 500, 500]))
        self.assertEqual(["x"], bad)

    def test_record_only_filters(self):
        two = [dict(ONE[0], id="a"), dict(ONE[0], id="b")]
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, two)
            _bad, doc = pb.record(tmp, only="a", runner=lambda cmd, n: (0, [10]))
        self.assertIn("a", doc["evidence"])
        self.assertNotIn("b", doc["evidence"])


class RealRepoTest(unittest.TestCase):
    def test_declaration_committed_with_evidence(self):
        p = ROOT / pb.DECL_REL
        self.assertTrue(p.is_file(), "须提交性能预算声明：%s" % pb.DECL_REL)
        doc = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(pb.SCHEMA, doc["schema"])
        self.assertGreaterEqual(len(doc["entries"]), 3, "至少声明 3 个性能目标")
        for e in doc["entries"]:
            self.assertTrue(e.get("id") and e.get("cmd") and float(e.get("budget_ms") or 0) > 0,
                            "每条须有 id/cmd/budget_ms：%s" % e)


if __name__ == "__main__":
    unittest.main()
