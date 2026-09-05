# -*- coding: utf-8 -*-
"""IR 内容归一化层单测（v1.2.0 协议中转站 v2，2.0 E0-①）。

运行：cd desktop && python -m unittest tests.test_ir -v
覆盖：render_ir 结构正确性（层序/模块 content 归一/资产 refs/缺失/extra）+ ir_to_md 序列化。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.models import Module, Pipeline, PipelineLayer, AssetPack  # noqa: E402
from core.ir import IRDocument, ir_to_md, normalize_module_body  # noqa: E402
from core.generator import render_ir  # noqa: E402


def _mk_module(mid, cat, layer, name, md, assets=None, enabled=True):
    m = Module(id=mid, category=cat, layer=layer, name=name,
               assets=assets or [], enabled=enabled)
    m.source_md = md
    return m


def _mk_pipeline():
    p = Pipeline(id="P01", name="标准管线")
    p.layers = [PipelineLayer(id="P00", name="基座", default_modules=["M00"]),
                PipelineLayer(id="P30", name="事件",
                              default_modules=["事件:M22"]),
                PipelineLayer(id="P80", name="输出", default_modules=["M80"])]
    return p


def _fixture():
    mods = [
        _mk_module("M00", "通用类", "P00", "数据结构",
                   "# M00 数据基座\n\n## 定义\n数据槽定义\n"),
        _mk_module("M22", "事件类", "P30", "事件叙事",
                   "# M22 事件\n\n## 职责\n事件推进\n", ["LOCATION"]),
        _mk_module("M80", "通用类", "P80", "输出生成器",
                   "# M80 输出\n\n## 职责\n生成文档\n"),
    ]
    ap = AssetPack(name="测试资产包", entries={"LOCATION": "教室/操场/天台"})
    return _mk_pipeline(), mods, ap


class TestNormalizeBody(unittest.TestCase):
    def test_heading_promoted(self):
        # 一级/二级标题提升为 ###/####（防干扰文档层级）
        body = normalize_module_body("# M00 基座\n\n## 定义\n内容")
        self.assertTrue(body.startswith("### M00 基座"))
        self.assertIn("#### 定义", body)

    def test_plain_body_kept(self):
        self.assertEqual(normalize_module_body("普通正文"), "普通正文")


class TestRenderIR(unittest.TestCase):
    def test_structure_layers_ordered(self):
        pipe, mods, ap = _fixture()
        ir = render_ir(pipe, mods, asset_pack=ap, title="测试")
        self.assertIsInstance(ir, IRDocument)
        self.assertEqual(ir.title, "测试")
        self.assertEqual(ir.type, "narrative")
        # 层间按管线层序 P00→P30→P80
        self.assertEqual([l.id for l in ir.layers], ["P00", "P30", "P80"])

    def test_module_content_normalized(self):
        pipe, mods, ap = _fixture()
        ir = render_ir(pipe, mods, asset_pack=ap)
        layer0 = ir.layers[0]
        self.assertEqual(len(layer0.modules), 1)
        m = layer0.modules[0]
        self.assertEqual(m.full_id, "通用类:M00")
        self.assertTrue(m.content.startswith("### M00 数据基座"))

    def test_asset_refs_and_missing(self):
        pipe, mods, ap = _fixture()
        ir = render_ir(pipe, mods, asset_pack=ap)
        self.assertEqual(ir.asset_refs.get("LOCATION"), "教室/操场/天台")
        self.assertEqual(ir.asset_missing, [])

    def test_extra_modules_outside_layers(self):
        pipe, mods, ap = _fixture()
        mods.append(_mk_module("M90", "技术文档类", "P90", "文档结构",
                               "# M90 结构\n\n正文"))
        ir = render_ir(pipe, mods, asset_pack=ap)
        self.assertEqual([m.layer for m in ir.extra_modules], ["P90"])

    def test_missing_asset_reported(self):
        pipe, mods, ap = _fixture()
        mods[1].assets = ["NOPE_KEY"]
        ir = render_ir(pipe, mods, asset_pack=ap)
        self.assertEqual(ir.asset_refs.get("NOPE_KEY"), None)
        self.assertEqual(ir.asset_missing, ["NOPE_KEY"])

    def test_disabled_module_excluded(self):
        pipe, mods, ap = _fixture()
        mods.append(_mk_module("M50", "通用类", "P50", "主循环",
                               "# M50 主循环", enabled=False))
        ir = render_ir(pipe, mods, asset_pack=ap)
        self.assertEqual([m.full_id for l in ir.layers for m in l.modules],
                         ["通用类:M00", "事件类:M22", "通用类:M80"])


class TestIRToMD(unittest.TestCase):
    def test_md_contains_structure(self):
        pipe, mods, ap = _fixture()
        ir = render_ir(pipe, mods, asset_pack=ap, title="测试文档")
        md = ir_to_md(ir)
        self.assertIn("# 测试文档", md)
        self.assertIn("层 P00 · 基座", md)
        self.assertIn("通用类:M00", md)
        self.assertIn("LOCATION", md)      # 资产附录
        # 关键顺序：目录 < 层内容 < 资产附录
        self.assertLess(md.index("## 目录"), md.index("层 P30"))
        self.assertLess(md.index("层 P80"), md.index("资产引用附录"))


if __name__ == "__main__":
    unittest.main()
