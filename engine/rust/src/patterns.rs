//! Pattern 包品类门禁（`patterns`）—— 与真源 `desktop/src/core/patterns.py` 对账。
//!
//! 真源 = 每个包自己的 frontmatter；`patterns/INDEX.md` 的登记表是**投影**。
//! 判据：必填字段齐、id 与目录名一致、id 唯一、status 在词表、rules 非空、
//! **`applies_to` 每条必须在仓库里匹配到真实件**（否则这条 pattern 指向空气）、
//! evidence 可解析；另加**投影一致**（登记表 == 实时重算）。

use crate::mdblocks;
use crate::pyjson::Json;
use crate::pyval::{get, obj_is_empty, plain_str, py_str, py_truthy};
use std::path::Path;

pub const GLOB: &str = "patterns/*/PATTERN.md";
pub const INDEX_REL: &str = "patterns/INDEX.md";
pub const BEGIN: &str = "<!-- BEGIN GENERATED: patterns-index -->";
pub const END: &str = "<!-- END GENERATED: patterns-index -->";
const REQUIRED: [&str; 6] = ["id", "name", "status", "scope", "applies_to", "rules"];
const STATUSES: [&str; 2] = ["active", "deprecated"];

struct Entry {
    dir: String,
    fm: Json,
}

/// 真源 `_as_list`：list → 逐项 str；否则真值 → `[str(v)]`，假值 → `[]`。
fn as_list(v: Option<&Json>) -> Vec<String> {
    match v {
        Some(Json::Array(a)) => a.iter().map(plain_str).collect(),
        Some(other) if py_truthy(other) => vec![plain_str(other)],
        _ => Vec::new(),
    }
}

/// 真源 `entries`：按 id（缺则目录名）排序。
fn entries(root: &Path) -> Vec<Entry> {
    let mut out: Vec<Entry> = crate::glob::expand(root, GLOB)
        .into_iter()
        .map(|rel| {
            let text = std::fs::read_to_string(root.join(&rel)).unwrap_or_default();
            let (fm, _body) = mdblocks::parse_frontmatter(&text);
            let dir = rel
                .rsplit('/')
                .nth(1)
                .unwrap_or("")
                .to_string();
            Entry { dir, fm }
        })
        .collect();
    out.sort_by_key(|e| {
        let id = get(&e.fm, "id");
        if py_truthy(id.unwrap_or(&Json::Null)) {
            plain_str(id.unwrap())
        } else {
            e.dir.clone()
        }
    });
    out
}

fn split_glob_ok(s: &str) -> bool {
    s.chars().any(|c| c == '*' || c == '?' || c == '[')
}

fn is_check(s: &str) -> bool {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| regex::Regex::new(r"^check\d+$").expect("判据引用正则固定合法"));
    re.is_match(s)
}

/// 真源 `scan` → `(issues, patterns 条数)`。
pub fn scan_issues(root: &Path) -> (Vec<String>, usize) {
    let mut issues = Vec::new();
    let rows = entries(root);
    if rows.is_empty() {
        return (vec![format!("未发现任何 pattern 包（{}）", GLOB)], 0);
    }
    let mut seen: Vec<(String, String)> = Vec::new();
    for e in &rows {
        let fm = &e.fm;
        let d = &e.dir;
        if obj_is_empty(fm) {
            issues.push(format!("{} 缺 frontmatter（修复指引：见 patterns/README.md）", d));
            continue;
        }
        for k in REQUIRED {
            let v = get(fm, k);
            // 真源 `fm.get(k) or fm.get(k) == []` —— **空列表算"已填"**
            let present = v.map(py_truthy).unwrap_or(false)
                || matches!(v, Some(Json::Array(a)) if a.is_empty());
            if !present {
                issues.push(format!("{} 缺必填字段：{}", d, k));
            }
        }
        let pid = py_str(get(fm, "id"));
        if !pid.is_empty() && pid != *d {
            issues.push(format!("{} 的 id 与目录名不一致：{} vs {}", d, pid, d));
        }
        if !pid.is_empty() {
            if let Some((_, prev)) = seen.iter().find(|(p, _)| *p == pid) {
                issues.push(format!("pattern id 重复：{}（{} / {}）", pid, prev, d));
            }
            seen.push((pid, d.clone()));
        }
        let st = py_str(get(fm, "status"));
        if !st.is_empty() && !STATUSES.contains(&st.as_str()) {
            issues.push(format!("{} status 越词表：{}（{}）", d, st, STATUSES.join("/")));
        }
        if as_list(get(fm, "rules")).is_empty() {
            issues.push(format!("{} 的 rules 为空（pattern 必须有可执行规则）", d));
        }
        for pat in as_list(get(fm, "applies_to")) {
            let pat_clean = pat.trim().to_string();
            if split_glob_ok(&pat_clean) {
                if crate::glob::expand_any(root, &pat_clean).is_empty() {
                    issues.push(format!(
                        "{} 的 applies_to 通配无匹配：{}（修复指引：指向仓库内真实文件）",
                        d, pat_clean
                    ));
                }
            } else if !root.join(&pat_clean).exists() {
                issues.push(format!("{} 的 applies_to 路径不存在：{}", d, pat_clean));
            }
        }
        for item in as_list(get(fm, "evidence")) {
            let s = item.trim().to_string();
            let looks_path = s.starts_with("docs/")
                || s.starts_with("desktop/")
                || s.starts_with("protocol/")
                || s.starts_with("library/");
            if is_check(&s) {
                continue;
            }
            if looks_path && !root.join(&s).exists() {
                // warns（本契约只看 issues）——此处不算 issues
            } else if s.is_empty() {
                // warns
            }
        }
    }
    (issues, rows.len())
}

/// 真源 `render_index`：投影表（`check_projection` 与它逐字比对）。
pub fn render_index(root: &Path) -> String {
    let mut out: Vec<String> = vec![
        BEGIN.to_string(),
        String::new(),
        "## Pattern 登记表（由各包 frontmatter 生成，勿手改）".to_string(),
        String::new(),
        "| id | 名称 | 状态 | 适用面 | 规则数 |".to_string(),
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
        let scope: Vec<String> = as_list(get(fm, "scope")).into_iter().take(2).collect();
        out.push(format!(
            "| {} | {} | {} | {} | {} |",
            cell("id", e.dir.clone()),
            cell("name", String::new()),
            cell("status", String::new()),
            scope.join("、"),
            as_list(get(fm, "rules")).len()
        ));
    }
    out.push(String::new());
    out.push("> 真源 = 各包 `PATTERN.md` 的 frontmatter；本表为投影（`nf patterns reindex` 重建）。".to_string());
    out.push(String::new());
    out.push(END.to_string());
    out.join("\n")
}

/// 真源 `check_projection`。
pub fn check_projection(root: &Path) -> Vec<String> {
    let p = root.join(INDEX_REL);
    if !p.is_file() {
        return vec![format!("缺 {}（修复指引：nf patterns reindex）", INDEX_REL)];
    }
    let text = std::fs::read_to_string(&p).unwrap_or_default();
    if !text.contains(BEGIN) || !text.contains(END) {
        return vec![format!("{} 缺生成区标记", INDEX_REL)];
    }
    let i = text.find(BEGIN).unwrap_or(0);
    let j = text.find(END).unwrap_or(0) + END.len();
    let cur = &text[i..j];
    if cur == render_index(root) {
        Vec::new()
    } else {
        vec!["patterns 登记表与实时重算不一致（跑 nf patterns reindex）".to_string()]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn globless_applies_to_must_exist() {
        let tmp = crate::testutil::fixture("pat-air");
        std::fs::create_dir_all(tmp.join("patterns/demo")).unwrap();
        std::fs::write(
            tmp.join("patterns/demo/PATTERN.md"),
            "---\nid: demo\nname: 演示\nstatus: active\nscope: [x]\napplies_to: [no/such/file.py]\nrules: [r]\n---\n"
                .as_bytes(),
        )
        .unwrap();
        let (issues, n) = scan_issues(&tmp);
        assert_eq!(n, 1);
        assert!(
            issues.iter().any(|i| i.contains("applies_to 路径不存在")),
            "指向空气必须判红：{:?}",
            issues
        );
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn empty_list_counts_as_filled_for_required_fields() {
        // 真源 `fm.get(k) or fm.get(k) == []` —— 空列表算已填
        let tmp = crate::testutil::fixture("pat-empty-required");
        std::fs::create_dir_all(tmp.join("patterns/demo")).unwrap();
        std::fs::write(
            tmp.join("patterns/demo/PATTERN.md"),
            "---\nid: demo\nname: 演示\nstatus: active\nscope: []\napplies_to: []\nrules: []\n---\n"
                .as_bytes(),
        )
        .unwrap();
        let (issues, _) = scan_issues(&tmp);
        assert!(
            !issues.iter().any(|i| i.contains("缺必填字段")),
            "空列表不得算缺字段：{:?}",
            issues
        );
        let _ = std::fs::remove_dir_all(&tmp);
    }    // >>> GENERATED by tools/gen_patterns_branches.py（勿手改；重跑生成器覆盖本段）

    /// ===== 分支级差分判据（期望值由 `tools/gen_patterns_branches.py` 从真源生成）=====
    ///
    /// 三场景：kitchen（逐分支）/ 撞号 / 无包。分支：缺 frontmatter / 缺必填 / id 与目录名不一致 /
    /// id 重复 / status 越词表 / rules 为空 / applies_to 通配无匹配 / applies_to 路径不存在 /
    /// evidence 缺失(warn) / evidence 空项(warn) / evidence 指向不存在(warn) / 无包。
    const PAT_KITCHEN: &str = r#"---
id: 别的名字
name: kitchen
status: 越词表
applies_to:
  - zzz/**/*.md
  - no/such/path.md
rules: []
---
# kitchen
"#;
    const PAT_GREEN: &str = r#"---
id: p3
name: 全绿
status: active
scope: [s]
applies_to:
  - docs/real.md
rules:
  - 规则一
evidence:
  - check1
  - docs/real.md
---
# green
"#;
    const PAT_DUP: &str = r#"---
id: p3
name: 与 p3 撞号
status: active
scope: [s]
applies_to:
  - docs/real.md
rules:
  - 规则
evidence:
  - check1
---
# dup
"#;
    const PAT_EV: &str = r#"---
id: p5
name: 证据面
status: deprecated
scope: [s]
applies_to:
  - docs/real.md
rules:
  - 规则
evidence:
  -
  - docs/nope.md
---
# ev
"#;
    const PAT_NOFM: &str = r#"# 没有 frontmatter
"#;

    fn build_patterns_fixture(scenario: &str, dirs: &[(&str, &str)]) -> std::path::PathBuf {
        let root = crate::testutil::fixture(&format!("patterns-branches-{}", scenario));
        std::fs::create_dir_all(root.join("docs")).unwrap();
        std::fs::write(root.join("docs/real.md"), "# real\n").unwrap();
        std::fs::write(root.join("verify.sh"), "#!/bin/bash\ncheck1(){\n  true\n}\n").unwrap();
        for (d, body) in dirs {
            let p = root.join("patterns").join(d);
            std::fs::create_dir_all(&p).unwrap();
            std::fs::write(p.join("PATTERN.md"), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_in_all_three_scenarios() {
        for (scenario, dirs, want_issues, want_warns, want_n) in [
            (
                "kitchen",
                &[("p2", PAT_KITCHEN), ("p3", PAT_GREEN), ("p5", PAT_EV), ("p1", PAT_NOFM)][..],
                &["p1 缺 frontmatter（修复指引：见 patterns/README.md）", "p2 缺必填字段：scope", "p2 的 id 与目录名不一致：别的名字 vs p2", "p2 status 越词表：越词表（active/deprecated）", "p2 的 rules 为空（pattern 必须有可执行规则）", "p2 的 applies_to 通配无匹配：zzz/**/*.md（修复指引：指向仓库内真实文件）", "p2 的 applies_to 路径不存在：no/such/path.md"] as &[&str],
                &["p5 的 evidence 指向不存在的件：docs/nope.md", "p2 缺 evidence（可证性弱：无法回溯规则来源）"] as &[&str],
                4,
            ),
            (
                "dup",
                &[("p3", PAT_GREEN), ("p3b", PAT_DUP)][..],
                &["p3b 的 id 与目录名不一致：p3 vs p3b", "pattern id 重复：p3（p3 / p3b）"] as &[&str],
                &[] as &[&str],
                2,
            ),
            ("nopkgs", &[][..], &["未发现任何 pattern 包（patterns/*/PATTERN.md）"] as &[&str], &[] as &[&str], 0),
        ] {
            let root = build_patterns_fixture(scenario, dirs);
            let (issues, n) = scan_issues(&root);
            assert_eq!(issues, want_issues, "场景 {} 的 issues", scenario);
            assert_eq!(n, want_n, "场景 {} 的包数", scenario);
            let _ = want_warns;   // 真源 warns 在本面无消费者，未纳入移植面
        }
    }
    // <<< GENERATED

}
