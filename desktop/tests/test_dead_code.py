# -*- coding: utf-8 -*-
"""墓碑代码门禁：公开/私有顶层函数**不得零引用**（全仓文本面都没人提）。

为什么：`ADR-0002 门禁不注水` 与「清理墓碑代码」都要求不留无主件，但仓库此前只有
**模块级**的零引用盘点（一次性审计），函数级零判据。本轮实测（2026-09-30）在
`desktop/src/core` + `scripts` + `.github/scripts` 里抓到 **9 条零引用函数**——4 条公开
（`autofix.fix_targets` / `autofix.fix_repo` 是被 `nf lint --fix` 绕过的手写包装、
`library.digest_of_entry`、`domain_pack.host_categories`）与 5 条私有（`daemon._recv_line`
等被 `_LineReader` 取代的旧读行实现），全部删除后本判据归零。

判据口径（防误杀）：**只要名字在任意入仓文本里出现过一次**（`.py` / `.sh` / `.cmd` /
`.yml` / `.md` / `.txt`，含字符串与文档）就不算零引用——因此「模块内字典派发」
（如 `GENERATORS = {"x": fn}`）与「文档里写着的 API」都不会被误判；真零引用 = 连自己
文件里都没人叫它。变异自证见 `ZeroRefRuleTest`。
"""
import ast
import collections
import functools
import hashlib
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET_DIRS = ("desktop/src/core", "scripts", ".github/scripts")
SUFFIXES = {".py", ".sh", ".cmd", ".yml", ".yaml", ".md", ".txt"}
TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@functools.lru_cache(maxsize=4096)
def _parse(text: str):
    """`ast.parse` 的**按正文**缓存（键是文本本身 ⇒ 合成 pool 与真仓都安全）。

    本件有 3 条判据都要遍历同一批 core/scripts 文件的 AST；逐条重解析纯属浪费
    （实测该文件一度 ~52 s）。同内容复用、异内容各自解析。
    """
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


@functools.lru_cache(maxsize=4096)
def _tokens(text: str) -> collections.Counter:
    """按**正文**缓存的标识符计数（本件多条判据都要同一批文本的词频）。"""
    return collections.Counter(TOKEN.findall(text))


def zero_ref_defs(pool: dict, targets=TARGET_DIRS) -> list:
    """→ 零引用定义清单 `[(仓库相对路径, 函数名, 行号)]`（纯函数，便于变异自证）。"""
    counts: collections.Counter[str] = collections.Counter()
    per_file = {}
    for rel, text in pool.items():
        c = _tokens(text)
        per_file[rel] = c
        counts.update(c)
    out = []
    wanted = tuple(d.rstrip("/") + "/" for d in targets)
    for rel in sorted(pool):
        if not rel.endswith(".py") or not rel.startswith(wanted):
            continue
        tree = _parse(pool[rel])
        if tree is None:
            continue
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            name = node.name
            if name.startswith("__"):
                continue
            # 自身文件里减去 def 那一行；为 0 且全仓总计数 ≤ 1 ⇒ 无人引用
            own = per_file[rel].get(name, 0) - 1
            if own <= 0 and counts[name] <= 1:
                out.append((rel, name, node.lineno))
    return out


def zero_ref_constants(pool: dict, targets=TARGET_DIRS) -> list:
    """→ 零引用**模块级大写常量**清单 `[(仓库相对路径, 名称, 行号)]`。

    口径与 `zero_ref_defs` 同源（**除定义行外**全仓任意文本出现过一次即算引用）。
    阈值取 `[A-Z][A-Z0-9_]{2,}`（≥3 字符），与 `zero_ref_defs` 同一套「防误杀」思路：
    短名（`T0` 之类）不判，避免把字面量巧合当引用。
    """
    counts: collections.Counter[str] = collections.Counter()
    per_file = {}
    for rel, text in pool.items():
        c = _tokens(text)
        per_file[rel] = c
        counts.update(c)
    out = []
    wanted = tuple(d.rstrip("/") + "/" for d in targets)
    for rel in sorted(pool):
        if not rel.endswith(".py") or not rel.startswith(wanted):
            continue
        tree = _parse(pool[rel])
        if tree is None:
            continue
        for node in tree.body:
            names = []
            if isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names = [node.target.id]
            for name in names:
                if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", name):
                    continue
                own = per_file[rel].get(name, 0) - 1      # 减去定义行自己
                if own <= 0 and counts[name] <= 1:
                    out.append((rel, name, node.lineno))
    return out


#: 允许「只有自己的单测引用」的 core 模块（**只减不增**：新增须在此登记理由）。
#: 口径：生产面 = 非 `desktop/tests/` 的 `.py`；命中本条说明该模块**没有任何生产代码入口**。
#: **当前为空**（2026-10-01）：唯一一条 `preset_manager` 已按登记里写的补齐方向落地——
#: 退役端壳的预设语义接成了 `nf preset ls/show/apply/save/rm/export/import`（见 `scripts/nf.py`
#: 的 `_cmd_preset`），生产面有入口 ⇒ 不再属「只有自己单测引用」，本条按「只减不增」清空。
TEST_ONLY_ALLOWED: dict = {}


def test_only_modules(pool: dict) -> list:
    """→ 「只有自己的单测引用」的 core 模块清单 `[(仓库相对路径, 模块名)]`。

    为什么单列：`zero_ref_defs` 只管顶层函数。整份**模块**只被自己的单测 import 时，
    函数的 token 计数不为 0（测试文件里出现过）⇒ 既有判据看不见——那正是「路径不可达」
    的墓碑（能力写完了、没人能调到）。
    """
    prod_py = {rel: text for rel, text in pool.items()
               if rel.endswith(".py") and not rel.startswith("desktop/tests/")}
    out = []
    for rel in sorted(pool):
        if not (rel.startswith("desktop/src/core/") and rel.endswith(".py")):
            continue
        stem = Path(rel).stem
        if stem.startswith("__") or stem in TEST_ONLY_ALLOWED:
            continue
        if any(stem in text for other, text in prod_py.items() if other != rel):
            continue
        out.append((rel, stem))
    return out


#: import 语句行（含缩进与 `from x import y` / `import x`）——判「只被 import 引用」时剔除
_IMPORT_LINE = re.compile(r"^\s*(from\s+\S+\s+import\s|import\s)")


def import_only_defs(pool: dict, targets=TARGET_DIRS) -> list:
    """→ 「**只被 import 引用、从未被调用**」的顶层函数 `[(路径, 名字, 行号)]`。

    为什么单列：`zero_ref_defs` 的口径是「名字在任意入仓文本出现过一次即算有人用」——
    于是「定义 + 被 import（但没人调用）」会**看起来有人用**，判据看不见。

    实测（2026-10-01）：全仓命中 **1** 条——`.github/scripts/library_ingest.py::rebuild_alias`
    （ALIAS 早已改由 `core.library.write_projection` 全量重生成，这个旧实现定义后从未被调用，
    只有 `gitee_ingest.py` 的 import 在「装作」被用）。已删函数 + 该 import；
    本判据把这一类钉死（把 import 行剔掉再数引用，为 0 即「只被 import 引用」）。
    """
    counts: collections.Counter[str] = collections.Counter()
    for text in pool.values():
        body = "\n".join(ln for ln in text.splitlines() if not _IMPORT_LINE.match(ln))
        counts.update(_tokens(body))
    out = []
    wanted = tuple(d.rstrip("/") + "/" for d in targets)
    for rel in sorted(pool):
        if not rel.endswith(".py") or not rel.startswith(wanted):
            continue
        tree = _parse(pool[rel])
        if tree is None:
            continue
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("__"):
                continue
            if counts[node.name] - 1 <= 0:      # 减去本行 def
                out.append((rel, node.name, node.lineno))
    return out


def unused_imports(pool: dict, targets=TARGET_DIRS) -> list:
    """→ 「导入了、本文件内一次没用到」的绑定名 `[(路径, 名字, 行号)]`（纯 stdlib 口径）。

    为什么单列：仓库的 `ruff.toml` **刻意**只开语法级规则（E9/F63/F7/F82，「不启用全库
    风格规则」），死 import 这一类从没被扫过。实测（2026-10-01 泛选扫描）：全仓 17 处
    （拆环残留的 `import_graph` 别名 6 处 + `os`/`typing`/`contextlib`/`subprocess` 等），
    另 1 处 `parse_frontmatter` 是**对外转发面**（保留并写 `# noqa` + 来由）。

    口径与其它墓碑判据一致：名字在**本文件正文 token**（含注释与字符串，import 行本身除外）
    里出现过即算用到——于是「兼容转发 + 写明来由」天然放行，真死件才判红。
    `from __future__ import ...` 是编译指令，不参与。
    """
    out = []
    wanted = tuple(d.rstrip("/") + "/" for d in targets)
    for rel in sorted(pool):
        if not rel.endswith(".py") or not rel.startswith(wanted):
            continue
        text = pool[rel]
        tree = _parse(text)
        if tree is None:
            continue
        body_tokens = set(TOKEN.findall(
            "\n".join(ln for ln in text.splitlines() if not _IMPORT_LINE.match(ln))))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [(a.asname or a.name.split(".")[0], node.lineno) for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
                names = [(a.asname or a.name, node.lineno)
                         for a in node.names if a.name != "*"]
            for name, lineno in names:
                if name not in body_tokens:
                    out.append((rel, name, lineno))
    return out


def duplicate_bodies(pool: dict, targets=TARGET_DIRS, min_lines: int = 12) -> list:
    """→ **逐字相同**的函数体组 `[(行数, [(路径, 函数名, 行号), …]), …]`（纯 stdlib）。

    为什么单列：重复实现是「逻辑垃圾」里最容易静默漂移的一类——改一份忘一份，两份就此
    分叉。实测（2026-10-01 静态扫）：全仓命中 **1 组**——`handover._bullet_blocks` 与
    `postmortem._bullet_blocks`（各 15 行，逐字相同：交接的「未决项」与复盘的「行动项」是
    同一件事），已收敛到叶子件 `core/md_blocks.py`。

    口径：AST 取函数体（**去 docstring**），按行 strip 后比对；短于 `min_lines` 的不看
    （小工具函数长得像属正常，判了会成噪声）。
    """
    groups: dict = {}
    wanted = tuple(d.rstrip("/") + "/" for d in targets)
    for rel in sorted(pool):
        if not rel.endswith(".py") or not rel.startswith(wanted):
            continue
        src = pool[rel]
        tree = _parse(src)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = [n for n in node.body
                    if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                            and isinstance(n.value.value, str))]   # 去 docstring
            lines = []
            for n in body:
                seg = ast.get_source_segment(src, n) or ""
                lines += [ln.strip() for ln in seg.splitlines() if ln.strip()]
            if len(lines) < min_lines:
                continue
            key = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
            groups.setdefault((key, len(lines)), []).append((rel, node.name, node.lineno))
    out = [(n, sorted(v)) for (_k, n), v in groups.items() if len(v) > 1]
    return sorted(out, key=lambda x: -x[0])


#: 由**框架按名隐式调用**的类方法（零引用 ≠ 死代码）：键 = `"<路径>::<类>.<方法>"`，值 = 理由。
#: 本表**只许缩小**——条目一旦不再零引用就必须删掉（见 `MethodRuleTest` 的陈旧检查）。
IMPLICIT_HOOKS = {
    "scripts/serve_decision_model.py::Handler.do_GET":
        "http.server 按 HTTP 动词**按名派发**（方法名就是路由，全仓永远不会出现 `do_GET(`）",
    "scripts/serve_decision_model.py::Handler.do_POST": "同上（POST 路由）",
    "scripts/serve_decision_model.py::Handler.log_message":
        "http.server 的日志钩子——框架回调，不显式调用",
}


def method_defs(pool: dict, targets=TARGET_DIRS) -> list:
    """→ 全部**类方法**定义 `[(路径, 类名, 方法名, 行号)]`（含魔法方法；供判据面下限）。"""
    out = []
    wanted = tuple(d.rstrip("/") + "/" for d in targets)
    for rel in sorted(pool):
        if not rel.endswith(".py") or not rel.startswith(wanted):
            continue
        tree = _parse(pool[rel])
        if tree is None:
            continue
        for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
            for node in cls.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.append((rel, cls.name, node.name, node.lineno))
    return out


def zero_ref_methods(pool: dict, targets=TARGET_DIRS, hooks=None) -> list:
    """→ 零引用**类方法**清单 `[(路径, 类名, 方法名, 行号)]`（口径与 `zero_ref_defs` 同源）。

    为什么单列（2026-10-02，作者指令「清理墓碑代码（注意辨别）」）：`zero_ref_defs` 只遍历
    `tree.body`——那是**顶层函数**，**类方法整个面无人管**；而历史墓碑里就有方法级的
    （`daemon._recv_line` 被新的读行实现取代后仍留着）。本轮全仓扫 122 个方法，命中 **3** 个，
    且**全部是框架按名隐式调用的钩子**（`http.server` 的 `do_GET` / `do_POST` / `log_message`）
    ——教科书级的「零引用 ≠ 死代码」，逐条登记在 `IMPLICIT_HOOKS` 里而不是误杀。
    真零引用 = 连自己类里都没人叫它，且全仓**任意文本**都没出现过它的名字。
    """
    hooks = IMPLICIT_HOOKS if hooks is None else hooks
    counts: collections.Counter[str] = collections.Counter()
    per_file: dict = {}
    for rel, text in pool.items():
        c = _tokens(text)
        per_file[rel] = c
        counts.update(c)
    out = []
    for rel, cls, name, lineno in method_defs(pool, targets):
        if name.startswith("__") and name.endswith("__"):
            continue                    # 魔法方法由语言隐式调用（`len()` / `with` …），不判
        if "%s::%s.%s" % (rel, cls, name) in hooks:
            continue
        own = per_file[rel].get(name, 0) - 1          # 减去 def 那一行
        if own <= 0 and counts[name] <= 1:
            out.append((rel, cls, name, lineno))
    return out


@functools.lru_cache(maxsize=1)
def tracked_pool() -> dict:
    """入仓文本面（判据口径的全部依据）→ `{相对路径: 文本}`。

    `lru_cache`（2026-10-01）：本件现在有 5 条判据都要这份全仓文本面，逐个重读一遍是纯浪费
    （实测该文件一度要 ~54 s）。文本面在**同一进程内**不变 ⇒ 缓存安全；变异自证用的是
    合成 pool，不经过本函数。
    """
    # `-z`：默认输出会把非 ASCII 路径转义加引号（见 test_live_doc_counts 同款注释），
    # 按空白切分会让整批中文名件从**引用面**里消失（判据变成「只看 ASCII 名」的假绿）。
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=str(ROOT), capture_output=True,
                            text=True, encoding="utf-8", errors="replace",
                            timeout=300).stdout.split("\0")
    pool = {}
    for rel in listed:
        if not rel:
            continue
        if Path(rel).suffix not in SUFFIXES:
            continue
        p = ROOT / rel
        try:
            pool[rel] = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return pool


class DeadCodeGateTest(unittest.TestCase):
    def test_no_zero_reference_functions(self):
        dead = zero_ref_defs(tracked_pool())
        self.assertEqual([], dead, "零引用函数（修复指引：删掉，或接线到生产面并补判据）：%s"
                         % dead)

    def test_no_test_only_modules(self):
        """core 模块不得「只被自己的单测引用」——那是不可达路径（能力写完没人能调到）。"""
        got = test_only_modules(tracked_pool())
        self.assertEqual([], got, "只有单测引用的 core 模块（修复指引：接线到生产面"
                         "（CLI/其它 core），确属死件则删掉并下调 §TEST_ONLY_ALLOWED）：%s"
                         % got)

    def test_no_import_only_functions(self):
        """顶层函数不得「只被 import、从未被调用」——import 会把它伪装成「有人用」。"""
        got = import_only_defs(tracked_pool())
        self.assertEqual([], got, "只被 import 引用（从未被调用）的函数"
                         "（修复指引：接线到真实调用点，或当墓碑删掉）：%s" % got)

    def test_no_unused_imports(self):
        """文件内不得留「导入了用不到」的绑定名（死引用；ruff 的 select 刻意不含 F401）。"""
        got = unused_imports(tracked_pool())
        self.assertEqual([], got, "未使用的 import（修复指引：删掉；确属对外转发面请写清"
                         "来由并保留——来由里的名字会使其放行）：%s" % got)

    def test_no_duplicate_bodies(self):
        """不得留**逐字相同**的长函数体（同一件事一处实现；重复实现会静默漂移）。"""
        got = duplicate_bodies(tracked_pool())
        self.assertEqual([], got, "重复函数体（修复指引：收敛到叶子件单一出处，"
                         "两侧改为 import；确属两种独立实现请写明理由并在此登记）：%s" % got)


class DuplicateBodyRuleTest(unittest.TestCase):
    def test_predicate_flags_verbatim_and_spares_variants(self):
        """变异自证：逐字相同的长函数体必判红；细节不同、太短的不许误报。"""
        same = ("def a(x):\n    n = 0\n    for i in x:\n        n += i\n    n += 1\n"
                "    n += 2\n    n += 3\n    n += 4\n    n += 5\n    n += 6\n"
                "    n += 7\n    n += 8\n    return n\n")
        other = same.replace("n += 7", "n += 70")
        short = "def tiny(x):\n    return x + 1\n"
        pool = {
            "desktop/src/core/p.py": same,
            "desktop/src/core/q.py": same,
            "desktop/src/core/r.py": other,      # 细节不同 ⇒ 不是重复
            "desktop/src/core/s.py": short,      # 太短 ⇒ 不看
        }
        got = duplicate_bodies(pool, targets=("desktop/src/core",))
        self.assertEqual(1, len(got), got)
        names = sorted(n for _f, n, _l in got[0][1])
        self.assertEqual(["a", "a"], names)
        pool["desktop/src/core/q.py"] = other.replace("n += 8", "n += 9")
        self.assertEqual([], duplicate_bodies(pool, targets=("desktop/src/core",)))


class UnusedImportRuleTest(unittest.TestCase):
    def test_predicate_flags_dead_and_spares_reexport(self):
        """变异自证：死 import 必判红；对外转发（来由写明）、`__future__`、`*` 不许误报。"""
        pool = {
            "desktop/src/core/a.py": ("from __future__ import annotations\n"
                                      "import json\n"
                                      "import os as _os\n"
                                      "from core import b\n"
                                      "from core.c import *\n\n"
                                      "print(b)\n"),
            "desktop/src/core/b.py": "VALUE = 1\n",
            "desktop/src/core/c.py": "VALUE = 2\n",
        }
        got = {n for _f, n, _l in unused_imports(pool)}
        self.assertIn("json", got, "死 import 必须判红")
        self.assertIn("_os", got, "别名形式也要能抓")
        self.assertNotIn("annotations", got, "__future__ 是编译指令")
        self.assertNotIn("b", got, "真被调用不许误报")
        # 兼容转发：来由里点名的名字放行（本仓 parse_frontmatter 同型）
        pool["desktop/src/core/d.py"] = ("from core.c import VALUE\n"
                                         "# `VALUE` 是对外转发面（调用点零改动）\n")
        self.assertNotIn("VALUE", {n for _f, n, _l in unused_imports(pool)})


class ImportOnlyRuleTest(unittest.TestCase):
    def test_predicate_flags_import_only_and_spares_called(self):
        """变异自证：只被 import 必判红；真被调用、被文档提及、被字符串派发都不许误报。"""
        pool = {
            "desktop/src/core/a.py": ("def unused_after_import():\n    return 1\n\n\n"
                                      "def called():\n    return 2\n\n\n"
                                      "def dispatched():\n    return 3\n\n\n"
                                      "TABLE = {'x': dispatched}\n"),
            "desktop/src/core/b.py": ("from core.a import unused_after_import\n"
                                      "from core.a import called\n\n"
                                      "called()\n"),
            "docs/note.md": "实现见 `dispatched`（文档面提及即豁免）。\n",
        }
        got = {n for _f, n, _l in import_only_defs(pool)}
        self.assertIn("unused_after_import", got, "只被 import 的函数必须判红")
        self.assertNotIn("called", got, "真被调用不许误报")
        self.assertNotIn("dispatched", got, "字符串派发/文档提及不许误报")


class TestOnlyRuleTest(unittest.TestCase):
    def test_predicate_flags_test_only_and_spares_wired(self):
        """变异自证：只被测试引用必判红；被生产面（其它 core / scripts）引用不许误报。"""
        pool = {
            "desktop/src/core/orphan.py": "def f():\n    return 1\n",
            "desktop/src/core/wired.py": "def g():\n    return 2\n",
            "desktop/src/core/caller.py": "from core import wired\n\nwired.g()\n",
            "desktop/tests/test_orphan.py": "from core import orphan\n\norphan.f()\n",
            "scripts/entry.py": "from core import caller\n\ncaller\n",
        }
        got = {name for _rel, name in test_only_modules(pool)}
        self.assertIn("orphan", got, "只被单测引用的模块必须判红")
        self.assertNotIn("wired", got, "被其它 core 引用不许误报")
        self.assertNotIn("caller", got, "被 scripts 引用不许误报")
        # 生产面一提即豁免
        pool["scripts/entry.py"] = "from core import orphan\n\norphan.f()\n"
        self.assertNotIn("orphan", {name for _r, name in test_only_modules(pool)})


class ConstantRuleTest(unittest.TestCase):
    """零引用**模块级常量**：本轮实测 12 处（含退役端壳遗留的 `PIPELINE_ALIASES` /
    `DOC_TEMPLATE`）——按「注意辨别」逐条核过（全仓文本只有定义行一处）后删除，本件保证不再长回来。
    """

    def test_no_zero_ref_constants(self):
        dead = zero_ref_constants(tracked_pool())
        self.assertEqual([], dead, "零引用模块级常量（修复指引：删掉，或接线到生产面/文档并补判据）："
                                   "%s" % dead)

    def test_rule_catches_mutation_and_keeps_referenced(self):
        """变异自证：无人用的大写常量必判红；同文件用、跨文件用、文档提及都不许误报。"""
        pool = {
            "desktop/src/core/a.py": ("LONELY_CONST = 1\n"
                                      "USED_HERE = 2\n"
                                      "SHORT = 3\n\n"
                                      "def f():\n"
                                      "    return USED_HERE\n"),
            "desktop/src/core/b.py": "from core import a\nprint(a.USED_HERE)\n",
            "docs/note.md": "见 `SHORT`（文档提及即豁免；且短名本就不判）。\n",
        }
        got = [n for _f, n, _l in zero_ref_constants(pool, targets=("desktop/src/core",))]
        self.assertEqual(["LONELY_CONST"], got, "变异未被准确抓到：%s" % got)


class ZeroRefRuleTest(unittest.TestCase):
    def test_predicate_flags_only_truly_unreferenced(self):
        """变异自证：无人叫的必判红；同文件派发、跨文件调用、文档提及都不许误报。"""
        pool = {
            "desktop/src/core/a.py": ("def lonely():\n    return 1\n\n\n"
                                      "def dispatched():\n    return 2\n\n\n"
                                      "TABLE = {'x': dispatched}\n"),
            "desktop/src/core/b.py": "from core import a\n\na.dispatched()\n",
            "docs/note.md": "实现见 `lonely_or_not`：本文提到的名字不算零引用。\n"
                            "另见 `a.lonely`（文档面提及即豁免）。\n",
        }
        got = zero_ref_defs(pool, targets=("desktop/src/core",))
        self.assertEqual([], got, "文档/同文件提及被误报：%s" % got)
        pool.pop("docs/note.md")
        got = zero_ref_defs(pool, targets=("desktop/src/core",))
        self.assertIn(("desktop/src/core/a.py", "lonely", 1), got)
        self.assertNotIn("dispatched", [n for _f, n, _l in got])


#: 已复核「不引用也不删」的 core 模块 → 理由（当前为空；有例外必须逐条写明）。
REVIEWED_UNREFERENCED: dict = {}

#: core 模块被「引用」的写法（缺一种就会把活模块判成墓碑）：
#: - `from .x import` / `from ..x import`：包内相对导入（**首版探针就漏在这个**：
#:   `exporter.py` 用 `from .skill_adapter import export_skill`，漏了它会把 skill_adapter
#:   误判成零引用模块）；
#: - `from core import x` / `from core.x import` / `core.x`：绝对写法；
#: - `x.py`：启动器/工作流直接按路径调用；
#: - `-m core.x`：模块入口。
_MODULE_REF_PATTERNS = (
    r"from\s+\.{{1,2}}{stem}\b",
    r"from\s+{stem}\b",
    r"import\s+{stem}\b",
    r"from\s+core\s+import\s+[^\n]*\b{stem}\b",
    r"from\s+core\.{stem}\b",
    r"core\.{stem}\b",
    r"{stem}\.py\b",
    r"-m\s+core\.{stem}\b",
)


def module_ref_file(stem: str, pool: dict):
    """某个 core 模块被哪个（非自身的）文件引用 → 该文件路径；全仓没有 → None。"""
    for rel, text in pool.items():
        if rel.endswith("/%s.py" % stem):
            continue
        for pat in _MODULE_REF_PATTERNS:
            if re.search(pat.format(stem=re.escape(stem)), text):
                return rel
    return None


class ModuleReachabilityTest(unittest.TestCase):
    """**模块级墓碑**门禁：`desktop/src/core/*.py` 每个模块都要有真引用（导入 / 启动）。

    依据（2026-10-01）：函数级零引用有判据（`DeadCodeGateTest`），模块级此前只有**一次性**盘点。
    本件把「core 里不许有没人用的模块」变成常驻判据；`辨别` 交给 `REVIEWED_UNREFERENCED`
    （当前为空：全 143 个模块在严格口径下都有引用）。口径比函数级**更严**：函数级认「文档里提过
    就算」，模块级只认**代码面**（py / sh / yml）的导入或启动——文档提到一个没人 import 的模块，
    那仍是墓碑。
    """

    def test_real_repo_core_modules_are_all_referenced(self):
        pool = tracked_pool()
        stems = sorted(p.stem for p in (ROOT / "desktop" / "src" / "core").glob("*.py")
                       if p.stem != "__init__")
        self.assertGreater(len(stems), 100, "没扫到 core 模块（判据可能已失效）")
        unref = sorted(s for s in stems if s not in REVIEWED_UNREFERENCED
                       and module_ref_file(s, pool) is None)
        self.assertEqual([], unref,
                         "core 有零引用模块（修复指引：删掉，或写进 REVIEWED_UNREFERENCED 说明"
                         "为什么它没有引用却必须在场）：%s" % unref)

    def test_relative_import_pattern_is_required(self):
        """非空转 + 变异自证：至少要有一个模块**只有相对导入**能认出来。

        否则本判据的模式集退化成「只认绝对导入」，会把活模块误判成墓碑——首版探针正是漏了
        `from .skill_adapter import …` 这一种写法。
        """
        pool = tracked_pool()
        only_relative = []
        for p in (ROOT / "desktop" / "src" / "core").glob("*.py"):
            if p.stem == "__init__":
                continue
            rel_patterns = _MODULE_REF_PATTERNS[:1]
            abs_patterns = _MODULE_REF_PATTERNS[1:]
            hit_rel = any(re.search(pat.format(stem=re.escape(p.stem)), text)
                          for rel, text in pool.items()
                          if not rel.endswith("/%s.py" % p.stem)
                          for pat in rel_patterns)
            hit_abs = any(re.search(pat.format(stem=re.escape(p.stem)), text)
                          for rel, text in pool.items()
                          if not rel.endswith("/%s.py" % p.stem)
                          for pat in abs_patterns)
            if hit_rel and not hit_abs:
                only_relative.append(p.stem)
        self.assertTrue(only_relative,
                        "没有任何模块只能靠相对导入认出——模式集退化了（本判据会误杀）")

    def test_exemptions_are_not_stale(self):
        pool = tracked_pool()
        stale = [s for s in REVIEWED_UNREFERENCED if module_ref_file(s, pool) is not None]
        self.assertEqual([], stale, "REVIEWED_UNREFERENCED 有失效条目（已恢复引用）：%s" % stale)


class MethodRuleTest(unittest.TestCase):
    """**类方法级**墓碑（`zero_ref_defs` 只覆盖顶层函数，方法面此前无人管）。"""

    def test_no_zero_ref_methods_outside_implicit_hooks(self):
        pool = tracked_pool()
        self.assertGreaterEqual(len(method_defs(pool)), 60,
                                "方法面塌缩（判据可能已失效）")
        found = zero_ref_methods(pool)
        keys = {"%s::%s.%s" % (rel, cls, name) for rel, cls, name, _ln in found}
        self.assertEqual(set(), keys - set(IMPLICIT_HOOKS),
                         "零引用类方法（修复指引：接线到调用点，或当墓碑删掉；框架按名隐式调用的"
                         "钩子请写进 IMPLICIT_HOOKS 并写明理由）：%s" % sorted(keys))

    def test_implicit_hook_table_is_not_stale(self):
        """本表只许缩小：条目对应的方法**一旦不在场**（删了/改名了）就必须删掉。

        判别口径（2026-10-02 踩过两次坑后钉死）：**只认「方法定义是否仍在场」**。
        第一版用「不带豁免重算零引用」——表里的条目被自己滤掉，必然自判「失效」；
        第二版改成「全仓是否出现调用形」——**本仓的引用面包含 CHANGELOG 与文档**，一句
        「代码里永远不会调用它」的说明就会把条目判成陈旧（自己的说明文字把它救活了）。
        故这里只问一件不可能被文字左右的事：定义在不在。
        """
        present = {"%s::%s.%s" % (rel, cls, name)
                   for rel, cls, name, _ln in method_defs(tracked_pool())}
        self.assertEqual(set(), set(IMPLICIT_HOOKS) - present,
                         "IMPLICIT_HOOKS 有陈旧条目（方法已不在场，该删）：%s"
                         % sorted(set(IMPLICIT_HOOKS) - present))

    def test_method_predicate_has_catch_power(self):
        """变异自证：没人叫的方法必判红；`self.x()` 调用的、魔法方法不许误报。"""
        pool = {
            "desktop/src/core/synth.py":
                "class C:\n"
                "    def used(self):\n        return 1\n"
                "    def _dead(self):\n        return 2\n"
                "    def caller(self):\n        return self.used()\n"
                "    def __len__(self):\n        return 0\n",
            "scripts/user.py": "from core.synth import C\n\n\nC().caller()\n",
        }
        self.assertEqual([("desktop/src/core/synth.py", "C", "_dead", 4)],
                         zero_ref_methods(pool))
        self.assertEqual([], zero_ref_methods(pool, hooks={
            "desktop/src/core/synth.py::C._dead": "刻意留作的登记样例（自证用）"}))


if __name__ == "__main__":
    unittest.main()
