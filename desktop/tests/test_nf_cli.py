#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.8.0 波C D2 —— scripts/nf.py CLI 层自动化测试（41 规划 D 组收口杂务）。

覆盖子命令参数面与装配链 smoke（替代手工冒烟；不依赖 GUI/端壳）。
"""
import argparse
import contextlib
import importlib.util
import io
import subprocess
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

    def test_market_list_json(self):
        code, out = self._run(["market", "--list", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "market-list"', out)
        self.assertIn('"grade"', out)

    def test_related_techdoc(self):
        code, out = self._run(["related", "技术文档域包"])
        self.assertEqual(code, 0)
        self.assertIn("官方核心", out)

    def test_diff_01_vs_36(self):
        """nf diff 冒烟：01 核心协议 vs 36 方案 → 判定行在场（C2 差异检测）。"""
        code, out = self._run(["diff", str(ROOT / "01_核心协议.md"),
                               str(ROOT / "36_v2.5.0_基础层深化续方案.md")])
        self.assertEqual(code, 0)
        self.assertIn("判定", out)

    def test_related_m90_reverse(self):
        """nf related 冒烟：M90 反向引用方（M2 校验 P03 drill 之外的人读链）。"""
        code, out = self._run(["related", "M90"])
        self.assertEqual(code, 0)
        self.assertIn("技术文档域包", out)

    def test_related_json(self):
        code, out = self._run(["related", "M90", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"target": "M90"', out)
        self.assertIn('"kind"', out)

    def test_asset_ls_json(self):
        code, out = self._run(["asset", "ls", "--json", "--root", str(ROOT)])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "asset-ls"', out)
        self.assertIn('"rows"', out)

    def test_asset_inventory_json(self):
        code, out = self._run(["asset", "inventory", "--json", "--root", str(ROOT)])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "asset-inventory"', out)

    def test_module_ls_json(self):
        code, out = self._run(["module", "ls", "--json", "--root", str(ROOT)])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "module-ls"', out)
        self.assertIn('"file"', out)

    def test_completion_bash(self):
        code, out = self._run(["completion", "bash"])
        self.assertEqual(code, 0)
        self.assertIn("complete -F _nf_completions nf", out)
        self.assertIn("sig", out)

    def test_completion_zsh(self):
        code, out = self._run(["completion", "zsh"])
        self.assertEqual(code, 0)
        self.assertIn("compdef _nf nf", out)

    def test_completion_fish(self):
        code, out = self._run(["completion", "fish"])
        self.assertEqual(code, 0)
        self.assertIn("__fish_use_subcommand", out)
        self.assertIn("doctor", out)

    def test_exit_code_matrix(self):
        """退出码矩阵（子进程）：0 成功 / 2 用法·未知命令·校验失败 / 未知子命令。"""
        cases = (
            (["bogus"], 2),
            (["run"], 2),
            (["explain", "no-such-check"], 2),
            (["doctor"], 0),
        )
        for argv, expected in cases:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "nf.py")] + argv,
                capture_output=True, text=True, encoding="utf-8", timeout=120,
            )
            self.assertEqual(proc.returncode, expected, "argv=%s" % argv)

    # ---- 44 波：CLI 工具链顶尖化（骨架约定：无参 help / help 子命令 / doctor / version）----
    def test_no_args_shows_help(self):
        code, out = self._run([])
        self.assertEqual(code, 0)
        self.assertIn("usage", out)

    def test_help_subcommand(self):
        code, out = self._run(["help", "sig"])
        self.assertEqual(code, 0)
        self.assertIn("usage: nf sig", out)
        self.assertIn("知识签名", out)
        self.assertIn("target", out)
        code2, _ = self._run(["help", "no-such"])
        self.assertEqual(code2, 2)

    def test_doctor_ok(self):
        code, out = self._run(["doctor"])
        self.assertEqual(code, 0)
        self.assertIn("体检", out)
        self.assertIn("[PASS]", out)

    def test_doctor_json(self):
        code, out = self._run(["doctor", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"ok": true', out)
        self.assertIn('"version"', out)

    def test_cli_version_flag(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "nf.py"), "--version"],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("nf 1.0.0", proc.stdout)


if __name__ == "__main__":
    unittest.main()
