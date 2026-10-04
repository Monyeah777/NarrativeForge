//! 基线相对回归评分（`score`）—— 与真源 `desktop/src/core/regression_score.py` 对账。
//!
//! 真源 `evaluate` 要跑 6 个扫描器。本线已移植其中 2 个（`doc_hygiene` / `asset_density`），
//! 其余 4 个（`schema_lint` / `conformance_scan` / `purity_scan` / `quality_depth_scan`）由
//! `--signals` 以**计数**形式喂入——`None` 表示"扫描器不可用"，与真源 `_count` 的哨兵语义一致
//! （**不可用 ≠ 零问题**：真源按 0 分计并记 issue，本线同）。
//!
//! 随着更多扫描器移植，`--signals` 的输入面会逐步缩小，直至 `nf score` 可完全自主。

use crate::asset_density;
use crate::doc_hygiene;
use crate::pyfloat;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, plain_str_opt};
use std::path::Path;

pub const SCHEMA: &str = "nf-score/1";
pub const DEFAULT_BASELINE: &str = "protocol/score_baseline.json";

/// 真源 `SIGNAL_SPECS`：(名, 权重, 说明)。权重和 = 1.0。
pub const SIGNAL_SPECS: [(&str, f64, &str); 6] = [
    ("schema_clean", 0.20, "IDL schema 零漂移（schema_lint）"),
    ("conformance_clean", 0.20, "机读契约/一致性分级零虚标（conformance_scan）"),
    ("purity_clean", 0.15, "架构纯度零违规（purity_scan）"),
    ("doc_hygiene", 0.15, "文档卫生零缺口（doc_hygiene）"),
    ("depth_clean", 0.15, "质量纵深零缺口（quality_depth_scan）"),
    ("asset_density", 0.15, "资产键密度归一（asset_density）"),
];

/// 尚未移植的扫描器的计数。`None` = 扫描器不可用（真源 `_count` 的哨兵）。
///
/// `schema_clean` 已**自主算出**（`schema_lint` 已移植），故不在此列——能自算的一律自算，
/// 喂入面越小越不容易掩盖分歧。
#[derive(Default, Clone)]
pub struct Supplied {
    pub depth_clean: Option<i64>,
}

pub struct Current {
    pub score: f64,
    /// (name, weight, value, note)
    pub signals: Vec<(String, f64, f64, String)>,
    pub asset_keys: i64,
    pub asset_files: i64,
    pub issues: Vec<String>,
}

impl Current {
    /// 真源 `_evaluate_impl` 的返回字典。
    pub fn to_json(&self) -> Json {
        Json::Object(vec![
            ("schema".to_string(), Json::Str(SCHEMA.to_string())),
            ("score".to_string(), Json::Float(self.score)),
            (
                "signals".to_string(),
                Json::Array(
                    self.signals
                        .iter()
                        .map(|(n, w, v, note)| {
                            Json::Object(vec![
                                ("name".to_string(), Json::Str(n.clone())),
                                ("weight".to_string(), Json::Float(*w)),
                                ("value".to_string(), Json::Float(*v)),
                                ("note".to_string(), Json::Str(note.clone())),
                            ])
                        })
                        .collect(),
                ),
            ),
            (
                "metrics".to_string(),
                Json::Object(vec![
                    ("asset_keys".to_string(), Json::Int(self.asset_keys)),
                    ("asset_files".to_string(), Json::Int(self.asset_files)),
                ]),
            ),
            (
                "issues".to_string(),
                Json::Array(self.issues.iter().map(|s| Json::Str(s.clone())).collect()),
            ),
        ])
    }
}

/// 真源 `_penalty`：问题数 → 0..1 得分。
fn penalty(issue_count: i64, step: f64) -> f64 {
    (1.0 - issue_count as f64 * step).max(0.0)
}

/// 真源 `_evaluate_impl`。
pub fn evaluate(root: &Path, sup: &Supplied) -> Current {
    let mut issues: Vec<String> = Vec::new();
    let mut values: Vec<(&'static str, f64)> = Vec::new();

    macro_rules! scan_signal {
        ($name:expr, $module:expr, $func:expr, $n:expr, $step:expr) => {
            match $n {
                None => {
                    issues.push(format!(
                        "扫描器不可用：core.{}.{}（评分按 0 分计，修复后重跑——不可用不等于零问题）",
                        $module, $func
                    ));
                    values.push(($name, 0.0));
                }
                Some(k) => values.push(($name, penalty(k, $step))),
            }
        };
    }

    // 真源 `_count(root, "schema_lint", "scan")`：本线自算（不喂入）。
    // 真源在扫描器**抛异常**时返回 None → 按 0 分计并记 issue；本线的 scan 把可预见的失败
    // 都收敛成 issue 而非异常，故此处恒为可用——语义不劣化。
    let schema_issues = crate::schema_lint::issue_count(root) as i64;
    values.push(("schema_clean", penalty(schema_issues, 0.1)));

    // 真源 `_count(root, "conformance_scan", "scan")`：本线自算（不喂入）。
    let conformance_issues = crate::conformance_scan::issue_count(root) as i64;
    values.push(("conformance_clean", penalty(conformance_issues, 0.1)));
    // 真源 `_count(root, "purity_scan", "scan")`：本线自算（不喂入）。
    let purity_issues = crate::purity::scan(root).0.len() as i64;
    values.push(("purity_clean", penalty(purity_issues, 0.1)));

    // 真源 `_markers` 把 doc_hygiene 包在 try/except 里：不可用 → None → 0 分 + issue。
    // 本线的 check_markers 不会抛，故恒为可用——语义不劣化（真源能算的，本线也算得出）。
    let marks = doc_hygiene::check_markers(root);
    values.push(("doc_hygiene", penalty(marks.len() as i64, 0.2)));

    scan_signal!(
        "depth_clean",
        "quality_depth_scan",
        "scan",
        sup.depth_clean,
        0.1
    );

    // 真源忽略 asset_density 自身的 issues（`_di` 未用）——本线同。
    let (_di, dstats) = asset_density::scan(root);
    let keys = dstats.keys as i64;
    let files = dstats.files as i64;
    let density = if files != 0 { keys as f64 / files as f64 } else { 0.0 };
    values.push((
        "asset_density",
        (density / asset_density::DENSITY_TARGET).clamp(0.0, 1.0),
    ));
    if files == 0 {
        issues.push("资产档扫描为空（asset_density 未取到文件数）".to_string());
    }

    let mut signals: Vec<(String, f64, f64, String)> = Vec::new();
    let mut total = 0.0f64;
    for (name, weight, desc) in SIGNAL_SPECS {
        let raw = values.iter().find(|(n, _)| *n == name).map(|(_, v)| *v).unwrap_or(0.0);
        let v = pyfloat::round_to(raw, 4);
        total += weight * v;
        signals.push((name.to_string(), weight, v, desc.to_string()));
    }
    let score = pyfloat::round_to(total * 100.0, 2);

    Current {
        score,
        signals,
        asset_keys: keys,
        asset_files: files,
        issues,
    }
}

fn f64_of(j: Option<&Json>) -> f64 {
    match j {
        Some(Json::Float(f)) => *f,
        Some(Json::Int(i)) => *i as f64,
        _ => 0.0,
    }
}

/// 真源 `compare`：当前 vs 基线 → `{ok, delta, verdict, regressed[], exempted[]}`。
pub fn compare(
    current: &Current,
    baseline: &Json,
    tolerance: f64,
    exceptions: &[(String, String)],
) -> Json {
    const EPS: f64 = 1e-9;

    let base_sig: Vec<(String, f64)> = arr_items(get(baseline, "signals"))
        .iter()
        .map(|s| (plain_str_opt(get(s, "name")), f64_of(get(s, "value"))))
        .collect();
    let cur_sig: Vec<(String, f64)> = current
        .signals
        .iter()
        .map(|(n, _, v, _)| (n.clone(), *v))
        .collect();

    let mut names: Vec<String> = base_sig
        .iter()
        .map(|(n, _)| n.clone())
        .filter(|n| cur_sig.iter().any(|(m, _)| m == n))
        .collect();
    names.sort();
    names.dedup();

    let mut regressed: Vec<Json> = Vec::new();
    let mut exempted: Vec<Json> = Vec::new();
    for name in &names {
        let b = base_sig.iter().find(|(n, _)| n == name).map(|(_, v)| *v).unwrap_or(0.0);
        let c = cur_sig.iter().find(|(n, _)| n == name).map(|(_, v)| *v).unwrap_or(0.0);
        if c < b - EPS {
            let mut pairs = vec![
                ("signal".to_string(), Json::Str(name.clone())),
                ("from".to_string(), Json::Float(pyfloat::round_to(b, 4))),
                ("to".to_string(), Json::Float(pyfloat::round_to(c, 4))),
                ("drop".to_string(), Json::Float(pyfloat::round_to(b - c, 4))),
            ];
            if let Some((_, reason)) = exceptions.iter().find(|(s, _)| s == name) {
                pairs.push(("reason".to_string(), Json::Str(reason.clone())));
                exempted.push(Json::Object(pairs));
            } else {
                regressed.push(Json::Object(pairs));
            }
        }
    }

    let base_score = f64_of(get(baseline, "score"));
    let cur_score = current.score;
    let delta = pyfloat::round_to(cur_score - base_score, 2);

    // 审计例外同时释放整体门预算（被豁免的回落按 权重×跌幅 折算成额度）
    let weights: Vec<(String, f64)> = current
        .signals
        .iter()
        .map(|(n, w, _, _)| (n.clone(), *w))
        .collect();
    let mut exempt_budget = 0.0f64;
    for e in &exempted {
        let sig = plain_str_opt(get(e, "signal"));
        let drop = f64_of(get(e, "drop"));
        exempt_budget += weights.iter().find(|(n, _)| *n == sig).map(|(_, w)| *w).unwrap_or(0.0)
            * drop
            * 100.0;
    }

    let ok = delta >= -(tolerance.abs() + exempt_budget) && regressed.is_empty();

    let has_base_signals = !arr_items(get(baseline, "signals")).is_empty();
    let verdict = if !has_base_signals {
        "无基线（只报当前分值，未做回归判定）".to_string()
    } else if !ok && !regressed.is_empty() {
        let names: Vec<String> = regressed
            .iter()
            .map(|r| plain_str_opt(get(r, "signal")))
            .collect();
        format!("回归（信号回落）：{}", names.join("、"))
    } else if !ok {
        format!(
            "回归（整体分下降 {:.2} > 容差 {:.2}）",
            -delta,
            tolerance.abs()
        )
    } else if !exempted.is_empty() {
        format!("通过（含 {} 项审计例外）", exempted.len())
    } else {
        "通过（无回归）".to_string()
    };

    Json::Object(vec![
        ("ok".to_string(), Json::Bool(ok)),
        ("delta".to_string(), Json::Float(delta)),
        ("baseline_score".to_string(), Json::Float(base_score)),
        ("current_score".to_string(), Json::Float(cur_score)),
        ("regressed".to_string(), Json::Array(regressed)),
        ("exempted".to_string(), Json::Array(exempted)),
        ("verdict".to_string(), Json::Str(verdict)),
    ])
}

/// `nf score --json` 的输出字节（`print` 的换行也含在内）。
pub fn render_bytes(current: &Current, baseline: &Json, tolerance: f64, exceptions: &[(String, String)]) -> Vec<u8> {
    let cmp = compare(current, baseline, tolerance, exceptions);
    Json::Object(vec![
        ("kind".to_string(), Json::Str("score".to_string())),
        ("current".to_string(), current.to_json()),
        ("compare".to_string(), cmp),
    ])
    .dumps_file()
    .into_bytes()
}

/// 退出码：`0 if out["ok"] else 1`。
pub fn is_ok(current: &Current, baseline: &Json, tolerance: f64, exceptions: &[(String, String)]) -> bool {
    matches!(get(&compare(current, baseline, tolerance, exceptions), "ok"), Some(Json::Bool(true)))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cur(vals: &[(&str, f64, f64)]) -> Current {
        Current {
            score: 100.0,
            signals: vals
                .iter()
                .map(|(n, w, v)| ((*n).to_string(), *w, *v, String::new()))
                .collect(),
            asset_keys: 0,
            asset_files: 0,
            issues: Vec::new(),
        }
    }

    #[test]
    fn penalty_floors_at_zero() {
        assert_eq!(penalty(0, 0.1), 1.0);
        assert_eq!(penalty(10, 0.1), 0.0);
        assert_eq!(penalty(25, 0.1), 0.0);
        assert!((penalty(3, 0.1) - 0.7).abs() < 1e-12);
    }

    #[test]
    fn no_baseline_signals_yields_dedicated_verdict() {
        let c = cur(&[("schema_clean", 0.2, 1.0)]);
        let out = compare(&c, &Json::Object(vec![]), 0.0, &[]);
        assert_eq!(
            plain_str_opt(get(&out, "verdict")),
            "无基线（只报当前分值，未做回归判定）"
        );
    }

    #[test]
    fn single_signal_drop_is_regression_even_if_total_score_holds() {
        // no silent worsening：总分不降掩盖不了单信号恶化
        let baseline: Json = crate::jsonread::convert(&serde_json::json!({
            "score": 100.0,
            "signals": [{"name": "schema_clean", "value": 1.0},
                        {"name": "purity_clean", "value": 0.5}]
        }))
        .unwrap();
        let c = cur(&[("schema_clean", 0.2, 1.0), ("purity_clean", 0.15, 0.4)]);
        let out = compare(&c, &baseline, 0.0, &[]);
        assert_eq!(get(&out, "ok"), Some(&Json::Bool(false)));
        assert!(plain_str_opt(get(&out, "verdict")).contains("信号回落"));
    }

    #[test]
    fn exemption_moves_item_and_releases_budget() {
        let baseline: Json = crate::jsonread::convert(&serde_json::json!({
            "score": 100.0,
            "signals": [{"name": "purity_clean", "value": 1.0}]
        }))
        .unwrap();
        let c = cur(&[("purity_clean", 0.15, 0.9)]);
        // 不豁免 → 回落
        assert_eq!(get(&compare(&c, &baseline, 0.0, &[]), "ok"), Some(&Json::Bool(false)));
        // 豁免 → 进 exempted 且释放额度
        let exc = vec![("purity_clean".to_string(), "已批准".to_string())];
        let out = compare(&c, &baseline, 0.0, &exc);
        assert_eq!(get(&out, "exempted").map(|v| matches!(v, Json::Array(a) if a.len() == 1)), Some(true));
        assert!(plain_str_opt(get(&out, "verdict")).contains("审计例外"));
    }
}
