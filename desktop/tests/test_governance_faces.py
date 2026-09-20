# -*- coding: utf-8 -*-
"""治理面六件（声明 / RFC / driver / 实践包 / 跑分台 / 端点契约）的正式与否定用例。"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core import bench, conformance_decl as cd, driver, endpoint  # noqa: E402
from core import patterns as pt, rfc  # noqa: E402
from core import conformance_report as cr  # noqa: E402


def _p(*parts):
    return Path(ROOT, *parts)


class TestDeclarationRealRepo(unittest.TestCase):
    def test_parse_and_scan_clean(self):
        decl = cd.parse(str(ROOT))
        self.assertGreaterEqual(len(decl["versions"]), 5)
        self.assertGreaterEqual(len(decl["scope"]), 15)
        self.assertGreaterEqual(len(decl["excluded"]), 8)
        self.assertEqual(cd.scan(str(ROOT))[0], [])

    def test_version_mismatch_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "protocol").mkdir(parents=True)
            # 造出真源，使断言针对"版本不一致"而不是"真源缺失"
            (Path(tmp) / "desktop" / "src" / "core").mkdir(parents=True)
            (Path(tmp) / "desktop" / "src" / "core" / "registry.json").write_text(
                json.dumps({"registry_schema_version": "2"}), encoding="utf-8")
            (Path(tmp) / "verify.sh").write_text(
                "# 版本 : v2.26\ncheck1(){}\n", encoding="utf-8")
            shutil.copy(_p("protocol", "CONFORMANCE.md"),
                        Path(tmp, "protocol", "CONFORMANCE.md"))
            p = Path(tmp, "protocol", "CONFORMANCE.md")
            p.write_text(p.read_text(encoding="utf-8").replace(
                "| registry schema | `2` |", "| registry schema | `9` |"), encoding="utf-8")
            issues = cd.scan(tmp)[0]
            self.assertTrue(any("registry schema" in i for i in issues), issues)

    def test_unverifiable_declaration_row_is_fail(self):
        """声明了真源里没有的规范项 → 必须报（不许用声明充数）。"""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "protocol").mkdir(parents=True)
            (Path(tmp) / "protocol" / "CONFORMANCE.md").write_text(
                "# C\n\n## 声明\n\n| 规范 | 版本 | 真源 |\n|---|---|---|\n"
                "| 不存在的规范 | `9` | 空气 |\n\n"
                "## 范围\n\n- `protocol`\n\n## 排除\n\n| 路径 | 理由 |\n|---|---|\n",
                encoding="utf-8")
            self.assertTrue(any("无法核验" in i for i in cd.scan(tmp)[0]))

    def test_scope_overlap_with_excluded_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "protocol").mkdir(parents=True)
            (Path(tmp) / "a.md").write_text("x", encoding="utf-8")
            (Path(tmp) / "protocol" / "CONFORMANCE.md").write_text(
                "# C\n\n## 声明\n\n| 规范 | 版本 | 真源 |\n|---|---|---|\n\n"
                "## 范围\n\n- `a.md`\n\n"
                "## 排除\n\n| 路径 | 理由 |\n|---|---|\n| `a.md` | 与范围重叠 |\n",
                encoding="utf-8")
            issues = cd.scan(tmp)[0]
            self.assertTrue(any("scope 与排除重叠" in i for i in issues), issues)

    def test_optional_excluded_may_be_absent(self):
        """「允许不存在」标注的运行期件缺省不报缺口；未标注的缺省仍报（宽容不放松）。"""
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "protocol").mkdir(parents=True)
            (Path(tmp) / "a.md").write_text("x", encoding="utf-8")
            (Path(tmp) / "protocol" / "CONFORMANCE.md").write_text(
                """# C

## 声明

| 规范 | 版本 | 真源 |
|---|---|---|

## 范围

- `a.md`

## 排除

| 路径 | 理由 |
|---|---|
| `gone-runtime` | 运行期件（允许不存在） |
| `gone-plain` | 陈旧条目 |
""", encoding="utf-8")
            issues = cd.scan(tmp)[0]
            self.assertTrue(any("gone-plain" in i for i in issues), issues)
            self.assertFalse(any("gone-runtime" in i for i in issues), issues)

class TestRfc(unittest.TestCase):
    HEAD = ("> 最后更新：2026-09-08\n> **RFC**: NF-0001 · **Category**: Standards Track · "
            "**Date**: 2026-09-08 · **Status**: Active · **Supersedes**: — · "
            "**Superseded by**: —\n")

    def _tree(self, tmp, docs, index):
        (Path(tmp) / "protocol").mkdir(parents=True)
        for name, text in docs.items():
            (Path(tmp) / name).write_text(text, encoding="utf-8")
        (Path(tmp) / "protocol" / "rfc_index.json").write_text(
            json.dumps(index, ensure_ascii=False), encoding="utf-8")
        return tmp

    def test_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, {"a.md": "# A\n" + self.HEAD},
                       {"schema": "nf-rfc/1",
                        "docs": [{"rfc": "NF-0001", "path": "a.md"}]})
            self.assertEqual(rfc.scan(tmp)[0], [])

    def test_date_must_match_last_updated(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = self.HEAD.replace("**Date**: 2026-09-08", "**Date**: 2020-01-01")
            self._tree(tmp, {"a.md": "# A\n" + bad},
                       {"schema": "nf-rfc/1",
                        "docs": [{"rfc": "NF-0001", "path": "a.md"}]})
            self.assertTrue(any("Date 与「最后更新」不一致" in i
                                for i in rfc.scan(tmp)[0]))

    def test_missing_head_and_duplicate_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._tree(tmp, {"a.md": "# A\n> 最后更新：2026-09-08\n",
                             "b.md": "# B\n" + self.HEAD},
                       {"schema": "nf-rfc/1", "docs": [
                           {"rfc": "NF-0001", "path": "a.md"},
                           {"rfc": "NF-0001", "path": "b.md"}]})
            issues = rfc.scan(tmp)[0]
            self.assertTrue(any("缺 RFC 头" in i for i in issues), issues)
            self.assertTrue(any("编号重复" in i for i in issues), issues)

    def test_supersede_chain_must_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = self.HEAD.replace("**Superseded by**: —", "**Superseded by**: NF-0002")
            self._tree(tmp, {"a.md": "# A\n" + h},
                       {"schema": "nf-rfc/1",
                        "docs": [{"rfc": "NF-0001", "path": "a.md"}]})
            self.assertTrue(any("指向不在册的编号" in i for i in rfc.scan(tmp)[0]))


class TestDriver(unittest.TestCase):
    def test_repo_scan_and_resolve(self):
        issues, _warns, stats = driver.scan(str(ROOT))
        self.assertEqual(issues, [])
        self.assertEqual(stats["workflows"], 3)
        self.assertEqual(stats["documents"], 3)
        r = driver.resolve(str(ROOT), "assemble")
        self.assertEqual(r["mode"], "mcp")
        self.assertEqual(driver.resolve(str(ROOT), "nope")["mode"], "unknown")

    def test_bad_tool_and_missing_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "protocol").mkdir(parents=True)
            (Path(tmp) / "x.md").write_text("# x\n", encoding="utf-8")
            (Path(tmp) / "protocol" / "driver.json").write_text(json.dumps({
                "schema": "nf-driver/1",
                "bindings": {"mcp.tools": ["no_such_tool"]},
                "workflows": {"w": {"mcp_tools": ["no_such_tool"], "fallback": ""}},
                "documents": [{"path": "x.md", "workflow": "w"}],
                "fail_closed": {"marker_keywords": ["不得回退"]}}), encoding="utf-8")
            issues = driver.scan(tmp)[0]
            self.assertTrue(any("运行时不存" in i for i in issues), issues)
            self.assertTrue(any("不存在的 MCP 工具" in i for i in issues), issues)
            self.assertTrue(any("缺 fallback" in i for i in issues), issues)
            self.assertTrue(any("DRIVER OVERRIDE" in i for i in issues), issues)


class TestPatterns(unittest.TestCase):
    def test_repo_clean_and_reverse_lookup(self):
        self.assertEqual(pt.scan(str(ROOT))[0], [])
        self.assertEqual(pt.check_projection(str(ROOT)), [])
        hits = pt.for_path(str(ROOT), "library/INDEX.md")
        self.assertTrue(any(h["id"] == "single-source-truth" for h in hits), hits)
        self.assertEqual(pt.for_path(str(ROOT), "no/such/file.md"), [])

    def test_bad_pattern_is_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp, "patterns", "bad-one")
            d.mkdir(parents=True)
            (d / "PATTERN.md").write_text(
                "---\nid: other-name\nname: x\nstatus: archived\napplies_to:\n"
                "  - no/such/path.md\nrules: []\nevidence: []\n---\n正文\n",
                encoding="utf-8")
            issues = pt.scan(tmp)[0]
            self.assertTrue(any("id 与目录名不一致" in i for i in issues), issues)
            self.assertTrue(any("status 越词表" in i for i in issues), issues)
            self.assertTrue(any("applies_to 路径不存在" in i for i in issues), issues)
            self.assertTrue(any("rules 为空" in i for i in issues), issues)


class TestBench(unittest.TestCase):
    CASE = "desktop/tests/fixtures/benchmark/suite/p03-western-cross/case.json"
    GOOD = "docs/完整版样本_西幻生存流P03.md"

    def test_cases_present(self):
        self.assertGreaterEqual(len(bench.cases(str(ROOT))), 2)

    def test_deterministic_and_degraded_scores_lower(self):
        """跑分台自身有效性：同产物同分；**被破坏的产物必须更低分**。"""
        good = bench.evaluate(str(ROOT), self.CASE, self.GOOD)
        again = bench.evaluate(str(ROOT), self.CASE, self.GOOD)
        self.assertEqual(good["scores"], again["scores"])
        self.assertGreaterEqual(good["total"], good["floor"])
        with tempfile.TemporaryDirectory() as tmp:
            src = _p("docs", "完整版样本_西幻生存流P03.md").read_text(encoding="utf-8")
            broken = (src.replace("## 7", "## 99").replace("事件闭合", "事件")[: len(src) // 3]
                      + "\n## 7. 注册表投影\n- M999 编造模块\n")
            bpath = Path(tmp, "bad.md")
            bpath.write_text(broken, encoding="utf-8")
            bad = bench.evaluate(str(ROOT), self.CASE, str(bpath))
        self.assertLess(bad["total"], good["total"], "退化产物必须低分")
        self.assertTrue(any("编造" in i or "缺段" in i for i in bad["detail"]["issues"]),
                        bad["detail"]["issues"])

    def test_compare_and_report(self):
        case2 = "desktop/tests/fixtures/benchmark/suite/p02-campus-emotion/case.json"
        runs = [bench.evaluate(str(ROOT), self.CASE, self.GOOD, model="a"),
                bench.evaluate(str(ROOT), case2,
                               "library/NF-1.md", model="b")]
        doc = bench.compare(runs)
        self.assertEqual(doc["runs"], 2)
        self.assertIn("structure", doc["dims"])
        self.assertEqual(len(doc["ranking"]), 2)
        self.assertIn("# NF 执行结果跑分报告", bench.report_markdown(doc))
        self.assertEqual(bench.compare([])["runs"], 0)


class TestEndpoint(unittest.TestCase):
    def test_repo_clean_and_proposed(self):
        issues, warns, stats = endpoint.scan(str(ROOT))
        self.assertEqual(issues, [])
        self.assertEqual(stats["status"], "proposed")
        self.assertGreaterEqual(stats["endpoints"], 6)
        self.assertTrue(any("proposed" in w for w in warns))

    def test_bad_contract_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "protocol").mkdir(parents=True)
            (Path(tmp) / "scripts").mkdir(parents=True)
            (Path(tmp) / "scripts" / "nf.py").write_text('sub.add_parser("run")\n',
                                                         encoding="utf-8")
            (Path(tmp) / "protocol" / "endpoint_contract.json").write_text(json.dumps({
                "schema": "nf-endpoint/1", "status": "unknown",
                "conventions": {}, "endpoints": [
                    {"id": "x", "method": "FETCH", "path": "/x", "streaming": True,
                     "maps_to": "nf nowhere"},
                    {"id": "x", "method": "GET", "path": "/x", "streaming": False,
                     "maps_to": "ghost_tool（MCP 工具）"}]}), encoding="utf-8")
            issues = endpoint.scan(tmp)[0]
            self.assertTrue(any("status 越词表" in i for i in issues), issues)
            self.assertTrue(any("method 越词表" in i for i in issues), issues)
            self.assertTrue(any("未定义 SSE 约定" in i for i in issues), issues)
            self.assertTrue(any("无法解析" in i for i in issues), issues)
            self.assertTrue(any("不存在的 MCP 工具" in i for i in issues), issues)
            self.assertTrue(any("id 重复" in i for i in issues), issues)

    def test_deprecation_needs_exit_and_only_when_implemented(self):
        """弃用/日落语义：未实装不许弃用；弃用必须带 sunset + replacement（无替代写 null）。"""
        base = {"schema": "nf-endpoint/1", "conventions": {"deprecation": "见契约"},
                "endpoints": [{"id": "a", "method": "GET", "path": "/a", "streaming": False,
                               "maps_to": "nf run"}]}
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "protocol").mkdir(parents=True)
            (Path(tmp) / "scripts").mkdir(parents=True)
            (Path(tmp) / "scripts" / "nf.py").write_text('sub.add_parser("run")\n',
                                                         encoding="utf-8")
            contract = Path(tmp) / "protocol" / "endpoint_contract.json"

            # ① proposed 期间声明弃用 = FAIL
            doc = dict(base, status="proposed")
            doc["endpoints"] = [dict(base["endpoints"][0], deprecated=True,
                                     sunset="2027-01-01", replacement=None)]
            contract.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            issues = endpoint.scan(tmp)[0]
            self.assertTrue(any("没有可弃用的东西" in i for i in issues), issues)

            # ② implemented + 有标志无出口 = FAIL
            doc["status"] = "implemented"
            doc["endpoints"] = [dict(base["endpoints"][0], deprecated=True, replacement="ghost")]
            contract.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            issues = endpoint.scan(tmp)[0]
            self.assertTrue(any("缺合规 sunset" in i for i in issues), issues)
            self.assertTrue(any("replacement 指向契约内不存在" in i for i in issues), issues)

            # ③ implemented + 合规弃用 = 零 FAIL
            doc["endpoints"] = [dict(base["endpoints"][0], deprecated=True,
                                     sunset="2027-01-01", replacement=None)]
            contract.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(endpoint.scan(tmp)[0], [])

            # ④ 未弃用却带 sunset = 悬空字段 FAIL
            doc["endpoints"] = [dict(base["endpoints"][0], sunset="2027-01-01")]
            contract.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            issues = endpoint.scan(tmp)[0]
            self.assertTrue(any("悬空弃用字段" in i for i in issues), issues)


class TestConformanceReport(unittest.TestCase):
    """一致性报告工件：确定可复现 + 在盘报告与实时重算一致 + 篡改/缺失可检。"""

    def test_run_deterministic_and_conformant(self):
        a = cr.run(str(ROOT))
        b = cr.run(str(ROOT))
        self.assertEqual(a["root"], b["root"])
        self.assertEqual(a["verdict"], "conformant")
        self.assertEqual(a["passed"], a["total"])
        self.assertGreaterEqual(a["total"], 16)

    def test_committed_report_matches_live(self):
        issues, stats = cr.verify_committed(str(ROOT))
        self.assertEqual(issues, [])
        self.assertEqual(stats["verdict"], "conformant")

    def test_missing_and_tampered_report_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(any("缺一致性报告" in i
                                for i in cr.verify_committed(tmp)[0]))
            cr.write(tmp)
            self.assertEqual(cr.verify_committed(tmp)[0], [])
            rel = cr.REPORT_REL.split("/")[-1]
            p = Path(tmp, "protocol", rel)
            doc = json.loads(p.read_text(encoding="utf-8"))
            doc["root"] = "0" * 64
            p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            self.assertTrue(any("过期或被改" in i
                                for i in cr.verify_committed(tmp)[0]))


if __name__ == "__main__":
    unittest.main()
