#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NF 终端（`nf shell`）回归测试——端壳退役后的人机入口。

覆盖三层：
1. **纯函数面**：菜单/分区渲染、行解析、写盘闸门判定（不依赖 CLI）。
2. **会话状态机**：dispatch/handle 的 kind·exit·输出，含递归/长驻动词拦截与确认放行。
3. **CLI 集成**：`nf shell --exec` 的确定性、退出码、JSON 机器面，以及
   「菜单示例必须指向真实子命令」（与 verify check39 同一判据，单测先兜一层）。
"""
import argparse
import ast
import contextlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import terminal as term  # noqa: E402

_spec = importlib.util.spec_from_file_location("nfcli", ROOT / "scripts" / "nf.py")
nf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nf)


def _top_commands():
    parser = nf._build_parser()
    for act in parser._actions:
        if isinstance(act, argparse._SubParsersAction):
            return set(act.choices)
    return set()


def _run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = nf.main(list(argv))
    return code, out.getvalue()


class MenuTest(unittest.TestCase):
    def test_menu_lists_all_zones(self):
        text = term.menu()
        self.assertIn("NF 能力菜单", text)
        for item in term.zone_table():
            self.assertIn("[%s] %s" % (item["key"], item["title"]), text)

    def test_zone_keys_are_contiguous_from_zero(self):
        keys = [z["key"] for z in term.zone_table()]
        self.assertEqual(keys, [str(i) for i in range(len(keys))])

    def test_zone_detail_and_unknown_key(self):
        self.assertIn("环境自检", term.zone_detail("0"))
        self.assertIn("可用键", term.zone_detail("99"))
        self.assertIsNone(term.zone_by_key("99"))

    def test_menu_examples_point_at_real_commands(self):
        """菜单不许指向死命令（与 verify check39 同一判据）。"""
        tree = nf._collect_cli_tree()
        cmds, flags = tree["commands"], tree["root_flags"]
        for item in term.zone_table():
            self.assertTrue(item["examples"], item["id"])
            for ex in item["examples"]:
                self.assertTrue(term.example_resolves(ex, cmds, flags), ex)

    def test_banner_is_deterministic_and_mentions_safety(self):
        a = term.banner("verify v2.28 · check1-38 · PASS=66")
        b = term.banner("verify v2.28 · check1-38 · PASS=66")
        self.assertEqual(a, b)
        self.assertIn("确认", a)
        self.assertIn("check1-38", a)


class ParseTest(unittest.TestCase):
    def test_nf_prefix_is_optional(self):
        self.assertEqual(term.parse("nf doctor").payload, ["doctor"])
        self.assertEqual(term.parse("doctor").payload, ["doctor"])
        self.assertEqual(term.parse("nf.py doctor").payload, ["doctor"])

    def test_slash_commands(self):
        self.assertEqual(term.parse("/menu").kind, "menu")
        self.assertEqual(term.parse("/zone 3").payload, "3")
        self.assertEqual(term.parse("/help sig").payload, "sig")
        self.assertEqual(term.parse("/quit").kind, "quit")
        self.assertEqual(term.parse("/bogus").kind, "unknown")

    def test_bare_digit_is_zone_and_quit_words(self):
        self.assertEqual(term.parse("5").kind, "zone")
        self.assertEqual(term.parse("99").kind, "run")   # 非菜单键 → 当命令处理
        for word in ("quit", "exit", "q", "退出"):
            self.assertEqual(term.parse(word).kind, "quit", word)

    def test_quoted_demand_keeps_one_argument(self):
        intent = term.parse('nf assemble "帮我组装一个西幻生存世界的完整版"')
        self.assertEqual(intent.payload,
                         ["assemble", "帮我组装一个西幻生存世界的完整版"])

    def test_empty_line(self):
        self.assertEqual(term.parse("   ").kind, "empty")

    def test_msys_mangled_slash_command_is_restored(self):
        """Git Bash/MSYS 会把 "/zone 4" 路径转换成 "C:/…/zone 4"——须仍被识别（实测坑）。

        单 token 的 `/menu` 不受影响，但带空格的斜杠命令会被通行层改写；还原判据 =
        首 token 末段命中斜杠命令词表（SLASH_WORDS）。
        """
        cases = (("C:/comfyui/Git/zone 4", "zone", "4"),
                 ("C:/comfyui/Git/menu", "menu", ""),
                 ("C:/msys64/usr/q", "quit", ""),
                 ("C:/x/y/help sig", "help", "sig"))
        for line, kind, payload in cases:
            intent = term.parse(line)
            self.assertEqual((intent.kind, intent.payload), (kind, payload), line)

    def test_msys_shim_does_not_eat_real_paths(self):
        """真实路径（末段不是斜杠命令词）不得被误判成命令。"""
        intent = term.parse("C:/tools/nf.py doctor")
        self.assertEqual(intent.kind, "run")
        self.assertEqual(intent.payload[0], "C:/tools/nf.py")


class ConfirmGateTest(unittest.TestCase):
    def test_write_flags_need_confirm(self):
        for argv in (["stats", "--write"], ["module", "types", "--write"],
                     ["import", "--register", "payload.md"],
                     ["release", "--tag"], ["rename", "a.md", "b.md"]):
            self.assertTrue(term.needs_confirm(argv), argv)

    def test_readonly_commands_do_not_need_confirm(self):
        for argv in (["doctor"], ["market", "--list"], ["asset", "ls"],
                     ["module", "ls"], ["assemble", "西幻生存"]):
            self.assertFalse(term.needs_confirm(argv), argv)

    def test_gate_blocks_by_default_and_opens_on_confirm(self):
        seen = []

        def runner(argv):
            seen.append(list(argv))
            return 0

        session = term.Session(runner)
        kind, code, text = session.handle("nf stats --write")
        self.assertEqual((kind, code), ("run", 2))
        self.assertEqual(seen, [], "未确认的写盘命令不得执行")
        self.assertIn("确认", text)
        rec = session.dispatch("nf stats --write", confirmed=True)
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(seen, [["stats", "--write"]])

    def test_assume_yes_opens_all(self):
        seen = []
        session = term.Session(lambda argv: seen.append(list(argv)) or 0,
                               assume_yes=True)
        self.assertEqual(session.dispatch("register --apply")["exit"], 0)
        self.assertEqual(seen, [["register", "--apply"]])


class SessionTest(unittest.TestCase):
    @staticmethod
    def _fake(argv):
        """最小 runner：只认 doctor/--version/help，其余异常或 1（保持离线）。"""
        text = " ".join(argv)
        if text.startswith("doctor"):
            print("  体检：3/3 通过")
            return 0
        if argv and argv[0] == "--version":
            print("nf 1.0.0")
            return 0
        if argv and argv[0] == "help":
            return 0
        if argv and argv[0] == "run":
            sys.exit(2)                       # 模拟 argparse 用法错误
        return 1

    def test_runner_must_be_callable(self):
        with self.assertRaises(ValueError) as ctx:
            term.Session(None)
        self.assertIn("请", str(ctx.exception))

    def test_dispatch_kinds(self):
        session = term.Session(self._fake)
        self.assertEqual(session.dispatch("  ")["kind"], "empty")
        self.assertEqual(session.dispatch("0")["kind"], "zone")
        self.assertEqual(session.dispatch("/menu")["kind"], "menu")
        self.assertEqual(session.dispatch("/nope")["exit"], 2)
        rec = session.dispatch("nf doctor")
        self.assertEqual(rec["exit"], 0)
        self.assertIn("体检", rec["out"])
        session.dispatch("quit")
        self.assertTrue(session.quit)

    def test_system_exit_from_argparse_is_normalized(self):
        """argparse 的 SystemExit 不得打断会话（run 缺参数 = 退出 2）。"""
        session = term.Session(self._fake)
        rec = session.dispatch("nf run")
        self.assertEqual(rec["exit"], 2)
        self.assertFalse(session.quit)

    def test_unexpected_exception_does_not_kill_session(self):
        def boom(_argv):
            raise RuntimeError("boom")

        session = term.Session(boom)
        rec = session.dispatch("nf doctor")
        self.assertEqual(rec["exit"], 1)
        self.assertIn("内部错误", rec["err"])
        self.assertFalse(session.quit)

    def test_long_running_and_recursive_verbs_are_redirected(self):
        session = term.Session(self._fake)
        for argv in ("nf shell", "nf serve snapshot.json"):
            rec = session.dispatch(argv)
            self.assertEqual(rec["exit"], 2, argv)
            self.assertIn("另开", rec["note"])

    def test_last_zone_is_remembered(self):
        session = term.Session(self._fake)
        session.dispatch("3")
        self.assertEqual(session.last_zone, "3")

    def test_run_session_loop_with_scripted_input(self):
        stdin = io.StringIO("0\n/quit\n")
        stdout = io.StringIO()
        code = term.run_session(self._fake, stdin, stdout, show_banner=False)
        self.assertEqual(code, 0)
        out = stdout.getvalue()
        self.assertIn("nf> ", out)
        self.assertIn("环境自检", out)

    def test_run_session_prompts_before_writing(self):
        calls = []
        stdin = io.StringIO("nf stats --write\nno\n")
        stdout = io.StringIO()
        code = term.run_session(lambda argv: calls.append(list(argv)) or 0,
                                stdin, stdout, show_banner=False)
        self.assertEqual(calls, [])
        self.assertEqual(code, 2)
        self.assertIn("已取消", stdout.getvalue())

    def test_run_session_confirms_with_yes_word(self):
        calls = []
        stdin = io.StringIO("nf stats --write\nyes\n")
        stdout = io.StringIO()
        code = term.run_session(lambda argv: calls.append(list(argv)) or 0,
                                stdin, stdout, show_banner=False)
        self.assertEqual(calls, [["stats", "--write"]])
        self.assertEqual(code, 0)


class CliIntegrationTest(unittest.TestCase):
    def test_exec_menu_is_deterministic(self):
        code1, out1 = _run(["shell", "--exec", "/menu", "--no-banner"])
        code2, out2 = _run(["shell", "--exec", "/menu", "--no-banner"])
        self.assertEqual((code1, code2), (0, 0))
        self.assertEqual(out1, out2)
        self.assertIn("能力菜单", out1)

    def test_exec_runs_real_command(self):
        code, out = _run(["shell", "--exec", "nf doctor", "--no-banner"])
        self.assertEqual(code, 0)
        self.assertIn("体检", out)

    def test_exec_json_machine_face(self):
        code, out = _run(["shell", "--exec", "/zone 5", "--no-banner", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["kind"], "nf-shell")
        self.assertEqual(payload["records"][0]["kind"], "zone")
        self.assertEqual(payload["records"][0]["exit"], 0)

    def test_exec_blocks_write_without_yes(self):
        code, out = _run(["shell", "--exec", "nf stats --write", "--no-banner"])
        self.assertEqual(code, 2)
        self.assertIn("确认", out)

    def test_exec_refuses_nested_shell(self):
        code, out = _run(["shell", "--exec", "nf shell", "--no-banner"])
        self.assertEqual(code, 2)
        self.assertIn("另开", out)

    def test_terminal_alias_works(self):
        code, out = _run(["terminal", "--exec", "nf --version", "--no-banner"])
        self.assertEqual(code, 0)
        self.assertIn("nf 1.0.0", out)

    def test_help_and_description_present(self):
        tree = nf._collect_cli_tree()
        self.assertIn("shell", tree["commands"])
        self.assertIn("--exec", tree["tree"]["shell"]["flags"])
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                nf._build_parser().parse_args(["shell", "--help"])
        self.assertEqual(ctx.exception.code, 0)


class ZeroDependencyTest(unittest.TestCase):
    def test_terminal_module_is_stdlib_only(self):
        src = (ROOT / "desktop" / "src" / "core" / "terminal.py").read_text(
            encoding="utf-8")
        # 文档里可以提到「不 import PySide6」这类说明；判据只看真实 import 语句
        for banned in ("import PySide6", "from PySide6", "import curses",
                       "import PyQt", "from PyQt", "import textual", "import rich"):
            self.assertNotIn(banned, src, "终端不得 %s（零第三方依赖红线）" % banned)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(alias.name.split(".")[0], sys.stdlib_module_names,
                                  alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                self.assertIn(node.module.split(".")[0], sys.stdlib_module_names,
                              node.module)


if __name__ == "__main__":
    unittest.main()
