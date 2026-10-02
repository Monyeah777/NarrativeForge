# -*- coding: utf-8 -*-
"""响应缓存适配器**不得吞掉被包装者的输出**（`response_cache.wrap_runner`）。

动机（本轮终端面取证，真缺陷）：`wrap_runner` 为了存/回放而捕获 stdout/stderr，但回放写在
`with redirect_*` **之后**——argparse 的 `--help` 与用法错误走 `SystemExit` 穿出 `with`，
回放被整段跳过。实测表现：`nf shell --exec "nf stats --help"` 只剩「结果：run（exit=0）」，
**帮助文本一个字都没有**；参数错误只留 `exit=2` 而看不到 usage。修复后回放放进 `finally`。
"""
import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import response_cache as rc  # noqa: E402


def _wrapped(base):
    return rc.wrap_runner(base, lambda argv: (1, True))     # 代际可知 + 准入 ⇒ 走捕获分支


class WrapRunnerReplayTest(unittest.TestCase):
    def test_help_text_survives_systemexit(self):
        def base(argv):
            print("HELP-TEXT")
            raise SystemExit(0)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                _wrapped(base)(["stats", "--help"])
        self.assertIn("HELP-TEXT", buf.getvalue(), "SystemExit 路径上的 stdout 被吞掉了")

    def test_usage_error_reaches_stderr(self):
        def base(argv):
            print("USAGE-TEXT", file=sys.stderr)
            raise SystemExit(2)

        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            with self.assertRaises(SystemExit):
                _wrapped(base)(["stats", "BAD"])
        self.assertIn("USAGE-TEXT", buf.getvalue(), "SystemExit 路径上的 stderr 被吞掉了")

    def test_systemexit_paths_are_not_cached(self):
        """帮助/用法错误不得入缓存（否则后续同命令会回放一个只有退出码的空响应）。"""
        calls = {"n": 0}

        def base(argv):
            calls["n"] += 1
            raise SystemExit(0)

        wrapped = _wrapped(base)
        for _ in range(2):
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    wrapped(["stats", "--help"])
        self.assertEqual(2, calls["n"], "SystemExit 路径被误缓存（第二次没有真跑）")

    def test_normal_return_still_replays_once(self):
        def base(argv):
            print("OK-TEXT")
            return 0

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(0, _wrapped(base)(["stats", "--check"]))
        self.assertIn("OK-TEXT", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
