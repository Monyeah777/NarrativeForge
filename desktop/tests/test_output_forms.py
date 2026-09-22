#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产出形态面单测：形态清单自洽 / 判件 / JSON Schema 子集语义 / 双源 / T4 复算 / 基线回退。

负例取自真实缺陷类（本波实际踩到的三类）：
  ① 声明了 T4 却没有可复算引擎（宣称≠实现）；
  ② 数据面与散文面键集不一致（双源漂移）；
  ③ JSON Schema 多余字段 / 不支持关键字必须显式上报（不得静默通过）。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import output_forms as of  # noqa: E402
from core import quant_metrics as qm  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


class RegistryTest(unittest.TestCase):
    def test_registry_self_consistent(self):
        issues, stats = of.registry_verify(ROOT)
        self.assertEqual(issues, [], issues)
        self.assertGreaterEqual(stats["forms"], 100, "形态清单须成规模（本次 ≥100 条）")
        self.assertGreaterEqual(stats["categories"], 8)
        for form in ("json", "json-schema", "vega-lite", "mermaid", "graphml",
                     "csv", "gips", "model-cards"):
            self.assertIn(form, {f["id"] for f in of.load_registry(ROOT)["forms"]})

    def test_every_form_carries_reachability_evidence(self):
        for f in of.load_registry(ROOT)["forms"]:
            self.assertIn("reachable", f["evidence"], f["id"])
            if f["evidence"]["reachable"]:
                self.assertTrue(f["evidence"]["sha256_sample"], f["id"])
            else:
                self.assertTrue(f["evidence"]["error"], f["id"])


class PackageIndexTest(unittest.TestCase):
    def test_repo_packages_green(self):
        issues, stats = of.index_verify(ROOT)
        self.assertEqual(issues, [], issues)
        self.assertGreaterEqual(stats["outputs"], 10)
        self.assertIn("T4", stats["by_tier"])

    def test_baseline_blocks_regression(self):
        issues, _ = of.baseline_verify(ROOT)
        self.assertEqual(issues, [], issues)

    def test_missing_declared_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "community", "样例包", "outputs"))
            idx = {"schema": "nf-output-index/1", "package": "样例包",
                   "outputs": [{"path": "outputs/NOPE.json", "form": "json",
                                "tier": "T2", "role": "data"}]}
            with open(os.path.join(tmp, "community", "样例包", of.INDEX_REL),
                      "w", encoding="utf-8") as fh:
                json.dump(idx, fh)
            issues, _ = of.index_verify(tmp)
            self.assertTrue(any("不存在" in i for i in issues), issues)

    def test_t4_without_generator_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "community", "样例包", "outputs")
            os.makedirs(base)
            with open(os.path.join(base, "X.json"), "w", encoding="utf-8") as fh:
                json.dump({"a": 1}, fh)
            idx = {"schema": "nf-output-index/1", "package": "样例包",
                   "outputs": [{"path": "outputs/X.json", "form": "json", "tier": "T4",
                                "role": "functional",
                                "recompute": {"id": "no-such-generator"}}]}
            with open(os.path.join(tmp, "community", "样例包", of.INDEX_REL),
                      "w", encoding="utf-8") as fh:
                json.dump(idx, fh)
            issues, _ = of.index_verify(tmp)
            self.assertTrue(any("无对应引擎" in i for i in issues), issues)


class JsonSchemaSubsetTest(unittest.TestCase):
    def test_type_required_enum(self):
        schema = {"type": "object", "required": ["a"],
                  "properties": {"a": {"type": "integer", "enum": [1, 2]}},
                  "additionalProperties": False}
        self.assertEqual(of.json_schema_check({"a": 1}, schema), [])
        self.assertTrue(of.json_schema_check({}, schema))
        self.assertTrue(of.json_schema_check({"a": 3}, schema))
        self.assertTrue(of.json_schema_check({"a": 1, "b": 2}, schema))

    def test_bool_is_not_number(self):
        errs = of.json_schema_check(True, {"type": "number"})
        self.assertTrue(errs, "布尔不得当数字通过（Python 子类陷阱）")

    def test_unsupported_keyword_is_reported_not_ignored(self):
        unsup = []
        of.json_schema_check({}, {"if": {"type": "object"}}, unsupported=unsup)
        self.assertTrue(unsup, "不支持的官方关键字必须显式上报（不得静默通过）")

    def test_local_ref_resolves_remote_does_not(self):
        schema = {"$defs": {"x": {"type": "string"}}, "properties": {"a": {"$ref": "#/$defs/x"}},
                  "type": "object"}
        self.assertEqual(of.json_schema_check({"a": "s"}, schema), [])
        unsup = []
        of.json_schema_check({}, {"$ref": "https://example.com/s.json"}, unsupported=unsup)
        self.assertTrue(unsup)


class FormValidatorTest(unittest.TestCase):
    def _write(self, tmp, rel, text):
        p = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return p

    def test_duplicate_json_key_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "a.json", '{"x": 1, "x": 2}')
            issues = of._check_json(tmp, "a.json")
            self.assertTrue(any("重复键" in i for i in issues), issues)

    def test_csv_ragged_rows_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "a.csv", "a,b\n1,2\n3\n")
            issues = of._check_csv(tmp, "a.csv")
            self.assertTrue(any("字段数" in i for i in issues), issues)

    def test_vega_lite_needs_mark_data_and_bound_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "c.json", json.dumps({
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "data": {"values": []}, "mark": "line",
                "encoding": {"x": {"type": "nominal"}}}))
            issues = of._check_vega_lite(tmp, "c.json")
            self.assertTrue(any("通道未绑定" in i for i in issues), issues)

    def test_graphml_dangling_edge_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "g.graphml", (
                '<?xml version="1.0"?><graphml xmlns="http://graphml.graphdrawing.org/xmlns">'
                '<graph id="g" edgedefault="directed"><node id="A"/>'
                '<edge source="A" target="B"/></graph></graphml>'))
            issues = of._check_graphml(tmp, "g.graphml")
            self.assertTrue(any("悬空" in i for i in issues), issues)

    def test_detect_distinguishes_schema_and_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "s.json", json.dumps(
                {"$schema": "https://json-schema.org/draft/2020-12/schema",
                 "type": "object"}))
            self._write(tmp, "v.json", json.dumps(
                {"$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                 "data": {"values": []}, "mark": "line"}))
            self.assertEqual(of.detect(tmp, "s.json")[0], "json-schema")
            self.assertEqual(of.detect(tmp, "v.json")[0], "vega-lite")

    def test_quant_metrics_engine_claim_must_be_implemented(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "q.json", json.dumps({
                "kind": "nf-quant-metrics/1", "domain": "d", "source": "assets/x.md",
                "annual_factors": {"daily": 252, "weekly": 52, "monthly": 12},
                "metrics": [{"id": "METRIC_X", "name": "X", "formula": "f", "unit": "ratio",
                             "category": "return", "required_params": ["prices"],
                             "pitfall": "p", "engine": "quant_metrics:not_there",
                             "verifiable": "T4"}],
                "declared_only": []}))
            issues = of._check_quant_metrics(tmp, "q.json")
            self.assertTrue(any("宣称≠实现" in i for i in issues), issues)


class RenderAndRecomputeTest(unittest.TestCase):
    def test_repo_render_is_idempotent(self):
        issues, rows = of.render_outputs(ROOT, write=False)
        self.assertEqual(issues, [], issues)
        self.assertTrue(rows)
        self.assertFalse([r for r in rows if r["changed"]],
                         "在盘产出面必须与生成器一致（改声明件后重跑 nf output render --write）")

    def test_meter_ratio_bounds(self):
        _, stats = of.meter(ROOT)
        for pkg, s in stats["packages"].items():
            self.assertGreater(s["machine_verifiable"], 0, pkg)
            self.assertLessEqual(s["machine_verifiable_ratio"], 1.0)
            self.assertGreaterEqual(s["machine_verifiable_ratio"], 0.0)

    def test_quant_engine_claim_covers_all_engines(self):
        """注册表宣称的每个 engine 都必须在 core.quant_metrics 真实存在。"""
        data = json.loads((Path(ROOT) / "community" / "量化金融域包" / "outputs"
                           / "QUANT_METRICS.json").read_text(encoding="utf-8"))
        for m in data["metrics"]:
            mod, _, fn = m["engine"].partition(":")
            self.assertEqual(mod, "quant_metrics")
            self.assertTrue(hasattr(qm, fn), m["id"])


if __name__ == "__main__":
    unittest.main()
