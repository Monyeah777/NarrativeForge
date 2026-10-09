# -*- coding: utf-8 -*-
"""NFA-L guard 诊断接入编辑器面（nf lsp）单测。

判据：管线声明的 condition（=nf-expr）未登记符号/非 bool 时，LSP 诊断必须落到真实行/列、
带 nfal-guard 源与诊断码；非管线文档不产 guard 诊断；真仓迁移后的管线零 fail 诊断。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import lsp_doc  # noqa: E402

P01 = "03_管线库/P01_标准管线.md"
BAD = ("structure:\n  flow:\n    - from: P00\n      to: P10\n"
       "      condition: =NoSuch.slot == 1\n")


def _guard(diags):
    return [d for d in diags if d.get("source") == "nfal-guard"]


class TestLspGuardDiagnostics(unittest.TestCase):
    def test_bad_guard_yields_error_at_real_position(self):
        diags = _guard(lsp_doc.diagnose("03_管线库/P99.md", BAD, str(ROOT)))
        self.assertTrue(diags, "未登记符号应产出 guard 诊断")
        codes = {d["code"] for d in diags}
        self.assertIn("E0301", codes)
        d = diags[0]
        self.assertEqual(d["severity"], 1, "fail 诊断应为 Error")
        self.assertEqual(d["range"]["start"]["line"], 4, "诊断应落在 condition 行（0-based）")

    def test_clean_real_pipeline_has_no_error(self):
        text = (ROOT / P01).read_text(encoding="utf-8")
        errs = [d for d in _guard(lsp_doc.diagnose(P01, text, str(ROOT))) if d["severity"] == 1]
        self.assertEqual([], errs, "迁移后的真仓管线不应有 guard 错误")

    def test_non_pipeline_doc_produces_no_guard_diag(self):
        text = "condition: =NoSuch.slot == 1\n"
        diags = _guard(lsp_doc.diagnose("04_模块库/通用类/M00_数据结构.md", text, str(ROOT)))
        self.assertEqual([], diags)

    def test_prose_condition_is_not_an_error(self):
        text = "      condition: 主循环回卷（散文）\n"
        diags = _guard(lsp_doc.diagnose("03_管线库/P98.md", text, str(ROOT)))
        self.assertEqual([], diags, "散文 condition 不产 guard 诊断（由 nfal build 记 advisory）")


if __name__ == "__main__":
    unittest.main()
