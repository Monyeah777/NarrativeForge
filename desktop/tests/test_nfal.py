# -*- coding: utf-8 -*-
"""NFA-L（声明式 + 命令式混合）前端/后端单测。

判据：guard 表达式从 Pipeline 声明的 condition 字段进入——词法/语法/类型检查/三值判决/
NFIR 规范化。未登记符号判 fail、非 bool guard 判 fail、未知值 fail-closed 记 abstain；
散文 condition 只记 advisory（V1 只增不删）。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "desktop" / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "desktop" / "src"))

from core import nfal                                        # noqa: E402
from core.nf_expr import LexError, ParseError, parse, strip_pos, tokenize  # noqa: E402

P01 = ROOT / "03_管线库" / "P01_标准管线.md"
FENCE = chr(96) * 3
STATE = {"WorldState": {"time": {"day": 45, "season": "winter"}}}
SYM = nfal.SymbolTable(
    state={"WorldState.time.day": "integer", "WorldState.time.season": "string"},
    events={"tick_day"}, tokens={"days": "integer"}, inputs={"strict": "boolean"})

_PIPELINE = (
    FENCE + "yaml\n"
    "Pipeline:\n"
    "  id: P99\n"
    "  name: 测试管线\n"
    "  structure:\n"
    "    type: linear\n"
    "    flow:\n"
    "      - from: P00\n"
    "        to: P10\n"
    "        condition: '=WorldState.time.day >= 30 && WorldState.time.season == \"winter\"'\n"
    "      - from: P10\n"
    "        to: P00\n"
    "        condition: 主循环回卷（散文）\n"
    "  layers:\n"
    "    - id: P00\n"
    "      name: 基座\n"
    "      description: 初始化\n"
    "      optional: false\n"
    "      default_modules: [M00]\n"
    "      allowed_modules: [M00]\n"
    + FENCE + "\n")


def _codes(diags):
    return [d["code"] for d in diags]


class TestLexParse(unittest.TestCase):
    def test_tokenize_kinds(self):
        kinds = [t["k"] for t in tokenize('a.b >= 30 && "x"')]
        self.assertEqual(kinds, ["ident", "punct", "ident", "punct", "int", "punct", "str", "eof"])

    def test_operator_precedence(self):
        self.assertEqual(nfal.eval_guard(parse("1 + 2 * 3"), {})["value"], 7)
        self.assertEqual(nfal.eval_guard(parse("(1 + 2) * 3"), {})["value"], 9)
        self.assertEqual(nfal.eval_guard(parse('1 < 2 ? "a" : "b"'), {})["value"], "a")

    def test_parse_error_carries_pos(self):
        with self.assertRaises(ParseError) as ctx:
            parse("1 +")
        self.assertGreaterEqual(ctx.exception.pos, 0)

    def test_lex_error_on_unclosed_string(self):
        with self.assertRaises(LexError):
            tokenize('"abc')

    def test_strip_pos_is_stable(self):
        self.assertEqual(strip_pos(parse("a.b == 1")), strip_pos(parse("a.b == 1")))
        self.assertNotIn("pos", json.dumps(strip_pos(parse("a.b == 1"))))


class TestCheck(unittest.TestCase):
    def test_unknown_symbol_fails(self):
        _t, diags = nfal.check_condition(parse("NoSuch.x == 1"), SYM)
        self.assertIn("E0301", _codes(diags))

    def test_non_bool_guard_fails(self):
        _t, diags = nfal.check_condition(parse("1 + 2"), SYM)
        self.assertIn("E0302", _codes(diags))

    def test_unknown_function_fails(self):
        _t, diags = nfal.check_condition(parse("frobnicate(1)"), SYM)
        self.assertIn("E0304", _codes(diags))

    def test_arity_checked(self):
        _t, diags = nfal.check_condition(parse("size(1, 2)"), SYM)
        self.assertIn("E0305", _codes(diags))

    def test_untyped_is_warn_not_fail(self):
        sym = nfal.SymbolTable(state={"X.y": "untyped"})
        t, diags = nfal.check_condition(parse("X.y == 1"), sym)
        self.assertIn("E0310", _codes(diags))
        self.assertTrue(all(d["severity"] == "warn" for d in diags))
        self.assertEqual(t, "untyped")   # 未收窄即 untyped，后端 fail-closed 记 abstain

    def test_registered_symbols_resolve(self):
        self.assertEqual(nfal.infer_type(parse("WorldState.time.day >= 1"), SYM)[0], "bool")
        self.assertEqual(nfal.infer_type(parse("event.tick_day"), SYM)[0], "bool")
        self.assertEqual(nfal.infer_type(parse("token.days + 1"), SYM)[0], "int")
        self.assertEqual(nfal.infer_type(parse("input.strict"), SYM)[0], "bool")

    def test_state_prefix_is_accepted(self):
        self.assertEqual(nfal.SymbolTable(state={"WorldState.time.day": "integer"}).resolve(
            ["state", "WorldState", "time", "day"]), "int")


class TestEval(unittest.TestCase):
    def test_kleene_and_false_collapses(self):
        res = nfal.eval_guard(parse("NoSuch.x > 1 && false"), {})
        self.assertEqual(res["verdict"], "fail")
        self.assertIs(res["value"], False)

    def test_kleene_or_true_collapses(self):
        self.assertEqual(nfal.eval_guard(parse("NoSuch.x > 1 || true"), {})["verdict"], "pass")

    def test_unknown_is_abstain(self):
        res = nfal.eval_guard(parse("NoSuch.x > 1 && true"), {})
        self.assertEqual(res["verdict"], "abstain")
        self.assertIsNone(res["value"])

    def test_type_error_is_abstain_not_pass(self):
        res = nfal.eval_guard(parse("1 && true"), {})
        self.assertEqual(res["verdict"], "abstain")
        self.assertTrue(res["diagnostics"])

    def test_functions_and_membership(self):
        self.assertEqual(nfal.eval_guard(parse('size([1, 2, 3]) == 3'), {})["verdict"], "pass")
        self.assertEqual(nfal.eval_guard(parse('contains("abc", "b")'), {})["verdict"], "pass")
        self.assertEqual(nfal.eval_guard(parse('has({a: 1}, "a")'), {})["verdict"], "pass")
        self.assertEqual(nfal.eval_guard(parse('startsWith("abc", "ab")'), {})["verdict"], "pass")
        self.assertEqual(nfal.eval_guard(parse('"snow" in ["snow", "rain"]'), {})["verdict"], "pass")

    def test_state_value_drives_verdict(self):
        expr = parse('WorldState.time.day >= 30 && WorldState.time.season == "winter"')
        self.assertEqual(nfal.eval_guard(expr, STATE)["verdict"], "pass")
        self.assertEqual(nfal.eval_guard(expr, {})["verdict"], "abstain")

    def test_verdict_of_is_three_valued(self):
        self.assertEqual(nfal.verdict_of(True), "pass")
        self.assertEqual(nfal.verdict_of(False), "fail")
        self.assertEqual(nfal.verdict_of(nfal.UNKNOWN), "abstain")

    def test_check_expression_envelope(self):
        res = nfal.check_expression("WorldState.time.day >= 1", SYM)
        self.assertEqual(res["verdict"], "pass")
        self.assertEqual(res["schema"], nfal.SCHEMA)
        bad = nfal.check_expression("WorldState.time.day >=", SYM)
        self.assertEqual(bad["verdict"], "fail")

    def test_diag_shape(self):
        d = nfal.diag("E9999", "warn", "x")
        self.assertEqual(set(d), {"code", "severity", "message", "pos"})


class TestNFIR(unittest.TestCase):
    def _build(self):
        tmp = tempfile.mkdtemp()
        p = Path(tmp, "P99.md")
        p.write_text(_PIPELINE, encoding="utf-8")
        return tmp, nfal.build_ir(tmp, str(p), sym=SYM, with_tokens=False)

    def test_typed_and_prose_edges(self):
        _tmp, ir = self._build()
        edges = {e["from"]: e for e in ir["edges"]}
        self.assertEqual(edges["P00"]["guard"]["source"], "expr")
        self.assertEqual(edges["P00"]["guard_types"]["guard"], "bool")
        self.assertEqual(edges["P10"]["guard"]["source"], "prose")
        self.assertIn("A0201", _codes(ir["diagnostics"]))
        self.assertEqual(ir["verdict"], "warn")

    def test_ir_is_deterministic(self):
        tmp, ir = self._build()
        again = nfal.build_ir(tmp, str(Path(tmp, "P99.md")), sym=SYM, with_tokens=False)
        self.assertEqual(nfal.canonical(ir), nfal.canonical(again))
        self.assertTrue(nfal.canonical(ir).endswith("\n"))

    def test_strict_promotes_prose_to_fail(self):
        tmp = tempfile.mkdtemp()
        p = Path(tmp, "P99.md")
        p.write_text(_PIPELINE, encoding="utf-8")
        ir = nfal.build_ir(tmp, str(p), sym=SYM, with_tokens=False, strict=True)
        self.assertEqual(ir["verdict"], "fail")

    def test_load_decl_reads_pipeline_block(self):
        tmp, _ir = self._build()
        decl = nfal.load_decl(tmp, str(Path(tmp, "P99.md")))
        self.assertEqual(decl["id"], "P99")

    def test_real_p01_conditions_compile(self):
        # 迁移后：真仓管线的 condition 已是 nf-expr（散文路径由合成夹具覆盖）
        ir = nfal.build_ir(str(ROOT), str(P01), with_tokens=False)
        sources = {e["guard"]["source"] for e in ir["edges"]}
        self.assertIn("expr", sources)
        self.assertNotEqual(ir["verdict"], "fail")


if __name__ == "__main__":
    unittest.main()
