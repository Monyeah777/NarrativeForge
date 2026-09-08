#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.8.0 波C C3 —— 语义矛盾扫描单测（41 规划，techdoc 链 testcase 驱动）。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import semantic_conflict as sc  # noqa: E402


M90 = """# 模块 M90 · 技术文档结构

> 类别：技术文档｜来源：官方｜挂载点：P90（active）｜依赖：M00

```yaml
machine_contract:
  schema: "1"
  id: M90
  name: 技术文档结构
  category: 技术文档
  layer: P90
  events:
    publish: [doc_delta]
    subscribe: [intent_received]
```
"""

M50 = """# 模块 M50 · 主循环

> 类别：通用｜来源：核心｜挂载点：调度器｜依赖：M00

```yaml
machine_contract:
  schema: "1"
  id: M50
  name: 主循环
  category: 通用
  layer: 调度器
  events:
    publish: []
    subscribe: []
```
"""


class SemanticConflictTest(unittest.TestCase):
    def _write(self, root, rel, text):
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def test_dangling_subscribe_is_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "04_模块库/通用类/M50_主循环.md", M50)
            self._write(tmp, "04_模块库/技术文档类/M90_技术文档结构.md", M90)
            issues, stats = sc.scan(tmp)
            self.assertTrue(any("intent_received" in i for i in issues), issues)
            self.assertEqual(stats["techdoc_chain"], 1)

    def test_publisher_resolves_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            m50 = M50.replace("publish: []", "publish: [intent_received]")
            self._write(tmp, "04_模块库/通用类/M50_主循环.md", m50)
            self._write(tmp, "04_模块库/技术文档类/M90_技术文档结构.md", M90)
            issues, _ = sc.scan(tmp)
            self.assertEqual(issues, [])

    def test_mount_and_category_drift_detected(self):
        text = M90.replace("挂载点：P90（active）", "挂载点：P60（active）")
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "04_模块库/通用类/M50_主循环.md", M50)
            self._write(tmp, "04_模块库/技术文档类/M90_技术文档结构.md", text)
            issues, _ = sc.scan(tmp)
            self.assertTrue(any("挂载点漂移" in i for i in issues), issues)


if __name__ == "__main__":
    unittest.main()
