# -*- coding: utf-8 -*-
"""遥测 semconv 映射单测（不改 trace 格式；只对齐属性命名与 OTLP 形状）。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import telemetry_semconv as ts  # noqa: E402

RECORD = {
    "tool": "nf assemble",
    "phase": "plan",
    "requirement": "校园情感，毕业遗憾线",
    "status": "preset",
    "matched": True,
    "package": "西幻生存领域包",
    "pipeline": "P03",
    "allowed_modules": 44,
    "ok": True,
    "issues": [],
    "stats": {"segments": 8},
}


class TestTelemetrySemconv(unittest.TestCase):
    def test_tool_name_and_call_id_deterministic(self):
        self.assertEqual(ts.tool_name_of(RECORD), "nf.assemble")
        self.assertEqual(ts.tool_name_of({"tool": "nf"}), "nf")
        self.assertEqual(ts.call_id_of(RECORD), ts.call_id_of(dict(RECORD)))

    def test_attributes_carry_semconv_names(self):
        attrs = ts.attributes_for(RECORD)
        self.assertEqual(attrs["gen_ai.operation.name"], "execute_tool")
        self.assertEqual(attrs["gen_ai.tool.name"], "nf.assemble")
        self.assertEqual(attrs["gen_ai.agent.name"], "narrativeforge")
        self.assertEqual(attrs["gen_ai.tool.call.arguments"]["phase"], "plan")
        self.assertEqual(attrs["gen_ai.tool.call.result"]["pipeline"], "P03")
        self.assertIn("gen_ai.tool.call.id", attrs)

    def test_span_name_and_status(self):
        span = ts.to_span(RECORD)
        self.assertEqual(span["name"], "execute_tool nf.assemble")
        self.assertEqual(span["status"]["code"], 1)
        bad = ts.to_span(dict(RECORD, ok=False))
        self.assertEqual(bad["status"]["code"], 2)
        keys = {a["key"] for a in span["attributes"]}
        self.assertIn("gen_ai.tool.name", keys)

    def test_export_shape(self):
        out = ts.to_export([RECORD, dict(RECORD, phase="check")])
        rs = out["resourceSpans"][0]
        self.assertEqual(rs["resource"]["attributes"][0]["key"], "service.name")
        spans = rs["scopeSpans"][0]["spans"]
        self.assertEqual(len(spans), 2)
        self.assertEqual(rs["scopeSpans"][0]["scope"]["name"], ts.SCOPE_NAME)

    def test_minimal_record_does_not_crash(self):
        attrs = ts.attributes_for({})
        self.assertEqual(attrs["gen_ai.tool.name"], "nf")
        self.assertNotIn("gen_ai.tool.call.arguments", attrs)

    def test_load_trace_accepts_single_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp, "one.json")
            p1.write_text(json.dumps(RECORD, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(len(ts.load_trace(str(p1))), 1)
            p2 = Path(tmp, "many.json")
            p2.write_text(json.dumps({"records": [RECORD, RECORD]}),
                          encoding="utf-8")
            self.assertEqual(len(ts.load_trace(str(p2))), 2)


if __name__ == "__main__":
    unittest.main()
