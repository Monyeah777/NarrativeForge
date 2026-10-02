# -*- coding: utf-8 -*-
"""回执单根与图书馆的**规模回归**（补「只在 2 件上跑过」的缺口）。

本文件的存在本身来自一个真 bug：inclusion proof 早期返回**自顶向下**顺序，而折叠按
自底向上——馆藏只有 2 件时（单步证明）完全掩盖了它，n≥3 全部折叠不到根。
"""
import hashlib
import builtins
import collections
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import library as lib  # noqa: E402
from core import receipts as rc  # noqa: E402

VERIFIER = ROOT / "scripts" / "nf_verify.py"


class TestProofScale(unittest.TestCase):
    def test_receipts_write_is_idempotent(self):
        """回执写入口**再跑一次逐字节不变**（2026-10-01 改原子写后补）。

        依据：agent 密集重复调用会重发同一写命令；回执单根又是 check35 的比对对象——
        写侧若引入任何抖动（时间戳/顺序），第二次跑就会把入仓面打红。另：本仓实测
        11 条 `--write` 命令二次调用**全部不改工作树指纹**（只读取证）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "library")
            d.mkdir(parents=True, exist_ok=True)
            (d / "NF-1.md").write_text(
                "---\nid: NF-1\ntype: 测试件\ntitle: 幂等件\ndescription: d\n"
                "license: MIT\ngenerated: 2026-09-14\nstatus: active\n"
                "sources:\n  - Issue #1\n---\n\n正文\n", encoding="utf-8", newline="\n")
            rc.write(tmp)
            target = Path(tmp, rc.RECEIPTS_REL)
            first = target.read_bytes()
            rc.write(tmp)
            self.assertEqual(first, target.read_bytes(), "回执二次写必须逐字节不变")

    def test_proofs_fold_to_root_for_many_sizes(self):
        for n in (1, 2, 3, 4, 5, 8, 9, 16, 17, 24, 100):
            leaves = [hashlib.sha256(b"%d-%d" % (n, i)).digest() for i in range(n)]
            root = rc.merkle_root(leaves)
            for i in range(n):
                proof = rc.inclusion_proof(leaves, i)
                self.assertEqual(rc.fold_proof(leaves[i].hex(), proof), root.hex(),
                                 "n=%d i=%d 折叠不到根" % (n, i))

    def test_single_leaf_and_empty(self):
        leaf = hashlib.sha256(b"only").digest()
        self.assertEqual(rc.inclusion_proof([leaf], 0), [])
        self.assertEqual(rc.fold_proof(leaf.hex(), []), leaf.hex())
        self.assertIsNone(rc.merkle_root([]))


class TestLibraryScale(unittest.TestCase):
    """合成 300 件馆藏：投影 / 检索 / 回执 / 读者工具在规模下仍正确。"""

    N = 300

    def _write_entries(self, tmp, n=None):
        """只造条目件（不含投影/回执）——供检索的形状判据复用。"""
        d = Path(tmp, "library")
        d.mkdir(parents=True, exist_ok=True)
        for i in range(1, (n or self.N) + 1):
            (d / ("NF-%d.md" % i)).write_text(
                "---\nid: NF-%d\ntype: 规模件\ntitle: 第 %d 件\n"
                "description: 规模回归样本 %d\nlicense: MIT\ngenerated: 2026-09-14\n"
                "status: active\nsources:\n  - 规模回归\n---\n\n正文 %d 「雨夜」\n"
                % (i, i, i, i), encoding="utf-8")
        return d

    def _big_library(self, tmp):
        d = self._write_entries(tmp)
        (d / "INDEX.md").write_text(
            "# INDEX\n\n" + lib.BEGIN_INDEX + "\n" + lib.END_INDEX + "\n",
            encoding="utf-8")
        lib.write_projection(tmp)
        rc.write(tmp)
        return tmp

    def test_300_entries_projection_search_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._big_library(tmp)
            rows = lib.entries(tmp)
            self.assertEqual(len(rows), self.N)
            # 投影一致 + frontmatter 全过
            self.assertEqual(lib.verify(tmp)[0], [])
            self.assertEqual(lib.check_projection(tmp), [])
            # 检索：命中且排序稳定
            hits = lib.search("雨夜", tmp, limit=5)
            self.assertEqual(len(hits), 5)
            self.assertEqual(hits[0]["id"], "NF-1")
            # 回执：根稳定、每条折叠到根
            doc = rc.load(tmp)
            self.assertEqual(doc["count"], self.N)
            self.assertEqual(rc.verify(doc, tmp)[0], [])
            # 读者工具单条验证（规模下仍 O(log n) 路径）
            env = dict(__import__("os").environ, PYTHONIOENCODING="utf-8")
            r = subprocess.run(
                [sys.executable, str(VERIFIER), "--entry", "NF-250",
                 "--receipts", str(Path(tmp, "library", "RECEIPTS.json")),
                 "--entry-file", str(Path(tmp, "library", "NF-250.md"))],
                capture_output=True, text=True, encoding="utf-8", cwd=tmp, env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            entry = [e for e in doc["entries"] if e["id"] == "NF-250"][0]
            self.assertLess(len(entry["proof"]), 12, "300 件的审计路径应远小于条数")


class TestLibrarySearchReadShape(unittest.TestCase):
    """`library.search` 的**读取形状**判据（确定性，不是墙钟）。

    依据：本仓真出过 O(n²)——`search` 曾对**每条命中**重跑一次全量 `entries()`，300 件馆藏
    实测 93,000 次读盘 / 24.7 s。墙钟断言在 CI 上会抖，读次数不会：把「每件读常数次、
    总量随件数线性」钉成判据，同类回归立刻红。
    """

    N = 300

    def _count_opens(self, root, fn):
        counts: collections.Counter = collections.Counter()
        orig = io.open

        def spy(file, *a, **k):
            try:
                path = os.path.abspath(str(file))
                if os.path.normcase(path).startswith(os.path.normcase(root)):
                    counts[os.path.normcase(path)] += 1
            except Exception:  # noqa: BLE001 - 计数失败不影响被测逻辑
                pass
            return orig(file, *a, **k)

        io.open = spy
        builtins.open = spy
        try:
            out = fn()
        finally:
            io.open = orig
            builtins.open = orig
        return out, counts

    def test_search_reads_each_entry_constant_times(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "library")
            d.mkdir(parents=True, exist_ok=True)
            for i in range(1, self.N + 1):
                (d / ("NF-%d.md" % i)).write_text(
                    "---\nid: NF-%d\ntype: 规模件\ntitle: 第 %d 件\n"
                    "description: 规模回归样本 %d\nlicense: MIT\ngenerated: 2026-09-14\n"
                    "status: active\nsources:\n  - 规模回归\n---\n\n正文 %d 「雨夜」\n"
                    % (i, i, i, i), encoding="utf-8")
            hits, counts = self._count_opens(tmp, lambda: lib.search("雨夜", tmp, limit=5))
        self.assertEqual(len(hits), 5)
        self.assertTrue(counts, "检定未捕获到任何读取（判据失效）")
        worst = max(counts.values())
        self.assertLessEqual(worst, 2,
                             "单件在检索里被读 %d 次（应 ≈1；O(n²) 会随件数放大）" % worst)
        self.assertLessEqual(
            sum(counts.values()), 2 * self.N,
            "总读次数 %d 必须随件数**线性**（O(n²) 会到 n × 命中数）" % sum(counts.values()))

    def test_bound_catches_quadratic_shape(self):
        """变异注入：把「每条命中重跑一次全量 entries()」的形状重建出来，证明该界限**能抓住**。

        纪律：判据必须有能把它打红的违规样本，否则只是「看起来很严」。
        """
        n = 60
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "library")
            d.mkdir(parents=True, exist_ok=True)
            for i in range(1, n + 1):
                (d / ("NF-%d.md" % i)).write_text(
                    "---\nid: NF-%d\ntype: 规模件\ntitle: 第 %d 件\n---\n正文雨夜\n"
                    % (i, i), encoding="utf-8")
            ids = [e["id"] for e in lib.entries(tmp)]
            _, counts = self._count_opens(
                tmp,
                # 旧实现的形状：对**每个命中**再走一遍全量 entries()
                lambda: [next(e for e in lib.entries(tmp) if e["id"] == eid) for eid in ids])
        worst = max(counts.values())
        self.assertGreater(worst, 2, "O(n²) 形状应远超单件 2 次的界限（实测 %d）" % worst)
        self.assertGreater(sum(counts.values()), 2 * n, "O(n²) 形状的总读次数应非线性")


if __name__ == "__main__":
    unittest.main()
