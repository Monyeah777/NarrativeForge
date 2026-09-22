#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""决策层端口单测（typed-decision：三原语 / schema / 确定性 / fail-closed / 拉取脚手架）。"""
import importlib.util
import io
import contextlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import decision_layer as dl  # noqa: E402

REQ = {"state": "雨天走廊 校园情感 中文 场景；候选 P02 校园情感流 / P03 西幻生存流",
       "questions": {
           "pipeline": {"type": "choice", "options": ["P02 校园情感流", "P03 西幻生存流"]},
           "need_multilingual": {"type": "noul", "true_hints": ["中文"]},
           "risk": {"type": "score", "levels": ["低", "中", "高"]}}}


class DecisionLayerTest(unittest.TestCase):
    def test_repo_declaration_is_clean(self):
        issues, stats = dl.scan(str(ROOT))
        self.assertEqual(issues, [], issues)
        self.assertEqual(stats["primitives"], 3)
        self.assertGreaterEqual(stats["adapters"], 3)
        self.assertGreaterEqual(stats["candidates"], 3)

    def test_only_stub_is_in_gate_path(self):
        decl = dl.load_decl(str(ROOT))
        in_gate = [a["id"] for a in decl["adapters"] if a.get("in_gate_path")]
        self.assertEqual(in_gate, ["stub"], "门禁只许离线确定性适配器")
        for a in decl["adapters"]:
            self.assertIn("calibrated", a)
            self.assertTrue(a.get("note"))

    def test_candidates_declare_source_license_evidence(self):
        cands = dl.load_decl(str(ROOT))["candidates"]
        for c in cands:
            self.assertTrue(c["source"].startswith("hf:"), c)
            self.assertEqual(c["license"], "apache-2.0", c)
            self.assertTrue(len(c["evidence"]) > 40, "实证要点须具体")
            self.assertIsInstance(c["pulled"], bool, "pulled 状态不许含糊")
            if c["pulled"]:
                # 已拉取 = 显式动作 → 必须自带可追溯的本地证据
                local = c.get("local") or {}
                for k in ("how", "runtime", "served_by"):
                    self.assertTrue(local.get(k), "%s 缺 local.%s" % (c["id"], k))
        self.assertTrue(any(not c["pulled"] for c in cands),
                        "至少保留未拉取候选：拉取是按模型逐个显式授权的动作")

    def test_stub_is_deterministic_and_uncalibrated(self):
        a = dl.decide(REQ, adapter="stub", root=str(ROOT))
        b = dl.decide(REQ, adapter="stub", root=str(ROOT))
        self.assertEqual(a["status"], "ok")
        self.assertEqual({k: v for k, v in a.items() if k != "meta"},
                         {k: v for k, v in b.items() if k != "meta"},
                         "stub 输出须确定（latency 之外的字段逐一相等）")
        self.assertFalse(a["meta"]["calibrated"])
        self.assertIs(a["meta"]["non_gate"], True)
        self.assertEqual(dl.fingerprint(REQ), dl.fingerprint(json.loads(json.dumps(REQ))))

    def test_request_shape_rules(self):
        self.assertEqual(dl.request_issue(REQ), "")
        self.assertIn("type 越词表", dl.request_issue(
            {"state": "x", "questions": {"q": {"type": "chat"}}}))
        self.assertIn("≥2 个候选", dl.request_issue(
            {"state": "x", "questions": {"q": {"type": "choice", "options": ["a"]}}}))
        self.assertIn("重复", dl.request_issue(
            {"state": "x", "questions": {"q": {"type": "choice",
                                               "options": ["a", "a"]}}}))
        self.assertIn("缺 state", dl.request_issue({"questions": {"q": {"type": "noul"}}}))

    def test_response_shape_rules(self):
        ok = dl.decide(REQ, adapter="stub", root=str(ROOT))
        self.assertEqual(dl.response_issue(ok, REQ), "")
        good_answers = dict(ok["answers"])
        bad_sum = {"schema": dl.RESPONSE_SCHEMA, "status": "ok",
                   "answers": dict(good_answers,
                                   pipeline={"type": "choice",
                                             "options": ["a", "b"], "probs": [0.2, 0.2],
                                             "argmax": "a"}),
                   "meta": {"calibrated": True, "non_gate": True}}
        self.assertIn("概率和", dl.response_issue(bad_sum, REQ))
        bad_argmax = {"schema": dl.RESPONSE_SCHEMA, "status": "ok",
                      "answers": dict(good_answers,
                                      pipeline={"type": "choice", "options": ["a", "b"],
                                                "probs": [0.5, 0.5], "argmax": "zzz"}),
                      "meta": {"calibrated": True, "non_gate": True}}
        self.assertIn("argmax", dl.response_issue(bad_argmax, REQ))
        missing = {"schema": dl.RESPONSE_SCHEMA, "status": "ok", "answers": {},
                   "meta": {"calibrated": True, "non_gate": True}}
        self.assertIn("缺问题", dl.response_issue(missing, REQ))
        no_gate_flag = dict(ok)
        no_gate_flag["meta"] = {"calibrated": True}
        self.assertIn("non_gate", dl.response_issue(no_gate_flag, REQ))

    def test_fail_closed_paths(self):
        cases = (
            ("未登记适配器", {"adapter": "ghost"}, "未登记"),
            ("缺 endpoint", {"adapter": "systemone-http"}, "endpoint"),
            ("openai 缺 model", {"adapter": "openai-json", "endpoint": "http://x"}, "model"),
        )
        for label, kwargs, hint in cases:
            out = dl.decide(REQ, root=str(ROOT), **kwargs)
            self.assertEqual(out["status"], "abstained", label)
            self.assertIn(hint, out["reason"], label)
        bad_req = dl.decide({"questions": {}}, adapter="stub", root=str(ROOT))
        self.assertEqual(bad_req["status"], "abstained")
        self.assertIn("请求不合规", bad_req["reason"])

    def test_unknown_adapter_without_declaration_abstains(self):
        out = dl.decide(REQ, adapter="systemone-http", root=str(ROOT))
        self.assertEqual(out["status"], "abstained")
        self.assertIs(out["meta"]["non_gate"], True)


class PullToolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "nf_pull_model", ROOT / "scripts" / "pull_decision_model.py")
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def test_list_offline(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = self.tool.main(["--root", str(ROOT), "--list"])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        for cid in ("laya-typed-decisions", "laya-multilingual", "open-jev-9b"):
            self.assertIn(cid, out)
        self.assertIn("apache-2.0", out)

    def test_dry_run_prints_commands_without_downloading(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = self.tool.main(["--root", str(ROOT), "--candidate", "laya-multilingual"])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("hf download", out)
        self.assertIn("未执行", out, "默认必须不下载")

    def test_run_requires_yes(self):
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = self.tool.main(["--root", str(ROOT), "--candidate", "open-jev-9b",
                                 "--run"])
        self.assertEqual(rc, 2)
        self.assertIn("--yes", err.getvalue())

    def test_unknown_candidate_is_usage_error(self):
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            rc = self.tool.main(["--root", str(ROOT), "--candidate", "nope"])
        self.assertEqual(rc, 2)


class WorkloopTest(unittest.TestCase):
    """构建回路：决策挑活 → 工单（含判据）→ 只落内部档案；决策模型不落笔。"""

    def setUp(self):
        from core import workloop as wl
        self.wl = wl

    def test_repo_loop_is_clean(self):
        issues, stats = self.wl.scan(str(ROOT))
        self.assertEqual(issues, [], issues)
        self.assertGreater(stats["items"], 50, "待办真源应有实际条目")
        self.assertTrue(stats["stub_order"].startswith("WO-"))

    def test_items_come_from_public_declarations(self):
        rows = self.wl.items(str(ROOT))
        sources = {r["source"] for r in rows}
        # 三类公开派生源：待办声明两件 + 「扩展/深化/创新」能力缺口（机械派生）
        self.assertEqual(sources, {"type-backlog", "pipeline-advisory", "capability-gaps"})
        gaps = [r for r in rows if r["source"] == "capability-gaps"]
        for g in gaps:
            self.assertIn(g.get("family"), ("extend", "deepen", "innovate"))
            self.assertTrue(g["where_hint"] and g["done_when"])
        for r in rows[:3]:
            self.assertTrue(r["where_hint"])
            self.assertTrue(r["done_when"])

    def test_plan_is_deterministic_and_brief_has_acceptance(self):
        p1 = self.wl.plan(str(ROOT), adapter="stub", top=3)
        p2 = self.wl.plan(str(ROOT), adapter="stub", top=3)
        self.assertEqual(p1, p2)
        self.assertEqual(p1["status"], "ok")
        brief = p1["worker_brief"]
        self.assertIn("verify.sh", brief["accept"])
        self.assertIn("生成式 worker", brief["worker_role"])
        self.assertIn("不写内容", p1["decision"]["note"])

    def test_order_written_only_into_internal_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "protocol"))
            for rel in ("protocol/type_backlog.json", "protocol/pipeline_advisory.json"):
                src = ROOT / rel
                with open(os.path.join(tmp, rel), "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(src.read_text(encoding="utf-8"))
            shutil.copy(ROOT / "protocol" / "decision_layer.json",
                        os.path.join(tmp, "protocol", "decision_layer.json"))
            doc = self.wl.plan(tmp, adapter="stub", top=2)
            rel = self.wl.write_order(tmp, doc)
            self.assertTrue(rel.startswith(self.wl.ARCHIVE_PREFIX), rel)
            self.assertTrue(os.path.isfile(os.path.join(tmp, rel)))
            rec = self.wl.close(tmp, doc["order_id"], "landed", "PASS=61", "演练")
            self.assertTrue(rec.startswith(self.wl.ARCHIVE_PREFIX))

    def test_plan_abstains_when_adapter_unavailable(self):
        doc = self.wl.plan(str(ROOT), adapter="systemone-http")   # 无 endpoint
        self.assertEqual(doc["status"], "abstained")
        self.assertIn("endpoint", doc["reason"])
        meta = doc.get("decision_meta") or {}
        self.assertEqual(meta.get("adapter"), "systemone-http")
        self.assertIs(meta.get("non_gate"), True, "决策层永不在门禁路径")

    def test_empty_sources_yield_empty_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "protocol"))
            for rel, body in (("protocol/type_backlog.json", {"fields": []}),
                              ("protocol/pipeline_advisory.json", {"items": []}),
                              ("protocol/decision_layer.json",
                               json.loads((ROOT / "protocol" / "decision_layer.json")
                                          .read_text(encoding="utf-8")))):
                with open(os.path.join(tmp, rel), "w", encoding="utf-8",
                          newline="\n") as fh:
                    json.dump(body, fh, ensure_ascii=False)
            doc = self.wl.plan(tmp, adapter="stub")
            self.assertEqual(doc["status"], "empty")


if __name__ == "__main__":
    unittest.main()
