# -*- coding: utf-8 -*-
"""导出层 exporter 单测（v2.0.0 T2：格式注册表 + CCV3 JSON/PNG 封装）。

运行：cd desktop && QT_QPA_PLATFORM=offscreen python -m unittest tests.test_exporter -v
覆盖：export('ccv3') 产 chara.json（spec 锚点+内嵌 character_book）+ world.json；
      PNG 卡（QImage tEXt chara 键，base64 回读 = chara JSON）；未知 fmt 报告。
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from core.ir import IRDocument, IRLayer, IRModule  # noqa: E402
from core.exporter import export, ExportResult, write_png_card  # noqa: E402


def _ir():
    return IRDocument(
        title="校园试炼", pipeline_id="P02", pipeline_name="校园情感流",
        layers=[IRLayer(id="P40", name="行为决策", modules=[
            IRModule(full_id="情感类:M40", name="关系推进", layer="P40",
                     content="好感度规则")])],
        asset_refs={}, asset_missing=[],
        meta={"timestamp": "2026-09-05 00:00"})


class TestExport(unittest.TestCase):
    def setUp(self):
        self.ir = _ir()
        self.dest = tempfile.mkdtemp(prefix="nf_exp_")

    def test_export_ccv3_produces_json_files(self):
        res = export(self.ir, "ccv3", dest_dir=self.dest)
        self.assertIsInstance(res, ExportResult)
        self.assertIn("ccv3", res.fmt)
        names = [os.path.basename(f) for f in res.files]
        self.assertIn("chara.json", names)
        self.assertIn("world.json", names)
        for f in res.files:
            self.assertTrue(os.path.exists(f))

    def test_chara_json_spec_anchor_and_book(self):
        export(self.ir, "ccv3", dest_dir=self.dest)
        chara = json.loads(Path(self.dest, "chara.json")
                           .read_text(encoding="utf-8"))
        self.assertEqual(chara.get("spec"), "chara_card_v3")
        self.assertIn("character_book", chara)
        self.assertGreaterEqual(len(chara["character_book"]["entries"]), 1)

    def test_world_json_entries(self):
        export(self.ir, "ccv3", dest_dir=self.dest)
        world = json.loads(Path(self.dest, "world.json")
                           .read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(world["entries"]), 1)
        self.assertEqual(world["entries"][0]["keys"][0], "情感类:M40")

    def test_unknown_format_reports(self):
        with self.assertRaises(KeyError):
            export(self.ir, "nope", dest_dir=self.dest)


class TestPNGCard(unittest.TestCase):
    def test_png_embeds_chara_text(self):
        ir = _ir()
        p = os.path.join(tempfile.mkdtemp(prefix="nf_png_"), "card.png")
        write_png_card(ir, p)
        self.assertTrue(os.path.exists(p))
        from PySide6.QtGui import QImage
        img = QImage(p)
        txt = img.text("chara")
        self.assertTrue(txt)
        decoded = base64.b64decode(txt).decode("utf-8")
        card = json.loads(decoded)
        self.assertEqual(card.get("spec"), "chara_card_v3")


if __name__ == "__main__":
    unittest.main()
