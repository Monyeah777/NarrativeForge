#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 · tool_face 扫描器单测。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import tool_face as tf  # noqa: E402


class ToolFaceTest(unittest.TestCase):
    def test_repo_has_first_battle_case(self):
        issues, stats = tf.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertEqual(stats["modules"], 1)
        self.assertGreaterEqual(stats["entries"], 1)
        self.assertGreaterEqual(stats["candidates"], 1)

    def test_missing_license_captured(self):
        issues = tf.validate_entry({
            "purpose": "x",
            "guidance": {"a": "b"},
            "candidates": [{"repo": "https://example.com/repo", "ref": "1.0"}],
        })
        self.assertTrue(any("license" in i for i in issues))


if __name__ == "__main__":
    unittest.main()
