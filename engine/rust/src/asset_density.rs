//! 资产密度扫描（`asset_density`）—— 与真源 `desktop/src/core/asset_density.py` 的 `scan` 对账。
//!
//! 只移植 `scan`（资产台账面体检：文件数 / 键数 / 无键件 / 微型件 / 均值）。
//! 真源的 `usage_scan` / `thickness_scan` / `count_keys` 走的是 Aho–Corasick 自动机与语料普查，
//! **不在本次范围**（它们是独立的另两个面）。
//!
//! 本扫描器是 `nf score` 的 `asset_density` 信号源与 `metrics` 的唯一出处。

use std::collections::BTreeSet;
use std::path::Path;
use crate::pyjson::Json;

/// 真源 `ASSET_INPUTS`：两条**资产面**（都很窄，故改文档/代码不作废其缓存）。
pub const ASSET_INPUTS: [&str; 2] = ["community/*/assets/*.md", "05_资产库/用户自定义/*.md"];
/// 真源 `regression_score.DENSITY_TARGET`（键/档的归一分母）。
pub const DENSITY_TARGET: f64 = 3.0;

#[derive(Default, Clone, Debug, PartialEq)]
pub struct DensityStats {
    pub files: usize,
    pub keys: usize,
    pub unkeyed: usize,
    pub tiny: usize,
    /// 真源 `round(n_keys / max(1, n_files), 2)`
    pub avg_keys_per_file: f64,
}

/// 真源 `_keys_of`：文件名令牌 ∪ 正文头 6000 字的三种键声明。
///
/// 四路取键缺一不可——真源注释记着一次实测教训：原字符集 `[A-Z0-9_]` 看不见**带连字符**的
/// 条目键（如域包的 `C01-01`），导致密度被系统性低估。
pub fn keys_of(stem: &str, text: &str) -> Vec<String> {
    let mut keys: BTreeSet<String> = BTreeSet::new();
    for m in re_stem().find_iter(stem) {
        keys.insert(m.as_str().to_string());
    }
    // 真源 `head = text[:6000]`（**按码点**切，不是字节）
    let head: String = text.chars().take(6000).collect();
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
    RE.get_or_init(|| {
        regex::Regex::new(r"`([A-Z][A-Z0-9_-]{2,})`").expect("反引号键正则固定合法")
    })
}

fn re_jsonkey() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r#""([A-Z][A-Z0-9_-]{2,})"\s*:"#).expect("JSON 键正则固定合法")
    })
}

fn re_heading() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"##\s*([A-Z][A-Z0-9_-]{2,})").expect("标题键正则固定合法")
    })
}

/// 真源 `_scan_impl` → `(issues, stats)`。
pub fn scan(root: &Path) -> (Vec<String>, DensityStats) {
    let mut issues: Vec<String> = Vec::new();
    let mut rows: Vec<(usize, usize)> = Vec::new(); // (keys, chars)

    for pat in ASSET_INPUTS {
        for rel in crate::glob::expand(root, pat) {
            if rel.rsplit('/').next().unwrap_or("") == "README.md" {
                continue;
            }
            let Ok(text) = std::fs::read_to_string(root.join(&rel)) else {
                issues.push(format!("{} 不可读：<读取失败>", rel));
                continue;
            };
            if text.trim().is_empty() {
                issues.push(format!("{} 为空档（0 字符）", rel));
                continue;
            }
            let stem = std::path::Path::new(&rel)
                .file_stem()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_default();
            let keys = keys_of(&stem, &text);
            rows.push((keys.len(), text.chars().count()));
        }
    }

    let n_files = rows.len();
    let n_keys: usize = rows.iter().map(|(k, _)| *k).sum();
    let n_unkeyed = rows.iter().filter(|(k, _)| *k == 0).count();
    let n_tiny = rows.iter().filter(|(_, c)| *c < 200).count();
    let avg = crate::pyfloat::round_to(n_keys as f64 / n_files.max(1) as f64, 2);
    (
        issues,
        DensityStats {
            files: n_files,
            keys: n_keys,
            unkeyed: n_unkeyed,
            tiny: n_tiny,
            avg_keys_per_file: avg,
        },
    )
}


/// 真源 `CORPUS_PATTERNS`：引用度普查的**语料面**。
pub const CORPUS_PATTERNS: [&str; 3] = ["04_模块库/**/*.md", "community/**/*.md", "docs/**/*.md"];

/// `DensityStats` → 真源 `scan()` 的 stats 字典。
impl DensityStats {
    pub fn to_json(&self) -> Json {
        Json::Object(vec![
            ("files".to_string(), Json::Int(self.files as i64)),
            ("keys".to_string(), Json::Int(self.keys as i64)),
            ("unkeyed".to_string(), Json::Int(self.unkeyed as i64)),
            ("tiny".to_string(), Json::Int(self.tiny as i64)),
            ("avg_keys_per_file".to_string(), Json::Float(self.avg_keys_per_file)),
        ])
    }
}

/// 真源 `_thickness_impl`：资产**语义厚度**（计数升半语义）。
///
/// `low = 空/过短(<200 字) 或 无键且无小节`；只报告不删（issues 恒空）。
pub fn thickness_scan(root: &Path) -> (Vec<String>, Json) {
    let section_re = regex::Regex::new(r"^#{1,3}\s").expect("固定合法");
    let mut rows: Vec<(String, String, usize, usize, usize, usize, bool)> = Vec::new();
    for pat in ASSET_INPUTS {
        for rel in crate::glob::expand(root, pat) {
            if rel.rsplit('/').next().unwrap_or("") == "README.md" {
                continue;
            }
            let Ok(text) = std::fs::read_to_string(root.join(&rel)) else {
                continue;
            };
            if text.trim().is_empty() {
                continue;
            }
            let stem = std::path::Path::new(&rel)
                .file_stem()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_default();
            let keys = keys_of(&stem, &text);
            let lines: Vec<&str> = text.split('\n').collect();
            let sections = lines.iter().filter(|l| section_re.is_match(l)).count();
            let tables = lines.iter().filter(|l| l.trim_start().starts_with('|')).count();
            let chars = text.chars().count();
            let low = chars < 200 || (keys.is_empty() && sections == 0);
            let pkg = if rel.starts_with("community") {
                rel.split('/').nth(1).unwrap_or("").to_string()
            } else {
                "官方".to_string()
            };
            rows.push((pkg, rel, chars, keys.len(), sections, tables, low));
        }
    }
    let mut low_files: Vec<String> =
        rows.iter().filter(|r| r.6).map(|r| r.1.clone()).collect();
    low_files.sort();
    let n = rows.len();
    let avg_chars =
        crate::pyfloat::round_to(rows.iter().map(|r| r.2).sum::<usize>() as f64 / n.max(1) as f64, 0);
    let avg_sections =
        crate::pyfloat::round_to(rows.iter().map(|r| r.4).sum::<usize>() as f64 / n.max(1) as f64, 0);
    (
        Vec::new(),
        Json::Object(vec![
            ("files".to_string(), Json::Int(n as i64)),
            ("low_info".to_string(), Json::Int(low_files.len() as i64)),
            (
                "low_files".to_string(),
                Json::Array(low_files.into_iter().map(Json::Str).collect()),
            ),
            ("avg_chars".to_string(), Json::Int(avg_chars as i64)),
            ("avg_sections".to_string(), Json::Int(avg_sections as i64)),
        ]),
    )
}

/// 真源 `usage_scan`：资产键在**语料面**被引用次数（纯统计，issues 恒空）。
///
/// 计数口径 = 逐件**逐键非重叠**计数再相加（真源 `count_keys_additive`；其 docstring 给出与
/// 「拼成一整条再数」的等价性证明：连接用 `"\n"`，而键不含换行 ⇒ 跨件匹配不可能）。
/// 真源另有 Aho–Corasick 自动机与逐件内容键缓存——都是**加速**，不改数字 ✅ 本线不移植。
pub fn usage_scan(root: &Path) -> (Vec<String>, Json) {
    let mut keys: Vec<String> = Vec::new();
    for pat in ASSET_INPUTS {
        for rel in crate::glob::expand(root, pat) {
            if rel.rsplit('/').next().unwrap_or("") == "README.md" {
                continue;
            }
            let Ok(text) = std::fs::read_to_string(root.join(&rel)) else {
                continue;
            };
            let stem = std::path::Path::new(&rel)
                .file_stem()
                .map(|s| s.to_string_lossy().to_string())
                .unwrap_or_default();
            for k in keys_of(&stem, &text) {
                if !keys.contains(&k) {
                    keys.push(k);
                }
            }
        }
    }
    let mut counts: Vec<(String, i64)> = keys.iter().map(|k| (k.clone(), 0i64)).collect();
    for pat in CORPUS_PATTERNS {
        for rel in crate::glob::expand(root, pat) {
            let Ok(text) = std::fs::read_to_string(root.join(&rel)) else {
                continue;
            };
            for slot in counts.iter_mut() {
                if text.contains(&slot.0) {
                    slot.1 += text.matches(&slot.0).count() as i64;
                }
            }
        }
    }
    let mut zero: Vec<String> = counts.iter().filter(|(_, n)| *n == 0).map(|(k, _)| k.clone()).collect();
    zero.sort();
    let total: i64 = counts.iter().map(|(_, n)| *n).sum();
    (
        Vec::new(),
        Json::Object(vec![
            ("assets".to_string(), Json::Int(keys.len() as i64)),
            ("zero_usage".to_string(), Json::Int(zero.len() as i64)),
            ("used".to_string(), Json::Int(keys.len() as i64 - zero.len() as i64)),
            ("total_refs".to_string(), Json::Int(total)),
            (
                "zero_keys".to_string(),
                Json::Array(zero.into_iter().map(Json::Str).collect()),
            ),
        ]),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn keys_come_from_four_sources_including_hyphenated() {
        // 正文键：反引号 / JSON 键 / 标题 —— 三路都要；**裸词不入册**（真源只认这三路）
        let text = "`C01-01` 与 \"A08-07\": 1\n## B12-3 标题\nBARE_WORD\n";
        let got = keys_of("M08_季节天气", text);
        assert!(got.contains(&"C01-01".to_string()), "反引号键：{:?}", got);
        assert!(got.contains(&"A08-07".to_string()), "JSON 键：{:?}", got);
        assert!(got.contains(&"B12-3".to_string()), "标题键：{:?}", got);
        assert!(!got.contains(&"BARE_WORD".to_string()), "裸词不得入册：{:?}", got);
        // 文件名令牌：`[A-Z][A-Z0-9_]*` 在 "M08_季节天气" 上只吃到 "M08_"（CJK 停住）
        assert!(got.contains(&"M08_".to_string()), "文件名令牌：{:?}", got);
    }

    #[test]
    fn keys_are_sorted_and_deduped() {
        let got = keys_of("x", "`AAA` `AAA` `BBB`");
        assert_eq!(got, vec!["AAA".to_string(), "BBB".to_string()]);
    }

    #[test]
    fn head_window_is_6000_code_points() {
        // 第 6001 个码点之后的反引号键不得被采纳
        let mut text = "a".repeat(6001);
        text.push_str("`ZZZKEY`");
        let got = keys_of("X", &text);
        assert!(!got.contains(&"ZZZKEY".to_string()), "超出 6000 码点的键不得入册：{:?}", got);
    }

    #[test]
    fn empty_asset_file_is_reported_and_skipped() {
        let tmp = crate::testutil::fixture("density-empty");
        std::fs::create_dir_all(tmp.join("community/p/assets")).unwrap();
        std::fs::write(tmp.join("community/p/assets/A.md"), b"   \n").unwrap();
        std::fs::write(tmp.join("community/p/assets/B.md"), "`KEYX`\n").unwrap();
        std::fs::write(tmp.join("community/p/assets/README.md"), "`SKIPME`\n").unwrap();
        let (issues, stats) = scan(&tmp);
        assert_eq!(issues.len(), 1);
        assert!(issues[0].contains("为空档"));
        assert_eq!(stats.files, 1, "README.md 应跳过、空档应跳过");
        assert!(stats.keys >= 1);
        let _ = std::fs::remove_dir_all(&tmp);
    }
}
