# -*- coding: utf-8 -*-
"""`tui/nf.py`（NF 终端 TUI）的安全底线与渲染确定性判据。

为什么单列一件：TUI 是**人机入口**，它自己就是一层权限边界——路径包含性、无 shell 执行、
写盘闸门、密钥不落地四条底线一旦松掉，使用者敲一次回车就可能改仓库或把凭据交出去。
这些底线都在 `--selftest` 里可跑一遍，本件把同一批判据钉进仓库回归面（两边同一套断言，
不维护第二份口径）。
"""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import re
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


def _load_tui():
    spec = importlib.util.spec_from_file_location("nf_tui_under_test", ROOT / "tui" / "nf.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TUI = _load_tui()


class PathContainmentTest(unittest.TestCase):
    def test_outside_writes_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ("../etc/passwd", "a/../../b", "C:foo", "/etc/passwd", "", "x\x00y"):
                with self.assertRaises(TUI.RefusedError, msg=bad):
                    TUI.validate_rel_path(tmp, bad)

    def test_inside_relative_path_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            full = TUI.validate_rel_path(tmp, os.path.join("docs", "terminal.md"))
            self.assertTrue(TUI.contained(tmp, full))

    def test_free_text_path_tokens_are_guarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in (["lint", "/etc/passwd"], ["lint", "../../x/y.md"],
                        ["--pipeline=C:x.md"]):
                with self.assertRaises(TUI.RefusedError, msg=str(bad)):
                    TUI.guard_path_tokens(tmp, bad)
            # 模块号 / 枚举值不是路径，不许误杀
            TUI.guard_path_tokens(tmp, ["run", "--modules", "通用类:M00", "--fmt", "ccv3"])


class NoShellTest(unittest.TestCase):
    def test_splitter_keeps_metacharacters_literal(self):
        self.assertEqual(TUI.split_argv('doctor "a b" ; rm -rf /'),
                         ["doctor", "a b", ";", "rm", "-rf", "/"])

    def test_real_process_receives_metacharacters_verbatim(self):
        probe = [sys.executable, "-c", "import sys;print(sys.argv[1])", "a;b|c&d"]
        proc = subprocess.run(probe, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=30, shell=False)
        self.assertEqual(proc.stdout.strip(), "a;b|c&d")

    def test_unclosed_quote_is_a_usage_error(self):
        with self.assertRaises(TUI.UsageError):
            TUI.split_argv('doctor "unterminated')


class GateTest(unittest.TestCase):
    def test_classify_covers_long_running_write_and_read(self):
        self.assertEqual("long", TUI.classify(["serve"]))
        self.assertEqual("long", TUI.classify(["daemon", "start", "--watch"]))
        self.assertEqual("write", TUI.classify(["stats", "--write"]))
        self.assertEqual("write", TUI.classify(["asset", "rm", "x"]))
        self.assertEqual("read", TUI.classify(["doctor"]))

    def test_dispatch_refuses_long_running_without_repo(self):
        with self.assertRaises(TUI.RefusedError) as ctx:
            TUI.dispatch(".", None, ["serve"])
        self.assertEqual(TUI.EXIT_REFUSED, ctx.exception.code)

    def test_dispatch_refuses_unconfirmed_write(self):
        with self.assertRaises(TUI.RefusedError) as ctx:
            TUI.dispatch(".", None, ["stats", "--write"])
        self.assertEqual(TUI.EXIT_REFUSED, ctx.exception.code)

    def test_dispatch_refuses_unknown_verb(self):
        with self.assertRaises(TUI.UsageError) as ctx:
            TUI.dispatch(".", None, ["definitely-not-a-command"])
        self.assertEqual(TUI.EXIT_USAGE, ctx.exception.code)

    def test_dispatch_refuses_secret_shaped_argument(self):
        shaped = "ghp" + "_" + "A" * 24
        with self.assertRaises(TUI.RefusedError):
            TUI.dispatch(".", None, ["doctor", shaped])


class SecretHandlingTest(unittest.TestCase):
    def test_mask_never_returns_whole_value(self):
        raw = "abcdefghijklmnop"
        masked = TUI.mask_secret(raw)
        self.assertNotIn(raw, masked)
        self.assertIn("*", masked)

    def test_source_has_no_hardcoded_credentials(self):
        text = (ROOT / "tui" / "nf.py").read_text(encoding="utf-8")
        self.assertIsNone(TUI._SECRET_RE.search(text))

    def test_key_is_read_from_env_not_source(self):
        self.assertEqual("", TUI.load_api_key(env={}))
        self.assertEqual("token-value", TUI.load_api_key(env={"NF_API_KEY": "token-value"}))


class RenderTest(unittest.TestCase):
    def test_frame_is_deterministic_and_fixed_width(self):
        first = TUI.demo_frame(100, 30)
        second = TUI.demo_frame(100, 30)
        self.assertEqual(first, second)
        self.assertEqual(30, len(first))
        self.assertEqual(1, len({TUI.display_width(line) for line in first}))

    def test_cjk_counts_as_double_width(self):
        self.assertEqual(4, TUI.display_width("中文"))
        self.assertEqual(1, TUI.display_width("A"))

    def test_demo_frame_needs_no_repo(self):
        frame = TUI.demo_frame(96, 26)
        self.assertEqual(26, len(frame))
        self.assertTrue(all(line.startswith(("┌", "│", "├", "└")) for line in frame))

    def test_demo_cli_surface_is_plain_json_free(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = TUI.main(["--demo", "--width", "90", "--height", "24"])
        self.assertEqual(TUI.EXIT_OK, code)
        self.assertNotIn("\x1b", buf.getvalue())

    def test_readme_demo_block_matches_the_renderer(self):
        """README 顶部的演示帧必须是 `--demo` 的逐字输出（防文档与渲染器漂移）。"""
        expected = "\n".join(TUI.demo_frame(96, 26))
        for rel in ("README.md", "README.en.md"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            block = re.search(r"\n```\n(.*?)\n```\n", text, re.S)
            self.assertIsNotNone(block, rel)
            self.assertEqual(expected, block.group(1), rel)


def _goto_action(ui, pred):
    """把选择指到第一个满足 pred 的动作（测试内导航助手）。"""
    for zi, (_title, acts) in enumerate(TUI.ZONES):
        for ai, act in enumerate(acts):
            if pred(act):
                ui.zpos, ui.apos, ui.focus = zi, ai, TUI.FOCUS_ACTIONS
                return act
    raise AssertionError("未找到目标动作")


class InteractionTest(unittest.TestCase):
    """交互语义（对标 lazygit / k9s 的公开键位约定）：焦点、移动、过滤、帮助、滚动、取消。"""

    def setUp(self):
        self.lay = TUI.layout_of(100, 30)
        self.ui = TUI.Ui()

    def test_arrows_move_inside_the_focused_pane(self):
        """↑↓ 只在当前面板内移动——旧版「↓ 换能力区」正是交互错乱的根源。"""
        TUI.handle_key(self.ui, "DOWN", self.lay)
        self.assertEqual(1, self.ui.zpos)
        self.assertEqual(TUI.FOCUS_ZONES, self.ui.focus)
        TUI.handle_key(self.ui, "UP", self.lay)
        TUI.handle_key(self.ui, "TAB", self.lay)
        self.assertEqual(TUI.FOCUS_ACTIONS, self.ui.focus)
        TUI.handle_key(self.ui, "DOWN", self.lay)
        self.assertEqual(1, self.ui.apos)
        self.assertEqual(TUI.FOCUS_ACTIONS, self.ui.focus)

    def test_focus_cycles_with_tab_and_arrows(self):
        for expected in (TUI.FOCUS_ACTIONS, TUI.FOCUS_OUTPUT, TUI.FOCUS_ZONES):
            TUI.handle_key(self.ui, "TAB", self.lay)
            self.assertEqual(expected, self.ui.focus)
        TUI.handle_key(self.ui, "LEFT", self.lay)
        self.assertEqual(TUI.FOCUS_OUTPUT, self.ui.focus)

    def test_slash_really_filters_the_action_pane(self):
        TUI.handle_key(self.ui, "TAB", self.lay)
        TUI.handle_key(self.ui, "/", self.lay)
        self.assertEqual("filter-actions", self.ui.prompt.kind)
        self.ui.prompt.buf = "体检"
        TUI.handle_key(self.ui, "ENTER", self.lay)
        view = TUI.actions_view(self.ui)
        self.assertTrue(view)
        for _i, act in view:
            self.assertIn("体检", act.title)

    def test_slash_filters_zones_and_esc_clears(self):
        TUI.handle_key(self.ui, "/", self.lay)
        self.assertEqual("filter-zones", self.ui.prompt.kind)
        self.ui.prompt.buf = "货架"
        TUI.handle_key(self.ui, "ENTER", self.lay)
        self.assertEqual(1, len(TUI.zones_view(self.ui)))
        TUI.handle_key(self.ui, "ESC", self.lay)
        self.assertEqual(len(TUI.ZONES), len(TUI.zones_view(self.ui)))

    def test_question_mark_opens_help_and_any_key_closes(self):
        TUI.handle_key(self.ui, "?", self.lay)
        self.assertTrue(self.ui.help)
        self.assertIn("键位帮助", "\n".join(TUI.render_frame(self.ui, 100, 30)))
        TUI.handle_key(self.ui, "x", self.lay)
        self.assertFalse(self.ui.help)

    def test_output_scrolls_and_follow_resumes_at_bottom(self):
        self.ui.out = ["line %d" % i for i in range(50)]
        self.ui.focus = TUI.FOCUS_OUTPUT
        TUI.handle_key(self.ui, "HOME", self.lay)
        self.assertEqual(0, self.ui.otop)
        self.assertFalse(self.ui.follow)
        TUI.handle_key(self.ui, "DOWN", self.lay)
        self.assertEqual(1, self.ui.otop)
        TUI.handle_key(self.ui, "END", self.lay)
        self.assertTrue(self.ui.follow)
        TUI.handle_key(self.ui, "PGUP", self.lay)
        self.assertFalse(self.ui.follow)

    def test_slash_on_output_searches_and_n_cycles_hits(self):
        self.ui.out = ["alpha", "beta", "gamma", "beta again"]
        self.ui.focus = TUI.FOCUS_OUTPUT
        TUI.handle_key(self.ui, "/", self.lay)
        self.assertEqual("search-output", self.ui.prompt.kind)
        self.ui.prompt.buf = "beta"
        TUI.handle_key(self.ui, "ENTER", self.lay)
        self.assertEqual(1, self.ui.search_hit)
        TUI.handle_key(self.ui, "n", self.lay)
        self.assertEqual(3, self.ui.search_hit)
        TUI.handle_key(self.ui, "N", self.lay)
        self.assertEqual(1, self.ui.search_hit)

    def test_prompt_editing_supports_caret_and_edits(self):
        TUI.handle_key(self.ui, "/", self.lay)
        prompt = self.ui.prompt
        for ch in "abc":
            TUI.handle_key(self.ui, ch, self.lay)
        TUI.handle_key(self.ui, "LEFT", self.lay)
        TUI.handle_key(self.ui, "LEFT", self.lay)
        TUI.handle_key(self.ui, "X", self.lay)
        self.assertEqual("aXbc", prompt.buf)
        self.assertEqual(2, prompt.cursor)
        TUI.handle_key(self.ui, "BACKSPACE", self.lay)
        self.assertEqual("abc", prompt.buf)
        TUI.handle_key(self.ui, "HOME", self.lay)
        TUI.handle_key(self.ui, "DELETE", self.lay)
        self.assertEqual("bc", prompt.buf)
        TUI.handle_key(self.ui, "CTRLU", self.lay)
        self.assertEqual("", prompt.buf)

    def test_write_action_requires_typed_yes(self):
        ui = TUI.Ui(root=Path("."))
        _goto_action(ui, lambda a: "--write" in a.argv)
        op, _p = TUI.handle_key(ui, "ENTER", self.lay)
        self.assertEqual("none", op)
        self.assertEqual("confirm-write", ui.prompt.kind)
        ui.prompt.buf = "yes"
        op, payload = TUI.handle_key(ui, "ENTER", self.lay)
        self.assertEqual("run", op)
        self.assertTrue(payload["confirmed"])
        self.assertIn("--write", payload["argv"])

    def test_write_action_rejects_non_yes_answers(self):
        ui = TUI.Ui(root=Path("."))
        _goto_action(ui, lambda a: "--write" in a.argv)
        TUI.handle_key(ui, "ENTER", self.lay)
        ui.prompt.buf = "no"
        op, _p = TUI.handle_key(ui, "ENTER", self.lay)
        self.assertEqual("none", op)
        self.assertIsNone(ui.params)

    def test_required_params_are_collected_then_run(self):
        ui = TUI.Ui(root=Path("."))
        ui.zone_filter = "需求"
        TUI.clamp_ui(ui, self.lay)
        ui.focus = TUI.FOCUS_ACTIONS
        TUI.handle_key(ui, "ENTER", self.lay)
        self.assertIsNotNone(ui.prompt)
        self.assertEqual("param", ui.prompt.kind)
        ui.prompt.buf = "西幻生存"
        op, payload = TUI.handle_key(ui, "ENTER", self.lay)
        self.assertEqual("run", op)
        self.assertEqual(["assemble", "西幻生存"], payload["argv"])

    def test_esc_cancels_a_prompt(self):
        TUI.handle_key(self.ui, "/", self.lay)
        self.assertIsNotNone(self.ui.prompt)
        TUI.handle_key(self.ui, "ESC", self.lay)
        self.assertIsNone(self.ui.prompt)
        self.assertEqual("", self.ui.zone_filter)

    def test_ctrl_c_cancels_a_running_command_instead_of_quitting(self):
        class _Running:
            argv, started = ["doctor"], 0.0
            cancel = threading.Event()

        self.ui.running = _Running()
        self.assertEqual("cancel", TUI.handle_key(self.ui, "CTRLC", self.lay)[0])
        self.assertEqual("none", TUI.handle_key(self.ui, "q", self.lay)[0])
        self.assertEqual("quit", TUI.handle_key(TUI.Ui(), "q", self.lay)[0])

    def test_no_repo_interactive_enter_explains_instead_of_crashing(self):
        ui = TUI.Ui(root=None, demo=True)
        ui.focus = TUI.FOCUS_ACTIONS
        op, _p = TUI.handle_key(ui, "ENTER", self.lay)
        self.assertEqual("none", op)
        self.assertTrue(ui.out)
        self.assertIn("未发现", "\n".join(ui.out))


class MachineSurfaceTest(unittest.TestCase):
    def test_selftest_json_is_a_typed_object(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = TUI.main(["--selftest", "--json", "--root", str(ROOT)])
        self.assertEqual(TUI.EXIT_OK, code)
        payload = json.loads(buf.getvalue())
        self.assertEqual("nf-tui-selftest", payload["kind"])
        self.assertTrue(payload["ok"])

    def test_list_actions_json_indexes_every_action(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = TUI.main(["--list-actions", "--json"])
        self.assertEqual(TUI.EXIT_OK, code)
        payload = json.loads(buf.getvalue())
        self.assertEqual("nf-tui-actions", payload["kind"])
        self.assertGreaterEqual(len(payload["actions"]), len(TUI.ZONES))

    def test_list_actions_json_exposes_the_agent_contract(self):
        """agent 面：动作目录同时给出退出码表与可用的机器面清单。"""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            TUI.main(["--list-actions", "--json"])
        payload = json.loads(buf.getvalue())
        self.assertEqual("nf-tui", payload["app"])
        self.assertEqual({"ok", "failure", "usage", "refused", "env", "interrupt"},
                         set(payload["exit_codes"]))
        self.assertTrue(any("--selftest" in s for s in payload["surfaces"]))

    def test_no_repo_still_shows_content(self):
        """「随时展现内容」：找不到仓库也不许空白——先给演示帧，再以退出码 4 报告。"""
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(TUI, "find_repo_root", return_value=None):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = TUI.main([])
        self.assertEqual(TUI.EXIT_ENV, code)
        self.assertIn("NF TUI", out.getvalue())
        self.assertGreaterEqual(len(out.getvalue().splitlines()), 20)
        self.assertIn("未发现", err.getvalue())

    def test_no_repo_json_is_a_typed_error(self):
        out = io.StringIO()
        with mock.patch.object(TUI, "find_repo_root", return_value=None):
            with contextlib.redirect_stdout(out):
                code = TUI.main(["--json"])
        self.assertEqual(TUI.EXIT_ENV, code)
        payload = json.loads(out.getvalue())
        self.assertFalse(payload["ok"])
        self.assertEqual(TUI.EXIT_ENV, payload["exit"])

    def test_missing_repo_is_an_env_error(self):
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf), mock.patch.dict(os.environ, {"NF_ROOT": ""}):
            code = TUI.main(["--plain", "--root", str(ROOT / "tui")])
        self.assertEqual(TUI.EXIT_ENV, code)


class CliDriftTest(unittest.TestCase):
    def test_whitelist_matches_the_real_argparse_face(self):
        spec = importlib.util.spec_from_file_location("nf_cli_drift", ROOT / "scripts" / "nf.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        parser = module._make_parser()
        real = set()
        for action in parser._actions:
            if isinstance(action, __import__("argparse")._SubParsersAction):
                real |= set(action.choices)
        self.assertEqual(set(), set(TUI.KNOWN_TOP) ^ real)

    def test_action_templates_only_use_real_verbs(self):
        for _no, _title, action in TUI.all_actions():
            first = action.argv[0]
            if first.startswith("-"):          # 根级旗标（如 `nf --help`）按设计放行
                continue
            self.assertIn(first, TUI.KNOWN_TOP, action.title)


if __name__ == "__main__":
    unittest.main()
