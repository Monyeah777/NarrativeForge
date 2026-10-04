//! JSON **读取**（Python `json.loads` 口径）+ **重复键**检测 —— 复刻 `output_forms._check_json`
//! 真正依赖的那一层。
//!
//! ## 为什么不直接用 `serde_json`
//!
//! 两处**口径不同**，都会改变判据结论：
//!
//! 1. **重复键**：`serde_json` 静默**后者覆盖**，而真源用 `object_pairs_hook` 把重复键**逐层
//!    收集**出来报「JSON 重复键」（这正是 `_check_json` 的主判据）；
//! 2. **非 RFC 常量**：Python `json.loads` **默认接受** `NaN` / `Infinity` / `-Infinity`
//!    （`parse_constant` 默认给 `float`），而 `serde_json` 一律拒。
//!    ⚠️ 注意与 `asset_contract._strict_json` 的区别：那里**显式**传 `parse_constant=_bad` 去拒
//!    它们；两个调用面的口径**本来就不同**，不能共用一个解析器。
//!
//! 越出子集即 fail-closed（不猜、不近似），路数同 `miniyaml` / `xmlmini`。
//!
//! **一处已知偏差**：超大整数（超出 `i64`）真源给任意精度整数，本线的 `Json` 装不下 ⇒ 记为
//! `Float`。本仓语料无此形态；若将来出现，对账会红。

use crate::pyjson::Json;

/// 解析结果：值 + **逐层收集到的重复键**（出现序，可能重复）。
pub struct Parsed {
    pub value: Json,
    pub dups: Vec<String>,
}

struct P<'a> {
    c: Vec<char>,
    i: usize,
    dups: Vec<String>,
    _t: std::marker::PhantomData<&'a ()>,
}

impl P<'_> {
    fn ws(&mut self) {
        while self.i < self.c.len() && matches!(self.c[self.i], ' ' | '\t' | '\n' | '\r') {
            self.i += 1;
        }
    }
    fn peek(&self) -> Option<char> {
        self.c.get(self.i).copied()
    }
    fn expect(&mut self, ch: char) -> Result<(), String> {
        if self.peek() == Some(ch) {
            self.i += 1;
            Ok(())
        } else {
            Err(format!(
                "Expecting '{}' delimiter: line {} column {}",
                ch,
                self.line(),
                self.col()
            ))
        }
    }
    fn line(&self) -> usize {
        self.c[..self.i].iter().filter(|c| **c == '\n').count() + 1
    }
    fn col(&self) -> usize {
        let last_nl = self.c[..self.i].iter().rposition(|c| *c == '\n');
        match last_nl {
            Some(k) => self.i - k,
            None => self.i + 1,
        }
    }

    fn value(&mut self) -> Result<Json, String> {
        self.ws();
        match self.peek() {
            None => Err(format!("Expecting value: line {} column {}", self.line(), self.col())),
            Some('{') => self.object(),
            Some('[') => self.array(),
            Some('"') => Ok(Json::Str(self.string()?)),
            Some('t') => self.literal("true", Json::Bool(true)),
            Some('f') => self.literal("false", Json::Bool(false)),
            Some('n') => {
                // null 或 NaN
                if self.c[self.i..].starts_with(&['n', 'u', 'l', 'l']) {
                    self.literal("null", Json::Null)
                } else if self.c[self.i..].starts_with(&['n', 'a', 'n']) {
                    self.i += 3;
                    Ok(Json::Float(f64::NAN))
                } else {
                    Err(self.err_value())
                }
            }
            Some('N') => self.literal("NaN", Json::Float(f64::NAN)),
            Some('I') => self.literal("Infinity", Json::Float(f64::INFINITY)),
            Some('-') => {
                if self.c[self.i..].starts_with(&['-', 'I', 'n', 'f']) {
                    self.i += 9;
                    return Ok(Json::Float(f64::NEG_INFINITY));
                }
                self.number()
            }
            Some(c) if c == '-' || c.is_ascii_digit() => self.number(),
            _ => Err(self.err_value()),
        }
    }

    fn err_value(&self) -> String {
        let snippet: String = self.c[self.i..].iter().take(12).collect();
        format!(
            "Expecting value: line {} column {} (char {})",
            self.line(),
            self.col(),
            snippet
        )
    }

    fn literal(&mut self, lit: &str, v: Json) -> Result<Json, String> {
        let chars: Vec<char> = lit.chars().collect();
        if self.c[self.i..].starts_with(&chars) {
            self.i += chars.len();
            Ok(v)
        } else {
            Err(self.err_value())
        }
    }

    fn object(&mut self) -> Result<Json, String> {
        self.expect('{')?;
        let mut out: Vec<(String, Json)> = Vec::new();
        let mut keys: Vec<String> = Vec::new();
        self.ws();
        if self.peek() == Some('}') {
            self.i += 1;
            return Ok(Json::Object(out));
        }
        loop {
            self.ws();
            let key = self.string()?;
            if keys.contains(&key) {
                self.dups.push(key.clone());
            }
            keys.push(key.clone());
            self.ws();
            self.expect(':')?;
            let val = self.value()?;
            match out.iter_mut().find(|(k, _)| *k == key) {
                Some(slot) => slot.1 = val,
                None => out.push((key, val)),
            }
            self.ws();
            match self.peek() {
                Some(',') => {
                    self.i += 1;
                }
                Some('}') => {
                    self.i += 1;
                    return Ok(Json::Object(out));
                }
                _ => {
                    return Err(format!(
                        "Expecting ',' delimiter: line {} column {}",
                        self.line(),
                        self.col()
                    ))
                }
            }
        }
    }

    fn array(&mut self) -> Result<Json, String> {
        self.expect('[')?;
        let mut out: Vec<Json> = Vec::new();
        self.ws();
        if self.peek() == Some(']') {
            self.i += 1;
            return Ok(Json::Array(out));
        }
        loop {
            out.push(self.value()?);
            self.ws();
            match self.peek() {
                Some(',') => {
                    self.i += 1;
                }
                Some(']') => {
                    self.i += 1;
                    return Ok(Json::Array(out));
                }
                _ => {
                    return Err(format!(
                        "Expecting ',' delimiter: line {} column {}",
                        self.line(),
                        self.col()
                    ))
                }
            }
        }
    }

    fn string(&mut self) -> Result<String, String> {
        if self.peek() != Some('"') {
            return Err(format!(
                "Expecting property name enclosed in double quotes: line {} column {}",
                self.line(),
                self.col()
            ));
        }
        self.i += 1;
        let mut s = String::new();
        loop {
            let Some(c) = self.peek() else {
                return Err(format!(
                    "Unterminated string starting at: line {} column {}",
                    self.line(),
                    self.col()
                ));
            };
            self.i += 1;
            match c {
                '"' => return Ok(s),
                '\\' => {
                    let Some(e) = self.peek() else {
                        return Err("Unterminated string".to_string());
                    };
                    self.i += 1;
                    match e {
                        '"' => s.push('"'),
                        '\\' => s.push('\\'),
                        '/' => s.push('/'),
                        'b' => s.push('\u{8}'),
                        'f' => s.push('\u{c}'),
                        'n' => s.push('\n'),
                        'r' => s.push('\r'),
                        't' => s.push('\t'),
                        'u' => {
                            let hex: String =
                                self.c.get(self.i..self.i + 4).map(|v| v.iter().collect()).unwrap_or_default();
                            if hex.len() != 4 {
                                return Err("Invalid \\uXXXX escape".to_string());
                            }
                            self.i += 4;
                            let cp = u32::from_str_radix(&hex, 16)
                                .map_err(|_| "Invalid \\uXXXX escape".to_string())?;
                            // 代理对：高代理后紧跟 \uDC00-\uDFFF 则合成
                            if (0xD800..0xDC00).contains(&cp)
                                && self.c.get(self.i) == Some(&'\\')
                                && self.c.get(self.i + 1) == Some(&'u')
                            {
                                let hex2: String = self
                                    .c
                                    .get(self.i + 2..self.i + 6)
                                    .map(|v| v.iter().collect())
                                    .unwrap_or_default();
                                if let Ok(lo) = u32::from_str_radix(&hex2, 16) {
                                    if (0xDC00..0xE000).contains(&lo) {
                                        self.i += 6;
                                        let combined =
                                            0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00);
                                        if let Some(ch) = char::from_u32(combined) {
                                            s.push(ch);
                                        }
                                        continue;
                                    }
                                }
                            }
                            if let Some(ch) = char::from_u32(cp) {
                                s.push(ch);
                            }
                        }
                        _ => return Err(format!("Invalid \\escape: {}", e)),
                    }
                }
                c if (c as u32) < 0x20 => {
                    return Err(format!(
                        "Invalid control character {:?} at: line {} column {}",
                        c,
                        self.line(),
                        self.col()
                    ))
                }
                _ => s.push(c),
            }
        }
    }

    fn number(&mut self) -> Result<Json, String> {
        let start = self.i;
        let mut is_float = false;
        if self.peek() == Some('-') {
            self.i += 1;
        }
        while let Some(c) = self.peek() {
            if c.is_ascii_digit() {
                self.i += 1;
            } else if c == '.' || c == 'e' || c == 'E' || c == '+' || c == '-' {
                if c == '.' || c == 'e' || c == 'E' {
                    is_float = true;
                }
                self.i += 1;
            } else {
                break;
            }
        }
        let text: String = self.c[start..self.i].iter().collect();
        if text.is_empty() || text == "-" {
            return Err(self.err_value());
        }
        if !is_float {
            if let Ok(v) = text.parse::<i64>() {
                return Ok(Json::Int(v));
            }
        }
        match text.parse::<f64>() {
            Ok(f) => Ok(Json::Float(f)),
            Err(_) => Err(format!("Expecting value: line {} column {}", self.line(), self.col())),
        }
    }
}

/// 真源 `json.loads(text, object_pairs_hook=hook)` 的对应物。
pub fn parse(text: &str) -> Result<Parsed, String> {
    let mut p = P {
        c: text.chars().collect(),
        i: 0,
        dups: Vec::new(),
        _t: std::marker::PhantomData,
    };
    let v = p.value()?;
    p.ws();
    if p.i < p.c.len() {
        return Err(format!(
            "Extra data: line {} column {} (char {})",
            p.line(),
            p.col(),
            p.i
        ));
    }
    Ok(Parsed { value: v, dups: p.dups })
}
