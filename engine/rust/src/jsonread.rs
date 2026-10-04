//! 读入侧：`serde_json::Value` → 本线 `pyjson::Json`。
//!
//! **为什么只用于读**：真源的机读件（registry / standards_catalog / standards_binding /
//! domain_packs）需要解析；而**写出**必须与 CPython `json.dumps` 逐字节同形，那是
//! `pyjson` 的职责——`serde_json` 的排版口径与之不同，绝不能拿它写。
//!
//! 数字只接整数：真源的统计/回执面不产浮点，一旦出现即 fail-fast（不静默走近似排版）。

use crate::pyjson::Json;
use serde_json::Value;
use std::path::Path;

/// 读一个 JSON 文件并转成本线值；读不到或不可解析 → `None`（与真源 `_read_json` 同语义）。
pub fn read_file(root: &Path, rel: &str) -> Option<Json> {
    let text = std::fs::read_to_string(root.join(rel)).ok()?;
    let v: Value = serde_json::from_str(&text).ok()?;
    convert(&v).ok()
}

/// `serde_json::Value` → `Json`。
pub fn convert(v: &Value) -> Result<Json, String> {
    Ok(match v {
        Value::Null => Json::Null,
        Value::Bool(b) => Json::Bool(*b),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Json::Int(i)
            } else if let Some(f) = n.as_f64() {
                // 读入宽容：真源机读件里确实有浮点（standards_binding / domain_packs 等）。
                // 写出的 fail-closed 由 pyjson 一侧负责。
                Json::Float(f)
            } else {
                return Err(format!("无法表示的数值：{}", n));
            }
        }
        Value::String(s) => Json::Str(s.clone()),
        Value::Array(a) => {
            let mut out = Vec::with_capacity(a.len());
            for it in a {
                out.push(convert(it)?);
            }
            Json::Array(out)
        }
        Value::Object(o) => {
            let mut out = Vec::with_capacity(o.len());
            for (k, val) in o {
                out.push((k.clone(), convert(val)?));
            }
            Json::Object(out)
        }
    })
}

/// 结构相等（**对象按无序键比较**——真源 JSON 键序由解析器决定，不承载语义）。
pub fn json_eq(a: &Json, b: &Json) -> bool {
    match (a, b) {
        (Json::Object(x), Json::Object(y)) => {
            if x.len() != y.len() {
                return false;
            }
            x.iter().all(|(k, v)| {
                y.iter()
                    .find(|(k2, _)| k2 == k)
                    .map(|(_, v2)| json_eq(v, v2))
                    .unwrap_or(false)
            })
        }
        (Json::Array(x), Json::Array(y)) => {
            x.len() == y.len() && x.iter().zip(y.iter()).all(|(p, q)| json_eq(p, q))
        }
        _ => a == b,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn object_compare_is_order_insensitive() {
        let a = serde_json::json!({"b": 1, "a": 2});
        let b = serde_json::json!({"a": 2, "b": 1});
        assert!(json_eq(&convert(&a).unwrap(), &convert(&b).unwrap()));
    }

    #[test]
    fn float_is_readable_and_now_writable() {
        // 读入宽容：真源机读件含浮点（standards_binding.json 302 处、domain_packs.json 608 处）。
        let v = serde_json::json!({"x": 1.5});
        let got = convert(&v).expect("浮点必须能读进来");
        assert_eq!(got, Json::Object(vec![("x".to_string(), Json::Float(1.5))]));
        // 写出：CPython `float.__repr__` 已复刻，故不再 fail-closed。
        assert_eq!(Json::Float(1.5).dumps(), "1.5");
        assert_eq!(Json::Float(0.2).dumps(), "0.2");
        assert_eq!(Json::Float(100.0).dumps(), "100.0");
    }

    #[test]
    fn nested_compare_works() {
        let a = serde_json::json!({"x": [1, {"k": "v"}]});
        let b = serde_json::json!({"x": [1, {"k": "v"}]});
        assert!(json_eq(&convert(&a).unwrap(), &convert(&b).unwrap()));
    }
}
