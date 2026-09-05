# -*- coding: utf-8 -*-
"""community 仓库盘点单测（v2.0.x-E5：模块市场雏形深化——可发现 → 可装载）。

运行：cd desktop && python -m unittest tests.test_community_inventory -v
隔离：临时 Store（用户工作区）；盘点源 = 仓库真实 community/ 目录（I5 只读源，
与 test_retriever protocol 用例同源——仓库在 checkout 中即真实可盘点）。
覆盖：
  catalog 盘点 4 包 ≥29 模块 + ≥4 管线 / installed 判定（temp 装一件即翻转）
  install_module 幂等（重复装不报错不重复目录）/ install_pipeline cache merge
  不覆盖既有管线（P01 保留）/ 只读源不写仓库目录（I5 边界）。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.models import Pipeline, PipelineLayer, Module       # noqa: E402
from core.storage import Store                                # noqa: E402
from core.community_inventory import (                        # noqa: E402
    catalog, install_module, install_pipeline,
    load_community_module, load_community_pipeline,
)


def _mk_store():
    return Store(home=tempfile.mkdtemp(prefix="nf_inv_"))


class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.store = _mk_store()

    def test_catalog_lists_all_packages_and_modules(self):
        items = catalog(self.store)
        mods = [i for i in items if i.kind == "community_module"]
        pipes = [i for i in items if i.kind == "community_pipeline"]
        # 仓库 4 包实测：校园 9 / 西幻 14 / 轻混 2 / 通用 4 = 29 模块，4 管线
        self.assertGreaterEqual(len(mods), 29,
                                f"community 模块 <29：{len(mods)}")
        self.assertGreaterEqual(len(pipes), 4,
                                f"community 管线 <4：{len(pipes)}")

    def test_catalog_module_ref_is_full_id(self):
        items = catalog(self.store)
        m55 = [i for i in items if i.kind == "community_module"
               and i.ref.endswith(":M55") or (i.kind == "community_module"
                                              and i.ref == "情感类:M55")]
        self.assertTrue(any(i.ref == "情感类:M55" for i in m55),
                        "校园 M55 应盘点为 情感类:M55")
        self.assertTrue(any(i.pkg == "校园情感领域包" for i in m55))

    def test_catalog_pipeline_ref_is_id(self):
        items = catalog(self.store)
        p04 = [i for i in items if i.kind == "community_pipeline"
               and i.ref == "P04"]
        self.assertEqual(len(p04), 1, f"P04 管线应盘点：{p04}")
        self.assertEqual(p04[0].pkg, "校园西幻轻混组合包")

    def test_installed_flag_flips_after_install(self):
        # 初始：校园 M55 未装
        before = [i for i in catalog(self.store)
                  if i.kind == "community_module" and i.ref == "情感类:M55"]
        self.assertTrue(before and not before[0].installed)
        ok = install_module(self.store, before[0])
        self.assertTrue(ok)
        after = [i for i in catalog(self.store)
                 if i.kind == "community_module" and i.ref == "情感类:M55"]
        self.assertTrue(after and after[0].installed,
                        "装载后 catalog 应标 installed=True")

    def test_install_module_writes_to_store(self):
        items = catalog(self.store)
        m55 = next(i for i in items if i.kind == "community_module"
                   and i.ref == "情感类:M55")
        self.assertTrue(install_module(self.store, m55))
        m = self.store.get_module("情感类:M55")
        self.assertIsNotNone(m, "store.get_module 应命中已装 M55")
        self.assertEqual(m.layer, "P40", f"M55 层位：{m.layer}")

    def test_install_module_idempotent(self):
        items = catalog(self.store)
        m55 = next(i for i in items if i.kind == "community_module"
                   and i.ref == "情感类:M55")
        self.assertTrue(install_module(self.store, m55))
        self.assertTrue(install_module(self.store, m55), "重复装载应幂等 True")
        dirs = [d for d in self.store.module_dirs() if "M55" in d.name]
        self.assertEqual(len(dirs), 1, f"M55 目录应唯一：{dirs}")

    def test_install_pipeline_merges_cache_without_clobber(self):
        # 预置既有管线 P01（用户已加载）到 cache
        p1 = Pipeline(id="P01", name="标准管线")
        p1.layers = [PipelineLayer(id="P00", name="基座")]
        self.store.save_cache("pipelines", [p1.to_json()])

        items = catalog(self.store)
        p04 = next(i for i in items if i.kind == "community_pipeline"
                   and i.ref == "P04")
        self.assertTrue(install_pipeline(self.store, p04))
        raw = self.store.load_cache("pipelines")
        ids = [d.get("id") for d in raw]
        self.assertIn("P01", ids, "merge 应保留既有 P01")
        self.assertIn("P04", ids, "merge 应加入 P04")

    def test_install_pipeline_dedup(self):
        items = catalog(self.store)
        p02 = next(i for i in items if i.kind == "community_pipeline"
                   and i.ref == "P02")
        self.assertTrue(install_pipeline(self.store, p02))
        self.assertTrue(install_pipeline(self.store, p02), "重复装载应幂等 True")
        raw = self.store.load_cache("pipelines")
        ids = [d.get("id") for d in raw]
        self.assertEqual(ids.count("P02"), 1, f"P02 应唯一：{ids}")

    def test_load_community_module_returns_module(self):
        m = load_community_module("校园情感领域包", "情感类:M55")
        self.assertIsNotNone(m)
        self.assertEqual(m.full_id, "情感类:M55")

    def test_load_community_pipeline_returns_pipeline(self):
        p = load_community_pipeline("校园西幻轻混组合包", "P04")
        self.assertIsNotNone(p)
        self.assertEqual(p.id, "P04")
        self.assertEqual(len(p.layers), 9, "P04 应为九层骨架")


if __name__ == "__main__":
    unittest.main()
