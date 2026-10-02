#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 #3 · trace→drill 自动比对器单测。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import trace_drill as td  # noqa: E402

NF = os.path.join(ROOT, "scripts", "nf.py")
SAMPLE = os.path.join(ROOT, "docs", "完整版样本_西幻生存流P03.md")
REQ = "帮我组装一个西幻生存世界的完整版"


def _nf(*argv):
    return subprocess.run([sys.executable, NF, *argv], capture_output=True,
                          encoding="utf-8", errors="replace", timeout=300,
                          cwd=ROOT)


class TraceDrillTest(unittest.TestCase):
    def _write(self, tmp, name, text):
        p = Path(tmp, name)
        p.write_text(text, encoding="utf-8")
        return p

    def test_trace_matches_recheck(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._write(tmp, "t.md",
                              "回合 1：引用 06 §3 推进，M00 写回 状态快照。\n")
            trace = Path(tmp, "trace.json")
            trace.write_text(json.dumps(
                {"phase": "check", "requirement": "西幻生存",
                 "source": str(src), "ok": True}), encoding="utf-8")
            issues, stats = td.analyze(str(trace), ROOT)
            self.assertEqual(issues, [])
            self.assertTrue(stats["actual_ok"])

    def test_verdict_drift_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "bad.md",
                        "回合 1：推进状态，无引用。\n")
            trace = Path(tmp, "trace.json")
            trace.write_text(json.dumps(
                {"phase": "check", "requirement": "西幻生存",
                 "source": str(Path(tmp, "bad.md")), "ok": True}),
                encoding="utf-8")
            issues, _ = td.analyze(str(trace), ROOT)
            self.assertTrue(any("漂移" in i for i in issues))

    def test_rounds_scope_is_honored(self):
        """`rounds:{checked,ok}` 在场时按其核；`checked=False` ⇒ 不适用（不做漂移断言）。

        口径缺口（2026-09-30 闭合闭环时抓到）：`nf assemble --check --trace` 的总判定 `ok`
        只在加 `--rounds` 时才含回合级；此前 trace 只记一个 `ok`，消费方会把「没做回合级」
        读成「回合级通过」（实测：`--check` 不带 `--rounds` 写出的 trace 读回必报假漂移）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            src = self._write(tmp, "t.md", "回合 1：引用 06 §3 推进，M00 写回 状态快照。\n")
            # checked=True 且记录为 False（回合级不达标）⇒ 与重跑一致 ⇒ 无漂移
            ok_trace = Path(tmp, "ok.json")
            ok_trace.write_text(json.dumps(
                {"requirement": "西幻生存", "source": str(src), "ok": True,
                 "rounds": {"checked": True, "ok": True}}), encoding="utf-8")
            issues, stats = td.analyze(str(ok_trace), ROOT)
            self.assertEqual(issues, [])
            self.assertEqual(stats["verdict_scope"], "rounds")
            # checked=False ⇒ 不适用：不冒充通过（有 issue + 明确 scope）
            none_trace = Path(tmp, "none.json")
            none_trace.write_text(json.dumps(
                {"requirement": "西幻生存", "source": str(src), "ok": True,
                 "rounds": {"checked": False, "ok": None}}), encoding="utf-8")
            issues2, stats2 = td.analyze(str(none_trace), ROOT)
            self.assertTrue(any("未含回合级判定" in i for i in issues2))
            self.assertEqual(stats2["verdict_scope"], "none")


class TraceDrillCliTest(unittest.TestCase):
    """闭环判据：`--trace` 写出的遥测件必须有**可达**的读回入口（此前只被自身单测引用）。"""

    def test_round_trip_has_no_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            trace = str(Path(tmp, "trace.json"))
            w = _nf("assemble", REQ, "--check", SAMPLE, "--trace", trace, "--rounds")
            self.assertTrue(Path(trace).is_file(), w.stdout + w.stderr)
            r = _nf("assemble", REQ, "--check-trace", trace)
            self.assertEqual(0, r.returncode, r.stdout + r.stderr)
            self.assertIn("无漂移", r.stdout)

    def test_scope_none_is_fail_closed_not_a_silent_pass(self):
        """trace 未含回合级判定 ⇒ rc=2「未执行」，不得读成「验收通过」。"""
        with tempfile.TemporaryDirectory() as tmp:
            trace = str(Path(tmp, "trace.json"))
            _nf("assemble", REQ, "--check", SAMPLE, "--trace", trace)   # 无 --rounds
            r = _nf("assemble", REQ, "--check-trace", trace)
            self.assertEqual(2, r.returncode, r.stdout + r.stderr)
            self.assertIn("未执行", r.stderr)
            self.assertIn("修复指引", r.stderr)

    def test_drift_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp, "bad.md")
            src.write_text("回合 1：推进状态，无引用。\n", encoding="utf-8")
            trace = Path(tmp, "trace.json")
            trace.write_text(json.dumps(
                {"phase": "check", "requirement": REQ, "source": str(src),
                 "ok": True, "rounds": {"checked": True, "ok": True}}),
                encoding="utf-8")
            r = _nf("assemble", REQ, "--check-trace", str(trace))
            self.assertEqual(1, r.returncode, r.stdout + r.stderr)
            self.assertIn("漂移", r.stderr)

    def test_missing_trace_is_a_clean_error(self):
        r = _nf("assemble", REQ, "--check-trace", "__NF_PROBE__.json")
        text = (r.stdout or "") + (r.stderr or "")
        self.assertNotEqual(0, r.returncode)
        self.assertNotIn("内部错误", text)
        self.assertIn("修复指引", text)


if __name__ == "__main__":
    unittest.main()
