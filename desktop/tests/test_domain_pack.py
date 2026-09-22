#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""域包工厂 + 域功能引擎单测：口径公式 / 夹具确定性 / 生成器幂等 / 唯一性守卫 /
机验占比 ≥95% / T4 复算一致。

负例取自工厂必须挡住的事故类：类别撞车、模块 token 撞车、管线撞车、无 T4 面、
可机验占比不足、口径族未登记。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import domain_metrics as dm  # noqa: E402
from core import domain_pack as dp  # noqa: E402
from core import output_forms as of  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


class MetricFamilyTest(unittest.TestCase):
    """口径公式：每条用可手算向量钉住（不是「跑通就算」）。"""

    def test_classification_metrics(self):
        rows = [{"gold": "pos", "pred": "pos"}, {"gold": "pos", "pred": "neg"},
                {"gold": "neg", "pred": "neg"}, {"gold": "neg", "pred": "pos"}]
        out = dm.classification(rows)
        self.assertEqual(out["n"], 4)
        self.assertAlmostEqual(out["accuracy"], 0.5)
        self.assertAlmostEqual(out["per_label"]["pos"]["recall"], 0.5)

    def test_retrieval_mrr_and_recall(self):
        rows = [{"query_id": "q1", "rank": "1", "relevant": "0"},
                {"query_id": "q1", "rank": "2", "relevant": "1"},
                {"query_id": "q1", "rank": "3", "relevant": "1"}]
        out = dm.retrieval(rows, k=3)
        self.assertAlmostEqual(out["recall_at_k"], 1.0)
        self.assertAlmostEqual(out["mrr"], 0.5)

    def test_extraction_and_generation(self):
        ex = dm.extraction([{"gold_fields": '["a","b"]', "pred_fields": '["a","c"]'}])
        self.assertAlmostEqual(ex["field_precision"], 0.5)
        self.assertAlmostEqual(ex["field_recall"], 0.5)
        self.assertAlmostEqual(ex["exact_match"], 0.0)
        gen = dm.generation([{"reference": "ab", "output": "ab"},
                             {"reference": "ab", "output": "cd"}])
        self.assertAlmostEqual(gen["exact_match"], 0.5)

    def test_regression_calibration_agreement(self):
        reg = dm.regression([{"gold": "1.0", "pred": "1.5"}, {"gold": "2.0", "pred": "2.0"}])
        self.assertAlmostEqual(reg["mae"], 0.25)
        cal = dm.calibration([{"prob": "1.0", "gold": "1"}, {"prob": "0.0", "gold": "0"}])
        self.assertAlmostEqual(cal["brier"], 0.0)
        self.assertAlmostEqual(cal["ece"], 0.0)
        agr = dm.agreement([{"a": "T", "b": "T"}, {"a": "F", "b": "F"}])
        self.assertAlmostEqual(agr["cohen_kappa"], 1.0)

    def test_exact_judgement_pass_at_k(self):
        rows = [{"task_id": "t1", "passed": "1"} for _ in range(4)]
        out = dm.exact_judgement(rows, k=4)
        self.assertAlmostEqual(out["pass_at_1"], 1.0)
        self.assertAlmostEqual(out["pass_at_k"], 1.0)
        rows = [{"task_id": "t1", "passed": "1"}, {"task_id": "t1", "passed": "1"},
                {"task_id": "t1", "passed": "0"}, {"task_id": "t1", "passed": "0"}]
        self.assertAlmostEqual(dm.exact_judgement(rows, k=2)["pass_at_k"],
                               1 - (2 / 4) * (1 / 3), places=5)

    def test_latency_cost_drift_compliance(self):
        lat = dm.latency_cost([{"latency_ms": "100", "tokens_in": "1000",
                                "tokens_out": "0"}], price_per_1k_in=1.0)
        self.assertAlmostEqual(lat["cost_total"], 1.0)
        self.assertEqual(lat["p50_ms"], 100.0)
        self.assertAlmostEqual(dm.drift([{"expected": "0.5", "actual": "0.5"}])["psi"], 0.0)
        comp = dm.contract_compliance([{"valid": "1"}, {"valid": "0",
                                                        "missing_fields": "unit"}])
        self.assertAlmostEqual(comp["compliance_rate"], 0.5)
        self.assertEqual(comp["missing_top"][0]["field"], "unit")

    def test_unknown_family_raises(self):
        with self.assertRaises(ValueError):
            dm.evaluate("no-such-family", [])


class FixtureTest(unittest.TestCase):
    def test_synthesize_is_deterministic(self):
        for fam in sorted(dm.FAMILIES):
            a = dm.synthesize(fam, "A01")
            b = dm.synthesize(fam, "A01")
            self.assertEqual(a, b, fam)
            self.assertTrue(a, fam)
            csv_text = dm.rows_to_csv(a)
            self.assertEqual(csv_text, dm.rows_to_csv(b))
            rows, err = _load_csv(csv_text)
            self.assertEqual(err, "")
            self.assertEqual(len(rows), len(a), fam)

    def test_every_family_evaluates_on_its_fixture(self):
        for fam in sorted(dm.FAMILIES):
            out = dm.evaluate(fam, dm.synthesize(fam, "A01"))
            self.assertEqual(out["family"], fam)
            self.assertGreaterEqual(len(out), 3)


def _load_csv(text):
    import csv
    import io
    rows = list(csv.DictReader(io.StringIO(text)))
    return rows, ""


class FactoryTest(unittest.TestCase):
    """真仓库：已建域包必须与生成器逐字节一致、登记三处到位、产出面机检通过。"""

    def _specs(self):
        d = Path(ROOT) / dp.SPEC_DIR
        if not d.is_dir():
            return []
        return sorted(p.stem for p in d.glob("*.json"))

    def test_specs_are_valid(self):
        for code in self._specs():
            spec = dp.load_spec(ROOT, code)
            self.assertEqual(dp.spec_issues(spec), [])
            self.assertEqual(len(spec["subdivisions"]), dp.SUB_COUNT)

    def test_built_packs_match_generator(self):
        specs = self._specs()
        if not specs:
            self.skipTest("无域规格（内部档案不在场）——工厂自检退化")
        for code in specs:
            spec = dp.load_spec(ROOT, code)
            issues, _stats = dp.verify(ROOT, spec)
            self.assertEqual(issues, [], "%s：%s" % (code, issues))

    def test_manifest_and_ratio(self):
        issues, stats = dp.manifest_verify(ROOT)
        self.assertEqual(issues, [], issues)
        path = Path(ROOT) / dp.MANIFEST_REL
        if not path.is_file():
            self.skipTest("无域包名录")
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(doc["count"], 1)
        for p in doc["packs"]:
            self.assertGreaterEqual(p["machine_verifiable_ratio"], 0.95,
                                    "%s 可机验占比不足" % p["code"])
            self.assertGreaterEqual(p["functional_faces"], 1, p["code"])
        self.assertEqual(stats["packs"], doc["count"])

    def test_identifier_uniqueness(self):
        reg = json.loads((Path(ROOT) / dp.REGISTRY_REL).read_text(encoding="utf-8"))
        pipes = [p["pipeline"] for p in reg["protocols"]]
        self.assertEqual(len(pipes), len(set(pipes)), "管线 id 须全局唯一")
        cats = [c for p in reg["protocols"] for c in p.get("categories") or []]
        self.assertEqual(len(cats), len(set(cats)), "R2 独占类别须全局互斥")
        stems = dp.module_stems(ROOT)
        dupes = {k: v for k, v in stems.items()
                 if len({x.split("/")[1] for x in v}) > 1}
        self.assertEqual(dupes, {}, "模块文件名 token 须跨包唯一")

    def test_negative_spec_rejected(self):
        bad = {"code": "Z99", "section": "X", "name": "n", "pack_name": "p",
               "category": "c", "metric_family": "generation",
               "module_titles": ["a"], "subdivisions": []}
        self.assertTrue(dp.spec_issues(bad))

    def test_build_dry_run_writes_nothing(self):
        code = self._specs()
        if not code:
            self.skipTest("无域规格")
        spec = dp.load_spec(ROOT, code[0])
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "community"), exist_ok=True)
            out = dp.build(tmp, spec, write=False)
            self.assertGreater(out["files"], 10)
            self.assertEqual(os.listdir(os.path.join(tmp, "community")), [])


if __name__ == "__main__":
    unittest.main()
