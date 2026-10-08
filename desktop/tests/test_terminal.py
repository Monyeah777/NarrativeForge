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
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import terminal as term  # noqa: E402

_spec = importlib.util.spec_from_file_location("nfcli", ROOT / "scripts" / "nf.py")
assert _spec is not None and _spec.loader is not None
nf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nf)


def _top_commands():
    parser = nf._build_parser()
    for act in parser._actions:
        if isinstance(act, argparse._SubParsersAction):
            return set(act.choices)
    return set()


def _nf_surface() -> tuple:
    """→ `(全部长旗标, 全部命令/子命令名)`——**从真 parser 解**（不是抄清单）。

    为什么用 parser 而不是读源码正则：`nf.py` 的 `add_subparsers()` 容器变量名会被复用，
    静态解析已实测会误判（见 CHANGELOG 2026-10-01「静态解析两次误判」）。parser 是运行时真源。
    """
    parser = nf._build_parser()
    flags, names = set(), set()

    def walk(p, depth=0):
        for act in p._actions:
            for opt in act.option_strings or ():
                flags.add(opt)
            if isinstance(act, argparse._SubParsersAction):
                for name, sub in act.choices.items():
                    names.add(name)
                    if depth < 3:
                        walk(sub, depth + 1)
    walk(parser)
    return flags, names


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
        """菜单不许指向死命令（与 verify check39 同一判据）。

        反空转断言按「可执行形态」算：区要么有 `nf …` 示例，要么有投影动作（表单区即后者——
        它的可执行形态是 `/form <id>`，由 `zone_action_dicts` 从 `FORMS` 投影而来）。
        """
        tree = nf._collect_cli_tree()
        cmds, flags = tree["commands"], tree["root_flags"]
        for item in term.zone_table():
            self.assertTrue(item["examples"] or term.zone_action_dicts(item), item["id"])
            for ex in item.get("examples") or ():
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


class FormCoverageTest(unittest.TestCase):
    """写面**必有去处**：闸门表里每一项，要么有组装式表单，要么在 `FORM_EXEMPT` 里逐条点名。

    依据（2026-10-01）：闸门表（`CONFIRM_VERBS` / `CONFIRM_FLAGS` / `CONFIRM_FLAG_PAIRS`）是写面的
    **穷举真源**，而表单当时只覆盖 8 张 —— 其余写面在终端里只能手敲全参数，且**没有任何判据**
    盯着这个比例：新写面入闸后不会有人想起给它配表。本件把「写面覆盖」变成可数事实。
    """

    def _faces(self) -> set:
        """闸门表 → 规范面名集合（`verb sub` / `--flag` / `cmd --flag`）。"""
        out = set(term.CONFIRM_FLAGS)
        for cmd, sub in term.CONFIRM_VERBS:
            out.add(("%s %s" % (cmd, sub)).strip())
        for cmd, flag in term.CONFIRM_FLAG_PAIRS:
            out.add("%s %s" % (cmd, flag))
        return out

    def _covered(self) -> set:
        """表单覆盖到的面：把每个面名按**空白切词**看成一段，在模板里找连续窗口（占位符 `{k}`
        当通配）——这样 `{force}` 也算覆盖 `--force`，而不靠文案或人工列表。"""
        forms = [[str(t) for t in (f.get("argv") or [])] for f in term.form_table()]
        covered = set()
        for face in self._faces():
            want = face.split()
            for toks in forms:
                if any(all(w == t or t.startswith("{") for w, t in zip(want, toks[i:i + len(want)]))
                       for i in range(len(toks) - len(want) + 1)):
                    covered.add(face)
                    break
        return covered

    def test_every_write_face_has_a_form_or_a_named_exemption(self):
        faces, covered, exempt = self._faces(), self._covered(), set(term.FORM_EXEMPT)
        orphan = sorted(faces - covered - exempt)
        self.assertEqual([], orphan, "写面既没有表单也没有登记理由（修复指引：加一张表，"
                                     "或写进 FORM_EXEMPT 并说明为什么不为它建表）：%s" % orphan)

    def test_exemptions_are_not_stale(self):
        faces, exempt = self._faces(), set(term.FORM_EXEMPT)
        stale = sorted(exempt - faces)
        self.assertEqual([], stale, "FORM_EXEMPT 有失效条目（闸门表里已没有这个面）：%s" % stale)
        empty = sorted(k for k, v in term.FORM_EXEMPT.items() if not str(v).strip())
        self.assertEqual([], empty, "FORM_EXEMPT 有条目没写理由：%s" % empty)

    def test_forms_target_gated_actions_and_are_not_vacuous(self):
        """每张表都必须指向**真入闸**的动作（否则表是摆设），且条数/豁免条数不得退化成空转。"""
        for form in term.form_table():
            answers = {st["key"]: "x" for st in form.get("steps") or [] if st.get("required")}
            argv = term.build_argv(form, answers)
            self.assertTrue(term.needs_confirm(argv),
                            "表单 %s 组装出的 argv 不在写盘闸门内：%s" % (form.get("id"), argv))
        self.assertGreater(len(term.form_table()), 8, "表单数量退化了")
        self.assertGreater(len(term.FORM_EXEMPT), 10, "豁免登记退化成空转")

    def test_new_forms_assemble_the_documented_argv(self):
        """抽查第二批的四张表：组装结果必须与 CLI 面逐字一致（防模板手滑）。"""
        cases = {
            "preset-save": ({"name": "演示", "pipeline": "P04"}, ["preset", "save", "演示",
                                                                  "--pipeline", "P04"]),
            "library-deprecate": ({"entry": "NF-1"}, ["library", "deprecate", "NF-1"]),
            "pipeline-new": ({"id": "P07", "name": "演示管线"},
                             ["pipeline", "new", "--id", "P07", "--name", "演示管线"]),
            "approve-subject": ({"subject": "protocol/CONFORMANCE.md"},
                                ["approve", "protocol/CONFORMANCE.md"]),
        }
        for fid, (answers, want) in cases.items():
            form = term.form_by_id(fid)
            self.assertIsNotNone(form, "表单不见了：%s" % fid)
            self.assertEqual(want, term.build_argv(form, answers), "表单 %s 组装结果漂了" % fid)

    def test_doc_form_count_matches_the_table(self):
        """文档里的表数量声明必须等于真源条数（本仓「活文档」纪律：计数不许钉死除非有判据）。

        依据（2026-10-01）：`docs/terminal.md` 写着「当前 **13 张表**」，而 `FORMS` 是唯一真源——
        这类**声明式计数**此前没人盯（同 `LiveTotalCountTest` 管 PASS=/check 计数，但不管这条）。
        """
        doc = (ROOT / "docs" / "terminal.md").read_text(encoding="utf-8")
        declared = {int(m) for m in re.findall(r"当前 \*\*(\d+) 张表\*\*", doc)}
        self.assertTrue(declared, "文档里没找到「当前 **N 张表**」的声明（改了措辞请同步判据）")
        self.assertEqual({len(term.form_table())}, declared,
                         "文档表数量与真源分叉：文档=%s / 真源=%d" % (declared, len(term.form_table())))


class GateDocSyncTest(unittest.TestCase):
    """`docs/terminal.md`「写盘闸门」一节**不得出现表里没有的项**（防文档飘）。

    为什么（2026-10-01 实测）：闸门补齐 6 项（`--write-baseline` / `--re-sign` / `--fix` /
    `approve` / `asset restore` / `knowledge transform`）后，**文档那一节仍停在旧清单**——而
    那正是使用者判断「这条命令要不要确认」的唯一出处，是「口径不统一」的典型。判据取**子集**：
    文档可以不写全（写成节选），但凡写了的必须真在表里。
    """

    SECTION = "## 写盘闸门"

    def _section(self) -> str:
        text = (ROOT / "docs" / "terminal.md").read_text(encoding="utf-8")
        start = text.index(self.SECTION)
        rest = text[start + len(self.SECTION):]
        end = rest.find("\n## ")
        return rest[:end if end != -1 else len(rest)]

    def test_doc_flags_exist_in_gate_tables(self):
        import re
        section = self._section()
        flags = set(re.findall(r"`(--[a-z][a-z-]*)`", section))
        known = set(term.CONFIRM_FLAGS) | {f for _cmd, f in term.CONFIRM_FLAG_PAIRS}
        self.assertTrue(flags, "该节没列出任何旗标（判据可能已失效）")
        # `--yes` 是**放行**旗标（本节明写「调用方显式 --yes」），不是闸门项 ⇒ 不算飘
        stale = sorted(f for f in flags if f not in known and f != "--yes")
        self.assertEqual([], stale, "文档列了闸门表里没有的旗标：%s（改文档或补表）" % stale)

    def test_doc_verb_pairs_exist_in_gate_tables(self):
        import re
        section = self._section()
        pairs = []
        for span in re.findall(r"`([a-z]+ [a-z|]+)`", section):
            cmd, subs = span.split(" ", 1)
            if cmd == "nf":
                continue        # `nf score` / `nf lint` 是**命令引用**，不是闸门动词对
            for sub in subs.split("|"):
                pairs.append((cmd, sub))
        self.assertTrue(pairs, "该节没列出任何动词对（判据可能已失效）")
        stale = [p for p in pairs if p not in term.CONFIRM_VERBS]
        self.assertEqual([], stale, "文档列了闸门表里没有的动词对：%s" % stale)


class BlockedDocSyncTest(unittest.TestCase):
    """`docs/terminal.md`「会话内不执行」一节列的命令必须真在 `BLOCKED_IN_SHELL` 里。

    为什么（2026-10-01）：这一节与写盘闸门那节同型——它是使用者判断「会话里这条能不能跑」的
    唯一人读出处。上一轮补 `lsp` / `terminal` 别名时**两边都改了**，但没有任何判据盯着；
    按 `GateDocSyncTest` 同一纪律取**子集**：文档可以只写节选，但凡写了的必须真在表里。
    """

    MARK = "会话内**不执行**"

    def _section(self) -> str:
        text = (ROOT / "docs" / "terminal.md").read_text(encoding="utf-8")
        start = text.index(self.MARK)
        rest = text[start:]
        end = rest.find("\n## ")
        return rest[:end if end != -1 else len(rest)]

    def test_doc_lists_only_blocked_commands(self):
        import re
        section = self._section()
        names = set(re.findall(r"`([a-z][a-z-]*)`", section))
        self.assertTrue(names, "该节没列出任何命令（判据可能已失效）")
        stale = sorted(n for n in names
                       if n not in term.BLOCKED_IN_SHELL and n not in ("nf", "ide"))
        self.assertEqual([], stale,
                         "文档列了 BLOCKED_IN_SHELL 里没有的命令：%s（改文档或补表）" % stale)


class ConfirmGateTest(unittest.TestCase):
    def test_write_flags_need_confirm(self):
        for argv in (["stats", "--write"], ["module", "types", "--write"],
                     ["import", "--register", "payload.md"],
                     ["asset", "baseline", "--write"], ["rename", "a.md", "b.md"]):
            self.assertTrue(term.needs_confirm(argv), argv)

    def test_readonly_commands_do_not_need_confirm(self):
        for argv in (["doctor"], ["market", "--list"], ["asset", "ls"],
                     ["module", "ls"], ["assemble", "西幻生存"]):
            self.assertFalse(term.needs_confirm(argv), argv)

    def test_unflagged_write_verbs_need_confirm(self):
        """**无标记写盘**动词也要入闸（2026-09-30 补）。

        依据：闸门此前只在 argv 里找 `--write` 一族旗标 + 一张动词表，而 `library deprecate`
        / `library reindex` / `decisions reindex` / `patterns reindex` / `pipeline new` 这些
        **不带任何旗标就直接改仓库件**（生命周期流转 / 投影重建 / 派生新件）全都不在表里——
        非交互 `nf shell --exec` 一路照跑。
        """
        for argv in (["library", "deprecate", "NF-1"], ["library", "restore", "NF-1"],
                     ["library", "supersede", "NF-1", "NF-2"], ["library", "attest", "NF-1"],
                     ["library", "reindex"], ["decisions", "reindex"],
                     ["patterns", "reindex"], ["pipeline", "new", "P99"]):
            self.assertTrue(term.needs_confirm(argv), argv)

    def test_command_scoped_flag_pairs_need_confirm(self):
        """`interop --all` 落盘要拦，但**同名的只读形态不许误拦**（`pipeline dryrun --all` 只扫）。"""
        self.assertTrue(term.needs_confirm(["interop", "--all"]))
        self.assertFalse(term.needs_confirm(["interop", "--check"]))
        self.assertFalse(term.needs_confirm(["pipeline", "dryrun", "--all"]))
        # 2026-10-01 三补：`--trace` / `--session` 只在 `nf assemble` 上是**写**（写你自己命名的
        # 文件，可仓库相对 ⇒ 粘贴面能落仓）；在其余命令上是只读输入或仓外受控 ⇒ **不许误拦**。
        self.assertTrue(term.needs_confirm(["assemble", "--check", "x.md", "--trace", "t.json"]))
        self.assertTrue(term.needs_confirm(["assemble", "需求", "--session", "s.json"]))
        self.assertFalse(term.needs_confirm(["knowledge", "frequency", "--trace", "t.json"]))
        self.assertFalse(term.needs_confirm(["shell", "--session", "C:/tmp/s.json"]))

    def test_long_running_faces_are_blocked_in_shell(self):
        """长驻/递归面在会话内**不执行**（给指引而不是占住终端）。

        2026-10-01 补：`serve` 一直被拦，而 **`lsp` 与它同型**（`LspServer.serve()` 是
        `while True: stdin.readline(...)`）却漏了——交互会话里跑它会静默占住终端。本判据把
        「长驻四件」钉住（`shell` / `terminal` 是同一命令的别名，两条拼写都要拦）。
        """
        for cmd in ("shell", "terminal", "serve", "lsp"):
            self.assertIn(cmd, term.BLOCKED_IN_SHELL, "%s 未被拦（会占住会话）" % cmd)
        # 防过度拦截：普通只读命令不许进这张表
        for cmd in ("stats", "doctor", "market", "asset", "layers", "daemon"):
            self.assertNotIn(cmd, term.BLOCKED_IN_SHELL)

    def test_every_write_capable_form_is_gated(self):
        """**写能力清点**：凡会改仓库件的形态都必须被闸门拦下（2026-10-01 补）。

        依据：按 help 把「写产物的旗标 / 无标记写盘的动词」逐条清点后，用 `needs_confirm`
        反向核对，抓到 4 处漏网——`nf score --write-baseline`、`nf asset baseline --re-sign`、
        `nf lint --fix`（三个**写盘但不叫 `--write`** 的旗标）与 **`nf approve <对象> --by <人>`**
        （会落 `protocol/approvals/*.json` 这条**治理/问责**记录，且不带任何写旗标）——此前在
        `nf shell` 里都能**不经确认**改仓库。

        2026-10-01 三补（**机械枚举全部旗标**，不再靠「已知名字」）：又抓三个不带写语义却直接
        改仓库件的旗标——`nf module types --harvest`（写 event_registry）、`nf pipeline dryrun
        --write-advisory`（写 pipeline_advisory）、`nf combine plan --certify`（写
        combo_certificates），外加与已入闸 `--out` 同类的 `nf assemble --save <文件>`。
        本判据把清点后的写形态逐条钉住，防回退。
        """
        for argv in (["stats", "--write"],
                     ["run", "--pipeline", "p", "--modules", "m", "--dest", "d"],
                     ["interop", "--all"],
                     ["domain", "build", "--spec", "X", "--write"],
                     ["combine", "materialize", "--write"],
                     ["output", "render", "--write"],
                     ["receipts", "--write"],
                     ["conformance", "--write"],
                     ["score", "--write-baseline"],
                     ["asset", "baseline", "--write"],
                     ["asset", "add", "x.md", "--key", "k", "--source", "s"],
                     ["asset", "rm", "k"],
                     ["module", "deprecate", "x.md"],
                     ["register", "pkg", "--apply"],
                     ["import", "x.md", "--register"],
                     ["rename", "A", "B", "--apply"],
                     ["pipeline", "new", "P99", "--id", "P99", "--name", "x"],
                     ["decisions", "reindex"],
                     ["patterns", "reindex"],
                     ["library", "reindex"],
                     ["library", "deprecate", "NF-1"],
                     ["library", "attest", "NF-1"],
                     ["approve", "README.md", "--by", "tester"],
                     ["asset", "restore", "k"],
                     ["knowledge", "transform", "add", "--src", "s", "--dst", "d"],
                     ["release", "--fast"],
                     ["knowledge", "frequency", "--trace", "t.json", "--write"],
                     ["lint", "--fix"],
                     ["module", "types", "--harvest"],
                     ["pipeline", "dryrun", "--all", "--write-advisory"],
                     ["combine", "plan", "--packs", "X", "--certify"],
                     ["assemble", "需求", "--save", "a.md"],
                     ["assemble", "--check", "x.md", "--trace", "t.json"],
                     ["assemble", "需求", "--session", "s.json"]):
            self.assertTrue(term.needs_confirm(argv), "写形态漏过闸门：%s" % argv)

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
            print("nf 1.0.1")
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


class TerminalSurfaceTest(unittest.TestCase):
    """单真值源 · 多视图投影（2026-10-03）：真源 → 机器面 / 生成件 / 各视图。

    这一类的判据面就是「三面同源」这句话的可执行形态：真源表变一处，投影件、机器面与
    全屏视图必须同步；谁留了第二份手抄表，这里与 verify check39 都会红。
    """

    def _tree(self):
        return nf._collect_cli_tree()

    def test_payload_projects_every_table(self):
        tree = self._tree()
        payload = term.surface_payload(tree["commands"], tree["root_flags"])
        self.assertEqual(payload["kind"], "nf-terminal-surface")
        self.assertEqual(payload["schema"], term.SURFACE_SCHEMA)
        self.assertEqual(len(payload["zones"]), len(term.zone_table()))
        self.assertEqual(len(payload["families"]), len(term.family_table()))
        self.assertEqual(len(payload["forms"]), len(term.form_table()))
        self.assertEqual(payload["commands"], sorted(tree["commands"]))
        self.assertEqual(payload["root_flags"], sorted(tree["root_flags"]))
        self.assertEqual(payload["gates"]["flags"], list(term.CONFIRM_FLAGS))
        self.assertEqual([tuple(v) for v in payload["gates"]["verbs"]], list(term.CONFIRM_VERBS))
        self.assertEqual([tuple(p) for p in payload["gates"]["pairs"]],
                         list(term.CONFIRM_FLAG_PAIRS))
        self.assertEqual(sorted(payload["blocked"]), sorted(term.BLOCKED_IN_SHELL))
        self.assertTrue(payload["digest"].startswith("sha256:"))
        for zone in payload["zones"]:
            self.assertTrue(zone["actions"], "区 %s 缺动作（全屏视图的动作面板会空）" % zone["id"])
            for action in zone["actions"]:
                self.assertTrue(action["key"] and action["title"])
                for param in action["params"]:
                    self.assertIn(param["kind"], ("text", "path"))

    def test_digest_ignores_dict_order(self):
        """摘要按规范 JSON 算，故与构造顺序无关——换序不该产生「假漂移」。"""
        payload = term.surface_payload(["doctor"], ["--help"])
        reordered = {k: payload[k] for k in reversed(list(payload))}
        self.assertEqual(term.surface_digest(payload), term.surface_digest(reordered))

    def test_module_text_is_deterministic_and_flags_drift(self):
        tree = self._tree()
        text = term.surface_module_text(tree["commands"], tree["root_flags"])
        self.assertEqual(text, term.surface_module_text(tree["commands"], tree["root_flags"]))
        self.assertEqual([], term.surface_sync_issues(text, tree["commands"], tree["root_flags"]))
        issues = term.surface_sync_issues(text + "\n# 手改一行\n",
                                          tree["commands"], tree["root_flags"])
        self.assertTrue(issues and "不同步" in issues[0], issues)
        self.assertIn("surface-write", issues[0])          # 修复指引给出重生成命令

    def test_projection_on_disk_is_in_sync_with_truth(self):
        """真源改了没重生成 ⇒ 红（这是「单真值源」在仓库里的落点判据）。"""
        tree = self._tree()
        path = ROOT / term.SURFACE_MODULE_PATH
        self.assertTrue(path.is_file(), "%s 不在场（生成：nf shell --surface-write）"
                        % term.SURFACE_MODULE_PATH)
        issues = term.surface_sync_issues(path.read_text(encoding="utf-8"),
                                          tree["commands"], tree["root_flags"])
        self.assertEqual(issues, [])

    def test_forms_zone_projects_every_form(self):
        """表单区**不留动作字面量**：它的动作必须恰好等于表单真源（改表即改视图，无需二次登记）。"""
        zones = [z for z in term.zone_table() if z.get("forms")]
        self.assertEqual(1, len(zones), "应恰好有一个「由 FORMS 投影」的区")
        acts = term.zone_action_dicts(zones[0])
        self.assertEqual([str(f["id"]) for f in term.form_table()],
                         [str(a["key"]) for a in acts])
        tree = self._tree()
        for act in acts:
            self.assertIn(act["argv"][0], tree["commands"], act["key"])
            self.assertEqual(list(term.form_by_id(act["key"])["argv"]), list(act["argv"]),
                             "投影动作的 argv 与表单真源分叉：%s" % act["key"])
        payload = term.surface_payload(tree["commands"], tree["root_flags"])
        self.assertEqual(sum(len(z["actions"]) for z in payload["zones"]),
                         sum(len(term.zone_action_dicts(z)) for z in term.zone_table()))

    def test_self_check_catches_dead_action(self):
        original = term.ZONES
        bad = dict(original[0])
        bad["actions"] = tuple(bad["actions"]) + (
            {"key": "zzz", "title": "假动作", "argv": ("zzz-fake",), "params": (), "note": ""},)
        term.ZONES = (bad,) + tuple(original[1:])
        try:
            tree = self._tree()
            issues, stats = term.self_check(nf._shell_command_index(), tree["commands"],
                                            tree["root_flags"])
            self.assertTrue(any("菜单动作指向死命令" in i for i in issues), issues)
            self.assertGreaterEqual(stats["actions"], 1)
        finally:
            term.ZONES = original

    def test_human_face_lists_every_zone(self):
        tree = self._tree()
        text = term.render_surface(term.surface_payload(tree["commands"], tree["root_flags"]))
        for zone in term.zone_table():
            self.assertIn(zone["title"], text)

    def test_cli_surface_json_is_pure_json(self):
        code, out = _run(["shell", "--surface", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["kind"], "nf-terminal-surface")
        self.assertEqual(payload["digest"],
                         term.surface_payload(nf._collect_cli_tree()["commands"],
                                              nf._collect_cli_tree()["root_flags"])["digest"])

    def test_cli_surface_write_refuses_escape(self):
        """生成件落点必须过包含性判据（写面不许把文件带出仓库）。"""
        code, _out = _run(["shell", "--surface-write", "../escape.py"])
        self.assertEqual(code, 2)


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


class FormTest(unittest.TestCase):
    """写盘表单：真源完整性、argv 组装、交互追问流程、会话持久化与守卫。"""

    def test_form_table_integrity(self):
        cmds = _top_commands()
        seen = set()
        for form in term.form_table():
            self.assertNotIn(form["id"], seen, form["id"])
            seen.add(form["id"])
            self.assertTrue(form["title"] and form["summary"], form["id"])
            keys = {st["key"] for st in form["steps"]}
            for st in form["steps"]:
                self.assertTrue(st.get("key") and st.get("prompt"), form["id"])
            self.assertIn(form["argv"][0], cmds,
                          "表单 %s 的模板动词不存在：%s" % (form["id"], form["argv"][0]))
            # 2026-10-01 补：表单模板的**子命令与旗标**也必须在真命令面上——此前只核了第一个
            # token（顶层命令）与占位符↔steps 的对应，`--reason` / `--apply` / `--scope` 这类
            # 旗标写错不会有任何检查察觉（`--form-run` 要真跑才暴露）；`nf.py` 换过旗标名时，
            # 表单就是下一个「文档/表与真实面分叉」的现场。
            all_flags, all_subs = _nf_surface()
            argv = [t for t in form["argv"] if isinstance(t, str)]
            for tok in argv:
                if tok.startswith("--"):
                    self.assertIn(tok, all_flags,
                                  "表单 %s 的旗标不在 argparse 面：%s" % (form["id"], tok))
            if len(argv) > 1 and not argv[1].startswith(("-", "{")):
                self.assertIn(argv[1], all_subs,
                              "表单 %s 的子命令不在 argparse 面：%s" % (form["id"], argv[1]))
            for tok in form["argv"]:
                if tok.startswith("{") and tok.endswith("}"):
                    self.assertIn(tok[1:-1], keys,
                                  "表单 %s 模板引用了未声明的 step：%s" % (form["id"], tok))

    def test_build_argv_drops_empty_optional_with_flag(self):
        form = term.form_by_id("deprecate-module")
        self.assertEqual(term.build_argv(form, {"file": "community/x/M1.md"}),
                         ["module", "deprecate", "community/x/M1.md"])
        self.assertEqual(
            term.build_argv(form, {"file": "a.md", "reason": "重复"}),
            ["module", "deprecate", "a.md", "--reason", "重复"])

    def test_build_argv_missing_required_guides(self):
        form = term.form_by_id("asset-add")
        with self.assertRaises(ValueError) as ctx:
            term.build_argv(form, {"file": "a.md"})
        self.assertIn("还缺必填项", str(ctx.exception))
        self.assertIn("修复指引", str(ctx.exception))

    def test_render_forms_and_form(self):
        listing = term.render_forms()
        for form in term.form_table():
            self.assertIn(form["id"], listing)
        text = term.render_form(term.form_by_id("deprecate-module"), {})
        self.assertIn("请回答 file", text)
        self.assertNotIn("\x1b", text)

    def test_session_form_flow_executes_after_confirm(self):
        calls = []
        session = term.Session(lambda argv: calls.append(list(argv)) or 0,
                               index=[{"path": "module", "summary": "", "flags": []}])
        kind, code, text = session.handle("/form deprecate-module")
        self.assertEqual((kind, code), ("form", 0))
        self.assertIn("请回答 file", text)
        kind, _code, text = session.handle("community/x/M1.md")      # 位置式回答
        self.assertEqual(kind, "form")
        self.assertIn("请回答 reason", text, "可选项也要逐项问到（空行=跳过）")
        kind, _code, text = session.handle("")                       # 空行 = 跳过可选项
        self.assertIn("组装命令：nf module deprecate community/x/M1.md", text)
        kind, code, _text = session.handle("no")                     # 先取消一次
        self.assertEqual(code, 0)
        self.assertIsNone(session.active_form)
        self.assertEqual(calls, [])
        # 再走一遍：这次补上可选项并确认
        session.dispatch("/form deprecate-module")
        session.dispatch("community/x/M1.md")
        kind, _code, text = session.handle("reason=重复")             # k=v 回答 → settle
        self.assertIn("组装命令：nf module deprecate community/x/M1.md --reason 重复", text)
        kind, code, _text = session.handle("yes")
        self.assertEqual((kind, code), ("run", 0))
        self.assertEqual(calls, [["module", "deprecate", "community/x/M1.md",
                                  "--reason", "重复"]])
        self.assertIsNone(session.active_form)

    def test_session_form_cancel_and_pending_routing(self):
        calls = []
        session = term.Session(lambda argv: calls.append(list(argv)) or 0)
        session.dispatch("/form restore-module")
        rec = session.dispatch("nf doctor")          # 表单挂起时：普通行=回答，不当命令跑
        self.assertEqual(rec["kind"], "form")
        self.assertEqual(calls, [])
        rec = session.dispatch("/cancel")
        self.assertIn("已中止", rec["note"])
        self.assertIsNone(session.active_form)
        self.assertEqual(calls, [])

    def test_session_state_roundtrip_and_bad_file(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            session = term.Session(lambda argv: 0, session_path=path, width=None)
            session.dispatch("/set width=120 limit=7 color=never")
            session.last_zone = "5"
            self.assertTrue(term.save_session_state(path, session))
            state, warn = term.load_session_state(path)
            self.assertEqual(warn, "")
            self.assertEqual(state["settings"]["width"], 120)
            self.assertEqual(state["settings"]["limit"], 7)
            self.assertEqual(state["last_zone"], "5")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("{ 坏 JSON")
            state2, warn2 = term.load_session_state(path)
            self.assertEqual(state2, {})
            self.assertIn("不是合法 JSON", warn2)
        finally:
            os.remove(path)

    def test_load_session_missing_file_is_silent(self):
        state, warn = term.load_session_state(str(ROOT / "no-such-session.json"))
        self.assertEqual((state, warn), ({}, ""))


class OutputExperienceTest(unittest.TestCase):
    """输出体验：CJK 列宽对齐 / 限长提示 / 着色克制（非 TTY 恒无色）。"""

    @staticmethod
    def _index():
        return nf._shell_command_index()

    def test_display_width_and_pad(self):
        self.assertEqual(term.display_width("abc"), 3)
        self.assertEqual(term.display_width("中文"), 4)
        self.assertEqual(term.display_width("a中b"), 4)
        self.assertEqual(term.pad_to("中", 4), "中  ")
        self.assertEqual(term.display_width(term.pad_to("中文", 6)), 6)

    def test_clip_respects_display_width(self):
        self.assertEqual(term.clip("abc", 5), "abc")
        self.assertEqual(term.clip("中文中文", 5), "中文…")
        self.assertEqual(term.display_width(term.clip("中" * 20, 9)), 9)

    def test_resolve_color_modes(self):
        class _Tty:
            @staticmethod
            def isatty():
                return True

        class _Pipe:
            @staticmethod
            def isatty():
                return False

        old = os.environ.get("NO_COLOR")
        os.environ.pop("NO_COLOR", None)      # 环境可能自带 NO_COLOR（本机实测 =1），须显式控制
        try:
            self.assertFalse(term.resolve_color("never", _Tty()))
            self.assertTrue(term.resolve_color("always", _Pipe()))
            self.assertTrue(term.resolve_color("auto", _Tty()))
            self.assertFalse(term.resolve_color("auto", _Pipe()))
            os.environ["NO_COLOR"] = "1"
            self.assertFalse(term.resolve_color("auto", _Tty()),
                             "NO_COLOR 一票否决 auto")
            self.assertTrue(term.resolve_color("always", _Tty()),
                            "always 是显式要求，NO_COLOR 不否决它")
        finally:
            if old is None:
                os.environ.pop("NO_COLOR", None)
            else:
                os.environ["NO_COLOR"] = old

    def test_render_commands_limit_hint_and_color(self):
        plain = term.render_commands(self._index(), "asset", limit=3)
        self.assertEqual(len([ln for ln in plain.splitlines()
                              if ln.lstrip().startswith("nf asset")]), 3)
        self.assertIn("还有", plain)
        self.assertNotIn("\x1b", plain, "默认（非 TTY 口径）不得带控制字符")
        colored = term.render_commands(self._index(), "asset", limit=3, color=True)
        self.assertIn("\x1b[", colored)

    def test_session_set_changes_settings(self):
        session = term.Session(lambda argv: 0, index=self._index())
        kind, code, text = session.handle("/set width=120 limit=2 color=never")
        self.assertEqual((kind, code), ("set", 0))
        self.assertIn("width = 120", text)
        self.assertIn("limit = 2", text)
        _k, code2, text2 = session.handle("/commands asset")
        self.assertEqual(code2, 0)
        self.assertIn("还有", text2)
        self.assertNotIn("\x1b", text2)
        _k, code3, text3 = session.handle("/set color=bogus")
        self.assertEqual(code3, 2)
        self.assertIn("无法识别", text3)

    def test_menu_and_map_default_plain(self):
        self.assertNotIn("\x1b", term.menu())
        self.assertNotIn("\x1b", term.render_map())
        self.assertIn("\x1b[", term.menu(color=True))


class TerminalBaselineDocCountTest(unittest.TestCase):
    """`docs/terminal.md` 的「当前 **N 行**覆盖」必须等于 `TERMINAL_BASELINE` 真实行数。

    依据（2026-10-01）：这个数字此前是**手工**跟着基线走的——本轮恢复外部事故时它就停在 17
    （真实 20），而没有任何判据盯着；同一行还并列着**按主题归并**的摘要清单（4 条写盘闸门行合成
    一项），于是「20 行」配上「17 项」看起来自相矛盾。现在：数字由判据钉住，摘要与真实行的关系
    在文档里写明（「下表按主题归并……逐行清单见 `terminal.py`」）。
    """

    def test_doc_baseline_count_matches_the_table(self):
        doc = (ROOT / "docs" / "terminal.md").read_text(encoding="utf-8")
        declared = {int(m) for m in re.findall(r"当前 \*\*(\d+) 行\*\*覆盖", doc)}
        self.assertTrue(declared, "文档里没找到「当前 **N 行**覆盖」的声明（改了措辞请同步判据）")
        self.assertGreaterEqual(len(term.TERMINAL_BASELINE), 15, "基线行数异常（判据可能已失效）")
        self.assertEqual({len(term.TERMINAL_BASELINE)}, declared,
                         "文档声明的基线行数与真源分叉：文档=%s / 真源=%d"
                         % (declared, len(term.TERMINAL_BASELINE)))


class TerminalHostileInputTest(unittest.TestCase):
    """终端**机器面**喂敌意输入：不得冒「内部错误 / Python 栈」。

    依据（2026-10-01 探针，6 例全过）：`--exec` 500 条命令、`--exec` 8 KB 单行、`--form` 4096
    字符回答、未知 `--form` id、4096 字符检索词、超长 `--history` 路径——逐条真跑，**零内部错误、
    零栈、零挂起**。本件把这一点钉住（退出码按各面语义分别断言：执行成功 0 / 用法与未命中 2 /
    坏路径 1）。NF_HOME 隔离到临时目录，避免长名预设落进真实预设库。
    """

    def _run(self, *argv):
        home = tempfile.mkdtemp(prefix="nf_term_hostile_")
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        env = dict(os.environ, NARRATIVE_FORGE_HOME=home, NF_AUTOSTART="0")
        return subprocess.run([sys.executable, str(Path(ROOT) / "scripts" / "nf.py"), *argv],
                              cwd=ROOT, env=env, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=300,
                              stdin=subprocess.DEVNULL)

    def test_hostile_inputs_do_not_crash_the_terminal_faces(self):
        big_script = "; ".join("nf stats --check" for _ in range(500))
        cases = (
            ("--exec 500 条", ["shell", "--exec", big_script, "--no-banner"], 0),
            ("--exec 8KB 单行", ["shell", "--exec", "nf doctor" + " " * 8000, "--no-banner"], 0),
            ("--form 超长回答", ["shell", "--form", "preset-save", "--answer",
                                 "name=" + "X" * 4096, "--json"], 0),
            ("--form 未知 id", ["shell", "--form", "no-such-form", "--json"], 2),
            ("--search 超长词", ["shell", "--search", "A" * 4096, "--json"], 2),
            ("--history 超长路径", ["shell", "--history", "C:" + "x" * 4000], 1),
        )
        for label, argv, want in cases:
            p = self._run(*argv)
            blob = (p.stdout or "") + (p.stderr or "")
            self.assertEqual(want, p.returncode, "%s：rc 变了（%s）" % (label, p.stderr[:150]))
            self.assertNotIn("内部错误", blob, "%s：不得冒内部错误" % label)
            self.assertNotIn("Traceback", blob, "%s：不得冒栈" % label)


class CompletionHistoryTest(unittest.TestCase):
    """补全与历史（顶尖 CLI 的体感面）：补全是纯判据，历史只在交互态写。"""

    @staticmethod
    def _index():
        return nf._shell_command_index()

    def test_complete_command_prefix(self):
        cands = term.complete("nf lay", self._index())
        self.assertEqual([c["text"] for c in cands], ["nf layers"])

    def test_complete_flags_for_command(self):
        texts = [c["text"] for c in term.complete("nf layers --", self._index())]
        self.assertIn("nf layers --write", texts)
        self.assertIn("nf layers --verify", texts)

    def test_complete_slash_families_and_zones(self):
        self.assertIn("/map", [c["text"] for c in term.complete("/ma", [])])
        self.assertEqual([c["text"] for c in term.complete("/map start", [])],
                         ["/map start"])
        self.assertEqual([c["text"] for c in term.complete("/zone 3", [])], ["/zone 3"])

    def test_complete_no_candidates(self):
        self.assertEqual(term.complete("nf zzzz", self._index()), [])
        self.assertIn("无补全候选", term.render_completions("nf zzzz", []))

    def test_complete_restores_msys_mangled_slash_prefix(self):
        """Git Bash 把 `/ma` 改写成 `C:/…/ma`；补全须仍给候选（前缀容错，与 parse 同判据）。"""
        texts = [c["text"] for c in term.complete("C:/comfyui/Git/ma", [])]
        self.assertIn("/map", texts)
        texts = [c["text"] for c in term.complete("C:/comfyui/Git/map verify", [])]
        self.assertEqual(texts, ["/map verify"])

    def test_tab_line_lists_candidates(self):
        stdin = io.StringIO("nf lay\t\nquit\n")
        stdout = io.StringIO()
        code = term.run_session(lambda argv: 0, stdin, stdout, show_banner=False,
                                index=self._index())
        self.assertEqual(code, 0)
        out = stdout.getvalue()
        self.assertIn("补全：「nf lay」", out)
        self.assertIn("nf layers", out)

    def test_history_append_dedupes_and_skips_blank(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            self.assertTrue(term.append_history(path, "nf doctor"))
            self.assertFalse(term.append_history(path, "nf doctor"))
            self.assertFalse(term.append_history(path, "   "))
            self.assertTrue(term.append_history(path, "nf layers"))
            self.assertEqual(term.load_history(path), ["nf doctor", "nf layers"])
            self.assertEqual(term.load_history(path, limit=1), ["nf layers"])
        finally:
            os.remove(path)

    def test_history_written_only_in_interactive_mode(self):
        import inspect
        self.assertNotIn("history_path", inspect.signature(term.run_lines).parameters,
                         "脚本面（--exec/--file）不得有历史钩子：确定性是硬契约")
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            term.run_lines(["nf doctor"], lambda argv: 0)
            self.assertEqual(term.load_history(path), [])
            term.run_session(lambda argv: 0, io.StringIO("nf doctor\nquit\n"),
                             io.StringIO(), show_banner=False, history_path=path)
            self.assertEqual(term.load_history(path), ["nf doctor"])
        finally:
            os.remove(path)

    def test_default_history_path_honours_nf_home(self):
        old = os.environ.get("NARRATIVE_FORGE_HOME")
        probe = str(ROOT / "tmp-home-probe")
        os.environ["NARRATIVE_FORGE_HOME"] = probe
        try:
            self.assertEqual(term.default_history_path(),
                             os.path.join(probe, "shell_history"))
        finally:
            if old is None:
                os.environ.pop("NARRATIVE_FORGE_HOME", None)
            else:
                os.environ["NARRATIVE_FORGE_HOME"] = old

    def test_default_history_path_survives_storage_unavailable(self):
        """storage 不可用时的兜底分支也必须算得出路径。

        回归依据（2026-09-27）：该分支用了**未导入**的 `Path`——只在 `core.storage` 导入失败
        时才走到，本机从未触发，ruff 的 F821 把它抓了出来（同类：`nf stats --json` 的 `json`）。
        """
        saved = sys.modules.get("core.storage")
        sys.modules["core.storage"] = None       # None → `from core import storage` 抛 ImportError
        try:
            path = term.default_history_path()
        finally:
            if saved is None:
                sys.modules.pop("core.storage", None)
            else:
                sys.modules["core.storage"] = saved
        self.assertTrue(path.endswith("shell_history"), path)


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

    def test_cli_form_faces(self):
        def _run_io(argv):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = nf.main(list(argv))
            return code, out.getvalue() + err.getvalue()

        code, out = _run_io(["shell", "--form", "--no-banner"])
        self.assertEqual(code, 0)
        self.assertIn("写盘表单", out)
        self.assertIn("deprecate-module", out)
        code, out = _run_io(["shell", "--form", "stats-write", "--no-banner"])   # dry-run
        self.assertEqual(code, 0)
        self.assertIn("nf stats --write", out)
        self.assertIn("dry-run", out)
        code, out = _run_io(["shell", "--form", "asset-add", "--answer", "file=a.md",
                             "--no-banner"])
        self.assertEqual(code, 2)
        self.assertIn("还缺必填项", out)
        code, out = _run_io(["shell", "--form", "no-such", "--no-banner"])
        self.assertEqual(code, 2)
        self.assertIn("未识别的表单", out)

    def test_cli_session_guards_and_persistence(self):
        def _run_io(argv):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = nf.main(list(argv))
            return code, out.getvalue() + err.getvalue()

        code, out = _run_io(["shell", "--session", "relative.json", "--no-banner"])
        self.assertEqual(code, 2)
        self.assertIn("绝对路径", out)
        inside = str(ROOT / "tmp-session-guard.json")
        code, out = _run_io(["shell", "--session", inside, "--no-banner"])
        self.assertEqual(code, 2)
        self.assertIn("不得落在仓库内", out)
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            old_in, old_out = sys.stdin, sys.stdout
            sys.stdin = io.StringIO("/set width=130\nquit\n")
            sys.stdout = io.StringIO()
            try:
                code = nf.main(["shell", "--session", path, "--no-banner",
                                "--no-history"])
            finally:
                sys.stdin, sys.stdout = old_in, old_out
            self.assertEqual(code, 0)
            state, warn = term.load_session_state(path)
            self.assertEqual(warn, "")
            self.assertEqual(state["settings"]["width"], 130,
                             "会话状态须在 /set 后落盘")
        finally:
            os.remove(path)

    def test_cli_output_experience_flags(self):
        code, out = _run(["shell", "--commands", "asset", "--limit", "3", "--no-banner"])
        self.assertEqual(code, 0)
        self.assertIn("还有", out)
        self.assertNotIn("\x1b", out, "默认（非 TTY）不得上色：确定性契约")
        code, out = _run(["shell", "--commands", "asset", "--limit", "3",
                          "--color", "always", "--no-banner"])
        self.assertEqual(code, 0)
        self.assertIn("\x1b[", out)

    def test_cli_complete_face(self):
        code, out = _run(["shell", "--complete", "nf lay", "--no-banner"])
        self.assertEqual(code, 0)
        self.assertIn("nf layers", out)
        code, _out = _run(["shell", "--complete", "nf zzzz", "--no-banner"])
        self.assertEqual(code, 2)

    def test_cli_interactive_session_writes_history_and_completes(self):
        """走 CLI 的交互态接线（含 history 默认路径解析 + 行尾 Tab）——此前一轮接线缺口
        （terminal 忘了 import os）正是靠这类端到端测试兜住。"""
        fd, hist = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        old_in, old_out = sys.stdin, sys.stdout
        sys.stdin = io.StringIO("nf lay\t\nnf layers --verify\nquit\n")
        sys.stdout = io.StringIO()
        try:
            code = nf.main(["shell", "--history", hist, "--no-banner"])
            out = sys.stdout.getvalue()
        finally:
            sys.stdin, sys.stdout = old_in, old_out
        try:
            self.assertEqual(code, 0, out)
            self.assertIn("补全：「nf lay」", out)
            self.assertIn("nf layers", out)
            # Tab 行与 quit 不入历史：只记真执行过的命令
            self.assertEqual(term.load_history(hist), ["nf layers --verify"])
        finally:
            os.remove(hist)

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


class NavigationConsistencyTest(unittest.TestCase):
    """菜单（任务路径）↔ 能力族（完整面）互标：两套结构可对照，不留隐含映射。"""

    def test_every_zone_declares_a_real_family(self):
        fam_ids = {f["id"] for f in term.family_table()}
        for z in term.zone_table():
            self.assertIn(z.get("family"), fam_ids, z["id"])

    def test_menu_states_uncovered_families(self):
        text = term.menu()
        rest = term.families_without_zone()
        self.assertTrue(rest, "当前 8 区覆盖不完 8 族——菜单应显式告知剩余族")
        for fid in rest:
            self.assertIn(fid, text)
        self.assertIn("/map", text)

    def test_map_marks_quick_zones(self):
        text = term.render_map()
        for z in term.zone_table():
            if term.zones_of_family(z["family"]):
                self.assertIn("菜单快捷区：", text)
                break
        self.assertIn("菜单无快捷区", text, "未被菜单覆盖的族须显式标注")
        self.assertEqual(term.zones_of_family("start"), ["0", "1"])
        self.assertEqual(term.zones_of_family("no-such-family"), [])

    def test_self_check_flags_bad_zone_family(self):
        original = term.ZONES
        bad = tuple([dict(original[0], family="no-such-family")] + list(original[1:]))
        term.ZONES = bad
        try:
            tree = nf._collect_cli_tree()
            issues, _ = term.self_check(nf._shell_command_index(), tree["commands"],
                                        tree["root_flags"])
            self.assertTrue(any("family 不在能力族名单" in i for i in issues), issues)
        finally:
            term.ZONES = original


class TerminalEfficiencyTest(unittest.TestCase):
    """终端效率：唯一前缀补全（少敲键）+ 宽度缓存（渲染热路径）。"""

    @staticmethod
    def _index():
        return nf._shell_command_index()

    def test_unique_prefix_is_resolved(self):
        calls = []
        session = term.Session(lambda argv: calls.append(list(argv)) or 0,
                               index=self._index())
        rec = session.dispatch("nf scor")
        self.assertEqual(rec["argv"], ["score"], "唯一前缀应自动补全")
        self.assertIn("唯一前缀补全", rec["note"])
        self.assertEqual(calls, [["score"]])

    def test_ambiguous_prefix_is_not_guessed(self):
        calls = []
        session = term.Session(lambda argv: calls.append(list(argv)) or 0,
                               index=self._index())
        rec = session.dispatch("nf stat")            # stats 与 state-front 两候选
        self.assertEqual(rec["exit"], 2)
        self.assertIn("未知命令", rec["note"])
        self.assertIn("你是不是想找", rec["note"])
        self.assertEqual(calls, [], "有歧义时不许猜着执行")

    def test_parser_and_index_are_cached(self):
        """效率核心：同一进程内解析器/索引/命令树只构建一次（否则每条命令多付 ~100 ms）。"""
        self.assertIs(nf._build_parser(), nf._build_parser())
        self.assertIs(nf._shell_command_index(), nf._shell_command_index())
        self.assertIs(nf._collect_cli_tree(), nf._collect_cli_tree())

    def test_char_width_cache_wired_and_correct(self):
        term.char_width.cache_clear()
        self.assertEqual(term.char_width("中"), 2)
        self.assertEqual(term.char_width("a"), 1)
        self.assertEqual(term.char_width("中"), 2)
        info = term.char_width.cache_info()
        self.assertGreaterEqual(info.hits, 1, "宽度查询走缓存（渲染热路径）")
        self.assertGreaterEqual(info.maxsize, 1024)
        self.assertEqual(term.display_width("中文ab"), 6)


class ReplayAndColorPolishTest(unittest.TestCase):
    """历史重放（!! / !n / !前缀）与着色细化（CLICOLOR_FORCE / 命中高亮）。"""

    def test_replay_specs(self):
        session = term.Session(lambda argv: 0)
        self.assertEqual(session.resolve_replay(""), (False, "本次会话还没有可重放的命令"
                                                      "（先跑一条；/replay 看清单）"))
        session.commands[:] = ["nf doctor", "nf layers --verify", "nf stats --check"]
        self.assertEqual(session.resolve_replay(""), (True, "nf stats --check"))
        self.assertEqual(session.resolve_replay("2"), (True, "nf layers --verify"))
        self.assertEqual(session.resolve_replay("!")[:1], (False,))
        self.assertEqual(session.resolve_replay("9")[0], False)
        self.assertEqual(session.resolve_replay("nf lay")[1], "nf layers --verify")
        self.assertEqual(session.resolve_replay("nf zzz")[0], False)

    def test_replay_dispatch_records_and_executes(self):
        calls = []
        session = term.Session(lambda argv: calls.append(list(argv)) or 0)
        session.dispatch("nf doctor")
        rec = session.dispatch("!!")
        self.assertEqual(rec["kind"], "replay")
        self.assertEqual(calls, [["doctor"], ["doctor"]])
        self.assertIn("重放：nf doctor", rec["note"])
        self.assertEqual(session.commands, ["nf doctor", "nf doctor"],
                         "被重放执行的那条也算本次会话命令")

    def test_replay_of_write_still_hits_gate(self):
        calls = []
        session = term.Session(lambda argv: calls.append(list(argv)) or 0)
        session.commands[:] = ["nf stats --write"]
        rec = session.dispatch("!!")
        self.assertEqual(rec["exit"], 2, "重放的写盘命令必须仍被闸门拦下（fail-closed）")
        self.assertIn("确认", rec["note"])
        self.assertEqual(calls, [])

    def test_render_replay_list(self):
        session = term.Session(lambda argv: 0)
        self.assertIn("还没有可重放", session.render_replay_list())
        session.commands[:] = ["nf doctor"]
        text = session.render_replay_list()
        self.assertIn("1  nf doctor", text)
        self.assertNotIn("\x1b", text)

    def test_clicolor_force_and_no_color_precedence(self):
        class _Pipe:
            @staticmethod
            def isatty():
                return False

        old_force, old_nc = os.environ.get("CLICOLOR_FORCE"), os.environ.get("NO_COLOR")
        os.environ.pop("NO_COLOR", None)
        os.environ["CLICOLOR_FORCE"] = "1"
        try:
            self.assertTrue(term.resolve_color("auto", _Pipe()),
                            "CLICOLOR_FORCE 应在 auto 档强制开启")
            os.environ["NO_COLOR"] = "1"
            self.assertFalse(term.resolve_color("auto", _Pipe()),
                             "NO_COLOR 优先于 CLICOLOR_FORCE（关比开安全）")
        finally:
            for k, v in (("CLICOLOR_FORCE", old_force), ("NO_COLOR", old_nc)):
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_highlight_only_when_colored(self):
        plain = term.highlight("一致性报告工件", "一致性", False)
        self.assertEqual(plain, "一致性报告工件")
        colored = term.highlight("一致性报告工件", "一致性", True)
        self.assertIn("\x1b[", colored)
        self.assertIn("一致性", colored)
        self.assertEqual(term.highlight("abc", "zzz", True), "abc")

    def test_search_highlight_keeps_alignment(self):
        index = nf._shell_command_index()
        plain = term.render_search(index, "装配", color=False)[0]
        colored = term.render_search(index, "装配", color=True)[0]
        self.assertNotIn("\x1b", plain)
        self.assertIn("\x1b[", colored)
        # 左列（命令列）补位不变：着色的只是右列命中词，剥掉 ANSI 后两版必须逐字对齐
        import re as _re
        _strip = lambda s: _re.sub(r"\x1b\[[0-9;]*m", "", s)

        def _lefts(text):
            out = []
            for ln in text.splitlines():
                bare = _strip(ln)
                if bare.startswith("  nf "):
                    out.append(bare[:30])
            return out

        self.assertTrue(_lefts(plain))
        self.assertEqual(_lefts(plain), _lefts(colored))


class BaselineTest(unittest.TestCase):
    """顶尖 CLI 基线：真源自洽 + 逐行可复跑（含「该被拒」的行）。"""

    def test_baseline_table_self_consistent(self):
        issues = term.baseline_argv_issues()
        self.assertEqual(issues, [])
        ids = [r["id"] for r in term.baseline_table()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(any(r.get("expect_exit") == 2 for r in term.baseline_table()),
                        "基线须含「该被拒」的行（安全面不能只测成功路径）")

    def test_run_baseline_with_fake_runner(self):
        rows = ({"id": "ok-row", "name": "A", "argv": ("shell", "--x"),
                 "expect": "好"},
                {"id": "refuse-row", "name": "B", "argv": ("shell", "--y"),
                 "expect": "拒", "expect_exit": 2},
                {"id": "forbid-row", "name": "C", "argv": ("shell", "--z"),
                 "forbid": "\x1b"})
        seen = []

        def _runner(argv, stdin_text=None):
            seen.append(list(argv))
            if argv[-1] == "--x":
                return 0, "好"
            if argv[-1] == "--y":
                return 2, "拒"
            return 0, "干净"

        results, stats = term.run_baseline(_runner, rows=rows)
        self.assertEqual((stats["rows"], stats["passed"]), (3, 3))
        self.assertIn("total_ms", stats)
        self.assertEqual([r["ok"] for r in results], [True, True, True])
        self.assertEqual(seen, [["shell", "--x"], ["shell", "--y"], ["shell", "--z"]])

    def test_run_baseline_detects_failures(self):
        rows = ({"id": "wrong-exit", "name": "A", "argv": ("shell",),
                 "expect": "x", "expect_exit": 0},)
        results, stats = term.run_baseline(
            lambda argv, stdin_text=None: (2, "x"), rows=rows)
        self.assertEqual(stats["passed"], 0)
        self.assertFalse(results[0]["ok"])

    def test_run_baseline_supports_stdin_and_expect_file(self):
        """交互态证据：stdin 喂输入 + 断言落盘文件真的存在（会话/历史两行就靠它）。"""
        tmp_dir = term.baseline_tmp_dir()
        target = os.path.join(tmp_dir, "unit_probe.txt")
        rows = ({"id": "file-probe", "name": "落盘探针",
                 "argv": ("shell", term.BASELINE_TMP + "/unit_probe.txt"),
                 "stdin": "喂给终端的输入\n", "expect": "收到了",
                 "expect_file": term.BASELINE_TMP + "/unit_probe.txt"},)

        def _runner(argv, stdin_text=None):
            self.assertEqual(argv[1], target, "`{TMP}` 须展开为受控临时目录下的绝对路径")
            self.assertEqual(stdin_text, "喂给终端的输入\n")
            with open(target, "w", encoding="utf-8") as fh:
                fh.write("x\n")
            return 0, "收到了"

        results, stats = term.run_baseline(_runner, rows=rows)
        self.assertEqual(stats["passed"], 1, results)
        self.assertEqual(results[0]["expect_file"], target)
        self.assertTrue(os.path.isfile(target))
        self.assertTrue(term.baseline_tmp_dir().startswith(str(Path(tempfile.gettempdir()))))

    def test_run_baseline_fails_when_expected_file_missing(self):
        rows = ({"id": "no-file", "name": "缺件", "argv": ("shell",),
                 "expect": "ok", "expect_file": term.BASELINE_TMP + "/never_written.bin"},)
        results, stats = term.run_baseline(lambda argv, stdin_text=None: (0, "ok"),
                                           rows=rows)
        self.assertEqual(stats["passed"], 0, "声明了 expect_file 就必须真有该文件")

    def test_baseline_enforces_latency_budget(self):
        """时间预算：超时即判「效率退化」（把「极致效率」钉成判据，而非口号）。"""
        import time as _time

        def _slow(argv, stdin_text=None):
            _time.sleep(0.02)
            return 0, "ok"

        rows = ({"id": "tight", "name": "紧预算", "argv": ("shell",), "expect": "ok",
                 "max_ms": 1},)
        results, stats = term.run_baseline(_slow, rows=rows)
        self.assertEqual(stats["passed"], 0, "超预算必须判不过")
        self.assertGreaterEqual(results[0]["ms"], 10)
        self.assertEqual(results[0]["max_ms"], 1)
        rows = ({"id": "loose", "name": "宽预算", "argv": ("shell",), "expect": "ok",
                 "max_ms": 5000},)
        results, stats = term.run_baseline(_slow, rows=rows)
        self.assertEqual(stats["passed"], 1)
        self.assertEqual(stats["rows"], 1)
        self.assertGreaterEqual(stats["total_ms"], 10)

    def test_real_baseline_rows_declare_sane_budgets(self):
        for row in term.baseline_table():
            budget = float(row.get("max_ms", term.BASELINE_DEFAULT_MAX_MS))
            self.assertGreater(budget, 0, row["id"])
            self.assertLessEqual(budget, 10000,
                                 "%s 的预算过高（>10s），拦不住数量级回归" % row["id"])

    def test_render_baseline_marks_and_no_ansi(self):
        results, stats = term.run_baseline(lambda argv, stdin_text=None: (0, "好"),
                                            rows=({"id": "a", "name": "甲",
                                                   "argv": ("shell",), "expect": "好"},))
        text = term.render_baseline(results, stats)
        self.assertIn("通过 1/1", text)
        self.assertIn("甲", text)
        self.assertNotIn("\x1b", text)


class BaselineCliTest(unittest.TestCase):
    def test_cli_baseline_passes_and_json_pure(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = nf.main(["shell", "--baseline", "--no-banner"])
        text = out.getvalue() + err.getvalue()
        self.assertEqual(code, 0, text)
        self.assertIn("顶尖 CLI 基线", text)
        self.assertIn("通过 %d/%d" % (len(term.baseline_table()),
                                      len(term.baseline_table())), text)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = nf.main(["shell", "--baseline", "--json", "--no-banner"])
        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())       # 纯 JSON
        self.assertEqual(payload["kind"], "shell-baseline")
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["stats"]["passed"], payload["stats"]["rows"])


class DeepCheckTest(unittest.TestCase):
    """活体自检：真跑一条只读命令 + 落点可写性探测（不落件）。"""

    @staticmethod
    def _index():
        return nf._shell_command_index()

    def test_writable_probe_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "sub", "deep", "history.txt")
            ok, why = term.writable_dir_probe(target)
            self.assertTrue(ok, why)
            self.assertEqual(os.listdir(tmp), [], "探测不得落件（删除能力受限，故用祖先目录判）")
            self.assertEqual(term.writable_dir_probe(""), (True, "未启用"))

    def test_deep_check_calls_live_runner_and_reports(self):
        calls = []

        def _live(argv):
            calls.append(list(argv))
            return 0

        tree = nf._collect_cli_tree()
        issues, stats = term.deep_check(self._index(), tree["commands"],
                                        tree["root_flags"], live_runner=_live)
        self.assertEqual(issues, [])
        self.assertEqual(calls[0], ["layers", "--verify"])
        self.assertEqual(len(calls), 1 + len(tree["commands"]),
                         "活体档须逐条跑 nf <cmd> --help（「最全」的可执行层证据）")
        self.assertEqual(stats["live_code"], 0)
        self.assertEqual(stats["help_sweep_failed"], [])
        self.assertEqual(stats["help_sweep_total"], len(tree["commands"]))
        self.assertIn("readline", stats)

    def test_deep_check_reports_uncallable_command(self):
        def _live(argv):
            return 1 if list(argv) == ["doctor", "--help"] else 0

        tree = nf._collect_cli_tree()
        issues, stats = term.deep_check(self._index(), tree["commands"],
                                        tree["root_flags"], live_runner=_live)
        self.assertEqual(stats["help_sweep_failed"], ["doctor"])
        self.assertTrue(any("全命令可调用性失败" in i for i in issues), issues)

    def test_deep_check_reports_live_failure(self):
        tree = nf._collect_cli_tree()
        issues, stats = term.deep_check(self._index(), tree["commands"],
                                        tree["root_flags"],
                                        live_runner=lambda argv: 1)
        self.assertEqual(stats["live_code"], 1)
        self.assertTrue(any("活体自检失败" in i for i in issues), issues)

    def test_deep_check_reports_unwritable_landing(self):
        tree = nf._collect_cli_tree()
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        try:
            issues, _ = term.deep_check(self._index(), tree["commands"],
                                        tree["root_flags"],
                                        live_runner=lambda argv: 0,
                                        history_path=path)
            self.assertEqual(issues, [], "可写落点不该报错")
        finally:
            os.remove(path)

    def test_families_for_filter(self):
        self.assertEqual([f["id"] for f in term.families_for("治理")], ["govern"])
        self.assertEqual(len(term.families_for("")), len(term.family_table()))


class MachineFaceTest(unittest.TestCase):
    """机器面：`--json` 输出必须是**纯 JSON**（可被工具直接消费）。"""

    @staticmethod
    def _run_io(argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = nf.main(list(argv))
        return code, out.getvalue() + err.getvalue()

    def test_commands_map_forms_json(self):
        code, out = self._run_io(["shell", "--commands", "asset", "--json", "--no-banner"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["kind"], "commands")
        self.assertTrue(payload["rows"])
        code, out = self._run_io(["shell", "--map", "verify", "--json", "--no-banner"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["kind"], "map")
        self.assertEqual([f["id"] for f in payload["families"]], ["verify"])
        code, out = self._run_io(["shell", "--form", "--json", "--no-banner"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["kind"], "forms")
        self.assertEqual(len(payload["rows"]), len(term.form_table()))

    def test_form_plan_and_verify_json_are_pure(self):
        code, out = self._run_io(["shell", "--form", "stats-write", "--json", "--no-banner"])
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["kind"], "form-plan")
        self.assertEqual(payload["argv"], ["stats", "--write"])
        self.assertFalse(payload["executed"])
        code, out = self._run_io(["shell", "--verify", "--deep", "--json", "--no-banner"])
        self.assertEqual(code, 0, out)
        payload = json.loads(out)          # 混入活体输出就会在这里炸
        self.assertTrue(payload["deep"])
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["stats"]["live_code"], 0)
        self.assertEqual(payload["stats"]["help_sweep_failed"], [],
                         "真仓库里全部命令的 --help 都必须可调用")
        self.assertGreaterEqual(payload["stats"]["help_sweep_total"], 60)

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
        self.assertIn("nf 1.0.1", out)

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
                    top = alias.name.split(".")[0]
                    self.assertTrue(top in sys.stdlib_module_names or top == "core",
                                    "终端不得依赖第三方：%s" % alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                top = node.module.split(".")[0]
                # `core.*` 是同包本地模块（纯度 R5 的 _is_local 同语义），不算第三方
                self.assertTrue(top in sys.stdlib_module_names or top == "core",
                                "终端不得依赖第三方：%s" % node.module)


if __name__ == "__main__":
    unittest.main()
