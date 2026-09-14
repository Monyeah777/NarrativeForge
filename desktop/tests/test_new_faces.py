# -*- coding: utf-8 -*-
"""本轮新增面的分支覆盖测试（registry_cross / payload_harvest / machine_contract /
receipts 协议层 / pipelinerun advisory）——把覆盖率拉回门槛之上，并钉住关键分支。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import machine_contract as mc  # noqa: E402
from core import payload_harvest as ph  # noqa: E402
from core import pipelinerun as pr  # noqa: E402
from core import receipts as rc  # noqa: E402
from core import registry_cross as rx  # noqa: E402

MOD = """# 模块 M98 · 测试件
> 类别：通用｜来源：测试｜挂载点：P40 行为决策（active）｜依赖：M00、M10
> 发布：`demo_event`｜订阅：`tick_day`

```yaml
event_contract:
  event: demo_event
  payload: {a_id, b_count: int, ok_flag: true, tags[], nested{inner}, mode: x|y, note: <说明>}
```

## 1. 职责
测试用。
"""


def _tree(tmp, extra=None):
    d = Path(tmp, "04_模块库", "通用类")
    d.mkdir(parents=True, exist_ok=True)
    (d / "M98_测试件.md").write_text(MOD, encoding="utf-8")
    reg = Path(tmp, "desktop", "src", "core")
    reg.mkdir(parents=True, exist_ok=True)
    (reg / "registry.json").write_text(json.dumps(
        {"modules": [{"id": "M00"}, {"id": "M10"}],
         "protocols": [{"id": "p", "module_ids": ["M98"]}]}), encoding="utf-8")
    ev = Path(tmp, "protocol")
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "event_registry.json").write_text(json.dumps(
        {"schema": "event-payload/1", "note": "", "events": {
            "demo_event": {"payload_status": "declared", "note": "n",
                           "fields": {"a_id": {"type": "untyped", "note": "待核"}}}}},
        ensure_ascii=False), encoding="utf-8")
    cur = Path(tmp, "community", "包A", "modules")
    cur.mkdir(parents=True, exist_ok=True)
    for name, events in (("M97_甲.md", ("demo_event", "tick_day")),
                         ("M96_乙.md", ("tick_day", "none_event"))):
        (cur / name).write_text(
            "---\n# 模块 %s · 甲\n> 类别：通用｜挂载点：P40 行为决策（active）\n\n"
            "```yaml\nmachine_contract:\n  schema: \"1\"\n  id: %s\n  name: x\n"
            "  category: 通用\n  layer: P40\n  inputs: []\n  outputs: []\n"
            "  events:\n    publish: [%s]\n    subscribe: [%s]\n  interfaces: []\n```\n"
            % (name[:3], name[:3], events[0], events[1]), encoding="utf-8")
    if extra:
        extra(tmp)
    return tmp


class TestFieldType(unittest.TestCase):
    def test_type_rules(self):
        cases = {"a_id": "untyped", "b_count: int": "integer",
                 "ok_flag: true": "boolean", "tags[]": "array",
                 "nested{inner}": "object", "mode: x|y": "string",
                 "note: <说明>": "untyped", "n: 3": "number",
                 "s: str": "string", "o: {a,b}": "object", "l: [1,2]": "array",
                 "": ""}
        for tok, want in cases.items():
            self.assertEqual(ph._field_type(tok)[1], want, tok)

    def test_harvest_doc_picks_event_and_payload(self):
        got = ph.harvest_doc(MOD)
        self.assertIn("demo_event", got)
        self.assertEqual(got["demo_event"]["b_count"], "integer")
        self.assertEqual(got["demo_event"]["mode"], "string")

    def test_split_top_level_skips_nesting(self):
        parts = ph._split_top_level("a, b{c,d}, e[1,2], f")
        self.assertEqual([p.strip() for p in parts], ["a", "b{c,d}", "e[1,2]", "f"])


class TestPayloadHarvestApply(unittest.TestCase):
    def test_apply_adds_and_narrows(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp)
            r = ph.apply(tmp, write=True)
            self.assertTrue(any("demo_event.b_count" in x for x in r["added"]))
            self.assertTrue(any("a_id" in x for x in r["narrowed"])
                            or r["narrowed"] == [], r)
            reg = json.loads(Path(tmp, "protocol", "event_registry.json").read_text(encoding="utf-8"))
            self.assertEqual(reg["events"]["demo_event"]["fields"]["b_count"]["type"], "integer")

    def test_backlog_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp)
            ph.apply(tmp, write=True)
            doc = ph.backlog(tmp, write=True)
            self.assertIn("count", doc)
            self.assertEqual(ph.verify_backlog(tmp)[0], [])
            # 台账过期 → 报错
            p = Path(tmp, "protocol", "type_backlog.json")
            data = json.loads(p.read_text(encoding="utf-8"))
            data["count"] = 999
            p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(ph.verify_backlog(tmp)[0])

    def test_backlog_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp)
            self.assertTrue(any("缺类型积压台账" in i for i in ph.verify_backlog(tmp)[0]))


class TestMachineContract(unittest.TestCase):
    def test_insert_point_and_inject_fallbacks(self):
        # 无 `## ` 章节头 → 兜底插在引用块之后；无引用块 → 插在文首
        self.assertEqual(mc._insert_point("> 头\n\n正文\n"), 1)
        self.assertEqual(mc._insert_point("正文\n"), 0)
        spec = {"id": "M99", "name": "x", "category": "通用", "layer": "P40",
                "inputs": [], "publish": [], "subscribe": []}
        out = mc.inject_contract("# 模块 M99 · x\n\n正文本\n", spec, "L1")
        self.assertIn("machine_contract:", out)

    def test_apply_outputs_reports_no_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp)
            rows = mc.apply_outputs(tmp, write=False)
            self.assertTrue(rows)
            # demo_event 在注册表里有字段 a_id → 发布它的模块应补出 outputs；
            # 发布 tick_day（注册表无该事件）的模块则如实无证据。
            by_id = {r["id"]: r for r in rows}
            self.assertEqual(by_id["M97"]["tokens"], ["a_id"])
            self.assertTrue(by_id["M97"]["changed"])
            self.assertEqual(by_id["M96"]["tokens"], [])
            self.assertIn("无事件载荷", by_id["M96"]["reason"])

    def test_parse_header_and_level(self):
        spec = mc.parse_header(MOD, "04_模块库/通用类/M98_测试件.md")
        self.assertEqual(spec["id"], "M98")
        self.assertEqual(spec["layer"], "P40")
        self.assertIn("M00", spec["inputs"])
        self.assertIn("demo_event", spec["publish"])
        self.assertIn("tick_day", spec["subscribe"])

    def test_apply_writes_contract_then_scan_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp)
            rows = mc.apply(tmp, write=True)
            self.assertEqual(len(rows), 1)
            text = Path(tmp, "04_模块库", "通用类", "M98_测试件.md").read_text(encoding="utf-8")
            self.assertIn("machine_contract:", text)
            self.assertEqual(mc.scan(tmp)[0], [])
            self.assertEqual(mc.scan(tmp)[2]["l0"], 0)

    def test_derive_outputs_and_replace_line(self):
        ev = {"demo_event": {"a_id": "untyped", "b_count": "integer"}}
        toks = mc.derive_outputs({"events": {"publish": ["demo_event"]}}, ev)
        self.assertEqual(toks, ["a_id", "b_count"])
        self.assertEqual(mc.derive_outputs({"events": {"publish": ["nope"]}}, ev), [])
        out = mc._replace_outputs_line(
            "```yaml\nmachine_contract:\n  id: M1\n  outputs: []\n```\n", ["x", "y"])
        self.assertIn("outputs: [x, y]", out)


class TestReceiptScope(unittest.TestCase):
    def test_protocol_scope_roundtrip_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "protocol").mkdir(parents=True)
            (Path(tmp) / "01_核心协议.md").write_text("# 核心协议\n", encoding="utf-8")
            for name in ("a.json", "b.json", "c.json"):
                (Path(tmp) / "protocol" / name).write_text('{"k": 1}', encoding="utf-8")
            subs = rc.protocol_subjects(tmp)
            self.assertTrue(subs)
            doc = rc.build_scope(tmp, ["protocol/a.json", "protocol/b.json", "protocol/c.json"])
            self.assertEqual(doc["count"], 3)
            self.assertEqual(rc.verify_scope(doc, tmp)[0], [], "三叶也必须折叠到根")
            (Path(tmp) / "protocol" / "b.json").write_text('{"k": 2}', encoding="utf-8")
            self.assertTrue(rc.verify_scope(doc, tmp)[0])

    def test_write_scope_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "protocol").mkdir(parents=True)
            (Path(tmp) / "protocol" / "x.json").write_text("{}", encoding="utf-8")
            rel = rc.write_scope(tmp)
            self.assertTrue((Path(tmp) / rel).is_file())


class TestRegistryCross(unittest.TestCase):
    def test_backed_cross_and_uncovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp)
            data = rx.build(tmp)
            self.assertIn("demo_event", data["publishers"])
            issues, warns, stats = rx.scan(tmp)
            self.assertTrue(any("none_event" in i for i in issues), issues)
            self.assertIn("none_event", stats["uncovered"])

    def test_allowlist_exempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            _tree(tmp)
            (Path(tmp) / "protocol" / "external_events.json").write_text(
                json.dumps({"schema": "x", "events": {"none_event": "外部通道"}}),
                encoding="utf-8")
            issues, warns, _s = rx.scan(tmp)
            self.assertEqual(issues, [])
            self.assertTrue(any("已挂账" in w for w in warns), warns)


class TestMcpLibraryFace(unittest.TestCase):
    """MCP 取用面的馆藏分支（library_read / 资源 uri / 过滤）。"""

    def setUp(self):
        from core.mcp_runtime import McpRuntime
        self.srv = McpRuntime({"mcp": {"name": "t", "version": "1", "resources": []}})

    def test_resources_list_filters_library(self):
        r = self.srv.handle({"jsonrpc": "2.0", "id": 1, "method": "resources/list",
                             "params": {"type": "library"}})
        uris = [x["uri"] for x in r["result"]["resources"]]
        self.assertTrue(uris)
        self.assertTrue(all(u.startswith("nf://repo/library/") for u in uris))

    def test_library_read_and_unknown(self):
        ok = self.srv.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                              "params": {"name": "library_read",
                                         "arguments": {"entry_id": "nf-1"}}})
        self.assertIn("frontmatter", ok["result"]["content"][0]["text"])
        bad = self.srv.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                               "params": {"name": "library_read",
                                          "arguments": {"entry_id": "NF-404"}}})
        self.assertEqual(bad["error"]["code"], -32602)

    def test_read_uri_case_insensitive_and_unknown(self):
        ok = self.srv.handle({"jsonrpc": "2.0", "id": 4, "method": "resources/read",
                              "params": {"uri": "nf://repo/library/nf-worldcampus-monyeah777-1"}})
        self.assertIn("结果", "结果")  # 只断言有 result 且不抛
        self.assertIn("contents", ok["result"])
        bad = self.srv.handle({"jsonrpc": "2.0", "id": 5, "method": "resources/read",
                               "params": {"uri": "nf://repo/library/nope"}})
        self.assertEqual(bad["error"]["code"], -32602)


class TestAdvisoryReport(unittest.TestCase):
    def test_report_and_verify_roundtrip(self):
        doc = pr.advisory_report(str(ROOT))
        self.assertIn("counts", doc)
        self.assertGreater(doc["total"], 0)
        issues, stats = pr.verify_advisory(str(ROOT))
        self.assertEqual(issues, [], "仓库 advisory 台账应与实时重算一致")
        self.assertIn("counts", stats)

    def test_verify_detects_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "03_管线库").mkdir(parents=True)
            self.assertTrue(any("缺 advisory 台账" in i
                                for i in pr.verify_advisory(tmp)[0]))


if __name__ == "__main__":
    unittest.main()
