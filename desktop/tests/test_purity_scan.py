#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""42 M3 —— 纯度体检 check27 单测（四规则 + 变异注入捕获力 = check 的 check）。"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import purity_scan as ps  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class PurityScanTest(unittest.TestCase):
    def test_mutation_r1_end_shell_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "02_联动注册表.md", "# 注册表\n\nandroid 残留行\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("端壳/APK 残留" in i for i in issues), issues)

    def test_mutation_r2_private_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "01_核心协议.md", "# 协议\n\n临时路径 C:\\Users\\x\\tmp 残留\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("私货/可变物" in i for i in issues), issues)

    def test_mutation_r3_dup_heading_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "06_Agent执行协议.md",
                   "# A\n## 回合执行\n## 回合执行\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("重复标题" in i for i in issues), issues)

    def test_mutation_r4_raise_no_guidance_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/bad.py",
                   'def f():\n    raise ValueError("oops")\n')
            issues, stats = ps.scan(tmp)
            self.assertTrue(any("raise 消息缺修复指引" in i for i in issues), issues)
            self.assertEqual(stats["raises"], 1)

    def test_clean_tree_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "01_核心协议.md", "# 协议\n## 模块协议\n")
            _write(tmp, "02_联动注册表.md", "# 注册表\n## 模块表\n")
            _write(tmp, "06_Agent执行协议.md", "# 执行\n## 回合执行\n")
            _write(tmp, "07_官方核心出厂与社区预设导航.md", "# 导航\n## 包索引\n")
            _write(tmp, "desktop/src/core/ok.py",
                   'def f():\n    raise ValueError("请先补 x 再继续")\n')
            issues, _ = ps.scan(tmp)
            self.assertEqual(issues, [])

    def test_mutation_r5_unregistered_third_party_captured(self):
        """R5：未登记的第三方硬 import 被抓（core/scripts 面）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/bad.py", "import requests\n")
            issues, stats = ps.scan(tmp)
            self.assertTrue(any("第三方 import 未登记" in i for i in issues), issues)
            self.assertGreaterEqual(stats["imports"], 1)

    def test_r5_soft_declared_and_hard_allowed_pass(self):
        """R5：软导入 + 登记（jsonschema）与硬依赖白名单（yaml）都放行。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/ok.py",
                   "import yaml\n"
                   "try:\n"
                   "    from jsonschema import Draft202012Validator\n"
                   "except ImportError:\n"
                   "    Draft202012Validator = None\n")
            issues, _ = ps.scan(tmp)
            self.assertEqual(issues, [])

    def test_r5_declared_soft_import_without_guard_is_caught(self):
        """R5：已登记的软依赖若**裸导入**（无守卫）仍判 FAIL——登记不等于免守卫。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "desktop/src/core/bad.py", "from PySide6.QtGui import QImage\n")
            issues, _ = ps.scan(tmp)
            self.assertTrue(any("未软导入" in i for i in issues), issues)

    def test_r5_residue_is_warn_not_fail(self):
        """R5：登记在 IMPORT_RESIDUE 的存量残留走 WARN 挂账（不判死但不得隐身）。

        真表当前为空（2026-09-20 清理后零残留），故用临时登记注入验证机制本身。
        """
        with tempfile.TemporaryDirectory() as tmp:
            saved = dict(ps.IMPORT_RESIDUE)
            ps.IMPORT_RESIDUE.clear()
            ps.IMPORT_RESIDUE["scripts/legacy_selfcheck.py"] = "测试用残留（带裁决指针）"
            try:
                _write(tmp, "scripts/legacy_selfcheck.py", "from ghost.controller import C\n")
                issues, stats = ps.scan(tmp)
                self.assertEqual(issues, [])
                self.assertTrue(any("残留" in w for w in stats["import_residue"]), stats)
                # 同一文件若未登记 → 判 FAIL（登记才是豁免的唯一出口）
                ps.IMPORT_RESIDUE.clear()
                issues2, _ = ps.scan(tmp)
                self.assertTrue(any("未登记" in i for i in issues2), issues2)
            finally:
                ps.IMPORT_RESIDUE.clear()
                ps.IMPORT_RESIDUE.update(saved)

    def test_mutation_r6_dangerous_sinks_captured(self):
        """R6：动态执行 / shell 命令 / 不安全反序列化逐个被抓（core/scripts 面）。"""
        cases = {
            "eval": ("desktop/src/core/s1.py", "eval('1+1')\n"),
            "exec": ("desktop/src/core/s2.py", "exec('x=1')\n"),
            "os.system": ("desktop/src/core/s3.py", "import os\nos.system('ls')\n"),
            "shell=True": ("scripts/s4.py",
                           "import subprocess\nsubprocess.run('ls', shell=True)\n"),
            "pickle.loads": ("desktop/src/core/s5.py", "import pickle\npickle.loads(b'')\n"),
            "yaml.load": ("desktop/src/core/s6.py", "import yaml\nyaml.load('a: 1')\n"),
        }
        for label, (rel, body) in cases.items():
            with tempfile.TemporaryDirectory() as tmp:
                _write(tmp, rel, body)
                issues, stats = ps.scan(tmp)
                self.assertTrue(any("危险 sink" in i for i in issues),
                                "%s 未被捕获：%s" % (label, issues))
                self.assertGreaterEqual(stats.get("sinks", 0), 1)

    def test_r6_registered_sink_allowed(self):
        """R6：登记在 SINK_ALLOW 的受控用法放行（放行须可审计）；未登记即 FAIL。"""
        with tempfile.TemporaryDirectory() as tmp:
            saved = dict(ps.SINK_ALLOW)
            ps.SINK_ALLOW.clear()
            ps.SINK_ALLOW["guarded.py:__import__"] = "测试用登记（模块名来自内部常量表）"
            try:
                _write(tmp, "desktop/src/core/guarded.py",
                       "def f(name):\n    return __import__('core.%s' % name)\n")
                issues, _ = ps.scan(tmp)
                self.assertEqual([i for i in issues if "危险 sink" in i], [])
                ps.SINK_ALLOW.clear()
                issues2, _ = ps.scan(tmp)
                self.assertTrue(any("危险 sink" in i for i in issues2), issues2)
            finally:
                ps.SINK_ALLOW.clear()
                ps.SINK_ALLOW.update(saved)

    def test_r6_real_repo_sink_surface_is_declared(self):
        """真仓库：危险 sink 面只剩已登记项（当前 = regression_score 的受控 __import__）。"""
        issues, stats = ps.scan(ROOT)
        self.assertEqual([i for i in issues if "危险 sink" in i], [],
                         "真仓库出现未登记 sink 即 FAIL")
        self.assertLessEqual(stats.get("sinks", 0), 2)


class SinkRegistryTest(unittest.TestCase):
    """R6 自洽面（本波净吸收）：sink 类目须带 CWE 对齐 + SINK_ALLOW 须指向已登记 sink。"""

    def test_repo_registry_is_self_consistent(self):
        issues, _ = ps.scan(ROOT)
        self.assertEqual([i for i in issues if "CWE" in i or "SINK_ALLOW" in i], [],
                         "仓库 sink 登记面须自洽")
        for call, desc in ps.DANGEROUS_CALLS.items():
            self.assertRegex(desc, r"^CWE-\d+ ", call)

    def test_mutation_missing_cwe_captured(self):
        original = dict(ps.DANGEROUS_CALLS)
        try:
            ps.DANGEROUS_CALLS["eval"] = "动态执行（无 CWE 对齐）"
            issues, _ = ps.scan(ROOT)
        finally:
            ps.DANGEROUS_CALLS.clear()
            ps.DANGEROUS_CALLS.update(original)
        self.assertTrue(any("缺 CWE 对齐" in i for i in issues), issues)

    def test_mutation_allow_key_for_unknown_sink_captured(self):
        original = dict(ps.SINK_ALLOW)
        try:
            ps.SINK_ALLOW["ghost.py:totally_unknown"] = "凭空放行（负例）"
            issues, _ = ps.scan(ROOT)
        finally:
            ps.SINK_ALLOW.clear()
            ps.SINK_ALLOW.update(original)
        self.assertTrue(any("指向未登记 sink" in i for i in issues), issues)


if __name__ == "__main__":
    unittest.main()
