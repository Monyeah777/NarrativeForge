#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""演练保真度（`core/drill_fidelity.py`）回归测试 —— 动态可执行面。

断言：量化口径（执行演练 + 回合回放 + 总口径）、不达标即 FAIL、**无载体即 FAIL**、
真仓保真度 100%。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import drill_fidelity as df  # noqa: E402


def _exec_set(tmp: str, name: str, cases) -> None:
    p = Path(tmp) / "desktop/tests/fixtures/execution" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"schema": "nf-drill-cases/1", "pipeline": "P01",
                             "real_ids": ["M00"], "semantics": {}, "source_text": "",
                             "cases": cases}, ensure_ascii=False), encoding="utf-8")


def _round(tmp: str, name: str, verdict: str, transcript: str, allowed=("M00",)) -> None:
    p = Path(tmp) / "desktop/tests/fixtures/execution/rounds" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"schema": "nf-round-fixture/1", "verdict": verdict,
                             "transcript": transcript, "allowed": list(allowed)},
                            ensure_ascii=False), encoding="utf-8")


#: 回合级 drill 的引用判据（_CITE）认 §N / 第N节|步|章 / L行 / 类别:Mxx——不认 [Mxx]
GOOD_TRANSCRIPT = ("回合 1：依 06 §3 推进，写回状态。\n"
                   "回合 2：依 06 §4 快照存档。\n")
BAD_TRANSCRIPT = "回合 1：既无引用也无推进。\n"


class MeasureTest(unittest.TestCase):
    def test_fidelity_is_ratio_of_passed_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            _exec_set(tmp, "p01_drill_cases.json", [
                {"id": "ok", "expect_captured": []},
                {"id": "bad", "expect_captured": ["不存在的捕获"]},
            ])
            _round(tmp, "good.json", "good", GOOD_TRANSCRIPT)
            m = df.measure(tmp)
        self.assertEqual(2, m["execution"]["cases"])
        self.assertEqual(1, m["execution"]["passed"])
        self.assertEqual(0.5, m["execution"]["fidelity"])
        self.assertEqual(1, m["rounds"]["total"])
        self.assertEqual(1, m["rounds"]["matched"])
        self.assertAlmostEqual(2 / 3, m["overall"]["fidelity"], places=4)

    def test_round_verdict_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            _round(tmp, "good.json", "good", GOOD_TRANSCRIPT)
            _round(tmp, "bad.json", "bad", BAD_TRANSCRIPT)
            m = df.measure(tmp)
        self.assertEqual(2, m["rounds"]["matched"], "good→conformant / bad→non-conformant 须复现")
        self.assertEqual(1.0, m["rounds"]["fidelity"])

    def test_round_mismatch_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _round(tmp, "wrong.json", "good", BAD_TRANSCRIPT)   # 声明 good 实则不合规
            m = df.measure(tmp)
        self.assertEqual(0, m["rounds"]["matched"])


class ScanTest(unittest.TestCase):
    def test_no_fixtures_fails_with_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, _w, _s = df.scan(tmp)
        self.assertTrue(any("执行演练用例" in i and "修复指引" in i for i in issues), issues)
        self.assertTrue(any("回合级回放样本" in i for i in issues), issues)

    def test_imperfect_fidelity_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            _exec_set(tmp, "p01_drill_cases.json", [{"id": "bad", "expect_captured": ["x"]}])
            _round(tmp, "good.json", "good", GOOD_TRANSCRIPT)
            issues, _w, _s = df.scan(tmp)
        self.assertTrue(any("保真度不足" in i for i in issues), issues)

    def test_perfect_fidelity_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _exec_set(tmp, "p01_drill_cases.json", [{"id": "ok", "expect_captured": []}])
            _round(tmp, "good.json", "good", GOOD_TRANSCRIPT)
            issues, _w, stats = df.scan(tmp)
        self.assertEqual([], issues)
        self.assertEqual(1.0, stats["fidelity"])

    def test_broken_json_set_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "desktop/tests/fixtures/execution/p01_drill_cases.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{oops", encoding="utf-8")
            issues, _w, _s = df.scan(tmp)
        self.assertTrue(any("不可解析" in i for i in issues), issues)


class RealRepoTest(unittest.TestCase):
    def test_real_repo_fidelity_is_full(self):
        issues, _w, stats = df.scan(str(ROOT))
        self.assertEqual([], issues, "真仓演练保真度须为满分，实得问题：%s" % issues[:3])
        self.assertEqual(1.0, stats["fidelity"])
        self.assertGreaterEqual(stats["exec_sets"], 5)
        self.assertGreaterEqual(stats["round_samples"], 2)


if __name__ == "__main__":
    unittest.main()
