# -*- coding: utf-8 -*-
"""ST 制卡校验器原型（A-S3）单测：**自造 fixture**（非真实卡，仅验证判据）。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import st_validator as sv  # noqa: E402


class TestCard(unittest.TestCase):
    def test_v2_clean_passes(self):
        doc = {"spec": "chara_card_v2", "spec_version": "2.0",
               "data": {"name": "n", "description": "d", "personality": "p",
                        "scenario": "s", "first_mes": "f", "mes_example": "m"}}
        self.assertEqual(sv.check_card(doc), [])

    def test_v2_wrong_spec_version_is_fail(self):
        doc = {"spec": "chara_card_v2", "spec_version": "1.0", "data": {}}
        rules = {i["rule"] for i in sv.check_card(doc)}
        self.assertIn("C2", rules)
        self.assertIn("C3", rules)

    def test_v1_flat_needs_six_fields(self):
        doc = {"name": "n", "description": "d"}          # V1 平铺
        self.assertTrue(any(i["rule"] == "C3" for i in sv.check_card(doc)))


class TestWorldbook(unittest.TestCase):
    def test_missing_entries_is_fail(self):
        self.assertTrue(any(i["rule"] == "W1" for i in sv.check_worldbook({})))

    def test_comma_key_and_duplicate_are_warn(self):
        doc = {"entries": {"0": {"keys": ["a,b"], "content": "x"},
                           "1": {"keys": ["a,b"], "content": "y"}}}
        issues = sv.check_worldbook(doc)
        self.assertTrue(any(i["rule"] == "W2" for i in issues))


class TestMvu(unittest.TestCase):
    def test_initial_mismatch_is_fail(self):
        doc = {"variables": [{"name": "a"}, {"name": "b"}], "initial": {"a": 1, "z": 2}}
        rules = {i["rule"] for i in sv.check_mvu_variables(doc)}
        self.assertIn("V2", rules)

    def test_array_and_prefix_are_advisory(self):
        doc = {"variables": [{"name": "_x", "kind": "array"}], "initial": {"_x": []}}
        issues = sv.check_mvu_variables(doc)
        self.assertTrue(any(i["rule"] == "V4" and i["severity"] == "warn" for i in issues))
        self.assertTrue(any(i["rule"] == "V5" for i in issues))


class TestDispatch(unittest.TestCase):
    def test_validate_real_mvu_artifact(self):
        rep = sv.validate(str(ROOT / "docs/examples/mvu-output/mvu_variables.json"))
        self.assertEqual(rep["kind"], "mvu-variables")
        self.assertEqual([i for i in rep["issues"] if i["severity"] == "fail"], [])
        self.assertIn("# ST 制卡校验报告", sv.report_markdown(rep))

    def test_unknown_shape_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "x.json")
            p.write_text(json.dumps({"hello": 1}), encoding="utf-8")
            self.assertEqual(sv.validate(str(p))["counts"]["fail"], 1)


if __name__ == "__main__":
    unittest.main()
