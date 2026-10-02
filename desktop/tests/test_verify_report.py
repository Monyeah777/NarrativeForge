#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""门禁机器可读报告（`core/verify_report.py`）回归测试 —— 静态可核验面。

覆盖：构建确定性 / 声明与实测并排 / 缺件与篡改可检出 / 坏判据记账为 error 而不崩 /
真仓报告零 FAIL。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import verify_report as vr  # noqa: E402


class BuildTest(unittest.TestCase):
    def test_build_is_deterministic(self):
        a, b = vr.build(str(ROOT)), vr.build(str(ROOT))
        self.assertEqual(a["root_digest"], b["root_digest"],
                         "同一棵树两次构建必须同根（否则报告不可核验）")

    def test_items_cover_declared_specs(self):
        r = vr.build(str(ROOT))
        self.assertEqual(len(vr.SPECS), len(r["items"]))
        self.assertEqual({"pass", "fail", "warn", "error"},
                         set(r["summary"]))
        self.assertEqual(len(r["items"]),
                         sum(r["summary"].values()), "汇总须等于逐条计数之和")

    def test_declared_side_is_present(self):
        d = vr.build(str(ROOT))["declared"]
        self.assertIsInstance(d.get("expected_checks"), int)
        self.assertGreater(d["expected_checks"], 0)
        self.assertTrue(str(d.get("verify_version") or ""), "声明面须含 verify 版本")

    def test_broken_judgement_is_recorded_not_crashing(self):
        """坏判据须记账为 error（报告本身必须出得来）。"""
        with tempfile.TemporaryDirectory() as tmp:      # 空根 → 多条判据会报 fail/error
            r = vr.build(tmp)
        self.assertEqual(len(vr.SPECS), len(r["items"]))
        self.assertNotIn(None, [i["status"] for i in r["items"]])


class CheckTest(unittest.TestCase):
    def test_missing_report_reports_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            issues, _ = vr.check(tmp)
        self.assertTrue(issues)
        self.assertIn("修复指引", issues[0])
        self.assertIn(vr.REPORT_REL, issues[0])

    def test_tampered_report_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            vr.write(tmp)
            p = Path(tmp) / vr.REPORT_REL
            doc = json.loads(p.read_text(encoding="utf-8"))
            doc["root_digest"] = "0" * 64
            p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            issues, _ = vr.check(tmp)
        self.assertTrue(any("不一致" in i for i in issues), issues)

    def test_written_report_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            vr.write(tmp)
            issues, _ = vr.check(tmp)
        self.assertEqual([], issues, "写后即读须一致")

    def test_schema_mismatch_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            vr.write(tmp)
            p = Path(tmp) / vr.REPORT_REL
            doc = json.loads(p.read_text(encoding="utf-8"))
            doc["schema"] = "bogus/0"
            p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            issues, _ = vr.check(tmp)
        self.assertTrue(any("schema" in i for i in issues), issues)


class RealRepoTest(unittest.TestCase):
    def test_real_repo_has_no_failing_judgement(self):
        r = vr.build(str(ROOT))
        bad = [i["id"] for i in r["items"] if i["status"] in ("fail", "error")]
        self.assertEqual([], bad, "真仓门禁报告不得有 FAIL/ERROR：%s" % bad)

    def test_summary_line_mentions_declared_baseline(self):
        line = vr.summary_line(vr.build(str(ROOT)))
        self.assertIn("声明 check1-", line)
        self.assertIn("PASS=", line)

    def test_committed_report_is_fresh(self):
        """**提交件 == 实时重算**——本地也要判（2026-10-01 取证）。

        为什么缺这条会出事：`ci-verify.yml` 与 `release-gate.yml` 都是**先 `--write` 再
        `--check`**（写一遍再比，天然通过），而 `verify.sh` **不跑** `verify_report`；
        于是「提交的机器可读报告陈旧」在**本地与云端都不会红**——本轮实测：
        `protocol/verification_report.json` 记录 `7ef20df0…` vs 实测 `1efe3d61…`（陈旧），
        而门禁全绿。`nf release --fresh` 会红，但那是可选入口。本件把它钉进常驻单测。
        """
        issues, live = vr.check(str(ROOT))
        self.assertEqual([], issues,
                         "机器可读报告过期（修复指引：python scripts/verify_report.py --write）：%s"
                         % issues)
        self.assertEqual(vr.SCHEMA, live.get("schema"))


if __name__ == "__main__":
    unittest.main()
