#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`nf shell` 会话缓存的判据：**新鲜度**（改了必须看见）+ **不留残影**（收尾必须整批作废）。

会话缓存＝监听（`core.watch`）+ 常驻语料层（`conformance_scan._RESIDENT`）：它只换「怎么读到
同一份字节」，值逐位相同（等值性由 `ResidentRawEquivalenceTest` 等既有判据守着）；新增的风险面
只有两个——**陈旧**与**跨会话残影**，本文件把这两条钉死。
"""
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import watch  # noqa: E402


def _wait_generation(w, before: int, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if w.generation > before:
            return True
        time.sleep(0.02)
    return False


class SessionCacheTest(unittest.TestCase):
    @staticmethod
    def _live():
        """绑**当前**模块实例。

        `test_watch.test_resident_layer_survives_a_code_reload` 会逼 `daemon._sync_code` 把 `core.*`
        从 `sys.modules` 摘掉重载 ⇒ 本模块**导入时**拿到的那份是**旧实例**，而 `session_watch._install`
        在调用时 `from core import ...` 现取的是**新实例**。拿旧实例当观测面会读出「release 之后常驻层
        还在」这种看着像 bug 的读数（2026-09-29 门禁整跑实测踩到）。统一在用例内现取。
        """
        import importlib
        return (importlib.import_module("core.conformance_scan"),
                importlib.import_module("core.session_watch"),
                importlib.import_module("core.watch"))

    def tearDown(self):
        self._live()[1].release()          # 任何路径都不许把残影留到下一个用例（按当前实例）

    def test_unavailable_platform_degrades_without_side_effects(self):
        """监听不可用时 `attach` 必须返回 False，且**不装常驻层**（行为与今天逐字一致）。"""
        csc, sw, watch = self._live()
        if watch.available():
            self.skipTest("本平台有监听实现；降级面由 `test_release_leaves_no_resident` 覆盖")
        csc.clear_resident()
        self.assertFalse(sw.attach("."))
        self.assertFalse(csc.resident_active(), "降级路径不许装常驻层")

    def test_release_leaves_no_resident(self):
        """收尾（正常/异常都走 `release`）之后不得再声称常驻层在位。"""
        csc, sw, _watch = self._live()
        with tempfile.TemporaryDirectory() as tmp:
            attached = sw.attach(tmp)
            if attached:
                self.assertTrue(csc.resident_active(), "装上监听就该装常驻层")
            sw.release()
            self.assertFalse(csc.resident_active(), "release 之后常驻层必须整批作废")

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现（本波仅 Windows）")
    def test_edit_is_visible_after_sync(self):
        """**新鲜度**：会话内改了件 ⇒ `sync` 之后必须读到新内容（缓存不许把改动藏起来）。"""
        csc, sw, _watch = self._live()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "probe.md")
            p.write_text("一\n", encoding="utf-8")
            self.assertTrue(sw.attach(tmp), "监听启动失败")
            try:
                self.assertEqual("一\n", csc.read_text_cached(p))
                w = sw._WATCHER
                before = w.generation
                p.write_text("二\n", encoding="utf-8")
                self.assertTrue(_wait_generation(w, before), "改动未被监听到")
                sw.sync(tmp)                       # 会话里每条命令前都会走这一步
                self.assertEqual("二\n", csc.read_text_cached(p),
                                 "改了却读到旧内容 ⇒ 会话缓存陈旧（比慢更糟）")
            finally:
                sw.release()


class SessionResponseCacheTest(unittest.TestCase):
    """会话**响应缓存**（`core.response_cache`）的判据：命中逐字相同 + 改了必重算 + 写形态必作废。

    会话命令走 `Session.invoke` 的捕获层，故「命中」判据必须是**逐字节相同**而不是「看起来像」；
    另两条（新鲜度、非准入作废）与守护同源，见 `core.response_cache` 的纪律段。
    """

    @staticmethod
    def _live():
        """绑**当前**模块实例（理由同 `SessionCacheTest._live`：换版用例会把 `core.*` 换掉）。"""
        import importlib
        return (importlib.import_module("core.response_cache"),
                importlib.import_module("core.session_watch"),
                importlib.import_module("core.daemon"),
                importlib.import_module("core.watch"))

    def setUp(self):
        self.rc, self.sw, self.dm, self.watch = self._live()
        self.rc.clear()

    def tearDown(self):
        self.sw.release()
        self.rc.clear()

    @staticmethod
    def _capture(runner, argv):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            code = runner(list(argv))
        return code, buf.getvalue()

    @staticmethod
    def _counter(state):
        """假命令：每**真跑**一次就自增并打印——命中回放时计数不动、文本也不变。"""
        def base(argv, *a, **k):
            state["n"] += 1
            print("输出 %d" % state["n"])
            return 0
        return base

    def _runner(self, tmp, state):
        return self.rc.wrap_runner(self._counter(state), self._decide,
                                   lambda: self.sw.sync(tmp))

    def _decide(self, argv):
        """代际 + 准入判据（与守护同源；由调用方给出 ⇒ `response_cache` 不依赖上层模块）。"""
        return self.dm._watch_generation(), self.dm.cacheable([str(a) for a in argv])

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现")
    def test_hit_replays_identical_bytes_without_rerun(self):
        """命中 = **不重跑** + 回放同一份字节（准入命令：`stats` 在守护的准入表里）。"""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(self.sw.attach(tmp), "监听启动失败")
            state = {"n": 0}
            run = self._runner(tmp, state)
            first = self._capture(run, ["stats"])
            second = self._capture(run, ["stats"])
            self.assertEqual(1, state["n"], "命中不得重跑命令")
            self.assertEqual((0, "输出 1\n"), first)
            self.assertEqual(first, second, "命中必须回放同一份字节")

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现")
    def test_edit_recomputes_and_serves_new_output(self):
        """**新鲜度**：会话内改了件 ⇒ 下一条准入命令必须重算（宁可慢，不可错）。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp, "probe.md")
            p.write_text("一\n", encoding="utf-8")
            self.assertTrue(self.sw.attach(tmp), "监听启动失败")
            state = {"n": 0}
            run = self._runner(tmp, state)
            self._capture(run, ["stats"])
            before = self.dm._watch_generation()
            p.write_text("二\n", encoding="utf-8")
            self.assertTrue(_wait_generation(self.dm._WATCHER, before), "改动未被监听到")
            code, out = self._capture(run, ["stats"])
            self.assertEqual(2, state["n"], "改了就必须重算（不得回放旧响应）")
            self.assertEqual((0, "输出 2\n"), (code, out))

    @unittest.skipUnless(watch.available(), "本平台没有目录监听实现")
    def test_non_cacheable_invalidates_whole_cache(self):
        """非准入（无法证明只读）⇒ **立刻整批作废**：下一条准入命令不得再命中。"""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(self.sw.attach(tmp), "监听启动失败")
            state = {"n": 0}
            run = self._runner(tmp, state)
            self._capture(run, ["stats"])
            self.assertEqual(1, self.rc.entries())
            self._capture(run, ["help"])               # `help` 不在准入表里
            self.assertEqual(0, self.rc.entries(), "非准入命令必须立刻整批作废")
            self._capture(run, ["stats"])
            # 计数账：`stats` 真跑(1) + `help` 真跑(2) + 作废后的 `stats` 再真跑(3)——若第二遍
            # 命中，第三次就不会跑（仍是 2）⇒ 这一条断言正是「作废是否真的发生了」。
            self.assertEqual(3, state["n"], "作废之后不得再命中（命中会少跑一次）")

    def test_no_watcher_means_no_caching_at_all(self):
        """fail-closed：代际不可知 ⇒ 一律不命中、不建档（行为与加缓存之前逐字一致）。"""
        self.sw.release()
        state = {"n": 0}
        run = self.rc.wrap_runner(self._counter(state), self._decide, None)
        self._capture(run, ["stats"])
        self._capture(run, ["stats"])
        self.assertEqual(2, state["n"], "没有监听时必须每条都真跑")
        self.assertEqual(0, self.rc.entries(), "没有监听时不得留下任何缓存条目")


if __name__ == "__main__":
    unittest.main()
