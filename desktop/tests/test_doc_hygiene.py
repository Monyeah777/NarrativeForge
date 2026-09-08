#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""42 M4 —— 文档可执行性卫生检查单测（标识/last-updated/过期告警 + 变异注入）。"""
import os
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import doc_hygiene as dh  # noqa: E402


def _mk(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class DocHygieneTest(unittest.TestCase):
    def _minimal_tree(self, tmp, updated="2026-09-08"):
        for rel in dh.REQUIRED_DOCS:
            mark = ""
            if rel in dh.INSTRUCTION_DOCS:
                mark = "> ⛔ 操作指令：阅读即执行。\n"
            _mk(tmp, rel, "# %s\n%s> 最后更新：%s\n\n正文\n"
                % (rel, mark, updated))

    def test_markers_present_passes(self):
        with self._tmpdir() as tmp:
            self._minimal_tree(tmp)
            issues = dh.check_markers(tmp)
            self.assertEqual(issues, [])

    def test_missing_instruction_mark_captured(self):
        with self._tmpdir() as tmp:
            self._minimal_tree(tmp)
            rel = dh.INSTRUCTION_DOCS[0]
            path = os.path.join(tmp, rel)
            text = open(path, encoding="utf-8").read().replace(
                "⛔ 操作指令：阅读即执行。\n", "", 1)
            open(path, "w", encoding="utf-8").write(text)
            issues = dh.check_markers(tmp)
            self.assertTrue(any("⛔ 操作指令" in i for i in issues), issues)

    def test_missing_last_updated_captured(self):
        with self._tmpdir() as tmp:
            self._minimal_tree(tmp)
            rel = dh.REQUIRED_DOCS[0]
            path = os.path.join(tmp, rel)
            text = open(path, encoding="utf-8").read().replace(
                "> 最后更新：2026-09-08\n", "", 1)
            open(path, "w", encoding="utf-8").write(text)
            issues = dh.check_markers(tmp)
            self.assertTrue(any("最后更新" in i for i in issues), issues)

    def test_stale_warns_and_fresh_silent(self):
        with self._tmpdir() as tmp:
            self._minimal_tree(tmp, updated="2025-01-01")
            warns = dh.stale(tmp, month_limit=3, today="2026-09-08")
            self.assertTrue(warns)
            self._minimal_tree(tmp, updated="2026-09-01")
            self.assertEqual(dh.stale(tmp, month_limit=3, today="2026-09-08"), [])

    def _tmpdir(self):
        import tempfile
        return tempfile.TemporaryDirectory()


if __name__ == "__main__":
    unittest.main()
