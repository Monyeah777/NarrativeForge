#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 · pipeline_loader 单测（官方管线装载 + 缺件拒绝）。"""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import pipeline_loader as pl  # noqa: E402


class PipelineLoaderTest(unittest.TestCase):
    def test_load_official_p01(self):
        pipe = pl.load_pipeline_file(str(ROOT / "03_管线库" / "P01_标准管线.md"))
        self.assertIsNotNone(pipe)
        self.assertEqual(pipe.id, "P01")

    def test_missing_file_returns_none(self):
        self.assertIsNone(pl.load_pipeline_file(str(ROOT / "no_such.md")))


if __name__ == "__main__":
    unittest.main()
