#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""域包自由组合单测：五不变量 / 传递闭包 / references 借入 / 证书 T4 复算 / 广度抽样。

负例取自组合引擎的真实失效类：未知包、悬挂依赖、未桥事件、未解析引用、层栈不稳定。
"""
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import pack_combo as pc  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


def _write_pack(root, name, mid, inputs=(), publish=(), subscribe=()):
    """最小可组合包：`protocol.yaml`（包 id + 模块清单 + 挂载层）+ 一份 `machine_contract` 模块件。"""
    d = Path(root, "community", name)
    (d / "modules").mkdir(parents=True, exist_ok=True)
    (d / "protocol.yaml").write_text(
        "protocol:\n  package:\n    id: %s\n    pipeline: P90\n    module_id_range:\n"
        '      - "%s"\n    mount_layers:\n      P40 行为决策: {default: [%s], available: []}\n'
        % (name, mid, mid), encoding="utf-8")
    stem = mid.split(":")[-1]
    (d / "modules" / ("%s_x.md" % stem)).write_text(
        "```yaml\nmachine_contract:\n  id: %s\n  layer: P40\n  inputs: [%s]\n"
        "  outputs: [x]\n  events:\n    publish: [%s]\n    subscribe: [%s]\n```\n"
        % (mid, ", ".join(inputs), ", ".join(publish), ", ".join(subscribe)),
        encoding="utf-8")


class ContentKeyedDerivedCacheTest(unittest.TestCase):
    """派生缓存按**内容**（不是按 root）：输入没变就复用；输入一变就重算（不许陈旧）。

    依据（实测）：广度证明要跑 6885 次组合（~0.92 s）、包画像要重解析 111 个协议声明 +
    235 份模块文档（~0.3–0.5 s），而守护是**逐请求清空按 root 的缓存**的——所以过去每条
    重命令都白交一遍。改按内容指纹缓存后，隔离 A/B（n=5）实测 `evaluate` 中位
    **3683 ms → 3172 ms（−511 ms / −14%）**。
    """

    def test_breadth_reuses_within_same_content(self):
        """键即内容：同内容**第二次不得新增** combine 调用；且判据自身先证明有效。

        口径（2026-09 修订）：本函数现在有**三层**缓存（进程内内容键 + **持久**内容键 +
        逐组合判决层），所以「第一次一定真跑」不再是真不变量——**先在三层都清空/关掉的最冷状态下
        证明计数器有效**（必须真跑 >1000 次），**再**测真不变量（第二次零新增）。
        """
        import os

        from core import disk_cache as dc

        def run_with_counter():
            calls = []
            orig = pc.combine

            def counting(*a, **k):
                calls.append(1)
                return orig(*a, **k)

            pc.combine = counting                  # type: ignore[assignment]
            try:
                got = pc.breadth(ROOT)
            finally:
                pc.combine = orig                  # type: ignore[assignment]
            return got, len(calls)

        # ① 最冷状态（进程内 + 持久都不可用）→ 计数器必须真的数到大数，否则判据本身没测到东西
        old_off = os.environ.get(dc.ENV_OFF)
        os.environ[dc.ENV_OFF] = "1"
        try:
            pc._CONTENT_CACHE.clear()
            pc._COMBO_CACHE.clear()            # 逐组合层也算一层：最冷状态必须把它清空
            _, cold = run_with_counter()
        finally:
            if old_off is None:
                os.environ.pop(dc.ENV_OFF, None)
            else:
                os.environ[dc.ENV_OFF] = old_off
        self.assertGreater(cold, 1000, "最冷状态下广度证明应真跑组合（判据自身要有效）")

        # ② 真不变量：同内容第二次**零新增**（无论这次是进程内命中还是持久命中）
        pc._CONTENT_CACHE.clear()
        first, n_first = run_with_counter()
        second, n_second = run_with_counter()
        self.assertEqual(0, n_second, "同内容的第二次不得再跑组合（缓存没生效？）")
        self.assertEqual(first, second, "命中缓存的结果必须与首算一致")

    def test_fingerprint_is_stable_and_sensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "community", "包甲")
            (d / "modules").mkdir(parents=True)
            (d / "protocol.yaml").write_text("id: 包甲\n", encoding="utf-8")
            mod = d / "modules" / "M01_样例.md"
            mod.write_text("内容一\n", encoding="utf-8")
            f1 = pc._inputs_fingerprint(tmp)
            self.assertEqual(f1, pc._inputs_fingerprint(tmp), "同内容指纹必须稳定")
            mod.write_text("内容二\n", encoding="utf-8")
            self.assertNotEqual(f1, pc._inputs_fingerprint(tmp),
                                "输入一变指纹必须变（否则会读到陈旧派生结果）")


class ContractCacheTest(unittest.TestCase):
    """契约解析的内容键缓存：**面内改动必重算、面外改动必命中**（键即内容，无陈旧面）。

    依据（实测 2026-09-29）：守护逐请求清空按根缓存，`_module_contracts` 此前每次新状态都要重解析
    235 份社区模块的 `machine_contract` 围栏（~34 ms）；而它只是**那几份正文**的纯函数。
    """

    def _tree(self, tmp):
        _write_pack(tmp, "包甲", "包甲:M01", publish=["ev_a"])
        core = Path(tmp, "04_模块库", "通用类")
        core.mkdir(parents=True, exist_ok=True)
        (core / "M00_x.md").write_text(
            "```yaml\nmachine_contract:\n  id: M00\n  layer: P00\n"
            "  events:\n    publish: [ev_core]\n```\n", encoding="utf-8")
        return core

    def test_community_contracts_cache_is_content_keyed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp)
            pc.cache_clear()
            pc._CONTRACTS_CACHE.clear()
            first = pc._module_contracts(tmp)
            self.assertIn("包甲:M01", first)
            pc.cache_clear()                       # 模拟守护逐请求清空按根缓存
            self.assertIs(first, pc._module_contracts(tmp),
                          "面没变时必须命中内容键缓存（这正是省掉 34 ms 的那一下）")
            mod = Path(tmp, "community", "包甲", "modules", "M01_x.md")
            mod.write_text(mod.read_text(encoding="utf-8") + "\n# 变更\n", encoding="utf-8")
            pc.cache_clear()
            self.assertIsNot(first, pc._module_contracts(tmp),
                             "面内改动必须重算（否则会读到陈旧契约）")

    def test_core_contracts_cache_is_content_keyed(self):
        with tempfile.TemporaryDirectory() as tmp:
            core = self._tree(tmp)
            pc.cache_clear()
            pc._CONTRACTS_CACHE.clear()
            first = pc._core_contracts(tmp)
            self.assertIn("M00", first)
            (Path(tmp, "community", "包甲", "modules", "M02_z.md")).write_text(
                "```yaml\nmachine_contract:\n  id: 包甲:M02\n  layer: P40\n```\n",
                encoding="utf-8")
            pc.cache_clear()
            self.assertIs(first, pc._core_contracts(tmp), "社区模块改了不该换核心契约的键")
            (core / "M00_x.md").write_text("```yaml\nmachine_contract:\n  id: M00\n"
                                           "  layer: P00\n  events:\n    publish: [ev_new]\n```\n",
                                           encoding="utf-8")
            pc.cache_clear()
            self.assertIsNot(first, pc._core_contracts(tmp), "核心模块改了必须重算")


class CertificateCacheTest(unittest.TestCase):
    """证书校验（schema + T4 复算）的内容键缓存：与**未缓存参考实现**逐证书等价 + 键随内容变。

    依据（实测 2026-09-29）：`pack_combo.scan` 稳态 ~36 ms 里，证书 T4 复算 **9.4–10.2 ms**、
    证书 schema 校验 **8.6–9.9 ms（1486 次嵌套调用）**——都是「证书正文 + 契约面」的纯函数。
    """

    @staticmethod
    def _reference(root, cert):
        from core import output_forms as of
        name = cert.get("label") or "+".join(cert.get("packs") or []) or "<空>"
        unsup: list = []
        schema_errs = of.json_schema_check(cert, pc.CERT_SCHEMA, unsupported=unsup)
        out = ["组合 %s: 证书不合 schema: %s" % (name, e) for e in schema_errs[:4]]
        if unsup:
            out.append("组合 %s: 证书校验器遇到不支持关键字 %s" % (name, sorted(set(unsup))[:2]))
        sub, _st = pc.verify_certificate(root, cert)
        out += ["组合 %s: %s" % (name, s) for s in sub]
        return out

    def test_matches_reference_on_real_certificates(self):
        certs = pc.declared(ROOT).get("certificates") or []
        self.assertGreater(len(certs), 5, "证书太少，判据没测到东西")
        witness = pc._combo_witness(ROOT, pc.profiles(ROOT), pc._module_contracts(ROOT))
        pc._CERT_CACHE.clear()
        for cert in certs:
            self.assertEqual(self._reference(ROOT, cert),
                             pc._certificate_lines(ROOT, cert, witness), cert.get("label"))

    def test_cache_is_content_and_witness_keyed(self):
        cert = (pc.declared(ROOT).get("certificates") or [])[0]
        witness = pc._combo_witness(ROOT, pc.profiles(ROOT), pc._module_contracts(ROOT))
        pc._CERT_CACHE.clear()
        first = pc._certificate_lines(ROOT, cert, witness)
        self.assertEqual(1, len(pc._CERT_CACHE), "第一次必须落缓存")
        self.assertEqual(first, pc._certificate_lines(ROOT, cert, witness))
        self.assertEqual(1, len(pc._CERT_CACHE), "同内容同见证不得新增条目（那一下就是省下来的钱）")
        other = pc._certificate_lines(ROOT, cert, witness + "-变了")
        self.assertEqual(first, other, "键变不该改结果（除非契约真的变了）")
        self.assertEqual(2, len(pc._CERT_CACHE), "见证一变必须换键（否则会读到陈旧复算）")


class ProfileInputFaceTest(unittest.TestCase):
    """`profiles()` 的内容键面**必须等于它真读的件**——收窄输入面是可判的，不是口头承诺。

    依据（实测 2026-09-29）：`profiles()` 不读 `04_模块库`，而旧的共用面把它算进来 ⇒ 改一页 04
    模块库正文会白白重算 111 个包画像（守护逐请求清空按根缓存，这一笔 ~50 ms）。
    """

    def test_reads_stay_inside_declared_face(self):
        import fnmatch
        import os
        from core import conformance_scan as csc
        seen = set()
        orig = csc.read_text_cached

        def traced(path, *a, **k):
            try:
                rel = os.path.relpath(str(path), ROOT).replace(os.sep, "/")
                seen.add(rel)
            except ValueError:                       # 别的盘符 → 记原样，判据照样会抓
                seen.add(str(path))
            return orig(path, *a, **k)

        pc._CACHE.clear()
        pc._CONTENT_CACHE.clear()
        csc.read_text_cached = traced             # type: ignore[assignment]
        try:
            prof = pc.profiles(ROOT)
        finally:
            csc.read_text_cached = orig           # type: ignore[assignment]
        self.assertGreater(len(prof), 100, "画像太少，判据没测到东西")
        bad = sorted(r for r in seen
                     if not any(fnmatch.fnmatch(r, pat) for pat in pc.PROFILE_PATTERNS))
        self.assertEqual([], bad, "画像读到了申报面之外的件（面会漏，缓存会陈旧）：%s" % bad[:5])

    def test_outside_face_change_does_not_rekey_and_inside_does(self):
        """合成树：改 `04_模块库` 不换键；改社区模块契约必换键。"""
        from core import conformance_scan as csc
        with tempfile.TemporaryDirectory() as tmp:
            _write_pack(tmp, "包甲", "包甲:M01")
            core = Path(tmp, "04_模块库", "通用类")
            core.mkdir(parents=True, exist_ok=True)
            (core / "M00_x.md").write_text("一\n", encoding="utf-8")
            fp0 = csc.content_fingerprint(tmp, pc.PROFILE_PATTERNS)
            (core / "M00_x.md").write_text("二\n", encoding="utf-8")
            self.assertEqual(fp0, csc.content_fingerprint(tmp, pc.PROFILE_PATTERNS),
                             "面外的件改了不该换键（否则又白算一遍画像）")
            mod = Path(tmp, "community", "包甲", "modules", "M01_x.md")
            mod.write_text(mod.read_text(encoding="utf-8") + "\n# 变更\n", encoding="utf-8")
            self.assertNotEqual(fp0, csc.content_fingerprint(tmp, pc.PROFILE_PATTERNS),
                                "面内的件改了必须换键（否则会读到陈旧画像）")


class ContractEnumerationTest(unittest.TestCase):
    """模块契约面换共享枚举器（`Path.glob` → `csc.iter_files`）后**面必须逐件一致**。

    依据（实测 2026-09-29）：`Path.glob("community/*/modules/*.md")` 在非末段逐条 `is_dir()`——
    **111 次**，一次新内容状态里独占 ~10 ms（占该状态 stat 面的三分之一）；共享枚举器 **~0.4 ms**。
    """

    def test_faces_match_pathlib_glob(self):
        from pathlib import Path
        from core import conformance_scan as csc
        for pattern in ("community/*/modules/*.md", "04_模块库/*/*.md"):
            want = sorted(p.relative_to(ROOT).as_posix()
                          for p in Path(ROOT).glob(pattern) if p.is_file())
            got = sorted(csc.iter_files(ROOT, pattern))
            self.assertTrue(want, "面 %s 为空，判据没测到东西" % pattern)
            self.assertEqual(want, got, "面 %s 与旧枚举不一致（换实现改动了面）" % pattern)


class PackDirEnumerationTest(unittest.TestCase):
    """`pack_combo._pack_dirs()` 换枚举器（`iterdir` + 逐条 stat → `csc.iter_files`）后面必须一致。

    依据（实测 2026-09-29）：旧写法每次 **20 ms**（111 个目录 ⇒ 200+ 次 stat），而守护**逐请求**
    清空按根缓存，`profiles()` 重算时要再付一遍；换共享枚举器后 **~0.5 ms**。提速只有在「面逐件
    不变」时才允许，所以这里把旧口径原样重算一遍比对。
    """

    def test_matches_legacy_enumeration(self):
        from pathlib import Path
        base = Path(ROOT) / "community"
        legacy = sorted(p for p in base.iterdir()
                        if p.is_dir() and (p / "protocol.yaml").is_file())
        self.assertTrue(legacy, "包面为空，判据没测到东西")
        self.assertEqual(legacy, pc._pack_dirs(ROOT), "包面与旧枚举不一致（换实现改动了面）")


class InputFaceTest(unittest.TestCase):
    """输入面的**枚举口径**与**逐件敏感性**：换实现不许悄悄改面或漏件。

    背景（实测 2026-09-29）：`_inputs_fingerprint` 从 `Path.glob` + 逐件 `read_text_cached(...)`
    换成 `csc.content_fingerprint`（`iter_files` 单遍枚举 + 常驻层逐件摘要）——**57 ms → 2.3 ms**，
    而广度证明一次要调它两遍。提速只有在「面逐件不变」时才允许，所以这两条判据把口径钉住。
    """

    def test_pattern_enumeration_matches_pathlib(self):
        from pathlib import Path

        from core import conformance_scan as csc
        for pat in pc.INPUT_PATTERNS:
            want = sorted(p.relative_to(ROOT).as_posix()
                          for p in Path(ROOT).glob(pat) if p.is_file())
            got = sorted(csc.iter_files(ROOT, pat))
            self.assertTrue(want, "面 %s 枚举为空，判据没测到东西" % pat)
            self.assertEqual(want, got, "输入面枚举在 %s 上不一致（换实现改动了面）" % pat)

    def test_every_face_file_moves_the_fingerprint(self):
        """面里的**每一件**都真的进指纹（逐件变 ⇒ 指纹变；还原 ⇒ 回到原值）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write_pack(tmp, "包甲", "包甲:M01")
            _write_pack(tmp, "包乙", "包乙:M01")
            core = Path(tmp, "desktop", "src", "core")
            core.mkdir(parents=True, exist_ok=True)
            (core / "registry.json").write_text("{}\n", encoding="utf-8")
            assets = Path(tmp, "community", "包甲", "assets")
            assets.mkdir(parents=True, exist_ok=True)
            (assets / "provenance.json").write_text('{"assets": []}\n', encoding="utf-8")

            base = pc._inputs_fingerprint(tmp)
            self.assertEqual(base, pc._inputs_fingerprint(tmp), "同内容必须同指纹")
            for target in (Path(tmp, "community", "包甲", "protocol.yaml"),
                           Path(tmp, "community", "包乙", "modules", "M01_x.md"),
                           core / "registry.json",
                           assets / "provenance.json"):
                before = target.read_text(encoding="utf-8")
                target.write_text(before + "\n# 变更\n", encoding="utf-8")
                self.assertNotEqual(base, pc._inputs_fingerprint(tmp),
                                    "%s 变了指纹却没变（漏件）" % target.name)
                target.write_text(before, encoding="utf-8")
                self.assertEqual(base, pc._inputs_fingerprint(tmp),
                                 "%s 还原后指纹应回到原值" % target.name)


class ComboCacheTest(unittest.TestCase):
    """逐组合判决缓存：等价（不改判定）／同状态零重算／**见证覆盖跨包闭包**（变异注入）。

    依据（实测，2026-09-29）：广度证明 **6885** 次组合 ≈ **982 ms**（唯一新状态里最大单项），而
    「合不合法 + 悬挂/未桥证据」只是「包声明 + 模块契约 + 核心发布集」的纯函数。接缓存后，
    把外层两层缓存**全部作废**，第二名仍是 0 次组合（982 ms → 255 ms，判决逐字段一致）；
    真守护里的新状态实测 `pack_combo.scan` 723 ms → 184 ms。
    """

    def test_combo_verdicts_survive_outer_cache_invalidation(self):
        """真不变量：外层两层缓存都作废，逐组合层仍不许再跑一次组合。"""
        import os

        from core import disk_cache as dc

        calls = []
        orig_combine = pc.combine

        def counting(*a, **k):
            calls.append(1)
            return orig_combine(*a, **k)

        old_off = os.environ.get(dc.ENV_OFF)
        os.environ[dc.ENV_OFF] = "1"          # 关持久层：第二名必须由逐组合层兜住，不许它顶包
        pc.combine = counting                 # type: ignore[assignment]
        try:
            pc.cache_clear()
            pc._CONTENT_CACHE.clear()
            pc._COMBO_CACHE.clear()
            first = pc.breadth(ROOT)
            n_first = len(calls)
            pc.cache_clear()
            pc._CONTENT_CACHE.clear()         # 只作废外层两层，逐组合层留着
            calls.clear()
            second = pc.breadth(ROOT)
            n_second = len(calls)
        finally:
            pc.combine = orig_combine         # type: ignore[assignment]
            if old_off is None:
                os.environ.pop(dc.ENV_OFF, None)
            else:
                os.environ[dc.ENV_OFF] = old_off
            pc.cache_clear()
            pc._CONTENT_CACHE.clear()
        self.assertGreater(n_first, 1000, "首次应真跑组合（判据自身要有效）")
        self.assertEqual(0, n_second, "外层作废后逐组合层仍应全命中")
        self.assertEqual(first, second, "命中缓存的判决必须与首算逐字段一致")

    def test_witness_covers_cross_pack_closure(self):
        """变异注入：**没被点名的包**的模块契约一变，见证必须变、判决必须跟着变。

        这就是「键不许只取参与包自己碰得到的模块」的判据——组合闭包会经 `pub_index` 拉入
        **任意发布方**、经 `by_id` 拉入**任意依赖件**，参与包的 `references` 根本框不住它们。
        按「involved modules」做细键的实现会在这里读到陈旧判决（假绿）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            _write_pack(tmp, "包甲", "包甲:M01", subscribe=["ev_pull"])
            _write_pack(tmp, "包丙", "包丙:M01", publish=["ev_pull"])
            w_before = pc._combo_witness(tmp, pc.profiles(tmp), pc._module_contracts(tmp))
            cert = pc.combine(tmp, packs=["包甲"])
            self.assertIn("包丙:M01", cert["modules"], "事件闭包应拉入第三方发布方")
            self.assertTrue(cert["legal"], "闭包补齐后：无悬挂、未桥")

            _write_pack(tmp, "包丙", "包丙:M01", publish=["ev_pull"], inputs=["查无此件"])
            # 按 root 的进程缓存是**逐请求**清的（守护每请求清一次），测试里手工清，模拟下一条命令
            pc.cache_clear()
            w_after = pc._combo_witness(tmp, pc.profiles(tmp), pc._module_contracts(tmp))
            self.assertNotEqual(w_before, w_after,
                                "第三方包的契约一变，见证必须变（否则会读到陈旧判决）")
            self.assertFalse(pc.combine(tmp, packs=["包甲"])["legal"], "悬挂依赖应让判决翻转")


class CombineTest(unittest.TestCase):
    def test_two_packs_legal_and_stacked(self):
        c = pc.combine(ROOT, packs=["大语言模型域包", "视觉模型域包"])
        self.assertTrue(c["legal"], c)
        self.assertEqual(c["module_count"], 4)
        stacks = {r["layer"]: r["modules"] for r in c["layer_stacks"]}
        self.assertEqual(sorted(stacks), ["P40", "P60"])
        self.assertEqual(len(stacks["P40"]), 2)   # 同层两包默认 → 堆叠

    def test_layer_stack_order_is_canonical(self):
        a = pc.combine(ROOT, packs=["大语言模型域包", "视觉模型域包"])
        b = pc.combine(ROOT, packs=["视觉模型域包", "大语言模型域包"])
        self.assertEqual(a["layer_stacks"], b["layer_stacks"],
                         "层栈顺序须与调用者给序无关（否则 T4 复算假失败）")
        self.assertEqual(a["digest"], b["digest"])

    def test_all_packs_combination_is_legal(self):
        names = sorted(pc.profiles(ROOT))
        c = pc.combine(ROOT, packs=names)
        self.assertTrue(c["legal"], c["dependency_closure"]["dangling"][:3])
        self.assertGreater(c["module_count"], 200)
        self.assertEqual(c["dependency_closure"]["dangling"], [])
        self.assertEqual(c["event_closure"]["unbridged"], [])

    def test_references_are_pulled_transitively(self):
        """轻混组合包借源包模块 → 闭包须连带拉入其 inputs 与事件发布方。"""
        c = pc.combine(ROOT, packs=["校园西幻轻混组合包", "AI保险域包"])
        self.assertTrue(c["legal"], c["event_closure"]["unbridged"])
        pulled = {b["module"] for b in c["modules_borrowed"]}
        self.assertIn("M43", pulled)

    def test_component_level_mix(self):
        c = pc.combine(ROOT, extra_modules=["大语言模型:M01", "视觉模型:M01", "数据采集与清洗:M01"],
                       extra_assets=["量化金融域包:QUANT_METRICS"])
        self.assertTrue(c["legal"], c)
        # 闭包后不止 3 个：事件面闭合会连带拉入 report 层发布方（引擎设计行为）
        self.assertGreaterEqual(c["module_count"], 3)
        self.assertTrue(any("M02" in m for m in c["modules"]), c["modules"])
        self.assertEqual(c["assets_borrowed"][0]["key"], "QUANT_METRICS")
        self.assertEqual(c["assets_borrowed"][0]["mode"], "asset_readonly")

    def test_unknown_pack_is_illegal(self):
        c = pc.combine(ROOT, packs=["不存在的域包"])
        self.assertFalse(c["legal"])
        self.assertEqual(c["unknown_packs"], ["不存在的域包"])

    def test_certificate_is_reproducible(self):
        cert = pc.combine(ROOT, packs=["大语言模型域包", "数据采集与清洗域包"])
        again = pc.combine(ROOT, packs=["大语言模型域包", "数据采集与清洗域包"])
        self.assertEqual(cert["digest"], again["digest"])
        issues, _ = pc.verify_certificate(ROOT, cert)
        self.assertEqual(issues, [])

    def test_declared_certificates_match_recompute(self):
        doc = pc.declared(ROOT)
        self.assertTrue(doc.get("certificates"), "证书台账不得为空")
        for cert in doc["certificates"]:
            issues, st = pc.verify_certificate(ROOT, cert)
            self.assertEqual(issues, [], cert.get("label"))
            self.assertTrue(st["legal"], cert.get("label"))

    def test_breadth_sample_all_legal(self):
        stats = pc.breadth(ROOT, triple_sample=30, quad_sample=15)
        self.assertTrue(stats["all_legal"], stats["failures"][:2])
        self.assertEqual(stats["pairs"], stats["pairs_legal"])

    def test_certificate_schema_rejects_extra_field(self):
        from core import output_forms as of
        bad = dict(pc.combine(ROOT, packs=["大语言模型域包"]))
        bad["surprise"] = 1
        errs = of.json_schema_check(bad, pc.CERT_SCHEMA)
        self.assertTrue(any("多余字段" in e for e in errs), errs)


if __name__ == "__main__":
    unittest.main()
