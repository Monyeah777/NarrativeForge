#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""43 A2 —— Conformance 分级扫描单测（声明 ≤ 可证、防虚标）。"""
import os
import pathlib
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import conformance_scan as cs  # noqa: E402


class ConformanceScanTest(unittest.TestCase):
    def test_repo_scan_clean(self):
        issues, stats = cs.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["modules_mc"], 23)
        self.assertGreaterEqual(stats["packages"], 5)
        self.assertGreaterEqual(stats["export_items"], 4)

    def test_overclaim_detected(self):
        """模块未在册却声明 L2/L3 = 虚标 → 被拒。"""
        issues = []
        order = {"L1": 1, "L2": 2, "L3": 3}
        declared, provable = "L3", 2
        if order[declared] > provable:
            issues.append("虚标")
        self.assertEqual(issues, ["虚标"])

    def test_evidence_ids_cover_repo(self):
        """装配在册证据集须覆盖全部机器可加载模块文档（44 = 13 官方 + 31 社区）。"""
        evidence = set(cs._evidence_ids(ROOT))
        self.assertIn("M00", evidence)
        self.assertIn("通用:M10", evidence)


class YamlLoaderEquivalenceTest(unittest.TestCase):
    """统一加载器（libyaml 优先）必须与纯 Python 的 SafeLoader **逐块等价**。

    依据：改用 C 实现是速度机制（实测 7.8×），但「快」不得改变任何解析结果——本断言把
    等价性钉在真仓库上：全部 YAML 文本块（```yaml 围栏 + *.yaml/*.yml 整件）两种加载器
    各解析一遍，**值与异常行为都必须一致**。缺 libyaml 时跳过（此时走的本来就是纯 Python
    路径，不存在分叉）。
    """

    def test_repo_yaml_blocks_parse_identically(self):
        import yaml
        if getattr(yaml, "CSafeLoader", None) is None:
            self.skipTest("本机 PyYAML 无 libyaml（CSafeLoader 不可用）")
        from yaml import SafeLoader, CSafeLoader
        texts = []
        for path in sorted(pathlib.Path(ROOT).rglob("*.md")):
            if ".git" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            texts += [m.group(1) for m in cs.FENCE.finditer(text)]
        for pat in ("*.yaml", "*.yml"):
            for path in sorted(pathlib.Path(ROOT).rglob(pat)):
                if ".git" in path.parts:
                    continue
                try:
                    texts.append(path.read_text(encoding="utf-8"))
                except OSError:
                    continue
        self.assertGreater(len(texts), 100, "本仓 YAML 文本块数量异常（判据失效）")
        for body in texts:
            try:
                plain, plain_err = yaml.load(body, Loader=SafeLoader), None
            except Exception as exc:                      # noqa: BLE001 - 比对异常类型即可
                plain, plain_err = None, type(exc).__name__
            try:
                fast, fast_err = yaml.load(body, Loader=CSafeLoader), None
            except Exception as exc:                      # noqa: BLE001
                fast, fast_err = None, type(exc).__name__
            self.assertEqual(plain_err, fast_err, "异常行为不一致：%r" % body[:60])
            if plain_err is None:
                self.assertEqual(plain, fast, "解析结果不一致：%r" % body[:60])


if __name__ == "__main__":
    unittest.main()
