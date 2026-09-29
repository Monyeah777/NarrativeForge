#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""代码规模/复杂度上限（`core/code_metrics.py`）回归测试 —— 架构纯度面 GAP-4。

关键断言：**棘轮**（存量只可降不可升）、新文件绝对限值、语法坏判死、真仓零超线。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import code_metrics as cm  # noqa: E402


def _mk(tmp: str, rel: str, body: str) -> Path:
    p = Path(tmp) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _fn(lines: int, branches: int = 0) -> str:
    body = "\n".join("    x = %d" % i for i in range(max(0, lines - 2 - branches)))
    br = "\n".join("    if x == %d:\n        x += 1" % i for i in range(branches))
    return "def f():\n%s\n%s\n    return x\n" % (body, br)


class MetricsTest(unittest.TestCase):
    def test_lines_and_complexity_measured(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = _fn(30, branches=5)
            p = _mk(tmp, "a.py", body)
            m = cm.metrics_of(str(p))
        self.assertEqual(len(body.splitlines()), m["lines"], "行数须等于实际行数")
        self.assertGreaterEqual(m["max_fn_cc"], 6, "5 个 if 至少 cc=6")
        self.assertGreater(m["max_fn_lines"], 10)

    def test_syntax_error_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _mk(tmp, "bad.py", "def f(:\n")
            m = cm.metrics_of(str(p))
        self.assertIn("syntax_error", m)
        self.assertIn("修复指引", m["syntax_error"])

    def test_syntax_error_file_fails_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk(tmp, "desktop/src/core/bad.py", "def f(:\n")
            issues, _warns, _stats = cm.scan(tmp)
        self.assertTrue(any("bad.py" in i for i in issues), issues)


class RatchetTest(unittest.TestCase):
    def _freeze(self, tmp: str, rel: str, body: str):
        _mk(tmp, rel, body)
        cm.write(tmp)

    def test_growth_beyond_frozen_ceiling_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            rel = "desktop/src/core/ratchet.py"
            self._freeze(tmp, rel, _fn(20))
            _mk(tmp, rel, _fn(60))
            issues, _w, _s = cm.scan(tmp)
        self.assertTrue(any("ratchet.py" in i and "冻结值" in i for i in issues), issues)

    def test_shrink_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            rel = "desktop/src/core/ratchet.py"
            self._freeze(tmp, rel, _fn(60))
            _mk(tmp, rel, _fn(20))
            issues, _w, _s = cm.scan(tmp)
        self.assertEqual([], issues, "棘轮只禁增长，不禁收缩")

    def test_new_file_within_limits_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            cm.write(tmp)
            _mk(tmp, "desktop/src/core/fresh.py", _fn(40))
            issues, _w, _s = cm.scan(tmp)
        self.assertEqual([], issues)

    def test_new_file_over_limits_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            cm.write(tmp)
            _mk(tmp, "desktop/src/core/monster.py", _fn(cm.LIMITS["max_fn_lines"] + 50))
            issues, _w, _s = cm.scan(tmp)
        self.assertTrue(any("monster.py" in i and "限值" in i for i in issues), issues)

    def test_missing_baseline_warns_with_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk(tmp, "desktop/src/core/x.py", _fn(10))
            _issues, warns, _s = cm.scan(tmp)
        self.assertTrue(any(cm.BASELINE_REL in w and "修复指引" in w for w in warns), warns)


class BaselineFileTest(unittest.TestCase):
    def test_write_records_all_scanned_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk(tmp, "desktop/src/core/a.py", _fn(10))
            _mk(tmp, "scripts/b.py", _fn(12))
            _i, doc = cm.write(tmp)
            self.assertEqual({"desktop/src/core/a.py", "scripts/b.py"}, set(doc["files"]))
            self.assertEqual(cm.SCHEMA, doc["schema"])
            saved = json.loads((Path(tmp) / cm.BASELINE_REL).read_text(encoding="utf-8"))
            self.assertEqual(cm.LIMITS, saved["limits"])

    def test_committed_baseline_is_valid_json_with_core_entries(self):
        p = ROOT / cm.BASELINE_REL
        self.assertTrue(p.is_file(), "须提交基线：%s" % cm.BASELINE_REL)
        doc = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(cm.SCHEMA, doc["schema"])
        self.assertIn("desktop/src/core/purity_scan.py", doc["files"])


class RealRepoTest(unittest.TestCase):
    def test_real_repo_has_no_over_limit_file(self):
        issues, _w, stats = cm.scan(str(ROOT))
        self.assertEqual([], issues, "真仓不得越过冻结上限：%s" % issues[:3])
        self.assertGreater(stats["files"], 100)
        self.assertGreater(stats["baseline"], 100)


if __name__ == "__main__":
    unittest.main()
