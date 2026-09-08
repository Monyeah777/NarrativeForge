#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.8.0 波C D2 —— scripts/nf.py CLI 层自动化测试（41 规划 D 组收口杂务）。

覆盖子命令参数面与装配链 smoke（替代手工冒烟；不依赖 GUI/端壳）。
"""
import argparse
import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("nfcli", ROOT / "scripts" / "nf.py")
nf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nf)


class NfCliSmokeTest(unittest.TestCase):
    @staticmethod
    def _run(argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = nf.main(list(argv))
        return code, out.getvalue()

    def _subcommands(self):
        p = nf._build_parser()
        for a in p._actions:
            if isinstance(a, argparse._SubParsersAction):
                return set(a.choices)
        return set()

    def test_wave_c_subcommands_exposed(self):
        cmds = self._subcommands()
        for c in ("sig", "diff", "explain", "related", "pipeline", "module", "demo"):
            self.assertIn(c, cmds)

    def test_sig_verify(self):
        code, out = self._run(["sig", "--verify"])
        self.assertEqual(code, 0)
        self.assertIn("可复现", out)

    def test_explain_check25(self):
        code, out = self._run(["explain", "25"])
        self.assertEqual(code, 0)
        self.assertIn("check25", out)

    def test_market_list(self):
        code, out = self._run(["market", "--list"])
        self.assertEqual(code, 0)
        self.assertIn("包", out)

    def test_related_techdoc(self):
        code, out = self._run(["related", "技术文档域包"])
        self.assertEqual(code, 0)
        self.assertIn("官方核心", out)

    def test_diff_01_vs_36(self):
        """nf diff 冒烟：01 核心协议 vs 36 方案 → 判定行在场（C2 差异检测）。"""
        code, out = self._run(["diff", "01_核心协议.md",
                               "36_v2.5.0_基础层深化续方案.md"])
        self.assertEqual(code, 0)
        self.assertIn("判定", out)

    def test_related_m90_reverse(self):
        """nf related 冒烟：M90 反向引用方（M2 校验 P03 drill 之外的人读链）。"""
        code, out = self._run(["related", "M90"])
        self.assertEqual(code, 0)
        self.assertIn("技术文档域包", out)


if __name__ == "__main__":
    unittest.main()
