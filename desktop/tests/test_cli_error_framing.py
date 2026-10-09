# -*- coding: utf-8 -*-
"""CLI 错误框定判据：失败必须是**干净错误 + 修复指引**（错误即微型文档）。

扫法（2026-09-30 全命令面系统扫，65 命令 × 2 种畸形输入）：把每条命令喂「多余位置参数 /
未知开关」，凡 rc≠0 的输出里出现「内部错误」或**完全没有指引词**即计缺陷（argparse 的标准
用法错误按惯例除外）。扫出的余项已逐条修掉：`render`、`attest/lint/sig/state-front/
telemetry`、`impact`、`market`。本件把其中可稳定复跑的几处钉住（全量扫见 CHANGELOG 记录）。
"""
import re
import json
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NF = str(ROOT / "scripts" / "nf.py")

GUIDE = re.compile(r"修复指引|示例|详见|参见|可枚举|看全量")

#: (标签, argv 尾巴)——都在仓库内稳定可跑、且不落盘
CASES = (
    ("render 缺包目录", ("render", "__NF_PROBE__")),
    ("lint 目标不存在", ("lint", "__NF_PROBE__")),
    ("impact 目标不在册", ("impact", "__NF_PROBE__")),
    ("market 包不在册", ("market", "__NF_PROBE__")),
    ("st-validate 文件不存在", ("st-validate", "__NF_PROBE__")),
    ("state-front 文件不存在", ("state-front", "__NF_PROBE__")),
    ("telemetry 文件不存在", ("telemetry", "__NF_PROBE__")),
    ("library 条目不存在", ("library", "deprecate", "NO-SUCH-ID")),
    ("serve 快照不存在", ("serve", "__NF_PROBE__.json")),
    # 2026-09-30 补：`nf domain` 的输入错误此前冒成「内部错误」并回吐 `.rivet` 绝对路径
    ("domain 规格不存在", ("domain", "build", "--spec", "ZZZ")),
    ("domain 规格代码越界", ("domain", "build", "--spec", "../evil")),
    ("domain verify 规格不存在", ("domain", "verify", "--spec", "ZZZ")),
    # 2026-09-30 补：**类型不符**的输入（目录当文件用）——`bench run --case docs` 此前冒成
    # 「内部错误：[Errno 2] … <机器绝对路径>」，既错框定又回吐路径。
    ("bench 夹具缺 case.json", ("bench", "run", "--case", "docs")),
    # 2026-09-30 补：口径统一——目标不在册时 `who-refers` 此前回 rc=0「无（无人引用）」，
    # 那是**错的事实**（用户会把「查错名字」读成「没人引用」）；现在与 `nf impact` 同判据拒。
    ("who-refers 目标不在册", ("who-refers", "__NF_PROBE__")),
    # 2026-10-01 补：同族最后一处——`nf related <不在册目标>` 此前回 rc=0「关联条目：—」，
    # 同样是**错的事实**；现与 `nf impact` / `nf who-refers` 同一判据、同一指引。
    ("related 目标不在册", ("related", "__NF_PROBE__")),
    # 2026-10-01 补：文档示例真跑抓到——`nf worldmodel --run --state state.json` 此前抛
    # 裸 `[Errno 2] … 'state.json'` 冒成「内部错误」（技能参考里的原样示例）。
    ("worldmodel 状态件缺失", ("worldmodel", "--run", "--state", "__NF_PROBE__.json")),
)


def _run(argv):
    return subprocess.run([sys.executable, NF, *argv], capture_output=True,
                          encoding="utf-8", errors="replace", timeout=180)


class CliErrorFramingTest(unittest.TestCase):
    def test_json_failures_still_return_a_json_body(self):
        """机器面：带 `--json` 的命令在 **rc=1** 时 stdout 不得为空——必须是可解析 JSON。

        动机（机器面扫 2026-09-30）：32 条带 `--json` 的命令里 6 条运行失败时 stdout 全空，
        按 JSON 解析 stdout 的消费方会直接崩。修复后统一为 `{"ok": false, "error": …, "exit": N}`
        （`market` 等自带结构化形状者亦可，只要**是**合法 JSON）。
        """
        import json as _json
        for label, argv in (("sig", ("sig", "__NF_PROBE__", "--json")),
                            ("attest", ("attest", "__NF_PROBE__", "--json")),
                            ("lint", ("lint", "__NF_PROBE__", "--json")),
                            ("st-validate", ("st-validate", "__NF_PROBE__", "--json")),
                            ("state-front", ("state-front", "__NF_PROBE__", "--json")),
                            ("approve", ("approve", "__NF_PROBE__", "--json")),
                            # 2026-09-30 机器面复扫补：这四条此前 rc=1 时 stdout 全空
                            ("patterns show", ("patterns", "show", "ZZZ", "--json")),
                            ("decisions show", ("decisions", "show", "ZZZ", "--json")),
                            ("receipts entry", ("receipts", "--entry", "ZZZ", "--json")),
                            ("library show", ("library", "show", "ZZZ", "--json")),
                            ("domain build", ("domain", "build", "--spec", "ZZZ", "--json"))):
            p = _run(list(argv))
            self.assertEqual(1, p.returncode, label)
            out = (p.stdout or "").strip()
            self.assertTrue(out, "%s：--json 失败时 stdout 不得为空" % label)
            doc = _json.loads(out)          # 解析失败即判红
            self.assertIsInstance(doc, dict, label)

    def test_failures_are_clean_and_carry_guidance(self):
        for label, argv in CASES:
            p = _run(list(argv))
            text = (p.stdout or "") + (p.stderr or "")
            self.assertNotEqual(0, p.returncode, label)
            self.assertNotIn("内部错误", text, "%s：用户输入问题不得报成内部故障" % label)
            self.assertNotIn("NF_DEBUG", text, "%s：不该让用户去查堆栈" % label)
            self.assertRegex(text, GUIDE, "%s：失败必须带修复指引" % label)

    def test_guidance_regex_has_catch_power(self):
        """变异自证：无指引的裸错误必须被判红（否则本判据是空转）。"""
        self.assertIsNone(GUIDE.search("✗ 目标不存在：__NF_PROBE__"))
        self.assertIsNotNone(GUIDE.search("✗ 目标不存在：__NF_PROBE__（修复指引：…）"))

    def test_return_code_vocabulary_is_closed(self):
        """CLI 的退出码只许 0 / 1 / 2（0 成功 · 1 失败 · 2 用法或形状拒）。

        取证（2026-10-01 全量实测）：100 张面 ×（成功 + 多余位置参数 + 未知开关）= **300 次调用，
        退出码集合恰为 {0:86, 1:12, 2:202}，越界 0**。本件把源码里的**字面** `return <int>` 钉住
        （表达式型 return——如 `return 1 if issues else 0`——由上面那次实测覆盖）；将来若有人
        写出 `return 3`，这里会红。
        """
        import ast
        tree = ast.parse(Path(NF).read_text(encoding="utf-8"))
        lits = {n.value.value for n in ast.walk(tree)
                if isinstance(n, ast.Return) and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, int) and not isinstance(n.value.value, bool)}
        self.assertTrue(lits <= {0, 1, 2},
                        "出现 {0,1,2} 之外的退出码（契约：0 成功 / 1 失败 / 2 用法或形状拒）：%s"
                        % sorted(lits - {0, 1, 2}))
        self.assertTrue(lits, "没扫到字面 return（判据可能已失效）")

    def test_malformed_json_inputs_carry_guidance(self):
        """**坏 JSON 输入** ⇒ 可执行指引，且**不得 rc=0**（2026-10-01 全量扫）。

        取证三处：`nf score --baseline <坏件>`、`nf attest --verify <坏件>` 此前回吐裸解析错
        （`Expecting property name…`，零指引）——而同一命令的 `--exceptions` / `--out` 早有格式
        指引，属**同命令内两套口径**；更严重的是 `nf knowledge frequency --trace <坏件>`：
        坏文件被读成「0 源有事件」，**rc=0 静默错答**（读者会把「文件坏了」读成「这次没用知识源」）。
        """
        fd, bad = tempfile.mkstemp(suffix=".json", prefix="nf_bad_")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("{ 这不是合法 JSON\n")
        try:
            for label, argv in (("score --baseline", ("score", "--baseline", bad)),
                                ("attest --verify", ("attest", "--verify", bad)),
                                ("knowledge frequency",
                                 ("knowledge", "frequency", "--trace", bad))):
                p = _run(list(argv))
                text = (p.stdout or "") + (p.stderr or "")
                self.assertNotEqual(0, p.returncode,
                                    "%s：坏 JSON 不得 rc=0（静默错答）" % label)
                self.assertNotIn("Traceback", text, label)
                self.assertRegex(text, GUIDE, "%s：坏 JSON 必须带修复指引" % label)
        finally:
            os.unlink(bad)

    def test_unknown_pack_name_is_named_not_just_illegal(self):
        """不在册的包名要**点名**，不能只回一句「合法=False」（2026-10-01 恶意值扫取证）。

        与 `who-refers` / `related` / `impact` 同一口径：目标不在册时给可枚举的指引，
        否则读者分不清「包名打错了」与「真冲突」——机读面 `unknown_packs` 一直有，缺的是
        人读面把这条决定性事实说出来。
        """
        p = _run(["combine", "plan", "--packs", "__NF_PROBE__"])
        text = p.stdout + p.stderr
        self.assertNotEqual(0, p.returncode, text)
        self.assertIn("不在册的包", text, text)
        self.assertRegex(text, GUIDE, text)

    def test_json_success_paths_are_machine_readable(self):
        """成功面同规：**声明了 `--json` 的命令，成功时 stdout 也必须是可解析 JSON**。

        依据（2026-09-30 成功面复扫 28 条只读命令）：`layers --verify --json` 与
        `interop --list/--all --json` 三处 rc=0 却打的是散文——按 JSON 解析的消费方在
        **正常路径**上崩，比失败面更隐蔽（失败至少还能看退出码）。修后 21 条全绿。
        """
        import json as _json
        for argv in (("layers", "--verify", "--json"),
                     ("layers", "--json"),
                     ("interop", "--list", "--json"),
                     ("stats", "--json"),
                     # 2026-10-01 全量复扫补：这两条声明了 `--json` 却打散文
                     ("decisions", "reindex", "--json"),
                     ("patterns", "reindex", "--json")):
            p = _run(list(argv))
            out = (p.stdout or "").strip()
            self.assertTrue(out, "%s：--json 成功时 stdout 不得为空" % (argv,))
            doc = _json.loads(out)          # 解析失败即判红
            self.assertIsInstance(doc, dict, argv)

    def test_bare_shell_json_is_refused_not_blocking(self):
        """裸 `nf shell --json` 必须**明确拒**（rc=2 + 指引），不许把机器消费方送进交互会话。

        依据（2026-10-01 全量 `--json` 面复扫）：93 条声明 `--json` 的命令里有 4 条 rc=0 却打散文
        ——`decisions/patterns reindex`（上面已修）与 `shell/terminal` 裸跑。后者的风险更重：
        非 TTY（agent / CI / 管道）下进交互会话会**永久阻塞**，而消费方还在等 JSON。
        """
        p = _run(["shell", "--json"])
        text = (p.stdout or "") + (p.stderr or "")
        self.assertEqual(2, p.returncode, text)
        self.assertIn("交互终端", text)
        self.assertIn("修复指引", text)


class ShapeMismatchTest(unittest.TestCase):
    """形状不符（目录当文件用 / 非 JSON 当 JSON 用）必须是干净错误 + 指引。

    2026-09-30 扫法（只读取证）：对「收文件」的只读命令喂在场**目录** `docs`（在仓库根
    跑），此前 `attest` / `sig` / `diff` / `bench compare|report` / `postmortem check` /
    `knowledge frequency --trace` 一律抛
    `[Errno 13] Permission denied: '<作者机绝对路径>'`——既无修复指引、又回吐机器路径；
    `st-validate` 喂在场非 JSON 则只回裸解析错误。修后一律「干净错误 + 指引 + 零机器路径」。
    """

    def _run_at_root(self, argv):
        return subprocess.run([sys.executable, NF, *argv], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=180,
                              cwd=str(ROOT))

    def _check(self, label, argv):
        """失败三要件：rc≠0、干净（无「内部错误」/`NF_DEBUG`/裸 `Errno`/机器路径）、带指引。"""
        p = self._run_at_root(list(argv))
        text = (p.stdout or "") + (p.stderr or "")
        self.assertNotEqual(0, p.returncode, "%s：%s" % (label, text))
        self.assertNotIn("内部错误", text, "%s：用户输入问题不得报成内部故障" % label)
        self.assertNotIn("NF_DEBUG", text, label)
        self.assertNotRegex(text, r"Errno", "%s：不得回吐 OS 层裸错误" % label)
        self.assertNotIn(str(ROOT), text, "%s：不得回吐机器绝对路径" % label)
        self.assertRegex(text, GUIDE, "%s：失败必须带修复指引" % label)

    def test_directory_as_file_targets_are_clean_and_guided(self):
        for label, argv in (("attest", ("attest", "docs")),
                            ("attest --verify", ("attest", "--verify", "docs")),
                            ("sig", ("sig", "docs")),
                            ("diff", ("diff", "docs", "docs")),
                            ("bench compare", ("bench", "compare", "docs")),
                            ("bench report", ("bench", "report", "docs")),
                            ("postmortem check", ("postmortem", "check", "docs")),
                            ("knowledge frequency", ("knowledge", "frequency",
                                                     "--trace", "docs"))):
            self._check(label, argv)

    def test_non_json_file_is_a_clean_error(self):
        self._check("st-validate 非 JSON", ["st-validate", "README.md"])

    def test_file_given_where_a_case_dir_is_expected(self):
        """`--case` 收**文件**（非 case.json）此前过 is_file 检查，到解析才抛裸 JSON 错。"""
        self._check("bench run --case <文件>",
                    ["bench", "run", "--case", "README.md"])

    def test_other_argv_path_shapes_are_clean(self):
        """同族扫的另一批：`decide --state/--questions`、`assemble --save` 的路径形状。"""
        self._check("decide --state <目录>",
                    ["decide", "--state", "docs", "--questions", "docs"])
        self._check("decide --questions <非 JSON>",
                    ["decide", "--state-text", "x", "--questions", "README.md"])
        self._check("assemble --save <目录>",
                    ["assemble", "x", "--save", "docs"])

    def test_report_style_and_module_shape_failures_are_clean(self):
        """轮询式检查命令的「目标不在场」也必须带指引（2026-10-01 二批）。

        此前 `nf audit check <目录>` / `nf handover check <目录>` 只吐一行 `[FAIL] …不存在`
        （**零指引**）；`nf output check <目录>` 同型；`nf module status <目录>` 则回吐
        `[Errno 13] …` 这样的 **OS 层裸错误**（带指引但框定不干净）。四处已按同一口径收口。
        """
        for label, argv in (("module status <目录>", ["module", "status", "docs"]),
                            ("audit check <目录>", ["audit", "check", "docs"]),
                            ("handover check <目录>", ["handover", "check", "docs"]),
                            ("output check <目录>", ["output", "check", "docs"])):
            self._check(label, argv)

    def test_registry_keyfile_baseline_artifact_shapes_are_clean(self):
        """同族扫第三批：`--registry`/`--key-file`/`--baseline`/`--artifact` 的形状。

        `--registry` 有 7 个声明点（market/spec/register/who-refers/impact/related/release），
        入口判一次即全覆盖（目录落点、非 JSON 件两形态）。
        """
        case = "desktop/tests/fixtures/benchmark/suite/p02-campus-emotion"
        for label, argv in (("who-refers --registry <目录>",
                             ["who-refers", "M00", "--registry", "docs"]),
                            ("impact --registry <目录>",
                             ["impact", "M00", "--registry", "docs"]),
                            ("market --list --registry <非 JSON>",
                             ["market", "--list", "--registry", "README.md"]),
                            ("spec --registry <非 JSON>",
                             ["spec", "ls", "--registry", "README.md"]),
                            ("register --registry <非 JSON>",
                             ["register", "community/技术文档域包",
                              "--registry", "README.md"]),
                            ("related --registry <非 JSON>",
                             ["related", "M00", "--registry", "README.md"]),
                            ("attest --key-file <目录>",
                             ["attest", "README.md", "--key-file", "docs"]),
                            ("library verify --key-file <缺失>",
                             ["library", "verify", "--key-file", "__NF_PROBE__"]),
                            ("score --baseline <目录>",
                             ["score", "--baseline", "docs"]),
                            ("bench run --artifact <目录>",
                             ["bench", "run", "--case", case,
                              "--artifact", "docs"])):
            self._check(label, argv)

    def test_out_pointing_at_a_directory_is_a_clean_error(self):
        """`--out` 指向**目录**：此前或冒「内部错误 + 机器路径」，或回裸 `Errno`（无指引）。"""
        case = "desktop/tests/fixtures/benchmark/suite/p02-campus-emotion"
        for label, argv in (("bench run --out <目录>",
                             ["bench", "run", "--case", case, "--out", "docs"]),
                            ("attest --out <目录>",
                             ["attest", "README.md", "--out", "docs"]),
                            ("st-validate --out <目录>",
                             ["st-validate",
                              "desktop/tests/fixtures/external/chara.json",
                              "--out", "docs"]),
                            ("interop --kind --out <目录>",
                             ["interop", "--kind", "openapi", "--out", "docs"])):
            self._check(label, argv)

    def test_dest_pointing_at_a_file_is_a_clean_error(self):
        """`--dest` 收**目录**，喂文件时必须干净拒（2026-10-01 二批）。

        此前 `nf render --dest <文件>` 与 `nf demo --dest <文件>` 冒
        「内部错误：[WinError 183] … '<机器绝对路径>'」，`nf assemble --build --dest <文件>`
        也回裸 OS 错误（有指引但框定不干净、且回吐机器路径）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            f = str(Path(tmp, "afile.md"))
            Path(f).write_text("x", encoding="utf-8", newline="\n")
            for label, argv in (
                    ("render --dest <文件>",
                     ["render", "community/技术文档域包", "--dest", f]),
                    ("demo --dest <文件>", ["demo", "--dest", f]),
                    ("assemble --build --dest <文件>",
                     ["assemble", "西幻生存+生存+单世界", "--build", "--dest", f])):
                self._check(label, argv)

    def test_other_file_flags_have_shape_gates(self):
        """`--exceptions` / `--out`（steelman init）/ `--file`（shell）的落点形状（2026-10-01 三批）。

        此前：`nf score --exceptions <目录|缺失>` 抛裸 `[Errno 13]`/`[Errno 2]`（零指引）；
        `nf design steelman init … --out <目录>` 与 `nf shell --file <目录>` 冒「内部错误」，
        后者还配一句「确认路径存在后重试」——对一个**确实存在**的目录说「不存在」。
        """
        with tempfile.TemporaryDirectory() as tmp:
            f = str(Path(tmp, "afile.md"))
            Path(f).write_text("x", encoding="utf-8", newline="\n")
            for label, argv in (
                    ("score --exceptions <目录>",
                     ["score", "--exceptions", "docs"]),
                    ("score --exceptions <非 JSON 文件>",
                     ["score", "--exceptions", f]),
                    ("design steelman init --out <目录>",
                     ["design", "steelman", "init", "问题", "--out", "docs"]),
                    ("shell --file <目录>", ["shell", "--file", "docs"])):
                self._check(label, argv)


class PathFlagWritingGateTest(unittest.TestCase):
    """收路径旗标的**写法闸门**：相对写法不得用 `..` / 盘符逃出仓库，绝对路径仍按原样放行。

    依据（2026-10-01 实测）：`nf interop --kind openapi --out ../x.json` 真的**写到了仓库外**
    （`_rel_out` 只做 `os.path.join`），而且报成「✗ 内部错误」（用户输入问题被框成内部故障）。
    相对路径的语义是「相对**仓库根**」，那就与 `core.paths.validate_path` 同一条包含性判据：
    `..` 段 / 盘符相对写法一律拒，要落到仓库外请给**绝对路径**（写清楚，不靠 `..` 猜）。
    """

    def test_helper_refuses_escape_forms_and_keeps_legit(self):
        nf = _load_nf()

        class _Args:
            out = ""

        a = _Args()
        # 反斜杠形态（2026-10-01 补）：Windows 上 `\` 是真分隔符而非转义字符，同一段逃逸写成
        # `..\x.json` 必须一样被拒；`validate_path` 先把 `\` 归一成 `/` 再查 `..` 段，
        # 故这条断言在 Windows 与 Linux 上都成立（不靠平台碰巧）。
        for bad in ("../x.json", "a/../../b.md", "C:foo.md",
                    "..\\x.json", "a\\..\\..\\b.md", "samples\\..\\..\\b.md"):
            a.out = bad
            issue = nf._path_writing_issue(a)
            self.assertIn("越界", issue, "%r 应被判越界写法" % bad)
            self.assertIn("修复指引", issue)
        # 反向（不许误杀）：仓内反斜杠相对路径解析后仍在根内 ⇒ 放行。
        for ok in ("docs/x.md", "x.json", str(Path(ROOT) / "x.json"), "docs\\x.md"):
            a.out = ok
            self.assertEqual("", nf._path_writing_issue(a),
                             "%r 属合法写法（绝对路径按原样放行）" % ok)

    def test_cli_refuses_relative_escape_without_writing_outside(self):
        """真跑一条：干净拒绝 + 带指引 + **仓外不落件**。"""
        outside = Path(ROOT).parent / "nf_escape_probe_test.json"
        self.assertFalse(outside.exists(), "用例开始前仓外就已有同名件，先清理")
        r = subprocess.run([sys.executable, NF, "interop", "--kind", "openapi",
                            "--out", "../nf_escape_probe_test.json"],
                           cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        self.assertNotEqual(0, r.returncode, "越界相对写法必须拒")
        self.assertIn("修复指引", r.stderr)
        self.assertNotIn("内部错误", r.stderr, "用户输入问题不得框成内部错误")
        self.assertFalse(outside.exists(), "越界写法竟然落件到仓库外")

    @unittest.skipUnless(os.name == "nt", "反斜杠当分隔符只在 Windows 上成立")
    def test_cli_refuses_backslash_escape_without_writing_outside(self):
        """Windows 原生写法：`..\\` 与 `../` 同等拒收（本仓 agent 密集面就在 Windows 上跑）。"""
        outside = Path(ROOT).parent / "nf_escape_probe_bs_test.json"
        self.assertFalse(outside.exists(), "用例开始前仓外就已有同名件，先清理")
        r = subprocess.run([sys.executable, NF, "interop", "--kind", "openapi",
                            "--out", "..\\nf_escape_probe_bs_test.json"],
                           cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300)
        self.assertNotEqual(0, r.returncode, "越界反斜杠写法必须拒")
        self.assertIn("修复指引", r.stderr)
        self.assertNotIn("内部错误", r.stderr, "用户输入问题不得框成内部错误")
        self.assertFalse(outside.exists(), "越界写法竟然落件到仓库外")


class PathFlagCoverageTest(unittest.TestCase):
    """写法闸门的旗标名单**不得漏面**：argparse 面里收路径的旗标要么在名单里、要么在豁免表里。

    依据（2026-10-01）：名单是从「help 含路径类词」的旗标里人工剔出来的，而**名单自身没有判据**
    ——加一个新的收路径旗标不会有人想起补进来，于是它又回到「`..` 静默逃出仓库」的老路。本件把
    「名单 ⇄ 真实参数面」钉在一起，并给豁免项逐条写明为什么不是路径。
    """

    #: 被 help 判成「路径类」但**不是路径**的参数 → 理由（逐条点名）。
    FREE_TEXT_EXEMPT = {
        "name": "--name 是显示名（预设名 / 管线名），不是落点",
        "entry": "--entry 是馆藏编号（NF-1 这类标识符）",
        "source": "--source 是溯源说明**文字**（写进台账，不是路径）",
        "write": "--write 是布尔旗标（无取值，故不参与写法判定）",
    }
    PATHISH = re.compile(r"文件|路径|目录|JSON|快照|密钥|信封")

    def _dests(self):
        import argparse
        nf = _load_nf()
        out = {}
        def walk(p):
            for a in p._actions:
                if isinstance(a, argparse._SubParsersAction):
                    for sub in a.choices.values():
                        walk(sub)
                elif a.option_strings:
                    out.setdefault(a.dest, {
                        "bool": isinstance(a, (argparse._StoreTrueAction,
                                               argparse._StoreFalseAction)),
                        "help": str(a.help or "")})
        walk(nf._build_parser())
        return nf, out

    def test_every_pathish_flag_is_covered_or_exempt(self):
        nf, dests = self._dests()
        listed = set(nf._PATH_FLAG_DESTS)
        pathish = {d for d, v in dests.items()
                   if self.PATHISH.search(v["help"]) and not v["bool"]}
        self.assertGreater(len(pathish), 15, "没扫到路径类旗标（判据可能已失效）")
        orphan = sorted(pathish - listed - set(self.FREE_TEXT_EXEMPT))
        self.assertEqual([], orphan,
                         "收路径的旗标没进写法闸门名单（`..` 会静默逃出仓库）：%s"
                         "（修复指引：加进 scripts/nf.py 的 _PATH_FLAG_DESTS，"
                         "或写进本件 FREE_TEXT_EXEMPT 说明它不是路径）" % orphan)

    def test_listed_dests_still_exist(self):
        """名单不得腐烂：写进名单的 dest 要真在参数面里（改了名就该同步）。"""
        nf, dests = self._dests()
        stale = sorted(d for d in nf._PATH_FLAG_DESTS if d not in dests)
        self.assertEqual([], stale, "写法闸门名单里有不存在的参数（改名后没同步）：%s" % stale)

    def test_exemptions_are_not_stale(self):
        """豁免不得腐烂：豁免的名字若已不在面内，或已变成布尔旗标，就该从豁免表划掉。"""
        _nf, dests = self._dests()
        stale = sorted(k for k in self.FREE_TEXT_EXEMPT if k not in dests)
        self.assertEqual([], stale, "豁免表里有已消失的参数：%s" % stale)

    def test_encoding_gate_covers_every_textish_dest(self):
        """**编码闸门的名单也是对账出来的**：argparse 面里自称收文本的参数，要么过闸、要么豁免。

        依据（2026-10-01 三批普查）：该闸门的手写名单曾两次漏网——第一批漏 `import` / `run` 等 5 条
        命令的**位置参数**写法，第二批又漏 `path` / `paths` 这两种 dest 名（同一概念换个参数名就
        漏出闸门）。故名单改成「运行时枚举（help 自称文本类）+ 逐条豁免（二进制 / 写侧落点）」，
        并由本判据保证枚举与名单**一一对齐**：新加一个自称收文本的参数却不进闸，这里就红。
        """
        import argparse
        nf = _load_nf()
        textish = re.compile("文件|路径|JSON|md|信封|快照|规则|脚本|台账|清单")
        dests = {}
        def walk(p):
            for a in p._actions:
                if isinstance(a, argparse._SubParsersAction):
                    for sub in a.choices.values():
                        walk(sub)
                elif (a.option_strings or (a.dest and a.dest != "cmd")):
                    if textish.search(str(a.help or "")) and not isinstance(
                            a, (argparse._StoreTrueAction, argparse._StoreFalseAction)):
                        dests[a.dest] = ",".join(a.option_strings) or "<%s>" % a.dest
        walk(nf._build_parser())
        self.assertGreater(len(dests), 30, "没枚举到文本类参数（判据可能已失效）")
        #: 写侧落点（目标而非被读内容）——与「二进制」两类之外**不得**再有豁免
        write_targets = {"out", "dest", "dst", "session_path", "write", "save_path", "build_dest",
                         "store"}
        gated = set(nf._UTF8_TEXT_DESTS) | set(nf._UTF8_BINARY_EXEMPT) | write_targets
        orphan = sorted(d for d in dests if d not in gated)
        self.assertEqual([], orphan,
                         "自称收文本的参数没进编码闸门（非 UTF-8 时仍会冒内部错误）：%s"
                         "（修复指引：加进 scripts/nf.py 的 _UTF8_TEXT_DESTS，"
                         "或写进 _UTF8_BINARY_EXEMPT / write_targets 说明为什么豁免）" % orphan)
        # 反向：名单里的 dest 必须真存在（改名后不同步即红）
        all_dests = set()
        def collect(p):
            for a in p._actions:
                if isinstance(a, argparse._SubParsersAction):
                    for sub in a.choices.values():
                        collect(sub)
                else:
                    all_dests.add(a.dest)
        collect(nf._build_parser())
        stale = sorted(d for d in nf._UTF8_TEXT_DESTS if d not in all_dests)
        self.assertEqual([], stale, "编码闸门名单里有不存在的参数（改名后没同步）：%s" % stale)


def _load_nf():
    spec = importlib.util.spec_from_file_location("nfcli_framing", NF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ShapeGateHelperTest(unittest.TestCase):
    """形状闸门 helper 的变异自证：空值/在场文件通过；目录与缺失判红；bool 旗标不受影响。"""

    def test_file_shape_issue(self):
        nf = _load_nf()
        self.assertEqual("", nf._file_shape_issue("", "--x", "g"))
        self.assertEqual("", nf._file_shape_issue(None, "--x", "g"))
        self.assertEqual("", nf._file_shape_issue("README.md", "--x", "g"))
        self.assertNotEqual("", nf._file_shape_issue("docs", "--x", "g"))
        self.assertNotEqual("", nf._file_shape_issue("__NF_PROBE__", "--x", "g"))
        # `nf shell --baseline` 是 **store_true**（布尔），绝不能被当成路径判红
        self.assertEqual("", nf._file_shape_issue(True, "--x", "g"))

    def test_existing_nonfile_issue_allows_missing_path(self):
        nf = _load_nf()
        self.assertEqual("", nf._existing_nonfile_issue("__NF_PROBE__", "--x", "g"))
        self.assertNotEqual("", nf._existing_nonfile_issue("docs", "--x", "g"))


class MachinePathRedactionTest(unittest.TestCase):
    """兜底脱敏必须真削掉**机器绝对路径**——含 Windows OSError 的**双写反斜杠**形态。

    实测（2026-09-30）：`str(OSError)` 走文件名 repr，Windows 下路径里的 `\\` 会变成 `\\\\`，
    只削单写版会**静默漏掉**（`nf diff <目录>` 实测仍在回吐作者机路径）。本判据钉住两种写法。
    """

    def test_windows_oserror_repr_is_redacted(self):
        nf = _load_nf()
        msg = str(OSError(13, "Permission denied", os.path.join(nf.ROOT, "docs")))
        out = nf._no_machine_paths(msg)
        self.assertNotIn(str(nf.ROOT), out, out)
        self.assertIn("docs", out, out)

    def test_plain_absolute_path_is_redacted(self):
        nf = _load_nf()
        p = os.path.join(nf.ROOT, "docs", "x.md")
        self.assertNotIn(nf.ROOT, nf._no_machine_paths("失败：%s（无指引）" % p))


class CwdIndependenceTest(unittest.TestCase):
    r"""**收路径的命令不依赖进程 cwd**（口径：仓库相对路径一律相对仓库根）。

    实测缺口（2026-10-01）：`_rel_to_root` 用 `os.path.abspath(target)` ⇒ 相对路径按**进程
    cwd** 解析，而同一份 CLI 的写盘侧 `_rel_out` 是**仓根**语义——同一口径两套实现。从
    `desktop/` 里跑，`nf sig 01_核心协议.md` 报「目标不存在」（文件明明在仓根）、
    `nf attest --verify <仓外绝对件>` 报 `[Errno 2] ..\..\AppData\…`（把绝对路径改写成仓相对后
    又按 cwd 打开）。本件从**非仓根 cwd** 跑这几条，钉住「相对=仓根、绝对=原样」。
    """

    def _run_from(self, cwd, argv):
        return subprocess.run([sys.executable, NF, *argv], capture_output=True,
                              encoding="utf-8", errors="replace",
                              cwd=str(cwd), timeout=180)

    def test_repo_relative_paths_work_from_a_subdirectory(self):
        cwd = ROOT / "desktop"
        for argv in (("sig", "01_核心协议.md"),
                     ("diff", "01_核心协议.md", "01_核心协议.md"),
                     # 2026-10-01 三批补：这两条此前把「相对路径」按 cwd 解析
                     # （`bench --case` 用 `os.path.abspath`、`st-validate` 把原串直接递给
                     # 校验器去 open），从 `desktop/` 里跑仓内路径必判失败。
                     ("bench", "run", "--case",
                      "desktop/tests/fixtures/benchmark/suite/p03-western-cross"),
                     ("st-validate", "desktop/tests/fixtures/external/chara.json")):
            p = self._run_from(cwd, argv)
            self.assertEqual(0, p.returncode, "%s：%s" % (argv, p.stdout + p.stderr))

    def test_absolute_paths_outside_the_repo_still_resolve(self):
        fd, env_file = tempfile.mkstemp(suffix=".json", prefix="nf_env_")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write('{"schema": "nf-attest/1"}\n')
        try:
            p = self._run_from(ROOT / "desktop", ("attest", "--verify", env_file))
            text = p.stdout + p.stderr
            self.assertNotIn("[Errno", text, "绝对路径被误按 cwd 打开：%s" % text)
            self.assertNotIn("目标不存在", text, text)
        finally:
            os.unlink(env_file)

    def test_relative_path_flags_behave_the_same_from_any_cwd(self):
        """收**相对路径**的旗标不许因 cwd 改变结论（2026-10-01 全量扫 96 组合后收口）。

        实测缺口：`attest --key-file <相对>` 与 `worldmodel --state <相对>` 此前按 **cwd** 解析，
        而各自命令内的**形状闸门**按仓根判 ⇒ 同一命令两条路径不同源：闸门放行、读取失败，
        从仓外 cwd 跑必然误判「文件不存在」。修后两者与闸门同源（相对 = 仓库根）。
        """
        cwd = ROOT / "desktop"
        for argv in (("attest", "docs/terminal.md", "--key-file", "docs/terminal.md"),
                     ("worldmodel", "--run", "--state", "docs/terminal.md")):
            a = self._run_from(ROOT, argv)
            b = self._run_from(cwd, argv)
            self.assertEqual(a.returncode, b.returncode,
                             "%s 换 cwd 结论变了：root=%d cwd=%d"
                             % (" ".join(argv), a.returncode, b.returncode))

    def test_relative_out_and_store_land_under_repo_root(self):
        """相对 `--out` / `--store` 按**仓库根**解析（与 `--dest` / `--root` 同一口径）。

        实测缺口（2026-10-01）：从临时 cwd 跑，`nf interop --kind openapi --out rel.json` 与
        `nf preset save … --store relstore` 都**落在 cwd**；而其余面的 `--out`（经 `_rel_out`）
        与 `--root` 都是仓根语义——同名概念两套解析，读者无法预测落点。修后两者都落到仓根。
        """
        import shutil
        rel_out = ".rivet/scratch/_cwd_probe_out.json"
        rel_store = ".rivet/scratch/_cwd_probe_store"
        with tempfile.TemporaryDirectory() as tmp:
            try:
                p = subprocess.run([sys.executable, NF, "interop", "--kind", "openapi",
                                    "--out", rel_out], cwd=tmp, capture_output=True,
                                   encoding="utf-8", errors="replace", timeout=300)
                self.assertEqual(0, p.returncode, p.stdout + p.stderr)
                q = subprocess.run([sys.executable, NF, "preset", "save", "口径探针",
                                    "--store", rel_store, "--pipeline", "P01"], cwd=tmp,
                                   capture_output=True, encoding="utf-8",
                                   errors="replace", timeout=300)
                self.assertEqual(0, q.returncode, q.stdout + q.stderr)
                self.assertTrue((ROOT / rel_out).is_file(), "相对 --out 没落到仓库根")
                self.assertFalse((Path(tmp) / rel_out).exists(), "相对 --out 落到了 cwd")
                self.assertTrue((ROOT / rel_store / "presets").is_dir(),
                                "相对 --store 没落到仓库根")
                self.assertFalse((Path(tmp) / rel_store).exists(), "相对 --store 落到了 cwd")
            finally:
                (ROOT / rel_out).unlink(missing_ok=True)
                shutil.rmtree(ROOT / rel_store, ignore_errors=True)


class StorePlacementTest(unittest.TestCase):
    """`--store` 落**仓库内且未忽略**时必须拒（用户态工作区不该变成 git 垃圾）。

    依据（2026-10-01 探针）：`--store out_probe` 会在仓库里建出
    `out_probe/{assets,cache,modules,presets}`（实测 rc=0），直接成为 `git status` 的未跟踪垃圾——
    与 `trace.json` / `docs/meta/档案.md` 那类残留同一类，还可能被误提交。仓库自己的约定是**已忽略的**
    `.rivet/scratch/…`（既有用例正落在那儿），故闸门只拦「仓内 + 未忽略」这一种。
    """

    def test_unignored_in_repo_store_is_refused(self):
        target = "out_probe_nf_store"
        self.assertFalse((ROOT / target).exists(), "用例开始前就有同名目录，先清掉再跑")
        r = _run(["preset", "ls", "--store", target, "--json"])
        self.assertNotEqual(0, r.returncode, "仓内未忽略的 --store 必须拒")
        blob = (r.stderr or "") + (r.stdout or "")
        self.assertIn("修复指引", blob)
        self.assertIn("gitignore", blob, "指引须点明忽略面这条出路")
        import json as _json
        self.assertIsInstance(_json.loads((r.stdout or "").strip()), dict,
                              "失败时机器面仍须是 JSON 体")
        self.assertFalse((ROOT / target).exists(), "拒了却还是把目录建出来了")

    def test_ignored_in_repo_store_is_accepted(self):
        """反例对照：**已忽略**的仓内落点（仓库自己的 `.rivet/scratch/` 约定）必须照常放行。"""
        import shutil
        target = ROOT / ".rivet" / "scratch" / "nf_store_probe"
        try:
            r = _run(["preset", "ls", "--store", str(target)])
            self.assertEqual(0, r.returncode, (r.stderr or "")[:200])
            self.assertTrue((target / "presets").is_dir(), "已忽略落点应当正常建库")
        finally:
            shutil.rmtree(target, ignore_errors=True)

    def test_outside_repo_store_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = _run(["preset", "ls", "--store", tmp])
            self.assertEqual(0, r.returncode, (r.stderr or "")[:200])
            self.assertTrue((Path(tmp) / "presets").is_dir())


class StorePathShapeTest(unittest.TestCase):
    """`--store` 指向**文件**时必须给干净错误 + 指引（不得冒成内部错误 + 回吐机器路径）。

    实测缺口（2026-09-30）：Store() 会落到 `_ensure_dirs()` 的 mkdir 抛 WinError 183，
    冒到 CLI 兜底报「内部错误」——那是**用户输入问题（落点形状不符）**，不是内部故障。
    修复后 `Store.__init__` 在 mkdir 前先判形状，CLI 两处 `Store(...)` 包 ValueError。
    """

    def test_store_pointing_at_a_file_is_a_clean_error(self):
        chara = ROOT / "desktop" / "tests" / "fixtures" / "external" / "chara.json"
        self.assertTrue(chara.is_file(), "夹具不在场")
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp, "not-a-dir.txt")
            f.write_text("x", encoding="utf-8", newline="\n")
            p = _run(["import", str(chara), "--register", "--store", str(f)])
        text = (p.stdout or "") + (p.stderr or "")
        self.assertNotEqual(0, p.returncode, text)
        self.assertNotIn("内部错误", text, "落点形状不符不得报成内部故障")
        self.assertNotIn("NF_DEBUG", text)
        self.assertRegex(text, GUIDE, "落点形状不符必须带修复指引")

    def test_unusable_nf_home_is_a_clean_error_for_every_store_face(self):
        """NF_HOME **不可用**（盘符不存在 / 落点是文件）时，三张要 store 的面都必须干净拒绝。

        实测缺口（2026-10-01）：`NARRATIVE_FORGE_HOME=Z:\\nope` 时 `nf preset ls` / `nf demo` /
        `nf run --seed` 全冒到 CLI 兜底报「✗ **内部错误**：[WinError 3] …（重跑 NF_DEBUG=1 看
        堆栈）」——用户配置问题被框成内部故障、零指引。根因两半：既有守卫只捕 `ValueError`
        （形状），漏了 `OSError`（盘/权限）；`demo` / `preset` 则根本没守卫。既有用例只覆盖了
        `--store <文件>` 一条路径，故漏掉了它。
        """
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp, "not-a-dir.txt")
            f.write_text("x", encoding="utf-8", newline="\n")
            for argv in (["preset", "ls"], ["demo"],
                         ["run", "--pipeline", "P00", "--modules", "通用类:M00", "--seed"]):
                p = subprocess.run([sys.executable, NF, *argv], capture_output=True,
                                   encoding="utf-8", errors="replace", cwd=str(ROOT),
                                   env=dict(os.environ, NARRATIVE_FORGE_HOME=str(f)), timeout=300)
                text = (p.stdout or "") + (p.stderr or "")
                self.assertNotEqual(0, p.returncode, "%s：%s" % (argv, text))
                self.assertNotIn("内部错误", text, "%s 把用户配置问题报成内部故障" % argv)
                self.assertNotIn("NF_DEBUG", text, argv)
                self.assertRegex(text, GUIDE, "%s：须带修复指引" % argv)


class StoreFileNameBoundTest(unittest.TestCase):
    """**用户输入变成文件名时必须限长**：超长名字不得把落盘炸成「内部错误 + 机器路径」。

    依据（2026-10-01 敌意输入普查：150 条命令路径 × {未知位置参数, 4096 字符值}）：唯一命中是
    `nf preset save <4096 个 A>` —— `Store._safe_name` 只做字符替换、不限长 ⇒ 文件名超过文件系统
    上限 ⇒ `open` 抛 `[Errno 2]`，冒到 CLI 兜底报「✗ 内部错误」**且回吐机器绝对路径**。
    修法是「截断 + 原文摘要后缀」（确定性、不撞名），本件把三件事钉住：能存下、名字有界、
    逻辑名保真（`preset ls` 仍能按原名找到）；另加两条不变式：同名幂等、不同长名不撞件。
    """

    def _home(self):
        home = tempfile.mkdtemp(prefix="nf_longname_")
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        return home

    def test_overlong_preset_name_is_stored_with_a_bounded_file_name(self):
        home = self._home()
        env = dict(os.environ, NARRATIVE_FORGE_HOME=home)
        long_name = "A" * 4096
        r = subprocess.run([sys.executable, NF, "preset", "save", long_name,
                            "--pipeline", "P01"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, cwd=str(ROOT), timeout=300)
        self.assertEqual(0, r.returncode, (r.stderr or "")[:200])
        self.assertNotIn("内部错误", (r.stderr or "") + (r.stdout or ""))
        files = sorted((Path(home) / "presets").glob("*.json"))
        self.assertEqual(1, len(files), "应当正好落一件")
        self.assertLessEqual(len(files[0].name), 160, "文件名必须有界")
        ls = subprocess.run([sys.executable, NF, "preset", "ls"], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env=env, cwd=str(ROOT), timeout=300)
        self.assertIn("A" * 50, ls.stdout, "逻辑名必须保真（否则用户找不到自己存的预设）")

    def test_long_names_are_idempotent_and_collision_free(self):
        home = self._home()
        env = dict(os.environ, NARRATIVE_FORGE_HOME=home)
        a, b = "B" * 300, "B" * 299 + "C"
        for _ in range(2):                      # 同名两次 ⇒ 同一件（幂等）
            subprocess.run([sys.executable, NF, "preset", "save", a, "--pipeline", "P01"],
                           capture_output=True, env=env, cwd=str(ROOT), timeout=300)
        subprocess.run([sys.executable, NF, "preset", "save", b, "--pipeline", "P01"],
                       capture_output=True, env=env, cwd=str(ROOT), timeout=300)
        files = sorted(p.name for p in (Path(home) / "presets").glob("*.json"))
        self.assertEqual(2, len(files), "截断后不同长名撞成同一个文件了：%s" % files)


class BareInvocationSweepTest(unittest.TestCase):
    """**每条命令路径无参直跑一次**，不得冒「内部错误 / Traceback」。

    依据（2026-10-01 普查，本判据当场抓到 3 处）：无参直跑是最常见的调用形态（agent 试错、补全、
    人敲一半就回车），而 `nf combine` / `nf domain` / `nf output` 三条子命令组**漏了
    `add_subparsers(required=True)`** ⇒ 无参时 handler 去读还不存在的属性（`args.packs` /
    `args.json`）⇒ AttributeError 冒到兜底报「✗ 内部错误：'Namespace' object has no attribute …」。
    同类命令（`daemon` / `asset` / `module` / `pipeline` / `design` / `bench`）都声明了 required，
    故这里取同一口径：**无参跑出 argparse usage（rc=2）是正常**，判红只认「内部错误」或 Python 栈。
    """

    #: 无参即跑**全量门禁**的命令 → 理由（按设计的长任务，不是挂起）
    LONG_BY_DESIGN = {"release": "无参即跑 verify.sh 全量（本机 ~10 分钟）——按设计，跳过"}

    def test_bare_invocation_never_crashes(self):
        inv = subprocess.run([sys.executable, NF, "shell", "--commands", "--json"],
                             cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=300)
        rows = json.loads(inv.stdout).get("rows") or []
        self.assertGreaterEqual(len(rows), 140, "命令面清单异常（判据可能已失效）")
        bad, checked = [], 0
        for row in rows:
            path = row["path"]
            if path.split()[0] in self.LONG_BY_DESIGN:
                continue
            checked += 1
            try:
                r = subprocess.run([sys.executable, "-X", "utf8", NF, *path.split()],
                                   cwd=str(ROOT), capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=120,
                                   stdin=subprocess.DEVNULL)
            except subprocess.TimeoutExpired:
                bad.append("%s：无参直跑超时（挂起？如属长任务请登记 LONG_BY_DESIGN）" % path)
                continue
            blob = (r.stderr or "") + (r.stdout or "")
            if "内部错误" in blob or "Traceback" in blob:
                bad.append("%s：rc=%d %s" % (path, r.returncode,
                                             (r.stderr or "").strip().splitlines()[:1]))
        self.assertGreaterEqual(checked, 140, "扫到的命令路径不足（判据可能已失效）")
        self.assertEqual([], bad, "无参直跑冒内部错误/栈（修复指引：给该子命令组加 "
                                 "`add_subparsers(required=True)`，或在 handler 里给用法指引）：%s" % bad)

    def test_bare_json_invocation_stays_machine_readable(self):
        """同一普查的**机器面**版本：声明了 `--json` 的面无参 + `--json` 直跑。

        依据（2026-10-01 普查）：100 个声明 `--json` 的面各跑一次——**0 内部错误、0 非 JSON**
        （65 条产出合法 JSON，其余是 argparse 用法错 rc=2，属正常）。这条与上一条互补：上一条
        覆盖「人敲一半」，这条覆盖**agent 真正反复调用的机器形态**（无参 + `--json`），一旦某条
        机器面在此崩掉，消费方按 JSON 解析 stdout 就会直接失败。
        """
        inv = subprocess.run([sys.executable, NF, "shell", "--commands", "--json"],
                             cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=300)
        rows = json.loads(inv.stdout).get("rows") or []
        faces = [r["path"] for r in rows
                 if "--json" in (r.get("flags") or [])
                 and r["path"].split()[0] not in self.LONG_BY_DESIGN]
        self.assertGreaterEqual(len(faces), 90, "带 --json 的面不足（判据可能已失效）")
        bad = []
        for path in faces:
            try:
                r = subprocess.run([sys.executable, "-X", "utf8", NF, *path.split(), "--json"],
                                   cwd=str(ROOT), capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=120,
                                   stdin=subprocess.DEVNULL)
            except subprocess.TimeoutExpired:
                bad.append("%s --json：超时" % path)
                continue
            blob = (r.stderr or "") + (r.stdout or "")
            if "内部错误" in blob or "Traceback" in blob:
                bad.append("%s --json：rc=%d %s" % (path, r.returncode,
                                                    (r.stderr or "").strip().splitlines()[:1]))
                continue
            if r.returncode == 2:
                continue                      # argparse 用法错：正常
            try:
                json.loads((r.stdout or "").strip())
            except ValueError:
                bad.append("%s --json：rc=%d stdout 非 JSON（%s）"
                           % (path, r.returncode, (r.stdout or "")[:40]))
        self.assertEqual([], bad, "机器面无参直跑不合契约：%s" % bad)


class EntryGateMachineFaceTest(unittest.TestCase):
    """**入口闸门**（写法 / 编码 / 体量）拦下时，机器面仍必须是 JSON 体。

    依据（2026-10-01）：本轮新增的两道入口闸（`_path_writing_issue` 写法闸、`_utf8_text_issue`
    编码闸）走的是 `_machine_fail`，而既有「`--json` 失败仍回 JSON」判据只点了 11 条命令、且都在
    rc=1 上。若不把新闸门纳入，将来有人把某处改回裸 `print(..., file=sys.stderr)`，
    **消费方按 JSON 解析 stdout 就会崩**（这正是 2026-09-30 那次机器面扫修掉的问题）。
    """

    def _run_json(self, argv):
        return subprocess.run([sys.executable, NF] + list(argv), cwd=str(ROOT),
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=300)

    def test_entry_gate_failures_still_return_json(self):
        import json as _json
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.md"
            bad.write_bytes(b"\xff\xfe not utf-8\n")
            badq = Path(tmp) / "bad.json"
            badq.write_bytes(b"\xff\xfe{}")
            outside = Path(ROOT).parent / "nf_probe_should_not_exist.json"
            cases = (
                ("写法闸：interop --out ../x.json",
                 ["interop", "--kind", "openapi", "--out", "../nf_probe_should_not_exist.json"]),
                ("编码闸：attest <非 UTF-8>", ["attest", str(bad)]),
                ("编码闸：worldmodel --state <非 UTF-8>",
                 ["worldmodel", "--run", "--state", str(badq)]),
                ("编码闸：score --exceptions <非 UTF-8>", ["score", "--exceptions", str(badq)]),
                ("编码闸：decide --state <非 UTF-8>",
                 ["decide", "--state", str(badq), "--questions", str(badq)]),
                ("运行时失败：library deprecate <不存在>",
                 ["library", "deprecate", "NF-9999"]),
            )
            for label, argv in cases:
                r = self._run_json(argv + ["--json"])
                self.assertNotEqual(0, r.returncode, label)
                out = (r.stdout or "").strip()
                self.assertTrue(out, "%s：--json 失败时 stdout 不得为空" % label)
                doc = _json.loads(out)                      # 解析失败即判红
                self.assertIsInstance(doc, dict, label)
                self.assertIn("error", doc, "%s：失败体须带 error" % label)
                self.assertIn("exit", doc, "%s：失败体须带 exit" % label)
                self.assertFalse(doc.get("ok"), "%s：失败体 ok 必须为假" % label)
            self.assertFalse(outside.exists(), "越界写法不得落件到仓外")


class NonUtf8InputTest(unittest.TestCase):
    """输入件一律 **UTF-8**：非 UTF-8 文本件必须 clean 拒（带指引），不得冒「内部错误」。

    依据（2026-10-01 探针）：把非 UTF-8 文件喂给 `nf attest` / `nf lint`（含 `target` 收**多件**）
    / `nf import` / `nf run --pipeline` / `nf decide --state`，此前要么冒
    「✗ **内部错误**：'utf-8' codec can't decode…（重跑 NF_DEBUG=1 看堆栈）」，要么只回裸解码错——
    用户输入问题被框成内部故障，且零指引。修法是在入口集中判一次（`_utf8_text_issue`），
    本件把「一律 clean 拒」钉住；**密钥等二进制输入不在闸门内**（那是字节，不是文本）。
    """

    def _bad_files(self, tmp):
        md = Path(tmp) / "bad.md"
        md.write_bytes(b"\xff\xfe not utf-8 \x80\n")
        js = Path(tmp) / "bad.json"
        js.write_bytes(b"\xff\xfe{}")
        return str(md), str(js)

    def test_non_utf8_text_inputs_are_refused_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            md, js = self._bad_files(tmp)
            for label, argv in (
                    ("attest <非 UTF-8>", ["attest", md]),
                    ("lint <非 UTF-8>", ["lint", md]),
                    ("lint 多件之一非 UTF-8", ["lint", md, "README.md"]),
                    ("import <非 UTF-8>", ["import", md]),
                    ("run --pipeline <非 UTF-8>", ["run", "--pipeline", md,
                                                   "--modules", "通用类:M00"]),
                    ("decide --state <非 UTF-8>", ["decide", "--state", js,
                                                   "--questions", js]),
                    ("score --exceptions <非 UTF-8>", ["score", "--exceptions", js]),
                    # 2026-10-01 二批（机器面 × 非 UTF-8 普查抓到 5 处）：这几条位置参数的
                    # dest 是 `path` / `paths`，此前不在编码闸门的名单里。
                    ("audit check <非 UTF-8>", ["audit", "check", md]),
                    ("handover check <非 UTF-8>", ["handover", "check", md]),
                    ("output check <非 UTF-8>", ["output", "check", md]),
                    ("postmortem check <非 UTF-8>", ["postmortem", "check", md]),
                    ("state-front <非 UTF-8>", ["state-front", md])):
                r = subprocess.run([sys.executable, NF] + argv, cwd=str(ROOT),
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=300)
                blob = (r.stderr or "") + (r.stdout or "")
                self.assertNotEqual(0, r.returncode, "%s 应被拒" % label)
                self.assertNotIn("内部错误", blob, "%s 不得框成内部错误" % label)
                self.assertNotIn("Traceback", blob, "%s 不得冒栈" % label)
                self.assertIn("修复指引", blob, "%s 须带修复指引" % label)
                self.assertIn("UTF-8", blob, "%s 的指引须点明编码口径" % label)

    def test_binary_key_file_is_still_accepted(self):
        """正例对照：`--key-file` 收的是**字节**（HMAC 密钥），不能被编码闸门误拦。"""
        with tempfile.TemporaryDirectory() as tmp:
            key = Path(tmp) / "k.bin"
            key.write_bytes(bytes(range(32)))
            out = Path(tmp) / "env.json"
            r = subprocess.run([sys.executable, NF, "attest", "protocol/CONFORMANCE.md",
                                "--key-file", str(key), "--out", str(out)],
                               cwd=str(ROOT), capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=300)
            self.assertEqual(0, r.returncode, (r.stderr or "")[:300])
            self.assertTrue(out.exists(), "二进制密钥应当照常可用（闸门只拦文本类输入）")


if __name__ == "__main__":
    unittest.main()
