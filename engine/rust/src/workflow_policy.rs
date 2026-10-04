//! 工作流供应链策略（`workflow_policy`）—— 与真源 `desktop/src/core/workflow_policy.py` 对账。
//!
//! 外部标准只作**机制借鉴**（ossf/scorecard 的 Pinned-Dependencies / Token-Permissions；
//! FAIR4RS 的 R 面），判据本体在仓库内可核：
//! ① 每条 `uses:` 须钉 **40 位提交 SHA**（`@v4` 这类可变引用判 FAIL；本地 `./…` 豁免）；
//! ② 每个工作流须有**显式** `permissions:` 且不得 `write-all`；
//! ③ 每个工作流须声明 job 级 `timeout-minutes`（**挂死有界**——GitHub 默认 6h，
//!    挂死的 job 会把 runner 占满并挤掉后续定时任务）；
//! ④ `.github/requirements-*.txt` 每条依赖须钉 `==` 具体版本。
//!
//! 本模块是 `nf verify-report` 的 `workflow_policy` 判据，**不单独开 CLI 面**。

use crate::pyjson::Json;
use std::path::Path;

pub const WORKFLOWS_REL: &str = ".github/workflows";

fn re_uses() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| {
        regex::Regex::new(r"^\s*(?:-\s*)?uses:\s*(\S+)(.*)$").expect("uses 正则固定合法")
    })
}

fn re_sha() -> &'static regex::Regex {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    RE.get_or_init(|| regex::Regex::new(r"^[0-9a-f]{40}$").expect("SHA 正则固定合法"))
}

/// 真源 `workflows`：仓库相对、排序（按全路径）。
pub fn workflows(root: &Path) -> Vec<String> {
    let d = root.join(WORKFLOWS_REL);
    if !d.is_dir() {
        return Vec::new();
    }
    let mut out: Vec<String> = crate::glob::expand(root, ".github/workflows/*")
        .into_iter()
        .filter(|rel| rel.ends_with(".yml") || rel.ends_with(".yaml"))
        .collect();
    out.sort();
    out
}

/// 真源 `_timeout_issues`。
fn timeout_issues(rel: &str, text: &str) -> Vec<String> {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| {
        regex::Regex::new(r"(?m)^\s*timeout-minutes:\s*\d+\s*(?:#.*)?$")
            .expect("timeout 正则固定合法")
    });
    if re.is_match(text) {
        return Vec::new();
    }
    vec![format!(
        "{} 未声明 job 级 `timeout-minutes`（修复指引：在该 job 的 `runs-on` 下一行加 `timeout-minutes: <分钟>`；挂死不许占满默认 6h）",
        rel
    )]
}

/// 真源 `_pin_issues`。
fn pin_issues(rel: &str, text: &str) -> Vec<String> {
    let mut out = Vec::new();
    for (i, line) in text.lines().enumerate() {
        let Some(c) = re_uses().captures(line) else { continue };
        let ref_ = c[1].trim_end_matches(',').trim_matches(|ch| ch == '"' || ch == '\'').to_string();
        if ref_.starts_with("./") {
            continue;
        }
        if !ref_.contains('@') {
            out.push(format!(
                "{}:{} uses 缺版本引用：{}（修复指引：钉 owner/repo@<40 位提交 SHA>）",
                rel,
                i + 1,
                ref_
            ));
            continue;
        }
        let rev = ref_.rsplit_once('@').map(|(_, r)| r).unwrap_or("");
        if !re_sha().is_match(rev) {
            let head: String = rev.chars().take(24).collect();
            let owner = ref_.split('@').next().unwrap_or("");
            out.push(format!(
                "{}:{} 未钉提交 SHA：{}@{}（修复指引：钉 40 位 SHA——`@v4` 这类可变引用可被上游改写；改法见 ossf/scorecard docs/checks.md §Pinned-Dependencies）",
                rel,
                i + 1,
                owner,
                head
            ));
        }
    }
    out
}

/// 真源 `_perm_issues`。
fn perm_issues(rel: &str, text: &str) -> Vec<String> {
    static TOP: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let top = TOP.get_or_init(|| regex::Regex::new(r"^permissions:\s*").expect("权限行正则固定合法"));
    static IND: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let ind = IND.get_or_init(|| regex::Regex::new(r"^\s+permissions:\s*").expect("权限行正则固定合法"));
    let mut out = Vec::new();
    let perms: Vec<&str> = text
        .lines()
        .filter(|ln| top.is_match(ln) || ind.is_match(ln))
        .collect();
    if perms.is_empty() {
        out.push(format!(
            "{} 缺显式 permissions 段（修复指引：按 ossf/scorecard §Token-Permissions 给 GITHUB_TOKEN 最小权限，如 `permissions:\n  contents: read`）",
            rel
        ));
    } else {
        static WA: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
        let wa = WA.get_or_init(|| regex::Regex::new(r"\bwrite-all\b").expect("write-all 正则固定合法"));
        if perms.iter().any(|ln| wa.is_match(ln)) {
            out.push(format!(
                "{} 使用 write-all（修复指引：改为按需最小集，见 §Token-Permissions）",
                rel
            ));
        }
    }
    out
}

pub struct WfScan {
    pub issues: Vec<String>,
    pub warns: Vec<String>,
    pub stats: Json,
}

/// 真源 `scan` → `(issues, warns, stats)`。
pub fn scan(root: &Path) -> WfScan {
    let mut issues: Vec<String> = Vec::new();
    let mut warns: Vec<String> = Vec::new();
    let files = workflows(root);
    let mut pinned = 0i64;
    for rel in &files {
        let text = std::fs::read_to_string(root.join(rel)).unwrap_or_default();
        issues.extend(pin_issues(rel, &text));
        issues.extend(perm_issues(rel, &text));
        issues.extend(timeout_issues(rel, &text));
        for line in text.lines() {
            let Some(c) = re_uses().captures(line) else { continue };
            let rev = c[1].trim_end_matches(',').rsplit_once('@').map(|(_, r)| r).unwrap_or("");
            if re_sha().is_match(rev) {
                pinned += 1;
                if !c[2].contains('#') {
                    warns.push(format!(
                        "{} 钉了 SHA 但没写版本注释（修复指引：行尾补 `# v4` 一类注释，便于依赖更新）",
                        rel
                    ));
                }
            }
        }
    }
    static PERM: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let perm = PERM.get_or_init(|| {
        regex::Regex::new(r"(?m)^permissions:\s*|^\s+permissions:\s*").expect("权限行正则固定合法")
    });
    let with_explicit = files
        .iter()
        .filter(|rel| {
            std::fs::read_to_string(root.join(rel))
                .map(|t| perm.is_match(&t))
                .unwrap_or(false)
        })
        .count();

    let reqs: Vec<String> = if root.join(".github").is_dir() {
        let mut v = crate::glob::expand(root, ".github/requirements-*.txt");
        v.sort();
        v
    } else {
        Vec::new()
    };
    for rel in &reqs {
        let name = rel.rsplit('/').next().unwrap_or(rel);
        let text = std::fs::read_to_string(root.join(rel)).unwrap_or_default();
        for (i, line) in text.lines().enumerate() {
            let t = line.trim().to_string();
            if t.is_empty() || t.starts_with('#') || t.starts_with('-') {
                continue;
            }
            if !t.contains("==") {
                issues.push(format!(
                    "{}:{} 依赖未钉版本：{}（修复指引：改 `包==版本`——FAIR4RS R 面要求依赖可重建，见 DOI 10.5281/zenodo.6374314 / Scorecard §Pinned-Dependencies）",
                    name,
                    i + 1,
                    t.chars().take(60).collect::<String>()
                ));
            }
        }
    }

    let stats = Json::Object(vec![
        ("workflows".to_string(), Json::Int(files.len() as i64)),
        ("pinned_uses".to_string(), Json::Int(pinned)),
        (
            "with_explicit_permissions".to_string(),
            Json::Int(with_explicit as i64),
        ),
        (
            "requirements_files".to_string(),
            Json::Int(reqs.len() as i64),
        ),
    ]);
    WfScan { issues, warns, stats }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// ===== 分支级差分判据（期望值由 `tools/gen_workflow_expected.py` 从真源生成）=====
    ///
    /// 真语料上 `workflow_policy` **全绿**（0 issues / 0 warns）⇒ 只靠契约对账，**各路判据一条
    /// 也没被核过**。本夹具逐分支踩：未钉 SHA / 缺版本引用 / 本地动作豁免 / 钉了带注释 /
    /// 钉了无注释 / 缺 permissions / write-all / 缺 timeout / 全绿 / 非 .yml 忽略 /
    /// requirements 已钉与未钉（`-` 开头跳过）。
    const WF_FILES: [(&str, &str); 5] = [
        ("clean.yml", r#"name: clean
on: push
permissions:
  contents: read
jobs:
  j:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v4
"#),
        ("mixed.yml", r#"name: mixed
on: push
permissions:
  contents: read
jobs:
  j:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python
      - uses: ./local-action
      - uses: actions/cache@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v3
      - uses: actions/upload-artifact@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"#),
        ("noperms.yml", r#"name: noperms
on: push
jobs:
  j:
    runs-on: ubuntu-latest
    steps:
      - run: echo hi
"#),
        ("notes.txt", r#"uses: actions/checkout@v4
"#),
        ("writeall.yml", r#"name: wa
on: push
permissions: write-all
jobs:
  j:
    runs-on: ubuntu-latest
    timeout-minutes: 3
    steps:
      - run: echo hi
"#),
    ];
    const WF_REQS: [(&str, &str); 2] = [
        ("requirements-a.txt", r#"pyyaml==6.0
# 注释
-r other.txt
requests
"#),
        ("requirements-b.txt", r#"numpy==1.26.0
"#),
    ];
    const WANT_WF_ISSUES: [&str; 6] = [
        ".github/workflows/mixed.yml:10 未钉提交 SHA：actions/checkout@v4（修复指引：钉 40 位 SHA——`@v4` 这类可变引用可被上游改写；改法见 ossf/scorecard docs/checks.md §Pinned-Dependencies）",
        ".github/workflows/mixed.yml:11 uses 缺版本引用：actions/setup-python（修复指引：钉 owner/repo@<40 位提交 SHA>）",
        ".github/workflows/noperms.yml 缺显式 permissions 段（修复指引：按 ossf/scorecard §Token-Permissions 给 GITHUB_TOKEN 最小权限，如 `permissions:\n  contents: read`）",
        ".github/workflows/noperms.yml 未声明 job 级 `timeout-minutes`（修复指引：在该 job 的 `runs-on` 下一行加 `timeout-minutes: <分钟>`；挂死不许占满默认 6h）",
        ".github/workflows/writeall.yml 使用 write-all（修复指引：改为按需最小集，见 §Token-Permissions）",
        "requirements-a.txt:4 依赖未钉版本：requests（修复指引：改 `包==版本`——FAIR4RS R 面要求依赖可重建，见 DOI 10.5281/zenodo.6374314 / Scorecard §Pinned-Dependencies）",
    ];
    const WANT_WF_WARNS: [&str; 1] = [
        ".github/workflows/mixed.yml 钉了 SHA 但没写版本注释（修复指引：行尾补 `# v4` 一类注释，便于依赖更新）",
    ];

    fn build_wf_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("workflow-branches");
        let wf = root.join(".github/workflows");
        std::fs::create_dir_all(&wf).unwrap();
        for (name, body) in WF_FILES {
            std::fs::write(wf.join(name), body).unwrap();
        }
        for (name, body) in WF_REQS {
            std::fs::write(root.join(".github").join(name), body).unwrap();
        }
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_wf_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, WANT_WF_ISSUES, "逐条消息与次序都须与真源一致");
        assert_eq!(got.warns, WANT_WF_WARNS);
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "workflows": 4, "pinned_uses": 3,
                "with_explicit_permissions": 3, "requirements_files": 2
            }))
            .unwrap()
        ));
    }
}
