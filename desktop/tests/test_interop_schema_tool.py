#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""互操作**外部权威校验工具**单测（离线可跑：只测声明面与失败口径，不联网）。

联网校验本身是非门禁任务（`scripts/check_interop_schemas.py --fetch`），
这里钉住两件事：① 目标 schema 表覆盖全部派生面；② 官方无 JSON Schema 的面必须
**如实记 no-schema**（不许假称校验过）；③ 拒写 protocol/ 的纪律。
"""
import importlib.util
import io
import contextlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import interop_export as ie  # noqa: E402


def _tool():
    spec = importlib.util.spec_from_file_location(
        "nf_interop_schemas", ROOT / "scripts" / "check_interop_schemas.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class InteropSchemaToolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = _tool()

    def test_schema_table_covers_all_faces(self):
        faces = set(ie.KINDS)
        declared = set(self.tool.SCHEMAS) | set(self.tool.NOSCHEMA)
        self.assertEqual(faces, declared, "每个派生面都要有校验口径（schema 或 no-schema）")

    def test_no_schema_faces_are_honest(self):
        for kind, why in self.tool.NOSCHEMA.items():
            self.assertTrue("JSON Schema" in why and "无" in why, why)
            spec = self.tool.SCHEMAS.get(kind, (why, None))
            row = self.tool.validate_one(kind, spec, {}, None)
            self.assertEqual(row["status"], "no-schema", kind)
            self.assertEqual(row["detail"], why)

    def test_listing_mode_offline_returns_zero(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = self.tool.main(["--root", str(ROOT)])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("未联网", out)
        for kind in ie.KINDS:
            self.assertIn(kind, out)

    def test_refuses_to_write_protocol(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = self.tool.main(["--write", "protocol/x.md"])
        self.assertEqual(code, 2)

    def test_validation_report_exists_and_records_statuses(self):
        rep = ROOT / "results" / "interop-schema-validation.md"
        self.assertTrue(rep.is_file(), "联网取证的报告须入仓（results/ 说明件）")
        text = rep.read_text(encoding="utf-8")
        for kind in ie.KINDS:
            self.assertIn(kind, text)
        self.assertTrue(any(s in text for s in ("ok", "OK")), text[:200])


if __name__ == "__main__":
    unittest.main()
