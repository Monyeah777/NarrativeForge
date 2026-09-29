#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""域包工厂**渲染面**在无内部档案时的回归（合成规格，不依赖 `.rivet` 私档）。

为什么需要：规格真源在私档 `.rivet/private_archive/ai_packs/specs`（不入库），于是
`test_domain_pack.FactoryTest` 在干净检出里**整段 skip**——`core/domain_pack.py` 的
渲染面（concept_graph_md / domain_spec_md / standards_md / module_md …）无人覆盖，
逐模块覆盖率门（`scripts/per_module_coverage.sh 30`，`nf release` 与 CI 都跑）因此
在干净树上红（实测 2026-09-29：19.9%）。本文件用**合成规格**把这条判据补回来：
规格合法（过 `spec_issues`）→ 分配 → 逐面渲染 → 断言产物结构可读。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import domain_pack as dp  # noqa: E402


def _spec(code: str = "F99") -> dict:
    """合成规格：结构过 `spec_issues`，内容自成一体（不引用私档）。"""
    subs = []
    for i in range(1, dp.SUB_COUNT + 1):
        subs.append({"id": "%s-%02d" % (code, i),
                     "name": "子级 %d" % i,
                     "definition": "第 %d 个子级的最小可行定义（测试合成）。" % i,
                     "anchor": "https://example.org/std/%d" % i,
                     "check": "断言第 %d 子级的必填字段在场且类型正确。" % i,
                     "pitfall": "把第 %d 子级与相邻子级混为一谈。" % i})
    return {"code": code, "section": "F", "name": "测试域", "pack_name": "test_domain",
            "category": "test-category", "metric_family": "generation",
            "module_titles": ["测试域·口径层", "测试域·收口层"],
            "subdivisions": subs,
            "edges": [[subs[0]["id"], subs[1]["id"]]],
            "node_ids": [s["id"] for s in subs]}


class SyntheticSpecRenderingTest(unittest.TestCase):
    def test_synthetic_spec_is_structurally_valid(self):
        self.assertEqual([], dp.spec_issues(_spec()))

    def test_allocate_works_without_private_archive(self):
        alloc = dp.allocate(str(ROOT), _spec())
        self.assertTrue(alloc.get("pipeline"))
        self.assertEqual(2, len(alloc.get("module_ids") or []))

    def test_renderers_produce_structured_markdown(self):
        spec = _spec()
        alloc = dp.allocate(str(ROOT), spec)
        for name, text in (("concept_graph_md", dp.concept_graph_md(spec, str(ROOT))),
                           ("domain_spec_md", dp.domain_spec_md(spec, str(ROOT))),
                           ("standards_md", dp.standards_md(spec, str(ROOT))),
                           ("module_md#0", dp.module_md(spec, 0, alloc)),
                           ("module_md#1", dp.module_md(spec, 1, alloc))):
            self.assertTrue(text.strip(), "%s 产物为空" % name)
            self.assertEqual(0, text.count("```") % 2, "%s 围栏须配平" % name)
            self.assertIn(spec["code"], text, "%s 产物须带域码" % name)

    def test_standard_binding_surface_is_reachable(self):
        spec = _spec()
        catalog = dp.standards_catalog(str(ROOT))
        self.assertIsInstance(catalog, dict)
        full = dp.bindings_full(spec, catalog)
        self.assertEqual(len(spec["subdivisions"]), len(full),
                         "每条子级都该算出标准绑定")
        for sid, binding in full.items():
            self.assertTrue(binding.get("primary"), "%s 缺主锚绑定" % sid)
            self.assertTrue(binding.get("support"), "%s 缺载体锚绑定" % sid)
        idx = dp.concept_index(spec, catalog)
        self.assertTrue(idx.get("nodes"), "概念图节点表不该为空")
        self.assertTrue(idx.get("edges"), "概念图边表不该为空")
        auth = dp.authenticity(spec, catalog)
        self.assertIn("score", auth)
        self.assertIn("threshold", auth)
        self.assertGreaterEqual(auth.get("in_catalog_ratio", 0), 0.0)
        self.assertIsInstance(dp.dump_yaml(spec), list)


if __name__ == "__main__":
    unittest.main()
