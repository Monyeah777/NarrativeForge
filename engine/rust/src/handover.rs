//! 接力协议门禁（`handover`）—— 与真源 `desktop/src/core/handover.py` 对账。
//!
//! 判据：声明五段齐 / 交接件 frontmatter 必填齐、status 在词表、date 格式、五段齐、
//! **「未决项」非空且每条带「判据」**、`refs` 可解析到真实件或 `checkN`。

use crate::jsonread;
use crate::mdblocks;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, obj_is_empty, plain_str, plain_str_opt, py_str, py_truthy};
use std::path::Path;

pub const DECL_REL: &str = "protocol/handover.json";
pub const GLOB: &str = "handovers/HO-*.md";
const SCHEMA: &str = "nf-handover/1";
const SECTIONS: [&str; 5] = ["## 情境", "## 背景", "## 评估", "## 建议", "## 未决项"];
const DEFAULT_FIELDS: [&str; 6] = ["id", "date", "from", "to", "status", "refs"];

pub struct HandoverScan {
    pub issues: Vec<String>,
    pub handovers: usize,
    pub pending: usize,
}

struct Entry {
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
            Entry { file, fm, body }
        })
        .collect()
}

fn check_ids(root: &Path) -> std::collections::BTreeSet<String> {
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

fn is_adr(s: &str) -> bool {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| regex::Regex::new(r"^ADR-\d{4}$").expect("ADR 正则固定合法"));
    re.is_match(s)
}

fn is_check(s: &str) -> Option<String> {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| regex::Regex::new(r"^check(\d+)$").expect("判据引用正则固定合法"));
    re.captures(s).map(|c| c[1].to_string())
}

/// 真源 `check_doc` → `(issues, pending 条数)`。
fn check_doc(root: &Path, e: &Entry, d: &Json, checks: &std::collections::BTreeSet<String>) -> (Vec<String>, usize) {
    let mut issues = Vec::new();
    let fm = &e.fm;
    let body = &e.body;

    let fields = arr_items(get(d, "required_fields"));
    let field_names: Vec<String> = if fields.is_empty() {
        DEFAULT_FIELDS.iter().map(|s| (*s).to_string()).collect()
    } else {
        fields.iter().map(|v| plain_str(v)).collect()
    };
    for k in field_names {
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
    let pending_text = if body.contains("## 未决项") {
        body.splitn(2, "## 未决项").nth(1).unwrap_or("").to_string()
    } else {
        String::new()
    };
    let items = mdblocks::bullet_blocks(&pending_text);
    if items.is_empty() {
        issues.push("未决项为空——空未决 = 不合格交接（没有未决就是没交接）".to_string());
    }
    for it in &items {
        if !it.contains("判据") {
            issues.push(format!(
                "未决项缺判据（怎样算完成）：{}",
                &it[..it.len().min(40)]
            ));
        }
    }

    let refs_raw = get(fm, "refs");
    let refs: Vec<String> = match refs_raw {
        Some(Json::Str(s)) => vec![s.clone()],
        Some(Json::Array(a)) => a.iter().map(plain_str).collect(),
        _ => Vec::new(),
    };
    for r in refs {
        let mut s = r.trim().to_string();
        if s.starts_with('[') && s.ends_with(']') {
            s = s.trim_matches(|c| c == '[' || c == ']').trim().to_string();
        }
        if let Some(n) = is_check(&s) {
            if !checks.contains(&n) {
                issues.push(format!("refs 指向不存在的 check：{}", s));
            }
            continue;
        }
        if is_adr(&s) {
            continue;
        }
        if !root.join(s.replace('\\', "/")).exists() {
            issues.push(format!("refs 无法解析：{}", s));
        }
    }
    (issues, items.len())
}

/// 真源 `scan`。
pub fn scan(root: &Path) -> HandoverScan {
    let mut issues: Vec<String> = Vec::new();
    let Some(d) = decl(root) else {
        return HandoverScan {
            issues: vec![format!("缺交接协议声明 {}", DECL_REL)],
            handovers: 0,
            pending: 0,
        };
    };
    if py_str(get(&d, "schema")) != SCHEMA {
        issues.push(format!("交接协议 schema 不匹配（期望 {}）", SCHEMA));
    }
    let secs = crate::pyval::str_list(get(&d, "sections"));
    if secs != ["情境", "背景", "评估", "建议", "未决项"] {
        issues.push("sections 必须是五段（情境/背景/评估/建议/未决项）".to_string());
    }
    if arr_items(get(&d, "rules")).is_empty() {
        issues.push("rules 不得为空（交接纪律必须成文）".to_string());
    }
    let checks = check_ids(root);
    let rows = entries(root);
    let mut pending_total = 0usize;
    for e in &rows {
        let (i, pending) = check_doc(root, e, &d, &checks);
        let tag = {
            let id = py_str(get(&e.fm, "id"));
            if id.is_empty() {
                e.file.clone()
            } else {
                id
            }
        };
        issues.extend(i.into_iter().map(|x| format!("{}：{}", tag, x)));
        pending_total += pending;
    }
    HandoverScan {
        issues,
        handovers: rows.len(),
        pending: pending_total,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn missing_declaration_is_reported() {
        let tmp = crate::testutil::fixture("ho-missing");
        let got = scan(&tmp);
        assert_eq!(got.issues.len(), 1);
        assert!(got.issues[0].contains("缺交接协议声明"));
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn empty_pending_is_a_failure_even_when_sections_present() {
        let tmp = crate::testutil::fixture("ho-pending");
        std::fs::create_dir_all(tmp.join("protocol")).unwrap();
        std::fs::create_dir_all(tmp.join("handovers")).unwrap();
        std::fs::write(
            tmp.join(DECL_REL),
            r#"{"schema": "nf-handover/1", "sections": ["情境","背景","评估","建议","未决项"], "rules": ["r"]}"#
                .as_bytes(),
        )
        .unwrap();
        std::fs::write(
            tmp.join("handovers/HO-0001-a.md"),
            "---\nid: HO-0001\ndate: 2026-01-01\nfrom: a\nto: b\nstatus: open\nrefs: []\n---\n## 情境\nx\n## 背景\ny\n## 评估\nz\n## 建议\nw\n## 未决项\n"
                .as_bytes(),
        )
        .unwrap();
        let got = scan(&tmp);
        assert!(
            got.issues.iter().any(|i| i.contains("未决项为空")),
            "空未决必须判红：{:?}",
            got.issues
        );
        let _ = std::fs::remove_dir_all(&tmp);
    }    // >>> GENERATED by tools/gen_handover_branches.py（勿手改；重跑生成器覆盖本段）

    /// ===== 分支级差分判据（期望值由 `tools/gen_handover_branches.py` 从真源生成）=====
    ///
    /// 三个场景：声明坏（schema / 非五段 / rules 空）/ 缺声明 / 无交接件（门禁空转 warn）。
    /// 交接件逐分支踩：缺必填 / status 越词表 / 日期非法 / 正文缺段落 /
    /// **未决项为空**（空未决 = 不合格交接）/ 未决项缺判据 / `refs` 为字符串形态 /
    /// **移植面**：真源 `scan` 还返回 warns（「门禁空转」提示），但该面无消费者（契约只看 issues），
    /// 故本线结构体未纳入；期望值里的 `want_warns` 仅作记录，不参与断言。
    const HO_KITCHEN: &str = r#"---
id: HO-2
from: a
to: b
status: 越词表
date: 2026/01/01
refs: check99
---
## 情境
s
## 未决项
- 没有判据的一条
- 有判据的一条（判据：能跑通）
"#;
    const HO_GREEN: &str = r#"---
id: HO-3
from: a
to: b
status: open
date: 2026-01-02
refs:
  - check1
  - ADR-0001
  - no/such/file
---
## 情境
x
## 背景
x
## 评估
x
## 建议
x
## 未决项
- 做完某事的判据：跑通 verify.sh
"#;

    fn build_handover_fixture(scenario: &str, decl: Option<&str>,
                              docs: &[(&str, &str)]) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("handover-branches-{}", scenario));
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        if let Some(d) = decl {
            std::fs::write(root.join("protocol/handover.json"), d).unwrap();
        }
        if !docs.is_empty() {
            std::fs::create_dir_all(root.join("handovers")).unwrap();
            for (name, body) in docs {
                std::fs::write(root.join("handovers").join(name), body).unwrap();
            }
        }
        std::fs::write(root.join("verify.sh"), "#!/bin/bash\ncheck1(){\n  true\n}\n").unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_in_all_three_scenarios() {
        for (scenario, decl, docs, want_issues, want_warns, want_handovers, want_pending) in [
            (
                "baddecl",
                Some(r#"{"schema": "wrong/1", "sections": ["情境", "背景"], "rules": [], "required_fields": ["id", "date", "from", "to", "status", "refs", "extra"], "status_vocabulary": ["open", "closed"]}"#),
                &[("HO-2-kitchen.md", HO_KITCHEN), ("HO-3-green.md", HO_GREEN)][..],
                &["交接协议 schema 不匹配（期望 nf-handover/1）", "sections 必须是五段（情境/背景/评估/建议/未决项）", "rules 不得为空（交接纪律必须成文）", "HO-2：缺必填字段：extra", "HO-2：status 越词表：越词表", "HO-2：date 非 YYYY-MM-DD：2026/01/01", "HO-2：正文缺段落：## 背景", "HO-2：正文缺段落：## 评估", "HO-2：正文缺段落：## 建议", "HO-2：refs 指向不存在的 check：check99", "HO-3：缺必填字段：extra", "HO-3：refs 无法解析：no/such/file"] as &[&str],
                &[] as &[&str],
                2, 3,
            ),
            (
                "nodecl",
                None,
                &[("HO-4.md", HO_GREEN)][..],
                &["缺交接协议声明 protocol/handover.json"] as &[&str],
                &[] as &[&str],
                0, 0,
            ),
            ("nodocs", Some(r#"{"schema": "nf-handover/1", "sections": ["情境", "背景", "评估", "建议", "未决项"], "rules": ["r"], "required_fields": ["id", "date", "from", "to", "status", "refs"], "status_vocabulary": ["open", "closed"]}"#), &[][..],
             &[] as &[&str], &["暂无交接件（handovers/HO-*.md）——门禁空转"] as &[&str], 0, 0),
        ] {
            let root = build_handover_fixture(scenario, decl, docs);
            let got = scan(&root);
            assert_eq!(got.issues, want_issues, "场景 {} 的 issues", scenario);
            // 真源 `handover.scan` 还返回 warns（门禁空转提示），但本面无消费者，故未纳入移植面；
            // `want_warns` 仅作记录（前缀下划线以免 unused）。
            let _want_warns = want_warns;
            let _ = _want_warns;
            assert_eq!(got.handovers, want_handovers, "场景 {} 的件数", scenario);
            assert_eq!(got.pending, want_pending, "场景 {} 的未决项数", scenario);
        }
    }
    // <<< GENERATED

}
