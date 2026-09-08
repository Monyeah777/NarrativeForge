#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.8.0 波C C4 —— 图书馆 See-Also related_of 单测（41 规划人读关联层）。"""
import os
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.market_analyzer import related_of  # noqa: E402


PROTS = {
    "官方核心基础包": {
        "id": "官方核心基础包", "module_ids": ["M00", "M90", "M80"], "references": []},
    "技术文档域包": {
        "id": "技术文档域包", "module_ids": ["M97", "M98"],
        "references": [{"source_package": "官方核心基础包"}]},
    "校园情感领域包": {
        "id": "校园情感领域包", "module_ids": ["情感:M22", "M40"], "references": []},
}


class RelatedOfTest(unittest.TestCase):
    def test_package_see_also_refs(self):
        r = related_of("技术文档域包", PROTS)
        self.assertEqual(r["kind"], "package")
        self.assertIn("官方核心基础包", r["refs"])

    def test_module_owners(self):
        r = related_of("M90", PROTS)
        self.assertEqual(r["kind"], "module")
        self.assertIn("官方核心基础包", r["related_modules"])

    def test_unknown_target(self):
        r = related_of("不存在", PROTS)
        self.assertEqual(r["refs"], [])
        self.assertEqual(r["referenced_by"], [])


if __name__ == "__main__":
    unittest.main()
