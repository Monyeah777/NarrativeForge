#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 W3 · 资产键语义密度体检单测。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import asset_density as ad  # noqa: E402


class AssetDensityTest(unittest.TestCase):
    def test_repo_scan_clean(self):
        issues, stats = ad.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["files"], 30)
        self.assertGreater(stats["keys"], 20)

    def test_empty_asset_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "community", "demo", "assets")
            d.mkdir(parents=True)
            (d / "EMPTY.md").write_text("\n", encoding="utf-8")
            issues, _ = ad.scan(tmp)
            self.assertTrue(any("空档" in i for i in issues))

    def test_thickness_repo(self):
        issues, stats = ad.thickness_scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["files"], 30)
        self.assertEqual(stats["low_files"], [])


if __name__ == "__main__":
    unittest.main()
