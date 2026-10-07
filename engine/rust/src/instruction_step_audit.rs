//! 指令档步进级可机检审计（`instruction_step_audit`）—— 与真源
//! `desktop/src/core/instruction_step_audit.py` 对账。
//!
//! 对核心指令/规范档审「步骤可执行性」：① 代码内联命令 `nf <sub>` / `python scripts/<file>`
//! 的子命令与脚本必须存在；② 引用仓库路径（`community/ docs/ protocol/ 03_管线库/` 且以
//! `.md/.json/.yaml` 结尾）必须真实存在；③ 未检出引用即 OK（只审可机检步骤，不要求每条 prose 可执行）。
//!
//! **已知近似（如实标注）**：真源 `code.split()[1]` 在 `nf`／`python scripts/` 后无词时抛
//! `IndexError` → `_call` 记 `error`；本线跳过该条。真源语料不触发这条分支。
//!
//! 本模块是 `nf verify-report` 的 `instruction` 判据，**不单独开 CLI 面**。

use crate::pyjson::Json;
use std::path::Path;

pub const AUDIT_DOCS: [&str; 5] = [
    "docs/agent/agent_组装指令包_v0.2.md",
    "docs/45_执行遥测规范.md",
    "docs/45_M2_回合级drill.md",
    "docs/45_M3_techdoc载荷提案.md",
    "docs/44_M2_AI通道内容规范.md",
];

#[derive(Debug, Clone, PartialEq)]
pub struct StepStats {
    pub docs: usize,
    pub steps: usize,
}

impl StepStats {
    pub fn to_json(&self) -> Json {
        Json::Object(vec![
            ("docs".to_string(), Json::Int(self.docs as i64)),
            ("steps".to_string(), Json::Int(self.steps as i64)),
        ])
    }
}

/// 真源 `scan` → `(issues, stats)`；`stats = None` 对应真源的空字典。
pub fn scan(root: &Path) -> (Vec<String>, Option<StepStats>) {
    let mut issues: Vec<String> = Vec::new();
    if !root.join("scripts/nf.py").is_file() {
        return (
            vec!["读不到 CLI 真源 scripts/nf.py（修复指引：在 NF 仓库根运行本扫描，或先补齐该件——本扫描要拿它当子命令面的单一真值）".to_string()],
            None,
        );
    }
    let nf_text = std::fs::read_to_string(root.join("scripts/nf.py")).unwrap_or_default();
    static SUBS: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let subs_re = SUBS.get_or_init(|| {
        regex::Regex::new(r#"add_parser\(\s*"([^"]+)""#).expect("子命令正则固定合法")
    });
    let nf_subs: std::collections::BTreeSet<String> =
        subs_re.captures_iter(&nf_text).map(|c| c[1].to_string()).collect();

    static CMD: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let cmd_re = CMD.get_or_init(|| {
        regex::Regex::new(r"`([^`\n]{1,160})`").expect("内联命令正则固定合法")
    });
    static REPO_PATH: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let repo_re = REPO_PATH.get_or_init(|| {
        regex::Regex::new(r"(?:community|docs|protocol|03_管线库)/").expect("仓库路径正则固定合法")
    });

    let mut steps = 0usize;
    for rel in AUDIT_DOCS {
        let path = root.join(rel);
        if !path.exists() {
            issues.push(format!("{} 缺失（审计清单内档须在场）", rel));
            continue;
        }
        let text = std::fs::read_to_string(&path).unwrap_or_default();
        for c in cmd_re.captures_iter(&text) {
            let code = c[1].trim().to_string();
            if let Some(rest) = code.strip_prefix("nf ") {
                steps += 1;
                let sub = rest.split_whitespace().next().unwrap_or("");
                if !nf_subs.contains(sub) {
                    issues.push(format!("{}: 引用未知子命令 nf {}", rel, sub));
                }
            } else if let Some(rest) = code.strip_prefix("python scripts/") {
                steps += 1;
                let fname = rest.split_whitespace().next().unwrap_or("").trim_start_matches("./");
                if !root.join(fname).exists() {
                    issues.push(format!("{}: 引用脚本不存在 {}", rel, fname));
                }
            } else if repo_re.is_match(&code)
                && (code.ends_with(".md") || code.ends_with(".json") || code.ends_with(".yaml"))
            {
                steps += 1;
                if !root.join(&code).exists() {
                    issues.push(format!("{}: 引用路径不存在 {}", rel, code));
                }
            }
        }
    }
    (
        issues,
        Some(StepStats { docs: AUDIT_DOCS.len(), steps }),
    )
}
