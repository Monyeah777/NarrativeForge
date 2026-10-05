#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判据接线覆盖（`core/judgement_coverage.py`）回归测试 —— 静态可核验 / 架构纯度面。

关键断言：未接线且未登记判 FAIL（带修复指引）、例外登记放行、例外失效记 WARN、
消费精度只认**真调用 / 真导入 / 注册表带引号名**（注释与文档串里的裸名字不算，本模块踩过
该假阳性的坑）、真仓零 FAIL 且例外表不虚挂。
"""
import json
import sys
from typing import Optional
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import judgement_coverage as jc  # noqa: E402


def _file(tmp: str, rel: str, text: str) -> Path:
    p = Path(tmp) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _decl(tmp: str, exceptions=None, schema: Optional[str] = None) -> None:
    _file(tmp, jc.DECL_REL, json.dumps(
        {"schema": schema if schema is not None else jc.SCHEMA,
         "exceptions": exceptions or {}}, ensure_ascii=False))


def _scanner(tmp: str, name: str, extra: str = "") -> None:
    _file(tmp, "%s/%s.py" % (jc.CORE_DIR, name),
          "def scan(root='.'):\n    return [], [], {}\n" + extra)


class DeclarationTest(unittest.TestCase):
    def test_missing_declaration_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, _w, _s = jc.scan(tmp)
        self.assertTrue(any(jc.DECL_REL in i and "修复指引" in i for i in issues), issues)

    def test_wrong_schema_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, schema="nf-other/1")
            issues, _w, _s = jc.scan(tmp)
        self.assertTrue(any("schema" in i for i in issues), issues)


class CandidatesTest(unittest.TestCase):
    def test_only_modules_defining_scan_are_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            _scanner(tmp, "alpha")
            _file(tmp, "%s/beta.py" % jc.CORE_DIR, "def runner(root='.'):\n    return 1\n")
            self.assertEqual(["alpha"], jc.candidates(tmp))
        self.assertTrue(jc.SCAN_DEF.search("def scan(root='.'):\n"))
        self.assertIsNone(jc.SCAN_DEF.search("    def scan(self):\n"))


class ConsumptionPrecisionTest(unittest.TestCase):
    def test_quoted_registry_entry_counts(self):
        """注册式引用（`verify_report` 判据表 / `quality_depth_scan` 子扫描表）算消费。"""
        with tempfile.TemporaryDirectory() as tmp:
            _scanner(tmp, "alpha")
            _file(tmp, "desktop/src/core/verify_report.py", 'SPECS = (("x", "y", "alpha"),)\n')
            self.assertIn("desktop/src/core/verify_report.py", jc.consumers_of("alpha", tmp))

    def test_bare_mention_in_comment_or_docstring_is_not_consumption(self):
        """本模块踩过的假阳性：例外说明/注释里出现模块名，不算被消费。"""
        with tempfile.TemporaryDirectory() as tmp:
            _scanner(tmp, "alpha")
            _file(tmp, "desktop/src/core/beta.py",
                  '"""alpha 是一个只报告不设闸的判据（说明文字，不是消费）。"""\n'
                  "# 例外：alpha 由外部驱动\nx = 1\n")
            self.assertEqual([], jc.consumers_of("alpha", tmp))

    def test_call_site_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            _scanner(tmp, "alpha")
            _file(tmp, "desktop/src/core/beta.py", "from core import alpha\n\n"
                                                   "def f(root):\n    return alpha.scan(root)\n")
            self.assertIn("desktop/src/core/beta.py", jc.consumers_of("alpha", tmp))
            _file(tmp, "verify.sh", "python -c \"from core import alpha; alpha.scan('.')\"\n")
            self.assertIn("verify.sh", jc.consumers_of("alpha", tmp))

    def test_import_alone_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            _scanner(tmp, "alpha")
            _file(tmp, "desktop/src/core/beta.py", "from core import alpha  # noqa: F401\n")
            self.assertIn("desktop/src/core/beta.py", jc.consumers_of("alpha", tmp))

    def test_self_is_not_a_consumer(self):
        with tempfile.TemporaryDirectory() as tmp:
            _scanner(tmp, "alpha", extra="\ndef g():\n    return alpha.scan('.')\n")
            self.assertEqual([], jc.consumers_of("alpha", tmp))


class ScanTest(unittest.TestCase):
    def test_orphan_without_exception_fails_with_repair_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp)
            _scanner(tmp, "alpha")
            issues, warns, stats = jc.scan(tmp)
        self.assertEqual(1, len(issues))
        self.assertIn("alpha", issues[0])
        self.assertIn(jc.DECL_REL, issues[0])
        self.assertIn("修复指引", issues[0])
        self.assertEqual([], warns)
        self.assertEqual({"scanners": 1, "consumed": 0, "exceptions": 0, "orphans": 1}, stats)

    def test_registered_exception_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, exceptions={"alpha": "只读报告器，由外部按需驱动。"})
            _scanner(tmp, "alpha")
            issues, warns, stats = jc.scan(tmp)
        self.assertEqual([], issues)
        self.assertEqual([], warns)
        self.assertEqual(1, stats["exceptions"])
        self.assertEqual(1, stats["orphans"])

    def test_stale_exception_is_warn_not_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, exceptions={"alpha": "已失效的登记。"})
            _scanner(tmp, "alpha")
            _file(tmp, "desktop/src/core/beta.py", "from core import alpha  # noqa: F401\n")
            issues, warns, _s = jc.scan(tmp)
        self.assertEqual([], issues)
        self.assertTrue(any("例外已失效" in w and "alpha" in w for w in warns), warns)


class RealRepoTest(unittest.TestCase):
    def test_real_repo_has_no_failing_judgement(self):
        """真仓：每条暴露 scan() 的判据要么被消费、要么在例外表里；例外表不得虚挂。"""
        issues, warns, stats = jc.scan(str(ROOT))
        self.assertEqual([], issues)
        self.assertEqual([], warns)
        self.assertGreater(stats["consumed"], 40, "真仓消费面须有规模（判据自身要有效）")
        self.assertIn("judgement_coverage", jc.candidates(str(ROOT)),
                      "本判据自己也要在候选集里（否则判据不覆盖自己）")


if __name__ == "__main__":
    unittest.main()
