#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 · plog 日志层单测（stderr 不污染 stdout 协议面）。"""
import logging
import sys
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import plog  # noqa: E402


class PLogTest(unittest.TestCase):
    def test_get_logger_and_write_stderr(self):
        log = plog.get_logger("t")
        self.assertIsInstance(log, logging.Logger)
        log.info("hi")
        log.error("boom")
        log.warning("warn")
        log.debug("dbg")
        self.assertEqual(plog.get_logger("t").name, log.name)


if __name__ == "__main__":
    unittest.main()
