#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""社区资产行数基线单测（可重签工件：漂移检测 + 新增包未登记 + 缺包只 WARN + 重签幂等）。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import asset_line_baseline as alb  # noqa: E402


def _mk_pkg(root, pkg, files):
    d = Path(root, "community", pkg, "assets")
    d.mkdir(parents=True, exist_ok=True)
    for name, lines in files.items():
        Path(d, name).write_text("x\n" * lines, encoding="utf-8")
    Path(d, "README.md").write_text("不计入（README 例外）\n" * 50, encoding="utf-8")


class AssetLineBaselineTest(unittest.TestCase):
    def test_scan_counts_exclude_readme(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk_pkg(tmp, "甲包", {"a.md": 3, "b.md": 4})
            got = alb.scan(tmp)["packages"]
            self.assertEqual(len(got), 1)
            self.assertEqual((got[0]["files"], got[0]["lines"]), (2, 7))

    def test_missing_baseline_is_fail_with_resign_hint(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk_pkg(tmp, "甲包", {"a.md": 3})
            issues, _w, _s = alb.verify(tmp)
            self.assertTrue(any("nf asset baseline --write" in i for i in issues), issues)

    def test_line_drift_and_unregistered_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mk_pkg(tmp, "甲包", {"a.md": 3})
            alb.write(tmp)
            self.assertEqual(alb.verify(tmp)[0], [], "重签后应零 FAIL")
            # 内容改一行 → 漂移 FAIL（带重签指引）
            Path(tmp, "community", "甲包", "assets", "a.md").write_text("x\n" * 4, encoding="utf-8")
            issues = alb.verify(tmp)[0]
            self.assertTrue(any("行数" in i and "重签" in i for i in issues), issues)
            # 新增包未登记 → FAIL
            alb.write(tmp)
            _mk_pkg(tmp, "乙包", {"c.md": 2})
            issues = alb.verify(tmp)[0]
            self.assertTrue(any("未登记基线" in i for i in issues), issues)

    def test_absent_package_warns_not_fails(self):
        """缺包部署语义：基线在册但目录不在场 → WARN（不判死，对齐段 B）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _mk_pkg(tmp, "甲包", {"a.md": 3})
            alb.write(tmp)
            import shutil
            shutil.rmtree(Path(tmp, "community", "甲包"))
            issues, warns, _s = alb.verify(tmp)
            self.assertEqual(issues, [])
            self.assertTrue(any("不在场" in w for w in warns), warns)

    def test_real_repo_baseline_is_current(self):
        """真仓库：基线件在场且与实时扫描一致（数字不再硬编码在 verify.sh）。"""
        issues, _w, stats = alb.verify(str(ROOT))
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["baseline"], 2)
        doc = json.loads(Path(ROOT, alb.BASELINE_REL).read_text(encoding="utf-8"))
        self.assertEqual(doc["schema"], alb.SCHEMA)
        self.assertTrue(all("digest" in p and "lines" in p for p in doc["packages"]))


if __name__ == "__main__":
    unittest.main()
