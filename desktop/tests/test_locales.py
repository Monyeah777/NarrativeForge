# -*- coding: utf-8 -*-
"""语言面（core/locales.py）回归：文件即真源 + 逐面同事实 + 切换行 + 结构对齐 + 变异自证。"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import locales as lc  # noqa: E402


class RealRepoTest(unittest.TestCase):
    def test_three_locales_and_no_issue(self):
        locs = lc.entries(str(ROOT))
        self.assertEqual(["zh", "en", "ja"], [x for x, _ in locs],
                         "语言面集合变了（判据按在场文件推导）")
        issues, stats = lc.check(str(ROOT))
        self.assertEqual([], issues, issues)
        self.assertEqual(3, len(stats["locales"]))

    def test_switcher_enumerates_all_locales(self):
        locs = lc.entries(str(ROOT))
        for lang, _fn in locs:
            line = lc.switcher(locs, lang)
            for other, other_fn in locs:
                if other != lang:
                    self.assertIn(other_fn, line, "切换行漏了 %s" % other_fn)


class MutationTest(unittest.TestCase):
    def test_missing_anchor_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            (r / "verify.sh").write_text("x\n", encoding="utf-8")
            (r / "README.md").write_text("# T\n\n<!-- nf:locales --> 语言 / Languages：**中文**\n",
                                         encoding="utf-8")
            (r / "README.en.md").write_text("# T\n\n<!-- nf:locales --> 语言 / Languages：[中文](README.md) · **English**\n",
                                            encoding="utf-8")
            issues, _ = lc.check(d)
            self.assertTrue(any("缺机读锚点" in i for i in issues), issues)

    def test_missing_switcher_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            (r / "verify.sh").write_text("x\n", encoding="utf-8")
            anchors = "".join(lc.anchors()) + " v2.30\n"
            (r / "README.md").write_text("# T\n\n" + anchors, encoding="utf-8")
            (r / "README.en.md").write_text("# T\n\n" + anchors, encoding="utf-8")
            issues, _ = lc.check(d)
            self.assertTrue(any("切换行" in i for i in issues), issues)

    def test_empty_root_reports_issue_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            issues, stats = lc.check(d)
            self.assertTrue(issues)
            self.assertEqual({}, stats)


class RegistryTest(unittest.TestCase):
    """注册表语义：覆盖面词表 / 责任方 / 未声明的多语文档（第二轮补的判据）。"""

    def test_real_registry_is_declared(self):
        data, issues = lc.registry(str(ROOT))
        self.assertEqual([], issues)
        self.assertEqual(["zh", "en", "ja"], [x["id"] for x in data["locales"]])
        for x in data["locales"]:
            self.assertIn(x["coverage"], lc.COVERAGES)
            self.assertTrue(x["codeowner"])
            self.assertTrue(x["label"])

    def _mini(self, root, registry):
        import json
        (root / "verify.sh").write_text("x\n", encoding="utf-8")
        (root / "README.md").write_text("# T\n", encoding="utf-8")
        (root / "README.en.md").write_text("# T\n", encoding="utf-8")
        (root / "protocol").mkdir(parents=True, exist_ok=True)
        (root / "protocol" / "locales.json").write_text(
            json.dumps(registry, ensure_ascii=False), encoding="utf-8")

    def test_missing_codeowner_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            self._mini(Path(d), {"schema": "nf-locales/1", "canonical": "zh", "guides": [],
                                 "locales": [{"id": "zh", "label": "中文", "entry": "README.md",
                                              "coverage": "entry"},
                                             {"id": "en", "label": "English", "entry": "README.en.md",
                                              "codeowner": "@x", "coverage": "entry"}]})
            issues, _ = lc.check(d)
            self.assertTrue(any("codeowner" in i for i in issues), issues)

    def test_undeclared_docs_locale_file_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            self._mini(Path(d), {"schema": "nf-locales/1", "canonical": "zh", "guides": [],
                                 "locales": [{"id": "zh", "label": "中文", "entry": "README.md",
                                              "codeowner": "@x", "coverage": "entry"},
                                             {"id": "en", "label": "English", "entry": "README.en.md",
                                              "codeowner": "@x", "coverage": "entry"}]})
            d2 = Path(d) / "docs" / "en"
            d2.mkdir(parents=True)
            (d2 / "foo.md").write_text("# 未声明\n", encoding="utf-8")
            issues, _ = lc.check(d)
            self.assertTrue(any("未声明的多语文档" in i for i in issues), issues)


class DocTreeTest(unittest.TestCase):
    """文档面（docs/<lang>/…）：路径镜像 + 源件摘要防过期（第二轮补的判据）。"""

    def _mini(self, root, registry, source, translation, tp):
        import json as _json
        (root / "verify.sh").write_text("x\n", encoding="utf-8")
        (root / "README.md").write_text("# T\n", encoding="utf-8")
        (root / "README.en.md").write_text("# T\n", encoding="utf-8")
        (root / "protocol").mkdir(parents=True, exist_ok=True)
        (root / "protocol" / "locales.json").write_text(
            _json.dumps(registry, ensure_ascii=False), encoding="utf-8")
        (root / "docs").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "a.md").write_text(source, encoding="utf-8")
        d = root / "docs" / "en"
        d.mkdir(parents=True, exist_ok=True)
        (d / "a.md").write_text(translation, encoding="utf-8")

    def _reg(self, digest):
        return {"schema": "nf-locales/1", "canonical": "zh",
                "locales": [{"id": "zh", "label": "中文", "entry": "README.md",
                             "codeowner": "@x", "coverage": "entry+guides"},
                            {"id": "en", "label": "English", "entry": "README.en.md",
                             "codeowner": "@x", "coverage": "entry+guides"}],
                "docs": [{"path": "docs/a.md",
                          "translations": {"en": {"path": "docs/en/a.md", "source_sha256": digest}}}]}

    def test_stale_translation_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            self._mini(Path(d), self._reg("0" * 64), "src v1\n", "translated\n", "docs/en/a.md")
            issues, _ = lc.check(d)
            self.assertTrue(any("译件过期" in i for i in issues), issues)

    def test_unsigned_translation_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            self._mini(Path(d), self._reg(""), "src v1\n", "translated\n", "docs/en/a.md")
            issues, _ = lc.check(d)
            self.assertTrue(any("未签源件摘要" in i for i in issues), issues)

    def test_non_mirrored_path_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            reg = self._reg("0" * 64)
            reg["docs"][0]["translations"]["en"]["path"] = "docs/en/deep/nested.md"
            self._mini(r, reg, "src\n", "t\n", "docs/en/a.md")
            (r / "docs" / "en" / "deep").mkdir(parents=True, exist_ok=True)
            (r / "docs" / "en" / "deep" / "nested.md").write_text("t\n", encoding="utf-8")
            issues, _ = lc.check(d)
            self.assertTrue(any("未镜像" in i for i in issues), issues)

    def test_stamp_signs_and_clears(self):
        with tempfile.TemporaryDirectory() as d:
            self._mini(Path(d), self._reg("0" * 64), "src v1\n", "translated\n", "docs/en/a.md")
            res = lc.stamp(d, write=True)
            self.assertTrue(res["ok"])
            issues, _ = lc.check(d)
            self.assertFalse(any("译件过期" in i for i in issues), issues)


if __name__ == "__main__":
    unittest.main()
