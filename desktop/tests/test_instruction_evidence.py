#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""规范入口指令实测记录（`core/instruction_evidence.py`）回归测试 —— 文档可执行性面 GAP-6。

全部用**注入执行器** + 临时根，不依赖工作区状态（并发会话不会把测试搞红）。
"""
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import instruction_evidence as ie  # noqa: E402


def _decl(tmp: str, instructions, evidence=None) -> None:
    p = Path(tmp) / ie.DECL_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"schema": ie.SCHEMA, "note": "t", "instructions": instructions,
                             "evidence": evidence or {}}, ensure_ascii=False),
                 encoding="utf-8")


ONE = [{"id": "x", "cmd": "python -c pass", "note": "t", "tier": "fast", "max_age_days": 7}]


class LoadTest(unittest.TestCase):
    def test_missing_declaration_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, _w, _s = ie.scan(tmp)
        self.assertTrue(any(ie.DECL_REL in i and "修复指引" in i for i in issues), issues)

    def test_bad_json_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / ie.DECL_REL
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{oops", encoding="utf-8")
            issues, _w, _s = ie.scan(tmp)
        self.assertTrue(any("合法 JSON" in i for i in issues), issues)

    def test_empty_instructions_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, [])
            issues, _w, _s = ie.scan(tmp)
        self.assertTrue(any("instructions" in i for i in issues), issues)


class ScanTest(unittest.TestCase):
    def test_missing_record_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE)
            issues, _w, _s = ie.scan(tmp)
        self.assertTrue(any("无实测记录" in i for i in issues), issues)

    def test_nonzero_exit_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE, {"x": {"cmd": "c", "exit_code": 2,
                                   "ran_at": dt.date.today().isoformat()}})
            issues, _w, _s = ie.scan(tmp)
        self.assertTrue(any("退出码" in i for i in issues), issues)

    def test_stale_record_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = (dt.date.today() - dt.timedelta(days=30)).isoformat()
            _decl(tmp, ONE, {"x": {"cmd": "c", "exit_code": 0, "ran_at": old}})
            issues, _w, _s = ie.scan(tmp)
        self.assertTrue(any("过期" in i for i in issues), issues)

    def test_fresh_zero_record_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE, {"x": {"cmd": "c", "exit_code": 0,
                                   "ran_at": dt.date.today().isoformat()}})
            issues, _w, stats = ie.scan(tmp)
        self.assertEqual([], issues)
        self.assertEqual({"declared": 1, "recorded": 1, "recorded_policy": 0}, stats)

    def test_recorded_policy_allows_nonzero_exit(self):
        """不动点例外：与判据表互为因果的入口只要求「真跑记录存在 + 新鲜」，退出码不判死。"""
        item = [dict(ONE[0], evidence_policy="recorded")]
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, item, {"x": {"cmd": "c", "exit_code": 1,
                                    "ran_at": dt.date.today().isoformat()}})
            issues, _w, stats = ie.scan(tmp)
        self.assertEqual([], issues)
        self.assertEqual(1, stats["recorded_policy"])

    def test_recorded_policy_still_requires_record_and_freshness(self):
        item = [dict(ONE[0], evidence_policy="recorded")]
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, item)
            missing, _w, _s = ie.scan(tmp)
            old = (dt.date.today() - dt.timedelta(days=30)).isoformat()
            _decl(tmp, item, {"x": {"cmd": "c", "exit_code": 1, "ran_at": old}})
            stale, _w2, _s2 = ie.scan(tmp)
        self.assertTrue(any("无实测记录" in i for i in missing), missing)
        self.assertTrue(any("过期" in i for i in stale), stale)

    def test_invalid_policy_is_reported(self):
        item = [dict(ONE[0], evidence_policy="whatever")]
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, item, {"x": {"cmd": "c", "exit_code": 0,
                                    "ran_at": dt.date.today().isoformat()}})
            issues, _w, _s = ie.scan(tmp)
        self.assertTrue(any("evidence_policy" in i for i in issues), issues)

    def test_undeclared_record_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE, {"x": {"cmd": "c", "exit_code": 0,
                                   "ran_at": dt.date.today().isoformat()},
                             "ghost": {"cmd": "c", "exit_code": 0,
                                       "ran_at": dt.date.today().isoformat()}})
            issues, _w, _s = ie.scan(tmp)
        self.assertTrue(any("ghost" in i for i in issues), issues)


class RecordTest(unittest.TestCase):
    def test_record_writes_evidence_and_scan_passes(self):
        def fake_runner(cmd):
            return 0, "ok: %s" % cmd

        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE)
            bad, doc = ie.record(tmp, only="all", runner=fake_runner)
            self.assertEqual([], bad)
            rec = doc["evidence"]["x"]
            self.assertEqual(0, rec["exit_code"])
            self.assertIn("output_sha256", rec)
            issues, _w, _s = ie.scan(tmp)
        self.assertEqual([], issues, "记录后应通过")

    def test_record_only_filters_by_tier_and_id(self):
        def fake_runner(cmd):
            return 0, "ok"

        two = [dict(ONE[0], id="fast1", tier="fast"),
               dict(ONE[0], id="heavy1", tier="release")]
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, two)
            ie.record(tmp, only="fast", runner=fake_runner)
            ev = json.loads((Path(tmp) / ie.DECL_REL).read_text(encoding="utf-8"))["evidence"]
        self.assertIn("fast1", ev)
        self.assertNotIn("heavy1", ev, "--only fast 只跑轻档")

    def test_record_reports_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, ONE)
            bad, _doc = ie.record(tmp, only="all", runner=lambda c: (3, "boom"))
        self.assertEqual(["x"], bad)


class RealRepoTest(unittest.TestCase):
    def test_declaration_is_committed_with_entries(self):
        p = ROOT / ie.DECL_REL
        self.assertTrue(p.is_file(), "须提交声明件：%s" % ie.DECL_REL)
        doc = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(ie.SCHEMA, doc["schema"])
        self.assertGreaterEqual(len(doc["instructions"]), 5,
                                "规范入口指令至少声明 5 条")
        for it in doc["instructions"]:
            self.assertTrue(it.get("id") and it.get("cmd"),
                            "每条声明须有 id 与 cmd：%s" % it)


if __name__ == "__main__":
    unittest.main()
