#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 遗留常驻化：载荷注册表 / 资产密度·引用度·厚度 / 基线自描述 全部机检常驻。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import asset_density as ad  # noqa: E402
from core import payload_registry as pr  # noqa: E402
from core import quality_baseline as qb  # noqa: E402


class Quality45StandingTest(unittest.TestCase):
    def test_payload_registry_standing(self):
        issues, stats = pr.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["registered"], 25)
        self.assertGreaterEqual(stats["declared"], 5)

    def test_asset_standing(self):
        for fn in (ad.scan, ad.usage_scan, ad.thickness_scan):
            issues, stats = fn(ROOT)
            self.assertEqual(issues, [], fn.__name__)
        issues, stats = ad.usage_scan(ROOT)
        self.assertGreater(stats["total_refs"], 0)
        _, stats = ad.thickness_scan(ROOT)
        self.assertEqual(stats["low_files"], [])

    def test_baseline_standing(self):
        issues, stats = qb.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertEqual(stats["checks"], 31)


if __name__ == "__main__":
    unittest.main()
