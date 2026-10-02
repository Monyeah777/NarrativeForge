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

    def test_command_face_accepts_argparse_aliases(self):
        """**别名也是命令面**（2026-10-01 修）。

        取证：注册表由 `sub.add_parser("name"` 正则而来，**只认主名**；而
        `add_parser("shell", aliases=["terminal"])` 的 `nf terminal` 是 argparse 真能跑的
        命令（`nf shell --commands` 里也确在册）⇒ 文档写别名反被判「不是 CLI 子命令」，
        本仓 `docs/terminal.md` 就这么被误红过一次。本件把「别名进注册表」钉住。
        """
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "scripts"))
            with open(os.path.join(tmp, "scripts", "nf.py"), "w", encoding="utf-8") as fh:
                fh.write('sub.add_parser("shell", aliases=["terminal"])\n')
            with open(os.path.join(tmp, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("入口：`nf shell`，别名 `nf terminal`。\n")
            issues, stats = pl.command_face(tmp)
            self.assertEqual(issues, [], issues)
            self.assertEqual(stats["commands_checked"], 2)


class PunctMixPrecisionTest(unittest.TestCase):
    """`punct_mix` 降噪（2026-09-30）：只报**真·中英标点混用**，两类假阳性豁免。

    实测：`nf lint --prose` 全仓 13 条命中里 7 条是假阳性——行内代码里的 `通用:M10` /
    `--context "C6:<slug>; 澄清稿:…"`、以及正文里的模块 id 语法，都被当成「中英标点混用」。
    """

    def _rules(self, text):
        return [h["rule"] for h in pl.lint_text(text)]

    def test_id_syntax_is_exempt(self):
        self.assertNotIn("punct_mix",
                         self._rules("重号模块以类别前缀限定（通用:M10 vs 生存:M10）"))

    def test_inline_code_is_exempt(self):
        self.assertNotIn("punct_mix",
                         self._rules('命令示例 `--context "C6:$slug; 澄清稿:docs/x.md"` 里的冒号'))

    def test_real_mixed_punctuation_is_still_caught(self):
        self.assertIn("punct_mix", self._rules("这一步做完,再进入下一步"))

    def test_fullwidth_punctuation_is_clean(self):
        self.assertNotIn("punct_mix", self._rules("口径：三件齐备。"))


if __name__ == "__main__":
    unittest.main()
