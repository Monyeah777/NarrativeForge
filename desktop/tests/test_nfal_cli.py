# -*- coding: utf-8 -*-
"""nfal_cli 命令面单测（覆盖 release 的逐模块覆盖率门 min30）。

判据：五条子命令（parse/check/build/eval/schema-check）+ help 的真跑退出码与 JSON 信封；
成功/失败/用法三条路径都要走到，保证 nfal_cli 不是零覆盖件。
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import nfal_cli  # noqa: E402

P01 = "03_管线库/P01_标准管线.md"
_FENCE = chr(96) * 3


def _run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = nfal_cli.main(argv)
    return code, buf.getvalue()


def _prose_pipeline(tmp):
    p = Path(tmp, "P99.md")
    p.write_text(
        _FENCE + "yaml\nPipeline:\n  id: P99\n  name: x\n"
        "  structure:\n    type: linear\n    flow:\n"
        "      - from: P00\n        to: P10\n        condition: 主循环回卷（散文）\n"
        "  layers:\n    - id: P00\n      name: n\n      description: d\n"
        "      optional: false\n      default_modules: [M00]\n      allowed_modules: [M00]\n"
        + _FENCE + "\n", encoding="utf-8")
    return str(p)


class TestNfalCli(unittest.TestCase):
    def test_help(self):
        code, out = _run(["help"])
        self.assertEqual(code, 0)
        self.assertIn("nfal", out)

    def test_parse_ok_and_error(self):
        code, out = _run(["--root", str(ROOT), "parse", "1 + 2"])
        self.assertEqual(code, 0)
        self.assertIn('"ast"', out)
        code, out = _run(["--root", str(ROOT), "parse", "1 +"])
        self.assertEqual(code, 1)
        self.assertIn("E0201", out)

    def test_check_ok_and_fail(self):
        code, out = _run(["--root", str(ROOT), "check", "WorldState.time.day >= 30"])
        self.assertEqual(code, 0)
        self.assertIn("guard_type", out)
        code, _ = _run(["--root", str(ROOT), "check", "1 + 2"])
        self.assertEqual(code, 1)

    def test_build_real_and_strict(self):
        code, out = _run(["--root", str(ROOT), "build", P01, "--no-tokens"])
        self.assertEqual(code, 0)
        self.assertIn("nfal-ir", out)
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = _run(["--root", str(ROOT), "build", _prose_pipeline(tmp),
                            "--no-tokens", "--strict"])
            self.assertEqual(code, 1)

    def test_eval(self):
        with tempfile.TemporaryDirectory() as tmp:
            st = Path(tmp, "state.json")
            st.write_text(json.dumps({"data_bus": {"round": {"phase": "roll"}}}), encoding="utf-8")
            code, out = _run(["--root", str(ROOT), "eval", P01, "--state", str(st), "--no-tokens"])
            self.assertEqual(code, 0)
            self.assertIn("edges", out)

    def test_schema_check(self):
        code, out = _run(["--root", str(ROOT), "schema-check", P01])
        self.assertEqual(code, 0)
        self.assertIn("pass", out)


if __name__ == "__main__":
    unittest.main()
