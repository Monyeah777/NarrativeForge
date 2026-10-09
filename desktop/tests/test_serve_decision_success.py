# -*- coding: utf-8 -*-
"""决策层本地服务的**成功路径**回归（内部差距实证：该路径此前只有手工 AUD-0013 一次真跑）。

缺口（2026-10-07 三轴审计）：serve_decision_model.py 只有「绑定守卫 + 请求体上限」的加固
测试，_to_laya_questions / _normalize 与 HTTP handler 的**成功路径**无任何常驻判据——
真实适配器（systemone-http）的成功面因此没有 CI 可跑证据，只有一次人工记录。
本件用**真 HTTP**（回环 + 临时端口）跑真 handler，把 NF 契约钉住：
- choice 概率按 NF 选项顺序、score 按 legend 数字序、noul 单值；
- _meta.model / usage / calibrated 回传（校准置信度可见，不藏）；
- 未知路径 404 / 空请求体 413 / **入参形状错 400 + 修复指引**（2026-10-08 改：旧实现一律 500，
  会把「永不成功的请求」报成服务端故障而诱发重试）；真·服务端故障仍是 500——两类分开。

模型以桩注入（AGENT 是模块级单例）：判据考的是**翻译层与 HTTP 契约**，不是模型质量；
真模型推理属外部运行事实（见 results/audit/docs_audit-61-real-model-loop.md）。
"""
import http.client
import importlib.util
import json
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOD_PATH = ROOT / "scripts" / "serve_decision_model.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("nf_serve_decision_success", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class StubAgent:
    """桩：按 Laya 返回形状给确定性答案（含缺键，考归一层的兜底）。"""

    model_id = "stub-laya"

    def __init__(self):
        self.seen = None

    def predict(self, state, questions):
        self.seen = (state, questions)
        return {
            "answers": {
                "pick": {"probabilities": {"甲": 0.7, "乙": 0.3}, "confidence": 0.71},
                "risk": {"probabilities": {"0": 0.1, "1": 0.2, "2": 0.7},
                         "legend": {"0": "低", "1": "中", "2": "高"}, "confidence": 0.55},
                "gate": {"noul": 0.98, "confidence": 0.9},
            },
            "usage": {"input_tokens": 604},
        }


class ServeSuccessPathTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        cls.mod.AGENT = StubAgent()
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), cls.mod.Handler)
        cls.port = cls.srv.server_address[1]
        cls.thread = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        cls.thread.join(timeout=5)

    def _post(self, path, body):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            conn.request("POST", path, body=payload,
                         headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            return resp.status, json.loads(resp.read().decode("utf-8"))
        finally:
            conn.close()

    def _get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            conn.request("GET", path)
            resp = conn.getresponse()
            return resp.status, json.loads(resp.read().decode("utf-8"))
        finally:
            conn.close()

    def test_health_reports_model_loaded(self):
        status, body = self._get("/health")
        self.assertEqual(200, status)
        self.assertEqual("ok", body["status"])
        self.assertIs(True, body["model_loaded"])

    def test_systemone_success_contract(self):
        questions = {
            "pick": {"type": "choice", "options": ["甲", "乙"], "instructions": "选一个"},
            "risk": {"type": "score", "levels": ["低", "中", "高"], "instructions": "评级"},
            "gate": {"type": "noul", "instructions": "是否安全"},
        }
        status, body = self._post("/v1/systemone", {"state": "回合状态", "questions": questions})
        self.assertEqual(200, status)
        self.assertEqual([0.7, 0.3], body["pick"]["probs"], "choice 概率须按 NF 选项顺序")
        self.assertEqual([0.1, 0.2, 0.7], body["risk"]["probs"], "score 概率须按 legend 数字序")
        self.assertEqual("高", body["risk"]["legend"]["2"])
        self.assertEqual([0.98], body["gate"]["probs"], "noul 只有单值")
        self.assertEqual("stub-laya", body["_meta"]["model"])
        self.assertEqual({"input_tokens": 604}, body["_meta"]["usage"])
        self.assertIs(True, body["_meta"]["calibrated"])

    def test_questions_translation_shape(self):
        got = self.mod._to_laya_questions({
            "pick": {"type": "choice", "options": ["甲", "乙"]},
            "risk": {"type": "score", "levels": ["低", "高"]},
            "gate": {"type": "noul", "instructions": "安全吗"},
        })
        self.assertEqual({"甲": "甲", "乙": "乙"}, got["pick"]["criteria"])
        self.assertEqual(["低", "高"], got["risk"]["criteria"])
        self.assertEqual("安全吗", got["gate"]["instructions"])
        self.assertNotIn("criteria", got["gate"], "noul 不带 criteria")
        self.assertEqual("pick", got["pick"]["instructions"], "缺 instructions 时回落 qid")

    def test_missing_probability_keys_default_to_zero(self):
        normalized = self.mod._normalize(
            {"answers": {"pick": {"probabilities": {"甲": 0.9}}}},
            {"pick": {"type": "choice", "options": ["甲", "乙"]}})
        self.assertEqual([0.9, 0.0], normalized["pick"]["probs"], "缺键补 0，不放任 KeyError")

    def _raw(self, method, path, body=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            conn.request(method, path, body=body,
                         headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            raw = resp.read()
            return resp.status, dict(resp.getheaders()), raw
        finally:
            conn.close()

    def test_error_paths_are_explicit(self):
        # 带真请求体打未知路径：服务端必须先读完再回 404，否则客户端拿到连接重置
        # （实测 Windows：ConnectionAbortedError [WinError 10053]）。
        status, body = self._post("/v1/nope", {"pad": "x" * 65536})
        self.assertEqual(404, status)
        self.assertIn("error", body)
        status, body = self._post("/v1/systemone", {})
        self.assertEqual(400, status, "入参形状错 = 客户端错（400），不是服务端 500")
        self.assertEqual("invalid_request", body["error"]["type"])
        conn0 = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        try:
            conn0.request("POST", "/v1/systemone", body=b"",
                          headers={"Content-Type": "application/json"})
            resp0 = conn0.getresponse()
            body0 = json.loads(resp0.read().decode("utf-8"))
            self.assertEqual(413, resp0.status, "空请求体应被上限守卫拒绝")
            self.assertIn("修复指引", body0["error"])
        finally:
            conn0.close()

    def test_client_input_errors_are_400_with_hint(self):
        """入参形状失败一律 400 + 修复指引（2026-10-08 改：旧实现全回 500）。

        为什么重要：调用方（NF 决策层）按状态码决定「重试 / 不重试」——把客户端错误报成 500
        会引发**对永不会成功的请求反复重试**，且 500 里带 Python 异常类名会把排查引向服务端。
        本仓另两个服务面（LSP -32602 / MCP -32602）早已分开，这里补齐同一口径。
        """
        for label, payload in (
                ("非对象请求体", json.dumps([1, 2]).encode("utf-8")),
                ("坏 JSON", b"{not json"),
                ("缺 state", json.dumps({"questions": {"q": {"type": "noul"}}}).encode("utf-8")),
                ("questions 是数组",
                 json.dumps({"state": "s", "questions": [{"type": "noul"}]}).encode("utf-8")),
                ("questions 项非对象",
                 json.dumps({"state": "s", "questions": {"q": "noul"}}).encode("utf-8"))):
            status, _hdrs, raw = self._raw("POST", "/v1/systemone", payload)
            body = json.loads(raw.decode("utf-8"))
            self.assertEqual(400, status, label)
            self.assertEqual("invalid_request", body["error"]["type"], label)
            self.assertIn("hint", body["error"], label)

    def test_server_side_failure_is_still_500(self):
        """真·服务端故障仍是 500（两类不许混：能 400 的别回 500，是 500 的别降成 400）。"""
        class Boom:
            model_id = "boom"

            def predict(self, state, questions):
                raise RuntimeError("推理崩了")

        original, self.mod.AGENT = self.mod.AGENT, Boom()
        try:
            status, _hdrs, raw = self._raw(
                "POST", "/v1/systemone",
                json.dumps({"state": "s", "questions": {"q": {"type": "noul"}}}).encode("utf-8"))
        finally:
            self.mod.AGENT = original
        body = json.loads(raw.decode("utf-8"))
        self.assertEqual(500, status)
        self.assertEqual("RuntimeError", body["error"]["type"])

    def test_other_methods_are_405_json_and_head_is_header_only(self):
        """未支持方法回 405 JSON（不是 BaseHTTPRequestHandler 的 HTML 501）；HEAD 只回表头。"""
        for method in ("PUT", "DELETE", "PATCH", "OPTIONS"):
            status, hdrs, raw = self._raw(method, "/v1/systemone")
            self.assertEqual(405, status, method)
            self.assertIn("GET", hdrs.get("Allow", ""), method)
            self.assertEqual("method not allowed", json.loads(raw.decode("utf-8"))["error"])
        status, _hdrs, raw = self._raw("HEAD", "/health")
        self.assertEqual(200, status)
        self.assertEqual(b"", raw, "HEAD 不得带正文")


if __name__ == "__main__":
    unittest.main()
