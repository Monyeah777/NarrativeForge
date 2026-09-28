#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""目录监听 + 守护响应缓存单测（毫秒级执行层的「**不重算**」判据）。

分层：
- 响应缓存的准入/失效逻辑**与平台无关**（注入假监听件测），任何平台都跑；
- `watch.DirWatcher` 本身只在有实现的本平台跑（本波仅 Windows），其余平台跳过并检查降级面。
"""
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[2])
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import daemon as dm  # noqa: E402
from core import watch  # noqa: E402


def _wait_generation(w, before: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if w.generation > before:
            return True
        time.sleep(0.02)
    return False


class _FakeWatcher:
    """假监听件：单测据此判「命中 / 未命中 / 失效」，不受平台与真实通知时序影响。"""

    def __init__(self, generation: int = 1, healthy: bool = True) -> None:
        self.generation = generation
        self.healthy = healthy
        self.overflowed = False


class ResponseCacheTest(unittest.TestCase):
    """响应缓存：准入表 + 「同代际命中 / 代际一变重算」+ 不可用时 fail-closed。"""

    def setUp(self):
        self._old = dm._WATCHER
        dm.reset_response_cache()
        for k in dm._CACHE_STATS:
            dm._CACHE_STATS[k] = 0

    def tearDown(self):
        dm._WATCHER = self._old
        dm.reset_response_cache()

    def test_cacheable_truth_table(self):
        """准入表：纯读且在表内 → 可缓存；写盘开关 / 表外命令 → 一律不缓存。"""
        yes = (["--version"], ["score"], ["score", "--json"], ["conformance"],
               ["layers"], ["stats", "--check"], ["stats", "--json"])
        no = ([], ["conformance", "--write"], ["score", "--write-baseline"],
              ["stats", "--write"], ["doctor"], ["serve"], ["layers", "--out", "x.json"],
              ["layers", "--fix"], ["conformance", "--write", "--json"])
        for argv in yes:
            self.assertTrue(dm.cacheable(argv), argv)
        for argv in no:
            self.assertFalse(dm.cacheable(argv), argv)

    def test_unchanged_tree_hits_cache_and_generation_bump_invalidates(self):
        dm._WATCHER = _FakeWatcher(generation=7)
        first = dm.execute(["--version"], Path(ROOT))
        second = dm.execute(["--version"], Path(ROOT))
        self.assertEqual(first, second)
        self.assertEqual(1, dm.cache_stats()["hits"], "同代际第二次必须命中缓存")
        dm._WATCHER.generation = 8                    # 树变了：监听件报新代际
        third = dm.execute(["--version"], Path(ROOT))
        self.assertEqual(first, third)
        self.assertEqual(1, dm.cache_stats()["hits"], "代际一变必须重算（不得复用旧响应）")

    def test_unhealthy_watcher_never_serves_cache(self):
        """监听不可信（未启动 / 失效）→ 缓存整体停用：不命中、也不留旧条目。"""
        dm._WATCHER = _FakeWatcher(generation=3, healthy=False)
        dm.execute(["--version"], Path(ROOT))
        dm.execute(["--version"], Path(ROOT))
        st = dm.cache_stats()
        self.assertFalse(st["enabled"])
        self.assertEqual(0, st["hits"])
        self.assertEqual(0, st["entries"])

    def test_non_allowlisted_command_is_not_cached(self):
        dm._WATCHER = _FakeWatcher(generation=1)
        dm.execute(["help"], Path(ROOT))
        dm.execute(["help"], Path(ROOT))
        st = dm.cache_stats()
        self.assertEqual(0, st["entries"], "非准入命令不得进缓存")
        self.assertEqual(0, st["hits"])

    def test_allowlisted_commands_are_byte_reproducible(self):
        """**准入判据本身**：同树连跑两次，退出码 / stdout / stderr 必须逐字节相同。

        缓存把「旧输出」当「新输出」的前提，是这些命令对同一棵树是**纯函数**——一旦某条命令
        的输出里混进时间戳 / 耗时 / 随机序，本判据当场红，逼着把它从 `CACHEABLE_COMMANDS` 删掉。
        """
        dm._WATCHER = None                            # 关缓存：这里测的是命令自身
        for argv in (["--version"], ["layers", "--json"], ["score", "--json"],
                     ["conformance", "--json"], ["stats", "--json"]):
            a = dm.execute(list(argv), Path(ROOT))
            b = dm.execute(list(argv), Path(ROOT))
            self.assertEqual(a, b,
                             "输出不可复现，不得进 CACHEABLE_COMMANDS：nf %s" % " ".join(argv))


class WatchDaemonIntegrationTest(unittest.TestCase):
    """端到端（进程内起真服务）：带监听的守护「树没变 → 整条复用；代际一变 → 重算」。

    进程内起服务是**覆盖率要点**：守护通常在子进程里跑，那段代码在 `coverage run` 里不可见
    （见 test_daemon.DaemonInProcessServerTest 的同款说明）。本用例**不往仓库写任何文件**：
    「树变了」由真监听件的代际推进来模拟，真通知面由 DirWatcherTest 在临时目录里测。
    """

    def setUp(self):
        if not watch.available():
            self.skipTest("本平台没有目录监听实现（本波仅 Windows）")
        self.home = tempfile.mkdtemp(prefix="nf_watch_ip_")
        self._old_home = os.environ.get("NARRATIVE_FORGE_HOME")
        os.environ["NARRATIVE_FORGE_HOME"] = self.home
        self.port = None

        def ready(port):
            self.port = port

        self.thread = threading.Thread(target=dm.serve_forever,
                                       args=(ROOT, 30.0, ready),
                                       kwargs={"watch": True}, daemon=True)
        self.thread.start()
        for _ in range(300):
            if self.port:
                break
            time.sleep(0.01)
        self.assertIsNotNone(self.port, "进程内服务未能就绪")

    def tearDown(self):
        dm.stop()
        self.thread.join(timeout=5)
        if self._old_home is None:
            os.environ.pop("NARRATIVE_FORGE_HOME", None)
        else:
            os.environ["NARRATIVE_FORGE_HOME"] = self._old_home
        import shutil
        shutil.rmtree(self.home, ignore_errors=True)

    def _call(self, argv):
        doc = dm.read_state()
        self.assertIsNotNone(doc, "服务在跑，状态文件必须可读")
        return dm.run_request(doc, argv, cwd=ROOT)

    def test_cache_enabled_and_hit_then_invalidated_by_generation(self):
        st = dm.query_stats()
        self.assertIsNotNone(st, "守护必须能回答 stats（观测面在守护进程内）")
        self.assertTrue(st["enabled"], "带 --watch 起的守护必须启用响应缓存")
        self.assertEqual(0, st["generation"])

        first = self._call(["--version"])
        second = self._call(["--version"])
        self.assertEqual(first, second)
        st2 = dm.query_stats()
        self.assertEqual(1, st2["hits"], "同代际第二次必须命中响应缓存")
        self.assertEqual(1, st2["entries"])

        dm._WATCHER._bump()                       # 模拟「真监听件收到一批变更通知」
        third = self._call(["--version"])
        self.assertEqual(first, third)
        st3 = dm.query_stats()
        self.assertEqual(1, st3["hits"], "代际一变不得复用旧响应")
        self.assertGreaterEqual(st3["generation"], 1)

    def test_readonly_commands_are_cached_and_write_flags_bypass(self):
        """两条只读命令各占一条缓存；带写盘开关的一律**绕过**（绝不进表）。

        口径要**确定性**：先清缓存与计数，再跑两条互不相同的只读命令 → 条目/未命中都必须是 2。
        （早先写成「只有 --version 该被缓存」是错的：`conformance` 本来就在准入表里。）
        """
        dm.reset_response_cache()
        for k in dm._CACHE_STATS:
            dm._CACHE_STATS[k] = 0
        self._call(["--version"])
        self._call(["layers", "--json"])
        st = dm.query_stats()
        self.assertEqual(2, st["entries"], "两条只读命令应各占一条响应缓存")
        self.assertEqual(2, st["misses"], "两条都该是未命中（缓存刚清）")
        for argv in (["conformance", "--write"], ["stats", "--write"],
                     ["score", "--write-baseline"], ["layers", "--out", "x"]):
            self.assertFalse(dm.cacheable(argv), argv)


class DirWatcherTest(unittest.TestCase):
    """真实监听件（有实现的平台才跑）+ 无实现平台的降级面。"""

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现（本波仅 Windows）")
    def test_detects_create_modify_and_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = watch.DirWatcher(tmp)
            self.assertTrue(w.start(), "监听启动失败（拿不到目录句柄？）")
            try:
                for action in ("create", "modify", "delete"):
                    before = w.generation
                    p = Path(tmp) / "probe.txt"
                    if action == "create":
                        p.write_text("一", encoding="utf-8")
                    elif action == "modify":
                        p.write_text("二", encoding="utf-8")
                    else:
                        p.unlink()
                    self.assertTrue(_wait_generation(w, before), "%s 未被监听到" % action)
            finally:
                w.stop()
            self.assertFalse(w.healthy, "stop() 之后不得再声称健康")
            self.assertFalse(w.start() and not w.healthy)

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现（本波仅 Windows）")
    def test_subdirectory_changes_are_recursive(self):
        """子树递归：本仓的语料大多在子目录里（漏了递归就等于漏判）。"""
        with tempfile.TemporaryDirectory() as tmp:
            w = watch.DirWatcher(tmp)
            self.assertTrue(w.start())
            try:
                before = w.generation
                sub = Path(tmp) / "community" / "包" / "modules"
                sub.mkdir(parents=True)
                (sub / "m.md").write_text("一", encoding="utf-8")
                self.assertTrue(_wait_generation(w, before), "子目录变更未被监听到")
            finally:
                w.stop()

    def test_overflow_is_reported_and_bumps_generation(self):
        """缓冲溢出必须**如实上报**（调用方据此作废全部缓存），且代际继续单调。"""
        w = watch.DirWatcher(ROOT)
        before = w.generation
        w._bump(overflow=True)
        self.assertTrue(w.overflowed)
        self.assertEqual(before + 1, w.generation)

    @unittest.skipIf(watch.available(), "仅在「无实现平台」检查降级面")
    def test_unavailable_platform_degrades_without_raising(self):
        w = watch.DirWatcher(ROOT)
        self.assertFalse(w.start())
        self.assertFalse(w.healthy)
        w.stop()                                      # 幂等、不抛


if __name__ == "__main__":
    unittest.main()
