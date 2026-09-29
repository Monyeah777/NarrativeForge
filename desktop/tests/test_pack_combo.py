#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""域包自由组合单测：五不变量 / 传递闭包 / references 借入 / 证书 T4 复算 / 广度抽样。

负例取自组合引擎的真实失效类：未知包、悬挂依赖、未桥事件、未解析引用、层栈不稳定。
"""
import json
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
