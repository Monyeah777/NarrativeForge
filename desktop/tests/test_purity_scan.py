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


if __name__ == "__main__":
    unittest.main()
