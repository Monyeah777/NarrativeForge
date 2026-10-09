# -*- coding: utf-8 -*-
"""两轴同族判据：**LSP 面与 MCP 面必须对同一批 JSON-RPC 语义给同一档处理**。

为什么需要（2026-10-08 实测教训）：两侧各自都有协议测试，但**没有一条判据把同一语义在两侧对齐**。
实证是 LSP 面曾把 `$/` **请求**静默吞掉（合规客户端会一直等应答），而同族语义在 MCP 面处理是对的
——这类「协议族口径」漂移天然会在**另一轴**复现，且两侧各自的测试都发现不了（各自都自洽）。
本件把共享口径列成表，逐条在两侧**实跑**，并带变异负例（对通知也回错的桩必须被判据抓到）。

MCP 特有的两条另行钉住（不与 LSP 混谈）：`ping` 规范要求必须回空结果；LSP 无 `ping`，未知方法
一律 -32601。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import json_schema  # noqa: E402
from core import lsp  # noqa: E402
from core import mcp_runtime as mrt  # noqa: E402

METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602


def _code(reply):
    """取应答的错误码；无应答返回 None（列表/dict 两种形态都收）。"""
    if isinstance(reply, list):
        reply = reply[0] if reply else None
    if not reply or "error" not in reply:
        return None
    return reply["error"].get("code")


def _replies_to_notification(server) -> bool:
    """该服务器是否对「通知」也回了应答（协议违规：通知没有应答位）。"""
    return bool(server.handle({"jsonrpc": "2.0", "method": "no/such-notification"}))


class _Faces:
    """两侧被测面的统一取用：LSP 需先握手（协议状态机），MCP 需注入参数校验器（依赖倒置）。"""

    @staticmethod
    def lsp():
        srv = lsp.LspServer(root=str(ROOT), explicit_root=True)
        srv.handle({"jsonrpc": "2.0", "id": 1, "method": lsp.M_INITIALIZE, "params": {}})
        return srv

    @staticmethod
    def mcp():
        rt = mrt.McpRuntime({"mcp": {"name": "parity", "version": "0", "resources": []}},
                            schema_check=json_schema.json_schema_check)
        if hasattr(rt, "set_root"):
            rt.set_root(str(ROOT))
        return rt


class TwoFacesJsonRpcParityTest(unittest.TestCase):
    def test_unknown_request_is_method_not_found_on_both_faces(self):
        for face in ("lsp", "mcp"):
            reply = getattr(_Faces, face)().handle(
                {"jsonrpc": "2.0", "id": 9, "method": "no/such"})
            self.assertEqual(METHOD_NOT_FOUND, _code(reply),
                             "%s 面未知请求未回 -32601" % face.upper())

    def test_notifications_are_silent_on_both_faces(self):
        for face in ("lsp", "mcp"):
            server = getattr(_Faces, face)()
            self.assertFalse(_replies_to_notification(server),
                             "%s 面对未知通知回了应答（通知没有应答位）" % face.upper())

    def test_request_shaped_method_as_notification_stays_silent(self):
        """把**真请求方法**当通知发：两侧都必须静默（没有应答位，也不得改状态）。"""
        lsp_out = _Faces.lsp().handle({"jsonrpc": "2.0", "method": lsp.M_HOVER,
                                       "params": {"textDocument": {"uri": "file:///x.md"},
                                                  "position": {"line": 0, "character": 0}}})
        self.assertEqual([], lsp_out)
        mcp_out = _Faces.mcp().handle({"jsonrpc": "2.0", "method": "tools/call",
                                       "params": {"name": "spec_ls", "arguments": {}}})
        self.assertFalse(mcp_out, "MCP 面对「请求当通知发」回了应答")

    def test_bad_params_is_invalid_params_on_both_faces(self):
        lsp_reply = _Faces.lsp().handle(
            {"jsonrpc": "2.0", "id": 10, "method": lsp.M_HOVER,
             "params": {"textDocument": {"uri": "file:///x.md"},
                        "position": {"line": "x", "character": 0}}})
        self.assertEqual(INVALID_PARAMS, _code(lsp_reply), "LSP 面非法参数未回 -32602")
        mcp_reply = _Faces.mcp().handle(
            {"jsonrpc": "2.0", "id": 10, "method": "tools/call",
             "params": {"name": "spec_ls", "arguments": []}})
        self.assertEqual(INVALID_PARAMS, _code(mcp_reply), "MCP 面非法参数未回 -32602")

    def test_ping_is_answered_by_mcp_and_unknown_to_lsp(self):
        """MCP 规范：服务器**必须**应答 ping（空结果）；LSP 无 ping（未知方法 → -32601）。"""
        mcp_reply = _Faces.mcp().handle({"jsonrpc": "2.0", "id": 11, "method": "ping"})
        self.assertIn("result", mcp_reply, "MCP 面 ping 必须有应答")
        lsp_reply = _Faces.lsp().handle({"jsonrpc": "2.0", "id": 11, "method": "ping"})
        self.assertEqual(METHOD_NOT_FOUND, _code(lsp_reply), "LSP 面 ping 应为未知方法")

    def test_harness_detects_a_violating_server(self):
        """变异负例：对通知也回应答的桩必须被本件的助手抓到，否则判据空转。"""
        class Noisy:
            @staticmethod
            def handle(msg):
                return {"jsonrpc": "2.0", "id": msg.get("id"), "result": None}

        self.assertTrue(_replies_to_notification(Noisy()), "变异负例未被抓到（判据失效）")
        self.assertFalse(_replies_to_notification(_Faces.lsp()))
        self.assertFalse(_replies_to_notification(_Faces.mcp()))


if __name__ == "__main__":
    unittest.main()
