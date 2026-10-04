//! 内容建模三件门禁（`modeling`）—— 与真源 `desktop/src/core/modeling.py` 对账。
//!
//! 三件：**词表登记册**（每个 scheme 的 probe 必须回指真源且逐项一致）/ **规范与说明件之分**
//! （两份名单交集为空；规范件须被回执锚定或显式 `covered_by`；说明件不得进回执覆盖面）/
//! **数据契约登记**（artifact 在场、quality_rule 解析到真实 checkN 或 assertion:<id>）。
//!
//! `python_attr` 探针走 [`crate::pyconsts`]（转录的真源常量；未登记即报"真源取不到"）。

use crate::jsonread;
use crate::pyconsts;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, plain_str, plain_str_opt, py_str};
use std::collections::BTreeSet;
use std::path::Path;

pub const VOCAB_REL: &str = "protocol/vocabularies.json";
pub const NORM_REL: &str = "protocol/normative.json";
pub const DC_REL: &str = "protocol/data_contracts.json";
pub const RECEIPTS_REL: &str = "protocol/RECEIPTS.json";
const VOCAB_SCHEMA: &str = "nf-vocabularies/1";
const NORM_SCHEMA: &str = "nf-normative/1";
const DC_SCHEMA: &str = "nf-data-contracts/1";

fn read(root: &Path, rel: &str) -> Option<Json> {
    if !root.join(rel).is_file() {
        return None;
    }
    jsonread::read_file(root, rel)
}

/// 真源 `_as_values`：dict → 键；list → 元素 str；其余 → 空。
fn as_values(j: &Json) -> Vec<String> {
    match j {
        Json::Object(p) => p.iter().map(|(k, _)| k.clone()).collect(),
        Json::Array(a) => a.iter().map(plain_str).collect(),
        _ => Vec::new(),
    }
}

/// 真源 `_probe` → `(values, note)`。
fn probe(root: &Path, pr: &Json) -> (Vec<String>, String) {
    let kind = py_str(get(pr, "kind"));
    match kind.as_str() {
        "literal" => (Vec::new(), "literal（以本册为准）".to_string()),
        "python_attr" => {
            let module = plain_str_opt(get(pr, "module"));
            let attr = plain_str_opt(get(pr, "attr"));
            match pyconsts::lookup(&module, &attr) {
                Some(vals) => (vals.iter().map(|s| (*s).to_string()).collect(), "python_attr".to_string()),
                None => (
                    Vec::new(),
                    format!("python_attr 未登记：{}.{}", module, attr),
                ),
            }
        }
        "json_path" => {
            let rel = py_str(get(pr, "file"));
            let Some(mut doc) = read(root, &rel) else {
                return (Vec::new(), format!("json_path 断链：{}", py_str(get(pr, "path"))));
            };
            for part in py_str(get(pr, "path")).split('.') {
                let next = match &doc {
                    Json::Object(p) => p.iter().find(|(k, _)| k == part).map(|(_, v)| v.clone()),
                    _ => None,
                };
                match next {
                    Some(v) => doc = v,
                    None => {
                        return (
                            Vec::new(),
                            format!("json_path 断链：{}", py_str(get(pr, "path"))),
                        )
                    }
                }
            }
            (as_values(&doc), "json_path".to_string())
        }
        other => (Vec::new(), format!("未知 probe.kind：{}", other)),
    }
}

/// 真源 `verify_vocabularies` → `(issues, schemes, literal_count)`。
fn verify_vocabularies(root: &Path) -> (Vec<String>, usize, usize) {
    let mut issues = Vec::new();
    let Some(doc) = read(root, VOCAB_REL) else {
        return (vec![format!("缺词表登记册 {}", VOCAB_REL)], 0, 0);
    };
    if crate::pyval::obj_is_empty(&doc) {
        return (vec![format!("缺词表登记册 {}", VOCAB_REL)], 0, 0);
    }
    if py_str(get(&doc, "schema")) != VOCAB_SCHEMA {
        issues.push(format!("词表登记册 schema 不匹配（期望 {}）", VOCAB_SCHEMA));
    }
    let mut statuses: Vec<String> = crate::pyval::str_list(get(&doc, "status_vocabulary"));
    statuses.sort();
    if statuses != ["active", "deprecated"] {
        issues.push("status 词表与判据不一致（期望 active/deprecated）".to_string());
    }
    let statuses = crate::pyval::str_list(get(&doc, "status_vocabulary"));
    let kinds = crate::pyval::str_list(get(&doc, "probe_kinds"));

    let mut seen: BTreeSet<String> = BTreeSet::new();
    let mut literal = 0usize;
    for s in arr_items(get(&doc, "schemes")) {
        let sid = py_str(get(s, "id"));
        if seen.contains(&sid) {
            issues.push(format!("词表 id 重复：{}", sid));
        }
        seen.insert(sid.clone());
        if !statuses.contains(&plain_str_opt(get(s, "status"))) {
            issues.push(format!("词表 {} status 越词表：{}", sid, plain_str_opt(get(s, "status"))));
        }
        let vals: Vec<String> = arr_items(get(s, "values")).iter().map(|v| plain_str(v)).collect();
        if vals.len() < 2 {
            issues.push(format!("词表 {} 少于两个值（不成词表）", sid));
        }
        let uniq: BTreeSet<&String> = vals.iter().collect();
        if uniq.len() != vals.len() {
            issues.push(format!("词表 {} 值重复", sid));
        }
        for a in arr_items(get(s, "aliases")) {
            if vals.contains(&plain_str(a)) {
                issues.push(format!("词表 {} 的 alias 与值撞车：{}", sid, plain_str(a)));
            }
        }
        let pr = get(s, "probe").filter(|v| matches!(v, Json::Object(_))).cloned().unwrap_or(Json::Object(Vec::new()));
        if !kinds.contains(&py_str(get(&pr, "kind"))) {
            issues.push(format!(
                "词表 {} 的 probe.kind 不在册：{}",
                sid,
                plain_str_opt(get(&pr, "kind"))
            ));
            continue;
        }
        let (live, note) = probe(root, &pr);
        let is_literal = py_str(get(&pr, "kind")) == "literal";
        if is_literal {
            literal += 1;
            continue;
        }
        if live.is_empty() {
            issues.push(format!("词表 {} 的真源取不到（{}）", sid, note));
            continue;
        }
        let mut a = live.clone();
        let mut b = vals.clone();
        a.sort();
        b.sort();
        if a != b {
            issues.push(format!(
                "词表 {} 与真源漂移：册={} 真源={}",
                sid,
                b.join("/"),
                a.join("/")
            ));
        }
    }
    (issues, seen.len(), literal)
}

/// 真源 `verify_normative` → `(issues, normative_count, informative_count)`。
fn verify_normative(root: &Path) -> (Vec<String>, usize, usize) {
    let mut issues = Vec::new();
    let Some(doc) = read(root, NORM_REL) else {
        return (vec![format!("缺规范/说明件名单 {}", NORM_REL)], 0, 0);
    };
    if crate::pyval::obj_is_empty(&doc) {
        return (vec![format!("缺规范/说明件名单 {}", NORM_REL)], 0, 0);
    }
    if py_str(get(&doc, "schema")) != NORM_SCHEMA {
        issues.push(format!("规范件名单 schema 不匹配（期望 {}）", NORM_SCHEMA));
    }
    let checks = check_ids(root);
    let receipts = receipt_ids(root);
    let mut norm_paths: Vec<String> = Vec::new();
    for item in arr_items(get(&doc, "normative")) {
        let entry = if matches!(item, Json::Object(_)) {
            item.clone()
        } else {
            Json::Object(vec![("path".to_string(), Json::Str(plain_str(item)))])
        };
        let rel = py_str(get(&entry, "path"));
        norm_paths.push(rel.clone());
        if rel.is_empty() {
            issues.push("规范件条目缺 path".to_string());
            continue;
        }
        if !root.join(&rel).is_file() {
            issues.push(format!("规范件不存在：{}", rel));
            continue;
        }
        if receipts.contains(&rel) {
            continue;
        }
        let covered: Vec<String> = arr_items(get(&entry, "covered_by"))
            .iter()
            .map(|c| plain_str(c))
            .collect();
        if covered.is_empty() {
            issues.push(format!(
                "规范件既未被回执锚定也无 covered_by：{}（修复指引：跑 nf receipts --write，或显式声明 covered_by）",
                rel
            ));
            continue;
        }
        for c in covered {
            if let Some(cap) = judge_check_re().captures(&c) {
                if !checks.contains(&cap[1]) {
                    issues.push(format!("规范件 {} 的 covered_by 指向不存在的 check：{}", rel, c));
                }
            }
        }
    }

    let mut info_hits: BTreeSet<String> = BTreeSet::new();
    for g in arr_items(get(&doc, "informative")).iter().map(|v| plain_str(v)) {
        // 真源 `pat = g + "/*" if g.endswith("/**") else g` —— 是**在 g 后面追加** `/*`，
        // 不是把 `/**` 换成 `/*`（`docs/**` → `docs/**/*`）。抄成后者会丢掉 `**`，
        // 说明件数从 2352 掉到 75，且**不会**被 ok/not-ok 察觉（只错一个计数）。
        let pat = if g.ends_with("/**") { format!("{}/*", g) } else { g.clone() };
        let hits = crate::glob::expand(root, &pat);
        for h in hits {
            info_hits.insert(h);
        }
    }
    for rel in &info_hits {
        if receipts.contains(rel) {
            issues.push(format!("说明件被回执锚定（等于把解释当规范）：{}", rel));
        }
    }
    let norm_set: BTreeSet<String> = norm_paths.iter().cloned().collect();
    let mut overlap: Vec<String> = info_hits.intersection(&norm_set).cloned().collect();
    overlap.sort();
    for rel in overlap {
        issues.push(format!("同一件既列规范又列说明：{}", rel));
    }
    (issues, norm_paths.len(), info_hits.len())
}

/// 真源 `verify_contracts` → `(issues, contracts_count)`。
fn verify_contracts(root: &Path) -> (Vec<String>, usize) {
    let mut issues = Vec::new();
    let Some(doc) = read(root, DC_REL) else {
        return (vec![format!("缺数据契约登记 {}", DC_REL)], 0);
    };
    if crate::pyval::obj_is_empty(&doc) {
        return (vec![format!("缺数据契约登记 {}", DC_REL)], 0);
    }
    if py_str(get(&doc, "schema")) != DC_SCHEMA {
        issues.push(format!("数据契约登记 schema 不匹配（期望 {}）", DC_SCHEMA));
    }
    let statuses = crate::pyval::str_list(get(&doc, "status_vocabulary"));
    let prefixes = crate::pyval::str_list(get(&doc, "rule_prefixes"));
    if prefixes != ["check", "assertion:"] {
        issues.push("rule_prefixes 与判据不一致（期望 check / assertion:）".to_string());
    }
    let checks = check_ids(root);
    let assertion_ids: BTreeSet<String> = read(root, "protocol/assertions.json")
        .map(|d| {
            arr_items(get(&d, "assertions"))
                .iter()
                .map(|a| plain_str_opt(get(a, "id")))
                .collect()
        })
        .unwrap_or_default();

    let mut seen: BTreeSet<String> = BTreeSet::new();
    for c in arr_items(get(&doc, "contracts")) {
        let cid = py_str(get(c, "id"));
        if seen.contains(&cid) {
            issues.push(format!("契约 id 重复：{}", cid));
        }
        seen.insert(cid.clone());
        let art = py_str(get(c, "artifact"));
        if art.is_empty() || !root.join(&art).is_file() {
            issues.push(format!(
                "契约 {} 的 artifact 不存在：{}",
                cid,
                if art.is_empty() { "(缺)" } else { art.as_str() }
            ));
        }
        if !statuses.contains(&plain_str_opt(get(c, "status"))) {
            issues.push(format!("契约 {} status 越词表：{}", cid, plain_str_opt(get(c, "status"))));
        }
        if py_str(get(c, "owner")).trim().is_empty() {
            issues.push(format!("契约 {} 缺 owner（无人认领的契约不许登记）", cid));
        }
        if py_str(get(c, "freshness")).trim().is_empty() {
            issues.push(format!("契约 {} 缺 freshness（重建动作必须写明）", cid));
        }
        let rule = py_str(get(c, "quality_rule"));
        if let Some(rest) = rule.strip_prefix("check") {
            if !checks.contains(rest) {
                issues.push(format!("契约 {} 的 quality_rule 指向不存在的 check：{}", cid, rule));
            }
        } else if let Some(rest) = rule.strip_prefix("assertion:") {
            if !assertion_ids.contains(rest) {
                issues.push(format!("契约 {} 的 quality_rule 指向不存在的断言：{}", cid, rule));
            }
        } else {
            issues.push(format!(
                "契约 {} 的 quality_rule 无法解析（须 checkN 或 assertion:<id>）：{}",
                cid,
                if rule.is_empty() { "(缺)" } else { rule.as_str() }
            ));
        }
    }
    (issues, seen.len())
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

fn judge_check_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^check(\d+)$").expect("判据引用正则固定合法"))
}

fn receipt_ids(root: &Path) -> BTreeSet<String> {
    read(root, RECEIPTS_REL)
        .map(|d| {
            arr_items(get(&d, "entries"))
                .iter()
                .map(|e| plain_str_opt(get(e, "id")))
                .collect()
        })
        .unwrap_or_default()
}

/// 真源 `modeling.scan` 的三段聚合（本契约只要 issues 与三个计数）。
pub struct ModelingScan {
    pub issues: Vec<String>,
    pub schemes: usize,
    pub normative: usize,
    pub informative_files: usize,
    pub contracts: usize,
}

pub fn scan(root: &Path) -> ModelingScan {
    let (mut issues, schemes, _literal) = verify_vocabularies(root);
    let (ni, normative, informative_files) = verify_normative(root);
    let (ci, contracts) = verify_contracts(root);
    issues.extend(ni);
    issues.extend(ci);
    ModelingScan {
        issues,
        schemes,
        normative,
        informative_files,
        contracts,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn missing_declarations_are_reported_in_scan_order() {
        let tmp = crate::testutil::fixture("modeling-missing");
        let got = scan(&tmp);
        assert_eq!(got.issues.len(), 3, "三件各报一条：{:?}", got.issues);
        assert!(got.issues[0].contains("缺词表登记册"));
        assert!(got.issues[1].contains("缺规范/说明件名单"));
        assert!(got.issues[2].contains("缺数据契约登记"));
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn informative_double_star_is_appended_not_replaced() {
        // 真源 `g + "/*"`：`docs/**` → `docs/**/*`（递归）。抄成 `docs/*` 会只数直接子级，
        // 而 ok/not-ok 不会变——只错一个计数（实测：2352 → 75）。
        let tmp = crate::testutil::fixture("modeling-informative");
        std::fs::create_dir_all(tmp.join("protocol")).unwrap();
        std::fs::create_dir_all(tmp.join("docs/sub")).unwrap();
        std::fs::write(tmp.join("docs/a.md"), "x").unwrap();
        std::fs::write(tmp.join("docs/sub/b.md"), "x").unwrap();
        std::fs::write(
            tmp.join(NORM_REL),
            r#"{"schema": "nf-normative/1", "normative": [], "informative": ["docs/**"]}"#
                .as_bytes(),
        )
        .unwrap();
        let got = scan(&tmp);
        assert_eq!(
            got.informative_files, 2,
            "`docs/**` 必须递归命中子目录（a.md + sub/b.md）"
        );
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn python_attr_probe_uses_the_transcribed_registry() {
        let pr: Json = jsonread::convert(&serde_json::json!({
            "kind": "python_attr", "module": "core.doc_hygiene", "attr": "KINDS"
        }))
        .unwrap();
        let (vals, note) = probe(Path::new("."), &pr);
        assert_eq!(note, "python_attr");
        assert_eq!(vals, vec!["tutorial", "how-to", "reference", "explanation"]);
        // 未登记的常量必须报"取不到"，不得冒充一致
        let pr2: Json = jsonread::convert(&serde_json::json!({
            "kind": "python_attr", "module": "core.nope", "attr": "X"
        }))
        .unwrap();
        let (v2, n2) = probe(Path::new("."), &pr2);
        assert!(v2.is_empty());
        assert!(n2.contains("未登记"), "got: {}", n2);
    }

    #[test]
    fn as_values_mirrors_truth_source() {
        let obj = jsonread::convert(&serde_json::json!({"b": 1, "a": 2})).unwrap();
        let mut got = as_values(&obj);
        got.sort();
        assert_eq!(got, vec!["a", "b"]);
        let arr = jsonread::convert(&serde_json::json!(["x", "y"])).unwrap();
        assert_eq!(as_values(&arr), vec!["x", "y"]);
    }
    /// ===== 分支级差分判据（期望值由 `tools/gen_modeling_branches.py` 从真源生成）=====
    ///
    /// 真语料上 `modeling` 三件全绿 ⇒ 只靠契约对账核不到错误分支。本夹具逐分支踩：
    /// 词表（schema / status 词表 / id 重复 / 值不足 / 值重复 / alias 撞车 / probe.kind 不在册 /
    /// json_path 断链 / 真源漂移 / python_attr 已登记与未登记）、规范件（缺 path / 不存在 /
    /// 无锚定 / covered_by 指向不存在 check / 合法 / 与说明件重叠 / 说明面未命中）、
    /// 数据契约（schema / rule_prefixes / id 重复 / artifact 缺 / status 越词表 / 缺 owner /
    /// 缺 freshness / 规则指向不存在 check / 指向不存在断言 / 无法解析 / 合法）。
    const WANT_MD_ISSUES: [&str; 27] = [
        "词表登记册 schema 不匹配（期望 nf-vocabularies/1）",
        "status 词表与判据不一致（期望 active/deprecated）",
        "词表 id 重复：v-literal",
        "词表 v-literal 少于两个值（不成词表）",
        "词表 v-status status 越词表：bogus",
        "词表 v-dup 值重复",
        "词表 v-dup 的 alias 与值撞车：a",
        "词表 v-kind 的 probe.kind 不在册：nope",
        "词表 v-broken 的真源取不到（json_path 断链：nope.deep）",
        "词表 v-drift 与真源漂移：册=x/y 真源=x/z",
        "词表 v-attr status 越词表：deprecated",
        "规范件名单 schema 不匹配（期望 nf-normative/1）",
        "规范件条目缺 path",
        "规范件不存在：docs/missing.md",
        "规范件既未被回执锚定也无 covered_by：docs/norm-a.md（修复指引：跑 nf receipts --write，或显式声明 covered_by）",
        "规范件 docs/norm-a.md 的 covered_by 指向不存在的 check：check99",
        "规范件既未被回执锚定也无 covered_by：docs/ex/one.md（修复指引：跑 nf receipts --write，或显式声明 covered_by）",
        "同一件既列规范又列说明：docs/ex/one.md",
        "数据契约登记 schema 不匹配（期望 nf-data-contracts/1）",
        "rule_prefixes 与判据不一致（期望 check / assertion:）",
        "契约 id 重复：c1",
        "契约 c1 的 artifact 不存在：no/such",
        "契约 c1 status 越词表：bogus",
        "契约 c1 缺 owner（无人认领的契约不许登记）",
        "契约 c1 缺 freshness（重建动作必须写明）",
        "契约 c1 的 quality_rule 指向不存在的断言：assertion:nope",
        "契约 c3 的 quality_rule 无法解析（须 checkN 或 assertion:<id>）：不能解析",
    ];

    fn build_modeling_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("modeling-branches");
        for rel in ["protocol", "protocol/schema", "docs", "docs/ex", "library"] {
            std::fs::create_dir_all(root.join(rel)).unwrap();
        }
        for (rel, body) in [
            ("docs/ex/one.md", r#"# one
"#),
            ("docs/ex/two.md", r#"# two
"#),
            ("docs/norm-a.md", r#"# a
"#),
            ("docs/norm-b.md", r#"# b
"#),
            ("protocol/RECEIPTS.json", r#"{"schema": "nf-receipts/1", "entries": [{"id": "docs/norm-b.md"}]}"#),
            ("protocol/assertions.json", r#"{"assertions": [{"id": "a1"}]}"#),
            ("protocol/data_contracts.json", r#"{"schema": "wrong/1", "status_vocabulary": ["active"], "rule_prefixes": ["check"], "contracts": [{"id": "c1", "artifact": "docs/norm-a.md", "status": "active", "owner": "o", "freshness": "f", "quality_rule": "check1"}, {"id": "c1", "artifact": "no/such", "status": "bogus", "owner": "", "freshness": "", "quality_rule": "assertion:nope"}, {"id": "c3", "artifact": "docs/norm-a.md", "status": "active", "owner": "o", "freshness": "f", "quality_rule": "不能解析"}, {"id": "c4", "artifact": "docs/norm-b.md", "status": "active", "owner": "o", "freshness": "f", "quality_rule": "assertion:a1"}]}"#),
            ("protocol/normative.json", r#"{"schema": "wrong/1", "normative": [{"path": ""}, "docs/missing.md", {"path": "docs/norm-a.md"}, {"path": "docs/norm-a.md", "covered_by": ["check99"]}, {"path": "docs/norm-b.md", "covered_by": ["check1"]}, {"path": "docs/ex/one.md"}], "informative": ["docs/ex/**", "docs/none/**"]}"#),
            ("protocol/other.json", r#"{"words": ["x", "z"]}"#),
            ("protocol/vocabularies.json", r#"{"schema": "wrong/1", "status_vocabulary": ["active"], "probe_kinds": ["literal", "json_path", "python_attr"], "schemes": [{"id": "v-literal", "status": "active", "values": ["a", "b"], "probe": {"kind": "literal"}}, {"id": "v-literal", "status": "active", "values": ["a"], "probe": {"kind": "literal"}}, {"id": "v-status", "status": "bogus", "values": ["a", "b"], "probe": {"kind": "literal"}}, {"id": "v-dup", "status": "active", "values": ["a", "a"], "aliases": ["a"], "probe": {"kind": "literal"}}, {"id": "v-kind", "status": "active", "values": ["a", "b"], "probe": {"kind": "nope"}}, {"id": "v-broken", "status": "active", "values": ["a", "b"], "probe": {"kind": "json_path", "file": "protocol/other.json", "path": "nope.deep"}}, {"id": "v-drift", "status": "active", "values": ["x", "y"], "probe": {"kind": "json_path", "file": "protocol/other.json", "path": "words"}}, {"id": "v-attr", "status": "deprecated", "values": ["tutorial", "how-to", "reference", "explanation"], "probe": {"kind": "python_attr", "module": "core.doc_hygiene", "attr": "KINDS"}}]}"#),
            ("verify.sh", r#"#!/bin/bash
check1(){
  true
}
check2(){
  true
}
"#),
        ] {
            std::fs::write(root.join(rel), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_modeling_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, WANT_MD_ISSUES, "逐条消息与次序都须与真源一致");
        assert_eq!(got.schemes, 7);
        assert_eq!(got.normative, 6);
        assert_eq!(got.informative_files, 2);
        assert_eq!(got.contracts, 3);
    }

}
