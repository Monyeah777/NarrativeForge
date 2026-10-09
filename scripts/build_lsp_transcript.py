#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LSP 会话转写夹具：把一次**真实客户端帧序列**的往返固化成金标（fixtures）。

为什么需要（2026-10-08 三轴审计收口）：编辑器面的回归此前全是「直接调 handle()」的行为
断言加传输层加固断言——**没有一件端到端帧级金标**：客户端真实发什么（Content-Length
分帧、消息次序、位置编码）到服务端回什么（逐条应答形状与次序）这条链没有可 diff 的产物。
任一能力的应答形状漂移，只有人眼能发现。

设计口径：
- 入站帧与出站帧**都不含机器路径**（根路径统一折成 <ROOT> 占位）——夹具是公开件，
  带机器路径既是隐私泄漏也让证据换台机器不可解释（同 engine/dotnet/probes 的 portable 纪律）；
- 时间无关：今天日期由 LspServer(today=...) 固定传入，产物不随日期漂；
- 金额依赖项只在**真件在场**时才有意义（符号表来自仓库），故夹具与仓库状态同版本。

用法：
  python scripts/build_lsp_transcript.py --write   # 重生成夹具（评审后）
  python scripts/build_lsp_transcript.py --check   # 只读：与在盘夹具逐字节对账（rc=1 即漂移）
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import atomic_write  # noqa: E402 —— 写面单源（机械判据逐行认定写盘行须出现 atomic_write）
from core import lsp  # noqa: E402

FIXTURE_REL = "desktop/tests/fixtures/lsp/session.json"
SCHEMA = "nf-lsp-transcript/1"
TODAY = "2026-10-08"          # 固定"今天"：产物不随日历漂
#: 根路径占位符——**不得含 <>**：文本卫生判据要求 JSON 键的字符集是
#: ASCII 字母数字 + _-.:/ 与 CJK 汉字，夹具里有 uri 键（edit.changes）。
ROOT_PLACEHOLDER = "nf-repo-root"
PROBE_NAME = "tmp_lsp_session.md"
SEED_TEXT = "# 模块 M00  \n\n事件 narrative_event 与资产 ATTR_TEMPLATES\n"
FIXED_TEXT = "# 模块 M00\n\n事件 narrative_event 与资产 ATTR_TEMPLATES\n"


def _frame(msg) -> bytes:
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    return ("Content-Length: %d\r\n\r\n" % len(data)).encode("ascii") + data


def _parse_frames(payload: bytes):
    out, buf = [], payload
    while buf:
        head, _, rest = buf.partition(b"\r\n\r\n")
        if not rest and not head:
            break
        length = None
        for line in head.split(b"\r\n"):
            if line.lower().startswith(b"content-length:"):
                length = int(line.split(b":", 1)[1].strip())
        if length is None or len(rest) < length:
            break
        out.append(json.loads(rest[:length].decode("utf-8")))
        buf = rest[length:]
    return out


def _sub(node, old: str, new: str):
    if isinstance(node, str):
        return node.replace(old, new)
    if isinstance(node, list):
        return [_sub(x, old, new) for x in node]
    if isinstance(node, dict):
        # 键也要折：codeAction 的 edit.changes 以 **uri 本身为键**
        return {_sub(k, old, new): _sub(v, old, new) for k, v in node.items()}
    return node


def normalize(node):
    """折叠机器路径（原文与 URL 编码两种形态，含盘符与分隔符变体）。"""
    raw = os.path.abspath(str(ROOT)).replace(os.sep, "/")
    variants = [quote(raw, safe="/:@"), raw, raw.replace("/", os.sep)]
    for v in sorted(set(variants), key=len, reverse=True):
        if v:
            node = _sub(node, v, ROOT_PLACEHOLDER)
    return node


def _core_frames(uri: str, doc) -> list:
    """协议主干：握手 → 五种智能 → quickfix → 保存同步 → 收摊。"""
    return [
        {"jsonrpc": "2.0", "id": 1, "method": lsp.M_INITIALIZE,
         "params": {"capabilities": {"textDocument": {"documentSymbol": {
             "hierarchicalDocumentSymbolSupport": True}}}}},
        {"jsonrpc": "2.0", "method": lsp.M_INITIALIZED, "params": {}},
        {"jsonrpc": "2.0", "method": lsp.M_DID_OPEN,
         "params": {"textDocument": {"uri": uri, "text": SEED_TEXT}}},
        {"jsonrpc": "2.0", "id": 2, "method": lsp.M_COMPLETION,
         "params": {**doc, "position": {"line": 0, "character": 6}}},
        {"jsonrpc": "2.0", "id": 3, "method": lsp.M_HOVER,
         "params": {**doc, "position": {"line": 0, "character": 6}}},
        {"jsonrpc": "2.0", "id": 4, "method": lsp.M_DEFINITION,
         "params": {**doc, "position": {"line": 0, "character": 6}}},
        {"jsonrpc": "2.0", "id": 5, "method": lsp.M_DOCUMENT_SYMBOL, "params": dict(doc)},
        {"jsonrpc": "2.0", "id": 6, "method": lsp.M_WORKSPACE_SYMBOL,
         "params": {"query": "M00"}},
        {"jsonrpc": "2.0", "id": 7, "method": lsp.M_CODE_ACTION,
         "params": {**doc, "context": {"diagnostics": [{"code": "trailing_ws"},
                                                       {"code": "final_newline"}]}}},
        {"jsonrpc": "2.0", "method": lsp.M_DID_CHANGE,
         "params": {**doc, "contentChanges": [{"text": FIXED_TEXT}]}},
    ]


def _edge_frames(uri: str, doc) -> list:
    """编辑器真会发、但此前无帧级证据的入站面（2026-10-08 扩金标）。"""
    return [
        # ---- 静默面：未声明能力的通知 / 心跳 / 抢先取消
        {"jsonrpc": "2.0", "method": "textDocument/willSave",
         "params": {**doc, "reason": 1}},
        {"jsonrpc": "2.0", "id": 9, "method": "textDocument/willSaveWaitUntil",
         "params": {**doc, "reason": 1}},            # 未声明该能力 → -32601
        {"jsonrpc": "2.0", "method": "workspace/didChangeWatchedFiles",
         "params": {"changes": [{"uri": uri, "type": 2}]}},
        {"jsonrpc": "2.0", "method": "workspace/didChangeConfiguration",
         "params": {"settings": {}}},
        {"jsonrpc": "2.0", "method": "$/setTrace", "params": {"value": "off"}},
        {"jsonrpc": "2.0", "method": "$/cancelRequest",
         "params": {"id": 2}},                       # 编辑器「打字抢先」时真会发
        {"jsonrpc": "2.0", "method": lsp.M_DID_SAVE, "params": dict(doc)},
        {"jsonrpc": "2.0", "method": lsp.M_HOVER,       # **请求方法当通知发**：禁止应答
         "params": {**doc, "position": {"line": 0, "character": 6}}},
        {"jsonrpc": "2.0", "id": 10, "method": lsp.M_HOVER,
         "params": {**doc, "position": {"line": 2, "character": 1}}},   # 无符号词 → null
        {"jsonrpc": "2.0", "id": 11, "method": lsp.M_WORKSPACE_SYMBOL,
         "params": {"query": "没有这个符号"}},                            # 命中空 → []
        {"jsonrpc": "2.0", "id": 16, "method": lsp.M_REFERENCES,
         "params": {**doc, "position": {"line": 2, "character": 4}}},     # 结构化引用（发布/订阅）
        {"jsonrpc": "2.0", "id": 17, "method": lsp.M_FOLDING_RANGE,
         "params": dict(doc)},                                            # 折叠区间（标题小节）
        {"jsonrpc": "2.0", "id": 12, "method": "no/such", "params": {}},  # -32601
        {"jsonrpc": "2.0", "id": 13, "method": "$/noSuchRequest", "params": {}},  # -32601
        {"jsonrpc": "2.0", "method": lsp.M_DID_CHANGE,
         "params": {**doc, "contentChanges": [{"text": "# 模块 M00  \n"},
                                              {"text": FIXED_TEXT}]}},  # 全文同步：末次为准
        {"jsonrpc": "2.0", "method": lsp.M_DID_CLOSE, "params": dict(doc)},
        {"jsonrpc": "2.0", "id": 14, "method": lsp.M_COMPLETION,
         "params": {**doc, "position": {"line": 0, "character": 6}}},   # 已关闭文档 → 空面
        {"jsonrpc": "2.0", "id": 8, "method": lsp.M_SHUTDOWN},
        {"jsonrpc": "2.0", "id": 15, "method": lsp.M_HOVER,
         "params": {**doc, "position": {"line": 0, "character": 6}}},   # shutdown 后 → -32600
        {"jsonrpc": "2.0", "method": lsp.M_EXIT},
    ]


def client_messages() -> list:
    """完整入站帧序列 = 协议主干 + 编辑器的其余真实入站面。"""
    uri = lsp.path_to_uri(str(ROOT / PROBE_NAME))
    doc = {"textDocument": {"uri": uri}}
    return _core_frames(uri, doc) + _edge_frames(uri, doc)


def build():
    msgs = client_messages()
    srv = lsp.LspServer(root=str(ROOT), today=TODAY, explicit_root=True)
    payload = b"".join(_frame(m) for m in msgs)
    out = io.BytesIO()
    rc = srv.serve(stdin=io.BytesIO(payload), stdout=out)
    server = _parse_frames(out.getvalue())
    return {"schema": SCHEMA,
            "note": "客户端帧序列 → 服务端应答（端到端金标；根路径折成 " + ROOT_PLACEHOLDER
            + "，today 固定）",
            "today": TODAY,
            "client_messages": normalize(msgs),
            "server_messages": normalize(server),
            "exit_code": rc,
            "digest": digest_of(normalize(server))}


def digest_of(server_messages):
    canon = json.dumps(server_messages, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def render(doc) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="LSP 会话转写夹具（端到端帧级金标）")
    ap.add_argument("--write", action="store_true", help="重生成夹具")
    ap.add_argument("--check", action="store_true", help="只读对账（rc=1 即漂移）")
    args = ap.parse_args(argv)
    path = ROOT / FIXTURE_REL
    want = render(build())
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write.write_text(path, want)
        print("已写入 %s（%d 条应答）" % (FIXTURE_REL, len(build()["server_messages"])))
        return 0
    if not path.is_file():
        print("缺夹具 %s（修复指引：跑 --write）" % FIXTURE_REL)
        return 1
    got = path.read_text(encoding="utf-8")
    if got == want:
        print("✓ 夹具与实时重算逐字节一致（%s · %d 条应答）"
              % (FIXTURE_REL, len(build()["server_messages"])))
        return 0
    print("✗ 夹具漂移：在盘 %d 字节，实时重算 %d 字节（修复指引：复核后跑 --write 重签）"
          % (len(got), len(want)))
    return 1


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
