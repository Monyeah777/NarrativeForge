# -*- coding: utf-8 -*-
"""MCP 默认路径（`nf serve` 无参 = 实时仓库面）回归测试。

动机：MCP 面此前**必须先产快照**（`nf run --fmt mcp`）才能 `nf serve`——对 agent 密集
重复调用是两跳。默认路径开 = 无参直接起只读 resources/tools/prompts 面（数据源 = 仓库
只读扫描）。本测试端到端跑 `_cmd_serve(snapshot=None)`：喂一行 `tools/list`，断言
stdout 真返回运行时工具面；并断言「给快照仍走快照面」不回归。
"""
import argparse
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import mcp_runtime as mrt  # noqa: E402

spec = importlib.util.spec_from_file_location("nfcli_serve_default", ROOT / "scripts" / "nf.py")
assert spec is not None and spec.loader is not None
nf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nf)


class ServeDefaultPathTest(unittest.TestCase):
    def test_parser_accepts_zero_arg_serve(self):
        args = nf._make_parser().parse_args(["serve"])
        self.assertIsNone(args.snapshot, "默认路径必须允许无参 serve")

    def test_zero_arg_serve_answers_tools_list(self):
        req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) + "\n"
        old_in, old_out, old_err = sys.stdin, sys.stdout, sys.stderr
        sys.stdin, sys.stdout, sys.stderr = io.StringIO(req), io.StringIO(), io.StringIO()
        try:
            code = nf._cmd_serve(argparse.Namespace(snapshot=None))
            out = sys.stdout.getvalue()
        finally:
            sys.stdin, sys.stdout, sys.stderr = old_in, old_out, old_err
        self.assertEqual(0, code)
        msg = json.loads(out.strip().splitlines()[0])
        names = {t["name"] for t in msg["result"]["tools"]}
        self.assertIn("registry_query", names)
        self.assertEqual(sorted(names), sorted(t["name"] for t in mrt.TOOL_DEFS))

    def test_zero_arg_serve_lists_repo_resources(self):
        srv = mrt.McpRuntime({"mcp": {"name": "nf-repo-live", "version": "1.0.0",
                                      "resources": []}})
        resp = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/list"})
        uris = [r["uri"] for r in resp["result"]["resources"]]
        self.assertTrue(any(u.startswith("nf://repo/") for u in uris),
                        "实时仓库面必须带上 nf://repo/* 资源")

    def test_snapshot_argument_still_wins(self):
        args = nf._make_parser().parse_args(["serve", "mcp.json"])
        self.assertEqual("mcp.json", args.snapshot)


class SnapshotFaceTest(unittest.TestCase):
    """快照面（`nf serve <mcp.json>`）：畸形输入必须是**干净错误**（rc=2 + 修复指引）。

    实测修复前：文件不存在 / 非法 JSON / 缺 mcp / `resources` 非列表——四种都冒到 CLI 兜底
    报「内部错误」rc=1，把**用户输入问题**说成内部故障（与 `nf import` 同类，本波一并收口）。
    """

    def _run(self, path):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = nf._cmd_serve(argparse.Namespace(snapshot=str(path)))
        return code, err.getvalue()

    def _write(self, tmp, name, text):
        p = Path(tmp, name)
        p.write_text(text, encoding="utf-8", newline="\n")
        return p

    def test_missing_file_is_a_clean_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, err = self._run(Path(tmp, "nope.json"))
        self.assertEqual(2, code)
        self.assertIn("修复指引", err)
        self.assertNotIn("内部错误", err)

    def test_bad_json_is_a_clean_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, err = self._run(self._write(tmp, "bad.json", "{not json"))
        self.assertEqual(2, code)
        self.assertIn("不是合法 JSON", err)
        self.assertNotIn("内部错误", err)

    def test_wrong_shapes_are_clean_errors(self):
        cases = {
            "empty.json": "{}",
            "mcpstr.json": json.dumps({"mcp": "x"}),
            "resstr.json": json.dumps({"mcp": {"resources": "nope"}}),
            "nouri.json": json.dumps({"mcp": {"resources": [{"name": "r"}]}}),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in cases.items():
                code, err = self._run(self._write(tmp, name, text))
                self.assertEqual(2, code, name)
                self.assertIn("修复指引", err, name)
                self.assertNotIn("内部错误", err, name)

    def test_valid_snapshot_still_serves(self):
        snap = {"mcp": {"name": "probe", "version": "0",
                        "resources": [{"uri": "nf://probe/x", "name": "X", "text": "hi"}]}}
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "ok.json", json.dumps(snap))
            req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "resources/list"}) + "\n"
            old_in, old_out, old_err = sys.stdin, sys.stdout, sys.stderr
            sys.stdin, sys.stdout, sys.stderr = io.StringIO(req), io.StringIO(), io.StringIO()
            try:
                code = nf._cmd_serve(argparse.Namespace(snapshot=str(path)))
                out = sys.stdout.getvalue()
            finally:
                sys.stdin, sys.stdout, sys.stderr = old_in, old_out, old_err
        self.assertEqual(0, code)
        self.assertIn("nf://probe/x", out)


if __name__ == "__main__":
    unittest.main()
