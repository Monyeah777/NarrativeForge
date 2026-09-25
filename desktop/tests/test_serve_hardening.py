#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""决策层本地服务加固回归测试 —— 渗透发现 F-06。

覆盖两处加固：
  ① 非回环绑定默认拒绝（该服务**无鉴权**，暴露即等于把决策接口与模型算力交出去）；
  ② 请求体上限常量在场（无上限时按自称长度无界读入 = 内存型 DoS）。

为什么可以安全地调 `main()`：`main()` 的绑定守卫排在 `_load_agent()` **之前**，
而 `_load_agent` 在缺 laya 或缺模型目录时一律 SystemExit——所以本测试永远不会真的起服务。
"""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOD_PATH = ROOT / "scripts" / "serve_decision_model.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("nf_serve_decision_model", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class ServeHardeningTest(unittest.TestCase):
    def setUp(self):
        self.mod = _load_module()

    def test_body_cap_constant_is_present(self):
        cap = getattr(self.mod, "MAX_BODY_BYTES", 0)
        self.assertGreater(cap, 0, "缺请求体上限 → 按自称长度无界读入（内存型 DoS）")
        self.assertLessEqual(cap, 16 * 1024 * 1024, "上限过大，起不到防护作用")

    def test_non_loopback_bind_is_refused_by_default(self):
        for host in ("0.0.0.0", "::", "192.168.1.10"):
            with self.assertRaises(SystemExit, msg=host) as ctx:
                self.mod.main(["--host", host])
            self.assertIn("拒绝绑定非回环地址", str(ctx.exception),
                          "非回环绑定须明确拒绝并给出修复指引")

    def test_loopback_bind_passes_the_guard(self):
        """回环地址不得被误拦：过了守卫后会停在 laya/模型目录检查（仍是 SystemExit）。"""
        with self.assertRaises(SystemExit) as ctx:
            self.mod.main(["--host", "127.0.0.1", "--model-dir", "no-such-model-dir"])
        self.assertNotIn("拒绝绑定非回环地址", str(ctx.exception))

    def test_explicit_opt_in_allows_non_loopback(self):
        with self.assertRaises(SystemExit) as ctx:
            self.mod.main(["--host", "0.0.0.0", "--allow-non-loopback",
                           "--model-dir", "no-such-model-dir"])
        self.assertNotIn("拒绝绑定非回环地址", str(ctx.exception))

    def test_loopback_host_allowlist_content(self):
        self.assertIn("127.0.0.1", self.mod.LOOPBACK_HOSTS)
        self.assertIn("::1", self.mod.LOOPBACK_HOSTS)


if __name__ == "__main__":
    unittest.main()
