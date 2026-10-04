//! 数字资产契约层（数据 / 代码 / 脚本三面 · 声明即契约）—— 与真源
//! `desktop/src/core/asset_contract.py` 的 `scan` 对账。
//!
//! **不移植**：`freeze()`（重冻 sha256）与 `run_tests()` / `_run_test_file()`（执行被声明脚本）
//! ——前者是写面、后者是执行层，按目标纪律都不碰。
//!
//! 三面口径见真源模块文档。本文件按面拆成三段：数据面 / 代码面 / 脚本面。
//!
//! ## 已知偏差（两处，都是**外来输入的报错文本**）
//!
//! 1. **JSON 解析失败的文本**：真源给 CPython `json` 的报错，本线给 `serde_json` 的。
//! 2. **读件失败的文本**：真源给 `OSError` / `UnicodeDecodeError` 的 repr，本线给 `std::io` 的。
//!
//! 二者都只在**坏输入**时出现在消息里；真语料上这两支都不触发。分支判据里做**归一**后比较，
//! 不假装文本相同（同 `code_metrics` 的语法支处理）。

use crate::json_schema;
use crate::pyjson::Json;
use crate::pyval;
use std::path::Path;

pub const DECL_REL: &str = "protocol/asset_contracts.json";
pub const SCHEMA: &str = "nf-asset-contracts/1";
pub const FACES: [&str; 3] = ["data", "code", "script"];
pub const LANGS: [&str; 3] = ["python", "bash", "vba"];
pub const FORMATS: [&str; 4] = ["json", "csv", "markdown", "text"];

// ---------------------------------------------------------------- 基础

fn obj_get<'a>(v: &'a Json, k: &str) -> Option<&'a Json> {
    match v {
        Json::Object(o) => o.iter().find(|(kk, _)| kk == k).map(|(_, vv)| vv),
        _ => None,
    }
}

/// 真源 `spec.get(k)`：缺键 → `Null`（Python 的 `None`）。
fn sg(spec: &Json, k: &str) -> Json {
    obj_get(spec, k).cloned().unwrap_or(Json::Null)
}

/// 真源 `str(spec.get(k) or "")` 的常用形态。
fn sg_str(spec: &Json, k: &str) -> String {
    match obj_get(spec, k) {
        None | Some(Json::Null) => String::new(),
        Some(v) => pyval::plain_str(v),
    }
}

/// 真源 `spec.get(k) or []` → 字符串列表。
fn sg_strs(spec: &Json, k: &str) -> Vec<String> {
    match obj_get(spec, k) {
        Some(Json::Array(a)) => a.iter().map(pyval::plain_str).collect(),
        _ => Vec::new(),
    }
}

/// 真源 `digest_of`：文件内容 sha256 十六进制。
pub fn digest_of(p: &Path) -> String {
    match std::fs::read(p) {
        Ok(b) => crate::merkle::hex(&crate::merkle::sha256(&b)),
        Err(_) => String::new(),
    }
}

/// 真源 `_read(root, rel)` → `(text, issue)`。
pub fn sread(root: &Path, rel: &str) -> (Option<String>, Option<String>) {
    let p = root.join(rel);
    match std::fs::read(&p) {
        Err(e) => (
            None,
            Some(format!("读不到 {}：{}（修复指引：核对声明里的路径在场）", rel, e)),
        ),
        Ok(b) => match String::from_utf8(b) {
            Ok(s) => (Some(s), None),
            Err(e) => (
                None,
                Some(format!("{} 不是 UTF-8：{}（修复指引：转成 UTF-8 再入库）", rel, e)),
            ),
        },
    }
}

/// 真源 `resolve`：`path` 单件 / `glob` 多件（稳定排序）。
pub fn resolve(root: &Path, spec: &Json) -> Vec<String> {
    if let Some(p) = obj_get(spec, "path") {
        if pyval::py_truthy(p) {
            let rel = pyval::plain_str(p).replace('\\', "/");
            return if root.join(&rel).is_file() { vec![rel] } else { vec![] };
        }
    }
    let pat = sg_str(spec, "glob");
    if pat.is_empty() {
        return Vec::new();
    }
    let mut v = crate::glob::expand(root, &pat);
    v.sort();
    v
}

/// 真源 `_dig`：按点号路径取值；取不到 → `None`（哨兵）。
pub fn dig(obj: &Json, path: &str) -> Option<Json> {
    let mut cur = obj.clone();
    for part in path.split('.') {
        match &cur {
            Json::Object(o) => match o.iter().find(|(k, _)| k == part) {
                Some((_, v)) => cur = v.clone(),
                None => return None,
            },
            Json::Array(a) => {
                let idx: Option<usize> = part.parse().ok();
                match idx {
                    Some(i) if i < a.len() => cur = a[i].clone(),
                    _ => return None,
                }
            }
            _ => return None,
        }
    }
    Some(cur)
}

// ---------------------------------------------------------------- CSV（Python csv.reader 默认方言）

/// Python `csv.reader` 默认方言：分隔 `,`、引号 `"`、`""` 转义、**不**跳过空白。
///
/// 不是"按逗号 split"——带引号字段里的逗号/换行不切分，这是真源 `_csv_rows` 的口径。
pub fn csv_rows(text: &str) -> Vec<Vec<String>> {
    let mut rows: Vec<Vec<String>> = Vec::new();
    let mut row: Vec<String> = Vec::new();
    let mut field = String::new();
    let mut in_quotes = false;
    let mut chars = text.chars().peekable();
    while let Some(c) = chars.next() {
        if in_quotes {
            if c == '"' {
                if chars.peek() == Some(&'"') {
                    field.push('"');
                    chars.next();
                } else {
                    in_quotes = false;
                }
            } else {
                field.push(c);
            }
            continue;
        }
        match c {
            '"' if field.is_empty() => in_quotes = true,
            ',' => {
                row.push(std::mem::take(&mut field));
            }
            '\r' => {
                if chars.peek() == Some(&'\n') {
                    chars.next();
                }
                row.push(std::mem::take(&mut field));
                rows.push(std::mem::take(&mut row));
            }
            '\n' => {
                row.push(std::mem::take(&mut field));
                rows.push(std::mem::take(&mut row));
            }
            _ => field.push(c),
        }
    }
    // 末尾无换行 ⇒ 还有一行（Python 同）
    if !field.is_empty() || !row.is_empty() {
        row.push(field);
        rows.push(row);
    }
    rows
}

// ---------------------------------------------------------------- 数据面

/// 真源 `_data_json`。
fn data_json(root: &Path, rel: &str, text: &str, spec: &Json) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let obj = match strict_json(text) {
        Ok(v) => v,
        Err(e) => {
            return (
                vec![format!("数据件 {} 不是合法 JSON：{}（修复指引：修好语法或换 format）", rel, e)],
                Json::Object(vec![]),
            )
        }
    };
    let sch_rel = sg_str(spec, "schema");
    if !sch_rel.is_empty() {
        let (sch_text, err) = sread(root, &sch_rel);
        match err {
            Some(e) => issues.push(format!("数据件 {} 的 schema 读不到：{}", rel, e)),
            None => {
                let errs = match strict_json(&sch_text.unwrap_or_default()) {
                    Ok(s) => json_schema::json_schema_check(&obj, &s),
                    Err(e) => vec![format!("schema 本身不是合法 JSON：{}", e)],
                };
                for e in errs.iter().take(5) {
                    issues.push(format!("数据件 {} 不符 schema {}：{}", rel, sch_rel, e));
                }
            }
        }
    }
    if let Some(Json::Array(req)) = obj_get(spec, "required_fields") {
        for field in req {
            let f = pyval::plain_str(field);
            if dig(&obj, &f).is_none() {
                issues.push(format!(
                    "数据件 {} 缺必填字段 {}（修复指引：补字段或从声明里删掉——声明即契约）",
                    rel, f
                ));
            }
        }
    }
    let nf = match obj_get(spec, "required_fields") {
        Some(Json::Array(a)) => a.len() as i64,
        _ => 0,
    };
    (issues, Json::Object(vec![("fields".to_string(), Json::Int(nf))]))
}

/// 真源 `_data_csv`。
fn data_csv(rel: &str, text: &str, spec: &Json) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    let rows = csv_rows(text);
    if rows.is_empty() {
        return (
            vec![format!("数据件 {} 是空 CSV（修复指引：至少要有表头行）", rel)],
            Json::Object(vec![("rows".to_string(), Json::Int(0))]),
        );
    }
    let header: Vec<String> = rows[0].iter().map(|c| c.trim().to_string()).collect();
    if header.iter().any(|c| c.is_empty()) {
        issues.push(format!("数据件 {} 表头有空列名（修复指引：每列都要有名字）", rel));
    }
    let width = header.len();
    let data: Vec<&Vec<String>> =
        rows[1..].iter().filter(|r| !(r.len() == 1 && r[0].is_empty())).collect();
    let bad: Vec<usize> = data
        .iter()
        .enumerate()
        .filter(|(_, r)| r.len() != width)
        .map(|(i, _)| i + 2)
        .collect();
    if !bad.is_empty() {
        let bs: Vec<String> = bad.iter().take(3).map(|b| b.to_string()).collect();
        issues.push(format!(
            "数据件 {} 第 {} 行列数 != 表头 {}（修复指引：补齐/删除多余的分隔符）",
            rel,
            bs.join(","),
            width
        ));
    }
    let missing: Vec<String> = sg_strs(spec, "required_columns")
        .into_iter()
        .filter(|c| !header.contains(c))
        .collect();
    if !missing.is_empty() {
        issues.push(format!(
            "数据件 {} 缺必需列 {}（修复指引：加列或改声明）",
            rel,
            missing.join(",")
        ));
    }
    let low = pyval::py_int_or(obj_get(spec, "min_rows"), 0);
    if (data.len() as i64) < low {
        issues.push(format!(
            "数据件 {} 数据行 {} < min_rows {}（修复指引：补样例或下调声明）",
            rel,
            data.len(),
            low
        ));
    }
    (
        issues,
        Json::Object(vec![
            ("rows".to_string(), Json::Int(data.len() as i64)),
            ("columns".to_string(), Json::Int(width as i64)),
        ]),
    )
}

/// 真源 `_md_tables`：按连续竖线行切表。
pub fn md_tables(text: &str) -> Vec<Vec<Vec<String>>> {
    let mut tables: Vec<Vec<Vec<String>>> = Vec::new();
    let mut cur: Vec<Vec<String>> = Vec::new();
    for line in text.lines() {
        let s = line.trim();
        if s.starts_with('|') && s.matches('|').count() >= 2 {
            let inner = s.trim_matches('|');
            cur.push(inner.split('|').map(|c| c.trim().to_string()).collect());
        } else if !cur.is_empty() {
            tables.push(std::mem::take(&mut cur));
        }
    }
    if !cur.is_empty() {
        tables.push(cur);
    }
    tables
}

/// 真源 `_data_markdown`。
fn data_markdown(rel: &str, text: &str, spec: &Json) -> (Vec<String>, Json) {
    let mut issues: Vec<String> = Vec::new();
    if pyval::py_truthy(&sg(spec, "frontmatter")) && !text.starts_with("---") {
        issues.push(format!("数据件 {} 缺 frontmatter（修复指引：件首补 --- 块）", rel));
    }
    let mut n = 0i64;
    for table in md_tables(text) {
        if table.len() < 2 {
            continue;
        }
        let header = &table[0];
        // 分隔行：每格只由 `-` 与 `:` 组成
        let body: Vec<&Vec<String>> = table[1..]
            .iter()
            .filter(|r| !r.iter().all(|c| c.chars().all(|ch| ch == '-' || ch == ':')))
            .collect();
        let ragged: Vec<&&Vec<String>> =
            body.iter().filter(|r| r.len() != header.len()).collect();
        if let Some(first) = ragged.first() {
            issues.push(format!(
                "数据件 {} 有一张表列数不齐：表头 {} 列 vs 数据 {} 列（修复指引：对齐竖线）",
                rel,
                header.len(),
                first.len()
            ));
        }
        n += 1;
    }
    (issues, Json::Object(vec![("tables".to_string(), Json::Int(n))]))
}

/// 真源 `_data_link`。
fn data_link(root: &Path, rel: &str, spec: &Json, obj: &Json) -> Vec<String> {
    let link = sg(spec, "link");
    let mut issues: Vec<String> = Vec::new();
    let path_field = sg_str(&link, "path_field");
    let target = match dig(obj, &path_field) {
        Some(Json::Str(s)) if !s.is_empty() => s,
        _ => {
            return vec![format!(
                "数据件 {} 的 link.path_field={} 取不到字符串路径（修复指引：核对字段名）",
                rel,
                pyval::py_str(Some(&sg(&link, "path_field")))
            )]
        }
    };
    let rel_dir = rel.rsplit_once('/').map(|(d, _)| d.to_string()).unwrap_or_default();
    let base = sg_str(&link, "base");
    let bases: Vec<String> = if !base.is_empty() {
        vec![base]
    } else {
        let parent = rel_dir.rsplit_once('/').map(|(d, _)| d.to_string()).unwrap_or_default();
        vec![rel_dir.clone(), parent]
    };
    let mut found: Option<std::path::PathBuf> = None;
    for b in &bases {
        let cand = root.join(b).join(&target);
        if cand.is_file() {
            found = Some(cand);
            break;
        }
    }
    let Some(fpath) = found else {
        return vec![format!(
            "数据件 {} 指向的 {} 不在场（修复指引：补件或修正 link.base）",
            rel, target
        )];
    };
    let rows_field = sg_str(&link, "rows_field");
    if !rows_field.is_empty() {
        let want = dig(obj, &rows_field).unwrap_or(Json::Null);
        let got = std::fs::read_to_string(&fpath)
            .map(|t| csv_rows(&t).len().saturating_sub(1))
            .unwrap_or(0);
        if !pyval::py_eq(&want, &Json::Int(got as i64)) {
            issues.push(format!(
                "数据件 {} 的 {}={} 与 {} 数据行 {} 不一致（修复指引：重算或改声明）",
                rel,
                rows_field,
                pyval::py_str(Some(&want)),
                target,
                got
            ));
        }
    }
    issues
}

/// 真源 `_check_data`。
pub fn check_data(root: &Path, spec: &Json) -> (Vec<String>, Json) {
    let sid = {
        let s = sg_str(spec, "id");
        if !s.is_empty() {
            s
        } else {
            let p = sg_str(spec, "path");
            if !p.is_empty() {
                p
            } else {
                let g = sg_str(spec, "glob");
                if !g.is_empty() {
                    g
                } else {
                    "?".to_string()
                }
            }
        }
    };
    let rels = resolve(root, spec);
    if rels.is_empty() {
        return (
            vec![format!(
                "数据契约 {} 未命中任何文件（修复指引：修正 path/glob —— 空气不是契约）",
                sid
            )],
            Json::Object(vec![("files".to_string(), Json::Int(0))]),
        );
    }
    let fmt = sg_str(spec, "format").to_lowercase();
    if !FORMATS.contains(&fmt.as_str()) {
        return (
            vec![format!(
                "数据契约 {} 的 format={} 不在词表 {}（修复指引：改用词表内格式）",
                sid,
                pyval::py_repr(&Json::Str(fmt)),
                FORMATS.join("/")
            )],
            Json::Object(vec![("files".to_string(), Json::Int(rels.len() as i64))]),
        );
    }
    let has_sha = pyval::py_truthy(&sg(spec, "sha256"));
    if has_sha && rels.len() != 1 {
        return (
            vec![format!(
                "数据契约 {} 声明了 sha256 却命中 {} 件（修复指引：sha256 只用于 path 单件）",
                sid,
                rels.len()
            )],
            Json::Object(vec![("files".to_string(), Json::Int(rels.len() as i64))]),
        );
    }
    let mut issues: Vec<String> = Vec::new();
    let mut stats: Vec<(String, Json)> = vec![
        ("files".to_string(), Json::Int(rels.len() as i64)),
        ("format".to_string(), Json::Str(fmt.clone())),
    ];
    for rel in &rels {
        let (text, err) = sread(root, rel);
        if let Some(e) = err {
            issues.push(e);
            continue;
        }
        let text = text.unwrap_or_default();
        let mut obj: Option<Json> = None;
        let (sub, s) = match fmt.as_str() {
            "json" => {
                let r = data_json(root, rel, &text, spec);
                obj = strict_json(&text).ok();
                r
            }
            "csv" => data_csv(rel, &text, spec),
            "markdown" => data_markdown(rel, &text, spec),
            _ => (
                Vec::new(),
                Json::Object(vec![(
                    "lines".to_string(),
                    Json::Int(pyval::splitlines_count(&text) as i64),
                )]),
            ),
        };
        issues.extend(sub);
        if let Json::Object(kv) = s {
            for (k, v) in kv {
                match stats.iter_mut().find(|(kk, _)| *kk == k) {
                    Some(e) => e.1 = v,
                    None => stats.push((k, v)),
                }
            }
        }
        if has_sha {
            let got = digest_of(&root.join(rel));
            let want = sg_str(spec, "sha256");
            if got != want {
                issues.push(format!(
                    "数据件 {} 摘要不符（记录 {} / 实测 {}）（修复指引：核对改动，确认后用 nf asset contract --freeze 重冻）",
                    rel,
                    head_chars(&want, 12),
                    head_chars(&got, 12)
                ));
            }
        }
        if pyval::py_truthy(&sg(spec, "link")) {
            if let Some(o) = &obj {
                issues.extend(data_link(root, rel, spec, o));
            }
        }
    }
    (issues, Json::Object(stats))
}

fn head_chars(s: &str, n: usize) -> String {
    s.chars().take(n).collect()
}

/// 真源 `_strict_json`：**严格如 RFC 8259**——`NaN` / `Infinity` 出现即报错。
pub fn strict_json(text: &str) -> Result<Json, String> {
    match serde_json::from_str::<serde_json::Value>(text) {
        Ok(v) => crate::jsonread::convert(&v),
        Err(e) => Err(e.to_string()),
    }
}

// ---------------------------------------------------------------- 代码面

/// 真源 `_check_tests`。
fn check_tests(root: &Path, rel: &str, spec: &Json) -> Vec<String> {
    let mut issues: Vec<String> = Vec::new();
    let stem = rel.rsplit_once('.').map(|(s, _)| s).unwrap_or(rel);
    let stem = stem.rsplit_once('/').map(|(_, s)| s).unwrap_or(stem);
    if !pyval::py_truthy(&sg(spec, "tests")) {
        issues.push(format!(
            "代码件 {} 未声明测试件（修复指引：补 tests 列表——没有用例的代码资产不算通过测试）",
            rel
        ));
    }
    for t in sg_strs(spec, "tests") {
        let trel = t.replace('\\', "/");
        let p = root.join(&trel);
        if !p.is_file() {
            issues.push(format!(
                "代码件 {} 声明的测试件不在场：{}（修复指引：先写测试再登记）",
                rel, trel
            ));
            continue;
        }
        let text = std::fs::read(&p)
            .map(|b| String::from_utf8_lossy(&b).into_owned())
            .unwrap_or_default();
        if crate::pyast::parse_module(&text).is_none() {
            // 真源在这里给 CPython 的 SyntaxError 文本 ⇒ **已知偏差**（见模块头）
            issues.push(format!("测试件 {} 语法坏：<TEXT>（修复指引：先修语法）", trel));
            continue;
        }
        if !text.contains(stem) {
            issues.push(format!(
                "测试件 {} 未点名被测模块 {}（修复指引：在测试里 import 或引用该模块）",
                trel, stem
            ));
        }
    }
    issues
}

/// 真源 `_check_code`。
pub fn check_code(root: &Path, spec: &Json) -> (Vec<String>, Json) {
    let rel = sg_str(spec, "path");
    let lang = {
        let l = sg_str(spec, "lang");
        if l.is_empty() {
            "python".to_string()
        } else {
            l
        }
    };
    if lang != "python" {
        return (
            vec![format!(
                "代码契约 {} 的 lang={} 不在支持面（仅 python 走 AST；Bash/VBA 走脚本面声明式契约）",
                pyval::py_str(obj_get(spec, "id")),
                pyval::py_str(obj_get(spec, "lang"))
            )],
            Json::Object(vec![]),
        );
    }
    let rels = resolve(root, spec);
    if rels.is_empty() {
        return (
            vec![format!(
                "代码契约 {} 未命中任何文件（修复指引：修正 path/glob）",
                pyval::py_str(obj_get(spec, "id"))
            )],
            Json::Object(vec![("files".to_string(), Json::Int(0))]),
        );
    }
    let mut issues: Vec<String> = Vec::new();
    let stats = Json::Object(vec![("files".to_string(), Json::Int(rels.len() as i64))]);
    let deny: std::collections::BTreeSet<String> =
        sg_strs(spec, "deny_calls").into_iter().collect();
    for one in &rels {
        let (text, err) = sread(root, one);
        if let Some(e) = err {
            issues.push(e);
            continue;
        }
        let text = text.unwrap_or_default();
        let Some(tree) = crate::pyast::parse_module(&text) else {
            issues.push(format!(
                "代码件 {} 语法坏：<TEXT>（修复指引：先修语法，AST 判据需要可解析的树）",
                one
            ));
            continue;
        };
        let ls = crate::pyast::LineStarts::new(&text);
        issues.extend(crate::asset_code::denied_calls(&tree, one, &deny, &ls));
        issues.extend(crate::asset_code::none_deref(&tree, one, &ls));
    }
    if !rel.is_empty() {
        issues.extend(check_tests(root, &rel, spec));
    }
    (issues, stats)
}

// ---------------------------------------------------------------- 脚本面

fn io_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"(?m)(?:#|')[ \t]*nf-io:[ \t]*(.+?)[ \t]*$").expect("固定合法")
    })
}

/// 真源 `parse_io_header` → `(inputs, outputs)`；无头 → `None`。
pub fn parse_io_header(text: &str) -> Option<(Vec<String>, Vec<String>)> {
    let m = io_re().captures(text)?;
    let mut ins: Vec<String> = Vec::new();
    let mut outs: Vec<String> = Vec::new();
    for token in m[1].split_whitespace() {
        let Some((key, val)) = token.split_once('=') else { continue };
        let key = key.trim().to_lowercase();
        let v = val.trim();
        let list: Vec<String> = if v == "-" || v.is_empty() {
            Vec::new()
        } else {
            v.split(',').map(|x| x.trim().to_string()).filter(|x| !x.is_empty()).collect()
        };
        match key.as_str() {
            "inputs" => ins = list,
            "outputs" => outs = list,
            _ => {}
        }
    }
    Some((ins, outs))
}

/// 真源 `observed_paths`：脚本里**字面量**形式的文件路径。
pub fn observed_paths(text: &str, lang: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    match lang {
        "python" => {
            let Some(tree) = crate::pyast::parse_module(text) else { return out };
            let ls = crate::pyast::LineStarts::new(text);
            for (_, _, _, name, args) in crate::asset_code::calls_with_args(&tree, &ls) {
                if name != "open" && name != "Path" && name != "pathlib.Path" {
                    continue;
                }
                for a in args {
                    if let Some(s) = a {
                        out.push(s);
                    }
                }
            }
        }
        "bash" => {
            let re = regex::Regex::new(r">>?[ \t]*([^\s;|&()]+)|<[ \t]*([^\s;|&()]+)").unwrap();
            for c in re.captures_iter(text) {
                out.push(
                    c.get(1).or_else(|| c.get(2)).map(|m| m.as_str().to_string()).unwrap_or_default(),
                );
            }
        }
        "vba" => {
            let re = regex::Regex::new(r#"(?i)\bOpen\s+"([^"]+)""#).unwrap();
            for c in re.captures_iter(text) {
                out.push(c[1].to_string());
            }
        }
        _ => {}
    }
    let skip = ["/dev/null", "/dev/stdin", "/dev/stdout", "-"];
    out.into_iter()
        .filter(|p| !p.is_empty() && !skip.contains(&p.as_str()) && !p.starts_with('$'))
        .collect()
}

/// 真源 `_check_script`。
pub fn check_script(root: &Path, spec: &Json) -> (Vec<String>, Json) {
    let sid = {
        let s = sg_str(spec, "id");
        if s.is_empty() {
            sg_str(spec, "path")
        } else {
            s
        }
    };
    let lang = sg_str(spec, "lang");
    if !LANGS.contains(&lang.as_str()) {
        return (
            vec![format!(
                "脚本契约 {} 的 lang={} 不在词表 {}（修复指引：改用词表内语言）",
                sid,
                pyval::py_repr(&Json::Str(lang)),
                LANGS.join("/")
            )],
            Json::Object(vec![]),
        );
    }
    let rel = sg_str(spec, "path");
    if !root.join(&rel).is_file() {
        return (
            vec![format!("脚本契约 {} 的件不在场：{}（修复指引：修正 path）", sid, rel)],
            Json::Object(vec![("files".to_string(), Json::Int(0))]),
        );
    }
    let (text, err) = sread(root, &rel);
    if let Some(e) = err {
        return (vec![e], Json::Object(vec![("files".to_string(), Json::Int(1))]));
    }
    let text = text.unwrap_or_default();
    let mut issues: Vec<String> = Vec::new();
    let header = parse_io_header(&text);
    let (emb_in, emb_out) = match header {
        Some((a, b)) => (a, b),
        None => {
            issues.push(format!(
                "脚本 {} 未自带 nf-io 头（修复指引：顶部加一行注释 # nf-io: inputs=a,b outputs=c；VBA 用单引号起头——脚本契约必须双源）",
                rel
            ));
            (Vec::new(), Vec::new())
        }
    };
    for (key, declared, embedded) in
        [("inputs", sg_strs(spec, "inputs"), emb_in), ("outputs", sg_strs(spec, "outputs"), emb_out)]
    {
        if declared != embedded {
            issues.push(format!(
                "脚本 {} 的 {} 双源不一致：声明={} / 头={}（修复指引：让两边逐字一致）",
                rel,
                key,
                pyval::py_repr_list(&declared.iter().map(|s| Json::Str(s.clone())).collect::<Vec<_>>()),
                pyval::py_repr_list(&embedded.iter().map(|s| Json::Str(s.clone())).collect::<Vec<_>>())
            ));
        }
    }
    let declared_all: std::collections::BTreeSet<String> =
        sg_strs(spec, "inputs").into_iter().chain(sg_strs(spec, "outputs")).collect();
    let mut extra: Vec<String> = observed_paths(&text, &lang)
        .into_iter()
        .filter(|x| !declared_all.contains(x))
        .collect();
    extra.sort();
    extra.dedup();
    if !extra.is_empty() {
        issues.push(format!(
            "脚本 {} 出现未声明的字面路径 {}（修复指引：补进 inputs/outputs 或去掉硬编码）",
            rel,
            extra.iter().take(3).cloned().collect::<Vec<_>>().join(",")
        ));
    }
    (
        issues,
        Json::Object(vec![
            ("files".to_string(), Json::Int(1)),
            ("inputs".to_string(), Json::Int(sg_strs(spec, "inputs").len() as i64)),
            ("outputs".to_string(), Json::Int(sg_strs(spec, "outputs").len() as i64)),
        ]),
    )
}

/// 真源 `_check_chain`。
pub fn check_chain(specs: &[(String, Json)], chain: &Json) -> (Vec<String>, Json) {
    let a_id = sg_str(chain, "from");
    let b_id = sg_str(chain, "to");
    let find = |id: &str| specs.iter().find(|(k, _)| k == id).map(|(_, v)| v);
    let (Some(a), Some(b)) = (find(&a_id), find(&b_id)) else {
        return (
            vec![format!(
                "链 {}→{} 的端点未在脚本面登记（修复指引：先登记两端脚本契约）",
                a_id, b_id
            )],
            Json::Object(vec![]),
        );
    };
    let norm = |v: Vec<String>| -> Vec<String> { v.into_iter().map(|x| x.replace('\\', "/")).collect() };
    let ao = norm(sg_strs(a, "outputs"));
    let bi = norm(sg_strs(b, "inputs"));
    let mut issues: Vec<String> = Vec::new();
    let feeds = obj_get(chain, "feeds").cloned().unwrap_or(Json::Null);
    match &feeds {
        Json::Array(fs) if !fs.is_empty() => {
            for f in fs {
                let out_p = sg_str(f, "output").replace('\\', "/");
                let in_p = sg_str(f, "input").replace('\\', "/");
                if !ao.contains(&out_p) {
                    issues.push(format!(
                        "链 {}→{}：上游未声明产物 {}（修复指引：补进上游 outputs）",
                        a_id, b_id, out_p
                    ));
                }
                if !bi.contains(&in_p) {
                    issues.push(format!(
                        "链 {}→{}：下游未声明该输入 {}（修复指引：补进下游 inputs）",
                        a_id, b_id, in_p
                    ));
                }
                if out_p != in_p {
                    issues.push(format!(
                        "链 {}→{}：产物路径不对齐（上游 {} vs 下游 {}）（修复指引：统一路径写法）",
                        a_id, b_id, out_p, in_p
                    ));
                }
            }
        }
        _ => {
            let inter: Vec<String> = ao.iter().filter(|x| bi.contains(x)).cloned().collect();
            if inter.is_empty() {
                issues.push(format!(
                    "链 {}→{}：上游产物与下游输入无交集（上游 {} / 下游 {}）（修复指引：契约未对齐——A 的输出必须匹配 B 的输入）",
                    a_id,
                    b_id,
                    pyval::py_repr_list(&ao.iter().take(3).map(|s| Json::Str(s.clone())).collect::<Vec<_>>()),
                    pyval::py_repr_list(&bi.iter().take(3).map(|s| Json::Str(s.clone())).collect::<Vec<_>>())
                ));
            }
        }
    }
    let matched = ao.iter().filter(|x| bi.contains(x)).count() as i64;
    (issues, Json::Object(vec![("matched".to_string(), Json::Int(matched))]))
}

// ---------------------------------------------------------------- 聚合 / 入口

/// 真源 `load`。
pub fn load(root: &Path) -> (Json, Vec<String>) {
    let p = root.join(DECL_REL);
    if !p.is_file() {
        return (
            Json::Object(vec![]),
            vec![format!(
                "缺数字资产契约声明 {}（修复指引：新建并写入 schema={} 与 data/code/script 三面）",
                DECL_REL, SCHEMA
            )],
        );
    }
    let text = match std::fs::read_to_string(&p) {
        Ok(s) => s,
        Err(e) => {
            return (
                Json::Object(vec![]),
                vec![format!("{} 不可读或不是合法 JSON：{}（修复指引：修好语法）", DECL_REL, e)],
            )
        }
    };
    let doc = match strict_json(&text) {
        Ok(v) => v,
        Err(e) => {
            return (
                Json::Object(vec![]),
                vec![format!("{} 不可读或不是合法 JSON：{}（修复指引：修好语法）", DECL_REL, e)],
            )
        }
    };
    if !matches!(doc, Json::Object(_)) || sg_str(&doc, "schema") != SCHEMA {
        return (
            Json::Object(vec![]),
            vec![format!(
                "{} schema 不匹配（期望 {}）（修复指引：改为声明件当前形态）",
                DECL_REL, SCHEMA
            )],
        );
    }
    (doc, Vec::new())
}

/// 真源 `scan(root, faces=())` → `(issues, warns, stats)`。
pub fn scan(root: &Path) -> (Vec<String>, Vec<String>, Json) {
    let (doc, mut issues) = load(root);
    let warns: Vec<String> = Vec::new();
    let mut counts: Vec<(String, i64)> =
        FACES.iter().map(|f| ((*f).to_string(), 0i64)).collect();
    let mut files = 0i64;
    let mut chains = 0i64;
    if !issues.is_empty() {
        let mut kv: Vec<(String, Json)> =
            counts.iter().map(|(k, v)| (k.clone(), Json::Int(*v))).collect();
        kv.push(("files".to_string(), Json::Int(0)));
        kv.push(("chains".to_string(), Json::Int(0)));
        return (issues, warns, Json::Object(kv));
    }
    for face in FACES {
        let specs = match obj_get(&doc, face) {
            Some(Json::Array(a)) => a.clone(),
            _ => Vec::new(),
        };
        for spec in specs {
            if !matches!(spec, Json::Object(_)) {
                issues.push(format!("契约 {} 面有非对象条目（修复指引：每条须是对象）", face));
                continue;
            }
            let (sub, s) = match face {
                "data" => check_data(root, &spec),
                "code" => check_code(root, &spec),
                _ => check_script(root, &spec),
            };
            issues.extend(sub);
            if let Some(e) = counts.iter_mut().find(|(k, _)| k == face) {
                e.1 += 1;
            }
            files += pyval::py_int_or(obj_get(&s, "files"), 0);
        }
    }
    let specs: Vec<(String, Json)> = match obj_get(&doc, "script") {
        Some(Json::Array(a)) => a
            .iter()
            .map(|s| (sg_str(s, "id"), s.clone()))
            .collect(),
        _ => Vec::new(),
    };
    if let Some(Json::Array(cs)) = obj_get(&doc, "chains") {
        for c in cs {
            let empty = Json::Object(vec![]);
            let chain = if matches!(c, Json::Object(_)) { c } else { &empty };
            let (sub, _) = check_chain(&specs, chain);
            issues.extend(sub);
            chains += 1;
        }
    }
    let mut kv: Vec<(String, Json)> =
        counts.iter().map(|(k, v)| (k.clone(), Json::Int(*v))).collect();
    kv.push(("files".to_string(), Json::Int(files)));
    kv.push(("chains".to_string(), Json::Int(chains)));
    (issues, warns, Json::Object(kv))
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 合成夹具的内容（与 `tools/gen_asset_data_cases.py` 里 Python 侧那份**逐字同源**）。
    const AC_FIX_FILES: [(&str, &str); 18] = [
        (r#"bad.json"#, r#"{"a": "x"}
"#),
        (r#"badschema.json"#, r#"{"type": }
"#),
        (r#"blankhdr.csv"#, r#"a,,c
1,2,3
"#),
        (r#"empty.csv"#, r#""#),
        (r#"link.csv"#, r#"h
1
2
3
"#),
        (r#"link.json"#, r#"{"p": "link.csv", "n": 3}
"#),
        (r#"linkbad.json"#, r#"{"p": "link.csv", "n": 9}
"#),
        (r#"linkmiss.json"#, r#"{"p": "nope.csv", "n": 1}
"#),
        (r#"nofm.md"#, r#"| a |
| --- |
| 1 |
"#),
        (r#"nonan.json"#, r#"{"a": NaN}
"#),
        (r#"ok.csv"#, r#"a,b
1,2
3,4
"#),
        (r#"ok.json"#, r#"{"a": 1, "n": 3}
"#),
        (r#"ok.md"#, r#"---
x: 1
---

| a | b |
| --- | --- |
| 1 | 2 |
"#),
        (r#"plain.txt"#, r#"l1
l2
"#),
        (r#"quoted.csv"#, r#"a,b
"x,1",2
"#),
        (r#"ragged.csv"#, r#"a,b
1,2,3
4,5
"#),
        (r#"ragged.md"#, r#"---

| a | b |
| --- | --- |
| 1 |
"#),
        (r#"sch.json"#, r#"{"type": "object", "required": ["a"]}
"#),
    ];

    fn write_asset_data_fixture(root: &std::path::Path) {
        for (rel, body) in AC_FIX_FILES {
            let p = root.join(rel);
            std::fs::create_dir_all(p.parent().unwrap()).unwrap();
            std::fs::write(p, body).unwrap();
        }
    }
    // >>> GENERATED by tools/gen_asset_data_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 数据面用例级判据（期望值由 `tools/gen_asset_data_cases.py` 从真源生成）=====
    ///
    /// ① **真实声明的四条**在**真仓库根**上跑：JSON(schema+required+link) / CSV(required_columns+
    /// min_rows) / markdown / sha256 的通过路径。
    /// ② **合成夹具**覆盖错误分支：缺件 / format 非法 / sha256 多件 / 必填缺 / CSV 空·空列名·
    /// 列数不齐·缺列·行数不足·带引号字段 / markdown 缺 frontmatter·表列数不齐 / link 三类。
    ///
    /// `strict_json` 与 `_read` 的**报错文本**两处已知偏差（serde_json / std::io vs CPython），
    /// 故断言前对这两类消息做**归一**——不假装文本相同。
    fn ac_repo_root() -> std::path::PathBuf {
        std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
    }

    /// 归一：解析/读件失败的文本两侧不可比，只留稳定前缀。
    fn ac_norm(issues: &[String]) -> Vec<String> {
        issues
            .iter()
            .map(|x| {
                for pat in ["不是合法 JSON：", "schema 本身不是合法 JSON：", "读不到 ",
                            " 不是 UTF-8："] {
                    if let Some(i) = x.find(pat) {
                        return format!("{}<TEXT>", &x[..i + pat.len()]);
                    }
                }
                x.clone()
            })
            .collect()
    }

    #[test]
    fn asset_data_real_declarations_match_truth_source() {
        let root = ac_repo_root();
        let cases: &[(&str, &[&str], &str)] = &[
        (
            r#"{"format": "json", "id": "pack-report-d05", "link": {"base": "community/AI保险域包", "path_field": "sample", "rows_field": "sample_rows"}, "path": "community/AI保险域包/outputs/REPORT.json", "required_fields": ["kind", "code", "domain", "family", "sample", "sample_rows", "metrics"], "schema": "community/AI保险域包/outputs/schemas/DOMAIN_REPORT.schema.json"}"#,
            &[],
            r#"{"fields": 7, "files": 1, "format": "json"}"#
        ),
        (
            r#"{"format": "csv", "id": "pack-cases-d05", "min_rows": 1, "path": "community/AI保险域包/outputs/samples/CASES.csv", "required_columns": ["case_id", "gold_fields", "pred_fields"]}"#,
            &[],
            r#"{"columns": 3, "files": 1, "format": "csv", "rows": 12}"#
        ),
        (
            r#"{"format": "markdown", "id": "library-index", "path": "library/INDEX.md"}"#,
            &[],
            r#"{"files": 1, "format": "markdown", "tables": 2}"#
        ),
        (
            r#"{"format": "json", "id": "ladder-truth", "path": "protocol/LAYERS.json", "required_fields": ["schema", "rules", "tiers"], "sha256": "bec48abcec388184847b424c14b4a1bbea0a7138e76a319963b7f86a6079c37c"}"#,
            &[],
            r#"{"fields": 3, "files": 1, "format": "json"}"#
        ),
        ];
        for (spec_s, want_issues, want_stats) in cases {
            let spec: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(spec_s).unwrap(),
            )
            .unwrap();
            let (issues, stats) = check_data(&root, &spec);
            assert_eq!(ac_norm(&issues), ac_norm(&want_issues.iter().map(|s| s.to_string()).collect::<Vec<_>>()),
                       "真实声明 issues 不一致");
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_stats).unwrap(),
            )
            .unwrap();
            assert!(crate::jsonread::json_eq(&stats, &want),
                    "真实声明 stats 不一致\n  实得 {}\n  期望 {}", stats.dumps(), want.dumps());
        }
    }

    #[test]
    fn asset_data_synthetic_branches_match_truth_source() {
        let root = crate::testutil::fixture("asset-data-cases-src");
        write_asset_data_fixture(&root);
        let cases: &[(&str, &str, &[&str], &str)] = &[
        (
            r#"ok-json-schema"#,
            r#"{"format": "json", "id": "s1", "path": "ok.json", "schema": "sch.json"}"#,
            &[],
            r#"{"fields": 0, "files": 1, "format": "json"}"#
        ),
        (
            r#"bad-json-schema"#,
            r#"{"format": "json", "id": "s2", "path": "bad.json", "schema": "sch.json"}"#,
            &[],
            r#"{"fields": 0, "files": 1, "format": "json"}"#
        ),
        (
            r#"non-rfc8259"#,
            r#"{"format": "json", "id": "s3", "path": "nonan.json"}"#,
            &[r#"数据件 nonan.json 不是合法 JSON：非 RFC 8259 常量 NaN（修复指引：改用 null 或有限数字）（修复指引：修好语法或换 format）"#],
            r#"{"files": 1, "format": "json"}"#
        ),
        (
            r#"bad-schema-json"#,
            r#"{"format": "json", "id": "s4", "path": "ok.json", "schema": "badschema.json"}"#,
            &[r#"数据件 ok.json 不符 schema badschema.json：schema 本身不是合法 JSON：Expecting value: line 1 column 10 (char 9)"#],
            r#"{"fields": 0, "files": 1, "format": "json"}"#
        ),
        (
            r#"schema-missing"#,
            r#"{"format": "json", "id": "s5", "path": "ok.json", "schema": "nope.json"}"#,
            &[r#"数据件 ok.json 的 schema 读不到：读不到 nope.json：[Errno 2] No such file or directory: 'C:\\Users\\mon_7\\Downloads\\NarrativeForge-main\\engine\\rust\\target\\test-fixtures\\asset-data-cases\\nope.json'（修复指引：核对声明里的路径在场）"#],
            r#"{"fields": 0, "files": 1, "format": "json"}"#
        ),
        (
            r#"required-missing"#,
            r#"{"format": "json", "id": "s6", "path": "bad.json", "required_fields": ["zz"]}"#,
            &[r#"数据件 bad.json 缺必填字段 zz（修复指引：补字段或从声明里删掉——声明即契约）"#],
            r#"{"fields": 1, "files": 1, "format": "json"}"#
        ),
        (
            r#"format-invalid"#,
            r#"{"format": "xml", "id": "s7", "path": "ok.json"}"#,
            &[r#"数据契约 s7 的 format='xml' 不在词表 json/csv/markdown/text（修复指引：改用词表内格式）"#],
            r#"{"files": 1}"#
        ),
        (
            r#"path-missing"#,
            r#"{"format": "json", "id": "s8", "path": "nope.json"}"#,
            &[r#"数据契约 s8 未命中任何文件（修复指引：修正 path/glob —— 空气不是契约）"#],
            r#"{"files": 0}"#
        ),
        (
            r#"glob-empty"#,
            r#"{"format": "json", "glob": "*.nope", "id": "s9"}"#,
            &[r#"数据契约 s9 未命中任何文件（修复指引：修正 path/glob —— 空气不是契约）"#],
            r#"{"files": 0}"#
        ),
        (
            r#"sha-multi"#,
            r#"{"format": "csv", "glob": "*.csv", "id": "s10", "sha256": "00"}"#,
            &[r#"数据契约 s10 声明了 sha256 却命中 6 件（修复指引：sha256 只用于 path 单件）"#],
            r#"{"files": 6}"#
        ),
        (
            r#"sha-mismatch"#,
            r#"{"format": "csv", "id": "s11", "path": "ok.csv", "sha256": "00"}"#,
            &[r#"数据件 ok.csv 摘要不符（记录 00 / 实测 b94851485464）（修复指引：核对改动，确认后用 nf asset contract --freeze 重冻）"#],
            r#"{"columns": 2, "files": 1, "format": "csv", "rows": 2}"#
        ),
        (
            r#"csv-ok"#,
            r#"{"format": "csv", "id": "s12", "path": "ok.csv", "required_columns": ["a"]}"#,
            &[],
            r#"{"columns": 2, "files": 1, "format": "csv", "rows": 2}"#
        ),
        (
            r#"csv-empty"#,
            r#"{"format": "csv", "id": "s13", "path": "empty.csv"}"#,
            &[r#"数据件 empty.csv 是空 CSV（修复指引：至少要有表头行）"#],
            r#"{"files": 1, "format": "csv", "rows": 0}"#
        ),
        (
            r#"csv-blank-header"#,
            r#"{"format": "csv", "id": "s14", "path": "blankhdr.csv"}"#,
            &[r#"数据件 blankhdr.csv 表头有空列名（修复指引：每列都要有名字）"#],
            r#"{"columns": 3, "files": 1, "format": "csv", "rows": 1}"#
        ),
        (
            r#"csv-ragged"#,
            r#"{"format": "csv", "id": "s15", "path": "ragged.csv"}"#,
            &[r#"数据件 ragged.csv 第 2 行列数 != 表头 2（修复指引：补齐/删除多余的分隔符）"#],
            r#"{"columns": 2, "files": 1, "format": "csv", "rows": 2}"#
        ),
        (
            r#"csv-missing-col"#,
            r#"{"format": "csv", "id": "s16", "path": "ok.csv", "required_columns": ["zz"]}"#,
            &[r#"数据件 ok.csv 缺必需列 zz（修复指引：加列或改声明）"#],
            r#"{"columns": 2, "files": 1, "format": "csv", "rows": 2}"#
        ),
        (
            r#"csv-min-rows"#,
            r#"{"format": "csv", "id": "s17", "min_rows": 99, "path": "ok.csv"}"#,
            &[r#"数据件 ok.csv 数据行 2 < min_rows 99（修复指引：补样例或下调声明）"#],
            r#"{"columns": 2, "files": 1, "format": "csv", "rows": 2}"#
        ),
        (
            r#"csv-quoted"#,
            r#"{"format": "csv", "id": "s18", "path": "quoted.csv", "required_columns": ["a", "b"]}"#,
            &[],
            r#"{"columns": 2, "files": 1, "format": "csv", "rows": 1}"#
        ),
        (
            r#"md-ok"#,
            r#"{"format": "markdown", "frontmatter": true, "id": "s19", "path": "ok.md"}"#,
            &[],
            r#"{"files": 1, "format": "markdown", "tables": 1}"#
        ),
        (
            r#"md-ragged"#,
            r#"{"format": "markdown", "frontmatter": true, "id": "s20", "path": "ragged.md"}"#,
            &[r#"数据件 ragged.md 有一张表列数不齐：表头 2 列 vs 数据 1 列（修复指引：对齐竖线）"#],
            r#"{"files": 1, "format": "markdown", "tables": 1}"#
        ),
        (
            r#"md-no-frontmatter"#,
            r#"{"format": "markdown", "frontmatter": true, "id": "s21", "path": "nofm.md"}"#,
            &[r#"数据件 nofm.md 缺 frontmatter（修复指引：件首补 --- 块）"#],
            r#"{"files": 1, "format": "markdown", "tables": 1}"#
        ),
        (
            r#"text-lines"#,
            r#"{"format": "text", "id": "s22", "path": "plain.txt"}"#,
            &[],
            r#"{"files": 1, "format": "text", "lines": 2}"#
        ),
        (
            r#"link-ok"#,
            r#"{"format": "json", "id": "s23", "link": {"path_field": "p", "rows_field": "n"}, "path": "link.json"}"#,
            &[],
            r#"{"fields": 0, "files": 1, "format": "json"}"#
        ),
        (
            r#"link-mismatch"#,
            r#"{"format": "json", "id": "s24", "link": {"path_field": "p", "rows_field": "n"}, "path": "linkbad.json"}"#,
            &[r#"数据件 linkbad.json 的 n=9 与 link.csv 数据行 3 不一致（修复指引：重算或改声明）"#],
            r#"{"fields": 0, "files": 1, "format": "json"}"#
        ),
        (
            r#"link-missing"#,
            r#"{"format": "json", "id": "s25", "link": {"path_field": "p"}, "path": "linkmiss.json"}"#,
            &[r#"数据件 linkmiss.json 指向的 nope.csv 不在场（修复指引：补件或修正 link.base）"#],
            r#"{"fields": 0, "files": 1, "format": "json"}"#
        ),
        (
            r#"link-no-path-field"#,
            r#"{"format": "json", "id": "s26", "link": {"path_field": "nope"}, "path": "link.json"}"#,
            &[r#"数据件 link.json 的 link.path_field=nope 取不到字符串路径（修复指引：核对字段名）"#],
            r#"{"fields": 0, "files": 1, "format": "json"}"#
        ),
        ];
        for (name, spec_s, want_issues, want_stats) in cases {
            let spec: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(spec_s).unwrap(),
            )
            .unwrap();
            let (issues, stats) = check_data(&root, &spec);
            assert_eq!(ac_norm(&issues),
                       ac_norm(&want_issues.iter().map(|s| s.to_string()).collect::<Vec<_>>()),
                       "合成用例 {} 的 issues 不一致", name);
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_stats).unwrap(),
            )
            .unwrap();
            assert!(crate::jsonread::json_eq(&stats, &want),
                    "合成用例 {} 的 stats 不一致\n  实得 {}\n  期望 {}", name,
                    stats.dumps(), want.dumps());
        }
    }
    // <<< GENERATED
    // >>> GENERATED by tools/gen_asset_code_cases.py（勿手改；重跑生成器覆盖本段）
    /// ===== 代码面 / 脚本面 / 链 / 聚合（真实声明，期望值由生成器从真源取）=====
    ///
    /// 语法坏那一支的**文本不可比**（真源给 CPython `SyntaxError`，本线给本线解析器的），
    /// 故那类消息在两侧都归一到 `<TEXT>`（同 `code_metrics` 的处理）。
    #[test]
    fn asset_code_real_declarations_match_truth_source() {
        let root = ac_repo_root();
        let cases: &[(&str, &[&str], &str)] = &[
        (
            r#"{"deny_calls": ["eval", "exec", "__import__", "os.system", "pickle.loads", "marshal.loads"], "id": "asset-contract", "lang": "python", "path": "desktop/src/core/asset_contract.py", "tests": ["desktop/tests/test_asset_contract.py"]}"#,
            &[],
            r#"{"files": 1}"#
        ),
        (
            r#"{"deny_calls": ["eval", "exec", "__import__", "os.system"], "id": "json-schema-leaf", "lang": "python", "path": "desktop/src/core/json_schema.py", "tests": ["desktop/tests/test_output_forms.py"]}"#,
            &[],
            r#"{"files": 1}"#
        ),
        (
            r#"{"deny_calls": ["eval", "exec", "__import__", "os.system"], "id": "content-face-leaf", "lang": "python", "path": "desktop/src/core/content_face.py", "tests": ["desktop/tests/test_content_face.py"]}"#,
            &[],
            r#"{"files": 1}"#
        ),
        ];
        for (spec_s, want_issues, want_stats) in cases {
            let spec: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(spec_s).unwrap(),
            )
            .unwrap();
            let (issues, stats) = check_code(&root, &spec);
            assert_eq!(ac_norm(&issues),
                       ac_norm(&want_issues.iter().map(|s| s.to_string()).collect::<Vec<_>>()),
                       "代码面 issues 不一致");
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_stats).unwrap(),
            )
            .unwrap();
            assert!(crate::jsonread::json_eq(&stats, &want), "代码面 stats 不一致");
        }
    }

    #[test]
    fn asset_script_real_declarations_match_truth_source() {
        let root = ac_repo_root();
        let cases: &[(&str, &[&str], &str)] = &[
        (
            r#"{"id": "cards", "inputs": ["verify.sh"], "lang": "python", "outputs": ["docs/verification-cards.md"], "path": "scripts/build_verification_cards.py"}"#,
            &[],
            r#"{"files": 1, "inputs": 1, "outputs": 1}"#
        ),
        (
            r#"{"id": "geo-export", "inputs": ["protocol/standards_catalog.json", "protocol/standards_binding.json"], "lang": "python", "outputs": ["docs/standards/index.md", "docs/standards/answer-cards.md", "protocol/geo_export.json", "docs/standards/layer-data.md", "docs/standards/layer-eng.md", "docs/standards/layer-form.md", "docs/standards/layer-gov.md", "docs/standards/layer-iface.md"], "path": "scripts/geo_export.py"}"#,
            &[],
            r#"{"files": 1, "inputs": 2, "outputs": 8}"#
        ),
        (
            r#"{"id": "external-links", "inputs": ["README.md", "README.en.md", "llms.txt", "AGENT_START.md", "ROUTES.md", "docs/verification-cards.md"], "lang": "python", "outputs": ["results/external-links-report.json"], "path": "scripts/check_external_links.py"}"#,
            &[],
            r#"{"files": 1, "inputs": 6, "outputs": 1}"#
        ),
        (
            r#"{"id": "quality-all", "inputs": ["verify.sh"], "lang": "bash", "outputs": [], "path": "scripts/quality_all.sh"}"#,
            &[],
            r#"{"files": 1, "inputs": 1, "outputs": 0}"#
        ),
        ];
        for (spec_s, want_issues, want_stats) in cases {
            let spec: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(spec_s).unwrap(),
            )
            .unwrap();
            let (issues, stats) = check_script(&root, &spec);
            assert_eq!(issues, want_issues.to_vec(), "脚本面 issues 不一致");
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_stats).unwrap(),
            )
            .unwrap();
            assert!(crate::jsonread::json_eq(&stats, &want), "脚本面 stats 不一致");
        }
    }

    #[test]
    fn asset_chains_match_truth_source() {
        let root = ac_repo_root();
        let specs: Vec<(String, Json)> = {
            let (doc, _) = load(&root);
            match obj_get(&doc, "script") {
                Some(Json::Array(a)) => a.iter().map(|s| (sg_str(s, "id"), s.clone())).collect(),
                _ => Vec::new(),
            }
        };
        let cases: &[(&str, &[&str], &str)] = &[
        (
            r#"{"feeds": [{"input": "docs/verification-cards.md", "output": "docs/verification-cards.md"}], "from": "cards", "to": "external-links"}"#,
            &[],
            r#"{"matched": 1}"#
        ),
        ];
        for (chain_s, want_issues, want_stats) in cases {
            let chain: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(chain_s).unwrap(),
            )
            .unwrap();
            let (issues, stats) = check_chain(&specs, &chain);
            assert_eq!(issues, want_issues.to_vec(), "链 issues 不一致");
            let want: Json = crate::jsonread::convert(
                &serde_json::from_str::<serde_json::Value>(want_stats).unwrap(),
            )
            .unwrap();
            assert!(crate::jsonread::json_eq(&stats, &want), "链 stats 不一致");
        }
    }

    #[test]
    fn asset_contract_scan_matches_truth_source() {
        let root = ac_repo_root();
        let (issues, warns, stats) = scan(&root);
        assert_eq!(ac_norm(&issues), &[] as &[&str], "聚合 issues 不一致");
        assert_eq!(warns, &[] as &[&str], "聚合 warns 不一致");
        let want: Json = crate::jsonread::convert(
            &serde_json::from_str::<serde_json::Value>(r#"{"chains": 1, "code": 3, "data": 4, "files": 11, "script": 4}"#).unwrap(),
        )
        .unwrap();
        assert!(crate::jsonread::json_eq(&stats, &want),
                "聚合 stats 不一致\n  实得 {}\n  期望 {}", stats.dumps(), want.dumps());
    }
    // <<< GENERATED
}
