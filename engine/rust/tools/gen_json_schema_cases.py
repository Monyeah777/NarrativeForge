"""为 `json_schema.json_schema_check` 生成**用例级**判据。

真语料上上游调用面全是 0 违例 ⇒ 校验器的错误分支一个都踩不到。本生成器造一批用例
（覆盖各官方关键字 + 边界 + 形态闸门 + 深度闸门），期望值从真源取，落成 Rust 单元判据。

用法：python engine/rust/tools/gen_json_schema_cases.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path('.').resolve()
sys.path.insert(0, str(ROOT / 'desktop' / 'src'))
sys.path.insert(0, str(ROOT / 'engine' / 'rust' / 'tools'))
from _rustlit import raw as rr  # noqa: E402
from core import json_schema as js  # noqa: E402

CASES = []


def case(name, instance, schema):
    CASES.append((name, instance, schema))


# ---- type
case("type-object-ok", {}, {"type": "object"})
case("type-object-bad", [], {"type": "object"})
case("type-array-bad", {}, {"type": "array"})
case("type-string-bad", 1, {"type": "string"})
case("type-bool-bad", None, {"type": "boolean"})
case("type-null-bad", 0, {"type": "null"})
case("type-integer-ok", 3, {"type": "integer"})
case("type-integer-float-bad", 3.5, {"type": "integer"})
case("type-number-int-ok", 3, {"type": "number"})
case("type-number-float-ok", 3.5, {"type": "number"})
case("type-bool-is-not-number", True, {"type": "number"})
case("type-bool-is-not-integer", True, {"type": "integer"})
case("type-list-ok", "x", {"type": ["string", "null"]})
case("type-list-bad", 1, {"type": ["string", "null"]})
case("type-unknown-name-passes", 1, {"type": "widget"})

# ---- const / enum（Python `==`：True == 1）
case("const-ok", 1, {"const": 1})
case("const-bad", 2, {"const": 1})
case("const-bool-vs-int-ok", 1, {"const": True})
case("enum-ok", "a", {"enum": ["a", "b"]})
case("enum-bad", "c", {"enum": ["a", "b"]})
case("enum-bool-vs-int-ok", 1, {"enum": [True]})

# ---- string
case("str-minLength-bad", "ab", {"minLength": 3})
case("str-minLength-ok", "abc", {"minLength": 3})
case("str-maxLength-bad", "abcd", {"maxLength": 3})
case("str-maxLength-cjk-counts-chars", "中文字", {"maxLength": 3})
case("str-maxLength-cjk-bad", "中文字符", {"maxLength": 3})
case("pattern-ok", "abc123", {"pattern": r"^[a-z]+\d+$"})
case("pattern-bad", "ABC", {"pattern": r"^[a-z]+$"})
case("pattern-nested-quant", "aaa", {"pattern": r"(a+)+$"})
case("pattern-star-star", "aaa", {"pattern": r"(a*)*b"})
case("pattern-too-long", "a", {"pattern": "a" * 600})
case("format-date-ok", "2026-10-04", {"format": "date"})
case("format-date-bad", "2026/10/04", {"format": "date"})
case("format-datetime-ok", "2026-10-04T11:00:00", {"format": "date-time"})
case("format-datetime-space-ok", "2026-10-04 11:00:00", {"format": "date-time"})
case("format-datetime-bad", "2026-10-04", {"format": "date-time"})
case("format-uri-ok", "https://x.y/z", {"format": "uri"})
case("format-uri-bad", "/relative/path", {"format": "uri"})
case("format-unknown-passes", "x", {"format": "email"})

# ---- number
case("minimum-bad", 1, {"minimum": 2})
case("minimum-ok", 2, {"minimum": 2})
case("maximum-bad", 3, {"maximum": 2})
case("exclusiveMinimum-bad", 2, {"exclusiveMinimum": 2})
case("exclusiveMaximum-bad", 2, {"exclusiveMaximum": 2})
case("multipleOf-ok", 6, {"multipleOf": 3})
case("multipleOf-bad", 7, {"multipleOf": 3})
case("multipleOf-float-ok", 0.3, {"multipleOf": 0.1})
case("multipleOf-float-bad", 0.35, {"multipleOf": 0.1})

# ---- array
case("minItems-bad", [1], {"minItems": 2})
case("maxItems-bad", [1, 2, 3], {"maxItems": 2})
case("uniqueItems-bad", [1, 1], {"uniqueItems": True})
case("uniqueItems-ok", [1, 2], {"uniqueItems": True})
case("uniqueItems-objects-bad", [{"a": 1}, {"a": 1}], {"uniqueItems": True})
case("prefixItems-bad", [1, "x"], {"prefixItems": [{"type": "integer"}, {"type": "integer"}]})
case("items-bad", [1, "x"], {"items": {"type": "integer"}})
case("items-with-prefix-skips-prefix", [1, "x"], {"prefixItems": [{"type": "integer"}], "items": {"type": "string"}})

# ---- object
case("required-bad", {}, {"required": ["a"]})
case("required-ok", {"a": 1}, {"required": ["a"]})
case("dependentRequired-bad", {"a": 1}, {"dependentRequired": {"a": ["b"]}})
case("dependentRequired-ok", {"a": 1, "b": 2}, {"dependentRequired": {"a": ["b"]}})
case("properties-nested-bad", {"a": "x"}, {"properties": {"a": {"type": "integer"}}})
case("patternProperties-bad", {"k1": "x"}, {"patternProperties": {"^k": {"type": "integer"}}})
case("patternProperties-nested-quant", {"k": 1}, {"patternProperties": {"(a+)+": {"type": "integer"}}})
case("additionalProperties-false-bad", {"a": 1, "b": 2}, {"properties": {"a": {}}, "additionalProperties": False})
case("additionalProperties-false-ok", {"a": 1}, {"properties": {"a": {}}, "additionalProperties": False})
case("additionalProperties-schema-bad", {"b": "x"}, {"properties": {"a": {}}, "additionalProperties": {"type": "integer"}})
case("propertyNames-bad", {"1bad": 1}, {"propertyNames": {"pattern": r"^[a-z]"}})

# ---- 组合
case("allOf-bad", 1, {"allOf": [{"type": "integer"}, {"minimum": 5}]})
case("anyOf-ok", 1, {"anyOf": [{"type": "string"}, {"type": "integer"}]})
case("anyOf-bad", 1.5, {"anyOf": [{"type": "string"}, {"type": "integer"}]})
case("oneOf-one-ok", 1, {"oneOf": [{"type": "integer"}, {"type": "string"}]})
case("oneOf-two-bad", 1, {"oneOf": [{"type": "integer"}, {"const": 1}]})
case("not-bad", 1, {"not": {"type": "integer"}})
case("not-ok", "x", {"not": {"type": "integer"}})

# ---- $ref
case("ref-local-ok", 3, {"$defs": {"pos": {"type": "integer"}}, "$ref": "#/defs/x"})
case("ref-local-resolved-bad", "x", {"$defs": {"pos": {"type": "integer"}}, "$ref": "#/$defs/pos"})
case("ref-local-resolved-ok", 3, {"$defs": {"pos": {"type": "integer"}}, "$ref": "#/$defs/pos"})
case("ref-remote-unsupported", 1, {"$ref": "https://example.com/s.json"})
case("ref-dangling-unsupported", 1, {"$ref": "#/$defs/nope"})

# ---- 不支持的关键字（进 unsupported，不影响 errors）
case("unsupported-if", 1, {"if": {"type": "integer"}, "then": {"minimum": 5}})
case("unsupported-dollar", 1, {"$dynamicRef": "#x"})
case("unknown-plain-keyword-ignored", 1, {"myKeyword": 1})

# ---- schema 节点非对象
case("schema-not-object", 1, "not-a-schema")

# ---- 深度闸门（嵌套 > 64）
_deep_schema = {"type": "integer"}
_deep_inst = 1
for _ in range(70):
    _deep_schema = {"type": "object", "properties": {"a": _deep_schema}}
    _deep_inst = {"a": _deep_inst}
case("depth-limit", _deep_inst, _deep_schema)

DEEP_NAME = "depth-limit"
rows = []
deep_row = None
for name, inst, schema in CASES:
    errs = js.json_schema_check(inst, schema)
    if name == DEEP_NAME:
        # serde_json 默认递归上限 128 ⇒ 这条**不进 JSON 表**，改为在 Rust 里直接构造
        deep_row = (name, inst, schema, errs)
        continue
    rows.append((name, inst, schema, errs))
assert deep_row is not None

n_err = sum(1 for r in rows if r[3])
print('# 用例 %d 条，其中 %d 条产出错误' % (len(rows), n_err))
for name, _i, _s, errs in rows:
    if errs:
        print('#   %-38s %s' % (name, errs[0][:90]))

entries = []
for name, inst, schema, errs in rows:
    entries.append(
        '    (\n        %s,\n        %s,\n        %s,\n        %s\n    ),'
        % (rr(name),
           rr(json.dumps(inst, ensure_ascii=False, sort_keys=True)),
           rr(json.dumps(schema, ensure_ascii=False, sort_keys=True)),
           '&[%s]' % ", ".join(rr(e) for e in errs)))

TEMPLATE = r'''
    // >>> GENERATED by tools/gen_json_schema_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 用例级差分（期望值由 `tools/gen_json_schema_cases.py` 从真源生成）=====
    ///
    /// 真语料上上游调用面全是 0 违例 ⇒ 校验器的错误分支一个都踩不到。本判据覆盖各官方关键字、
    /// 边界（`bool` 不算 number、`True == 1`、CJK 按**字符**计长、浮点 `multipleOf`）、
    /// 形态闸门（嵌套量词 / 超长 pattern）、`$ref`（本地 / 远程 / 悬空）、不支持关键字、
    /// schema 非对象、**深度闸门**（> 64 层）。
    #[test]
    fn json_schema_matches_truth_source_case_by_case() {
        let cases: &[(&str, &str, &str, &[&str])] = &[
@@CASES@@
        ];
        let mut n = 0;
        for (name, inst_s, sch_s, want) in cases {
            let inst: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(inst_s).unwrap(),
            )
            .unwrap();
            let sch: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(sch_s).unwrap(),
            )
            .unwrap();
            let got = json_schema_check(&inst, &sch);
            assert_eq!(got, *want, "用例 {} 不一致", name);
            n += 1;
        }
        assert_eq!(n, @@N@@);
    }

    /// 深度闸门单独一条：这条用例有 **70 层**嵌套，`serde_json` 默认递归上限（128）解析不了，
    /// 若硬塞进上面的 JSON 表，报的会是**夹具**的错而不是校验器的结论。故在 Rust 里直接构造。
    #[test]
    fn json_schema_depth_limit_matches_truth_source() {
        let mut sch = Json::Object(vec![("type".to_string(), Json::Str("integer".to_string()))]);
        let mut inst = Json::Int(1);
        for _ in 0..70 {
            sch = Json::Object(vec![
                ("type".to_string(), Json::Str("object".to_string())),
                (
                    "properties".to_string(),
                    Json::Object(vec![("a".to_string(), sch)]),
                ),
            ]);
            inst = Json::Object(vec![("a".to_string(), inst)]);
        }
        assert_eq!(json_schema_check(&inst, &sch), @@DEEPERRS@@ as &[&str]);
    }
    // <<< GENERATED
'''

text = (TEMPLATE.replace('@@CASES@@', "\n".join(entries))
        .replace('@@N@@', str(len(rows)))
        .replace('@@DEEPERRS@@', '&[%s]' % ", ".join(rr(e) for e in deep_row[3])))
BEGIN = '    // >>> GENERATED by tools/gen_json_schema_cases.py（勿手改；重跑生成器覆盖本段）\n'
END = '    // <<< GENERATED\n'
block = BEGIN + text.split(BEGIN, 1)[1]

path = ROOT / 'engine' / 'rust' / 'src' / 'json_schema.rs'
t = path.read_text(encoding='utf-8')
if BEGIN in t:
    a = t.index(BEGIN)
    b = t.index(END, a) + len(END)
    path.write_text(t[:a] + block + t[b:], encoding='utf-8', newline='')
    print('# 已刷新标记区间')
else:
    t = t.rstrip() + '\n\n#[cfg(test)]\nmod tests {\n    use super::*;\n}\n'
    path.write_text(t.rstrip()[:-1].rstrip() + '\n' + block + '}\n', encoding='utf-8', newline='')
    print('# 已插入标记区间')
