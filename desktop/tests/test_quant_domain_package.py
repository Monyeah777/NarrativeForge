# -*- coding: utf-8 -*-
"""量化金融域包（community 第 7 包 / 第 3 个非叙事域）单测 —— 包体一致性 + 概念图 + 负例。

覆盖：协议声明 ↔ 模块 ↔ 资产 ↔ registry 投影 四面一致；README 双源（check14 ⑥ 口径）；
概念图资产健康（check32 子扫描同源）+ 跨域求值（闭包 / 就绪清单，确定性）；
事件登记闭合与发布方唯一；管线九层与允许段。
负例：图缺陷必须在**本资产**上被抓（注入环）；求值器对越界检索词拒绝。
"""
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

import yaml  # noqa: E402
from core import concept_graph as cg  # noqa: E402
from core.concept_graph import ClosureError  # noqa: E402

PKG = ROOT / "community" / "量化金融域包"
GRAPH = PKG / "assets" / "QUANT_GRAPH.md"
_spec = importlib.util.spec_from_file_location(
    "nf_ai_domain_closure", ROOT / "scripts" / "ai_domain_closure.py")
adc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adc)

OFFICIAL13 = {"M00", "通用:M10", "M08", "M23", "事件:M22", "M06", "M12", "M13",
              "M20", "M24", "M50", "M80", "M90"}


def _mc(text: str) -> dict:
    return yaml.safe_load(text.split("```yaml", 1)[1].split("```", 1)[0])["machine_contract"]


class PackageFaceTest(unittest.TestCase):
    """包体四面一致（协议声明 / 模块 / 资产 / registry 投影）。"""

    @classmethod
    def setUpClass(cls):
        cls.doc = yaml.safe_load((PKG / "protocol.yaml").read_text(encoding="utf-8"))
        cls.pkg = cls.doc["package"]
        reg = json.loads((ROOT / "desktop" / "src" / "core" / "registry.json")
                         .read_text(encoding="utf-8"))
        cls.entry = next(p for p in reg["protocols"] if p["id"] == cls.pkg["id"])

    def test_protocol_fields(self):
        self.assertEqual(self.pkg["pipeline"], "P08")
        self.assertEqual(self.pkg["categories"], ["量化金融"])
        self.assertEqual(self.doc["protocol"]["schema_version"], "2")
        self.assertEqual(self.pkg["references"], [])
        self.assertEqual(self.pkg["dependencies"]["cross_package"], [])
        self.assertTrue(self.pkg["dependencies"]["core_only"])
        self.assertTrue(set(self.pkg["dependencies"]["core_modules"]) <= OFFICIAL13,
                        self.pkg["dependencies"]["core_modules"])

    def test_module_range_matches_modules_and_files(self):
        ids = [m["id"] for m in self.pkg["modules"]]
        self.assertEqual(ids, self.pkg["module_id_range"])
        files = sorted(p.name.split("_", 1)[0] for p in (PKG / "modules").glob("*.md"))
        self.assertEqual(files, ["M31", "M32"])
        for mid in ids:
            cat, num = mid.split(":")
            self.assertIn(cat, self.pkg["categories"])
            self.assertIn(num, files)

    def test_assets_count_matches_files(self):
        count = len(list((PKG / "assets").glob("*.md")))
        self.assertEqual(count, self.pkg["assets"]["count"])
        self.assertEqual(count, 4)

    def test_registry_projection_matches(self):
        self.assertEqual(self.entry["pipeline"], self.pkg["pipeline"])
        self.assertEqual(self.entry["module_ids"], self.pkg["module_id_range"])
        self.assertEqual(self.entry["categories"], self.pkg["categories"])
        self.assertEqual(self.entry["assets"]["count"], self.pkg["assets"]["count"])
        self.assertEqual(str(self.entry.get("version") or "1.0.0"), self.pkg["version"])
        self.assertEqual(self.entry["schema_version"],
                         self.doc["protocol"]["schema_version"])

    def test_readme_is_dual_source_consistent(self):
        readme = (PKG / "README.md").read_text(encoding="utf-8")
        self.assertIn(self.pkg["name"], readme)
        self.assertIn(self.pkg["pipeline"], readme)
        self.assertIn(str(self.pkg["assets"]["count"]), readme)

    def test_pipeline_layers_and_allowed_segment(self):
        text = (PKG / "pipelines" / "P08_量化金融域装配流管线.md").read_text(encoding="utf-8")
        block = yaml.safe_load(text.split("```yaml", 1)[1].split("```", 1)[0])["Pipeline"]
        self.assertEqual(block["id"], "P08")
        layers = block["layers"]
        self.assertEqual([l["id"] for l in layers],
                         ["P00", "P10", "P20", "P30", "P40", "P50", "P60", "P70", "P80"])
        defaults = {l["id"]: l["default_modules"] for l in layers}
        self.assertEqual(defaults["P40"], ["量化金融:M31"])
        self.assertEqual(defaults["P60"], ["量化金融:M32"])
        own = set(self.pkg["module_id_range"])
        for l in layers:
            self.assertTrue(set(l["default_modules"]) <= own | OFFICIAL13, l)
            self.assertTrue(set(l["allowed_modules"]) <= own | OFFICIAL13, l)

    def test_events_are_registered_and_publisher_unique(self):
        reg = json.loads((ROOT / "protocol" / "event_registry.json")
                         .read_text(encoding="utf-8"))
        registered = set(reg["events"])
        published = {}
        for f in sorted((PKG / "modules").glob("*.md")):
            mc = _mc(f.read_text(encoding="utf-8"))
            for ev in mc["events"]["publish"]:
                self.assertIn(ev, registered, "事件未登记载荷：%s" % ev)
                published.setdefault(ev, []).append(mc["id"])
        for ev, owners in published.items():
            self.assertEqual(len(owners), 1, "发布方须唯一：%s -> %s" % (ev, owners))
        self.assertEqual(len(published), 4)

    def test_module_contracts_are_complete(self):
        for f in sorted((PKG / "modules").glob("*.md")):
            mc = _mc(f.read_text(encoding="utf-8"))
            self.assertEqual(mc["schema"], "1")
            self.assertEqual(mc["conformance"], "L2")
            self.assertEqual(mc["category"], "量化金融")
            self.assertIn(mc["layer"], ("P40", "P60"))
            self.assertTrue(mc["interfaces"])


class QuantGraphTest(unittest.TestCase):
    """概念前置图：健康 + 跨域求值 + 负例。"""

    @classmethod
    def setUpClass(cls):
        cls.graph = cg.load_graph(GRAPH)

    def test_graph_health_and_shape(self):
        self.assertEqual(cg.problems(self.graph), [])
        self.assertEqual(len(cg.in_package_ids(self.graph)), 30)
        self.assertEqual(sorted(cg.branch_map(self.graph)),
                         ["data", "foundations", "research"])

    def test_closure_and_frontier_are_reproducible(self):
        first = cg.closure(self.graph, "Q17")
        self.assertEqual(first, cg.closure(cg.load_graph(GRAPH), "Q17"))
        self.assertIn("Q15", first)
        self.assertIn("Q16", first)
        front = cg.frontier(self.graph, ["Q00", "Q01", "Q02", "Q03", "Q04",
                                        "Q05", "Q06", "Q07", "Q08"], branch="research")
        self.assertEqual(front, ["Q09", "Q10", "Q29"])
        self.assertEqual(adc.closure(self.graph, "Q17"), first)   # 工具与门禁同源

    def test_alias_resolution(self):
        self.assertEqual(cg.resolve(self.graph, "回测"), "Q15")
        self.assertEqual(cg.resolve(self.graph, "TCA"), "Q18")
        self.assertEqual(cg.resolve(self.graph, "过拟合"), "Q17")

    def test_unknown_token_rejected(self):
        with self.assertRaises(ClosureError):
            cg.resolve(self.graph, "Q99")

    def test_injected_cycle_is_caught_on_this_asset(self):
        """负例：本资产注入环 → 门禁必抓（证明判据确实作用在本图上）。"""
        broken = copy.deepcopy(self.graph)
        for node in broken["nodes"]:
            if node["id"] == "Q02":
                node["prereqs"] = list(node["prereqs"]) + ["Q15"]
        self.assertTrue(any("环" in i for i in cg.problems(broken)), cg.problems(broken))

    def test_scan_reports_two_graphs_in_repo(self):
        issues, stats = cg.scan(str(ROOT))
        self.assertEqual(issues, [])
        # 图数从货架推导（原硬编码 2：AI 品类域包进场后即误报——同 test_license_gate 修法）
        self.assertEqual(stats["graphs"], len(cg.graph_assets(str(ROOT))))
        self.assertGreaterEqual(stats["graphs"], 2)


if __name__ == "__main__":
    unittest.main()
