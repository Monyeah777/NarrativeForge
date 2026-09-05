# -*- coding: utf-8 -*-
"""协议定义向导单测（v2.0.x-E2：ProtocolForm → protocol.yaml v2 生成 + self_check）。

运行：cd desktop && python -m unittest tests.test_protocol_wizard -v
结构对齐 01 §6.1 Schema v2 + 真实实例（community/通用核心基础包 + 校园包 protocol.yaml）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.protocol_wizard import (  # noqa: E402
    ProtocolForm, build_protocol_yaml, self_check, DEFAULT_CORE_MODULES)


def _sample_form():
    return ProtocolForm(
        id="灵异校园包",
        name="灵异校园包",
        pipeline="P02",
        module_id_range=["M66", "M67"],
        categories=["灵异"],
        modules=[("M66", "灵异事件触发"), ("M67", "鬼怪出没规则")],
        mount_layers={
            "P30 事件": {"default": ["M66"], "available": []},
            "P40 行为决策": {"default": ["M67"], "available": []},
        })


class TestBuildProtocolYAML(unittest.TestCase):
    def setUp(self):
        self.form = _sample_form()

    def test_yaml_contains_required_structure(self):
        text = build_protocol_yaml(self.form)
        # 顶部声明 + schema_version v2
        self.assertIn("protocol.yaml", text)
        self.assertIn('schema_version: "2"', text)
        # package 关键字段
        self.assertIn("id: 灵异校园包", text)
        self.assertIn("pipeline: P02", text)
        self.assertIn("categories:", text)
        self.assertIn("- 灵异", text)
        # 结构字段自动填
        self.assertIn("references: []", text)
        self.assertIn("cross_package: []", text)
        # modules 清单 + 挂载层
        self.assertIn("M66", text)
        self.assertIn("灵异事件触发", text)
        self.assertIn("P30 事件:", text)

    def test_core_modules_default_present(self):
        text = build_protocol_yaml(self.form)
        self.assertIn("core_only: true", text)
        self.assertIn(DEFAULT_CORE_MODULES[0], text)   # 官方核心集首项在 core_modules

    def test_yaml_parses_and_keys(self):
        import yaml
        text = build_protocol_yaml(self.form)
        # 剥注释行后解析
        body = "\n".join(l for l in text.splitlines()
                         if not l.strip().startswith("#"))
        data = yaml.safe_load(body)
        self.assertEqual(data["protocol"]["schema_version"], "2")
        self.assertEqual(data["package"]["id"], "灵异校园包")
        self.assertEqual(len(data["package"]["modules"]), 2)


class TestSelfCheck(unittest.TestCase):
    def test_valid_form_passes(self):
        text = build_protocol_yaml(_sample_form())
        self.assertEqual(self_check(text), [])

    def test_module_id_range_empty_fails(self):
        f = _sample_form()
        f.module_id_range = []
        text = build_protocol_yaml(f)
        self.assertTrue(any("编号" in w or "module_id" in w
                            for w in self_check(text)))

    def test_mount_default_not_in_range_fails(self):
        f = _sample_form()
        f.mount_layers = {"P40 行为决策": {"default": ["M99"], "available": []}}
        text = build_protocol_yaml(f)
        self.assertTrue(any("挂载" in w or "default" in w or "M99" in w
                            for w in self_check(text)))


if __name__ == "__main__":
    unittest.main()
