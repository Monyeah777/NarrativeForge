#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/orchestrate.py（编排面 CLI 入口）回归：目录 / 计划编译 / 机检 / 退出码。

为什么单列：core.orchestration 是**叶子**（工具面由调用方注入），命令行入口落在 core 之外，
因此它不在这条线的单测覆盖里——而「能力有入口、入口没人验」正是本仓反复收口的那类缺口。
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "orchestrate.py"
GOOD = {"schema": "nf-orchestration/1", "workflow": "menu",
        "steps": [{"id": "search", "tool": "library_search", "args": {"query": "x"}}]}


def run(args):
    return subprocess.run([sys.executable, str(SCRIPT)] + list(args),
                          cwd=str(ROOT), capture_output=True, timeout=600)


class OrchestrateCliTest(unittest.TestCase):
    def test_catalog_is_valid_json_with_plan_guide(self):
        p = run(["--catalog"])
        self.assertEqual(0, p.returncode, p.stderr.decode("utf-8", "replace"))
        doc = json.loads(p.stdout.decode("utf-8"))
        self.assertEqual("nf-orchestration/1", doc["schema"])
        self.assertIn("expects", doc["plan"], "计划格式自述须随目录交回（agent 第一跳）")
        self.assertGreaterEqual(len(doc["tools"]), 10, "工具面塌缩")

    def test_check_passes_on_real_repo(self):
        p = run(["--check"])
        self.assertEqual(0, p.returncode, p.stderr.decode("utf-8", "replace"))
        self.assertIn("编排面", p.stdout.decode("utf-8"))

    def test_no_args_runs_default_summary(self):
        """无参默认分支此前无判据：它走的是「汇总 + 有问题才 rc=1」那条路。"""
        p = run([])
        self.assertEqual(0, p.returncode, p.stderr.decode("utf-8", "replace"))
        out = p.stdout.decode("utf-8")
        self.assertIn("编排面", out)
        self.assertIn("问题 0", out)

    def test_unknown_flag_is_usage_error_rc2(self):
        """文档承诺「2 = 用法错误」——此前没有任何判据守它（2026-10-04 补）。"""
        p = run(["--nope"])
        self.assertEqual(2, p.returncode, "用法错误必须 rc=2（docstring 的退出码契约）")
        self.assertIn("usage", (p.stderr or b"").decode("utf-8", "replace").lower())

    def test_good_plan_compiles_with_rc0(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "ok.json"
            plan.write_text(json.dumps(GOOD), encoding="utf-8")
            p = run(["--plan", str(plan)])
        self.assertEqual(0, p.returncode, p.stderr.decode("utf-8", "replace"))
        self.assertTrue(json.loads(p.stdout.decode("utf-8"))["ok"])

    def test_bad_plan_exits_nonzero(self):
        bad = {"schema": "nf-orchestration/1", "workflow": "menu",
               "steps": [{"id": "s1", "tool": "module_read", "args": {}}]}
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "bad.json"
            plan.write_text(json.dumps(bad), encoding="utf-8")
            p = run(["--plan", str(plan)])
        self.assertEqual(1, p.returncode, "有问题的计划必须 rc=1")
        res = json.loads(p.stdout.decode("utf-8"))
        self.assertFalse(res["ok"])
        self.assertTrue(any("映射集" in i for i in res["issues"]), res["issues"])


if __name__ == "__main__":
    unittest.main()
