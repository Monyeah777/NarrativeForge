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


class KeyCountEquivalenceTest(unittest.TestCase):
    """`count_keys`（Aho–Corasick + 非重叠贪心）必须与逐键 `str.count` **逐字节同语义**。

    依据（实测）：`{k: blob.count(k) for k in keys}` 在真语料上是「1499 键 × 3.5 MB」= 5.2 GB 扫描
    = **2.9 s**，且**每个新内容状态都要重付**；换成自动机后同一批数字只要 **0.32 s**（同机实测）。
    这里的判据不看时间，只看**数字**：随机串（可复现种子）+ 重叠/嵌套/空键边界 + 真语料子集。
    """

    def test_matches_str_count_on_random_strings(self):
        import random
        rng = random.Random(20260929)                  # 固定种子：失败可复现
        for _ in range(400):
            blob = "".join(rng.choice("abc")
                           for _ in range(rng.randint(0, 60)))
            keys = ["".join(rng.choice("abc") for _ in range(rng.randint(1, 4)))
                    for _ in range(rng.randint(1, 6))]
            self.assertEqual({k: blob.count(k) for k in keys},
                             ad.count_keys(blob, keys), (blob, keys))

    def test_overlapping_nested_and_empty_keys(self):
        cases = (("aaa", ["aa"]),                       # 非重叠：`str.count` 给 1，不是 2
                 ("aaaa", ["aa", "aaa", "a"]),          # 互相包含
                 ("ABC", ["AB", "BC", "ABC"]),          # 同位置重叠
                 ("", ["a"]), ("a", ["a"]),
                 ("abc", [""]),                         # 空键：走参考实现（len+1）
                 ("banana", ["an", "ana", "na"]))
        for blob, keys in cases:
            self.assertEqual({k: blob.count(k) for k in keys},
                             ad.count_keys(blob, keys), (blob, keys))

    def test_matches_on_a_real_corpus_subset(self):
        """逐件相加（`count_keys_additive`）也必须与整条计数一致——这是它敢缓存的前提。"""
        """真语料子集（键取前 200 个、语料取前 300 件）：口径一致才算保住。"""
        keys = {}
        for pat in ("community/*/assets/*.md", "05_资产库/用户自定义/*.md"):
            for rel in csc.iter_files(ROOT, pat):
                if rel.rsplit("/", 1)[-1] == "README.md":
                    continue
                for k in ad._keys_of(Path(rel)):
                    keys.setdefault(k, rel)
        picked = sorted(keys)[:200]
        corpus = []
        for base in ("04_模块库", "community", "docs"):
            for rel in csc.iter_files(ROOT, base + "/**/*.md"):
                try:
                    corpus.append(csc.read_text_cached(Path(ROOT) / rel))
                except OSError:
                    continue
                if len(corpus) >= 300:
                    break
            if len(corpus) >= 300:
                break
        blob = "\n".join(corpus)
        self.assertGreater(len(picked), 50, "真语料子集至少要有几十个键才有意义")
        self.assertEqual({k: blob.count(k) for k in picked},
                         ad.count_keys(blob, picked))


    def test_additive_per_file_matches_whole_blob(self):
        """`count_keys_additive`（逐件计数再相加）必须与「用 `"\\n"` 拼成一整条再数」**逐键相同**。

        这是它敢按**文件内容**缓存的前提：等价成立 ⇒ 一次真编辑只让被改的那一件重算。
        依据：键（资产 id）不可能含换行 ⇒ 跨件匹配不存在（真语料子集上断言，含随机切分）。
        """
        keys = ["a", "ab", "ba", "abc", "c", "zz", "aa"]
        texts = ["ab", "c", "abc", "aa", "b", "", "a\nb"]
        self.assertEqual(ad.count_keys("\n".join(texts), keys),
                         ad.count_keys_additive(texts, keys))
        picked = {}
        for pat in ("community/*/assets/*.md", "05_资产库/用户自定义/*.md"):
            for rel in csc.iter_files(ROOT, pat):
                if rel.rsplit("/", 1)[-1] == "README.md":
                    continue
                for k in ad._keys_of(Path(rel)):
                    picked.setdefault(k, rel)
        subset = sorted(picked)[:150]
        corpus = []
        for base in ("community", "04_模块库"):
            for rel in csc.iter_files(ROOT, base + "/**/*.md"):
                try:
                    corpus.append(csc.read_text_cached(Path(ROOT) / rel))
                except OSError:
                    continue
                if len(corpus) >= 250:
                    break
            if len(corpus) >= 250:
                break
        self.assertEqual(ad.count_keys("\n".join(corpus), subset),
                         ad.count_keys_additive(corpus, subset), "真语料子集上不等价")

    def test_newline_key_falls_back_to_whole_blob(self):
        """fail-closed：键里出现换行（当前不可能）⇒ 逐件相加不再等价 ⇒ 退回整条计数。"""
        texts = ["ab", "cd"]
        self.assertEqual(ad.count_keys("\n".join(texts), ["b\nc"]),
                         ad.count_keys_additive(texts, ["b\nc"]),
                         "含换行的键必须退回整条拼接口径")


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

    def test_corpus_patterns_constant_covers_the_same_face(self):
        """`CORPUS_PATTERNS`（内容键用的语料面）必须**逐件**等于那三条 rglob 面——键面不许缩水。"""
        base = Path(ROOT)
        ref = sorted(p.relative_to(base).as_posix()
                     for d in ("04_模块库", "community", "docs")
                     for p in (base / d).rglob("*.md"))
        with csc.read_memo():
            got = sorted(r for pat in ad.CORPUS_PATTERNS for r in csc.iter_files(ROOT, pat))
        self.assertTrue(got)
        self.assertEqual(ref, got, "CORPUS_PATTERNS 与语料面不一致（内容键会漏件）")


class KeysOfCacheTest(unittest.TestCase):
    """`_keys_of` 的逐件内容键缓存：与**未缓存参考实现**逐件等价（真仓库资产件 + 合成件）。

    依据（实测 2026-09-29）：`usage_scan` 要为 360 份资产件各跑四个正则取键（6.6 ms），而键集只是
    「该件正文 + 文件名」的纯函数——改与资产无关的件时这一整笔应当为零。
    """

    @staticmethod
    def _reference(path: Path, text: str):
        import re
        keys = set(re.findall(r"[A-Z][A-Z0-9_]*", path.stem))
        head = text[:6000]
        keys.update(re.findall(r"`([A-Z][A-Z0-9_-]{2,})`", head))
        keys.update(re.findall(r"\"([A-Z][A-Z0-9_-]{2,})\"\s*:", head))
        keys.update(re.findall(r"##\s*([A-Z][A-Z0-9_-]{2,})", head))
        return sorted(keys)

    def test_real_repo_assets_match_reference(self):
        seen = 0
        for pat in ad.ASSET_INPUTS:
            for rel in csc.iter_files(ROOT, pat):
                if rel.rsplit("/", 1)[-1] == "README.md":
                    continue
                p = Path(ROOT).joinpath(*rel.split("/"))
                text = p.read_text(encoding="utf-8")
                self.assertEqual(self._reference(p, text), ad._keys_of(p, text), rel)
                seen += 1
        self.assertGreater(seen, 50, "资产件太少，判据没测到东西")

    def test_content_keyed_and_sensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "A01_样例.md"
            p.write_text("正文 `A02-KEY` 与 \"A03\": 与 ## A04\n", encoding="utf-8")
            ad._KEYS_OF_CACHE.clear()
            first = ad._keys_of(p)
            self.assertEqual(self._reference(p, p.read_text(encoding="utf-8")), first)
            self.assertIs(first, ad._keys_of(p), "同内容第二次必须命中缓存（同一对象）")
            p.write_text("正文 只有 A01\n", encoding="utf-8")
            self.assertNotEqual(first, ad._keys_of(p), "正文一变必须重取（否则读到陈旧键集）")


class CorpusKeyCoverageTest(unittest.TestCase):
    """语料内容键换机器（逐件 `encode+sha256` → 常驻层摘要）后**覆盖面不许缩小**。

    判据是**行为**：语料面里新增一件引用 ⇒ 统计必须跟着变（不许陈旧命中）。
    """

    def test_corpus_change_moves_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            # 文件名即令牌：`A01.md` → 键 `A01`（`_keys_of` 的名称面是 `[A-Z][A-Z0-9_]*`，
            # 所以 `A01_x.md` 会得到 `A01_`——这不是本判据要测的东西）
            for rel, text in (("community/包甲/assets/A01.md", "A01 说明\n"),
                              ("04_模块库/通用类/M00_y.md", "引用 A01 一次\n")):
                path = os.path.join(tmp, *rel.split("/"))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
            ad._CENSUS_CACHE.clear()
            _, before = ad.usage_scan(tmp)
            # 语料含资产件自己（community/**/*.md）+ 那份引用它的模块件 ⇒ 2 次引用
            self.assertEqual(2, before["total_refs"], before)
            again = os.path.join(tmp, "docs")
            os.makedirs(again, exist_ok=True)
            with open(os.path.join(again, "z.md"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("再引用 A01 一次\n")
            _, after = ad.usage_scan(tmp)
            self.assertEqual(before["total_refs"] + 1, after["total_refs"],
                             "语料新增一件引用后统计没变（陈旧命中）")


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
