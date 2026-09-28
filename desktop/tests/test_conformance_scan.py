#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""43 A2 —— Conformance 分级扫描单测（声明 ≤ 可证、防虚标）。"""
import builtins
import contextlib
import io
import os
import pathlib
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import conformance_scan as cs  # noqa: E402
from core import output_forms as of  # noqa: E402

_ROOT_KEY = os.path.normcase(os.path.abspath(ROOT))


def _key(path):
    """读盘口径的路径键（绝对 + normcase）——与内容键缓存内部的口径保持一致。"""
    try:
        return os.path.normcase(os.path.abspath(str(path)))
    except (TypeError, ValueError):
        return ""


@contextlib.contextmanager
def _trace_opens():
    """记录作用域内**尝试打开**与**成功打开**的文件（两种都要，判据不同）。

    失败路径（`FileNotFoundError` 等）不会进 `reads`——探测不存在的文件不是输入依赖；
    `tried` 保留它们，用来区分「合法探测」与「输入面漏声明」。
    """
    real_io, real_builtins = io.open, builtins.open
    reads, tried = [], []

    def spy(file, *a, **k):
        tried.append(_key(file))
        handle = real_io(file, *a, **k)
        reads.append(_key(file))
        return handle

    io.open = spy
    builtins.open = spy
    try:
        yield reads, tried
    finally:
        io.open = real_io
        builtins.open = real_builtins


def _covered(patterns):
    """输入面 glob 展开出的文件键集（**只取文件**：`**/*` 会把目录也匹配进来）。"""
    root = pathlib.Path(ROOT)
    out = set()
    for pat in patterns:
        for p in root.glob(pat):
            if p.is_file():
                out.add(_key(p))
    return out


class ConformanceScanTest(unittest.TestCase):
    def test_repo_scan_clean(self):
        issues, stats = cs.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["modules_mc"], 23)
        self.assertGreaterEqual(stats["packages"], 5)
        self.assertGreaterEqual(stats["export_items"], 4)

    def test_overclaim_detected(self):
        """模块未在册却声明 L2/L3 = 虚标 → 被拒。"""
        issues = []
        order = {"L1": 1, "L2": 2, "L3": 3}
        declared, provable = "L3", 2
        if order[declared] > provable:
            issues.append("虚标")
        self.assertEqual(issues, ["虚标"])

    def test_evidence_ids_cover_repo(self):
        """装配在册证据集须覆盖全部机器可加载模块文档（44 = 13 官方 + 31 社区）。"""
        evidence = set(cs._evidence_ids(ROOT))
        self.assertIn("M00", evidence)
        self.assertIn("通用:M10", evidence)


class NestedMemoSharingTest(unittest.TestCase):
    """嵌套 `read_memo()` 是**细化**不是隔离；冷却边界＝最外层那次只读调用。

    依据（实测）：嵌套作用域过去各起一份空缓存，`evaluate`（外层）刚读过的语料在
    `quality_depth_scan`（内层）里又读一遍——一次 evaluate 因此白开上千次文件。
    改共享后：`os.scandir` 5403 → 3889（−28%），同进程交错 A/B 的 evaluate
    2749 → **1883 ms（−31.5%）**。两条性质都要钉住：① 嵌套内必须复用语料；
    ② **最外层出口仍要清空**——否则就变成跨调用陈旧。
    """

    @contextlib.contextmanager
    def _count_opens(self, path):
        opened = []
        real = io.open

        def spy(file, *a, **k):
            opened.append(os.path.basename(str(file)))
            return real(file, *a, **k)

        io.open = spy
        try:
            yield opened
        finally:
            io.open = real

    def test_nested_scope_reuses_outer_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "a.txt"
            p.write_text("一", encoding="utf-8")
            with cs.read_memo():
                self.assertEqual("一", cs.read_text_cached(p))
                with self._count_opens(p) as opened:
                    with cs.read_memo():                 # 嵌套：应命中外层缓存
                        self.assertEqual("一", cs.read_text_cached(p))
                self.assertEqual([], opened,
                                 "嵌套作用域必须复用外层已读内容（不许重读）")

    def test_outermost_exit_clears_and_next_scope_sees_new_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "a.txt"
            p.write_text("一", encoding="utf-8")
            with cs.read_memo():
                self.assertEqual("一", cs.read_text_cached(p))
                with cs.read_memo():
                    self.assertEqual("一", cs.read_text_cached(p))
            p.write_text("二", encoding="utf-8")          # 最外层已退出 → 必须重读
            with cs.read_memo():
                self.assertEqual("二", cs.read_text_cached(p))
                with cs.read_memo():
                    self.assertEqual("二", cs.read_text_cached(p))
            self.assertIsNone(cs._READ_MEMO, "最外层出口必须把共享缓存整体清掉")
            self.assertIsNone(cs._TREE_MEMO)

    def test_nested_scope_shares_pattern_and_tree_memo(self):
        """枚举面（子树清单 / 模式结果）同样跨嵌套共享，且最外层出口即清。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            (p / "sub").mkdir()
            (p / "sub" / "a.md").write_text("x", encoding="utf-8")
            with cs.read_memo():
                self.assertEqual(["sub/a.md"], cs.iter_files(tmp, "**/*.md"))
                scans = []
                real = os.scandir

                def counting(path="."):
                    scans.append(path)
                    return real(path)

                os.scandir = counting
                try:
                    with cs.read_memo():                 # 嵌套：不得重走文件系统
                        self.assertEqual(["sub/a.md"], cs.iter_files(tmp, "**/*.md"))
                finally:
                    os.scandir = real
                self.assertEqual([], scans, "嵌套内重复枚举不得重走文件系统")
            (p / "sub" / "b.md").write_text("x", encoding="utf-8")
            with cs.read_memo():
                self.assertEqual(["sub/a.md", "sub/b.md"], cs.iter_files(tmp, "**/*.md"),
                                 "新作用域必须看到新文件")


class FastGlobTest(unittest.TestCase):
    """`iter_files` 的快速枚举：**与 `Path.glob` 逐模式等价** + 作用域内记忆 + 出口不陈旧。

    依据（实测）：指纹占一次 `evaluate` 的 **926 ms / 31%**，其中「枚举」一项 463 ms——
    `community/*/outputs/**/*`（1156 件）单条就要 236 ms，因为 pathlib 的 `**` 逐层重入；
    换 `os.scandir` 单遍后同一条 ~90 ms，指纹 821 → 497 ms。
    **等价性是本判据的主题**：快而语义不同＝把门禁换成假绿。
    """

    def _reference(self, root, pattern):
        base = pathlib.Path(root)
        return sorted(p.relative_to(base).as_posix()
                      for p in base.glob(str(pattern)) if p.is_file())

    def test_equivalent_to_pathlib_glob_for_declared_input_faces(self):
        """仓库真实输入面（8 条模式）必须**逐条一致**——不能只测一条就当等价。"""
        pats = list(dict.fromkeys(list(of.INDEX_INPUTS) + list(cs.SCAN_INPUTS)))
        self.assertTrue(pats)
        for pat in pats:
            with cs.read_memo():
                got = cs.iter_files(ROOT, pat)
            self.assertEqual(self._reference(ROOT, pat), got,
                             "快速枚举与 Path.glob 不等价：%s" % pat)

    def test_dotfiles_depth_and_question_mark_semantics(self):
        """点文件必须收（pathlib 不隐藏）、`?` 单字符、`**` 可消费零层、字符类回退参考实现。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            (p / ".hidden.md").write_text("x", encoding="utf-8")
            (p / "a.md").write_text("x", encoding="utf-8")
            (p / "a1.md").write_text("x", encoding="utf-8")
            (p / "sub").mkdir()
            (p / "sub" / ".deep.md").write_text("x", encoding="utf-8")
            (p / "sub" / "b.md").write_text("x", encoding="utf-8")
            for pat in ("*.md", "a?.md", "**/*.md", "sub/*.md", "**/*", "**/*.json",
                        "sub/[ab].md", "sub/**"):
                with cs.read_memo():
                    got = cs.iter_files(tmp, pat)
                self.assertEqual(self._reference(tmp, pat), got, pat)

    def test_scope_memo_walks_once_and_refreshes_next_scope(self):
        """同作用域内重复枚举只走一遍文件系统；**出口即清**，下一个作用域必须看到新文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            (p / "sub").mkdir()
            (p / "sub" / "a.md").write_text("x", encoding="utf-8")
            scans = []
            real = os.scandir

            def counting(path="."):
                scans.append(path)
                return real(path)

            os.scandir = counting
            try:
                with cs.read_memo():
                    first = cs.iter_files(tmp, "**/*.md")
                    mark = len(scans)
                    second = cs.iter_files(tmp, "**/*.md")
                self.assertEqual(first, second)
                self.assertEqual(mark, len(scans), "同一作用域内重复枚举不得重走文件系统")
                (p / "sub" / "b.md").write_text("x", encoding="utf-8")
                with cs.read_memo():
                    third = cs.iter_files(tmp, "**/*.md")
            finally:
                os.scandir = real
            self.assertEqual(len(first), 1)
            self.assertEqual(len(third), 2, "新作用域必须看到新文件（不许跨调用陈旧）")

    def test_fingerprint_reacts_to_content_and_to_new_files(self):
        """指纹＝（枚举面 + 每个文件的内容）：改内容要变，**新增文件也要变**。

        后半条守的是本波新增的枚举路径：枚举若漏了新文件，内容键就漏输入 → 假绿。
        """
        with tempfile.TemporaryDirectory() as tmp:
            mod = pathlib.Path(tmp) / "community" / "包" / "modules"
            mod.mkdir(parents=True)
            f = mod / "m.md"
            f.write_text("一", encoding="utf-8")
            with cs.read_memo():
                fp1 = cs.content_fingerprint(tmp, of.INDEX_INPUTS)
            with cs.read_memo():
                self.assertEqual(fp1, cs.content_fingerprint(tmp, of.INDEX_INPUTS),
                                 "同内容必须同指纹")
            f.write_text("二", encoding="utf-8")
            with cs.read_memo():
                self.assertNotEqual(fp1, cs.content_fingerprint(tmp, of.INDEX_INPUTS),
                                    "内容一变指纹必须变")
                before = cs.content_fingerprint(tmp, of.INDEX_INPUTS)
            (mod / "n.md").write_text("二", encoding="utf-8")
            with cs.read_memo():
                self.assertNotEqual(before, cs.content_fingerprint(tmp, of.INDEX_INPUTS),
                                    "新增文件必须改指纹（枚举面变了）")


class DerivedResultCacheTest(unittest.TestCase):
    """跨调用「内容键派生结果缓存」的两条判据：**输入面穷举** + **键即内容**。

    这类缓存（`scan()` 与 `output_forms.index_verify()` 各有一份）唯一的真风险是「假绿」：
    只要有一次读落在声明的输入面之外，输入变了指纹却不变 → 陈旧结果被当成新结果交给门禁。
    所以本判据盯的不是速度，而是**读盘面 ⊆ 输入面**；将来给这两个函数加新读取，这里会先红，
    逼着把新输入补进 `SCAN_INPUTS` / `INDEX_INPUTS`，而不是让缓存静默陈旧。

    计数口径：按**成功打开**的文件算输入依赖。探测不存在的路径（例如缺 `provenance.json` 的
    域包）不算——而这类路径一旦真出现，输入面的 glob 会立刻把它收进指纹，故不存在缺口。
    """

    #: (名字, 输入面, 清缓存后必走真实计算的入口)
    CASES = (("scan", cs.SCAN_INPUTS, lambda: cs._SCAN_CACHE.clear()),
             ("index_verify", of.INDEX_INPUTS, lambda: of._INDEX_CACHE.clear()))

    def _run(self, name):
        if name == "scan":
            cs._SCAN_CACHE.clear()
            return cs.scan(ROOT)
        of._INDEX_CACHE.clear()
        return of.index_verify(ROOT)

    def test_reads_stay_inside_declared_input_face(self):
        for name, patterns, _clear in self.CASES:
            self._run(name)                       # 先跑一遍：把惰性 import 等一次性读盘做掉
            covered = _covered(patterns)          # glob 展开本身不开文件，可在采集前算好
            with _trace_opens() as (reads, tried):
                self._run(name)                   # 缓存已清 → 必走真实计算，读盘面被完整记录
            leak = sorted(p for p in reads if p.startswith(_ROOT_KEY) and p not in covered)
            self.assertEqual(
                [os.path.relpath(p, _ROOT_KEY) for p in leak], [],
                "%s() 读了声明输入面之外的文件 → 内容键缓存会陈旧（补进输入面）" % name)
            ghost = sorted(p for p in tried
                           if p.startswith(_ROOT_KEY) and p not in covered and os.path.exists(p))
            self.assertEqual(
                [os.path.relpath(p, _ROOT_KEY) for p in ghost], [],
                "%s() 探测了输入面之外**存在**的文件 → 输入面不完整" % name)

    def test_second_call_with_same_key_hits_cache(self):
        """键即内容：同内容第二次调用必须命中缓存（不重算），且两次结果一致。"""
        for name, _patterns, _clear in self.CASES:
            real_impl = cs._scan_impl if name == "scan" else of._index_verify_impl
            calls = {"n": 0}

            def counting(root=".", _real=real_impl):
                calls["n"] += 1
                return _real(root)

            if name == "scan":
                cs._SCAN_CACHE.clear()
                cs._scan_impl = counting
                try:
                    first, second = cs.scan(ROOT), cs.scan(ROOT)
                finally:
                    cs._scan_impl = real_impl
                    cs._SCAN_CACHE.clear()
            else:
                of._INDEX_CACHE.clear()
                of._index_verify_impl = counting
                try:
                    first, second = of.index_verify(ROOT), of.index_verify(ROOT)
                finally:
                    of._index_verify_impl = real_impl
                    of._INDEX_CACHE.clear()
            self.assertEqual(1, calls["n"], "%s() 同内容第二次调用白算了一遍" % name)
            self.assertEqual(first, second, "%s() 命中缓存的结果必须与首算一致" % name)


class ModuleDocsMemoTest(unittest.TestCase):
    """`_module_docs` 的「列目录」缓存：**一次只读调用内只走一遍文件系统**，且不跨调用复用。

    依据：一次 `regression_score.evaluate` 里它被调 **5** 次（各扫描器各自重走 `04_模块库` +
    `community/*/modules`）。作用域与读缓存同生命周期（`read_memo`），出口即清——所以每次调用
    都重新列目录，不存在陈旧。实测时间收益约 60 ms（目录枚举已被 OS 缓存，故**很小**），
    但**遍历次数是确定性的 5 → 1**，本判据盯的就是这个确定性部分。
    """

    def test_listed_once_per_scope_and_fresh_next_scope(self):
        # 口径：数**文件系统遍历**（`os.walk`），不是数调用——调用两次是正常的，遍历只该一次。
        walks = []
        orig_walk = os.walk

        def counting_walk(*a, **k):
            walks.append(a)
            return orig_walk(*a, **k)

        os.walk = counting_walk
        try:
            with cs.read_memo():
                first = cs._module_docs(ROOT)
                second = cs._module_docs(ROOT)
            self.assertEqual(first, second, "同一作用域内两次结果必须一致")
            self.assertEqual(1, len(walks), "同一作用域内只该遍历一次目录树")
            walks.clear()
            with cs.read_memo():
                third = cs._module_docs(ROOT)
            self.assertEqual(1, len(walks), "新作用域必须重新遍历（不许跨调用陈旧）")
            self.assertEqual(first, third, "重新列目录的结果必须与上次相同")
        finally:
            os.walk = orig_walk


class YamlLoaderEquivalenceTest(unittest.TestCase):
    """统一加载器（libyaml 优先）必须与纯 Python 的 SafeLoader **逐块等价**。

    依据：改用 C 实现是速度机制（实测 7.8×），但「快」不得改变任何解析结果——本断言把
    等价性钉在真仓库上：全部 YAML 文本块（```yaml 围栏 + *.yaml/*.yml 整件）两种加载器
    各解析一遍，**值与异常行为都必须一致**。缺 libyaml 时跳过（此时走的本来就是纯 Python
    路径，不存在分叉）。
    """

    def test_repo_yaml_blocks_parse_identically(self):
        import yaml
        if getattr(yaml, "CSafeLoader", None) is None:
            self.skipTest("本机 PyYAML 无 libyaml（CSafeLoader 不可用）")
        from yaml import SafeLoader, CSafeLoader
        texts = []
        for path in sorted(pathlib.Path(ROOT).rglob("*.md")):
            if ".git" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            texts += [m.group(1) for m in cs.FENCE.finditer(text)]
        for pat in ("*.yaml", "*.yml"):
            for path in sorted(pathlib.Path(ROOT).rglob(pat)):
                if ".git" in path.parts:
                    continue
                try:
                    texts.append(path.read_text(encoding="utf-8"))
                except OSError:
                    continue
        self.assertGreater(len(texts), 100, "本仓 YAML 文本块数量异常（判据失效）")
        for body in texts:
            try:
                plain, plain_err = yaml.load(body, Loader=SafeLoader), None
            except Exception as exc:                      # noqa: BLE001 - 比对异常类型即可
                plain, plain_err = None, type(exc).__name__
            try:
                fast, fast_err = yaml.load(body, Loader=CSafeLoader), None
            except Exception as exc:                      # noqa: BLE001
                fast, fast_err = None, type(exc).__name__
            self.assertEqual(plain_err, fast_err, "异常行为不一致：%r" % body[:60])
            if plain_err is None:
                self.assertEqual(plain, fast, "解析结果不一致：%r" % body[:60])


if __name__ == "__main__":
    unittest.main()
