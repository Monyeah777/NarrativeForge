# -*- coding: utf-8 -*-
"""路径可达门禁：入口文档里的仓库相对路径与 `nf <子命令>` 必须真实可达。

为什么：文档是 agent 的**唯一入口**——一个写错的路径（实测：README 曾写
`scripts/verify.sh`，而 verify.sh 在仓库根）会让消费方在第一步就断，而 verify
此前对「文档里的路径写没写对」零判据。本判据把「读了就能走到」立成可核事实。

判定纪律（防误杀）：只认**能在仓库根解析**的写法——首段命中根目录既有条目，
且不含占位符。于是 `ALIAS.md`（相对 library/ 的引用）、`tools/call`（RPC 方法名）、
`yes/no`、`NF-XXXX` 这类都不算路径，不参与判定；真路径一旦写错即 FAIL。
"""
import argparse
import importlib.util
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import repo_face as _repo_face  # noqa: E402

#: 入口文档面（agent 与人的第一跳）：新增入口文档须同步入表，否则本门禁漏检。
ENTRY_DOCS = (
    "README.md", "README.en.md", "llms.txt", "docs/agent/ROUTES.md", "docs/agent/AGENT_START.md",
    "docs/agent/AI_ROUTING.md", "docs/meta/DEEP_DIVE.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md",
    "docs/mcp.md", "docs/terminal.md", "docs/ai-menu.md", "docs/library.md",
    "docs/nfal.md", "docs/conformance.md",
)

_TOKEN = re.compile(r"`([^`\n]+)`")
_NF_CMD = re.compile(r"\bnf(?:\.py)?\s+([a-z][a-z0-9-]*)")
_SECOND = re.compile(r"\bnf\s+([a-z][a-z0-9-]*)\s+([a-z][a-z0-9-]*)\b")
#: 占位符/通配写法（不是真路径，跳过）
_PLACEHOLDER = ("XXXX", "NNNN", "<", ">", "\u2026", "::")
_WILDCARD = set("*?|{}$")
_BAD_CHARS = frozenset("\uFF08\uFF09\u3010\u3011\u201C\u201D\u2018\u2019,\uFF0C\u3001\uFF1A\uFF1B")
_FILEY = (".md", ".json", ".py", ".yaml", ".yml", ".txt", ".sh", ".cmd")


def _root_tops() -> set:
    return {p.name for p in ROOT.iterdir()}


def _tokens(rel: str) -> list:
    p = ROOT / rel
    if not p.is_file():
        return []
    return _TOKEN.findall(p.read_text(encoding="utf-8"))


def _looks_like_rel_path(tok: str, tops: set) -> bool:
    s = tok.strip()
    if not s or " " in s or "://" in s or s.startswith(("-", "/", "~")):
        return False
    if any(mark in s for mark in _PLACEHOLDER):
        return False
    if any(c in _WILDCARD or c in _BAD_CHARS for c in s):
        return False
    if not (s.endswith(_FILEY) or "/" in s):
        return False
    return s.split("/", 1)[0] in tops


_PARSER_CACHE: list = []


def _parser():
    if _PARSER_CACHE:
        return _PARSER_CACHE[0]
    spec = importlib.util.spec_from_file_location("nfcli_reachability",
                                                  ROOT / "scripts" / "nf.py")
    nf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nf)
    parser = nf._make_parser()
    _PARSER_CACHE.append(parser)
    return parser


def _subcommands() -> set:
    parser = _parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    return set()


class DocPathReachabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tops = _root_tops()

    def test_entry_docs_exist(self):
        for rel in ENTRY_DOCS:
            self.assertTrue((ROOT / rel).is_file(), "入口文档缺失：%s" % rel)

    def test_relative_paths_resolve(self):
        seen, missing = 0, []
        for rel in ENTRY_DOCS:
            for tok in _tokens(rel):
                if not _looks_like_rel_path(tok, self.tops):
                    continue
                seen += 1
                cand = tok.strip().split("::", 1)[0]
                if not (ROOT / cand).exists():
                    missing.append("%s <- %s" % (cand, rel))
        self.assertGreaterEqual(seen, 30, "候选路径面塌缩（判定可能已失效）")
        self.assertEqual([], sorted(set(missing)), "入口文档引用了不存在的路径")

    def test_nf_subcommands_resolve(self):
        valid = _subcommands()
        self.assertGreater(len(valid), 40, "子命令面解析失败")
        missing = []
        for rel in ENTRY_DOCS:
            for tok in _tokens(rel):
                for cmd in _NF_CMD.findall(tok):
                    if cmd not in valid:
                        missing.append("nf %s <- %s" % (cmd, rel))
        self.assertEqual([], sorted(set(missing)), "入口文档引用了不存在的 nf 子命令")


#: 按设计引用「在场外/运行期件」的文档（逐条写明理由；本表只许缩小并由变异用例守着）。
EXEMPT_DOCS = {
    "docs/L3_FROZEN.md": "退役清单索引——按设计列出**已移除**的端壳件",
    "docs/fde-stack.md": "FDE 样例文本——引用的 results/interop/* 为运行期产物",
    "engine/dotnet/_aux_golden.cs.txt": "负例 golden 夹具——含刻意不存在的路径",
}
#: 在场文档里**按设计指向在场外**的路径（生成物 / gitignored 内部档案）：fresh clone 不在场。
#: 逐条写明理由；判定按**前缀边界**（`.rivet/scratchx` 不算命中 `.rivet/scratch`）。本表只许缩小。
LIVING_PATH_EXEMPT = {
    ".rivet/scratch": "内部档案暂存区（gitignored）：手稿/记录按设计引用，非仓库件",
    "engine/rust/target": "Rust 构建产物目录（gitignored）：README/手稿指其布局，fresh clone 不在场",
    "packaging/npm/payload": "npm 一键包暂存产物（gitignored）：由 npm run stage 生成",
}


def _is_exempt(cand: str) -> bool:
    """cand 是否命中在场外豁免（前缀按边界，避免 .rivet/scratchx 误命中）。"""
    return any(cand == k or cand.startswith(k + "/") for k in LIVING_PATH_EXEMPT)


def _unresolved_paths(tokens: list, tops: set) -> list:
    """文档 token 里**写成了真路径却走不到**的（含豁免；供判据与变异自证共用）。"""
    out = []
    for tok in tokens:
        if "#" in tok:
            continue
        if not _looks_like_rel_path(tok, tops):
            continue
        cand = tok.strip().split("::", 1)[0]
        if _is_exempt(cand):
            continue
        if not (ROOT / cand).exists():
            out.append(cand)
    return out


def _living_docs() -> list:
    """全部「在场文档」（.md/.txt，排除结果归档与变更日志）——口径必须与仓库实况一致。

    面 = 仓库件（`core.paths.walk_repo_paths`）：被 `.gitignore` 覆盖的暂存副本不算在场文档
    （否则同一份正文以第二份路径进面，路径可达判据会对着副本的裁剪面假红）。
    """
    out = []
    for p in _repo_face.walk_repo_paths(str(ROOT)):
        if p.suffix not in (".md", ".txt"):
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel == "CHANGELOG.md" or rel.startswith("results/"):
            continue
        out.append(rel)
    return sorted(out)


class LivingDocConsistencyTest(unittest.TestCase):
    """全部在场文档的路径与二级命令必须可达（口径统一：写了就要能走到）。"""

    @classmethod
    def setUpClass(cls):
        cls.tops = _root_tops()
        cls.docs = _living_docs()

    def test_living_docs_paths_resolve(self):
        self.assertGreater(len(self.docs), 60, "在场文档面塌缩（判定可能已失效）")
        missing = []
        for rel in self.docs:
            if rel in EXEMPT_DOCS:
                continue
            for cand in _unresolved_paths(_tokens(rel), self.tops):
                missing.append("%s <- %s" % (cand, rel))
        self.assertEqual([], sorted(set(missing)), "在场文档引用了不存在的路径")

    def test_path_exempt_is_boundary_precise(self):
        """豁免只认前缀边界：同类名不是豁免对象（防豁免表悄悄放宽）。"""
        self.assertTrue(_is_exempt(".rivet/scratch/x.py"))
        self.assertTrue(_is_exempt("engine/rust/target"))
        self.assertTrue(_is_exempt("packaging/npm/payload/"))
        self.assertFalse(_is_exempt(".rivet/scratchx"))
        self.assertFalse(_is_exempt("engine/rust/targets"))
        self.assertEqual(["docs/不存在的手册.md"],
                         _unresolved_paths(["docs/不存在的手册.md"], self.tops))

    def test_living_docs_second_level_resolve(self):
        valid = _subcommands()
        parser = _parser()
        missing = []
        for rel in self.docs:
            for tok in _tokens(rel):
                for top, second in _SECOND.findall(tok):
                    if top not in valid:
                        continue
                    choices = set()
                    for action in parser._actions:
                        if (isinstance(action, argparse._SubParsersAction)
                                and top in action.choices):
                            for sub in action.choices[top]._actions:
                                if isinstance(sub, argparse._SubParsersAction):
                                    choices |= set(sub.choices)
                    if choices and second not in choices:
                        missing.append("nf %s %s <- %s" % (top, second, rel))
        self.assertEqual([], sorted(set(missing)), "在场文档引用了不存在的二级子命令")


#: 旗标级可达的扫描面（文档 + **修复指引真源**：core 的 `修复指引` 串与 CLI 的 `CHECK_GUIDE`
#: + **agent 第一跳**：`skills/**` 是给 agent 看的入口文案，写了不存在的旗标同样会让人照着撞墙；
#: 2026-10-02 扩面时实测该面零漂移，属「补判据面」而非「修缺陷」）。
FLAG_FACES = ("docs", "desktop/src/core", "scripts", "skills")
_NF_INVOCATION = re.compile(
    r"\bnf\s+([a-z][a-z0-9-]*)(?:\s+([a-z][a-z0-9-]*))?((?:\s+--[a-z-]+)*)")


def _flag_surface() -> dict:
    """→ {(命令[, 子命令]): 可用旗标集}（从真 argparse 面取，权威与 CLI 同源）。"""
    parser = _parser()
    out: dict = {}
    for action in parser._actions:
        if not isinstance(action, argparse._SubParsersAction):
            continue
        for name, sub in action.choices.items():
            flags = set()
            for a in sub._actions:
                flags |= set(a.option_strings)
            out[(name, "")] = flags
            for a2 in sub._actions:
                if isinstance(a2, argparse._SubParsersAction):
                    for n2, sub2 in a2.choices.items():
                        f2 = set()
                        for a3 in sub2._actions:
                            f2 |= set(a3.option_strings)
                        out[(name, n2)] = f2
    return out


class GuidanceFlagReachabilityTest(unittest.TestCase):
    """**修复指引里的旗标也必须可达**（2026-09-30 补）：「路径保证一定可达」此前只判到子命令级，
    `nf explain 37` 写着 `nf knowledge --check`——该子命令根本没有 `--check`，照做只会吃
    argparse 用法错误。本判据把「指引里出现的 `nf <命令> [子命令] --旗标`」逐条对真 argparse 面
    核验；只认**在场面**（docs / core / scripts）里的写法。
    """

    @classmethod
    def setUpClass(cls):
        cls.surface = _flag_surface()
        cls.commands = {k[0] for k in cls.surface}

    @staticmethod
    def _unreachable(text: str, surface: dict, commands: set) -> list:
        """一段文本里「`nf <命令> [子命令] --旗标` 但旗标不存在」的写法（纯函数，便于变异自证）。"""
        bad = []
        for m in _NF_INVOCATION.finditer(text):
            cmd, sub = m.group(1), m.group(2) or ""
            if cmd not in commands:
                continue
            table = surface.get((cmd, sub)) or surface.get((cmd, "")) or set()
            for fl in re.findall(r"--[a-z-]+", m.group(3) or ""):
                if fl not in table:
                    bad.append("nf %s%s %s" % (cmd, (" " + sub) if sub else "", fl))
        return bad

    def test_flags_in_guidance_exist(self):
        missing = []
        for face in FLAG_FACES:
            for p in sorted((ROOT / face).rglob("*")):
                if not p.is_file() or p.suffix not in (".md", ".py", ".txt"):
                    continue
                text = p.read_text(encoding="utf-8", errors="replace")
                for hit in self._unreachable(text, self.surface, self.commands):
                    missing.append("%s <- %s" % (hit, p.relative_to(ROOT).as_posix()))
        self.assertEqual([], sorted(set(missing)),
                         "指引引用了不存在的旗标（修复指引：改写成真实旗标，或删掉该写法）")

    def test_predicate_has_catch_power(self):
        """变异自证：把那条历史漂移（`nf knowledge --check`）喂回判据，必须判红；真写法不许误报。"""
        self.assertIn("nf knowledge --check",
                      self._unreachable("补什么：`nf knowledge --check` 看逐条。",
                                        self.surface, self.commands))
        self.assertEqual([], self._unreachable(
            "补什么：`nf knowledge lint`；复核用 `nf stats --json`。",
            self.surface, self.commands))


#: 代码内指引里**刻意写的不存在命令**（逐条写明理由；本表只许缩小）
GUIDANCE_EXEMPT = {
    "nf stat": "唯一前缀/拼错建议的**示例**——刻意拿一个不存在的命令演示「歧义不猜」",
}
_NF_INVOKE_CODE = re.compile(r"`(nf\s+([a-z][a-z0-9-]*)[^`]*)`")


class GuidanceCommandReachabilityTest(unittest.TestCase):
    """**代码内指引**（core/scripts 的反引号串）引用的 `nf 子命令` 必须真实存在。

    依据（2026-09-30）：文档侧的「写了就要能走到」已有判据，但**修复指引写在代码里**的那批
    一直没人管——实测 `nf ls` 被两处指路（共享路径解析器与 `nf lint`），而 CLI 里根本没有
    `ls` 这个子命令：照做的读者只会拿到 `invalid choice: 'ls'`。本件把这批也钉住。
    """

    commands: set = set()

    @classmethod
    def setUpClass(cls):
        cls.commands = _subcommands()

    def _bad(self, text: str) -> list:
        bad = []
        for m in _NF_INVOKE_CODE.finditer(text):
            raw, word = m.group(1).strip(), m.group(2)
            if raw in GUIDANCE_EXEMPT or word in self.commands:
                continue
            bad.append(raw)
        return bad

    def test_code_guidance_commands_exist(self):
        missing = []
        for face in ("desktop/src/core", "scripts"):
            for p in sorted((ROOT / face).glob("*.py")):
                text = p.read_text(encoding="utf-8", errors="replace")
                for hit in self._bad(text):
                    missing.append("%s <- %s" % (hit, p.relative_to(ROOT).as_posix()))
        self.assertEqual([], sorted(set(missing)),
                         "代码内指引引用了不存在的 nf 子命令（修复指引：改成真实命令，"
                         "或在 GUIDANCE_EXEMPT 里写明「刻意为之」的理由）")

    def test_predicate_has_catch_power(self):
        """变异自证：历史漂移 `nf ls` 必判红；刻意示例（`nf stat`）与真命令不许误报。"""
        self.assertEqual(["nf ls"], self._bad("修复指引：用 `nf ls` 看根级面。"))
        self.assertEqual([], self._bad("修复指引：用 `ls` 看根级面、`nf spec ls` 看协议包。"))
        self.assertEqual([], self._bad("示例：`nf stat` → `nf stats`（歧义不猜）"))


#: 代码指引里**刻意指向仓外**的路径（逐条写明理由；本表只许缩小）
GUIDANCE_PATH_EXEMPT = {
    "docs/checks.md": "引的是**上游项目** ossf/scorecard 的仓内文件（非本仓路径）",
    "packaging/npm/payload/": "npm 一键包的暂存产物：由 npm run stage 生成，且被 "
                              "packaging/npm/.gitignore 忽略——fresh clone 本就不在场（生成物非仓库件）",
}
_CODE_FACE = ("desktop/src/core", "scripts")


class GuidancePathReachabilityTest(unittest.TestCase):
    """**代码内指引**里写下的仓库相对路径必须可达（2026-09-30 补；此处沿用文档侧的辨别口径）。

    依据：文档侧的「路径写了就要能走到」抓过三处真漂移（README 的 `scripts/verify.sh`、
    community 的兄弟仓路径、`nf decisions new` 这类死命令）；而**写在代码里**的修复指引
    同样会指路（「按 `docs/xxx.md` 裁决」「补 `protocol/yyy.json`」），这一批此前没人扫。
    判定沿用文档侧同一套 `_looks_like_rel_path`（含占位/模板过滤），命中后逐条核对能否解析。
    """

    tops: set = set()

    @classmethod
    def setUpClass(cls):
        cls.tops = _root_tops()

    def _bad(self, text: str) -> list:
        bad = []
        for m in _TOKEN.finditer(text):
            tok = m.group(1).strip()
            if tok in GUIDANCE_PATH_EXEMPT:
                continue
            if "%s" in tok or "%d" in tok:          # 格式化模板不是路径
                continue
            if not _looks_like_rel_path(tok, self.tops):
                continue
            cand = tok.split("::", 1)[0]
            if not (ROOT / cand).exists():
                bad.append(cand)
        return bad

    def test_code_guidance_paths_resolve(self):
        missing = []
        for face in _CODE_FACE:
            for p in sorted((ROOT / face).glob("*.py")):
                text = p.read_text(encoding="utf-8", errors="replace")
                for hit in self._bad(text):
                    missing.append("%s <- %s" % (hit, p.relative_to(ROOT).as_posix()))
        self.assertEqual([], sorted(set(missing)),
                         "代码内指引引用了不可达的仓库路径（修复指引：改指向在场件，"
                         "或在 GUIDANCE_PATH_EXEMPT 里写明「本就指向仓外」的理由）")

    def test_predicate_has_catch_power(self):
        """变异自证：假路径必判红；真路径与登记在外的（上游项目文件）不许误报。"""
        self.assertEqual(["docs/不存在的手册.md"], self._bad("按 `docs/不存在的手册.md` 裁决。"))
        self.assertEqual([], self._bad("按 `docs/verification-cards.md` 裁决。"))
        self.assertEqual([], self._bad("见 ossf/scorecard 的 `docs/checks.md`。"))


class OrphanArtifactTest(unittest.TestCase):
    """**样例/夹具不得成为孤儿**：`docs/examples/**` 与 `desktop/tests/fixtures/**` 里的件，
    必须被别的仓内文本引用（路径或文件名出现即算）。

    依据（2026-10-01 反向可达性普查）：正方向的判据（文档里写的路径必须在场）仓里早有，**反方向**
    没有——于是 `docs/examples/st-validate-report.md` 这类**真产物样例**躺在树里没人指向它：
    `docs/examples/st-validate/README.md` 自称「覆盖 R1 卡 / R3 世界书 / **R4 变量**」，
    而 R4 的那份报告其实在目录外、且全仓零引用。修法是**把它链回来**（而不是删件：它是真实产物
    样例，删了就少一份证据），本判据保证此类孤儿不再出现。
    """

    #: 有意不引用（上游/临时件）→ 理由（当前为空）。
    KNOWN_ORPHAN: dict = {}
    TREES = ("docs/examples", "desktop/tests/fixtures")
    EXTS = (".py", ".md", ".txt", ".json", ".yml", ".yaml", ".sh", ".cmd", ".toml", ".mmd")

    def _tracked_texts(self):
        import subprocess
        listed = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT), capture_output=True,
                                text=True, encoding="utf-8", errors="replace",
                                timeout=300).stdout.split("\0")
        out = {}
        for rel in listed:
            if not rel:
                continue
            p = ROOT / rel
            if p.suffix.lower() in self.EXTS and p.is_file():
                try:
                    out[rel] = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
        return out

    def test_sample_artifacts_are_referenced(self):
        texts = self._tracked_texts()
        self.assertGreater(len(texts), 200, "扫到的文本件太少（判据可能已失效）")
        orphans, checked = [], 0
        for tree in self.TREES:
            members = [r for r in texts if r.startswith(tree + "/")]
            self.assertTrue(members, "%s 里没有件（判据可能已失效）" % tree)
            for rel in members:
                checked += 1
                if rel in self.KNOWN_ORPHAN:
                    continue
                name = rel.rsplit("/", 1)[-1]
                if not any((rel in t or name in t) for r, t in texts.items() if r != rel):
                    orphans.append(rel)
        self.assertGreaterEqual(checked, 20, "样例/夹具件数不足（判据可能已失效）")
        self.assertEqual([], orphans,
                         "样例/夹具成了孤儿（无人指向；修复指引：在对应文档里链上它，"
                         "或写进 KNOWN_ORPHAN 说明为什么它不需要被引用）：%s" % orphans)


#: 有意「不链进任何入口」的**存档记录** → 一句理由。本表只许缩小：条目一旦被别处引用
#: （或已不在场）就必须删掉，否则会变成掩盖新孤儿的黑洞（见 `test_archive_registry_has_no_stale_entries`）。
ARCHIVE_DOCS = {
    "docs/41_波C_C1_C2_实测记录.md":
        "41 波C C1/C2 一次性验收实测记录——结论已入 CHANGELOG 与 `nf sig`/`nf diff` 判据，本件供追溯",
    "docs/41_波C_W2_C3_C4_实测记录.md":
        "41 波C W2 C3/C4 一次性验收实测记录——同上，供追溯",
    "docs/41_波C_W3_实测记录.md":
        "41 波C W3 一次性实测记录（C6/C8/C9 + D2/D5/D6），供追溯",
    "docs/41_波C_W5_实测记录.md":
        "41 波C W5 一次性实测记录（D3 ruff / D4 日志级别），供追溯",
    "docs/42_M1_P06_演练集.md":
        "42 M1 P06 内部执行演练集（第 2 份）——载体 fixture 在 desktop/tests/fixtures/execution/，本件是演练记录",
    "docs/42_M4_文档分类普查.md":
        "42 M4 文档分类普查一次性报告——机检已由 `core/doc_hygiene.py` 承担，本件是普查结论存档",
    "docs/42_M4_资产评估报告.md":
        "42 M4 资产密度评估一次性报告——人读抽查 + 引用计数结论存档",
    "docs/42_M5_工程收口.md":
        "42 M5 里程碑收口记录（5.1-5.6 交付明细）——供追溯，各交付物本身另有常驻判据",
}


class UnlinkedDocTest(unittest.TestCase):
    """**在场文档不得成为孤儿**：`docs/` 下的 .md 每篇要么被别处引用，要么在 `ARCHIVE_DOCS` 里登记理由。

    依据（2026-10-01 反向可达性普查）：仓里已有「样例/夹具不得成孤儿」（`OrphanArtifactTest`）
    与「文档写的路径必须在场」（正向），但**手册本身有没有人指向它**此前无人核——实测
    `docs/` 下 86 篇 .md 里 8 篇零引用（wave-41/42 的实测记录 / 演练集 / 普查报告 / 评估报告 / 收口记录）。
    逐条辨别：那是**存档记录**（一次性取证/演练/评估/收口），**不是墓碑**，故**不删**；也不硬塞进
    `llms.txt`（策展清单）或 README 文件表（刻意只列主入口），而是**逐条登记为「有意不链接」**，
    让**新增**的未链接文档即红。

    口径（与 `_living_docs` 一致，防自证）：`CHANGELOG.md`（历史流水，不是导航入口）与
    `results/`（生成物归档）里的提及**不算链接**；判据文件自身（登记表就在里面）也从语料里剔除。
    """

    #: 与 `_living_docs` 同一套口径：变更日志与结果归档不是入口链接。
    NON_LINKING = ("CHANGELOG.md", "results/")
    SELF = "desktop/tests/test_doc_reachability.py"
    EXTS = (".py", ".md", ".txt", ".json", ".yml", ".yaml", ".sh", ".cmd", ".toml")

    @classmethod
    def _counts_as_link(cls, rel: str) -> bool:
        """这份文本件里的提及算不算「链接」（口径函数，便于变异自证）。"""
        if rel == cls.SELF:
            return False
        return rel not in cls.NON_LINKING and not rel.startswith(cls.NON_LINKING[1])

    def _tracked_texts(self):
        import subprocess
        listed = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT), capture_output=True,
                                text=True, encoding="utf-8", errors="replace",
                                timeout=300).stdout.split("\0")
        out = {}
        for rel in listed:
            if not rel or not self._counts_as_link(rel):
                continue
            p = ROOT / rel
            if p.suffix.lower() in self.EXTS and p.is_file():
                try:
                    out[rel] = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
        return out

    @staticmethod
    def _referenced(rel, texts):
        """该件是否被**别处**引用（仓库相对路径或文件名出现即算；不含自身）。"""
        name = rel.rsplit("/", 1)[-1]
        return any((rel in t or name in t) for r, t in texts.items() if r != rel)

    def _docs(self, texts):
        return sorted(r for r in texts if r.startswith("docs/") and r.endswith(".md"))

    def test_docs_are_referenced_or_archived(self):
        texts = self._tracked_texts()
        docs = self._docs(texts)
        self.assertGreaterEqual(len(docs), 80, "docs/**.md 面塌缩（判据可能已失效）")
        self.assertGreaterEqual(len(ARCHIVE_DOCS), 1, "存档登记表为空（判据可能已失效）")
        orphans = [r for r in docs if r not in ARCHIVE_DOCS and not self._referenced(r, texts)]
        self.assertEqual([], orphans,
                         "docs 下的手册成了孤儿（修复指引：在入口/相关文档里链上它，"
                         "或写进 ARCHIVE_DOCS 说明为什么它不需要被引用）：%s" % orphans)

    def test_archive_registry_has_no_stale_entries(self):
        """登记表只许缩小——陈旧条目会变成掩盖新孤儿的黑洞（变异自证见下一个用例）。"""
        texts = self._tracked_texts()
        stale = [r for r in ARCHIVE_DOCS if r not in texts or self._referenced(r, texts)]
        self.assertEqual([], stale,
                         "ARCHIVE_DOCS 里有陈旧条目（该文档已被引用或已不在场，"
                         "修复指引：从表里删掉）：%s" % stale)

    def test_predicate_has_catch_power(self):
        """变异自证：零引用件必判红；被引用的件不许误报；CHANGELOG / 自带登记表不算链接。"""
        texts = {
            "docs/a.md": "# 甲",
            "docs/b.md": "# 乙",
            "docs/sub/c.md": "见 `docs/a.md`",
            "scripts/x.py": "# 按 docs/b.md 裁决",
        }
        self.assertTrue(self._referenced("docs/a.md", texts), "被路径引用应判「有链接」")
        self.assertTrue(self._referenced("docs/b.md", texts), "被文件名引用应判「有链接」")
        self.assertFalse(self._referenced("docs/sub/c.md", texts), "零引用件应判「孤儿」")
        self.assertFalse(self._counts_as_link("CHANGELOG.md"), "变更日志不是链接来源")
        self.assertFalse(self._counts_as_link("results/audit/x.md"), "结果归档不是链接来源")
        self.assertFalse(self._counts_as_link(self.SELF), "登记表自身不是链接来源")
        self.assertTrue(self._counts_as_link("docs/verification-cards.md"), "在册文档是链接来源")


if __name__ == "__main__":
    unittest.main()
