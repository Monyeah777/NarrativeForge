# -*- coding: utf-8 -*-
"""Agentic 检索单测（v1.3.0 retriever.search：四类对象统一检索入口）。

运行：cd desktop && python -m unittest tests.test_retriever -v
隔离：临时 Store；module/asset 源用假数据；protocol 源读真实 registry.json（I5 真相源）。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.models import Module, AssetPack, Pipeline, PipelineLayer  # noqa: E402
from core.storage import Store  # noqa: E402
from core.retriever import search, Hit  # noqa: E402


def _mk_store():
    store = Store(home=tempfile.mkdtemp(prefix="nf_ret_"))
    # 模块
    m1 = Module(id="M00", category="通用类", layer="P00", name="数据结构")
    m1.source_md = "# 模块 通用:M00\n数据基座"
    m2 = Module(id="M22", category="事件类", layer="P30", name="事件叙事")
    store.save_module(m1)
    store.save_module(m2)
    # 资产包
    store.save_asset_pack(AssetPack(name="测试资产", entries={"LOCATION": "x"}))
    # 管线缓存（桌面侧管线经 cache 键 pipelines）
    p = Pipeline(id="P01", name="标准管线")
    p.layers = [PipelineLayer(id="P00", name="基座")]
    store.save_cache("pipelines", [p.to_json()])
    return store


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.store = _mk_store()

    def test_module_by_ref(self):
        hits = search(self.store, "module", "M00")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].kind, "module")
        self.assertEqual(hits[0].ref, "通用类:M00")
        self.assertEqual(hits[0].layer, "P00")

    def test_module_by_name(self):
        hits = search(self.store, "module", "事件叙事")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].name, "事件叙事")

    def test_asset_pack(self):
        hits = search(self.store, "asset_pack", "测试资产")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].kind, "asset_pack")
        self.assertEqual(hits[0].ref, "测试资产")

    def test_pipeline_via_cache(self):
        hits = search(self.store, "pipeline", "标准管线")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].ref, "P01")

    def test_protocol_from_registry(self):
        # 真实 registry.json protocols[]（I5 真相源）——v1.1.0 应有 ≥3 条
        hits = search(self.store, "protocol", "")
        self.assertGreaterEqual(len(hits), 1)

    def test_cross_kind_search(self):
        hits = search(self.store, None, "标准管线")
        kinds = {h.kind for h in hits}
        self.assertIn("pipeline", kinds)
        # kind=None 跨类返回全部类型命中

    def test_no_match_empty(self):
        hits = search(self.store, "module", "不存在的关键词XYZ")
        self.assertEqual(hits, [])

    def test_hit_is_dataclass_with_metadata(self):
        hits = search(self.store, "module", "M00")
        h = hits[0]
        self.assertIsInstance(h, Hit)
        # Discovery 轻量：有元数据，不强制带正文
        self.assertTrue(hasattr(h, "name") and hasattr(h, "layer"))

    # ---- E5：community 盘点源（真实仓库） ----
    def test_community_module_kind(self):
        hits = search(self.store, "community_module", "M55")
        self.assertTrue(hits, "community_module 应命中校园 M55")
        self.assertTrue(any(h.ref == "情感类:M55" for h in hits),
                        f"refs={[h.ref for h in hits]}")
        hit = next(h for h in hits if h.ref == "情感类:M55")
        self.assertEqual(hit.kind, "community_module")
        self.assertEqual(hit.tags[0], "校园情感领域包", f"tags={hit.tags}")

    def test_community_pipeline_kind(self):
        hits = search(self.store, "community_pipeline", "P04")
        self.assertTrue(hits)
        self.assertTrue(any(h.ref == "P04" for h in hits),
                        f"refs={[h.ref for h in hits]}")

    def test_community_default_all_excludes_community(self):
        # kind=None 全量不并入社区项（与 E4 四类语义隔离）
        hits = search(self.store, None, "M55")
        kinds = {h.kind for h in hits}
        self.assertNotIn("community_module", kinds,
                         "kind=None 不应混入 community_module")

    def test_community_installed_flag(self):
        # 先装一件 community 模块 → 盘点 ref installed 标记在 Hit tags 中
        from core.community_inventory import catalog, install_module
        items = [i for i in catalog(self.store)
                 if i.kind == "community_module" and i.ref == "情感类:M55"]
        self.assertTrue(items)
        self.assertTrue(install_module(self.store, items[0]))
        hits = search(self.store, "community_module", "M55")
        hit = next(h for h in hits if h.ref == "情感类:M55")
        self.assertIn("✓已装", hit.tags, f"tags={hit.tags}")


if __name__ == "__main__":
    unittest.main()
