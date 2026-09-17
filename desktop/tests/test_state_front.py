# -*- coding: utf-8 -*-
"""条件先行排布（state_front）单测：幂等 / 排布判据 / A-B 差异仅在位置。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import state_front as sf  # noqa: E402

SAMPLE = "# 世界\n\n## 1. 概述\n\n- 要点甲\n- 要点乙\n\n## 2. 细节\n\n正文 M50 / P20。\n"


class TestStateFront(unittest.TestCase):
    def test_block_is_deterministic_and_cites_digest(self):
        a = sf.build_state_block(SAMPLE)
        self.assertEqual(a, sf.build_state_block(SAMPLE))
        self.assertIn("## 状态块（条件先行摘要）", a)
        self.assertIn("非模型生成", a)
        self.assertIn("M50", a)          # 编号清单来自原文
        self.assertIn("P20", a)

    def test_reorder_is_idempotent(self):
        once = sf.reorder(SAMPLE, "front")
        twice = sf.reorder(once, "front")
        self.assertEqual(once, twice)
        self.assertNotIn("## 状态块（条件先行摘要）\n\n---\n\n## 状态块", twice)

    def test_check_order_front_pass_back_fail(self):
        self.assertEqual(sf.check_order(sf.reorder(SAMPLE, "front")), [])
        self.assertTrue(sf.check_order(sf.reorder(SAMPLE, "back")))
        self.assertTrue(sf.check_order(SAMPLE))

    def test_ab_differs_only_by_position(self):
        man = sf.ab_manifest(SAMPLE)
        self.assertTrue(man["front"]["state_front"])
        self.assertFalse(man["back"]["state_front"])
        self.assertEqual(man["front"]["chars"], man["back"]["chars"])   # 同长：同一块，只换位置
        self.assertNotEqual(man["front"]["sha256"], man["back"]["sha256"])
        self.assertLess(man["none"]["chars"], man["front"]["chars"])    # 省略组更短

    def test_real_artifact_apparatus(self):
        p = ROOT / "docs/完整版样本_西幻生存流P03.md"
        if not p.is_file():
            self.skipTest("样本不在（可选件）")
        man = sf.ab_manifest(p.read_text(encoding="utf-8"))
        self.assertEqual(set(man), {"front", "back", "none"})
        self.assertNotEqual(man["front"]["sha256"], man["back"]["sha256"])


if __name__ == "__main__":
    unittest.main()
