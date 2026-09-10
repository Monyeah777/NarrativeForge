#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""world_slots 注册表扫描器单测。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import world_slots as ws  # noqa: E402


class WorldSlotsTest(unittest.TestCase):
    def test_repo_scan_clean(self):
        issues, stats = ws.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["slots"], 1)

    def test_bad_kind_fails(self):
        data = {
            "schema_version": "1",
            "slots": {"x": {"kind": "bad", "owner": "M50"}},
        }
        self.assertTrue(any("非法类型" in i for i in ws.validate_registry(data)))

    def test_item_kind_only_array_fails(self):
        data = {
            "schema_version": "1",
            "slots": {"x": {"kind": "string", "owner": "M50", "item_kind": "string"}},
        }
        self.assertTrue(any("仅 kind=array 可用" in i for i in ws.validate_registry(data)))

    def test_missing_owner_fails(self):
        data = {
            "schema_version": "1",
            "slots": {"x": {"kind": "string"}},
        }
        self.assertTrue(any("owner" in i for i in ws.validate_registry(data)))


if __name__ == "__main__":
    unittest.main()
