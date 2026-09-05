# -*- coding: utf-8 -*-
"""MCP server 定义导出单测（v2.1.0 A2：techdoc IR → MCP 资源型 server 定义）。

运行：cd desktop && python -m unittest tests.test_mcp_adapter -v
矩阵约束（27 方案 A2）：MCP 出口接协议/规则类 techdoc IR（Resources 承载规则
正文——uri/name/mimeType/text）；narrative IR 拒出（0 文件 + warnings，同
skill/agents 纪律）；硬映射 Tool 不做（无结构化参数源，造假不做）。
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.ir import IRDocument, IRLayer, IRModule  # noqa: E402
from core.exporter import export  # noqa: E402


def _techdoc_ir():
    """协议/规则类 techdoc IR（P90 语义：多模块 → 多 Resource）。"""
    return IRDocument(
        type="techdoc", title="模组协议规范", pipeline_id="P90",
        pipeline_name="技术文档生成管线",
        layers=[
            IRLayer(id="P10", name="结构", modules=[
                IRModule(full_id="技术文档类:M90", name="协议骨架", layer="P10",
                         content="协议必含：前置声明/字段表/示例三段。")]),
            IRLayer(id="P30", name="片段", modules=[
                IRModule(full_id="技术文档类:M90", name="规则校验", layer="P30",
                         content="字段命名：snake_case；引用闭合。")]),
        ],
        asset_refs={}, asset_missing=[], meta={})


def _narrative_ir():
    return IRDocument(
        type="narrative", title="校园试炼", pipeline_id="P02",
        pipeline_name="校园情感流",
        layers=[IRLayer(id="P40", name="决策", modules=[
            IRModule(full_id="情感类:M40", name="关系推进", layer="P40",
                     content="好感度规则")])],
        asset_refs={}, asset_missing=[], meta={})


class TestMcpAdapter(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.dest = Path(tempfile.mkdtemp(prefix="nf_mcp_"))

    def test_techdoc_exports_mcp_json_with_resources(self):
        res = export(_techdoc_ir(), "mcp", dest_dir=self.dest)
        files = [Path(f) for f in res.files]
        self.assertTrue(files, f"应产 mcp.json：{res.files}")
        mcp = next(f for f in files if f.name == "mcp.json")
        data = json.loads(mcp.read_text(encoding="utf-8"))
        self.assertEqual(data["mcp"]["capabilities"]["resources"], {})
        res_list = data["mcp"]["resources"]
        self.assertEqual(len(res_list), 2, f"2 模块 → 2 资源：{len(res_list)}")
        for r in res_list:
            self.assertTrue(r["uri"].startswith("nf://P90/"))
            self.assertTrue(r["name"])
            self.assertEqual(r["mimeType"], "text/markdown")
            self.assertTrue(r["text"])

    def test_extra_modules_included_in_resources(self):
        ir = IRDocument(
            type="techdoc", title="协议+层外", pipeline_id="P90",
            pipeline_name="技术文档生成管线",
            layers=[IRLayer(id="P10", name="结构", modules=[
                IRModule(full_id="技术文档类:M90", name="主规则", layer="P10",
                         content="正文A")])],
            extra_modules=[IRModule(full_id="技术文档类:M90", name="附加规则",
                                    layer="P80", content="正文B")],
            asset_refs={}, asset_missing=[], meta={})
        res = export(ir, "mcp", dest_dir=self.dest)
        data = json.loads(Path(res.files[0]).read_text(encoding="utf-8"))
        self.assertEqual(len(data["mcp"]["resources"]), 2,
                         "层外模块也入 resources（不静默丢）")

    def test_narrative_rejected_no_file(self):
        res = export(_narrative_ir(), "mcp", dest_dir=self.dest)
        self.assertEqual(res.files, [])
        self.assertTrue(res.warnings)
        self.assertTrue(any("narrative" in w.lower() or "CCV3" in w
                            for w in res.warnings))


if __name__ == "__main__":
    unittest.main()
