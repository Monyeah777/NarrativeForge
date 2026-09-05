"""导出产物 schema 校验测试（v2.2.0 A1：5 格式 shape 自检）。

锚点：真实 IR 经 exporter.export() 产 5 格式 → validate_export 零 issue；
篡改产物（删必填键/破坏结构）→ 校验器检出。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import export_schema  # noqa: E402
from core.exporter import export  # noqa: E402
from core.ir import IRDocument, IRLayer, IRModule  # noqa: E402


def _techdoc_ir() -> IRDocument:
    """techdoc IR（skill/mcp 接受）。"""
    m = IRModule(full_id="M90", name="技术文档结构", layer="P90",
                 content="结构骨架与模板装载规则。")
    layer = IRLayer(id="P90", name="技术文档生成",
                    description="P90 链技术文档装载", modules=[m])
    return IRDocument(type="techdoc", title="技术文档装配战例",
                      pipeline_id="P06", pipeline_name="技术文档题材装配流",
                      layers=[layer])


def _project_rules_ir() -> IRDocument:
    """project_rules 语义 IR（agents/claude 接受——meta 声明项目约定）。"""
    m = IRModule(full_id="M90", name="项目规则", layer="P90",
                 content="仓库构建/提交纪律。")
    layer = IRLayer(id="P90", name="项目约定", description="项目常驻规则",
                    modules=[m])
    return IRDocument(type="techdoc", title="项目约定规则",
                      pipeline_id="P06", pipeline_name="项目约定",
                      layers=[layer], meta={"doc_semantics": "project_rules"})


def _narrative_ir() -> IRDocument:
    """narrative IR（skill/agents/mcp 拒出；ccv3 接受）。"""
    m = IRModule(full_id="M55", name="匿名情书", layer="P40",
                 content="情书匿名投递与回应。")
    layer = IRLayer(id="P40", name="行为决策", modules=[m])
    return IRDocument(type="narrative", title="校园叙事例", layers=[layer])


class ExportSchemaValidTest(unittest.TestCase):
    """合法产物：export() 产出后 validate_export 应零 issue。"""

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix="nf_schema_")

    def _export_and_validate(self, ir, fmt):
        res = export(ir, fmt, dest_dir=self.dir)
        issues = export_schema.validate_export(fmt, self.dir)
        return res, issues

    def test_ccv3_narrative_passes(self):
        res, issues = self._export_and_validate(_narrative_ir(), "ccv3")
        self.assertEqual(res.warnings, [], res.warnings)
        self.assertEqual(issues, [], issues)

    def test_skill_techdoc_passes(self):
        _, issues = self._export_and_validate(_techdoc_ir(), "skill")
        self.assertEqual(issues, [], issues)

    def test_agents_techdoc_passes(self):
        _, issues = self._export_and_validate(_project_rules_ir(), "agents")
        self.assertEqual(issues, [], issues)

    def test_claude_techdoc_passes(self):
        _, issues = self._export_and_validate(_project_rules_ir(), "claude")
        self.assertEqual(issues, [], issues)

    def test_mcp_techdoc_passes(self):
        _, issues = self._export_and_validate(_techdoc_ir(), "mcp")
        self.assertEqual(issues, [], issues)

    def test_ccv3_world_entries_have_required_keys(self):
        """world.json 每条目含 name/keys/content/enabled/insertion_order/id。"""
        res, _ = self._export_and_validate(_narrative_ir(), "ccv3")
        world = json.load(open(os.path.join(self.dir, "world.json"),
                               encoding="utf-8"))
        for e in world["entries"]:
            for k in ("name", "keys", "content", "enabled",
                      "insertion_order", "id"):
                self.assertIn(k, e)


class ExportSchemaTamperTest(unittest.TestCase):
    """篡改产物 → 校验器检出（RED 反证）。"""

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix="nf_schema_bad_")
        export(_techdoc_ir(), "mcp", dest_dir=cls.dir)
        export(_narrative_ir(), "ccv3", dest_dir=cls.dir)

    def test_mcp_missing_name_detected(self):
        p = os.path.join(self.dir, "mcp.json")
        data = json.load(open(p, encoding="utf-8"))
        del data["mcp"]["name"]
        json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        issues = export_schema.validate_export("mcp", self.dir)
        self.assertTrue(any("mcp.name" in i for i in issues), issues)

    def test_ccv3_missing_spec_detected(self):
        p = os.path.join(self.dir, "chara.json")
        data = json.load(open(p, encoding="utf-8"))
        for k in ("spec", "spec_version"):
            data.pop(k, None)
        json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False)
        issues = export_schema.validate_export("ccv3", self.dir)
        self.assertTrue(any("缺必填键" in i for i in issues), issues)


class ExportSchemaUnregisteredTest(unittest.TestCase):
    def test_unregistered_fmt_flagged(self):
        issues = export_schema.validate_export("nope", "/tmp/x")
        self.assertTrue(any("未登记" in i for i in issues))


if __name__ == "__main__":
    unittest.main()
