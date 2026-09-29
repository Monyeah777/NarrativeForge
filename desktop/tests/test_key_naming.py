#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""资产键命名规范机检（`core/key_naming.py`）回归测试 —— 资产密度面 GAP-5。

关键断言：形态/词表双判据来自**声明件**（不写死）、未登记与形态错都判 FAIL 且带修复指引、
词表未回看记 WARN、缺声明件 fail-closed、真仓零违规。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import key_naming as kn  # noqa: E402


def _decl(tmp: str, pattern: str, keys) -> None:
    p = Path(tmp) / kn.DECL_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"schema": "nf-asset-keys/1", "pattern": pattern,
                             "keys": {k: {"note": "t", "scope": "domain_pack"} for k in keys}},
                            ensure_ascii=False), encoding="utf-8")


def _asset(tmp: str, rel: str, key: str) -> None:
    p = Path(tmp) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('<!-- nf-asset: key="%s" version="1.0" status="active" -->\n\n# x\n' % key,
                 encoding="utf-8")


class DeclarationTest(unittest.TestCase):
    def test_missing_declaration_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, _w, _s = kn.scan(tmp)
        self.assertTrue(any(kn.DECL_REL in i and "修复指引" in i for i in issues), issues)

    def test_bad_json_declaration_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / kn.DECL_REL
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("{not json", encoding="utf-8")
            issues, _w, _s = kn.scan(tmp)
        self.assertTrue(any("合法 JSON" in i for i in issues), issues)

    def test_pattern_comes_from_declaration(self):
        """把 pattern 收紧到只许 CONCEPT_GRAPH → 既有的 OTHER 键必须被判形态不合。"""
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, "^CONCEPT_GRAPH$", ["CONCEPT_GRAPH", "OTHER"])
            _asset(tmp, "community/x/assets/OTHER.md", "OTHER")
            issues, _w, _s = kn.scan(tmp)
        self.assertTrue(any("形态不合规范" in i for i in issues), issues)


class JudgementTest(unittest.TestCase):
    def test_unregistered_key_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, "^[A-Z][A-Z0-9_]{2,39}$", ["DOMAIN_SPEC"])
            _asset(tmp, "community/x/assets/NEW_THING.md", "NEW_THING")
            _asset(tmp, "community/x/assets/DOMAIN_SPEC.md", "DOMAIN_SPEC")
            issues, _w, _s = kn.scan(tmp)
        self.assertTrue(any("未登记进词表" in i and kn.DECL_REL in i for i in issues), issues)

    def test_lowercase_key_fails_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, "^[A-Z][A-Z0-9_]{2,39}$", ["concept_graph"])
            _asset(tmp, "community/x/assets/a.md", "concept_graph")
            issues, _w, _s = kn.scan(tmp)
        self.assertTrue(any("形态不合规范" in i for i in issues), issues)

    def test_unused_registered_key_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, "^[A-Z][A-Z0-9_]{2,39}$", ["DOMAIN_SPEC", "NEVER_USED"])
            _asset(tmp, "community/x/assets/DOMAIN_SPEC.md", "DOMAIN_SPEC")
            issues, warns, _s = kn.scan(tmp)
        self.assertEqual([], issues)
        self.assertTrue(any("NEVER_USED" in w for w in warns), warns)

    def test_provenance_keys_are_also_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            _decl(tmp, "^[A-Z][A-Z0-9_]{2,39}$", ["DOMAIN_SPEC"])
            p = Path(tmp) / "05_资产库/provenance.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({"assets": [{"key": "ROGUE_KEY", "file": "x.md"}]}),
                         encoding="utf-8")
            issues, _w, _s = kn.scan(tmp)
        self.assertTrue(any("ROGUE_KEY" in i for i in issues), issues)


class RealRepoTest(unittest.TestCase):
    def test_real_repo_keys_all_registered_and_wellformed(self):
        issues, _w, stats = kn.scan(str(ROOT))
        self.assertEqual([], issues, "真仓键须全部在册且形态合规：%s" % issues[:3])
        self.assertGreaterEqual(stats["keys_seen"], 5)
        self.assertEqual(stats["keys_seen"], stats["registered"],
                         "盘上键数应等于词表条数（存量全在册）")

    def test_declaration_is_committed(self):
        self.assertTrue((ROOT / kn.DECL_REL).is_file())


if __name__ == "__main__":
    unittest.main()
