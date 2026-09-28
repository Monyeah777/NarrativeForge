#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 W3 · 资产键语义密度体检单测。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import asset_density as ad  # noqa: E402
from core import conformance_scan as csc  # noqa: E402


class SharedEnumerationEquivalenceTest(unittest.TestCase):
    """三个函数改走共享枚举器后，**扫描面必须与 `Path.glob` / `rglob` 逐一相同**。

    依据（实测）：一次 `evaluate` 里 community 这棵树被 scan / thickness / usage 各走一遍
    （外加 layer_model 与两个指纹）；改共享枚举后 `os.scandir` 3889 → 1957（−49%），三个函数
    自身交错 A/B 3662 → 3378 ms。**等价性是本判据的主题**——快而不同＝把门禁换成假绿。
    """

    ASSET_PATS = ("community/*/assets/*.md", "05_资产库/用户自定义/*.md")

    def test_asset_face_equals_glob(self):
        base = Path(ROOT)
        ref = sorted(p.relative_to(base).as_posix()
                     for pat in self.ASSET_PATS
                     for p in base.glob(pat)
                     if p.is_file() and p.name != "README.md")
        with csc.read_memo():
            got = sorted(r for pat in self.ASSET_PATS
                         for r in csc.iter_files(ROOT, pat)
                         if r.rsplit("/", 1)[-1] != "README.md")
        self.assertTrue(got)
        self.assertEqual(ref, got, "资产档扫描面与 Path.glob 不一致")

    def test_corpus_face_equals_rglob(self):
        """usage 的语料面 `(r/base).rglob("*.md")` ≡ `iter_files(base + "/**/*.md")`。"""
        base = Path(ROOT)
        for d in ("04_模块库", "community", "docs"):
            ref = sorted(p.relative_to(base).as_posix() for p in (base / d).rglob("*.md"))
            with csc.read_memo():
                got = csc.iter_files(ROOT, d + "/**/*.md")
            self.assertTrue(got, d)
            self.assertEqual(ref, got, "语料面与 rglob 不一致：%s" % d)


class AssetDensityTest(unittest.TestCase):
    def test_repo_scan_clean(self):
        issues, stats = ad.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["files"], 30)
        self.assertGreater(stats["keys"], 20)

    def test_empty_asset_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "community", "demo", "assets")
            d.mkdir(parents=True)
            (d / "EMPTY.md").write_text("\n", encoding="utf-8")
            issues, _ = ad.scan(tmp)
            self.assertTrue(any("空档" in i for i in issues))

    def test_thickness_repo(self):
        issues, stats = ad.thickness_scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["files"], 30)
        self.assertEqual(stats["low_files"], [])


if __name__ == "__main__":
    unittest.main()
