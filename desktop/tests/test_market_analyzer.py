"""市场协议分析库测试（v2.1.0-B4：依赖闭包 + 挂载冲突，verify check15 ②③ 同构）。

锚点：真实 4 包下 dependencies/conflicts 零 issue（check15 PASS 语义一致）；
构造环/冲突案例触发 issue（RED→GREEN 反证）。
"""
import json
import os
import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import market_analyzer  # noqa: E402
from core.market_analyzer import OFFICIAL13, conflicts, dependencies  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
COMMUNITY = ROOT / "community"
REGISTRY = Path(__file__).resolve().parent.parent / "src" / "core" / "registry.json"


def _prots() -> dict:
    with open(REGISTRY, encoding="utf-8") as f:
        reg = json.load(f)
    return {p["id"]: p for p in reg.get("protocols", [])}


def _data() -> dict:
    """包 id → protocol.yaml package 内容（含 dependencies/references/mount_layers）。"""
    out = {}
    for d in sorted(COMMUNITY.iterdir()):
        pf = d / "protocol.yaml"
        if not pf.is_file():
            continue
        with open(pf, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        out[raw["package"]["id"]] = raw
    return out


class DependenciesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prots = _prots()
        cls.data = _data()

    def test_lightmix_closure_reaches_sources(self):
        """轻混包 references=[校园,西幻] → 依赖闭包 seen 含两源包、零 issue。"""
        seen, issues = dependencies("校园西幻轻混组合包", self.prots, self.data)
        self.assertIn("校园情感领域包", seen)
        self.assertIn("西幻生存领域包", seen)
        self.assertEqual(issues, [])

    def test_plain_package_no_references_empty_closure(self):
        """校园包 references=[] → 依赖闭包空、零 issue。"""
        seen, issues = dependencies("校园情感领域包", self.prots, self.data)
        self.assertEqual(seen, set())
        self.assertEqual(issues, [])

    def test_cycle_detected(self):
        """构造源包含 references → 检出「嵌套 references」（verify 判据：不支持多层组合）。

        注意 verify check15 ② 不递归 references——源包若含 references 直接报「嵌套」
        （多层组合不支持，须闭合官方核心），故 A↔B 环在本语义下以「嵌套」形式暴露而非
        遍历成环。测试锚定此与 verify 一致的判据。
        """
        prots = dict(self.prots)
        prots["环A"] = {"id": "环A", "references": [{"source_package": "环B"}]}
        data = dict(self.data)
        data["环A"] = {"package": {"dependencies": {"core_modules": ["M00"]},
                                   "references": [{"source_package": "环B"}]}}
        # 环B 是环A 的源包，且含 references → 应报「嵌套 references」
        data["环B"] = {"package": {"dependencies": {"core_modules": ["M00"]},
                                   "references": [{"source_package": "环A"}]}}
        seen, issues = dependencies("环A", prots, data)
        self.assertTrue(any("嵌套" in i for i in issues), issues)

    def test_leaf_beyond_official_detected(self):
        """源包 core_modules 越界官方 13 → issues 命中。"""
        prots = dict(self.prots)
        prots["假组合"] = {"id": "假组合", "references": [{"source_package": "假源"}]}
        data = dict(self.data)
        data["假源"] = {"package": {"dependencies": {"core_modules": ["M99"]}}}
        data["假组合"] = {"package": {"dependencies": {"core_modules": []},
                                      "references": [{"source_package": "假源"}]}}
        _, issues = dependencies("假组合", prots, data)
        self.assertTrue(any("M99" in i for i in issues), issues)


class ConflictsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prots = _prots()
        cls.data = _data()

    def test_lightmix_no_conflict_with_sources(self):
        """轻混包各层 default ∩ 校园/西幻同层 default 为空（真实数据零冲突）。"""
        issues = conflicts("校园西幻轻混组合包", self.prots, self.data)
        self.assertEqual(issues, [])

    def test_conflict_detected_when_intersection(self):
        """构造同层 default 交集 → conflicts 命中。"""
        prots = dict(self.prots)
        prots["冲突组合"] = {"id": "冲突组合",
                            "references": [{"source_package": "校园情感领域包"}]}
        data = dict(self.data)
        data["冲突组合"] = {"package": {
            "mount_layers": {"P40 行为决策": {"default": ["情感:M22", "M40"],
                                            "available": []}},
            "references": [{"source_package": "校园情感领域包"}]}}
        issues = conflicts("冲突组合", prots, data)
        # 校园包 P40 default 含 情感:M22 → 交集非空
        self.assertTrue(any("P40" in i and "冲突" in i for i in issues), issues)


class OfficialAnchorTest(unittest.TestCase):
    def test_official13_matches_verify(self):
        """OFFICIAL13 与 verify check14/check15 硬编码一致（12+1 件）。"""
        self.assertEqual(len(OFFICIAL13), 13)
        self.assertIn("M00", OFFICIAL13)
        self.assertIn("通用:M10", OFFICIAL13)
        self.assertIn("事件:M22", OFFICIAL13)


class GradeTest(unittest.TestCase):
    """v2.4.0 A6：模块/包质量分级徽章（官方核心/社区/实验）。"""

    def test_official_module_grade(self):
        self.assertEqual(market_analyzer.grade_of_module("M00"), "official")
        self.assertEqual(market_analyzer.grade_of_module("通用:M10"), "official")
        self.assertEqual(market_analyzer.grade_of_module("事件:M22"), "official")

    def test_experimental_module_grade(self):
        # M91-M99 社区预留段 → experimental
        self.assertEqual(market_analyzer.grade_of_module("M91"), "experimental")
        self.assertEqual(market_analyzer.grade_of_module("M97"), "experimental")
        self.assertEqual(market_analyzer.grade_of_module("M99"), "experimental")

    def test_community_module_grade(self):
        # 社区自带非 M91-M99 段模块（如 M40/M55）→ community
        self.assertEqual(market_analyzer.grade_of_module("M40"), "community")
        self.assertEqual(market_analyzer.grade_of_module("M55"), "community")
        self.assertEqual(market_analyzer.grade_of_module("情感:M22"), "community")

    def test_grades_of_package(self):
        prots = {"校园情感领域包": {"module_ids": ["情感:M22", "M40", "M55"]}}
        grades = market_analyzer.grades_of_package(prots, "校园情感领域包")
        self.assertEqual(grades["情感:M22"], "community")
        self.assertEqual(grades["M40"], "community")
        self.assertEqual(grades["M55"], "community")

    def test_grades_of_package_mixed(self):
        prots = {"测试包": {"module_ids": ["M00", "M91", "M40"]}}
        grades = market_analyzer.grades_of_package(prots, "测试包")
        self.assertEqual(grades["M00"], "official")
        self.assertEqual(grades["M91"], "experimental")
        self.assertEqual(grades["M40"], "community")


if __name__ == "__main__":
    unittest.main()
