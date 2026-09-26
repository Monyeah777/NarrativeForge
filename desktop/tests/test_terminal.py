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
import os
import sys
import tempfile
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


class CommandFaceTest(unittest.TestCase):
    """命令面检索/列出/纠错（「最全功能」的可发现性面）。"""

    @staticmethod
    def _index():
        return nf._shell_command_index()

    def test_index_covers_every_top_level_command(self):
        """索引必须覆盖 CLI 的**全部**顶层命令——否则「最全」就有盲区。"""
        cmds = _top_commands()
        paths = {e["path"] for e in self._index()}
        missing = sorted(cmds - {p.split(" ")[0] for p in paths})
        self.assertEqual(missing, [], "未被终端索引覆盖的命令：%s" % missing)

    def test_index_includes_nested_subcommands(self):
        paths = {e["path"] for e in self._index()}
        self.assertIn("asset ls", paths)
        self.assertIn("module verify", paths)

    def test_search_prefers_exact_name(self):
        index = self._index()
        hits = term.search(index, "doctor")
        self.assertTrue(hits)
        self.assertEqual(hits[0][1]["path"], "doctor")

    def test_search_by_summary_keyword(self):
        hits = term.search(self._index(), "一致性")
        self.assertTrue(hits)
        self.assertIn("conformance", [e["path"] for _s, e in hits])

    def test_search_no_hit_gives_next_step(self):
        text, n = term.render_search(self._index(), "zzzz-不存在-zzzz")
        self.assertEqual(n, 0)
        self.assertIn("/commands", text)

    def test_search_is_deterministic(self):
        index = self._index()
        self.assertEqual(term.search(index, "asset"), term.search(index, "asset"))

    def test_did_you_mean(self):
        self.assertIn("stats", term.did_you_mean("statss", ["stats", "run", "layers"]))
        self.assertEqual(term.did_you_mean("", ["run"]), [])
        self.assertEqual(term.did_you_mean("run", ["run"]), [])

    def test_render_commands_filters(self):
        text = term.render_commands(self._index(), "asset")
        self.assertIn("nf asset ls", text)
        self.assertNotIn("nf doctor ", text)

    def test_families_partition_all_commands(self):
        """能力地图必须**恰好分区**命令集：不缺（未策展）、不重（多族）、不虚（无此命令）。"""
        cmds = _top_commands()
        seen = {}
        for fam in term.family_table():
            self.assertTrue(fam["name"] and fam["summary"] and fam["commands"], fam["id"])
            for cmd in fam["commands"]:
                self.assertNotIn(cmd, seen, "%s 同时归入 %s 与 %s" % (cmd, seen.get(cmd), fam["id"]))
                self.assertIn(cmd, cmds, "族 %s 含不存在的命令 %s" % (fam["id"], cmd))
                seen[cmd] = fam["id"]
        self.assertEqual(sorted(cmds - set(seen)), [], "未被策展的命令")

    def test_family_of_lookup(self):
        self.assertEqual(term.family_of("doctor")["id"], "start")
        self.assertEqual(term.family_of("layers")["id"], "start")
        self.assertIsNone(term.family_of("no-such-command"))

    def test_render_map_lists_and_filters(self):
        text = term.render_map()
        for fam in term.family_table():
            self.assertIn(fam["name"], text)
            for cmd in fam["commands"]:
                self.assertIn("nf %s" % cmd, text)
        only = term.render_map("治理")
        self.assertIn("治理与决策", only)
        self.assertNotIn("上手与自检", only)

    def test_self_check_clean_on_real_repo(self):
        tree = nf._collect_cli_tree()
        issues, stats = term.self_check(self._index(), tree["commands"], tree["root_flags"])
        self.assertEqual(issues, [])
        self.assertEqual(stats["families"], len(term.family_table()))
        self.assertGreaterEqual(stats["index_entries"], 2 * stats["commands"])

    def test_self_check_catches_uncurated_command(self):
        tree = nf._collect_cli_tree()
        issues, _ = term.self_check(self._index(), set(tree["commands"]) | {"zzz-fake"},
                                    tree["root_flags"])
        self.assertTrue(any("未被能力地图策展" in i for i in issues), issues)

    def test_self_check_catches_unknown_family_command(self):
        original = term.FAMILIES
        bad = tuple([dict(original[0], commands=tuple(original[0]["commands"]) + ("zzz-fake",))]
                    + list(original[1:]))
        term.FAMILIES = bad
        try:
            tree = nf._collect_cli_tree()
            issues, _ = term.self_check(self._index(), tree["commands"], tree["root_flags"])
            self.assertTrue(any("含不存在的命令" in i for i in issues), issues)
        finally:
            term.FAMILIES = original

    def test_parse_map_words(self):
        self.assertEqual(term.parse("/map").kind, "map")
        self.assertEqual(term.parse("/map 治理").payload, "治理")
        self.assertEqual(term.parse("/族 govern").kind, "map")


class ShellScriptTest(unittest.TestCase):
    """脚本文件面：与交互态共用同一条执行链（同一 Session/索引/闸门）。"""

    def test_run_lines_skips_comments_and_blanks(self):
        seen = []
        code, text, records = term.run_lines(
            ["# 注释", "", "  ", "nf doctor ; # 行尾注释", "nf layers --verify"],
            lambda argv: seen.append(list(argv)) or 0,
            index=[{"path": "doctor", "summary": "", "flags": []},
                   {"path": "layers", "summary": "", "flags": []}])
        self.assertEqual(code, 0)
        self.assertEqual(seen, [["doctor"], ["layers", "--verify"]])
        self.assertEqual([r["kind"] for r in records], ["run", "run"])
        self.assertIn("[nf shell] >", text)

    def test_run_file_executes_and_reports(self):
        fd, path = tempfile.mkstemp(suffix=".nf")
        os.close(fd)
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("# NF 脚本\n\nnf doctor   # 体检\n")
            code, text, records = term.run_file(
                path, lambda argv: 0 if argv[0] == "doctor" else 1,
                index=[{"path": "doctor", "summary": "", "flags": []}])
            self.assertEqual(code, 0)
            self.assertEqual(records[0]["argv"], ["doctor"])
            self.assertIn("doctor", text)
        finally:
            os.remove(path)

    def test_inline_comment_stripped_but_quoted_hash_kept(self):
        self.assertEqual(term.parse("nf doctor   # 说明").payload, ["doctor"])
        intent = term.parse('nf assemble "含 # 号的需求"')
        self.assertEqual(intent.payload, ["assemble", "含 # 号的需求"])


class ResilienceTest(unittest.TestCase):
    """健壮性：Ctrl-C 不杀会话、行尾反斜杠续行（对标顶尖 CLI 终端）。"""

    class _KbStdin:
        """第一次 readline 抛 KeyboardInterrupt，之后按脚本给行。"""

        def __init__(self, lines):
            self.lines = list(lines)
            self.calls = 0

        def readline(self):
            self.calls += 1
            if self.calls == 1:
                raise KeyboardInterrupt
            return self.lines.pop(0) if self.lines else ""

    def test_ctrl_c_cancels_line_not_session(self):
        stdin = self._KbStdin(["quit\n"])
        stdout = io.StringIO()
        code = term.run_session(lambda argv: 0, stdin, stdout, show_banner=False)
        self.assertEqual(code, 0)
        self.assertIn("已取消当前输入", stdout.getvalue())

    def test_backslash_continuation_joins_lines(self):
        seen = []
        stdin = io.StringIO("nf layers \\\n--verify\nquit\n")
        stdout = io.StringIO()
        code = term.run_session(lambda argv: seen.append(list(argv)) or 0,
                                stdin, stdout, show_banner=False,
                                index=[{"path": "layers", "summary": "", "flags": []}])
        self.assertEqual(code, 0)
        self.assertEqual(seen, [["layers", "--verify"]])
        self.assertIn("... ", stdout.getvalue())


class CliIntegrationTest(unittest.TestCase):
    def test_cli_map_and_verify_faces(self):
        code, out = _run(["shell", "--map", "--no-banner"])
        self.assertEqual(code, 0)
        self.assertIn("能力地图", out)
        self.assertIn("治理与决策", out)
        code, out = _run(["shell", "--map", "治理", "--no-banner"])
        self.assertEqual(code, 0)
        self.assertNotIn("上手与自检", out)
        code, out = _run(["shell", "--verify", "--no-banner"])
        self.assertEqual(code, 0, out)
        self.assertIn("通过", out)
        self.assertIn("能力族", out)

    def test_session_map_command(self):
        code, out = _run(["shell", "--exec", "/map start", "--no-banner"])
        self.assertEqual(code, 0)
        self.assertIn("[start]", out)

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
