#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""变更日志生成（`core/changelog_gen.py`）回归测试 —— 渲染确定 + 写面幂等 + 丢内容守卫。

丢内容守卫的出处：62 计划 §二·1「首例发布」取证（2026-10-05）——同版本节替换会把
人工积累的未发布节静默换掉（实测 1790 行 → 13 行），故写面默认 fail-closed。
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import changelog_gen as cg  # noqa: E402


def _root(tmp: str, changelog: str, entries=None) -> Path:
    r = Path(tmp)
    (r / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    d = r / "changes" / "unreleased"
    d.mkdir(parents=True, exist_ok=True)
    for name, body in (entries or {}).items():
        (d / name).write_text(body, encoding="utf-8")
    return r


OLD = "# Changelog\n\n## [2.11.0] - 2026-09-15\n\n- 旧版本条目\n"
CURATED = ("# Changelog\n\n## [2.12.0] - 未发布\n\n"
           "- **人工积累的详细条目一**（1790 行里的第一条）\n"
           "- **人工积累的详细条目二**\n\n"
           "## [2.11.0] - 2026-09-15\n\n- 旧版本条目\n")
ENTRY = {"e.md": "type: feat\nsurface: x\nnote: 生成条目\n"}


class RenderTest(unittest.TestCase):
    def test_render_is_deterministic_and_traceable(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = _root(tmp, OLD, ENTRY)
            a = cg.render(str(r), version="2.13.0", date="2026-10-05", use_commits=False)
            b = cg.render(str(r), version="2.13.0", date="2026-10-05", use_commits=False)
            self.assertEqual(a, b)
            self.assertIn("- 生成条目（x）", a)


class InsertGuardTest(unittest.TestCase):
    def test_fresh_version_inserts_after_header(self):
        section = "## [2.13.0] - 2026-10-05\n\n- 新条目\n"
        out = cg.insert_into_changelog(OLD, section, "2.13.0")
        self.assertTrue(out.startswith("# Changelog"))
        self.assertIn(section.strip(), out)
        self.assertIn("## [2.11.0]", out)

    def test_idempotent_rewrite_of_generated_section_allowed(self):
        section = "## [2.12.0] - 2026-10-05\n\n- 生成条目\n"
        one = cg.insert_into_changelog(OLD, section, "2.12.0")
        two = cg.insert_into_changelog(one, section, "2.12.0")
        self.assertEqual(one, two, "同版本重复写须幂等")

    def test_replace_that_would_lose_bullets_is_refused(self):
        section = "## [2.12.0] - 2026-10-05\n\n- 生成条目\n"
        with self.assertRaises(ValueError) as ctx:
            cg.insert_into_changelog(CURATED, section, "2.12.0")
        self.assertIn("丢失", str(ctx.exception))
        self.assertIn("fail-closed", str(ctx.exception))


class WriteTest(unittest.TestCase):
    def test_write_refuses_and_leaves_file_and_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = _root(tmp, CURATED, ENTRY)
            before = (r / "CHANGELOG.md").read_text(encoding="utf-8")
            res = cg.write(str(r), version="2.12.0", date="2026-10-05", use_commits=False)
            self.assertFalse(res.get("ok"))
            self.assertTrue(any("丢失" in i for i in res["issues"]))
            self.assertEqual(before, (r / "CHANGELOG.md").read_text(encoding="utf-8"))
            self.assertTrue((r / "changes" / "unreleased" / "e.md").is_file(), "拒绝时不得归档条目")

    def test_write_lands_and_archives_on_fresh_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = _root(tmp, OLD, ENTRY)
            res = cg.write(str(r), version="2.13.0", date="2026-10-05", use_commits=False)
            self.assertTrue(res.get("ok"), res)
            self.assertEqual(["e.md"], res["archived"])
            txt = (r / "CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("## [2.13.0] - 2026-10-05", txt)
            self.assertTrue((r / "changes" / "2.13.0" / "e.md").is_file())


if __name__ == "__main__":
    unittest.main()
