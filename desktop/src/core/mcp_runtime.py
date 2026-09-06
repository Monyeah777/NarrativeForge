"""MCP Server 运行时（v2.5.0 Wave5 C1：快照烧成服务——静态 mcp.json → stdio JSON-RPC）。

33_v2.2.0_A5-MCP规范差距核查报告 三差距勾销（对照 2025-11-25 schema.ts 实证）：
- G1 形态级：mcp.json 静态定义文件 → 运行时 JSON-RPC 会话协议（stdio transport，
  换行分隔 UTF-8 消息——transport 页实证）；mcp.json 快照降为数据源。
- G2 字段级：resources/list 返回去 text 的 Resource 纯元数据（schema.ts L802 Resource
  无 text）；正文经 resources/read 按 uri 返回 contents[].text（L895 TextResourceContents）。
- G4 归属层：name/version 从快照顶层迁入 initialize 握手 serverInfo（L550 Implementation）——
  快照文件仅作数据源，运行时自述经握手。

C2 最小安全层（Wave5 随 C1）：
- 只读：本运行时只实现 resources 只读面（list/read），无 tools/prompts 写路径——
  未实现方法一律 -32601 METHOD_NOT_FOUND（tools/call 等写请求天然被拒）。
- uri 白名单：resources/read 只接受快照内已登记 uri，未知 uri → -32602 INVALID_PARAMS
  （schema.ts 无 resource-not-found 专用码，参数级拒绝为最小面裁决，不泄露目录结构）。

协议事实（schema.ts 2025-11-25 权威）：
- LATEST_PROTOCOL_VERSION = "2025-11-25"；JSONRPC_VERSION = "2.0"
- initialize 响应：{protocolVersion, capabilities, serverInfo: Implementation}
- notifications/initialized 是通知（无 id）→ 不应答
- ping → EmptyResult（{}）
- 标准错误码：PARSE_ERROR=-32700 / INVALID_REQUEST=-32600 / METHOD_NOT_FOUND=-32601 /
  INVALID_PARAMS=-32602 / INTERNAL_ERROR=-32603

用法：
    snap = load_snapshot("mcp.json")     # 快照 → 运行时数据源
    srv = McpRuntime(snap)
    srv.serve_stdio(sys.stdin, sys.stdout)   # 换行分隔 JSON-RPC 循环
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

#: 协议版本常量（schema.ts L12 实证）
PROTOCOL_VERSION = "2025-11-25"
JSONRPC_VERSION = "2.0"

#: JSON-RPC 标准错误码（schema.ts L173-177 实证）
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def _err(code: int, message: str) -> dict:
    return {"jsonrpc": JSONRPC_VERSION, "id": None, "error": {"code": code,
                                                              "message": message}}


class McpRuntime:
    """快照 → MCP 资源型 server 运行时。

    数据源 = mcp_adapter 产出的 mcp.json 快照（mcp{name, version, resources[]}）。
    内部把 text 从 Resource 元数据剥离，list 与 read 两段式对外。
    """

    def __init__(self, snapshot: Dict[str, Any]):
        mcp = snapshot.get("mcp", snapshot)
        self.server_name = str(mcp.get("name") or "nf-mcp")
        self.server_version = str(mcp.get("version") or "0.1.0")
        #: uri → Resource 元数据（无 text——G2 剥离点）
        self._meta: Dict[str, Dict[str, Any]] = {}
        #: uri → 正文（read 专用，G2 两段式）
        self._text: Dict[str, str] = {}
        for r in mcp.get("resources") or []:
            uri = r.get("uri")
            if not uri:
                continue
            self._meta[uri] = {
                "uri": uri,
                "name": r.get("name") or uri,
                "mimeType": r.get("mimeType") or "text/markdown",
            }
            self._text[uri] = r.get("text") or ""

    # ---- 消息面 ----
    def handle(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理一条入站 JSON-RPC 消息。

        通知（无 id）→ None（不应答）；请求 → 响应 dict。
        """
        if not isinstance(msg, dict):
            return _err(INVALID_REQUEST, "消息必须是 JSON 对象")
        if msg.get("jsonrpc") != JSONRPC_VERSION:
            return _err(INVALID_REQUEST, f"jsonrpc 版本必须为 {JSONRPC_VERSION}")
        method = msg.get("method")
        if not isinstance(method, str):
            return _err(INVALID_REQUEST, "缺 method")
        # 通知：无 id 字段 → 处理但不应答
        is_request = "id" in msg
        rid = msg.get("id")
        params = msg.get("params") or {}

        try:
            result = self._dispatch(method, params)
        except KeyError:
            # uri 白名单外（read）——由 _dispatch 内显式抛，见 _read
            if is_request:
                return {"jsonrpc": JSONRPC_VERSION, "id": rid,
                        "error": {"code": INVALID_PARAMS, "message": "未知资源 uri"}}
            return None
        except ValueError as exc:
            if is_request:
                return {"jsonrpc": JSONRPC_VERSION, "id": rid,
                        "error": {"code": INVALID_PARAMS, "message": str(exc)}}
            return None

        if result is _NOT_IMPLEMENTED:
            if is_request:
                return {"jsonrpc": JSONRPC_VERSION, "id": rid,
                        "error": {"code": METHOD_NOT_FOUND,
                                  "message": f"Method not found: {method}"}}
            return None
        if not is_request:
            return None
        return {"jsonrpc": JSONRPC_VERSION, "id": rid, "result": result}

    def _dispatch(self, method: str, params: dict) -> Any:
        if method == "initialize":
            return self._initialize(params)
        if method == "resources/list":
            return {"resources": list(self._meta.values())}
        if method == "resources/read":
            return self._read(params)
        if method == "ping":
            return {}
        return _NOT_IMPLEMENTED

    # ---- 方法实现 ----
    def _initialize(self, params: dict) -> dict:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"resources": {}},
            "serverInfo": {"name": self.server_name, "version": self.server_version},
        }

    def _read(self, params: dict) -> dict:
        uri = params.get("uri") if isinstance(params, dict) else None
        if not isinstance(uri, str) or uri not in self._text:
            # C2 白名单：未知 uri 拒绝（schema 无 not-found 码，参数级拒绝）
            raise KeyError(uri)
        return {"contents": [{
            "uri": uri,
            "mimeType": self._meta[uri]["mimeType"],
            "text": self._text[uri],
        }]}

    # ---- transport ----
    def serve_stdio(self, stdin: Optional[TextIO] = None,
                    stdout: Optional[TextIO] = None) -> int:
        """stdio transport 主循环：逐行读 stdin → handle → 写 stdout。

        transport 纪律（modelcontextprotocol.io 2025-11-25 transports 页实证）：
        消息以换行分隔、UTF-8、消息内不得含嵌入换行；stdout 只写 MCP 消息；
        stderr 可作日志通道（本实现静默，日志由调用方决定）。
        """
        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout
        # transport 纪律：消息 MUST 为 UTF-8 编码（schema.ts JSONRPCMessage）——
        # Windows 下管道默认按 locale（GBK）解码，须强制 UTF-8，否则含非 ASCII
        # uri 的消息会乱码、命中白名单拒绝。
        for stream in (stdin, stdout):
            reconfigure = getattr(stream, "reconfigure", None)
            if reconfigure is not None:
                try:
                    reconfigure(encoding="utf-8")
                except (ValueError, OSError):
                    pass
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                out = _err(PARSE_ERROR, "Parse error")
                stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
                stdout.flush()
                continue
            try:
                resp = self.handle(msg)
            except Exception as exc:  # 防御：单条消息异常不杀循环
                resp = _err(INTERNAL_ERROR, f"Internal error: {exc}")
            if resp is not None:
                stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                stdout.flush()
        return 0


#: 哨兵：方法存在但本运行时未实现（只读纪律——tools/prompts 一律拒出）
_NOT_IMPLEMENTED = object()


def load_snapshot(path: str) -> Dict[str, Any]:
    """读 mcp.json 静态快照 → 运行时数据源 dict（mcp{name, version, resources[]}）。"""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if "mcp" not in data:
        raise ValueError(f"快照缺 mcp 顶层键（非 mcp.json 产物）：{p}")
    return data


def main(argv: Optional[List[str]] = None) -> int:
    """CLI 入口：python -m core.mcp_runtime <mcp.json>（stdio 服务）。"""
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        print("用法: python -m core.mcp_runtime <mcp.json>  （stdio MCP 服务）",
              file=sys.stderr)
        return 2
    snap = load_snapshot(args[0])
    return McpRuntime(snap).serve_stdio()


if __name__ == "__main__":
    sys.exit(main())
