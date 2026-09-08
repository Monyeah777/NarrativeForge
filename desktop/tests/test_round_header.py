#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""42 M2 —— 回合状态头 + 判级器 + 中断重入单测。"""
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import round_header as rh  # noqa: E402


class RoundHeaderTest(unittest.TestCase):
    def test_make_header_deterministic_and_complete(self):
        h1 = rh.make_header("P03", "5", ["P10 装载"], rh.law_ids())
        h2 = rh.make_header("P03", "5", ["P10 装载"], rh.law_ids())
        self.assertEqual(h1, h2)                 # 幂等
        self.assertIn("回合状态头 v1", h1)
        self.assertIn("管线：P03", h1)
        self.assertIn("本回合：5", h1)
        self.assertIn("06 §11", h1)              # 判级器引用
        self.assertIn("L1", h1)

    def test_laws_levels_cover_three_tiers(self):
        self.assertTrue(rh.law_ids("必须"))
        self.assertTrue(rh.law_ids("禁止"))
        self.assertTrue(rh.law_ids("应"))

    def test_interrupt_replay_identity(self):
        steps = ["P10 装载", "P20 状态装载", "P30 事件生产", "P50 交互执行", "P80 输出"]
        r = rh.replay_identity(
            "community/西幻生存领域包/pipelines/P03_西幻生存流管线.md",
            steps, interrupt_at=2, laws=rh.law_ids())
        self.assertTrue(r["idempotent"])          # 同输入重跑产出一致
        self.assertTrue(r["rejoin_matches"])       # 中断重入 = 连续执行同一切片


if __name__ == "__main__":
    unittest.main()
