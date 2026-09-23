#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""域包自由组合单测：五不变量 / 传递闭包 / references 借入 / 证书 T4 复算 / 广度抽样。

负例取自组合引擎的真实失效类：未知包、悬挂依赖、未桥事件、未解析引用、层栈不稳定。
"""
import json
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import pack_combo as pc  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


class CombineTest(unittest.TestCase):
    def test_two_packs_legal_and_stacked(self):
        c = pc.combine(ROOT, packs=["大语言模型域包", "视觉模型域包"])
        self.assertTrue(c["legal"], c)
        self.assertEqual(c["module_count"], 4)
        self.assertEqual(sorted(c["layer_stacks"]), ["P40", "P60"])
        self.assertEqual(len(c["layer_stacks"]["P40"]), 2)   # 同层两包默认 → 堆叠

    def test_layer_stack_order_is_canonical(self):
        a = pc.combine(ROOT, packs=["大语言模型域包", "视觉模型域包"])
        b = pc.combine(ROOT, packs=["视觉模型域包", "大语言模型域包"])
        self.assertEqual(a["layer_stacks"], b["layer_stacks"],
                         "层栈顺序须与调用者给序无关（否则 T4 复算假失败）")
        self.assertEqual(a["digest"], b["digest"])

    def test_all_packs_combination_is_legal(self):
        names = sorted(pc.profiles(ROOT))
        c = pc.combine(ROOT, packs=names)
        self.assertTrue(c["legal"], c["dependency_closure"]["dangling"][:3])
        self.assertGreater(c["module_count"], 200)
        self.assertEqual(c["dependency_closure"]["dangling"], [])
        self.assertEqual(c["event_closure"]["unbridged"], [])

    def test_references_are_pulled_transitively(self):
        """轻混组合包借源包模块 → 闭包须连带拉入其 inputs 与事件发布方。"""
        c = pc.combine(ROOT, packs=["校园西幻轻混组合包", "AI保险域包"])
        self.assertTrue(c["legal"], c["event_closure"]["unbridged"])
        pulled = {b["module"] for b in c["modules_borrowed"]}
        self.assertIn("M43", pulled)

    def test_component_level_mix(self):
        c = pc.combine(ROOT, extra_modules=["大语言模型:M01", "视觉模型:M01", "数据采集与清洗:M01"],
                       extra_assets=["量化金融域包:QUANT_METRICS"])
        self.assertTrue(c["legal"], c)
        self.assertEqual(c["module_count"], 3)
        self.assertEqual(c["assets_borrowed"][0]["key"], "QUANT_METRICS")
        self.assertEqual(c["assets_borrowed"][0]["mode"], "asset_readonly")

    def test_unknown_pack_is_illegal(self):
        c = pc.combine(ROOT, packs=["不存在的域包"])
        self.assertFalse(c["legal"])
        self.assertEqual(c["unknown_packs"], ["不存在的域包"])

    def test_certificate_is_reproducible(self):
        cert = pc.combine(ROOT, packs=["大语言模型域包", "数据采集与清洗域包"])
        again = pc.combine(ROOT, packs=["大语言模型域包", "数据采集与清洗域包"])
        self.assertEqual(cert["digest"], again["digest"])
        issues, _ = pc.verify_certificate(ROOT, cert)
        self.assertEqual(issues, [])

    def test_declared_certificates_match_recompute(self):
        doc = pc.declared(ROOT)
        self.assertTrue(doc.get("certificates"), "证书台账不得为空")
        for cert in doc["certificates"]:
            issues, st = pc.verify_certificate(ROOT, cert)
            self.assertEqual(issues, [], cert.get("label"))
            self.assertTrue(st["legal"], cert.get("label"))

    def test_breadth_sample_all_legal(self):
        stats = pc.breadth(ROOT, triple_sample=30, quad_sample=15)
        self.assertTrue(stats["all_legal"], stats["failures"][:2])
        self.assertEqual(stats["pairs"], stats["pairs_legal"])

    def test_certificate_schema_rejects_extra_field(self):
        from core import output_forms as of
        bad = dict(pc.combine(ROOT, packs=["大语言模型域包"]))
        bad["surprise"] = 1
        errs = of.json_schema_check(bad, pc.CERT_SCHEMA)
        self.assertTrue(any("多余字段" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
