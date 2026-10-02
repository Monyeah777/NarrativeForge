# -*- coding: utf-8 -*-
"""守护协议体量上限（`daemon._parse_request` / `_check_argv_size`）回归测试。

动机（本轮守护面模糊测试）：请求体虽限 1 MB，但**单条 argv 无上限**——实测一条 200 KB 的
参数会被照单执行，CLI 回吐 200 KB 的 argparse 用法（放大）。本件把「参数=命令/选项/标识符」
的口径钉住，越界即拒（归「请求不可读」，exit 2）。
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import daemon as dm  # noqa: E402


class _Reader:
    """最小可用的逐行读桩（`_parse_request` 只依赖 `readline`）。"""

    def __init__(self, lines):
        self._lines = list(lines)

    def readline(self, limit: int = 1 << 20) -> bytes:      # noqa: ARG002
        raw = self._lines.pop(0) if self._lines else b""
        # 与 `daemon._LineReader.readline` 同口径：行尾换行不外传。
        return raw[:-1] if raw.endswith(b"\n") else raw


def _nfreq(argv, token="t"):
    lines = [("NFREQ %d %s\n" % (dm.PROTO, token)).encode(),
             b".\n", ("%d\n" % len(argv)).encode()]
    lines += [(a + "\n").encode("utf-8") for a in argv]
    return _Reader(lines)


class DaemonArgvLimitTest(unittest.TestCase):
    def test_normal_argv_passes(self):
        req = dm._parse_request(_nfreq(["stats", "--check"]))
        self.assertEqual(["stats", "--check"], req["argv"])

    def test_oversized_single_argument_is_refused(self):
        with self.assertRaises(ValueError) as ctx:
            dm._parse_request(_nfreq(["run", "A" * (dm.MAX_ARGV_CHARS + 1)]))
        self.assertIn("修复指引", str(ctx.exception))

    def test_oversized_total_is_refused(self):
        chunk = "B" * 4096
        argv = ["x"] + [chunk] * ((dm.MAX_ARGV_TOTAL // 4096) + 2)
        with self.assertRaises(ValueError):
            dm._check_argv_size(argv)

    def test_json_frame_is_checked_too(self):
        import json
        huge = json.dumps({"proto": dm.PROTO, "token": "t",
                           "argv": ["A" * (dm.MAX_ARGV_CHARS + 1)]}).encode()
        with self.assertRaises(ValueError):
            dm._parse_request(_Reader([huge]))

    def test_non_list_argv_is_left_to_later_validation(self):
        """`op=stats` 这类无 argv 的请求不受本判据影响（类型校验另有其处）。"""
        dm._check_argv_size(None)
        dm._check_argv_size("not-a-list")


if __name__ == "__main__":
    unittest.main()
