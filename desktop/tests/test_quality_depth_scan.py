#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 check32 · 质量纵深汇总扫描单测。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import quality_depth_scan as qds  # noqa: E402


class QualityDepthScanTest(unittest.TestCase):
    def test_repo_clean(self):
        issues, stats = qds.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertIn("payload_registry", stats)
        self.assertIn("asset_ledger", stats)
        self.assertIn("payload_consumer", stats)
        self.assertIn("tool_face", stats)
        self.assertIn("world_model", stats)
        self.assertIn("world_slots", stats)


if __name__ == "__main__":
    unittest.main()
