#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""40 总纲 v2.8 波B S4 —— nf pipeline new 派生脚手架单测（纯 unittest，L2 core 零依赖）。"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from core import pipeline_scaffold as ps

TEMPLATE = """# 管线 P00 · 通用文档生成管线

> 通用骨架模板

```yaml
Pipeline:
  id: P00
  name: 通用文档生成管线
  structure:
    type: linear
  layers:
    - id: P00
      name: 装载
      default_modules: []
      allowed_modules: []
  tags: [领域无关, 骨架, 元管线]
```
"""


class ScaffoldPipelineTest(unittest.TestCase):
    def test_derive_replaces_id_name_and_domain_tag(self):
        text = ps.scaffold_pipeline(TEMPLATE, "p07", "演示领域管线",
                                    domain="悬疑")
        self.assertIn("# 管线 P07 · 演示领域管线", text)
        self.assertIn("  id: P07", text)
        self.assertIn("  name: 演示领域管线", text)
        self.assertIn("悬疑领域", text)          # domain → tags
        self.assertIn("P07", text)
        # 层位 id 不被误替换（仍为 P00）
        self.assertIn("    - id: P00", text)

    def test_without_domain_no_extra_tag(self):
        text = ps.scaffold_pipeline(TEMPLATE, "P90", "技术文档链")
        self.assertNotIn("悬疑领域", text)
        self.assertIn("  name: 技术文档链", text)

    def test_bad_id_raises(self):
        with self.assertRaises(ValueError):
            ps.scaffold_pipeline(TEMPLATE, "P7", "x")   # 至少两位
        with self.assertRaises(ValueError):
            ps.scaffold_pipeline(TEMPLATE, "Q07", "x")

    def test_missing_template_keys_raise(self):
        with self.assertRaises(ValueError):
            ps.scaffold_pipeline("# 管线 P00 · x\n```yaml\nPipeline:\n  id: P00\n```",
                                 "P07", "x")

    def test_default_filename(self):
        name = ps.default_filename("P07", "演示 领域-管线")
        self.assertTrue(name.startswith("P07_"))
        self.assertTrue(name.endswith(".md"))


if __name__ == "__main__":
    unittest.main()