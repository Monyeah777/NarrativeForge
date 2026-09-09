#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 #2 · 资产键表机读投影单测。"""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import asset_ledger_projection as alp  # noqa: E402


class AssetLedgerProjectionTest(unittest.TestCase):
    def test_repo_ledger_clean_and_deterministic(self):
        issues, stats = alp.verify(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["entries"], 100)
        a = alp.build(ROOT)
        self.assertEqual(a, alp.build(ROOT))

    def test_each_entry_has_key_package_file_line(self):
        for e in alp.build(ROOT):
            for f in ("key", "package", "file", "line"):
                self.assertIn(f, e)


if __name__ == "__main__":
    unittest.main()
