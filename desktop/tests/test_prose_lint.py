# -*- coding: utf-8 -*-
"""正文级 lint 单测（AI 味机械特征；只报告不阻断）。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import prose_lint as pl  # noqa: E402


def rules(text):
    return {f["rule"] for f in pl.lint_text(text)}


class TestProseLint(unittest.TestCase):
    def test_cliche_and_summary_and_lecture(self):
        text = ("在这个时代里，一切都变得不同。\n"
                "我们应该记住那些名字。\n"
                "总而言之，事情就是这样。\n")
        got = rules(text)
        self.assertIn("cliche_open", got)
        self.assertIn("lecture_tone", got)
        self.assertIn("summary_tail", got)

    def test_binary_parallel_and_triple_adj(self):
        text = "他不是害怕，而是犹豫。\n春和景明、秋高气爽、冬雪皑皑，四季轮转。\n"
        got = rules(text)
        self.assertIn("binary_parallel", got)
        self.assertIn("triple_adj", got)

    def test_punct_mix_detected(self):
        self.assertIn("punct_mix", rules("他说完后,没有回头。\n"))

    def test_repeat_connector_detected(self):
        text = "然而雨还是下了。\n天气很闷。\n然而他没有回头。\n"
        self.assertIn("repeat_connector", rules(text))

    def test_hedge_overuse(self):
        text = "他似乎可能大概也许或许仿佛大概似乎可能看见了什么。\n"
        self.assertIn("hedge_overuse", rules(text))
        self.assertNotIn("hedge_overuse",
                         rules("他看见了什么。\n", ))

    def test_code_fence_and_headings_skipped(self):
        text = "# 标题\n\n```\n总而言之我们应该在某种程度上\n```\n\n正文。\n"
        self.assertEqual(pl.lint_text(text), [])

    def test_findings_addressable_and_summarized(self):
        text = "总而言之，我们应该谨慎。\n"
        found = pl.lint_text(text)
        self.assertTrue(found)
        for f in found:
            self.assertIn("line", f)
            self.assertGreaterEqual(f["line"], 1)
        counts = pl.summarize(found)
        self.assertEqual(sum(counts.values()), len(found))


    def test_command_face_flags_unknown_cli_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "scripts"))
            with open(os.path.join(tmp, "scripts", "nf.py"), "w", encoding="utf-8") as fh:
                fh.write('sub.add_parser("doctor")\nsub.add_parser("market")\n')
            with open(os.path.join(tmp, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("跑 `python scripts/nf.py doctor` 自检；`nf market --list` 看货架。\n")
            issues, stats = pl.command_face(tmp)
            self.assertEqual(issues, [], issues)
            self.assertEqual(stats["commands_checked"], 2)
            with open(os.path.join(tmp, "README.md"), "a", encoding="utf-8") as fh:
                fh.write("另见 `nf doctorr`。\n")
            issues2, _ = pl.command_face(tmp)
            self.assertTrue(any("doctorr" in i for i in issues2), issues2)

    def test_command_face_ignores_prose_mentions(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "scripts"))
            with open(os.path.join(tmp, "scripts", "nf.py"), "w", encoding="utf-8") as fh:
                fh.write('sub.add_parser("doctor")\n')
            with open(os.path.join(tmp, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("NF doctor 这一节是散文里的词，不是命令片段。\n")
            issues, stats = pl.command_face(tmp)
            self.assertEqual(issues, [], issues)
            self.assertEqual(stats["commands_checked"], 0)

    def test_command_face_flags_unknown_mcp_tool(self):
        tmp = str(Path(__file__).resolve().parents[2])
        issues, _ = pl.command_face(tmp)
        self.assertEqual(issues, [], "本仓文档命令面须零漂移：%s" % issues[:3])


if __name__ == "__main__":
    unittest.main()
