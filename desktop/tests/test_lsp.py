# -*- coding: utf-8 -*-
"""最小 LSP 服务器单测（Content-Length 分帧 / 诊断 / quickfix）。"""
import io
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import lsp  # noqa: E402


def frame(msg):
    data = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    return ("Content-Length: %d\r\n\r\n" % len(data)).encode("ascii") + data


def parse_frames(payload: bytes):
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


class TestLsp(unittest.TestCase):
    def setUp(self):
        self.srv = lsp.LspServer(root=".", today="2026-09-14")

    def test_initialize_capabilities(self):
        out = self.srv.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                               "params": {}})
        caps = out[0]["result"]["capabilities"]
        self.assertEqual(caps["textDocumentSync"], 1)
        self.assertTrue(caps["codeActionProvider"])
        self.assertEqual(out[0]["result"]["serverInfo"]["name"], "nf-lsp")

    def test_did_open_publishes_diagnostics(self):
        uri = "file:///work/x.md"
        out = self.srv.handle({"jsonrpc": "2.0", "method": "textDocument/didOpen",
                               "params": {"textDocument": {
                                   "uri": uri, "text": "# T  \n正文"}}})
        msg = out[0]
        self.assertEqual(msg["method"], "textDocument/publishDiagnostics")
        codes = {d["code"] for d in msg["params"]["diagnostics"]}
        self.assertIn("final_newline", codes)
        self.assertIn("trailing_ws", codes)

    def test_code_action_returns_full_document_edit(self):
        uri = "file:///work/y.md"
        self.srv.handle({"jsonrpc": "2.0", "method": "textDocument/didOpen",
                         "params": {"textDocument": {"uri": uri, "text": "# T  \n正文"}}})
        diags = self.srv.docs[uri] and self.srv._publish(uri)["params"]["diagnostics"]
        out = self.srv.handle({"jsonrpc": "2.0", "id": 7,
                               "method": "textDocument/codeAction",
                               "params": {"textDocument": {"uri": uri},
                                          "context": {"diagnostics": diags}}})
        actions = out[0]["result"]
        self.assertTrue(actions)
        new_text = actions[0]["edit"]["changes"][uri][0]["newText"]
        self.assertEqual(new_text, "# T\n正文\n")
        self.assertIn("quickfix", actions[0]["kind"])

    def test_unknown_method_returns_error(self):
        out = self.srv.handle({"jsonrpc": "2.0", "id": 9, "method": "no/such"})
        self.assertEqual(out[0]["error"]["code"], -32601)

    def test_serve_loop_shutdown_exit(self):
        payload = (frame({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                          "params": {}})
                   + frame({"jsonrpc": "2.0", "method": "exit"}))
        out = io.BytesIO()
        rc = self.srv.serve(stdin=io.BytesIO(payload), stdout=out)
        self.assertEqual(rc, 0)
        msgs = parse_frames(out.getvalue())
        self.assertEqual(msgs[0]["id"], 1)


if __name__ == "__main__":
    unittest.main()
