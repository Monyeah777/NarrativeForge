//! 文档卫生（`doc_hygiene`）的**只读子集** —— 与真源 `desktop/src/core/doc_hygiene.py` 对账。
//!
//! 覆盖三件（皆纯表驱动，不涉 YAML/AST）：
//! - `kind_coverage`：关键文档与指令档每件都须有四型归属（**连 root 都不用**）；
//! - `kind_rules`：四型**写法**判据 → WARN 清单；
//! - `check_markers`：指令标识 + 「最后更新」位覆盖校验。
//!
//! 这三件同时是三条链的输入：conformance 契约 `doc-kinds`、`score` 的 `doc_hygiene` 信号、
//! `verify_report` 的同名项——所以先落它，一次投入三处可用。
//!
//! **常量表来自 [`crate::doc_tables`]**（真源转录，勿手改）。
//! 真源里 `check_markers` 有一层按正文取键的缓存；对账只看**结论**，故本线不移植缓存。

use crate::doc_tables::{DOC_KINDS, INSTRUCTION_DOCS, KIND_RULES, KINDS, REQUIRED_DOCS};
use std::collections::BTreeSet;
use std::path::Path;

// 这两个常量与 `check_markers` 的真源消费者是 `score` 的 `doc_hygiene` 信号与
// `verify_report` 的同名项——本线那两面尚未落地，故此处暂未接线（刻意保留，
// 免得下次做 `score` 时重新翻真源）。
#[allow(dead_code)]
pub const INSTRUCTION_MARK: &str = "⛔ 操作指令";
#[allow(dead_code)]
pub const LAST_UPDATED_PREFIX: &str = "> 最后更新：";

/// 真源 `kind_coverage(root)`：四型覆盖校验（**真源忽略 root**，本函数同样无参）。
pub fn kind_coverage() -> Vec<String> {
    let mut all: BTreeSet<&str> = BTreeSet::new();
    for r in REQUIRED_DOCS {
        all.insert(r);
    }
    for r in INSTRUCTION_DOCS {
        all.insert(r);
    }
    let mut issues = Vec::new();
    for rel in all {
        match DOC_KINDS.iter().find(|(k, _)| *k == rel).map(|(_, v)| *v) {
            None => issues.push(format!(
                "{} 缺四型归属（DOC_KINDS；取值 {}）",
                rel,
                KINDS.join("/")
            )),
            Some(kind) => {
                if !KINDS.contains(&kind) {
                    issues.push(format!(
                        "{} 四型取值非法：{}（取值 {}）",
                        rel,
                        kind,
                        KINDS.join("/")
                    ));
                }
            }
        }
    }
    issues
}

/// 真源 `kind_rules(root)`：四型写法判据 → `（写法未定型）` 清单。
///
/// 真源用 `re.search(p, text, re.M)`，故此处给模式加 `(?m)` 前缀。
pub fn kind_rules(root: &Path) -> Vec<String> {
    let mut pairs: Vec<(&str, &str)> = DOC_KINDS.to_vec();
    pairs.sort_by(|a, b| a.0.cmp(b.0)); // 真源 `sorted(DOC_KINDS.items())` 按 key
    let mut warns = Vec::new();
    for (rel, kind) in pairs {
        let Some(rule) = KIND_RULES.iter().find(|(k, _, _)| *k == kind) else {
            continue;
        };
        let path = root.join(rel);
        if !path.exists() {
            continue;
        }
        let text = std::fs::read_to_string(&path).unwrap_or_default();
        let hit = rule
            .1
            .iter()
            .any(|p| match regex::Regex::new(&format!("(?m){}", p)) {
                Ok(re) => re.is_match(&text),
                Err(_) => false,
            });
        if !hit {
            warns.push(format!("{} 属 {} 型但缺「{}」（写法未定型）", rel, kind, rule.2));
        }
    }
    warns
}

/// 真源 `check_markers(root)`：指令标识 + 「最后更新」位覆盖校验。
///
/// **尚未接线**：真源里它供 `score` 的 `doc_hygiene` 信号与 `verify_report` 使用，
/// 本线那两面未落地。已有单元判据守着（含"第 9 行的最后更新位不算数"）。
#[allow(dead_code)]
pub fn check_markers(root: &Path) -> Vec<String> {
    let mut texts: Vec<(&str, Option<String>)> = Vec::new();
    for rel in REQUIRED_DOCS.iter().chain(INSTRUCTION_DOCS.iter()) {
        texts.push((rel, std::fs::read_to_string(root.join(rel)).ok()));
    }
    let lookup = |rel: &str| -> Option<String> {
        texts
            .iter()
            .find(|(r, _)| *r == rel)
            .and_then(|(_, t)| t.clone())
    };

    let mut issues = Vec::new();
    for rel in REQUIRED_DOCS {
        match lookup(rel) {
            None => issues.push(format!("{} 缺失（须入 REQUIRED_DOCS 清单）", rel)),
            Some(text) => {
                let head: Vec<&str> = text.lines().take(8).collect();
                if !head.iter().any(|ln| ln.starts_with(LAST_UPDATED_PREFIX)) {
                    issues.push(format!("{} 缺「最后更新」位（头部 {} 行内）", rel, head.len()));
                }
            }
        }
    }
    for rel in INSTRUCTION_DOCS {
        let Some(text) = lookup(rel) else { continue };
        let head: Vec<&str> = text.lines().take(8).collect();
        if !head.iter().any(|ln| ln.contains(INSTRUCTION_MARK)) {
            issues.push(format!("{} 缺「⛔ 操作指令」标识头（指令类文档须全覆盖）", rel));
        }
    }
    issues
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn kind_coverage_flags_docs_missing_from_table() {
        // 真源表里每件都应有归属；当前语料下应为空
        let issues = kind_coverage();
        assert!(issues.is_empty(), "真源表应自洽，实得：{:?}", issues);
    }

    #[test]
    fn kind_rules_only_counts_rule_kinds() {
        // 四型都配有 must_any；缺件跳过（不凭空报）
        assert_eq!(KIND_RULES.len(), 4);
        let warns = kind_rules(Path::new("."));
        // 只断言形状：每条 warn 都带「写法未定型」
        for w in &warns {
            assert!(w.ends_with("（写法未定型）"), "got: {}", w);
        }
    }

    #[test]
    fn head_window_is_eight_lines_like_truth_source() {
        // 「最后更新」落在第 9 行即不算数（真源 `_head_lines(text, 8)`）
        let tmp = crate::testutil::fixture("doc-head");
        let mut body = String::new();
        for _ in 0..8 {
            body.push_str("填充\n");
        }
        body.push_str("> 最后更新：2026-01-01\n");
        std::fs::write(tmp.join("01_核心协议.md"), &body).unwrap();
        let issues = check_markers(&tmp);
        assert!(
            issues.iter().any(|i| i.contains("01_核心协议.md") && i.contains("最后更新")),
            "第 9 行的最后更新位不得被采纳；实得 {:?}",
            issues
        );
        let _ = std::fs::remove_dir_all(&tmp);
    }
}
