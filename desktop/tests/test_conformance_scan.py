#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""43 A2 —— Conformance 分级扫描单测（声明 ≤ 可证、防虚标）。"""
import builtins
import contextlib
import io
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import asset_density as ad  # noqa: E402
from core import asset_ledger_projection as alp  # noqa: E402
from core import conformance_scan as cs  # noqa: E402
from core import concept_graph as cg  # noqa: E402
from core import disk_cache  # noqa: E402
from core import domain_pack as dpk  # noqa: E402
from core import layer_model as lm  # noqa: E402
from core import output_forms as of  # noqa: E402
from core import pack_combo as pcb  # noqa: E402
from core import purity_scan as ps  # noqa: E402
from core import quality_depth_scan as qd  # noqa: E402
from core import schema_lint as sl  # noqa: E402

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


class FingerprintRobustnessTest(unittest.TestCase):
    """内容指纹对**非 UTF-8 附件**必须按字节取，不许整体崩掉。

    依据（实测）：把输入面放宽到「整个仓库」时立刻踩到——`community/**/*`、`docs/**/*` 里只要
    有一张图片/一个二进制附件，`read_text` 就抛 `UnicodeDecodeError`，**整条命令直接失败**。
    这等于「多放一个附件」＝「命令崩」；指纹本就只需要"变了没有"，按字节哈希是更稳也更省的取法
    （文本件仍走文本路径，故哈希值与既有口径逐位相同、不失效任何现有缓存）。
    """

    def test_binary_payload_is_hashed_by_bytes_and_stays_sensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = pathlib.Path(tmp) / "community" / "包" / "assets"
            d.mkdir(parents=True)
            (d / "A.md").write_text("A01 键\n", encoding="utf-8")
            (d / "cover.png").write_bytes(b"\x89PNG\r\n\x1a\n\xa7\xff")   # 非法 UTF-8 起始字节
            face = ("community/*/assets/*",)
            with cs.read_memo():
                first = cs.content_fingerprint(tmp, face)
                again = cs.content_fingerprint(tmp, face)
            self.assertEqual(first, again, "同内容必须同指纹（含二进制件）")
            (d / "cover.png").write_bytes(b"\x89PNG\r\n\x1a\n\xa7\xfe")   # 只改一个字节
            with cs.read_memo():
                changed = cs.content_fingerprint(tmp, face)
            self.assertNotEqual(first, changed, "二进制件改了也必须换指纹")


class DerivedResultCacheTest(unittest.TestCase):
    """跨调用「内容键派生结果缓存」的两条判据：**输入面穷举** + **键即内容**。

    这类缓存（`scan()` 与 `output_forms.index_verify()` 各有一份）唯一的真风险是「假绿」：
    只要有一次读落在声明的输入面之外，输入变了指纹却不变 → 陈旧结果被当成新结果交给门禁。
    所以本判据盯的不是速度，而是**读盘面 ⊆ 输入面**；将来给这两个函数加新读取，这里会先红，
    逼着把新输入补进 `SCAN_INPUTS` / `INDEX_INPUTS`，而不是让缓存静默陈旧。

    计数口径：按**成功打开**的文件算输入依赖。探测不存在的路径（例如缺 `provenance.json` 的
    域包）不算——而这类路径一旦真出现，输入面的 glob 会立刻把它收进指纹，故不存在缺口。
    """

    #: 站点表：名字 → {输入面 / 清进程内缓存 / 真算入口（供替换计数）/ 入口}
    #: 表驱动是为了「新站点接进来只加一行」，而不是每加一个就抄一遍 if/else。
    @staticmethod
    def _sites():
        return {
            "conformance_scan.scan": {
                "patterns": cs.SCAN_INPUTS,
                "clear": lambda: cs._SCAN_CACHE.clear(),
                "owner": cs, "impl": "_scan_impl",
                "run": lambda: cs.scan(ROOT)},
            "output_forms.index_verify": {
                "patterns": of.INDEX_INPUTS,
                "clear": lambda: of._INDEX_CACHE.clear(),
                "owner": of, "impl": "_index_verify_impl",
                "run": lambda: of.index_verify(ROOT)},
            "schema_lint.scan": {
                "patterns": sl.LINT_INPUTS,
                "clear": lambda: cs._DERIVED_MEMO.pop("schema-lint", None),
                "owner": sl, "impl": "_scan_impl",
                "run": lambda: sl.scan(ROOT)},
            "asset_density.scan": {
                "patterns": ad.ASSET_INPUTS,
                "clear": lambda: cs._DERIVED_MEMO.pop("asset-density", None),
                "owner": ad, "impl": "_scan_impl",
                "run": lambda: ad.scan(ROOT)},
            "asset_density.thickness_scan": {
                "patterns": ad.ASSET_INPUTS,
                "clear": lambda: cs._DERIVED_MEMO.pop("asset-thickness", None),
                "owner": ad, "impl": "_thickness_impl",
                "run": lambda: ad.thickness_scan(ROOT)},
            "layer_model.scan": {
                "patterns": lm.patterns(ROOT),
                "clear": lambda: cs._DERIVED_MEMO.pop("layer-model", None),
                "owner": lm, "impl": "_scan_impl",
                "run": lambda: lm.scan(ROOT), "resident": True},
            "purity_scan.scan": {
                "patterns": ps.patterns(ROOT),
                "clear": lambda: cs._DERIVED_MEMO.pop("purity-scan", None),
                "owner": ps, "impl": "_scan_impl",
                "run": lambda: ps.scan(ROOT), "resident": True},
            "asset_ledger_projection.verify": {
                "patterns": alp.VERIFY_INPUTS,
                "clear": lambda: cs._DERIVED_MEMO.pop("asset-ledger-verify", None),
                "owner": alp, "impl": "_verify_impl",
                "run": lambda: alp.verify(ROOT), "resident": True},
            "quality_depth_scan.scan": {
                "patterns": qd.QD_INPUTS,
                "clear": lambda: cs._DERIVED_MEMO.pop("quality-depth", None),
                "owner": qd, "impl": "_inner",
                "run": lambda: qd.scan(ROOT), "resident": True},
            "concept_graph.scan": {
                "patterns": cg.CG_INPUTS,
                "clear": lambda: cs._DERIVED_MEMO.pop("concept-graph", None),
                "owner": cg, "impl": "_scan_impl",
                "run": lambda: cg.scan(ROOT), "resident": True},
            "output_forms.scan": {
                "patterns": of.INDEX_INPUTS,
                "clear": lambda: cs._DERIVED_MEMO.pop("output-forms-scan", None),
                "owner": of, "impl": "_scan_impl",
                "run": lambda: of.scan(ROOT), "resident": True},
            "domain_pack.scan": {
                "patterns": dpk.SCAN_INPUTS,
                "clear": lambda: cs._DERIVED_MEMO.pop("domain-pack-scan", None),
                "owner": dpk, "impl": "_scan_impl",
                "run": lambda: dpk.scan(ROOT), "resident": True},
            "pack_combo.scan": {
                "patterns": pcb.SCAN_INPUTS,
                "clear": lambda: cs._DERIVED_MEMO.pop("pack-combo-scan", None),
                "owner": pcb, "impl": "_scan_impl",
                "run": lambda: pcb.scan(ROOT), "resident": True},
        }

    def _run(self, site):
        site["clear"]()
        return site["run"]()

    @contextlib.contextmanager
    def _cold(self):
        """采集读盘面时**关掉持久缓存**：否则盘上已有同内容条目 ⇒ 根本不读盘 ⇒ 判据空转。

        这条是判据强度的关键（2026-09-29 修订）：本机反复跑过之后，`<NF_HOME>/cache` 里什么都有，
        不关它的话「读盘面 ⊆ 输入面」会**全绿却什么都没验**。
        """
        with mock.patch.dict(os.environ, {"NF_NO_DISK_CACHE": "1"}):
            yield

    @contextlib.contextmanager
    def _resident(self, site):
        """宽面的站点**只在常驻语料层在位时**才走缓存——判据也得按同一条件跑，否则它永远不命中。"""
        if site.get("resident"):
            cs.install_resident(ROOT)
        try:
            yield
        finally:
            if site.get("resident"):
                cs.clear_resident()

    def test_reads_stay_inside_declared_input_face(self):
        for name, site in self._sites().items():
            with self._resident(site), self._cold():
                self._run(site)                   # 先跑一遍：把惰性 import 等一次性读盘做掉
                covered = _covered(site["patterns"])   # glob 展开本身不开文件，可在采集前算好
                with _trace_opens() as (reads, tried):
                    self._run(site)               # 缓存已清 → 必走真实计算，读盘面被完整记录
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
        """键即内容：同内容**第二次调用不得新增重算**，且两次结果一致。

        判据口径（2026-09 修订）：本函数现在有两层缓存——进程内内容键 + **持久**内容键
        （`core.disk_cache`）。于是**第一次调用也可能免算**（盘上已有同内容条目），
        所以「两次调用总共只算 1 次」不再是真不变量；真不变量是**第二次相对于第一次零新增**
        （缓存被拆掉时第二次就会新增，本判据照样当场红）。
        """
        for name, site in self._sites().items():
            owner, attr = site["owner"], site["impl"]
            real_impl = getattr(owner, attr)
            calls = {"n": 0}

            # 透传额外实参：有的站点会把「已经算好的面指纹」顺手传给自己的 impl
            # （如 `purity_scan` 把阶梯面指纹交给 `_scan_impl`，免得同一张面枚举两遍）。
            # 本判据只数**调用次数**，签名变化不该让它误报。
            def counting(root=".", *extra, _real=real_impl, **kwargs):
                calls["n"] += 1
                return _real(root, *extra, **kwargs)

            with self._resident(site):
                site["clear"]()
                setattr(owner, attr, counting)
                try:
                    first = site["run"]()
                    after_first = calls["n"]
                    second = site["run"]()
                    after_second = calls["n"]
                finally:
                    setattr(owner, attr, real_impl)
                    site["clear"]()
            self.assertEqual(after_first, after_second,
                             "%s() 同内容第二次调用白算了一遍（缓存没生效）" % name)
            self.assertEqual(first, second, "%s() 命中缓存的结果必须与首算一致" % name)


class InputFaceHygieneTest(unittest.TestCase):
    """**输入面卫生**：声明面里的每一件都要是「小件」，且不得卷进无关大文件。

    依据（2026-09-29 实测事故）：`domain_pack.SCAN_INPUTS` 原写 `.rivet/**/*`（整棵私档），于是
    「见证」要把 **676 MB**（含一个 **628 MB** 的模型文件）读一遍算摘要 ✗，而该扫描器其实只读
    那 100 份 specs。收窄之后判据仍绿。这条把它钉住：**宽面不许把大件卷进来**——输入面的宽度是
    算力，不是免费的。
    """

    #: 单件上限：远大于仓库里任何**真被当语料读**的件（最大的模块文档 ~61 KB），但足以挡住
    #: 模型/权重/压缩包这类「根本不是语料」的大件。
    MAX_BYTES = 8 * 1024 * 1024

    def test_no_declared_face_pulls_in_a_huge_file(self):
        from core import asset_ledger_projection as _alp
        from core import concept_graph as _cg
        from core import domain_pack as _dpk
        from core import layer_model as _lm
        from core import pack_combo as _pcb
        from core import purity_scan as _ps
        from core import quality_depth_scan as _qd
        from core import schema_lint as _sl
        faces = {
            "conformance_scan": cs.SCAN_INPUTS, "output_forms": of.INDEX_INPUTS,
            "schema_lint": _sl.LINT_INPUTS, "asset_density": ad.ASSET_INPUTS,
            "asset_ledger_projection": _alp.VERIFY_INPUTS, "concept_graph": _cg.CG_INPUTS,
            "domain_pack": _dpk.SCAN_INPUTS, "pack_combo": _pcb.SCAN_INPUTS,
            "quality_depth_scan": _qd.QD_INPUTS,
            "layer_model": _lm.patterns(ROOT), "purity_scan": _ps.patterns(ROOT),
        }
        offenders = []
        for name, patterns in faces.items():
            for pat in patterns:
                for rel in cs.iter_files(ROOT, str(pat)):
                    path = os.path.join(ROOT, *rel.split("/"))
                    try:
                        size = os.path.getsize(path)
                    except OSError:
                        continue
                    if size > self.MAX_BYTES:
                        offenders.append((name, rel, size))
        self.assertEqual([], ["%s: %s（%.1f MB）" % (n, r, s / 1048576)
                              for n, r, s in offenders][:5],
                         "输入面卷进了大件：见证会把它们整份读一遍（把面收窄到真读的件）")


class ResidentRawEquivalenceTest(unittest.TestCase):
    """共享读改成「**一次物理读服务两种口径**」之后，文本/字节的口径必须**逐字节不变**。

    依据（2026-09-29）：`read_text_cached` 过去用 `Path.read_text`、`read_bytes_cached` 用
    `Path.read_bytes` —— 同一份件既当文本又当字节读时**读两遍**（实测一次重算里 211 次重复读）。
    现在底层只读一次原始字节、文本由 `io.TextIOWrapper(BytesIO(raw), encoding="utf-8",
    newline=None)` 解出。判据就是「换实现不许换口径」：真语料逐件比对 + 换行/无尾换行/BOM 边界。
    """

    def test_text_matches_path_read_text_on_real_corpus(self):
        csc_module = cs
        csc_module.install_resident(ROOT)
        self.addCleanup(csc_module.clear_resident)
        checked = 0
        for base in ("protocol", "docs", "04_模块库", "01_核心协议.md", "verify.sh"):
            targets = ([base] if os.path.isfile(os.path.join(ROOT, base))
                       else [os.path.join(dp, f)
                             for dp, _dn, fs in os.walk(os.path.join(ROOT, base))
                             for f in fs][:60])
            for rel in targets:
                path = os.path.join(ROOT, rel)
                try:
                    want = pathlib.Path(path).read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                checked += 1
                self.assertEqual(want, csc_module.read_text_cached(path),
                                 "共享读的文本口径漂了：%s" % rel)
                self.assertEqual(pathlib.Path(path).read_bytes(),
                                 csc_module.read_bytes_cached(path),
                                 "共享读的字节口径漂了：%s" % rel)
        self.assertGreater(checked, 40, "真语料样本太少，判据没意义")

    def test_newline_and_bom_boundaries(self):
        """CRLF / 单 \r / 无尾换行 / BOM —— 通用换行语义最容易在这几处漂。"""
        cases = (b"a\r\nb\r\nc", b"a\rb\rc", b"a\nb\nc", b"a\nb\nc\n",
                 b"\xef\xbb\xbfhello\n", b"", b"tail-no-newline")
        cs.install_resident(ROOT)
        self.addCleanup(cs.clear_resident)
        with tempfile.TemporaryDirectory() as tmp:
            for i, raw in enumerate(cases):
                path = os.path.join(tmp, "n%d.txt" % i)
                with open(path, "wb") as fh:
                    fh.write(raw)
                self.assertEqual(pathlib.Path(path).read_text(encoding="utf-8"),
                                 cs.read_text_cached(path), raw)
                self.assertEqual(raw, cs.read_bytes_cached(path))
                cs.clear_resident()             # 每例都从空层走一遍真读
                cs.install_resident(ROOT)


class CodeScopeFaceTest(unittest.TestCase):
    """代码面**按导入闭包**细化（`disk_cache.key(..., code_modules=…)`）：精度 / fail-closed / 完整性。

    动机（实测）：整块代码面 119 件 ⇒ 改**任何**一个 core 文件都会让所有落盘派生换键，下一条重命令
    付一次全量重建（~4–6 s）；而多数派生只依赖 3–21 件。三条判据分别盯三件事：
    ① **精度**：闭包只含自己及其依赖（无关件如 `terminal.py` 不得在内）；
    ② **fail-closed**：闭包里一旦出现动态导入构造（`__import__` / `importlib`）就判「说不清」
       （返回 None ⇒ 调用方退回整块代码面，绝不拿不完整的闭包当键）；
    ③ **完整性（运行时）**：在**全新解释器**里真跑一遍该派生，期间被导入的 `core.*` 模块
       必须全部落在声明闭包内——静态分析漏判会在这里红。
    """

    #: 站点 → (自己的模块, 真算入口)。与各站点源码里的 `code_modules=` 声明一一对应（漂移即红）。
    SITES = (("core.schema_lint", "_scan_impl"),
             ("core.asset_density", "_thickness_impl"),
             ("core.asset_ledger_projection", "_verify_impl"),
             ("core.layer_model", "_scan_impl"),
             ("core.purity_scan", "_scan_impl"),
             ("core.quality_depth_scan", "_inner"),
             ("core.conformance_scan", "_scan_impl"),
             ("core.output_forms", "_index_verify_impl"),
             ("core.pack_combo", "scan"))

    def test_scope_is_precise_and_fails_closed(self):
        scope = disk_cache.code_scope_files(ROOT, ("core.schema_lint",))
        self.assertIsNotNone(scope, "schema_lint 的闭包应当算得出")
        self.assertIn("desktop/src/core/schema_lint.py", scope)
        self.assertNotIn("desktop/src/core/terminal.py", scope,
                         "无关模块不得进闭包（否则等于退回整块代码面）")
        self.assertLess(len(scope), 20, "闭包应当远小于整块代码面（119 件）")
        self.assertIsNone(disk_cache.code_scope_files(ROOT, ("core.regression_score",)),
                          "含动态导入构造（`__import__`）的模块必须判「说不清」→ 退回整块代码面")
        with tempfile.TemporaryDirectory() as tmp:
            core = pathlib.Path(tmp) / "desktop" / "src" / "core"
            core.mkdir(parents=True)
            (core / "a.py").write_text("from core import b  # noqa\n", encoding="utf-8")
            (core / "b.py").write_text("x = 1\n", encoding="utf-8")
            self.assertEqual(("desktop/src/core/a.py", "desktop/src/core/b.py"),
                             disk_cache.code_scope_files(tmp, ("core.a",)),
                             "合成树：闭包应含 a 与被 a 依赖的 b")
            (core / "b.py").write_text("x = __import__('os')\n", encoding="utf-8")
            self.assertIsNone(disk_cache.code_scope_files(tmp, ("core.a",)),
                              "合成树：闭包里出现动态导入 ⇒ 判说不清（fail-closed）")
            (core / "a.py").write_text("def (:\n", encoding="utf-8")   # 真·语法错
            self.assertIsNone(disk_cache.code_scope_files(tmp, ("core.a",)),
                              "合成树：解析不出 ⇒ 判说不清")

    def test_every_site_has_a_computable_scope(self):
        for module, _fn in self.SITES:
            scope = disk_cache.code_scope_files(ROOT, (module,))
            self.assertIsNotNone(scope, "%s 的代码闭包算不出（会退回整块代码面）" % module)
            self.assertIn("desktop/src/core/%s.py" % module.split(".")[-1], scope)

    #: 运行期完整性探针只挑 4 个站点跑（每个都得起一次全新解释器；全跑 9 个会把门禁时间拉长一倍），
    #: 挑的是「hub + 三类叶子」：conformance_scan（被最多模块依赖）、schema_lint、layer_model、
    #: asset_density。闭包算法对所有站点是同一个，抽样足够暴露「静态分析漏判」。
    RUNTIME_SITES = (("core.conformance_scan", "_scan_impl"),
                     ("core.schema_lint", "_scan_impl"),
                     ("core.layer_model", "_scan_impl"),
                     ("core.asset_density", "_thickness_impl"))

    def test_runtime_imports_stay_inside_declared_scope(self):
        """全新解释器里真跑一遍：**懒导入**的 `core.*` 模块必须都在声明闭包内。

        （静态导入由闭包算法覆盖；这里盯的是「运行期才 import」的那一半——静态分析漏判会当场红。）
        探针脚本写在**临时目录**里：单测不得往仓库里落任何件。
        """
        src = ("import json, os, sys\n"
               "sys.path.insert(0, os.path.join(sys.argv[1], 'desktop', 'src'))\n"
               "os.environ['NF_NO_DISK_CACHE'] = '1'\n"
               "import importlib\n"
               "mod = importlib.import_module(sys.argv[2])\n"
               "fn = getattr(mod, sys.argv[3])\n"
               "before = set(sys.modules)\n"
               "fn('.')\n"
               "print(json.dumps(sorted(m for m in set(sys.modules) - before\n"
               "                        if m.startswith('core.'))))\n")
        with tempfile.TemporaryDirectory() as tmp:
            probe = os.path.join(tmp, "scope_probe.py")
            with open(probe, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(src)
            for module, fn in self.RUNTIME_SITES:
                scope = disk_cache.code_scope_files(ROOT, (module,))
                allowed = {os.path.basename(p)[:-3] for p in scope}
                out = subprocess.run([sys.executable, probe, ROOT, module, fn], cwd=ROOT,
                                     capture_output=True, text=True, encoding="utf-8",
                                     timeout=600)
                self.assertEqual(0, out.returncode, out.stderr[-400:])
                lazy = set(json.loads(out.stdout.strip() or "[]"))
                leak = sorted(m for m in lazy if m.split(".")[-1] not in allowed)
                self.assertEqual([], leak,
                                 "%s 运行期导入了闭包外的模块 → 闭包不完整，缓存会陈旧" % module)


class ModuleDocsMemoTest(unittest.TestCase):
    """`_module_docs` 的作用域缓存与**新鲜度**：同作用域两次一致，新作用域必须看见新增件。

    口径（2026-09-29 修订）：本函数已改走**共享枚举器**（`iter_files`；目录清单在常驻层里），
    不再是「一次 `os.walk`」，所以判据从「数 `os.walk` 次数」改成**行为**：同作用域稳定、
    跨作用域不许陈旧。真仓库上的**逐件等价**由 `ModuleDocsEquivalenceTest` 另行守着。
    """

    def test_fresh_next_scope_and_stable_within_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            for rel in ("04_模块库/通用类/A01_x.md", "community/包甲/modules/M01_x.md"):
                path = os.path.join(tmp, *rel.split("/"))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write("x\n")
            with cs.read_memo():
                first = cs._module_docs(tmp)
                second = cs._module_docs(tmp)
            self.assertEqual(first, second, "同一作用域内两次结果必须一致")
            self.assertEqual(2, len(first), first)
            with open(os.path.join(tmp, "community", "包甲", "modules", "M02_y.md"),
                      "w", encoding="utf-8", newline="\n") as fh:
                fh.write("y\n")
            with cs.read_memo():
                third = cs._module_docs(tmp)
            self.assertEqual(3, len(third), "新作用域必须看见新增件（不许跨调用陈旧）")


class ModuleDocsEquivalenceTest(unittest.TestCase):
    """`_module_docs()` 换枚举器（`os.walk` + 逐包 `listdir` → `iter_files`）后面必须**逐件一致**。

    依据（实测 2026-09-29）：旧写法在守护口径下每次新内容状态都要重付——**107 次 `listdir` +
    113 次 `isdir` ≈ 21 ms**（占该状态 os/stat 面的四分之一）；共享枚举器同一张面 **~0.5 ms**。
    """

    def test_matches_legacy_enumeration(self):
        legacy: list = []
        for dirpath, _dirs, files in os.walk(os.path.join(ROOT, "04_模块库")):
            legacy += [os.path.join(dirpath, f) for f in files if f.endswith(".md")]
        pkg_dir = os.path.join(ROOT, "community")
        for pkg in sorted(os.listdir(pkg_dir)):
            mdir = os.path.join(pkg_dir, pkg, "modules")
            if os.path.isdir(mdir):
                legacy += [os.path.join(mdir, f) for f in sorted(os.listdir(mdir))
                           if f.endswith(".md")]
        want = sorted(legacy)
        self.assertGreater(len(want), 100, "面太小，判据没测到东西")
        self.assertEqual(want, cs._module_docs(ROOT), "面与旧枚举不一致（换实现改动了面）")


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
