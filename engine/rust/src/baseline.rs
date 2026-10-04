//! 基线自描述一致性（`quality_baseline`）—— 与真源 `desktop/src/core/quality_baseline.py` 对账。
//!
//! 以 `verify.sh` 为**单一真值**做四处自洽断言：版本头、check 函数编号连续、
//! README / CHANGELOG / VERSION-MATRIX 三处 `PASS=` 声明齐全。
//!
//! 它同时是 `nf verify-report` 里 `declared.verify_version` 的出处。

use std::path::Path;

/// 真源 `EXPECTED_CHECKS` / `EXPECTED_PASS`（**从真源文件现读**，不硬编码——
/// 真源改了而本线未同步时，`declared` 会立刻对不上，属应然）。
fn expected(root: &Path, name: &str) -> i64 {
    let text = std::fs::read_to_string(root.join("desktop/src/core/quality_baseline.py"))
        .unwrap_or_default();
    crate::stats::py_int_const(&text, name).unwrap_or(0)
}

/// 真源 `getattr(qb, "EXPECTED_*", None)` 的两个声明常量（缺 → `None`，对应 JSON null）。
pub fn constants(root: &Path) -> (Option<i64>, Option<i64>) {
    let text = std::fs::read_to_string(root.join("desktop/src/core/quality_baseline.py"))
        .unwrap_or_default();
    (
        crate::stats::py_int_const(&text, "EXPECTED_CHECKS"),
        crate::stats::py_int_const(&text, "EXPECTED_PASS"),
    )
}

#[derive(Debug, Clone, PartialEq)]
pub struct BaselineStats {
    pub verify_version: String,
    pub checks: i64,
}

/// 真源 `scan` → `(issues, stats)`。`stats = None` 对应真源返回的空字典 `{}`。
pub fn scan(root: &Path) -> (Vec<String>, Option<BaselineStats>) {
    let mut issues: Vec<String> = Vec::new();
    if !root.join("verify.sh").is_file() {
        return (
            vec!["读不到基线真源 verify.sh（修复指引：在 NF 仓库根运行本扫描，或先补齐该件——本模块以它为单一真值做四处自洽断言）".to_string()],
            None,
        );
    }
    let expected_checks = expected(root, "EXPECTED_CHECKS");
    let expected_pass = expected(root, "EXPECTED_PASS");

    let verify_text = std::fs::read_to_string(root.join("verify.sh")).unwrap_or_default();
    static VRE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let vre = VRE.get_or_init(|| regex::Regex::new(r"# 版本 : (v\d+\.\d+)").expect("版本行正则固定合法"));
    let ver = vre.captures(&verify_text).map(|c| c[1].to_string()).unwrap_or_default();

    static CRE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let cre = CRE.get_or_init(|| {
        regex::Regex::new(r"(?m)^check(\d+)\(\)\{").expect("check 定义正则固定合法")
    });
    let mut nums: Vec<i64> = cre
        .captures_iter(&verify_text)
        .filter_map(|c| c[1].parse::<i64>().ok())
        .collect();
    nums.sort_unstable();
    nums.dedup();
    let n_checks = nums.len() as i64;

    if ver.is_empty() {
        issues.push("verify.sh 缺版本头（vX.Y）".to_string());
    }
    let want: Vec<i64> = (1..=expected_checks).collect();
    if n_checks != expected_checks || nums != want {
        issues.push(format!("verify.sh check 函数数/编号异常：{}", py_int_list(&nums)));
    }

    // 三处声明：README 要求三串**同时**在场；CHANGELOG / VERSION-MATRIX 数 PASS= 出现次数
    let pass_tok = format!("PASS={}", expected_pass);
    let readme = std::fs::read_to_string(root.join("README.md")).unwrap_or_default();
    let readme_ok = !ver.is_empty()
        && readme.contains(&ver)
        && readme.contains(&format!("check1-{}", expected_checks))
        && readme.contains(&pass_tok);
    let changelog = std::fs::read_to_string(root.join("CHANGELOG.md")).unwrap_or_default();
    let head = changelog.split("\n## [2.8.0]").next().unwrap_or("").to_string();
    let matrix = std::fs::read_to_string(root.join("VERSION-MATRIX.md")).unwrap_or_default();

    let checks: [(&str, &str, i64); 3] = [
        ("README", "基线句", if readme_ok { 1 } else { 0 }),
        ("CHANGELOG 最新节", "PASS=", count_occurrences(&head, &pass_tok)),
        ("VERSION-MATRIX", "PASS=", count_occurrences(&matrix, &pass_tok)),
    ];
    for (name, what, n) in checks {
        if n < 1 {
            issues.push(format!(
                "{} 缺 {} 声明（预期含 v2.x/check1-{}/PASS={}）",
                name, what, expected_checks, expected_pass
            ));
        }
    }

    (
        issues,
        Some(BaselineStats { verify_version: ver, checks: n_checks }),
    )
}

/// Python `str(list[int])`：`[1, 2, 3]`。
fn py_int_list(v: &[i64]) -> String {
    let inner: Vec<String> = v.iter().map(|x| x.to_string()).collect();
    format!("[{}]", inner.join(", "))
}

fn count_occurrences(hay: &str, needle: &str) -> i64 {
    if needle.is_empty() {
        return 0;
    }
    hay.matches(needle).count() as i64
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn missing_verify_sh_is_reported_without_panicking() {
        let tmp = crate::testutil::fixture("qb-missing");
        let (issues, stats) = scan(&tmp);
        assert_eq!(issues.len(), 1);
        assert!(issues[0].contains("读不到基线真源 verify.sh"));
        assert!(stats.is_none(), "缺件时 stats 应为空字典");
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn int_list_renders_like_python() {
        assert_eq!(py_int_list(&[1, 2, 3]), "[1, 2, 3]");
        assert_eq!(py_int_list(&[]), "[]");
    }

    #[test]
    fn pass_token_is_counted_not_merely_present() {
        assert_eq!(count_occurrences("a PASS=70 b PASS=70", "PASS=70"), 2);
        assert_eq!(count_occurrences("nothing", "PASS=70"), 0);
    }
}
