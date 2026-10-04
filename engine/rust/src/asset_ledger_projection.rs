//! 资产键表机读 ledger 投影（`asset_ledger_projection`）—— 与真源
//! `desktop/src/core/asset_ledger_projection.py` 对账。
//!
//! 把「键发现」从人读键表投影成机读 ledger：键源 = 资产文件名令牌 ∪ 正文头 8000 字的三路键声明
//! （`` `KEY` `` / `"KEY":` / `## KEY`），每键记 `{package, file, first_line}`；
//! `protocol/community_asset_ledger.json` 是常驻投影，`verify` 判**双源一致**。
//!
//! ⚠️ `_file_keys` 与 [`crate::asset_density::keys_of`] **不是同一套口径**（各自真源如此）：
//! 本件的字符集不含连字符（`[A-Z0-9_]`）、头部窗口是 8000 而非 6000、`##` 走 `re.M`。
//! 抄成另一套会静默改变键集。
//!
//! 本模块是 `nf verify-report` 的 `assets_ledger` 判据，**不单独开 CLI 面**。

use crate::jsonread;
use crate::pyjson::Json;
use crate::jsonread::json_eq;
use std::collections::BTreeSet;
use std::path::Path;

pub const LEDGER_REL: &str = "protocol/community_asset_ledger.json";
const FACES: [&str; 2] = ["community/*/assets/*.md", "05_资产库/用户自定义/*.md"];

/// 真源 `_file_keys`（**本件专属口径**，勿与 asset_density 混用）。
pub fn file_keys(stem: &str, text: &str) -> Vec<String> {
    let mut keys: BTreeSet<String> = BTreeSet::new();
    for m in re_stem().find_iter(stem) {
        keys.insert(m.as_str().to_string());
    }
    let head: String = text.chars().take(8000).collect();
    for m in re_backtick().captures_iter(&head) {
        keys.insert(m[1].to_string());
    }
    for m in re_jsonkey().captures_iter(&head) {
        keys.insert(m[1].to_string());
    }
    for m in re_heading().captures_iter(&head) {
        keys.insert(m[1].to_string());
    }
    keys.into_iter().collect()
}

fn re_stem() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"[A-Z][A-Z0-9_]*").expect("文件名键正则固定合法"))
}

fn re_backtick() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"`([A-Z][A-Z0-9_]{2,})`").expect("反引号键正则固定合法"))
}

fn re_jsonkey() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r#""([A-Z][A-Z0-9_]{2,})"\s*:"#).expect("JSON 键正则固定合法")
    })
}

fn re_heading() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"(?m)^##\s*([A-Z][A-Z0-9_]{2,})").expect("标题键正则固定合法")
    })
}

/// 真源 `build` → 已排序的 ledger 行。
pub fn build(root: &Path) -> Vec<Json> {
    let mut rows: Vec<(String, String, String, i64)> = Vec::new();
    for pat in FACES {
        for rel in crate::glob::expand(root, pat) {
            if rel.rsplit('/').next().unwrap_or("") == "README.md" {
                continue;
            }
            let Ok(text) = std::fs::read_to_string(root.join(&rel)) else { continue };
            let stem = Path::new(&rel)
                .file_stem()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_default();
            let pkg = if rel.starts_with("community") {
                rel.split('/').nth(1).unwrap_or("").to_string()
            } else {
                "官方".to_string()
            };
            let lines: Vec<&str> = text.lines().collect();
            for k in file_keys(&stem, &text) {
                // 真源：`re.search(r"\b" + re.escape(k) + r"\b", ln)` 取**首个**命中行，找不到记 1
                let mut line = 1i64;
                for (idx, ln) in lines.iter().enumerate() {
                    if word_match(ln, &k) {
                        line = idx as i64 + 1;
                        break;
                    }
                }
                rows.push((pkg.clone(), k, rel.clone(), line));
            }
        }
    }
    rows.sort_by(|a, b| (&a.0, &a.1, &a.2).cmp(&(&b.0, &b.1, &b.2)));
    rows.into_iter()
        .map(|(package, key, file, line)| {
            Json::Object(vec![
                ("key".to_string(), Json::Str(key)),
                ("package".to_string(), Json::Str(package)),
                ("file".to_string(), Json::Str(file)),
                ("line".to_string(), Json::Int(line)),
            ])
        })
        .collect()
}

/// `\bKEY\b`（键字符集为 `[A-Z0-9_]`，无需转义）。
fn word_match(line: &str, key: &str) -> bool {
    let b = line.as_bytes();
    let kb = key.as_bytes();
    let mut i = 0usize;
    while i + kb.len() <= b.len() {
        if &b[i..i + kb.len()] == kb {
            let left_ok = i == 0 || !is_word_byte(b[i - 1]);
            let right = i + kb.len();
            let right_ok = right == b.len() || !is_word_byte(b[right]);
            if left_ok && right_ok {
                return true;
            }
        }
        i += 1;
    }
    false
}

fn is_word_byte(c: u8) -> bool {
    c.is_ascii_alphanumeric() || c == b'_'
}

/// 真源 `_verify_impl` → `(issues, {"entries": n})`；`None` 对应真源的空字典。
pub fn verify(root: &Path) -> (Vec<String>, Option<Json>) {
    let path = root.join(LEDGER_REL);
    if !path.exists() {
        return (vec![format!("{} 缺失（refresh 生成）", LEDGER_REL)], None);
    }
    let Some(data) = jsonread::read_file(root, LEDGER_REL) else {
        return (vec![format!("{} 不是合法 JSON", LEDGER_REL)], None);
    };
    let current = build(root);
    let recorded = crate::pyval::get(&data, "entries").cloned().unwrap_or(Json::Null);
    let mut issues = Vec::new();
    if !json_eq(&recorded, &Json::Array(current.clone())) {
        issues.push(format!("{} 过期：与资产扫描不一致（refresh）", LEDGER_REL));
    }
    (
        issues,
        Some(Json::Object(vec![(
            "entries".to_string(),
            Json::Int(current.len() as i64),
        )])),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn file_keys_uses_this_modules_character_set() {
        // 本件字符集 **不含连字符**（与 asset_density 的 `C01-01` 口径不同）
        let got = file_keys("M08_季节天气", "`C01-01` `AAA` \"BBB\": 1\n## CCC\n");
        assert!(got.contains(&"AAA".to_string()), "{:?}", got);
        assert!(got.contains(&"BBB".to_string()), "{:?}", got);
        assert!(got.contains(&"CCC".to_string()), "{:?}", got);
        assert!(!got.contains(&"C01-01".to_string()), "连字符不在本件字符集：{:?}", got);
    }

    #[test]
    fn word_match_respects_boundaries() {
        assert!(word_match("a KEY b", "KEY"));
        assert!(!word_match("aKEYb", "KEY"));
        assert!(word_match("KEY", "KEY"));
    }

    #[test]
    fn head_window_is_8000_code_points() {
        let mut text = "a".repeat(8001);
        text.push_str("`ZZZKEY`");
        assert!(!file_keys("X", &text).contains(&"ZZZKEY".to_string()));
    }

    #[test]
    fn ledger_entries_compare_order_insensitively_per_object() {
        let a: Json = jsonread::convert(&serde_json::json!([{"key": "A", "line": 1}])).unwrap();
        let b: Json = jsonread::convert(&serde_json::json!([{"line": 1, "key": "A"}])).unwrap();
        assert!(json_eq(&a, &b), "对象内键序不该影响相等");
        let c: Json = jsonread::convert(&serde_json::json!([{"key": "B", "line": 1}])).unwrap();
        assert!(!json_eq(&a, &c));
    }
}
