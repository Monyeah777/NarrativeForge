#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内容分级门单测（挂账收口）：词表真源 = 声明件；缺字段/越词表即 FAIL。"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import rating_gate as rg  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


class RatingGateTest(unittest.TestCase):
    def test_repo_library_is_rated(self):
        issues, stats = rg.scan(ROOT)
        self.assertEqual(issues, [], issues)
        self.assertGreaterEqual(stats["entries"], 3)
        self.assertIn("general", stats["vocabulary"])
        self.assertEqual(sum(stats["counts"].values()), stats["entries"],
                         "每条馆藏都须落入词表内")

    def test_vocabulary_comes_from_declaration(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "library"))
            with open(os.path.join(tmp, rg.INTAKE_REL), "w", encoding="utf-8",
                      newline="\n") as fh:
                json.dump({"schema": "nf-intake/1",
                           "rating": {"vocabulary": ["safe", "risky"]}}, fh)
            self.assertEqual(rg.vocabulary(tmp), ["safe", "risky"])
            issues, stats = rg.scan(tmp)
            self.assertEqual(stats["vocabulary"], ["safe", "risky"])
            self.assertTrue(any("缺 %s" % rg.INTAKE_REL in i or "ENTRIES" in i
                                for i in issues) or issues == [])

    def test_missing_rating_field_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "library"))
            with open(os.path.join(tmp, rg.INTAKE_REL), "w", encoding="utf-8",
                      newline="\n") as fh:
                json.dump({"schema": "nf-intake/1",
                           "rating": {"vocabulary": ["general", "teen", "mature",
                                                     "unrated"]}}, fh)
            with open(os.path.join(tmp, "library", "NF-9.md"), "w", encoding="utf-8",
                      newline="\n") as fh:
                fh.write("---\nid: NF-9\ntitle: 无分级样例\nlicense: MIT\nstatus: active\n---\n\n正文\n")
            issues, _ = rg.scan(tmp)
            self.assertTrue(any("缺 frontmatter `rating`" in i for i in issues), issues)

    def test_out_of_vocabulary_rating_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "library"))
            with open(os.path.join(tmp, rg.INTAKE_REL), "w", encoding="utf-8",
                      newline="\n") as fh:
                json.dump({"schema": "nf-intake/1",
                           "rating": {"vocabulary": ["general", "teen"]}}, fh)
            with open(os.path.join(tmp, "library", "NF-9.md"), "w", encoding="utf-8",
                      newline="\n") as fh:
                fh.write("---\nid: NF-9\ntitle: 越词表样例\nrating: extreme\n"
                         "license: MIT\nstatus: active\n---\n\n正文\n")
            issues, _ = rg.scan(tmp)
            self.assertTrue(any("越词表" in i for i in issues), issues)

    def test_index_projects_rating_column(self):
        text = Path(ROOT, "library", "INDEX.md").read_text(encoding="utf-8")
        self.assertIn("| 许可 | 分级 |", text, "登记表须投影分级列（真源 = 条目 frontmatter）")
        summary = rg.summary(rg.scan(ROOT)[1])
        self.assertIn("馆藏", summary)
        self.assertIn("词表", summary)


if __name__ == "__main__":
    unittest.main()
