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

ROOT = str(Path(__file__).resolve().parents[2])


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
            with open(path, encoding="utf-8") as fh:
                text = fh.read().replace("⛔ 操作指令：阅读即执行。\n", "", 1)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            issues = dh.check_markers(tmp)
            self.assertTrue(any("⛔ 操作指令" in i for i in issues), issues)

    def test_missing_last_updated_captured(self):
        with self._tmpdir() as tmp:
            self._minimal_tree(tmp)
            rel = dh.REQUIRED_DOCS[0]
            path = os.path.join(tmp, rel)
            with open(path, encoding="utf-8") as fh:
                text = fh.read().replace("> 最后更新：2026-09-08\n", "", 1)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            issues = dh.check_markers(tmp)
            self.assertTrue(any("最后更新" in i for i in issues), issues)

    def test_stale_warns_and_fresh_silent(self):
        with self._tmpdir() as tmp:
            self._minimal_tree(tmp, updated="2025-01-01")
            warns = dh.stale(tmp, month_limit=3, today="2026-09-08")
            self.assertTrue(warns)
            self._minimal_tree(tmp, updated="2026-09-01")
            self.assertEqual(dh.stale(tmp, month_limit=3, today="2026-09-08"), [])

    def test_text_sanity_flags_fence_and_mojibake(self):
        """正文正规性（WARN 级）：围栏未配平 / mojibake 特征各被抓到。"""
        with self._tmpdir() as tmp:
            _mk(tmp, "docs/clean.md", "# 干净\n\n```yaml\na: 1\n```\n\n正文\n")
            _mk(tmp, "docs/unbalanced.md", "# 未配平\n\n```yaml\na: 1\n\n正文不闭合\n")
            _mk(tmp, "docs/mojibake.md", "# 乱码\n\n管线 鏄鏂鐨涓鍦 鎶璁缂 正文\n")
            warns = dh.text_sanity(tmp)
            joined = "\n".join(warns)
            self.assertIn("围栏未配平", joined)
            self.assertIn("mojibake", joined)
            self.assertNotIn("clean.md", joined)

    def test_text_sanity_real_repo_counts_are_explicit(self):
        """真实仓库：正文正规性发现项显式可数（存量挂账；数量变化即需复核）。"""
        warns = dh.text_sanity(ROOT)
        self.assertTrue(all(w.startswith("WARN: ") for w in warns))
        # 存量按 WARN 挂账（不判死），但**当前为 0**：修复后本仓库不得再有
        # 围栏未配平 / mojibake 的正文——本断言即该不变量本身（新增漂移即红）。
        self.assertEqual(warns, [], "正文正规性缺口应已清零（围栏未配平 / mojibake）")

    def _tmpdir(self):
        import tempfile
        return tempfile.TemporaryDirectory()


if __name__ == "__main__":
    unittest.main()
