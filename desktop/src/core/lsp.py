"""最小 LSP 服务器（内部差距实证：仓库无编辑器面——agnix 类工具的 LSP/自动修能力
在 NF 侧为 0 命中；协议本体长在 Markdown 上，编辑器是天然入口）。

范围（刻意最小，够用即止）：
- transport：LSP 标准 `Content-Length` 分帧（与 MCP 的换行分隔不同，互不混用）；
- 能力：full-sync 文档 + 发布诊断 + quickfix code action；
- 诊断源：doc_hygiene 同源判据（autofix.lint_rules）+ 正文 lint（prose_lint，若在场）；
- 修复：codeAction 直接给整文档替换编辑（与 autofix.apply_rules 同源，不另造规则）。

纪律：只读分析 + 只在客户端**显式请求** codeAction 时给编辑；本模块不自行写盘。
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional, TextIO
from urllib.parse import unquote, urlparse

from core import autofix

#: LSP 方法名（只实现本模块承诺的最小面；其余按规范拒/忽略）
M_INITIALIZE = "initialize"
M_INITIALIZED = "initialized"
M_DID_OPEN = "textDocument/didOpen"
M_DID_CHANGE = "textDocument/didChange"
M_DID_SAVE = "textDocument/didSave"
M_CODE_ACTION = "textDocument/codeAction"
M_SHUTDOWN = "shutdown"
M_EXIT = "exit"

SEVERITY_WARNING = 2


def uri_to_path(uri: str) -> str:
    """file:// uri → 本地路径（Windows 盘符与 URL 编码均还原）。"""
    parsed = urlparse(uri)
    path = unquote(parsed.path or "")
    if parsed.netloc:
        path = "//%s%s" % (parsed.netloc, path)
    if len(path) > 2 and path[0] == "/" and path[2] == ":":
        path = path[1:]  # /C:/… → C:/…
    return path.replace("/", os.sep)


def _binary(stream):
    return getattr(stream, "buffer", None) or stream


def write_message(stream, msg: Dict[str, Any]) -> None:
    """LSP 分帧写出（Content-Length 以**字节**计）。"""
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    frame = ("Content-Length: %d\r\n\r\n" % len(data)).encode("ascii") + data
    target = _binary(stream)
    try:
        target.write(frame)
    except TypeError:
        stream.write(frame.decode("utf-8"))
    flush = getattr(target, "flush", None)
    if flush:
        flush()


def read_message(stream) -> Optional[Dict[str, Any]]:
    """读一条 LSP 消息；EOF → None。"""
    src = _binary(stream)
    length = None
    while True:
        line = src.readline()
        if not line:
            return None
        if isinstance(line, bytes):
            line = line.decode("utf-8", "replace")
        line = line.strip()
        if not line:
            break
        if line.lower().startswith("content-length:"):
            try:
                length = int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    if length is None:
        return None
    body = src.read(length)
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def diagnose(path: str, text: str, root: str = ".") -> List[Dict[str, Any]]:
    """文本 → LSP 诊断列表（doc_hygiene 同源 + 正文 lint）。"""
    out: List[Dict[str, Any]] = []
    for item in autofix.lint_rules(path, text, root):
        out.append({
            "range": {"start": {"line": 0, "character": 0},
                      "end": {"line": 0, "character": 0}},
            "severity": SEVERITY_WARNING,
            "source": "nf",
            "code": item["rule"],
            "message": item["message"],
        })
    try:
        from core import prose_lint
        for f in prose_lint.lint_text(text):
            out.append({
                "range": {"start": {"line": max(0, f["line"] - 1), "character": 0},
                          "end": {"line": max(0, f["line"] - 1), "character": 0}},
                "severity": SEVERITY_WARNING,
                "source": "nf-prose",
                "code": f["rule"],
                "message": f["message"],
            })
    except Exception:
        pass
    return out


def _full_range(text: str) -> Dict[str, Any]:
    lines = text.split("\n")
    return {"start": {"line": 0, "character": 0},
            "end": {"line": len(lines) - 1, "character": len(lines[-1])}}


class LspServer:
    """最小 LSP 会话（stdio）。不写盘：编辑只经 codeAction 交客户端。"""

    def __init__(self, root: str = ".", today: str = ""):
        self.root = root
        self.today = today
        self.docs: Dict[str, Dict[str, str]] = {}

    # ---- 消息面 ----
    def handle(self, msg: Dict[str, Any]) -> List[Dict[str, Any]]:
        method = msg.get("method")
        params = msg.get("params") or {}
        rid = msg.get("id")
        out: List[Dict[str, Any]] = []

        def reply(result):
            out.append({"jsonrpc": "2.0", "id": rid, "result": result})

        if method == M_INITIALIZE:
            reply({
                "capabilities": {
                    "textDocumentSync": 1,          # full sync
                    "codeActionProvider": True,
                },
                "serverInfo": {"name": "nf-lsp", "version": "1.0.0"},
            })
        elif method == M_INITIALIZED:
            pass
        elif method == M_DID_OPEN:
            doc = params.get("textDocument") or {}
            uri, text = doc.get("uri", ""), doc.get("text", "")
            self.docs[uri] = {"path": uri_to_path(uri), "text": text}
            out.append(self._publish(uri))
        elif method == M_DID_CHANGE:
            doc = params.get("textDocument") or {}
            uri = doc.get("uri", "")
            changes = params.get("contentChanges") or []
            if uri in self.docs and changes:
                self.docs[uri]["text"] = changes[-1].get("text", "")
                out.append(self._publish(uri))
        elif method == M_DID_SAVE:
            doc = params.get("textDocument") or {}
            uri = doc.get("uri", "")
            if uri in self.docs:
                out.append(self._publish(uri))
        elif method == M_CODE_ACTION:
            doc = params.get("textDocument") or {}
            uri = doc.get("uri", "")
            diags = params.get("context", {}).get("diagnostics") or []
            actions = self._actions(uri, diags)
            reply(actions)
        elif method == M_SHUTDOWN:
            reply(None)
        elif method == M_EXIT:
            pass
        elif rid is not None:
            out.append({"jsonrpc": "2.0", "id": rid,
                        "error": {"code": -32601,
                                  "message": "Method not found: %s" % method}})
        return out

    def _publish(self, uri: str) -> Dict[str, Any]:
        doc = self.docs.get(uri) or {"path": uri_to_path(uri), "text": ""}
        diags = diagnose(doc["path"], doc["text"], self.root)
        return {"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics",
                "params": {"uri": uri, "diagnostics": diags}}

    def _actions(self, uri: str, diags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        doc = self.docs.get(uri)
        if not doc:
            return []
        rules = sorted({d.get("code") for d in diags
                        if d.get("code") in autofix.RULES})
        if not rules:
            return []
        after = autofix.apply_rules(doc["text"], rules, self.today)
        if after == doc["text"]:
            return []
        return [{
            "title": "NF：机械修复（%s）" % "、".join(rules),
            "kind": "quickfix",
            "diagnostics": [d for d in diags if d.get("code") in rules],
            "edit": {"changes": {uri: [{"range": _full_range(doc["text"]),
                                        "newText": after}]}},
        }]

    # ---- transport ----
    def serve(self, stdin: Optional[TextIO] = None,
              stdout: Optional[TextIO] = None) -> int:
        stdin = stdin if stdin is not None else sys.stdin
        stdout = stdout if stdout is not None else sys.stdout
        while True:
            msg = read_message(stdin)
            if msg is None:
                return 0
            if msg.get("method") == M_EXIT:
                return 0
            try:
                for resp in self.handle(msg):
                    write_message(stdout, resp)
            except Exception as exc:  # 单条异常不杀会话
                if "id" in msg:
                    write_message(stdout, {"jsonrpc": "2.0", "id": msg["id"],
                                           "error": {"code": -32603,
                                                     "message": str(exc)}})


def main(argv: Optional[List[str]] = None) -> int:
    args = list(argv) if argv is not None else sys.argv[1:]
    root = args[0] if args else "."
    return LspServer(root=root).serve()
