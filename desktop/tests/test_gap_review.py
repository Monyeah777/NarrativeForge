#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""缺口逐行审查（gap_review）单测：候选筛法可复现 + 确定性证据复核 + stub 双轨纪律。

补齐既有覆盖缺口（逐模块覆盖率门禁实测 `gap_review.py` 0.0%——AUD-0015 落地时无随行单测；
本波把它顶上 ≥30%）。判据只用**离线 stub**（真模型不进单测，避免不确定性进 CI）。
"""
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import gap_review as gr  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


class CandidateTest(unittest.TestCase):
    def test_candidates_are_deterministic_and_capped(self):
        a = gr.candidates(ROOT)
        b = gr.candidates(ROOT)
        self.assertEqual(a, b, "候选筛法必须确定性可复现（同输入同输出）")
        self.assertTrue(a, "真仓库应有候选（缺证据/静默吞错/缺质量规则三类）")
        for row in a[:5]:
            self.assertIn("class", row)
            self.assertIn("file", row)
            self.assertIn("line", row)

    def test_class_filter_narrows_scope(self):
        allrows = gr.candidates(ROOT)
        classes = sorted({r["class"] for r in allrows})
        self.assertGreaterEqual(len(classes), 1)
        only = gr.candidates(ROOT, classes=(classes[0],))
        self.assertTrue(all(r["class"] == classes[0] for r in only))
        self.assertLessEqual(len(only), len(allrows))


class EvidenceTest(unittest.TestCase):
    def test_evidence_available_for_some_rows_and_always_a_string(self):
        rows = gr.candidates(ROOT)
        self.assertTrue(rows)
        texts = [gr.evidence(ROOT, r) for r in rows]
        self.assertTrue(all(isinstance(t, str) for t in texts))
        self.assertTrue(any(t.strip() for t in texts),
                        "候选池里应至少有一部分行有确定性证据（否则筛法失真）")

    def test_rows_without_evidence_are_the_suspected_class(self):
        """无证据行不得进修复清单——按类归到 suspected（双轨纪律的机检面）。"""
        doc = gr.review(ROOT, adapter="stub", limit=0)
        for row in doc.get("fixable", []):
            self.assertTrue(str(row.get("evidence", "")).strip(),
                            "fixable 行必须带确定性证据：%r" % row)


class ReviewTest(unittest.TestCase):
    def test_stub_review_shape_and_double_track(self):
        doc = gr.review(ROOT, adapter="stub", limit=6, batch=3)
        self.assertEqual(doc.get("schema"), "nf-gap-review/1")
        self.assertIn("fixable", doc)
        self.assertIn("suspected", doc)
        self.assertIn("by_class", doc)
        self.assertLessEqual(doc["scanned"], 6)
        self.assertFalse(doc["model_meta"]["calibrated"],
                         "stub 未校准（calibrated=false）——不得当质量背书")
        self.assertTrue(gr.summary(doc))

    def test_limit_zero_means_all_rows(self):
        all_rows = gr.review(ROOT, adapter="stub", limit=0)
        few = gr.review(ROOT, adapter="stub", limit=2)
        self.assertGreaterEqual(all_rows["scanned"], few["scanned"])
        self.assertEqual(few["scanned"], 2)


if __name__ == "__main__":
    unittest.main()
