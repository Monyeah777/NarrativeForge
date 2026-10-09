# -*- coding: utf-8 -*-
"""定义库品类注册表（core/category_registry.py）回归测试 —— 注册表模式 / 单一发现真源。

关键断言：LAYERS 派生 + 本地登记合并、attributed 标志诚实、按品类枚举与反查、
缺真源件如实报 issue、id 唯一、确定性。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import category_registry as cr  # noqa: E402

MIN_LAYERS = {
    "schema": "nf-layers/1",
    "tiers": [{"id": "contract", "name": "契约", "source": {"globs": ["protocol/*.json"]}}],
    "asset_levels": [{"id": "declaration", "name": "声明", "tier": "asset",
                      "globs": ["community/*/protocol.yaml"]}],
}


def _mk(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


class RealRepoTest(unittest.TestCase):
    def test_registry_selfcheck_clean(self):
        issues, _w, stats = cr.scan(str(ROOT))
        self.assertEqual([], issues)
        self.assertGreaterEqual(stats["categories"], 11)
        self.assertGreaterEqual(stats["attributed"], 9)

    def test_derived_and_local_categories_present(self):
        ids = {c["id"] for c in cr.categories(str(ROOT))}
        for cid in ("tier:contract", "level:declaration", "level:ontology",
                    "patterns", "integrations", "core-pipelines", "library-items"):
            self.assertIn(cid, ids)

    def test_attribution_flag_is_honest(self):
        by_id = {c["id"]: c for c in cr.categories(str(ROOT))}
        self.assertTrue(by_id["tier:contract"]["attributed"])
        self.assertFalse(by_id["patterns"]["attributed"])
        self.assertTrue(by_id["level:ontology"]["attributed"])

    def test_files_enumeration_and_locate(self):
        pipes = cr.files(str(ROOT), "core-pipelines")
        self.assertTrue(pipes)
        self.assertTrue(all(p.startswith("03_管线库/") for p in pipes))
        hit = cr.locate(str(ROOT), "library/NF-1.md")
        self.assertIn("library-items", hit)
        self.assertIn("tier:asset", hit)

    def test_unknown_category_is_empty(self):
        self.assertEqual((), cr.globs(str(ROOT), "no-such-category"))
        self.assertEqual([], cr.files(str(ROOT), "no-such-category"))
        self.assertEqual({}, cr.category(str(ROOT), "no-such-category"))

    def test_deterministic(self):
        self.assertEqual(cr.categories(str(ROOT)), cr.categories(str(ROOT)))

    def test_no_exact_duplicate_glob_sets(self):
        """单一真源：同一 glob 集合不得挂在两个品类 id 下（一物一名）。"""
        from collections import defaultdict
        d = defaultdict(list)
        for c in cr.categories(str(ROOT)):
            d[tuple(c["globs"])].append(c["id"])
        self.assertEqual({}, {k: v for k, v in d.items() if len(v) > 1},
                         "glob 集合重复（同一件事两个 id）")


class DuplicateGlobGateTest(unittest.TestCase):
    def test_duplicate_glob_sets_are_caught(self):
        """变异自证：手工登记一个与 LAYERS 派生项同 glob 集的品类，scan 必须判 issue。"""
        with tempfile.TemporaryDirectory() as tmp:
            _mk(tmp, cr.LAYERS_REL, json.dumps(MIN_LAYERS, ensure_ascii=False))
            _mk(tmp, "community/pkg/protocol.yaml", "id: x")
            dup = {"id": "dup-declaration", "title": "重复子面", "tier": "asset",
                   "globs": ("community/*/protocol.yaml",), "attributed": False,
                   "note": "变异注入：与 level:declaration 同 glob 集"}
            orig = cr.LOCAL_CATEGORIES
            cr.LOCAL_CATEGORIES = tuple(list(orig) + [dup])
            try:
                issues, _w, _s = cr.scan(tmp)
            finally:
                cr.LOCAL_CATEGORIES = orig
        self.assertTrue(any("glob 集合重复" in i for i in issues), issues)


class MutationTest(unittest.TestCase):
    def test_missing_layers_is_an_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, _w, _s = cr.scan(tmp)
        self.assertTrue(any(cr.LAYERS_REL in i for i in issues), issues)

    def test_layers_derive_categories_and_local_supplement(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk(tmp, cr.LAYERS_REL, json.dumps(MIN_LAYERS, ensure_ascii=False))
            _mk(tmp, "community/pkg/protocol.yaml", "id: x")
            ids = {c["id"] for c in cr.categories(tmp)}
            self.assertIn("tier:contract", ids)
            self.assertIn("level:declaration", ids)
            self.assertIn("patterns", ids)
            self.assertEqual(["community/pkg/protocol.yaml"], cr.files(tmp, "level:declaration"))
            issues, warns, _s = cr.scan(tmp)
            self.assertEqual([], issues)
            self.assertTrue(any("未归属" in w for w in warns), warns)

    def test_duplicate_local_id_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk(tmp, cr.LAYERS_REL, json.dumps(MIN_LAYERS, ensure_ascii=False))
            orig = cr.LOCAL_CATEGORIES
            try:
                cr.LOCAL_CATEGORIES = tuple(orig) + (dict(orig[0]),)
                issues, _w, _s = cr.scan(tmp)
            finally:
                cr.LOCAL_CATEGORIES = orig
        self.assertTrue(any("重复" in i for i in issues), issues)


if __name__ == "__main__":
    unittest.main()
