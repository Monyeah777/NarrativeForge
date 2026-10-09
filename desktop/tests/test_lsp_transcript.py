# -*- coding: utf-8 -*-
"""LSP 会话转写：端到端**帧级金标**（客户端帧序列 → 服务端应答）的常驻判据。

内部差距实证（2026-10-08）：编辑器面的回归此前全是「直接调 handle()」的行为断言加传输层
加固断言——**没有一件端到端帧级金标**：真实客户端发什么（Content-Length 分帧、消息次序、
位置编码）到服务端回什么（逐条应答形状与次序）这条链没有可 diff 的产物。

判据三层：
1. **可移植**：夹具不得含机器绝对路径（同 engine/dotnet/probes 的 portable 纪律）；
2. **逐字节对账**：用夹具里的入站帧真跑一次 serve，出站消息与夹具完全相等（含摘要）；
3. **不空转**：应答面覆盖必须有下限（诊断/补全/悬停/跳定义/大纲/工作区符号/quickfix）。

生成器是 scripts/build_lsp_transcript.py（--write 重签、--check 只读对账）；本件复用它的
取帧/归一/摘要实现（单一实现，不在测试里另抄一份）。
"""
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "desktop" / "src"))
FIXTURE_REL = "desktop/tests/fixtures/lsp/session.json"
BUILDER_REL = "scripts/build_lsp_transcript.py"
MACHINE_PATH = re.compile(r"C:[\\/]Users[\\/]|/Users/[A-Za-z]|/home/[a-z]")


def _load_builder():
    spec = importlib.util.spec_from_file_location("nf_build_lsp_transcript", ROOT / BUILDER_REL)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestLspSessionTranscript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = _load_builder()
        cls.path = ROOT / FIXTURE_REL
        cls.text = cls.path.read_text(encoding="utf-8")
        cls.fixture = json.loads(cls.text)

    def test_fixture_is_portable(self):
        self.assertEqual("nf-lsp-transcript/1", self.fixture["schema"])
        self.assertIsNone(MACHINE_PATH.search(self.text),
                          "夹具不得含机器绝对路径（修复指引：归一成 <ROOT> 后 --write）")
        self.assertIn(self.builder.ROOT_PLACEHOLDER, self.text)

    def test_live_run_round_trips_through_client_frames(self):
        import io
        msgs = self.fixture["client_messages"]
        payload = b"".join(self.builder._frame(m) for m in msgs)
        out = io.BytesIO()
        srv = self.builder.lsp.LspServer(root=str(ROOT), today=self.fixture["today"],
                                         explicit_root=True)
        rc = srv.serve(stdin=io.BytesIO(payload), stdout=out)
        got = self.builder.normalize(self.builder._parse_frames(out.getvalue()))
        self.assertEqual(self.fixture["server_messages"], got,
                         "出站消息与夹具不一致（协议面漂移）")
        self.assertEqual(self.fixture["exit_code"], rc)

    def test_digest_matches_and_coverage_is_not_vacuous(self):
        server = self.fixture["server_messages"]
        self.assertEqual(self.fixture["digest"], self.builder.digest_of(server))
        self.assertGreaterEqual(len(server), 18, "应答过少（判据可能空转）")
        published = [m for m in server if m.get("method") == "textDocument/publishDiagnostics"]
        self.assertGreaterEqual(len(published), 3, "诊断推送次数过少")
        self.assertTrue(any(d.get("code") == "trailing_ws"
                            for d in published[0]["params"]["diagnostics"]),
                        "首推诊断缺目标规则")
        ids = {m.get("id") for m in server if "id" in m}
        for rid in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17):
            self.assertIn(rid, ids, "缺 id=%s 的应答" % rid)

    def test_lifecycle_and_dollar_edges_are_pinned(self):
        """帧级钉住协议边界：未声明能力 / 未知方法 / 未知 $/ 请求 / shutdown 之后。

        2026-10-08 扩金标：这些入站面编辑器真会发（willSave、watchedFiles、$/ 心跳、探活），此
        前只有直接调 handle() 的断言；扩到帧级后，连「$/ 请求必须回错误」这条规范口径也在金标里。
        """
        by_id = {m["id"]: m for m in self.fixture["server_messages"] if "id" in m}
        self.assertEqual(-32601, by_id[9]["error"]["code"], "未声明的 willSaveWaitUntil 应回 -32601")
        self.assertIsNone(by_id[10]["result"], "无符号词悬停应为 null")
        self.assertEqual([], by_id[11]["result"], "工作区符号无命中应为空表")
        self.assertEqual(-32601, by_id[12]["error"]["code"], "未知方法应回 -32601")
        self.assertEqual(-32601, by_id[13]["error"]["code"],
                         "未知 $/ **请求**必须回 -32601（静默不回会让客户端一直等）")
        self.assertEqual([], by_id[14]["result"]["items"], "已关闭文档的补全面应为空")
        self.assertEqual(-32600, by_id[15]["error"]["code"], "shutdown 之后的请求应回 -32600")
        refs = by_id[16]["result"]
        self.assertGreaterEqual(len(refs), 2, "事件引用面应给出发布/订阅位置")
        self.assertTrue(all(x["uri"].startswith("file:") for x in refs))
        folds = by_id[17]["result"]
        self.assertGreaterEqual(len(folds), 1, "折叠面应给出至少一条区间")
        self.assertTrue(all(r["endLine"] > r["startLine"] for r in folds), "折叠不得出现空跨")
        ignored = [m for m in self.fixture["client_messages"]
                   if m.get("method") in ("textDocument/willSave", "workspace/didChangeWatchedFiles",
                                          "workspace/didChangeConfiguration", "$/setTrace",
                                          "$/cancelRequest", "textDocument/didSave")]
        self.assertGreaterEqual(len(ignored), 6, "静默面入站帧过少（判据可能空转）")
        # 请求方法当**通知**发：金标里没有任何应答对应它——哪天回了一条（id=null），出站消息
        # 与夹具就不再逐字节相等（这正是本件存在的意义）。
        from core import lsp as _lsp
        silent_req = [m for m in self.fixture["client_messages"]
                      if "id" not in m and m.get("method") in _lsp._REQUESTS]
        self.assertGreaterEqual(len(silent_req), 1, "缺「请求当通知发」的入站帧")

    def test_generator_recompute_equals_on_disk_fixture(self):
        want = self.builder.render(self.builder.build())
        self.assertEqual(want, self.text,
                         "在盘夹具与实时重算不一致（修复指引：复核后跑 --write 重签）")


#: 声明能力 → 该能力在转写里被真正跑到的应答 id（声明与证据必须对上）
CAPABILITY_EVIDENCE = {
    "hoverProvider": 3,
    "referencesProvider": 16,
    "foldingRangeProvider": 17,
    "completionProvider": 2,
    "definitionProvider": 4,
    "documentSymbolProvider": 5,
    "workspaceSymbolProvider": 6,
    "codeActionProvider": 7,
}


class TestDeclaredCapabilitiesHaveEvidence(unittest.TestCase):
    """服务端**声明**的能力必须在转写里有对应应答——声明不能没有证据。

    为什么需要：能力声明（initialize）与能力实现是两处代码；只核「声明了」等于把
    「说了」当「做到了」。转写是端到端实跑产物，正好当这条对账的证据面。
    """

    def test_every_declared_capability_is_exercised(self):
        fixture = json.loads((ROOT / FIXTURE_REL).read_text(encoding="utf-8"))
        server = fixture["server_messages"]
        init = next(m for m in server if m.get("id") == 1)
        caps = init["result"]["capabilities"]
        ids = {m.get("id") for m in server if "id" in m}
        for key, rid in CAPABILITY_EVIDENCE.items():
            if key in caps:
                self.assertIn(rid, ids, "声明了 %s 但转写里没有对应应答（id=%s）" % (key, rid))
        published = [m for m in server if m.get("method") == "textDocument/publishDiagnostics"]
        self.assertTrue(published, "同步能力（openClose）应有诊断推送作证据")


if __name__ == "__main__":
    unittest.main()
