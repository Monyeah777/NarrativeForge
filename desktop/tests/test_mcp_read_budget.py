# -*- coding: utf-8 -*-
"""MCP 工具面的**读取面预算**（稳态毫秒级的计数判据，不测墙钟）。

口径同 `test_nf_cli.LightCommandReadBudgetTest`：**能数就别计时**——一旦有人把「全仓扫描」
塞进本该只读几个文件的工具，打开次数会从个位数跳到四位数，当场红；内容自然增长不会误伤
（面板留了两个数量级余量）。

实测（2026-09-30，默认实时仓库面 · 每个工具一次 `tools/call`）：

    轻面（1–4 次）：spec_ls 1 · registry_query 1 · pattern_read 1 · pipeline_read 1 ·
                    knowledge_order 3 · library_read 4
    扫树面（每次调用都枚举目录）：pipeline_ls 114 · library_search 179 ·
                                module_read 249 · asset_get 361

扫树面是**已知代价**（按 id 解析要枚举 03_管线库 / community/*/modules / community/*/assets）；
本判据只钉「不许更宽」，不假装它免费——按仓库纪律（宁可重算，不可拿旧账当新账），
没有做 mtime 式缓存。
"""
import builtins
import collections
import io
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import mcp_runtime as mrt  # noqa: E402

#: 轻工具：只该碰几个文件（实测 1–4）
LIGHT = {"spec_ls": {}, "registry_query": {"query": "M90"},
         "pattern_read": {"pattern_id": "single-source-truth"},
         "pipeline_read": {"pipeline": "P01"},
         "knowledge_order": {"clearance": "public"},
         "library_read": {"entry_id": "NF-1"}}
LIGHT_BUDGET = 30
#: 扫树工具：按 id 解析要枚举目录树（实测 114–361），留两个数量级余量
SCAN = {"pipeline_ls": {}, "library_search": {"query": "雨天"},
        "module_read": {"module_id": "M90"}, "asset_get": {"key": "STYLE_DNA"}}
SCAN_BUDGET = 600


def _opens(srv, name, args):
    """一次 `tools/call` 期间打开的文件数（计数与机器快慢无关）。"""
    counts = collections.Counter()
    orig = io.open

    def spy(file, *a, **k):
        try:
            path = os.path.normcase(os.path.abspath(str(file)))
            if ".git" not in path and ".rivet" not in path:
                counts[path] += 1
        except Exception:                    # noqa: BLE001 - 计数失败不影响被测逻辑
            pass
        return orig(file, *a, **k)

    io.open = spy
    builtins.open = spy
    try:
        srv.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": name, "arguments": args}})
    finally:
        io.open = orig
        builtins.open = orig
    return sum(counts.values())


class McpReadBudgetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = mrt.McpRuntime({"mcp": {"name": "budget", "version": "0", "resources": []}})

    def test_light_tools_do_not_scan_the_repo(self):
        for name, args in LIGHT.items():
            got = _opens(self.srv, name, args)
            self.assertLessEqual(
                got, LIGHT_BUDGET,
                "MCP 工具 `%s` 打开了 %d 个文件（>%d）——轻面里混进了全仓扫描？"
                % (name, got, LIGHT_BUDGET))

    def test_scan_tools_stay_within_the_known_ceiling(self):
        for name, args in SCAN.items():
            got = _opens(self.srv, name, args)
            self.assertLessEqual(
                got, SCAN_BUDGET,
                "MCP 工具 `%s` 打开了 %d 个文件（>%d）——扫树面比在册上限更宽了？"
                % (name, got, SCAN_BUDGET))

    def test_repeat_calls_do_not_amplify(self):
        """稳态：连续两次同一调用，第二次的开销不得**放大**（防「每次调用都加一层扫描」）。"""
        first = _opens(self.srv, "registry_query", {"query": "M90"})
        second = _opens(self.srv, "registry_query", {"query": "M90"})
        self.assertLessEqual(second, max(first, 1) * 2)


if __name__ == "__main__":
    unittest.main()
