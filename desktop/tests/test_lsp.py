# -*- coding: utf-8 -*-
"""LSP 服务器单测（分帧 / 能力 / 诊断定位 / 领域智能 / 编辑 / 退出语义 / 配置生成）。

判据来源：LSP 3.17 规范（initialize 能力、positionEncoding、didClose、shutdown/exit 退出码、
最小编辑范围语义）与 docs/lsp.md 的承诺面。测试跑在**真仓库根**上——符号表是派生面，
用真件才判得出「模块 id / 资产键 / 事件名 / 层位 id / 管线 id」是否真被接上。
"""
import io
import json
import os
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import lsp  # noqa: E402
from core import lsp_client  # noqa: E402
from core import lsp_doc  # noqa: E402   # 文档级能力已独立成模块（诊断/大纲/编辑）

ROOT = str(Path(__file__).resolve().parents[2])


def _ready(srv):
    """按**真实客户端序列**先 initialize（协议：未初始化的会话只接受 initialize）。

    2026-10-08 补状态机后，先发请求会正确地回 -32002——所以每处「要用请求面」的用例都必须先握手；
    这也让判据更贴近编辑器实际发生的事。
    """
    srv.handle({"jsonrpc": "2.0", "id": 1, "method": lsp.M_INITIALIZE, "params": {}})
    return srv
ASTRA = chr(0x1F600)          # 星号外字符：UTF-16 里占 2 个码元
BS = chr(92)
FENCE = chr(96) * 3


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


def open_doc(srv, uri, text):
    return srv.handle({"jsonrpc": "2.0", "method": lsp.M_DID_OPEN,
                       "params": {"textDocument": {"uri": uri, "text": text}}})


class TestCapabilities(unittest.TestCase):
    """initialize 声明面：能力齐全 + rootUri 采纳口径。"""

    def _init(self, params=None):
        srv = lsp.LspServer(root=ROOT, today="2026-10-07")
        out = srv.handle({"jsonrpc": "2.0", "id": 1, "method": lsp.M_INITIALIZE,
                          "params": params or {}})
        return srv, out[0]["result"]

    def test_declares_editor_surface(self):
        _srv, res = self._init()
        caps = res["capabilities"]
        self.assertEqual(caps["positionEncoding"], "utf-16")
        self.assertEqual(caps["textDocumentSync"],
                         {"openClose": True, "change": 1, "save": True})
        self.assertEqual(caps["codeActionProvider"], {"codeActionKinds": ["quickfix"]})
        for key in ("hoverProvider", "definitionProvider", "documentSymbolProvider",
                    "workspaceSymbolProvider"):
            self.assertTrue(caps[key], key)
        self.assertTrue(caps["completionProvider"]["triggerCharacters"])
        self.assertEqual(res["serverInfo"]["name"], "nf-lsp")

    def test_root_uri_adopted_only_without_explicit_root(self):
        srv, _res = self._init({"rootUri": "file:///C:/somewhere/else"})
        self.assertTrue(srv.root.replace(BS, "/").endswith("somewhere/else"))
        explicit = lsp.LspServer(root=ROOT, explicit_root=True)
        explicit.handle({"jsonrpc": "2.0", "id": 1, "method": lsp.M_INITIALIZE,
                         "params": {"rootUri": "file:///C:/somewhere/else"}})
        self.assertEqual(explicit.root, str(Path(ROOT).resolve()))


class TestDiagnostics(unittest.TestCase):
    """诊断定位：每条诊断必须带真实行/列（旧实现恒为 (0,0)，编辑器无法定位）。"""

    def test_trailing_ws_points_at_first_trailing_space(self):
        diags = lsp_doc.diagnose("x.md", "# T  \n正文\n", ".")
        hits = [d for d in diags if d["code"] == "trailing_ws"]
        self.assertTrue(hits)
        self.assertEqual(hits[0]["range"]["start"], {"line": 0, "character": 3})
        self.assertEqual(hits[0]["range"]["end"], {"line": 0, "character": 5})

    def test_final_newline_points_at_last_line(self):
        diags = lsp_doc.diagnose("x.md", "# T\n正文", ".")
        hits = [d for d in diags if d["code"] == "final_newline"]
        self.assertTrue(hits)
        self.assertEqual(hits[0]["range"]["start"]["line"], 1)

    def test_prose_finding_carries_column(self):
        diags = lsp_doc.diagnose("x.md", "# T\n\n总而言之，我们应该谨慎。\n", ".")
        hits = [d for d in diags if d["source"] == "nf-prose"]
        self.assertTrue(hits, "正文 lint 应在场（prose_lint 与 lint 同源）")
        self.assertEqual(hits[0]["range"]["start"]["line"], 2)
        self.assertLessEqual(hits[0]["range"]["start"]["character"],
                             hits[0]["range"]["end"]["character"])

    def test_utf16_positions_for_astral_characters(self):
        diags = lsp_doc.diagnose("x.md", "# T" + ASTRA + "  \n", ".")
        hits = [d for d in diags if d["code"] == "trailing_ws"]
        self.assertTrue(hits)
        self.assertEqual(hits[0]["range"]["start"]["character"], 5)
        self.assertEqual(hits[0]["range"]["end"]["character"], 7)


class TestDomainIntelligence(unittest.TestCase):
    """领域智能：补全 / 悬停 / 跳定义 / 大纲（符号表来自真仓库件）。"""

    def setUp(self):
        self.srv = lsp.LspServer(root=ROOT, today="2026-10-07")
        self.srv.handle({"jsonrpc": "2.0", "id": 0, "method": lsp.M_INITIALIZE,
                         "params": {"capabilities": {"textDocument": {"documentSymbol": {
                             "hierarchicalDocumentSymbolSupport": True}}}}})
        self.uri = "file:///" + ROOT.replace(BS, "/").lstrip("/") + "/tmp_test.md"

    def _text(self):
        return ("# 模块 演示\n\n挂载层 P40，模块 M00 与 情感:M22，事件 narrative_event，\n"
                "资产 ATTR_TEMPLATES，管线 P01，裸号 M10。\n")

    def _pos(self, needle, offset=1):
        text = self._text()
        idx = text.index(needle) + offset
        line = text[:idx].count("\n")
        return line, idx - (text.rfind("\n", 0, idx) + 1)

    def test_completion_returns_domain_symbols(self):
        open_doc(self.srv, self.uri, self._text())
        line, ch = self._pos("P40")
        out = self.srv.handle({"jsonrpc": "2.0", "id": 2, "method": lsp.M_COMPLETION,
                               "params": {"textDocument": {"uri": self.uri},
                                          "position": {"line": line, "character": ch}}})
        result = out[0]["result"]
        labels = {i["label"] for i in result["items"]}
        self.assertIn("P40", labels)
        self.assertEqual(result["isIncomplete"], False)

    def test_completion_empty_prefix_returns_nothing(self):
        open_doc(self.srv, self.uri, "# T \n")
        out = self.srv.handle({"jsonrpc": "2.0", "id": 2, "method": lsp.M_COMPLETION,
                               "params": {"textDocument": {"uri": self.uri},
                                          "position": {"line": 0, "character": 4}}})
        self.assertEqual(out[0]["result"]["items"], [])

    def test_hover_reports_module_metadata(self):
        open_doc(self.srv, self.uri, self._text())
        line, ch = self._pos("M00")
        out = self.srv.handle({"jsonrpc": "2.0", "id": 3, "method": lsp.M_HOVER,
                               "params": {"textDocument": {"uri": self.uri},
                                          "position": {"line": line, "character": ch}}})
        value = out[0]["result"]["contents"]["value"]
        self.assertIn("模块 M00", value)
        self.assertIn("04_模块库/通用类/M00_数据结构.md", value)

    def test_hover_reports_ambiguous_candidates(self):
        open_doc(self.srv, self.uri, self._text())
        line, ch = self._pos("M10")
        out = self.srv.handle({"jsonrpc": "2.0", "id": 4, "method": lsp.M_HOVER,
                               "params": {"textDocument": {"uri": self.uri},
                                          "position": {"line": line, "character": ch}}})
        self.assertIn("同名符号", out[0]["result"]["contents"]["value"])

    def test_definition_jumps_to_unique_symbol_file(self):
        open_doc(self.srv, self.uri, self._text())
        line, ch = self._pos("ATTR_TEMPLATES")
        out = self.srv.handle({"jsonrpc": "2.0", "id": 5, "method": lsp.M_DEFINITION,
                               "params": {"textDocument": {"uri": self.uri},
                                          "position": {"line": line, "character": ch}}})
        loc = out[0]["result"]
        self.assertIn("community/", loc["uri"])
        self.assertIn("ATTR_TEMPLATES.md", loc["uri"])

    def test_definition_fail_closed_on_ambiguous_token(self):
        open_doc(self.srv, self.uri, self._text())
        line, ch = self._pos("M10")
        out = self.srv.handle({"jsonrpc": "2.0", "id": 6, "method": lsp.M_DEFINITION,
                               "params": {"textDocument": {"uri": self.uri},
                                          "position": {"line": line, "character": ch}}})
        self.assertIsNone(out[0]["result"])

    def test_document_symbols_hierarchical_and_flat(self):
        text = "# 一级\n\n" + FENCE + "\n# 不是标题\n" + FENCE + "\n\n## 二级\n"
        open_doc(self.srv, self.uri, text)
        out = self.srv.handle({"jsonrpc": "2.0", "id": 7, "method": lsp.M_DOCUMENT_SYMBOL,
                               "params": {"textDocument": {"uri": self.uri}}})
        tree = out[0]["result"]
        self.assertEqual([n["name"] for n in tree], ["一级"])
        self.assertEqual([n["name"] for n in tree[0]["children"]], ["二级"])
        flat_srv = lsp.LspServer(root=ROOT)
        flat_srv.handle({"jsonrpc": "2.0", "id": 0, "method": lsp.M_INITIALIZE,
                         "params": {"capabilities": {"textDocument": {"documentSymbol": {
                             "hierarchicalDocumentSymbolSupport": False}}}}})
        open_doc(flat_srv, self.uri, text)
        out = flat_srv.handle({"jsonrpc": "2.0", "id": 8, "method": lsp.M_DOCUMENT_SYMBOL,
                              "params": {"textDocument": {"uri": self.uri}}})
        names = [s["name"] for s in out[0]["result"]]
        self.assertEqual(names, ["一级", "二级"])
        self.assertIn("location", out[0]["result"][0])

    def test_workspace_symbol_query(self):
        out = self.srv.handle({"jsonrpc": "2.0", "id": 9, "method": lsp.M_WORKSPACE_SYMBOL,
                               "params": {"query": "M00"}})
        names = {s["name"] for s in out[0]["result"]}
        self.assertIn("M00", names)


class TestLifecycleAndEdits(unittest.TestCase):
    """会话生命周期与 quickfix 编辑面。"""

    def setUp(self):
        self.srv = _ready(lsp.LspServer(root=ROOT, today="2026-10-07"))
        self.uri = "file:///" + ROOT.replace(BS, "/").lstrip("/") + "/tmp_test2.md"

    def test_did_close_clears_state_and_diagnostics(self):
        open_doc(self.srv, self.uri, "# T  \n正文")
        self.assertIn(self.uri, self.srv.docs)
        out = self.srv.handle({"jsonrpc": "2.0", "method": lsp.M_DID_CLOSE,
                               "params": {"textDocument": {"uri": self.uri}}})
        self.assertNotIn(self.uri, self.srv.docs)
        self.assertEqual(out[0]["params"]["diagnostics"], [])

    def test_code_action_edits_are_minimal_and_apply_cleanly(self):
        text = "# T  \n正文  多项"
        open_doc(self.srv, self.uri, text)
        diags = self.srv._publish(self.uri)["params"]["diagnostics"]
        out = self.srv.handle({"jsonrpc": "2.0", "id": 7, "method": lsp.M_CODE_ACTION,
                               "params": {"textDocument": {"uri": self.uri},
                                          "context": {"diagnostics": diags}}})
        action = out[0]["result"][0]
        edits = action["edit"]["changes"][self.uri]
        self.assertEqual(lsp_doc.apply_edits(text, edits), "# T\n正文  多项\n")
        self.assertLess(sum(len(e["newText"]) for e in edits), len(text))

    def test_code_action_respects_context_only(self):
        open_doc(self.srv, self.uri, "# T  \n正文")
        diags = self.srv._publish(self.uri)["params"]["diagnostics"]
        out = self.srv.handle({"jsonrpc": "2.0", "id": 8, "method": lsp.M_CODE_ACTION,
                               "params": {"textDocument": {"uri": self.uri},
                                          "context": {"diagnostics": diags,
                                                      "only": ["refactor"]}}})
        self.assertEqual(out[0]["result"], [])

    def test_exit_code_depends_on_shutdown(self):
        payload = frame({"jsonrpc": "2.0", "method": lsp.M_EXIT})
        self.assertEqual(self.srv.serve(stdin=io.BytesIO(payload), stdout=io.BytesIO()), 1)
        # 协议：shutdown 请求只在 initialize 之后有效（2026-10-08 补状态机后，未握手就 shutdown
        # 会被拒 -32002，exit 因而已收到 shutdown 不成立 → 1；故这里按真实序列先握手）。
        polite = _ready(lsp.LspServer(root=ROOT))
        payload = (frame({"jsonrpc": "2.0", "id": 1, "method": lsp.M_SHUTDOWN})
                   + frame({"jsonrpc": "2.0", "method": lsp.M_EXIT}))
        out = io.BytesIO()
        self.assertEqual(polite.serve(stdin=io.BytesIO(payload), stdout=out), 0)
        self.assertEqual(parse_frames(out.getvalue())[0]["id"], 1)

    def test_unknown_dollar_notification_is_ignored(self):
        out = self.srv.handle({"jsonrpc": "2.0", "method": "$/cancelRequest",
                               "params": {"id": 1}})
        self.assertEqual(out, [])


class TestClientConfig(unittest.TestCase):
    """编辑器装配面：配置由唯一真相生成（不手抄、不伪造未验证的编辑器面）。"""

    def test_each_editor_config_names_repo_and_entry(self):
        for editor in lsp_client.CLIENT_EDITORS:
            cfg = lsp_client.render_client_config(editor, ROOT)
            self.assertIn("scripts/nf.py", cfg)
            self.assertIn('"lsp"', cfg)

    def test_unknown_editor_rejected(self):
        with self.assertRaises(ValueError):
            lsp_client.render_client_config("vscode", ROOT)


class TestDocConfigStaysInSync(unittest.TestCase):
    """docs/lsp.md 的三块编辑器配置必须是 render_client_config 的**逐字投影**。

    为什么需要：docs/lsp.md 的配置块此前登记为「不必真跑」（带路径占位符），于是它只是
    一段**无人核对**的手抄文本——生成器一改，文档就静默漂移（本仓对这种「声明 > 实测」
    有明令）。本判据把占位符还原后逐块比对：文档 = 生成器输出。
    """

    PLACEHOLDER = "<仓库绝对路径>"

    def _doc(self):
        return (Path(ROOT) / "docs" / "lsp.md").read_text(encoding="utf-8")

    def _normalized_generator_output(self, editor):
        cfg = lsp_client.render_client_config(editor, ROOT)
        norm = os.path.abspath(ROOT).replace(os.sep, "/")
        return cfg.replace(norm, self.PLACEHOLDER)

    def test_each_editor_block_is_the_generator_output(self):
        doc = self._doc()
        for editor in lsp_client.CLIENT_EDITORS:
            block = self._normalized_generator_output(editor)
            body = "\n".join(block.splitlines()[1:])      # 去掉生成器首行标题
            for line in body.splitlines():
                if line.strip():
                    self.assertIn(line, doc,
                                  "%s 的配置行已漂移（应为生成器输出）：%s" % (editor, line))

    def test_placeholder_is_used_not_a_machine_path(self):
        doc = self._doc()
        self.assertIn(self.PLACEHOLDER, doc)
        self.assertNotIn(os.path.abspath(ROOT).replace(os.sep, "/"), doc,
                         "文档不得写死本机绝对路径")


class TestTransport(unittest.TestCase):
    """分帧回归（hardening 细节见 test_lsp_hardening）。"""

    def test_serve_loop_initialize_then_exit(self):
        srv = lsp.LspServer(root=ROOT)
        payload = (frame({"jsonrpc": "2.0", "id": 1, "method": lsp.M_INITIALIZE, "params": {}})
                   + frame({"jsonrpc": "2.0", "method": lsp.M_SHUTDOWN})
                   + frame({"jsonrpc": "2.0", "method": lsp.M_EXIT}))
        out = io.BytesIO()
        self.assertEqual(srv.serve(stdin=io.BytesIO(payload), stdout=out), 0)
        self.assertEqual(parse_frames(out.getvalue())[0]["id"], 1)

    def test_unknown_method_returns_error(self):
        out = _ready(lsp.LspServer(root=ROOT)).handle({"jsonrpc": "2.0", "id": 9, "method": "no/such"})
        self.assertEqual(out[0]["error"]["code"], -32601)


class TestUriRoundTrip(unittest.TestCase):
    """uri ↔ 路径往返（编辑器把 uri 交给我们，我们在定义跳转里把它交回去）。

    此前无判据：Windows 盘符（file:///C:/…）与空格/CJK 路径这两类在编辑器里天天出现，
    任一处错位都会让「跳定义」打开一个不存在的文件，而协议层测试全绿。
    """

    def test_windows_drive_uri_to_path(self):
        self.assertEqual(os.path.join("C:" + os.sep, "work", "x.md"),
                         lsp.uri_to_path("file:///C:/work/x.md"))

    def test_percent_encoded_and_cjk_round_trip(self):
        raw = os.path.join(ROOT, "docs", "lsp.md")
        uri = lsp.path_to_uri(raw)
        self.assertTrue(uri.startswith("file:///"))
        self.assertNotIn(" ", uri, "空格须百分号编码")
        self.assertEqual(os.path.abspath(raw), os.path.abspath(lsp.uri_to_path(uri)))

    def test_round_trip_with_spaces_and_cjk(self):
        for name in ("a b.md", "中文 名称.md"):
            raw = os.path.join(ROOT, name)
            self.assertEqual(os.path.abspath(raw),
                             os.path.abspath(lsp.uri_to_path(lsp.path_to_uri(raw))),
                             name)


class TestIndexTtl(unittest.TestCase):
    """索引签名 TTL：同一窗口内复用索引，过期才重扫（性能判据，不看墙钟）。

    实测（2026-10-08 本机）：签名对 731 件逐件 stat 需 **119.5 ms**，补全请求 **158 ms**——
    若每请求都扫，编辑器里就是「每敲一个字卡一下」。本判据用**调用计数**（不依赖计时）钉住：
    窗口内多次取索引只扫一次签名；invalidate() 与 TTL 过期各强制一次。
    """

    def _patched(self, values):
        # 必须改**lsp 实际引用的那个模块对象**：进程里 core.* 会被换版（daemon/watch 测试
        # 会从 sys.modules 摘掉重载），`from core import nf_language` 可能拿到另一份实例——
        # 那是本仓已记档的坑（test_watch「模块身份还原」）。
        nf_language = lsp.nf_language
        seq = list(values)

        def fake(root):
            return seq.pop(0) if len(seq) > 1 else seq[0]

        real = nf_language.signature
        nf_language.signature = fake
        self.addCleanup(setattr, nf_language, "signature", real)
        return fake

    def test_warm_requests_reuse_one_signature_scan(self):
        nf_language = lsp.nf_language
        calls = []
        real = nf_language.signature
        nf_language.signature = lambda root: (calls.append(1), real(root))[1]
        self.addCleanup(setattr, nf_language, "signature", real)
        srv = _ready(lsp.LspServer(root=ROOT, explicit_root=True))
        first = srv.symbols()
        for _ in range(5):
            self.assertIs(first, srv.symbols(), "窗口内应复用同一索引对象")
        self.assertEqual(1, len(calls), "同一 TTL 窗口内只该扫一次签名")

    def test_invalidate_forces_a_rescan(self):
        nf_language = lsp.nf_language
        calls = []
        real = nf_language.signature
        nf_language.signature = lambda root: (calls.append(1), real(root))[1]
        self.addCleanup(setattr, nf_language, "signature", real)
        srv = _ready(lsp.LspServer(root=ROOT, explicit_root=True))
        srv.symbols()
        srv.invalidate()
        srv.symbols()
        self.assertEqual(2, len(calls), "invalidate() 后应重扫一次")

    def test_expired_ttl_and_changed_signature_rebuild(self):
        self._patched([("a",), ("b",), ("b",)])
        srv = _ready(lsp.LspServer(root=ROOT, explicit_root=True))
        first = srv.symbols()
        srv._sig_at -= (lsp.INDEX_TTL_S + 1.0)          # 把窗口拨到过期
        second = srv.symbols()
        self.assertIsNot(first, second, "签名变了应重建索引")
        srv._sig_at -= (lsp.INDEX_TTL_S + 1.0)
        self.assertIs(second, srv.symbols(), "签名未变则复用（不重复建表）")

    def test_did_save_invalidates_the_index(self):
        self._patched([("a",), ("a",), ("a",)])
        srv = _ready(lsp.LspServer(root=ROOT, explicit_root=True))
        srv.symbols()
        self.assertGreater(srv._sig_at, 0.0)
        srv.handle({"jsonrpc": "2.0", "method": lsp.M_DID_SAVE,
                    "params": {"textDocument": {"uri": "file:///x.md"}}})
        self.assertEqual(0.0, srv._sig_at, "didSave 应强制下次重扫")


class TestSelfReportMatchesIntegrationCard(unittest.TestCase):
    """服务端自述（serverInfo）必须与接入面卡一致：两处各写一遍就会静默漂。"""

    def test_server_info_uses_the_constants(self):
        info = lsp.LspServer(root=ROOT).handle(
            {"jsonrpc": "2.0", "id": 1, "method": lsp.M_INITIALIZE,
             "params": {}})[0]["result"]["serverInfo"]
        self.assertEqual(lsp.SERVER_NAME, info["name"])
        self.assertEqual(lsp.SERVER_VERSION, info["version"])

    def test_integration_card_version_matches(self):
        card = json.loads((Path(ROOT) / "integrations" / "lsp" / "integration.json")
                          .read_text(encoding="utf-8"))
        self.assertEqual(lsp.SERVER_VERSION, card["version"],
                         "接入面卡版本与服务端自述不一致（修复指引：两处同步）")


class TestHoverRangeUsesUtf16(unittest.TestCase):
    """悬停范围同样按 UTF-16 码元折算（BMP 外字符占 2 个码元）。

    诊断范围早有判据（test_utf16_positions_for_astral_characters），悬停范围此前没有——
    位置口径只要有一处漏折，编辑器里光标框就会偏一格，而协议层测试全绿。
    """

    def test_astral_character_shifts_hover_range(self):
        srv = _ready(lsp.LspServer(root=ROOT, today="2026-10-08"))
        uri = "file:///tmp_astral.md"
        line = "# T" + chr(0x1F600) + " M00"
        srv.handle({"jsonrpc": "2.0", "method": lsp.M_DID_OPEN,
                    "params": {"textDocument": {"uri": uri, "text": line + "\n"}}})
        cp = line.index("M00")
        out = srv.handle({"jsonrpc": "2.0", "id": 3, "method": lsp.M_HOVER,
                          "params": {"textDocument": {"uri": uri},
                                     "position": {"line": 0, "character": cp + 1}}})
        rng = out[0]["result"]["range"]
        self.assertEqual(cp + 1, rng["start"]["character"], "起点应含星号外字符多出的 1 码元")
        self.assertEqual(cp + 4, rng["end"]["character"], "终点同理")


class TestParamAdmission(unittest.TestCase):
    """参数准入：不合形的请求回 -32602（带修复指引），不得冒成 -32603 内部错误。

    内部差距实证（2026-10-08 实测四类）：position.line 非整数 → ValueError、
    context.diagnostics 是字典/字符串 → AttributeError、didOpen.text 非字符串 → AttributeError、
    contentChanges 元素非对象 → AttributeError；四类都被 serve 兜成「服务内部错误」并把 Python
    异常文本回给客户端。协议上这属于**参数非法**，与 MCP 面的参数准入同一纪律。
    """

    def setUp(self):
        self.srv = _ready(lsp.LspServer(root=ROOT, today="2026-10-08"))
        self.uri = "file:///tmp_admit.md"

    def _req(self, mid, method, params):
        out = self.srv.handle({"jsonrpc": "2.0", "id": mid, "method": method, "params": params})
        self.assertEqual(1, len(out))
        return out[0]

    def test_bad_position_is_invalid_params(self):
        msg = self._req(1, lsp.M_HOVER, {"textDocument": {"uri": self.uri},
                                         "position": {"line": "a", "character": []}})
        self.assertEqual(lsp.INVALID_PARAMS, msg["error"]["code"])
        self.assertIn("position", msg["error"]["message"])

    def test_missing_uri_is_invalid_params(self):
        msg = self._req(2, lsp.M_COMPLETION, {})
        self.assertEqual(lsp.INVALID_PARAMS, msg["error"]["code"])

    def test_bad_diagnostics_is_invalid_params(self):
        for bad in ({"code": "trailing_ws"}, "trailing_ws", [1, 2]):
            msg = self._req(3, lsp.M_CODE_ACTION,
                            {"textDocument": {"uri": self.uri},
                             "context": {"diagnostics": bad}})
            self.assertEqual(lsp.INVALID_PARAMS, msg["error"]["code"], bad)
            self.assertIn("diagnostics", msg["error"]["message"])

    def test_non_string_query_is_invalid_params(self):
        msg = self._req(4, lsp.M_WORKSPACE_SYMBOL, {"query": 5})
        self.assertEqual(lsp.INVALID_PARAMS, msg["error"]["code"])

    def test_bad_notifications_do_not_corrupt_state(self):
        srv = self.srv
        srv.handle({"jsonrpc": "2.0", "method": lsp.M_DID_OPEN,
                    "params": {"textDocument": {"uri": self.uri, "text": 123}}})
        self.assertNotIn(self.uri, srv.docs, "非字符串正文不得进状态")
        srv.handle({"jsonrpc": "2.0", "method": lsp.M_DID_OPEN,
                    "params": {"textDocument": {"uri": self.uri, "text": "# T\n"}}})
        srv.handle({"jsonrpc": "2.0", "method": lsp.M_DID_CHANGE,
                    "params": {"textDocument": {"uri": self.uri}, "contentChanges": ["oops"]}})
        self.assertEqual("# T\n", srv.docs[self.uri]["text"], "坏 contentChanges 不得改正文")
        # 会话仍能服务后续请求
        msg = self._req(5, lsp.M_DOCUMENT_SYMBOL, {"textDocument": {"uri": self.uri}})
        self.assertIn("result", msg)


class TestLifecycleStateMachine(unittest.TestCase):
    """LSP 会话状态机：未 initialize 只接受 initialize；一个会话只允许一次；shutdown 后只接受 exit。

    内部差距实证（2026-10-08 实测）：旧实现对这三类**一律照常服务**——
    ① 未初始化就服务，会用 CLI 默认根（还没采纳客户端 rootUri）去解析，结果可能是错的；
    ② 重复 initialize 规范要求回 InvalidRequest；
    ③ shutdown 之后继续服务掩盖客户端 bug，并使「会话已收摊」在两端口径不一。
    """

    def setUp(self):
        self.srv = lsp.LspServer(root=ROOT, explicit_root=True)

    def _call(self, rid, method, params=None):
        return self.srv.handle({"jsonrpc": "2.0", "id": rid, "method": method,
                                "params": params or {}})[0]

    def test_request_before_initialize_is_server_not_initialized(self):
        msg = self._call(1, lsp.M_COMPLETION, {"textDocument": {"uri": "file:///x.md"}})
        self.assertEqual(lsp.SERVER_NOT_INITIALIZED, msg["error"]["code"])
        self.assertIn("initialize", msg["error"]["message"])

    def test_notification_before_initialize_is_ignored_not_an_error(self):
        out = self.srv.handle({"jsonrpc": "2.0", "method": lsp.M_DID_OPEN,
                               "params": {"textDocument": {"uri": "file:///x.md", "text": "# T\n"}}})
        self.assertEqual([], out, "通知没有应答位：静默忽略，不回错误")

    def test_second_initialize_is_invalid_request(self):
        first = self._call(1, lsp.M_INITIALIZE)
        self.assertIn("result", first)
        second = self._call(2, lsp.M_INITIALIZE)
        self.assertEqual(lsp.INVALID_REQUEST, second["error"]["code"])

    def test_requests_after_shutdown_are_invalid_request(self):
        self._call(1, lsp.M_INITIALIZE)
        self.assertIn("result", self._call(2, lsp.M_SHUTDOWN))
        after = self._call(3, lsp.M_HOVER, {"textDocument": {"uri": "file:///x.md"},
                                            "position": {"line": 0, "character": 0}})
        self.assertEqual(lsp.INVALID_REQUEST, after["error"]["code"])
        # exit 始终放行（由 serve 循环收口退出码）
        self.assertEqual([], self.srv.handle({"jsonrpc": "2.0", "method": lsp.M_EXIT}))

    def test_shutdown_without_initialize_is_refused(self):
        msg = self._call(1, lsp.M_SHUTDOWN)
        self.assertEqual(lsp.SERVER_NOT_INITIALIZED, msg["error"]["code"])


class TestReferencesFace(unittest.TestCase):
    """引用面：结构化引用 → Location[]；未登记即空表；includeDeclaration 语义；参数准入。

    内部差距实证（2026-10-08）：编辑器此前只有「跳定义」——问「谁引用了这个事件」没有承接面，
    而 NF 的引用是**有登记**的（registry 的发布/订阅、挂载、域包采用）。这里把四件事钉住：
    给出位置、位置是 file: uri、未知 token 不猜、includeDeclaration=false 会剔除声明自身。
    """

    def setUp(self):
        self.srv = _ready(lsp.LspServer(root=ROOT, explicit_root=True))
        self.uri = "file:///" + ROOT.replace(BS, "/").lstrip("/") + "/tmp_refs.md"
        open_doc(self.srv, self.uri, "# 引用探针\n事件 narrative_event\n")

    def _refs(self, line=1, character=4, context=None):
        params = {"textDocument": {"uri": self.uri},
                  "position": {"line": line, "character": character}}
        if context is not None:
            params["context"] = context
        return self.srv.handle({"jsonrpc": "2.0", "id": 1, "method": lsp.M_REFERENCES,
                                "params": params})[0]

    def test_event_references_return_file_locations(self):
        locs = self._refs()["result"]
        self.assertGreaterEqual(len(locs), 2, "事件应给出发布/订阅位置")
        self.assertTrue(all(x["uri"].startswith("file:") for x in locs))
        self.assertTrue(all(x["range"]["start"]["line"] >= 0 for x in locs))

    def test_unknown_token_is_empty_not_fuzzy(self):
        open_doc(self.srv, self.uri, "# 探针\n此处没有登记符号\n")
        self.assertEqual([], self._refs(line=1, character=3)["result"])

    def test_include_declaration_false_drops_the_declaration(self):
        class _Shim:
            """桩索引：让「引用」集合里含符号自身的定义位置（考 includeDeclaration 语义）。"""

            sig = ()

            @staticmethod
            def references(_tok):
                return [{"name": "X", "kind": "module", "path": "a.md", "line": 0,
                         "why": "自引用"}]

            @staticmethod
            def resolve(_tok):
                return {"path": "a.md", "line": 0}

        self.srv._index = _Shim()
        self.srv._sig_at = lsp.time.monotonic()          # 落在 TTL 内：直接复用桩索引
        self.assertEqual(1, len(self._refs()["result"]))
        self.assertEqual([], self._refs(context={"includeDeclaration": False})["result"])

    def test_missing_position_is_invalid_params(self):
        out = self.srv.handle({"jsonrpc": "2.0", "id": 2, "method": lsp.M_REFERENCES,
                               "params": {"textDocument": {"uri": self.uri}}})[0]
        self.assertEqual(lsp.INVALID_PARAMS, out["error"]["code"])


class TestGeneratedConfigIsUsable(unittest.TestCase):
    """生成的编辑器配置必须**真的能用**：TOML 解析通过 + 结构对 + 危险路径不破格式。

    内部差距实证（2026-10-08）：配置面此前只有「字符串包含」判据（含 scripts/nf.py 与 "lsp"）——
    生成器若把 Windows 路径或含空格路径写成**非法 TOML**（例如把反斜杠留在基本字符串里），旧判据
    全绿，用户粘进 languages.toml 才炸。这里钉三件事：① 四种根（POSIX / Windows / 含空格 /
    盘符+空格）下生成件都能被 tomllib 解析；② 解析出的结构就是 Helix 要的样子；③ 文档里那段
    （用户真正复制的东西）也必须是合法 TOML——三语各查一遍。
    """

    BS = chr(92)
    ROOTS = ("/repo", "C:" + BS + "Users" + BS + "x" + BS + "NarrativeForge-main",
             "/tmp/my repo", "C:/repo with space")

    @staticmethod
    def _body(editor, root):
        cfg = lsp_client.render_client_config(editor, root)
        return "\n".join(cfg.split("\n")[1:])          # 去掉生成器首行标题

    def test_helix_config_is_valid_toml_for_every_root(self):
        import tomllib
        for root in self.ROOTS:
            data = tomllib.loads(self._body("helix", root))
            self.assertEqual(["nf-lsp"],
                             (data["language"][0] or {}).get("language-servers"), root)
            srv = data["language-server"]["nf-lsp"]
            self.assertEqual("python", srv["command"], root)
            self.assertEqual("lsp", srv["args"][-1], root)
            self.assertTrue(srv["args"][0].endswith("scripts/nf.py"), root)
            self.assertNotIn(self.BS, srv["args"][0],
                             "路径里的反斜杠必须先折成正斜杠（否则 TOML 基本字符串非法）：%s" % root)

    def test_lua_and_elisp_blocks_are_delimiter_balanced(self):
        for editor in ("neovim", "emacs"):
            body = self._body(editor, "C:" + self.BS + "a b" + self.BS + "repo")
            self.assertEqual(body.count("("), body.count(")"), editor)
            self.assertEqual(body.count("{"), body.count("}"), editor)

    def test_doc_toml_blocks_parse_in_every_locale(self):
        import tomllib
        fence = chr(96) * 3
        pattern = fence + "toml" + "\n" + "(.*?)" + fence
        checked = 0
        for rel in ("docs/lsp.md", "docs/en/lsp.md", "docs/ja/lsp.md"):
            text = (Path(ROOT) / rel).read_text(encoding="utf-8")
            blocks = re.findall(pattern, text, re.S)
            self.assertTrue(blocks, "%s 缺 toml 配置块（用户复制的那段）" % rel)
            for block in blocks:
                tomllib.loads(block)                   # 不合法即抛
                checked += 1
        self.assertGreaterEqual(checked, 3, "文档配置块过少（判据可能空转）")


class TestFoldingRanges(unittest.TestCase):
    """折叠面：标题小节（到下一个同级/更高级标题前）+ 代码围栏；单行与空文档不给。

    内部差距实证（2026-10-08）：本仓长档常见（02_联动注册表.md 1151 行、CHANGELOG 1538 行），
    此前 LSP 面**没有折叠能力**，编辑器里只能一路滚。折叠的真源是标题结构——与大纲同一份口径，
    故它是「派生自既有真源」的能力；本件钉住三件事：嵌套小节的**边界**、围栏可折、不给空跨。
    """

    NL = chr(10)
    F = chr(96) * 3

    def test_sections_end_before_same_or_higher_level(self):
        text = ("# A" + self.NL + "x" + self.NL + "## B" + self.NL + "y" + self.NL
                + "# C" + self.NL + "z" + self.NL)
        got = lsp_doc.folding_ranges(text)
        self.assertEqual([{"startLine": 0, "endLine": 3, "kind": "region"},
                          {"startLine": 2, "endLine": 3, "kind": "region"},
                          {"startLine": 4, "endLine": 5, "kind": "region"}], got)

    def test_fence_block_is_foldable(self):
        text = self.F + self.NL + "code" + self.NL + self.F + self.NL
        self.assertEqual([{"startLine": 0, "endLine": 2, "kind": "region"}],
                         lsp_doc.folding_ranges(text))

    def test_single_line_and_empty_documents_give_no_range(self):
        self.assertEqual([], lsp_doc.folding_ranges("# A" + self.NL))
        self.assertEqual([], lsp_doc.folding_ranges(""))

    def test_fence_content_is_not_treated_as_headings(self):
        text = ("# A" + self.NL + self.F + self.NL + "# 不是标题" + self.NL + self.F + self.NL
                + "## B" + self.NL + "x" + self.NL)
        got = lsp_doc.folding_ranges(text)
        self.assertIn({"startLine": 1, "endLine": 3, "kind": "region"}, got)
        self.assertFalse([r for r in got if r["startLine"] == 2], "围栏内的 # 不得成为折叠起点")

    def test_protocol_level_request_and_admission(self):
        srv = _ready(lsp.LspServer(root=ROOT, explicit_root=True))
        uri = "file:///tmp_fold.md"
        srv.handle({"jsonrpc": "2.0", "method": lsp.M_DID_OPEN,
                    "params": {"textDocument": {"uri": uri,
                                                "text": "# 一" + self.NL + "正文" + self.NL
                                                        + "## 二" + self.NL + "正文" + self.NL}}})
        out = srv.handle({"jsonrpc": "2.0", "id": 1, "method": lsp.M_FOLDING_RANGE,
                          "params": {"textDocument": {"uri": uri}}})[0]
        self.assertEqual(2, len(out["result"]))
        bad = srv.handle({"jsonrpc": "2.0", "id": 2, "method": lsp.M_FOLDING_RANGE,
                          "params": {}})[0]
        self.assertEqual(lsp.INVALID_PARAMS, bad["error"]["code"])


if __name__ == "__main__":
    unittest.main()
