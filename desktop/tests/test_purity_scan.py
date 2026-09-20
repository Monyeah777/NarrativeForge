#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""42 M3 —— 纯度体检 check27 单测（四规则 + 变异注入捕获力 = check 的 check）。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import purity_scan as ps  # noqa: E402


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class PurityScanTest(unittest.TestCase):
    def test_mutation_r1_end_shell_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "02_联动注册表.md", "# 注册表\n\nandroid 残留行\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("端壳/APK 残留" in i for i in issues), issues)

    def test_mutation_r2_private_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "01_核心协议.md", "# 协议\n\n临时路径 C:\\Users\\x\\tmp 残留\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("私货/可变物" in i for i in issues), issues)

    def test_mutation_r3_dup_heading_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "06_Agent执行协议.md",
                   "# A\n## 回合执行\n## 回合执行\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("重复标题" in i for i in issues), issues)

    def test_mutation_r4_raise_no_guidance_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/bad.py",
                   'def f():\n    raise ValueError("oops")\n')
            issues, stats = ps.scan(tmp)
            self.assertTrue(any("raise 消息缺修复指引" in i for i in issues), issues)
            self.assertEqual(stats["raises"], 1)

    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "01_核心协议.md", "# 协议\n## 模块协议\n")
            _write(tmp, "02_联动注册表.md", "# 注册表\n## 模块表\n")
            _write(tmp, "06_Agent执行协议.md", "# 执行\n## 回合执行\n")
            _write(tmp, "07_官方核心出厂与社区预设导航.md", "# 导航\n## 包索引\n")
            _write(tmp, "desktop/src/core/ok.py",
                   'def f():\n    raise ValueError("请先补 x 再继续")\n')
            issues, _ = ps.scan(tmp)
            self.assertEqual(issues, [])

    def test_mutation_r5_unregistered_third_party_captured(self):
        """R5：未登记的第三方硬 import 被抓（core/scripts 面）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/bad.py", "import requests\n")
            issues, stats = ps.scan(tmp)
            self.assertTrue(any("第三方 import 未登记" in i for i in issues), issues)
            self.assertGreaterEqual(stats["imports"], 1)

    def test_r5_soft_declared_and_hard_allowed_pass(self):
        """R5：软导入 + 登记（jsonschema）与硬依赖白名单（yaml）都放行。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/ok.py",
                   "import yaml\n"
                   "try:\n"
                   "    from jsonschema import Draft202012Validator\n"
                   "except ImportError:\n"
                   "    Draft202012Validator = None\n")
            issues, _ = ps.scan(tmp)
            self.assertEqual(issues, [])

    def test_r5_declared_soft_import_without_guard_is_caught(self):
        """R5：已登记的软依赖若**裸导入**（无守卫）仍判 FAIL——登记不等于免守卫。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/bad.py", "from PySide6.QtGui import QImage\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("未软导入" in i for i in issues), issues)

    def test_r5_residue_is_warn_not_fail(self):
        """R5：登记在 IMPORT_RESIDUE 的存量残留走 WARN 挂账（不判死但不得隐身）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "scripts/selftest_android.py", "from app.controller import Controller\n")
            issues, stats = ps.scan(tmp)
            self.assertEqual(issues, [])
            self.assertTrue(any("残留" in w for w in stats["import_residue"]), stats)


if __name__ == "__main__":
    unittest.main()
