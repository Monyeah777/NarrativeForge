# -*- coding: utf-8 -*-
"""MCP Server 运行时单测（v2.5.0 Wave5 C1：快照 → stdio JSON-RPC 服务）。

运行：cd desktop && python -m unittest tests.test_mcp_runtime -v
33-A5 报告差距勾销（对照 33_v2.2.0_A5-MCP规范差距核查报告.md）：
- G1 形态级：mcp.json 静态快照 → 运行时 JSON-RPC 会话（handle 逐消息应答）
- G2 字段级：resources/list 返回去 text 元数据；正文经 resources/read contents[].text
- G4 归属层：name/version 入 initialize 握手 serverInfo（快照顶层仅作数据源）
- C2 最小安全层：只读 + uri 白名单（未知 uri → -32602）；41 波C C7 开放只读
  tools/prompts 面（无写路径工具，未知工具/方法仍拒出）
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
        self.assertIn("tools", result["capabilities"])
        self.assertIn("prompts", result["capabilities"])
        self.assertEqual(result["serverInfo"]["name"], "P90-mcp")
        self.assertTrue(result["serverInfo"]["version"])

    def test_initialized_notification_no_response(self):
        """notifications/initialized 是通知——无 id，不应回响应。"""
        self.assertIsNone(self.srv.handle(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_list_resources_no_text_g2(self):
        """G2 + 44 + A3：resources/list 分页返回快照+仓库资源元数据——条目绝无 text。"""
        resources = []
        cursor = None
        for _ in range(30):
            params = {} if cursor is None else {"cursor": cursor}
            resp = self.srv.handle(_req(50, "resources/list", params))
            page = resp["result"]["resources"]
            resources += page
            cursor = resp["result"].get("nextCursor")
            if not cursor:
                break
        self.assertGreaterEqual(len(resources), 2)
        self.assertTrue(any(r["uri"].startswith("nf://repo/module/")
                            for r in resources))
        for r in resources:
            self.assertIn("uri", r)
            self.assertIn("name", r)
            self.assertNotIn("text", r, f"list 元数据不得内嵌正文（G2）：{r}")

    def test_resources_templates_list(self):
        """A3：resources/templates/list 暴露仓库内容寻址模板。"""
        resp = self.srv.handle(_req(51, "resources/templates/list"))
        tpls = resp["result"]["resourceTemplates"]
        self.assertEqual(len(tpls), 3)
        self.assertTrue(any("nf://repo/module/" in t["uriTemplate"]
                            for t in tpls))

    def test_resources_list_filter_type(self):
        uris = set()
        cursor = None
        for _ in range(20):
            params = {"type": "module"}
            if cursor:
                params["cursor"] = cursor
            resp = self.srv.handle(_req(52, "resources/list", params))
            page = resp["result"]["resources"]
            uris |= {r["uri"] for r in page}
            cursor = resp["result"].get("nextCursor")
            if not cursor:
                break
        self.assertTrue(uris)
        self.assertTrue(all(u.startswith("nf://repo/module/") for u in uris))

    def test_resources_list_filter_asset_package(self):
        import urllib.parse as up
        resp = self.srv.handle(_req(53, "resources/list",
                                    {"type": "asset", "package": "官方"}))
        page = resp["result"]["resources"]
        self.assertTrue(page)
        for r in page:
            parts = r["uri"].split("/")
            self.assertEqual(up.unquote(parts[4]), "官方")

    def test_read_repo_module_resource_content(self):
        """44 深化：resources/read 经 nf://repo/… 取模块正文实质内容。"""
        resp = self.srv.handle(_req(31, "resources/read",
                                    {"uri": "nf://repo/module/M90"}))
        contents = resp["result"]["contents"]
        self.assertEqual(len(contents), 1)
        self.assertIn("machine_contract", contents[0]["text"])

    def test_channel_surface_end_to_end_deep(self):
        """44 深化：资源面与内容工具端到端自检（模块/管线/资产三类代表件全可读）。"""
        uris = set()
        cursor = None
        for _ in range(30):
            params = {} if cursor is None else {"cursor": cursor}
            resp = self.srv.handle(_req(40, "resources/list", params))
            page = resp["result"]["resources"]
            uris |= {r["uri"] for r in page}
            cursor = resp["result"].get("nextCursor")
            if not cursor:
                break
        self.assertTrue(any(u.endswith("/repo/module/M90") for u in uris))
        self.assertTrue(any(u.endswith("/repo/pipeline/P90") for u in uris))
        self.assertTrue(any(u.endswith("/TECH_RULES") for u in uris))
        for u in ("nf://repo/module/M90", "nf://repo/pipeline/P90"):
            resp = self.srv.handle(_req(41, "resources/read", {"uri": u}))
            self.assertIn("text", resp["result"]["contents"][0])
            self.assertNotIn("error", resp)
        # 资产：包内社区键也可经 asset_get 取正文
        resp = self.srv.handle(_req(42, "tools/call", {
            "name": "asset_get",
            "arguments": {"key": "EMOTION_WHEEL", "package": "校园情感领域包"}}))
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertTrue(payload["found"])
        self.assertGreater(len(payload["matches"][0]["text"]), 100)

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
        """未实现方法（非只读面方法）→ -32601 METHOD_NOT_FOUND。"""
        resp = self.srv.handle(_req(5, "bogus/method", {}))
        self.assertEqual(resp["error"]["code"], -32601)

    def test_tools_list_exposes_read_tools_c7(self):
        """41 波C C7 + 44：tools/list 暴露只读检索工具与内容通道工具（真实 inputSchema）。"""
        resp = self.srv.handle(_req(20, "tools/list"))
        tools = resp["result"]["tools"]
        names = {t["name"] for t in tools}
        self.assertEqual(names,
                         {"library_search", "registry_query",
                          "pipeline_ls", "spec_ls",
                          "module_read", "pipeline_read", "asset_get"})
        for t in tools:
            self.assertIn("inputSchema", t)

    def test_tools_call_module_read_content(self):
        """44 内容通道：module_read 返回模块正文实质内容（非仅元数据）。"""
        resp = self.srv.handle(_req(25, "tools/call", {
            "name": "module_read", "arguments": {"module_id": "M90"}}))
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertTrue(payload["found"])
        self.assertTrue(payload["bytes"] > 200)
        self.assertIn("machine_contract", payload["text"])

    def test_tools_call_module_read_content_only_module(self):
        """44 深化：存量内容模块（无机读块）也可按 id 读取正文。"""
        resp = self.srv.handle(_req(32, "tools/call", {
            "name": "module_read", "arguments": {"module_id": "M40"}}))
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertTrue(payload["found"])
        self.assertFalse(payload["has_machine_contract"])
        self.assertIn("关系深度", payload["text"])

    def test_tools_call_pipeline_read_content(self):
        """44 内容通道：pipeline_read 按 id 返回管线正文。"""
        resp = self.srv.handle(_req(26, "tools/call", {
            "name": "pipeline_read", "arguments": {"pipeline": "P90"}}))
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertTrue(payload["found"])
        self.assertIn("P90", payload["text"])

    def test_tools_call_asset_get_content(self):
        """44 内容通道：asset_get 返回资产正文（官方用户自定义 TECH_RULES）。"""
        resp = self.srv.handle(_req(27, "tools/call", {
            "name": "asset_get", "arguments": {"key": "TECH_RULES"}}))
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertTrue(payload["found"])
        self.assertEqual(payload["matches"][0]["package"], "官方")
        self.assertIn("text", payload["matches"][0])

    def test_tools_call_content_unknown_rejected(self):
        """44 内容通道：未知模块/资产 → -32602（参数级拒绝，不泄露）。"""
        resp = self.srv.handle(_req(28, "tools/call", {
            "name": "module_read", "arguments": {"module_id": "M99-X"}}))
        self.assertEqual(resp["error"]["code"], -32602)

    def test_prompts_list_exposes_guide_c7(self):
        resp = self.srv.handle(_req(21, "prompts/list"))
        self.assertEqual(resp["result"]["prompts"][0]["name"], "assemble_guide")

    def test_tools_call_registry_query(self):
        resp = self.srv.handle(_req(22, "tools/call", {
            "name": "registry_query", "arguments": {"query": "M90"}}))
        text = resp["result"]["content"][0]["text"]
        self.assertIn("M90", text)

    def test_tools_call_unknown_tool_rejected(self):
        resp = self.srv.handle(_req(23, "tools/call", {"name": "evil_write"}))
        self.assertEqual(resp["error"]["code"], -32602)

    def test_prompts_get_guide(self):
        resp = self.srv.handle(_req(24, "prompts/get",
                                    {"name": "assemble_guide"}))
        msg = resp["result"]["messages"][0]
        self.assertEqual(msg["role"], "user")
        self.assertIn("装配师", msg["content"]["text"])

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

    def test_serve_stdio_client_disconnect_silent(self):
        """client 断开（stdout BrokenPipeError）→ serve_stdio 静默退出，不 traceback。"""
        from io import StringIO

        class _BrokenStdout(StringIO):
            def write(self, *a, **kw):
                raise BrokenPipeError("Broken pipe")

        out = _BrokenStdout()
        rc = self.srv.serve_stdio(
            stdin=StringIO(json.dumps({"jsonrpc": "2.0", "id": 1,
                                       "method": "ping"}) + "\n"),
            stdout=out)
        self.assertEqual(rc, 0)

    def test_serve_stdio_keyboard_interrupt_silent(self):
        """Ctrl+C（KeyboardInterrupt）→ serve_stdio 静默退出，不 traceback。"""

        class _IntrIn:
            def __init__(self):
                self._sent = False
            def reconfigure(self, *a, **kw):
                pass
            def __iter__(self):
                return self
            def __next__(self):
                if not self._sent:
                    self._sent = True
                    return json.dumps({"jsonrpc": "2.0", "id": 1,
                                       "method": "ping"})
                raise KeyboardInterrupt()

        from io import StringIO
        rc = self.srv.serve_stdio(stdin=_IntrIn(), stdout=StringIO())
        self.assertEqual(rc, 130)

    def test_internal_keyerror_not_masked_as_unknown_uri(self):
        """未来新方法抛 KeyError 不得被 handle 吞成「未知资源 uri」(-32602)。

        白名单拒绝信号须专用化：仅 resources/read 的 C2 拒绝才标 -32602；
        其它内部 KeyError（真实 bug）须走 INTERNAL_ERROR 面而非伪装成
        参数错误。RED 版（修复前）：except KeyError 把任意 KeyError 归为
        -32602，本测试断言应失败。
        """
        from io import StringIO

        class _BoomSrv(McpRuntime):
            def _dispatch(self, method, params):
                if method == "boom":
                    raise KeyError("内部真实 bug：字典缺键")
                return super()._dispatch(method, params)

        srv = _BoomSrv(self.snap)
        out = StringIO()
        srv.serve_stdio(stdin=StringIO(json.dumps(
            {"jsonrpc": "2.0", "id": 9, "method": "boom"}) + "\n"), stdout=out)
        msg = json.loads(out.getvalue().strip())
        self.assertEqual(msg["error"]["code"], -32603)


if __name__ == "__main__":
    unittest.main()
