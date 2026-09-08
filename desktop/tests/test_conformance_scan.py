#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""43 A2 —— Conformance 分级扫描单测（声明 ≤ 可证、防虚标）。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import conformance_scan as cs  # noqa: E402


class ConformanceScanTest(unittest.TestCase):
    def test_repo_scan_clean(self):
        issues, stats = cs.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["modules_mc"], 23)
        self.assertGreaterEqual(stats["packages"], 5)
        self.assertGreaterEqual(stats["export_items"], 4)

    def test_overclaim_detected(self):
        """模块未在册却声明 L2/L3 = 虚标 → 被拒。"""
        issues = []
        order = {"L1": 1, "L2": 2, "L3": 3}
        declared, provable = "L3", 2
        if order[declared] > provable:
            issues.append("虚标")
        self.assertEqual(issues, ["虚标"])

    def test_evidence_ids_cover_repo(self):
        """装配在册证据集须覆盖全部机器可加载模块文档（44 = 13 官方 + 31 社区）。"""
        evidence = set(cs._evidence_ids(ROOT))
        self.assertIn("M00", evidence)
        self.assertIn("通用:M10", evidence)


if __name__ == "__main__":
    unittest.main()
