# -*- coding: utf-8 -*-
"""AGENTS/CLAUDE 出口适配器单测（v2.1.0 A1：techdoc+project_rules → AGENTS.md）。

运行：cd desktop && python -m unittest tests.test_agent_rules_adapter -v
矩阵约束（25 方案 A1）：AGENTS 出口只接「项目约定语义」装配
（classify_doc_semantics == project_rules，如 P90 装配产项目构建/提交/纪律规则）；
narrative IR 或 techdoc 但非 project_rules 语义（能力包 → 走 skill）→ 拒出
（0 文件 + warnings 说明，语义错配防混，同 skill 拒 narrative 纪律）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.ir import IRDocument, IRLayer, IRModule  # noqa: E402
from core.exporter import export  # noqa: E402
from core.semantics import PROJECT_RULES  # noqa: E402


def _project_rules_ir():
    """项目约定语义 techdoc IR（title 命中约定词，或 meta 显式）。"""
    return IRDocument(
        type="techdoc", title="项目构建与提交约定", pipeline_id="P90",
        pipeline_name="技术文档生成管线",
        layers=[IRLayer(id="P10", name="规则", modules=[
            IRModule(full_id="技术文档类:M90", name="项目约定规则", layer="P10",
                     content="构建命令：bash verify.sh；测试：python -m unittest；"
                             "提交纪律：Conventional Commits。")])],
        asset_refs={}, asset_missing=[], meta={"doc_semantics": PROJECT_RULES})


def _capability_ir():
    """能力语义 techdoc IR（title 是指南，无项目约定词——该走 skill）。"""
    return IRDocument(
        type="techdoc", title="API 迁移指南", pipeline_id="P90",
        pipeline_name="技术文档生成管线",
        layers=[IRLayer(id="P10", name="流程", modules=[
            IRModule(full_id="技术文档类:M90", name="迁移流程", layer="P10",
                     content="逐步迁移 API 的教程。")])],
        asset_refs={}, asset_missing=[], meta={})


def _narrative_ir():
    return IRDocument(
        type="narrative", title="校园试炼", pipeline_id="P02",
        pipeline_name="校园情感流",
        layers=[IRLayer(id="P40", name="决策", modules=[
            IRModule(full_id="情感类:M40", name="关系推进", layer="P40",
                     content="好感度规则")])],
        asset_refs={}, asset_missing=[], meta={})


class TestAgentsAdapter(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.dest = Path(tempfile.mkdtemp(prefix="nf_agents_"))

    def test_project_rules_exports_agents_md(self):
        res = export(_project_rules_ir(), "agents", dest_dir=self.dest)
        files = [Path(f) for f in res.files]
        self.assertTrue(files, f"应产出 AGENTS.md：{res.files}")
        agents = next(f for f in files if f.name == "AGENTS.md")
        text = agents.read_text(encoding="utf-8")
        self.assertIn("项目", text)
        self.assertIn("verify", text)      # 正文含命令纪律内容

    def test_claude_format_exports_claude_md(self):
        res = export(_project_rules_ir(), "claude", dest_dir=self.dest)
        files = [Path(f) for f in res.files]
        self.assertTrue(files)
        claude = next(f for f in files if f.name == "CLAUDE.md")
        self.assertIn("verify", claude.read_text(encoding="utf-8"))

    def test_narrative_rejected_no_file(self):
        res = export(_narrative_ir(), "agents", dest_dir=self.dest)
        self.assertEqual(res.files, [])
        self.assertTrue(res.warnings)
        self.assertTrue(any("narrative" in w.lower() or "CCV3" in w
                            for w in res.warnings))

    def test_capability_techdoc_rejected_toward_skill(self):
        # techdoc 但能力语义（无 project_rules 信号）→ AGENTS 出口拒出，
        # 提示走 skill（裁决缺省）
        res = export(_capability_ir(), "agents", dest_dir=self.dest)
        self.assertEqual(res.files, [], "能力语义不应进 AGENTS")
        self.assertTrue(res.warnings)
        self.assertTrue(any("skill" in w.lower() for w in res.warnings),
                        f"应提示走 skill：{res.warnings}")


if __name__ == "__main__":
    unittest.main()
