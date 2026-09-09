#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""42 M5.2 —— VERSION-MATRIX 一致性校验（版本×方案×能力，常驻 unittest）。"""
import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


class VersionMatrixTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / "VERSION-MATRIX.md").read_text(encoding="utf-8")
        cls.rows = [ln for ln in cls.text.splitlines()
                    if ln.startswith("| v") and "方案文件" not in ln]

    def test_matrix_has_rows(self):
        self.assertGreaterEqual(len(self.rows), 10)

    def test_rows_have_four_columns(self):
        for ln in self.rows:
            self.assertEqual(len(ln.split("|")) - 2, 4, ln)

    def test_scheme_files_exist(self):
        """方案列若带 .md 后缀须真实存在于根目录。"""
        missing = []
        for ln in self.rows:
            cells = [c.strip() for c in ln.split("|")[1:-1]]
            for token in re.findall(r"[A-Za-z0-9_.\-·/\u4e00-\u9fff]+\.md", cells[2]):
                if not (ROOT / token).exists():
                    missing.append(token)
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
