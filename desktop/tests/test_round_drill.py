#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 A2 · 回合级 drill 单测（引用/推进/编造/跳号）。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import round_drill as rd  # noqa: E402


ALLOWED = ["M00", "通用:M10", "M80"]


class RoundDrillTest(unittest.TestCase):
    def _good(self):
        return ("回合 1：引用 06 §3 推进，M00 写回 状态快照。\n"
                "回合 2：第 2 回合，引用 06 §3，M80 输出并进入下一回合。\n")

    def test_good_transcript_passes(self):
        issues, stats = rd.scan(self._good(), ALLOWED)
        self.assertEqual(issues, [])
        self.assertEqual(stats["turns"], 2)

    def test_missing_citation_captured(self):
        bad = "回合 1：推进状态，无引用。\n"
        issues, _ = rd.scan(bad, ALLOWED)
        self.assertTrue(any("缺引用" in i for i in issues))

    def test_fabricated_id_captured(self):
        bad = "回合 1：引用 06 §3 由 M99 推进并写回。\n"
        issues, _ = rd.scan(bad, ALLOWED)
        self.assertTrue(any("M99" in i for i in issues))


if __name__ == "__main__":
    unittest.main()
