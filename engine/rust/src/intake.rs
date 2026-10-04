//! 投稿闸门声明的一致性门禁（`intake`）—— 与真源 `desktop/src/core/intake.py` 对账。
//!
//! **声明驱动的三方一致**：① 声明件 `library/intake.json` 在场 / JSON 合法 / `schema` 正确 /
//! `updated` 合法 / `after_action` 非空；② 每通道 `mode ∈ {open, author_only, paused}`、
//! `author_only` 须给非空 `allowlist`、`index_label` 非空；③ `library/INDEX.md` 须出现每通道的
//! `index_label`（防「闸门变了、须知没变」）；④ 两个入库机器人脚本都须**引用**声明件路径
//!（防「声明成摆设：改了没人读」）。
//!
//! 本模块是 `nf verify-report` 的 `intake` 判据，**不单独开 CLI 面**。

use crate::jsonread;
use crate::pyjson::Json;
use crate::pyval::{get, plain_str, py_str, py_truthy};
use std::collections::BTreeSet;
use std::path::Path;

pub const INTAKE_REL: &str = "library/intake.json";
pub const INDEX_REL: &str = "library/INDEX.md";
const BOTS: [&str; 2] = [
    ".github/scripts/library_ingest.py",
    ".github/scripts/gitee_ingest.py",
];
const MODES: [&str; 3] = ["open", "author_only", "paused"];
const SCHEMA: &str = "nf-intake/1";

fn is_dated(s: &str) -> bool {
    static RE: std::sync::OnceLock<regex::Regex> = std::sync::OnceLock::new();
    let re = RE.get_or_init(|| regex::Regex::new(r"^\d{4}-\d{2}-\d{2}$").expect("日期正则固定合法"));
    re.is_match(s)
}

/// 真源 `load`：缺失 / 非法 JSON / 非 dict → 空 dict。
fn load(root: &Path) -> Option<Json> {
    if !root.join(INTAKE_REL).is_file() {
        return None;
    }
    jsonread::read_file(root, INTAKE_REL).filter(|d| matches!(d, Json::Object(_)))
}

pub struct IntakeScan {
    pub issues: Vec<String>,
    pub stats: Json,
}

/// 真源 `scan` → `(issues, stats)`。
pub fn scan(root: &Path) -> IntakeScan {
    let mut issues: Vec<String> = Vec::new();
    let Some(doc) = load(root) else {
        return IntakeScan {
            issues: vec![format!(
                "缺投稿闸门声明 {}（修复指引：补声明件，字段见 results/audit 与 library/INDEX.md）",
                INTAKE_REL
            )],
            stats: Json::Object(vec![
                ("channels".to_string(), Json::Int(0)),
                ("modes".to_string(), Json::Array(Vec::new())),
            ]),
        };
    };
    if py_str(get(&doc, "schema")) != SCHEMA {
        issues.push(format!("{} schema 不匹配（期望 {}）", INTAKE_REL, SCHEMA));
    }
    if !is_dated(&py_str(get(&doc, "updated"))) {
        issues.push(format!(
            "{} updated 非 YYYY-MM-DD：{}",
            INTAKE_REL,
            crate::pyval::py_repr(get(&doc, "updated").unwrap_or(&Json::Null))
        ));
    }
    if py_str(get(&doc, "after_action")).trim().is_empty() {
        issues.push(format!(
            "{} 缺 after_action（事后处置口径须成文：违规内容怎么下架）",
            INTAKE_REL
        ));
    }

    let channels: Vec<(String, Json)> = match get(&doc, "channels") {
        Some(Json::Object(p)) if !p.is_empty() => p.clone(),
        _ => Vec::new(),
    };
    if channels.is_empty() {
        issues.push(format!("{} channels 为空（修复指引：至少声明一条接收通道）", INTAKE_REL));
    }

    let idx = root.join(INDEX_REL);
    let index_text = if idx.is_file() {
        std::fs::read_to_string(&idx).unwrap_or_default()
    } else {
        issues.push(format!("缺 {}（闸门措辞无处可查）", INDEX_REL));
        String::new()
    };

    let mut sorted = channels.clone();
    sorted.sort_by(|a, b| a.0.cmp(&b.0));
    for (name, ch) in &sorted {
        let ch = if matches!(ch, Json::Object(_)) { ch.clone() } else { Json::Object(Vec::new()) };
        let mode = py_str(get(&ch, "mode"));
        if !MODES.contains(&mode.as_str()) {
            // 真源是 `%r`（带引号）：`通道 bad-mode mode 非法：'sometimes'（取值 …）`
            issues.push(format!(
                "通道 {} mode 非法：{}（取值 {}）",
                name,
                crate::pyval::py_repr(&Json::Str(mode.clone())),
                MODES.join(" / ")
            ));
        }
        if mode == "author_only" {
            let allow: Vec<String> = crate::pyval::arr_items(get(&ch, "allowlist"))
                .iter()
                .map(|x| plain_str(x).trim().to_lowercase())
                .filter(|x| !x.is_empty())
                .collect();
            if allow.is_empty() {
                issues.push(format!(
                    "通道 {} 为 author_only 但 allowlist 为空（修复指引：给白名单，或改为 open / paused）",
                    name
                ));
            }
        }
        let label = py_str(get(&ch, "index_label"));
        if label.is_empty() {
            issues.push(format!(
                "通道 {} 缺 index_label（修复指引：给须在 {} 出现的措辞）",
                name, INDEX_REL
            ));
        } else if !index_text.is_empty() && !index_text.contains(&label) {
            issues.push(format!(
                "通道 {} 的 index_label 未出现在 {}：{}（修复指引：同步投稿须知措辞，防闸门与须知漂移）",
                name,
                INDEX_REL,
                crate::pyval::py_repr(&Json::Str(label))
            ));
        }
    }

    for rel in BOTS {
        let p = root.join(rel);
        if !p.is_file() {
            issues.push(format!("缺入库机器人脚本 {}（修复指引：闸门须有执行面）", rel));
            continue;
        }
        let text = std::fs::read_to_string(&p).unwrap_or_default();
        if !text.contains(INTAKE_REL) {
            issues.push(format!(
                "{} 未引用闸门声明 {}（修复指引：机器人须读声明件，否则改闸门不生效 = 声明成摆设）",
                rel, INTAKE_REL
            ));
        }
    }

    let mut modes: BTreeSet<String> = BTreeSet::new();
    for (_, c) in &channels {
        modes.insert(py_str(get(c, "mode")));
    }
    let _ = py_truthy(&Json::Null);
    IntakeScan {
        issues,
        stats: Json::Object(vec![
            ("channels".to_string(), Json::Int(channels.len() as i64)),
            (
                "modes".to_string(),
                Json::Array(modes.into_iter().map(Json::Str).collect()),
            ),
        ]),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// ===== 分支级差分判据（期望值由 `tools/gen_intake_branches.py` 从真源生成）=====
    ///
    /// 真语料上该面全绿 ⇒ 错误分支须合成夹具核。本夹具踩：schema / updated 非日期 / 缺 after_action /
    /// mode 非法 / author_only 白名单为空 / 缺 index_label / index_label 不在 INDEX /
    /// 合法 mode（open 与 paused）/ 缺机器人脚本 / 机器人未引用声明件。
    const WANT_IT_ISSUES: [&str; 8] = [
        "library/intake.json schema 不匹配（期望 nf-intake/1）",
        "library/intake.json updated 非 YYYY-MM-DD：'2026/01/01'",
        "library/intake.json 缺 after_action（事后处置口径须成文：违规内容怎么下架）",
        "通道 auth-only 为 author_only 但 allowlist 为空（修复指引：给白名单，或改为 open / paused）",
        "通道 auth-only 的 index_label 未出现在 library/INDEX.md：'不存在的措辞'（修复指引：同步投稿须知措辞，防闸门与须知漂移）",
        "通道 bad-mode mode 非法：'sometimes'（取值 open / author_only / paused）",
        "通道 bad-mode 缺 index_label（修复指引：给须在 library/INDEX.md 出现的措辞）",
        "缺入库机器人脚本 .github/scripts/gitee_ingest.py（修复指引：闸门须有执行面）",
    ];

    fn build_intake_fixture() -> std::path::PathBuf {
        let root = crate::testutil::fixture("intake-branches");
        std::fs::create_dir_all(root.join("library")).unwrap();
        std::fs::create_dir_all(root.join(".github/scripts")).unwrap();
        std::fs::write(root.join("library/intake.json"), r#"{"schema": "wrong/1", "updated": "2026/01/01", "after_action": "  ", "channels": {"bad-mode": {"mode": "sometimes"}, "auth-only": {"mode": "author_only", "allowlist": ["  ", ""], "index_label": "不存在的措辞"}, "good": {"mode": "open", "index_label": "开放投稿"}, "paused-ok": {"mode": "paused", "index_label": "暂停接收"}}}"#).unwrap();
        std::fs::write(root.join("library/INDEX.md"), r#"# 馆藏

> 开放投稿
> 暂停接收
"#).unwrap();
        std::fs::write(root.join(".github/scripts/library_ingest.py"), r#"# 读 library/intake.json
"#).unwrap();
        root
    }

    #[test]
    fn scan_matches_truth_source_branch_by_branch() {
        let root = build_intake_fixture();
        let got = scan(&root);
        assert_eq!(got.issues, WANT_IT_ISSUES, "逐条消息与次序都须与真源一致");
        assert!(crate::jsonread::json_eq(
            &got.stats,
            &crate::jsonread::convert(&serde_json::json!({
                "channels": 4, "modes": ["author_only", "open", "paused", "sometimes"]
            }))
            .unwrap()
        ));
    }
}
