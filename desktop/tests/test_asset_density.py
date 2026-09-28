#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 W3 · 资产键语义密度体检单测。"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import asset_density as ad  # noqa: E402
from core import conformance_scan as csc  # noqa: E402
from core import disk_cache as dc  # noqa: E402


class CensusDiskCacheTest(unittest.TestCase):
    """引用度普查的**持久**缓存（走 `core.disk_cache`）：新进程免付那 3 s，且不可信即重算。

    依据（实测）：普查 = 1499 键 × 3.5 MB 语料的逐键子串计数 = **3.02 s**，占冷进程 `evaluate`
    的近一半；它是内容的纯函数，落盘后**新进程免付**——实测冷进程 `nf score` **7204 → 4001 ms**。
    通用面（往返 / 校验否决 / 关闭 / 裁剪 / 键的构成）由 `test_disk_cache` 覆盖，这里只钉
    「普查真的接上了」这一条端到端事实。
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="nf_census_")
        self._old_home = os.environ.get("NARRATIVE_FORGE_HOME")
        self._old_off = os.environ.pop(dc.ENV_OFF, None)
        os.environ["NARRATIVE_FORGE_HOME"] = self.home
        ad._CENSUS_CACHE.clear()

    def tearDown(self):
        ad._CENSUS_CACHE.clear()
        if self._old_home is None:
            os.environ.pop("NARRATIVE_FORGE_HOME", None)
        else:
            os.environ["NARRATIVE_FORGE_HOME"] = self._old_home
        if self._old_off is not None:
            os.environ[dc.ENV_OFF] = self._old_off
        shutil.rmtree(self.home, ignore_errors=True)

    def test_usage_scan_falls_back_to_disk_on_a_fresh_process(self):
        """端到端：冷跑写盘 → 清进程缓存（模拟新进程）→ 结果一致**且真的走盘**。"""
        issues, stats = ad.usage_scan(ROOT)
        self.assertEqual([], issues)
        ad._CENSUS_CACHE.clear()
        seen = []
        real = dc.load

        def spy(tag, ckey, validate=None):
            got = real(tag, ckey, validate=validate)
            if tag == "census":
                seen.append(got is not None)
            return got

        dc.load = spy
        ad.disk_cache.load = spy
        try:
            issues2, stats2 = ad.usage_scan(ROOT)
        finally:
            dc.load = real
            ad.disk_cache.load = real
        self.assertEqual([], issues2)
        self.assertEqual(stats, stats2, "盘上取回的结果必须与现算一致")
        self.assertTrue(seen and all(seen), "第二次必须真从盘上取回（否则新进程仍要重算 3 s）")


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
