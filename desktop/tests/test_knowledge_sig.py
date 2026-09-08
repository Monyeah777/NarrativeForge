#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.8.0 波C C1/C2 —— 知识签名 + 版本差异检测单测（41 规划，纯 unittest）。"""
import os
import tempfile
import unittest
from pathlib import Path

sys_path = str(Path(__file__).resolve().parent.parent / "src")
if sys_path not in os.sys.path:
    os.sys.path.insert(0, sys_path)

from core import knowledge_sig as ks  # noqa: E402


DOC_A = """# 01 · 样例协议 v1.0

> 协议文档样例

## 1. 模块协议

```yaml
Module:
  id: M00
  layer: P00
```

引用 M01 与 P20。
"""

DOC_B = """# 01 · 样例协议 v1.1

> 协议文档样例（修订）

## 1. 模块协议

```yaml
Module:
  id: M00
  layer: P00
```

引用 M02 与 P20。
"""


class SignTest(unittest.TestCase):
    def test_build_signature_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "01_样例协议.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(DOC_A)
            sig = ks.build_signature("01_样例协议.md", tmp)
            self.assertEqual(sig["doc_id"], "01")
            self.assertEqual(sig["kind"], "doc")
            self.assertEqual(sig["version"], "v1.0")
            self.assertIn("M00", sig["self_id"])
            self.assertIn("M01", sig["refs"])
            self.assertIn("P20", sig["refs"])
            self.assertIn("样例协议", sig["title"])

    def test_signature_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "01_样例协议.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(DOC_A)
            s1 = ks.build_signature("01_样例协议.md", tmp)
            s2 = ks.build_signature("01_样例协议.md", tmp)
            self.assertEqual(ks.signature_digest(s1), ks.signature_digest(s2))

    def test_verify_reproducible_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("01_a.md", "24_b.md", "36_c.md"):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    fh.write("# %s\n正文 M01\n" % name)
            issues, stats = ks.verify_reproducible(tmp)
            self.assertEqual(issues, [])
            self.assertEqual(stats["docs"], 3)
            self.assertEqual(stats["reproducible"], 1)

    def test_diff_reports_changes_and_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            pa = os.path.join(tmp, "01_a.md")
            pb = os.path.join(tmp, "01_b.md")
            for path, text in ((pa, DOC_A), (pb, DOC_B)):
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text)
            diff = ks.diff_signatures(
                ks.build_signature("01_a.md", tmp),
                ks.build_signature("01_b.md", tmp))
            fields = {c["field"] for c in diff["changes"]}
            self.assertIn("version", fields)
            self.assertIn("refs", fields)   # M01→M02 引用替换
            self.assertEqual(diff["verdict"], "需评审（存在移除项：引用/章节收缩）")

    def test_diff_breaking_on_id_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            pa = os.path.join(tmp, "01_a.md")
            pb = os.path.join(tmp, "02_b.md")
            with open(pa, "w", encoding="utf-8") as fh:
                fh.write(DOC_A)
            with open(pb, "w", encoding="utf-8") as fh:
                fh.write(DOC_B)
            diff = ks.diff_signatures(
                ks.build_signature("01_a.md", tmp),
                ks.build_signature("02_b.md", tmp))
            self.assertEqual(diff["verdict"], "破坏（文档编号变更）")


if __name__ == "__main__":
    unittest.main()
