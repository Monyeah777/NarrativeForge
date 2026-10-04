//! 复盘门禁（`postmortem`）—— 与真源 `desktop/src/core/postmortem.py` 对账。
//!
//! 判据：声明四段齐 / blame_tokens 与 root_cause_tokens 非空；复盘件 frontmatter 必填齐、
//! `trigger` 与 `refs` 可解析、四段齐、**禁指责**（blame 命中即 FAIL）、**根因指向机制**、
//! **行动项须同时含「负责人」与「判据」**、`status: closed` 须已被协议回执锚定。

use crate::jsonread;
use crate::mdblocks;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, obj_is_empty, plain_str, plain_str_opt, py_str, py_truthy};
use std::collections::BTreeSet;
use std::path::Path;

pub const DECL_REL: &str = "protocol/postmortem.json";
pub const RECEIPTS_REL: &str = "protocol/RECEIPTS.json";
pub const GLOB: &str = "postmortems/PO-*.md";
const SCHEMA: &str = "nf-postmortem/1";
const SECTIONS: [&str; 4] = ["## 现象", "## 影响", "## 根因", "## 行动项"];
const DEFAULT_FIELDS: [&str; 5] = ["id", "date", "trigger", "status", "refs"];

pub struct PostmortemScan {
    pub issues: Vec<String>,
    pub postmortems: usize,
    pub actions: usize,
}

struct Entry {
    path: String,
    file: String,
    fm: Json,
    body: String,
}

fn decl(root: &Path) -> Option<Json> {
    if !root.join(DECL_REL).is_file() {
        return None;
    }
    jsonread::read_file(root, DECL_REL).filter(|d| !obj_is_empty(d))
}

fn entries(root: &Path) -> Vec<Entry> {
    crate::glob::expand(root, GLOB)
        .into_iter()
        .map(|rel| {
            let text = std::fs::read_to_string(root.join(&rel)).unwrap_or_default();
            let (fm, body) = mdblocks::parse_frontmatter(&text);
            let file = rel.rsplit('/').next().unwrap_or(&rel).to_string();
            Entry { path: rel, file, fm, body }
        })
        .collect()
}

fn check_ids(root: &Path) -> BTreeSet<String> {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| {
        regex::Regex::new(r"(?m)^check(\d+)\(\)\{").expect("check 定义正则固定合法")
    });
    std::fs::read_to_string(root.join("verify.sh"))
        .map(|t| re.captures_iter(&t).map(|c| c[1].to_string()).collect())
        .unwrap_or_default()
}

fn is_dated(s: &str) -> bool {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| regex::Regex::new(r"^\d{4}-\d{2}-\d{2}$").expect("日期正则固定合法"));
    re.is_match(s)
}

/// 真源 `_refs_ok`。
fn refs_ok(root: &Path, refs: Option<&Json>, checks: &BTreeSet<String>) -> Vec<String> {
    let mut issues = Vec::new();
    let list: Vec<String> = match refs {
        Some(Json::Str(s)) => vec![s.clone()],
        Some(Json::Array(a)) => a.iter().map(plain_str).collect(),
        _ => Vec::new(),
    };
    for r in list {
        let s = r.trim().to_string();
        if let Some(n) = is_check(&s) {
            if !checks.contains(&n) {
                issues.push(format!("引用指向不存在的 check：{}", s));
            }
            continue;
        }
        if !root.join(s.replace('\\', "/")).exists() {
            issues.push(format!("引用无法解析：{}", s));
        }
    }
    issues
}

fn is_check(s: &str) -> Option<String> {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| regex::Regex::new(r"^check(\d+)$").expect("判据引用正则固定合法"));
    re.captures(s).map(|c| c[1].to_string())
}

fn check_doc(
    root: &Path,
    e: &Entry,
    d: &Json,
    checks: &BTreeSet<String>,
    receipts: &Option<BTreeSet<String>>,
) -> (Vec<String>, usize) {
    let mut issues = Vec::new();
    let fm = &e.fm;
    let body = &e.body;

    let fields = arr_items(get(d, "required_fields"));
    let names: Vec<String> = if fields.is_empty() {
        DEFAULT_FIELDS.iter().map(|s| (*s).to_string()).collect()
    } else {
        fields.iter().map(|v| plain_str(v)).collect()
    };
    for k in names {
        if !py_truthy(get(fm, &k).unwrap_or(&Json::Null)) {
            issues.push(format!("缺必填字段：{}", k));
        }
    }
    let vocab: Vec<String> = {
        let v = crate::pyval::str_list(get(d, "status_vocabulary"));
        if v.is_empty() {
            vec!["open".to_string(), "closed".to_string()]
        } else {
            v
        }
    };
    if !vocab.contains(&plain_str_opt(get(fm, "status"))) {
        issues.push(format!("status 越词表：{}", plain_str_opt(get(fm, "status"))));
    }
    if !is_dated(&py_str(get(fm, "date"))) {
        issues.push(format!("date 非 YYYY-MM-DD：{}", plain_str_opt(get(fm, "date"))));
    }
    for sec in SECTIONS {
        if !body.contains(sec) {
            issues.push(format!("正文缺段落：{}", sec));
        }
    }
    for tok in arr_items(get(d, "blame_tokens")) {
        let t = plain_str(tok);
        if !t.is_empty() && body.contains(&t) {
            issues.push(format!("命中指责性归因词「{}」——复盘对事不对人", t));
        }
    }
    let root_sec = if body.contains("## 根因") {
        body.splitn(2, "## 根因")
            .nth(1)
            .unwrap_or("")
            .splitn(2, "## 行动项")
            .next()
            .unwrap_or("")
            .to_string()
    } else {
        String::new()
    };
    let toks: Vec<String> = arr_items(get(d, "root_cause_tokens")).iter().map(|v| plain_str(v)).collect();
    if !root_sec.is_empty() && !toks.is_empty() && !toks.iter().any(|t| root_sec.contains(t)) {
        let head: Vec<String> = toks.iter().take(4).cloned().collect();
        issues.push(format!("根因段未指向机制（须出现 {} 之一）", head.join("/")));
    }
    let acts = if body.contains("## 行动项") {
        mdblocks::bullet_blocks(body.splitn(2, "## 行动项").nth(1).unwrap_or(""))
    } else {
        Vec::new()
    };
    if acts.is_empty() {
        issues.push("行动项为空——没有行动项的复盘不闭环".to_string());
    }
    for a in &acts {
        if !a.contains("负责人") {
            issues.push(format!("行动项缺负责人：{}", &a[..a.len().min(40)]));
        }
        if !a.contains("判据") {
            issues.push(format!("行动项缺判据：{}", &a[..a.len().min(40)]));
        }
    }
    issues.extend(refs_ok(root, get(fm, "trigger"), checks));
    issues.extend(refs_ok(root, get(fm, "refs"), checks));
    if plain_str_opt(get(fm, "status")) == "closed" {
        if let Some(ids) = receipts {
            if !ids.contains(&e.path) {
                issues.push(
                    "status=closed 但未被协议回执锚定（防事后美化；修复指引：nf receipts --write）"
                        .to_string(),
                );
            }
        }
    }
    (issues, acts.len())
}

/// 真源 `scan`。
pub fn scan(root: &Path) -> PostmortemScan {
    let mut issues: Vec<String> = Vec::new();
    let Some(d) = decl(root) else {
        return PostmortemScan {
            issues: vec![format!("缺复盘协议声明 {}", DECL_REL)],
            postmortems: 0,
            actions: 0,
        };
    };
    if py_str(get(&d, "schema")) != SCHEMA {
        issues.push(format!("复盘协议 schema 不匹配（期望 {}）", SCHEMA));
    }
    let secs = crate::pyval::str_list(get(&d, "sections"));
    if secs != ["现象", "影响", "根因", "行动项"] {
        issues.push("sections 必须是四段（现象/影响/根因/行动项）".to_string());
    }
    for k in ["blame_tokens", "root_cause_tokens"] {
        if arr_items(get(&d, k)).is_empty() {
            issues.push(format!("{} 不得为空（无指责与根因判据必须成文）", k));
        }
    }
    let checks = check_ids(root);
    let receipts: Option<BTreeSet<String>> = if root.join(RECEIPTS_REL).is_file() {
        jsonread::read_file(root, RECEIPTS_REL).map(|doc| {
            arr_items(get(&doc, "entries"))
                .iter()
                .map(|e| plain_str_opt(get(e, "id")))
                .collect()
        })
    } else {
        None
    };
    let rows = entries(root);
    let mut actions = 0usize;
    for e in &rows {
        let (i, n) = check_doc(root, e, &d, &checks, &receipts);
        let tag = {
            let id = py_str(get(&e.fm, "id"));
            if id.is_empty() {
                e.file.clone()
            } else {
                id
            }
        };
        issues.extend(i.into_iter().map(|x| format!("{}：{}", tag, x)));
        actions += n;
    }
    PostmortemScan {
        issues,
        postmortems: rows.len(),
        actions,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::pyjson::Json as J;

    #[test]
    fn blame_token_is_a_failure() {
        let tmp = crate::testutil::fixture("pm-blame");
        std::fs::create_dir_all(tmp.join("protocol")).unwrap();
        std::fs::create_dir_all(tmp.join("postmortems")).unwrap();
        std::fs::write(
            tmp.join(DECL_REL),
            r#"{"schema": "nf-postmortem/1", "sections": ["现象","影响","根因","行动项"], "blame_tokens": ["某人"], "root_cause_tokens": ["机制"]}"#
                .as_bytes(),
        )
        .unwrap();
        std::fs::write(
            tmp.join("postmortems/PO-0001-a.md"),
            "---\nid: PO-0001\ndate: 2026-01-01\ntrigger: protocol/LAYERS.json\nstatus: open\nrefs: []\n---\n## 现象\n某人手滑\n## 影响\nx\n## 根因\n机制缺陷\n## 行动项\n- 负责人：甲；判据：绿\n"
                .as_bytes(),
        )
        .unwrap();
        let got = scan(&tmp);
        assert!(
            got.issues.iter().any(|i| i.contains("指责性归因词")),
            "blame token 命中必须判红：{:?}",
            got.issues
        );
        assert_eq!(got.actions, 1);
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn refs_ok_distinguishes_check_from_path() {
        let checks: BTreeSet<String> = ["13".to_string()].into_iter().collect();
        let refs = J::Array(vec![J::Str("check13".into()), J::Str("check99".into())]);
        let got = refs_ok(Path::new("."), Some(&refs), &checks);
        assert_eq!(got.len(), 1);
        assert!(got[0].contains("check99"));
    }    // >>> GENERATED by tools/gen_postmortem_branches.py（勿手改；重跑生成器覆盖本段）

    /// ===== 分支级差分判据（期望值由 `tools/gen_postmortem_branches.py` 从真源生成）=====
    ///
    /// 四场景：kitchen / 声明齐 / 缺声明 / 无复盘件（门禁空转 warn）。
    /// 分支：引用指向不存在 check / 引用无法解析 / 缺必填 / status 越词表 / 日期非法 / 正文缺段落 /
    /// **命中指责性归因词** / 根因段未指向机制 / 行动项为空 / 行动项缺负责人 / 行动项缺判据 /
    /// `status=closed` 但未被回执锚定 / 声明 schema / sections 非四段 / 词表不得为空 / 全绿。
    /// 注：真源 `scan` 的 warns 在本面无消费者，故本线未纳入移植面。
    const PM_GREEN: &str = r#"---
id: PO-1
title: t
status: open
date: 2026-01-01
refs: check1
---
## 现象
p
## 影响
i
## 根因
根因是流程机制
## 行动项
- 改流程（负责人：张三）判据：跑通 verify.sh
"#;
    const PM_KITCHEN: &str = r#"---
id: PO-2
status: 越词表
date: 2026/01/01
refs:
  - check99
  - no/such/file
---
## 现象
p
## 根因
因为疏忽操作不当
## 行动项
- 没有负责人也没有判据的行动项
"#;
    const PM_CLOSED: &str = r#"---
id: PO-3
title: t
status: closed
date: 2026-01-02
refs: check1
---
## 现象
p
## 影响
i
## 根因
机制机制
## 行动项
- 做某事（负责人：李四）判据：跑通
"#;
    const PM_DECL_OK: &str = r#"{"schema": "nf-postmortem/1", "sections": ["现象", "影响", "根因", "行动项"], "blame_tokens": ["疏忽"], "root_cause_tokens": ["机制"]}"#;

    fn build_pm_fixture(scenario: &str, decl: Option<&str>,
                        docs: &[(&str, &str)]) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("postmortem-branches-{}", scenario));
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        if let Some(d) = decl {
            std::fs::write(root.join("protocol/postmortem.json"), d).unwrap();
        }
        if !docs.is_empty() {
            std::fs::create_dir_all(root.join("postmortems")).unwrap();
            for (name, body) in docs {
                std::fs::write(root.join("postmortems").join(name), body).unwrap();
            }
        }
        std::fs::write(root.join("verify.sh"), "#!/bin/bash\ncheck1(){\n  true\n}\n").unwrap();
        std::fs::write(
            root.join("protocol/RECEIPTS.json"),
            r#"{"schema": "nf-receipts/1", "entries": [{"id": "postmortems/PO-3-closed.md"}]}"#,
        )
        .unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_in_all_four_scenarios() {
        for (scenario, decl, docs, want) in [
            (
                "kitchen",
                Some(r#"{"schema": "wrong/1", "sections": ["现象"], "blame_tokens": [], "root_cause_tokens": []}"#),
                &[("PO-2-kitchen.md", PM_KITCHEN), ("PO-3-closed.md", PM_CLOSED)][..],
                &["复盘协议 schema 不匹配（期望 nf-postmortem/1）", "sections 必须是四段（现象/影响/根因/行动项）", "blame_tokens 不得为空（无指责与根因判据必须成文）", "root_cause_tokens 不得为空（无指责与根因判据必须成文）", "PO-2：缺必填字段：trigger", "PO-2：status 越词表：越词表", "PO-2：date 非 YYYY-MM-DD：2026/01/01", "PO-2：正文缺段落：## 影响", "PO-2：引用指向不存在的 check：check99", "PO-2：引用无法解析：no/such/file", "PO-3：缺必填字段：trigger"] as &[&str],
            ),
            (
                "gooddecl",
                Some(PM_DECL_OK),
                &[("PO-1-green.md", PM_GREEN), ("PO-3-closed.md", PM_CLOSED)][..],
                &["PO-1：缺必填字段：trigger", "PO-3：缺必填字段：trigger"] as &[&str],
            ),
            ("nodecl", None, &[("PO-1-green.md", PM_GREEN)][..], &["缺复盘协议声明 protocol/postmortem.json"] as &[&str]),
            ("nodocs", Some(PM_DECL_OK), &[][..], &[] as &[&str]),
        ] {
            let root = build_pm_fixture(scenario, decl, docs);
            let got = scan(&root);
            assert_eq!(got.issues, want, "场景 {} 的 issues", scenario);
        }
    }
    // <<< GENERATED

}
