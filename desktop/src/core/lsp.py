"""NF LSP 服务器（编辑器接管面：诊断 / 补全 / 悬停 / 跳定义 / 大纲 / quickfix）。

内部差距实证（2026-10-07 审计）：本模块此前只有「full-sync 诊断 + quickfix」——
- 诊断位置恒为 `(0,0)`（autofix 规则）或零宽（正文 lint），**编辑器无法定位到正文**；
- 没有 didClose（长驻会话状态泄漏、旧诊断不清）；initialize 忽略 rootUri / capabilities；
- 没有 NF 领域智能（模块 id / 资产键 / 事件名 / 层位 id / 管线 id 的补全、悬停、跳定义）；
- 未 shutdown 直接 exit 也回 0（LSP 规范要求 1）；
- 编辑器装配面为零：没有任何生成好的客户端配置，使用者要照文档手抄。
于是「IDE 集成」在门禁里只剩一个布尔（check33 旧第 5 面只断言 codeActionProvider 为真）。

本版把编辑器面做成**可机检的协议行为**：
1. 传输：LSP 标准 `Content-Length` 分帧（与 MCP 的换行分隔不同，互不混用），坏帧不杀会话；
2. 能力：full-sync（openClose + save）、诊断、quickfix、补全、悬停、跳定义、文档大纲、
   工作区符号；`positionEncoding` 按客户端能力协商（默认 utf-16，位置一律按 UTF-16 码元折算）；
3. 领域智能：符号表单一真相来自 `core/nf_language`（不另造标准）；
4. 装配：`render_client_config()` 生成 Neovim / Emacs(eglot) / Helix 的现成配置
   （`nf lsp --print-config <editor>`）——**只覆盖内置 LSP 客户端的编辑器**；VS Code 类
   需要扩展宿主，本仓无编辑器可装载验证，按诚实标注留给使用者，不假称已适配（见 docs/lsp.md）。

纪律：只读分析 + 只在客户端**显式请求** codeAction 时给编辑；本模块不自行写盘。
"""
from __future__ import annotations

import io
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO, Tuple
from urllib.parse import quote, unquote, urlparse

from core import autofix
from core import nf_language
from core.lsp_client import CLIENT_EDITORS, render_client_config
#: 索引签名复查的 TTL（秒）：同一窗口内复用索引，避免每请求都逐件 stat（实测 119.5 ms/次）
INDEX_TTL_S = 1.0

#: 传输分帧（线格式）独立成 core/lsp_framing.py；这里只做转口，调用方口径不变
from core.lsp_framing import BAD_FRAME, read_message, write_message   # noqa: E402
from core.lsp_params import (INVALID_PARAMS, INVALID_REQUEST, SERVER_NOT_INITIALIZED,
                             advise_request, did_change_text, did_open_payload,
                             lifecycle_problem)

#: LSP 方法名（只实现本模块承诺的面；其余按规范拒/忽略）
M_INITIALIZE = "initialize"
M_INITIALIZED = "initialized"
M_DID_OPEN = "textDocument/didOpen"
M_DID_CHANGE = "textDocument/didChange"
M_DID_SAVE = "textDocument/didSave"
M_DID_CLOSE = "textDocument/didClose"
M_COMPLETION = "textDocument/completion"
M_HOVER = "textDocument/hover"
M_DEFINITION = "textDocument/definition"
M_DOCUMENT_SYMBOL = "textDocument/documentSymbol"
M_WORKSPACE_SYMBOL = "workspace/symbol"
M_REFERENCES = "textDocument/references"
M_FOLDING_RANGE = "textDocument/foldingRange"
M_CODE_ACTION = "textDocument/codeAction"
M_SHUTDOWN = "shutdown"
M_EXIT = "exit"

#: 服务端自述（唯一真相 = 这两个常量；接入面卡 `integrations/lsp/integration.json` 的
#: version 必须与 SERVER_VERSION 一致，由 test_lsp 判据对账——两处各写一遍就会静默漂）。
METHOD_NOT_FOUND = -32601
SERVER_NAME = "nf-lsp"
SERVER_VERSION = "2.7.0"

#: 领域符号种类 → LSP CompletionItemKind / SymbolKind（协议常量，不引入 LSP 依赖）
COMPLETION_KIND = {"module": 9, "asset": 6, "event": 23, "layer": 7, "pipeline": 3}
#: check33 编辑器面判据要求的 initialize 能力键（缺一即红）
_REQUIRED_CAPS = ("positionEncoding", "textDocumentSync", "hoverProvider", "completionProvider",
                  "definitionProvider", "documentSymbolProvider", "workspaceSymbolProvider",
                  "referencesProvider", "foldingRangeProvider", "codeActionProvider")
_FENCE = re.compile(r"^```")
_URI_SAFE = "/:@"

# 注：SEVERITY_WARNING / SYMBOL_KIND / HEADING / WORD 随文档级能力迁到 core/lsp_doc.py——
# 这里不再各留一份（死代码判据 2026-10-08 抓到四处零引用常量，正是「拆完没清场」的痕迹）。

def uri_to_path(uri: str) -> str:
    """file:// uri → 本地路径（Windows 盘符与 URL 编码均还原）。"""
    parsed = urlparse(uri)
    path = unquote(parsed.path or "")
    if parsed.netloc:
        path = "//%s%s" % (parsed.netloc, path)
    if len(path) > 2 and path[0] == "/" and path[2] == ":":
        path = path[1:]  # /C:/… → C:/…
    return path.replace("/", os.sep)


def path_to_uri(path: str) -> str:
    """本地路径 → file:// uri（盘符与空格/CJK 逐段百分号编码，与客户端回传形态对称）。"""
    p = os.path.abspath(path).replace(os.sep, "/")
    if len(p) > 1 and p[1] == ":":
        p = "/" + p
    return "file://" + quote(p, safe=_URI_SAFE)


from core.lsp_doc import (diagnose, folding_ranges, outline,  # noqa: E402
                           prefix_before, text_edits, u16_col, word_span)

def _error(rid: Any, code: int, message: str) -> Dict[str, Any]:
    """JSON-RPC 错误应答（三种入站拒绝共用一处形状）。"""
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


class LspServer:
    """NF LSP 会话（stdio）。不写盘：编辑只经 codeAction 交客户端。"""

    def __init__(self, root: str = ".", today: str = "", explicit_root: bool = False):
        self.root = os.path.abspath(root or ".")
        self.today = today
        self.explicit_root = explicit_root
        self.docs: Dict[str, Dict[str, str]] = {}
        self.client_caps: Dict[str, Any] = {}
        self.shutting_down = False
        self.initialized = False
        self._index: Optional[nf_language.SymbolIndex] = None
        self._sig_at = 0.0

    # ---- 索引：惰性 + 面孔径签名失效（长驻会话不需要重启就能看到新件）
    def invalidate(self) -> None:
        """强制下一次取索引时重扫签名（客户端**显式**告知仓库件变了的场合用，如 didSave）。"""
        self._sig_at = 0.0

    def symbols(self) -> nf_language.SymbolIndex:
        """NF 符号表（TTL 内复用；过期即重算签名，变了才重建）。

        为什么要有 TTL（2026-10-08 本机实测）：签名要对**全部扫描面**（731 件）逐件 stat，
        实测 **119.5 ms/次**——而补全/悬停/跳定义每个请求都要取一次索引，实测补全 158 ms/请求。
        编辑器里那就是「每敲一个字卡一下」。加 TTL 后同一窗口内复用：索引刷新最多滞后一个
        TTL，而 didSave（磁盘件真变了）会 invalidate() 强制下次重扫——**正确性不降**，
        只是把「每次请求都问一遍仓库变没变」换成「每 TTL 问一遍」。
        """
        now = time.monotonic()
        if self._index is not None and (now - self._sig_at) < INDEX_TTL_S:
            return self._index
        sig = nf_language.signature(self.root)
        self._sig_at = now
        if self._index is None or self._index.sig != sig:
            self._index = nf_language.build(self.root, sig)   # 复用刚扫的签名，不再扫第二遍
        return self._index

    def _text_of(self, uri: str) -> str:
        doc = self.docs.get(uri)
        if doc:
            return doc.get("text", "")
        path = uri_to_path(uri)
        try:
            with open(path, encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return ""

    def _rel(self, path: str) -> str:
        try:
            return os.path.relpath(os.path.abspath(path), self.root).replace("\\", "/")
        except ValueError:                     # 跨盘符（Windows）——退化为绝对路径，不裸崩
            return path.replace("\\", "/")

    def _publish(self, uri: str, clear: bool = False) -> Dict[str, Any]:
        path = (self.docs.get(uri) or {}).get("path") or uri_to_path(uri)
        text = "" if clear else self._text_of(uri)
        diags = [] if clear else diagnose(self._rel(path), text, self.root)
        return {"jsonrpc": "2.0", "method": "textDocument/publishDiagnostics",
                "params": {"uri": uri, "diagnostics": diags}}

    def _hierarchical(self) -> bool:
        ds = ((self.client_caps.get("textDocument") or {}).get("documentSymbol") or {})
        return bool(ds.get("hierarchicalDocumentSymbolSupport"))

    # ---- 各类请求
    def _line_at(self, uri: str, line_no: int) -> Tuple[List[str], int, str]:
        """文档行快照 → (全部行, 收敛后行号, 该行正文)；行号越界收敛到文末那一行。"""
        lines = self._text_of(uri).split("\n")
        ln = min(max(0, line_no), max(0, len(lines) - 1))
        return lines, ln, (lines[ln] if lines else "")

    def _completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        uri = (params.get("textDocument") or {}).get("uri", "")
        pos = params.get("position") or {}
        _lines, _ln, line = self._line_at(uri, int(pos.get("line", 0) or 0))
        prefix = prefix_before(line, int(pos.get("character", 0) or 0))
        items = []
        for sym in self.symbols().complete(prefix):
            items.append({"label": sym["name"], "kind": COMPLETION_KIND.get(sym["kind"], 1),
                          "detail": sym["detail"], "documentation": {"kind": "markdown",
                                                                     "value": sym["doc"]},
                          "sortText": "%d_%s" % (nf_language.KINDS.index(sym["kind"]), sym["name"])})
        return {"isIncomplete": False, "items": items}

    def _hover(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        uri = (params.get("textDocument") or {}).get("uri", "")
        pos = params.get("position") or {}
        lines, ln, cur = self._line_at(uri, int(pos.get("line", 0) or 0))
        tok, start, end = word_span(cur, int(pos.get("character", 0) or 0))
        hits = self.symbols().resolve_all(tok) if tok else []
        if not hits:
            return None
        blocks = []
        for sym in hits:
            blocks.append("**%s**（%s）\n\n%s\n\n定义：`%s`" % (
                sym["name"], sym["kind"], sym["doc"], sym["path"]))
        if len(hits) > 1:
            blocks.insert(0, "> 有 %d 个同名符号（歧义：跳定义按失败关闭处理）" % len(hits))
        return {"contents": {"kind": "markdown", "value": "\n\n---\n\n".join(blocks)},
                "range": {"start": {"line": ln, "character": u16_col(lines[ln], start)},
                          "end": {"line": ln, "character": u16_col(lines[ln], end)}}}

    def _definition(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        uri = (params.get("textDocument") or {}).get("uri", "")
        pos = params.get("position") or {}
        _lines, _ln, cur = self._line_at(uri, int(pos.get("line", 0) or 0))
        tok, _s, _e = word_span(cur, int(pos.get("character", 0) or 0))
        sym = self.symbols().resolve(tok) if tok else None
        if not sym:
            return None
        target = os.path.join(self.root, sym["path"])
        tl = int(sym.get("line", 0) or 0)
        return {"uri": path_to_uri(target),
                "range": {"start": {"line": tl, "character": 0}, "end": {"line": tl, "character": 0}}}

    def _document_symbols(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        uri = (params.get("textDocument") or {}).get("uri", "")
        tree = outline(self._text_of(uri))
        if self._hierarchical():
            return tree
        flat: List[Dict[str, Any]] = []

        def walk(nodes):
            for n in nodes:
                flat.append({"name": n["name"], "kind": n["kind"], "location": {"uri": uri,
                                                                                "range": n["range"]}})
                walk(n.get("children") or [])
        walk(tree)
        return flat

    def _workspace_symbols(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        q = str(params.get("query") or "")
        out = []
        for sym in self.symbols().all_symbols():
            if q and q not in sym["name"] and not any(q in a for a in sym.get("aliases") or []):
                continue
            out.append({"name": sym["name"], "kind": COMPLETION_KIND.get(sym["kind"], 1),
                        "containerName": sym["kind"],
                        "location": {"uri": path_to_uri(os.path.join(self.root, sym["path"])),
                                     "range": {"start": {"line": int(sym.get("line") or 0),
                                                         "character": 0},
                                               "end": {"line": int(sym.get("line") or 0),
                                                       "character": 0}}}})
        return out[:500]

    def _references(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """结构化引用 → LSP Location[]（**只认登记关系**；未登记即空表，失败关闭）。

        为什么值得单列（2026-10-08）：NF 的引用是**有登记的**（事件 ↔ 发布/订阅模块、模块 ↔
        挂载层、管线 ← 域包采用），编辑器里「谁引用了这个事件」因此能给出**可解释**的位置；
        若改成全文搜索，只会喷出同名噪声——本仓对「不猜」有明确纪律（同 hover 的歧义口径）。
        `context.includeDeclaration=false` 时去掉与符号自身定义同位置的那条（规范语义）。
        """
        uri = (params.get("textDocument") or {}).get("uri", "")
        pos = params.get("position") or {}
        _lines, _ln, cur = self._line_at(uri, int(pos.get("line", 0) or 0))
        tok, _s, _e = word_span(cur, int(pos.get("character", 0) or 0))
        if not tok:
            return []
        include_decl = bool((params.get("context") or {}).get("includeDeclaration", True))
        decl = self.symbols().resolve(tok)
        decl_key = (decl["path"], int(decl.get("line") or 0)) if decl else None
        out = []
        for ref in self.symbols().references(tok):
            if not include_decl and (ref["path"], int(ref["line"])) == decl_key:
                continue
            out.append({"uri": path_to_uri(os.path.join(self.root, ref["path"])),
                        "range": {"start": {"line": int(ref["line"]), "character": 0},
                                  "end": {"line": int(ref["line"]), "character": 0}}})
        return out

    def _folding_ranges(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """折叠区间（标题小节 + 代码围栏）——派生自与大纲同一份标题口径，不新造事实。"""
        uri = (params.get("textDocument") or {}).get("uri", "")
        return folding_ranges(self._text_of(uri))

    def _code_actions(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        uri = (params.get("textDocument") or {}).get("uri", "")
        only = ((params.get("context") or {}).get("only") or [])
        if only and "quickfix" not in only:
            return []
        diags = (params.get("context") or {}).get("diagnostics") or []
        rules = sorted({str(d.get("code")) for d in diags if d.get("code") in autofix.RULES})
        if not rules:
            return []
        before = self._text_of(uri)
        after = autofix.apply_rules(before, rules, self.today)
        if after == before:
            return []
        return [{
            "title": "NF：机械修复（%s）" % "、".join(rules),
            "kind": "quickfix",
            "isPreferred": True,
            "diagnostics": [d for d in diags if d.get("code") in rules],
            "edit": {"changes": {uri: text_edits(before, after)}},
        }]

    # ---- 消息面
    # ---- 消息面
    def handle(self, msg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """单条消息 → 待发消息列表（表驱动分派；通知/请求分开走，便于各自收敛）。"""
        method = msg.get("method")
        params = msg.get("params") or {}
        rid = msg.get("id")
        problem = lifecycle_problem(method, rid, self.shutting_down, self.initialized)
        if problem:
            return [_error(rid, problem[0], problem[1])]
        if method == M_INITIALIZE:
            return [self._handshake(rid, params)]
        if method in (M_INITIALIZED, M_EXIT):
            return []                      # 规范：initialized 通知忽略；exit 由 serve 循环收口
        if (method or "").startswith("$/"):
            # 规范（$/ 请求与通知）：**通知**可忽略；**请求**必须回 MethodNotFound——
            # 静默不回会让合规客户端一直等应答（2026-10-08 实测：旧实现两种都吞掉）。
            if rid is None:
                return []
            return [_error(rid, METHOD_NOT_FOUND, "Method not found: %s" % method)]
        if not self.initialized:
            # 未握手前的**通知**一律不做（请求已在状态机处回 -32002）：根还没采纳，照做只会
            # 用 CLI 默认根产出「看起来对」的诊断与索引状态。
            return []
        note = self._notification(method, params)
        if note is not None:
            return note
        if method == M_SHUTDOWN:
            self.shutting_down = True
            if rid is None:                    # 通知形态的 shutdown：记状态但不回应答
                return []
            return [{"jsonrpc": "2.0", "id": rid, "result": None}]
        return self._dispatch_request(method, params, rid)

    def _dispatch_request(self, method: Any, params: Dict[str, Any],
                          rid: Any) -> List[Dict[str, Any]]:
        """请求分派：参数准入 → 处理器；未知方法回 -32601、参数不合回 -32602。"""
        handler = _REQUESTS.get(method)
        if rid is None:
            # 无 id = **通知**：JSON-RPC 2.0 §4.1 禁止应答。2026-10-08 实测：旧实现对
            # 「请求方法当通知发」会回一条 id=null 的应答——客户端会收到不请自来的响应
            # （同族口径在 MCP 面是对的，两轴判据 test_two_faces_jsonrpc 把它抓了出来）。
            return []
        if handler is None:
            return [_error(rid, METHOD_NOT_FOUND, "Method not found: %s" % method)]
        problem = advise_request(method, params)
        if problem:
            return [_error(rid, INVALID_PARAMS, problem)]
        return [{"jsonrpc": "2.0", "id": rid, "result": handler(self, params)}]

    def _handshake(self, rid: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """initialize 应答（能力清单 + 服务端自述）；成功后会话才算建立。"""
        self._on_initialize(params)
        self.initialized = True
        return {"jsonrpc": "2.0", "id": rid,
                "result": {"capabilities": self.capabilities(),
                           "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}}}

    def _notification(self, method: Any, params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """文档生命周期通知 → 待发消息；**非通知返回 None**（交由请求分派）。"""
        if method not in (M_DID_OPEN, M_DID_CHANGE, M_DID_SAVE, M_DID_CLOSE):
            return None
        if method == M_DID_SAVE:
            # 磁盘件可能刚被改：下次取索引强制重扫签名（放在 docs 守卫之前——没跟踪的文档
            # 也可能是仓库件，保存事实本身就足以让缓存失效）。
            self.invalidate()
        uri = (params.get("textDocument") or {}).get("uri", "")
        if method == M_DID_OPEN:
            payload = did_open_payload(params)          # 不合形即丢弃（详见 core/lsp_params）
            if payload is None:
                return []
            self.docs[payload[0]] = {"path": uri_to_path(payload[0]), "text": payload[1]}
            return [self._publish(payload[0])]
        if method == M_DID_CLOSE:
            self.docs.pop(uri, None)
            return [self._publish(uri, clear=True)]
        if uri not in self.docs:
            return []
        if method == M_DID_CHANGE:
            text = did_change_text(params)               # 同上：坏帧不进状态
            if text is None:
                return []
            self.docs[uri]["text"] = text
        return [self._publish(uri)]

    def _on_initialize(self, params: Dict[str, Any]) -> None:
        self.client_caps = params.get("capabilities") or {}
        if self.explicit_root:
            return
        root = params.get("rootUri")
        if not root:
            folders = params.get("workspaceFolders") or []
            root = (folders[0] or {}).get("uri") if folders else ""
        if not root:
            root = params.get("rootPath")
        if root:
            self.root = os.path.abspath(uri_to_path(str(root)) if str(root).startswith("file:")
                                        else str(root))

    def capabilities(self) -> Dict[str, Any]:
        """服务端能力（`positionEncoding` 固定 utf-16——LSP 规范要求客户端必须支持）。"""
        return {
            "positionEncoding": "utf-16",
            "textDocumentSync": {"openClose": True, "change": 1, "save": True},
            "hoverProvider": True,
            "completionProvider": {"triggerCharacters": [":", "`", "\"", "'", "{", "[", " "],
                                   "resolveProvider": False},
            "definitionProvider": True,
            "documentSymbolProvider": True,
            "workspaceSymbolProvider": True,
            "referencesProvider": True,
            "foldingRangeProvider": True,
            "codeActionProvider": {"codeActionKinds": ["quickfix"]},
        }

    # ---- transport
    def serve(self, stdin: Optional[TextIO] = None,
              stdout: Optional[TextIO] = None) -> int:
        """stdio 主循环；返回进程退出码（规范：未收 shutdown 就 exit ⇒ 1）。"""
        stdin = stdin if stdin is not None else sys.stdin
        stdout = stdout if stdout is not None else sys.stdout
        while True:
            msg = read_message(stdin)
            if msg is None:
                return 0          # 传输关闭（EOF）：按旧行为正常收摊；退出码约束只针对 exit 通知
            if msg is BAD_FRAME:
                # 坏帧不杀会话：回 -32700（id 不可判定 ⇒ null）后继续读下一帧。
                write_message(stdout, {
                    "jsonrpc": "2.0", "id": None,
                    "error": {"code": -32700,
                              "message": "Parse error（非法 UTF-8 / 非法 JSON / 坏 Content-Length；"
                                         "修复指引：Content-Length 以**字节**计，正文为 UTF-8 JSON）"}})
                continue
            if not isinstance(msg, dict):
                # JSON-RPC 2.0：消息须为对象（本实现不支持批量数组）→ -32600 后继续。
                write_message(stdout, {
                    "jsonrpc": "2.0", "id": None,
                    "error": {"code": -32600,
                              "message": "Invalid Request（消息须为 JSON 对象；"
                                         "修复指引：勿发数组/标量，本服务不支持批量请求）"}})
                continue
            if msg.get("method") == M_EXIT:
                return 0 if self.shutting_down else 1
            try:
                for resp in self.handle(msg):
                    write_message(stdout, resp)
            except Exception as exc:  # 单条异常不杀会话
                if "id" in msg:
                    write_message(stdout, {"jsonrpc": "2.0", "id": msg["id"],
                                           "error": {"code": -32603,
                                                     "message": str(exc)}})


#: 请求方法 → 处理器（表驱动分派：避免 handle 的线性分支把圈复杂度推过高限）
_REQUESTS: Dict[str, Any] = {
    M_COMPLETION: lambda s, p: s._completion(p),
    M_HOVER: lambda s, p: s._hover(p),
    M_DEFINITION: lambda s, p: s._definition(p),
    M_DOCUMENT_SYMBOL: lambda s, p: s._document_symbols(p),
    M_WORKSPACE_SYMBOL: lambda s, p: s._workspace_symbols(p),
    M_REFERENCES: lambda s, p: s._references(p),
    M_FOLDING_RANGE: lambda s, p: s._folding_ranges(p),
    M_CODE_ACTION: lambda s, p: s._code_actions(p),
}


def _check_capabilities(srv: "LspServer", init: Dict[str, Any]) -> List[str]:
    """initialize 能力声明：编辑器面要用的能力必须齐备且口径正确。

    `init` = 握手应答（由 check() 送**一次** initialize 得到；本函数不再自己发包——
    2026-10-08 补状态机后，重复 initialize 会正确地回 -32600）。
    """
    issues: List[str] = []
    caps = init["capabilities"]
    for key in _REQUIRED_CAPS:
        if key not in caps:
            issues.append("initialize 能力缺 " + key)
    if caps.get("positionEncoding") != "utf-16":
        issues.append("positionEncoding 应为 utf-16（LSP 默认口径，客户端必须支持）")
    if not (caps.get("codeActionProvider") or {}).get("codeActionKinds"):
        issues.append("codeActionProvider 未声明 codeActionKinds")
    server = init["serverInfo"]
    if server.get("name") != SERVER_NAME or server.get("version") != SERVER_VERSION:
        issues.append("serverInfo 与 SERVER_NAME/SERVER_VERSION 不一致：%s" % server)
    return issues


def _check_lifecycle(srv: "LspServer", probe: str, root_s: str) -> List[str]:
    """诊断定位 / didClose 清理 / 未 shutdown 的 exit 退出码。"""
    issues: List[str] = []
    srv.handle({"jsonrpc": "2.0", "method": M_DID_OPEN,
                "params": {"textDocument": {"uri": probe, "text": "# 标题  \n\n正文  \n"}}})
    diags = srv._publish(probe)["params"]["diagnostics"]
    if not diags:
        issues.append("已知坏文档零诊断（诊断源与 nf lint 失同源？）")
    elif all(d["range"]["start"]["character"] == 0 for d in diags):
        issues.append("诊断位置全为列 0——编辑器无法定位到正文")
    srv.handle({"jsonrpc": "2.0", "method": M_DID_CLOSE,
                "params": {"textDocument": {"uri": probe}}})
    if probe in srv.docs:
        issues.append("didClose 未清理文档状态（长驻会话状态泄漏）")
    # 协议状态机（2026-10-08 补）：未初始化就发请求 / 重复 initialize / shutdown 后再发请求
    fresh = LspServer(root=root_s, explicit_root=True)
    pre = fresh.handle({"jsonrpc": "2.0", "id": 90, "method": M_COMPLETION,
                        "params": {"textDocument": {"uri": probe}}})[0]
    if (pre.get("error") or {}).get("code") != SERVER_NOT_INITIALIZED:
        issues.append("未 initialize 就发请求未回 -32002（协议状态机）")
    fresh.handle({"jsonrpc": "2.0", "id": 91, "method": M_INITIALIZE, "params": {}})
    again = fresh.handle({"jsonrpc": "2.0", "id": 92, "method": M_INITIALIZE, "params": {}})[0]
    if (again.get("error") or {}).get("code") != INVALID_REQUEST:
        issues.append("重复 initialize 未回 -32600（协议：一个会话只允许一次）")
    fresh.handle({"jsonrpc": "2.0", "id": 93, "method": M_SHUTDOWN, "params": {}})
    after = fresh.handle({"jsonrpc": "2.0", "id": 94, "method": M_COMPLETION,
                          "params": {"textDocument": {"uri": probe}}})[0]
    if (after.get("error") or {}).get("code") != INVALID_REQUEST:
        issues.append("shutdown 之后仍服务请求（未回 -32600）")
    buf = io.BytesIO()
    write_message(buf, {"jsonrpc": "2.0", "method": M_EXIT})
    if LspServer(root=root_s).serve(stdin=io.BytesIO(buf.getvalue()),
                                    stdout=io.BytesIO()) != 1:
        issues.append("未 shutdown 直接 exit 应返回 1（LSP 规范）")
    return issues


def _references_issues(srv: "LspServer", probe: str) -> List[str]:
    """引用面体检：**登记关系**（事件 ↔ 发布/订阅模块）必须给出可解释的位置。"""
    srv.handle({"jsonrpc": "2.0", "method": M_DID_OPEN,
                "params": {"textDocument": {"uri": probe, "text": "# 探针\n事件 narrative_event\n"}}})
    out = srv.handle({"jsonrpc": "2.0", "id": 70, "method": M_REFERENCES,
                      "params": {"textDocument": {"uri": probe},
                                 "position": {"line": 1, "character": 4}}})[0]
    locs = out.get("result") or []
    if not locs:
        return ["引用面为空：事件 narrative_event 的登记引用（发布/订阅）未给出位置"]
    if not all(str(x.get("uri") or "").startswith("file:") for x in locs):
        return ["引用面给了非 file: 的 uri（编辑器打不开）"]
    return []


def _folding_issues(srv: "LspServer", probe: str) -> List[str]:
    """折叠面体检：多标题文档必须给出 ≥2 条区间，且不得出现空跨（客户端会忽略）。

    为什么值得进闸门（2026-10-08）：折叠是「长档可用性」的地基（02_联动注册表.md 1151 行），
    而它的实现直接依赖标题口径——口径一变（例如把围栏内 # 当标题）折叠就会碎成噪声。
    """
    srv.handle({"jsonrpc": "2.0", "method": M_DID_OPEN,
                "params": {"textDocument": {"uri": probe,
                                            "text": "# 一级\n\n正文\n\n## 二级\n\n正文\n"}}})
    ranges = srv.handle({"jsonrpc": "2.0", "id": 71, "method": M_FOLDING_RANGE,
                         "params": {"textDocument": {"uri": probe}}})[0].get("result") or []
    if len(ranges) < 2:
        return ["折叠面区间过少（多标题文档应给出 ≥2 条）：%s" % ranges]
    if any(int(r.get("endLine") or 0) <= int(r.get("startLine") or 0) for r in ranges):
        return ["折叠区间出现空跨（endLine ≤ startLine）：%s" % ranges]
    return []


def _client_config_issues(r: Path) -> List[str]:
    """客户端配置体检：生成件必须指向 nf lsp 入口，且 **Helix 那份要能当 TOML 解析**。

    为什么加解析（2026-10-08）：此前只查子串——生成器若把 Windows 路径写成非法 TOML
    （反斜杠留在基本字符串里），子串判据全绿，用户粘进 languages.toml 才炸。
    """
    import tomllib
    out = []
    for editor in CLIENT_EDITORS:
        cfg = render_client_config(editor, str(r.resolve()))
        if "scripts/nf.py" not in cfg or '"lsp"' not in cfg:
            out.append("客户端配置 %s 未指向 nf lsp 入口" % editor)
        if editor != "helix":
            continue
        try:
            data = tomllib.loads("\n".join(cfg.split("\n")[1:]))
        except tomllib.TOMLDecodeError as exc:
            out.append("Helix 配置不是合法 TOML：%s" % exc)
            continue
        srv_cfg = ((data.get("language-server") or {}).get("nf-lsp") or {})
        if srv_cfg.get("command") != "python" or "lsp" not in (srv_cfg.get("args") or []):
            out.append("Helix 配置的 language-server 段结构不对：%s" % srv_cfg)
    return out


def _check_intelligence(srv: "LspServer", probe: str, r: Path) -> List[str]:
    """领域解析（真仓库件）+ 补全 / 悬停 / 跳定义 / 大纲真跑 + 客户端配置生成。"""
    issues: List[str] = []
    sym = srv.symbols().resolve("M00")
    if sym is None or not (r / sym["path"]).is_file():
        issues.append("模块 M00 未解析到真实模块件（符号表与仓库失同步）")
    srv.handle({"jsonrpc": "2.0", "method": M_DID_OPEN,
                "params": {"textDocument": {"uri": probe, "text": "# 模块 M00\n"}}})
    pos = {"line": 0, "character": 6}
    doc = {"textDocument": {"uri": probe}, "position": pos}
    comp = srv.handle({"jsonrpc": "2.0", "id": 3, "method": M_COMPLETION,
                       "params": doc})[0]["result"]["items"]
    if not any(i["label"] == "M00" for i in comp):
        issues.append("补全未给模块 M00")
    hov = srv.handle({"jsonrpc": "2.0", "id": 4, "method": M_HOVER,
                      "params": doc})[0]["result"]
    if not hov or "模块 M00" not in hov["contents"]["value"]:
        issues.append("悬停未给模块元数据")
    defn = srv.handle({"jsonrpc": "2.0", "id": 5, "method": M_DEFINITION,
                       "params": doc})[0]["result"]
    if not defn or "M00_" not in unquote(defn["uri"]):
        issues.append("跳定义未指向模块件")
    outl = srv.handle({"jsonrpc": "2.0", "id": 6, "method": M_DOCUMENT_SYMBOL,
                       "params": {"textDocument": {"uri": probe}}})[0]["result"]
    if not outl:
        issues.append("文档大纲为空")
    issues += _client_config_issues(r)
    issues += _references_issues(srv, probe)
    issues += _folding_issues(srv, probe)
    # 参数准入（2026-10-08 补）：非法参数必须回 -32602，而不是冒成 -32603 内部错误。
    bad = srv.handle({"jsonrpc": "2.0", "id": 8, "method": M_HOVER,
                      "params": {"textDocument": {"uri": probe},
                                 "position": {"line": "a", "character": 0}}})[0]
    if (bad.get("error") or {}).get("code") != INVALID_PARAMS:
        issues.append("参数准入失效：非法 position 未回 -32602（实得 %s）" % (bad.get("error"),))
    return issues


def check(root: str = ".") -> Tuple[List[str], Dict[str, Any]]:
    """编辑器面机检（check33 子扫描口径）：把「IDE 集成」从布尔升成协议行为判据。

    内部差距实证：旧 check33 第 5 面只断言 'codeActionProvider' 为真，而门禁自述写着
    「编辑器面」——声明与实测不符。本判据真跑一遍协议行为：能力声明齐备 / 诊断带真实
    位置 / didClose 清理 / 未 shutdown 的 exit 退出码 / 领域解析（真仓库件）/ 补全·悬停·
    跳定义·大纲 / 三种编辑器配置可生成。缺根或不可用如实报 issue，不裸崩。
    """
    r = Path(root)
    if not (r / "verify.sh").is_file():
        return (["读不到仓库根（缺 verify.sh）——编辑器面判据须在 NF 仓库根运行"], {})
    srv = LspServer(root=str(r.resolve()), explicit_root=True)
    probe = path_to_uri(str(r / "editor_face_probe.md"))
    # 握手一次（真实客户端序列；后续请求面都依赖它——协议状态机要求先 initialize）
    init = srv.handle({"jsonrpc": "2.0", "id": 1, "method": M_INITIALIZE, "params": {}})[0]["result"]
    issues = _check_capabilities(srv, init)
    issues += _check_lifecycle(srv, probe, str(r.resolve()))
    issues += _check_intelligence(srv, probe, r)
    counts: Dict[str, int] = {}
    for s in srv.symbols().all_symbols():
        counts[s["kind"]] = counts.get(s["kind"], 0) + 1
    return issues, {"capabilities": len(_REQUIRED_CAPS), "clients": len(CLIENT_EDITORS),
                    "modules": counts.get("module", 0), "assets": counts.get("asset", 0),
                    "events": counts.get("event", 0), "layers": counts.get("layer", 0),
                    "pipelines": counts.get("pipeline", 0)}


#: 扫描器统一入口名（与 integrations / repo_stats / release_gate 一致）。
scan = check
