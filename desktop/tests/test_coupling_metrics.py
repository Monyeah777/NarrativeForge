#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模块级耦合度量（`core/coupling_metrics.py`）回归测试 —— Martin 包度量 / SDP / 环。

关键断言：新增环或新增 SDP 违例判 FAIL、登记债放行、债务消除记 WARN、
SDP 方向敏感（A→B 与 B→A 不是一回事）、真仓零新增。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import coupling_metrics as cm  # noqa: E402


def _mod(tmp: str, name: str, imports=()) -> None:
    p = Path(tmp) / cm.SCAN_DIR / (name + ".py")
    p.parent.mkdir(parents=True, exist_ok=True)
    body = "".join("from core import %s  # noqa: F401\n" % i for i in imports)
    p.write_text(body + "\ndef f():\n    return 1\n", encoding="utf-8")


class GraphTest(unittest.TestCase):
    def test_cycle_detected_and_metrics_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mod(tmp, "a", ["b"])
            _mod(tmp, "b", ["a"])
            deps, metrics = cm.graph(tmp)
        cyc = cm.cycles(deps)
        self.assertEqual(1, len(cyc))
        self.assertEqual({"a", "b"}, set(cyc[0]))
        self.assertIn("i", metrics["a"])

    def test_sdp_is_direction_sensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mod(tmp, "leaf")
            _mod(tmp, "other")
            _mod(tmp, "sink", ["leaf", "other"])      # Ce=2, Ca=1 → I=0.67（不稳）
            _mod(tmp, "core_util", ["sink"])          # Ce=1, Ca=3 → I=0.25（较稳）
            _mod(tmp, "top1", ["core_util"])
            _mod(tmp, "top2", ["core_util"])
            _mod(tmp, "top3", ["core_util"])
            deps, metrics = cm.graph(tmp)
            viol = cm.sdp_violations(deps, metrics)
        self.assertIn(("core_util", "sink"), viol, "低 I 依赖高 I = 违例")
        self.assertNotIn(("sink", "core_util"), viol, "反向不是违例")


class RatchetTest(unittest.TestCase):
    def test_unregistered_cycle_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mod(tmp, "a", ["b"])
            _mod(tmp, "b", ["a"])
            issues, _w, stats = cm.scan(tmp)
        self.assertTrue(any("新增模块级环" in i for i in issues), issues)
        self.assertEqual(1, stats["cycles"])

    def test_registered_cycle_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mod(tmp, "a", ["b"])
            _mod(tmp, "b", ["a"])
            cm.write(tmp)
            issues, warns, stats = cm.scan(tmp)
        self.assertEqual([], issues, "登记债应放行")
        self.assertEqual(1, stats["registered_cycles"])
        self.assertEqual([], [w for w in warns if "消除" in w])

    def test_new_sdp_violation_fails_with_baseline_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mod(tmp, "leaf")
            _mod(tmp, "mid", ["leaf"])
            _mod(tmp, "t1", ["leaf"])
            _mod(tmp, "t2", ["leaf"])
            _mod(tmp, "t3", ["leaf"])
            cm.write(tmp)                       # 基线：leaf I=0（最稳）→ 无违例
            before, _w, _s = cm.scan(tmp)
            self.assertEqual([], before)
            _mod(tmp, "x1")
            _mod(tmp, "x2")
            _mod(tmp, "x3")
            _mod(tmp, "hub", ["x1", "x2", "x3"])       # hub：Ce=3 · Ca=1 → I=0.75
            _mod(tmp, "leaf", ["hub"])                 # 稳定侧 leaf（I≈0.2）反向依赖 hub
            issues, _w2, _s2 = cm.scan(tmp)
        self.assertTrue(any("新增 SDP 违例" in i and "hub" in i for i in issues), issues)

    def test_eliminated_debt_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mod(tmp, "a", ["b"])
            _mod(tmp, "b", ["a"])
            cm.write(tmp)
            _mod(tmp, "b")                      # 断环
            issues, warns, _s = cm.scan(tmp)
        self.assertEqual([], issues)
        self.assertTrue(any("已消除" in w for w in warns), warns)

    def test_missing_baseline_warns_with_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            _mod(tmp, "a")
            _issues, warns, _s = cm.scan(tmp)
        self.assertTrue(any(cm.BASELINE_REL in w and "修复指引" in w for w in warns), warns)


class RealRepoTest(unittest.TestCase):
    def test_baseline_committed_and_scan_clean(self):
        p = ROOT / cm.BASELINE_REL
        self.assertTrue(p.is_file(), "须提交耦合基线：%s" % cm.BASELINE_REL)
        doc = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(cm.SCHEMA, doc["schema"])
        issues, _w, stats = cm.scan(str(ROOT))
        self.assertEqual([], issues, "真仓不得有未登记的新增环/SDP 违例：%s" % issues[:3])
        self.assertGreater(stats["modules"], 50)
        # 2026-09-29 拆环完成后：真仓**零环**（此前 3 条登记债已全部消除）。
        self.assertEqual(0, stats["cycles"], "真仓模块级环必须为 0（零环是硬判据）")
        self.assertEqual(0, stats["registered_cycles"])
        # 判据自身不许空转：合成一个有环的图，分析器必须抓得到。
        self.assertTrue(cm.cycles({"a": {"b"}, "b": {"a"}}), "合成环必须被抓（否则本判据空转）")


if __name__ == "__main__":
    unittest.main()
