#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""编码卫生门禁单测（check33 新面：RFC 3629 / RFC 8259 §4 / UAX #15 / UTS #39）。

每条规定一条**正例**（合规树零 issue）与**变异负例**（注入违规必须被抓）——
「check 的 check」写法与 test_purity_scan 同源。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import text_hygiene as th  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])
GA = "* text=auto eol=lf\n"


def _write(root, rel, text, encoding="utf-8"):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path) or root, exist_ok=True)
    with open(path, "w", encoding=encoding, newline="") as fh:
        fh.write(text)
    return path


def _write_bytes(root, rel, blob):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path) or root, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(blob)
    return path


class TextHygieneTest(unittest.TestCase):
    def test_clean_tree_has_no_issue(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ".gitattributes", GA)
            _write(tmp, "protocol/x.json", '{"a": 1, "模块:M01": {"b": "c"}}\n')
            _write(tmp, "README.md", "# 标题\n")
            issues, stats = th.scan(tmp)
            self.assertEqual(issues, [])
            self.assertEqual(stats["json"], 1)
            self.assertEqual(stats["crlf"], 0)

    def test_real_repo_is_clean(self):
        issues, stats = th.scan(ROOT)
        self.assertEqual(issues, [], "仓库自身编码卫生须零 issue：%s" % issues[:3])
        self.assertGreater(stats["keys_checked"], 1000)

    def test_mutation_missing_gitattributes_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "README.md", "# 标题\n")
            issues, _ = th.scan(tmp)
            self.assertTrue(any(".gitattributes" in i for i in issues), issues)

    def test_mutation_gitattributes_without_lf_declaration(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ".gitattributes", "*.png binary\n")
            issues, _ = th.scan(tmp)
            self.assertTrue(any("eol=lf" in i for i in issues), issues)

    def test_mutation_crlf_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ".gitattributes", GA)
            _write_bytes(tmp, "README.md", "# 标题\r\n第二行\r\n".encode("utf-8"))
            issues, stats = th.scan(tmp)
            self.assertEqual(stats["crlf"], 1)
            self.assertTrue(any("CRLF" in i for i in issues), issues)

    def test_mutation_bom_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ".gitattributes", GA)
            _write_bytes(tmp, "protocol/x.json", b"\xef\xbb\xbf{}\n")
            issues, stats = th.scan(tmp)
            self.assertEqual(stats["bom"], 1)
            self.assertTrue(any("BOM" in i for i in issues), issues)

    def test_mutation_bad_utf8_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ".gitattributes", GA)
            _write_bytes(tmp, "notes.txt", b"\xc3\x28 bad utf8 line\n")
            issues, _ = th.scan(tmp)
            self.assertTrue(any("UTF-8" in i for i in issues), issues)

    def test_mutation_duplicate_json_key_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ".gitattributes", GA)
            _write(tmp, "protocol/x.json", '{"a": 1, "a": 2}\n')
            issues, _ = th.scan(tmp)
            self.assertTrue(any("重复键" in i for i in issues), issues)

    def test_mutation_invisible_and_fullwidth_key_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ".gitattributes", GA)
            _write(tmp, "protocol/x.json",
                   '{"a\u200bb": 1, "\uff21BC": 2}\n')
            issues, _ = th.scan(tmp)
            self.assertEqual(len([i for i in issues if "JSON 键" in i]), 2, issues)

    def test_identifier_issue_units(self):
        self.assertEqual(th.identifier_issue("M01"), "")
        self.assertEqual(th.identifier_issue("通用:M10"), "")
        self.assertEqual(th.identifier_issue("$schema"), "")
        self.assertIn("NFC", th.identifier_issue("e\u0301"))
        self.assertIn("隐形", th.identifier_issue("a\u00a0b"))
        self.assertIn("越界", th.identifier_issue("a→b"))
        self.assertIn("空", th.identifier_issue(""))

    def test_semver_lexemes(self):
        """SemVer 2.0.0 词法（§9/§10）：三段必填、数字标识禁前导零、预发布段非空。"""
        for good in ("1.0.0", "1.1.0", "0.0.1", "1.0.0-alpha.1", "1.0.0+build.5",
                     "1.0.0-rc.1+exp.sha.5114f85"):
            self.assertEqual(th.semver_issue(good), "", good)
        for bad, why in (("01.0.0", "前导零"), ("1.0", "缺补丁号"), ("1.0.0-", "空段"),
                         ("1.0.0-01", "不符合"), ("v1.0.0", "不符合"), ("", "空")):
            self.assertIn(why, th.semver_issue(bad), bad)

    def test_version_source_scans_packages(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ".gitattributes", GA)
            _write(tmp, "community/演示包/protocol.yaml",
                   "package:\n  version: \"01.0.0\"\n")
            issues, stats = th.scan(tmp)
            self.assertEqual(stats["versions_checked"], 1)
            self.assertTrue(any("版本值" in i and "前导零" in i for i in issues), issues)
            _write(tmp, "community/演示包/protocol.yaml",
                   "package:\n  version: \"1.0.0\"\n")
            issues2, stats2 = th.scan(tmp)
            self.assertEqual(stats2["versions_checked"], 1)
            self.assertEqual([i for i in issues2 if "版本值" in i], [])

    def test_repo_package_versions_are_semver(self):
        _issues, stats = th.scan(ROOT)
        self.assertGreaterEqual(stats["versions_checked"], 7, "七个域包版本位须在扫")

    def test_identifier_value_face_scanned(self):
        """标识**值**面：键有判据、值没有 = 给同形留后门（西里尔 М 当 M 用）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ".gitattributes", GA)
            _write(tmp, "desktop/src/core/registry.json", json.dumps(
                {"modules": [{"id": "\u041c00", "category": "通用类"}]},
                ensure_ascii=False))
            issues, stats = th.scan(tmp)
            self.assertEqual(stats["values_checked"], 2)
            self.assertTrue(any("modules[*].id" in i for i in issues), issues)
        _issues, stats_repo = th.scan(ROOT)
        self.assertGreaterEqual(stats_repo["values_checked"], 50,
                                "仓库登记册标识值面须在扫")


if __name__ == "__main__":
    unittest.main()
