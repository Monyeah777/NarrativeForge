#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""44 追加 · 契约事件闭包扫描单测（元工具只报告不设闸 + 确定性）。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import closure_scan as cs  # noqa: E402


class ClosureScanTest(unittest.TestCase):
    def test_repo_scan_deterministic(self):
        issues1, s1 = cs.scan(ROOT)
        issues2, s2 = cs.scan(ROOT)
        self.assertEqual(issues1, [])
        self.assertEqual(s1, s2)
        self.assertGreaterEqual(s1["modules"], 20)
        self.assertGreaterEqual(len(s1["linked_events"]), 10)

    def test_orphan_side_reporting(self):
        """文本侧孤儿只报告并标注所在模块，不 FAIL——覆盖不设闸。

        L0 retro-fit 后社区模块的发布方可见，订阅侧孤儿面显著收敛
        （历史 ≥5 → 现 0）；本测固定的是「只报告」这一契约，不是孤儿数量。
        """
        issues, stats = cs.scan(ROOT)
        self.assertEqual(issues, [])
        for key in ("sub_only_events", "pub_only_events", "sub_only_by_module"):
            self.assertIn(key, stats)
        self.assertIsInstance(stats["sub_only_events"], list)
        self.assertIsInstance(stats["pub_only_events"], list)
        for module_ids in stats["sub_only_by_module"].values():
            self.assertIsInstance(module_ids, list)


if __name__ == "__main__":
    unittest.main()
