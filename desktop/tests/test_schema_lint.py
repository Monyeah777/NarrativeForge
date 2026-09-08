#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""43 A1 —— 协议层 IDL schema 校验器单测（自实现 JSON-schema 子集 + 全量件扫描）。"""
import os
import unittest

import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import schema_lint as sl  # noqa: E402


class SchemaSubsetValidatorTest(unittest.TestCase):
    def test_type_and_required_catch(self):
        schema = {
            "type": "object",
            "required": ["id", "events"],
            "properties": {
                "id": {"type": "string", "pattern": "^M[0-9]{2}$"},
                "count": {"type": "integer", "minimum": 0},
                "events": {
                    "type": "object",
                    "required": ["publish"],
                    "properties": {"publish": {"type": "array", "items": {"type": "string"}}},
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        }
        msgs = sl.subset_validate({"id": 12, "count": -1, "extra": 1}, schema)
        joined = "\n".join(msgs)
        self.assertIn("缺必填字段 events", joined)
        self.assertIn("应为 string", joined)
        self.assertIn("未知字段 extra", joined)

    def test_real_contract_mutation_detected(self):
        """真实机读块逐字段变异 → 均被 schema 拦截（漂移即 FAIL 的实证）。"""
        m00 = os.path.join(ROOT, "04_模块库", "通用类", "M00_数据结构.md")
        with open(m00, encoding="utf-8") as fh:
            text = fh.read()
        parsed = sl._fence_yaml(text, "machine_contract")
        self.assertIsNotNone(parsed)
        mc = parsed["machine_contract"]
        schema = sl.load_schema(ROOT, "contract.schema.json")
        self.assertIsNotNone(schema)
        # 基线：原样零违例
        self.assertEqual(sl.subset_validate(mc, schema), [])
        # 枚举变异
        mut = dict(mc, schema="2")
        self.assertTrue(any("枚举" in m for m in sl.subset_validate(mut, schema)))
        # pattern 变异
        mut = dict(mc, id="X1")
        self.assertTrue(any("pattern" in m for m in sl.subset_validate(mut, schema)))
        # 类型变异
        mut = dict(mc, name=123)
        self.assertTrue(any("应为 string" in m for m in sl.subset_validate(mut, schema)))
        # 必填删除（events.subscribe 缺键）
        events = dict(mc["events"])
        del events["subscribe"]
        mut = dict(mc, events=events)
        self.assertTrue(any("未知字段" in m or "缺必填" in m for m in sl.subset_validate(mut, schema)))
        # 事件对象内未知字段
        events = dict(mc["events"], extra_event="x")
        mut = dict(mc, events=events)
        self.assertTrue(any("未知字段 extra_event" in m for m in sl.subset_validate(mut, schema)))


class SchemaScanTest(unittest.TestCase):
    def test_schema_files_meta(self):
        issues, schemas = sl.check_schema_files(ROOT)
        self.assertEqual(issues, [])
        self.assertEqual(len(schemas), 5)

    def test_repo_scan_clean(self):
        issues, stats = sl.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["module_docs"], 40)
        self.assertGreaterEqual(stats["contract_covered"], 20)
        self.assertGreaterEqual(stats["pipelines"], 8)
        self.assertGreaterEqual(stats["protocols"], 5)
        self.assertGreaterEqual(stats["asset_entries"], 2)
        self.assertEqual(stats["schema_files"], 5)


if __name__ == "__main__":
    unittest.main()
