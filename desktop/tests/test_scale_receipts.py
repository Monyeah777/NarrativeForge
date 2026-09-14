# -*- coding: utf-8 -*-
"""回执单根与图书馆的**规模回归**（补「只在 2 件上跑过」的缺口）。

本文件的存在本身来自一个真 bug：inclusion proof 早期返回**自顶向下**顺序，而折叠按
自底向上——馆藏只有 2 件时（单步证明）完全掩盖了它，n≥3 全部折叠不到根。
"""
import hashlib
import json
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

    def _big_library(self, tmp):
        d = Path(tmp, "library")
        d.mkdir(parents=True, exist_ok=True)
        for i in range(1, self.N + 1):
            (d / ("NF-%d.md" % i)).write_text(
                "---\nid: NF-%d\ntype: 规模件\ntitle: 第 %d 件\n"
                "description: 规模回归样本 %d\nlicense: MIT\ngenerated: 2026-09-14\n"
                "status: active\nsources:\n  - 规模回归\n---\n\n正文 %d 「雨夜」\n"
                % (i, i, i, i), encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
