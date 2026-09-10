#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""world_model 契约扫描器单测。"""
import os
import sys
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop", "src"))

from core import world_model as wm  # noqa: E402


def _base_world_model():
    return {
        "abstract_state": {
            "variables": [
                {"name": "phase", "kind": "string", "source": "M50"},
                {"name": "tick", "kind": "integer", "source": "M10"},
                {"name": "chain", "kind": "array", "item_kind": "string", "source": "M50"},
            ],
            "initial": {"phase": "begin", "tick": 0, "chain": []},
        },
        "transition": {
            "initial_phase": "begin",
            "phases": [
                {"phase": "begin", "next": "run", "guard": "start", "writes": []},
                {"phase": "run", "next": "begin", "guard": "loop", "writes": ["x"]},
            ],
        },
        "invariants": ["phase 有限"],
    }


class WorldModelTest(unittest.TestCase):
    def test_repo_scan_clean_and_first_case(self):
        issues, stats = wm.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats["modules"], 1)
        self.assertGreaterEqual(stats["variables"], 1)
        self.assertGreaterEqual(stats["phases"], 1)
        self.assertGreaterEqual(stats["invariants"], 1)

    def test_valid_minimal_contract(self):
        self.assertEqual(wm.validate_contract(_base_world_model()), [])

    def test_missing_invariant_fails(self):
        data = _base_world_model()
        data["invariants"] = []
        self.assertTrue(any("invariants" in i for i in wm.validate_contract(data)))

    def test_unreachable_phase_fails(self):
        data = _base_world_model()
        data["transition"]["phases"] = [
            {"phase": "begin", "next": "run", "guard": "start", "writes": []},
            {"phase": "run", "next": "begin", "guard": "loop", "writes": []},
            {"phase": "orphan", "next": "run", "guard": "unused", "writes": []},
        ]
        self.assertTrue(any("不可达" in i for i in wm.validate_contract(data)))

    def test_initial_missing_variable_fails(self):
        data = _base_world_model()
        del data["abstract_state"]["initial"]["tick"]
        self.assertTrue(any("缺变量 'tick'" in i for i in wm.validate_contract(data)))

    def test_array_item_kind_mismatch_fails(self):
        data = _base_world_model()
        data["abstract_state"]["initial"]["chain"] = [1]
        self.assertTrue(any("不匹配 kind='array'" in i for i in wm.validate_contract(data)))

    def test_duplicate_phase_fails(self):
        data = _base_world_model()
        data["transition"]["phases"].append(
            {"phase": "run", "next": "begin", "guard": "dup", "writes": []}
        )
        self.assertTrue(any("相位重名" in i for i in wm.validate_contract(data)))

    def test_phase_sequence_and_advance(self):
        data = _base_world_model()
        state = wm.initial_state(data)
        self.assertEqual(state["phase"], "begin")
        state = wm.advance_phase(data, state)
        self.assertEqual(state["phase"], "run")
        sequence, reason, repeat = wm.phase_sequence(data)
        self.assertEqual(sequence, ["begin", "run"])
        self.assertEqual(reason, "cycle")
        self.assertEqual(repeat, "begin")

    def test_m50_reference_cycle(self):
        issues, stats = wm.scan(ROOT)
        self.assertEqual(issues, [])
        self.assertGreaterEqual(stats.get("checks", 0), 1)
        self.assertGreaterEqual(stats.get("slots", 0), 1)
        m50 = next(m for m in stats["models"] if m["module"] == "M50")
        text = (Path(ROOT) / m50["source"]).read_text(encoding="utf-8")
        from core import conformance_scan as csc

        parsed = csc._fence_yaml(text, "machine_contract")
        contract = parsed["machine_contract"]["world_model"]
        sequence, reason, repeat = wm.phase_sequence(contract)
        self.assertEqual(sequence, ["begin", "run", "end", "archive", "roll"])
        self.assertEqual(reason, "cycle")
        self.assertEqual(repeat, "begin")

    def test_m50_runtime_replay(self):
        issues, stats = wm.scan(ROOT)
        self.assertEqual(issues, [])
        m50 = next(m for m in stats["models"] if m["module"] == "M50")
        text = (Path(ROOT) / m50["source"]).read_text(encoding="utf-8")
        from core import conformance_scan as csc

        contract = csc._fence_yaml(text, "machine_contract")["machine_contract"]["world_model"]
        runtime = wm.WorldModelRuntime(contract)
        result = runtime.replay()
        self.assertEqual(result["reason"], "cycle")
        self.assertEqual(result["repeat"], "begin")
        self.assertEqual(len(result["steps"]), 5)
        self.assertEqual(len(result.get("digest", "")), 64)
        self.assertEqual(result["digest"], runtime.replay()["digest"])
        self.assertEqual(
            [s["phase_from"] for s in result["steps"]],
            ["begin", "run", "end", "archive", "roll"],
        )
        self.assertEqual(
            result["final_state"]["phase_trace"],
            ["begin", "run", "end", "archive", "roll"],
        )

    def test_runtime_monotonic_violation(self):
        data = _base_world_model()
        data["checks"] = [{"kind": "monotonic", "field": "tick"}]
        runtime = wm.WorldModelRuntime(data)
        state = wm.initial_state(data)
        previous = dict(state)
        previous["tick"] = 2
        state["tick"] = 1
        with self.assertRaises(wm.WorldModelViolation):
            runtime.advance(state, previous)

    def test_invalid_check_field_fails(self):
        data = _base_world_model()
        data["checks"] = [{"kind": "finite_phase", "field": "not_declared", "values": ["x"]}]
        self.assertTrue(any("未声明变量" in i for i in wm.validate_contract(data)))

    def test_slot_registry_unknown_slot_fails(self):
        data = _base_world_model()
        data["abstract_state"]["variables"][0]["slot"] = "data_bus.round.unknown"
        slots = {"data_bus.round.phase": {"kind": "string", "owner": "M50"}}
        self.assertTrue(any("未在 protocol/world_slots.json 注册" in i
                            for i in wm.validate_contract(data, "world_model", slots)))

    def test_slot_registry_owner_drift_fails(self):
        data = _base_world_model()
        data["abstract_state"]["variables"][0]["slot"] = "data_bus.round.phase"
        slots = {"data_bus.round.phase": {"kind": "string", "owner": "M99"}}
        self.assertTrue(any("owner 漂移" in i
                            for i in wm.validate_contract(data, "world_model", slots)))

    def test_slot_registry_type_drift_fails(self):
        data = _base_world_model()
        data["abstract_state"]["variables"][0]["slot"] = "data_bus.round.phase"
        slots = {"data_bus.round.phase": {"kind": "integer", "owner": "M50"}}
        self.assertTrue(any("类型漂移" in i
                            for i in wm.validate_contract(data, "world_model", slots)))

    def test_finite_sequence_invalid_field_fails(self):
        data = _base_world_model()
        data["checks"] = [{"kind": "finite_sequence", "field": "phase", "values": ["begin"]}]
        self.assertTrue(any("只能用于 array" in i for i in wm.validate_contract(data)))

    def test_runtime_finite_sequence_violation(self):
        data = _base_world_model()
        data["abstract_state"]["variables"].append(
            {"name": "phase_trace", "kind": "array", "item_kind": "string", "source": "M50"}
        )
        data["abstract_state"]["initial"]["phase_trace"] = []
        data["checks"] = [
            {"kind": "finite_sequence", "field": "phase_trace", "values": ["begin", "run"]}
        ]
        runtime = wm.WorldModelRuntime(data)
        state = wm.initial_state(data)
        state["phase_trace"] = ["begin", "bad"]
        with self.assertRaises(wm.WorldModelViolation):
            runtime.advance(state)

    def _m50_runtime_and_concrete(self):
        issues, stats = wm.scan(ROOT)
        self.assertEqual(issues, [])
        m50 = next(m for m in stats["models"] if m["module"] == "M50")
        text = (Path(ROOT) / m50["source"]).read_text(encoding="utf-8")
        from core import conformance_scan as csc

        contract = csc._fence_yaml(text, "machine_contract")["machine_contract"]["world_model"]
        runtime = wm.WorldModelRuntime(contract)
        concrete = {
            "data_bus": {
                "active_pipeline": "P01",
                "round": {"phase": "begin", "phase_trace": []},
            },
            "WorldState": {"time": {"tick": 0}},
        }
        return runtime, concrete

    def test_extract_concrete_state(self):
        runtime, concrete = self._m50_runtime_and_concrete()
        state, issues = runtime.extract_state(concrete)
        self.assertEqual(issues, [])
        self.assertEqual(state["phase"], "begin")
        self.assertEqual(state["tick"], 0)
        self.assertEqual(state["phase_trace"], [])

    def test_advance_concrete_state(self):
        runtime, concrete = self._m50_runtime_and_concrete()
        next_concrete, trace = runtime.advance_concrete(concrete)
        self.assertEqual(next_concrete["data_bus"]["round"]["phase"], "run")
        self.assertEqual(next_concrete["data_bus"]["round"]["phase_trace"], ["begin"])
        self.assertEqual(trace["phase_from"], "begin")
        self.assertEqual(trace["phase_to"], "run")

    def test_replay_concrete_state(self):
        runtime, concrete = self._m50_runtime_and_concrete()
        result = runtime.replay_concrete(concrete)
        self.assertEqual(result["reason"], "cycle")
        self.assertEqual(len(result["steps"]), 5)
        self.assertEqual(result["final_state"]["data_bus"]["round"]["phase_trace"],
                         ["begin", "run", "end", "archive", "roll"])


if __name__ == "__main__":
    unittest.main()
