# -*- coding: utf-8 -*-
"""无效/变异语料 + golden 修复对（机制借鉴 Pipelex `invalid_*` 语料与 `*.golden.mthds`）。

两件事：
1. **无效语料**：每类应当被拒的输入各一件，断言对应该拒（防「校验器只会说通过」）；
2. **golden 修复对**：`fixtures/fixes/fix_cases.json` 里 输入 + 规则 → 期望输出，
   逐条对拍（防修复器漂移）。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import approval, autofix, receipts  # noqa: E402
from core import library as lib  # noqa: E402
from core import module_signature as ms  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIX_CASES = ROOT / "desktop" / "tests" / "fixtures" / "fixes" / "fix_cases.json"


class TestGoldenFixPairs(unittest.TestCase):
    def test_fix_cases_match_golden(self):
        doc = json.loads(FIX_CASES.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(doc["cases"]), 3)
        for case in doc["cases"]:
            got = autofix.apply_rules(case["input"], case["rules"], case["today"])
            self.assertEqual(got, case["expected"], "golden 不符：%s" % case["name"])


class TestInvalidCorpus(unittest.TestCase):
    """每类无效输入 → 对应校验器必须报错（变异测试思路：只增不减）。"""

    def _lib_tree(self, tmp, body):
        d = Path(tmp, "library")
        d.mkdir(parents=True, exist_ok=True)
        (d / "NF-9.md").write_text(body, encoding="utf-8")
        return tmp

    def test_invalid_missing_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._lib_tree(tmp, "# 无 frontmatter\n正文\n")
            self.assertTrue(any("缺 YAML frontmatter" in i
                                for i in lib.verify(tmp)[0]))

    def test_invalid_license_out_of_vocab(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._lib_tree(tmp, "---\nid: NF-9\ntype: T\ntitle: X\nlicense: WTFPL\n---\n正文\n")
            self.assertTrue(any("license 不在词表" in i for i in lib.verify(tmp)[0]))

    def test_invalid_supersede_cycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._lib_tree(tmp, "---\nid: NF-9\ntype: T\ntitle: X\n"
                                "status: superseded\nsuperseded_by: NF-9\n---\n正文\n")
            self.assertTrue(any("指向自身" in i for i in lib.verify(tmp)[0]))

    def test_invalid_receipt_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "library")
            d.mkdir(parents=True, exist_ok=True)
            (d / "NF-9.md").write_text(
                "---\nid: NF-9\ntype: T\ntitle: X\n---\n正文\n", encoding="utf-8")
            doc = receipts.build(tmp)
            self.assertEqual(receipts.verify(doc, tmp)[0], [])
            doc["entries"][0]["digest"] = "0" * 64
            self.assertTrue(receipts.verify(doc, tmp)[0])

    def test_invalid_approval_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            subject = Path(tmp, "doc.md")
            subject.write_text("# v1\n", encoding="utf-8")
            approval.approve(tmp, "doc.md", "作者", today="2026-09-14")
            self.assertEqual(approval.verify(tmp)[0], [])
            subject.write_text("# v2\n", encoding="utf-8")
            issues = approval.verify(tmp)[0]
            self.assertTrue(any("批准已失效" in i for i in issues), issues)

    def test_invalid_module_boundary_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            mods = Path(tmp, "04_模块库", "通用类")
            mods.mkdir(parents=True, exist_ok=True)
            fm = ("# 模块 M99 · 测试\n> 类别：通用｜挂载点：P00\n\n```yaml\n"
                  "machine_contract:\n  schema: \"1\"\n  id: M99\n  name: 测试\n"
                  "  category: 通用\n  layer: P00\n  inputs: [M00]\n  outputs: []\n"
                  "  events:\n    publish: []\n    subscribe: []\n  interfaces: []\n"
                  "```\n")
            (mods / "M99_测试.md").write_text(fm, encoding="utf-8")
            ms.write(tmp)
            self.assertEqual(ms.verify(tmp)[0], [])
            (mods / "M99_测试.md").write_text(
                fm.replace("inputs: [M00]", "inputs: [M00, M01]"), encoding="utf-8")
            self.assertTrue(any("边界漂移" in i for i in ms.verify(tmp)[0]))


if __name__ == "__main__":
    unittest.main()
