"""LSP 传输分帧面：Content-Length 读写 + 入站上限 + 坏帧哨兵。

为什么独立成模块（2026-10-08 拆分）：`core/lsp.py` 加会话状态机与入站准入后越过 800 行上限，
按纪律「能拆就拆」——**线格式**（Content-Length 分帧、UTF-8 解码、上限闸门）与**协议语义**
（initialize/shutdown 状态机、能力、诊断、索引）是两个变化原因：前者跟 LSP 传输层走，后者跟
NF 语言面走。

关键口径（实测教训，2026-09-30 与 2026-10-01 两次修复都落在这里）：
- 表头行与正文都按 `MAX_MESSAGE_BYTES` 有界（不发换行、或报一个巨大的 Content-Length 就能让
  长驻服务把任意量数据读进内存）；
- 区分「对端关闭（EOF → None）」与「坏帧（BAD_FRAME 哨兵）」：前者收摊，后者回 -32700 后
  **继续服务**——修复前坏帧会打死整个长驻会话。
纯标准库；无副作用。
"""
from __future__ import annotations

import json
from typing import Any, Dict

#: 单条入站消息上限（含表头行）——与 MCP 面同一档 8 MiB，理由相同：不发换行/报一个巨大的
#: Content-Length 就能让长驻服务把任意量数据读进内存（2026-09-30 补；此前 length 直接喂给
#: src.read()，负值更会「读到 EOF」）。
MAX_MESSAGE_BYTES = 8 * 1024 * 1024

#: 传输层**解不出**消息（非法 UTF-8 / 非法 JSON / 坏 Content-Length）——与「对端关闭」区分：
#: 前者要回 -32700 后**继续服务**，后者（None）才收摊。
BAD_FRAME = object()


def binary_stream(stream):
    """拿到可读字节的底层流（文本流走其 buffer）。"""
    return getattr(stream, "buffer", None) or stream


def write_message(stream, msg: Dict[str, Any]) -> None:
    """LSP 分帧写出（Content-Length 以**字节**计）。"""
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    frame = ("Content-Length: %d\r\n\r\n" % len(data)).encode("ascii") + data
    target = binary_stream(stream)
    try:
        target.write(frame)
    except TypeError:
        stream.write(frame.decode("utf-8"))
    flush = getattr(target, "flush", None)
    if flush:
        flush()


def read_message(stream) -> Any:
    """读一条 LSP 消息；EOF → None，坏帧 → BAD_FRAME（调用方据此回错误码后继续）。"""
    src = binary_stream(stream)
    length = None
    while True:
        line = src.readline(MAX_MESSAGE_BYTES + 1)
        if not line:
            return None
        if len(line) > MAX_MESSAGE_BYTES:
            return BAD_FRAME           # 表头行本身超限 ⇒ 直接判坏帧（内存有界，不读完）
        if isinstance(line, bytes):
            line = line.decode("utf-8", "replace")
        line = line.strip()
        if not line:
            break
        if line.lower().startswith("content-length:"):
            try:
                length = int(line.split(":", 1)[1].strip())
            except ValueError:
                return BAD_FRAME
    if length is None or length < 0 or length > MAX_MESSAGE_BYTES:
        return BAD_FRAME
    body = src.read(length)
    if isinstance(body, bytes):
        try:
            body = body.decode("utf-8")
        except UnicodeDecodeError:
            return BAD_FRAME
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return BAD_FRAME
