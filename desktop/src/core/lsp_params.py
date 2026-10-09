"""LSP 入站准入面：**形状**（请求/通知的参数）与**会话状态**（initialize/shutdown 状态机）。

为什么独立成模块（2026-10-08 拆分）：`core/lsp.py` 加准入层后到 843 行（越过 800 行上限）、
且最长函数涨到 37 行（越过冻结 35）——两处棘轮同时亮，按纪律「能拆就拆」。准入面也是**另一个
变化原因**：它跟协议规范（什么形状合法）与客户端实现（编辑器实际送什么）走，不跟 NF 语言面走。

内部差距实证（本模块存在的理由）：旧实现遇到不合形参数直接冒到 Python 异常，被 serve 兜成
-32603「内部错误」并把异常文本回给客户端。实测四类：position.line 非整数（ValueError）、
context.diagnostics 是字典或字符串（AttributeError）、didOpen.text 非字符串（AttributeError）、
contentChanges 元素非对象（AttributeError）。协议上这属于**参数非法**（-32602）——该带修复指引
拒绝；通知没有应答位，则**丢弃且不进状态**（存进去会让后续每次诊断都以 AttributeError 收场）。

与 MCP 面同一纪律：参数按声明校验，不合即拒（见 protocol/mcp_package.json 的 red_lines）。
纯标准库；无副作用。
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

#: JSON-RPC 标准码（与 MCP 面同一套；INVALID_PARAMS = 参数面准入失败）
INVALID_PARAMS = -32602

#: 请求面需要校验形状的方法（键用协议方法名，避免与本模块外部常量耦合）
_REQUIREMENTS: Dict[str, Tuple[str, ...]] = {
    "textDocument/completion": ("uri",),
    "textDocument/hover": ("uri", "pos"),
    "textDocument/definition": ("uri", "pos"),
    "textDocument/documentSymbol": ("uri",),
    "workspace/symbol": ("query",),
    "textDocument/references": ("uri", "pos"),
    "textDocument/foldingRange": ("uri",),
    "textDocument/codeAction": ("uri", "diagnostics"),
}


#: 会话状态机错误码（LSP：-32002 未初始化 / -32600 非法请求）
SERVER_NOT_INITIALIZED = -32002
INVALID_REQUEST = -32600


def lifecycle_problem(method: Any, rid: Any, shutting_down: bool, initialized: bool):
    """LSP 生命周期状态机 → (错误码, 说明) 或 None（2026-10-08 补）。

    为什么必须有（实测三处协议违规）：旧实现对「未 initialize 就发请求」「重复 initialize」
    「shutdown 之后继续发请求」一律照常服务——① 未初始化就服务意味着拿 CLI 默认根（还没采纳
    客户端 rootUri）去解析，结果可能是错的；② 规范明确要求重复 initialize 与 shutdown 之后的
    请求都回 InvalidRequest；③ 违反状态机会掩盖客户端 bug，让「会话已收摊」在两端口径不一。
    通知（无 id）不在这里拦：通知没有应答位，交给分派层静默忽略。
    """
    if rid is None or method == "exit":
        return None                      # 通知与 exit 不属于「请求被拒」的场合
    if shutting_down:
        return (INVALID_REQUEST, "会话已 shutdown，仅接受 exit（修复指引：退出进程后重连）")
    if method == "initialize":
        if initialized:
            return (INVALID_REQUEST, "重复 initialize（协议：一个会话只允许一次）")
        return None
    if not initialized:
        return (SERVER_NOT_INITIALIZED, "会话未 initialize（协议：先 initialize 再发请求）")
    return None


def uri_of(params: Dict[str, Any]) -> str:
    """params.textDocument.uri（非字符串/缺失 → 空串）。"""
    doc = params.get("textDocument")
    if not isinstance(doc, dict):
        return ""
    uri = doc.get("uri")
    return uri if isinstance(uri, str) else ""


def pos_of(params: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    """params.position → (line, character)；非法（缺/非整数/负数）返回 None。"""
    pos = params.get("position")
    if not isinstance(pos, dict):
        return None
    line, character = pos.get("line"), pos.get("character")
    for v in (line, character):
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            return None
    return line, character


def advise_request(method: Any, params: Dict[str, Any]) -> str:
    """请求参数准入 → 错误说明（空串 = 通过）。"""
    need = _REQUIREMENTS.get(str(method))
    if not need:
        return ""
    if "uri" in need and not uri_of(params):
        return "缺 textDocument.uri（须为非空字符串）"
    if "pos" in need and pos_of(params) is None:
        return "缺/非法 position（line 与 character 须为非负整数）"
    if "query" in need and not isinstance(params.get("query"), str):
        return "workspace/symbol 的 query 须为字符串（可省略，传别的类型即参数非法）"
    if "diagnostics" in need:
        ctx = params.get("context")
        if not isinstance(ctx, dict):
            return "缺 context 对象（codeAction 需要 {diagnostics: [...]}）"
        diags = ctx.get("diagnostics")
        if not isinstance(diags, list) or any(not isinstance(d, dict) for d in diags):
            return "context.diagnostics 须为对象数组（每项含 code/range）"
    return ""


def did_open_payload(params: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """didOpen 的（uri, text）；不合形返回 None（调用方丢弃，不进状态）。"""
    uri = uri_of(params)
    doc = params.get("textDocument")
    text = doc.get("text") if isinstance(doc, dict) else None
    if not uri or not isinstance(text, str):
        return None
    return uri, text


def did_change_text(params: Dict[str, Any]) -> Optional[str]:
    """didChange 的末次全文；不合形返回 None（调用方丢弃，不改正文）。"""
    changes = params.get("contentChanges")
    last = changes[-1] if isinstance(changes, list) and changes else None
    text = last.get("text") if isinstance(last, dict) else None
    return text if isinstance(text, str) else None
