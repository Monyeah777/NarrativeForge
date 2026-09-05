# -*- coding: utf-8 -*-
"""变体/条件装配库单测（v2.3.0 B2：装配层变体模板选择 + 重叠仲裁）。

运行：cd desktop && python -m unittest tests.test_variants -v
纯函数：apply_variant 增删变换幂等；variant_assemblies 全变体展开 + 跨变体
模块重叠报告（声明级不阻断）。不改 references 协议结构（composer freeze）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.variants import apply_variant, variant_assemblies  # noqa: E402

BASE = ["通用类:M00", "轻混类:M91", "轻混类:M92", "通用类:M80"]


class TestApplyVariant(unittest.TestCase):
    def test_add_extends_base(self):
        v = apply_variant(BASE, {"name": "x", "add": ["校园情感类:M55"]})
        self.assertEqual(v.name, "x")
        self.assertIn("校园情感类:M55", v.selected)
        self.assertEqual(len(v.selected), len(BASE) + 1)

    def test_remove_drops_module(self):
        v = apply_variant(BASE, {"name": "x", "remove": ["轻混类:M92"]})
        self.assertNotIn("轻混类:M92", v.selected)
        self.assertEqual(len(v.selected), len(BASE) - 1)

    def test_add_duplicate_deduped(self):
        v = apply_variant(BASE, {"name": "x", "add": ["通用类:M00"]})
        self.assertEqual(v.selected.count("通用类:M00"), 1,
                         "add 与 base 重复应去重")
        self.assertEqual(len(v.selected), len(BASE))

    def test_remove_ignores_unknown(self):
        # remove 不存在模块：幂等不崩
        v = apply_variant(BASE, {"name": "x", "remove": ["幽灵:M99"]})
        self.assertEqual(v.selected, BASE)

    def test_remove_then_add_same(self):
        # remove 优先：base 中模块被 remove 后 add 同 full_id 不复活
        v = apply_variant(BASE, {"name": "x", "add": ["轻混类:M92"],
                                 "remove": ["轻混类:M92"]})
        self.assertNotIn("轻混类:M92", v.selected)

    def test_idempotent_double_apply(self):
        spec = {"name": "x", "add": ["校园情感类:M55"]}
        v1 = apply_variant(BASE, spec)
        v2 = apply_variant(v1.selected, spec)
        self.assertEqual(v1.selected, v2.selected,
                         "同变体二次应用应幂等（add 已存在不去重叠加）")


class TestVariantAssemblies(unittest.TestCase):
    def test_expand_all_variants(self):
        plan = variant_assemblies(BASE, {
            "完整": {"add": ["校园情感类:M55"]},
            "极简": {"remove": ["轻混类:M92"]},
        })
        self.assertEqual(len(plan.variants), 2)
        by_name = {v.name: v for v in plan.variants}
        self.assertIn("校园情感类:M55", by_name["完整"].selected)
        self.assertNotIn("轻混类:M92", by_name["极简"].selected)

    def test_overlap_detected_when_module_shared(self):
        # 两变体都含 M91（base 未移除）→ 重叠报告
        plan = variant_assemblies(BASE, {
            "甲": {"add": ["校园情感类:M55"]},
            "乙": {"add": ["西幻生存类:M17"]},
        })
        issues = plan.overlap_issues
        self.assertTrue(any("M91" in i for i in issues),
                        f"base 共有模块应报重叠：{issues}")

    def test_no_overlap_when_disjoint_additions_but_base_removed(self):
        # 变体间 base 各不相同（各移除对方独有的）仍共享 base——如实报告重叠
        plan = variant_assemblies(["通用类:M00"], {
            "甲": {"remove": []},
            "乙": {"remove": []},
        })
        self.assertTrue(plan.overlap_issues, "同 base 变体天然重叠（如实报告）")

    def test_empty_variants_no_crash(self):
        plan = variant_assemblies(BASE, {})
        self.assertEqual(plan.variants, [])
        self.assertEqual(plan.overlap_issues, [])

    def test_base_preserved_in_plan(self):
        plan = variant_assemblies(BASE, {"a": {"add": ["校园情感类:M55"]}})
        self.assertEqual(plan.base, BASE)


if __name__ == "__main__":
    unittest.main()
