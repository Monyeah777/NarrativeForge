#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产出形态面单测：形态清单自洽 / 判件 / JSON Schema 子集语义 / 双源 / T4 复算 / 基线回退。

负例取自真实缺陷类（本波实际踩到的三类）：
  ① 声明了 T4 却没有可复算引擎（宣称≠实现）；
  ② 数据面与散文面键集不一致（双源漂移）；
  ③ JSON Schema 多余字段 / 不支持关键字必须显式上报（不得静默通过）。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import output_forms as of  # noqa: E402
from core import quant_metrics as qm  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


class PackKeyReuseTest(unittest.TestCase):
    """**确知变更面**驱动的键复用：只在「确知本包切片没变」时复用；说不清一律重算（fail-closed）。

    依据（实测 2026-09-29）：`index_verify` 为 106 个包各算一次切片指纹（合计 ~15 ms），而最常见的
    改动（`04_模块库` 正文、文档、声明面外的件）**一件都不落在任何包切片里**——算完 106 次才发现全都
    没变。读层一直在用「确知变更路径」精确失效（`drop_resident`），**键层过去没用**。判据直接问三态：
    不知道 / 确知没沾到 / 确知沾到了（外加「共享面变了也不许复用」）。
    """

    def _with_changes(self, known, paths):
        from unittest import mock
        return mock.patch.object(of._csc, "changed_paths", lambda: (known, set(paths)))

    def test_reuses_only_when_change_face_is_known_and_clean(self):
        pkg = of._pack_dirs(ROOT)[0]
        shared = of.shared_face_key(ROOT)
        of._PACK_KEY_MEMO.clear()
        of._PACK_KEY_MEMO[pkg] = (shared, "SENTINEL")
        with self._with_changes(False, []):                       # 说不清 → 不许复用
            self.assertNotEqual("SENTINEL", of.pack_content_key(ROOT, pkg, shared))
        of._PACK_KEY_MEMO[pkg] = (shared, "SENTINEL")
        with self._with_changes(True, ["docs/x.md"]):             # 确知没沾到本包切片 → 复用
            self.assertEqual("SENTINEL", of.pack_content_key(ROOT, pkg, shared))
        of._PACK_KEY_MEMO[pkg] = (shared, "SENTINEL")
        with self._with_changes(True, ["community/%s/outputs/INDEX.json".lower() % pkg]):
            self.assertNotEqual("SENTINEL", of.pack_content_key(ROOT, pkg, shared),
                                "切片的件确知变了（且监听给的是小写）时必须重算")
        of._PACK_KEY_MEMO[pkg] = ("别的共享面带", "SENTINEL")
        with self._with_changes(True, ["docs/x.md"]):             # 共享面变了 → 不许复用
            self.assertNotEqual("SENTINEL", of.pack_content_key(ROOT, pkg, shared))


class PackKeyReadCoverageTest(unittest.TestCase):
    """逐包内容键必须**覆盖 `_verify_pack` 真读的件**——同族陈旧洞的可执行判据。

    依据（实测 2026-09-29，读追踪全 106 包）：`_verify_pack(pkg)` 的 T4 复算会经
    `pack_combo.combine/profiles` 读到 **核心模块文档**（`04_模块库/*/*.md` 13 件）与
    **别的包的声明/资产台账**（`community/*/protocol.yaml`、`community/*/assets/provenance.json`），
    而当时的共享面只有「社区模块 + registry」⇒ 这些件一变，逐包缓存就**命中旧判决**（陈旧/假绿）。

    两类**不是漏申报**的例外：① `04_模块库/*/*.md` 按**解析后的核心契约**进键（`shared_face_key`
    里拼了 `pack_combo.core_contracts_fingerprint`）——`combine` 只消费 `core_pub`，正文改动不该
    重算 106 个包（实测按正文取键会 +800 ms/条命令）；该判据另有一段专测「改核心契约必须换键」。
    ② `desktop/src/core/*.py` 属**代码面**——它在落盘键里（`disk_cache.key` 的 `code_modules`），
    且代码换版时守护会摘掉 `core.*` 重载 ⇒ 进程内缓存自然作废；仓外的 `cache/` 件是缓存自身。
    """

    CODE_PREFIX = "desktop/src/core/"

    def test_every_verify_pack_read_is_inside_the_key_face(self):
        import builtins
        from core import conformance_scan as csc
        shared = set(r for pat in of._PACK_FACE_SHARED for r in csc.iter_files(ROOT, pat))
        self.assertGreater(len(shared), 200, "共享面太小，判据没测到东西")
        reads = set()
        orig_read, orig_open = csc.read_text_cached, builtins.open

        def rel_of(path):
            try:
                return os.path.relpath(str(path), ROOT).replace(os.sep, "/")
            except ValueError:
                return ""

        def read_traced(path, *a, **k):
            reads.add(rel_of(path))
            return orig_read(path, *a, **k)

        def open_traced(file, *a, **k):
            if isinstance(file, (str, bytes, os.PathLike)):
                reads.add(rel_of(file))
            return orig_open(file, *a, **k)

        csc.read_text_cached, builtins.open = read_traced, open_traced
        try:
            for pkg in of._pack_dirs(ROOT):
                reads.clear()
                slice_files = set(r for rel_pat in of._PACK_FACE_SLICE
                                  for r in csc.iter_files(
                                      ROOT, "community/%s/%s" % (pkg, rel_pat)))
                of._verify_pack(ROOT, pkg)
                leak = sorted(r for r in reads
                              if r and not r.startswith("..")
                              # 读**不存在**的件（探在不在）不算输入：失败读取不贡献结论，而「件后来出现」
                              # 会让枚举面变 ⇒ 键自然跟着变（枚举在面里，见 `content_fingerprint`）。
                              and os.path.isfile(os.path.join(ROOT, *r.split("/")))
                              and r not in slice_files and r not in shared
                              and not r.startswith(self.CODE_PREFIX)
                              and not r.startswith(of._PACK_FACE_PARSED[0][:4]))
                self.assertEqual([], leak,
                                 "%s 的逐包键面缺了它真读的件：%s" % (pkg, leak[:3]))
        finally:
            csc.read_text_cached, builtins.open = orig_read, orig_open

    def test_shared_key_includes_the_parsed_core_fingerprint(self):
        """核心模块按**解析后契约**进键：`core_contracts_fingerprint` 一变，共享键必变。"""
        from core import pack_combo as pc
        base = of.shared_face_key(ROOT)
        orig = pc.core_contracts_fingerprint
        pc.core_contracts_fingerprint = lambda root=".": "0" * 64      # type: ignore[assignment]
        try:
            self.assertNotEqual(base, of.shared_face_key(ROOT),
                                "共享键必须把「解析后的核心契约」算进去")
        finally:
            pc.core_contracts_fingerprint = orig                       # type: ignore[assignment]
        self.assertEqual(base, of.shared_face_key(ROOT), "同内容必须同键")


class PackSliceIndexTest(unittest.TestCase):
    """逐包键改「一次枚举 + 按包切片」后，**键值必须逐包不变**（面与顺序都不许动）。

    依据（实测 2026-09-29）：104 包 × 4 条面 = 424 个包级模式，一次 `nf score` 里 `iter_files`
    因此被调 619 次（35.5 ms），其中约 424 次是「同一批面按包切」。
    """

    def test_index_route_equals_per_pack_route(self):
        shared = of.shared_face_key(ROOT)
        slices = of.pack_slice_index(ROOT)
        pkgs = of._pack_dirs(ROOT)
        self.assertGreater(len(pkgs), 50, "包太少，判据没测到东西")
        for pkg in pkgs:
            self.assertEqual(of.pack_content_key(ROOT, pkg, shared),           # 逐包枚举（旧路线）
                             of.pack_content_key(ROOT, pkg, shared, slices.get(pkg, [])),
                             "%s 的键在两条路线上不一致" % pkg)

    def test_index_covers_exactly_the_declared_slice(self):
        """切片索引的**路径集合**必须等于该包在声明面里的那几条（多一条少一条都是面变了）。"""
        from core import conformance_scan as csc
        slices = of.pack_slice_index(ROOT)
        for pkg in of._pack_dirs(ROOT)[:3]:
            want = [r for rel_pat in of._PACK_FACE_SLICE
                    for r in csc.iter_files(ROOT, "community/%s/%s" % (pkg, rel_pat))]
            self.assertTrue(want, "%s 的切片为空，判据没测到东西" % pkg)
            self.assertEqual(want, slices[pkg], "%s 的切片面不一致" % pkg)


class PackEnumerationTest(unittest.TestCase):
    """`_pack_dirs()` 换枚举器（`iterdir` + 逐条 stat → `csc.iter_files`）后**面必须逐件一致**。

    依据（实测 2026-09-29）：原实现每次 **20 ms**（106 个包 ⇒ 200+ 次 stat），而 `index_verify`
    与 `meter` 每个内容状态各调一次 ⇒ 一次新状态白花 **40 ms**；换枚举器后 **~1 ms**。提速只有在
    「面不变」时才允许，所以这里把旧口径原样重算一遍逐件比对。
    """

    def test_matches_legacy_enumeration(self):
        base = Path(ROOT) / "community"
        legacy = sorted(d.name for d in base.iterdir()
                        if d.is_dir() and (d / of.INDEX_REL).is_file())
        self.assertTrue(legacy, "包面为空，判据没测到东西")
        self.assertEqual(legacy, of._pack_dirs(ROOT), "包面与旧枚举不一致（换实现改动了面）")


class ReadMemoTest(unittest.TestCase):
    """一次 `index_verify` 内的共享读：同文件只读一遍，且**不得跨调用**（不许陈旧）。

    依据（实测）：逐件校验会把同一份产物读 5–8 遍（detect / 查重 / schema / 双源 / 复算），
    一次 `index_verify` 曾达 3027 次读盘、占该函数 1.54 s 的大半；加共享读后降到 ~0.72 s。
    两条性质都要钉住：① 作用域内去重；② 作用域出口即清（下一次调用必须看到新内容）。
    """

    def test_same_file_read_once_inside_memo_and_fresh_after(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.txt"
            p.write_text("一", encoding="utf-8")
            calls = []
            # 2026-09-29 起共享读是**一次物理读服务两种口径**：文本与字节都从
            # `Path.read_bytes()` 出（文本经通用换行语义解出）。所以计数口径要**两条都数**，
            # 否则「一次读」这条不变量会被读成 0 次（实际是换了一层实现，不是没读）。
            orig_text, orig_bytes = Path.read_text, Path.read_bytes

            def counting(self, *a, **k):
                calls.append(str(self))
                return orig_text(self, *a, **k)

            def counting_bytes(self, *a, **k):
                calls.append(str(self))
                return orig_bytes(self, *a, **k)

            Path.read_text = counting                      # type: ignore[assignment]
            Path.read_bytes = counting_bytes               # type: ignore[assignment]
            try:
                with of._memo_reads():
                    self.assertEqual("一", of._read_text_cached(p))
                    self.assertEqual("一", of._read_text_cached(p))
                    self.assertEqual("一", of._read_text_cached(p))
                self.assertEqual(1, len(calls), "同一次调用内同文件只该读一遍")
                calls.clear()
                of._read_text_cached(p)                    # 不在 memo 里：照常真读
                self.assertEqual(1, len(calls))
                p.write_text("二", encoding="utf-8")
                with of._memo_reads():
                    self.assertEqual("二", of._read_text_cached(p),
                                     "新的一次调用必须看到新内容（作用域出口即清）")
            finally:
                Path.read_text = orig_text                 # type: ignore[assignment]
                Path.read_bytes = orig_bytes               # type: ignore[assignment]


class RegistryTest(unittest.TestCase):
    def test_registry_self_consistent(self):
        issues, stats = of.registry_verify(ROOT)
        self.assertEqual(issues, [], issues)
        self.assertGreaterEqual(stats["forms"], 100, "形态清单须成规模（本次 ≥100 条）")
        self.assertGreaterEqual(stats["categories"], 8)
        for form in ("json", "json-schema", "vega-lite", "mermaid", "graphml",
                     "csv", "gips", "model-cards"):
            self.assertIn(form, {f["id"] for f in of.load_registry(ROOT)["forms"]})

    def test_every_form_carries_reachability_evidence(self):
        for f in of.load_registry(ROOT)["forms"]:
            self.assertIn("reachable", f["evidence"], f["id"])
            if f["evidence"]["reachable"]:
                self.assertTrue(f["evidence"]["sha256_sample"], f["id"])
            else:
                self.assertTrue(f["evidence"]["error"], f["id"])


class PackVerifyCacheTest(unittest.TestCase):
    """逐包产出面校验的**内容键缓存**：行为不变 + 键对内容敏感 + 只影响被改的包。

    依据（2026-09-29 实测）：106 个包逐包真算（形态/档位/schema/双源/T4 复算）**533 ms**，
    而按包内容键缓存后命中只要 **11 ms**——一次真编辑只让**被改的那个包**重算。
    """

    def test_cache_is_behavior_preserving(self):
        # 直接打内层：外层还有「整块内容键」缓存，命中时根本不会走到逐包这层（那也算对，
        # 但本判据要钉的是**逐包那层**的行为与命中）。
        of._INDEX_CACHE.clear()
        of._PACK_VERIFY_CACHE.clear()
        cold = of._index_verify_impl(ROOT)
        self.assertGreater(len(of._PACK_VERIFY_CACHE), 0, "逐包缓存必须真的被填上")
        warm = of._index_verify_impl(ROOT)              # 逐包缓存热
        self.assertEqual(cold, warm, "缓存不得改变判定")
        self.assertEqual(cold[0], [], cold[0][:3])

    def test_outer_face_cache_still_works(self):
        of._PACK_VERIFY_CACHE.clear()
        first = of.index_verify(ROOT)                   # 外层内容键未命中 → 走内层
        of._INDEX_CACHE.clear()
        second = of.index_verify(ROOT)
        self.assertEqual(first, second, "外层内容键缓存不得改变判定")

    def test_pack_key_tracks_content_and_is_per_pack(self):
        """合成树：改 A 包的件 → 只有 A 的键变；B 的键不动（这就是「只重算被改的包」）。"""
        with tempfile.TemporaryDirectory() as tmp:
            for pkg in ("A", "B"):
                d = Path(tmp) / "community" / pkg / "outputs"
                d.mkdir(parents=True)
                (d / "INDEX.json").write_text('{"schema": "nf-output-index/1"}',
                                              encoding="utf-8")
                (d / "x.md").write_text("一", encoding="utf-8")
            (Path(tmp) / "desktop" / "src" / "core").mkdir(parents=True)
            (Path(tmp) / "desktop" / "src" / "core" / "registry.json").write_text(
                "{}", encoding="utf-8")
            a1 = of.pack_content_key(tmp, "A")
            b1 = of.pack_content_key(tmp, "B")
            self.assertNotEqual(a1, b1, "不同包的内容键必须不同")
            (Path(tmp) / "community" / "A" / "outputs" / "x.md").write_text(
                "二", encoding="utf-8")
            self.assertNotEqual(a1, of.pack_content_key(tmp, "A"), "包内容一变键必须变")
            self.assertEqual(b1, of.pack_content_key(tmp, "B"), "别的包的键不得跟着变")

    def test_shared_face_moves_every_pack_key(self):
        """共享面切出来之后，**覆盖面不许缩小**：跨包模块面 / registry 一变 ⇒ 所有包的键都得变。

        口径变更（2026-09-29 实测）：逐包键过去是「切片 ∪ 共享面」一次性指纹，**每个包都把 235 份
        `community/*/modules/*.md` 重新枚举一遍**（111 遍），占 `index_verify` 185 ms 里的大头；
        改成「共享面算一遍 + 逐包切片」两半组合后 `index_verify` **185 → 75 ms**。这条判据钉住
        「切出来的两半合起来仍等于原来的面」。
        """
        with tempfile.TemporaryDirectory() as tmp:
            for pkg in ("A", "B"):
                (Path(tmp) / "community" / pkg / "outputs").mkdir(parents=True)
                mods = Path(tmp) / "community" / pkg / "modules"
                mods.mkdir(parents=True)
                (mods / "M01_x.md").write_text("一", encoding="utf-8")
            (Path(tmp) / "desktop" / "src" / "core").mkdir(parents=True)
            (Path(tmp) / "desktop" / "src" / "core" / "registry.json").write_text(
                "{}", encoding="utf-8")

            shared1 = of.shared_face_key(tmp)
            self.assertEqual(shared1, of.shared_face_key(tmp), "同内容必须同指纹")
            a1 = of.pack_content_key(tmp, "A", shared1)
            b1 = of.pack_content_key(tmp, "B", shared1)

            (Path(tmp) / "community" / "A" / "modules" / "M01_x.md").write_text(
                "二", encoding="utf-8")
            shared2 = of.shared_face_key(tmp)
            self.assertNotEqual(shared1, shared2, "跨包模块面一变，共享面指纹必须变")
            self.assertNotEqual(a1, of.pack_content_key(tmp, "A", shared2), "A 的键必须变")
            self.assertNotEqual(b1, of.pack_content_key(tmp, "B", shared2),
                                "共享面一变，**别的包**的键也必须变（覆盖面不许缩小）")
            (Path(tmp) / "community" / "A" / "modules" / "M01_x.md").write_text(
                "一", encoding="utf-8")
            self.assertEqual(shared1, of.shared_face_key(tmp), "还原后共享面指纹应回到原值")
            self.assertEqual(a1, of.pack_content_key(tmp, "A", of.shared_face_key(tmp)),
                             "还原后逐包键也应回到原值")


class PackageIndexTest(unittest.TestCase):
    def test_repo_packages_green(self):
        issues, stats = of.index_verify(ROOT)
        self.assertEqual(issues, [], issues)
        self.assertGreaterEqual(stats["outputs"], 10)
        self.assertIn("T4", stats["by_tier"])

    def test_baseline_blocks_regression(self):
        issues, _ = of.baseline_verify(ROOT)
        self.assertEqual(issues, [], issues)

    def test_missing_declared_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "community", "样例包", "outputs"))
            idx = {"schema": "nf-output-index/1", "package": "样例包",
                   "outputs": [{"path": "outputs/NOPE.json", "form": "json",
                                "tier": "T2", "role": "data"}]}
            with open(os.path.join(tmp, "community", "样例包", of.INDEX_REL),
                      "w", encoding="utf-8") as fh:
                json.dump(idx, fh)
            issues, _ = of.index_verify(tmp)
            self.assertTrue(any("不存在" in i for i in issues), issues)

    def test_t4_without_generator_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "community", "样例包", "outputs")
            os.makedirs(base)
            with open(os.path.join(base, "X.json"), "w", encoding="utf-8") as fh:
                json.dump({"a": 1}, fh)
            idx = {"schema": "nf-output-index/1", "package": "样例包",
                   "outputs": [{"path": "outputs/X.json", "form": "json", "tier": "T4",
                                "role": "functional",
                                "recompute": {"id": "no-such-generator"}}]}
            with open(os.path.join(tmp, "community", "样例包", of.INDEX_REL),
                      "w", encoding="utf-8") as fh:
                json.dump(idx, fh)
            issues, _ = of.index_verify(tmp)
            self.assertTrue(any("无对应引擎" in i for i in issues), issues)


class JsonSchemaSubsetTest(unittest.TestCase):
    def test_type_required_enum(self):
        schema = {"type": "object", "required": ["a"],
                  "properties": {"a": {"type": "integer", "enum": [1, 2]}},
                  "additionalProperties": False}
        self.assertEqual(of.json_schema_check({"a": 1}, schema), [])
        self.assertTrue(of.json_schema_check({}, schema))
        self.assertTrue(of.json_schema_check({"a": 3}, schema))
        self.assertTrue(of.json_schema_check({"a": 1, "b": 2}, schema))

    def test_bool_is_not_number(self):
        errs = of.json_schema_check(True, {"type": "number"})
        self.assertTrue(errs, "布尔不得当数字通过（Python 子类陷阱）")

    def test_unsupported_keyword_is_reported_not_ignored(self):
        unsup = []
        of.json_schema_check({}, {"if": {"type": "object"}}, unsupported=unsup)
        self.assertTrue(unsup, "不支持的官方关键字必须显式上报（不得静默通过）")

    def test_local_ref_resolves_remote_does_not(self):
        schema = {"$defs": {"x": {"type": "string"}}, "properties": {"a": {"$ref": "#/$defs/x"}},
                  "type": "object"}
        self.assertEqual(of.json_schema_check({"a": "s"}, schema), [])
        unsup = []
        of.json_schema_check({}, {"$ref": "https://example.com/s.json"}, unsupported=unsup)
        self.assertTrue(unsup)


class FormValidatorTest(unittest.TestCase):
    def _write(self, tmp, rel, text):
        p = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return p

    def test_duplicate_json_key_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "a.json", '{"x": 1, "x": 2}')
            issues = of._check_json(tmp, "a.json")
            self.assertTrue(any("重复键" in i for i in issues), issues)

    def test_csv_ragged_rows_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "a.csv", "a,b\n1,2\n3\n")
            issues = of._check_csv(tmp, "a.csv")
            self.assertTrue(any("字段数" in i for i in issues), issues)

    def test_vega_lite_needs_mark_data_and_bound_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "c.json", json.dumps({
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "data": {"values": []}, "mark": "line",
                "encoding": {"x": {"type": "nominal"}}}))
            issues = of._check_vega_lite(tmp, "c.json")
            self.assertTrue(any("通道未绑定" in i for i in issues), issues)

    def test_graphml_dangling_edge_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "g.graphml", (
                '<?xml version="1.0"?><graphml xmlns="http://graphml.graphdrawing.org/xmlns">'
                '<graph id="g" edgedefault="directed"><node id="A"/>'
                '<edge source="A" target="B"/></graph></graphml>'))
            issues = of._check_graphml(tmp, "g.graphml")
            self.assertTrue(any("悬空" in i for i in issues), issues)

    def test_detect_distinguishes_schema_and_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "s.json", json.dumps(
                {"$schema": "https://json-schema.org/draft/2020-12/schema",
                 "type": "object"}))
            self._write(tmp, "v.json", json.dumps(
                {"$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                 "data": {"values": []}, "mark": "line"}))
            self.assertEqual(of.detect(tmp, "s.json")[0], "json-schema")
            self.assertEqual(of.detect(tmp, "v.json")[0], "vega-lite")

    def test_quant_metrics_engine_claim_must_be_implemented(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, "q.json", json.dumps({
                "kind": "nf-quant-metrics/1", "domain": "d", "source": "assets/x.md",
                "annual_factors": {"daily": 252, "weekly": 52, "monthly": 12},
                "metrics": [{"id": "METRIC_X", "name": "X", "formula": "f", "unit": "ratio",
                             "category": "return", "required_params": ["prices"],
                             "pitfall": "p", "engine": "quant_metrics:not_there",
                             "verifiable": "T4"}],
                "declared_only": []}))
            issues = of._check_quant_metrics(tmp, "q.json")
            self.assertTrue(any("宣称≠实现" in i for i in issues), issues)


class RenderAndRecomputeTest(unittest.TestCase):
    def test_repo_render_is_idempotent(self):
        issues, rows = of.render_outputs(ROOT, write=False)
        self.assertEqual(issues, [], issues)
        self.assertTrue(rows)
        self.assertFalse([r for r in rows if r["changed"]],
                         "在盘产出面必须与生成器一致（改声明件后重跑 nf output render --write）")

    def test_meter_ratio_bounds(self):
        _, stats = of.meter(ROOT)
        for pkg, s in stats["packages"].items():
            self.assertGreater(s["machine_verifiable"], 0, pkg)
            self.assertLessEqual(s["machine_verifiable_ratio"], 1.0)
            self.assertGreaterEqual(s["machine_verifiable_ratio"], 0.0)

    def test_quant_engine_claim_covers_all_engines(self):
        """注册表宣称的每个 engine 都必须在 core.quant_metrics 真实存在。"""
        data = json.loads((Path(ROOT) / "community" / "量化金融域包" / "outputs"
                           / "QUANT_METRICS.json").read_text(encoding="utf-8"))
        for m in data["metrics"]:
            mod, _, fn = m["engine"].partition(":")
            self.assertEqual(mod, "quant_metrics")
            self.assertTrue(hasattr(qm, fn), m["id"])


if __name__ == "__main__":
    unittest.main()
