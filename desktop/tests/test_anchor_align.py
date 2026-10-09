# -*- coding: utf-8 -*-
"""双向锚定对齐面（core/anchor_align.py）回归测试 —— 反向利用率 / 正向词汇交叉。"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import anchor_align as aa  # noqa: E402


class RealRepoTest(unittest.TestCase):
    def test_stats_internally_consistent(self):
        st = aa.stats(str(ROOT))
        self.assertGreater(st["standards"], 100)
        self.assertGreater(st["packs"], 10)
        self.assertEqual(st["standards"], st["bound"] + st["unbound"])
        self.assertGreater(st["bound"], 0)
        self.assertGreater(st["unbound"], 0)
        self.assertTrue(0.0 < st["utilization"] < 1.0)
        self.assertEqual(st["standards"], sum(c["total"] for c in st["by_layer"].values()))

    def test_unbound_partition_by_layer(self):
        rows = aa.unbound(str(ROOT))
        self.assertEqual(len(rows), aa.stats(str(ROOT))["unbound"])
        gov = aa.unbound(str(ROOT), layer="gov")
        self.assertTrue(all(str(r.get("layer")) == "gov" for r in gov))

    def test_intersect_is_deterministic_and_ranked(self):
        a = aa.intersect(str(ROOT), "model", limit=5)
        b = aa.intersect(str(ROOT), "model", limit=5)
        self.assertEqual(a, b)
        self.assertEqual([r["hits"] for r in a], sorted([r["hits"] for r in a], reverse=True))
        self.assertTrue(all("id" in r for r in a))
        self.assertEqual([], aa.intersect(str(ROOT), ""))

    def test_report_has_header(self):
        self.assertIn("双向锚定对齐报告", aa.report(str(ROOT)))


class FailClosedTest(unittest.TestCase):
    def test_missing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([], aa.catalog(tmp))
            self.assertEqual(set(), aa.bound_ids(tmp))
            st = aa.stats(tmp)
            self.assertEqual(0, st["standards"])
            self.assertEqual(0.0, st["utilization"])
            self.assertEqual([], aa.intersect(tmp, "model"))


if __name__ == "__main__":
    unittest.main()
