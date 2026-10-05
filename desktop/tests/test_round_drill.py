#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 A2 · 回合级 drill 单测（引用/推进/编造/跳号）。"""
import os
import json
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import round_drill as rd  # noqa: E402


ALLOWED = ["M00", "通用:M10", "M80"]


class RoundDrillTest(unittest.TestCase):
    def _fixture(self, name):
        with open(os.path.join(ROOT, "desktop", "tests", "fixtures",
                               "execution", "rounds", name),
                  encoding="utf-8") as fh:
            return json.load(fh)

    def test_good_transcript_passes(self):
        fx = self._fixture("good.json")
        issues, stats = rd.scan(fx["transcript"], fx["allowed"])
        self.assertEqual(issues, [])
        self.assertEqual(stats["turns"], 2)

    def test_missing_citation_captured(self):
        fx = self._fixture("bad.json")
        issues, _ = rd.scan(fx["transcript"], fx["allowed"])
        self.assertTrue(any("缺引用" in i for i in issues))

    def test_fabricated_id_captured(self):
        fx = self._fixture("bad.json")
        issues, _ = rd.scan(fx["transcript"], fx["allowed"])
        self.assertTrue(any("M99" in i for i in issues))

    def test_missing_progress_captured(self):
        """R-R2：有引用与真实编号但无推进/状态留痕 → 捕获。"""
        fx = self._fixture("bad_r2.json")
        issues, _ = rd.scan(fx["transcript"], fx["allowed"])
        self.assertTrue(any("无推进" in i for i in issues), issues)

    def test_cross_pipeline_id_captured(self):
        """R-R3：允许集外编号（M99）→ 捕获。"""
        fx = self._fixture("bad_r3.json")
        issues, _ = rd.scan(fx["transcript"], fx["allowed"])
        self.assertTrue(any("M99" in i for i in issues), issues)

    def test_turn_gap_is_warn_not_fail(self):
        """R-R4：跳号只入 WARN 清单，不产生 FAIL 级 issue。"""
        fx = self._fixture("gap_ok.json")
        issues, stats = rd.scan(fx["transcript"], fx["allowed"])
        self.assertEqual(issues, [])
        self.assertEqual(stats["warn_gaps"], [(1, 3)])


if __name__ == "__main__":
    unittest.main()
