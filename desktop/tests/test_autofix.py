# -*- coding: utf-8 -*-
"""机械修复引擎单测（只改机械面；dry-run 不写盘；幂等）。"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import autofix  # noqa: E402


class TestAutofix(unittest.TestCase):
    def test_apply_rules_inserts_header_after_title(self):
        text = "# 标题\n\n正文\n"
        out = autofix.apply_rules(text, ["instruction_mark", "last_updated"],
                                  today="2026-09-14")
        lines = out.split("\n")
        self.assertEqual(lines[0], "# 标题")
        self.assertIn(autofix.INSTRUCTION_MARK, lines[1])
        self.assertEqual(lines[2], "> 最后更新：2026-09-14")
        self.assertIn("正文", out)

    def test_apply_rules_trailing_ws_and_final_newline(self):
        out = autofix.apply_rules("# T  \n正文   ", ["trailing_ws", "final_newline"])
        self.assertEqual(out, "# T\n正文\n")

    def test_apply_rules_idempotent(self):
        text = "# T\n> 最后更新：2026-09-14\n正文\n"
        once = autofix.apply_rules(text, ["instruction_mark", "last_updated"],
                                   today="2026-09-14")
        twice = autofix.apply_rules(once, ["instruction_mark", "last_updated"],
                                    today="2026-09-14")
        self.assertEqual(once, twice)

    def test_fix_file_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "a.md")
            p.write_text("# T  \n正文", encoding="utf-8")
            rep = autofix.fix_file(str(p), root=tmp, dry_run=True)
            self.assertTrue(rep["changed"])
            self.assertEqual(p.read_text(encoding="utf-8"), "# T  \n正文")

    def test_fix_file_applies_and_then_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "a.md")
            p.write_text("# T  \n正文", encoding="utf-8")
            first = autofix.fix_file(str(p), root=tmp, today="2026-09-14")
            self.assertTrue(first["changed"])
            self.assertEqual(p.read_text(encoding="utf-8"), "# T\n正文\n")
            second = autofix.fix_file(str(p), root=tmp)
            self.assertFalse(second["changed"])
            self.assertEqual(second["rules"], [])

    def test_lint_rules_detects_missing_final_newline(self):
        rules = [r["rule"] for r in autofix.lint_rules("x.md", "abc", root=".")]
        self.assertIn("final_newline", rules)


if __name__ == "__main__":
    unittest.main()
