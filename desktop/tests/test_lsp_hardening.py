# -*- coding: utf-8 -*-
"""LSP 传输面加固（`core/lsp.py`）：坏帧不杀长驻会话，且给出标准错误码。

动机（本轮 LSP 面取证，两个真缺陷）：① 正文是**非法 UTF-8** 时 `body.decode("utf-8")` 抛
`UnicodeDecodeError`；② 正文是**合法 JSON 但非对象**（`[]` / `123`）时 `msg.get(...)` 抛
`AttributeError`——两者都冒到 CLI 兜底报「内部错误」并以 rc=1 退出，**一条坏帧打死整个 LSP
服务**（与 MCP 面修的是同一类缺陷）。修复后：坏帧 → `-32700`、非对象 → `-32600`，各自继续服务。
"""
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import lsp as lsp  # noqa: E402

OK_FRAME = b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'


def _frame(body: bytes) -> bytes:
    return ("Content-Length: %d\r\n\r\n" % len(body)).encode() + body


def _serve(payload: bytes):
    stdin = io.TextIOWrapper(io.BytesIO(payload), encoding="utf-8")
    stdout = io.BytesIO()
    code = lsp.LspServer(root=str(ROOT)).serve(stdin, stdout)
    return code, stdout.getvalue()


class LspTransportHardeningTest(unittest.TestCase):
    def test_invalid_utf8_frame_is_a_parse_error_and_session_survives(self):
        code, out = _serve(_frame(b"\xff\xfe\xfd\xfc\xfb") + _frame(OK_FRAME))
        self.assertEqual(0, code, "坏帧不应让服务非零退出")
        self.assertIn(b"-32700", out)
        self.assertIn(b'"id": 1', out, "坏帧之后的好帧必须仍被服务")

    def test_non_object_json_is_an_invalid_request(self):
        for body in (b"[]", b"123", b'"str"', b"true"):
            code, out = _serve(_frame(body) + _frame(OK_FRAME))
            self.assertEqual(0, code, body)
            self.assertIn(b"-32600", out, body)
            self.assertNotIn(b"Internal", out, "非对象消息不得报成内部错误")

    def test_lying_content_length_is_a_parse_error(self):
        code, out = _serve(b"Content-Length: 999\r\n\r\nshort")
        self.assertEqual(0, code)
        self.assertIn(b"-32700", out)

    def test_non_numeric_content_length_is_a_parse_error(self):
        code, out = _serve(b"Content-Length: abc\r\n\r\n{}")
        self.assertEqual(0, code)
        self.assertIn(b"-32700", out)

    def test_oversized_or_negative_content_length_is_bounded(self):
        """入站资源闸门（2026-09-30 补）：`Content-Length` 上限 8 MiB、负值判坏帧。

        依据：此前 `length` 被直接喂给 `src.read()`——客户端报一个巨大的长度就能让长驻服务
        按那个数分配/读取（负值更会「读到 EOF」）。现在两者都归 `-32700` 坏帧，会话照旧存活。
        """
        for payload in (b"Content-Length: 999999999999\r\n\r\n" + OK_FRAME,
                        b"Content-Length: %d\r\n\r\n" % (lsp.MAX_MESSAGE_BYTES + 1) + OK_FRAME,
                        b"Content-Length: -5\r\n\r\n" + OK_FRAME):
            code, out = _serve(payload)
            self.assertEqual(0, code, payload[:30])
            self.assertIn(b"-32700", out, payload[:30])

    def test_oversized_header_line_is_bounded(self):
        """表头行本身也不能无界：不发换行的超长表头 ⇒ 坏帧（而不是把整条流读进内存）。"""
        payload = b"X-Pad: " + b"y" * (lsp.MAX_MESSAGE_BYTES + 10) + b"\r\n\r\n" + OK_FRAME
        code, out = _serve(payload)
        self.assertEqual(0, code)
        self.assertIn(b"-32700", out)

    def test_clean_frame_still_works(self):
        code, out = _serve(_frame(OK_FRAME))
        self.assertEqual(0, code)
        self.assertTrue(out.startswith(b"Content-Length: "), out[:40])
        self.assertIn(b'"id": 1', out)
        self.assertIn(b"capabilities", out)


if __name__ == "__main__":
    unittest.main()
