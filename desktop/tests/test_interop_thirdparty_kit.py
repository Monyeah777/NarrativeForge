# -*- coding: utf-8 -*-
"""他证通道（`scripts/interop_thirdparty_kit.py`）的输入形状与可达性判据。

实测缺口（2026-10-01）：`--record <不存在的证据件>` 直接 **FileNotFoundError 裸 traceback**；
`--emit --root <新目录>` 也崩（只给 `docs/` 建了目录，写 `results/` 那件时目录不在）。
两条都是「用户输入/落点形状」问题，必须给干净错误 + 修复指引。
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "interop_thirdparty_kit.py"


def _run(*argv):
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True,
                          encoding="utf-8", errors="replace", timeout=120, cwd=str(ROOT))


class ThirdPartyKitTest(unittest.TestCase):
    def test_emit_into_a_fresh_root_creates_both_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _run("--emit", "--root", tmp)
            self.assertNotIn("Traceback", (p.stdout or "") + (p.stderr or ""))
            self.assertEqual(0, p.returncode, p.stdout + p.stderr)
            self.assertTrue(Path(tmp, "docs", "interop-thirdparty.md").is_file())
            self.assertTrue(Path(tmp, "results",
                                 "interop-thirdparty-status.md").is_file())
            q = _run("--check", "--root", tmp)
            self.assertEqual(0, q.returncode, q.stdout + q.stderr)

    def test_record_missing_evidence_is_a_clean_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            _run("--emit", "--root", tmp)
            p = _run("--record", str(Path(tmp, "nope.jsonl")), "--root", tmp)
            text = (p.stdout or "") + (p.stderr or "")
            self.assertEqual(1, p.returncode, text)
            self.assertNotIn("Traceback", text)
            self.assertIn("证据件不存在", text)
            self.assertIn("修复指引", text)

    def test_record_broken_jsonl_is_a_clean_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            _run("--emit", "--root", tmp)
            bad = Path(tmp, "bad.jsonl")
            bad.write_text("not json\n", encoding="utf-8", newline="\n")
            p = _run("--record", str(bad), "--root", tmp)
            text = (p.stdout or "") + (p.stderr or "")
            self.assertEqual(1, p.returncode, text)
            self.assertNotIn("Traceback", text)
            self.assertIn("不是合法 JSONL", text)
            self.assertIn("修复指引", text)


if __name__ == "__main__":
    unittest.main()
