# -*- coding: utf-8 -*-
"""认知族（术语表 / 执行分档）正式与否定用例。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import cognition as cg  # noqa: E402


def _mk(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _scene(tmp, glossary=None, modes=None):
    _mk(tmp, "src.md", "这里出现 真源 一词\n")
    _mk(tmp, "use.md", "也用到 真源\n")
    _mk(tmp, "inst.md", "步骤\n预期\n")
    _mk(tmp, cg.GLOSSARY_REL, json.dumps(glossary or {
        "schema": cg.G_SCHEMA, "rules": ["r"],
        "terms": [{"term": "真源", "definition": "d", "source": "src.md",
                   "used_in": ["use.md"]}]}, ensure_ascii=False))
    _mk(tmp, cg.MODES_REL, json.dumps(modes or {
        "schema": cg.M_SCHEMA,
        "modes": [{"id": "runbook", "required_blocks": ["步骤", "预期"],
                   "instances": ["inst.md"]}]}, ensure_ascii=False))
    return tmp


class TestRealRepo(unittest.TestCase):
    def test_scan_clean(self):
        issues, _w, stats = cg.scan(str(ROOT))
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["glossary"]["terms"], 8)
        self.assertGreaterEqual(stats["modes"]["instances_ok"], 2)


class TestNegatives(unittest.TestCase):
    def test_term_absent_from_source_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), glossary={
            "schema": cg.G_SCHEMA, "rules": ["r"],
            "terms": [{"term": "不存在的行话", "definition": "d", "source": "src.md",
                       "used_in": []}]})
        self.assertTrue(any("未在其 source 中逐字出现" in i
                            for i in cg.verify_glossary(tmp)[0]))

    def test_term_absent_from_used_in_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), glossary={
            "schema": cg.G_SCHEMA, "rules": ["r"],
            "terms": [{"term": "真源", "definition": "d", "source": "src.md",
                       "used_in": ["inst.md"]}]})
        self.assertTrue(any("used_in 未逐字出现" in i for i in cg.verify_glossary(tmp)[0]))

    def test_duplicate_term_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), glossary={
            "schema": cg.G_SCHEMA, "rules": ["r"],
            "terms": [{"term": "真源", "definition": "d", "source": "src.md", "used_in": []},
                      {"term": "真源", "definition": "d2", "source": "src.md", "used_in": []}]})
        self.assertTrue(any("术语重复" in i for i in cg.verify_glossary(tmp)[0]))

    def test_instance_missing_blocks_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), modes={
            "schema": cg.M_SCHEMA,
            "modes": [{"id": "playbook", "required_blocks": ["角色", "决策"],
                       "instances": ["inst.md"]}]})
        self.assertTrue(any("不属于 playbook 档" in i for i in cg.verify_modes(tmp)[0]))

    def test_mode_without_instance_is_fail(self):
        tmp = _scene(tempfile.mkdtemp(), modes={
            "schema": cg.M_SCHEMA,
            "modes": [{"id": "runbook", "required_blocks": ["步骤"], "instances": []}]})
        self.assertTrue(any("无实例" in i for i in cg.verify_modes(tmp)[0]))


if __name__ == "__main__":
    unittest.main()
