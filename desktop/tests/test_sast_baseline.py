#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SAST 计数棘轮（`scripts/sast_check.py`）回归测试 —— 安全/供应链面。

只测**纯函数比对**（`compare`）与声明件在场性：不依赖 bandit/ruff 是否安装，
也不依赖工作区状态（并发会话不会把它搞红）。
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("nf_sast_check",
                                                 ROOT / "scripts" / "sast_check.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class CompareTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def test_missing_platform_section_fails_closed(self):
        """缺**本平台**段 = FAIL（fail-closed）：没有冻过的平台不许靠空基线蒙过。"""
        issues, _warns, stats = self.m.compare({"bandit": {"a.py::B101": 1}, "ruff": {}}, {})
        self.assertTrue(any(self.m.BASELINE_REL in i and self.m.PLATFORM in i for i in issues),
                        issues)
        self.assertEqual(0, stats["baseline_bandit"], "缺基线时基线计数须为 0（不得 KeyError）")
        self.assertEqual(1, stats["bandit"])

    def test_new_file_rule_pair_fails(self):
        issues, _w, _s = self.m.compare(
            {"bandit": {"a.py::B101": 1, "b.py::S301": 1}, "ruff": {}},
            {"bandit": {"a.py::B101": 1}, "ruff": {}})
        self.assertTrue(any("新增命中" in i and "b.py" in i for i in issues), issues)

    def test_count_increase_fails(self):
        issues, _w, _s = self.m.compare({"bandit": {"a.py::B101": 3}, "ruff": {}},
                                        {"bandit": {"a.py::B101": 2}, "ruff": {}})
        self.assertTrue(any("命中数上升" in i and "2 → 3" in i for i in issues), issues)

    def test_count_decrease_warns(self):
        issues, warns, _s = self.m.compare({"bandit": {"a.py::B101": 1}, "ruff": {}},
                                           {"bandit": {"a.py::B101": 2}, "ruff": {}})
        self.assertEqual([], issues)
        self.assertTrue(any("命中数下降" in w for w in warns), warns)

    def test_equal_counts_pass(self):
        base = {"bandit": {"a.py::B101": 2}, "ruff": {"b.py::S110": 1}}
        cur = {"bandit": {"a.py::B101": 2}, "ruff": {"b.py::S110": 1}}
        issues, warns, stats = self.m.compare(cur, base)
        self.assertEqual([], issues)
        self.assertEqual([], warns)
        self.assertEqual(3, stats["bandit"] + stats["ruff"])


class RealRepoTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def test_baseline_committed_and_wellformed(self):
        p = ROOT / "protocol" / "sast_baseline.json"
        self.assertTrue(p.is_file(), "须提交 SAST 基线：protocol/sast_baseline.json")
        doc = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual("nf-sast/1", doc["schema"])
        plats = doc.get("platforms") or {}
        self.assertIn("nt", plats, "Windows 段须在册（原基线在此冻结）")
        for name, sec in plats.items():
            self.assertIn("bandit", sec, "platforms[%s] 缺 bandit" % name)
            self.assertIn("ruff", sec, "platforms[%s] 缺 ruff" % name)
            self.assertGreater(sum(sec["bandit"].values()) + sum(sec["ruff"].values()), 0,
                               "platforms[%s] 不许为空（须实算而来）" % name)

    def test_platform_section_is_what_scan_uses(self):
        """比对只吃**本平台**那一段：换平台不会拿另一平台的计数去判。"""
        cur = {"bandit": {"a.py::B101": 1}, "ruff": {}}
        section = {"bandit": {"a.py::B101": 1}, "ruff": {}}
        self.assertEqual([], self.m.compare(cur, section)[0])
        higher = {"bandit": {"a.py::B101": 2}, "ruff": {}}
        self.assertTrue(any("上升" in i for i in self.m.compare(higher, section)[0]),
                        "当前 > 基线 ⇒ 必判上升")
        self.assertEqual({}, self.m.platform_baseline({}))
        other = "posix" if self.m.PLATFORM != "posix" else "nt"     # 不许依赖跑测平台
        self.assertEqual({}, self.m.platform_baseline({"platforms": {other: section}}))
        self.assertEqual(section, self.m.platform_baseline({"platforms": {self.m.PLATFORM: section}}))

    def test_requirements_sast_is_pinned(self):
        p = ROOT / ".github" / "requirements-sast.txt"
        self.assertTrue(p.is_file())
        pins = [l.strip() for l in p.read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#")]
        self.assertTrue(all("==" in l for l in pins), "SAST 工具须固定版本：%s" % pins)


if __name__ == "__main__":
    unittest.main()
