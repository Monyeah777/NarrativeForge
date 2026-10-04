//! YAML **子集**解析器 + 围栏块提取 —— 复刻真源 `conformance_scan._fence_yaml` 的输入面。
//!
//! **为什么自己写**：真源用 PyYAML（`lazy_yaml` 惰性入口），而本线的依赖纪律不容 Python 运行时。
//! 这与 `engine/dotnet` 的 `MiniYaml.cs` 是同一条路数：**只支持真源用到的那一层，越出子集即
//! fail-closed**（不猜、不近似）。
//!
//! **实测界定子集**（2026-10-03，248 份模块文档的 `machine_contract` 围栏块全量普查）：
//!
//! | 构造 | 用量 |
//! |---|---|
//! | 嵌套映射（缩进驱动） | 全部 |
//! | 裸标量 | 3,428 |
//! | 带引号标量 | 486 |
//! | 行内列表 `[a, b]` | 1,226 |
//! | 块列表 `- item` | 41 |
//! | 多行折叠 `\|`/`>` · 锚点 `&`/`*` · 文档分隔 `---` · 制表符 | **0** |
//!
//! **解析后类型面**（同上普查）：`dict` 1,225 · `list` 1,242 · `str` 3,830 · `NoneType` 5，
//! **零 int/float/bool**。故本模块把裸标量一律当字符串；**若某裸标量在 YAML 1.1 下本应解析成
//! 数字/布尔/null，则直接报错**——宁可让对账在门禁上显形，也不静默给出一个错误的字符串值。

use crate::pyjson::Json;

/// 真源 `FENCE = re.compile(r"(?ms)```yaml\s*(.*?)```")`。
fn fence_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"(?s)```yaml\s*(.*?)```").expect("围栏正则固定合法")
    })
}

/// 真源 `_fence_yaml(text, marker)`：取**含 marker 的第一个** ```yaml 块并解析；
/// 未命中 / 解析失败 / 顶层不是映射 → `None`（等价于"本件无该块"）。
pub fn fence_yaml(text: &str, marker: &str) -> Option<Json> {
    for cap in fence_re().captures_iter(text) {
        let body = cap.get(1).map(|m| m.as_str()).unwrap_or("");
        if !body.contains(marker) {
            continue;
        }
        let Ok(parsed) = parse(body) else {
            return None; // 真源此处 except → None
        };
        if matches!(parsed, Json::Object(_)) {
            return Some(parsed);
        }
        return None;
    }
    None
}

/// 解析一段 YAML 子集文本。
pub fn parse(body: &str) -> Result<Json, String> {
    let lines = meaningful_lines(body);
    if lines.is_empty() {
        return Ok(Json::Null);
    }
    let mut i = 0usize;
    let indent = lines[0].0;
    let v = parse_block(&lines, &mut i, indent)?;
    Ok(v)
}

/// `(缩进, 去尾空白的内容)`，跳过空行与整行注释；**行尾注释也剥掉**。
///
/// YAML 里 `#` 只有在**前面是空白**时才是注释开头——真源语料里
/// `host_consumed:          # 终端事件：…` 正是这种：剥掉后才是「空值 + 子块」，
/// 不剥就会被当成值 `"# 终端事件：…"`，摘要随之漂移。
fn meaningful_lines(body: &str) -> Vec<(usize, String)> {
    let mut out = Vec::new();
    for raw in body.lines() {
        let no_cr = raw.trim_end_matches('\r');
        let indent = no_cr.len() - no_cr.trim_start().len();
        let decomm = strip_comment(no_cr);
        let content = decomm.trim();
        if content.is_empty() || content.starts_with('#') {
            continue;
        }
        out.push((indent, content.trim_end().to_string()));
    }
    out
}

/// 剥行尾注释（引号内的 `#` 不算）。
fn strip_comment(line: &str) -> String {
    let chars: Vec<char> = line.chars().collect();
    let mut out = String::with_capacity(line.len());
    let mut quote: Option<char> = None;
    let mut i = 0usize;
    while i < chars.len() {
        let c = chars[i];
        match quote {
            Some(q) => {
                out.push(c);
                if c == '\\' && q == '"' && i + 1 < chars.len() {
                    out.push(chars[i + 1]);
                    i += 2;
                    continue;
                }
                if c == q {
                    quote = None;
                }
            }
            None => {
                if c == '"' || c == '\'' {
                    quote = Some(c);
                    out.push(c);
                } else if c == '#' && (i == 0 || chars[i - 1].is_whitespace()) {
                    break;
                } else {
                    out.push(c);
                }
            }
        }
        i += 1;
    }
    out
}

fn parse_block(
    lines: &[(usize, String)],
    i: &mut usize,
    indent: usize,
) -> Result<Json, String> {
    if lines[*i].1.starts_with("- ") || lines[*i].1 == "-" {
        return parse_seq(lines, i, indent);
    }
    parse_map(lines, i, indent)
}

fn parse_seq(lines: &[(usize, String)], i: &mut usize, indent: usize) -> Result<Json, String> {
    let mut items = Vec::new();
    while *i < lines.len() && lines[*i].0 == indent {
        let text = lines[*i].1.clone();
        if !(text.starts_with("- ") || text == "-") {
            break;
        }
        let rest = text[1..].trim().to_string();
        *i += 1;
        if rest.is_empty() {
            if *i < lines.len() && lines[*i].0 > indent {
                let child = lines[*i].0;
                items.push(parse_block(lines, i, child)?);
            } else {
                items.push(Json::Null);
            }
            continue;
        }
        if rest.starts_with('{') || rest.starts_with('[') {
            // ⚠️ **流式**项必须直接走 `parse_inline`：否则 `split_key` 会把 `{id: C01, ...}`
            // 当成"块式映射项"（键 `id`、值 `C01, branch: compute, ...`），整条节点被压成一个字符串。
            // 实测（2026-10-04）：概念图资产里节点就写成 `- {id: C01, branch: compute, …}`，
            // 102 份图里有 2 份（AI系统域包 / 量化金融域包）踩到这里 ⇒ 它们解析出的节点**全部**缺 id。
            items.push(parse_inline(&rest)?);
            continue;
        }
        if let Some((k, v)) = split_key(&rest) {
            // **列表项本身是映射**（真源 `tool_face:` 就是这个形态）。`- ` 占两列，
            // 故该项内后续键的内容列 = 列表缩进 + 2。
            let child_indent = indent + 2;
            items.push(parse_map_with(lines, i, child_indent, Some((k, v)))?);
            continue;
        }
        items.push(parse_inline(&rest)?);
    }
    Ok(Json::Array(items))
}

fn parse_map(lines: &[(usize, String)], i: &mut usize, indent: usize) -> Result<Json, String> {
    parse_map_with(lines, i, indent, None)
}

/// 映射解析；`first` 用于「首对键值已在手」（列表项映射的首行已被 `- ` 消费掉）。
fn parse_map_with(
    lines: &[(usize, String)],
    i: &mut usize,
    indent: usize,
    first: Option<(String, String)>,
) -> Result<Json, String> {
    let mut pairs: Vec<(String, Json)> = Vec::new();
    let mut pending = first;
    loop {
        let (key, val) = match pending.take() {
            Some(kv) => kv,
            None => {
                if *i >= lines.len() || lines[*i].0 != indent {
                    break;
                }
                let text = lines[*i].1.clone();
                if text.starts_with("- ") {
                    break;
                }
                let Some(kv) = split_key(&text) else {
                    return Err(format!("越出子集：不是键值行：{}", text));
                };
                *i += 1;
                kv
            }
        };
        let value = if val.is_empty() {
            if *i < lines.len() && lines[*i].0 > indent {
                let child = lines[*i].0;
                parse_block(lines, i, child)?
            } else {
                Json::Null
            }
        } else {
            parse_inline(&val)?
        };
        // **同键覆盖**：PyYAML / Python dict 都是后者胜——保留第一条会让摘要在重复键上分叉
        match pairs.iter_mut().find(|(k, _)| *k == key) {
            Some(slot) => slot.1 = value,
            None => pairs.push((key, value)),
        }
    }
    Ok(Json::Object(pairs))
}

/// 找键值分隔点：**第一个「冒号+空格」**，或行尾冒号。
/// （YAML 明文标量里的冒号只要后不跟空格就属内容——真源里 `通用:M10: untyped` 正是这种。）
fn find_key_sep(s: &str) -> Option<usize> {
    if let Some(p) = s.find(": ") {
        return Some(p);
    }
    if s.ends_with(':') && !s.ends_with(": ") {
        return Some(s.len() - 1);
    }
    None
}

fn split_key(line: &str) -> Option<(String, String)> {
    let p = find_key_sep(line)?;
    let key = line[..p].trim().to_string();
    let val = line[p + 1..].trim().to_string();
    Some((key, val))
}

/// 流式映射项的分隔点：**第一个「冒号 + 空白/流指示符/串尾」**。
///
/// 与块式 `find_key_sep` 同一条道理——`AI保险:M01` 里的冒号后面跟的是字母，属内容。
fn split_inline_pair(s: &str) -> Option<(&str, &str)> {
    let b = s.as_bytes();
    let mut quote: Option<u8> = None;
    let mut i = 0usize;
    while i < b.len() {
        let c = b[i];
        match quote {
            Some(q) => {
                if c == b'\\' && q == b'"' {
                    i += 2;
                    continue;
                }
                if c == q {
                    quote = None;
                }
            }
            None => {
                if c == b'"' || c == b'\'' {
                    quote = Some(c);
                } else if c == b':' {
                    let next = b.get(i + 1).copied();
                    let is_sep = matches!(next, None | Some(b' ') | Some(b',') | Some(b'}') | Some(b']'));
                    if is_sep {
                        return Some((&s[..i], &s[i + 1..]));
                    }
                }
            }
        }
        i += 1;
    }
    None
}

/// 行内值：`[]` / `{}` / `[a, b]` / 引号标量 / 裸标量。
fn parse_inline(s: &str) -> Result<Json, String> {
    let t = s.trim();
    if t == "{}" {
        return Ok(Json::Object(Vec::new()));
    }
    if t == "[]" {
        return Ok(Json::Array(Vec::new()));
    }
    if t.starts_with('{') {
        // 流式映射 `{k: v, k: v}`（真源 `protocol.yaml` 的 `mount_layers` 就是这种）。
        // ⚠️ 早先这里对非空流式映射 fail-closed——结果 **111 份 protocol.yaml 全部解析失败**。
        // 教训同变量那条：fail-closed 的粒度要准，拒得越宽，被整件连坐的越多。
        if !t.ends_with('}') {
            return Err(format!("越出子集：花括号不闭合：{}", t));
        }
        let inner = &t[1..t.len() - 1];
        if inner.trim().is_empty() {
            return Ok(Json::Object(Vec::new()));
        }
        let mut pairs: Vec<(String, Json)> = Vec::new();
        for part in split_inline_items(inner) {
            let part = part.trim();
            if part.is_empty() {
                continue;
            }
            let Some((k, v)) = split_inline_pair(part) else {
                return Err(format!("越出子集：流式映射项不是键值对：{}", part));
            };
            let key = plain_or_quoted(k.trim())?;
            let value = if v.trim().is_empty() {
                Json::Null
            } else {
                parse_inline(v.trim())?
            };
            match pairs.iter_mut().find(|(n, _)| *n == key) {
                Some(slot) => slot.1 = value,
                None => pairs.push((key, value)),
            }
        }
        return Ok(Json::Object(pairs));
    }
    if t.starts_with('[') {
        if !t.ends_with(']') {
            return Err(format!("越出子集：方括号不闭合：{}", t));
        }
        let inner = &t[1..t.len() - 1];
        if inner.trim().is_empty() {
            return Ok(Json::Array(Vec::new()));
        }
        let mut items = Vec::new();
        for part in split_inline_items(inner) {
            items.push(parse_inline(part.trim())?);
        }
        return Ok(Json::Array(items));
    }
    if t.starts_with('"') || t.starts_with('\'') {
        return Ok(Json::Str(unquote(t)?));
    }
    plain_scalar(t)
}

/// 行内列表切分：只在**引号外**的逗号处切。
fn split_inline_items(inner: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    let mut quote: Option<char> = None;
    let mut depth: i32 = 0;
    let chars: Vec<char> = inner.chars().collect();
    let mut k = 0;
    while k < chars.len() {
        let c = chars[k];
        match quote {
            Some(q) => {
                cur.push(c);
                if c == '\\' && q == '"' && k + 1 < chars.len() {
                    cur.push(chars[k + 1]);
                    k += 2;
                    continue;
                }
                if c == q {
                    quote = None;
                }
            }
            None => {
                if c == '"' || c == '\'' {
                    quote = Some(c);
                    cur.push(c);
                } else if c == '[' || c == '{' {
                    depth += 1;
                    cur.push(c);
                } else if c == ']' || c == '}' {
                    depth -= 1;
                    cur.push(c);
                } else if c == ',' && depth == 0 {
                    out.push(cur.clone());
                    cur.clear();
                } else {
                    cur.push(c);
                }
            }
        }
        k += 1;
    }
    out.push(cur);
    out
}

/// 剥引号。**首字符必须是引号**——否则 fail-closed。
///
/// ⚠️ 踩过：早先只判「首字符 == 末字符」，于是裸键 `default` 被判为引号标量
/// （`q='d'`，`ends_with('d')` 为真），首尾各剥一个字符 → `efaul`。流式映射的键全被改坏。
fn plain_or_quoted(t: &str) -> Result<String, String> {
    if t.starts_with('"') || t.starts_with('\'') {
        unquote(t)
    } else {
        Ok(t.to_string())
    }
}

fn unquote(t: &str) -> Result<String, String> {
    let q = match t.chars().next() {
        Some(c @ ('"' | '\'')) => c,
        _ => return Err(format!("越出子集：不是引号标量：{}", t)),
    };
    if !t.ends_with(q) || t.chars().count() < 2 {
        return Err(format!("越出子集：引号不闭合：{}", t));
    }
    let inner = &t[1..t.len() - 1];
    if q == '\'' {
        // 单引号里 `''` 表示一个单引号
        return Ok(inner.replace("''", "'"));
    }
    let mut out = String::with_capacity(inner.len());
    let chars: Vec<char> = inner.chars().collect();
    let mut k = 0;
    while k < chars.len() {
        if chars[k] == '\\' && k + 1 < chars.len() {
            let n = chars[k + 1];
            out.push(match n {
                'n' => '\n',
                't' => '\t',
                'r' => '\r',
                '"' => '"',
                '\\' => '\\',
                '0' => '\0',
                other => other,
            });
            k += 2;
            continue;
        }
        out.push(chars[k]);
        k += 1;
    }
    Ok(out)
}

/// 裸标量 → 按 YAML 1.1 解析（与 PyYAML `SafeLoader` 对齐）。
///
/// **为什么必须解析类型而不是一律当字符串**（实测教训 2026-10-03）：一开始本模块对
/// 「看着像非字符串」的裸标量 fail-closed，结果 `M50_主循环.md` 里一个 `tick: 0`
/// 就让**整个模块**解析失败被丢弃，它发布的 `minute_tick` 随之变成"无发布方"，
/// `event-backing` 凭空报出缺口。**fail-closed 必须精确到标量，不能连坐整件。**
///
/// 覆盖 null / bool / int（十·十六·八·二进制）/ float / 字符串；
/// 日期与六十进制（`1:30`）不在子集内，仍 fail-closed。
fn plain_scalar(t: &str) -> Result<Json, String> {
    if is_null_scalar(t) {
        return Ok(Json::Null);
    }
    if let Some(b) = resolve_bool(t) {
        return Ok(Json::Bool(b));
    }
    if let Some(i) = resolve_int(t) {
        return Ok(Json::Int(i));
    }
    if let Some(f) = resolve_float(t) {
        return Ok(Json::Float(f));
    }
    if looks_out_of_subset(t) {
        return Err(format!(
            "越出子集：裸标量 `{}` 在 YAML 1.1 下非字符串，且本线未复刻该类型（不猜）",
            t
        ));
    }
    Ok(Json::Str(t.to_string()))
}

fn is_null_scalar(t: &str) -> bool {
    matches!(t, "~" | "null" | "Null" | "NULL" | "NuLL" | "") || t.trim().is_empty()
}

fn resolve_bool(t: &str) -> Option<bool> {
    match t {
        "yes" | "Yes" | "YES" | "true" | "True" | "TRUE" | "on" | "On" | "ON" => Some(true),
        "no" | "No" | "NO" | "false" | "False" | "FALSE" | "off" | "Off" | "OFF" => Some(false),
        _ => None,
    }
}

fn resolve_int(t: &str) -> Option<i64> {
    let (sign, body) = match t.strip_prefix('-') {
        Some(r) => (-1i64, r),
        None => match t.strip_prefix('+') {
            Some(r) => (1i64, r),
            None => (1i64, t),
        },
    };
    if body.is_empty() {
        return None;
    }
    let clean = body.replace('_', "");
    let radix_prefixed = |p: &str, radix: u32| -> Option<i64> {
        clean.strip_prefix(p).and_then(|h| {
            if h.is_empty() {
                None
            } else {
                i64::from_str_radix(h, radix).ok().map(|v| v * sign)
            }
        })
    };
    if clean.starts_with("0x") || clean.starts_with("0X") {
        return radix_prefixed(&clean[..2], 16);
    }
    if clean.starts_with("0o") || clean.starts_with("0O") {
        return radix_prefixed(&clean[..2], 8);
    }
    if clean.starts_with("0b") || clean.starts_with("0B") {
        return radix_prefixed(&clean[..2], 2);
    }
    // YAML 1.1：前导 0 且全为 0-7 ⇒ 八进制
    if clean.len() > 1 && clean.starts_with('0') && clean.chars().all(|c| ('0'..='7').contains(&c)) {
        return i64::from_str_radix(&clean, 8).ok().map(|v| v * sign);
    }
    if !clean.is_empty() && clean.chars().all(|c| c.is_ascii_digit()) {
        return clean.parse::<i64>().ok().map(|v| v * sign);
    }
    None
}

fn resolve_float(t: &str) -> Option<f64> {
    match t {
        ".inf" | "+.inf" | ".Inf" | "+.Inf" | ".INF" | "+.INF" => return Some(f64::INFINITY),
        "-.inf" | "-.Inf" | "-.INF" => return Some(f64::NEG_INFINITY),
        ".nan" | ".NaN" | ".NAN" => return Some(f64::NAN),
        _ => {}
    }
    let clean = t.replace('_', "");
    // PyYAML 的浮点正则要求有小数点或指数；纯整数归 int
    if !clean.contains('.') && !clean.contains('e') && !clean.contains('E') {
        return None;
    }
    if clean.contains(':') {
        return None; // 六十进制不在子集内
    }
    clean.parse::<f64>().ok()
}

/// 本线**未复刻**但 YAML 1.1 会解析成非字符串的形态（日期 / 六十进制）。
///
/// ⚠️ **不能见冒号就拒**：明文标量里的冒号只要**后面不跟空格**就是内容本身——
/// 真源里 `inputs: [通用:M10]`、`通用:M10: untyped` 都属此列。踩过一次：
/// 一律拒含冒号的标量 ⇒ 大批模块被丢弃 ⇒ `event-backing` 凭空报缺口。
fn looks_out_of_subset(t: &str) -> bool {
    static DATE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = DATE.get_or_init(|| {
        regex::Regex::new(r"^\d{4}-\d{2}-\d{2}([Tt ].*)?$").expect("日期正则固定合法")
    });
    if re.is_match(t) {
        return true;
    }
    static SEXAGESIMAL: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let sx = SEXAGESIMAL.get_or_init(|| {
        regex::Regex::new(r"^[-+]?\d+(:[0-5]?\d)+(\.\d+)?$").expect("六十进制正则固定合法")
    });
    sx.is_match(t)
}

#[cfg(test)]
mod tests {
    use super::*;

    const SAMPLE: &str = "machine_contract:\n  conformance: \"L2\"\n  schema: \"1\"\n  id: M08\n  name: 季节天气\n  inputs: [通用:M10]\n  events:\n    publish: [weather_state]\n    subscribe: [tick_day]\n  interfaces: []\n  io_types:\n    outputs:\n      region: untyped\n";

    #[test]
    fn parses_real_module_block_shape() {
        let v = parse(SAMPLE).expect("真实样本必须可解析");
        let get = |j: &Json, k: &str| crate::pyval::get(j, k).cloned();
        let mc = get(&v, "machine_contract").unwrap();
        assert_eq!(get(&mc, "id"), Some(Json::Str("M08".into())));
        assert_eq!(get(&mc, "name"), Some(Json::Str("季节天气".into())));
        assert_eq!(
            get(&mc, "inputs"),
            Some(Json::Array(vec![Json::Str("通用:M10".into())]))
        );
        assert_eq!(get(&mc, "interfaces"), Some(Json::Array(vec![])));
        let events = get(&mc, "events").unwrap();
        assert_eq!(
            get(&events, "publish"),
            Some(Json::Array(vec![Json::Str("weather_state".into())]))
        );
        let io = get(&mc, "io_types").unwrap();
        let outs = get(&io, "outputs").unwrap();
        assert_eq!(get(&outs, "region"), Some(Json::Str("untyped".into())));
    }

    #[test]
    fn key_colon_without_space_belongs_to_the_key() {
        // 真源里 `通用:M10: untyped` —— 分隔点是**第一个「冒号+空格」**
        let v = parse("io_types:\n  inputs:\n    通用:M10: untyped\n").unwrap();
        let io = crate::pyval::get(&v, "io_types").unwrap();
        let ins = crate::pyval::get(io, "inputs").unwrap();
        assert_eq!(
            crate::pyval::get(ins, "通用:M10"),
            Some(&Json::Str("untyped".into()))
        );
    }

    #[test]
    fn absent_key_and_empty_value_both_yield_null() {
        // `a:` 后无子块 → null；`b: text` 是字符串
        let v = parse("a:\nb: text\n").unwrap();
        assert_eq!(crate::pyval::get(&v, "a"), Some(&Json::Null));
        assert_eq!(crate::pyval::get(&v, "b"), Some(&Json::Str("text".into())));
    }

    #[test]
    fn empty_flow_collections_are_containers_not_strings() {
        // 真源语料里真的有 `outputs: {}` —— 当成字符串会让边界摘要在该件上漂移
        let v = parse("io_types:\n  outputs: {}\n  inputs: []\n").unwrap();
        let io = crate::pyval::get(&v, "io_types").unwrap();
        assert_eq!(crate::pyval::get(io, "outputs"), Some(&Json::Object(vec![])));
        assert_eq!(crate::pyval::get(io, "inputs"), Some(&Json::Array(vec![])));
        // 非空流式映射**现已支持**（真源 protocol.yaml 的 `mount_layers:` 需要它——
        // 早先 fail-closed 曾让 111 份 protocol.yaml 整件解析失败）
        let v2 = parse("k: {a: 1, b: x}\n").unwrap();
        assert_eq!(
            crate::pyval::get(&v2, "k"),
            Some(&Json::Object(vec![
                ("a".into(), Json::Int(1)),
                ("b".into(), Json::Str("x".into())),
            ]))
        );
    }

    #[test]
    fn block_list_items_may_be_mappings() {
        // 真源 `tool_face:` 的真形态（M10_时间推进.md）——曾因「列表项是映射」被我 fail-closed，
        // 导致整个 M10 被丢弃、它发布的 minute_tick 变成"无发布方"。
        let body = "machine_contract:\n  id: 通用:M10\n  tool_face:\n    - purpose: 三轨换算\n      candidates:\n        - repo: https://github.com/arrow-py/arrow\n          ref: 1.3.0\n  events:\n    publish: [minute_tick]\n";
        let v = parse(body).expect("列表项是映射时必须可解析");
        let mc = crate::pyval::get(&v, "machine_contract").unwrap();
        let tf = crate::pyval::get(mc, "tool_face").unwrap();
        let Json::Array(items) = tf else { panic!("tool_face 应是列表") };
        assert_eq!(items.len(), 1);
        assert_eq!(
            crate::pyval::get(&items[0], "purpose"),
            Some(&Json::Str("三轨换算".into()))
        );
        let cands = crate::pyval::get(&items[0], "candidates").unwrap();
        let Json::Array(cs) = cands else { panic!("candidates 应是列表") };
        assert_eq!(
            crate::pyval::get(&cs[0], "repo"),
            Some(&Json::Str("https://github.com/arrow-py/arrow".into()))
        );
        // `ref: 1.3.0` 不是合法浮点 ⇒ PyYAML 当字符串
        assert_eq!(
            crate::pyval::get(&cs[0], "ref"),
            Some(&Json::Str("1.3.0".into()))
        );
    }

    #[test]
    fn scalar_types_follow_yaml_1_1() {
        assert_eq!(parse("k: 0\n").unwrap(), Json::Object(vec![("k".into(), Json::Int(0))]));
        assert_eq!(parse("k: 12\n").unwrap(), Json::Object(vec![("k".into(), Json::Int(12))]));
        assert_eq!(parse("k: -3\n").unwrap(), Json::Object(vec![("k".into(), Json::Int(-3))]));
        assert_eq!(parse("k: 010\n").unwrap(), Json::Object(vec![("k".into(), Json::Int(8))]));
        assert_eq!(parse("k: 0x1f\n").unwrap(), Json::Object(vec![("k".into(), Json::Int(31))]));
        assert_eq!(parse("k: true\n").unwrap(), Json::Object(vec![("k".into(), Json::Bool(true))]));
        assert_eq!(parse("k: no\n").unwrap(), Json::Object(vec![("k".into(), Json::Bool(false))]));
        assert_eq!(parse("k: ~\n").unwrap(), Json::Object(vec![("k".into(), Json::Null)]));
        assert_eq!(parse("k: 1.5\n").unwrap(), Json::Object(vec![("k".into(), Json::Float(1.5))]));
        assert_eq!(parse("k: untyped\n").unwrap(), Json::Object(vec![("k".into(), Json::Str("untyped".into()))]));
    }

    #[test]
    fn one_bad_scalar_must_not_sink_the_whole_block() {
        // 实测教训：`tick: 0` 曾让整件 M50 被丢弃，连带它的 publish 消失
        let body = "machine_contract:\n  id: M50\n  world_model:\n    abstract_state:\n      initial:\n        tick: 0\n  events:\n    publish: [minute_tick]\n";
        let v = parse(body).expect("含整数标量的块必须仍可解析");
        let mc = crate::pyval::get(&v, "machine_contract").unwrap();
        let ev = crate::pyval::get(mc, "events").unwrap();
        assert_eq!(
            crate::pyval::get(ev, "publish"),
            Some(&Json::Array(vec![Json::Str("minute_tick".into())]))
        );
    }

    #[test]
    fn out_of_subset_scalars_are_refused() {
        for bad in ["2026-01-01", "1:30"] {
            let body = format!("k: {}\n", bad);
            assert!(parse(&body).is_err(), "`{}` 应被拒绝", bad);
        }
    }

    #[test]
    fn fence_requires_marker_and_yaml_language() {
        let text = "```yaml\nother: 1\n```\n\n```yaml\nmachine_contract:\n  id: M01\n```\n";
        let got = fence_yaml(text, "machine_contract").expect("应命中第二个块");
        assert!(crate::pyval::get(&got, "machine_contract").is_some());
        assert!(fence_yaml("```json\nmachine_contract: x\n```", "machine_contract").is_none());
    }

    #[test]
    fn flow_mapping_is_supported() {
        // 真源 protocol.yaml 的 `mount_layers:` 真形态——早先 fail-closed 让 111 份件全挂
        let body = "mount_layers:\n  P40 行为决策: {default: [AI保险:M01], available: []}\n  P60 长期演变: {default: [AI保险:M02], available: []}\n";
        let v = parse(body).expect("流式映射必须可解析");
        let ml = crate::pyval::get(&v, "mount_layers").unwrap();
        let p40 = crate::pyval::get(ml, "P40 行为决策").unwrap();
        assert_eq!(
            crate::pyval::get(p40, "default"),
            Some(&Json::Array(vec![Json::Str("AI保险:M01".into())]))
        );
        assert_eq!(
            crate::pyval::get(p40, "available"),
            Some(&Json::Array(Vec::new()))
        );
    }

    #[test]
    fn flow_mapping_value_colon_is_content() {
        // `default: [A:B]` —— 值里的冒号后不跟空白，属内容
        let v = parse("m:\n  k: {default: [A:B], n: 1}\n").unwrap();
        let m = crate::pyval::get(&v, "m").unwrap();
        let k = crate::pyval::get(m, "k").unwrap();
        assert_eq!(
            crate::pyval::get(k, "default"),
            Some(&Json::Array(vec![Json::Str("A:B".into())]))
        );
        assert_eq!(crate::pyval::get(k, "n"), Some(&Json::Int(1)));
    }

    #[test]
    fn inline_splitting_respects_nesting() {
        // 嵌套集合里的逗号不得在顶层切分
        let v = parse("k: [[1, 2], [3]]\n").unwrap();
        assert_eq!(
            crate::pyval::get(&v, "k"),
            Some(&Json::Array(vec![
                Json::Array(vec![Json::Int(1), Json::Int(2)]),
                Json::Array(vec![Json::Int(3)]),
            ]))
        );
    }

    #[test]
    fn trailing_comment_after_empty_value_key_is_not_a_value() {
        // 真源 M91/M92 的真形态：`host_consumed:   # 说明` 后跟块列表
        let body = "events:\n  publish:\n    - a\n  host_consumed:   # 终端事件\n    - b\n";
        let v = parse(body).unwrap();
        let ev = crate::pyval::get(&v, "events").unwrap();
        assert_eq!(
            crate::pyval::get(ev, "publish"),
            Some(&Json::Array(vec![Json::Str("a".into())]))
        );
        assert_eq!(
            crate::pyval::get(ev, "host_consumed"),
            Some(&Json::Array(vec![Json::Str("b".into())])),
            "行尾注释不得被当成值"
        );
    }

    #[test]
    fn hash_inside_quotes_is_not_a_comment() {
        let v = parse("k: \"a # b\"\n").unwrap();
        assert_eq!(crate::pyval::get(&v, "k"), Some(&Json::Str("a # b".into())));
    }

    #[test]
    fn duplicate_keys_take_the_last_like_pyyaml() {
        let v = parse("k: a\nk: b\n").unwrap();
        assert_eq!(crate::pyval::get(&v, "k"), Some(&Json::Str("b".into())));
    }

    #[test]
    fn quoted_scalars_lose_their_quotes() {
        let v = parse("a: \"L2\"\nb: 'it''s'\n").unwrap();
        assert_eq!(crate::pyval::get(&v, "a"), Some(&Json::Str("L2".into())));
        assert_eq!(crate::pyval::get(&v, "b"), Some(&Json::Str("it's".into())));
    }
}
