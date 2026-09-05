"""协议投影生成器测试（v2.1.0 B3-A：protocol.yaml → registry protocols[] 条目）。

锚点：project_all 产物 == registry.json protocols[] 现有 4 条目（逐字段）；
生成器与 check14 ⑦ 元素级断言同构——产物天然过门禁（集成自证见 test 尾部）。
"""
import json
import os
import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.protocol_projection import _layer_key, project_all, project_entry  # noqa: E402

REGISTRY = Path(__file__).resolve().parent.parent / "src" / "core" / "registry.json"
COMMUNITY = Path(__file__).resolve().parent.parent.parent / "community"
VERIFY = Path(__file__).resolve().parent.parent.parent / "verify.sh"


def _reg_protocols():
    with open(REGISTRY, encoding="utf-8") as f:
        reg = json.load(f)
    return {p["id"]: p for p in reg.get("protocols", [])}


class ProjectionAnchorTest(unittest.TestCase):
    """回归锚点：生成产物与 registry 现有条目逐字段一致（字段与 C1 ⑦ 断言同构）。"""

    @classmethod
    def setUpClass(cls):
        cls.prots = _reg_protocols()
        cls.entries = {e["id"]: e for e in project_all(COMMUNITY)}

    def test_id_set_matches_registry(self):
        self.assertEqual(set(self.entries), set(self.prots))

    def test_entry_fields_match_registry(self):
        for pid, reg in self.prots.items():
            gen = self.entries[pid]
            with self.subTest(pkg=pid):
                self.assertEqual(gen["pipeline"], reg["pipeline"])
                self.assertEqual(gen["categories"], reg["categories"])
                self.assertEqual(gen["schema_version"], reg["schema_version"])
                # C1 ⑦ 元素级全序：module_ids 逐条 == module_id_range
                self.assertEqual(gen["module_ids"], reg["module_ids"])
                self.assertEqual(gen["assets"], reg["assets"])
                self.assertEqual(gen["references"], reg["references"])
                self.assertEqual(gen["mount_layers"], reg["mount_layers"])

    def test_lightmix_references_projected(self):
        """轻混组合包 references 入产物（含 asset_readonly/source_schema_version）。"""
        gen = self.entries["校园西幻轻混组合包"]
        reg = self.prots["校园西幻轻混组合包"]
        self.assertEqual(len(gen["references"]), 2)
        self.assertEqual(gen["references"], reg["references"])
        for r in gen["references"]:
            for k in ("source_package", "module_id", "source_schema_version", "asset_readonly"):
                self.assertIn(k, r)


class ProjectionLayerTest(unittest.TestCase):
    """mount_layers 键归一与层名推断（protocol 长键 → registry 短键形态）。"""

    @classmethod
    def setUpClass(cls):
        cls.prots = _reg_protocols()

    def test_layer_key_normalizes(self):
        self.assertEqual(_layer_key("P40 行为决策"), "P40")
        self.assertEqual(_layer_key("P40"), "P40")

    def test_generated_layer_shape_matches_registry(self):
        """层内含 name（protocol 无 name 时取长键第二段），default/available 透传。"""
        pkg_dir = os.path.join(COMMUNITY, "校园情感领域包")
        entry = project_entry(pkg_dir)
        reg = self.prots["校园情感领域包"]
        for key in ("P20", "P40", "P50", "P60"):
            with self.subTest(layer=key):
                self.assertIn(key, entry["mount_layers"])
                self.assertEqual(entry["mount_layers"][key]["name"], reg["mount_layers"][key]["name"])
                self.assertEqual(entry["mount_layers"][key]["default"], reg["mount_layers"][key]["default"])
                self.assertEqual(entry["mount_layers"][key]["available"], reg["mount_layers"][key]["available"])


class GateIsomorphismTest(unittest.TestCase):
    """集成自证：生成产物合并回 registry → check14 ⑦ 元素级比对通过（同构验证）。

    不落盘真实 registry：在内存副本上跑与 verify.sh check14 ⑦ 同构的元素级断言。
    """

    def test_generated_entries_pass_element_wise_gate(self):
        reg = _reg_protocols()
        errs = []
        for pid, entry in {e["id"]: e for e in project_all(COMMUNITY)}.items():
            p = reg.get(pid)
            if not p:
                errs.append("缺 registry 条目: %s" % pid)
                continue
            if p["pipeline"] != entry["pipeline"]:
                errs.append("%s pipeline" % pid)
            if sorted(p["categories"]) != sorted(entry["categories"]):
                errs.append("%s categories" % pid)
            if p["schema_version"] != entry["schema_version"]:
                errs.append("%s schema_version" % pid)
            if [str(x) for x in p["module_ids"]] != [str(x) for x in entry["module_ids"]]:
                errs.append("%s module_ids" % pid)
            if p["assets"]["count"] != entry["assets"]["count"]:
                errs.append("%s assets.count" % pid)
            reg_ml = {_layer_key(k): v for k, v in p["mount_layers"].items()}
            if set(reg_ml) != set(entry["mount_layers"]):
                errs.append("%s mount_layers 层集" % pid)
            else:
                for lid in sorted(reg_ml):
                    for f in ("default", "available"):
                        rv = (reg_ml[lid].get(f) or []) if isinstance(reg_ml[lid], dict) else []
                        pv = entry["mount_layers"][lid].get(f) or []
                        if (rv or []) != (pv or []):
                            errs.append("%s 层%s %s" % (pid, lid, f))
        self.assertEqual(errs, [])

    def test_expected_projection_error_message(self):
        """⑦ 断言错误消息文本（生成物与门禁共享语义的回归锚）。"""
        with open(VERIFY, encoding="utf-8") as f:
            verify_src = f.read()
        self.assertIn("module_ids 与 module_id_range 不一致（元素级）", verify_src)
        self.assertIn("mount_layers 层集不一致", verify_src)


if __name__ == "__main__":
    unittest.main()
