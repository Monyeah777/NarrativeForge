//! 图书馆入库许可证门（`license_gate`）—— 与真源 `desktop/src/core/license_gate.py` 对账。
//!
//! 真源动机（内部差距实证）：library 登记表只有 编号/标题/形态/投稿人/日期/一句话，**无许可列**；
//! 第三方投稿的共享条款只写在投稿须知里，入库产物与登记行都不承载它。
//!
//! 判据：每条登记行的「许可」列必须有值且取值合规（**走 SPDX 表达式词法判据**，单一 id 是特例）；
//! `未声明` 允许存在但计入 WARN 挂账；条目文件应带内联许可声明，缺失/双源不一致同样记 WARN。
//!
//! 表达式解析只做**词法级**判定（id 在册 + 运算符合法 + 括号配平），不做许可兼容性推断
//! ——那是法律判断，不是门禁的活。
//!
//! 本模块是 `nf verify-report` 的 `license` 判据，**不单独开 CLI 面**。

use crate::pyjson::Json;
use crate::pyval::py_str;
use std::path::Path;

pub const INDEX_REL: &str = "library/INDEX.md";
pub const UNDECLARED: &str = "未声明";
pub const ALLOWED: [&str; 10] = [
    "MIT",
    "Apache-2.0",
    "BSD-3-Clause",
    "BSD-2-Clause",
    "ISC",
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "CC0-1.0",
    "专有",
    "未声明",
];
const OPERATORS: [&str; 3] = ["AND", "OR", "WITH"];

fn expr_token() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"\(|\)|[A-Za-z0-9.+\-]+").expect("表达式词法正则固定合法")
    })
}

fn ws_re() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"\s+").expect("空白正则固定合法"))
}

/// 真源 `expression_issue`：SPDX 表达式词法体检（空串 = 合规）。
pub fn expression_issue(expr: &str) -> String {
    let text = expr.trim().to_string();
    if text.is_empty() {
        return "许可为空".to_string();
    }
    if text == "专有" || text == UNDECLARED {
        return String::new();
    }
    let tokens: Vec<String> = expr_token()
        .find_iter(&text)
        .map(|m| m.as_str().to_string())
        .collect();
    if tokens.join("") != ws_re().replace_all(&text, "") {
        return "含非法字符（修复指引：SPDX id / AND / OR / WITH / 括号 / `+` 之外不得出现）"
            .to_string();
    }
    if text.matches('(').count() != text.matches(')').count() {
        return "括号不配平".to_string();
    }
    let atoms: Vec<String> = tokens
        .iter()
        .filter(|t| *t != "(" && *t != ")")
        .cloned()
        .collect();
    if atoms.is_empty() {
        return "表达式无许可 id".to_string();
    }
    for a in &atoms {
        if OPERATORS.contains(&a.as_str()) {
            continue;
        }
        let base = a.strip_suffix('+').unwrap_or(a);
        if ALLOWED.contains(&base) || base.starts_with("LicenseRef-") {
            continue;
        }
        let mut allowed: Vec<&str> = ALLOWED.iter().copied().filter(|x| *x != UNDECLARED).collect();
        allowed.sort();
        return format!(
            "许可 id 不在词表：{}（允许：{}；或用 `LicenseRef-<自定义>` 显式自造）",
            a,
            allowed.join("、")
        );
    }
    for (i, tok) in tokens.iter().enumerate() {
        if !OPERATORS.contains(&tok.as_str()) {
            continue;
        }
        if i == 0 || i == tokens.len() - 1 {
            return format!("运算符 {} 出现在表达式首/尾（缺操作数）", tok);
        }
        if OPERATORS.contains(&tokens[i - 1].as_str()) || tokens[i - 1] == "(" {
            return format!("运算符 {} 前缺少操作数", tok);
        }
        if tokens[i + 1] == ")" {
            return format!("运算符 {} 后缺少操作数", tok);
        }
    }
    String::new()
}

pub struct IndexRow {
    pub id: String,
    pub license: String,
}

/// 真源 `parse_index`。
pub fn parse_index(root: &Path) -> Vec<IndexRow> {
    static ROW: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let row_re = ROW.get_or_init(|| {
        regex::Regex::new(r"^\|\s*(NF-[A-Za-z0-9\-]+)\s*\|").expect("登记行正则固定合法")
    });
    let path = root.join(INDEX_REL);
    let Ok(text) = std::fs::read_to_string(&path) else { return Vec::new() };
    let mut rows = Vec::new();
    for ln in text.lines() {
        if !row_re.is_match(ln) {
            continue;
        }
        let cells: Vec<String> = ln
            .trim()
            .trim_matches('|')
            .split('|')
            .map(|c| c.trim().to_string())
            .collect();
        if cells.len() < 6 {
            continue;
        }
        rows.push(IndexRow {
            id: cells[0].clone(),
            // 真源 `c[5] if len(c) >= 7 else ""` —— 注意是**列数**门槛，不是取值判断
            license: if cells.len() >= 7 { cells[5].clone() } else { String::new() },
        });
    }
    rows
}

/// 真源 `inline_license`：条目文件内联许可声明（缺 = 空串）。
pub fn inline_license(root: &Path, entry_id: &str) -> String {
    static INLINE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = INLINE.get_or_init(|| {
        regex::Regex::new(r"(?m)^\s*(?:>\s*)?(?:许可|license)\s*[:：]\s*([^\s（(]+)")
            .expect("内联许可正则固定合法")
    });
    let path = root.join("library").join(format!("{}.md", entry_id));
    if !path.exists() {
        return String::new();
    }
    let text = std::fs::read_to_string(&path).unwrap_or_default();
    // 真源 `fh.read(4000)` 按**字符**读
    let head: String = text.chars().take(4000).collect();
    re.captures(&head)
        .map(|c| c[1].trim().to_string())
        .unwrap_or_default()
}

pub struct LicenseScan {
    pub issues: Vec<String>,
    pub stats: Json,
}

/// 真源 `scan` → `(issues, stats)`（warns 在 stats 内）。
pub fn scan(root: &Path) -> LicenseScan {
    let mut issues: Vec<String> = Vec::new();
    let mut warnings: Vec<String> = Vec::new();
    let rows = parse_index(root);
    let mut undeclared: Vec<String> = Vec::new();
    let mut unknown: Vec<String> = Vec::new();
    let mut no_inline: Vec<String> = Vec::new();
    let mut mismatched: Vec<String> = Vec::new();

    for r in &rows {
        let lic = r.license.clone();
        if lic.is_empty() {
            issues.push(format!(
                "登记行缺「许可」列值：{}（修复指引：按许可词表补值，投稿人未回填写「{}」）",
                r.id, UNDECLARED
            ));
            continue;
        }
        let expr_bad = expression_issue(&lic);
        if !expr_bad.is_empty() {
            let mut allowed: Vec<&str> = ALLOWED.iter().copied().collect();
            allowed.sort();
            issues.push(format!(
                "许可取值不合规：{} = {}（{}；允许：{}）",
                r.id,
                lic,
                expr_bad,
                allowed.join("、")
            ));
            unknown.push(r.id.clone());
            continue;
        }
        if lic == UNDECLARED {
            warnings.push(format!("许可未声明（待投稿人确认）：{}", r.id));
            undeclared.push(r.id.clone());
        }
        let inner = inline_license(root, &r.id);
        if inner.is_empty() {
            warnings.push(format!(
                "条目文件缺内联许可声明：{}（修复指引：文件头补 「> 许可：<SPDX>」）",
                r.id
            ));
            no_inline.push(r.id.clone());
        } else if inner != lic {
            warnings.push(format!(
                "许可双源不一致：{} 登记={} 文件={}",
                r.id, lic, inner
            ));
            mismatched.push(r.id.clone());
        }
    }

    let stats = Json::Object(vec![
        ("entries".to_string(), Json::Int(rows.len() as i64)),
        (
            "declared".to_string(),
            Json::Int((rows.len() - undeclared.len() - unknown.len()) as i64),
        ),
        (
            "undeclared".to_string(),
            Json::Array(undeclared.into_iter().map(Json::Str).collect()),
        ),
        (
            "unknown".to_string(),
            Json::Array(unknown.into_iter().map(Json::Str).collect()),
        ),
        (
            "no_inline".to_string(),
            Json::Array(no_inline.into_iter().map(Json::Str).collect()),
        ),
        (
            "mismatched".to_string(),
            Json::Array(mismatched.into_iter().map(Json::Str).collect()),
        ),
        (
            "warnings".to_string(),
            Json::Array(warnings.into_iter().map(Json::Str).collect()),
        ),
    ]);
    let _ = py_str(None);
    LicenseScan { issues, stats }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn single_ids_are_the_trivial_case_of_expressions() {
        assert_eq!(expression_issue("MIT"), "");
        assert_eq!(expression_issue("未声明"), "");
        assert_eq!(expression_issue("专有"), "");
        assert!(!expression_issue("Frobnicate-9.9").is_empty());
    }

    #[test]
    fn spdx_expressions_are_lexically_checked() {
        assert_eq!(expression_issue("MIT OR Apache-2.0"), "");
        // ⚠️ 反直觉但**与真源一致**（11/11 实测核对过）：`WITH` 运算符本身合法，
        // 但 `WITH` 之后的 **SPDX 例外 id 不在词表里**——真源只认 `ALLOWED` ∪ `LicenseRef-*`。
        // 故 `Apache-2.0 WITH LLVM-exception` 是**判红**的。照抄，不要"顺手修好"。
        assert!(expression_issue("Apache-2.0 WITH LLVM-exception").contains("不在词表"));
        assert_eq!(expression_issue("LicenseRef-MyCustom"), "");
        assert!(expression_issue("MIT OR").contains("首/尾"));
        assert!(expression_issue("MIT AND AND Apache-2.0").contains("缺少操作数"));
        assert!(expression_issue("(MIT").contains("括号不配平"));
        assert!(expression_issue("MIT $ Apache").contains("含非法字符"));
    }

    #[test]
    fn allowed_message_includes_undeclared_but_id_message_excludes_it() {
        // 真源两处口径不同：`许可 id 不在词表` 排除 未声明；`允许：` 全列
        let a = expression_issue("Nope");
        assert!(!a.contains("未声明"), "id 提示不应列 未声明：{}", a);
        let b = expression_issue("Nope");
        assert!(b.contains("允许："));
    }
    /// ===== 分支级差分判据（期望值由 `tools/gen_license_branches.py` 从真源生成）=====
    ///
    /// 真语料上许可门是**全绿**的 ⇒ 只靠契约对账核不到任何错误分支。
    /// 本夹具逐分支踩：空许可列(FAIL) / 表达式越词表(FAIL) / `未声明`(WARN) / 无内联(WARN) /
    /// 双源不一致(WARN) / 单 id 全绿 / SPDX 表达式合法 / 单元格过少不计入。
    const WANT_LIC_ISSUES: [&str; 2] = [
        "登记行缺「许可」列值：NF-1（修复指引：按许可词表补值，投稿人未回填写「未声明」）",
        "许可取值不合规：NF-2 = Frobnicate（许可 id 不在词表：Frobnicate（允许：Apache-2.0、BSD-2-Clause、BSD-3-Clause、CC-BY-4.0、CC-BY-SA-4.0、CC0-1.0、ISC、MIT、专有；或用 `LicenseRef-<自定义>` 显式自造）；允许：Apache-2.0、BSD-2-Clause、BSD-3-Clause、CC-BY-4.0、CC-BY-SA-4.0、CC0-1.0、ISC、MIT、专有、未声明）",
    ];

    fn build_license_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("license-branches");
        std::fs::create_dir_all(root.join("library")).unwrap();
        std::fs::write(root.join("library/INDEX.md"), r#"# 馆藏

| 编号 | 标题 | 形态/领域 | 投稿人 | 入库日期 | 许可 | 分级 | 状态 | 一句话 |
|---|---|---|---|---|---|---|---|---|
| NF-1 | 缺许可列 | t | a | 2026-01-01 |  | g | active | s |
| NF-2 | 表达式非法 | t | a | 2026-01-01 | Frobnicate | g | active | s |
| NF-3 | 未声明 | t | a | 2026-01-01 | 未声明 | g | active | s |
| NF-4 | 无内联 | t | a | 2026-01-01 | MIT | g | active | s |
| NF-5 | 双源不一致 | t | a | 2026-01-01 | MIT | g | active | s |
| NF-6 | 全绿 | t | a | 2026-01-01 | Apache-2.0 | g | active | s |
| NF-7 | 表达式合法 | t | a | 2026-01-01 | MIT OR Apache-2.0 | g | active | s |
| NF-8 |
"#).unwrap();
        for (name, body) in [
            ("NF-1.md", r#"# x
"#),
            ("NF-2.md", r#"# x
"#),
            ("NF-3.md", r#"> 许可：未声明
"#),
            ("NF-4.md", r#"# x
"#),
            ("NF-5.md", r#"> 许可：BSD-3-Clause
"#),
            ("NF-6.md", r#"> 许可：Apache-2.0
"#),
            ("NF-7.md", r#"# x
"#),
        ] {
            std::fs::write(root.join("library").join(name), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_license_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, WANT_LIC_ISSUES, "逐条消息与次序都须与真源一致");
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "entries": 7, "declared": 5,
                "undeclared": ["NF-3"], "unknown": ["NF-2"],
                "no_inline": ["NF-4", "NF-7"], "mismatched": ["NF-5"],
                "warnings": ["许可未声明（待投稿人确认）：NF-3", "条目文件缺内联许可声明：NF-4（修复指引：文件头补 「> 许可：<SPDX>」）", "许可双源不一致：NF-5 登记=MIT 文件=BSD-3-Clause", "条目文件缺内联许可声明：NF-7（修复指引：文件头补 「> 许可：<SPDX>」）"]
            }))
            .unwrap()
        ));
    }

}
