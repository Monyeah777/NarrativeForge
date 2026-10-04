//! 资产键命名规范机检（`key_naming`）—— 与真源 `desktop/src/core/key_naming.py` 对账。
//!
//! 键（文件头 `nf-asset key="…"` + `provenance.json` 的 `assets[].key`）是**跨包寻址面**：
//! ① **形态**：须匹配声明件 `protocol/asset_keys.json` 的 `pattern`；② **在册**：须在声明件的
//! `keys` 词表里（未登记即 FAIL）；③ **回看**：词表登记但盘上从未出现 → WARN（词表腐化可见，
//! 不判死）。声明件缺失/不可解析 → fail-closed。
//!
//! ⚠️ 真源用 `rx.match(key)`——**只锚起始、不锚结尾**。Rust 的 `is_match` 是任意位置匹配，
//! 直接用会把 `XABC` 判成匹配 `ABC`。故本线显式包成 `^(?:pattern)`。
//!
//! 本模块是 `nf verify-report` 的 `key_naming` 判据，**不单独开 CLI 面**。

use crate::jsonread;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, py_repr, py_str};
use std::collections::BTreeSet;
use std::path::Path;

pub const DECL_REL: &str = "protocol/asset_keys.json";
const HEADER_GLOBS: [&str; 2] = ["05_资产库/**/*.md", "community/*/assets/*.md"];
const PROVENANCE_GLOBS: [&str; 2] =
    ["05_资产库/**/provenance.json", "community/*/assets/provenance.json"];

pub struct KeyScan {
    pub status: Option<&'static str>,
    pub issues: Vec<String>,
    pub warns: Vec<String>,
    pub stats: Json,
}

/// 真源 `declaration` → `(doc, issues)`。
fn declaration(root: &Path) -> (Option<Json>, Vec<String>) {
    let p = root.join(DECL_REL);
    if !p.is_file() {
        return (
            None,
            vec![format!(
                "缺键词表声明 {}（修复指引：新建该声明件并写明 pattern 与 keys）",
                DECL_REL
            )],
        );
    }
    let Some(doc) = jsonread::read_file(root, DECL_REL) else {
        return (
            None,
            vec![format!("{} 不是合法 JSON（修复指引：修好 JSON 语法）", DECL_REL)],
        );
    };
    let mut issues = Vec::new();
    if py_str(get(&doc, "pattern")).trim().is_empty() {
        issues.push(format!("{} 缺 pattern（修复指引：写明键的形态正则）", DECL_REL));
    }
    let keys_ok = matches!(get(&doc, "keys"), Some(Json::Object(p)) if !p.is_empty());
    if !keys_ok {
        issues.push(format!("{} 缺 keys 词表（修复指引：把在册键逐条写进 keys）", DECL_REL));
    }
    (Some(doc), issues)
}

/// 真源 `collect` → `{key: [仓库相对路径,…]}`。
fn collect(root: &Path) -> Vec<(String, Vec<String>)> {
    let mut found: Vec<(String, Vec<String>)> = Vec::new();
    let add = |k: String, rel: String, found: &mut Vec<(String, Vec<String>)>| {
        match found.iter_mut().find(|(n, _)| *n == k) {
            Some((_, v)) => v.push(rel),
            None => found.push((k, vec![rel])),
        }
    };
    static HRE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let hre = HRE.get_or_init(|| {
        regex::Regex::new(r#"nf-asset:\s*key="([^"]*)""#).expect("键头正则固定合法")
    });
    for pat in HEADER_GLOBS {
        for rel in crate::glob::expand(root, pat) {
            let Ok(text) = std::fs::read_to_string(root.join(&rel)) else { continue };
            // 真源 `[:600]` 按**字符**切
            let head: String = text.chars().take(600).collect();
            if let Some(c) = hre.captures(&head) {
                add(c[1].to_string(), rel, &mut found);
            }
        }
    }
    for pat in PROVENANCE_GLOBS {
        for rel in crate::glob::expand(root, pat) {
            let Some(doc) = jsonread::read_file(root, &rel) else { continue };
            for a in arr_items(get(&doc, "assets")) {
                let k = py_str(get(a, "key"));
                if !k.is_empty() {
                    add(k, rel.clone(), &mut found);
                }
            }
        }
    }
    found
}

/// 真源 `scan` → `(issues, warns, stats)`。
pub fn scan(root: &Path) -> KeyScan {
    let (doc, issues) = declaration(root);
    let mut warns: Vec<String> = Vec::new();
    let found = collect(root);
    let keys_seen = found.len();
    let occurrences: usize = found.iter().map(|(_, v)| v.len()).sum();
    let base_stats = |registered: usize, max_len: usize| {
        Json::Object(vec![
            ("keys_seen".to_string(), Json::Int(keys_seen as i64)),
            ("occurrences".to_string(), Json::Int(occurrences as i64)),
            ("registered".to_string(), Json::Int(registered as i64)),
            ("max_key_len".to_string(), Json::Int(max_len as i64)),
        ])
    };
    let Some(doc) = doc else {
        return KeyScan {
            status: None,
            issues,
            warns,
            stats: base_stats(0, 0),
        };
    };
    if !issues.is_empty() {
        return KeyScan {
            status: None,
            issues,
            warns,
            stats: base_stats(0, 0),
        };
    }

    let pattern = py_str(get(&doc, "pattern"));
    // 真源 `re.compile(...)` 失败会抛 → `_call` 记 error；本线同样如实记 error
    let Ok(rx) = regex::Regex::new(&format!("^(?:{})", pattern)) else {
        return KeyScan {
            status: Some("error"),
            issues: vec![format!("key_naming.scan 抛 error：pattern 不是合法正则：{}", pattern)],
            warns,
            stats: base_stats(0, 0),
        };
    };
    let registered: BTreeSet<String> = match get(&doc, "keys") {
        Some(Json::Object(p)) => p.iter().map(|(k, _)| k.clone()).collect(),
        _ => BTreeSet::new(),
    };
    let mut sorted: Vec<(String, Vec<String>)> = found.clone();
    sorted.sort_by(|a, b| a.0.cmp(&b.0));
    let mut issues = issues;
    for (key, files) in &sorted {
        if !rx.is_match(key) {
            let samples: Vec<String> = registered.iter().take(3).cloned().collect();
            issues.push(format!(
                "资产键形态不合规范：{}（{}）（修复指引：匹配 {}；示例：{}）",
                py_repr(&Json::Str(key.clone())),
                files.first().cloned().unwrap_or_default(),
                pattern,
                samples.join("、")
            ));
        } else if !registered.contains(key) {
            let samples: Vec<String> = registered.iter().take(5).cloned().collect();
            issues.push(format!(
                "资产键未登记进词表：{}（{}）（修复指引：把该键与用途写进 {} 的 keys，或改用既有键之一：{}）",
                py_repr(&Json::Str(key.clone())),
                files.first().cloned().unwrap_or_default(),
                DECL_REL,
                samples.join("、")
            ));
        }
    }
    let found_keys: BTreeSet<String> = found.iter().map(|(k, _)| k.clone()).collect();
    let unused: Vec<String> = registered.difference(&found_keys).cloned().collect();
    if !unused.is_empty() {
        warns.push(format!(
            "词表登记但盘上未见：{}（修复指引：确认键仍在使用，或从 {} 移除）",
            unused.join("、"),
            DECL_REL
        ));
    }
    let max_len = found.iter().map(|(k, _)| k.chars().count()).max().unwrap_or(0);
    KeyScan {
        status: None,
        issues,
        warns,
        stats: base_stats(registered.len(), max_len),
    }
}
