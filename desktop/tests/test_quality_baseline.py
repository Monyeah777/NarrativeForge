#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 W1 · 基线自描述一致性机检单测。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import quality_baseline as qb  # noqa: E402


class QualityBaselineTest(unittest.TestCase):
    def test_repo_scan_clean(self):
        issues, stats = qb.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertEqual(stats["verify_version"], "v2.22")
        self.assertEqual(stats["checks"], 32)

    def test_drift_detected_in_fake_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "verify.sh").write_text(
                "# 版本 : v2.19\ncheck1(){}\ncheck2(){}\n",
                encoding="utf-8")
            Path(tmp, "README.md").write_text("v2.19\n", encoding="utf-8")
            Path(tmp, "CHANGELOG.md").write_text(
                "## [2.9.0]\nPASS=49\n", encoding="utf-8")
            Path(tmp, "VERSION-MATRIX.md").write_text(
                "| v2.9.0（内容波收口） | PASS=49 |\n", encoding="utf-8")
            issues, stats = qb.scan(tmp)
            self.assertTrue(issues)
            self.assertNotEqual(stats["verify_version"], "v2.20")


if __name__ == "__main__":
    unittest.main()
