#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`lazy_yaml` 的**出声**判据：缺 PyYAML 时不许静默换口径。

依据（实测 2026-09-29）：缺 PyYAML 的后果**不是「慢一点」而是「结果偏小」**——调用方都是静默
降级的（`pipeline_loader` 回退内置子集解析器、`conformance_scan` 解析不出 YAML 字段），实测
`nf doctor` 的 tool_face 1/1/1→0/0/0、world_model 1/4/3/4→0/0/0/0、`pipeline dryrun --json`
6671→3597 字节。故本模块必须**报一次**（stderr，含修复指引），`NF_QUIET_YAML=1` 可静默。
"""
import builtins
import contextlib
import importlib
import io
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


class YamlFallbackNoticeTest(unittest.TestCase):
    @staticmethod
    def _live():
        """绑**当前**模块实例（换版用例会把 `core.*` 换掉——本仓既有纪律）。"""
        return importlib.import_module("core.lazy_yaml")

    def setUp(self):
        self.ly = self._live()
        self._saved = (self.ly._TRIED, self.ly._YAML, getattr(self.ly, "_WARNED", False))

    def tearDown(self):
        self.ly._TRIED, self.ly._YAML = self._saved[0], self._saved[1]
        self.ly._WARNED = self._saved[2]
        os.environ.pop("NF_QUIET_YAML", None)

    def _reset(self):
        self.ly._TRIED = False
        self.ly._YAML = None
        self.ly._WARNED = False

    @staticmethod
    def _capture(fn):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            value = fn()
        return value, err.getvalue()

    @contextlib.contextmanager
    def _yaml_blocked(self):
        """把 `import yaml` 变成 ImportError（只影响本用例，退出即还原）。"""
        real_import = builtins.__import__

        def blocked(name, *a, **k):
            if name == "yaml":
                raise ImportError("blocked for test")
            return real_import(name, *a, **k)

        builtins.__import__ = blocked
        try:
            yield
        finally:
            builtins.__import__ = real_import

    def test_present_yaml_is_silent(self):
        """PyYAML 在位：拿得到模块、拿得到安全加载器、**零告警**（正常环境不许刷噪声）。"""
        self._reset()
        value, err = self._capture(self.ly.module)
        if value is None:
            self.skipTest("本机没装 PyYAML（缺依赖那面由下两条用例覆盖）")
        self.assertEqual("", err, "装了 PyYAML 还告警 = 噪声")
        self.assertIsNotNone(self.ly.safe_loader())

    def test_missing_yaml_warns_exactly_once(self):
        """缺 PyYAML：返回 None（不吞不造）+ **报一次**（含修复指引），第二次不再刷。"""
        self._reset()
        with self._yaml_blocked():
            value, err = self._capture(self.ly.module)
            loader, err2 = self._capture(self.ly.safe_loader)
        self.assertIsNone(value, "缺依赖必须返回 None（不吞不造）")
        self.assertIsNone(loader, "缺依赖时不许给出加载器")
        self.assertIn("PyYAML", err, "缺依赖必须出声（否则结果悄悄偏小）")
        self.assertIn("修复指引", err, "出声必须带修复指引（本仓文案纪律）")
        self.assertEqual("", err2, "只许报一次")

    def test_quiet_switch_silences_the_notice(self):
        """`NF_QUIET_YAML=1`：机器面/对照要能静默（但仍是 None 语义）。"""
        os.environ["NF_QUIET_YAML"] = "1"
        self._reset()
        with self._yaml_blocked():
            value, err = self._capture(self.ly.module)
        self.assertIsNone(value)
        self.assertEqual("", err, "设了静默开关就不许再出声")


if __name__ == "__main__":
    unittest.main()
