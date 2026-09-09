#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 · 载荷注册表单测（自校验 + 防死注册）。"""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import payload_registry as pr  # noqa: E402


class PayloadRegistryTest(unittest.TestCase):
    def test_repo_registry_clean(self):
        issues, stats = pr.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["registered"], 5)

    def test_registry_dead_event_captured(self):
        import tempfile
        from core import schema_lint as sl

        schema = json.loads((Path(ROOT) / "protocol/event_payload.schema.json")
                            .read_text(encoding="utf-8"))
        reg = json.loads((Path(ROOT) / "protocol/event_registry.json")
                         .read_text(encoding="utf-8"))
        reg["events"]["never_fired_anywhere"] = {"fields": {"x": {"type": "string"}}}
        self.assertEqual(sl.subset_validate(reg, schema), [])


if __name__ == "__main__":
    unittest.main()
