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


def _book(card: dict) -> dict:
    """取世界书：v3 真形状在 `data` 内，v2 旧形状在顶层（两者都支持）。"""
    body = card.get("data") if isinstance(card.get("data"), dict) else card
    return body.get("character_book") or {}


class TestMapIRToCCV3(unittest.TestCase):
    def setUp(self):
        self.ir = _ir()

    def test_spec_anchor_and_name(self):
        chara = map_ir_to_ccv3(self.ir)
        self.assertEqual(chara.get("spec"), "chara_card_v3")
        # v2.4.0 A2 核查：SillyTavern validator 要求 Number(spec_version) ∈ [3.0,4.0)
        # ——"v3" 字符串经 Number() 得 NaN 校验 fail，须为数值字符串 "3.0"
        self.assertEqual(chara.get("spec_version"), "3.0")
        self.assertEqual(chara.get("name"), "校园试炼")

    def test_v3_real_shape_data_block_and_mirror(self):
        """v3 真形状（外部实证 2026-09-21）：内容字段在 `data` 内，顶层仅 v2 兼容镜像。"""
        chara = map_ir_to_ccv3(self.ir)
        self.assertIsInstance(chara.get("data"), dict)
        inner = chara["data"]
        for k in ("name", "description", "personality", "scenario", "first_mes",
                  "mes_example", "character_book", "extensions", "creator"):
            self.assertIn(k, inner, "data 缺字段 %s" % k)
        for k in ("name", "description", "personality", "scenario", "first_mes",
                  "mes_example"):
            self.assertEqual(chara[k], inner[k], "顶层镜像须与 data.%s 同源" % k)
        self.assertGreaterEqual(len(inner["character_book"]["entries"]), 1)

    def test_persona_placeholder_semantics(self):
        # NF 装配 = 世界观非单角色：persona 为引导占位，不伪称角色定义
        persona = map_ir_to_ccv3(self.ir).get("personality", "")
        self.assertIn("主角", persona)   # 占位语义引导

    def test_character_book_excludes_engine_anchors(self):
        # P00/P80 引擎锚点（数据结构/输出生成器）不导叙事 world
        cb = _book(map_ir_to_ccv3(self.ir))
        entries = cb.get("entries") or []
        keys = "".join("".join(e.get("keys") or []) for e in entries)
        self.assertIn("M06", keys)
        self.assertIn("M40", keys)
        self.assertNotIn("M00", keys)     # P00 排除
        self.assertNotIn("M80", keys)     # P80 排除

    def test_asset_entry_present(self):
        cb = _book(map_ir_to_ccv3(self.ir))
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


class TestScenarioHead(unittest.TestCase):
    """外部实测回归（2026-10-02）：scenario 不得硬切词、不得夹带机器契约围栏。

    实证缺陷：`_scenario_text` 原用 `content[:400]`，切口落在 `…arrow-py/arrow`
    的 `repo` 一词中段，且把 ```machine_contract``` 围栏带进玩家可见文本。
    """

    @staticmethod
    def _ir_with(content: str) -> IRDocument:
        return IRDocument(
            type="narrative", title="测试世界", pipeline_id="P04",
            pipeline_name="轻混装配流",
            layers=[IRLayer(id="P10", name="世界", modules=[
                IRModule(full_id="通用类:M10", name="时间推进", layer="P10",
                         content=content)])],
            asset_refs={}, asset_missing=[], meta={})

    def test_machine_contract_fence_excluded(self):
        ir = self._ir_with("时间推进规则：每十分钟一刻。\n\n```machine_contract\nstep: 17\n```\n")
        scen = map_ir_to_ccv3(ir)["scenario"]
        self.assertNotIn("machine_contract", scen)
        self.assertNotIn("```", scen)
        self.assertIn("每十分钟一刻", scen)

    def test_truncation_lands_on_a_sentence_boundary(self):
        # 200 句 × 6 字 → 远超 400；硬切必然落在句中
        body = "".join("第%03d句。" % i for i in range(200))
        scen = map_ir_to_ccv3(self._ir_with(body))["scenario"]
        head = scen.split("\n\n")[0]
        self.assertTrue(head.endswith("……"), "超限须以省略号收尾：%r" % head[-8:])
        self.assertEqual(head[-3], "。", "截断点须落在句读边界：%r" % head[-8:])

    def test_short_content_untouched(self):
        ir = self._ir_with("短说明，不截断。")
        self.assertIn("短说明，不截断。", map_ir_to_ccv3(ir)["scenario"])


if __name__ == "__main__":
    unittest.main()
