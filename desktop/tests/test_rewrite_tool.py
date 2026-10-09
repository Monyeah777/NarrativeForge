# -*- coding: utf-8 -*-
"""机械改写工具（scripts/rewrite_text.py）的常驻判据。

内部差距实证（2026-10-08 两次自伤）：一处生成笔误被我用**全仓批量替换**去修，结果把五处**合法正文**
里的反斜杠削掉——语法不报、判据不报，只能靠人眼回捞。本仓已有惯例（atomic_write 单写面、各生成器的
--write/--check 双态、rebind 的 --check 干跑），但缺一个**通用**的「干跑优先 + 逐行对照 + 爆炸半径闸门」
入口。本件把这个入口的行为钉死：干跑不动盘、落盘只改命中行、超限拒绝、可复验残留。
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "rewrite_text.py"


class RewriteTextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base / "a.py").write_text("x = 'old'\ny = 'old'\n", encoding="utf-8", newline="\n")
        (self.base / "b.md").write_text("z = 'old'\n", encoding="utf-8", newline="\n")
        (self.base / "c.py").write_text("w = 'other'\n", encoding="utf-8", newline="\n")
        self.addCleanup(self.tmp.cleanup)

    def _run(self, *argv):
        return subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.base), *argv],
                              capture_output=True, encoding="utf-8", errors="replace", timeout=120)

    def _text(self, rel):
        return (self.base / rel).read_text(encoding="utf-8")

    def test_dry_run_prints_table_and_changes_nothing(self):
        before = self._text("a.py")
        p = self._run("--find", "old", "--replace", "new", "--include", "**/*.py")
        self.assertEqual(0, p.returncode, p.stdout + p.stderr)
        self.assertIn("a.py:1", p.stdout)
        self.assertIn("--write", p.stdout)
        self.assertEqual(before, self._text("a.py"), "干跑不得改盘")
        self.assertEqual("", p.stderr)

    def test_write_touches_only_matching_files(self):
        p = self._run("--find", "old", "--replace", "new", "--include", "**/*.py", "--write")
        self.assertEqual(0, p.returncode, p.stdout + p.stderr)
        self.assertEqual("x = 'new'\ny = 'new'\n", self._text("a.py"))
        self.assertEqual("w = 'other'\n", self._text("c.py"), "未命中文件不得动")
        self.assertEqual("z = 'old'\n", self._text("b.md"), "include 之外的文件不得动")
        q = self._run("--find", "old", "--replace", "new", "--include", "**/*.py", "--check")
        self.assertEqual(0, q.returncode, "落盘后不应再有命中")

    def test_check_reports_remaining_hits(self):
        p = self._run("--find", "old", "--replace", "new", "--include", "**/*.py", "--check")
        self.assertEqual(1, p.returncode, "还有命中就该 rc=1")

    def test_blast_radius_guard_refuses_without_touching_anything(self):
        """超上限即拒绝——这条正是「一处笔误改成全仓事故」的那道闸门。"""
        before = self._text("a.py")
        p = self._run("--find", "old", "--replace", "new", "--include", "**/*", "--max-hits", "1")
        self.assertEqual(2, p.returncode, p.stdout + p.stderr)
        self.assertIn("拒绝执行", p.stdout)
        self.assertEqual(before, self._text("a.py"), "拒绝时不得改盘")

    def test_undecodable_file_is_skipped_not_corrupted(self):
        blob = (self.base / "bin.py")
        blob.write_bytes(b"\xff\xfeold\x00")
        p = self._run("--find", "old", "--replace", "new", "--include", "**/*.py", "--write")
        self.assertEqual(0, p.returncode, p.stdout + p.stderr)
        self.assertIn("跳过 bin.py", p.stdout)
        self.assertEqual(b"\xff\xfeold\x00", blob.read_bytes(), "非文本件不得被改写")


if __name__ == "__main__":
    unittest.main()
