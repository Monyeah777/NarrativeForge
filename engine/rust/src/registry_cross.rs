//! 全仓事件背书（`registry_cross`）—— 与真源 `desktop/src/core/registry_cross.py` 对账。
//!
//! 判据：某模块**订阅**的事件，全仓（官方核心 ∪ 社区包）里必须有发布方；无发布方且未登记进
//! `protocol/external_events.json`（外部通道显式挂账）→ **背书缺口 = FAIL**。
//! 发布方在**别的包**只是 WARN（不是错，但须可见）。
//!
//! 依赖 [`crate::module_signature::module_docs`] + [`crate::miniyaml`]（与 `module-signature`
//! 同一套地基——这正是先落 YAML 子集的杠杆所在）。

use crate::jsonread;
use crate::miniyaml;
use crate::pyjson::Json;
use crate::pyval::{arr_items, get, plain_str, py_str};
use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

pub const ALLOWLIST_REL: &str = "protocol/external_events.json";

/// 真源 `scan(root)` 的结论面（只保留本契约用到的量）。
pub struct CrossScan {
    pub issues: Vec<String>,
    /// `stats["events"]`
    pub events: usize,
    /// `len(stats["cross_pkg"])`
    pub cross_pkg: usize,
    /// `len(warns) - len(cross_pkg)`：已挂账为外部通道、无仓内发布方的事件数
    pub allowlisted: usize,
}

/// 模块 → `machine_contract`（沿用 `module_signature` 的枚举口径）。
fn modules(root: &Path) -> Vec<(String, Json)> {
    let mut out = Vec::new();
    for rel in crate::module_signature::module_docs(root) {
        let Ok(text) = std::fs::read_to_string(root.join(&rel)) else {
            continue;
        };
        let Some(parsed) = miniyaml::fence_yaml(&text, "machine_contract") else {
            continue;
        };
        let Some(mc) = get(&parsed, "machine_contract") else {
            continue;
        };
        if !matches!(mc, Json::Object(_)) || py_str(get(mc, "id")).is_empty() {
            continue;
        }
        out.push((rel, mc.clone()));
    }
    out
}

fn allowlist(root: &Path) -> BTreeSet<String> {
    let Some(d) = jsonread::read_file(root, ALLOWLIST_REL) else {
        return BTreeSet::new();
    };
    match get(&d, "events") {
        Some(Json::Object(pairs)) => pairs.iter().map(|(k, _)| k.clone()).collect(),
        _ => BTreeSet::new(),
    }
}

/// 真源 `scan`。
pub fn scan(root: &Path) -> CrossScan {
    // (module, pkg)
    let mut publishers: BTreeMap<String, Vec<(String, String)>> = BTreeMap::new();
    let mut subscribers: BTreeMap<String, Vec<(String, String)>> = BTreeMap::new();
    for (rel, mc) in modules(root) {
        let pkg = if let Some(rest) = rel.strip_prefix("community/") {
            rest.split('/').next().unwrap_or("").to_string()
        } else {
            "官方核心".to_string()
        };
        let mid = py_str(get(&mc, "id"));
        let Some(ev) = get(&mc, "events") else { continue };
        for e in arr_items(get(ev, "publish")) {
            publishers
                .entry(plain_str(e))
                .or_default()
                .push((mid.clone(), pkg.clone()));
        }
        for e in arr_items(get(ev, "subscribe")) {
            subscribers
                .entry(plain_str(e))
                .or_default()
                .push((mid.clone(), pkg.clone()));
        }
    }
    let allow = allowlist(root);

    let mut issues = Vec::new();
    let mut cross_pkg = 0usize;
    let mut allowlisted = 0usize;
    for (ev, subs) in subscribers.iter() {
        let empty = Vec::new();
        let pubs = publishers.get(ev).unwrap_or(&empty);
        if pubs.is_empty() {
            if allow.contains(ev) {
                allowlisted += 1;
            } else {
                let mods: Vec<String> = subs
                    .iter()
                    .map(|(m, _)| m.clone())
                    .collect::<BTreeSet<_>>()
                    .into_iter()
                    .take(3)
                    .collect();
                issues.push(format!(
                    "事件背书缺口：{} 被 {} 订阅，但全仓无发布方（修复指引：补发布模块，或登记进 {} 作为外部通道）",
                    ev,
                    mods.join("、"),
                    ALLOWLIST_REL
                ));
            }
            continue;
        }
        let sub_pkgs: BTreeSet<&String> = subs.iter().map(|(_, p)| p).collect();
        let pub_pkgs: BTreeSet<&String> = pubs.iter().map(|(_, p)| p).collect();
        if !sub_pkgs.is_empty() && !pub_pkgs.is_empty() && sub_pkgs.is_disjoint(&pub_pkgs) {
            cross_pkg += 1;
        }
    }

    let events: BTreeSet<&String> = publishers.keys().chain(subscribers.keys()).collect();
    CrossScan {
        issues,
        events: events.len(),
        cross_pkg,
        allowlisted,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn missing_allowlist_is_an_empty_set_not_an_error() {
        let tmp = crate::testutil::fixture("rc-empty");
        assert!(allowlist(&tmp).is_empty());
        let got = scan(&tmp);
        assert!(got.issues.is_empty());
        assert_eq!(got.events, 0);
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn uncovered_subscription_is_flagged_and_allowlist_silences_it() {
        let tmp = crate::testutil::fixture("rc-gap");
        std::fs::create_dir_all(tmp.join("04_模块库/通用类")).unwrap();
        std::fs::write(
            tmp.join("04_模块库/通用类/M01_a.md"),
            "```yaml\nmachine_contract:\n  id: M01\n  events:\n    subscribe: [ghost_event]\n```\n",
        )
        .unwrap();
        let a = scan(&tmp);
        assert_eq!(a.issues.len(), 1, "无发布方必须判红：{:?}", a.issues);
        assert!(a.issues[0].contains("ghost_event"));
        assert_eq!(a.events, 1);

        // 挂账为外部通道后不再判红
        std::fs::create_dir_all(tmp.join("protocol")).unwrap();
        std::fs::write(
            tmp.join(ALLOWLIST_REL),
            r#"{"events": {"ghost_event": {"note": "外部通道"}}}"#.as_bytes(),
        )
        .unwrap();
        let b = scan(&tmp);
        assert!(b.issues.is_empty(), "已挂账不得再判红：{:?}", b.issues);
        assert_eq!(b.allowlisted, 1);
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn cross_package_publication_is_counted_not_flagged() {
        let tmp = crate::testutil::fixture("rc-cross");
        std::fs::create_dir_all(tmp.join("04_模块库/通用类")).unwrap();
        std::fs::create_dir_all(tmp.join("community/某包/modules")).unwrap();
        std::fs::write(
            tmp.join("04_模块库/通用类/M01_a.md"),
            "```yaml\nmachine_contract:\n  id: M01\n  events:\n    subscribe: [e1]\n```\n",
        )
        .unwrap();
        std::fs::write(
            tmp.join("community/某包/modules/M02_b.md"),
            "```yaml\nmachine_contract:\n  id: M02\n  events:\n    publish: [e1]\n```\n",
        )
        .unwrap();
        let got = scan(&tmp);
        assert!(got.issues.is_empty(), "跨包是 WARN 不是 FAIL：{:?}", got.issues);
        assert_eq!(got.cross_pkg, 1);
        let _ = std::fs::remove_dir_all(&tmp);
    }
}
