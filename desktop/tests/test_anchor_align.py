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


class BootstrapTest(unittest.TestCase):
    def test_depends_is_closed_and_inverse(self):
        dep = aa.depends(str(ROOT))
        rev = aa.dependents(str(ROOT))
        ids = {s["id"] for s in aa.catalog(str(ROOT))}
        self.assertTrue(dep)
        for sid, targets in dep.items():
            self.assertTrue(set(targets) <= ids, sid)
            for t in targets:
                self.assertIn(sid, rev.get(t, []))

    def test_bootstrap_expands_from_seed(self):
        rows = aa.bootstrap(str(ROOT), "元数据", depth=1, limit=60)
        self.assertTrue(rows)
        self.assertEqual(0, min(r["depth"] for r in rows))
        self.assertTrue(any(r["depth"] == 1 for r in rows))
        seeds = aa.bootstrap(str(ROOT), "元数据", depth=0)
        self.assertTrue(all(r["depth"] == 0 for r in seeds))

    def test_bootstrap_empty_term(self):
        self.assertEqual([], aa.bootstrap(str(ROOT), "", depth=2))


class PackStatsTest(unittest.TestCase):
    def test_pack_stats_shape_and_order(self):
        rows = aa.pack_stats(str(ROOT))
        self.assertGreaterEqual(len(rows), 10)
        self.assertTrue(all(r["bindings"] > 0 for r in rows))
        self.assertTrue(all(r["layer_breadth"] >= 1 for r in rows))
        keys = [(int(r["layer_breadth"]), int(r["distinct_standards"]), str(r["code"]))
                for r in rows]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual([], aa.pack_stats(str(ROOT / "no-such-root")))

    def test_missing_layers_partition(self):
        for r in aa.pack_stats(str(ROOT)):
            self.assertEqual(set(aa.LAYERS),
                             set(r["layers"]) | set(r["missing_layers"]))
            self.assertEqual([], sorted(set(r["layers"]) & set(r["missing_layers"])))

    def test_shallow_packs_filter_and_order(self):
        rows = aa.shallow_packs(str(ROOT), 2)
        self.assertTrue(rows)
        self.assertTrue(all(int(r["layer_breadth"]) <= 2 for r in rows))
        keys = [(int(r["layer_breadth"]), int(r["distinct_standards"]), str(r["code"]))
                for r in rows]
        self.assertEqual(keys, sorted(keys))

    def test_pack_stats_deterministic(self):
        self.assertEqual(aa.pack_stats(str(ROOT)), aa.pack_stats(str(ROOT)))


if __name__ == "__main__":
    unittest.main()
