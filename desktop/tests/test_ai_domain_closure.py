# -*- coding: utf-8 -*-
"""AI 系统域 · 概念前置闭包求值单测（域包战例回归 + 负例注入）。

被测件：`scripts/ai_domain_closure.py`（只读求值器）+ 域包资产
`community/AI系统域包/assets/CONCEPT_GRAPH.md`（概念前置偏序图）。

覆盖：图健康度 / 闭包与缺失清单数值 / 装载序合法性 / 确定性两遍一致 /
序校验（一条合法线性化 0 违反、一份目录序存在违反）/ 负例（环 / 悬空 / 缺溯源 /
逆序 / 越界目标 / 缺资产 / 无机读块）。
"""
import contextlib
import copy
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSET = ROOT / "community" / "AI系统域包" / "assets" / "CONCEPT_GRAPH.md"
_spec = importlib.util.spec_from_file_location(
    "nf_ai_domain_closure", ROOT / "scripts" / "ai_domain_closure.py")
adc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adc)


def _mutate(graph, node_id, extra_prereq):
    """注入一条额外前置边（负例构造，只改内存副本，不动仓库资产）。"""
    clone = copy.deepcopy(graph)
    for node in clone["nodes"]:
        if node["id"] == node_id:
            node["prereqs"] = list(node["prereqs"]) + [extra_prereq]
    return clone


class GraphTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = adc.load_graph(ASSET)

    def test_graph_health_zero_problem(self):
        """正例：资产图无环 / 无悬空 / 节点均有溯源与合法层位。"""
        self.assertEqual(adc.problems(self.graph), [])

    def test_node_and_external_counts(self):
        self.assertEqual(len(adc.in_package_ids(self.graph)), 47)
        self.assertEqual(len(self.graph.get("external_prereqs") or []), 1)

    def test_branches_cover_every_concept_once(self):
        """双支覆盖：每个包内概念恰属一个分支，分支成员合计 == 概念数。"""
        branches = adc.branch_map(self.graph)
        self.assertEqual(sorted(branches), ["app", "compute"])
        self.assertEqual(sum(len(v) for v in branches.values()),
                         len(adc.in_package_ids(self.graph)))
        self.assertEqual(len(adc.node_branch(self.graph)),
                         len(adc.in_package_ids(self.graph)))

    def test_closure_of_c22(self):
        """closure(C22)：含目标自身与包外前置族 C00，共 13 个概念。"""
        clo = adc.closure(self.graph, "C22")
        self.assertEqual(len(clo), 13)
        self.assertEqual(clo, sorted(clo), "闭包输出须排序（确定性）")
        self.assertIn("C22", clo)
        self.assertIn("C00", clo)
        self.assertNotIn("C02", clo)

    def test_missing_against_loaded_set(self):
        """missing(C22, L)：L 已含 5 个概念 → 缺 8 个。"""
        missing = adc.missing(self.graph, "C22",
                              ["C01", "C07", "C08", "C10", "C18"])
        self.assertEqual(len(missing), 8)
        self.assertIn("C09", missing)
        self.assertIn("C22", missing)
        self.assertNotIn("C01", missing)
        full = adc.closure(self.graph, "C22")
        self.assertEqual(adc.missing(self.graph, "C22", full), [])

    def test_load_order_is_valid_linearization(self):
        order = adc.toposort(self.graph)
        self.assertEqual(len(order), 47)
        self.assertEqual(adc.violations(self.graph, order), [])

    def test_determinism_two_runs_identical(self):
        """确定性：同一图两遍求值逐字节一致（NF 同输入同输出纪律）。"""
        again = adc.load_graph(ASSET)
        self.assertEqual(adc.closure(self.graph, "C22"), adc.closure(again, "C22"))
        self.assertEqual(adc.toposort(self.graph), adc.toposort(again))


class OrderingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = adc.load_graph(ASSET)

    def _seq(self, oid):
        return [o["seq"] for o in self.graph["orderings"] if o["id"] == oid][0]

    def test_declared_course_order_has_no_violation(self):
        """讲序是本图的一个合法线性化（对诱导子图零违反）= 边集与独立来源相容。"""
        self.assertEqual(adc.violations(self.graph, self._seq("cmu-mlsys")), [])

    def test_declared_directory_order_does_violate(self):
        """目录序不是前置序：存在违反边（禁当前置序使用）。"""
        bad = adc.violations(self.graph, self._seq("aisystem-module-order"))
        self.assertGreater(len(bad), 0)
        self.assertIn(("C09", "C12"), bad)

    def test_declared_guide_order_violation_is_the_eval_reliability_edge(self):
        """指南章节序：教学序把可靠性排在评测之前，唯一违反边 = C40 → C41。"""
        bad = adc.violations(self.graph, self._seq("design-guide-chapter-order"))
        self.assertEqual(bad, [("C40", "C41")])


class AliasTest(unittest.TestCase):
    """检索词面：条目键 / 别名 / 概念名同解；别名歧义即拒。"""

    @classmethod
    def setUpClass(cls):
        cls.graph = adc.load_graph(ASSET)

    def test_alias_resolves_to_entry_key(self):
        self.assertEqual(adc.resolve(self.graph, "RAG"), "C28")
        self.assertEqual(adc.resolve(self.graph, "PagedAttention"), "C22")
        self.assertEqual(adc.resolve(self.graph, "MCP"), "C33")

    def test_alias_is_case_and_whitespace_insensitive(self):
        self.assertEqual(adc.resolve(self.graph, "  autodiff  "), "C08")
        self.assertEqual(adc.resolve(self.graph, "rerank"), "C30")

    def test_concept_name_resolves(self):
        name = adc.node_meta(self.graph)["C45"]["name"]
        self.assertEqual(adc.resolve(self.graph, name), "C45")

    def test_alias_closure_equals_key_closure(self):
        self.assertEqual(adc.closure(self.graph, "RAG"), adc.closure(self.graph, "C28"))

    def test_unknown_token_rejected(self):
        with self.assertRaises(adc.ClosureError):
            adc.resolve(self.graph, "NOT_A_CONCEPT")


class FrontierTest(unittest.TestCase):
    """就绪清单 frontier(L) = 前置已齐且未装载者。"""

    @classmethod
    def setUpClass(cls):
        cls.graph = adc.load_graph(ASSET)

    def test_frontier_requires_all_prereqs(self):
        front = adc.frontier(self.graph, ["C00", "C01"])
        # C02 ← C01；C07 ← C01；C11 ← C00——三者前置皆齐，其余概念仍有缺口
        self.assertEqual(front, ["C02", "C07", "C11"])

    def test_frontier_branch_filter(self):
        loaded = ["C00", "C01", "C20", "C25"]
        self.assertEqual(adc.frontier(self.graph, loaded, branch="app"),
                         ["C26", "C27"])
        self.assertIn("C02", adc.frontier(self.graph, loaded))
        self.assertNotIn("C02", adc.frontier(self.graph, loaded, branch="app"))

    def test_frontier_excludes_loaded_and_is_deterministic(self):
        loaded = ["C00", "C01", "C02"]
        self.assertNotIn("C02", adc.frontier(self.graph, loaded))
        self.assertEqual(adc.frontier(self.graph, loaded),
                         adc.frontier(self.graph, list(loaded)))

    def test_app_branch_blocked_before_foundations(self):
        """应用栈概念在计算栈前置未齐时不得进入就绪清单。"""
        self.assertEqual(adc.frontier(self.graph, [], branch="app"), [])


class NegativeCaseTest(unittest.TestCase):
    """负例注入：图非法 / 输入非法时必须报错，不得静默给答案。"""

    @classmethod
    def setUpClass(cls):
        cls.graph = adc.load_graph(ASSET)

    def test_injected_cycle_is_detected(self):
        cyc = _mutate(self.graph, "C09", "C12")
        self.assertTrue(any("环" in i for i in adc.problems(cyc)), adc.problems(cyc))
        with self.assertRaises(adc.ClosureError):
            adc.toposort(cyc)

    def test_injected_dangling_prereq_is_detected(self):
        dang = _mutate(self.graph, "C22", "C99")
        self.assertTrue(any("悬空" in i for i in adc.problems(dang)), adc.problems(dang))

    def test_injected_missing_provenance_is_detected(self):
        clone = copy.deepcopy(self.graph)
        for node in clone["nodes"]:
            if node["id"] == "C10":
                node.pop("provenance", None)
        self.assertTrue(any("溯源" in i for i in adc.problems(clone)), adc.problems(clone))

    def test_injected_duplicate_alias_is_detected(self):
        clone = copy.deepcopy(self.graph)
        for node in clone["nodes"]:
            if node["id"] == "C29":
                node["aliases"] = list(node.get("aliases") or []) + ["RAG"]
        self.assertTrue(any("别名重复" in i for i in adc.problems(clone)),
                        adc.problems(clone))

    def test_concept_outside_branches_is_detected(self):
        clone = copy.deepcopy(self.graph)
        for br in clone["branches"]:
            br["nodes"] = [n for n in br["nodes"] if n != "C45"]
        self.assertTrue(any("未归入任何分支" in i for i in adc.problems(clone)),
                        adc.problems(clone))

    def test_unknown_branch_is_usage_error(self):
        """未知分支 = 用法错误（退出码 2），不得静默按全图求值。"""
        with contextlib.redirect_stderr(io.StringIO()):
            code = adc.main(["--asset", str(ASSET), "--ready-list",
                             "--branch", "no_such_branch"])
        self.assertEqual(code, 2)

    def test_unknown_order_id_is_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()):
            code = adc.main(["--asset", str(ASSET), "--order", "no_such_order"])
        self.assertEqual(code, 2)

    def test_reversed_order_has_violations(self):
        bad = adc.violations(self.graph, list(reversed(adc.toposort(self.graph))))
        self.assertGreater(len(bad), 0)

    def test_unknown_target_rejected(self):
        with self.assertRaises(adc.ClosureError):
            adc.closure(self.graph, "C99")

    def test_missing_asset_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(adc.ClosureError):
                adc.load_graph(Path(tmp) / "NO_SUCH_ASSET.md")

    def test_asset_without_machine_block_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            plain = Path(tmp) / "PLAIN.md"
            plain.write_text("# 只有人读文字\n\n没有机读块。\n", encoding="utf-8")
            with self.assertRaises(adc.ClosureError):
                adc.load_graph(plain)

    def test_self_check_passes_on_real_asset(self):
        fails, passes = adc.self_check(ASSET)
        self.assertEqual(fails, [])
        self.assertEqual(len(passes), 15)


if __name__ == "__main__":
    unittest.main()
