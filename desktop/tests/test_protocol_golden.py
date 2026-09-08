#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""43 A4 —— 生成物同仓 golden 单测（确定性 + 双源一致 + 过期可检出）。"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import protocol_golden as pg  # noqa: E402


class ProtocolGoldenTest(unittest.TestCase):
    def test_repo_golden_clean(self):
        issues, stats = pg.verify_golden(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["schema_ids"], 5)

    def test_render_deterministic(self):
        data = pg.collect(ROOT)
        self.assertEqual(pg.render_json(data), pg.render_json(data))
        self.assertEqual(pg.render_markdown(data), pg.render_markdown(data))

    def test_generated_report_is_json(self):
        data = json.load(open(os.path.join(ROOT, "protocol", "generated", "idl_report.json"), encoding="utf-8"))
        self.assertEqual(len(data["schema_ids"]), 5)
        self.assertGreaterEqual(data["coverage"]["contract_covered"], 20)


if __name__ == "__main__":
    unittest.main()
