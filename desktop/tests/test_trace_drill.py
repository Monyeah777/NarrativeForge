#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 #3 · trace→drill 自动比对器单测。"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import trace_drill as td  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
