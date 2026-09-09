#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 A5 · 指令档步进审计单测。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import instruction_step_audit as isa  # noqa: E402


class InstructionStepAuditTest(unittest.TestCase):
    def test_repo_clean(self):
        issues, stats = isa.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["steps"], 1)


if __name__ == "__main__":
    unittest.main()
