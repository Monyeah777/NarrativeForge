#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2.8.0 波C D2 —— scripts/nf.py CLI 层自动化测试（41 规划 D 组收口杂务）。

覆盖子命令参数面与装配链 smoke（替代手工冒烟；不依赖 GUI/端壳）。
"""
import argparse
import ast
import builtins
import collections
import re
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
spec = importlib.util.spec_from_file_location("nfcli", ROOT / "scripts" / "nf.py")
assert spec is not None and spec.loader is not None
nf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nf)

_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def declared_flags(src: str) -> list:
    """→ `[(行号, dest, 长选项串表)]`：全部 `add_argument` 声明（纯函数）。"""
    tree = ast.parse(src)
    out = []
    for call in [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "add_argument"]:
        opts = [a.value for a in call.args
                if isinstance(a, ast.Constant) and isinstance(a.value, str)
                and a.value.startswith("-")]
        longs = [o for o in opts if o.startswith("--")]
        if not longs:
            continue                    # 只有短选项（`-h`）或位置参数，跳过
        dest, decl_hits = "", 0
        for kw in call.keywords:
            if kw.arg == "dest" and isinstance(kw.value, ast.Constant):
                dest = str(kw.value.value)
                decl_hits = 1           # 显式 `dest="x"` 字面量本身占 1 次词元
        if not dest:
            dest = longs[-1][2:].replace("-", "_")
        out.append((call.lineno, dest, longs, decl_hits))
    return out


def unread_flags(src: str) -> list:
    """→ 「**声明了、却从没被读过**」的旗标 `[(行号, dest, 长选项串)]`（纯函数，变异自证直接喂它）。

    口径（探针先证伪过一版）：隐式 dest 的**声明行不含 dest 词元**——`--no-render` 分词成
    `no` + `render`，一次「读」是 `args.no_render` 这种写法。第一版按「词元数 ≤1 即零引用」判，
    把 7 个真在用的旗标（`--no-render`/`--state-text`/`--no-banner`/`--no-history`/`--no-start`/
    `--no-include-refs`/`--write-advisory`）全报成死旗标——所以阈值必须区分「显式 dest=」与
    「由选项串推出来的 dest」。
    """
    counts = collections.Counter(_TOKEN.findall(src))
    out = []
    for lineno, dest, longs, decl_hits in declared_flags(src):
        if dest in ("help", "version"):
            continue
        if counts[dest] <= decl_hits:
            out.append((lineno, dest, longs[-1]))
    return out


class LightCommandReadBudgetTest(unittest.TestCase):
    """轻命令的**读取面预算**：它们必须只碰少量文件，否则「毫秒级」立刻不成立。

    动机（本轮全景实测）：24 条代表命令里 22 条守护热跑 ≤135 ms（多数 2–40 ms），只有
    `score` / `conformance` 是「全仓工具」。轻命令之所以轻，是因为**不读全仓**——本判据把
    「轻」钉成可核事实：一旦有人往轻命令里塞一次全仓扫描（全仓 ≈2354 个文件），打开次数会
    从个位数跳到四位数，当场红。口径是**计数**（不是计时），与机器快慢、噪声都无关。
    """

    BUDGET = 60        # 实测 0–36 次；全仓扫描会到 2000+（两个数量级余量）
    CMDS = (("domain", "ls"), ("assertions", "--check"), ("approve", "--verify"),
            ("output", "ls"), ("library", "ls"), ("market", "--list"),
            ("state-front",), ("knowledge", "--check"), ("sig", "--check"),
            ("patterns", "ls"), ("audit",))

    def _opens(self, argv):
        counts: collections.Counter = collections.Counter()
        orig = io.open

        def spy(file, *a, **k):
            try:
                path = os.path.normcase(os.path.abspath(str(file)))
                if ".git" not in path and ".rivet" not in path:
                    counts[path] += 1
            except Exception:                    # noqa: BLE001 - 计数失败不影响被测逻辑
                pass
            return orig(file, *a, **k)

        io.open = spy
        builtins.open = spy
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                try:
                    nf.main(list(argv))
                except SystemExit:
                    pass
        finally:
            io.open = orig
            builtins.open = orig
        return sum(counts.values())

    def test_light_commands_do_not_scan_the_whole_repo(self):
        for argv in self.CMDS:
            got = self._opens(argv)
            self.assertLessEqual(
                got, self.BUDGET,
                "`nf %s` 打开了 %d 个文件（>%d）——轻命令里混进了全仓扫描？"
                % (" ".join(argv), got, self.BUDGET))


class NoDeadFlagTest(unittest.TestCase):
    """CLI 面：**声明了却从没被读过**的旗标必须为零。

    依据（2026-10-02，作者指令「清除逻辑垃圾（注意辨别）」「内外口径统一」）：本轮修
    `nf review --scope` 时发现它属「读了但不起作用」；比它更早一层的形态是**压根没读**——
    旗标进了 `--help`、进了 shell 补全、进了文档，却没有任何代码路径看它一眼。本判据把这一层
    钉住（「读了但不生效」那类语义问题另由各自的真跑用例守）。
    """

    def test_no_declared_flag_is_unread(self):
        src = (ROOT / "scripts" / "nf.py").read_text(encoding="utf-8")
        declared = declared_flags(src)
        self.assertGreaterEqual(len(declared), 60,
                                "旗标面塌缩（判据可能已失效）：%d" % len(declared))
        got = unread_flags(src)
        self.assertEqual([], got,
                         "声明了却从没读过的旗标（修复指引：接线到代码，或删掉声明与文档）：%s"
                         % ["%s:%d %s" % (ROOT.joinpath("scripts/nf.py").as_posix(), ln, opt)
                            for ln, _dest, opt in got])

    def test_predicate_has_catch_power(self):
        """变异自证：**没读**的旗标必判红；`args.x` 读过的、显式 dest= 的不许误报。"""
        dead = ("p = subparsers.add_parser('x')\n"
                "p.add_argument('--never-read', action='store_true', help='说明')\n")
        self.assertEqual([(2, "never_read", "--never-read")], unread_flags(dead))
        used = ("p = subparsers.add_parser('x')\n"
                "p.add_argument('--no-render', action='store_true')\n"
                "def f(args):\n    return not args.no_render\n")
        self.assertEqual([], unread_flags(used))
        explicit = ("p = subparsers.add_parser('x')\n"
                    "p.add_argument('--x-y', dest='foo', action='store_true')\n"
                    "def f(args):\n    return args.foo\n")
        self.assertEqual([], unread_flags(explicit))


class NfCliSmokeTest(unittest.TestCase):
    @staticmethod
    def _run(argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = nf.main(list(argv))
        return code, out.getvalue()

    def _subcommands(self):
        p = nf._build_parser()
        for a in p._actions:
            if isinstance(a, argparse._SubParsersAction):
                return set(a.choices)
        return set()

    def test_wave_c_subcommands_exposed(self):
        cmds = self._subcommands()
        for c in ("sig", "diff", "explain", "related", "pipeline", "module", "demo", "worldmodel"):
            self.assertIn(c, cmds)

    def test_sig_verify(self):
        code, out = self._run(["sig", "--verify"])
        self.assertEqual(code, 0)
        self.assertIn("可复现", out)

    def test_explain_check25(self):
        code, out = self._run(["explain", "25"])
        self.assertEqual(code, 0)
        self.assertIn("check25", out)

    def test_market_list(self):
        code, out = self._run(["market", "--list"])
        self.assertEqual(code, 0)
        self.assertIn("包", out)

    def test_market_list_json(self):
        code, out = self._run(["market", "--list", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "market-list"', out)
        self.assertIn('"grade"', out)

    def test_stats_json_is_pure_json(self):
        """`nf stats --json` 必须真的输出 JSON。

        回归依据（2026-09-27）：该分支直接用了模块级未导入的 `json`，命令**当场崩**成
        「内部错误：name 'json' is not defined」；而 `nf stats --check` 走的是另一条分支，
        门禁只覆盖了后者——ruff 的 F821（未定义名）把它抓了出来。机器面是终端的公开契约，
        必须有直接判据。
        """
        code, out = self._run(["stats", "--json"])
        self.assertEqual(code, 0, out)
        data = json.loads(out)
        # 期望值取自基线真源，不写字面量（此前钉死 40/70，基线一动本判据就假红）。
        from core import quality_baseline as _qb
        self.assertEqual(_qb.EXPECTED_CHECKS, data["baseline_checks"])
        self.assertEqual(_qb.EXPECTED_PASS, data["baseline_pass"])

    def test_related_techdoc(self):
        code, out = self._run(["related", "技术文档域包"])
        self.assertEqual(code, 0)
        self.assertIn("官方核心", out)

    def test_diff_01_vs_36(self):
        """nf diff 冒烟：01 核心协议 vs 36 方案 → 判定行在场（C2 差异检测）。"""
        code, out = self._run(["diff", str(ROOT / "01_核心协议.md"),
                               str(ROOT / "02_联动注册表.md")])
        self.assertEqual(code, 0)
        self.assertIn("判定", out)

    def test_related_m90_reverse(self):
        """nf related 冒烟：M90 反向引用方（M2 校验 P03 drill 之外的人读链）。"""
        code, out = self._run(["related", "M90"])
        self.assertEqual(code, 0)
        self.assertIn("技术文档域包", out)

    def test_related_json(self):
        code, out = self._run(["related", "M90", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"target": "M90"', out)
        self.assertIn('"kind"', out)

    def test_id_arguments_tolerate_surrounding_whitespace(self):
        """**标识符**入参裁空白：粘贴常带看不见的尾随/前导空格（2026-10-01 口径统一）。

        实测缺口：`nf who-refers "M90 "` / `nf related "M90 "` / `nf impact "M90 "` 此前判
        「不在册」——那是**假事实**（id 本来就是对的）；而 `library show` / `decisions show`
        / `patterns show` 一直是裁的。路径类入参**不裁**（POSIX 下尾随空格是合法文件名），
        故本件只钉标识符面。
        """
        # 2026-10-10：原第 4 例【domain build --spec ' A01 '】依赖
        # .rivet/private_archive/ai_packs/specs/（gitignored 内部档案）——fresh clone 上该
        # spec 不在场，命令**应当**返回 1，故不能当 CI 判据；换成 tracked 数据面的标识符命令。
        for argv in (["related", " M90 "], ["who-refers", "M90 "],
                     ["impact", " M90"], ["patterns", "show", " predicate-single-source "]):
            code, out = self._run(argv)
            self.assertEqual(0, code, "%s 应当接受带空白的标识符：%s" % (argv, out[:120]))

    def test_asset_ls_json(self):
        code, out = self._run(["asset", "ls", "--json", "--root", str(ROOT)])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "asset-ls"', out)
        self.assertIn('"rows"', out)

    def test_asset_inventory_json(self):
        code, out = self._run(["asset", "inventory", "--json", "--root", str(ROOT)])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "asset-inventory"', out)

    def test_module_ls_json(self):
        code, out = self._run(["module", "ls", "--json", "--root", str(ROOT)])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "module-ls"', out)
        self.assertIn('"file"', out)

    def test_completion_bash(self):
        code, out = self._run(["completion", "bash"])
        self.assertEqual(code, 0)
        self.assertIn("complete -F _nf_completions nf", out)
        self.assertIn('"$cur" == -*', out)
        self.assertIn("sig", out)

    def test_completion_zsh(self):
        code, out = self._run(["completion", "zsh"])
        self.assertEqual(code, 0)
        self.assertIn("compdef _nf nf", out)
        self.assertIn("_nf_all_flags", out)

    def test_completion_fish(self):
        code, out = self._run(["completion", "fish"])
        self.assertEqual(code, 0)
        self.assertIn("__fish_use_subcommand", out)
        self.assertIn("doctor", out)
        self.assertIn("and __fish_seen_subcommand_from", out)

    def test_assemble_plan_match(self):
        """nf assemble：需求 → 装配计划（西幻关键词命中 P03 预设包）。"""
        code, out = self._run(["assemble", "帮我组装一个西幻生存世界的完整版"])
        self.assertEqual(code, 0)
        self.assertIn("西幻生存领域包", out)
        self.assertIn("P03", out)

    def test_assemble_plan_custom_flow(self):
        """nf assemble：未命中关键词 → 用户自定义流（不复位为死路）。"""
        code, out = self._run(["assemble", "做一个古代宫廷权谋世界的完整版"])
        self.assertEqual(code, 0)
        self.assertIn("用户自定义流", out)
        self.assertIn("M91-M99", out)

    def test_assemble_clarify_when_underspecified(self):
        """需求收敛漏斗：信息不足（无题材线索）→ 抛澄清问句，不硬猜。"""
        code, out = self._run(["assemble", "给我做一个世界"])
        self.assertEqual(code, 0)
        self.assertIn("需求澄清", out)
        self.assertIn("题材方向", out)

    def test_assemble_save_dossier(self):
        """需求档案：--save 把澄清/计划落成八字段回填稿。"""
        fd, path = tempfile.mkstemp(suffix=".md")
        os.close(fd)
        try:
            code, out = self._run(["assemble", "西幻生存",
                                   "--save", path])
            self.assertEqual(code, 0, out)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("需求澄清稿", text)
            self.assertIn("1. 一句话需求：西幻生存", text)
            self.assertIn("验收标准", text)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_assemble_dossier_merges_answers(self):
        fd, path = tempfile.mkstemp(suffix=".md")
        os.close(fd)
        try:
            code, out = self._run(["assemble", "给我做一个世界",
                                   "--answer", "题材：西幻生存",
                                   "--save", path])
            self.assertEqual(code, 0, out)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("澄清回填", text)
            self.assertIn("题材：西幻生存", text)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_assemble_check_real_p03_sample(self):
        """真实战例回归：仓库 P03 完整样本须通过 nf assemble --check。"""
        sample = os.path.join(ROOT, "docs", "完整版样本_西幻生存流P03.md")
        self.assertTrue(os.path.exists(sample), sample)
        code, out = self._run(["assemble",
                               "帮我组装一个西幻生存世界的完整版",
                               "--check", sample])
        self.assertEqual(code, 0, out)

    def test_assemble_check_is_not_silently_skipped_by_a_vague_requirement(self):
        """`--check` 是**验收动作**（2026-09-30 修）：需求无法解析时须明确拒（rc=2），不许回 0。

        修复前：`nf assemble "x" --check out.md` 走澄清分支后 `return 0`——脚本里的
        `nf assemble "$REQ" --check out.md && 发布` 会把「**根本没验收**」读成「验收通过」
        （与工具面那些「看起来正常的错答」同类）。允许集来自需求解析，解析不出就不能假装核对过。
        """
        sample = os.path.join(ROOT, "docs", "完整版样本_西幻生存流P03.md")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code, out = self._run(["assemble", "x", "--check", sample])
        self.assertEqual(2, code, out)
        self.assertIn("未执行验收", err.getvalue())
        self.assertIn("修复指引", err.getvalue())

    def test_asset_usage_json(self):
        code, out = self._run(["asset", "usage", "--json", "--root", str(ROOT)])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "asset-usage"', out)
        self.assertIn('"total_refs"', out)

    def test_asset_usage_strict_passes_repo(self):
        code, out = self._run(["asset", "usage", "--strict",
                               "--root", str(ROOT)])
        self.assertEqual(code, 0, out)

    def test_release_check_fast(self):
        code, out = self._run(["release", "--fast"])
        self.assertEqual(code, 0, out)
        self.assertIn("基线自描述一致", out)

    def test_toolface_ls_and_json(self):
        code, out = self._run(["toolface"])
        self.assertEqual(code, 0, out)
        self.assertIn("模块工具面", out)
        self.assertIn("M10", out)
        code, out = self._run(["toolface", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "toolface"', out)

    def test_worldmodel_ls_and_json(self):
        code, out = self._run(["worldmodel"])
        self.assertEqual(code, 0, out)
        self.assertIn("worldmodel", out)
        self.assertIn("M50", out)
        code, out = self._run(["worldmodel", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "worldmodel"', out)
        code, out = self._run(["worldmodel", "--walk"])
        self.assertEqual(code, 0, out)
        self.assertIn("begin → run → end → archive → roll", out)
        code, out = self._run(["worldmodel", "--run"])
        self.assertEqual(code, 0, out)
        self.assertIn("5 steps", out)
        self.assertIn("begin → run", out)
        code, out = self._run(["worldmodel", "--run", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"kind": "worldmodel-run"', out)
        self.assertIn('"digest"', out)
        fd, state_path = tempfile.mkstemp(suffix=".json")
        os.write(fd, json.dumps({
            "data_bus": {
                "active_pipeline": "P01",
                "round": {"phase": "begin", "phase_trace": []},
            },
            "WorldState": {"time": {"tick": 0}},
        }, ensure_ascii=False).encode("utf-8"))
        os.close(fd)
        try:
            code, out = self._run(["worldmodel", "--run", "--state", state_path, "--json"])
            self.assertEqual(code, 0, out)
            self.assertIn('"concrete_before"', out)
        finally:
            if os.path.exists(state_path):
                os.remove(state_path)

    def test_explain_check32(self):
        code, out = self._run(["explain", "32"])
        self.assertEqual(code, 0)
        self.assertIn("check32", out)

    def test_assemble_rounds_flag(self):
        good = ("回合 1：引用 06 §3 推进，M00 写回 状态快照。\n"
                "回合 2：引用 06 §3，M80 输出并进入下一回合。\n")
        fd, path = tempfile.mkstemp(suffix=".md")
        os.write(fd, good.encode("utf-8"))
        os.close(fd)
        try:
            code, out = self._run(["assemble", "西幻生存",
                                   "--check", path, "--rounds"])
            self.assertEqual(code, 0, out)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_assemble_answers_fill_clarify(self):
        """A3.2：--answer 多次回填 → 澄清转 ready（西幻命中预设）。"""
        code, out = self._run(["assemble", "给我做一个世界",
                               "--answer", "题材：西幻生存",
                               "--answer", "主轴：生存"])
        self.assertEqual(code, 0, out)
        self.assertIn("西幻生存领域包", out)
        self.assertNotIn("需求澄清", out)

    def test_assemble_session_memory(self):
        """会话存储：第一轮回填被记忆，第二轮无需重复 --answer。"""
        fd, sess = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            code, _ = self._run(["assemble", "给我做一个世界",
                                 "--answer", "题材：西幻生存",
                                 "--session", sess])
            self.assertEqual(code, 0)
            code, out = self._run(["assemble", "给我做一个世界",
                                   "--session", sess])
            self.assertEqual(code, 0, out)
            self.assertIn("西幻生存领域包", out)
        finally:
            if os.path.exists(sess):
                os.remove(sess)

    def test_assemble_trace(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            code, out = self._run(["assemble", "西幻生存", "--trace", path])
            self.assertEqual(code, 0, out)
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(data["phase"], "plan")
            self.assertEqual(data["pipeline"], "P03")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_assemble_check_ok_and_reject(self):
        """nf assemble --check：合格成品过、编造编号成品拒。"""
        def _write(text):
            fd, path = tempfile.mkstemp(suffix=".md")
            os.write(fd, text.encode("utf-8"))
            os.close(fd)
            return path

        try:
            ok_md = "\n".join("## %d. 段" % i for i in range(8)) + "\n由 M00 数据槽 记录。\n"
            path = _write(ok_md)
            code, out = self._run(["assemble", "西幻生存",
                                   "--check", path])
            self.assertEqual(code, 0, out)
            self.assertIn("通过", out)

            bad_md = ok_md + "由 M99 推进 回合。\n"
            path2 = _write(bad_md)
            code, _ = self._run(["assemble", "西幻生存", "--check", path2])
            self.assertEqual(code, 1)
        finally:
            for p in (path, path2):
                if os.path.exists(p):
                    os.remove(p)

    def test_exit_code_matrix(self):
        """退出码矩阵（子进程）：0 成功 / 1 运行·校验失败 / 2 用法（argparse）。"""
        cases = (
            (["bogus"], 2),
            (["run"], 2),
            (["explain", "no-such-check"], 2),
            (["doctor"], 0),
        )
        for argv, expected in cases:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "nf.py")] + argv,
                capture_output=True, text=True, encoding="utf-8", timeout=120,
            )
            self.assertEqual(proc.returncode, expected, "argv=%s" % argv)

    def test_market_package_json(self):
        code, out = self._run(["market", str(ROOT / "community" / "技术文档域包"), "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"registered": true', out)
        self.assertIn('"kind": "market-package"', out)

    def test_cli_catch_all_hides_traceback(self):
        """未预期异常：一句错误 + 退出 1，不裸刷 traceback（NF_DEBUG 时透出）。"""
        orig = nf.main

        def boom(argv=None):
            raise RuntimeError("boom")

        nf.main = boom
        try:
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = nf.cli([])
        finally:
            nf.main = orig
        self.assertEqual(code, 1)
        self.assertIn("内部错误", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    @staticmethod
    def _walk(parser, prefix=""):
        out = [(prefix or "<root>", parser)]
        for act in parser._actions:
            if isinstance(act, argparse._SubParsersAction):
                for name, sp in act.choices.items():
                    out += NfCliSmokeTest._walk(sp, (prefix + " " if prefix else "") + name)
        return out

    def test_all_commands_have_help_and_description(self):
        """命令面自洽矩阵：根 + 全部子命令（含二级）均带 description 与 -h/--help。"""
        bad = []
        for path, sp in self._walk(nf._build_parser()):
            if not getattr(sp, "description", ""):
                bad.append("%s: 缺 description" % path)
            opts = [o for a in sp._actions for o in a.option_strings]
            if "-h" not in opts and "--help" not in opts:
                bad.append("%s: 缺 help 选项" % path)
        self.assertEqual(bad, [])

    def test_json_flag_surface(self):
        """JSON 面自洽矩阵：声明的数据命令逐点带 --json（与 README 速查一致）。"""
        tree = nf._collect_cli_tree()["tree"]
        for cmd in ("sig", "diff", "doctor", "market", "related"):
            self.assertIn("--json", tree[cmd]["flags"], cmd)
        for sub in ("ls", "inventory"):
            self.assertIn("--json", tree["asset"]["nested"][sub], "asset " + sub)
        self.assertIn("--json", tree["module"]["nested"]["ls"], "module ls")

    def test_root_version_flag(self):
        tree_flags = nf._collect_cli_tree()["root_flags"]
        self.assertIn("--version", tree_flags)
        self.assertIn("--help", tree_flags)

    # ---- 44 波：CLI 工具链顶尖化（骨架约定：无参 help / help 子命令 / doctor / version）----
    def test_no_args_shows_help(self):
        code, out = self._run([])
        self.assertEqual(code, 0)
        self.assertIn("usage", out)

    def test_help_subcommand(self):
        code, out = self._run(["help", "sig"])
        self.assertEqual(code, 0)
        self.assertIn("usage: nf sig", out)
        self.assertIn("知识签名", out)
        self.assertIn("target", out)
        code2, _ = self._run(["help", "no-such"])
        self.assertEqual(code2, 2)

    def test_doctor_ok(self):
        code, out = self._run(["doctor"])
        self.assertEqual(code, 0)
        self.assertIn("体检", out)
        self.assertIn("[PASS]", out)

    def test_doctor_json(self):
        code, out = self._run(["doctor", "--json"])
        self.assertEqual(code, 0)
        self.assertIn('"ok": true', out)
        self.assertIn('"version"', out)

    def test_cli_version_flag(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "nf.py"), "--version"],
            capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("nf 1.0.1", proc.stdout)


SKIP_DESTS = {"help", "cmd"}
READ_PATTERNS = (
    r"args\.%s\b",
    r"getattr\(args,\s*[\"']%s[\"']",
    r"[\"']%s[\"']\s*\)",
)


def unread_flag_dests(parser, source: str, allow=()) -> list:
    """→ 声明了却**没人读**的旗标 dest 清单（纯函数：parser + 入口源码文本）。

    为什么要有这条：「声明面 = 执行面」是本仓纪律（MCP 那轮的同一条）。一个 `--flag`
    只在 `_build_parser()` 里挂着、代码里从不读它，就是**传了也没用的静默空转**——
    用户按 `--help` 传参却得到默认行为，比报错更难发现。
    """
    import re as _re
    found: dict = {}

    def _walk(p):
        for act in p._actions:
            if isinstance(act, argparse._SubParsersAction):
                for name, sp in act.choices.items():
                    _walk(sp)
                continue
            if not act.option_strings:
                continue
            dest = act.dest
            if not dest or dest in SKIP_DESTS or dest in allow:
                continue
            found.setdefault(dest, act.option_strings)

    _walk(parser)
    out = []
    for dest, flags in sorted(found.items()):
        if not any(_re.search(pat % _re.escape(dest), source) for pat in READ_PATTERNS):
            out.append((dest, tuple(flags)))
    return out


class DeclaredFlagsAreReadTest(unittest.TestCase):
    """「声明面 = 执行面」：`nf` 的每个旗标都必须真被读到（防静默空转）。"""

    def test_no_declared_flag_is_unread(self):
        source = (ROOT / "scripts" / "nf.py").read_text(encoding="utf-8")
        got = unread_flag_dests(nf._build_parser(), source)
        self.assertEqual([], got, "声明了却没人读的旗标（修复指引：在处理器里读它，"
                         "或删掉这个假接口）：%s" % got)

    def test_predicate_flags_unread_but_spares_read(self):
        """变异自证：只声明不读的旗标必判红；被 `args.x` / `getattr(args, "x")` 读的不许误报。"""
        p = argparse.ArgumentParser(prog="t")
        p.add_argument("--dead")
        p.add_argument("--live")
        p.add_argument("--gotten")
        src = 'print(args.live)\nprint(getattr(args, "gotten", False))\n'
        got = {d for d, _f in unread_flag_dests(p, src)}
        self.assertEqual({"dead"}, got)


class RootFlagHonoredTest(unittest.TestCase):
    """**声明了 `--root` 就必须真按它扫**（2026-09-30 补）。

    为什么要这条：`--root` 的用途是「对另一棵树做同一套体检」（例如在临时夹具上验证规则）。
    若某个命令声明了参数却仍扫真仓，用户会拿到**真仓的结论**当夹具的结论——一种安静的错答。
    判据取「空树 ⇒ 空结论」：把 `--root` 指向一个空临时目录，命令必须如实报空。
    """

    def _run(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = nf.main(list(argv))
        return code, out.getvalue()

    def test_declared_root_is_honored(self):
        with tempfile.TemporaryDirectory(prefix="nf_root_") as tmp:
            for argv, marker in (
                    (["asset", "ls", "--root", tmp], "货架为空"),
                    (["module", "ls", "--root", tmp], "合计 0"),
                    (["module", "verify", "--root", tmp], "模块 0"),
                    (["asset", "density", "--root", tmp], "资产文件 0"),
                    (["asset", "usage", "--root", tmp], "资产键 0"),
                    (["asset", "thickness", "--root", tmp], "资产档 0"),
                    (["asset", "inventory", "--root", tmp], "无 provenance"),
                    (["asset", "verify", "--root", tmp], "台账 0"),
                    (["design", "audit", "--root", tmp], "无 audit.md"),
                    (["design", "steelman", "--root", tmp], "无 steelman")):
                code, out = self._run(argv)
                self.assertEqual(0, code, (argv, out))
                self.assertIn(marker, out, "--root 未被兑现：%s" % (argv,))

    def test_non_directory_root_is_refused_not_answered(self):
        """`--root` 落点不在场 / 是文件 ⇒ 必须**拒**，不得对没有载体的树下肯定结论。

        实测缺口（2026-09-30，同族复扫）：`nf asset verify --root README.md` →
        「✓ 台账闭合：每资产可溯源 / 可发现 / 键无孤儿」、`nf module verify --root
        <不存在>` → 「✓ 无 deprecated/retired 模块被引用」——对**不存在的树**报绿，
        正是「看起来正常的错答」（同 `drill_fidelity`「标准不得无载体」）。空树体检
        （在场但空的目录）仍按 `test_declared_root_is_honored` 报空结论。
        """
        for argv in (["asset", "verify", "--root", "README.md"],
                     ["asset", "ls", "--root", "README.md"],
                     ["module", "verify", "--root", "README.md"],
                     ["asset", "verify", "--root", "__NF_NO_SUCH_ROOT__"]):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = nf.main(argv)
            text = out.getvalue() + err.getvalue()
            self.assertEqual(2, code, (argv, text))
            self.assertIn("--root 落点不是在场目录", text, (argv, text))
            self.assertIn("修复指引", text, (argv, text))
            self.assertNotIn("内部错误", text, argv)


class ParserBuildBudgetTest(unittest.TestCase):
    """建命令面的**固定成本**：不许走 gettext 探测（argparse 的内建 help 串会逐个翻译）。

    依据（2026-09-29 实测）：`argparse._` 是 `gettext.gettext`，每个内建 help 串（`-h` 的
    「show this help message and exit」之类）都要 `translation()` 一次、每次都去 stat locale
    目录——建一次 65 命令的面要 **432 次 → 0.11 s**，而本 CLI 不做本地化（help 全是中文字面量）。
    判据是**次数**（与机器快慢无关）：建面期间 `gettext.translation` 必须 0 次。
    """

    def test_parser_build_does_not_probe_gettext(self):
        import gettext
        seen = []
        real = gettext.translation
        gettext.translation = lambda *a, **k: (seen.append(a), gettext.NullTranslations())[1]
        saved = nf._PARSER_CACHE
        try:
            nf._PARSER_CACHE = None
            nf._build_parser()                 # 建面：翻译钩子必须已是恒等函数
        finally:
            gettext.translation = real
            nf._PARSER_CACHE = saved
        self.assertEqual([], seen,
                         "建命令面时仍在探测 gettext（每次 translation 都要 stat locale 目录）")


class VersionShortCircuitTest(unittest.TestCase):
    """`nf --version` 必须走**短路**：不许为打印一行版本号建整个 argparse 命令面。

    依据（2026-09-29 实测）：命令面构建 **99 ms**（65 条顶层命令 / 141 个子解析器），而
    `main()` 里早有 `argv == ["--version"]` 短路判据——但 `cli()` 原样转 `main(None)`，
    判据永远为假 ⇒ 每条 `nf --version`（最常被调用的探针命令，也是守护/启动器的探针形态）
    都白付这 99 ms。判据是**构建次数**（不是计时），与机器快慢无关。
    """

    def test_cli_version_does_not_build_the_command_face(self):
        calls = []
        real = nf._build_parser

        def counting(*a, **k):
            calls.append(1)
            return real(*a, **k)

        nf._build_parser = counting
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = nf.cli(["--version"])
        finally:
            nf._build_parser = real
        self.assertEqual(0, code)
        self.assertEqual([], calls,
                         "`nf --version` 建了命令面 ⇒ 短路判据失效（argv 没递进 main）")

    def test_cli_version_profile_has_no_command_face_build(self):
        """端到端那一条：profile 统计里不许出现命令面构建（抓「**入口**传 None」这个原缺陷）。

        `cli(["--version"])` 的进程内判据只证明短路本身可用；把入口改回 `cli()`，同一次
        profile 立刻出现 `_make_parser` / `add_subparsers`（实测 2 条）——故本判据必须端到端。
        """
        proc = subprocess.run(
            [sys.executable, "-m", "cProfile", "-s", "tottime",
             str(ROOT / "scripts" / "nf.py"), "--version"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        self.assertEqual(0, proc.returncode, proc.stderr[-400:])
        self.assertIn("nf 1.0.1", proc.stdout)
        self.assertNotIn("_make_parser", proc.stdout, "命令面被建了（入口没把 argv 递进去？）")
        self.assertNotIn("add_subparsers", proc.stdout, "命令面被建了（入口没把 argv 递进去？）")


if __name__ == "__main__":
    unittest.main()
