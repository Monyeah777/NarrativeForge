# -*- coding: utf-8 -*-
"""引擎动态加载器（core/engine_loader.py）回归测试 —— 装载机制 / fail-closed。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import engine_loader as el  # noqa: E402


class EngineLoaderTest(unittest.TestCase):
    def test_c_library_nonempty(self):
        self.assertTrue(el.c_library())

    def test_abi_probe_mechanism_works(self):
        doc = el.abi_probe()
        self.assertTrue(doc["library"])
        self.assertIn("detail", doc)
        self.assertTrue(doc["ok"], doc)

    def test_load_missing_is_none(self):
        self.assertIsNone(el.load(str(ROOT / "no-such-lib.dll")))
        self.assertIsNone(el.load(""))

    def test_engine_abi_is_fail_closed(self):
        self.assertTrue(el.ABI_SYMBOL)
        self.assertIsNone(el.engine_abi(str(ROOT / "no-such-lib.dll")))
        # 平台 C 运行库没有本仓的 ABI 符号 → 必须 fail-closed 返回 None（不假装成功）
        self.assertIsNone(el.engine_abi(el.c_library()))

    def test_engine_abi_for_every_built_provider_lib(self):
        """引擎线产出原生库时（target/ 与 dist/ 均不入库），必须能真载入并取到 ABI 版本。

        覆盖面 = 两条线：Rust cdylib（cargo --lib）与 .NET NativeAOT（dotnet publish -p:PublishAot）。
        """
        found = 0
        for engine_dir in ("rust", "dotnet"):
            for rel in el.provider_libs(str(ROOT), engine_dir):
                got = el.engine_abi(str(ROOT / rel))
                self.assertIsInstance(got, int, rel)
                self.assertGreaterEqual(got, 1)
                found += 1
        if not found:
            self.skipTest("两条引擎线均未构建原生库（target/ 与 dist/ 不入库）")

    def test_provider_libs_are_relative_sorted(self):
        libs = el.provider_libs(str(ROOT), "rust")
        self.assertEqual(sorted(libs), libs)
        self.assertTrue(all(l.endswith((".dll", ".so", ".dylib")) for l in libs))
        self.assertEqual([], el.provider_libs(str(ROOT), "no-such-engine"))
        self.assertEqual([], el.provider_libs(str(ROOT), ""))


if __name__ == "__main__":
    unittest.main()
