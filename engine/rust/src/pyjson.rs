//! 逐字节复刻 Python `json.dumps(v, ensure_ascii=False, indent=2, sort_keys=True)`。
//!
//! **为什么手写而不用 serde_json**：本线的判据是**与 Python 真源逐字节一致**，而
//! serde_json 的输出在缩进、键序、空容器、字符串转义上与 CPython 并不逐字节同形。
//! 真源用哪套排版，本线就必须用哪套——否则"对账"变成"近似"。
//!
//! 已覆盖真源实际用到的值域：对象 / 数组 / 字符串 / 整数 / 浮点 / 布尔 / null。
//! 浮点走 [`crate::pyfloat::repr`]（CPython `float.__repr__` 的复刻）。

/// 一个 JSON 值。
///
/// `Null` / `Bool` 目前未被回执面构造，但**刻意保留**：真源 `json.dumps` 支持它们，
/// 本线的目标是"真源用哪套排版就用哪套"，缺一个变体就会在下一面静默走近似路径。
///
/// `Float` 的写出走 [`crate::pyfloat::repr`]。该实现曾经缺失，那时本模块对浮点
/// **fail-closed 拒绝写出**——理由是没有 repr 就写不出逐字节对账，吐出来的只是"看起来像"。
/// 现已复刻并经真源逐值比对（见 `pyfloat` 模块文档）。
#[derive(Clone, Debug, PartialEq)]
#[allow(dead_code)]
pub enum Json {
    Null,
    Bool(bool),
    Int(i64),
    /// 写出走 [`crate::pyfloat::repr`]（CPython `float.__repr__` 口径）。
    Float(f64),
    Str(String),
    Array(Vec<Json>),
    /// 键值对；**发射时按 UTF-8 字节序排序**（等价 CPython 对 ASCII/Unicode 的码点序）。
    Object(Vec<(String, Json)>),
}

impl Json {
    /// 按 CPython `ensure_ascii=False, indent=2, sort_keys=True` 排版（不含末尾换行）。
    pub fn dumps(&self) -> String {
        let mut out = String::with_capacity(1024);
        emit(self, 0, &mut out);
        out
    }

    /// 按 CPython `ensure_ascii=False, sort_keys=True, separators=(",", ":")` 紧凑排版。
    /// 真源用它构造**叶子载荷**（`{"id":…,"digest":…}`）——载荷差一个空格，根就全变。
    pub fn dumps_compact(&self) -> String {
        let mut out = String::with_capacity(256);
        emit_compact(self, &mut out);
        out
    }

    /// 真源落盘形态：排版 + `\n`（对应 Python `... + "\n"` 后以 `newline=""` 写出的 LF 字节）。
    pub fn dumps_file(&self) -> String {
        let mut s = self.dumps();
        s.push('\n');
        s
    }

    /// CPython `json.dumps(v, ensure_ascii=False, sort_keys=True)`——**默认分隔符**（带空格）、无缩进。
    /// 真源拿它的字节做 sha256（如 `verify_report.root_digest`）。
    pub fn dumps_default(&self) -> String {
        let mut out = String::with_capacity(1024);
        emit_default(self, &mut out);
        out
    }
}

fn indent(out: &mut String, level: usize) {
    for _ in 0..(level * 2) {
        out.push(' ');
    }
}

/// CPython `json.encoder.encode_basestring` 的转义子集（`ensure_ascii=False` 分支）。
fn write_string(s: &str, out: &mut String) {
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{08}' => out.push_str("\\b"),
            '\u{0c}' => out.push_str("\\f"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            c => out.push(c),
        }
    }
    out.push('"');
}

fn emit(v: &Json, level: usize, out: &mut String) {
    match v {
        Json::Null => out.push_str("null"),
        Json::Bool(true) => out.push_str("true"),
        Json::Bool(false) => out.push_str("false"),
        Json::Int(i) => out.push_str(&i.to_string()),
        Json::Float(f) => out.push_str(&crate::pyfloat::repr(*f)),
        Json::Str(s) => write_string(s, out),
        Json::Array(items) => {
            if items.is_empty() {
                out.push_str("[]");
                return;
            }
            out.push('[');
            for (i, it) in items.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                out.push('\n');
                indent(out, level + 1);
                emit(it, level + 1, out);
            }
            out.push('\n');
            indent(out, level);
            out.push(']');
        }
        Json::Object(pairs) => {
            if pairs.is_empty() {
                out.push_str("{}");
                return;
            }
            let mut sorted: Vec<&(String, Json)> = pairs.iter().collect();
            sorted.sort_by(|a, b| a.0.as_bytes().cmp(b.0.as_bytes()));
            out.push('{');
            for (i, (k, val)) in sorted.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                out.push('\n');
                indent(out, level + 1);
                write_string(k, out);
                out.push_str(": ");
                emit(val, level + 1, out);
            }
            out.push('\n');
            indent(out, level);
            out.push('}');
        }
    }
}

/// 无缩进排版；分隔符由参数给定（CPython 有两套：默认 `", "`/`": "` 与紧凑 `","`/`":"`）。
fn emit_flat(v: &Json, out: &mut String, item_sep: &str, kv_sep: &str) {
    match v {
        Json::Null => out.push_str("null"),
        Json::Bool(true) => out.push_str("true"),
        Json::Bool(false) => out.push_str("false"),
        Json::Int(i) => out.push_str(&i.to_string()),
        Json::Float(f) => out.push_str(&crate::pyfloat::repr(*f)),
        Json::Str(s) => write_string(s, out),
        Json::Array(items) => {
            out.push('[');
            for (i, it) in items.iter().enumerate() {
                if i > 0 {
                    out.push_str(item_sep);
                }
                emit_flat(it, out, item_sep, kv_sep);
            }
            out.push(']');
        }
        Json::Object(pairs) => {
            let mut sorted: Vec<&(String, Json)> = pairs.iter().collect();
            sorted.sort_by(|a, b| a.0.as_bytes().cmp(b.0.as_bytes()));
            out.push('{');
            for (i, (k, val)) in sorted.iter().enumerate() {
                if i > 0 {
                    out.push_str(item_sep);
                }
                write_string(k, out);
                out.push_str(kv_sep);
                emit_flat(val, out, item_sep, kv_sep);
            }
            out.push('}');
        }
    }
}

/// 紧凑排版（`separators=(",", ":")`）。
fn emit_compact(v: &Json, out: &mut String) {
    emit_flat(v, out, ",", ":");
}

/// 默认分隔符的无缩进排版（`separators=(", ", ": ")`）——
/// CPython `json.dumps(v)` 不传 separators 时就是这个口径。
/// 真源 `verify_report.build` 的 `root_digest` 源串用它；差一个空格摘要就全变。
fn emit_default(v: &Json, out: &mut String) {
    emit_flat(v, out, ", ", ": ");
}

#[cfg(test)]
mod tests {
    use super::*;

    fn obj(pairs: Vec<(&str, Json)>) -> Json {
        Json::Object(pairs.into_iter().map(|(k, v)| (k.to_string(), v)).collect())
    }

    #[test]
    fn empty_containers_are_inline() {
        assert_eq!(Json::Array(vec![]).dumps(), "[]");
        assert_eq!(Json::Object(vec![]).dumps(), "{}");
    }

    #[test]
    fn sort_keys_is_applied() {
        let v = obj(vec![("b", Json::Int(2)), ("a", Json::Int(1))]);
        assert_eq!(v.dumps(), "{\n  \"a\": 1,\n  \"b\": 2\n}");
    }

    #[test]
    fn default_separators_carry_spaces() {
        // 对照 CPython：json.dumps({"a":1,"b":[1,2]}, ensure_ascii=False, sort_keys=True)
        let v = crate::jsonread::convert(&serde_json::json!({"a": 1, "b": [1, 2]})).unwrap();
        assert_eq!(v.dumps_default(), r#"{"a": 1, "b": [1, 2]}"#);
        assert_eq!(v.dumps_compact(), r#"{"a":1,"b":[1,2]}"#);
    }

    #[test]
    fn nested_layout_matches_cpython_indent2() {
        // 对照 CPython：json.dumps({"a":[{"b":1}]}, ensure_ascii=False, indent=2, sort_keys=True)
        let v = obj(vec![("a", Json::Array(vec![obj(vec![("b", Json::Int(1))])]))]);
        let expect = "{\n  \"a\": [\n    {\n      \"b\": 1\n    }\n  ]\n}";
        assert_eq!(v.dumps(), expect);
    }

    #[test]
    fn non_ascii_is_not_escaped() {
        assert_eq!(Json::Str("新增".into()).dumps(), "\"新增\"");
    }

    #[test]
    fn control_chars_use_cpython_shortcuts() {
        assert_eq!(Json::Str("\n\t\u{8}\u{c}".into()).dumps(), "\"\\n\\t\\b\\f\"");
        assert_eq!(Json::Str("\u{1}".into()).dumps(), "\"\\u0001\"");
    }

    #[test]
    fn file_form_has_single_trailing_newline() {
        assert_eq!(Json::Int(1).dumps_file(), "1\n");
    }
}
