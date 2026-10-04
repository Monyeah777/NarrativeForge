#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智能体工具编排（`core/orchestration.py`）回归：目录派生 / 计划编译 / 确定性序 / fail-closed 派发。

正例（真仓零问题、合法计划编译通过）+ 变异自证（编排错误九类必判红）+ 派发停点与证据。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import mcp_runtime as mrt  # noqa: E402
from core import orchestration as orch  # noqa: E402

#: 运行时工具面（{name: tool_def}）——按 orchestration 的叶子纪律**由调用方注入**，模块自己不 import。
TOOLS = {t["name"]: t for t in mrt.TOOL_DEFS}


def _plan(steps, workflow="menu", schema=orch.SCHEMA):
    return {"schema": schema, "workflow": workflow, "steps": steps}


def _issues(plan, root=str(ROOT), tools=TOOLS):
    return orch.compile_plan(root, plan, tools)["issues"]


def _required_args(tool):
    spec = [t for t in mrt.TOOL_DEFS if t["name"] == tool][0]["inputSchema"]
    out = {}
    for key in spec.get("required") or []:
        ptype = (spec.get("properties") or {}).get(key, {}).get("type")
        out[key] = {"integer": 1, "boolean": True, "array": [], "object": {}}.get(ptype, "x")
    return out


#: 计划自述（orch.PLAN_GUIDE）的每个字段 → 一条**必须判红**的用例。
#: 自述是给 agent 的第一跳文档：写了什么就得真的判什么（内外口径统一）。
PLAN_GUIDE_CASES = {
    "schema": _plan([{"id": "s1", "tool": "library_search", "args": {"query": "x"}}],
                    schema="bogus/1"),
    "workflow": _plan([{"id": "s1", "tool": "library_search", "args": {"query": "x"}}],
                      workflow="nope"),
    "steps": _plan([]),
    "id": _plan([{"id": "S1", "tool": "library_search", "args": {"query": "x"}}]),
    "tool": _plan([{"id": "s1", "tool": "module_read", "args": {"module_id": "M90"}}],
                  workflow="menu"),
    "args": _plan([{"id": "s1", "tool": "library_search", "args": {}}]),
    "needs": _plan([{"id": "s1", "tool": "library_search", "args": {"query": "x"},
                     "needs": ["ghost"]}]),
    "expects": _plan([{"id": "s1", "tool": "library_search", "args": {"query": "x"},
                       "expects": [""]}]),
}


class PlanGuideConsistencyTest(unittest.TestCase):
    """自述 ⇄ 实现两侧集合**恰好相等**：自述里承诺的字段，必须真的各有判据。"""

    def test_guide_and_cases_are_the_same_set(self):
        self.assertEqual(sorted(orch.PLAN_GUIDE), sorted(PLAN_GUIDE_CASES),
                         "自述字段与用例集合必须恰好相等（加字段要带用例，删字段要删用例）")

    def test_every_documented_field_is_actually_enforced(self):
        blind = [k for k, plan in sorted(PLAN_GUIDE_CASES.items()) if not _issues(plan)]
        self.assertEqual([], blind,
                         "自述里承诺了却没人判的字段（文档在说自己做不到的事）：%s" % blind)


class CatalogTest(unittest.TestCase):
    def test_catalog_derives_from_live_sources(self):
        cat = orch.catalog(str(ROOT), TOOLS)
        self.assertEqual({t["name"] for t in mrt.TOOL_DEFS}, set(cat["tools"]))
        self.assertEqual(set(orch.workflow_tools(str(ROOT))), set(cat["workflows"]))
        self.assertIn("query", cat["tools"]["library_search"]["required"])
        self.assertFalse(cat["tools"]["library_search"]["additional_properties"])
        self.assertEqual(orch.SCHEMA, cat["plan"]["schema"])
        self.assertIn("expects", cat["plan"], "计划格式自述须随目录交回（agent 第一跳）")

    def test_scan_real_repo_is_clean(self):
        issues, stats = orch.scan(str(ROOT), TOOLS)
        self.assertEqual([], issues)
        self.assertGreaterEqual(stats["workflows"], 3)
        self.assertGreaterEqual(stats["tools"], 10)

    def test_scan_flags_uncompilable_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "protocol"
            pdir.mkdir()
            (pdir / "driver.json").write_text(
                json.dumps({"workflows": {"w": {"mcp_tools": ["nope"]}}}), encoding="utf-8")
            issues, stats = orch.scan(tmp, TOOLS)
        self.assertTrue(any("不可编排" in i for i in issues), issues)
        self.assertEqual(1, stats["mapped"])

    def test_scan_empty_root_reports_but_does_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, stats = orch.scan(tmp, TOOLS)
        self.assertTrue(any(orch.DRIVER_REL in i for i in issues), issues)
        self.assertEqual(0, stats["workflows"])


class CompilePositiveTest(unittest.TestCase):
    def test_valid_plan_compiles_with_deterministic_order(self):
        plan = _plan([
            {"id": "search", "tool": "library_search", "args": {"query": "世界"}},
            {"id": "read", "tool": "library_read",
             "args": {"entry_id": "$search.entry_id"}, "needs": ["search"]},
        ])
        res = orch.compile_plan(str(ROOT), plan, TOOLS)
        self.assertEqual([], res["issues"])
        self.assertTrue(res["ok"])
        self.assertEqual(["search", "read"], res["order"])
        self.assertEqual(res["order"], orch.compile_plan(str(ROOT), plan, TOOLS)["order"],
                         "同计划两次编译顺序必须逐位相同")

    def test_declaration_order_breaks_ties(self):
        plan = _plan([
            {"id": "b", "tool": "library_search", "args": {"query": "x"}},
            {"id": "a", "tool": "library_search", "args": {"query": "y"}},
        ])
        self.assertEqual(["b", "a"], orch.compile_plan(str(ROOT), plan, TOOLS)["order"])

    def test_every_mapped_tool_compiles_in_its_workflow(self):
        for name, tools in sorted(orch.workflow_tools(str(ROOT)).items()):
            for tool in tools:
                issues = _issues(_plan([{"id": "s1", "tool": tool,
                                         "args": _required_args(tool)}], workflow=name))
                self.assertEqual([], issues, "%s / %s 应能编译：%s" % (name, tool, issues))


class CompileMutationTest(unittest.TestCase):
    def test_wrong_schema_flagged(self):
        plan = _plan([{"id": "s1", "tool": "library_search", "args": {"query": "x"}}],
                     schema="bogus/1")
        self.assertTrue(any("schema" in i for i in _issues(plan)), _issues(plan))

    def test_unknown_workflow_flagged(self):
        plan = _plan([{"id": "s1", "tool": "library_search", "args": {"query": "x"}}],
                     workflow="nope")
        self.assertTrue(any("未在" in i for i in _issues(plan)), _issues(plan))

    def test_tool_outside_workflow_mapping_flagged(self):
        plan = _plan([{"id": "s1", "tool": "module_read", "args": {"module_id": "M90"}}],
                     workflow="menu")
        self.assertTrue(any("映射集" in i for i in _issues(plan)), _issues(plan))

    def test_tool_not_in_runtime_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdir = Path(tmp) / "protocol"
            pdir.mkdir()
            (pdir / "driver.json").write_text(
                json.dumps({"workflows": {"w": {"mcp_tools": ["nope"]}}}), encoding="utf-8")
            issues = _issues(_plan([{"id": "s1", "tool": "nope", "args": {}}], workflow="w"),
                             root=tmp)
        self.assertTrue(any("运行时工具面" in i for i in issues), issues)

    def test_missing_required_arg_flagged(self):
        issues = _issues(_plan([{"id": "s1", "tool": "library_search", "args": {}}]))
        self.assertTrue(any("必填" in i for i in issues), issues)

    def test_wrong_arg_type_flagged(self):
        issues = _issues(_plan([{"id": "s1", "tool": "library_search", "args": {"query": 5}}]))
        self.assertTrue(any("类型" in i for i in issues), issues)

    def test_undeclared_arg_flagged(self):
        issues = _issues(_plan([{"id": "s1", "tool": "library_search",
                                 "args": {"query": "x", "bogus": 1}}]))
        self.assertTrue(any("未声明参数" in i for i in issues), issues)

    def test_unknown_need_flagged(self):
        issues = _issues(_plan([{"id": "s1", "tool": "library_search",
                                 "args": {"query": "x"}, "needs": ["ghost"]}]))
        self.assertTrue(any("不存在的步" in i for i in issues), issues)

    # ---- 以下七例由**覆盖率**补出（2026-10-03）：原判据自称「九类必判红」，实测这七条错误分支
    #      一条都没被走到——即「变异自证」的口径比它覆盖的分支宽。补法：逐条喂最小非法计划。
    def test_step_without_tool_flagged(self):
        issues = _issues(_plan([{"id": "s1", "args": {"query": "x"}}]))
        self.assertTrue(any("缺 tool" in i for i in issues), issues)

    def test_non_object_step_flagged(self):
        issues = _issues(_plan(["not-an-object"]))
        self.assertTrue(any("不是对象" in i for i in issues), issues)

    def test_args_must_be_object_flagged(self):
        issues = _issues(_plan([{"id": "s1", "tool": "library_search", "args": "x"}]))
        self.assertTrue(any("args 须为对象" in i for i in issues), issues)

    def test_needs_must_be_list_flagged(self):
        issues = _issues(_plan([{"id": "s1", "tool": "library_search",
                                 "args": {"query": "x"}, "needs": "ghost"}]))
        self.assertTrue(any("needs 须为列表" in i for i in issues), issues)

    def test_self_dependency_flagged(self):
        issues = _issues(_plan([{"id": "s1", "tool": "library_search",
                                 "args": {"query": "x"}, "needs": ["s1"]}]))
        self.assertTrue(any("依赖自己" in i for i in issues), issues)

    def test_missing_workflow_flagged(self):
        plan = {"schema": orch.SCHEMA,
                "steps": [{"id": "s1", "tool": "library_search", "args": {"query": "x"}}]}
        self.assertTrue(any("缺 workflow" in i for i in _issues(plan)), _issues(plan))

    def test_ref_to_nonexistent_step_flagged(self):
        issues = _issues(_plan([{"id": "s1", "tool": "library_search",
                                 "args": {"query": "$ghost.title"}}]))
        self.assertTrue(any("指向不存在的步" in i for i in issues), issues)

    def test_cycle_flagged_and_order_incomplete(self):
        plan = _plan([
            {"id": "a", "tool": "library_search", "args": {"query": "x"}, "needs": ["b"]},
            {"id": "b", "tool": "library_search", "args": {"query": "y"}, "needs": ["a"]},
        ])
        res = orch.compile_plan(str(ROOT), plan, TOOLS)
        self.assertTrue(any("成环" in i for i in res["issues"]), res["issues"])
        self.assertEqual([], res["order"], "成环时不得给出一个假装可用的顺序")

    def test_implicit_ref_dependency_flagged(self):
        plan = _plan([
            {"id": "search", "tool": "library_search", "args": {"query": "x"}},
            {"id": "read", "tool": "library_read",
             "args": {"entry_id": "$search.entry_id"}},
        ])
        self.assertTrue(any("隐式依赖" in i for i in _issues(plan)), _issues(plan))

    def test_malformed_ref_is_flagged_not_silently_ignored(self):
        plan = _plan([
            {"id": "search", "tool": "library_search", "args": {"query": "x"}},
            {"id": "read", "tool": "library_read",
             "args": {"entry_id": "$Search.entry_id"}, "needs": ["search"]},
        ])
        self.assertTrue(any("引用写法非法" in i for i in _issues(plan)), _issues(plan))

    def test_bare_dollar_is_flagged(self):
        issues = _issues(_plan([{"id": "s1", "tool": "library_search",
                                 "args": {"query": "$"}}]))
        self.assertTrue(any("引用写法非法" in i for i in issues), issues)

    def test_duplicate_step_id_flagged(self):
        plan = _plan([
            {"id": "s1", "tool": "library_search", "args": {"query": "x"}},
            {"id": "s1", "tool": "library_search", "args": {"query": "y"}},
        ])
        self.assertTrue(any("重复" in i for i in _issues(plan)), _issues(plan))

    def test_expects_must_be_non_empty_strings(self):
        issues = _issues(_plan([{"id": "s1", "tool": "library_search",
                                 "args": {"query": "x"}, "expects": [""]}]))
        self.assertTrue(any("expects" in i for i in issues), issues)

    def test_empty_plan_flagged(self):
        self.assertTrue(any("空" in i for i in orch.compile_plan(str(ROOT), {}, TOOLS)["issues"]))


class TypeIssueTest(unittest.TestCase):
    """`_type_issue` 的 integer / number 分支：**真实工具面没有这两个类型**，只能直接单测私有函数——
    否则那两行是活代码里的死角（覆盖率正是这样把它暴露出来的，2026-10-03）。"""

    def test_integer_and_number_accept_and_reject(self):
        self.assertEqual("", orch._type_issue(3, {"type": "integer"}))
        self.assertEqual("integer", orch._type_issue(True, {"type": "integer"}), "bool 不得当整数")
        self.assertEqual("integer", orch._type_issue("3", {"type": "integer"}))
        self.assertEqual("", orch._type_issue(3, {"type": "number"}))
        self.assertEqual("", orch._type_issue(3.5, {"type": "number"}))
        self.assertEqual("number", orch._type_issue(True, {"type": "number"}), "bool 不得当数值")
        self.assertEqual("", orch._type_issue("x", {"type": "bogus"}), "未知类型不判（宁少勿滥）")


class DispatchTest(unittest.TestCase):
    def _compiled(self):
        plan = _plan([
            {"id": "search", "tool": "library_search", "args": {"query": "x"}},
            {"id": "read", "tool": "library_read",
             "args": {"entry_id": "$search.entry_id"}, "needs": ["search"]},
            {"id": "again", "tool": "library_search", "args": {"query": "z"}},
        ])
        return orch.compile_plan(str(ROOT), plan, TOOLS)

    def test_stops_at_first_failure(self):
        res = self._compiled()
        calls = []

        def call(tool, args):
            calls.append(tool)
            if tool == "library_read":
                raise RuntimeError("boom")
            return {"ok": True}

        out = orch.dispatch(res["order"], res["steps"], call)
        self.assertEqual(["search", "read"], out["executed"])
        self.assertEqual("read", out["stopped_at"])
        self.assertEqual(["again"], out["not_executed"], "失败后不得继续派发")
        self.assertEqual(2, len(calls), "首个失败即停——后续步不得被调用")

    def _plan_with_expects(self):
        return _plan([
            {"id": "search", "tool": "library_search", "args": {"query": "x"},
             "expects": ["entry_id"]},
            {"id": "read", "tool": "library_read",
             "args": {"entry_id": "$search.entry_id"}, "needs": ["search"]},
        ])

    def test_expects_satisfied_is_ok(self):
        res = orch.compile_plan(str(ROOT), self._plan_with_expects(), TOOLS)
        out = orch.dispatch(res["order"], res["steps"],
                            lambda tool, args: {"entry_id": "NF-1"})
        self.assertIsNone(out["stopped_at"])
        self.assertEqual(["search", "read"], out["executed"])

    def test_missing_evidence_stops_fail_closed(self):
        res = orch.compile_plan(str(ROOT), self._plan_with_expects(), TOOLS)
        out = orch.dispatch(res["order"], res["steps"], lambda tool, args: {})
        self.assertEqual("search", out["stopped_at"])
        self.assertIn("缺证据", out["results"][-1]["detail"])
        self.assertEqual(["read"], out["not_executed"])

    def test_non_object_result_fails_expects(self):
        res = orch.compile_plan(str(ROOT), self._plan_with_expects(), TOOLS)
        out = orch.dispatch(res["order"], res["steps"], lambda tool, args: "ok")
        self.assertEqual("search", out["stopped_at"],
                         "非对象返回值不得当作证据齐全")

    def test_success_records_per_step_evidence(self):
        res = self._compiled()
        out = orch.dispatch(res["order"], res["steps"], lambda tool, args: {"tool": tool})
        self.assertIsNone(out["stopped_at"])
        self.assertEqual([], out["not_executed"])
        self.assertEqual(3, len(out["results"]))
        self.assertTrue(all(r["ok"] for r in out["results"]))
        self.assertEqual("library_search", out["results"][0]["detail"]["tool"])


class RealToolFaceDispatchTest(unittest.TestCase):
    """端到端：**真工具面**（`core.mcp_runtime.TOOL_DEFS` + `TOOL_HANDLERS`）→ 编译 → 派发 → 证据验收。

    为什么补这条：其余派发用例喂的都是合成 stub——那只能证明「编排代数对」，证明不了「接上真工具面
    能跑」。这里用 `routing` 工作流（`spec_ls` → `registry_query`，两者皆只读）跑一遍**真调用**，
    并另起一例证明「真工具成功但 `expects` 不满足」时同样即停。
    """

    @staticmethod
    def _caller(name, args):
        return mrt.TOOL_HANDLERS[name](args)

    def test_routing_plan_runs_against_real_tool_face(self):
        plan = _plan([{"id": "specs", "tool": "spec_ls", "args": {}},
                      {"id": "query", "tool": "registry_query", "args": {"query": "layers"},
                       "needs": ["specs"], "expects": ["modules", "protocols"]}],
                     workflow="routing")
        compiled = orch.compile_plan(str(ROOT), plan, TOOLS)
        self.assertEqual([], compiled["issues"])
        out = orch.dispatch(compiled["order"], compiled["steps"], self._caller)
        self.assertIsNone(out["stopped_at"], out)
        self.assertEqual([], out["not_executed"])
        self.assertTrue(all(r["ok"] for r in out["results"]), out)
        # 真产物（不是 stub）：registry_query 的对象里确有这两个字段
        detail = [r["detail"] for r in out["results"] if r["id"] == "query"][0]
        self.assertIn("modules", detail)
        self.assertIn("protocols", detail)

    def test_real_tool_success_but_missing_evidence_still_stops(self):
        """真工具成功 ≠ 证据齐：`expects` 不满足时同样即停（fail-closed 不因工具成功而放松）。"""
        plan = _plan([{"id": "ls", "tool": "library_search", "args": {"query": "x"},
                       "expects": ["not_a_field"]}], workflow="menu")
        compiled = orch.compile_plan(str(ROOT), plan, TOOLS)
        self.assertEqual([], compiled["issues"])
        out = orch.dispatch(compiled["order"], compiled["steps"], self._caller)
        self.assertEqual("ls", out["stopped_at"])
        self.assertFalse(out["results"][0]["ok"])
        self.assertIn("缺证据", out["results"][0]["detail"])


if __name__ == "__main__":
    unittest.main()
