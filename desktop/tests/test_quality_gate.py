# -*- coding: utf-8 -*-
"""质量治理门单测（v1.4.0 quality_gate：三态质检门，2.0 E0-③）。

运行：cd desktop && python -m unittest tests.test_quality_gate -v
隔离：纯 IR 结构构造（IRDocument），无 store/GUI 依赖。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.ir import IRDocument, IRLayer, IRModule  # noqa: E402
from core.quality_gate import run_gate, default_rules, GateResult, Issue  # noqa: E402


def _ir(layers=None, extra=None, missing=None):
    return IRDocument(
        title="测试", pipeline_id="P01", pipeline_name="标准",
        layers=layers or [], extra_modules=extra or [],
        asset_refs={}, asset_missing=missing or [],
    )


class TestRunGate(unittest.TestCase):
    def test_empty_assembly_fails(self):
        ir = _ir()   # 无任何层模块
        res = run_gate(ir)
        self.assertIsInstance(res, GateResult)
        self.assertGreaterEqual(res.n_fail, 1)
        self.assertFalse(res.ok())
        levels = {i.level for i in res.issues}
        self.assertIn("fail", levels)

    def test_missing_core_anchor_fails(self):
        # 只有中间层模块，缺 P00/P80 锚点
        ir = _ir(layers=[IRLayer(id="P30", name="事件", modules=[
            IRModule(full_id="事件类:M22", name="事件叙事", layer="P30",
                     content="正文")])])
        res = run_gate(ir)
        self.assertGreaterEqual(res.n_fail, 1)
        self.assertFalse(res.ok())

    def test_asset_missing_warns(self):
        ir = _ir(
            layers=[IRLayer(id="P00", name="基座", modules=[
                IRModule(full_id="通用类:M00", name="数据结构", layer="P00",
                         content="正文")]),
                IRLayer(id="P80", name="输出", modules=[
                    IRModule(full_id="通用类:M80", name="输出生成器", layer="P80",
                             content="正文")])],
            missing=["NOPE_KEY"])
        res = run_gate(ir)
        # 锚点齐全 → fail 0；资产悬空 → warn 计入
        self.assertEqual(res.n_fail, 0)
        self.assertGreaterEqual(res.n_warn, 1)
        self.assertTrue(res.ok())
        self.assertTrue(any("NOPE_KEY" in i.message
                            for i in res.issues if i.level == "warn"))

    def test_valid_assembly_ok(self):
        ir = _ir(layers=[
            IRLayer(id="P00", name="基座", modules=[
                IRModule(full_id="通用类:M00", name="数据结构", layer="P00",
                         content="正文")]),
            IRLayer(id="P30", name="事件", modules=[
                IRModule(full_id="事件类:M22", name="事件叙事", layer="P30",
                         content="正文")]),
            IRLayer(id="P80", name="输出", modules=[
                IRModule(full_id="通用类:M80", name="输出生成器", layer="P80",
                         content="正文")])])
        res = run_gate(ir)
        self.assertEqual(res.n_fail, 0)
        self.assertTrue(res.ok())

    def test_extra_module_warns(self):
        ir = _ir(
            layers=[IRLayer(id="P00", name="基座", modules=[
                IRModule(full_id="通用类:M00", name="数据结构", layer="P00",
                         content="正文")]),
                IRLayer(id="P80", name="输出", modules=[
                    IRModule(full_id="通用类:M80", name="输出生成器", layer="P80",
                             content="正文")])],
            extra=[IRModule(full_id="通用类:M50", name="主循环", layer="P50",
                            content="正文")])
        res = run_gate(ir)
        self.assertEqual(res.n_fail, 0)
        self.assertGreaterEqual(res.n_warn, 1)   # 层外模块 warn
        self.assertTrue(res.ok())

    def test_rule_fail_blocks_ok(self):
        # 明确 fail 存在时 ok() 必须 False（可信任度：fail 阻断通过）
        res = run_gate(_ir())
        self.assertFalse(res.ok())
        self.assertEqual(res.n_pass, 0 if not res.issues else res.n_pass)


if __name__ == "__main__":
    unittest.main()
