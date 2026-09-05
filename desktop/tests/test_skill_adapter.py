# -*- coding: utf-8 -*-
"""SKILL 出口适配器单测（v2.0.x 插件：techdoc IR → SKILL.md，产物矩阵第二行）。

运行：cd desktop && python -m unittest tests.test_skill_adapter -v
矩阵约束（18 方案）：SKILL 只接指令/协议类装配（IR.type=techdoc）；narrative IR
请求 skill → 拒（0 文件 + warning，语义错配防混）。
格式锚点（agentskills.io）：目录 + SKILL.md，YAML frontmatter name/description 必填。
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.ir import IRDocument, IRLayer, IRModule  # noqa: E402
from core.exporter import export  # noqa: E402


def _techdoc_ir():
    """技术文档类 IR（P90 语义：指令/协议/操作规格）。"""
    return IRDocument(
        type="techdoc", title="模组协议生成规范", pipeline_id="P90",
        pipeline_name="技术文档生成管线",
        layers=[IRLayer(id="P10", name="结构", modules=[
            IRModule(full_id="技术文档类:M90", name="技术文档结构", layer="P10",
                     content="协议文档必须含：前置声明/字段表/示例三段。")])],
        asset_refs={}, asset_missing=[], meta={})


def _narrative_ir():
    return IRDocument(
        type="narrative", title="校园试炼", pipeline_id="P02",
        pipeline_name="校园情感流",
        layers=[IRLayer(id="P40", name="决策", modules=[
            IRModule(full_id="情感类:M40", name="关系推进", layer="P40",
                     content="好感度规则")])],
        asset_refs={}, asset_missing=[], meta={})


class TestSkillAdapter(unittest.TestCase):
    def setUp(self):
        self.dest = Path(tempfile.mkdtemp(prefix="nf_skill_"))

    def test_techdoc_export_produces_skill_md(self):
        res = export(_techdoc_ir(), "skill", dest_dir=self.dest)
        files = [Path(f) for f in res.files]
        self.assertTrue(files)
        skill = next(f for f in files if f.name == "SKILL.md")
        text = skill.read_text(encoding="utf-8")
        # agentskills 格式：YAML frontmatter 必填 name/description
        self.assertIn("---", text)
        self.assertIn("name:", text)
        self.assertIn("description:", text)
        # 正文含层序模块内容
        self.assertIn("M90", text)

    def test_narrative_ir_rejected_no_file(self):
        res = export(_narrative_ir(), "skill", dest_dir=self.dest)
        self.assertEqual(res.files, [])           # 语义错配拒绝，不产文件
        self.assertTrue(res.warnings)             # 有说明警告
        self.assertTrue(any("CCV3" in w or "narrative" in w.lower()
                            for w in res.warnings))

    def test_skill_md_frontmatter_valid_shape(self):
        res = export(_techdoc_ir(), "skill", dest_dir=self.dest)
        text = Path(res.files[0]).read_text(encoding="utf-8")
        head = text.split("---", 2)[1]            # frontmatter 块
        name = re.search(r"^name:\s*(.+)$", head, re.M)
        desc = re.search(r"^description:\s*(.+)$", head, re.M)
        self.assertTrue(name and name.group(1).strip())
        self.assertTrue(desc and desc.group(1).strip())


if __name__ == "__main__":
    unittest.main()
