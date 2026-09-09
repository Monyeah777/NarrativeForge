#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 A1 · 载荷证据扫描器单测（确定性 + 保守候选）。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import payload_evidence as pe  # noqa: E402


class PayloadEvidenceTest(unittest.TestCase):
    def test_repo_scan_deterministic_and_nonempty(self):
        c1 = pe.scan(ROOT)
        c2 = pe.scan(ROOT)
        self.assertEqual(c1, c2)
        self.assertTrue(c1)  # 至少一批候选供人工核验
        for sources in c1.values():
            for s in sources:
                self.assertIn("source", s)
                self.assertIn("fields", s)


if __name__ == "__main__":
    unittest.main()
