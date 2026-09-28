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


class ContentKeyedDerivedCacheTest(unittest.TestCase):
    """派生缓存按**内容**（不是按 root）：输入没变就复用；输入一变就重算（不许陈旧）。

    依据（实测）：广度证明要跑 6885 次组合（~0.92 s）、包画像要重解析 111 个协议声明 +
    235 份模块文档（~0.3–0.5 s），而守护是**逐请求清空按 root 的缓存**的——所以过去每条
    重命令都白交一遍。改按内容指纹缓存后，隔离 A/B（n=5）实测 `evaluate` 中位
    **3683 ms → 3172 ms（−511 ms / −14%）**。
    """

    def test_breadth_reuses_within_same_content(self):
        """键即内容：同内容**第二次不得新增** combine 调用；且判据自身先证明有效。

        口径（2026-09 修订）：本函数现在有两层缓存（进程内内容键 + **持久**内容键），
        所以「第一次一定真跑」不再是真不变量——**先在两层都关掉的最冷状态下证明计数器有效**
        （必须真跑 >1000 次），**再**测真不变量（第二次零新增）。
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
