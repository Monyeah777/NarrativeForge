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


class QualityDepthScanTest(unittest.TestCase):
    def test_repo_clean(self):
        (issues, stats), reads = _count_opens(lambda: qds.scan(ROOT))
        self.assertEqual(issues, [])
        self.assertIn("payload_registry", stats)
        self.assertIn("asset_ledger", stats)
        self.assertIn("payload_consumer", stats)
        self.assertIn("tool_face", stats)
        self.assertIn("world_model", stats)
        self.assertIn("world_slots", stats)
        # 读取形状（判据，不是计时）：一次纵深扫描里**单份件不得被反复读**。
        # 实测（v16 后）：平均 3.5 次/件、单件最大 9 次；界限取 14（~1.5× 余量）——
        # 内容自然增长够用，而「又加了一个对每条目重跑全量读取的扫描器」会把它顶到几十上百。
        worst = max(reads.values())
        self.assertLessEqual(
            worst, 14, "单份件在一次纵深扫描里被读了 %d 次（疑似重复读回归）" % worst)


if __name__ == "__main__":
    unittest.main()
