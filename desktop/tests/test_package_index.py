# -*- coding: utf-8 -*-
"""包管理器核心解析面（core/package_index.py）回归测试 —— 按品类取件 / 解析 / 检索。"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import package_index as pi  # noqa: E402


def _mk(root, rel, text=""):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


class ItemIdTest(unittest.TestCase):
    def test_id_rules(self):
        self.assertEqual("M55", pi.item_id("community/pkg/modules/M55_x.md"))
        self.assertEqual("P04", pi.item_id("community/pkg/pipelines/P04_y.md"))
        self.assertEqual("NF-1", pi.item_id("library/NF-1.md"))
        self.assertEqual("predicate-single-source",
                         pi.item_id("patterns/predicate-single-source/PATTERN.md"))


class RealRepoTest(unittest.TestCase):
    def test_core_pipelines_entries_and_resolve(self):
        ids = {r["id"] for r in pi.entries(str(ROOT), "core-pipelines")}
        for pid in ("P00", "P01", "P90"):
            self.assertIn(pid, ids)
        rec = pi.resolve(str(ROOT), "core-pipelines", "P01")
        self.assertTrue(rec["path"].startswith("03_管线库/"))
        self.assertTrue(pi.read_text(str(ROOT), "core-pipelines", "P01"))

    def test_community_facets_and_find(self):
        mods = pi.entries(str(ROOT), "community-modules")
        self.assertGreaterEqual(len(mods), 29)
        self.assertTrue(any(r["id"] == "M55" for r in mods))
        pipes = pi.entries(str(ROOT), "community-pipelines")
        self.assertGreaterEqual(len(pipes), 4)
        hits = pi.find(str(ROOT), "P04")
        self.assertTrue(any(h["category"] == "community-pipelines" for h in hits), hits)
        self.assertGreaterEqual(len(pi.package_dirs(str(ROOT))), 4)

    def test_search_categories_are_registered(self):
        """检索面品类必须都在注册表在册（判据直测，不再挂一个无人消费的 scan()）。"""
        from core import category_registry as cr
        known = {str(c["id"]) for c in cr.categories(str(ROOT))}
        miss = [c for c in pi.SEARCH_CATEGORIES if c not in known]
        self.assertEqual([], miss, "检索面品类不在注册表：%s" % miss)
        self.assertTrue(all(cr.files(str(ROOT), c) for c in pi.SEARCH_CATEGORIES),
                        "检索面品类 glob 应命中在場件")


class FailClosedTest(unittest.TestCase):
    def test_unknown_category_returns_empty(self):
        self.assertEqual([], pi.entries(str(ROOT), "no-such"))
        self.assertEqual({}, pi.resolve(str(ROOT), "no-such", "X"))
        self.assertEqual("", pi.read_text(str(ROOT), "no-such", "X"))
        self.assertIsNone(pi.path_of(str(ROOT), "no-such", "X"))

    def test_temp_root_resolution_and_under_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk(tmp, "community/pkg/modules/M01_alpha.md", "alpha")
            _mk(tmp, "community/pkg/modules/M02_beta.md", "beta")
            _mk(tmp, "community/other/modules/M01_gamma.md", "gamma")
            _mk(tmp, "community/pkg/pipelines/P09_x.md", "p09")
            rec = pi.resolve(tmp, "community-modules", "M01",
                             under="community/pkg/modules/")
            self.assertEqual("community/pkg/modules/M01_alpha.md", rec["path"])
            self.assertEqual("alpha", pi.read_text(tmp, "community-modules", "M01",
                                                   under="community/pkg/modules/"))
            self.assertEqual("gamma", pi.read_text(tmp, "community-modules", "M01",
                                                   under="community/other/modules/"))
            self.assertIsNone(pi.path_of(tmp, "community-modules", "M99"))
            self.assertEqual(["other", "pkg"], pi.package_dirs(tmp))
            self.assertEqual([], pi.find(tmp, "no-such-id"))


if __name__ == "__main__":
    unittest.main()
