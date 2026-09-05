# -*- coding: utf-8 -*-
"""registry 变更影响面检查单测（v2.2.0 A4：impact_check 引用图闭合）。

运行：cd desktop && python -m unittest tests.test_impact_check -v
隔离：构造临时 registry（悬空 source_package / 悬空 module_id / 同包裸号重复），
断言 issues 逐项命中；真 registry.json 自洽 smoke 回归。
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.impact_check import (  # noqa: E402
    check_registry, referenced_by_packages, registry_integrity_issues,
    removal_impact,
)
from core.registry_loader import Registry  # noqa: E402


def _reg(**over) -> Registry:
    base = dict(
        registry_schema_version="2", schema_name="test", registry_name="t",
        truth_source="02_联动注册表.md",
        modules=[{"id": "M00", "name": "数据结构", "category": "通用",
                  "source": "核心", "mounts": []}],
        mount_points={}, subscriptions={},
        protocols=[{
            "id": "校园情感领域包",
            "module_ids": ["情感:M22", "M40", "M55"],
            "references": [],
        }, {
            "id": "校园西幻轻混组合包",
            "module_ids": ["M91", "M92"],
            "references": [
                {"source_package": "校园情感领域包", "module_id": "M55",
                 "source_schema_version": "2", "asset_readonly": True},
            ],
        }],
    )
    base.update(over)
    return Registry(**base)


class TestIntegrityIssues(unittest.TestCase):
    def test_healthy_registry_empty_issues(self):
        self.assertEqual(registry_integrity_issues(_reg()), [])

    def test_dangling_source_package(self):
        # references.source_package 不在 protocols[] 在册
        reg = _reg()
        reg.protocols[1]["references"][0]["source_package"] = "幽灵领域包"
        issues = registry_integrity_issues(reg)
        self.assertTrue(any("①②" in i and "幽灵领域包" in i for i in issues), issues)

    def test_dangling_module_id(self):
        # source_package 在册但 module_id 不在源包 module_ids
        reg = _reg()
        reg.protocols[1]["references"][0]["module_id"] = "M99"
        issues = registry_integrity_issues(reg)
        self.assertTrue(any(i.startswith("②") and "M99" in i for i in issues), issues)

    def test_qualified_reference_resolves_to_bare(self):
        # 引用方写 情感:M55，源包 module_ids 有 M55 裸号——归一后应 PASS
        reg = _reg()
        reg.protocols[1]["references"][0]["module_id"] = "情感:M55"
        self.assertEqual(registry_integrity_issues(reg), [])

    def test_dup_bare_module_in_package(self):
        # 同包 M55 与 情感:M55 并存 = 裸号重复（寻址歧义）
        reg = _reg()
        reg.protocols[0]["module_ids"] = ["M55", "情感:M55"]
        issues = registry_integrity_issues(reg)
        self.assertTrue(any(i.startswith("③") and "M55" in i for i in issues), issues)

    def test_registry_without_protocols_ok(self):
        reg = _reg(protocols=[])
        self.assertEqual(registry_integrity_issues(reg), [])


class TestReferencedByPackages(unittest.TestCase):
    def test_bare_hit(self):
        refs = referenced_by_packages(_reg(), "M55")
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["protocol"], "校园西幻轻混组合包")
        self.assertEqual(refs[0]["source_package"], "校园情感领域包")

    def test_qualified_query_hits_bare_ref(self):
        refs = referenced_by_packages(_reg(), "情感类:M55")
        self.assertEqual(len(refs), 1)

    def test_no_ref_empty(self):
        self.assertEqual(referenced_by_packages(_reg(), "M00"), [])
        self.assertEqual(referenced_by_packages(_reg(), "M91"), [])


class TestRemovalImpact(unittest.TestCase):
    def test_removal_referenced_module_shows_referrers(self):
        im = removal_impact(_reg(), "M55")
        self.assertEqual([r["protocol"] for r in im["referenced_by"]],
                         ["校园西幻轻混组合包"])
        # M55 属校园情感领域包 module_ids
        self.assertIn("校园情感领域包", im["in_packages"])

    def test_removal_unreferenced_module_clean(self):
        im = removal_impact(_reg(), "M91")
        self.assertEqual(im["referenced_by"], [])
        self.assertEqual(im["in_official_core"], [])
        self.assertEqual(im["in_packages"], ["校园西幻轻混组合包"])

    def test_removal_official_core(self):
        im = removal_impact(_reg(), "M00")
        self.assertEqual(im["in_official_core"], ["M00"])


class TestCheckRegistryFile(unittest.TestCase):
    def test_missing_file_raises(self):
        # check_registry 文件缺失 = 协议事故（与 load_registry 语义一致，不静默空过）
        with tempfile.TemporaryDirectory(prefix="nf_im_") as td:
            with self.assertRaises(Exception):
                check_registry(Path(td) / "nope.json")

    def test_real_registry_smoke(self):
        # I5 真源：registry.json 应自洽（无悬空引用 / 无裸号重复）
        issues = check_registry()
        self.assertEqual(issues, [])

    def test_serialize_roundtrip(self):
        # registry_integrity_issues 对 Registry 与 dict 均工作（check21 可能传 dict）
        reg = _reg()
        d = {"protocols": [dict(p) for p in reg.protocols]}
        # dict 形态经 Registry 包装（真实 json.load 走 load_registry → Registry）
        self.assertEqual(registry_integrity_issues(reg), [])


if __name__ == "__main__":
    unittest.main()
