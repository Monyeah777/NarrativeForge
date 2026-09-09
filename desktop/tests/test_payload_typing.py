#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 #1 · 载荷类型收窄工具单测（证据型机械规则）。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import payload_typing as pt  # noqa: E402


class PayloadTypingTest(unittest.TestCase):
    def test_proposal_deterministic(self):
        p1 = pt.propose(ROOT)
        p2 = pt.propose(ROOT)
        self.assertEqual(p1, p2)
        self.assertGreaterEqual(len(p1["events"]), 25)

    def test_scan_clean(self):
        issues, stats = pt.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertIn("proposal-only", stats["status"])


if __name__ == "__main__":
    unittest.main()
