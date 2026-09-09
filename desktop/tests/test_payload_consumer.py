#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 #5 · payload-consumer 雏形单测（确定性 + 消费映射）。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import payload_consumer as pc  # noqa: E402


class PayloadConsumerTest(unittest.TestCase):
    def test_scan_deterministic(self):
        i1, s1 = pc.scan(ROOT)
        i2, s2 = pc.scan(ROOT)
        self.assertEqual(i1, [])
        self.assertEqual(s1, s2)
        self.assertGreaterEqual(s1["events_declared"], 25)
        self.assertGreaterEqual(s1["events_consumed"], 1)


if __name__ == "__main__":
    unittest.main()
