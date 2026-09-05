# -*- coding: utf-8 -*-
"""AGENTS vs SKILL 语义裁决单测（v2.1.0 A1：两判据机制化）。

运行：cd desktop && python -m unittest tests.test_semantics -v
裁决规则（用户草案机制化）：
  复用性判据——内容脱离本仓库仍有意义 → SKILL；绑死本仓库 → project_rules。
  装载判据——读者需常驻知道 → AGENTS；按需调用 → SKILL。
信号优先级：IR.meta['doc_semantics'] 显式声明 > title/模块名项目约定词启发
> 缺省回退 SKILL（兼容现状：无信号 techdoc 装配走既有 skill 出口）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.ir import IRDocument, IRLayer, IRModule  # noqa: E402
from core.semantics import classify_doc_semantics, PROJECT_RULES, SKILL  # noqa: E402


def _ir(title="协议生成规范", type_="techdoc", meta=None, mod_names=None):
    mods = [IRModule(full_id="技术文档类:M90", name=(mod_names or ["技术文档结构"])[0],
                     layer="P10", content="规则正文")]
    return IRDocument(type=type_, title=title, pipeline_id="P90",
                      pipeline_name="技术文档生成管线",
                      layers=[IRLayer(id="P10", name="结构", modules=mods)],
                      asset_refs={}, asset_missing=[],
                      meta=meta or {})


class TestClassifyDocSemantics(unittest.TestCase):
    def test_explicit_project_rules_wins(self):
        ir = _ir(meta={"doc_semantics": PROJECT_RULES})
        self.assertEqual(classify_doc_semantics(ir), PROJECT_RULES)

    def test_explicit_skill_wins(self):
        ir = _ir(meta={"doc_semantics": SKILL})
        self.assertEqual(classify_doc_semantics(ir), SKILL)

    def test_title_project_convention_heuristic(self):
        # title 含项目约定词 → project_rules（绑仓库的构建/提交纪律）
        for t in ("项目构建与提交约定", "仓库开发规则", "项目约定与命令纪律"):
            self.assertEqual(classify_doc_semantics(_ir(title=t)),
                             PROJECT_RULES, f"title={t}")

    def test_no_signal_defaults_to_skill(self):
        # 无 meta 声明、title 无项目词 → 缺省 SKILL（兼容现状）
        ir = _ir(title="API 迁移指南")
        self.assertEqual(classify_doc_semantics(ir), SKILL)

    def test_narrative_ir_defaults_skill(self):
        # narrative 无 project_rules 语义；裁决层不管类型（出口层拒）——
        # narrative→agents 由 agent_rules_adapter 拒（同 skill 拒 narrative）
        ir = _ir(title="校园试炼", type_="narrative")
        self.assertEqual(classify_doc_semantics(ir), SKILL)


if __name__ == "__main__":
    unittest.main()
