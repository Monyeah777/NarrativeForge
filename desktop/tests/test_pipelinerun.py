# -*- coding: utf-8 -*-
"""管线抽象执行（dry-run → GraphSpec）单测。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import pipelinerun as pr  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


class TestPipelineDryRun(unittest.TestCase):
    def test_graph_shape(self):
        g = pr.graph("community/校园西幻轻混组合包/pipelines/P04_轻混装配流管线.md", ROOT)
        self.assertEqual(g["schema"], "nf-graphspec/1")
        self.assertEqual(g["pipeline"]["id"], "P04")
        self.assertGreaterEqual(len(g["steps"]), 9)
        self.assertGreaterEqual(g["stats"]["core_base"], 10)
        self.assertIn("issues", g)
        self.assertIn("notes", g)

    def test_sweep_zero_hard_issues(self):
        issues, tot = pr.sweep(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(tot["pipelines"], 8)

    def test_missing_pipeline_raises(self):
        with self.assertRaises(ValueError):
            pr.graph("no/such/pipeline.md", ROOT)

    def test_layer_override(self):
        p = "community/校园西幻轻混组合包/pipelines/P04_轻混装配流管线.md"
        g = pr.graph(p, ROOT, overrides={"P40": ["M91"]})
        ids = [m["id"] for s in g["steps"] for m in s["modules"]]
        self.assertIn("M91", ids)
        self.assertLessEqual(len([i for i in ids if i == "M92"]), 1)


if __name__ == "__main__":
    unittest.main()
