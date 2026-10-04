//! JSON Schema 2020-12 **子集**校验器 —— 与真源 `desktop/src/core/json_schema.py` 对账。
//!
//! 真源是**叶子件**（不 import 任何 core 模块）；本线同形，只依赖 `pyjson` / `pyval`。
//! 调用面：`asset_contract` 的数据面，以及 `output_forms` / `pack_combo`（后者在深度子扫描器里）。
//!
//! 子集边界与真源一致，且**"不支持"绝不等价"通过"**：超出 `_SUPPORTED` 的官方关键字进
//! `unsupported` 清单（调用方若关心可自行取用；`asset_contract` 不取，故不影响其结论）。
//!
//! 三处口径陷阱（都影响逐字节对账）：
//!
//! 1. **`bool` 不是 `number`/`integer`**（Python 里 `isinstance(True, int)` 为真，真源显式排除）。
//! 2. **`const` / `enum` 用 Python 的 `==`**：`True == 1` 成立 ⇒ 本线走 `pyval::py_eq`，
//!    不能用结构相等。
//! 3. **`type(instance).__name__`**：消息里出现的是 `dict` / `list` / `NoneType` 这些
//!    **Python 类型名**，不是 Rust 的。

use crate::pyjson::Json;
use crate::pyval;

const MAX_DEPTH: usize = 64;
const MAX_PATTERN_CHARS: usize = 512;

/// 真源 `_SUPPORTED`：**不**进 `unsupported` 的关键字。
const SUPPORTED: [&str; 34] = [
    "$schema", "$id", "$ref", "$defs", "definitions", "title", "description", "type", "enum",
    "const", "properties", "patternProperties", "required", "additionalProperties", "items",
    "prefixItems", "minItems", "maxItems", "uniqueItems", "minLength", "maxLength", "pattern",
    "format", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "allOf",
    "anyOf", "oneOf", "not", "propertyNames", "dependentRequired",
];

/// 真源 `_UNSUPPORTED_WORDS`：**进** `unsupported` 的官方关键字。
const UNSUPPORTED_WORDS: [&str; 13] = [
    "if", "then", "else", "contains", "minContains", "maxContains", "unevaluatedProperties",
    "unevaluatedItems", "dependentSchemas", "$dynamicRef", "$dynamicAnchor", "contentEncoding",
    "contentMediaType",
];

/// 真源 `type(instance).__name__` 的对应物。
fn py_type_name(v: &Json) -> &'static str {
    match v {
        Json::Null => "NoneType",
        Json::Bool(_) => "bool",
        Json::Int(_) => "int",
        Json::Float(_) => "float",
        Json::Str(_) => "str",
        Json::Array(_) => "list",
        Json::Object(_) => "dict",
    }
}

/// 真源 `_type_ok`。
fn type_ok(value: &Json, want: &str) -> bool {
    match want {
        // `bool` 不算 number/integer（真源显式排除）
        "number" | "integer" => match value {
            Json::Bool(_) | Json::Null | Json::Str(_) | Json::Array(_) | Json::Object(_) => false,
            Json::Int(_) | Json::Float(_) => want == "number" || matches!(value, Json::Int(_)),
        },
        "object" => matches!(value, Json::Object(_)),
        "array" => matches!(value, Json::Array(_)),
        "string" => matches!(value, Json::Str(_)),
        "boolean" => matches!(value, Json::Bool(_)),
        "null" => matches!(value, Json::Null),
        _ => true, // 未知类型名 → 真源 `py is None` → True
    }
}

fn obj_get<'a>(v: &'a Json, k: &str) -> Option<&'a Json> {
    match v {
        Json::Object(o) => o.iter().find(|(kk, _)| kk == k).map(|(_, vv)| vv),
        _ => None,
    }
}

fn obj_has(v: &Json, k: &str) -> bool {
    obj_get(v, k).is_some()
}

/// 迭代 JSON 对象的键（插入序）。
fn obj_keys(v: &Json) -> Vec<String> {
    match v {
        Json::Object(o) => o.iter().map(|(k, _)| k.clone()).collect(),
        _ => Vec::new(),
    }
}

/// 真源 `_resolve_ref`：只支持本地引用；远程/悬空 → `None`。
fn resolve_ref(reference: &str, root_schema: &Json) -> Option<Json> {
    if !reference.starts_with("#/") {
        return None;
    }
    let mut node: Json = root_schema.clone();
    for part in reference[2..].split('/') {
        let part = part.replace("~1", "/").replace("~0", "~");
        match obj_get(&node, &part) {
            Some(v) => node = v.clone(),
            None => return None,
        }
    }
    match node {
        Json::Object(_) => Some(node),
        _ => None,
    }
}

/// 真源 `pattern_issue` → 该 pattern 的形态问题（空串 = 可用）。
pub fn pattern_issue(pat: &Json, path: &str) -> String {
    let text = pyval::plain_str(pat);
    if text.chars().count() > MAX_PATTERN_CHARS {
        return format!(
            "{}: pattern 过长（{} > {} 字符）（修复指引：只写必要的约束）",
            path,
            text.chars().count(),
            MAX_PATTERN_CHARS
        );
    }
    // 嵌套量词（ReDoS 形态）：`(x+)+` / `(x*)*` 一族
    match nested_quant_re() {
        Ok(re) if re.is_match(&text).unwrap_or(false) => {
            format!(
                "{}: pattern 含嵌套量词 {}（可能指数回溯）（修复指引：改写表达式，避免 `(x+)+` / `(x*)*` 这类形态）",
                path,
                pyval::py_repr(&Json::Str(text))
            )
        }
        _ => String::new(),
    }
}

fn nested_quant_re() -> Result<fancy_regex::Regex, fancy_regex::Error> {
    static RE: std::sync::OnceLock<Result<fancy_regex::Regex, fancy_regex::Error>> =
        std::sync::OnceLock::new();
    RE.get_or_init(|| fancy_regex::Regex::new(r"\([^()]*[+*][^()]*\)\s*[+*{]")).clone()
}

/// 用真源同款引擎搜（pattern 来自投稿者，Rust `regex` 不支持回溯构造）。
fn re_search(pat: &str, s: &str) -> bool {
    fancy_regex::Regex::new(pat).map(|r| r.is_match(s).unwrap_or(false)).unwrap_or(false)
}

fn re_fullmatch(pat: &str, s: &str) -> bool {
    fancy_regex::Regex::new(&format!("^(?:{})$", pat))
        .map(|r| r.is_match(s).unwrap_or(false))
        .unwrap_or(false)
}

/// 真源 `_format_errors`。
fn format_errors(value: &str, fmt: &str, path: &str) -> Vec<String> {
    match fmt {
        "date" => {
            if re_fullmatch(r"\d{4}-\d{2}-\d{2}", value) {
                Vec::new()
            } else {
                vec![format!("{}: 非 ISO 8601 日期", path)]
            }
        }
        "date-time" => {
            if re_fullmatch(r"\d{4}-\d{2}-\d{2}[Tt ].+", value) {
                Vec::new()
            } else {
                vec![format!("{}: 非 ISO 8601 日期时间", path)]
            }
        }
        "uri" => {
            if re_search(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value) {
                Vec::new()
            } else {
                vec![format!("{}: 非绝对 URI", path)]
            }
        }
        _ => Vec::new(),
    }
}

/// 真源 `_check`。
#[allow(clippy::too_many_arguments)]
fn check(
    instance: &Json,
    schema: &Json,
    path: &str,
    root_schema: Option<&Json>,
    unsupported: &mut Vec<String>,
    depth: usize,
) -> Vec<String> {
    if depth > MAX_DEPTH {
        return vec![format!(
            "{}: 嵌套超过上限 {} 层（修复指引：schema/实例别做这么深的结构；本仓判据面只处理扁平声明）",
            path, MAX_DEPTH
        )];
    }
    let Json::Object(_) = schema else {
        return vec![format!("{}: schema 节点非对象", path)];
    };
    let root_owned;
    let root: &Json = match root_schema {
        Some(r) => r,
        None => {
            root_owned = schema.clone();
            &root_owned
        }
    };
    let mut errors: Vec<String> = Vec::new();

    // 不支持的官方关键字（排序后遍历，去重）
    let mut keys: Vec<String> = obj_keys(schema);
    keys.sort();
    keys.dedup();
    for kw in keys {
        if SUPPORTED.contains(&kw.as_str()) {
            continue;
        }
        if UNSUPPORTED_WORDS.contains(&kw.as_str()) || kw.starts_with('$') {
            let tag = format!("{}@{}", kw, path);
            if !unsupported.contains(&tag) {
                unsupported.push(tag);
            }
        }
    }

    if let Some(r) = obj_get(schema, "$ref") {
        let refstr = pyval::plain_str(r);
        match resolve_ref(&refstr, root) {
            None => unsupported.push(format!("远程/悬空 $ref {}@{}", refstr, path)),
            Some(target) => {
                errors.extend(check(instance, &target, path, Some(root), unsupported, depth + 1))
            }
        }
    }

    if let Some(types) = obj_get(schema, "type") {
        if !matches!(types, Json::Null) {
            let cand: Vec<Json> = match types {
                Json::Array(a) => a.clone(),
                other => vec![other.clone()],
            };
            if !cand.iter().any(|t| type_ok(instance, &pyval::plain_str(t))) {
                let names: Vec<String> = cand.iter().map(|x| pyval::py_str(Some(x))).collect();
                errors.push(format!(
                    "{}: 类型应为 {}，实为 {}",
                    path,
                    names.join("/"),
                    py_type_name(instance)
                ));
            }
        }
    }
    if let Some(c) = obj_get(schema, "const") {
        if !pyval::py_eq(instance, c) {
            errors.push(format!("{}: 应为常量 {}", path, pyval::py_repr(c)));
        }
    }
    if let Some(Json::Array(en)) = obj_get(schema, "enum") {
        if !en.iter().any(|e| pyval::py_eq(instance, e)) {
            errors.push(format!("{}: 取值 {} 不在枚举内", path, pyval::py_repr(instance)));
        }
    }

    if let Json::Str(s) = instance {
        let len = s.chars().count() as i64;
        if let Some(v) = obj_get(schema, "minLength") {
            if len < pyval::py_int_or(Some(v), 0) {
                errors.push(format!("{}: 长度 < {}", path, pyval::plain_str(v)));
            }
        }
        if let Some(v) = obj_get(schema, "maxLength") {
            if len > pyval::py_int_or(Some(v), 0) {
                errors.push(format!("{}: 长度 > {}", path, pyval::plain_str(v)));
            }
        }
        if let Some(p) = obj_get(schema, "pattern") {
            let why = pattern_issue(p, path);
            if !why.is_empty() {
                errors.push(why);
            } else if !re_search(&pyval::plain_str(p), s) {
                errors.push(format!("{}: 不匹配 pattern {}", path, pyval::plain_str(p)));
            }
        }
        if let Some(f) = obj_get(schema, "format") {
            let fmt = pyval::plain_str(f);
            if !fmt.is_empty() {
                errors.extend(format_errors(s, &fmt, path));
            }
        }
    }

    if matches!(instance, Json::Int(_) | Json::Float(_)) {
        let iv = num_of(instance);
        for (kw, op, cmp) in [
            ("minimum", ">=", 0),
            ("maximum", "<=", 1),
            ("exclusiveMinimum", ">", 2),
            ("exclusiveMaximum", "<", 3),
        ] {
            if let Some(b) = obj_get(schema, kw) {
                let bv = num_of(b);
                let ok = match cmp {
                    0 => iv >= bv,
                    1 => iv <= bv,
                    2 => iv > bv,
                    _ => iv < bv,
                };
                if !ok {
                    errors.push(format!(
                        "{}: {} {} {} 不成立",
                        path,
                        pyval::plain_str(instance),
                        op,
                        pyval::plain_str(b)
                    ));
                }
            }
        }
        if let Some(m) = obj_get(schema, "multipleOf") {
            let mv = num_of(m);
            if mv != 0.0 {
                let q = iv / mv;
                if (q - round_half_even(q)).abs() > 1e-9 {
                    errors.push(format!("{}: 非 {} 的整数倍", path, pyval::plain_str(m)));
                }
            }
        }
    }

    if let Json::Array(items) = instance {
        if let Some(v) = obj_get(schema, "minItems") {
            if (items.len() as i64) < pyval::py_int_or(Some(v), 0) {
                errors.push(format!("{}: 元素数 < {}", path, pyval::plain_str(v)));
            }
        }
        if let Some(v) = obj_get(schema, "maxItems") {
            if (items.len() as i64) > pyval::py_int_or(Some(v), 0) {
                errors.push(format!("{}: 元素数 > {}", path, pyval::plain_str(v)));
            }
        }
        if pyval::py_truthy(&obj_get(schema, "uniqueItems").cloned().unwrap_or(Json::Bool(false)))
        {
            let seen: Vec<String> = items.iter().map(|x| x.dumps()).collect();
            let mut uniq: Vec<&String> = seen.iter().collect();
            uniq.sort();
            uniq.dedup();
            if uniq.len() != seen.len() {
                errors.push(format!("{}: uniqueItems 被违反", path));
            }
        }
        let prefix = obj_get(schema, "prefixItems");
        if let Some(Json::Array(prefix)) = prefix {
            for (i, sub) in prefix.iter().enumerate() {
                if i < items.len() {
                    errors.extend(check(
                        &items[i],
                        sub,
                        &format!("{}[{}]", path, i),
                        Some(root),
                        unsupported,
                        depth + 1,
                    ));
                }
            }
        }
        if let Some(items_schema) = obj_get(schema, "items") {
            if matches!(items_schema, Json::Object(_)) {
                let start = match prefix {
                    Some(Json::Array(p)) => p.len(),
                    _ => 0,
                };
                for i in start..items.len() {
                    errors.extend(check(
                        &items[i],
                        items_schema,
                        &format!("{}[{}]", path, i),
                        Some(root),
                        unsupported,
                        depth + 1,
                    ));
                }
            }
        }
    }

    if let Json::Object(map) = instance {
        let props = obj_get(schema, "properties").cloned().unwrap_or(Json::Object(vec![]));
        let pats =
            obj_get(schema, "patternProperties").cloned().unwrap_or(Json::Object(vec![]));
        if let Some(Json::Array(req)) = obj_get(schema, "required") {
            for key in req {
                let k = pyval::plain_str(key);
                if !obj_has(instance, &k) {
                    errors.push(format!("{}: 缺必填字段 {}", path, k));
                }
            }
        }
        if let Some(Json::Object(deps)) = obj_get(schema, "dependentRequired") {
            for (dep, need) in deps {
                if obj_has(instance, dep) {
                    if let Json::Array(ns) = need {
                        for n in ns {
                            let nk = pyval::plain_str(n);
                            if !obj_has(instance, &nk) {
                                errors.push(format!("{}: 出现 {} 时必填 {}", path, dep, nk));
                            }
                        }
                    }
                }
            }
        }
        for (key, value) in map {
            let mut matched = false;
            if let Some(sub) = obj_get(&props, key) {
                matched = true;
                errors.extend(check(
                    value,
                    sub,
                    &format!("{}.{}", path, key),
                    Some(root),
                    unsupported,
                    depth + 1,
                ));
            }
            if let Json::Object(pats) = &pats {
                for (pat, sub) in pats {
                    let why = pattern_issue(&Json::Str(pat.clone()), path);
                    if !why.is_empty() {
                        errors.push(why); // 形态闸门：不拿投稿者的表达式去跑匹配
                        continue;
                    }
                    if re_search(pat, key) {
                        matched = true;
                        errors.extend(check(
                            value,
                            sub,
                            &format!("{}.{}", path, key),
                            Some(root),
                            unsupported,
                            depth + 1,
                        ));
                    }
                }
            }
            if !matched {
                let ap = obj_get(schema, "additionalProperties").cloned().unwrap_or(Json::Bool(true));
                match ap {
                    Json::Bool(false) => errors.push(format!(
                        "{}: 多余字段 {}（additionalProperties=false）",
                        path, key
                    )),
                    Json::Object(_) => errors.extend(check(
                        value,
                        &ap,
                        &format!("{}.{}", path, key),
                        Some(root),
                        unsupported,
                        depth + 1,
                    )),
                    _ => {}
                }
            }
        }
        if let Some(pn) = obj_get(schema, "propertyNames") {
            if matches!(pn, Json::Object(_)) {
                for (key, _) in map.iter() {
                    errors.extend(check(
                        &Json::Str(key.clone()),
                        pn,
                        &format!("{}<键:{}>", path, key),
                        Some(root),
                        unsupported,
                        depth + 1,
                    ));
                }
            }
        }
    }

    for (kw, mode) in [("allOf", "all"), ("anyOf", "any"), ("oneOf", "one")] {
        let Some(Json::Array(subs)) = obj_get(schema, kw) else { continue };
        let results: Vec<Vec<String>> = subs
            .iter()
            .map(|s| check(instance, s, path, Some(root), unsupported, depth + 1))
            .collect();
        let ok = results.iter().filter(|r| r.is_empty()).count();
        if mode == "all" && ok != subs.len() {
            errors.push(format!(
                "{}: allOf 有 {}/{} 子式不成立",
                path,
                subs.len() - ok,
                subs.len()
            ));
        }
        if mode == "any" && ok == 0 {
            errors.push(format!("{}: anyOf 全不成立", path));
        }
        if mode == "one" && ok != 1 {
            errors.push(format!("{}: oneOf 命中 {} 个（须恰 1）", path, ok));
        }
    }

    if let Some(not) = obj_get(schema, "not") {
        if matches!(not, Json::Object(_))
            && check(instance, not, path, Some(root), unsupported, depth + 1).is_empty()
        {
            errors.push(format!("{}: not 子式被满足", path));
        }
    }
    errors
}

fn num_of(v: &Json) -> f64 {
    match v {
        Json::Int(i) => *i as f64,
        Json::Float(f) => *f,
        Json::Bool(b) => {
            if *b {
                1.0
            } else {
                0.0
            }
        }
        _ => 0.0,
    }
}

/// Python 的 `round()`（**银行家舍入**）。
fn round_half_even(x: f64) -> f64 {
    let r = x.round();
    if (x - x.trunc()).abs() == 0.5 && r % 2.0 != 0.0 {
        r - x.signum()
    } else {
        r
    }
}

/// 真源公开入口 `json_schema_check(instance, schema, path="$", ...)`。
/// 真源 `json_schema_check(..., unsupported=out)` 的对应物：同时给出**不支持关键字**清单。
pub fn json_schema_check_unsup(instance: &Json, schema: &Json) -> (Vec<String>, Vec<String>) {
    let mut unsupported: Vec<String> = Vec::new();
    let errs = check(instance, schema, "$", None, &mut unsupported, 0);
    (errs, unsupported)
}

pub fn json_schema_check(instance: &Json, schema: &Json) -> Vec<String> {
    let mut unsupported: Vec<String> = Vec::new();
    check(instance, schema, "$", None, &mut unsupported, 0)
}

#[cfg(test)]
mod tests {
    use super::*;
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
    (
        r#"type-object-ok"#,
        r#"{}"#,
        r#"{"type": "object"}"#,
        &[]
    ),
    (
        r#"type-object-bad"#,
        r#"[]"#,
        r#"{"type": "object"}"#,
        &[r#"$: 类型应为 object，实为 list"#]
    ),
    (
        r#"type-array-bad"#,
        r#"{}"#,
        r#"{"type": "array"}"#,
        &[r#"$: 类型应为 array，实为 dict"#]
    ),
    (
        r#"type-string-bad"#,
        r#"1"#,
        r#"{"type": "string"}"#,
        &[r#"$: 类型应为 string，实为 int"#]
    ),
    (
        r#"type-bool-bad"#,
        r#"null"#,
        r#"{"type": "boolean"}"#,
        &[r#"$: 类型应为 boolean，实为 NoneType"#]
    ),
    (
        r#"type-null-bad"#,
        r#"0"#,
        r#"{"type": "null"}"#,
        &[r#"$: 类型应为 null，实为 int"#]
    ),
    (
        r#"type-integer-ok"#,
        r#"3"#,
        r#"{"type": "integer"}"#,
        &[]
    ),
    (
        r#"type-integer-float-bad"#,
        r#"3.5"#,
        r#"{"type": "integer"}"#,
        &[r#"$: 类型应为 integer，实为 float"#]
    ),
    (
        r#"type-number-int-ok"#,
        r#"3"#,
        r#"{"type": "number"}"#,
        &[]
    ),
    (
        r#"type-number-float-ok"#,
        r#"3.5"#,
        r#"{"type": "number"}"#,
        &[]
    ),
    (
        r#"type-bool-is-not-number"#,
        r#"true"#,
        r#"{"type": "number"}"#,
        &[r#"$: 类型应为 number，实为 bool"#]
    ),
    (
        r#"type-bool-is-not-integer"#,
        r#"true"#,
        r#"{"type": "integer"}"#,
        &[r#"$: 类型应为 integer，实为 bool"#]
    ),
    (
        r#"type-list-ok"#,
        r#""x""#,
        r#"{"type": ["string", "null"]}"#,
        &[]
    ),
    (
        r#"type-list-bad"#,
        r#"1"#,
        r#"{"type": ["string", "null"]}"#,
        &[r#"$: 类型应为 string/null，实为 int"#]
    ),
    (
        r#"type-unknown-name-passes"#,
        r#"1"#,
        r#"{"type": "widget"}"#,
        &[]
    ),
    (
        r#"const-ok"#,
        r#"1"#,
        r#"{"const": 1}"#,
        &[]
    ),
    (
        r#"const-bad"#,
        r#"2"#,
        r#"{"const": 1}"#,
        &[r#"$: 应为常量 1"#]
    ),
    (
        r#"const-bool-vs-int-ok"#,
        r#"1"#,
        r#"{"const": true}"#,
        &[]
    ),
    (
        r#"enum-ok"#,
        r#""a""#,
        r#"{"enum": ["a", "b"]}"#,
        &[]
    ),
    (
        r#"enum-bad"#,
        r#""c""#,
        r#"{"enum": ["a", "b"]}"#,
        &[r#"$: 取值 'c' 不在枚举内"#]
    ),
    (
        r#"enum-bool-vs-int-ok"#,
        r#"1"#,
        r#"{"enum": [true]}"#,
        &[]
    ),
    (
        r#"str-minLength-bad"#,
        r#""ab""#,
        r#"{"minLength": 3}"#,
        &[r#"$: 长度 < 3"#]
    ),
    (
        r#"str-minLength-ok"#,
        r#""abc""#,
        r#"{"minLength": 3}"#,
        &[]
    ),
    (
        r#"str-maxLength-bad"#,
        r#""abcd""#,
        r#"{"maxLength": 3}"#,
        &[r#"$: 长度 > 3"#]
    ),
    (
        r#"str-maxLength-cjk-counts-chars"#,
        r#""中文字""#,
        r#"{"maxLength": 3}"#,
        &[]
    ),
    (
        r#"str-maxLength-cjk-bad"#,
        r#""中文字符""#,
        r#"{"maxLength": 3}"#,
        &[r#"$: 长度 > 3"#]
    ),
    (
        r#"pattern-ok"#,
        r#""abc123""#,
        r#"{"pattern": "^[a-z]+\\d+$"}"#,
        &[]
    ),
    (
        r#"pattern-bad"#,
        r#""ABC""#,
        r#"{"pattern": "^[a-z]+$"}"#,
        &[r#"$: 不匹配 pattern ^[a-z]+$"#]
    ),
    (
        r#"pattern-nested-quant"#,
        r#""aaa""#,
        r#"{"pattern": "(a+)+$"}"#,
        &[r#"$: pattern 含嵌套量词 '(a+)+$'（可能指数回溯）（修复指引：改写表达式，避免 `(x+)+` / `(x*)*` 这类形态）"#]
    ),
    (
        r#"pattern-star-star"#,
        r#""aaa""#,
        r#"{"pattern": "(a*)*b"}"#,
        &[r#"$: pattern 含嵌套量词 '(a*)*b'（可能指数回溯）（修复指引：改写表达式，避免 `(x+)+` / `(x*)*` 这类形态）"#]
    ),
    (
        r#"pattern-too-long"#,
        r#""a""#,
        r#"{"pattern": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}"#,
        &[r#"$: pattern 过长（600 > 512 字符）（修复指引：只写必要的约束）"#]
    ),
    (
        r#"format-date-ok"#,
        r#""2026-10-04""#,
        r#"{"format": "date"}"#,
        &[]
    ),
    (
        r#"format-date-bad"#,
        r#""2026/10/04""#,
        r#"{"format": "date"}"#,
        &[r#"$: 非 ISO 8601 日期"#]
    ),
    (
        r#"format-datetime-ok"#,
        r#""2026-10-04T11:00:00""#,
        r#"{"format": "date-time"}"#,
        &[]
    ),
    (
        r#"format-datetime-space-ok"#,
        r#""2026-10-04 11:00:00""#,
        r#"{"format": "date-time"}"#,
        &[]
    ),
    (
        r#"format-datetime-bad"#,
        r#""2026-10-04""#,
        r#"{"format": "date-time"}"#,
        &[r#"$: 非 ISO 8601 日期时间"#]
    ),
    (
        r#"format-uri-ok"#,
        r#""https://x.y/z""#,
        r#"{"format": "uri"}"#,
        &[]
    ),
    (
        r#"format-uri-bad"#,
        r#""/relative/path""#,
        r#"{"format": "uri"}"#,
        &[r#"$: 非绝对 URI"#]
    ),
    (
        r#"format-unknown-passes"#,
        r#""x""#,
        r#"{"format": "email"}"#,
        &[]
    ),
    (
        r#"minimum-bad"#,
        r#"1"#,
        r#"{"minimum": 2}"#,
        &[r#"$: 1 >= 2 不成立"#]
    ),
    (
        r#"minimum-ok"#,
        r#"2"#,
        r#"{"minimum": 2}"#,
        &[]
    ),
    (
        r#"maximum-bad"#,
        r#"3"#,
        r#"{"maximum": 2}"#,
        &[r#"$: 3 <= 2 不成立"#]
    ),
    (
        r#"exclusiveMinimum-bad"#,
        r#"2"#,
        r#"{"exclusiveMinimum": 2}"#,
        &[r#"$: 2 > 2 不成立"#]
    ),
    (
        r#"exclusiveMaximum-bad"#,
        r#"2"#,
        r#"{"exclusiveMaximum": 2}"#,
        &[r#"$: 2 < 2 不成立"#]
    ),
    (
        r#"multipleOf-ok"#,
        r#"6"#,
        r#"{"multipleOf": 3}"#,
        &[]
    ),
    (
        r#"multipleOf-bad"#,
        r#"7"#,
        r#"{"multipleOf": 3}"#,
        &[r#"$: 非 3 的整数倍"#]
    ),
    (
        r#"multipleOf-float-ok"#,
        r#"0.3"#,
        r#"{"multipleOf": 0.1}"#,
        &[]
    ),
    (
        r#"multipleOf-float-bad"#,
        r#"0.35"#,
        r#"{"multipleOf": 0.1}"#,
        &[r#"$: 非 0.1 的整数倍"#]
    ),
    (
        r#"minItems-bad"#,
        r#"[1]"#,
        r#"{"minItems": 2}"#,
        &[r#"$: 元素数 < 2"#]
    ),
    (
        r#"maxItems-bad"#,
        r#"[1, 2, 3]"#,
        r#"{"maxItems": 2}"#,
        &[r#"$: 元素数 > 2"#]
    ),
    (
        r#"uniqueItems-bad"#,
        r#"[1, 1]"#,
        r#"{"uniqueItems": true}"#,
        &[r#"$: uniqueItems 被违反"#]
    ),
    (
        r#"uniqueItems-ok"#,
        r#"[1, 2]"#,
        r#"{"uniqueItems": true}"#,
        &[]
    ),
    (
        r#"uniqueItems-objects-bad"#,
        r#"[{"a": 1}, {"a": 1}]"#,
        r#"{"uniqueItems": true}"#,
        &[r#"$: uniqueItems 被违反"#]
    ),
    (
        r#"prefixItems-bad"#,
        r#"[1, "x"]"#,
        r#"{"prefixItems": [{"type": "integer"}, {"type": "integer"}]}"#,
        &[r#"$[1]: 类型应为 integer，实为 str"#]
    ),
    (
        r#"items-bad"#,
        r#"[1, "x"]"#,
        r#"{"items": {"type": "integer"}}"#,
        &[r#"$[1]: 类型应为 integer，实为 str"#]
    ),
    (
        r#"items-with-prefix-skips-prefix"#,
        r#"[1, "x"]"#,
        r#"{"items": {"type": "string"}, "prefixItems": [{"type": "integer"}]}"#,
        &[]
    ),
    (
        r#"required-bad"#,
        r#"{}"#,
        r#"{"required": ["a"]}"#,
        &[r#"$: 缺必填字段 a"#]
    ),
    (
        r#"required-ok"#,
        r#"{"a": 1}"#,
        r#"{"required": ["a"]}"#,
        &[]
    ),
    (
        r#"dependentRequired-bad"#,
        r#"{"a": 1}"#,
        r#"{"dependentRequired": {"a": ["b"]}}"#,
        &[r#"$: 出现 a 时必填 b"#]
    ),
    (
        r#"dependentRequired-ok"#,
        r#"{"a": 1, "b": 2}"#,
        r#"{"dependentRequired": {"a": ["b"]}}"#,
        &[]
    ),
    (
        r#"properties-nested-bad"#,
        r#"{"a": "x"}"#,
        r#"{"properties": {"a": {"type": "integer"}}}"#,
        &[r#"$.a: 类型应为 integer，实为 str"#]
    ),
    (
        r#"patternProperties-bad"#,
        r#"{"k1": "x"}"#,
        r#"{"patternProperties": {"^k": {"type": "integer"}}}"#,
        &[r#"$.k1: 类型应为 integer，实为 str"#]
    ),
    (
        r#"patternProperties-nested-quant"#,
        r#"{"k": 1}"#,
        r#"{"patternProperties": {"(a+)+": {"type": "integer"}}}"#,
        &[r#"$: pattern 含嵌套量词 '(a+)+'（可能指数回溯）（修复指引：改写表达式，避免 `(x+)+` / `(x*)*` 这类形态）"#]
    ),
    (
        r#"additionalProperties-false-bad"#,
        r#"{"a": 1, "b": 2}"#,
        r#"{"additionalProperties": false, "properties": {"a": {}}}"#,
        &[r#"$: 多余字段 b（additionalProperties=false）"#]
    ),
    (
        r#"additionalProperties-false-ok"#,
        r#"{"a": 1}"#,
        r#"{"additionalProperties": false, "properties": {"a": {}}}"#,
        &[]
    ),
    (
        r#"additionalProperties-schema-bad"#,
        r#"{"b": "x"}"#,
        r#"{"additionalProperties": {"type": "integer"}, "properties": {"a": {}}}"#,
        &[r#"$.b: 类型应为 integer，实为 str"#]
    ),
    (
        r#"propertyNames-bad"#,
        r#"{"1bad": 1}"#,
        r#"{"propertyNames": {"pattern": "^[a-z]"}}"#,
        &[r#"$<键:1bad>: 不匹配 pattern ^[a-z]"#]
    ),
    (
        r#"allOf-bad"#,
        r#"1"#,
        r#"{"allOf": [{"type": "integer"}, {"minimum": 5}]}"#,
        &[r#"$: allOf 有 1/2 子式不成立"#]
    ),
    (
        r#"anyOf-ok"#,
        r#"1"#,
        r#"{"anyOf": [{"type": "string"}, {"type": "integer"}]}"#,
        &[]
    ),
    (
        r#"anyOf-bad"#,
        r#"1.5"#,
        r#"{"anyOf": [{"type": "string"}, {"type": "integer"}]}"#,
        &[r#"$: anyOf 全不成立"#]
    ),
    (
        r#"oneOf-one-ok"#,
        r#"1"#,
        r#"{"oneOf": [{"type": "integer"}, {"type": "string"}]}"#,
        &[]
    ),
    (
        r#"oneOf-two-bad"#,
        r#"1"#,
        r#"{"oneOf": [{"type": "integer"}, {"const": 1}]}"#,
        &[r#"$: oneOf 命中 2 个（须恰 1）"#]
    ),
    (
        r#"not-bad"#,
        r#"1"#,
        r#"{"not": {"type": "integer"}}"#,
        &[r#"$: not 子式被满足"#]
    ),
    (
        r#"not-ok"#,
        r#""x""#,
        r#"{"not": {"type": "integer"}}"#,
        &[]
    ),
    (
        r#"ref-local-ok"#,
        r#"3"#,
        r##"{"$defs": {"pos": {"type": "integer"}}, "$ref": "#/defs/x"}"##,
        &[]
    ),
    (
        r#"ref-local-resolved-bad"#,
        r#""x""#,
        r##"{"$defs": {"pos": {"type": "integer"}}, "$ref": "#/$defs/pos"}"##,
        &[r#"$: 类型应为 integer，实为 str"#]
    ),
    (
        r#"ref-local-resolved-ok"#,
        r#"3"#,
        r##"{"$defs": {"pos": {"type": "integer"}}, "$ref": "#/$defs/pos"}"##,
        &[]
    ),
    (
        r#"ref-remote-unsupported"#,
        r#"1"#,
        r#"{"$ref": "https://example.com/s.json"}"#,
        &[]
    ),
    (
        r#"ref-dangling-unsupported"#,
        r#"1"#,
        r##"{"$ref": "#/$defs/nope"}"##,
        &[]
    ),
    (
        r#"unsupported-if"#,
        r#"1"#,
        r#"{"if": {"type": "integer"}, "then": {"minimum": 5}}"#,
        &[]
    ),
    (
        r#"unsupported-dollar"#,
        r#"1"#,
        r##"{"$dynamicRef": "#x"}"##,
        &[]
    ),
    (
        r#"unknown-plain-keyword-ignored"#,
        r#"1"#,
        r#"{"myKeyword": 1}"#,
        &[]
    ),
    (
        r#"schema-not-object"#,
        r#"1"#,
        r#""not-a-schema""#,
        &[r#"$: schema 节点非对象"#]
    ),
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
        assert_eq!(n, 83);
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
        assert_eq!(json_schema_check(&inst, &sch), &[r#"$.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a: 嵌套超过上限 64 层（修复指引：schema/实例别做这么深的结构；本仓判据面只处理扁平声明）"#] as &[&str]);
    }
    // <<< GENERATED
}
