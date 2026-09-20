# -*- coding: utf-8 -*-
"""概念图健康门禁测试（check32 子扫描 `core.concept_graph` + 求值器同源校验）。

覆盖：
- 正例：仓库真实概念图（AI系统域包）零 issue，且统计到节点/边；
- 同源：`scripts/ai_domain_closure.py` 与 `core.concept_graph` 语义一致（单一实现）；
- 中性：货架上没有 concept_graph 机读块 → 扫描 0 图 0 issue（不影响既有包 / 用户资产）；
- 负例（七类）：环 / 悬空前置 / 重复别名 / 未归支 / 缺溯源 / 节点 id 重复 / 层位越界。
"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import concept_graph as cg  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "nf_ai_domain_closure", ROOT / "scripts" / "ai_domain_closure.py")
adc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adc)


def _graph_md(body: str) -> str:
    return "# 概念图（夹具）\n\n```yaml\nconcept_graph:\n%s\n```\n" % body


_BASE = """  version: "1.0"
  domain: 夹具域
  branches:
    - id: b1
      nodes: [C01, C02]
  nodes:
    - {id: C01, name: 甲, layer: P00, prereqs: [], provenance: [fixture], aliases: [alpha]}
    - {id: C02, name: 乙, layer: P10, prereqs: [C01], provenance: [fixture], aliases: [beta]}
"""


def _tree(tmp: str, body: str = _BASE, pkg: str = "测试域包") -> Path:
    path = Path(tmp) / "community" / pkg / "assets"
    path.mkdir(parents=True, exist_ok=True)
    (path / "CONCEPT_GRAPH.md").write_text(_graph_md(body), encoding="utf-8")
    return path


class RepoGraphTest(unittest.TestCase):
    """仓库真实资产：零 issue + 统计可复现 + 与求值器同源。"""

    def test_repo_scan_clean(self):
        issues, stats = cg.scan(str(ROOT))
        self.assertEqual(issues, [])
        # 两个域包各带一件概念图资产（AI系统域包 47 概念 + 量化金融域包 30 概念）
        self.assertEqual(stats["graphs"], 2)
        self.assertEqual(stats["nodes"], 77)
        self.assertGreater(stats["edges"], 0)

    def test_scanner_and_evaluator_share_semantics(self):
        """单一实现：求值器（scripts/）与门禁（core/）对同一图同解。"""
        graph = cg.load_graph(ROOT / cg.DEFAULT_ASSET)
        self.assertEqual(adc.closure(graph, "C22"), cg.closure(graph, "C22"))
        self.assertEqual(adc.toposort(graph), cg.toposort(graph))
        self.assertEqual(adc.problems(graph), cg.problems(graph))
        self.assertEqual(adc.frontier(graph, ["C00", "C01"]),
                         cg.frontier(graph, ["C00", "C01"]))


class NeutralTest(unittest.TestCase):
    """无概念图资产的货架：扫描中性通过（不误伤既有包与用户自定义资产）。"""

    def test_shelf_without_graph_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "community" / "无图包" / "assets"
            d.mkdir(parents=True)
            (d / "PLAIN_ASSET.md").write_text("# 普通资产\n\n无机读块。\n", encoding="utf-8")
            issues, stats = cg.scan(tmp)
            self.assertEqual(issues, [])
            self.assertEqual(stats["graphs"], 0)

    def test_empty_repo_is_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cg.scan(tmp), ([], {"graphs": 0, "nodes": 0, "edges": 0}))


class NegativeGraphTest(unittest.TestCase):
    """七类图缺陷必须被门禁点名（负例注入，逐例独立夹具）。"""

    def _scan(self, body: str):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp, body)
            return cg.scan(tmp)

    def test_cycle_detected(self):
        body = _BASE.replace("prereqs: []", "prereqs: [C02]")
        issues, _ = self._scan(body)
        self.assertTrue(any("环" in i for i in issues), issues)

    def test_dangling_prereq_detected(self):
        body = _BASE.replace("prereqs: [C01]", "prereqs: [C01, C99]")
        issues, _ = self._scan(body)
        self.assertTrue(any("悬空" in i for i in issues), issues)

    def test_duplicate_alias_detected(self):
        body = _BASE.replace("aliases: [beta]", "aliases: [alpha]")
        issues, _ = self._scan(body)
        self.assertTrue(any("别名重复" in i for i in issues), issues)

    def test_node_outside_branch_detected(self):
        body = _BASE.replace("nodes: [C01, C02]", "nodes: [C01]")
        issues, _ = self._scan(body)
        self.assertTrue(any("未归入任何分支" in i for i in issues), issues)

    def test_missing_provenance_detected(self):
        body = _BASE.replace(", provenance: [fixture], aliases: [beta]", "")
        issues, _ = self._scan(body)
        self.assertTrue(any("溯源" in i for i in issues), issues)

    def test_duplicate_node_id_detected(self):
        body = _BASE + ("    - {id: C02, name: 丙, layer: P10, prereqs: [C01],"
                        " provenance: [fixture]}\n")
        issues, _ = self._scan(body)
        self.assertTrue(any("节点 id 重复" in i for i in issues), issues)

    def test_layer_out_of_range_detected(self):
        body = _BASE.replace("layer: P10", "layer: P99")
        issues, _ = self._scan(body)
        self.assertTrue(any("层位越界" in i for i in issues), issues)

    def test_issue_is_prefixed_with_asset_path(self):
        body = _BASE.replace("prereqs: []", "prereqs: [C02]")
        issues, _ = self._scan(body)
        self.assertTrue(any(i.startswith("community/") for i in issues), issues)


if __name__ == "__main__":
    unittest.main()
