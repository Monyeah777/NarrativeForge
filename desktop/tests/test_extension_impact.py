#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""43 A3 —— 扩展策略 + nf diff 影响度三档单测。"""
import os
import unittest

import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import knowledge_sig as ks  # noqa: E402


def _sig(**over):
    base = {
        "path": "01_核心协议.md",
        "kind": "方案文档",
        "doc_id": "01",
        "title": "核心协议",
        "version": "",
        "self_id": "",
        "layer": "",
        "category": "",
        "heading_count": 9,
        "meta_line_count": 1,
        "line_count": 200,
        "body_hash": "a",
        "headings": ["## 1", "## 2"],
        "schema_names": [],
        "refs": ["02_联动注册表.md"],
    }
    base.update(over)
    return base


class ImpactTierTest(unittest.TestCase):
    def test_editorial(self):
        a = _sig()
        b = _sig(body_hash="b", line_count=201)
        diff = ks.diff_signatures(a, b)
        self.assertEqual(diff["impact"], "editorial")
        self.assertEqual(diff["verdict"], "兼容")

    def test_additive(self):
        a = _sig()
        b = _sig(refs=["02_联动注册表.md", "03_管线库/P01.md"])
        diff = ks.diff_signatures(a, b)
        self.assertEqual(diff["impact"], "additive")

    def test_bump_removal(self):
        a = _sig(headings=["## 1", "## 2"])
        b = _sig(headings=["## 1"])
        diff = ks.diff_signatures(a, b)
        self.assertEqual(diff["impact"], "bump")
        self.assertIn("需评审", diff["verdict"])

    def test_bump_docid(self):
        a = _sig(doc_id="01")
        b = _sig(doc_id="01a")
        diff = ks.diff_signatures(a, b)
        self.assertEqual(diff["impact"], "bump")


class ExtensionDocTest(unittest.TestCase):
    def test_extension_policy_present(self):
        text = open(os.path.join(ROOT, "protocol", "EXTENSION.md"), encoding="utf-8").read()
        for marker in ("字段级新增", "结构性", "迁移记录", "bump", "additive", "editorial"):
            self.assertIn(marker, text)
        # 三档回放实证：3+1 例标题在场
        self.assertGreaterEqual(text.count("| bump |"), 2)
        self.assertGreaterEqual(text.count("| additive |"), 2)


if __name__ == "__main__":
    unittest.main()
