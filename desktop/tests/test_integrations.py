# -*- coding: utf-8 -*-
"""接入面（core/integrations.py）回归：描述件在场 + 词表封闭 + 投影逐字 + 变异自证。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import integrations as it  # noqa: E402


class RealRepoTest(unittest.TestCase):
    def test_real_repo_has_no_issue(self):
        issues, stats = it.check(str(ROOT))
        self.assertEqual([], issues, issues)
        self.assertGreaterEqual(stats["count"], 10, "接入面退化成空转")
        for must in ("mcp", "tui", "cli"):
            self.assertIn(must, stats["ids"])

    def test_strings_present_for_every_integration(self):
        for iid in it.check(str(ROOT))[1]["ids"]:
            row = it.localized(str(ROOT), iid, "ja")
            self.assertTrue(row.get("title"), "接入面 %s 缺 ja title" % iid)
            self.assertTrue(row.get("summary"), "接入面 %s 缺 ja summary" % iid)

    def test_projection_matches_render(self):
        txt = (ROOT / it.INDEX_REL).read_text(encoding="utf-8")
        a = it.BEGIN in txt and it.END in txt
        self.assertTrue(a, "投影缺生成区标记")
        seg = txt.split(it.BEGIN, 1)[1].split(it.END, 1)[0].strip()
        self.assertEqual(it.render_index(str(ROOT)).strip(), seg, "投影与实时渲染不一致")


class MutationTest(unittest.TestCase):
    def _mini(self, root: Path, rec: dict) -> None:
        (root / "verify.sh").write_text("x\n", encoding="utf-8")
        sdir = root / "protocol" / "schema"
        sdir.mkdir(parents=True, exist_ok=True)
        for name in ("integration.schema.json", "integration_strings.schema.json"):
            src = ROOT / "protocol" / "schema" / name
            if src.is_file():
                (sdir / name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        (root / "protocol" / "locales.json").write_text(json.dumps(
            {"schema": "nf-locales/1", "canonical": "zh",
             "locales": [{"id": x, "label": x, "entry": "README.md", "codeowner": "@x",
                          "coverage": "entry"} for x in ("zh", "en", "ja")]},
            ensure_ascii=False), encoding="utf-8")
        d = root / it.DIR / "demo"
        d.mkdir(parents=True)
        (d / "integration.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
        (root / it.DIR / "README.md").write_text(
            it.BEGIN + "\n" + it.render_index(str(root)) + "\n" + it.END + "\n", encoding="utf-8")

    def _rec(self, **kw):
        base = {"schema": it.SCHEMA, "id": "demo", "title": "演示", "kind": "cli",
                "status": "active", "version": "1.0.0", "codeowner": "@tester",
                "tier": "core", "entry": {"path": "verify.sh"}, "docs": ["verify.sh"],
                "evidence": ["verify.sh"]}
        base.update(kw)
        return base

    def test_schema_violation_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            self._mini(Path(d), self._rec(tier="bogus"))
            issues, _ = it.check(d)
            self.assertTrue(any("越界" in i or "tier" in i for i in issues), issues)

    def test_bad_kind_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            self._mini(Path(d), self._rec(kind="bogus"))
            issues, _ = it.check(d)
            self.assertTrue(any("kind" in i for i in issues), issues)

    def test_missing_evidence_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            self._mini(Path(d), self._rec(evidence=["nope/missing.py"]))
            issues, _ = it.check(d)
            self.assertTrue(any("不在场" in i for i in issues), issues)

    def test_missing_locale_strings_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            self._mini(r, self._rec())
            (r / it.DIR / "demo" / "strings.json").write_text(json.dumps(
                {"schema": "nf-integration-strings/1", "id": "demo",
                 "locales": {"zh": {"title": "演示", "summary": "中文说明"},
                             "en": {"title": "Demo", "summary": "English text"}}},
                ensure_ascii=False), encoding="utf-8")
            issues, _ = it.check(d)
            self.assertTrue(any("strings 缺语言" in i for i in issues), issues)

    def test_projection_drift_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            self._mini(Path(d), self._rec())
            (Path(d) / it.DIR / "README.md").write_text(
                it.BEGIN + "\n手改过的一行\n" + it.END + "\n", encoding="utf-8")
            issues, _ = it.check(d)
            self.assertTrue(any("生成区" in i for i in issues), issues)

    def test_empty_root_reports_issue_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            issues, stats = it.check(d)
            self.assertTrue(issues)
            self.assertEqual({}, stats)

    def test_unknown_nf_subcommand_in_entry_is_caught(self):
        """接入面卡里的 **nf 子命令**也要在册：「nf srve」这种拼错此前全绿（只查引用的件在场）。"""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._mini(root, self._rec(entry={"command": "python scripts/nf.py srve"}))
            (root / "scripts").mkdir()
            (root / "scripts" / "nf.py").write_text('sub.add_parser("serve")' + chr(10),
                                                    encoding="utf-8", newline=chr(10))
            issues, _ = it.check(d)
            self.assertTrue(any("srve" in i for i in issues), issues)

    def test_registered_nf_subcommand_passes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._mini(root, self._rec(entry={"command": "python scripts/nf.py serve"}))
            (root / "scripts").mkdir()
            (root / "scripts" / "nf.py").write_text('sub.add_parser("serve")' + chr(10),
                                                    encoding="utf-8", newline=chr(10))
            issues, _ = it.check(d)
            self.assertEqual([], [i for i in issues if "子命令" in i], issues)

    def test_no_registry_means_no_false_red(self):
        """读不到 CLI 注册表时**不判**（宁少不假）——只有注册表在场才核子命令。"""
        with tempfile.TemporaryDirectory() as d:
            self._mini(Path(d), self._rec(entry={"command": "python scripts/nf.py srve"}))
            issues, _ = it.check(d)
            self.assertEqual([], [i for i in issues if "子命令" in i], issues)


if __name__ == "__main__":
    unittest.main()
