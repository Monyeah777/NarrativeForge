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

from core import conformance_scan as csc  # noqa: E402
from core import session_watch as sw  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
