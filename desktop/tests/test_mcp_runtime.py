# -*- coding: utf-8 -*-
"""MCP Server 运行时单测（v2.5.0 Wave5 C1：快照 → stdio JSON-RPC 服务）。

运行：cd desktop && python -m unittest tests.test_mcp_runtime -v
33-A5 报告差距勾销（对照 33_v2.2.0_A5-MCP规范差距核查报告.md）：
- G1 形态级：mcp.json 静态快照 → 运行时 JSON-RPC 会话（handle 逐消息应答）
- G2 字段级：resources/list 返回去 text 元数据；正文经 resources/read contents[].text
- G4 归属层：name/version 入 initialize 握手 serverInfo（快照顶层仅作数据源）
- C2 最小安全层：只读（无 tools/prompts）+ uri 白名单（未知 uri → -32602）
数据源 = mcp_adapter 真实产出（export(ir,'mcp') → mcp.json 快照）。
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.exporter import export  # noqa: E402
from core.ir import IRDocument, IRLayer, IRModule  # noqa: E402
from core.mcp_runtime import McpRuntime, load_snapshot  # noqa: E402


def _techdoc_snapshot() -> dict:
    """真实 techdoc IR → mcp.json 快照（与 test_mcp_adapter 同构，P90+M90）。"""
    ir = IRDocument(
        type="techdoc", title="模组协议规范", pipeline_id="P90",
        pipeline_name="技术文档生成管线",
        layers=[
            IRLayer(id="P10", name="结构", modules=[
                IRModule(full_id="技术文档类:M90", name="协议骨架", layer="P10",
                         content="协议必含：前置声明/字段表/示例三段。")]),
            IRLayer(id="P30", name="片段", modules=[
                IRModule(full_id="技术文档类:M90", name="规则校验", layer="P30",
                         content="字段命名：snake_case；引用闭合。")]),
        ],
        asset_refs={}, asset_missing=[], meta={})
    tmp = Path(tempfile.mkdtemp(prefix="nf_mcp_rt_"))
    res = export(ir, "mcp", dest_dir=tmp)
    snap_path = next(Path(f) for f in res.files if f.endswith("mcp.json"))
    return load_snapshot(str(snap_path))


def _req(mid, method, params=None):
    msg = {"jsonrpc": "2.0", "id": mid, "method": method}
    if params is not None:
        msg["params"] = params
    return msg


class TestMcpRuntime(unittest.TestCase):
    def setUp(self):
        self.snap = _techdoc_snapshot()
        self.srv = McpRuntime(self.snap)

    def test_initialize_handshake_g4(self):
        """G4 勾销：serverInfo.name/version 出自 initialize 握手；capabilities.resources 在场。"""
        resp = self.srv.handle(_req(1, "initialize", {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "0.0.1"},
        }))
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["id"], 1)
        result = resp["result"]
        self.assertEqual(result["protocolVersion"], "2025-11-25")
        self.assertEqual(result["capabilities"]["resources"], {})
        self.assertEqual(result["serverInfo"]["name"], "P90-mcp")
        self.assertTrue(result["serverInfo"]["version"])

    def test_initialized_notification_no_response(self):
        """notifications/initialized 是通知——无 id，不应回响应。"""
        self.assertIsNone(self.srv.handle(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_list_resources_no_text_g2(self):
        """G2 勾销：resources/list 返回纯元数据——Resource 条目绝无 text。"""
        resp = self.srv.handle(_req(2, "resources/list"))
        resources = resp["result"]["resources"]
        self.assertEqual(len(resources), 2)
        for r in resources:
            self.assertIn("uri", r)
            self.assertIn("name", r)
            self.assertNotIn("text", r, f"list 元数据不得内嵌正文（G2）：{r}")
            self.assertTrue(r["uri"].startswith("nf://P90/"))

    def test_read_resource_returns_text_g2(self):
        """G2 勾销：正文经 resources/read → contents[].text（TextResourceContents）。"""
        listed = self.srv.handle(_req(2, "resources/list"))["result"]["resources"]
        uri = listed[0]["uri"]
        resp = self.srv.handle(_req(3, "resources/read", {"uri": uri}))
        contents = resp["result"]["contents"]
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0]["uri"], uri)
        self.assertIn("text", contents[0])
        self.assertTrue(contents[0]["text"])  # 正文非空

    def test_read_unknown_uri_rejected_c2(self):
        """C2 白名单：未知 uri → -32602 INVALID_PARAMS（只读拒绝，不泄露）。"""
        resp = self.srv.handle(_req(4, "resources/read",
                                   {"uri": "nf://P90/P10/不存在-XX"}))
        self.assertEqual(resp["error"]["code"], -32602)

    def test_unknown_method_not_found(self):
        """未实现方法（含 tools/call 写路径）→ -32601 METHOD_NOT_FOUND（只读纪律）。"""
        resp = self.srv.handle(_req(5, "tools/call", {"name": "x"}))
        self.assertEqual(resp["error"]["code"], -32601)

    def test_ping_empty_result(self):
        resp = self.srv.handle(_req(6, "ping"))
        self.assertEqual(resp["result"], {})

    def test_invalid_jsonrpc_version(self):
        resp = self.srv.handle({"jsonrpc": "1.0", "id": 7, "method": "ping"})
        self.assertEqual(resp["error"]["code"], -32600)

    def test_serve_stdio_line_delimited_roundtrip(self):
        """G1 形态：serve_stdio 换行分隔循环——init/list/read 逐行往返，中文 uri 不丢。"""
        from io import StringIO
        uri = next(iter(self.snap["mcp"]["resources"]))["uri"]
        self.assertIn("nf://", uri)
        inbound = "\n".join([
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2025-11-25",
                                   "capabilities": {},
                                   "clientInfo": {"name": "t", "version": "0"}}},
                       ensure_ascii=False),
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            json.dumps({"jsonrpc": "2.0", "id": 3, "method": "resources/list"}),
            json.dumps({"jsonrpc": "2.0", "id": 4, "method": "resources/read",
                        "params": {"uri": uri}}, ensure_ascii=False),
            "这不是 JSON\n",
        ]) + "\n"
        out = StringIO()
        self.srv.serve_stdio(stdin=StringIO(inbound), stdout=out)
        lines = [l for l in out.getvalue().splitlines() if l.strip()]
        # init + list + read 三响应（notification 无响应；坏 JSON → -32700）
        self.assertEqual(len(lines), 4)
        msgs = [json.loads(l) for l in lines]
        by_id = {m["id"]: m for m in msgs if "id" in m}
        self.assertEqual(by_id[1]["result"]["serverInfo"]["name"], "P90-mcp")
        listed = by_id[3]["result"]["resources"]
        self.assertTrue(all("text" not in r for r in listed))
        read = by_id[4]["result"]["contents"][0]
        self.assertEqual(read["uri"], uri)
        self.assertTrue(read["text"])
        # 坏 JSON → PARSE_ERROR(-32700)
        errs = [m for m in msgs if "error" in m]
        self.assertTrue(errs and errs[0]["error"]["code"] == -32700)


if __name__ == "__main__":
    unittest.main()
