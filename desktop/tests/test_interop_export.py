#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""互操作导出面单测（OpenAPI 3.1 / AsyncAPI 3.0 / in-toto v1 / SPDX 2.3 / CloudEvents）。

两件事必须被钉住：① 派生面**覆盖完整**（声明件里有多少端点/事件/回执，导出面就有多少）；
② **确定性**（同输入两次渲染逐字节一致——否则外部工具链无法做内容寻址/比对）。
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

if str(Path(__file__).resolve().parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import interop_export as ie  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[2])


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


class InteropExportTest(unittest.TestCase):
    def test_repo_export_is_consistent(self):
        issues, stats = ie.verify(ROOT)
        self.assertEqual(issues, [], "仓库导出面须自洽：%s" % issues[:3])
        self.assertGreaterEqual(stats["openapi_paths"], 8)
        self.assertGreaterEqual(stats["asyncapi_channels"], 40)
        self.assertGreaterEqual(stats["intoto_subjects"], 40)

    def test_render_is_byte_deterministic(self):
        for kind in ie.KINDS:
            self.assertEqual(ie.render(kind, ROOT), ie.render(kind, ROOT))

    def test_openapi_covers_every_declared_endpoint(self):
        contract = json.loads(Path(ROOT, ie.CONTRACT_REL).read_text(encoding="utf-8"))
        doc = ie.openapi_doc(ROOT)
        want = {e["path"] for e in contract["endpoints"]}
        self.assertEqual(set(doc["paths"]), want)
        for path, ops in doc["paths"].items():
            for method, op in ops.items():
                self.assertEqual(op["operationId"],
                                 next(e["id"] for e in contract["endpoints"]
                                      if e["path"] == path and e["method"].lower() == method))
                self.assertIn("default", op["responses"])
        self.assertIn("NfError", doc["components"]["schemas"])
        self.assertIn("title", doc["x-nf-error-mapping"])

    def test_asyncapi_covers_every_event_and_unique_ce_type(self):
        reg = json.loads(Path(ROOT, ie.EVENTS_REL).read_text(encoding="utf-8"))
        doc = ie.asyncapi_doc(ROOT)
        want = set(reg["events"])
        got = {k.split("/", 1)[1] for k in doc["channels"]}
        self.assertEqual(got, want)
        ce = [c["x-nf-cloudevents"]["type"] for c in doc["channels"].values()]
        self.assertEqual(len(set(ce)), len(ce))
        for name, msg in doc["components"]["messages"].items():
            self.assertEqual(msg["name"], name)
            self.assertEqual(msg["payload"]["type"], "object")

    def test_intoto_statement_shape(self):
        st = ie.intoto_statement(ROOT)
        self.assertEqual(st["_type"], "https://in-toto.io/Statement/v1")
        rec = json.loads(Path(ROOT, ie.RECEIPTS_REL).read_text(encoding="utf-8"))
        self.assertEqual(len(st["subject"]), len(rec["entries"]))
        for s in st["subject"]:
            self.assertRegex(s["digest"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(st["predicateType"].startswith("https://"))

    def test_sbom_declares_project_and_registered_dependencies(self):
        sb = ie.sbom_doc(ROOT)
        self.assertEqual(sb["spdxVersion"], "SPDX-2.3")
        # 外部 meta-schema 实测：creationInfo.created 必填 → 本仓取「声明日期最大值」（非墙钟）
        self.assertRegex(sb["creationInfo"]["created"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual(sb["creationInfo"]["created"],
                         "%sT00:00:00Z" % ie._declared_max_date(ROOT))
        self.assertNotIn("documentComment", sb, "SPDX 2.3 词表无 documentComment（用 comment）")
        names = [p["name"] for p in sb["packages"]]
        self.assertIn("NarrativeForge", names)
        from core import purity_scan as ps
        for dep in list(ps.HARD_ALLOW) + list(ps.SOFT_IMPORTS):
            self.assertIn(dep, names, "登记依赖须出现在 SBOM：%s" % dep)
        self.assertTrue([r for r in sb["relationships"]
                         if r["relationshipType"] == "DESCRIBES"])

    def test_mutation_missing_endpoint_coverage_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ie.CONTRACT_REL, json.dumps({
                "schema": "nf-endpoint/1", "status": "proposed",
                "conventions": {}, "endpoints": [
                    {"id": "a", "method": "GET", "path": "/a", "maps_to": "nf doctor"},
                    {"id": "b", "method": "GET", "path": "/b", "maps_to": "nf doctor"}]}))
            doc = ie.openapi_doc(tmp)
            self.assertEqual(set(doc["paths"]), {"/a", "/b"})
            issues, _ = ie.verify(tmp)
            # 真源缺失须 fail-closed（事件登记 / 协议层回执未落）
            self.assertTrue(any(ie.EVENTS_REL in i for i in issues), issues)
            self.assertTrue(any(ie.RECEIPTS_REL in i for i in issues), issues)

    def test_mutation_bad_digest_captured(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ie.CONTRACT_REL, json.dumps(
                {"schema": "nf-endpoint/1", "status": "proposed", "conventions": {},
                 "endpoints": [{"id": "a", "method": "GET", "path": "/a",
                                "maps_to": "nf doctor"}]}))
            _write(tmp, ie.EVENTS_REL, json.dumps({"events": {}}))
            _write(tmp, ie.RECEIPTS_REL, json.dumps({
                "schema": "nf-receipts/1", "algorithm": "x", "count": 1,
                "root": "y", "entries": [{"path": "a.md", "digest": "nothex"}]}))
            issues, _ = ie.verify(tmp)
            self.assertTrue(any("sha256" in i for i in issues), issues)

    def test_empty_sources_yield_empty_channels_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = ie.asyncapi_doc(tmp)
            self.assertEqual(doc["channels"], {})
            self.assertEqual(doc["x-nf-events"], 0)

    def test_slsa_provenance_shape_and_honesty(self):
        sl = ie.slsa_provenance(ROOT)
        self.assertEqual(sl["_type"], "https://in-toto.io/Statement/v1")
        self.assertEqual(sl["predicateType"], "https://slsa.dev/provenance/v1")
        pred = sl["predicate"]
        self.assertIn("buildDefinition", pred)
        self.assertIn("runDetails", pred)
        self.assertEqual(pred["buildDefinition"]["buildType"],
                         "https://narrativeforge.dev/buildtypes/local-gate/v1")
        note = pred["runDetails"]["metadata"]["note"]
        self.assertIn("不构成 SLSA 等级声明", note, "本地门禁不得虚标 SLSA 等级")
        self.assertRegex(pred["buildDefinition"]["externalParameters"]["gateVersion"], r"^v\d+")
        self.assertEqual(len(sl["subject"]), len(ie.intoto_statement(ROOT)["subject"]))
        # 基线句必须取自真源且非 0（早期写成 check1-0 PASS=0 的真事故）
        from core import quality_baseline as qb
        self.assertEqual(pred["buildDefinition"]["externalParameters"]["declaredBaseline"],
                         "check1-%d PASS=%d" % (qb.EXPECTED_CHECKS, qb.EXPECTED_PASS))

    def test_a2a_card_projects_endpoints_and_declares_not_implemented(self):
        card = ie.a2a_agent_card(ROOT)
        contract = json.loads(Path(ROOT, ie.CONTRACT_REL).read_text(encoding="utf-8"))
        self.assertEqual(len(card["skills"]), len(contract["endpoints"]))
        self.assertEqual([s["id"] for s in card["skills"]],
                         [e["id"] for e in contract["endpoints"]])
        self.assertTrue(card["capabilities"]["streaming"])
        self.assertIn("未实装", card["x-nf-note"])
        for s in card["skills"]:
            self.assertTrue(s["description"].startswith("maps_to "))

    def test_interop_kinds_cover_six_faces(self):
        self.assertEqual(sorted(ie.KINDS),
                         ["a2a", "asyncapi", "c2pa", "cid", "cyclonedx", "decisions",
                          "intoto", "openapi", "prov", "sbom", "slsa", "vc"])

    def test_cid_multiformats_vector(self):
        """multiformats 已知向量：raw codec + sha2-256 下 sha256("") 的 CIDv1。"""
        import base64
        import hashlib
        empty = "b" + base64.b32encode(
            b"\x01\x71" + b"\x12\x20" + hashlib.sha256(b"").digest()).decode().lower().rstrip("=")
        self.assertEqual(empty, "bafyreihdwdcefgh4dqkjv67uzcmw7ojee6xedzdetojuzjevtenxquvyku")
        idx = ie.cid_index(ROOT)
        rec = json.loads(Path(ROOT, ie.RECEIPTS_REL).read_text(encoding="utf-8"))
        self.assertEqual(len(idx["entries"]), len(rec["entries"]))
        for e in idx["entries"]:
            self.assertRegex(e["cid"], r"^b[a-z2-7]{50,}$")

    def test_cyclonedx_shape_and_same_source_as_spdx(self):
        cdx = ie.cyclonedx_doc(ROOT)
        self.assertEqual(cdx["bomFormat"], "CycloneDX")
        self.assertEqual(cdx["specVersion"], "1.5")
        self.assertRegex(cdx["serialNumber"], r"^urn:uuid:[0-9a-f-]{36}$")
        self.assertRegex(cdx["metadata"]["timestamp"],
                         r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        require = {c["name"] for c in cdx["components"] if c["scope"] == "required"}
        from core import purity_scan as ps
        self.assertEqual(require, set(ps.HARD_ALLOW), "两形同源：硬依赖集须一致")
        self.assertEqual(cdx["serialNumber"], ie.cyclonedx_doc(ROOT)["serialNumber"])

    def test_vc_and_c2pa_declare_honest_boundaries(self):
        vc = ie.vc_document(ROOT)
        self.assertIn("https://www.w3.org/ns/credentials/v2", vc["@context"])
        self.assertIn("VerifiableCredential", vc["type"])
        self.assertNotIn("proof", vc)
        self.assertIn("unsigned", vc["x-nf-proof-status"])
        c2 = ie.c2pa_manifest(ROOT)
        labels = {a["label"] for a in c2["assertions"]}
        self.assertEqual(labels, {"c2pa.actions", "c2pa.hash.data"})
        self.assertIn("未封装", c2["x-nf-package-status"])

    def test_committed_interop_faces_match_live(self):
        """入仓面（results/interop/*.json）必须与实时派生逐字节一致。"""
        d = Path(ROOT, "results", "interop")
        self.assertTrue(d.is_dir(), "入仓面目录须存在（nf interop --all --out results/interop）")
        for kind in ie.KINDS:
            p = d / ("%s.json" % kind)
            self.assertTrue(p.is_file(), "缺入仓面：%s" % kind)
            self.assertEqual(p.read_bytes(), ie.render(kind, ROOT),
                             "入仓面与实时派生不一致：%s" % kind)

    def test_cli_kind_choices_derive_from_declaration(self):
        """CLI `--kind` 对每个声明面都必须可跑（此前手写列表两次漏同步 slsa/a2a、c2pa）。"""
        import subprocess
        for kind in sorted(ie.KINDS):
            r = subprocess.run([sys.executable, "scripts/nf.py", "interop", "--kind", kind],
                               cwd=ROOT, capture_output=True, text=True,
                               encoding="utf-8", timeout=90)
            self.assertEqual(r.returncode, 0, "kind=%s 不可跑：%s" % (kind, r.stderr[:200]))
            self.assertTrue(r.stdout.strip().startswith("{"),
                            "kind=%s 输出不像机读面：%s" % (kind, r.stdout[:120]))

    def test_decision_surface_excludes_internal_work_orders(self):
        ds = ie.decision_surface(ROOT)
        self.assertIn("不随本面发布", ds["x-nf-internal"])
        self.assertGreaterEqual(len(ds["publicDecisionIndex"]), 5)
        self.assertEqual(len(ds["adapters"]), 3)
        for c in ds["candidates"]:
            self.assertIn("pulled", c)

    def test_prov_graph_shape_and_coverage(self):
        pv = ie.prov_document(ROOT)
        nodes = pv["@graph"]
        ids = [n["@id"] for n in nodes]
        self.assertEqual(len(set(ids)), len(ids), "节点 id 须唯一（同一投稿人会重复出现）")
        known = set(ids)
        for n in nodes:
            for rel in ("prov:used", "prov:generated", "prov:wasAssociatedWith"):
                if n.get(rel):
                    self.assertIn(n[rel], known, rel)
        prov_src = json.loads(Path(ROOT, "05_资产库/provenance.json").read_text(encoding="utf-8"))
        for a in prov_src["assets"]:
            self.assertIn("nf:asset/%s" % a["key"], known)
        types = {n["@type"] for n in nodes}
        self.assertTrue({"prov:Entity", "prov:Activity", "prov:SoftwareAgent"} <= types, types)
        self.assertIn("prov", pv["@context"])
        self.assertEqual(ie.render("prov", ROOT), ie.render("prov", ROOT))

    def test_prov_is_honest_about_empty_faces(self):
        """transform_log 当前 0 条 → 图里不得凭空出现消化活动（空面如实为空）。"""
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, "protocol/transform_log.json", json.dumps({"entries": []}))
            pv = ie.prov_document(tmp)
            self.assertEqual([n for n in pv["@graph"] if n["@id"].startswith("nf:transform/")], [])
            self.assertEqual(pv["x-nf-counts"]["activities"], 0)

    def test_schema_for_type_mapping(self):
        self.assertEqual(ie._schema_for("integer")["type"], "integer")
        self.assertEqual(ie._schema_for("array")["items"], {})
        self.assertEqual(ie._schema_for("string|null")["type"], ["string", "null"])
        unknown = ie._schema_for("widget-shaped thing")
        self.assertEqual(unknown["type"], "object")
        self.assertTrue(unknown["additionalProperties"])
        self.assertEqual(unknown["description"], "widget-shaped thing")

    def test_openapi_streaming_and_deprecated_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ie.CONTRACT_REL, json.dumps({
                "schema": "nf-endpoint/1", "status": "implemented",
                "conventions": {"streaming": "SSE 分片", "deprecation": "见契约",
                                "idempotency": "默认幂等"},
                "endpoints": [
                    {"id": "a", "method": "GET", "path": "/a", "streaming": True,
                     "maps_to": "nf doctor"},
                    {"id": "b", "method": "GET", "path": "/b", "streaming": False,
                     "maps_to": "nf doctor", "deprecated": True, "sunset": "2027-01-01",
                     "replacement": None}]}))
            doc = ie.openapi_doc(tmp)
            self.assertIn("text/event-stream", doc["paths"]["/a"]["get"]["responses"]["200"]["content"])
            self.assertEqual(doc["paths"]["/b"]["get"]["x-nf-sunset"], "2027-01-01")
            self.assertTrue(doc["paths"]["/b"]["get"]["deprecated"])
            self.assertIsNone(doc["paths"]["/b"]["get"]["x-nf-replacement"])

    def test_missing_declared_dates_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ie.CONTRACT_REL, json.dumps(
                {"schema": "nf-endpoint/1", "status": "proposed", "conventions": {},
                 "endpoints": [{"id": "a", "method": "GET", "path": "/a",
                                "maps_to": "nf doctor"}]}))
            _write(tmp, ie.EVENTS_REL, json.dumps({"events": {}}))
            _write(tmp, ie.RECEIPTS_REL, json.dumps({"algorithm": "x", "root": "y",
                                                     "entries": []}))
            self.assertEqual(ie._declared_max_date(tmp), "")
            issues, _ = ie.verify(tmp)
            self.assertTrue(any("created" in i for i in issues), issues)

    def test_openapi_missing_operation_id_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _write(tmp, ie.CONTRACT_REL, json.dumps(
                {"schema": "nf-endpoint/1", "status": "proposed", "conventions": {},
                 "endpoints": [{"id": "", "method": "GET", "path": "/a",
                                "maps_to": "nf doctor"}]}))
            _write(tmp, ie.EVENTS_REL, json.dumps({"events": {}}))
            _write(tmp, ie.RECEIPTS_REL, json.dumps({"algorithm": "x", "root": "y",
                                                     "entries": []}))
            issues, _ = ie.verify(tmp)
            self.assertTrue(any("operationId" in i for i in issues), issues)


if __name__ == "__main__":
    unittest.main()
