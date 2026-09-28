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


class CensusDiskCacheTest(unittest.TestCase):
    """引用度普查的**磁盘**缓存：内容寻址 + 口径标签 + 不可信即重算 + 可整体关闭。

    依据（实测）：普查 = 1499 键 × 3.5 MB 语料的逐键子串计数 = **3.02 s**，占冷进程 `evaluate`
    的近一半；它是内容的纯函数，落盘后**新进程免付**——实测冷进程 `nf score` **7204 → 4001 ms**。
    落点在 `NF_HOME`（不在仓库内），故不影响仓库纯净与门禁。
    """

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="nf_census_")
        self._old_home = os.environ.get("NARRATIVE_FORGE_HOME")
        self._old_off = os.environ.pop(ad._DISK_CACHE_ENV, None)
        os.environ["NARRATIVE_FORGE_HOME"] = self.home
        ad._CENSUS_CACHE.clear()

    def tearDown(self):
        ad._CENSUS_CACHE.clear()
        if self._old_home is None:
            os.environ.pop("NARRATIVE_FORGE_HOME", None)
        else:
            os.environ["NARRATIVE_FORGE_HOME"] = self._old_home
        if self._old_off is not None:
            os.environ[ad._DISK_CACHE_ENV] = self._old_off
        shutil.rmtree(self.home, ignore_errors=True)

    def test_round_trip_and_untrusted_entries_are_rejected(self):
        ckey = "a" * 64
        counts = {"A01": 3, "B02": 0}
        ad._disk_store(ckey, counts)
        self.assertEqual(counts, ad._disk_load(ckey, sorted(counts)))
        self.assertIsNone(ad._disk_load("b" * 64, sorted(counts)), "别的键不得命中")
        self.assertIsNone(ad._disk_load(ckey, ["A01"]), "键集不符必须拒绝（半截/串味）")
        p = ad._disk_cache_dir() / ("%s-%s.json" % (ad._DISK_CACHE_TAG, ckey))
        with open(p, "w", encoding="utf-8") as fh:
            fh.write('{"A01": ')                    # 半截 JSON
        self.assertIsNone(ad._disk_load(ckey, sorted(counts)), "坏文件必须拒绝")

    def test_env_switch_disables_read_and_write(self):
        os.environ[ad._DISK_CACHE_ENV] = "1"
        try:
            ckey = "c" * 64
            ad._disk_store(ckey, {"X": 1})
            d = ad._disk_cache_dir()
            self.assertEqual([], list(d.glob("*.json")) if d.is_dir() else [],
                             "关闭时不得落任何缓存文件")
            self.assertIsNone(ad._disk_load(ckey, ["X"]))
        finally:
            os.environ.pop(ad._DISK_CACHE_ENV, None)

    def test_cache_tag_is_part_of_the_filename(self):
        """口径版本进文件名：算法一变（bump tag）就不会再吃到旧算法算出来的账。"""
        ad._disk_store("d" * 64, {"X": 1})
        names = [p.name for p in ad._disk_cache_dir().glob("*.json")]
        self.assertTrue(names)
        self.assertTrue(all(n.startswith(ad._DISK_CACHE_TAG + "-") for n in names), names)

    def test_prune_keeps_only_recent_entries(self):
        for i in range(ad._DISK_CACHE_KEEP + 4):
            ad._disk_store("%064d" % i, {"X": i})
        left = list(ad._disk_cache_dir().glob("%s-*.json" % ad._DISK_CACHE_TAG))
        self.assertLessEqual(len(left), ad._DISK_CACHE_KEEP, "缓存不得无界增长")

    def test_usage_scan_falls_back_to_disk_on_a_fresh_process(self):
        """端到端：冷跑写盘 → 清进程缓存（模拟新进程）→ 结果一致**且真的走盘**。"""
        issues, stats = ad.usage_scan(ROOT)
        self.assertEqual([], issues)
        ad._CENSUS_CACHE.clear()
        seen = []
        real = ad._disk_load

        def spy(ckey, keys):
            got = real(ckey, keys)
            seen.append(got is not None)
            return got

        ad._disk_load = spy
        try:
            issues2, stats2 = ad.usage_scan(ROOT)
        finally:
            ad._disk_load = real
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
