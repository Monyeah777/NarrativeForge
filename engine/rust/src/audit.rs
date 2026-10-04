//! 审计 / 验收门禁（`audit`）—— 与真源 `desktop/src/core/audit.py` 的 `scan` 对账。
//!
//! 真源：`protocol/audit.json`（规范件）+ `results/audit/*.md`（说明件）。
//! 带审计头的报告：必填齐 / verdict 在词表 / date 格式 / **`subjects` 每条 `路径:sha256` 必须与
//! 当前文件一致**（对象一改，旧审计即失效）/ `accepted_by` 出现则必须有 `accepted_at`（签收双要素）。
//! 无审计头的存量件按 **WARN** 挂账（legacy），不判死。
//!
//! 真源另有 `init_audit` / `check_audit` / `scan_audit` 三个 M_AUDIT 门面（委托 `core.steelman`）——
//! 那是**写面/交互面**，不在本线范围，故未移植。
//!
//! 本模块是 `nf verify-report` 的 `audit` 判据，**不单独开 CLI 面**。

use crate::jsonread;
use crate::mdblocks::parse_frontmatter;
use crate::merkle;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, plain_str, py_str, py_truthy};
use std::path::Path;

pub const DECL_REL: &str = "protocol/audit.json";
pub const GLOB: &str = "results/audit/*.md";
pub const SCHEMA: &str = "nf-audit/1";
const DEFAULT_FIELDS: [&str; 6] = ["id", "date", "scope", "verdict", "auditor", "subjects"];
const DEFAULT_VERDICTS: [&str; 3] = ["pass", "fail", "warn"];

fn is_date(s: &str) -> bool {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| regex::Regex::new(r"^\d{4}-\d{2}-\d{2}$").expect("日期正则固定合法"));
    re.is_match(s)
}

fn decl(root: &Path) -> Option<Json> {
    if !root.join(DECL_REL).is_file() {
        return None;
    }
    jsonread::read_file(root, DECL_REL)
}

struct Row {
    path: String,
    file: String,
    fm: Json,
}

fn entries(root: &Path) -> Vec<Row> {
    crate::glob::expand(root, GLOB)
        .into_iter()
        .map(|rel| {
            let text = std::fs::read_to_string(root.join(&rel)).unwrap_or_default();
            let (fm, _body) = parse_frontmatter(&text);
            let file = rel.rsplit('/').next().unwrap_or(&rel).to_string();
            Row { path: rel, file, fm }
        })
        .collect()
}

struct DocCheck {
    /// 真源 `st.get("legacy")`（空 stats 时为假）
    legacy: bool,
    subjects: i64,
}

/// 真源 `check_doc`。
fn check_doc(root: &Path, rel: &str) -> (Vec<String>, DocCheck) {
    let p = root.join(rel);
    if !p.is_file() {
        return (
            vec![format!("审计件不存在：{}", rel)],
            DocCheck { legacy: false, subjects: 0 },
        );
    }
    let d = decl(root);
    let text = std::fs::read_to_string(&p).unwrap_or_default();
    let (fm, _body) = parse_frontmatter(&text);
    if !py_truthy(get(&fm, "id").unwrap_or(&Json::Null)) {
        return (
            Vec::new(),
            DocCheck { legacy: true, subjects: 0 },
        );
    }
    let mut issues: Vec<String> = Vec::new();
    let fields: Vec<String> = {
        let f: Vec<String> = arr_items(d.as_ref().and_then(|x| get(x, "required_fields")))
            .iter()
            .map(|v| plain_str(v))
            .collect();
        if f.is_empty() { DEFAULT_FIELDS.iter().map(|s| (*s).to_string()).collect() } else { f }
    };
    for k in fields {
        if !py_truthy(get(&fm, &k).unwrap_or(&Json::Null)) {
            issues.push(format!("缺必填字段：{}", k));
        }
    }
    let vocab: Vec<String> = {
        let v: Vec<String> = arr_items(d.as_ref().and_then(|x| get(x, "verdict_vocabulary")))
            .iter()
            .map(|x| plain_str(x))
            .collect();
        if v.is_empty() { DEFAULT_VERDICTS.iter().map(|s| (*s).to_string()).collect() } else { v }
    };
    if !vocab.contains(&py_str(get(&fm, "verdict"))) {
        issues.push(format!(
            "verdict 越词表：{}",
            plain_str(get(&fm, "verdict").unwrap_or(&Json::Null))
        ));
    }
    if !is_date(&py_str(get(&fm, "date"))) {
        issues.push(format!(
            "date 非 YYYY-MM-DD：{}",
            plain_str(get(&fm, "date").unwrap_or(&Json::Null))
        ));
    }

    let subs: Vec<String> = match get(&fm, "subjects") {
        Some(Json::Str(s)) => vec![s.clone()],
        Some(Json::Array(a)) => a.iter().map(plain_str).collect(),
        _ => Vec::new(),
    };
    let mut ok_subs = 0i64;
    for s in subs {
        let t = s.trim().to_string();
        // 真源 `if ":" not in t` + `t.rsplit(":", 1)`：只判「有没有冒号」，
        // 故 `:abc` 会走到「被审对象不存在：」（rel_p 为空串）——不要在此另加特判。
        let Some(pos) = t.rfind(':') else {
            issues.push(format!(
                "subjects 条目格式须为 路径:sha256：{}",
                t.chars().take(40).collect::<String>()
            ));
            continue;
        };
        let rel_p = t[..pos].to_string();
        let want = t[pos + 1..].trim().to_string();
        let sp = root.join(rel_p.replace('\\', "/"));
        if !sp.is_file() {
            issues.push(format!("被审对象不存在：{}", rel_p));
            continue;
        }
        let live = std::fs::read(&sp)
            .map(|b| merkle::hex(&merkle::sha256(&b)))
            .unwrap_or_default();
        if live != want {
            issues.push(format!(
                "被审对象已变，旧审计失效：{}（修复指引：重审并更新 digest）",
                rel_p
            ));
            continue;
        }
        ok_subs += 1;
    }
    if py_truthy(get(&fm, "accepted_by").unwrap_or(&Json::Null))
        && !is_date(&py_str(get(&fm, "accepted_at")))
    {
        issues.push("有 accepted_by 但 accepted_at 缺失或格式非法（签收须双要素）".to_string());
    }
    (issues, DocCheck { legacy: false, subjects: ok_subs })
}

pub struct AuditScan {
    pub issues: Vec<String>,
    pub warns: Vec<String>,
    pub stats: Json,
}

/// 真源 `scan` → `(issues, warns, stats)`。
pub fn scan(root: &Path) -> AuditScan {
    let mut issues: Vec<String> = Vec::new();
    let mut warns: Vec<String> = Vec::new();
    let Some(d) = decl(root) else {
        return AuditScan {
            issues: vec![format!("缺审计协议声明 {}", DECL_REL)],
            warns,
            stats: Json::Object(Vec::new()),
        };
    };
    if py_str(get(&d, "schema")) != SCHEMA {
        issues.push(format!("审计协议 schema 不匹配（期望 {}）", SCHEMA));
    }
    let vv: Vec<String> = arr_items(get(&d, "verdict_vocabulary"))
        .iter()
        .map(|v| plain_str(v))
        .collect();
    if vv != DEFAULT_VERDICTS {
        issues.push("verdict 词表与判据不一致（期望 pass/fail/warn）".to_string());
    }
    if arr_items(get(&d, "rules")).is_empty() {
        issues.push("rules 不得为空（审计纪律必须成文）".to_string());
    }

    let rows = entries(root);
    let mut legacy: Vec<String> = Vec::new();
    let mut subs = 0i64;
    for e in &rows {
        let (i, st) = check_doc(root, &e.path);
        if st.legacy {
            legacy.push(e.file.clone());
            continue;
        }
        let tag = {
            let id = py_str(get(&e.fm, "id"));
            if id.is_empty() { e.file.clone() } else { id }
        };
        issues.extend(i.into_iter().map(|x| format!("{}：{}", tag, x)));
        subs += st.subjects;
    }
    if !legacy.is_empty() {
        let head: Vec<String> = legacy.iter().take(3).cloned().collect();
        warns.push(format!(
            "存量审计件无审计头（legacy，按回合收）：{} 件 —— {}",
            legacy.len(),
            head.join("、")
        ));
    }
    if rows.is_empty() {
        warns.push(format!("暂无审计件（{}）", GLOB));
    }
    let stats = Json::Object(vec![
        ("audits".to_string(), Json::Int(rows.len() as i64)),
        (
            "with_header".to_string(),
            Json::Int((rows.len() - legacy.len()) as i64),
        ),
        ("legacy".to_string(), Json::Int(legacy.len() as i64)),
        ("subjects_ok".to_string(), Json::Int(subs)),
    ]);
    AuditScan { issues, warns, stats }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// ===== 分支级差分判据（期望值由 `tools/gen_audit_branches.py` 从真源生成）=====
    ///
    /// 真语料上 `audit` 的 issues 会随外部状态漂（`verify.sh` 一改，多件审计的 subjects 摘要
    /// 就失效）——**正是"结论依赖外部状态"的面，最不该只靠真语料对账**。
    /// 本夹具逐分支踩：无审计头(legacy) / verdict 越词表 / date 非法 / subjects 无冒号 /
    /// 被审对象不存在 / 摘要不符 / 摘要相符 / accepted_by 缺合法 accepted_at / 签收双要素齐(全绿)。
    const WANT_AUDIT_ISSUES: [&str; 6] = [
        "AUD-0002：verdict 越词表：越词表",
        "AUD-0002：date 非 YYYY-MM-DD：2026/01/01",
        "AUD-0002：subjects 条目格式须为 路径:sha256：没有冒号",
        "AUD-0002：被审对象不存在：no/such.md",
        "AUD-0002：被审对象已变，旧审计失效：subject.md（修复指引：重审并更新 digest）",
        "AUD-0002：有 accepted_by 但 accepted_at 缺失或格式非法（签收须双要素）",
    ];
    const WANT_AUDIT_WARNS: [&str; 1] = [
        "存量审计件无审计头（legacy，按回合收）：1 件 —— A1.md",
    ];

    fn build_audit_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("audit-branches");
        std::fs::create_dir_all(root.join("protocol")).unwrap();
        std::fs::create_dir_all(root.join("results/audit")).unwrap();
        std::fs::write(root.join("protocol/audit.json"), r#"{"schema": "nf-audit/1", "verdict_vocabulary": ["pass", "fail", "warn"], "rules": ["r"]}"#).unwrap();
        std::fs::write(root.join("subject.md"), "hello\n").unwrap();
        let good = crate::merkle::hex(&crate::merkle::sha256(b"hello\n"));
        std::fs::write(root.join("results/audit/A1.md"), r#"---
title: 无编号
---
正文
"#).unwrap();
        let a2 = r#"---
id: AUD-0002
scope: s
verdict: 越词表
date: 2026/01/01
auditor: a
subjects:
  - 没有冒号
  - no/such.md:@Z64@
  - subject.md:@GOOD@
  - subject.md:@O64@
accepted_by: 张三
accepted_at: 不是日期
---
正文
"#
            .replace("@GOOD@", &good)
            .replace("@Z64@", &"0".repeat(64))
            .replace("@O64@", &"1".repeat(64));
        std::fs::write(root.join("results/audit/A2.md"), a2).unwrap();
        let a3 = r#"---
id: AUD-0003
scope: s
verdict: pass
date: 2026-01-02
auditor: a
subjects:
  - subject.md:@GOOD@
accepted_by: 李四
accepted_at: 2026-01-03
---
正文
"#.replace("@GOOD@", &good);
        std::fs::write(root.join("results/audit/A3.md"), a3).unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_audit_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, WANT_AUDIT_ISSUES, "逐条消息与次序都须与真源一致");
        assert_eq!(got.warns, WANT_AUDIT_WARNS);
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "audits": 3, "with_header": 2,
                "legacy": 1, "subjects_ok": 2
            }))
            .unwrap()
        ));
    }
}
