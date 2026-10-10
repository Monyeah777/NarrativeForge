# -*- coding: utf-8 -*-
"""包管理器面 CLI（scripts/pkg.py）回归测试 —— 品类枚举 / 取件 / 检索（机器面）。"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "scripts" / "pkg.py"


def _run(*argv):
    p = subprocess.run([sys.executable, str(PKG), *argv], cwd=str(ROOT),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=180)
    return p.returncode, p.stdout


class PkgCliTest(unittest.TestCase):
    def test_categories_json(self):
        code, out = _run("categories", "--json")
        self.assertEqual(0, code, out[:200])
        doc = json.loads(out)
        self.assertEqual("pkg-categories", doc["kind"])
        ids = {r["id"] for r in doc["rows"]}
        self.assertIn("patterns", ids)
        self.assertIn("tier:contract", ids)
        self.assertTrue(any(r["attributed"] is False for r in doc["rows"]))

    def test_ls_core_pipelines(self):
        code, out = _run("ls", "core-pipelines", "--json")
        self.assertEqual(0, code, out[:200])
        doc = json.loads(out)
        self.assertEqual("pkg-ls", doc["kind"])
        self.assertIn("P01", {r["id"] for r in doc["rows"]})

    def test_find_community_pipeline(self):
        code, out = _run("find", "P04", "--json")
        self.assertEqual(0, code, out[:200])
        doc = json.loads(out)
        self.assertEqual("pkg-find", doc["kind"])
        self.assertTrue(any(r["category"] == "community-pipelines" for r in doc["rows"]), doc)


    def test_check_reports_attribution_state(self):
        code, out = _run("check", "--json")
        self.assertEqual(0, code, out[:300])
        doc = json.loads(out)
        self.assertEqual("pkg-check", doc["kind"])
        self.assertTrue(doc["ok"])
        self.assertEqual([], doc["issues"])
        self.assertTrue(any("命名子面" in w for w in doc["warns"]), doc["warns"])
        self.assertFalse(any("未归属" in w for w in doc["warns"]), doc["warns"])
        self.assertGreaterEqual(doc["stats"]["categories"], 10)


if __name__ == "__main__":
    unittest.main()
