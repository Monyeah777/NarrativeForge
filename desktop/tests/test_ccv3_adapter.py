# -*- coding: utf-8 -*-
"""CCV3 映射层单测（v2.0.0 T1：IR→chara_card_v3 + world entries）。

运行：cd desktop && python -m unittest tests.test_ccv3_adapter -v
映射规则（17 方案 §B1）：P00/P80 引擎锚点不导叙事；叙事层模块 → world 条目
（key=层:full_id）；资产 → 独立条目；persona 主角占位；spec 锚点 chara_card_v3。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.ir import IRDocument, IRLayer, IRModule  # noqa: E402
from core.ccv3_adapter import map_ir_to_ccv3, world_entries  # noqa: E402


def _ir():
    return IRDocument(
        type="narrative", title="校园试炼", pipeline_id="P02",
        pipeline_name="校园情感流",
        layers=[
            IRLayer(id="P00", name="基座", modules=[
                IRModule(full_id="通用类:M00", name="数据结构", layer="P00",
                         content="数据槽定义")]),
            IRLayer(id="P30", name="事件", modules=[
                IRModule(full_id="事件类:M06", name="任务剧情", layer="P30",
                         content="开局事件：入学试炼触发")]),
            IRLayer(id="P40", name="行为决策", modules=[
                IRModule(full_id="情感类:M40", name="关系推进", layer="P40",
                         content="好感度规则：互动累积")]),
            IRLayer(id="P80", name="输出", modules=[
                IRModule(full_id="通用类:M80", name="输出生成器", layer="P80",
                         content="生成器")]),
        ],
        asset_refs={"ATTR_TEMPLATES": "角色模板库内容"},
        asset_missing=[],
        meta={"timestamp": "2026-09-05 00:00"})


class TestMapIRToCCV3(unittest.TestCase):
    def setUp(self):
        self.ir = _ir()

    def test_spec_anchor_and_name(self):
        chara = map_ir_to_ccv3(self.ir)
        self.assertEqual(chara.get("spec"), "chara_card_v3")
        self.assertEqual(chara.get("spec_version"), "v3")
        self.assertEqual(chara.get("name"), "校园试炼")

    def test_persona_placeholder_semantics(self):
        # NF 装配 = 世界观非单角色：persona 为引导占位，不伪称角色定义
        persona = map_ir_to_ccv3(self.ir).get("personality", "")
        self.assertIn("主角", persona)   # 占位语义引导

    def test_character_book_excludes_engine_anchors(self):
        # P00/P80 引擎锚点（数据结构/输出生成器）不导叙事 world
        cb = map_ir_to_ccv3(self.ir).get("character_book") or {}
        entries = cb.get("entries") or []
        keys = "".join("".join(e.get("keys") or []) for e in entries)
        self.assertIn("M06", keys)
        self.assertIn("M40", keys)
        self.assertNotIn("M00", keys)     # P00 排除
        self.assertNotIn("M80", keys)     # P80 排除

    def test_asset_entry_present(self):
        cb = map_ir_to_ccv3(self.ir).get("character_book") or {}
        entries = cb.get("entries") or []
        content_all = "\n".join(e.get("content", "") for e in entries)
        self.assertIn("角色模板库", content_all)

    def test_scenario_derived(self):
        # scenario = 叙事入口模块内容或引导
        scen = map_ir_to_ccv3(self.ir).get("scenario") or ""
        self.assertTrue(len(scen) > 0)


class TestWorldEntries(unittest.TestCase):
    def setUp(self):
        self.ir = _ir()

    def test_entry_keys_use_full_id(self):
        entries = world_entries(self.ir)
        entry40 = next(e for e in entries if "M40" in (e.get("keys") or [""])[0])
        self.assertIn("情感类:M40", entry40["keys"])

    def test_every_rule_module_mapped_no_silent_drop(self):
        entries = world_entries(self.ir)
        # 叙事层模块 M06/M40 都在；P00/P80 引擎锚点被显式排除（非静默丢弃——映射规则声明）
        mapped = "".join("".join(e.get("keys") or []) for e in entries)
        self.assertIn("M06", mapped)
        self.assertIn("M40", mapped)


if __name__ == "__main__":
    unittest.main()
