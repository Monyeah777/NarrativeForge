#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""42 M1 —— 执行失范捕获器单测（多管线演练集：P03/P06 + 变异自检/捕获率验收）。"""
import json
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import execution_drill as drill  # noqa: E402

FIX_DIR = Path(__file__).resolve().parent / "fixtures" / "execution"
FIXTURES = [FIX_DIR / "p03_drill_cases.json",
            FIX_DIR / "p06_drill_cases.json"]


class ExecutionDrillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sets = [json.loads(p.read_text(encoding="utf-8")) for p in FIXTURES]

    def _all_cases(self):
        for data in self.sets:
            for case in data["cases"]:
                yield data, case

    def _hits(self, data, case):
        return drill.run_case(case, data["real_ids"],
                              data.get("semantics") or {},
                              data.get("source_text", ""))

    def test_deviation_capture_all(self):
        """失范样本须全部被硬断言捕获（无漏报）。"""
        for data, case in self._all_cases():
            expected = set(case.get("expect_captured") or [])
            if not expected:
                continue
            hits = set(self._hits(data, case))
            self.assertTrue(expected <= hits,
                            "%s/%s 期望捕获 %s 实得 %s" %
                            (data["pipeline"], case["id"],
                             sorted(expected), sorted(hits)))

    def test_guard_samples_no_false_positive(self):
        """变异对照（guard）样本不得误捕获（特异性）。"""
        for data, case in self._all_cases():
            if not case.get("guard"):
                continue
            hits = set(self._hits(data, case))
            self.assertEqual(hits, set(),
                             "%s/%s 应无捕获，实得 %s" %
                             (data["pipeline"], case["id"], sorted(hits)))

    def test_capture_rate_at_least_two_thirds(self):
        """M1 验收：注入 ≥3 失范样本捕获率 ≥2/3（逐管线）。"""
        for data in self.sets:
            dev = [c for c in data["cases"]
                   if c.get("expect_captured") and not c.get("guard")]
            captured = sum(1 for c in dev
                           if set(c["expect_captured"]) <= set(self._hits(data, c)))
            self.assertGreaterEqual(captured, len(dev))
            self.assertGreaterEqual(captured / max(1, len(dev)), 2 / 3,
                                    data["pipeline"])

    def test_state_header_acceptance_rule_law_mapping(self):
        """带状态头执行口径：硬断言须一一映射到判级器必须/禁止铁律（无越级）。"""
        from core import round_header as rh
        for rule, law_id in drill.RULE_LAW.items():
            law = rh.LAW_INDEX[law_id]
            self.assertIn(law["level"], ("必须", "禁止"),
                          "%s 不得映射到软级/自由级" % rule)
        self.assertEqual(len(drill.RULE_LAW), 4)


if __name__ == "__main__":
    unittest.main()
