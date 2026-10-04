//! Python 值语义助手 —— 逐字节对账的**公共地基**。
//!
//! 真源在 `str(x)` 与 `str(x or "")` 之间**混用**（同一模块内并存），二者的差别只在假值上：
//!
//! | 表达式 | `None` | `False` | `0` | `""` | `[]` |
//! |---|---|---|---|---|---|
//! | `str(x or "")`（[`py_str`]） | `""` | `""` | `""` | `""` | `""` |
//! | `str(x)`（[`plain_str`]） | `"None"` | `"False"` | `"0"` | `""` | `"[]"` |
//!
//! 抄错一处就会在边界案例上静默分叉，故两者分开实现、各有对照判据。
//! 本模块被 `contracts`（一致性契约）与 `layers`（阶梯体检）共用——**唯一实现**。

use crate::pyjson::Json;

/// `j.get(k)`（缺失 → `None`）。
pub fn get<'a>(j: &'a Json, k: &str) -> Option<&'a Json> {
    match j {
        Json::Object(p) => p.iter().find(|(n, _)| n == k).map(|(_, v)| v),
        _ => None,
    }
}

pub fn obj_is_empty(j: &Json) -> bool {
    matches!(j, Json::Object(p) if p.is_empty())
}

pub fn arr_items(j: Option<&Json>) -> Vec<&Json> {
    match j {
        Some(Json::Array(a)) => a.iter().collect(),
        _ => Vec::new(),
    }
}

pub fn arr_is_empty(j: Option<&Json>) -> bool {
    match j {
        None | Some(Json::Null) => true,
        Some(Json::Array(a)) => a.is_empty(),
        _ => false,
    }
}

/// `[str(v) for v in (x or [])]`。
pub fn str_list(j: Option<&Json>) -> Vec<String> {
    match j {
        Some(Json::Array(a)) => a
            .iter()
            .map(|v| match v {
                Json::Str(s) => s.clone(),
                other => py_str(Some(other)),
            })
            .collect(),
        _ => Vec::new(),
    }
}

/// Python `str(x)`（**无** `or ""` 兜底）：`None` → `"None"`、`False` → `"False"`、`0` → `"0"`。
///
/// 浮点走 [`crate::pyfloat::repr`]（Py3 的 `str(float) is repr(float)`）——
/// 用 Rust 的 `Display` 会把 `1.0` 打成 `1`、`1e16` 打成 `10000000000000000`，与真源分叉。
pub fn plain_str(j: &Json) -> String {
    match j {
        Json::Null => "None".into(),
        Json::Bool(b) => if *b { "True".into() } else { "False".into() },
        Json::Int(i) => i.to_string(),
        Json::Float(f) => crate::pyfloat::repr(*f),
        Json::Str(s) => s.clone(),
        Json::Array(a) => py_repr_list(a),
        Json::Object(_) => py_repr(j),
    }
}

/// Python `str(x)`，`x` 可能因缺键而为 `None`。
pub fn plain_str_opt(j: Option<&Json>) -> String {
    match j {
        Some(v) => plain_str(v),
        None => "None".to_string(),
    }
}

/// Python `str(x or "")`：假值（None / False / 0 / "" / [] / {}）→ 空串。
///
/// 等价式：`if not py_truthy(x) { "" } else { plain_str(x) }` —— 真值与 [`plain_str`] 同源，
/// 只在假值上分道，故不需第二套 str 实现。
pub fn py_str(j: Option<&Json>) -> String {
    let Some(v) = j else { return String::new() };
    if !py_truthy(v) {
        return String::new();
    }
    plain_str(v)
}

/// Python `bool(x)`。
pub fn py_truthy(j: &Json) -> bool {
    match j {
        Json::Null => false,
        Json::Bool(b) => *b,
        Json::Int(i) => *i != 0,
        Json::Float(f) => *f != 0.0,
        Json::Str(s) => !s.is_empty(),
        Json::Array(a) => !a.is_empty(),
        Json::Object(p) => !p.is_empty(),
    }
}

/// Python `==`（含 `True == 1`；对象比较与键序无关）。
pub fn py_eq(a: &Json, b: &Json) -> bool {
    match (a, b) {
        (Json::Object(_), Json::Object(_)) => crate::jsonread::json_eq(a, b),
        (Json::Array(x), Json::Array(y)) => {
            x.len() == y.len() && x.iter().zip(y.iter()).all(|(p, q)| py_eq(p, q))
        }
        (Json::Bool(x), Json::Int(y)) => (*x as i64) == *y,
        (Json::Int(x), Json::Bool(y)) => *x == (*y as i64),
        _ => a == b,
    }
}

/// Python `int(x or default)`：**0 是假值**，会落到 default。
pub fn py_int_or(j: Option<&Json>, default: i64) -> i64 {
    match j {
        Some(Json::Int(i)) => if *i == 0 { default } else { *i },
        Some(Json::Bool(true)) => 1,
        _ => default,
    }
}

/// Python `repr()` 对一个字符串的**转义口径**（`str.__repr__`）。
///
/// 为什么单列一条（实测，2026-10-04）：原实现只替换 `\` 与 `'`，于是 `repr("ok\x00bad")`
/// 会吐出**裸 NUL**，而 Python 给 `'ok\\x00bad'`。凡消息里带 `%r` 且值含控制字符的面都会**逐字节**
/// 不符——`paths` 的控制字符分支就是当场抓到它的地方。
///
/// 覆盖：`\\` `\'` `\t` `\n` `\r`；其余 C0 与 DEL → `\xNN`；不可打印的更高码位 → `\xNN`/`\uNNNN`/`\UNNNNNNNN`。
/// **一处近似（如实记）**：Python 的 `str.isprintable()` 走 `unicodedata` 全表；本线用
/// `char::is_control()` + 常见 Cf/Co/Cs/Zl/Zp 区段近似。本仓语料无这类字符；若将来出现，对账会红。
fn repr_str(s: &str) -> String {
    let mut out = String::new();
    for c in s.chars() {
        match c {
            '\\' => out.push_str("\\\\"),
            '\'' => out.push_str("\\'"),
            '\t' => out.push_str("\\t"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            c if (c as u32) < 0x20 || (c as u32) == 0x7f => {
                out.push_str(&format!("\\x{:02x}", c as u32))
            }
            c if !py_isprintable(c) => {
                let cp = c as u32;
                if cp < 0x100 {
                    out.push_str(&format!("\\x{:02x}", cp));
                } else if cp < 0x10000 {
                    out.push_str(&format!("\\u{:04x}", cp));
                } else {
                    out.push_str(&format!("\\U{:08x}", cp));
                }
            }
            c => out.push(c),
        }
    }
    out
}

/// Python `str.isprintable()` 的**近似**（见 `repr_str` 的说明）。
fn py_isprintable(c: char) -> bool {
    if c == ' ' {
        return true;
    }
    if c.is_control() {
        return false;
    }
    let cp = c as u32;
    // Cf（格式字符）/ Co（私用区）/ Cs（代理区）/ Zl / Zp 的主要区段
    !matches!(cp,
        0x00AD | 0x0600..=0x0605 | 0x061C | 0x06DD | 0x070F | 0x0890..=0x0891
        | 0x08E2 | 0x180E | 0x200B..=0x200F | 0x2028..=0x202E | 0x2060..=0x2064
        | 0x2066..=0x206F | 0xFEFF | 0xFFF9..=0xFFFB | 0x110BD | 0x110CD
        | 0xE000..=0xF8FF | 0xF0000..=0xFFFFD | 0x100000..=0x10FFFD)
}

/// Python `repr(x)` 的子集（真源 `%s` 打在 list/dict 上时走它）。字符串用单引号。
pub fn py_repr(j: &Json) -> String {
    match j {
        Json::Null => "None".into(),
        Json::Bool(b) => if *b { "True".into() } else { "False".into() },
        Json::Int(i) => i.to_string(),
        Json::Float(f) => crate::pyfloat::repr(*f),
        Json::Str(s) => format!("'{}'", repr_str(s)),
        Json::Array(a) => py_repr_list(a),
        Json::Object(p) => {
            let body: Vec<String> = p
                .iter()
                .map(|(k, v)| format!("{}: {}", py_repr(&Json::Str(k.clone())), py_repr(v)))
                .collect();
            format!("{{{}}}", body.join(", "))
        }
    }
}

/// Python `str(list)` / `repr(list)`：`['a', 'b']`。
pub fn py_repr_list(items: &[Json]) -> String {
    let parts: Vec<String> = items.iter().map(py_repr).collect();
    format!("[{}]", parts.join(", "))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn plain_str_and_py_str_differ_only_on_falsy() {
        assert_eq!(plain_str(&Json::Null), "None");
        assert_eq!(py_str(Some(&Json::Null)), "");
        assert_eq!(plain_str(&Json::Int(0)), "0");
        assert_eq!(py_str(Some(&Json::Int(0))), "");
        assert_eq!(plain_str(&Json::Bool(false)), "False");
        assert_eq!(py_str(Some(&Json::Bool(false))), "");
        // 真值上二者一致
        assert_eq!(plain_str(&Json::Int(7)), py_str(Some(&Json::Int(7))));
        assert_eq!(plain_str(&Json::Str("x".into())), py_str(Some(&Json::Str("x".into()))));
    }

    #[test]
    fn list_repr_matches_python() {
        let l = vec![Json::Str("a".into()), Json::Str("b".into())];
        assert_eq!(py_repr_list(&l), "['a', 'b']");
        assert_eq!(plain_str(&Json::Array(l.clone())), "['a', 'b']");
    }

    #[test]
    fn list_repr_escapes_quotes_like_python() {
        assert_eq!(py_repr(&Json::Str("it's".into())), "'it\\'s'");
    }

    #[test]
    fn truthiness_and_equality_follow_python() {
        assert!(!py_truthy(&Json::Null));
        assert!(!py_truthy(&Json::Array(vec![])));
        assert!(py_eq(&Json::Bool(true), &Json::Int(1)));
        assert!(py_eq(&Json::Int(1), &Json::Bool(true)));
        assert!(!py_eq(&Json::Bool(true), &Json::Int(2)));
    }

    #[test]
    fn int_or_treats_zero_as_falsy() {
        assert_eq!(py_int_or(Some(&Json::Int(0)), 5), 5);
        assert_eq!(py_int_or(Some(&Json::Int(3)), 5), 3);
        assert_eq!(py_int_or(None, 5), 5);
        assert_eq!(py_int_or(Some(&Json::Bool(true)), 5), 1);
    }
}

/// Python `str.splitlines()` 的**行数**。
///
/// 为什么不直接用 Rust 的 `lines()`：两者的换行符集合不同——Python 还在 `\v`(0x0b)、
/// `\f`(0x0c)、`\x1c`/`\x1d`/`\x1e`、`\x85`、`\u2028`、`\u2029` 处断行，Rust 只认 `\n` 与 `\r\n`。
/// 实测边界（`''`→0、`'a\n'`→1、`'a\n\n'`→2、`'\n'`→1）两者一致，但"常见情况一致"不是口径：
/// `code_metrics` 的行数要拿去和**冻结基线**比，差一行就是假红/假绿。
pub fn splitlines_count(s: &str) -> usize {
    let breaks = |c: char| {
        matches!(
            c,
            '\n' | '\r' | '\u{0b}' | '\u{0c}' | '\u{1c}' | '\u{1d}' | '\u{1e}' | '\u{85}'
                | '\u{2028}' | '\u{2029}'
        )
    };
    let mut n = 0usize;
    let mut it = s.chars().peekable();
    let mut any = false;
    while let Some(c) = it.next() {
        any = true;
        if c == '\r' {
            if it.peek() == Some(&'\n') {
                it.next();
            }
            n += 1;
        } else if breaks(c) {
            n += 1;
        }
    }
    // 末尾不是换行符 ⇒ 最后一行还没算
    if any && !s.ends_with(breaks) {
        n += 1;
    }
    n
}
