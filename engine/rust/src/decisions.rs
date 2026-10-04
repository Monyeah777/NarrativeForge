//! 决策记录门禁（`decisions`）—— 与真源 `desktop/src/core/decisions.py` 对账。
//!
//! 判据：编号合法且与文件名一致 / 编号唯一 / 必填齐 / status 在词表 / date 格式 / 三段齐 /
//! evidence 可解析（真实件或 `checkN` 或 `ADR-N`）/ **accepted 须被协议回执锚定** /
//! supersede 链可解析且无环；另加**投影一致**（`decisions/INDEX.md` == 实时重算）。

use crate::jsonread;
use crate::mdblocks;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, plain_str, plain_str_opt, py_str, py_truthy};
use std::collections::BTreeSet;
use std::path::Path;

pub const GLOB: &str = "decisions/ADR-*.md";
pub const INDEX_REL: &str = "decisions/INDEX.md";
pub const RECEIPTS_REL: &str = "protocol/RECEIPTS.json";
pub const BEGIN: &str = "<!-- BEGIN GENERATED: decisions-index -->";
pub const END: &str = "<!-- END GENERATED: decisions-index -->";
const STATUSES: [&str; 4] = ["proposed", "accepted", "superseded", "deprecated"];
const SECTIONS: [&str; 3] = ["## 背景", "## 决策", "## 后果"];
/// 真源 `_DASH = ("—", "-", "")`。
const DASHES: [&str; 3] = ["—", "-", ""];

struct Entry {
    file: String,
    path: String,
    fm: Json,
    body: String,
}

fn re_id() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^ADR-(\d{4})$").expect("ADR id 正则固定合法"))
}

fn re_file_id() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^ADR-(\d{4})-").expect("ADR 文件名正则固定合法"))
}

fn re_check() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^check(\d+)$").expect("判据引用正则固定合法"))
}

fn re_adr() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^ADR-\d{4}$").expect("ADR 引用正则固定合法"))
}

fn re_dated() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^\d{4}-\d{2}-\d{2}$").expect("日期正则固定合法"))
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

fn receipt_ids(root: &Path) -> BTreeSet<String> {
    jsonread::read_file(root, RECEIPTS_REL)
        .map(|d| {
            arr_items(get(&d, "entries"))
                .iter()
                .map(|e| plain_str_opt(get(e, "id")))
                .collect()
        })
        .unwrap_or_default()
}

/// 真源 `entries`：按 id（缺则文件名）排序。
fn entries(root: &Path) -> Vec<Entry> {
    let mut out: Vec<Entry> = crate::glob::expand(root, GLOB)
        .into_iter()
        .map(|rel| {
            let text = std::fs::read_to_string(root.join(&rel)).unwrap_or_default();
            let (fm, body) = mdblocks::parse_frontmatter(&text);
            let file = rel.rsplit('/').next().unwrap_or(&rel).to_string();
            Entry { file, path: rel, fm, body }
        })
        .collect();
    out.sort_by_key(|e| {
        let id = get(&e.fm, "id");
        if py_truthy(id.unwrap_or(&Json::Null)) {
            plain_str(id.unwrap())
        } else {
            e.file.clone()
        }
    });
    out
}

/// 真源 `scan` → `(issues, decisions, accepted, chains)`。
pub fn scan(root: &Path) -> (Vec<String>, usize, usize, usize) {
    let mut issues: Vec<String> = Vec::new();
    let rows = entries(root);
    if rows.is_empty() {
        return (vec![format!("未发现任何 ADR（{}）", GLOB)], 0, 0, 0);
    }
    let checks = check_ids(root);
    let receipts = receipt_ids(root);
    let has_receipts = root.join(RECEIPTS_REL).is_file();

    let mut ids: Vec<(String, String)> = Vec::new(); // id → file（真源 dict：同 id 覆盖）
    let mut supby: Vec<(String, String)> = Vec::new();
    for e in &rows {
        let fm = &e.fm;
        let name = &e.file;
        let did = py_str(get(fm, "id"));
        let tag = if did.is_empty() { name.clone() } else { did.clone() };
        if did.is_empty() {
            issues.push(format!("{} 缺 frontmatter id", name));
            continue;
        }
        if !re_id().is_match(&did) {
            issues.push(format!("{} 的 id 不合法（须 ADR-四位数字）：{}", name, did));
        }
        match re_file_id().captures(name) {
            Some(c) if format!("ADR-{}", &c[1]) == did => {}
            _ => issues.push(format!("{} 的 id 与文件名不一致：{}", name, did)),
        }
        if let Some((_, prev)) = ids.iter().find(|(i, _)| *i == did) {
            issues.push(format!("ADR 编号重复：{}（{} 与 {}）", did, prev, name));
            if let Some(slot) = ids.iter_mut().find(|(i, _)| *i == did) {
                slot.1 = name.clone();
            }
        } else {
            ids.push((did.clone(), name.clone()));
        }
        for k in ["title", "status", "date", "evidence"] {
            if !py_truthy(get(fm, k).unwrap_or(&Json::Null)) {
                issues.push(format!("{} 缺必填字段：{}", tag, k));
            }
        }
        let st = py_str(get(fm, "status"));
        if !st.is_empty() && !STATUSES.contains(&st.as_str()) {
            issues.push(format!("{} 的 status 越词表：{}（{}）", tag, st, STATUSES.join("/")));
        }
        let date = py_str(get(fm, "date"));
        if !date.is_empty() && !re_dated().is_match(&date) {
            issues.push(format!("{} 的 date 非 YYYY-MM-DD：{}", tag, date));
        }
        for sec in SECTIONS {
            if !e.body.contains(sec) {
                issues.push(format!("{} 正文缺段落：{}", tag, sec));
            }
        }
        for ev in arr_items(get(fm, "evidence")) {
            let s = plain_str(ev).trim().to_string();
            if s.is_empty() {
                issues.push(format!("{} 的 evidence 有空项", tag));
                continue;
            }
            if let Some(c) = re_check().captures(&s) {
                if !checks.contains(&c[1]) {
                    issues.push(format!("{} 的 evidence 指向不存在的 check：{}", tag, s));
                }
                continue;
            }
            if re_adr().is_match(&s) {
                continue;
            }
            if !root.join(s.replace('\\', "/")).exists() {
                issues.push(format!(
                    "{} 的 evidence 无法解析：{}（修复指引：改为真实件路径，或 checkN，或 ADR-N）",
                    tag, s
                ));
            }
        }
        if st == "accepted" && has_receipts && !receipts.contains(&e.path) {
            issues.push(format!(
                "{} 已 accepted 但未被协议回执锚定（修复指引：nf receipts --write）——未锚定的 accepted 等于可被偷改",
                tag
            ));
        }
        let sb = py_str(get(fm, "superseded_by")).trim().to_string();
        if st == "superseded" && DASHES.contains(&sb.as_str()) {
            issues.push(format!("{} 标 superseded 但缺 superseded_by", tag));
        }
        if !DASHES.contains(&sb.as_str()) {
            if let Some(slot) = supby.iter_mut().find(|(i, _)| *i == did) {
                slot.1 = sb;
            } else {
                supby.push((did.clone(), sb));
            }
        }
    }

    for (did, target) in &supby {
        if !ids.iter().any(|(i, _)| i == target) {
            issues.push(format!("{} 的 superseded_by 指向不在册编号：{}", did, target));
            continue;
        }
        let mut cur = target.clone();
        let mut hops = 0usize;
        while let Some((_, next)) = supby.iter().find(|(i, _)| *i == cur) {
            if hops >= supby.len() + 1 {
                break;
            }
            cur = next.clone();
            hops += 1;
            if cur == *did {
                issues.push(format!("取代链成环：{} → … → {}", did, did));
                break;
            }
        }
    }

    for (did, _) in &ids {
        for other in &rows {
            if &py_str(get(&other.fm, "id")) != did {
                continue;
            }
            let sup = py_str(get(&other.fm, "supersedes")).trim().to_string();
            if !DASHES.contains(&sup.as_str()) && !ids.iter().any(|(i, _)| *i == sup) {
                issues.push(format!("{} 的 supersedes 指向不在册编号：{}", did, sup));
            }
        }
    }

    let accepted = rows
        .iter()
        .filter(|e| plain_str_opt(get(&e.fm, "status")) == "accepted")
        .count();
    (issues, ids.len(), accepted, supby.len())
}

/// 真源 `render_index`：投影表。
pub fn render_index(root: &Path) -> String {
    let mut out: Vec<String> = vec![
        BEGIN.to_string(),
        String::new(),
        "## 决策登记表（由各 ADR frontmatter 生成，勿手改）".to_string(),
        String::new(),
        "| 编号 | 标题 | 状态 | 日期 | 取代 |".to_string(),
        "|---|---|---|---|---|".to_string(),
    ];
    for e in entries(root) {
        let fm = &e.fm;
        let cell = |k: &str, default: String| -> String {
            match get(fm, k) {
                Some(v) => plain_str(v),
                None => default,
            }
        };
        // 真源 `fm.get("superseded_by") or "—"` —— 假值落横线
        let sb = match get(fm, "superseded_by") {
            Some(v) if py_truthy(v) => plain_str(v),
            _ => "—".to_string(),
        };
        out.push(format!(
            "| {} | {} | {} | {} | {} |",
            cell("id", e.file.clone()),
            cell("title", String::new()),
            cell("status", String::new()),
            cell("date", String::new()),
            sb
        ));
    }
    out.push(String::new());
    out.push(
        "> 真源 = `decisions/ADR-*.md` 的 frontmatter；本表为投影（`nf decisions reindex` 重建）。"
            .to_string(),
    );
    out.push(String::new());
    out.push(END.to_string());
    out.join("\n")
}

/// 真源 `check_projection`。
pub fn check_projection(root: &Path) -> Vec<String> {
    let p = root.join(INDEX_REL);
    if !p.is_file() {
        return vec![format!("缺 {}（修复指引：nf decisions reindex）", INDEX_REL)];
    }
    let text = std::fs::read_to_string(&p).unwrap_or_default();
    if !text.contains(BEGIN) || !text.contains(END) {
        return vec![format!("{} 缺生成区标记", INDEX_REL)];
    }
    let i = text.find(BEGIN).unwrap_or(0);
    let j = text.find(END).unwrap_or(0) + END.len();
    if &text[i..j] == render_index(root) {
        Vec::new()
    } else {
        vec!["决策登记表与实时重算不一致（跑 nf decisions reindex）".to_string()]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn missing_adrs_reports_and_zeroes_stats() {
        let tmp = crate::testutil::fixture("dec-none");
        let (issues, d, a, c) = scan(&tmp);
        assert_eq!(issues.len(), 1);
        assert!(issues[0].contains("未发现任何 ADR"));
        assert_eq!((d, a, c), (0, 0, 0));
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn id_must_match_file_name() {
        let tmp = crate::testutil::fixture("dec-idmismatch");
        std::fs::create_dir_all(tmp.join("decisions")).unwrap();
        std::fs::write(
            tmp.join("decisions/ADR-0007-x.md"),
            "---\nid: ADR-0009\ntitle: t\nstatus: accepted\ndate: 2026-01-01\nevidence: [protocol/LAYERS.json]\n---\n## 背景\n## 决策\n## 后果\n"
                .as_bytes(),
        )
        .unwrap();
        let (issues, _, _, _) = scan(&tmp);
        assert!(
            issues.iter().any(|i| i.contains("id 与文件名不一致")),
            "编号与文件名不一致必须判红：{:?}",
            issues
        );
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn supersede_cycle_is_detected() {
        let tmp = crate::testutil::fixture("dec-cycle");
        std::fs::create_dir_all(tmp.join("decisions")).unwrap();
        for (n, sb) in [("0001", "ADR-0002"), ("0002", "ADR-0001")] {
            std::fs::write(
                tmp.join(format!("decisions/ADR-{}-x.md", n)),
                format!(
                    "---\nid: ADR-{}\ntitle: t\nstatus: superseded\ndate: 2026-01-01\nevidence: [protocol/LAYERS.json]\nsuperseded_by: {}\n---\n## 背景\n## 决策\n## 后果\n",
                    n, sb
                )
                .as_bytes(),
            )
            .unwrap();
        }
        let (issues, _, _, chains) = scan(&tmp);
        assert_eq!(chains, 2);
        assert!(
            issues.iter().any(|i| i.contains("取代链成环")),
            "环必须判红：{:?}",
            issues
        );
        let _ = std::fs::remove_dir_all(&tmp);
    }    // >>> GENERATED by tools/gen_decisions_branches.py（勿手改；重跑生成器覆盖本段）

    /// ===== 分支级差分判据（期望值由 `tools/gen_decisions_branches.py` 从真源生成）=====
    ///
    /// 真源在 `decisions.scan` 里有 **16 个 issue 分支**；真语料只踩到其中少数（如成环）。
    /// 本夹具逐分支踩：缺 id / id 不合法 / id 与文件名不一致 / 编号重复 / 缺必填 / status 越词表 /
    /// 日期非法 / 缺正文段落 / 证据空项 / 证据指向不存在 check / 证据无法解析 / accepted 未被回执锚定 /
    /// superseded 缺 superseded_by / superseded_by 指向不在册 / 取代链成环 / supersedes 指向不在册。
    const WANT_DEC_ISSUES: [&str; 38] = [
        "ADR-0001-missing-id.md 缺 frontmatter id",
        "ADR-0004 缺必填字段：title",
        "ADR-0004 缺必填字段：evidence",
        "ADR 编号重复：ADR-0004（ADR-0004-dupA.md 与 ADR-0004-dupB.md）",
        "ADR-0004 缺必填字段：title",
        "ADR-0004 缺必填字段：evidence",
        "ADR-0005 缺必填字段：title",
        "ADR-0005 的 status 越词表：越词表（proposed/accepted/superseded/deprecated）",
        "ADR-0005 的 date 非 YYYY-MM-DD：2026/01/01",
        "ADR-0005 正文缺段落：## 决策",
        "ADR-0005 正文缺段落：## 后果",
        "ADR-0005 的 evidence 无法解析：-（修复指引：改为真实件路径，或 checkN，或 ADR-N）",
        "ADR-0005 的 evidence 指向不存在的 check：check99",
        "ADR-0005 的 evidence 无法解析：no/such/pattern（修复指引：改为真实件路径，或 checkN，或 ADR-N）",
        "ADR-0006 缺必填字段：title",
        "ADR-0006 缺必填字段：evidence",
        "ADR-0006 已 accepted 但未被协议回执锚定（修复指引：nf receipts --write）——未锚定的 accepted 等于可被偷改",
        "ADR-0007 缺必填字段：title",
        "ADR-0007 缺必填字段：evidence",
        "ADR-0007 标 superseded 但缺 superseded_by",
        "ADR-0008 缺必填字段：title",
        "ADR-0008 缺必填字段：evidence",
        "ADR-0009 缺必填字段：title",
        "ADR-0009 缺必填字段：evidence",
        "ADR-0010 缺必填字段：title",
        "ADR-0010 缺必填字段：evidence",
        "ADR-0011 缺必填字段：title",
        "ADR-0003-mismatch.md 的 id 与文件名不一致：ADR-9999",
        "ADR-9999 缺必填字段：title",
        "ADR-9999 缺必填字段：evidence",
        "ADR-0002-bad-id.md 的 id 不合法（须 ADR-四位数字）：ADR-abc",
        "ADR-0002-bad-id.md 的 id 与文件名不一致：ADR-abc",
        "ADR-abc 缺必填字段：title",
        "ADR-abc 缺必填字段：evidence",
        "ADR-0008 的 superseded_by 指向不在册编号：ADR-7777",
        "取代链成环：ADR-0009 → … → ADR-0009",
        "取代链成环：ADR-0010 → … → ADR-0010",
        "ADR-0011 的 supersedes 指向不在册编号：['ADR-8888']",
    ];

    fn build_decisions_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("decisions-branches");
        for (rel, body) in [
            ("decisions/ADR-0001-missing-id.md", r#"---
status: proposed
date: 2026-01-01
deciders: a
evidence: []
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("decisions/ADR-0002-bad-id.md", r#"---
id: ADR-abc
status: proposed
date: 2026-01-01
deciders: a
evidence: []
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("decisions/ADR-0003-mismatch.md", r#"---
id: ADR-9999
status: proposed
date: 2026-01-01
deciders: a
evidence: []
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("decisions/ADR-0004-dupA.md", r#"---
id: ADR-0004
status: proposed
date: 2026-01-01
deciders: a
evidence: []
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("decisions/ADR-0004-dupB.md", r#"---
id: ADR-0004
status: proposed
date: 2026-01-01
deciders: a
evidence: []
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("decisions/ADR-0005-kitchen.md", r#"---
id: ADR-0005
status: 越词表
date: 2026/01/01
evidence:
  - 
  - check99
  - no/such/pattern
---
## 背景
只有背景
"#),
            ("decisions/ADR-0006-unanchored.md", r#"---
id: ADR-0006
status: accepted
date: 2026-01-01
deciders: a
evidence: []
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("decisions/ADR-0007-nosupby.md", r#"---
id: ADR-0007
status: superseded
date: 2026-01-01
deciders: a
evidence: []
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("decisions/ADR-0008-badsupby.md", r#"---
id: ADR-0008
status: superseded
date: 2026-01-01
deciders: a
evidence: []
superseded_by: ADR-7777
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("decisions/ADR-0009-cycleA.md", r#"---
id: ADR-0009
status: superseded
date: 2026-01-01
deciders: a
evidence: []
superseded_by: ADR-0010
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("decisions/ADR-0010-cycleB.md", r#"---
id: ADR-0010
status: superseded
date: 2026-01-01
deciders: a
evidence: []
superseded_by: ADR-0009
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("decisions/ADR-0011-badsupersedes.md", r#"---
id: ADR-0011
status: accepted
date: 2026-01-01
deciders: a
evidence:
  - check1
supersedes:
  - ADR-8888
---
## 背景
b

## 决策
d

## 后果
c
"#),
            ("protocol/RECEIPTS.json", r#"{"schema": "nf-receipts/1", "entries": [{"id": "decisions/ADR-0011-badsupersedes.md"}]}"#),
            ("verify.sh", r#"#!/bin/bash
check1(){
  true
}
"#),
        ] {
            let p = root.join(rel);
            if let Some(d) = p.parent() {
                std::fs::create_dir_all(d).unwrap();
            }
            std::fs::write(p, body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_decisions_fixture();
        let (issues, decisions, accepted, chains) = scan(&root);
        assert_eq!(issues, WANT_DEC_ISSUES, "逐条消息与次序都须与真源一致");
        assert_eq!((decisions, accepted, chains), (10, 2, 3), "三项统计");
    }
    // <<< GENERATED

}
