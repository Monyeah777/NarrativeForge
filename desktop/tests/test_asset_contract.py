# -*- coding: utf-8 -*-
"""数字资产契约层（core/asset_contract）回归 —— 数据 / 代码 / 脚本三面。

覆盖：严格 JSON、CSV 列数、Markdown 表格列数、输入输出一致性（link）、sha256 防篡改、
可证空指针（正例 + 两类防误杀）、禁用调用面、测试用例在场、脚本 nf-io 双源一致、
三语言（Python/Bash/VBA）链对齐、冻结重签、以及**真仓库**的活契约扫描。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import asset_contract as ac  # noqa: E402


def _make(root: Path, rel, text) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _decl(root: Path, doc) -> None:
    _make(root, ac.DECL_REL, json.dumps(doc, ensure_ascii=False))


class DataFaceTest(unittest.TestCase):
    def test_strict_json_rejects_nan(self):
        with self.assertRaises(ValueError) as ctx:
            ac._strict_json('{"a": NaN}')
        self.assertIn("RFC 8259", str(ctx.exception))

    def test_csv_ragged_row_is_issue(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "a.csv", "x,y\n1,2\n3\n")
            issues, stats = ac._check_data(str(r), {"id": "c", "path": "a.csv", "format": "csv",
                                                    "required_columns": ["x", "y"], "min_rows": 1})
            self.assertTrue(any("列数" in i for i in issues), issues)
            self.assertEqual(2, stats["rows"])

    def test_csv_missing_column(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "a.csv", "x,y\n1,2\n")
            issues, _ = ac._check_data(str(r), {"id": "c", "path": "a.csv", "format": "csv",
                                                "required_columns": ["z"]})
            self.assertTrue(any("缺必需列" in i for i in issues), issues)

    def test_markdown_ragged_table_is_issue(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "m.md", "| a | b |\n|---|---|\n| 1 | 2 |\n| 3 |\n")
            issues, _ = ac._check_data(str(r), {"id": "m", "path": "m.md", "format": "markdown"})
            self.assertTrue(any("列数不齐" in i for i in issues), issues)

    def test_link_rows_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "s.csv", "c\na\nb\n")
            _make(r, "rep.json", '{"sample": "s.csv", "rows": 9}')
            issues, _ = ac._check_data(str(r), {"id": "r", "path": "rep.json", "format": "json",
                                                "link": {"path_field": "sample", "rows_field": "rows"}})
            self.assertTrue(any("不一致" in i for i in issues), issues)

    def test_link_rows_match_is_clean(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "s.csv", "c\na\nb\n")
            _make(r, "rep.json", '{"sample": "s.csv", "rows": 2}')
            issues, _ = ac._check_data(str(r), {"id": "r", "path": "rep.json", "format": "json",
                                                "link": {"path_field": "sample", "rows_field": "rows"}})
            self.assertEqual([], issues, issues)

    def test_sha256_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "f.json", "{}")
            issues, _ = ac._check_data(str(r), {"id": "f", "path": "f.json", "format": "json",
                                                "sha256": "0" * 64})
            self.assertTrue(any("摘要不符" in i for i in issues), issues)

    def test_missing_glob_is_issue(self):
        with tempfile.TemporaryDirectory() as d:
            issues, _ = ac._check_data(d, {"id": "g", "glob": "nope/*.json", "format": "json"})
            self.assertTrue(any("未命中任何文件" in i for i in issues), issues)

    def test_text_format_glob_multi_file(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "a.txt", "hello\nworld\n")
            _make(r, "b.txt", "again\n")
            issues, stats = ac._check_data(str(r), {"id": "t", "glob": "*.txt", "format": "text"})
            self.assertEqual([], issues, issues)
            self.assertEqual(2, stats["files"])

    def test_strict_json_rejects_infinity(self):
        with self.assertRaises(ValueError) as ctx:
            ac._strict_json('{"a": Infinity}')
        self.assertIn("RFC 8259", str(ctx.exception))

    def test_sha256_on_glob_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "a.json", "{}")
            _make(r, "b.json", "{}")
            issues, _ = ac._check_data(str(r), {"id": "g", "glob": "*.json", "format": "json",
                                                "sha256": "0" * 64})
            self.assertTrue(any("只用于 path 单件" in i for i in issues), issues)


class CodeFaceTest(unittest.TestCase):
    def _code(self, text, **kw):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "m.py", text)
            _make(r, "t.py", "import m\n")
            spec = {"id": "m", "path": "m.py", "lang": "python", "tests": ["t.py"]}
            spec.update(kw)
            return ac._check_code(str(r), spec)

    def test_none_deref_detected(self):
        issues, _ = self._code("def f():\n    x = None\n    return x.y\n")
        self.assertTrue(any("可证为 None" in i for i in issues), issues)

    def test_default_arg_none_detected(self):
        issues, _ = self._code("def f(x=None):\n    return x[0]\n")
        self.assertTrue(any("可证为 None" in i for i in issues), issues)

    def test_guard_returns_no_false_positive(self):
        issues, _ = self._code("def f(x=None):\n    if x is None:\n        return 0\n    return x.y\n")
        self.assertEqual([], issues, issues)

    def test_branch_reassign_no_false_positive(self):
        issues, _ = self._code("def f(cond):\n    x = None\n    if cond:\n        x = object()\n"
                               "        return x.y\n    return 0\n")
        self.assertEqual([], [i for i in issues if "可证为 None" in i], issues)

    def test_loop_reassign_no_false_positive(self):
        issues, _ = self._code("def f(items):\n    x = None\n    for i in items:\n        x = i\n"
                               "    return x.y\n")
        self.assertEqual([], [i for i in issues if "可证为 None" in i], issues)

    def test_deny_call(self):
        issues, _ = self._code("def f(cmd):\n    return eval(cmd)\n", deny_calls=["eval"])
        self.assertTrue(any("eval" in i for i in issues), issues)

    def test_missing_test_file(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "m.py", "x = 1\n")
            issues, _ = ac._check_code(str(r), {"id": "m", "path": "m.py", "tests": ["nope.py"]})
            self.assertTrue(any("不在场" in i for i in issues), issues)

    def test_no_tests_declared(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "m.py", "x = 1\n")
            issues, _ = ac._check_code(str(r), {"id": "m", "path": "m.py"})
            self.assertTrue(any("未声明测试件" in i for i in issues), issues)

    def test_syntax_error_is_issue(self):
        issues, _ = self._code("def f(:\n")
        self.assertTrue(any("语法坏" in i for i in issues), issues)


PY_HEAD = "# nf-io: inputs=in.txt outputs=out.txt\nx = 1\n"
SH_HEAD = "#!/usr/bin/env bash\n# nf-io: inputs=out.txt outputs=report.json\ncat out.txt > report.json\n"
VBA_HEAD = "' nf-io: inputs=report.json outputs=-\nOption Explicit\n"


class ScriptFaceTest(unittest.TestCase):
    def _root(self, d, texts):
        r = Path(d)
        for rel, txt in texts.items():
            _make(r, rel, txt)
        return r

    def test_three_language_chain_aligned(self):
        with tempfile.TemporaryDirectory() as d:
            r = self._root(d, {"a.py": PY_HEAD, "b.sh": SH_HEAD, "c.vba": VBA_HEAD})
            specs = [
                {"id": "a", "lang": "python", "path": "a.py", "inputs": ["in.txt"],
                 "outputs": ["out.txt"]},
                {"id": "b", "lang": "bash", "path": "b.sh", "inputs": ["out.txt"],
                 "outputs": ["report.json"]},
                {"id": "c", "lang": "vba", "path": "c.vba", "inputs": ["report.json"],
                 "outputs": []},
            ]
            issues = []
            for s in specs:
                sub, _ = ac._check_script(str(r), s)
                issues += sub
            by_id = {x["id"]: x for x in specs}
            for a, b in (("a", "b"), ("b", "c")):
                sub, _ = ac._check_chain(by_id, {"from": a, "to": b})
                issues += sub
            self.assertEqual([], issues, issues)

    def test_chain_misaligned(self):
        specs = {"a": {"id": "a", "outputs": ["x.json"]}, "b": {"id": "b", "inputs": ["y.json"]}}
        issues, _ = ac._check_chain(specs, {"from": "a", "to": "b"})
        self.assertTrue(any("无交集" in i for i in issues), issues)

    def test_chain_feeds_must_match(self):
        specs = {"a": {"id": "a", "outputs": ["x.json"]}, "b": {"id": "b", "inputs": ["y.json"]}}
        issues, _ = ac._check_chain(specs, {"from": "a", "to": "b",
                                           "feeds": [{"output": "x.json", "input": "x.json"}]})
        self.assertTrue(any("下游未声明" in i for i in issues), issues)

    def test_dual_source_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            r = self._root(d, {"a.py": PY_HEAD})
            issues, _ = ac._check_script(str(r), {"id": "a", "lang": "python", "path": "a.py",
                                                  "inputs": ["other.txt"], "outputs": ["out.txt"]})
            self.assertTrue(any("双源不一致" in i for i in issues), issues)

    def test_missing_header(self):
        with tempfile.TemporaryDirectory() as d:
            r = self._root(d, {"a.py": "x = 1\n"})
            issues, _ = ac._check_script(str(r), {"id": "a", "lang": "python", "path": "a.py"})
            self.assertTrue(any("nf-io" in i for i in issues), issues)

    def test_bad_lang(self):
        with tempfile.TemporaryDirectory() as d:
            r = self._root(d, {"a.rs": "fn main() {}\n"})
            issues, _ = ac._check_script(str(r), {"id": "a", "lang": "rust", "path": "a.rs"})
            self.assertTrue(any("不在词表" in i for i in issues), issues)

    def test_observed_literal_path_must_be_declared(self):
        with tempfile.TemporaryDirectory() as d:
            r = self._root(d, {"a.py": "# nf-io: inputs=in.txt outputs=-\n"
                                        "open('secret.txt').read()\n"})
            issues, _ = ac._check_script(str(r), {"id": "a", "lang": "python", "path": "a.py",
                                                  "inputs": ["in.txt"], "outputs": []})
            self.assertTrue(any("未声明的字面路径" in i for i in issues), issues)

    def test_bash_and_vba_header_parse(self):
        self.assertEqual({"inputs": ["a"], "outputs": ["b"]},
                         ac.parse_io_header("#!/bin/sh\n# nf-io: inputs=a outputs=b\n"))
        self.assertEqual({"inputs": ["a"], "outputs": []},
                         ac.parse_io_header("' nf-io: inputs=a outputs=-\nOption Explicit\n"))

    def test_missing_script_file(self):
        with tempfile.TemporaryDirectory() as d:
            issues, _ = ac._check_script(d, {"id": "a", "lang": "python", "path": "nope.py"})
            self.assertTrue(any("不在场" in i for i in issues), issues)


class DeclarationTest(unittest.TestCase):
    def test_missing_declaration(self):
        with tempfile.TemporaryDirectory() as d:
            issues, _warns, stats = ac.scan(d)
            self.assertTrue(any("缺数字资产契约声明" in i for i in issues), issues)
            self.assertEqual(0, stats["files"])

    def test_bad_schema(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _decl(r, {"schema": "wrong/0"})
            issues, _warns, _stats = ac.scan(str(r))
            self.assertTrue(any("schema 不匹配" in i for i in issues), issues)

    def test_freeze_updates_digest(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "f.json", "{}")
            _decl(r, {"schema": ac.SCHEMA,
                      "data": [{"id": "f", "path": "f.json", "format": "json",
                                "sha256": "0" * 64}]})
            issues, stats = ac.freeze(str(r))
            self.assertEqual([], issues, issues)
            self.assertEqual(1, stats["frozen"])
            doc = json.loads((r / ac.DECL_REL).read_text(encoding="utf-8"))
            self.assertEqual(ac.digest_of(r / "f.json"), doc["data"][0]["sha256"])
            again, _warns, _s = ac.scan(str(r))
            self.assertEqual([], again, again)

    def test_run_tests_runs_declared_file(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "t_ok.py", "import unittest\n\n\nclass T(unittest.TestCase):\n"
                                "    def test_ok(self):\n        self.assertTrue(True)\n")
            _decl(r, {"schema": ac.SCHEMA,
                      "code": [{"id": "x", "path": "t_ok.py", "tests": ["t_ok.py"]}]})
            issues, stats = ac.run_tests(str(r))
            self.assertEqual([], issues, issues)
            self.assertEqual(1, stats["tests"])

    def test_run_tests_reports_failure(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "t_bad.py", "import unittest\n\n\nclass T(unittest.TestCase):\n"
                                 "    def test_bad(self):\n        self.assertTrue(False)\n")
            _decl(r, {"schema": ac.SCHEMA,
                      "code": [{"id": "x", "path": "t_bad.py", "tests": ["t_bad.py"]}]})
            issues, _stats = ac.run_tests(str(r))
            self.assertTrue(any("测试未过" in i for i in issues), issues)

    def test_face_filter_limits_scope(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            _make(r, "f.json", "{}")
            _decl(r, {"schema": ac.SCHEMA,
                      "data": [{"id": "f", "path": "f.json", "format": "json"}],
                      "code": [{"id": "c", "path": "missing.py", "tests": ["missing.py"]}]})
            issues, _warns, stats = ac.scan(str(r), faces=("data",))
            self.assertEqual([], issues, issues)
            self.assertEqual(1, stats["data"])
            self.assertEqual(0, stats["code"])


FIXTURES = ROOT / "desktop" / "tests" / "fixtures" / "asset_contract"


class FixtureChainTest(unittest.TestCase):
    """仓库内驻留的三语言夹具链（Python → Bash → VBA）：契约必须对齐。"""

    def test_three_language_fixture_chain_aligns(self):
        specs = [
            {"id": "a", "lang": "python", "path": "stage_a.py",
             "inputs": ["raw.txt"], "outputs": ["parsed.json"]},
            {"id": "b", "lang": "bash", "path": "stage_b.sh",
             "inputs": ["parsed.json"], "outputs": ["report.md"]},
            {"id": "c", "lang": "vba", "path": "stage_c.vba",
             "inputs": ["report.md"], "outputs": []},
        ]
        issues = []
        for s in specs:
            sub, _ = ac._check_script(str(FIXTURES), s)
            issues += sub
        by_id = {s["id"]: s for s in specs}
        for a, b in (("a", "b"), ("b", "c")):
            sub, _ = ac._check_chain(by_id, {"from": a, "to": b})
            issues += sub
        self.assertEqual([], issues, issues)

    def test_fixture_headers_are_parseable(self):
        for rel, want in (("stage_a.py", ["raw.txt"]), ("stage_b.sh", ["parsed.json"]),
                          ("stage_c.vba", ["report.md"])):
            text = (FIXTURES / rel).read_text(encoding="utf-8")
            header = ac.parse_io_header(text)
            self.assertIsNotNone(header, rel)
            self.assertEqual(want, header["inputs"], rel)


class LiveRepoTest(unittest.TestCase):
    """活契约：真仓库声明件必须全绿（战例即本仓自身）。"""

    def test_repo_declaration_passes(self):
        issues, _warns, stats = ac.scan(str(ROOT))
        self.assertEqual([], issues, issues)
        for face in ac.FACES:
            self.assertGreater(stats[face], 0, face)
        self.assertGreater(stats["chains"], 0)

    def test_repo_declaration_covers_three_faces(self):
        doc, issues = ac.load(str(ROOT))
        self.assertEqual([], issues, issues)
        for face in ac.FACES:
            self.assertTrue(doc.get(face), face)


if __name__ == "__main__":
    unittest.main()
