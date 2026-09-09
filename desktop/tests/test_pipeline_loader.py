#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 · pipeline_loader 单测（官方管线装载 + 缺件拒绝）。"""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import pipeline_loader as pl  # noqa: E402


class PipelineLoaderTest(unittest.TestCase):
    def test_load_official_p01(self):
        pipe = pl.load_pipeline_file(str(ROOT / "03_管线库" / "P01_标准管线.md"))
        self.assertIsNotNone(pipe)
        self.assertEqual(pipe.id, "P01")

    def test_missing_file_returns_none(self):
        self.assertIsNone(pl.load_pipeline_file(str(ROOT / "no_such.md")))

    def test_load_official_p90_and_community_p03(self):
        for rel, pid in (("03_管线库/P90_技术文档生成管线.md", "P90"),
                         ("community/西幻生存领域包/pipelines/P03_西幻生存流管线.md", "P03")):
            pipe = pl.load_pipeline_file(str(ROOT / rel))
            self.assertIsNotNone(pipe, rel)
            self.assertEqual(pipe.id, pid)

    def test_bad_content_returns_none(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            bad = os.path.join(tmp, "bad.md")
            with open(bad, "w", encoding="utf-8") as fh:
                fh.write("not a pipeline yaml at all\n")
            self.assertIsNone(pl.load_pipeline_file(bad))

    def test_load_all_repo_pipelines(self):
        """全量装载：03 官方 + community 每份管线都可解析且 id 合法。"""
        docs = sorted((ROOT / "03_管线库").glob("*.md"))
        for pkg in sorted((ROOT / "community").iterdir()):
            docs += sorted((pkg / "pipelines").glob("*.md"))
        self.assertGreaterEqual(len(docs), 8)
        for doc in docs:
            pipe = pl.load_pipeline_file(str(doc))
            self.assertIsNotNone(pipe, str(doc))
            self.assertTrue(pipe.id.startswith("P"), doc.name)

    def test_fallback_subset_parser(self):
        text = ("Pipeline:\n  id: P99\n  structure:\n    type: linear\n"
                "  tags: [a, b]\n  optional: true\n  n: 1\n  x: null\n"
                "  layers:\n    - id: P00\n      name: 层\n"
                "      default_modules: [M00]\n")
        data = pl._parse_yaml_block(text)
        self.assertEqual(data["Pipeline"]["id"], "P99")
        self.assertEqual(data["Pipeline"]["tags"], ["a", "b"])
        self.assertTrue(data["Pipeline"]["optional"])

    def test_fallback_used_when_yaml_missing(self):
        import sys
        saved = sys.modules.get("yaml", None)
        sys.modules["yaml"] = None  # force ImportError inside loader
        try:
            md = ("# 管线 P99\n```yaml\nPipeline:\n  id: P99\n"
                  "  layers:\n    - id: P00\n      name: X\n"
                  "      optional: false\n      default_modules: []\n"
                  "      allowed_modules: []\n```\n")
            pipe = pl.parse_pipeline_md(md)
            self.assertIsNotNone(pipe)
            self.assertEqual(pipe.id, "P99")
        finally:
            if saved is None:
                sys.modules.pop("yaml", None)
            else:
                sys.modules["yaml"] = saved

    def test_parse_edges(self):
        self.assertIsNone(pl.parse_pipeline_md("no fence here"))
        self.assertIsNone(pl.parse_pipeline_md("```yaml\nnot a map\n```"))

    def test_discover_pipelines(self):
        pipes = pl.discover_pipelines(str(ROOT / "03_管线库"))
        self.assertGreaterEqual(len(pipes), 3)
        self.assertEqual(pl.discover_pipelines(str(ROOT / "no_such_dir")), [])


if __name__ == "__main__":
    unittest.main()
