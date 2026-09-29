#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""45 check32 · 质量纵深汇总扫描单测。"""
import builtins
import collections
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import quality_depth_scan as qds  # noqa: E402


def _count_opens(fn):
    """跑 fn → (结果, {仓库内文件: 打开次数})。

    用途：把「同一份件在一次扫描里被反复读」变成**确定性判据**——墙钟断言会在 CI 上抖，
    读次数不会；O(n²) 式回归（对每个条目/每条结果重跑一次全量读）会立刻把「单件最大
    读次数」顶上去。
    """
    counts: collections.Counter = collections.Counter()
    orig = io.open

    def spy(file, *a, **k):
        try:
            path = os.path.abspath(str(file))
            if path.startswith(ROOT) and os.sep + ".git" + os.sep not in path \
                    and os.sep + ".rivet" + os.sep not in path:
                counts[os.path.normcase(path)] += 1
        except Exception:  # noqa: BLE001 - 计数失败不影响被测逻辑
            pass
        return orig(file, *a, **k)

    io.open = spy
    builtins.open = spy
    try:
        return fn(), counts
    finally:
        io.open = orig
        builtins.open = orig


class CompositeFaceCoverageTest(unittest.TestCase):
    """并集面 `QD_INPUTS` 必须**覆盖每个子扫描器的面**——漏一条就是「子扫描器会变、聚合却说没变」。

    本判据是为一个**真实陈旧洞**写的（实测 2026-09-29）：`QD_INPUTS` 少了 `domain_pack.SCAN_INPUTS`
    里的两条面——`.rivet/private_archive/ai_packs/specs/*.json`（100 件）与 `registry.json`（1 件）
    ⇒ 改这 101 件里任何一件时，聚合缓存会命中旧值（子扫描器自己的内容键缓存失效了，但外层并集键没变）。
    修法：把两条补齐（并集面是保守面，**宁可多列、不许漏列**），并在此把覆盖性变成可执行判据。
    """

    SUB_FACES = ("core.domain_pack:SCAN_INPUTS", "core.pack_combo:SCAN_INPUTS",
                 "core.output_forms:INDEX_INPUTS", "core.asset_density:ASSET_INPUTS",
                 "core.asset_density:CORPUS_PATTERNS",
                 "core.asset_ledger_projection:VERIFY_INPUTS",
                 "core.concept_graph:CG_INPUTS")

    def test_union_covers_declared_sub_faces(self):
        import importlib
        from core import conformance_scan as csc
        covered = set(r for pat in qds.QD_INPUTS for r in csc.iter_files(ROOT, pat))
        self.assertTrue(covered, "并集面为空")
        for spec in self.SUB_FACES:
            mod_name, attr = spec.split(":")
            pats = getattr(importlib.import_module(mod_name), attr)
            for pat in pats:
                files = csc.iter_files(ROOT, pat)
                miss = [r for r in files if r not in covered]
                self.assertEqual([], miss,
                                 "%s 的 %s 有 %d 件未被 QD_INPUTS 覆盖（陈旧洞）：%s"
                                 % (spec, pat, len(miss), miss[:3]))


class QualityDepthScanTest(unittest.TestCase):
    def test_repo_clean(self):
        # **按当前模块实例量，并先清缓存**（2026-09-29 实测）：本判据量的是「一次纵深扫描的读取形状」，
        # 而派生结果有内容键缓存 ⇒ 若前面某个用例/模块已经把这一状态算热，`scan` 直接命中缓存、
        # **一件都不读**（实测：与 `test_conformance_scan` 同进程连跑时 `reads` 为空，`max()` 直接炸）。
        # 故先绑**当前**实例、清掉两层缓存再量，并把「必须真读到件」立成前提（判据自身要有效）。
        import importlib
        qds_now = importlib.import_module("core.quality_depth_scan")
        csc_now = importlib.import_module("core.conformance_scan")
        csc_now.clear_resident()
        csc_now._DERIVED_MEMO.clear()
        (issues, stats), reads = _count_opens(lambda: qds_now.scan(ROOT))
        self.assertTrue(reads, "判据自身要有效：清缓存后必须真的读到件")
        self.assertEqual(issues, [])
        self.assertIn("payload_registry", stats)
        self.assertIn("asset_ledger", stats)
        self.assertIn("payload_consumer", stats)
        self.assertIn("tool_face", stats)
        self.assertIn("world_model", stats)
        self.assertIn("world_slots", stats)
        # 读取形状（判据，不是计时）：一次纵深扫描里**单份件不得被反复读**。
        # 走「共享语料」后实测：单件最大 5 次、平均 1.94 次/件（此前 9 次 / 3.48 次）。
        # 界限取 8（~1.6× 余量）：内容自然增长够用，而「又加了一个对每条目重跑全量读取的
        # 扫描器」或「共享语料被拆掉」会立刻把它顶上去。
        worst = max(reads.values())
        self.assertLessEqual(
            worst, 8, "单份件在一次纵深扫描里被读了 %d 次（疑似重复读回归）" % worst)


if __name__ == "__main__":
    unittest.main()
