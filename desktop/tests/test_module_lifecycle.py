#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""40 总纲 v2.8 波B S5 —— 模块生命周期单测（status 位 + deprecate/restore + 引用门禁）。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from core import module_lifecycle as ml

MOD = """# 模块 M99 · 流转演示

> 类别：通用｜来源：测试｜挂载点：P20（active）｜依赖：M00｜被依赖：无

## 1. 职责

演示模块。
"""

REF = """# 模块 M88 · 引用方

> 类别：通用｜来源：测试｜挂载点：P20（active）｜依赖：M99｜被依赖：无

## 1. 职责

引用 M99。
"""


class StatusRoundTripTest(unittest.TestCase):
    def test_deprecate_then_restore(self):
        text = ml.set_status(MOD, "deprecated", reason="v2.8 流转战例演示")
        status, reason = ml.get_status(text)
        self.assertEqual(status, "deprecated")
        self.assertEqual(reason, "v2.8 流转战例演示")
        self.assertIn("状态：deprecated", text)
        text = ml.set_status(text, "active")
        status, reason = ml.get_status(text)
        self.assertEqual(status, "active")
        self.assertNotIn("deprecated", text)

    def test_default_status_active(self):
        status, reason = ml.get_status(MOD)
        self.assertEqual(status, "active")

    def test_bad_status_raises(self):
        with self.assertRaises(ValueError):
            ml.set_status(MOD, "unknown")

    def test_no_meta_line_raises(self):
        with self.assertRaises(ValueError):
            ml.set_status("# 模块 M99 · x\n正文", "deprecated")

    def test_module_id_from_title(self):
        self.assertEqual(ml.module_id_from_text(MOD), "M99")


class VerifyGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name

    def _write(self, rel, text):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_deprecated_referenced_by_active_is_issue(self):
        self._write("04_模块库/通用类/M99_流转演示.md", ml.set_status(MOD, "deprecated"))
        self._write("04_模块库/通用类/M88_引用方.md", REF)
        issues, stats = ml.verify_modules(self.root)
        self.assertTrue(any("M99" in i for i in issues), issues)
        self.assertEqual(stats["deprecated"], 1)

    def test_deprecated_standalone_passes(self):
        self._write("04_模块库/通用类/M99_流转演示.md", ml.set_status(MOD, "deprecated"))
        issues, stats = ml.verify_modules(self.root)
        self.assertEqual(issues, [])
        self.assertEqual(stats["deprecated"], 1)


if __name__ == "__main__":
    unittest.main()